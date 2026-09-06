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
"""

from __future__ import annotations

import contextlib
import json
import logging
import os
from pathlib import Path
from typing import Any

logger = logging.getLogger("Optimizer")

_ROOT = Path(__file__).resolve().parent.parent


def directory() -> Path:
    """Where runs are stored. Overridable for tests and deployments."""
    configured = os.environ.get("VAI_RUN_HISTORY_DIR")
    return Path(configured) if configured else _ROOT / "output" / "runs"


# A ceiling rather than unbounded growth. Each report is a few hundred
# KB with its executions, and a machine left running for months should
# not quietly fill a disk with sweeps nobody will look at again.
MAX_RUNS = 200


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
        _prune(target)
        return path
    except OSError as exc:
        logger.warning(f"Could not persist run {run_id}: {exc}")
        return None


def _prune(target: Path) -> None:
    """Keep the newest MAX_RUNS files."""
    files = sorted(target.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
    for stale in files[MAX_RUNS:]:
        # A file that cannot be removed is not worth failing a save
        # over: the run itself is already written.
        with contextlib.suppress(OSError):
            stale.unlink()


def load_all() -> list[dict[str, Any]]:
    """Every persisted run, newest first.

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
        if isinstance(loaded, dict) and loaded.get("run_id"):
            loaded.setdefault("saved_at", path.stat().st_mtime)
            out.append(loaded)
    return out


def load(run_id: str) -> dict[str, Any] | None:
    path = directory() / f"{run_id}.json"
    try:
        loaded = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    return loaded if isinstance(loaded, dict) else None


__all__ = ["MAX_RUNS", "directory", "load", "load_all", "save"]
