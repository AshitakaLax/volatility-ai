"""
Which code a process is running -- answerable inside the image, which has no
.git (.dockerignore keeps it out), so `git rev-parse` there says nothing.

Two answers, each honest about what it is:

  commit   VAI_BUILD_COMMIT, when the image was built with it
           (`VAI_BUILD_COMMIT=$(git rev-parse --short HEAD) docker compose
           build`); None otherwise -- not a guess.
  code     a fingerprint of the Python this process can load: the project
           directories and cli.py, tests left out. Two processes print the
           same fingerprint exactly when they run the same code, which is the
           question the Live page asks of a trader and the web server it is
           read through -- so neither a test-only change nor a rebuilt page
           (which the trader never runs) makes them read as different.

Standard library only; engine/core is layer 0.
"""

from __future__ import annotations

import hashlib
import os
import sys
import time
from datetime import UTC, datetime
from functools import lru_cache
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]

# The engine's release version (what the web header and the shard list show).
# Bump it when cutting a release; the commit/code fingerprint below say which
# exact code is running, this says which release it belongs to.
ENGINE_VERSION = "1.0.0"
_SOURCES = ("engine", "research", "server", "fidelity_gateway", "tools")
_SKIPPED = {"__pycache__", "tests"}

# When this process started, near enough: when this module was first imported.
STARTED_AT = time.time()


@lru_cache(maxsize=1)
def code_fingerprint(root: Path = REPO_ROOT) -> str | None:
    """12 hex digits over every source file's path and bytes, in path order.
    None if there is nothing to fingerprint (a stripped install)."""
    files = [root / "cli.py"]
    for name in _SOURCES:
        directory = root / name
        if directory.is_dir():
            files.extend(
                path
                for path in directory.rglob("*.py")
                if not _SKIPPED & set(path.relative_to(root).parts)
            )
    digest = hashlib.sha256()
    found = False
    for path in sorted(set(files)):
        try:
            data = path.read_bytes()
        except OSError:
            continue
        found = True
        digest.update(path.relative_to(root).as_posix().encode())
        digest.update(b"\0")
        digest.update(data)
        digest.update(b"\0")
    return digest.hexdigest()[:12] if found else None


def identity() -> dict:
    """This process: its build and how long it has been up."""
    return {
        "version": ENGINE_VERSION,
        "commit": os.environ.get("VAI_BUILD_COMMIT") or None,
        "code": code_fingerprint(),
        "python": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
        "pid": os.getpid(),
        "started_at": datetime.fromtimestamp(STARTED_AT, UTC).isoformat(),
    }


__all__ = ["ENGINE_VERSION", "REPO_ROOT", "STARTED_AT", "code_fingerprint", "identity"]
