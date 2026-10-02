"""Completed runs, kept on disk so history outlives the process.

--------------------------------------------------------------------
WHAT THIS DOES AND DOES NOT CHANGE

server/jobs.py states that a restart loses queued and running jobs, and
that this is acceptable for a single-operator tool. That stands. A
queued run is a few seconds of intent and resubmitting it is trivial.

A COMPLETED run is different: it is minutes of engine time, and it is
the thing a history view exists to compare against. Losing those on a
restart would make the feature useless the first time the server was
updated -- which, for a tool under active development, is daily.

So only completed runs are written, and only their REPORTS. No queue
state, no scheduler, no recovery of work in flight. The narrow version
of persistence, not a task queue.

--------------------------------------------------------------------
WHY JSON FILES RATHER THAN THE LEDGER STORE

The SQLite store belongs to a trading deployment and is opened read-only
by everything else in this server, deliberately. Writing backtest
results into it would give this process a reason to hold a writable
handle on the file a live loop is using, which is exactly the coupling
the read-only design exists to prevent.

One file per run under output/runs/. output/ is already git-ignored, so
nothing here can be committed by accident.

--------------------------------------------------------------------
NO RETENTION CAP

There used to be a 200-run ceiling. It silently evicted the oldest runs
as new ones landed -- a day of tuned sweeps pushed out a 170k-cell
brute-force study that history queries are supposed to be able to
compare against. Every completed run is now kept; the views that read
history query it (by fund, filtered and paged server-side) rather than
downloading it, so its size no longer has to be bounded for them.

--------------------------------------------------------------------
DERIVED FILES (output/runs/derived/)

`<id>.json` stays the source of truth and is never rewritten. Beside
it, three DERIVED files -- rebuilt from it whenever they are missing or
older than it, so deleting them is always safe:

  <id>.summary.json        the run with every fund's fills replaced by
                           `fills_count` -- what GET /runs/{id} serves.
  <id>.index.json          run-level fields once, then one slim row per
                           (fund, cell) -- what history queries read.
  <id>.<TICKER>.fills.npz  that fund's fills, columnar (server/fills.py).

They exist because the alternatives were parsing a ~100 MB archive on
every history request (20-28 s) or serving it whole.
"""

from __future__ import annotations

import json
import logging
import os
import threading
from collections import OrderedDict
from pathlib import Path
from typing import Any

from server import contract
from server.fills import FundFills, strip_report

logger = logging.getLogger("Optimizer")

_ROOT = Path(__file__).resolve().parent.parent

# The metrics a history row carries: what Run History ranks by, shows,
# and offers as filters (web/src/lib/filters.ts HISTORY_METRIC_FIELDS).
# A cell's other metrics stay in the archive and the run's own report.
HISTORY_METRICS = (
    "net_yield_pct",
    "cagr_pct",
    "worst_year_pct",
    "best_year_pct",
    "max_drawdown_pct",
    "return_over_drawdown",
    "sharpe_ratio",
    "sortino_ratio",
    "profit_factor",
    "win_rate_pct",
    "capital_velocity_index",
    "stuck_capital_value",
    "avg_hold_duration",
    "total_trades",
)

# Bumped when a derived file's layout changes, so old ones are rebuilt.
DERIVED_VERSION = 1


def directory() -> Path:
    """Where runs are stored. Overridable for tests and deployments."""
    configured = os.environ.get("VAI_RUN_HISTORY_DIR")
    return Path(configured) if configured else _ROOT / "output" / "runs"


def derived_directory() -> Path:
    return directory() / "derived"


def save(run_id: str, snapshot: dict[str, Any]) -> Path | None:
    """Persist one completed run. Failures are logged, never raised.

    A history feature must not be able to fail a backtest. If the disk
    is full or the directory is unwritable the run still completed and
    the caller still has its result in memory -- losing the archive copy
    is a strictly smaller problem than losing the run.
    """
    try:
        target = directory()
        target.mkdir(parents=True, exist_ok=True)
        path = target / f"{run_id}.json"
        # Written to a temporary name and moved, so a crash mid-write
        # cannot leave a half-parsed file that breaks the whole history
        # listing on the next start.
        staging = path.with_suffix(".json.tmp")
        staging.write_text(json.dumps(snapshot), encoding="utf-8")
        staging.replace(path)
    except OSError as exc:
        logger.warning(f"Could not persist run {run_id}: {exc}")
        return None
    # Derived files are a cache of the archive just written; failing to
    # build them now only means they are built on first read instead.
    try:
        _write_derived(run_id, snapshot, path.stat().st_mtime)
    except Exception as exc:
        logger.warning(f"Could not build derived files for run {run_id}: {exc}")
    return path


# ---------------------------------------------------------------------
# Derived files
# ---------------------------------------------------------------------

# One lock per run for building its derived files (a big archive takes a
# couple of seconds to parse, and two requests must not build it twice),
# and one short lock for the in-memory caches. Never a single global lock
# held across a whole warm-up: that would stall every /runs/{id} behind it.
_cache_lock = threading.Lock()
_run_locks: dict[str, threading.Lock] = {}


def _run_lock(run_id: str) -> threading.Lock:
    with _cache_lock:
        return _run_locks.setdefault(run_id, threading.Lock())


def _summary_path(run_id: str) -> Path:
    return derived_directory() / f"{run_id}.summary.json"


def _index_path(run_id: str) -> Path:
    return derived_directory() / f"{run_id}.index.json"


def _fills_path(run_id: str, ticker: str) -> Path:
    return derived_directory() / f"{run_id}.{ticker}.fills.npz"


def _atomic_json(path: Path, value: Any) -> None:
    staging = path.with_name(path.name + ".tmp")
    staging.write_text(json.dumps(value, separators=(",", ":")), encoding="utf-8")
    staging.replace(path)


def _write_derived(run_id: str, raw: dict[str, Any], saved_at: float) -> None:
    """Build all three derived files for one run from its full snapshot."""
    run = contract.run(dict(raw))
    run.setdefault("saved_at", saved_at)
    report = run.get("report") if isinstance(run.get("report"), dict) else None
    target = derived_directory()
    target.mkdir(parents=True, exist_ok=True)

    funds = (report or {}).get("funds") or {}
    for ticker, fund in funds.items():
        if not isinstance(fund, dict):
            continue
        # Per fund: fills a converter cannot read must not make the whole
        # run -- its summary and history rows -- unloadable.
        try:
            FundFills.from_fills(fund.get("fills") or []).save(_fills_path(run_id, ticker))
        except (KeyError, TypeError, ValueError) as exc:
            logger.warning(f"Run {run_id} {ticker}: fills not indexed ({exc!r})")

    summary = {**run, "report": strip_report(report), "derived_version": DERIVED_VERSION}
    _atomic_json(_summary_path(run_id), summary)

    rows: list[dict[str, Any]] = []
    for ticker, fund in funds.items():
        if not isinstance(fund, dict):
            continue
        count = (fund.get("bars") or {}).get("count")
        for rank, cell in enumerate(fund.get("cells") or []):
            metrics = cell.get("m") or {}
            rows.append(
                {
                    "ticker": ticker,
                    "grid": cell.get("grid"),
                    "target": cell.get("target"),
                    "params": cell.get("params") or {},
                    "m": {key: metrics[key] for key in HISTORY_METRICS if key in metrics},
                    # Where the ENGINE ranked this cell; 0 is its own pick.
                    "rank": rank,
                    "bars": count,
                }
            )
    meta = {key: value for key, value in (report or {}).items() if key not in ("id", "funds")}
    meta["saved_at"] = run.get("saved_at", saved_at)
    _atomic_json(
        _index_path(run_id),
        {
            "id": run_id,
            "derived_version": DERIVED_VERSION,
            "run": meta if report else None,
            "rows": rows,
        },
    )


def _archive_path(run_id: str) -> Path:
    return directory() / f"{run_id}.json"


def _derived_fresh(run_id: str, archive_mtime: float) -> bool:
    for path in (_summary_path(run_id), _index_path(run_id)):
        try:
            if path.stat().st_mtime < archive_mtime:
                return False
        except OSError:
            return False
    try:
        version = json.loads(_index_path(run_id).read_text(encoding="utf-8")).get("derived_version")
    except (OSError, ValueError):
        return False
    return version == DERIVED_VERSION


def ensure_derived(run_id: str) -> bool:
    """Build the derived files for `run_id` if missing or stale. False if
    the run has no readable archive."""
    archive = _archive_path(run_id)
    try:
        mtime = archive.stat().st_mtime
    except OSError:
        return False
    with _run_lock(run_id):
        if _derived_fresh(run_id, mtime):
            return True
        try:
            raw = json.loads(archive.read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            logger.warning(f"Skipping unreadable run file {archive.name}: {exc}")
            return False
        if not isinstance(raw, dict):
            return False
        try:
            _write_derived(run_id, raw, mtime)
        except Exception as exc:
            logger.warning(f"Could not build derived files for run {run_id}: {exc}")
            return False
        return True


def load_summary(run_id: str) -> dict[str, Any] | None:
    """One run without its fills -- each fund carries `fills_count`."""
    if not ensure_derived(run_id):
        return None
    try:
        summary = json.loads(_summary_path(run_id).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    summary.pop("derived_version", None)
    return summary


_FILLS_CACHE: OrderedDict[tuple[str, float], FundFills] = OrderedDict()
_FILLS_CACHE_SIZE = 3


def load_fills(run_id: str, ticker: str) -> FundFills | None:
    """One fund's fills, columnar. The few most recent are kept in memory:
    a chart and a trade log page through the same run in quick succession."""
    if not ensure_derived(run_id):
        return None
    path = _fills_path(run_id, ticker)
    try:
        mtime = path.stat().st_mtime
    except OSError:
        return None
    key = (str(path), mtime)
    with _cache_lock:
        if key in _FILLS_CACHE:
            _FILLS_CACHE.move_to_end(key)
            return _FILLS_CACHE[key]
    loaded = FundFills.load(path)
    with _cache_lock:
        _FILLS_CACHE[key] = loaded
        while len(_FILLS_CACHE) > _FILLS_CACHE_SIZE:
            _FILLS_CACHE.popitem(last=False)
    return loaded


# Keyed by (history directory, run id): tests and tools point the store at
# other directories, and a run id is only unique within one of them.
_INDEX_CACHE: dict[tuple[str, str], tuple[float, dict[str, Any]]] = {}
# Changes whenever the set of indexed runs (or any run's archive) does, so
# callers can cache work derived from index_entries() against it.
_INDEX_GENERATION = 0


def index_generation() -> int:
    return _INDEX_GENERATION


def index_entries() -> list[dict[str, Any]]:
    """Every run's index entry, newest first. Cached per archive mtime, so
    a call after the first re-reads only runs written since."""
    target = directory()
    if not target.is_dir():
        return []
    root = str(target)
    seen: dict[str, float] = {}
    for path in target.glob("*.json"):
        try:
            seen[path.stem] = path.stat().st_mtime
        except OSError:
            continue
    global _INDEX_GENERATION
    with _cache_lock:
        stale_keys = {key for key in _INDEX_CACHE if key[0] != root or key[1] not in seen}
        for stale in stale_keys:
            del _INDEX_CACHE[stale]
        if stale_keys:
            _INDEX_GENERATION += 1
        cached_now = {key[1]: value for key, value in _INDEX_CACHE.items()}
    out: list[tuple[float, dict[str, Any]]] = []
    for run_id, mtime in seen.items():
        cached = cached_now.get(run_id)
        if cached is None or cached[0] != mtime:
            if not ensure_derived(run_id):
                continue
            try:
                entry = json.loads(_index_path(run_id).read_text(encoding="utf-8"))
            except (OSError, ValueError):
                continue
            cached = (mtime, entry)
            with _cache_lock:
                _INDEX_CACHE[(root, run_id)] = cached
                _INDEX_GENERATION += 1
        if cached[1].get("run") is not None:
            out.append((mtime, cached[1]))
    out.sort(key=lambda item: item[0], reverse=True)
    return [entry for _, entry in out]


def warm() -> int:
    """Build every missing derived file now (e.g. at startup, in a thread),
    so the first history query does not pay for it. Returns runs indexed."""
    return len(index_entries())


def load_all() -> list[dict[str, Any]]:
    """Every persisted run, newest first -- a LISTING, for run history.

    Every fund's `fills` and `equity` are stripped here explicitly, not
    left to contract.run(detail=False): that only translates a LEGACY
    `report` blob, so a run saved since the contract was condensed has
    no `report` key to translate and passes through untouched -- full
    trade blotter included. A single brute-force sweep's best fund can
    carry tens of thousands of fills; nothing that lists runs reads
    them, and shipping them here once blew up this endpoint's response
    to 100+ MB for 200 runs. load() returns a single run in full.

    An unreadable file is SKIPPED with a warning rather than failing the
    listing. One corrupt run must not hide the other hundred -- and the
    atomic write above means a corrupt file should only ever come from
    outside this module anyway.
    """
    target = directory()
    if not target.is_dir():
        return []

    out: list[dict[str, Any]] = []
    for path in sorted(target.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True):
        try:
            loaded = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            logger.warning(f"Skipping unreadable run file {path.name}: {exc}")
            continue
        if isinstance(loaded, dict) and (loaded.get("id") or loaded.get("run_id")):
            loaded.setdefault("saved_at", path.stat().st_mtime)
            # A run archived before the contract was condensed is read in
            # the new shape; the file itself is left as it was written.
            translated = contract.run(loaded, detail=False)
            for fund in ((translated.get("report") or {}).get("funds") or {}).values():
                fund["fills"] = []
                fund["equity"] = {"dates": [], "equity": []}
            out.append(translated)
    return out


def load(run_id: str) -> dict[str, Any] | None:
    path = directory() / f"{run_id}.json"
    try:
        loaded = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    if not isinstance(loaded, dict):
        return None
    loaded.setdefault("saved_at", path.stat().st_mtime)
    return contract.run(loaded)


__all__ = [
    "HISTORY_METRICS",
    "derived_directory",
    "directory",
    "ensure_derived",
    "index_entries",
    "index_generation",
    "load",
    "load_all",
    "load_fills",
    "load_summary",
    "save",
    "warm",
]
