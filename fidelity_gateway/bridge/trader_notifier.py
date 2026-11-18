"""
Notifications for a deployment no bridge sees: read from its trader's journals.

The Fidelity bridge hears a Fidelity deployment's every order from the
browser extension, and every engine status from the trader attached to it
(notifications.py). An Alpaca deployment's trading loop talks to no bridge --
cli.py opens none for it -- but everything a phone wants to hear about it is
already in files its trader keeps in the control directory
(engine/trading/control_inbox.py), and in its ledger:

  status.json          what the trader is doing, rewritten as it works: the
                       loop while a session runs, the supervisor between them
  fills/<day>.jsonl    every fill it booked: a buy with where its lot sells, a
                       sale with what it fetched and made after costs
  orders/<day>.jsonl   each order's life: placed, cancelled, expired, rejected
  the ledger           the open lots (book.py)

TraderWatch follows one deployment's files and turns what changes into the
bridge's own notification kinds -- buy, sell, order_update, order_problem,
engine, session, window -- and status parts, in a Notifications hub of its
own:

  engine   the trading loop's state in the bridge's words (running, paused,
           stopped, ...), None between sessions -- as a Fidelity bridge sends
  book     open lots, the last sales, today's profit (book.py)
  trader   the trader's own report, loop or supervisor: its state word,
           whether it is still reporting, the next open

TraderNotifier serves every watched deployment through ONE NotificationServer,
each at /notifications/<id> and the first also at /notifications, each hello
naming its account (id, label, broker, paper or real money), so an app can
tell an Alpaca stream from a Fidelity one by itself.

Read-only by construction: it writes no file, holds no broker key and reaches
no broker. What it says is what the trader journaled, a poll later
(POLL_SECONDS). It announces only what changes after it starts -- the
journals' lines already there are history, not news -- so a notifier
restarting (a new stream, as the bridge's hub is new per run) tells a phone
nothing twice.

Its key is VAI_NOTIFIER_KEY (keys.py, `keygen --notifier`), and it refuses
either of the bridge's keys: the two listeners prove nothing to each other.
"""

from __future__ import annotations

import json
import os
import threading
import time
from collections.abc import Callable, Iterable, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import yaml

from engine.core.exceptions import ConfigurationError
from engine.trading.control_inbox import ControlInbox
from fidelity_gateway.bridge.book import BOOK_SECONDS, read_book
from fidelity_gateway.bridge.ip_policy import AddressPolicy
from fidelity_gateway.bridge.keys import (
    API_KEY_ENV_VAR,
    NOTIFIER_KEY_ENV_VAR,
    NOTIFY_KEY_ENV_VAR,
    BridgeApiKey,
    default_env_file,
    load_api_key,
    read_env_value,
)
from fidelity_gateway.bridge.notifications import DEFAULT_EVENTS, Notifications, _duration, _epoch
from fidelity_gateway.bridge.notify_protocol import NOTIFY_PATH
from fidelity_gateway.bridge.notify_server import NotificationServer, NotifyRoute
from fidelity_gateway.bridge.order_reports import _shares

DEFAULT_NOTIFIER_HOST = "127.0.0.1"
#: The bridge's listener is 8766; this one sits beside it.
DEFAULT_NOTIFIER_PORT = 8767
#: How often each deployment's files are read.
POLL_SECONDS = 2.0
_REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_REGISTRY = _REPO_ROOT / "config" / "deployments.yaml"
# server/live.py's rule for a trader that stopped reporting: three heartbeats,
# and never under this. The same words on the Live page and the phone.
_STALE_FLOOR_SECONDS = 90.0
# The trading loop's status words (operator_control.write_status, cli.py) in
# the engine words apps already know (notifications._ENGINE_TITLES).
_LOOP_STATES = {
    "trading": "running",
    "winding_down": "running",
    "buys_paused": "paused",
    "waiting_for_broker": "paused",
    "stopping": "stopped",
}
_LOOP_WORDS = {
    "trading": "trading",
    "winding_down": "winding down: selling what it holds, buying nothing",
    "buys_paused": "new buys paused",
    "waiting_for_broker": "waiting for the broker",
    "stopping": "stopping",
}
# A loop in one of these has ended, whatever its process still says.
_LOOP_ENDED = frozenset({"stopping", "stopped", "recovery_required"})
# A trader that went quiet after saying one of these meant to: not news.
_QUIET_ON_PURPOSE = frozenset({"stopped", "disabled"})
_SALE_REASONS = {"profit_target": "profit target", "signal_exit": "regime exit"}
_WINDOWS = {"pre_market": "pre-market", "after_hours": "after-hours"}
_BROKER_NAMES = {"alpaca": "Alpaca", "fidelity": "Fidelity"}


def _float(value: Any) -> float | None:
    if isinstance(value, bool) or not isinstance(value, int | float):
        return None
    return float(value)


def _iso(value: Any) -> str | None:
    """A time as ISO-8601: strings as they are, epoch seconds converted."""
    if isinstance(value, str) and value:
        return value
    seconds = _float(value)
    if seconds is None:
        return None
    return datetime.fromtimestamp(seconds, UTC).isoformat(timespec="seconds")


def _money(value: float) -> str:
    return f"${value:,.2f}"


def _signed(value: float) -> str:
    return f"{'+' if value >= 0 else '-'}{_money(abs(value))}"


# -- which deployments ----------------------------------------------------------


@dataclass(frozen=True)
class WatchedDeployment:
    """One deployment the notifier follows, from config/deployments.yaml."""

    id: str
    label: str
    broker: str
    paper: bool | None
    symbol: str | None
    control_dir: Path
    state_db: Path | None = None

    @property
    def account(self) -> dict:
        """What each app's hello says this stream is about."""
        return {
            "id": self.id,
            "label": self.label,
            "broker": self.broker,
            "paper": self.paper,
            "symbol": self.symbol,
        }

    @property
    def mode(self) -> str | None:
        return None if self.paper is None else "paper" if self.paper else "live"

    @property
    def broker_name(self) -> str:
        return _BROKER_NAMES.get(self.broker, self.broker)


def registry_path() -> Path:
    """$VAI_DEPLOYMENTS, else config/deployments.yaml -- as the server reads it."""
    configured = os.environ.get("VAI_DEPLOYMENTS")
    return Path(configured) if configured else DEFAULT_REGISTRY


def _resolve(value: Any) -> Path | None:
    if not value:
        return None
    path = Path(str(value))
    return path if path.is_absolute() else _REPO_ROOT / path


def _config_facts(path: Path | None) -> tuple[str | None, bool | None, str | None]:
    """(live.broker, live.paper_trading, backtest.symbol) from a deployment's
    config, with the engine's defaults for what it leaves out (alpaca, paper).
    Read as YAML, not validated: the trader validates its own, and a notifier
    that refused a config would only go quiet. (None, None, None) unreadable."""
    if path is None:
        return None, None, None
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except (OSError, yaml.YAMLError):
        return None, None, None
    live = data.get("live") if isinstance(data.get("live"), dict) else {}
    backtest = data.get("backtest") if isinstance(data.get("backtest"), dict) else {}
    broker = live.get("broker", "alpaca")
    paper = live.get("paper_trading", True)
    symbol = backtest.get("symbol")
    return (
        str(broker) if broker else None,
        paper if isinstance(paper, bool) else None,
        str(symbol) if symbol else None,
    )


def load_deployments(
    path: Path | None = None, *, only: Sequence[str] = ()
) -> list[WatchedDeployment]:
    """The deployments to follow, in the registry's order: those named in
    `only`, or else every Alpaca deployment with a control directory."""
    path = path or registry_path()
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except FileNotFoundError as exc:
        raise ConfigurationError(f"No deployment registry at {path}.") from exc
    entries = data.get("deployments") if isinstance(data, dict) else None
    if not isinstance(entries, dict):
        raise ConfigurationError(f"{path}: `deployments` must be a mapping of id -> entry.")
    unknown = [name for name in only if name not in entries]
    if unknown:
        raise ConfigurationError(
            f"{path} has no deployment {', '.join(unknown)}; it has {', '.join(entries)}."
        )
    chosen: list[WatchedDeployment] = []
    for deployment_id, entry in entries.items():
        if only and deployment_id not in only:
            continue
        entry = entry if isinstance(entry, dict) else {}
        control_dir = _resolve(entry.get("control_dir"))
        broker, paper, symbol = _config_facts(_resolve(entry.get("config")))
        broker = broker or entry.get("broker") or "alpaca"
        if not only and broker != "alpaca":
            continue
        if control_dir is None:
            if only:
                raise ConfigurationError(
                    f"{path}: {deployment_id} has no control_dir, so it has no journals to read."
                )
            continue
        chosen.append(
            WatchedDeployment(
                id=str(deployment_id),
                label=str(entry.get("label") or deployment_id),
                broker=str(broker),
                paper=paper,
                symbol=symbol,
                control_dir=control_dir,
                state_db=_resolve(entry.get("state_db")),
            )
        )
    if not chosen:
        raise ConfigurationError(
            f"{path} names no Alpaca deployment with a control_dir; name one with --deployment."
        )
    return chosen


# -- reading the journals -----------------------------------------------------------


class JournalTail:
    """The complete lines added to one journal (fills/ or orders/: a file per
    session, appended) since the last read. A line still being written is
    left for the next read; a file that shrank was rewritten, and is followed
    from its new end rather than told again."""

    def __init__(self, directory: Path) -> None:
        self.directory = Path(directory)
        self._offsets: dict[str, int] = {}

    def _files(self) -> list[Path]:
        if not self.directory.is_dir():
            return []
        return sorted(
            path
            for path in self.directory.iterdir()
            if path.suffix == ".jsonl" and path.name[:4].isdigit()
        )

    def skip_to_end(self) -> None:
        """What is there now is history: start from each file's end."""
        self._offsets = {}
        for path in self._files():
            try:
                self._offsets[path.name] = path.stat().st_size
            except OSError:
                continue

    def read(self) -> list[dict]:
        rows: list[dict] = []
        present: set[str] = set()
        for path in self._files():
            present.add(path.name)
            offset = self._offsets.get(path.name, 0)
            try:
                size = path.stat().st_size
                if size < offset:
                    self._offsets[path.name] = size
                    continue
                if size == offset:
                    continue
                with open(path, "rb") as handle:
                    handle.seek(offset)
                    chunk = handle.read(size - offset)
            except OSError:
                continue
            end = chunk.rfind(b"\n")
            if end < 0:
                continue
            self._offsets[path.name] = offset + end + 1
            for line in chunk[: end + 1].splitlines():
                try:
                    row = json.loads(line)
                except ValueError:
                    continue
                if isinstance(row, dict) and _float(row.get("t")) is not None:
                    rows.append(row)
        for gone in set(self._offsets) - present:
            del self._offsets[gone]
        return sorted(rows, key=lambda row: float(row["t"]))


def trader_report(status: dict | None, now: float) -> dict | None:
    """The trader's own report (status.json) as apps are shown it, or None
    when no trader has reported. `stale` is server/live.py's rule; `running`
    is a trading loop that is still reporting and has not ended."""
    if not status:
        return None
    updated = _epoch(status.get("updated_at")) if status.get("updated_at") else None
    age = None if updated is None else now - updated
    heartbeat = _float(status.get("heartbeat_seconds")) or 60.0
    stale = age is None or age > max(3 * heartbeat, _STALE_FLOOR_SECONDS)
    state = str(status.get("state") or "unknown")
    process = status.get("process") if isinstance(status.get("process"), str) else None
    lots, orders = status.get("open_lots"), status.get("open_orders")
    return {
        "state": state,
        "detail": str(status.get("detail") or "") or None,
        "process": process,
        "stale": stale,
        "running": process == "loop" and not stale and state not in _LOOP_ENDED,
        "nextOpen": _iso(status.get("next_open")),
        "lastTickAt": _iso(status.get("last_tick_at")),
        # Never its age: that changes every poll, and apps are sent the status
        # whenever it changes.
        "updatedAt": _iso(status.get("updated_at")),
        "openLots": lots if isinstance(lots, int) and not isinstance(lots, bool) else None,
        "openOrders": orders if isinstance(orders, int) and not isinstance(orders, bool) else None,
    }


def engine_part(report: dict | None, deployment: WatchedDeployment) -> dict | None:
    """A trading loop's state in the bridge's engine words, for the status's
    `engine` part; None between sessions, or when the loop stopped reporting."""
    if report is None or report["process"] != "loop" or report["stale"]:
        return None
    raw = report["state"]
    return {
        "mode": deployment.mode,
        "state": _LOOP_STATES.get(raw, raw),
        "detail": report["detail"] or _LOOP_WORDS.get(raw, raw.replace("_", " ")),
        "symbol": deployment.symbol,
        "lastTickAt": report["lastTickAt"],
        "updatedAt": report["updatedAt"],
    }


def _window_key(status: dict | None) -> str | None:
    window = (status or {}).get("last_window")
    if not isinstance(window, dict):
        return None
    return f"{window.get('day')}|{window.get('session')}"


class TraderWatch:
    """One deployment's journals, followed into a hub of its own. poll() is
    called from one thread; the hub is what apps' connections read."""

    def __init__(
        self,
        deployment: WatchedDeployment,
        notifications: Notifications,
        *,
        log: Callable[[str], None] | None = None,
        book: Callable[..., dict | None] = read_book,
    ) -> None:
        self.deployment = deployment
        self.notifications = notifications
        self._log = log or (lambda _message: None)
        self._read_book = book
        self._inbox = ControlInbox(deployment.control_dir)
        self._fills = JournalTail(deployment.control_dir / "fills")
        self._orders = JournalTail(deployment.control_dir / "orders")
        self._started = False
        self._engine_state: str | None = None
        self._stale: bool | None = None
        self._stale_said = False
        self._last_fresh: dict | None = None
        self._window_baseline: str | None = None
        self._next_book = 0.0

    def poll(self, now: float) -> None:
        status = self._inbox.status()
        report = trader_report(status, now)
        engine = engine_part(report, self.deployment)
        if not self._started:
            # Where things stand when it starts is not news.
            self._started = True
            self._fills.skip_to_end()
            self._orders.skip_to_end()
            self._engine_state = engine["state"] if engine else None
            self._stale = report["stale"] if report else None
            self._window_baseline = _window_key(status)
        else:
            fills = self._fills.read()
            for fill in fills:
                self._fill(fill)
            for event in self._orders.read():
                self._order(event)
            self._engine(engine)
            self._staleness(report, now)
            self._window(status)
            if fills:
                self._next_book = 0.0  # the book changed: send it now
        if report is not None and not report["stale"]:
            self._last_fresh = report
        self.notifications.update_status(engine=engine, trader=report)
        if now >= self._next_book:
            self._next_book = now + BOOK_SECONDS
            self.notifications.update_status(book=self._book(now))

    def _book(self, now: float) -> dict | None:
        try:
            return self._read_book(
                self.deployment.state_db, self._inbox, symbol=self.deployment.symbol, now=now
            )
        except Exception as exc:
            self._log(f"[notifier] {self.deployment.id}: the book could not be read: {exc}")
            return None

    # -- what changed -------------------------------------------------------------

    def _engine(self, engine: dict | None) -> None:
        # Between sessions (None) nothing is said, and the last state said is
        # kept: the next session's "starting" is news against it.
        state = engine["state"] if engine else None
        if state is None or state == self._engine_state:
            return
        previous, self._engine_state = self._engine_state, state
        self.notifications.engine_state(engine, previous)

    def _staleness(self, report: dict | None, now: float) -> None:
        if report is None or report["stale"] == self._stale:
            return
        self._stale = report["stale"]
        label = self.deployment.label
        if report["stale"]:
            last = self._last_fresh or report
            if last["state"] in _QUIET_ON_PURPOSE:
                return
            updated = _epoch(report["updatedAt"]) if report["updatedAt"] else None
            ago = (
                f"{_duration(now - updated)} ago"
                if updated is not None
                else "at an unreadable time"
            )
            said = last["state"].replace("_", " ")
            if last["detail"]:
                said += f": {last['detail']}"
            notification = self.notifications.publish(
                "session",
                "Trader not reporting",
                f"{label} last reported {ago} ({said}). Nothing more is known until it "
                "reports again.",
                severity="warning",
                data={"deployment": self.deployment.id, "state": last["state"]},
            )
            self._stale_said = notification is not None
        elif self._stale_said:
            self._stale_said = False
            self.notifications.publish(
                "session",
                "Trader reporting again",
                f"{label}: {report['state'].replace('_', ' ')}"
                + (f", {report['detail']}" if report["detail"] else "")
                + ".",
                data={"deployment": self.deployment.id, "state": report["state"]},
            )

    def _window(self, status: dict | None) -> None:
        key = _window_key(status)
        if key is None or key == self._window_baseline:
            return
        self.notifications.window_summary(dict(status["last_window"]))  # deduped by the hub

    def _fill(self, fill: dict) -> None:
        side = fill.get("side")
        qty, price = _float(fill.get("qty")), _float(fill.get("price"))
        if side not in ("buy", "sell") or not qty or price is None:
            return
        symbol = self.deployment.symbol or ""
        shares = _shares(qty)
        data: dict[str, Any] = {
            "symbol": symbol or None,
            "side": side,
            "qty": qty,
            "price": price,
            "lot": fill.get("lot"),
        }
        if side == "buy":
            value, target = _float(fill.get("value")), _float(fill.get("target_price"))
            data.update(value=value, targetSellPrice=target)
            body = f"{shares} at {_money(price)}" + (f" ({_money(value)})" if value else "") + "."
            if target:
                body += f" Sells at {_money(target)}."
            self.notifications.publish("buy", f"Bought {shares} {symbol}".strip(), body, data=data)
            return
        pnl, reason = _float(fill.get("pnl")), fill.get("reason")
        data.update(
            pnl=pnl,
            reason=reason,
            proceeds=_float(fill.get("proceeds")),
            cost=_float(fill.get("cost")),
        )
        why = _SALE_REASONS.get(reason, str(reason or "").replace("_", " "))
        body = f"{shares} at {_money(price)}"
        if pnl is not None:
            body += f": {_signed(pnl)} after costs"
        body += f" ({why})." if why else "."
        self.notifications.publish(
            "sell",
            f"Sold {shares} {symbol}".strip(),
            body,
            # A sale below cost is only ever a regime exit -- allowed, but worth a look.
            severity="warning" if pnl is not None and pnl < 0 else "info",
            data=data,
        )

    def _order(self, event: dict) -> None:
        what = event.get("event")
        if what not in ("placed", "cancelled", "expired", "rejected"):
            return  # filled ones are in the fill journal; the rest is the routine middle
        side = event.get("kind") if event.get("kind") in ("buy", "sell") else "order"
        qty, limit = _float(event.get("qty")), _float(event.get("limit"))
        filled = _float(event.get("filled_qty")) or 0.0
        symbol = self.deployment.symbol or ""
        summary = " ".join(part for part in (side, _shares(qty) if qty else "", symbol) if part)
        summary += f" at {_money(limit)} limit" if limit else ""
        session = _WINDOWS.get(str(event.get("session") or ""))
        if session:
            summary += f" ({session})"
        why = event.get("why") or event.get("detail")
        data = {
            "orderId": event.get("order"),
            "symbol": symbol or None,
            "side": side,
            "qty": qty,
            "limitPrice": limit,
            "state": what,
            "filledQty": filled,
            "avgPrice": _float(event.get("avg_price")),
        }
        broker = self.deployment.broker_name
        if what == "placed":
            self.notifications.publish(
                "order_update",
                "Order placed",
                f"{summary[:1].upper()}{summary[1:]}, to {broker}.",
                data=data,
            )
        elif what == "rejected":
            self.notifications.publish(
                "order_problem",
                "Order rejected",
                f"{broker} rejected the {summary}" + (f": {why}" if why else "") + ".",
                severity="warning",
                data=data,
            )
        else:
            body = f"{summary[:1].upper()}{summary[1:]}"
            if filled > 0:
                body += f", {_shares(filled)} filled first"
            body += (f": {why}" if why else "") + "."
            self.notifications.publish("order_update", f"Order {what}", body, data=data)


# -- the service ----------------------------------------------------------------------


def load_notifier_key(*, env_file: Path | None = None) -> BridgeApiKey:
    """VAI_NOTIFIER_KEY, refused when it is either of the bridge's keys."""
    key = load_api_key(env_file=env_file, name=NOTIFIER_KEY_ENV_VAR)
    path = env_file or default_env_file()
    for other in (API_KEY_ENV_VAR, NOTIFY_KEY_ENV_VAR):
        value = os.environ.get(other) or read_env_value(path, other)
        if value and value == key.value:
            raise ConfigurationError(
                f"{NOTIFIER_KEY_ENV_VAR} is the same as {other}. Give the trader notifier a key "
                "of its own -- `python -m fidelity_gateway.bridge keygen --notifier`."
            )
    return key


class TraderNotifier:
    """Every watched deployment, one listener: /notifications/<id> each, the
    first also at /notifications."""

    def __init__(
        self,
        deployments: Sequence[WatchedDeployment],
        api_key: BridgeApiKey,
        *,
        host: str = DEFAULT_NOTIFIER_HOST,
        port: int = DEFAULT_NOTIFIER_PORT,
        policy: AddressPolicy | None = None,
        events: Iterable[str] = DEFAULT_EVENTS,
        log: Callable[[str], None] | None = None,
        clock: Callable[[], float] = time.time,
        book: Callable[..., dict | None] = read_book,
    ) -> None:
        if not deployments:
            raise ConfigurationError("The trader notifier needs at least one deployment.")
        self._log = log or (lambda _message: None)
        self._clock = clock
        events = tuple(events)
        self.watches = [
            TraderWatch(
                deployment,
                Notifications(events, clock=clock, log=self._log),
                log=self._log,
                book=book,
            )
            for deployment in deployments
        ]
        first = self.watches[0]
        self.server = NotificationServer(
            api_key,
            first.notifications,
            host=host,
            port=port,
            policy=policy or AddressPolicy(["127.0.0.1", "::1"]),
            log=self._log,
            account=first.deployment.account,
            routes={
                f"{NOTIFY_PATH}/{watch.deployment.id}": NotifyRoute(
                    watch.notifications, watch.deployment.account
                )
                for watch in self.watches
            },
        )

    def poll(self) -> None:
        now = self._clock()
        for watch in self.watches:
            try:
                watch.poll(now)
            except Exception as exc:  # one deployment's files never stop the others
                self._log(f"[notifier] {watch.deployment.id}: {type(exc).__name__}: {exc}")

    def start(self) -> None:
        """Read where each deployment stands, then listen: the first app to
        connect is shown the status, not an empty one."""
        self.poll()
        self.server.start()
        for watch in self.watches:
            d = watch.deployment
            self._log(
                f"[notifier] {d.label} ({d.broker}, {d.mode or 'mode unknown'}): apps may connect "
                f"at {self.server.url_for(f'{NOTIFY_PATH}/{d.id}')}"
            )
        self._log(
            f"[notifier] {self.server.url_for(NOTIFY_PATH)} is {self.watches[0].deployment.label}"
        )

    def run(self, stop: threading.Event, *, poll_seconds: float = POLL_SECONDS) -> None:
        self.start()
        try:
            while not stop.wait(poll_seconds):
                self.poll()
        finally:
            self.server.stop("the trader notifier is restarting")


__all__ = [
    "DEFAULT_NOTIFIER_PORT",
    "JournalTail",
    "TraderNotifier",
    "TraderWatch",
    "WatchedDeployment",
    "engine_part",
    "load_deployments",
    "load_notifier_key",
    "trader_report",
]
