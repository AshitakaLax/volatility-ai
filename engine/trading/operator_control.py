"""
Applying operator commands inside the trading process.

engine/trading/control_inbox.py is where the web server leaves them; this is
the trader's side. Two processes apply them, never at once:

  LoopControl        the running trading loop, on its own thread, after
                     every tick (cli.py wires it to the tick listener) --
                     through the CircuitBreaker and loop it trades with, so a
                     pause stops the very next buy decision.
  SupervisorControl  tools/market_hours_supervisor.py, while no loop runs:
                     waiting for the open, disabled, after the close. It
                     opens the ledger itself, under the same StateStoreLock a
                     loop takes, so it can never write beside a running one.

Each command is claimed, applied by a handler and answered with a result.
A handler refuses with CommandRejected and its message reaches the operator;
any other exception is caught and reported the same way -- a bad command
must never take a trading process down.
"""

from __future__ import annotations

import hashlib
import logging
import os
import time
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from engine.trading.control_inbox import Command, ControlInbox

logger = logging.getLogger(__name__)

Handler = Callable[[Command], str]

# A newer queued command of the same family replaces an older one that has
# not been applied: two queued algorithm switches mean the operator changed
# their mind, not "switch twice".
_FAMILY = {"switch_algorithm": "algorithm", "revert_algorithm": "algorithm"}

# States a disabled deployment reports as "disabled" instead.
_WAITING = {"waiting_for_open", "closed", "restarting", "waiting_for_broker"}

# How long the supervisor waits between looks at the inbox.
SUPERVISOR_SLICE_SECONDS = 15.0
# How long a just-launched loop may take to report (history replay,
# reconciliation) before the page calls it unresponsive.
STARTUP_ALLOWANCE_SECONDS = 600.0


class CommandRejected(Exception):
    """A command this process will not apply; the message says why."""


def account_fingerprint() -> str | None:
    """A short, one-way tag for the Alpaca account this process trades: the
    first 12 hex digits of SHA-256 over its key id -- never the key. Two
    deployments reporting the same tag trade one account, and two loops on
    one account diverge both ledgers from the venue (docs/DEPLOY.md), so the
    Live page refuses to enable the second."""
    key = os.environ.get("APCA_API_KEY_ID")
    return hashlib.sha256(key.encode()).hexdigest()[:12] if key else None


def account_tag(live) -> str | None:
    """The account tag a trader of this LiveConfig reports. A Fidelity
    deployment's Alpaca key reads prices and the clock only, so that key's
    tag would tie it to whichever paper trader shares the key -- and the
    Live page would refuse to enable the two together. It is tagged by the
    Fidelity account it trades instead: "fidelity-" and the first 12 hex
    digits of SHA-256 over the number, never the number."""
    if live.broker != "fidelity":
        return account_fingerprint()
    account = (live.fidelity.account if live.fidelity is not None else None) or ""
    return "fidelity-" + hashlib.sha256(account.encode()).hexdigest()[:12]


class ControlApplier:
    """Claims queued commands in order and applies them through `handlers`.

    `ready(command)` decides whether a command may apply now; one that may
    not stays queued (a "when_flat" switch while lots are open, say).
    """

    def __init__(
        self,
        inbox: ControlInbox,
        handlers: dict[str, Handler],
        *,
        ready: Callable[[Command], bool] | None = None,
        clock: Callable[[], float] = time.time,
    ) -> None:
        self.inbox = inbox
        self.handlers = handlers
        self._ready = ready or (lambda _command: True)
        self._clock = clock

    def poll(self) -> list[dict]:
        """Apply what is due. Returns the results written."""
        results: list[dict] = []
        queued = self.inbox.queued()
        newest: dict[str, str] = {}
        for command in queued:
            family = _FAMILY.get(command.type)
            if family is not None:
                newest[family] = command.id
        now = self._clock()
        for command in queued:
            family = _FAMILY.get(command.type)
            if command.expired(now):
                if self.inbox.claim(command):
                    results.append(
                        self.inbox.record(
                            command, "expired", "nothing applied it before it expired"
                        )
                    )
                continue
            if family is not None and newest[family] != command.id:
                if self.inbox.claim(command):
                    results.append(
                        self.inbox.record(command, "superseded", "a newer change replaced it")
                    )
                continue
            if not self._ready(command):
                continue
            if not self.inbox.claim(command):
                continue  # cancelled between the listing and the claim
            results.append(self._apply(command))
        return results

    def _apply(self, command: Command) -> dict:
        handler = self.handlers.get(command.type)
        if handler is None:
            return self.inbox.record(
                command, "rejected", f"{command.type} cannot be applied by this trader"
            )
        try:
            detail = handler(command)
        except CommandRejected as exc:
            return self.inbox.record(command, "rejected", str(exc))
        except Exception as exc:
            logger.exception(f"Applying {command.type} {command.id} failed")
            return self.inbox.record(command, "rejected", f"{type(exc).__name__}: {exc}")
        logger.info(f"[control] {command.type} by {command.operator}: {detail}")
        return self.inbox.record(command, "applied", detail)


# --------------------------------------------------------------------
# The commands themselves
# --------------------------------------------------------------------


def _pause(breaker, command: Command) -> str:
    if breaker.halt_by_operator(command.operator, command.reason):
        return "new buys paused; open lots still exit at their targets"
    return f"already halted ({breaker.reason}); left as it was"


def _resume(breaker, command: Command, reset_baseline: Callable[[], None]) -> str:
    if breaker.allows_new_buys:
        return "buying was already allowed"
    breaker.manual_reset(command.operator, command.reason)
    if command.args.get("reset_drawdown_baseline"):
        reset_baseline()
        return "buying resumed; drawdown is measured from the next tick's equity"
    return "buying resumed"


def _lot_count(count: int) -> str:
    return f"{count} lot{'' if count == 1 else 's'}"


class LoopControl:
    """The running loop's side of the control directory: applies commands
    after each tick, finishes a wind-down once flat, and reports status.

    `loop()` returns the loop currently trading (cli.py rebuilds it when the
    algorithm changes); `stop(reason)` asks it to stop after this tick.
    `extra` adds handlers -- the algorithm commands, which cli.py builds
    from research/strategies/live_algorithm.py. `account()` is the tag its
    status carries for the account it trades (account_tag).
    """

    def __init__(
        self,
        inbox: ControlInbox,
        *,
        breaker,
        loop: Callable[[], Any],
        stop: Callable[[str], None],
        heartbeat_seconds: float,
        extra: dict[str, Handler] | None = None,
        status_fields: Callable[[], dict] | None = None,
        account: Callable[[], str | None] = account_fingerprint,
        clock: Callable[[], float] = time.time,
    ) -> None:
        self.inbox = inbox
        self.breaker = breaker
        self._loop = loop
        self._stop = stop
        self._heartbeat = heartbeat_seconds
        self._status_fields = status_fields or (lambda: {})
        self._account = account
        self.stopping: str | None = None
        handlers: dict[str, Handler] = {
            "pause_buys": lambda c: _pause(self.breaker, c),
            "resume_buys": self._resume,
            "disable": self._disable,
            "enable": self._enable,
        }
        handlers.update(extra or {})
        self.applier = ControlApplier(inbox, handlers, ready=self._ready, clock=clock)

    def _ready(self, command: Command) -> bool:
        if command.type == "reset_paper_ledger":
            return False  # only while nothing trades: the supervisor's
        if command.timing == "next_session":
            return False  # the supervisor applies it before the next launch
        if command.timing == "when_flat":
            return self._loop().is_flat()
        return True

    def _resume(self, command: Command) -> str:
        desired = self.inbox.desired()
        detail = _resume(self.breaker, command, self._loop().reset_drawdown_baseline)
        if desired["wind_down"]:
            self.inbox.set_desired(
                enabled=True, wind_down=False, by=command.operator, reason=command.reason
            )
            detail += "; the wind-down is cancelled"
        return detail

    def _disable(self, command: Command) -> str:
        if command.args.get("mode", "now") == "wind_down":
            _pause(self.breaker, command)
            self.inbox.set_desired(
                enabled=True, wind_down=True, by=command.operator, reason=command.reason
            )
            lots = len(self._loop().ledger.open_lots)
            return (
                f"winding down: buys paused, {_lot_count(lots)} still managed; trading stops "
                "once none are left"
            )
        self.inbox.set_desired(
            enabled=False, wind_down=False, by=command.operator, reason=command.reason
        )
        self.stopping = f"disabled by {command.operator}"
        self._stop(self.stopping)
        lots = len(self._loop().ledger.open_lots)
        return (
            f"stopping after this tick; {_lot_count(lots)} unmanaged until enabled -- no "
            "exits while disabled"
        )

    def _enable(self, command: Command) -> str:
        desired = self.inbox.desired()
        if desired["enabled"] and not desired["wind_down"]:
            return "already enabled"
        self.inbox.set_desired(
            enabled=True, wind_down=False, by=command.operator, reason=command.reason
        )
        if desired["wind_down"]:
            return "the wind-down is cancelled; new buys stay paused until resumed"
        return "enabled"

    def tick(self) -> None:
        """After every tick (and once before the first)."""
        try:
            self.applier.poll()
            self._finish_wind_down()
            self.write_status()
        except Exception:
            # The control directory is a convenience next to trading, never
            # a reason to stop it.
            logger.exception("Operator control failed this tick; trading continues")

    def _finish_wind_down(self) -> None:
        if self.stopping or not self.inbox.desired()["wind_down"]:
            return
        if not self._loop().is_flat():
            return
        self.inbox.set_desired(
            enabled=False, wind_down=False, by="wind-down", reason="no lots or orders left"
        )
        self.stopping = "wound down: no lots or orders left"
        self._stop(self.stopping)

    def write_status(self, state: str | None = None, detail: str | None = None) -> dict:
        loop = self._loop()
        desired = self.inbox.desired()
        if state is None:
            if self.stopping:
                state, detail = "stopping", self.stopping
            elif desired["wind_down"]:
                state = "winding_down"
            elif not self.breaker.allows_new_buys:
                state = "buys_paused"
            else:
                state = "trading"
        if detail is None and not self.breaker.allows_new_buys:
            detail = self.breaker.reason
        return self.inbox.write_status(
            state=state,
            detail=detail,
            process="loop",
            heartbeat_seconds=self._heartbeat,
            last_tick_at=loop.state.last_tick_at,
            open_lots=len(loop.ledger.open_lots),
            open_orders=len(loop.state.open_orders),
            cash=loop.state.cash,
            breaker={"state": self.breaker.state.value, "reason": self.breaker.reason},
            account=self._account(),
            **self._status_fields(),
        )


class SupervisorControl:
    """The supervisor's side, while no loop runs: commands applied at once,
    the desired state honoured, status reported, waits made interruptible."""

    def __init__(
        self,
        inbox: ControlInbox,
        *,
        state_db: str,
        extra: dict[str, Handler] | None = None,
        account: Callable[[], str | None] = account_fingerprint,
        clock: Callable[[], float] = time.time,
        sleep: Callable[[float], None] = time.sleep,
        slice_seconds: float = SUPERVISOR_SLICE_SECONDS,
    ) -> None:
        self.inbox = inbox
        self.state_db = state_db
        self._account = account
        self._clock = clock
        self._sleep = sleep
        self.slice_seconds = slice_seconds
        handlers: dict[str, Handler] = {
            "pause_buys": lambda c: self._with_breaker(lambda breaker, _store: _pause(breaker, c)),
            "resume_buys": self._resume,
            "disable": self._disable,
            "enable": self._enable,
            # Every session starts by replaying history: nothing to redo here.
            "rewarm": lambda _c: "no session is running; the next one starts from history",
        }
        handlers.update(extra or {})
        self.applier = ControlApplier(inbox, handlers, ready=self._ready, clock=clock)

    def _ready(self, command: Command) -> bool:
        # Between sessions "now" and "next_session" are the same moment, and
        # a deployment is flat or not regardless of whether a loop runs.
        if command.timing == "when_flat":
            try:
                return self._with_ledger(lambda store: not _open_lots(store))
            except CommandRejected:
                return False  # a loop holds the ledger; it decides
        return True

    def _with_ledger(self, apply: Callable[[Any], Any]) -> Any:
        from engine.core.persistence import LedgerStore
        from engine.core.process_lock import LockHeldError, StateStoreLock

        lock = StateStoreLock(self.state_db)
        try:
            lock.acquire()
        except LockHeldError as exc:
            raise CommandRejected(
                "a trading loop holds the ledger; queue the command again for it to apply"
            ) from exc
        store = LedgerStore(self.state_db)
        try:
            return apply(store)
        finally:
            store.close()
            lock.release()

    def _with_breaker(self, apply: Callable[[Any, Any], str]) -> str:
        from engine.trading.risk_manager import CircuitBreaker

        return self._with_ledger(lambda store: apply(CircuitBreaker(store=store), store))

    def _resume(self, command: Command) -> str:
        from engine.trading.live_trading_loop import reset_drawdown_baseline

        def apply(breaker, store) -> str:
            return _resume(breaker, command, lambda: reset_drawdown_baseline(store))

        detail = self._with_breaker(apply)
        if self.inbox.desired()["wind_down"]:
            self.inbox.set_desired(
                enabled=True, wind_down=False, by=command.operator, reason=command.reason
            )
            detail += "; the wind-down is cancelled"
        return detail

    def _disable(self, command: Command) -> str:
        if command.args.get("mode", "now") == "wind_down":
            lots = self._with_breaker(
                lambda breaker, store: (_pause(breaker, command), _open_lots(store))[1]
            )
            if not lots:
                self.inbox.set_desired(
                    enabled=False, wind_down=False, by=command.operator, reason=command.reason
                )
                return "nothing open: disabled now"
            self.inbox.set_desired(
                enabled=True, wind_down=True, by=command.operator, reason=command.reason
            )
            return (
                f"winding down: buys paused, {_lot_count(lots)} managed at the next session; "
                "trading stops once none are left"
            )
        self.inbox.set_desired(
            enabled=False, wind_down=False, by=command.operator, reason=command.reason
        )
        return "disabled: no session starts until enabled"

    def _enable(self, command: Command) -> str:
        desired = self.inbox.desired()
        if desired["enabled"] and not desired["wind_down"]:
            return "already enabled"
        self.inbox.set_desired(
            enabled=True, wind_down=False, by=command.operator, reason=command.reason
        )
        return "enabled: sessions start again"

    # -- what the supervisor asks ---------------------------------------------

    def poll(self) -> list[dict]:
        try:
            return self.applier.poll()
        except Exception:
            logger.exception("Operator control failed; the supervisor carries on")
            return []

    def enabled(self) -> bool:
        return self.inbox.desired()["enabled"]

    def report(self, state: str, detail: str = "", **fields: Any) -> dict:
        from engine.core.build_info import identity

        fields.setdefault("build", identity())
        return self.inbox.write_status(
            state=state,
            detail=detail,
            process="supervisor",
            heartbeat_seconds=fields.pop("heartbeat_seconds", self.slice_seconds),
            account=self._account(),
            **fields,
        )

    def serve(
        self,
        seconds: float,
        *,
        state: str,
        detail: str = "",
        until: Callable[[], bool] | None = None,
        **fields: Any,
    ) -> bool:
        """Wait `seconds`, looking at the inbox every slice and reporting
        `state`. Returns True as soon as `until()` holds (checked after each
        look), False when the time runs out."""
        deadline = self._clock() + max(0.0, seconds)
        while True:
            self.poll()
            if until is not None and until():
                return True
            if state in _WAITING and not self.enabled():
                self.report("disabled", "no session starts until enabled", **fields)
            else:
                self.report(state, detail, **fields)
            left = deadline - self._clock()
            if left <= 0:
                return False
            self._sleep(min(self.slice_seconds, left))


def _open_lots(store) -> int:
    return len(store.load_ledger().open_lots)


def reset_paper_ledger_handler(
    inbox: ControlInbox,
    *,
    state_db: str,
    paper: bool,
    broker_book: Callable[[], dict],
    clock: Callable[[], float] = time.time,
) -> Handler:
    """The Live page's "fresh paper ledger", for the SUPERVISOR only.

    Refused unless the deployment is paper, disabled (no session can start
    meanwhile) and its broker account holds no positions and no open orders
    -- a fresh ledger beside a non-empty account would fail reconciliation
    at the next start, or worse, forget lots that exist. The old ledger is
    moved, not deleted: archive/<UTC time>/ beside it, on the same volume.
    The new one starts with the account's cash (`broker_book()`:
    {"positions", "open_orders", "cash"}).
    """

    def handle(command: Command) -> str:
        from engine.core.persistence import LedgerStore
        from engine.core.process_lock import LockHeldError, StateStoreLock
        from engine.trading.live_trading_loop import seed_fresh_ledger

        if not paper:
            raise CommandRejected("a real-money ledger is never reset from the Live page")
        if inbox.desired()["enabled"]:
            raise CommandRejected(
                "disable it first: a ledger is reset only while no session can start"
            )
        book = broker_book()
        if book["positions"] or book["open_orders"]:
            raise CommandRejected(
                f"the paper account still holds {book['positions']} position(s) and "
                f"{book['open_orders']} open order(s); reset the paper account in Alpaca's "
                "dashboard first"
            )
        lock = StateStoreLock(state_db)
        try:
            lock.acquire()
        except LockHeldError as exc:
            raise CommandRejected("a trading loop holds the ledger") from exc
        try:
            ledger = Path(state_db)
            stamp = datetime.fromtimestamp(clock(), UTC).strftime("%Y-%m-%dT%H%M%SZ")
            archive = ledger.parent / "archive" / stamp
            archive.mkdir(parents=True, exist_ok=True)
            for suffix in ("", "-wal", "-shm", "-journal"):
                path = Path(f"{ledger}{suffix}")
                if path.exists():
                    os.replace(path, archive / path.name)
            store = LedgerStore(state_db)
            try:
                seed_fresh_ledger(store, book["cash"])
            finally:
                store.close()
        finally:
            lock.release()
        return (
            f"the old ledger is archived in {archive}; the fresh one starts with "
            f"{float(book['cash']):,.2f} cash from the paper account"
        )

    return handle


__all__ = [
    "STARTUP_ALLOWANCE_SECONDS",
    "SUPERVISOR_SLICE_SECONDS",
    "CommandRejected",
    "ControlApplier",
    "LoopControl",
    "SupervisorControl",
    "account_fingerprint",
    "reset_paper_ledger_handler",
]
