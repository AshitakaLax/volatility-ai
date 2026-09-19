"""
Opening the warehouse: ATTACH both databases, tune for this machine.

WHY THE PRAGMAS ARE NOT LEFT AT DEFAULT

A sweep over the 10-year minute dataset scans ~1M rows per symbol and
joins them against sweep output. DuckDB's defaults are deliberately
conservative because it does not know what else is running. Three
settings matter here:

  threads        -- defaults to core count already, but is set
                    explicitly so the value is visible in
                    duckdb_settings() and can be capped by a caller
                    that is sharing the box with a live trading loop.
  memory_limit   -- defaults to ~80% of RAM in recent DuckDB, but the
                    default is computed from the CONTAINER's view of
                    memory, which on this project's Raspberry Pi and in
                    Docker has historically over-reported. Setting it
                    explicitly from a value we measured ourselves is
                    the difference between spilling to disk and being
                    OOM-killed mid-sweep.
  temp_directory -- a memory_limit with nowhere to spill turns a large
                    join into an error instead of a slow query.

WHY TimeZone IS FORCED TO UTC

Measured on this machine: DuckDB's default TimeZone is the system
zone (America/Denver here), and it affects both how TIMESTAMPTZ values
render and what TIMESTAMPTZ::TIMESTAMP produces -- the same instant
came back as 14:30 under UTC and 07:30 under America/Denver, silently.
Every bar in data/ is stored UTC and every backtest reasons in UTC, so
a warehouse whose answers depend on the developer's timezone is a
reproducibility bug waiting to happen. Pinned, not inherited.
"""

from __future__ import annotations

import ctypes
import logging
import os
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# Fraction of system RAM DuckDB may use. Not 1.0: the sweep engine
# itself holds the bar DataFrame plus one blotter per in-flight
# combination, and with n_jobs > 1 there is a worker process per job
# holding its own copy. The warehouse is a guest here, not the tenant.
DEFAULT_MEMORY_FRACTION = 0.8

# Used when RAM cannot be determined. Deliberately small -- being
# needlessly slow on a big machine is recoverable; claiming 80% of a
# number we guessed too high is not.
_FALLBACK_RAM_BYTES = 8 * 1024**3

MARKET_DATA_DB = "market_data.duckdb"
SIM_RESULTS_DB = "sim_results.duckdb"
OHLCV_DIR = "ohlcv"
EXECUTIONS_DIR = "executions"
EXTERNAL_DIR = "external"


class _MemoryStatusEx(ctypes.Structure):
    """Windows MEMORYSTATUSEX. dwLength must be set to sizeof(self)
    before the call or GlobalMemoryStatusEx rejects it."""

    _fields_ = [
        ("dwLength", ctypes.c_ulong),
        ("dwMemoryLoad", ctypes.c_ulong),
        ("ullTotalPhys", ctypes.c_ulonglong),
        ("ullAvailPhys", ctypes.c_ulonglong),
        ("ullTotalPageFile", ctypes.c_ulonglong),
        ("ullAvailPageFile", ctypes.c_ulonglong),
        ("ullTotalVirtual", ctypes.c_ulonglong),
        ("ullAvailVirtual", ctypes.c_ulonglong),
        ("ullAvailExtendedVirtual", ctypes.c_ulonglong),
    ]


def total_system_ram_bytes() -> int:
    """Physical RAM, without adding psutil as a dependency.

    psutil would be the one-liner, but it is a compiled package and
    this project keeps its dependency surface deliberately small (the
    Pi builds wheels from source). Both branches here are stdlib.
    """
    if os.name == "nt":
        try:
            status = _MemoryStatusEx()
            status.dwLength = ctypes.sizeof(_MemoryStatusEx)
            if ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(status)):
                return int(status.ullTotalPhys)
            logger.warning("GlobalMemoryStatusEx returned failure; using fallback RAM figure.")
        except (AttributeError, OSError) as e:
            logger.warning(f"Could not read Windows memory status ({e}); using fallback.")
        return _FALLBACK_RAM_BYTES

    try:
        return int(os.sysconf("SC_PHYS_PAGES") * os.sysconf("SC_PAGE_SIZE"))
    except (AttributeError, OSError, ValueError) as e:
        logger.warning(f"Could not read sysconf memory figures ({e}); using fallback.")
        return _FALLBACK_RAM_BYTES


def open_warehouse(
    root: str | Path,
    *,
    read_only: bool = False,
    threads: int | None = None,
    memory_fraction: float = DEFAULT_MEMORY_FRACTION,
) -> Any:
    """Open market_data with sim_results ATTACHed as `sim`, tuned.

    Returns a duckdb connection whose default catalog is market_data.
    Both catalogs are addressable (`market_data.ohlcv`, `sim.simulations`).

    read_only opens both databases read-only, which is how a second
    process may safely inspect a warehouse a sweep is writing to --
    DuckDB permits one read-write process per file and many readers.
    """
    import duckdb  # deferred: see the package docstring

    root = Path(root)
    if not read_only:
        root.mkdir(parents=True, exist_ok=True)

    con = duckdb.connect(str(root / MARKET_DATA_DB), read_only=read_only)

    # Qualified as a raw literal rather than a parameter: ATTACH does
    # not accept a prepared-statement placeholder for the path.
    attach_flags = " (READ_ONLY)" if read_only else ""
    sim_path = str(root / SIM_RESULTS_DB).replace("'", "''")
    con.execute(f"ATTACH IF NOT EXISTS '{sim_path}' AS sim{attach_flags}")

    resolved_threads = threads if threads is not None else (os.cpu_count() or 1)
    memory_mib = max(256, int(total_system_ram_bytes() * memory_fraction) // 1024**2)

    con.execute(f"SET threads TO {int(resolved_threads)}")
    con.execute(f"SET memory_limit = '{memory_mib}MiB'")
    con.execute("SET TimeZone='UTC'")
    if not read_only:
        # Only meaningful for writes, and a read-only connection should
        # not be creating directories.
        temp_dir = str(root / "tmp").replace("'", "''")
        con.execute(f"SET temp_directory = '{temp_dir}'")
        # Large COPY statements do not need to preserve row order, and
        # not preserving it lets DuckDB parallelize the write.
        con.execute("SET preserve_insertion_order = false")

    logger.info(
        f"Warehouse open at {root} (threads={resolved_threads}, "
        f"memory_limit={memory_mib}MiB, read_only={read_only})"
    )
    return con


def lake_path(root: str | Path, subdir: str) -> str:
    """A Parquet lake directory as a forward-slashed absolute string.

    DuckDB's glob syntax treats backslash as an escape character, so a
    Windows path interpolated raw into read_parquet('...') silently
    matches nothing. Every SQL-bound path goes through here.
    """
    return Path(root).joinpath(subdir).resolve().as_posix()
