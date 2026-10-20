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
import threading
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class _ReadWriteLock:
    """Many readers or one writer, within this process.

    DuckDB refuses a second connection to a file this process already
    holds in another mode -- a read-only open while a read-write one is
    up, or an ATTACH of sim_results.duckdb while another connection has it
    attached ("Unique file handle conflict", measured). The server both
    reads bars for every backtest and records every finished configuration,
    on different threads, so it takes this around each: reads stay
    concurrent, and a write waits for the reads in flight and holds new
    ones off only for its own few seconds.
    """

    def __init__(self) -> None:
        self._condition = threading.Condition()
        self._readers = 0
        self._writing = False

    @contextmanager
    def reading(self) -> Iterator[None]:
        with self._condition:
            self._condition.wait_for(lambda: not self._writing)
            self._readers += 1
        try:
            yield
        finally:
            with self._condition:
                self._readers -= 1
                self._condition.notify_all()

    @contextmanager
    def writing(self) -> Iterator[None]:
        with self._condition:
            self._condition.wait_for(lambda: not self._writing and self._readers == 0)
            self._writing = True
        try:
            yield
        finally:
            with self._condition:
                self._writing = False
                self._condition.notify_all()


# This process's warehouse connections: bars.py reads under reading(),
# result_writer.BatchedResultWriter writes under writing().
WAREHOUSE_LOCK = _ReadWriteLock()

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
    elif (root / MARKET_DATA_DB).exists():
        _migrate_absolute_views(root)

    con = duckdb.connect(str(root / MARKET_DATA_DB), read_only=read_only)
    # The lake views read RELATIVE globs (schema.ohlcv_view_ddl), resolved
    # here: the same catalog then works wherever the warehouse is mounted
    # -- the host's checkout and /app/warehouse in a container at once.
    con.execute(f"SET file_search_path = '{_sql_path(root.resolve())}'")

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
        if _has_absolute_views(con):
            from engine.warehouse.schema import refresh_views

            refresh_views(con, root)

    logger.info(
        f"Warehouse open at {root} (threads={resolved_threads}, "
        f"memory_limit={memory_mib}MiB, read_only={read_only})"
    )
    return con


_LAKE_VIEWS = {"ohlcv": OHLCV_DIR, "external": EXTERNAL_DIR, "trade_executions": EXECUTIONS_DIR}


def _has_absolute_views(con: Any) -> bool:
    """True if a persisted lake view still reads an ABSOLUTE path.

    Views created before they became relative stored their read_parquet
    glob as an absolute path, fixed when created. A warehouse moved to
    another directory or machine (it moved from C:/workspace/... on Windows
    to Linux) kept pointing at the old location: every query failed, and
    bars.load_frame -- which must never raise -- read that as "no data".
    """
    views = con.execute(
        "SELECT view_name, sql FROM duckdb_views() WHERE NOT internal AND view_name IN "
        "('ohlcv', 'external', 'trade_executions')"
    ).fetchall()
    return any(f"'{_LAKE_VIEWS[name]}/**/*.parquet'" not in sql for name, sql in views)


def _migrate_absolute_views(root: Path) -> None:
    """Rewrite an older warehouse's absolute views as relative ones, once,
    before a read-only open.

    A read-only connection cannot rewrite them, so this opens read-write
    briefly: afterwards the check finds nothing to do, wherever the
    warehouse is later moved or mounted. If the file is locked by a writer
    (or not writable), the read-only open proceeds and the warning names
    the fix.
    """
    import duckdb

    try:
        con = duckdb.connect(str(root / MARKET_DATA_DB), read_only=True)
        try:
            sim_path = _sql_path(root / SIM_RESULTS_DB)
            con.execute(f"ATTACH IF NOT EXISTS '{sim_path}' AS sim (READ_ONLY)")
            stale = _has_absolute_views(con)
        finally:
            con.close()
        if stale:
            open_warehouse(root).close()  # read-write: rewrites the views
            logger.info(f"Warehouse views at {root} rewritten with relative paths")
    except Exception as e:
        if "lock" in str(e).lower():
            # Another process is writing, so nothing could be checked: the
            # caller's own open waits it out, and the next open checks again.
            # Not a sign the views are stale, and not worth a warning.
            logger.debug(f"Warehouse at {root} busy; view check skipped ({e})")
            return
        logger.warning(
            f"Warehouse at {root} has views with absolute paths and they could not be "
            f"rewritten ({e}). Run `python tools/build_warehouse.py --init` once."
        )


def _sql_path(path: Path) -> str:
    return str(path).replace("'", "''")


def lake_path(root: str | Path, subdir: str) -> str:
    """A Parquet lake directory as a forward-slashed absolute string, for
    writes (ingest, the executions sink). The views read relative globs.

    DuckDB's glob syntax treats backslash as an escape character, so a
    Windows path interpolated raw into read_parquet('...') silently
    matches nothing. Every SQL-bound path goes through here.
    """
    return Path(root).joinpath(subdir).resolve().as_posix()
