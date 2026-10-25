"""
Operator commands for one live deployment, kept as files.

--------------------------------------------------------------------
WHY THE TRADING PROCESS APPLIES THEM

The web server and the trading loop are different processes in different
containers, and the loop is the only thing that may write its ledger: it
holds the circuit breaker, the algorithm and the book in memory. A change
written into the ledger behind its back is one it does not see until it
next starts -- it reads the halt once, at startup, which is how the Live
page's old halt came to say "halted" while the loop kept buying. So the web
server writes an INTENT here, and the trading process applies it on its own
thread, between ticks, through the same objects it trades with
(engine/trading/operator_control.py).

Files rather than a socket: nothing listens inside the process that places
orders (the reasoning server/live.py records for its own polling), a queued
command survives either side restarting, and the directory is its own audit
trail.

--------------------------------------------------------------------
LAYOUT -- one directory per deployment, a volume both containers mount

  inbox/<ns>-<id>.json      queued, by the server
  claimed/<ns>-<id>.json    taken by the trader, which then writes
  results/<id>.json         applied / rejected / superseded / expired
  cancelled/<ns>-<id>.json  withdrawn by the server before a claim
  desired.json              whether sessions should run; the trader writes it
  status.json               what the trader is doing, rewritten as it works
  bars/<session>.jsonl      the minute bars the trader traded on
  fills/<session>.jsonl     every fill it booked, with its price
  bridge/                   a Fidelity deployment's bridge host (fidelity_gateway/
                            bridge/host.py): its own inbox, status.json and
                            events/<day>.jsonl -- the same layout, one level down

Every write is a temporary file renamed into place, so a reader sees a whole
file or none. Claim and cancel are both a rename OUT of inbox/, so exactly
one of them wins a race; the other finds the file gone.

--------------------------------------------------------------------
THE JOURNALS

One JSON line per bar and per fill, a file per session (its Eastern date),
the newest JOURNAL_SESSIONS kept. They are what the Live page draws its chart
and its trades from, because nothing else has them: the warehouse's bars are
not the feed the loop trades on and lag it by days, and the ledger keeps lots
but never what a sale fetched (record_lot_shares stores no price). Appended,
not renamed into place: a reader skips the one line that may be half
written.
"""

from __future__ import annotations

import json
import logging
import os
import re
import threading
import time
import uuid
from collections.abc import Callable
from dataclasses import asdict, dataclass, field
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

logger = logging.getLogger(__name__)

# What an operator can ask of a deployment. There is no liquidation command,
# deliberately: the loop sells a lot only at its target under the no-loss
# guard, or by the Ultimate family's two-key regime exit, and a forced sell
# that realises losses is not a thing to add so that a button can exist.
COMMAND_TYPES = (
    "pause_buys",
    "resume_buys",
    "disable",
    "enable",
    "switch_algorithm",
    "revert_algorithm",
    "rewarm",
    "reset_paper_ledger",
    # Read-only: a Fidelity deployment's bridge host checks the account
    # through the extension. Queued in its own inbox (bridge/), never a
    # trader's.
    "check_connection",
)

# When a command applies. "now" is the trader's next tick (or at once
# between sessions); "next_session" waits for the next session to start;
# "when_flat" waits until the deployment holds no lots and no orders.
TIMINGS = ("now", "next_session", "when_flat")

# A command no trader picked up in this long is expired rather than applied
# late: "pause now" applied tomorrow morning is a different instruction.
NOW_TTL_SECONDS = 10 * 60
LATER_TTL_SECONDS = 7 * 24 * 3600

# The outcomes a result file records.
FINAL_STATUSES = ("applied", "rejected", "superseded", "expired", "cancelled")

_MAX_REASON = 500
_MAX_OPERATOR = 80
_MAX_ARGS_BYTES = 16 * 1024
_ID = re.compile(r"^[0-9a-f]{12}$")
_LOCK = threading.Lock()

# The journals (module docstring), and how many sessions -- Eastern dates --
# each keeps. "events" is the bridge host's: connects, disconnects, sign-outs.
JOURNALS = ("bars", "fills", "events")
JOURNAL_SESSIONS = 10
_KEEP = {"events": 14}
_JOURNAL_FILE = re.compile(r"^\d{4}-\d{2}-\d{2}\.jsonl$")
_EASTERN = ZoneInfo("America/New_York")


class InvalidCommand(ValueError):
    """A command that cannot be queued as written."""


def _iso(seconds: float) -> str:
    return datetime.fromtimestamp(seconds, UTC).isoformat()


def _seconds(iso: str) -> float:
    return datetime.fromisoformat(iso).timestamp()


@dataclass(frozen=True)
class Command:
    """One operator instruction, validated when built."""

    id: str
    type: str
    reason: str
    operator: str
    created_at: str
    expires_at: str
    args: dict = field(default_factory=dict)
    timing: str = "now"
    client: str | None = None
    idempotency_key: str | None = None
    # Nanoseconds since the epoch at creation: the queue's order.
    seq: int = 0

    @classmethod
    def new(
        cls,
        type: str,
        *,
        reason: str,
        operator: str,
        args: dict | None = None,
        timing: str = "now",
        client: str | None = None,
        idempotency_key: str | None = None,
        now: float | None = None,
    ) -> Command:
        now = time.time() if now is None else now
        ttl = NOW_TTL_SECONDS if timing == "now" else LATER_TTL_SECONDS
        command = cls(
            id=uuid.uuid4().hex[:12],
            type=type,
            reason=(reason or "").strip(),
            operator=(operator or "").strip(),
            created_at=_iso(now),
            expires_at=_iso(now + ttl),
            args=dict(args or {}),
            timing=timing,
            client=client,
            idempotency_key=idempotency_key,
            seq=int(now * 1e9),
        )
        command.check()
        return command

    def check(self) -> None:
        """Raise InvalidCommand if this could not have come from new()."""
        if not _ID.match(self.id):
            raise InvalidCommand(f"command id {self.id!r} is not 12 hex digits")
        if self.type not in COMMAND_TYPES:
            raise InvalidCommand(
                f"unknown command {self.type!r}; known: {', '.join(COMMAND_TYPES)}"
            )
        if self.timing not in TIMINGS:
            raise InvalidCommand(f"timing must be one of {', '.join(TIMINGS)}, got {self.timing!r}")
        if not 3 <= len(self.reason) <= _MAX_REASON:
            raise InvalidCommand(
                f"a reason of 3 to {_MAX_REASON} characters is required -- it is shown to "
                "whoever finds the deployment in this state"
            )
        if not 1 <= len(self.operator) <= _MAX_OPERATOR:
            raise InvalidCommand(
                f"name the operator (1 to {_MAX_OPERATOR} characters): every change is recorded "
                "with who made it"
            )
        if not isinstance(self.args, dict):
            raise InvalidCommand("args must be an object")
        if len(json.dumps(self.args, default=str)) > _MAX_ARGS_BYTES:
            raise InvalidCommand("args are too large")
        if self.idempotency_key is not None and not (0 < len(self.idempotency_key) <= 100):
            raise InvalidCommand("idempotency_key must be 1 to 100 characters")

    def expired(self, now: float) -> bool:
        return now >= _seconds(self.expires_at)

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> Command:
        known = set(cls.__dataclass_fields__)
        command = cls(**{key: value for key, value in data.items() if key in known})
        command.check()
        return command

    @property
    def filename(self) -> str:
        return f"{self.seq:020d}-{self.id}.json"


def _write_json(path: Path, data: dict) -> None:
    """Whole file or none: written beside its destination, then renamed."""
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{uuid.uuid4().hex[:8]}.tmp")
    with open(temporary, "w", encoding="utf-8") as handle:
        json.dump(data, handle, indent=2, sort_keys=True)
        handle.write("\n")
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temporary, path)


def _read_json(path: Path) -> dict | None:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return None
    except (OSError, ValueError) as exc:
        logger.warning(f"Unreadable control file {path}: {exc}")
        return None
    return data if isinstance(data, dict) else None


class ControlInbox:
    """One deployment's control directory."""

    def __init__(self, root: str | Path, *, clock: Callable[[], float] = time.time) -> None:
        self.root = Path(root)
        self._clock = clock

    # -- paths ----------------------------------------------------------------

    def _dir(self, name: str) -> Path:
        return self.root / name

    def _commands_in(self, name: str) -> list[Command]:
        directory = self._dir(name)
        if not directory.is_dir():
            return []
        commands = []
        for path in sorted(directory.glob("*.json")):
            data = _read_json(path)
            if data is None:
                continue
            try:
                commands.append(Command.from_dict(data))
            except (InvalidCommand, TypeError) as exc:
                logger.warning(f"Ignoring malformed command {path}: {exc}")
        return commands

    # -- the server's side ----------------------------------------------------

    def enqueue(self, command: Command) -> tuple[Command, bool]:
        """Queue `command`. Returns (the queued command, whether it is new):
        a repeat of a recent idempotency key returns the original instead,
        so a double-click queues one command."""
        command.check()
        with _LOCK:
            if command.idempotency_key:
                existing = self.find_by_key(command.idempotency_key)
                if existing is not None:
                    return existing, False
            _write_json(self._dir("inbox") / command.filename, command.to_dict())
        return command, True

    def find_by_key(self, key: str) -> Command | None:
        horizon = (self._clock() - 24 * 3600) * 1e9
        for name in ("inbox", "claimed", "cancelled"):
            for command in self._commands_in(name):
                if command.seq >= horizon and command.idempotency_key == key:
                    return command
        return None

    def cancel(self, command_id: str, operator: str) -> dict | None:
        """Withdraw a queued command. None if it is not queued any more --
        a trader claimed it first, or it never existed."""
        for command in self._commands_in("inbox"):
            if command.id != command_id:
                continue
            try:
                self._dir("cancelled").mkdir(parents=True, exist_ok=True)
                os.replace(
                    self._dir("inbox") / command.filename,
                    self._dir("cancelled") / command.filename,
                )
            except FileNotFoundError:
                return None
            return self.record(command, "cancelled", f"withdrawn by {operator}")
        return None

    # -- the trader's side ----------------------------------------------------

    def queued(self) -> list[Command]:
        """Queued commands, oldest first."""
        return self._commands_in("inbox")

    def claim(self, command: Command) -> bool:
        """Take `command` off the queue. False if it was cancelled first."""
        try:
            self._dir("claimed").mkdir(parents=True, exist_ok=True)
            os.replace(
                self._dir("inbox") / command.filename, self._dir("claimed") / command.filename
            )
        except FileNotFoundError:
            return False
        return True

    def record(self, command: Command, status: str, detail: str = "", **extra: Any) -> dict:
        """The outcome of a claimed (or cancelled) command."""
        if status not in FINAL_STATUSES:
            raise ValueError(f"unknown command status {status!r}")
        result = {
            "id": command.id,
            "status": status,
            "detail": detail,
            "finished_at": _iso(self._clock()),
            **extra,
        }
        _write_json(self._dir("results") / f"{command.id}.json", result)
        return result

    def result(self, command_id: str) -> dict | None:
        if not _ID.match(command_id):
            return None
        return _read_json(self._dir("results") / f"{command_id}.json")

    # -- what has been asked, and what came of it --------------------------------

    def history(self, limit: int = 50) -> list[dict]:
        """Every command, newest first, each with its outcome: "queued" while
        in the inbox (or "expired" once past its time and still unclaimed --
        nothing may be running to expire it), "applying" while claimed
        without a result, and the result's status after."""
        now = self._clock()
        rows = []
        for name in ("inbox", "claimed", "cancelled"):
            for command in self._commands_in(name):
                row = command.to_dict()
                result = self.result(command.id)
                if result is not None:
                    row.update(
                        status=result["status"],
                        detail=result.get("detail", ""),
                        finished_at=result.get("finished_at"),
                    )
                elif name == "inbox":
                    row.update(
                        status="expired" if command.expired(now) else "queued",
                        detail="",
                        finished_at=None,
                    )
                else:
                    row.update(status="applying", detail="", finished_at=None)
                rows.append(row)
        rows.sort(key=lambda row: row["seq"], reverse=True)
        return rows[:limit]

    # -- desired state and status -------------------------------------------------

    def desired(self) -> dict:
        """Whether sessions should run. Enabled unless an operator said
        otherwise: a deployment with no control file trades as it always has."""
        data = _read_json(self.root / "desired.json") or {}
        return {
            "enabled": bool(data.get("enabled", True)),
            "wind_down": bool(data.get("wind_down", False)),
            "by": data.get("by"),
            "reason": data.get("reason"),
            "at": data.get("at"),
        }

    def set_desired(self, *, enabled: bool, wind_down: bool, by: str, reason: str) -> dict:
        data = {
            "enabled": enabled,
            "wind_down": wind_down,
            "by": by,
            "reason": reason,
            "at": _iso(self._clock()),
        }
        _write_json(self.root / "desired.json", data)
        return data

    def status(self) -> dict | None:
        return _read_json(self.root / "status.json")

    def write_status(self, **fields: Any) -> dict:
        data = {**fields, "updated_at": _iso(self._clock()), "pid": os.getpid()}
        try:
            _write_json(self.root / "status.json", data)
        except OSError as exc:
            # A status write must never take a trading process down.
            logger.warning(f"Could not write {self.root / 'status.json'}: {exc}")
        return data

    # -- the journals: the bars the trader traded on, the fills it booked ------

    def record_bars(self, bars: list[dict], *, keep_past: bool = False) -> int:
        """Append minute bars ({"t": epoch seconds, "o", "h", "l", "c", "v"}).
        With `keep_past`, a session before today that already has a file is
        left as it is -- the history a restart replays covers sessions the
        journal already holds whole. Returns the bars written."""
        return self._append("bars", bars, keep_past=keep_past)

    def record_fill(self, fill: dict) -> int:
        """Append one booked fill ({"t": epoch seconds, "side", "qty",
        "price", ...})."""
        return self._append("fills", [fill])

    def record_event(self, event: dict) -> int:
        """Append one event ({"t": epoch seconds, "kind", "detail", ...}) --
        the bridge host's account of its connection."""
        return self._append("events", [event])

    def events(self, days: int = 2) -> list[dict]:
        """The last `days` days' events, oldest first."""
        return sorted(self._journal("events", days), key=lambda row: row["t"])

    def bars(self, sessions: int = 2) -> list[dict]:
        """The last `sessions` sessions' bars, oldest first, one per minute:
        a minute recorded twice (a tick that re-read its bar) keeps the later
        record."""
        latest = {}
        for row in self._journal("bars", sessions):
            latest[row["t"]] = row
        return [latest[t] for t in sorted(latest)]

    def fills(self, sessions: int = 1) -> list[dict]:
        """The last `sessions` sessions' fills, oldest first."""
        return sorted(self._journal("fills", sessions), key=lambda row: row["t"])

    def _session(self, seconds: float) -> date:
        return datetime.fromtimestamp(seconds, _EASTERN).date()

    def _append(self, name: str, rows: list[dict], *, keep_past: bool = False) -> int:
        """Never raises: a journal must not take a trading process down."""
        if name not in JOURNALS:
            raise ValueError(f"unknown journal {name!r}")
        written = 0
        try:
            by_session: dict[date, list[dict]] = {}
            for row in rows:
                by_session.setdefault(self._session(float(row["t"])), []).append(row)
            today = self._session(self._clock())
            directory = self._dir(name)
            directory.mkdir(parents=True, exist_ok=True)
            started = False
            for session in sorted(by_session):
                path = directory / f"{session.isoformat()}.jsonl"
                if keep_past and session < today and path.exists():
                    continue
                started = started or not path.exists()
                with open(path, "a", encoding="utf-8") as handle:
                    handle.writelines(
                        json.dumps(row, sort_keys=True) + "\n" for row in by_session[session]
                    )
                written += len(by_session[session])
            if started:
                for old in self._journal_files(name)[: -_KEEP.get(name, JOURNAL_SESSIONS)]:
                    old.unlink(missing_ok=True)
        except (OSError, KeyError, TypeError, ValueError) as exc:
            logger.warning(f"Could not record to the {name} journal in {self.root}: {exc}")
        return written

    def _journal_files(self, name: str) -> list[Path]:
        directory = self._dir(name)
        if not directory.is_dir():
            return []
        return sorted(path for path in directory.iterdir() if _JOURNAL_FILE.match(path.name))

    def _journal(self, name: str, sessions: int) -> list[dict]:
        if name not in JOURNALS:
            raise ValueError(f"unknown journal {name!r}")
        rows = []
        for path in self._journal_files(name)[-sessions:] if sessions > 0 else []:
            try:
                lines = path.read_text(encoding="utf-8").splitlines()
            except OSError as exc:
                logger.warning(f"Unreadable journal {path}: {exc}")
                continue
            for line in lines:
                try:
                    row = json.loads(line)
                except ValueError:
                    continue  # the line being written as it was read
                if isinstance(row, dict) and isinstance(row.get("t"), int | float):
                    rows.append(row)
        return rows


__all__ = [
    "COMMAND_TYPES",
    "FINAL_STATUSES",
    "JOURNALS",
    "JOURNAL_SESSIONS",
    "LATER_TTL_SECONDS",
    "NOW_TTL_SECONDS",
    "TIMINGS",
    "Command",
    "ControlInbox",
    "InvalidCommand",
]
