"""
What the bridge tells apps as it happens: the notifications a phone shows.

The bridge already sees every moment someone away from the computer wants
to hear about. Each becomes a notification of one kind:

  buy, sell        the extension reports an order FILLED, or partly filled
  order_update     Fidelity accepted, cancelled or expired an order -- the
                   routine middle of an order's life, so off by default
  order_problem    Fidelity rejected an order, the extension refused one,
                   or the extension could not tell what became of one
  engine           a trading session's engine changed state: starting,
                   running, paused, halted, stopped
  session          a second trader was turned away, or a session ended
                   without saying it had stopped
  readiness        the connection is not ready to trade (and the one thing
                   to fix), not ready shortly before an open, or ready again
  fidelity_signin  Fidelity signed you out, or no Fidelity tab is open
  account_check    a read-only account check failed, or passed again
  connected        the extension connected, or reconnected
  disconnected     the extension went away, and how
  trading_switch   "Allow trading" was switched on or off in the extension
  refused          a connection was turned away: an address not allowed, a
                   key that does not match
  bridge           the bridge cannot listen (its port is taken), listens
                   again, or restarts with new settings

Which kinds are sent at all is the deployment's choice
(live.fidelity.bridge.notifications.events, or `serve --notify-events`);
the app chooses again which of those it shows.

Two places feed it. The BridgeServer reports what the extension does --
its order reports, coming and going, switches, Fidelity tab, refusals --
and every engine status a trader sends through it. The bridge host
(host.py), which outlives sessions, adds what only it knows: readiness,
account checks, sessions attaching, its own port. It owns this hub, so a
bridge it restarts with new settings keeps the same stream and the same
memory of what was already said.

Notifications keeps the recent ones, numbered within a STREAM that is new
each time the hub is made, so an app that reconnects with the last
(stream, id) it saw is sent only what it missed. It also keeps the status
apps are shown -- named parts, each from its own source (the extension's
connection and the engine's words from the BridgeServer, readiness from the
host) -- and hands both to its subscribers: the apps connected to the
NotificationServer (notify_server.py).

A notification is a report, never an instruction, and nothing flows back:
an app can neither place, cancel nor change anything through this.
"""

from __future__ import annotations

import secrets
import threading
import time
from collections import deque
from collections.abc import Callable, Iterable
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from typing import Any

from engine.core.exceptions import ConfigurationError
from fidelity_gateway.bridge.order_reports import OrderReport, _shares

#: Every kind, and what it means. engine/core/config.py names the same
#: kinds (FIDELITY_NOTIFICATION_EVENTS) to validate a config up front; a
#: test keeps the two lists the same.
EVENT_KINDS: dict[str, str] = {
    "buy": "a buy order filled, or partly filled",
    "sell": "a sell order filled, or partly filled",
    "order_update": "Fidelity accepted, cancelled or expired an order",
    "order_problem": "an order was rejected, refused, or its outcome is unknown",
    "engine": "a trading session's engine changed state: starting, running, paused, halted",
    "session": "a second trader was turned away, or a session ended without stopping",
    "readiness": "not ready to trade, not ready shortly before an open, or ready again",
    "fidelity_signin": "Fidelity signed you out, or no Fidelity tab is open",
    "account_check": "a read-only account check failed, or passed again",
    "connected": "the extension connected or reconnected",
    "disconnected": "the extension disconnected",
    "trading_switch": "the extension's Allow trading switch was turned on or off",
    "refused": "a connection was turned away: an address not allowed, a wrong key",
    "bridge": "the bridge cannot listen, listens again, or restarts with new settings",
}
#: All but the routine middle of an order's life.
DEFAULT_EVENTS = tuple(kind for kind in EVENT_KINDS if kind != "order_update")
SEVERITIES = ("info", "warning", "critical")
#: Notifications kept for an app that reconnects: days of them.
KEEP = 200
#: Not ready for this long before it is said -- a browser restarting, a
#: bridge starting up, is not news -- and an outage this long is what makes
#: "ready again" news.
READINESS_GRACE_SECONDS = 60.0
#: The same refusal (address and reason) again within this long is not news:
#: a refused extension retries every minute.
REFUSAL_REPEAT_SECONDS = 600.0

_ENGINE_TITLES = {
    "starting": "Engine starting",
    "running": "Engine running",
    "paused": "Engine paused",
    "halted": "Engine HALTED",
    "stopped": "Engine stopped",
    "recovery_required": "Engine needs recovery",
}
_ENGINE_SEVERITY = {"halted": "critical", "recovery_required": "critical", "paused": "warning"}
# The engine states a session reports when it ends on purpose.
_FINAL_STATES = frozenset({"stopped", "halted", "recovery_required"})
# readiness.py's blocking items, and the kind that announces each the moment
# it happens -- the readiness kind does not say the same thing again.
_CAUSE_KINDS = {
    "bridge": "bridge",
    "extension": "disconnected",
    "fidelity": "fidelity_signin",
    "trading": "trading_switch",
    "account": "account_check",
}
_CLOSE_WORDS = {
    1000: "closed normally",
    1001: "going away: the browser, the extension or the engine closed it",
    1006: "the connection dropped",
    1008: "refused",
    1011: "an error on the other side",
}


def close_words(code: object, reason: object) -> str:
    """How a WebSocket connection ended, in words: the bridge host's journal
    and the apps' notifications say it the same way."""
    words = _CLOSE_WORDS.get(code, f"code {code}") if isinstance(code, int) else "no close code"
    return f"{words}{f': {reason}' if reason else ''}"


def _duration(seconds: float) -> str:
    seconds = max(0, int(seconds))
    if seconds < 60:
        return f"{seconds}s"
    minutes, seconds = divmod(seconds, 60)
    if minutes < 60:
        return f"{minutes}m {seconds}s"
    hours, minutes = divmod(minutes, 60)
    if hours < 24:
        return f"{hours}h {minutes}m"
    days, hours = divmod(hours, 24)
    return f"{days}d {hours}h"


def _epoch(text: str) -> float | None:
    """An ISO-8601 time as epoch seconds, or None. Naive means UTC."""
    try:
        moment = datetime.fromisoformat(text)
    except (TypeError, ValueError):
        return None
    if moment.tzinfo is None:
        moment = moment.replace(tzinfo=UTC)
    return moment.timestamp()


def _checked_events(events: Iterable[str]) -> frozenset[str]:
    events = tuple(events)
    unknown = sorted(set(events) - set(EVENT_KINDS))
    if unknown:
        raise ConfigurationError(
            f"Unknown notification event(s) {unknown}; known: {list(EVENT_KINDS)}"
        )
    return frozenset(events)


@dataclass(frozen=True)
class Notification:
    """One thing that happened, as an app is told it."""

    id: int
    stream: str
    kind: str
    severity: str
    title: str
    body: str
    at: str
    data: dict = field(default_factory=dict)

    def to_wire(self) -> dict:
        return asdict(self)


@dataclass(frozen=True)
class Subscription:
    """What a new subscriber starts from, and how it stops listening."""

    backlog: list[Notification]
    status: dict
    close: Callable[[], None]


class Notifications:
    """The recent notifications and the status apps are shown.

    Thread-safe: the bridge's connection thread, the host's tick and the
    attached trader's thread publish; each app's connection thread
    subscribes. Listeners are called in order, under the lock that numbers
    each notification, so they must not block -- the server's only puts on
    a queue. What has already been said (the engine's last state, the
    Fidelity tab, a refusal, readiness) is remembered here under a lock of
    its own, so a restarted BridgeServer does not say it again.
    """

    def __init__(
        self,
        events: Iterable[str] = DEFAULT_EVENTS,
        *,
        keep: int = KEEP,
        clock: Callable[[], float] = time.time,
        log: Callable[[str], None] | None = None,
        stream: str | None = None,
    ) -> None:
        self._events = _checked_events(events)
        self._stream = stream or secrets.token_hex(8)
        self._clock = clock
        self._started = clock()
        self._log = log or (lambda _message: None)
        self._lock = threading.Lock()
        self._recent: deque[Notification] = deque(maxlen=keep)
        self._next_id = 1
        self._status: dict = {}
        self._listeners: list[Callable[[str, Any], None]] = []
        # What has been said, for what is news next.
        self._said = threading.Lock()
        self._engine_state: str | None = None
        self._tab: str | None = None
        self._refusals: dict[tuple[str, str], float] = {}
        self._check_failed = False
        self._causes: set[str] = set()  # readiness items announced by their own kind
        self._not_ready_since: float | None = None
        self._announced: str | None = None  # the blocking item readiness last announced
        self._warned_opens: set[str] = set()

    @property
    def events(self) -> tuple[str, ...]:
        """The kinds this bridge sends, in EVENT_KINDS order."""
        return tuple(kind for kind in EVENT_KINDS if kind in self._events)

    def set_events(self, events: Iterable[str]) -> None:
        """Change which kinds are sent: a config edit, picked up by the host."""
        self._events = _checked_events(events)

    @property
    def stream(self) -> str:
        """This hub's stream: notification ids count from 1 within it."""
        return self._stream

    @property
    def status(self) -> dict:
        with self._lock:
            return dict(self._status)

    def recent(self) -> list[Notification]:
        """Oldest first."""
        with self._lock:
            return list(self._recent)

    def subscribe(
        self, listener: Callable[[str, Any], None], *, since: tuple[str, int] | None = None
    ) -> Subscription:
        """Start calling listener("notification", Notification) and
        listener("status", dict) as each happens. Returns what the
        subscriber missed -- every kept notification after `since`, or all
        of them for another stream or none given -- and the status now,
        taken together with the subscription so nothing falls between."""
        with self._lock:
            if since is not None and since[0] == self._stream:
                backlog = [n for n in self._recent if n.id > since[1]]
            else:
                backlog = list(self._recent)
            status = dict(self._status)
            self._listeners.append(listener)

        def close() -> None:
            with self._lock:
                if listener in self._listeners:
                    self._listeners.remove(listener)

        return Subscription(backlog=backlog, status=status, close=close)

    def publish(
        self,
        kind: str,
        title: str,
        body: str,
        *,
        severity: str = "info",
        data: dict | None = None,
    ) -> Notification | None:
        """Send one notification, or nothing when its kind is not enabled."""
        if kind not in EVENT_KINDS:
            raise ValueError(f"not a notification kind: {kind!r}")
        if severity not in SEVERITIES:
            raise ValueError(f"not a severity: {severity!r}")
        if kind not in self._events:
            return None
        with self._lock:
            notification = Notification(
                id=self._next_id,
                stream=self._stream,
                kind=kind,
                severity=severity,
                title=title,
                body=body,
                at=datetime.fromtimestamp(self._clock(), UTC).isoformat(timespec="seconds"),
                data=dict(data or {}),
            )
            self._next_id += 1
            self._recent.append(notification)
            self._fan_out("notification", notification)
        return notification

    def update_status(self, **parts: Any) -> None:
        """Replace the named parts of the status apps are shown (`extension`
        and `engine` from the BridgeServer, `bridge` from the host), telling
        subscribers when anything changed."""
        with self._lock:
            status = {**self._status, **parts}
            if status == self._status:
                return
            self._status = status
            self._fan_out("status", dict(status))

    def _fan_out(self, kind: str, payload: Any) -> None:
        for listener in list(self._listeners):
            try:
                listener(kind, payload)
            except Exception as exc:
                self._log(f"[notify] a listener failed: {type(exc).__name__}: {exc}")

    # -- what the BridgeServer sees ---------------------------------------------

    def extension_connected(
        self, *, version: str | None, peer: str, away_seconds: float | None = None
    ) -> Notification | None:
        """`away_seconds`: how long it had been gone, or None for the first
        connection since the bridge started."""
        with self._said:
            self._causes.discard("extension")
        name = f"Fidelity Bridge {version}" if version else "The Fidelity Bridge extension"
        if away_seconds is None:
            return self.publish(
                "connected",
                "Extension connected",
                f"{name} connected from {peer}.",
                data={"version": version, "client": peer},
            )
        return self.publish(
            "connected",
            "Extension reconnected",
            f"{name} reconnected from {peer} after {_duration(away_seconds)} away.",
            data={"version": version, "client": peer, "awaySeconds": round(away_seconds)},
        )

    def extension_disconnected(
        self, *, peer: str, code: int | None = None, reason: str | None = None
    ) -> Notification | None:
        notification = self.publish(
            "disconnected",
            "Extension disconnected",
            f"The Fidelity Bridge extension at {peer} went away ({close_words(code, reason)}). "
            "Orders wait until it reconnects.",
            severity="warning",
            data={"client": peer, "code": code, "reason": reason or None},
        )
        if notification is not None:
            with self._said:
                self._causes.add("extension")
        return notification

    def trading_switch(self, *, allowed: bool) -> Notification | None:
        if allowed:
            with self._said:
                self._causes.discard("trading")
            return self.publish(
                "trading_switch",
                "Trading switched on",
                '"Allow trading" is on in the extension: the engine\'s orders will be placed.',
                data={"trading": True},
            )
        notification = self.publish(
            "trading_switch",
            "Trading switched OFF",
            '"Allow trading" is off in the extension: every order is refused until it is '
            "switched back on. The engine keeps reading.",
            severity="warning",
            data={"trading": False},
        )
        if notification is not None:
            with self._said:
                self._causes.add("trading")
        return notification

    def fidelity_tab(self, state: str) -> Notification | None:
        """Where the extension's Fidelity tab is (session.tab_state). A
        sign-out, or no tab, is news; the first word after the bridge
        starts, when it is signed in, is how things are; signing in again is
        said by readiness ("Ready to trade"). Remembered across the
        extension reconnecting, so the same state is not said twice."""
        with self._said:
            previous, self._tab = self._tab, state
            if state == previous:
                return None
            if state == "signed_in":
                self._causes.discard("fidelity")
        if state == "signed_out":
            notification = self.publish(
                "fidelity_signin",
                "Fidelity signed you out",
                "Sign in to Fidelity again in the browser the extension runs in. Nothing is "
                "traded until you do.",
                severity="warning",
                data={"state": state},
            )
        elif state == "no_tab":
            notification = self.publish(
                "fidelity_signin",
                "No Fidelity tab is open",
                "Open Fidelity in the browser the extension runs in, and sign in. Nothing is "
                "traded until you do.",
                severity="warning",
                data={"state": state},
            )
        else:
            return None
        if notification is not None:
            with self._said:
                self._causes.add("fidelity")
        return notification

    def connection_refused(self, *, peer: str, reason: str) -> Notification | None:
        """A connection turned away. The same address and reason again
        within REFUSAL_REPEAT_SECONDS is the same news."""
        now = self._clock()
        with self._said:
            last = self._refusals.get((peer, reason))
            if last is not None and now - last < REFUSAL_REPEAT_SECONDS:
                return None
            self._refusals[(peer, reason)] = now
            for key, at in list(self._refusals.items()):
                if now - at >= REFUSAL_REPEAT_SECONDS:
                    del self._refusals[key]
        return self.publish(
            "refused",
            "Connection refused",
            f"The bridge turned away {peer}: {reason}.",
            severity="warning",
            data={"client": peer, "reason": reason},
        )

    def engine_status(self, status: dict) -> Notification | None:
        """Every engine status the bridge relays. A change of state is news;
        the bridge's own standby status (mode "bridge": the bridge host
        between sessions, or `serve`) is not an engine's, and is skipped."""
        if status.get("mode") == "bridge":
            return None
        state = str(status.get("state") or "unknown")
        with self._said:
            previous, self._engine_state = self._engine_state, state
        if state == previous:
            return None
        return self.engine_state(status, previous)

    def engine_state(self, status: dict, previous: str | None) -> Notification | None:
        """An engine's status reached a new state; `previous` is the one
        before, None for its first."""
        state = str(status.get("state") or "unknown")
        detail = str(status.get("detail") or "")
        where = " · ".join(str(status[k]) for k in ("symbol", "mode") if status.get(k))
        body = f"{where}: {detail}" if where and detail else (where or detail or state)
        return self.publish(
            "engine",
            _ENGINE_TITLES.get(state, f"Engine {state}"),
            body,
            severity=_ENGINE_SEVERITY.get(state, "info"),
            data={
                "state": state,
                "previous": previous,
                "detail": detail,
                "mode": status.get("mode"),
                "symbol": status.get("symbol"),
            },
        )

    def order_report(
        self, report: OrderReport, previous: OrderReport | None, resent: bool = False
    ) -> Notification | None:
        """An order report that is news (OrderReports.add_listener).

        Only a change of state is announced: a partial fill growing is
        not a new notification each time. And a report in the extension's
        resent log about an order this bridge never heard of is history,
        not news, unless it changed after this hub was made -- otherwise
        the first connect of a bridge with no reports file would announce
        every order in the extension's log at once.
        """
        if previous is not None and previous.state == report.state:
            return None
        if resent and previous is None:
            updated = _epoch(report.updated_at)
            if updated is None or updated < self._started:
                return None
        order = f"order {report.conf_num}" if report.conf_num else "no confirmation number yet"
        data = {
            "orderId": report.id,
            "confNum": report.conf_num,
            "symbol": report.symbol,
            "side": report.side,
            "qty": report.qty,
            "limitPrice": report.limit_price,
            "state": report.state,
            "filledQty": report.filled_qty,
            "avgPrice": report.avg_price,
        }
        buy = report.side == "buy"
        if report.state == "filled":
            filled = report.filled_qty or report.qty
            return self.publish(
                report.side,
                f"{'Bought' if buy else 'Sold'} {_shares(filled)} {report.symbol}",
                f"{_shares(filled)} at ${report.avg_price:,.2f} ({report.summary}), {order}.",
                data=data,
            )
        if report.state == "partially_filled":
            return self.publish(
                report.side,
                f"{'Buy' if buy else 'Sell'} partly filled: {_shares(report.filled_qty)} of "
                f"{_shares(report.qty)} {report.symbol}",
                f"{_shares(report.filled_qty)} so far at ${report.avg_price:,.2f} "
                f"({report.summary}), {order}.",
                data=data,
            )
        if report.state == "submitted":
            return self.publish(
                "order_update",
                "Order accepted",
                f"Fidelity accepted {report.summary}, {order}.",
                data=data,
            )
        if report.state in ("cancelled", "expired"):
            return self.publish(
                "order_update",
                f"Order {report.state}",
                f"{report.summary}, {order}.",
                data=data,
            )
        reason = report.detail or "no reason given"
        if report.state == "rejected":
            return self.publish(
                "order_problem",
                "Order rejected",
                f"Fidelity rejected {report.summary}, {order}: {reason}.",
                severity="warning",
                data=data,
            )
        if report.state == "blocked":
            return self.publish(
                "order_problem",
                "Order refused by the extension",
                f"{report.summary}: {reason}.",
                severity="warning",
                data=data,
            )
        if report.state == "unknown":
            return self.publish(
                "order_problem",
                "Order outcome unknown",
                f"The extension could not confirm {report.summary}, {order}: {reason}. "
                "Check the account at Fidelity.",
                severity="critical",
                data=data,
            )
        return None  # working, cancel_requested: the routine middle

    # -- what only the bridge host knows ------------------------------------------

    def readiness(
        self,
        verdict: dict,
        *,
        now: float,
        session_open: bool = False,
        opens_soon: bool = False,
        opens_in_minutes: float | None = None,
        next_open: str | None = None,
    ) -> Notification | None:
        """The host's verdict (readiness.py), every tick. `opens_soon`: the
        next open is close enough that not being ready is urgent (the
        host's NOT_READY_WARNING_MINUTES).

        Not ready for READINESS_GRACE_SECONDS is said once per cause --
        unless that cause's own kind already said it the moment it happened
        (the extension leaving, a sign-out, the switch, a failed check, the
        port). Shortly before an open it is said once more, urgently, for
        that open. Ready again after an outage that long, one that was said,
        is news too.
        """
        with self._said:
            if verdict.get("ready"):
                since, self._not_ready_since = self._not_ready_since, None
                announced = self._announced is not None or bool(self._causes)
                self._announced = None
                self._causes.clear()
                if since is None or now - since < READINESS_GRACE_SECONDS or not announced:
                    return None
                outage = now - since
                publish = (
                    "Ready to trade",
                    f"The Fidelity connection is ready again, after {_duration(outage)} not ready.",
                    "info",
                )
            else:
                if self._not_ready_since is None:
                    self._not_ready_since = now
                if now - self._not_ready_since < READINESS_GRACE_SECONDS:
                    return None
                blocking = verdict.get("blocking")
                summary = str(verdict.get("summary") or "not ready")
                fix = verdict.get("fix")
                soon = session_open or opens_soon
                if (
                    opens_soon
                    and not session_open
                    and next_open is not None
                    and next_open not in self._warned_opens
                ):
                    self._warned_opens.add(next_open)
                    self._announced = blocking
                    minutes = max(0, round(opens_in_minutes or 0))
                    publish = (
                        "Not ready for the open",
                        f"The market opens in {minutes} min and the Fidelity connection is not "
                        f"ready: {summary}." + (f" To fix: {fix}." if fix else ""),
                        "critical",
                    )
                elif blocking == self._announced:
                    return None
                else:
                    self._announced = blocking
                    if blocking in self._causes and _CAUSE_KINDS.get(blocking) in self._events:
                        return None  # its own kind said it already
                    publish = (
                        "Not ready to trade",
                        f"{summary}." + (f" To fix: {fix}." if fix else ""),
                        "critical" if soon else "warning",
                    )
        title, body, severity = publish
        return self.publish(
            "readiness",
            title,
            body,
            severity=severity,
            data={
                "ready": bool(verdict.get("ready")),
                "blocking": verdict.get("blocking"),
                "summary": verdict.get("summary"),
                "fix": verdict.get("fix"),
                "nextOpen": next_open,
            },
        )

    def account_check(self, result: dict) -> Notification | None:
        """The host's read-only account check (host.run_check): a failure is
        news, and so is passing again after one."""
        if result.get("busy"):
            return None
        ok = bool(result.get("ok"))
        with self._said:
            failed_before, self._check_failed = self._check_failed, not ok
            if ok:
                self._causes.discard("account")
        by = result.get("by")
        detail = str(result.get("detail") or "")
        data = {"ok": ok, "detail": detail, "by": by}
        if ok:
            if not failed_before:
                return None
            return self.publish("account_check", "Account check passed", f"{detail}.", data=data)
        notification = self.publish(
            "account_check",
            "Account check failed",
            f"The read-only check of the account{f' ({by})' if by else ''} failed: {detail}.",
            severity="warning",
            data=data,
        )
        if notification is not None:
            with self._said:
                self._causes.add("account")
        return notification

    def session_refused(self, detail: str) -> Notification | None:
        """A second process tried to attach while one was."""
        return self.publish(
            "session",
            "A second trader was turned away",
            detail,
            severity="warning",
        )

    def session_ended(
        self, *, process: str | None, who: str, status: dict | None
    ) -> Notification | None:
        """A process detached from the host. A trading loop that had said it
        stopped (or halted) was announced by its engine already; one that
        had not, ended some other way."""
        if process != "loop":
            return None
        state = (status or {}).get("state")
        if state in _FINAL_STATES:
            return None
        last = (
            f" Its last report: {state} -- {(status or {}).get('detail') or 'no detail'}."
            if state
            else " It had not reported anything."
        )
        return self.publish(
            "session",
            "Trading session ended unexpectedly",
            f"{who[:1].upper()}{who[1:]} detached without saying it had stopped.{last}",
            severity="warning",
            data={"process": process, "state": state},
        )

    def bridge_port_conflict(self, detail: str) -> Notification | None:
        notification = self.publish(
            "bridge",
            "Bridge cannot listen",
            f"{detail} The extension cannot connect until it can; it tries again every 30 s.",
            severity="critical",
        )
        if notification is not None:
            with self._said:
                self._causes.add("bridge")
        return notification

    def bridge_listening(self, url: str) -> Notification | None:
        """Listening again -- news only after a port conflict was said."""
        with self._said:
            if "bridge" not in self._causes:
                return None
            self._causes.discard("bridge")
        return self.publish("bridge", "Bridge listening again", f"Listening on {url}.")

    def bridge_restarting(self) -> Notification | None:
        return self.publish(
            "bridge",
            "Bridge restarting",
            "The bridge's settings changed: it restarts with them, and the extension "
            "reconnects within a minute.",
        )
