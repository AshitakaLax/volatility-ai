"""
One trading loop per state store, enforced.

--------------------------------------------------------------------
THE FAILURE THIS PREVENTS

Two live loops against the same account is not a degraded mode -- it is
duplicate orders. Both read the same ledger, both see the same grid
trigger, and both submit. src/duplicate_order_guard.py cannot help:
its decision_id is derived from the symbol, side and bar timestamp, so
two loops on the same bar compute the SAME id and each believes it is
the one submitting it.

It nearly happened here. A manually started loop was running while a
scheduled supervisor was waiting to start another at the open, both
pointed at paper_ledger.db. Nothing in the system would have objected.

--------------------------------------------------------------------
WHY A LOCK FILE AND NOT SQLITE'S OWN LOCKING

SQLite locks a transaction, not a session. Both loops would happily
interleave writes and each would be individually valid -- the database
would never notice anything was wrong, because at the database level
nothing is.

The lock is keyed on the STATE STORE path, not on the config or the
account, because the store is what the two processes would actually
corrupt. Two loops on different stores are two deployments and are
fine; two on one store are one deployment run twice.

--------------------------------------------------------------------
A STALE LOCK MUST NOT WEDGE THE SYSTEM

A machine that loses power mid-session leaves a lock behind. If that
blocked every future start, the lock would cause more downtime than the
problem it prevents -- and an operator who has to delete a file to start
trading will delete it reflexively, including on the day it was right.

So the holder's PID is recorded and checked. A lock whose process is
gone is stale and is taken over, with a line saying so. A lock whose
process is ALIVE is refused, naming the PID so the operator can look at
it rather than guess.
"""

from __future__ import annotations

import logging
import os
from pathlib import Path

from src.exceptions import ConfigurationError

logger = logging.getLogger("Optimizer")


class LockHeldError(ConfigurationError):
    """Another live process already owns this state store."""


def _process_alive(pid: int) -> bool:
    """Whether `pid` is a running process.

    Errs toward ALIVE on anything it cannot determine. A lock wrongly
    judged stale lets a second loop trade; a lock wrongly judged live
    only asks a human to look. Those costs are not symmetric.
    """
    if pid <= 0:
        return False
    if os.name == "nt":
        import subprocess

        try:
            out = subprocess.run(
                ["tasklist", "/FI", f"PID eq {pid}", "/NH"],
                capture_output=True,
                text=True,
                timeout=15,
            )
            return str(pid) in out.stdout
        except (OSError, subprocess.SubprocessError):
            return True
    try:
        os.kill(pid, 0)  # signal 0 tests existence without touching it
    except ProcessLookupError:
        return False
    except PermissionError:
        return True  # exists, owned by someone else
    except OSError:
        return True
    return True


class StateStoreLock:
    """Exclusive claim on one state store, for the life of a process.

    Use as a context manager. Releasing is best-effort on the way out:
    a crash leaves the file behind, and the staleness check above is
    what makes that recoverable rather than fatal.
    """

    def __init__(self, state_db: str) -> None:
        self.state_db = state_db
        self.path = Path(f"{state_db}.lock")
        self._held = False

    def acquire(self) -> StateStoreLock:
        if self.path.exists():
            holder = self._read_holder()
            if holder is not None and _process_alive(holder):
                raise LockHeldError(
                    f"Another live loop (pid {holder}) already owns "
                    f"{self.state_db}. Two loops on one store submit DUPLICATE "
                    "ORDERS -- the duplicate-order guard cannot catch it, because "
                    "both derive the same decision_id from the same bar. Stop that "
                    f"process, or point --state-db somewhere else.\n"
                    f"Lock file: {self.path}"
                )
            logger.warning(
                f"Taking over a stale lock on {self.state_db} "
                f"(pid {holder} is gone). A previous run did not exit cleanly."
            )

        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(str(os.getpid()), encoding="utf-8")
        self._held = True
        return self

    def _read_holder(self) -> int | None:
        try:
            return int(self.path.read_text(encoding="utf-8").strip())
        except (OSError, ValueError):
            # Unreadable or garbage. Treated as stale rather than as a
            # live holder: an empty file is what a crash mid-write
            # leaves, and refusing forever over it is the wedge this
            # class is written to avoid.
            return None

    def release(self) -> None:
        if not self._held:
            return
        try:
            if self._read_holder() == os.getpid():
                self.path.unlink(missing_ok=True)
        except OSError as exc:  # pragma: no cover - filesystem edge
            logger.warning(f"Could not remove {self.path}: {exc}")
        finally:
            self._held = False

    def __enter__(self) -> StateStoreLock:
        return self.acquire()

    def __exit__(self, *exc) -> None:
        self.release()
