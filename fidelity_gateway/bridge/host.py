"""
The bridge host: one bridge for a Fidelity deployment, up for as long as the
deployment is -- not for one trading session.

--------------------------------------------------------------------
WHY THE BRIDGE STOPPED LIVING IN THE TRADING LOOP

It used to start inside each session's `cli.py live` (live.py connect_live ->
open_bridge -> BridgeServer.start) and stop with it. So between sessions
nothing listened: the extension said OFF every night and weekend, and there
was no way to see the connection was good before the open. Every failed
start closed the bridge and opened it again (the extension's log filled with
1001 closes), and anything else that wanted the bridge -- a check, a run by
hand -- fought the trader for its port: on 10-23 a bridge started by hand
held it all day and the trader failed 65 times.

Now this process holds the port for the deployment's life
(docker-compose.yml's fidelity-bridge service). The extension connects once
and stays connected. Each session's trading loop ATTACHES to it over a Unix
socket (attach.py; VAI_BRIDGE_SOCKET) instead of listening itself, and is
handed what the extension already said -- its auth headers, its tab, its
switches, its order log -- so a session is connected in seconds.

--------------------------------------------------------------------
WHAT IT DOES BESIDES RELAYING

  * One process attached at a time: the session's loop, or a connection
    check. A second is refused, naming the first -- two trading loops on one
    account duplicate orders.
  * Readiness (readiness.py), every second: listening, the extension
    connected and heard from, its version, Fidelity signed in, "Allow
    trading" on, the last account check. Written with everything else into
    its status (`bridge/status.json` in the deployment's control directory),
    which tools/market_hours_supervisor.py waits on before starting a
    session and the Live page shows.
  * Events, as they happen, into `bridge/events/<day>.jsonl`: connects and
    disconnects with their close codes, refusals, sign-ins and sign-outs,
    the trading switch, attaches, the verdict changing, checks. A disconnect
    explains itself after the fact.
  * The account check: a read-only look at the account through the
    extension -- orders, positions, settled cash -- on the Live page's
    `check_connection` (its own inbox, `bridge/`) and by itself 30 and 10
    minutes before the open. And READ BEFORE TRADING: while a session is
    open or within 30 minutes, with nothing attached, a connection is not
    ready until a check has passed through it -- run as soon as the
    extension connects, and again every CHECK_RETRY_SECONDS while it fails.
    A tab's address says "signed in" even after Fidelity's session has
    expired; on 10-26 the trader started on one, could not read the
    account, and left a halt in its ledger. Read-only by construction: FidelitySession's
    defaults allow no previews and no orders, and this module never imports
    the placing broker (a test holds it to both).
  * While nothing is attached it tells the extension what it is doing:
    standing by for the next session, ready or not and why -- "paused"
    within NOT_READY_WARNING_MINUTES of the open when not ready, so the
    extension's badge turns amber in time to fix it.
  * A port held by another program is retried every BIND_RETRY_SECONDS and
    reported, never fatal; a config edit (allowed_clients, say) restarts the
    bridge with it.
  * Apps' notifications (notifications.py, notify_server.py): with
    live.fidelity.bridge.notifications enabled, the listener the Notifier
    app connects to. This host owns the hub, so a bridge restarted with new
    settings keeps the apps' stream, and an edit to the notifications alone
    restarts only their listener -- never the extension's connection. What
    only the host knows reaches them from here: readiness and a warning
    before the open, account checks, a second trader refused or a session
    ending unexpectedly, its own port. A listener that cannot start (no key,
    a taken port) is reported and retried; a phone never stops the bridge.
"""

from __future__ import annotations

import contextlib
import dataclasses
import os
import queue
import socket
import sys
import threading
import time
import uuid
from collections import OrderedDict
from collections.abc import Callable
from datetime import UTC, datetime
from datetime import time as day_time
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

from engine.core import trading_calendar
from engine.core.exceptions import ConfigurationError
from fidelity_gateway.bridge.local import Line, LinkClosed, error_payload
from fidelity_gateway.bridge.notifications import Notifications, close_words
from fidelity_gateway.bridge.notify_server import NotificationServer, NotifySettings
from fidelity_gateway.bridge.readiness import readiness
from fidelity_gateway.bridge.server import (
    BridgeError,
    BridgeRefusal,
    BridgeServer,
    BridgeUnavailable,
)

EASTERN = ZoneInfo("America/New_York")
OPEN = day_time(9, 30)
CLOSE = day_time(16, 0)

# How often the status file is rewritten when nothing changed: the supervisor
# and the Live page call a host silent for three of these "not reporting".
STATUS_SECONDS = 15.0
BIND_RETRY_SECONDS = 30.0
CONFIG_POLL_SECONDS = 30.0
# Read-only account checks before each open, this many minutes ahead.
CHECK_BEFORE_OPEN_MINUTES = (30, 10)
# A connection that must be read before trading (module docstring, READ
# BEFORE TRADING) and failed its check is checked again this often.
CHECK_RETRY_SECONDS = 120.0
# Not ready this close to the open (or during a session): the extension is
# told "paused", so its badge turns amber.
NOT_READY_WARNING_MINUTES = 15
CALL_TIMEOUT_SECONDS = 60.0
HELLO_TIMEOUT_SECONDS = 10.0
# The attached socket's timeout: a send that cannot finish in this long means
# the attached process has stopped reading, and it is detached rather than
# allowed to hold up the extension's connection. Receives just look again.
SEND_TIMEOUT_SECONDS = 10.0
MAX_REQUEST_TIMEOUT_SECONDS = 180.0
# The extension's auth headers, per address, replayed to whoever attaches.
REQUEST_CACHE = 64
ORDER_EVENTS_KEPT = 1000
# A refusal repeated by an extension retrying every minute is journaled once
# per this long unless its reason changes.
REFUSAL_EVENT_EVERY_SECONDS = 600.0
COMMAND_POLL_SECONDS = 2.0
# The readiness apps are shown is sent when what it says changes; its
# details ("last heard 4 s ago") are refreshed at most this often.
APP_STATUS_SECONDS = 60.0

ALGORITHM_CALLS = ("algorithm.describe", "algorithm.set", "algorithm.reset")

_GONE = object()


def _iso(seconds: float | None) -> str | None:
    return datetime.fromtimestamp(seconds, UTC).isoformat() if seconds else None


def _seconds(iso: object) -> float | None:
    if not isinstance(iso, str) or not iso:
        return None
    try:
        return datetime.fromisoformat(iso).timestamp()
    except ValueError:
        return None


def _stderr(message: str) -> None:
    print(message, file=sys.stderr, flush=True)


def session_window(now: float, sessions: tuple = ("regular",)) -> dict[str, Any]:
    """Whether the deployment's trading day is open, and when the next one
    opens: {"open": bool, "next_open": datetime (ET), "closes": datetime |
    None}. The day runs from its first traded window's start to its last's
    end (engine/core/venue_sessions.py, Fidelity's windows; holidays from
    engine/core/trading_calendar.py, early closes not modelled) -- for the
    regular session alone, 09:30-16:00; for a deployment that trades the
    pre-market (live.sessions), from 07:00, so the account is checked and
    readiness warned of before THAT."""
    from engine.core.venue_sessions import VenueCalendar

    calendar = VenueCalendar("fidelity", sessions)
    moment = datetime.fromtimestamp(now, EASTERN)
    day = moment.date()
    span = calendar.day_span(day)
    if span is not None:
        opens, closes = span
        if moment < opens:
            return {"open": False, "next_open": opens, "closes": None}
        if moment < closes:
            return {"open": True, "next_open": opens, "closes": closes}
    following = trading_calendar.next_session(day)
    span = calendar.day_span(following)
    opens = span[0] if span is not None else datetime.combine(following, OPEN, EASTERN)
    return {"open": False, "next_open": opens, "closes": None}


def _when(moment: datetime, now: float) -> str:
    """'09:30 ET' today, 'Mon 09:30 ET' on another day."""
    today = datetime.fromtimestamp(now, EASTERN).date()
    return f"{moment:%H:%M} ET" if moment.date() == today else f"{moment:%a %H:%M} ET"


class _Attachment:
    """The one process attached to the host."""

    def __init__(self, line: Line, client: dict, since: float) -> None:
        self.line = line
        self.client = client
        self.since = since
        self.status: dict | None = None  # its engine status, as last sent
        self.methods: set[str] = set()
        self.calls: dict[str, queue.Queue] = {}
        self.welcomed = False

    def describe(self) -> str:
        process = self.client.get("process") or "process"
        what = {"loop": "the trading loop", "check": "a connection check"}.get(
            process, f"a {process}"
        )
        pid = self.client.get("pid")
        return f"{what}{f' (pid {pid})' if pid else ''}"

    def summary(self) -> dict:
        return {
            "process": self.client.get("process"),
            "pid": self.client.get("pid"),
            "deployment": self.client.get("deployment"),
            "build": self.client.get("build"),
            "since": _iso(self.since),
            "status": self.status,
        }


class _Feed:
    """What a BridgePage needs of a server, for the host's own account check:
    requests go to the bridge, events come from the host's fan-out (with
    what the extension already said replayed first)."""

    def __init__(self, host: BridgeHost) -> None:
        self._host = host
        self._events: queue.Queue = queue.Queue()

    def put(self, name: str, data: dict) -> None:
        self._events.put((name, data))

    def request(self, command: str, args: dict, *, timeout: float = 45.0) -> dict:
        return self._host.server.request(command, args, timeout=timeout)

    def next_event(self, timeout: float = 0.0) -> tuple[str, dict] | None:
        try:
            if timeout <= 0:
                return self._events.get_nowait()
            return self._events.get(timeout=timeout)
        except queue.Empty:
            return None


ServerFactory = Callable[..., BridgeServer]
Checker = Callable[..., str]


class BridgeHost:
    """The deployment's bridge, its local socket, its status and its journal.

    `make_server(settings, on_event)` builds the BridgeServer for a
    FidelityBridgeConfig (main() passes the real one; tests their own).
    `notifications` is the hub apps hear through (every server built is
    handed it), and `make_notifier(settings, notifications)` builds their
    listener for a NotifySettings -- None runs none.
    `settings()` returns the deployment's current (FidelityConfig, symbol),
    re-read when the config file changes; `check(page, may_navigate=...)`
    runs the read-only account check and returns what it found, raising on
    failure. `inbox` is the host's own control directory (bridge/): its
    status, events and the Live page's check_connection commands.
    """

    def __init__(
        self,
        *,
        make_server: ServerFactory,
        settings: Callable[[], tuple[Any, str]],
        socket_path: str | Path,
        inbox=None,
        check: Checker | None = None,
        deployment: str | None = None,
        build: dict | None = None,
        clock: Callable[[], float] = time.time,
        log: Callable[[str], None] = _stderr,
        notifications: Notifications | None = None,
        make_notifier: Callable[[NotifySettings, Notifications], NotificationServer] | None = None,
        sessions: Callable[[], tuple] | None = None,
    ) -> None:
        self._make_server = make_server
        self._settings_source = settings
        # The windows the deployment trades (live.sessions): when its trading
        # day starts, for the checks before it and the warning near it.
        self._sessions_source = sessions
        self._sessions = self._read_sessions()
        self.socket_path = Path(socket_path)
        self.inbox = inbox
        self._check = check
        self.deployment = deployment
        self._build = build or {}
        self._clock = clock
        self._log = log

        self._fidelity, self._symbol = settings()
        self.notifications = notifications if notifications is not None else Notifications(())
        self._make_notifier = make_notifier
        self._notifier: NotificationServer | None = None
        self._notifier_error: str | None = None
        self._next_notifier = 0.0
        self._app_status: tuple[dict, dict, float] | None = None
        self.server: BridgeServer = self._new_server()
        self._listening = False
        self._listen_error: str | None = None
        self._next_bind = 0.0

        self._lock = threading.RLock()  # the attachment, the caches, the fan-out
        self._attached: _Attachment | None = None
        self._requests: OrderedDict[str, dict] = OrderedDict()
        self._tab_event: dict | None = None
        self._permissions_event: dict | None = None
        self._orders_event: dict | None = None
        self._order_events: list[dict] = []
        self._feeds: set[_Feed] = set()

        self._check_lock = threading.Lock()
        self.last_check: dict | None = None
        self._checked_for: set[tuple] = set()
        # The connection (its "since") the last check ran through, the one
        # the read-before-trading checks are for, and when the next may run.
        # Matched by connection, not by time: the host's clock and the
        # server's need not agree.
        self._check_since: str | None = None
        self._auto_since: str | None = None
        self._next_auto_check = 0.0

        self._seen: dict[str, Any] = {}
        self._verdict: dict | None = None
        self._standby_sent: dict | None = None
        self._written_at = 0.0
        self._written: dict | None = None
        self._connection_sent: tuple[float, dict] | None = None
        self._listener: socket.socket | None = None
        self._threads: list[threading.Thread] = []
        self._applier = None
        self._install_defaults()

    # -- the bridge itself ------------------------------------------------------

    @property
    def mode(self) -> str:
        """ "live" places real orders, "preview" does not (dry_run)."""
        return "preview" if self._fidelity.dry_run else "live"

    def _new_server(self) -> BridgeServer:
        server = self._make_server(self._fidelity.bridge, self._on_extension_event)
        server.notify_through(self.notifications)
        return server

    def _install_defaults(self) -> None:
        """With no trading loop attached, the extension's algorithm editor is
        told where to go instead of "unknown method"."""

        def nothing_attached(_args: dict) -> dict:
            raise PermissionError(
                "No trading session is running now, so there is no algorithm to change here. "
                "Change it on the Live page -- it applies at the next session -- or here once "
                "a session runs."
            )

        for method in ALGORITHM_CALLS:
            self.server.register_call(method, nothing_attached)

    def bind(self) -> bool:
        """Listen for the extension; on a taken port, say so and try again
        BIND_RETRY_SECONDS later."""
        now = self._clock()
        try:
            self.server.start()
        except BridgeUnavailable as exc:
            first = self._listen_error is None
            self._listening, self._listen_error = False, str(exc)
            self._next_bind = now + BIND_RETRY_SECONDS
            if first:
                self._log(f"[bridge-host] {exc} Trying again every {BIND_RETRY_SECONDS:.0f}s.")
                self._journal("port_conflict", str(exc), t=now)
                self.notifications.bridge_port_conflict(str(exc))
            return False
        self._listening, self._listen_error = True, None
        self._log(f"[bridge-host] listening for the extension on {self.server.url}")
        self._journal("listening", f"Listening for the extension on {self.server.url}.", t=now)
        self.notifications.bridge_listening(self.server.url)
        return True

    def _read_sessions(self, keep: tuple = ("regular",)) -> tuple:
        if self._sessions_source is None:
            return ("regular",)
        try:
            return tuple(self._sessions_source())
        except Exception as exc:
            self._log(f"[bridge-host] the trading windows do not load ({exc}); keeping {keep}")
            return keep

    def reload(self) -> bool:
        """Re-read the deployment's settings; restart the bridge when where
        or whom it listens for changed. False when nothing did."""
        self._sessions = self._read_sessions(self._sessions)
        try:
            fidelity, symbol = self._settings_source()
        except Exception as exc:
            self._log(f"[bridge-host] the config does not load ({exc}); keeping the last one")
            return False
        changed = _extension_side(fidelity.bridge) != _extension_side(self._fidelity.bridge)
        notify_changed = _notify_side(fidelity.bridge) != _notify_side(self._fidelity.bridge)
        self._fidelity, self._symbol = fidelity, symbol
        if notify_changed:
            self._log("[bridge-host] the apps' notification settings changed: restarting them")
            self.start_notifier()
        if not changed:
            return False
        self._log("[bridge-host] the bridge's settings changed: restarting it with them")
        self._journal("config", "The bridge's settings changed: restarting it with them.")
        self.notifications.bridge_restarting()
        with contextlib.suppress(Exception):
            self.server.stop()
        self.server = self._new_server()
        self._install_defaults()
        attached = self._attached
        if attached is not None:
            for method in attached.methods:
                self.server.register_call(method, self._forwarder(attached, method))
            if attached.status is not None:
                self.server.set_engine_status(attached.status)
        self._listening, self._listen_error, self._next_bind = False, None, 0.0
        self._standby_sent = None
        self.bind()
        return True

    # -- what the extension sends: kept for replay, and fanned out -------------

    def _on_extension_event(self, name: str, data: dict) -> None:
        """On the bridge's connection thread, for every event the extension
        sends. Kept for whoever attaches next, and passed to whoever is
        attached now -- under one lock with the replay, so an attaching
        process sees every event exactly once, replayed or live."""
        with self._lock:
            if name == "request":
                key = str(data.get("url"))
                self._requests.pop(key, None)
                self._requests[key] = data
                while len(self._requests) > REQUEST_CACHE:
                    self._requests.popitem(last=False)
            elif name == "tab":
                self._tab_event = data
            elif name == "permissions":
                self._permissions_event = data
            elif name == "orders":
                self._orders_event, self._order_events = data, []
            elif name == "order":
                self._order_events = [*self._order_events, data][-ORDER_EVENTS_KEPT:]
            attached = self._attached
            if attached is not None and attached.welcomed:
                self._send(attached, {"type": "event", "event": name, "data": data})
            if name in ("request", "tab"):
                for feed in self._feeds:
                    feed.put(name, data)

    def _replay(self) -> list[list]:
        """What the extension has said that a process attaching now needs:
        its auth headers, its tab, its switches, its order log."""
        events: list[list] = [["request", data] for data in self._requests.values()]
        if self._tab_event is not None:
            events.append(["tab", self._tab_event])
        if self._permissions_event is not None:
            events.append(["permissions", self._permissions_event])
        if self._orders_event is not None:
            events.append(["orders", self._orders_event])
        events.extend(["order", data] for data in self._order_events)
        return events

    def _forget_extension(self) -> None:
        """The extension went away: what it said no longer holds. It says
        all of it again when it reconnects (its onReady)."""
        with self._lock:
            self._requests.clear()
            self._tab_event = self._permissions_event = None

    # -- the local socket: one process attached at a time -----------------------

    @staticmethod
    def _send(attachment: _Attachment, message: dict) -> bool:
        """Send to the attached process; a send that fails closes its link,
        so its reader detaches it instead of a dead link lingering."""
        try:
            attachment.line.send(message)
            return True
        except LinkClosed:
            attachment.line.close()
            return False

    def open_socket(self) -> None:
        path = self.socket_path
        path.parent.mkdir(parents=True, exist_ok=True)
        with contextlib.suppress(OSError):
            os.chmod(path.parent, 0o700)
        if path.exists() or path.is_symlink():
            probe = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            try:
                probe.settimeout(1.0)
                probe.connect(str(path))
            except OSError:
                path.unlink()  # a socket file left by a host that stopped
            else:
                raise ConfigurationError(f"Another bridge host already listens at {path}.")
            finally:
                probe.close()
        listener = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        listener.bind(str(path))
        os.chmod(path, 0o600)
        listener.listen(4)
        self._listener = listener
        self._spawn(self._accept, "bridge-host-accept")

    def _spawn(self, target: Callable, name: str, *args: Any) -> threading.Thread:
        thread = threading.Thread(target=target, args=args, name=name, daemon=True)
        thread.start()
        self._threads.append(thread)
        return thread

    def _accept(self) -> None:
        listener = self._listener
        while listener is not None:
            try:
                connection, _ = listener.accept()
            except OSError:
                return  # closed: the host is stopping
            self._spawn(self._serve_attachment, "bridge-host-attached", connection)

    def _serve_attachment(self, connection: socket.socket) -> None:
        line = Line(connection)
        try:
            connection.settimeout(HELLO_TIMEOUT_SECONDS)
            hello = line.receive()
        except (LinkClosed, OSError):
            line.close()
            return
        if hello.get("type") != "hello":
            line.close()
            return
        client = hello.get("client") if isinstance(hello.get("client"), dict) else {}
        client = {key: client.get(key) for key in ("process", "pid", "deployment", "build")}
        now = self._clock()
        with self._lock:
            holder = self._attached
            if holder is not None:
                reason = (
                    f"{holder.describe()} is attached to this deployment's bridge (since "
                    f"{datetime.fromtimestamp(holder.since, EASTERN):%H:%M} ET); one process "
                    "at a time -- two trading loops on one account would duplicate orders"
                )
                with contextlib.suppress(LinkClosed):
                    line.send({"type": "refused", "reason": reason})
                line.close()
                newcomer = _Attachment(line, client, now)
                self._journal(
                    "attach_refused",
                    f"Refused {newcomer.describe()}: {reason}.",
                    t=now,
                )
                self.notifications.session_refused(f"Refused {newcomer.describe()}: {reason}.")
                return
            attachment = _Attachment(line, client, now)
            self._attached = attachment
            try:
                connection.settimeout(SEND_TIMEOUT_SECONDS)
                line.send(
                    {
                        "type": "welcome",
                        "replay": self._replay(),
                        "connection": self.server.connection_report(),
                    }
                )
            except (LinkClosed, OSError):
                self._attached = None
                line.close()
                return
            attachment.welcomed = True
        self._log(f"[bridge-host] {attachment.describe()} attached")
        self._journal("attached", f"{attachment.describe().capitalize()} attached.", t=now)
        try:
            while True:
                try:
                    message = line.receive()
                except TimeoutError:
                    continue  # nothing to read yet; the timeout bounds sends
                if message.get("type") == "bye":
                    break
                self._from_attached(attachment, message)
        except (LinkClosed, OSError):
            pass
        finally:
            self._detach(attachment)

    def _from_attached(self, attachment: _Attachment, message: dict) -> None:
        kind = message.get("type")
        if kind == "request":
            self._spawn(self._relay, "bridge-host-request", attachment, message)
        elif kind == "status":
            engine = message.get("engine")
            if isinstance(engine, dict):
                attachment.status = engine
                self.server.set_engine_status(engine)
        elif kind == "register":
            method = message.get("method")
            if isinstance(method, str) and 0 < len(method) <= 100:
                attachment.methods.add(method)
                self.server.register_call(method, self._forwarder(attachment, method))
        elif kind == "result":
            waiter = attachment.calls.get(str(message.get("id")))
            if waiter is not None:
                with contextlib.suppress(queue.Full):
                    waiter.put_nowait(message)

    def _relay(self, attachment: _Attachment, message: dict) -> None:
        """One request, through the bridge, answered on the link."""
        request_id = message.get("id")
        command = str(message.get("command") or "")
        args = message.get("args") if isinstance(message.get("args"), dict) else {}
        try:
            timeout = min(float(message.get("timeout") or 45.0), MAX_REQUEST_TIMEOUT_SECONDS)
        except (TypeError, ValueError):
            timeout = 45.0
        try:
            result = self.server.request(command, args, timeout=timeout)
            reply = {"type": "response", "id": request_id, "ok": True, "result": result}
        except (BridgeRefusal, BridgeError) as exc:  # BridgeUnavailable is a refusal
            reply = {"type": "response", "id": request_id, "ok": False, "error": error_payload(exc)}
        except Exception as exc:
            # Not the bridge's own: it may have reached the extension, so it
            # is carried as "may have run" -- never as a refusal.
            reply = {
                "type": "response",
                "id": request_id,
                "ok": False,
                "error": {
                    "kind": "error",
                    "code": "internal_error",
                    "message": f"{type(exc).__name__}: {exc}",
                },
            }
        self._send(attachment, reply)

    def _forwarder(self, attachment: _Attachment, method: str) -> Callable[[dict], dict]:
        """The extension's call of `method`, answered by the attached process."""

        def forward(args: dict) -> dict:
            if self._attached is not attachment:
                raise PermissionError("The trading session that offered this has ended.")
            call_id = uuid.uuid4().hex
            waiter: queue.Queue = queue.Queue(maxsize=1)
            attachment.calls[call_id] = waiter
            try:
                if not self._send(
                    attachment, {"type": "call", "id": call_id, "method": method, "args": args}
                ):
                    raise PermissionError("The trading session ended before answering.")
                answer = waiter.get(timeout=CALL_TIMEOUT_SECONDS)
            except queue.Empty:
                raise RuntimeError(
                    f"The trading session did not answer {method} in time."
                ) from None
            finally:
                attachment.calls.pop(call_id, None)
            if answer is _GONE:
                raise PermissionError("The trading session ended before answering.")
            if answer.get("ok") is True:
                result = answer.get("result")
                return result if isinstance(result, dict) else {}
            error = answer.get("error") if isinstance(answer.get("error"), dict) else {}
            text = str(error.get("message") or "no reason given")
            if error.get("code") == "invalid":
                raise ConfigurationError(text)
            if error.get("code") == "not_allowed":
                raise PermissionError(text)
            raise RuntimeError(text)

        return forward

    def _detach(self, attachment: _Attachment) -> None:
        with self._lock:
            if self._attached is not attachment:
                return
            # Before the attachment goes: a tick that sees it gone must also
            # see that the extension is owed the host's own status again.
            self._standby_sent = None
            self._attached = None
        for method in attachment.methods:
            self.server.unregister_call(method)
        self._install_defaults()
        for waiter in list(attachment.calls.values()):
            with contextlib.suppress(queue.Full):
                waiter.put_nowait(_GONE)
        attachment.line.close()
        self._log(f"[bridge-host] {attachment.describe()} detached")
        self._journal("detached", f"{attachment.describe().capitalize()} detached.")
        self.notifications.session_ended(
            process=attachment.client.get("process"),
            who=attachment.describe(),
            status=attachment.status,
        )

    @property
    def attached(self) -> dict | None:
        attachment = self._attached
        return attachment.summary() if attachment is not None else None

    # -- the account check ------------------------------------------------------

    def run_check(self, by: str) -> dict:
        """The read-only account check, through the extension. Returns
        {"at", "ok", "detail", "by"}; never raises. One at a time: a second
        asked for meanwhile is answered as such, and changes nothing."""
        if not self._check_lock.acquire(blocking=False):
            return {
                "at": _iso(self._clock()),
                "ok": False,
                "detail": "a check is already running",
                "by": by,
                "busy": True,
            }
        through = None  # the connection it ran through: its "since"
        try:
            if self._check is None:
                detail, ok = "this host was started without an account check", False
            elif not self.server.connected:
                detail, ok = "no extension is connected", False
            else:
                through = self.server.connection_report().get("since")
                feed = _Feed(self)
                with self._lock:
                    for name, data in self._replay():
                        if name in ("request", "tab"):
                            feed.put(name, data)
                    self._feeds.add(feed)
                try:
                    from fidelity_gateway.bridge.page import BridgePage

                    detail = self._check(BridgePage(feed), may_navigate=self._attached is None)
                    ok = True
                except Exception as exc:
                    detail, ok = f"{type(exc).__name__}: {exc}", False
                finally:
                    with self._lock:
                        self._feeds.discard(feed)
            result = {"at": _iso(self._clock()), "ok": ok, "detail": str(detail), "by": by}
        finally:
            self._check_lock.release()
        self.last_check, self._check_since = result, through
        self._journal(
            "check",
            f"Account check {'passed' if result['ok'] else 'failed'}: {result['detail']}",
            ok=result["ok"],
            by=by,
        )
        self.notifications.account_check(result)
        return result

    def _check_first(self, window: dict, now: float) -> bool:
        """Whether a connection must be read before it is ready (module
        docstring, READ BEFORE TRADING): a session open or within the first
        pre-open check, nothing attached, and a check to run."""
        if self._check is None or self._attached is not None:
            return False
        if window["open"]:
            return True
        return (window["next_open"].timestamp() - now) / 60 <= max(CHECK_BEFORE_OPEN_MINUTES)

    def _auto_check(self, now: float, window: dict, report: dict) -> None:
        """30 and 10 minutes before each open, with nothing attached. A host
        started late runs one check for every moment it already passed.
        And, when a connection must be read before trading, on connecting
        and every CHECK_RETRY_SECONDS while its check fails."""
        since = report.get("since") if report["connected"] else None
        if since != self._auto_since:
            self._auto_since, self._next_auto_check = since, 0.0  # a new connection
        if not window["open"]:
            minutes = (window["next_open"].timestamp() - now) / 60
            due = [
                before
                for before in CHECK_BEFORE_OPEN_MINUTES
                if minutes <= before
                and (window["next_open"].isoformat(), before) not in self._checked_for
            ]
            if due:
                self._checked_for.update(
                    (window["next_open"].isoformat(), before) for before in due
                )
                if self.server.connected and self._attached is None:
                    self._next_auto_check = now + CHECK_RETRY_SECONDS
                    self._spawn(
                        self.run_check, "bridge-host-check", f"{min(due)} min before the open"
                    )
                    return
        if since is None or not self._check_first(window, now):
            return
        checked = self.last_check is not None and self._check_since == since
        if (checked and self.last_check["ok"]) or now < self._next_auto_check:
            return
        self._next_auto_check = now + CHECK_RETRY_SECONDS
        self._spawn(
            self.run_check,
            "bridge-host-check",
            "again: the last check failed" if checked else "the extension connected",
        )

    def poll_commands(self) -> list[dict]:
        """Apply the Live page's check_connection commands, from the host's
        own inbox. Returns the results written."""
        if self.inbox is None:
            return []
        if self._applier is None:
            from engine.trading.operator_control import CommandRejected, ControlApplier

            def check(command) -> str:
                result = self.run_check(by=command.operator)
                if result.get("busy"):
                    raise CommandRejected("a check is already running; its result will show")
                if not result["ok"]:
                    raise CommandRejected(f"the check failed: {result['detail']}")
                return result["detail"]

            self._applier = ControlApplier(
                self.inbox, {"check_connection": check}, clock=self._clock
            )
        return self._applier.poll()

    def _commands(self, stop: threading.Event) -> None:
        while not stop.wait(COMMAND_POLL_SECONDS):
            try:
                self.poll_commands()
            except Exception as exc:
                self._log(f"[bridge-host] the command inbox failed: {type(exc).__name__}: {exc}")

    # -- every second: the journal, the verdict, the extension, the status -------

    def tick(self) -> dict:
        """One look at everything; returns the status it wrote (or would)."""
        now = self._clock()
        if not self._listening and now >= self._next_bind:
            self.bind()
        if self._notifier_error is not None and now >= self._next_notifier:
            self.start_notifier()
        report = self.server.connection_report()
        self._journal_changes(report)
        if not report["connected"] and (self._tab_event or self._requests):
            self._forget_extension()
        window = session_window(now, self._sessions)
        verdict = readiness(
            listening=self._listening,
            listen_error=self._listen_error,
            report=report,
            mode=self.mode,
            now=now,
            check=self.last_check,
            check_first=self._check_first(window, now),
        )
        if (
            self._verdict is None
            or self._verdict["ready"] != verdict["ready"]
            or (not verdict["ready"] and self._verdict["summary"] != verdict["summary"])
        ):
            self._journal(
                "ready" if verdict["ready"] else "not_ready",
                "Ready to trade." if verdict["ready"] else f"Not ready: {verdict['summary']}.",
                t=now,
            )
        self._verdict = verdict
        opens_in = (window["next_open"].timestamp() - now) / 60
        self.notifications.readiness(
            verdict,
            now=now,
            session_open=window["open"],
            opens_soon=not window["open"] and opens_in <= NOT_READY_WARNING_MINUTES,
            opens_in_minutes=opens_in,
            next_open=window["next_open"].astimezone(UTC).isoformat(),
        )
        self._tell_extension(verdict, window, now)
        self._auto_check(now, window, report)
        self._send_connection(report, now)
        self._publish_app_status(verdict, window, now)
        return self._write_status(report, verdict, window, now)

    def _journal_changes(self, report: dict) -> None:
        seen = self._seen
        now = self._clock()
        gone = report.get("last_disconnect") or None
        if gone and gone.get("at") != seen.get("gone_at"):
            seen["gone_at"] = gone.get("at")
            self._journal(
                "disconnected",
                f"The extension at {gone.get('client')} disconnected "
                f"({close_words(gone.get('code'), gone.get('reason'))}).",
                t=_seconds(gone.get("at")),
                code=gone.get("code"),
                client=gone.get("client"),
            )
        if report.get("connected") and report.get("since") != seen.get("since"):
            seen["since"] = report.get("since")
            self._journal(
                "connected",
                f"The extension {report.get('version') or ''} connected from "
                f"{report.get('client')}.".replace("  ", " "),
                t=_seconds(report.get("since")),
                client=report.get("client"),
                version=report.get("version"),
            )
        refused = report.get("last_refused") or None
        if refused and refused.get("at") != seen.get("refused_at"):
            seen["refused_at"] = refused.get("at")
            same = (refused.get("client"), refused.get("reason")) == seen.get("refused")
            if not same or now - seen.get("refused_logged", 0.0) >= REFUSAL_EVENT_EVERY_SECONDS:
                seen["refused"] = (refused.get("client"), refused.get("reason"))
                seen["refused_logged"] = now
                self._journal(
                    "refused",
                    f"Turned away {refused.get('client')}: {refused.get('reason')}.",
                    t=_seconds(refused.get("at")),
                    client=refused.get("client"),
                )
        if not report.get("connected"):
            seen.pop("tab", None)
            seen.pop("place", None)
            return
        tab = (report.get("fidelity_tab") or {}).get("state")
        if tab and tab != seen.get("tab"):
            seen["tab"] = tab
            words = {
                "signed_in": "Fidelity is signed in.",
                "signed_out": "Fidelity signed you out.",
                "no_tab": "No Fidelity tab is open.",
                "elsewhere": "The Fidelity tab is not on the signed-in site.",
            }
            self._journal("fidelity", words.get(tab, tab), state=tab)
        place = (report.get("permissions") or {}).get("place")
        if place is not None and place != seen.get("place"):
            seen["place"] = place
            self._journal(
                "trading",
                f'"Allow trading" is {"on" if place else "off"} in the extension.',
                on=bool(place),
            )

    def _tell_extension(self, verdict: dict, window: dict, now: float) -> None:
        """While nothing is attached (or the attached process has said
        nothing yet), what the host is doing -- for the extension's popup."""
        attached = self._attached
        if attached is not None and attached.status is not None:
            return
        if window["open"]:
            when = f"a session is open until {_when(window['closes'], now)}"
        else:
            when = f"the next session opens {_when(window['next_open'], now)}"
        soon = window["open"] or (
            window["next_open"].timestamp() - now <= NOT_READY_WARNING_MINUTES * 60
        )
        if attached is not None:
            state, detail = "starting", f"{attached.describe()} is starting"
        elif verdict["ready"]:
            state, detail = "running", f"{when}; ready"
        else:
            state = "paused" if soon else "running"
            detail = f"{when}; not ready -- {verdict['summary']}"
        status = {
            "mode": "bridge",
            "state": state,
            "detail": detail,
            "ready": verdict["ready"],
            "nextOpen": window["next_open"].astimezone(UTC).isoformat(),
        }
        if self.deployment:
            status["deployment"] = self.deployment
        if status == self._standby_sent:
            return
        self._standby_sent = dict(status)
        self.server.set_engine_status({**status, "updatedAt": _iso(now)})

    def _send_connection(self, report: dict, now: float) -> None:
        """The extension's connection, to the attached process: on a change,
        and every STATUS_SECONDS so its "last heard" stays current."""
        attached = self._attached
        if attached is None or not attached.welcomed:
            self._connection_sent = None
            return
        timeless = {key: value for key, value in report.items() if key != "last_heard"}
        previous = self._connection_sent
        if previous is not None and previous[1] == timeless and now - previous[0] < STATUS_SECONDS:
            return
        self._connection_sent = (now, timeless)
        self._send(attached, {"type": "connection", "report": report})

    def _write_status(self, report: dict, verdict: dict, window: dict, now: float) -> dict:
        state = "listening" if self._listening else "port_conflict"
        status = {
            "state": state,
            "detail": verdict["summary"],
            "process": "bridge",
            "heartbeat_seconds": STATUS_SECONDS,
            "listening": self._listening,
            "listen_error": self._listen_error,
            "mode": self.mode,
            "deployment": self.deployment,
            "symbol": self._symbol,
            "account_name": self._fidelity.account_name,
            "max_order_value": self._fidelity.max_order_value,
            "connection": report,
            "attached": self.attached,
            "readiness": verdict,
            "last_check": self.last_check,
            "session_open": window["open"],
            "next_open": window["next_open"].astimezone(UTC).isoformat(),
            "build": self._build,
        }
        # What changes every tick -- the extension's last ping, the attached
        # loop's own report -- is rewritten every STATUS_SECONDS; the rest at
        # once when it changes.
        timeless = {
            **status,
            "connection": {k: v for k, v in report.items() if k != "last_heard"},
            "attached": {k: v for k, v in (status["attached"] or {}).items() if k != "status"},
        }
        if timeless == self._written and now - self._written_at < STATUS_SECONDS:
            return status
        self._written, self._written_at = timeless, now
        if self.inbox is not None:
            self.inbox.write_status(**status)
        return status

    # -- apps' notifications -------------------------------------------------------

    def start_notifier(self) -> None:
        """(Re)start the apps' listener the config asks for, or stop it when
        it asks for none. A listener that cannot start -- no
        FIDELITY_BRIDGE_NOTIFY_KEY, its port taken -- is reported and tried
        again every BIND_RETRY_SECONDS; the extension's bridge never waits on
        it."""
        self._stop_notifier("the bridge's notification settings changed")
        settings = NotifySettings.from_config(self._fidelity.bridge.notifications)
        if settings is None or self._make_notifier is None:
            self._notifier_error = None
            return
        self.notifications.set_events(settings.events)
        try:
            notifier = self._make_notifier(settings, self.notifications)
            notifier.start()
        except Exception as exc:
            first = self._notifier_error is None
            self._notifier_error = str(exc)
            self._next_notifier = self._clock() + BIND_RETRY_SECONDS
            if first:
                self._log(
                    f"[bridge-host] apps' notifications could not start: {exc} Trying again "
                    f"every {BIND_RETRY_SECONDS:.0f}s."
                )
                self._journal("notifications", f"Apps' notifications could not start: {exc}")
            return
        self._notifier, self._notifier_error = notifier, None
        self._log(
            f"[bridge-host] apps may connect for notifications at {notifier.url} (allowed: "
            f"{', '.join(settings.allowed_clients)}; events: "
            f"{', '.join(self.notifications.events) or 'none'})"
        )
        self._journal("notifications", f"Apps may connect for notifications at {notifier.url}.")

    def _stop_notifier(self, reason: str) -> None:
        notifier, self._notifier = self._notifier, None
        if notifier is not None:
            with contextlib.suppress(Exception):
                notifier.stop(reason)

    @property
    def notifier(self) -> NotificationServer | None:
        return self._notifier

    def _publish_app_status(self, verdict: dict, window: dict, now: float) -> None:
        """The host's part of what apps are shown: the readiness checklist,
        what is attached, the last account check, the next open. Sent when
        any of it changes; the checklist's wording ("last heard 4 s ago") is
        refreshed at most every APP_STATUS_SECONDS, so a phone is not woken
        every second."""
        attached = self.attached
        bridge = {
            "listening": self._listening,
            "listenError": self._listen_error,
            "mode": self.mode,
            "deployment": self.deployment,
            "symbol": self._symbol,
            "ready": verdict["ready"],
            "blocking": verdict["blocking"],
            "summary": verdict["summary"],
            "fix": verdict["fix"],
            "items": [dict(item) for item in verdict["items"]],
            "attached": (
                {"process": attached.get("process"), "since": attached.get("since")}
                if attached
                else None
            ),
            "lastCheck": self.last_check,
            "sessionOpen": window["open"],
            "nextOpen": window["next_open"].astimezone(UTC).isoformat(),
        }
        meaning = {
            **bridge,
            "summary": None,
            "items": [
                {key: value for key, value in item.items() if key != "detail"}
                for item in bridge["items"]
            ],
        }
        previous = self._app_status
        if previous is not None and (
            previous[0] == meaning
            and (previous[1] == bridge or now - previous[2] < APP_STATUS_SECONDS)
        ):
            return
        self._app_status = (meaning, bridge, now)
        self.notifications.update_status(bridge=bridge)

    def _journal(self, kind: str, detail: str, *, t: float | None = None, **fields: Any) -> None:
        if self.inbox is None:
            return
        self.inbox.record_event(
            {"t": t if t is not None else self._clock(), "kind": kind, "detail": detail, **fields}
        )

    # -- running -------------------------------------------------------------------

    def run(self, stop: threading.Event, config_changed: Callable[[], bool] | None = None) -> None:
        """Until `stop` is set: listen, serve the socket, tick every second."""
        self.open_socket()
        self._journal("started", "The bridge host started.")
        self.bind()
        self.start_notifier()
        if self.inbox is not None:
            self._spawn(self._commands, "bridge-host-commands", stop)
        next_config = self._clock() + CONFIG_POLL_SECONDS
        try:
            while not stop.is_set():
                try:
                    self.tick()
                except Exception as exc:  # a status write must never stop the bridge
                    self._log(f"[bridge-host] tick failed: {type(exc).__name__}: {exc}")
                if config_changed is not None and self._clock() >= next_config:
                    next_config = self._clock() + CONFIG_POLL_SECONDS
                    if config_changed():
                        self.reload()
                stop.wait(1.0)
        finally:
            self.close()

    def close(self) -> None:
        listener, self._listener = self._listener, None
        if listener is not None:
            with contextlib.suppress(OSError):
                listener.close()
            with contextlib.suppress(OSError):
                self.socket_path.unlink()
        attachment = self._attached
        if attachment is not None:
            attachment.line.close()
        with contextlib.suppress(Exception):
            self.server.stop()
        self._stop_notifier("the bridge host is stopping: a restart or a deploy")
        self._journal("stopped", "The bridge host stopped.")
        if self.inbox is not None:
            self.inbox.write_status(
                state="stopped",
                detail="the bridge host stopped",
                process="bridge",
                heartbeat_seconds=STATUS_SECONDS,
                listening=False,
            )


def _extension_side(bridge) -> Any:
    """live.fidelity.bridge without its notifications: what the extension's
    connection depends on."""
    return dataclasses.replace(bridge, notifications=None)


def _notify_side(bridge) -> Any:
    return bridge.notifications


def account_checker(symbol_of: Callable[[], tuple[Any, str]]) -> Checker:
    """The host's read-only account check: auth headers (navigating to
    Trader+ for them only when `may_navigate` -- never while a trading loop
    is attached), then the account's orders, positions and settled cash.
    FidelitySession's defaults allow neither previews nor orders."""

    def check(page, *, may_navigate: bool) -> str:
        from fidelity_gateway.broker import FidelityBroker
        from fidelity_gateway.session import FidelitySession, FidelitySessionError

        fidelity, symbol = symbol_of()
        session = FidelitySession(page)
        session.attach()
        try:
            session.wait_for_credentials(timeout_seconds=10)
        except FidelitySessionError:
            if not may_navigate:
                raise FidelitySessionError(
                    "no Fidelity auth headers seen yet, and a trading session is attached: not "
                    "moving its tab"
                ) from None
            session.prime()
            session.wait_for_credentials(timeout_seconds=60)
        session.assert_authenticated()
        broker = FidelityBroker(
            session,
            fidelity.account,
            tuple(fidelity.allowed_accounts) or (fidelity.account,),
            symbol=symbol,
            account_name=fidelity.account_name,
        )
        orders = broker._orders()
        positions = broker._positions()
        cash = broker._cash()
        held = float(positions.get(symbol, 0.0) or 0.0)
        return f"{len(orders)} order(s) listed, {symbol} {held:g} share(s), settled cash " + (
            "unknown" if cash is None else f"${cash:,.2f}"
        )

    return check


__all__ = [
    "ALGORITHM_CALLS",
    "BIND_RETRY_SECONDS",
    "STATUS_SECONDS",
    "BridgeHost",
    "account_checker",
    "session_window",
]
