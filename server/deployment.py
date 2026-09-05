"""What is running, and where it came from.

--------------------------------------------------------------------
READ-ONLY, AND NARROW ABOUT IT

Everything here answers "which build is this". It touches no store, no
broker and no order path, and tests/unit/test_server_capability.py holds
it to that alongside the other modules.

The one thing it does that no other module does is run a subprocess, so
that is worth being explicit about: the argv is a fixed constant list,
`shell=False`, and NO caller input reaches it. There is no path from an
HTTP request to a command string.

--------------------------------------------------------------------
CONTAINER STATS ARE READ FROM cgroup, NOT INVENTED

A dashboard that shows "CPU 0%" because it could not measure anything is
worse than one that shows nothing: the first is a number someone will
act on. psutil is not a dependency of this project and adding one for a
status card is not worth it, so the numbers come from cgroup v2, which
is the only place they are actually true inside a container -- and
outside one they are reported as null, which is the honest answer.

The Raspberry Pi deployment runs under Docker and has these files; a
developer machine does not.
"""

from __future__ import annotations

import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

from fastapi import APIRouter

router = APIRouter(prefix="/api", tags=["deployment"])

# When this process started. Module import time is close enough to
# "deployed at" for a status card, and it needs no state.
STARTED_AT = time.time()

REPO_ROOT = Path(__file__).resolve().parent.parent


def _git(*args: str) -> str | None:
    """One git query, or None.

    Fixed argv, shell=False, no interpolation of anything a caller
    controls. A missing git, a missing repository and a timeout are all
    the same answer here: we do not know, so say so.
    """
    try:
        result = subprocess.run(
            ["git", *args],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    return result.stdout.strip() if result.returncode == 0 else None


def _read_int(path: str) -> int | None:
    try:
        text = Path(path).read_text(encoding="utf-8").strip()
    except OSError:
        return None
    # cgroup writes "max" for "no limit", which is not a number and must
    # not become one.
    return None if text == "max" else int(text) if text.isdigit() else None


def container_stats() -> dict[str, Any]:
    """Memory from cgroup v2, or nulls outside a container.

    CPU is deliberately absent rather than approximated. cgroup exposes
    cumulative usage in microseconds, and turning that into a percentage
    needs two samples over a known interval -- state this endpoint does
    not keep. A single-sample "CPU %" would be a fabrication.
    """
    used = _read_int("/sys/fs/cgroup/memory.current")
    limit = _read_int("/sys/fs/cgroup/memory.max")
    return {
        "memory_mb": round(used / 1_048_576, 1) if used is not None else None,
        "memory_limit_mb": round(limit / 1_048_576, 1) if limit is not None else None,
        "cpu_pct": None,
        "containerised": used is not None,
    }


@router.get("/deployment")
def deployment() -> dict[str, Any]:
    """Build identity and process health."""
    status = _git("status", "--porcelain")
    return {
        "git_commit": _git("rev-parse", "--short", "HEAD"),
        "git_branch": _git("rev-parse", "--abbrev-ref", "HEAD"),
        # None means "could not tell", which is different from False.
        # A card that showed a clean checkmark because git was missing
        # would be asserting something it does not know.
        "git_dirty": None if status is None else bool(status),
        "started_at": STARTED_AT,
        "uptime_seconds": round(time.time() - STARTED_AT, 1),
        "python": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
        "pid": os.getpid(),
        **container_stats(),
    }


__all__ = ["container_stats", "deployment", "router"]
