"""OHLCV bars for the ONGOING backtest/simulation path.

--------------------------------------------------------------------
WHY THIS EXISTS

server/backtest.py used to read bars with a plain
`pd.read_csv(KNOWN_DATA[ticker], ...)` -- straight off `data/`. On
2026-09-16 that directory's entire contents (every fund's decade of
minute bars) were deleted as a side effect of an unrelated `git
worktree remove` walking through a directory junction. The backtest
engine had no independent copy of anything it needed to run.

It turned out one existed anyway: `tools/build_warehouse.py` had
already ingested most of `data/` into `warehouse/market_data.duckdb`
(a Parquet lake, `warehouse/ohlcv/ticker=.../year=.../*.parquet`, plus
the DuckDB catalog and views over it) for unrelated analytical
purposes -- `--top`, `--explain-execution`, ad-hoc SQL. It lives
outside `data/`, so it survived, and every recovered fund's bars in
this rebuilt `data/` were exported straight back out of it.

This module is the fix for the actual gap: the SIMULATION read path
now goes through the warehouse directly, so a `data/` loss (this one
or a future one) no longer takes the backtest engine down with it.
`data/` still exists and is still where `cli.py fetch-data` lands new
downloads and `tools/build_warehouse.py --ingest` reads from -- that
intake step legitimately needs a file on disk to ingest -- but nothing
that RUNS a backtest, serves a chart, or asks "is this fund available"
touches it anymore.

--------------------------------------------------------------------
DUCKDB IS IMPORTED LAZILY

duckdb/polars are optional dependencies (requirements-warehouse.txt,
not requirements.txt) -- server/backtest.py imports this module
UNCONDITIONALLY, including on the Raspberry Pi, which forwards every
backtest to the workstation and never actually calls these functions.
Importing duckdb at module scope here would make this module -- and
therefore server/backtest.py, and therefore server/app.py -- fail to
import on a machine that never needed it. src/warehouse/connection.py
defers the same way, for the same reason; every function below opens
its own connection and closes it, matching that module's "read-only
opens are safe from many processes at once" contract.

--------------------------------------------------------------------
WHAT "NO DATA" MEANS HERE

A missing warehouse, a missing ticker, and a duckdb import failure all
produce the SAME answer -- an empty result, never an exception. This
mirrors the file-existence check this module replaces
(`Path(KNOWN_DATA[ticker]).exists()`): the caller decides what "no
data for this fund" means (a 404, a "None of [...] has a data file"
ValueError, an `ok: false` in the funds listing), and this module's
job is only to say honestly whether there is any.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import pandas as pd

# Overridable so tests can point at a small warehouse built from a
# fixture CSV instead of the real multi-GB one -- the same pattern
# server/jobs.py's VAI_QUEUE_DIR and server/history.py's
# VAI_RUN_HISTORY_DIR already use for the identical reason.
_ROOT_ENV = "VAI_WAREHOUSE_DIR"
_REPO_ROOT = Path(__file__).resolve().parent.parent.parent

_EMPTY_COLUMNS = ("open", "high", "low", "close", "volume")


def warehouse_root() -> Path:
    configured = os.environ.get(_ROOT_ENV)
    return Path(configured) if configured else _REPO_ROOT / "warehouse"


def _empty_frame() -> pd.DataFrame:
    frame = pd.DataFrame(columns=list(_EMPTY_COLUMNS))
    frame.index = pd.DatetimeIndex([], name="timestamp", tz="UTC")
    return frame


def _connect(root: Path) -> Any | None:
    """A read-only connection, or None if the warehouse cannot be opened.

    Never raises: a corrupt or absent warehouse is "no data", the same
    as a missing CSV used to be -- not a reason to 500 a chart request.
    """
    if not (root / "market_data.duckdb").exists():
        return None
    try:
        from src.warehouse.connection import open_warehouse

        return open_warehouse(root, read_only=True)
    except Exception:
        return None


def available_tickers() -> set[str]:
    """Every ticker with at least one bar in the warehouse right now.

    Replaces `{t for t in KNOWN_DATA if Path(KNOWN_DATA[t]).exists()}`.
    Empty when the warehouse is absent or empty -- a normal state (a
    fresh checkout, a fund fetched but never ingested), not an error.
    """
    con = _connect(warehouse_root())
    if con is None:
        return set()
    try:
        return {row[0] for row in con.execute("SELECT DISTINCT ticker FROM ohlcv").fetchall()}
    except Exception:
        return set()
    finally:
        con.close()


def row_count(ticker: str) -> int | None:
    """Bars for one ticker, or None if the warehouse or ticker is absent.

    For callers that only need a length (server/backtest.py did this
    with `pd.read_csv(path, usecols=["close"])` to avoid parsing every
    column) -- COUNT(*) over the Parquet lake's row-group metadata does
    not need to read the data at all.
    """
    con = _connect(warehouse_root())
    if con is None:
        return None
    try:
        (count,) = con.execute("SELECT COUNT(*) FROM ohlcv WHERE ticker = ?", [ticker]).fetchone()
    except Exception:
        return None
    finally:
        con.close()
    return int(count) if count else None


def load_frame(ticker: str) -> pd.DataFrame:
    """One ticker's full bar history, shaped exactly like the old

        pd.read_csv(KNOWN_DATA[ticker], parse_dates=["timestamp"]).set_index("timestamp")

    -- a UTC tz-aware DatetimeIndex named "timestamp", ascending,
    columns open/high/low/close/volume (float64 x4, int64). Every
    existing caller applies its own date-window and bar-cap AFTER
    loading (server/backtest.py's `window()`); this deliberately does
    not duplicate that logic, so there is one definition of "windowed"
    rather than two that could drift.

    Empty (same columns, zero rows) for an unknown ticker or an absent
    warehouse, never an exception -- callers gate on
    `available_tickers()` first for the "no data at all" case, exactly
    as they gated on file-existence before; this only has to behave
    sanely if that gate is skipped.
    """
    con = _connect(warehouse_root())
    if con is None:
        return _empty_frame()
    try:
        frame = con.execute(
            "SELECT timestamp, open, high, low, close, volume "
            "FROM ohlcv WHERE ticker = ? ORDER BY timestamp",
            [ticker],
        ).df()
    except Exception:
        return _empty_frame()
    finally:
        con.close()
    if frame.empty:
        return _empty_frame()
    return frame.set_index("timestamp")


def fingerprint(ticker: str) -> str | None:
    """A cheap, STABLE identity for one ticker's bars, or None if absent.

    For remote shards deciding whether their cached copy is current
    (server/shards.py). One aggregate scan rather than hashing a million
    rows in Python.

    IT MUST BE THE SAME ANSWER EVERY TIME, AND THE OBVIOUS VERSION WAS
    NOT. This first summed the price columns, which DuckDB aggregates in
    parallel -- and float addition is not associative, so the sum (and
    the fingerprint) changed on every single call. A shard therefore
    believed its cache was stale every time and re-downloaded ~16 MB of
    bars before each sweep; the caching this exists for never once hit.
    Caught by watching a Raspberry Pi shard download the same bars twice
    in a row. BIT_XOR over a row hash is exact, integer, and independent
    of the order rows are combined in.
    """
    con = _connect(warehouse_root())
    if con is None:
        return None
    try:
        row = con.execute(
            "SELECT COUNT(*), MIN(timestamp), MAX(timestamp), "
            "BIT_XOR(hash(timestamp, open, high, low, close, volume)) "
            "FROM ohlcv WHERE ticker = ?",
            [ticker],
        ).fetchone()
    except Exception:
        return None
    finally:
        con.close()
    if not row or not row[0]:
        return None
    import hashlib

    return hashlib.sha256(repr(tuple(str(value) for value in row)).encode()).hexdigest()[:32]


__all__ = ["available_tickers", "fingerprint", "load_frame", "row_count", "warehouse_root"]
