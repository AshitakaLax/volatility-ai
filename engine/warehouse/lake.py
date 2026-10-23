"""
The bar lake's files, read and replaced directly: how the warehouse is kept
current (tools/refresh_warehouse.py).

--------------------------------------------------------------------
WHY NOT THROUGH THE CATALOG

Everything else reads bars through market_data.duckdb's `ohlcv` view
(bars.py), and that view is only a glob over these files. The catalog has
one writer at a time, and the server takes it for every batch of sweep
results. A refresh in its own container would wait for it, or make that
writer wait. It needs neither: it reads the files the view reads, writes
files the view picks up, uses an in-memory DuckDB for both, and never
opens the catalog.

--------------------------------------------------------------------
A YEAR IS REPLACED WHOLE, IN ONE RENAME

`ohlcv/ticker=X/year=Y/` is one fund's year (the year of the UTC
timestamp, as the ingest partitions it). An update writes the year's
merged bars into a new directory under `staging/`, then exchanges the two
directories in one rename: Linux's renameat2 with RENAME_EXCHANGE. A
backtest reading the lake sees the old year or the new one, never both and
never neither. A re-download replaces every year of a fund in one exchange
of the fund's directory, so no reader sees 2016 adjusted one way and 2026
another.

Where there is no such call (not Linux; a filesystem without it), two
renames do it, and a reader in the microseconds between finds the year
missing.

Each year is one file, `data_0.parquet`, sorted by time, in the ingest's
schema: the timestamp as UTC microseconds, four DOUBLE prices, a BIGINT
volume, and the ticker and year only in the path.

--------------------------------------------------------------------
THE PREVIOUS COPY IS KEPT

A fund replaced whole keeps its previous directory in staging/previous/
until it is replaced again, so a re-download that went wrong can be moved
back by hand.
"""

from __future__ import annotations

import ctypes
import errno
import os
import shutil
import sys
import time
from collections.abc import Iterable, Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

from engine.core.exceptions import DataValidationError
from engine.core.trading_calendar import EASTERN
from engine.warehouse.connection import OHLCV_DIR

COLUMNS = ("open", "high", "low", "close", "volume")
PARTITION_FILE = "data_0.parquet"
STAGING_DIR = "staging"
PREVIOUS_DIR = "previous"
_LOCK_FILE = ".lock"

# renameat2(2): the working directory as the base, and swap both names.
_AT_FDCWD = -100
_RENAME_EXCHANGE = 2


class RefreshBusy(RuntimeError):
    """Another process is refreshing this warehouse."""


@dataclass(frozen=True)
class Written:
    """What a write changed: the partitions (years) rewritten, the bars in
    them, and where a replaced fund's previous copy now is."""

    years: tuple[int, ...]
    bars: int
    previous: Path | None = None


def empty_bars() -> pd.DataFrame:
    """No bars, in bars.load_frame's shape."""
    frame = pd.DataFrame(
        {
            "open": pd.Series(dtype="float64"),
            "high": pd.Series(dtype="float64"),
            "low": pd.Series(dtype="float64"),
            "close": pd.Series(dtype="float64"),
            "volume": pd.Series(dtype="int64"),
        }
    )
    frame.index = pd.DatetimeIndex([], name="timestamp", tz="UTC")
    return frame


def fund_dir(root: str | Path, ticker: str) -> Path:
    return Path(root) / OHLCV_DIR / f"ticker={ticker}"


def stored_years(root: str | Path, ticker: str) -> list[int]:
    """The years the fund has a partition for."""
    directory = fund_dir(root, ticker)
    if not directory.is_dir():
        return []
    years = []
    for child in directory.iterdir():
        name = child.name
        if child.is_dir() and name.startswith("year=") and name[5:].isdigit():
            years.append(int(name[5:]))
    return sorted(years)


def _files(root: str | Path, ticker: str, years: Iterable[int] | None) -> list[Path]:
    wanted = None if years is None else set(years)
    files: list[Path] = []
    for year in stored_years(root, ticker):
        if wanted is None or year in wanted:
            files.extend(sorted((fund_dir(root, ticker) / f"year={year}").glob("*.parquet")))
    return files


def _sql_list(paths: list[Path]) -> str:
    return "[" + ", ".join("'" + str(p).replace("'", "''") + "'" for p in paths) + "]"


def _memory_connection():
    import duckdb  # deferred: see the package docstring

    con = duckdb.connect()
    con.execute("SET TimeZone='UTC'")
    return con


def read_bars(root: str | Path, ticker: str, *, years: Iterable[int] | None = None) -> pd.DataFrame:
    """The fund's bars (in `years`, if given) straight from its files, in
    bars.load_frame's shape: a UTC DatetimeIndex named timestamp, ascending.
    Empty if it has none."""
    files = _files(root, ticker, years)
    if not files:
        return empty_bars()
    con = _memory_connection()
    try:
        frame = con.execute(
            "SELECT timestamp, open, high, low, close, volume "
            f"FROM read_parquet({_sql_list(files)}) ORDER BY timestamp"
        ).df()
    finally:
        con.close()
    frame = frame.set_index("timestamp")
    frame.index = pd.DatetimeIndex(frame.index, name="timestamp").tz_convert("UTC")
    return frame


def session_counts(root: str | Path, ticker: str) -> pd.Series:
    """Bars per session (Eastern date) the fund holds, oldest first. Empty
    if it has none. Reads only the timestamps."""
    files = _files(root, ticker, None)
    if not files:
        return pd.Series(dtype="int64", index=pd.Index([], dtype="object"))
    con = _memory_connection()
    try:
        rows = con.execute(
            "SELECT (timestamp AT TIME ZONE 'America/New_York')::DATE AS day, COUNT(*) "
            f"FROM read_parquet({_sql_list(files)}) GROUP BY day ORDER BY day"
        ).fetchall()
    finally:
        con.close()
    return pd.Series([n for _, n in rows], index=[day for day, _ in rows], dtype="int64")


def sessions_of(index: pd.DatetimeIndex) -> pd.DatetimeIndex:
    """Each bar's session, its Eastern date, as a naive midnight."""
    return index.tz_convert(EASTERN).tz_localize(None).normalize()


def validate_bars(frame: pd.DataFrame, ticker: str) -> None:
    """Refuse bars the lake could not hold, or a backtest could not use: a
    non-UTC or unsorted or repeated time, a missing column, a price that is
    not a positive number, a negative volume."""
    index = frame.index
    if not isinstance(index, pd.DatetimeIndex) or str(index.tz) != "UTC":
        raise DataValidationError(f"{ticker}: bars must be indexed by UTC timestamps")
    missing = [c for c in COLUMNS if c not in frame.columns]
    if missing:
        raise DataValidationError(f"{ticker}: bars missing column(s) {missing}")
    if len(frame) == 0:
        return
    if index.has_duplicates:
        raise DataValidationError(f"{ticker}: repeated timestamp {index[index.duplicated()][0]}")
    if not index.is_monotonic_increasing:
        raise DataValidationError(f"{ticker}: bars out of time order")
    prices = frame[["open", "high", "low", "close"]].to_numpy(dtype="float64")
    bad = ~(np.isfinite(prices) & (prices > 0)).all(axis=1)
    if bad.any():
        raise DataValidationError(f"{ticker}: a price that is not positive at {index[bad][0]}")
    volume = frame["volume"].to_numpy(dtype="float64")
    bad = ~(np.isfinite(volume) & (volume >= 0))
    if bad.any():
        raise DataValidationError(f"{ticker}: a negative or missing volume at {index[bad][0]}")


def merge_sessions(stored: pd.DataFrame, fresh: pd.DataFrame) -> pd.DataFrame:
    """`stored`, with every session `fresh` holds replaced by fresh's bars:
    a session is taken whole from one fetch or the other, never mixed."""
    if fresh.empty:
        return stored
    replaced = sessions_of(stored.index).isin(sessions_of(fresh.index).unique())
    parts = [part for part in (stored[~replaced], fresh) if len(part)]
    return pd.concat(parts).sort_index()


# --------------------------------------------------------------------
# Writing
# --------------------------------------------------------------------


def _fsync(path: Path) -> None:
    """Flush a file, or a directory's entries, to disk (POSIX)."""
    flags = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0) if path.is_dir() else os.O_RDONLY
    try:
        fd = os.open(path, flags)
    except OSError:
        return
    try:
        os.fsync(fd)
    except OSError:
        pass
    finally:
        os.close(fd)


def _write_year(directory: Path, frame: pd.DataFrame) -> None:
    """One year's bars as `directory`/data_0.parquet, sorted by time."""
    directory.mkdir(parents=True)
    path = directory / PARTITION_FILE
    rows = frame.rename_axis("timestamp").reset_index()[["timestamp", *COLUMNS]]
    rows["volume"] = rows["volume"].round().astype("int64")
    con = _memory_connection()
    try:
        con.register("rows", rows)
        target = str(path).replace("'", "''")
        con.execute(
            "COPY (SELECT timestamp, open, high, low, close, volume FROM rows ORDER BY timestamp) "
            f"TO '{target}' (FORMAT PARQUET, COMPRESSION ZSTD)"
        )
    finally:
        con.close()
    _fsync(path)
    _fsync(directory)


def _exchange(a: Path, b: Path) -> bool:
    """Swap two paths in one step. False where the platform or the
    filesystem has no call for it."""
    if not sys.platform.startswith("linux"):
        return False
    try:
        renameat2 = ctypes.CDLL(None, use_errno=True).renameat2
    except (OSError, AttributeError):
        return False
    renameat2.argtypes = (
        ctypes.c_int,
        ctypes.c_char_p,
        ctypes.c_int,
        ctypes.c_char_p,
        ctypes.c_uint,
    )
    renameat2.restype = ctypes.c_int
    if renameat2(_AT_FDCWD, os.fsencode(a), _AT_FDCWD, os.fsencode(b), _RENAME_EXCHANGE) == 0:
        return True
    code = ctypes.get_errno()
    if code in (errno.EINVAL, errno.ENOSYS, errno.EOPNOTSUPP):
        return False
    raise OSError(code, os.strerror(code), str(b))


def _swap(staged: Path, live: Path) -> bool:
    """Put `staged` at `live`. True if `live` existed, and its old content is
    now at `staged`."""
    if not live.exists():
        live.parent.mkdir(parents=True, exist_ok=True)
        os.rename(staged, live)
        _fsync(live.parent)
        return False
    if not _exchange(staged, live):
        aside = staged.with_name(staged.name + ".old")
        os.rename(live, aside)
        os.rename(staged, live)
        os.rename(aside, staged)
    _fsync(live.parent)
    _fsync(staged.parent)
    return True


def _work_dir(root: str | Path) -> Path:
    path = Path(root) / STAGING_DIR / f"work-{os.getpid()}-{time.time_ns()}"
    path.mkdir(parents=True)
    return path


def update_sessions(root: str | Path, ticker: str, fresh: pd.DataFrame) -> Written:
    """Write `fresh`'s sessions into the fund, replacing any it holds; every
    other stored bar stays. Each year touched is rewritten whole and swapped
    in at once."""
    validate_bars(fresh, ticker)
    if fresh.empty:
        return Written((), 0)
    fresh_years = set(fresh.index.year)
    # A replaced session's stored bars can lie in a year fresh's do not: an
    # extended session's evening is past midnight UTC.
    nearby = {
        year
        for year in stored_years(root, ticker)
        if min(fresh_years) - 1 <= year <= max(fresh_years) + 1
    }
    stored = read_bars(root, ticker, years=nearby)
    merged = merge_sessions(stored, fresh)
    validate_bars(merged, ticker)
    touched = sessions_of(stored.index).isin(sessions_of(fresh.index).unique())
    years = sorted(fresh_years | set(stored.index[touched].year))

    work = _work_dir(root)
    try:
        for year in years:
            rows = merged[merged.index.year == year]
            live = fund_dir(root, ticker) / f"year={year}"
            staged = work / f"year={year}"
            if rows.empty:
                if live.exists():
                    os.rename(live, staged)
                continue
            _write_year(staged, rows)
            _swap(staged, live)
    finally:
        shutil.rmtree(work, ignore_errors=True)
    return Written(tuple(years), int(sum((merged.index.year == y).sum() for y in years)))


def replace_fund(root: str | Path, ticker: str, frame: pd.DataFrame) -> Written:
    """Replace every bar the fund holds with `frame`'s, in one exchange; its
    previous directory is kept in staging/previous/."""
    validate_bars(frame, ticker)
    if frame.empty:
        raise DataValidationError(f"{ticker}: refusing to replace a fund's bars with none")
    work = _work_dir(root)
    try:
        staged = work / f"ticker={ticker}"
        for year, rows in frame.groupby(frame.index.year):
            _write_year(staged / f"year={year}", rows)
        previous = None
        if _swap(staged, fund_dir(root, ticker)):
            previous = Path(root) / STAGING_DIR / PREVIOUS_DIR / f"ticker={ticker}"
            if previous.exists():
                shutil.rmtree(previous)
            previous.parent.mkdir(parents=True, exist_ok=True)
            os.rename(staged, previous)
        return Written(tuple(sorted(set(frame.index.year))), len(frame), previous)
    finally:
        shutil.rmtree(work, ignore_errors=True)


# --------------------------------------------------------------------
# One refresh at a time
# --------------------------------------------------------------------


@contextmanager
def refresh_lock(root: str | Path) -> Iterator[None]:
    """Held for a whole refresh. A second process refuses (RefreshBusy)
    rather than waiting: the first is doing its work."""
    try:
        import fcntl
    except ImportError:  # not POSIX: nothing to lock with
        fcntl = None
    path = Path(root) / STAGING_DIR / _LOCK_FILE
    path.parent.mkdir(parents=True, exist_ok=True)
    # Closing the file releases the lock.
    with open(path, "a+", encoding="utf-8") as handle:
        if fcntl is not None:
            try:
                fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError as e:
                raise RefreshBusy(f"another refresh holds {path}") from e
        yield


def clean_staging(root: str | Path) -> int:
    """Remove what a refresh that was killed left in staging/; the previous
    copies stay. Call it holding refresh_lock. Returns how many it removed."""
    staging = Path(root) / STAGING_DIR
    if not staging.is_dir():
        return 0
    removed = 0
    for child in staging.iterdir():
        if child.name.startswith("work-"):
            shutil.rmtree(child, ignore_errors=True)
            removed += 1
    return removed


__all__ = [
    "COLUMNS",
    "PARTITION_FILE",
    "RefreshBusy",
    "Written",
    "clean_staging",
    "empty_bars",
    "fund_dir",
    "merge_sessions",
    "read_bars",
    "refresh_lock",
    "replace_fund",
    "session_counts",
    "sessions_of",
    "stored_years",
    "update_sessions",
    "validate_bars",
]
