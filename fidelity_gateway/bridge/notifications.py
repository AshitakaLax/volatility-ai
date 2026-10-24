"""
What the bridge tells apps as it happens: the notifications a phone shows.

The bridge already sees every moment someone away from the computer wants
to hear about. Each becomes a notification of one kind:

  buy, sell        the extension reports an order FILLED, or partly filled
  order_update     Fidelity accepted, cancelled or expired an order -- the
                   routine middle of an order's life, so off by default
  order_problem    Fidelity rejected an order, the extension refused one,
                   or the extension could not tell what became of one
  connected        the extension connected, or reconnected
  disconnected     the extension went away
  trading_switch   "Allow trading" was switched on or off in the extension
  engine           the engine's state changed: starting, running, paused,
                   halted, stopped

Which kinds are sent at all is the deployment's choice
(live.fidelity.bridge.notifications.events, or `serve --notify-events`);
the app chooses again which of those it shows.

Notifications keeps the recent ones, numbered within a STREAM that is new
each time the bridge starts, so an app that reconnects with the last
(stream, id) it saw is sent only what it missed. It also keeps the
bridge's current status -- the extension's connection and switches, the
engine's state -- and hands both to its subscribers: the apps connected to
the NotificationServer (notify_server.py).

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
    "connected": "the extension connected or reconnected",
    "disconnected": "the extension disconnected",
    "trading_switch": "the extension's Allow trading switch was turned on or off",
    "engine": "the engine's state changed: starting, running, paused, halted, stopped",
}
#: All but the routine middle of an order's life.
DEFAULT_EVENTS = tuple(kind for kind in EVENT_KINDS if kind != "order_update")
SEVERITIES = ("info", "warning", "critical")
#: Notifications kept for an app that reconnects: a trading session's worth.
KEEP = 200

_ENGINE_TITLES = {
    "starting": "Engine starting",
    "running": "Engine running",
    "paused": "Engine paused",
    "halted": "Engine HALTED",
    "stopped": "Engine stopped",
    "recovery_required": "Engine needs recovery",
}
_ENGINE_SEVERITY = {"halted": "critical", "recovery_required": "critical", "paused": "warning"}


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
    """The recent notifications and the bridge's status, for apps.

    Thread-safe: the bridge's connection thread and the engine's thread
    publish, each app's connection thread subscribes. Listeners are called
    in order, under the lock that numbers each notification, so they must
    not block -- the server's only puts on a queue.
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
        events = tuple(events)
        unknown = sorted(set(events) - set(EVENT_KINDS))
        if unknown:
            raise ConfigurationError(
                f"Unknown notification event(s) {unknown}; known: {list(EVENT_KINDS)}"
            )
        self._events = frozenset(events)
        self._stream = stream or secrets.token_hex(8)
        self._clock = clock
        self._started = clock()
        self._log = log or (lambda _message: None)
        self._lock = threading.Lock()
        self._recent: deque[Notification] = deque(maxlen=keep)
        self._next_id = 1
        self._status: dict = {}
        self._listeners: list[Callable[[str, Any], None]] = []

    @property
    def events(self) -> tuple[str, ...]:
        """The kinds this bridge sends, in EVENT_KINDS order."""
        return tuple(kind for kind in EVENT_KINDS if kind in self._events)

    @property
    def stream(self) -> str:
        """This run's stream: notification ids count from 1 within it."""
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

    def set_status(self, status: dict) -> None:
        """Replace the bridge's status, telling subscribers if it changed."""
        with self._lock:
            if status == self._status:
                return
            self._status = dict(status)
            self._fan_out("status", dict(status))

    def _fan_out(self, kind: str, payload: Any) -> None:
        for listener in list(self._listeners):
            try:
                listener(kind, payload)
            except Exception as exc:
                self._log(f"[notify] a listener failed: {type(exc).__name__}: {exc}")

    # -- what the bridge sees ------------------------------------------------

    def extension_connected(
        self, *, version: str | None, peer: str, away_seconds: float | None = None
    ) -> Notification | None:
        """`away_seconds`: how long it had been gone, or None for the first
        connection since the bridge started."""
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

    def extension_disconnected(self, *, peer: str) -> Notification | None:
        return self.publish(
            "disconnected",
            "Extension disconnected",
            f"The Fidelity Bridge extension at {peer} went away. The engine's orders wait "
            "until it reconnects.",
            severity="warning",
            data={"client": peer},
        )

    def trading_switch(self, *, allowed: bool) -> Notification | None:
        if allowed:
            return self.publish(
                "trading_switch",
                "Trading switched on",
                '"Allow trading" is on in the extension: the engine\'s orders will be placed.',
                data={"trading": True},
            )
        return self.publish(
            "trading_switch",
            "Trading switched OFF",
            '"Allow trading" is off in the extension: every order is refused until it is '
            "switched back on. The engine keeps reading.",
            severity="warning",
            data={"trading": False},
        )

    def engine_state(self, status: dict, previous: str | None) -> Notification | None:
        """The engine's status (BridgeServer.set_engine_status) reached a
        new state; `previous` is the one before, None for its first."""
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
        not news, unless it changed after this bridge started -- otherwise
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
