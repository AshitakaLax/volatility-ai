#!/usr/bin/env python
"""Keep every outside series current: the files a live strategy reads, and
the warehouse's external lake.

    python tools/refresh_external.py                      # every series, once
    python tools/refresh_external.py --provider ofr cftc  # some of them
    python tools/refresh_external.py --dry-run            # fetch and compare; write nothing
    python tools/refresh_external.py --daily 20:45 07:30  # now, then at those Eastern times
    python tools/refresh_external.py --status             # what is on disk, and how old
    python tools/refresh_external.py --list               # the registry

docker-compose.yml's `market-inputs` service runs the --daily form. It needs
no keys: every source in research/ml/sources.py is a public endpoint.
tools/fetch_market_inputs.py is the same download by hand, without the
checks or the lake.

--------------------------------------------------------------------
WHAT A RUN DOES

1. EVERY SERIES IS FETCHED WHOLE, four at a time, and written to
   data/external/<provider>_<key>.csv (--dir, or VAI_EXTERNAL_DIR) only
   when it passes: at least KEEP_ROWS of the rows the stored file has, and
   a last stamp no earlier than the stored one. A source that answers with
   half its history, or with yesterday's file again after today's was
   stored, is KEPT as it was and reported. A bar still forming (Yahoo
   serves today's while the session trades) is dropped first, so a midday
   run never stores a midday price as a close. Each file is replaced in
   one rename, so a strategy starting up reads the old file or the new one.
2. manifest.json is brought up to date for what was written.
3. THE EXTERNAL LAKE (warehouse/external/) is rewritten from the directory
   when anything changed, through an in-memory DuckDB: the catalog has one
   writer, and the server holds it while a sweep records. The
   external_series rows are upserted afterwards if the catalog is free,
   and reported as waiting when it is not; the next run brings them up.
4. THE RISK GOVERNOR'S READING for the next session is printed
   (research/strategies/risk_governor.py), with any warning that has gone
   stale: that line is how an operator sees a source quietly stop.
5. THE FOMC CALENDAR is read from the Federal Reserve's page, written to
   fomc_calendar.csv, and compared with the list the strategies' event-day
   sizing reads (engine/data/fomc_calendar.py). A scheduled meeting that
   list lacks is reported on every run until someone adds it.

A failed source is one line, not a failed run; the run fails (and a daily
one is tried again within the hour) only when a series the governor's core
signals read could not be fetched, or when the lake could not be written.

--------------------------------------------------------------------
WHEN

20:45 Eastern has the day's closes from CBOE and Yahoo, and FRED's from the
day before; 07:30 picks up what was posted overnight (the OFR stress index,
SqueezeMetrics, the SF Fed) before a session's process starts and reads
them. The governor reads a value only once it is stamped readable, so a
late file costs a day's freshness, never correctness.
"""

from __future__ import annotations

import argparse
import json
import os
import signal
import sys
import time
from collections.abc import Callable, Iterable
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta
from datetime import time as clock_time
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

import pandas as pd  # noqa: E402

from engine.core.trading_calendar import EASTERN, is_session, next_session  # noqa: E402
from research.ml import sources  # noqa: E402
from research.strategies.risk_governor import (  # noqa: E402
    CORE_SIGNALS,
    SIGNALS,
    RiskGovernor,
    external_directory,
)

WORKERS = 4  # as tools/fetch_market_inputs.py: more is how a free service starts refusing
KEEP_ROWS = 0.9
RETRY_SECONDS = 3600
DEFAULT_TIMES = ("20:45", "07:30")
FOMC_FILE = "fomc_calendar.csv"
# The series a missing fetch of fails the run for.
REQUIRED = frozenset(key for name in CORE_SIGNALS for key in SIGNALS[name].inputs)


@dataclass(frozen=True)
class Outcome:
    key: str
    status: str  # new | updated | unchanged | kept | failed
    detail: str = ""
    entry: dict | None = None  # the manifest row, when a file was written

    def line(self, dry_run: bool = False) -> str:
        status = self.status
        if dry_run and status in ("new", "updated"):
            status = f"would be {status}"
        return f"[external] {self.key:<24} {status:<10} {self.detail}"


# --------------------------------------------------------------------
# One series
# --------------------------------------------------------------------


def as_csv(frame: pd.DataFrame) -> str:
    return frame.to_csv(index=False)


def last_stamp(text: str) -> pd.Timestamp | None:
    """The newest stamp in a stored file, or None for one with no rows."""
    lines = [line for line in text.splitlines()[1:] if line.strip()]
    if not lines:
        return None
    return pd.Timestamp(lines[-1].split(",", 1)[0]).tz_convert("UTC")


def judge(stored: str | None, fresh: pd.DataFrame) -> tuple[str, str]:
    """(status, detail) for a fetched series against the stored file's text."""
    newest = pd.Timestamp(fresh["timestamp"].iloc[-1]).tz_convert("UTC")
    span = f"{len(fresh):,} rows to {newest:%Y-%m-%d}"
    if stored is None:
        return "new", span
    if as_csv(fresh) == stored:
        return "unchanged", span
    had = max(0, len(stored.splitlines()) - 1)
    if len(fresh) < KEEP_ROWS * had:
        return "kept", f"fetched {len(fresh):,} rows against {had:,} stored"
    was = last_stamp(stored)
    if was is not None and newest < was:
        return "kept", f"fetched to {newest:%Y-%m-%d}, stored to {was:%Y-%m-%d}"
    return "updated", span


def write_atomic(path: Path, text: str) -> None:
    """The whole file, or the old one: written beside it and renamed over."""
    partial = path.with_name(f".{path.name}.partial")
    with open(partial, "w", encoding="utf-8", newline="") as handle:
        handle.write(text)
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(partial, path)


def settled(source: sources.Source, frame: pd.DataFrame, now: datetime) -> pd.DataFrame:
    """`frame` without a bar that is still forming. A same-day source
    stamps a session at its close, and Yahoo serves today's bar while the
    session trades (futures and currencies, all night): a row stamped
    later than `now` holds a price from the middle of its day. A lagged
    source's stamps run ahead of the clock by design and are left alone."""
    if source.lag > timedelta(0):
        return frame
    return frame[pd.to_datetime(frame["timestamp"], utc=True) <= now].reset_index(drop=True)


def refresh_one(
    source: sources.Source, directory: Path, fetch: Callable, dry_run: bool, now: datetime
) -> Outcome:
    key = sources.manifest_key(source)
    try:
        frame = settled(source, fetch(source), now)
    except sources.SourceUnavailable as exc:
        return Outcome(key, "failed", str(exc)[:160])
    except Exception as exc:  # a parse error in one source is still just one source
        return Outcome(key, "failed", f"{type(exc).__name__}: {exc}"[:160])
    if frame.empty:
        return Outcome(key, "failed", "no settled rows")
    path = directory / source.filename
    stored = path.read_text(encoding="utf-8") if path.exists() else None
    status, detail = judge(stored, frame)
    if status in ("new", "updated") and not dry_run:
        write_atomic(path, as_csv(frame))
    entry = sources.manifest_entry(source, frame) if status in ("new", "updated") else None
    return Outcome(key, status, detail, entry)


def refresh_series(
    wanted: Iterable[sources.Source],
    directory: Path,
    *,
    fetch: Callable = sources.fetch,
    dry_run: bool = False,
    workers: int = WORKERS,
    now: datetime | None = None,
    report: Callable[[str], None] = print,
) -> list[Outcome]:
    """Fetch and store every source in `wanted`; one outcome each. Only
    what changed, was refused or failed is reported line by line."""
    wanted = list(wanted)
    now = now or datetime.now(UTC)
    if not dry_run:
        directory.mkdir(parents=True, exist_ok=True)
    with ThreadPoolExecutor(max_workers=max(1, workers)) as pool:
        outcomes = list(
            pool.map(lambda s: refresh_one(s, directory, fetch, dry_run, now), wanted)
        )
    for outcome in outcomes:
        if outcome.status != "unchanged":
            report(outcome.line(dry_run))
    written = {o.key: o.entry for o in outcomes if o.entry is not None}
    if written and not dry_run:
        update_manifest(directory, written)
    return outcomes


def update_manifest(directory: Path, entries: dict[str, dict]) -> None:
    """Merged, not overwritten: a --provider run keeps every other series' row."""
    path = directory / "manifest.json"
    manifest: dict = {}
    if path.exists():
        try:
            manifest = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            manifest = {}
    manifest.update(entries)
    write_atomic(path, json.dumps(manifest, indent=2, sort_keys=True))


# --------------------------------------------------------------------
# The lake
# --------------------------------------------------------------------


def write_lake(root: Path, directory: Path) -> str:
    """The external lake from `directory`, without the catalog's writer;
    then the external_series rows if the catalog is free. A line to report."""
    try:
        import duckdb
    except ImportError as exc:
        return f"lake skipped: {exc} (pip install -r requirements-warehouse.txt)"
    from engine.warehouse import ingest
    from engine.warehouse.connection import MARKET_DATA_DB, open_warehouse

    con = duckdb.connect()
    try:
        result = ingest.ingest_external_series(con, root, directory, dimension=False)
    finally:
        con.close()
    line = f"lake: {result['series']} series, {result['rows']:,} rows into {root / 'external'}"
    if not (Path(root) / MARKET_DATA_DB).exists():
        return f"{line}; no catalog yet (tools/build_warehouse.py --init makes one)"
    try:
        catalog = open_warehouse(root)
    except Exception as exc:  # held by the server while a sweep records
        return f"{line}; external_series rows are waiting ({type(exc).__name__}: catalog in use)"
    try:
        ingest.upsert_external_series(catalog, result["dimension"])
    except Exception as exc:  # no such table: a catalog made before the external lake
        return f"{line}; external_series rows not written ({type(exc).__name__}: {exc})"[:300]
    finally:
        catalog.close()
    return f"{line}; external_series rows current"


# --------------------------------------------------------------------
# What an operator needs to see
# --------------------------------------------------------------------


def governor_line(directory: Path, session: date) -> str:
    """The core governor's reading for `session`, from what is on disk."""
    try:
        reading = RiskGovernor.from_directory(directory).reading(session)
    except Exception as exc:
        return f"governor: no reading for {session} ({exc})"[:300]
    state = "new buying PAUSED" if reading.paused else "buying as usual"
    raised = ", ".join(reading.raised) or "none"
    line = (
        f"governor for {session}: {reading.votes} of {reading.known} warnings raised "
        f"({raised}); {state}"
    )
    if reading.stale:
        line += f"; STALE, casting no vote: {', '.join(reading.stale)}"
    return line


def fomc_lines(directory: Path, today: date, fetch: Callable[[], list[date]]) -> list[str]:
    """Store the Federal Reserve's meeting calendar, and name the scheduled
    decision days the engine's own list lacks."""
    try:
        published = fetch()
    except Exception as exc:
        return [f"FOMC calendar not fetched: {exc}"[:300]]
    text = "date\n" + "".join(f"{day.isoformat()}\n" for day in published)
    path = directory / FOMC_FILE
    if not path.exists() or path.read_text(encoding="utf-8") != text:
        write_atomic(path, text)
    try:
        from engine.data.fomc_calendar import FOMC_DECISION_DATES as known
    except Exception as exc:
        return [f"FOMC calendar stored; the engine's list could not be read ({exc})"]
    first = min(known)
    lacking = [day for day in published if day >= first and day not in known]
    if not lacking:
        return [f"FOMC calendar: the engine has every scheduled meeting to {max(published)}"]
    passed = [day for day in lacking if day < today]
    ahead = [day for day in lacking if day >= today]
    lines = [
        f"FOMC calendar: the engine's list ends {max(known)} and lacks "
        f"{len(lacking)} scheduled decision day(s); event-day sizing is off on them"
    ]
    if passed:
        lines.append(f"  already passed: {', '.join(map(str, passed))}")
    if ahead:
        lines.append(f"  next: {', '.join(map(str, ahead[:8]))}")
    return lines


def status_lines(directory: Path, now: datetime) -> list[str]:
    """Every series in the registry: its newest stamp on disk, and its age."""
    lines = []
    for source in sources.registry():
        path = directory / source.filename
        key = sources.manifest_key(source)
        if not path.exists():
            lines.append(f"{key:<24} missing")
            continue
        newest = last_stamp(path.read_text(encoding="utf-8"))
        if newest is None:
            lines.append(f"{key:<24} empty")
            continue
        age = (now - newest).total_seconds() / 86400
        mark = "  governor" if key in REQUIRED else ""
        lines.append(f"{key:<24} to {newest:%Y-%m-%d %H:%M}Z  {age:6.1f} days old{mark}")
    return lines


# --------------------------------------------------------------------
# A run, and the daily loop
# --------------------------------------------------------------------


def upcoming_session(now: datetime) -> date:
    """The session a process started at `now` would trade: today before the
    close on a session day, else the next one."""
    local = now.astimezone(EASTERN)
    today = local.date()
    if is_session(today) and local.time() < clock_time(16, 0):
        return today
    return next_session(today)


def run_once(
    wanted: list[sources.Source],
    directory: Path,
    root: Path | None,
    *,
    now: datetime,
    dry_run: bool = False,
    fetch: Callable = sources.fetch,
    fomc: Callable[[], list[date]] | None = sources.fetch_fomc_decision_dates,
    lake: Callable[[Path, Path], str] = write_lake,
    report: Callable[[str], None] = print,
) -> bool:
    """One refresh. True unless a governor input failed or the lake did."""
    outcomes = refresh_series(
        wanted, directory, fetch=fetch, dry_run=dry_run, now=now, report=report
    )
    counts: dict[str, int] = {}
    for outcome in outcomes:
        counts[outcome.status] = counts.get(outcome.status, 0) + 1
    summary = ", ".join(f"{n} {status}" for status, n in sorted(counts.items()))
    report(f"[external] {len(outcomes)} series: {summary}")
    ok = not any(o.status == "failed" and o.key in REQUIRED for o in outcomes)
    if dry_run:
        return ok
    if root is not None and any(o.status in ("new", "updated") for o in outcomes):
        try:
            report(f"[external] {lake(root, directory)}")
        except Exception as exc:
            report(f"[external] lake NOT written: {type(exc).__name__}: {exc}"[:300])
            ok = False
    report(f"[external] {governor_line(directory, upcoming_session(now))}")
    if fomc is not None:
        for line in fomc_lines(directory, now.astimezone(EASTERN).date(), fomc):
            report(f"[external] {line}")
    return ok


def next_run(now: datetime, times: Iterable[clock_time]) -> datetime:
    """The next of `times` (Eastern wall clock) after `now`."""
    local = now.astimezone(EASTERN)
    candidates = []
    for at in times:
        candidate = datetime.combine(local.date(), at, tzinfo=EASTERN)
        if candidate <= local:
            candidate = datetime.combine(local.date() + timedelta(days=1), at, tzinfo=EASTERN)
        candidates.append(candidate)
    return min(candidates)


def run_daily(
    times: list[clock_time],
    once: Callable[[], bool],
    *,
    now: Callable[[], datetime] = lambda: datetime.now(UTC),
    sleep: Callable[[float], None] = time.sleep,
    report: Callable[[str], None] = print,
    rounds: int | None = None,
) -> None:
    """Run now, then at each of `times` every day. A run that failed is
    tried again within the hour, never later than the next scheduled one.
    `rounds` ends the loop after that many runs (tests)."""
    done = 0
    while rounds is None or done < rounds:
        ok = once()
        done += 1
        wake = next_run(now(), times)
        if not ok:
            wake = min(wake, now() + timedelta(seconds=RETRY_SECONDS))
        report(f"[external] next run {wake.astimezone(EASTERN):%Y-%m-%d %H:%M %Z}")
        sleep(max(0.0, (wake - now()).total_seconds()))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--dir",
        type=Path,
        default=None,
        help="where the series are kept (default: VAI_EXTERNAL_DIR, else data/external/)",
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=None,
        help="warehouse directory (default: VAI_WAREHOUSE_DIR, else warehouse/)",
    )
    parser.add_argument("--no-lake", action="store_true", help="write the files only")
    parser.add_argument("--provider", nargs="+", help="only these providers")
    parser.add_argument("--category", nargs="+", help="only these categories")
    parser.add_argument("--dry-run", action="store_true", help="fetch and compare, write nothing")
    parser.add_argument(
        "--daily",
        nargs="*",
        metavar="HH:MM",
        help=f"run now, then daily at these Eastern times (default: {' '.join(DEFAULT_TIMES)})",
    )
    parser.add_argument("--status", action="store_true", help="what is on disk, and how old")
    parser.add_argument("--list", action="store_true", help="the registry")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    wanted = sources.registry()
    if args.provider:
        names = {p.lower() for p in args.provider}
        unknown = sorted(names - {s.provider for s in wanted})
        if unknown:
            parser.error(f"no such provider: {', '.join(unknown)}")
        wanted = [s for s in wanted if s.provider in names]
    if args.category:
        names = {c.lower() for c in args.category}
        wanted = [s for s in wanted if s.category in names]
    if args.list:
        for source in wanted:
            print(
                f"{sources.manifest_key(source):<24} {source.category:<13} "
                f"lag {source.lag.total_seconds() / 86400:5.2f}d  {source.description}"
            )
        print(f"\n{len(wanted)} series")
        return 0
    directory = external_directory(args.dir)
    if args.status:
        now = datetime.now(UTC)
        print("\n".join(status_lines(directory, now)))
        print(governor_line(directory, upcoming_session(now)))
        return 0
    times = None
    if args.daily is not None:
        try:
            times = [datetime.strptime(t, "%H:%M").time() for t in (args.daily or DEFAULT_TIMES)]
        except ValueError:
            parser.error(f"--daily wants HH:MM times, got {args.daily!r}")

    root = None
    if not args.no_lake:
        from engine.warehouse.bars import warehouse_root

        root = args.root or warehouse_root()

    def once() -> bool:
        started = datetime.now(UTC)
        print(
            f"[external] {started.astimezone(EASTERN):%Y-%m-%d %H:%M %Z} -- {len(wanted)} series"
            f" into {directory}{' (dry run: nothing is written)' if args.dry_run else ''}"
        )
        ok = run_once(wanted, directory, root, now=started, dry_run=args.dry_run)
        seconds = (datetime.now(UTC) - started).total_seconds()
        print(f"[external] done in {seconds:.0f}s{'' if ok else '; FAILED (see above)'}")
        return ok

    if times is None:
        return 0 if once() else 1

    def stop(signum, frame):  # PID 1 in a container: SIGTERM has no default action
        raise SystemExit(0)

    signal.signal(signal.SIGTERM, stop)
    run_daily(times, once)
    return 0


if __name__ == "__main__":
    sys.exit(main())
