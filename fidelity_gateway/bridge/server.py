"""
The engine's end of the browser bridge: a WebSocket server the Fidelity
Bridge extension connects to.

The extension cannot listen -- browsers do not let an extension open a
server socket -- so the engine does, at ws://<host>:<port>/fidelity-bridge.
Before a connection can do anything it must pass, in order:

  1. the CLIENT ADDRESS policy (allowed / blocked, ip_policy.py),
  2. the ORIGIN check: a web page's Origin is refused, so a site you
     happen to visit cannot even start the handshake,
  3. the HANDSHAKE: the extension proves it holds the API key, and the
     engine proves it back (protocol.py),

and after that every frame must open as a sealed message in sequence.
Any failure closes the connection without acting on what it carried.

One extension at a time. A second one that authenticates replaces the
first, which is what a browser restart looks like from here.

Beyond relaying requests, the server carries three things the other
way: the VERSIONS of the extension this engine expects (versions.py),
sent on every connect; the engine's STATUS (what it is doing, for the
extension's popup), sent on every connect and whenever it changes; and
CALLS the extension makes -- the algorithm editor's -- answered by
handlers the engine registers. A call the engine did not register is
refused.

Given a Notifications hub (notifications.py), it also tells apps what it
sees: the extension connecting and going away, its trading switch, an
engine's state, and every order report that is news. Those apps connect
to a listener of their own (notify_server.py), with a key of their own,
and can send nothing that reaches this one.

The websockets package is imported inside start(), not at module scope,
for the same reason recon.py defers Playwright: importing
fidelity_gateway must stay cheap and must work where the optional
dependencies were never installed.
"""

from __future__ import annotations

import contextlib
import errno
import json
import queue
import threading
import time
import uuid
from collections.abc import Callable
from datetime import UTC, datetime
from http import HTTPStatus
from typing import Any

from engine.core.exceptions import BrokerUnavailableError, ConfigurationError
from fidelity_gateway.bridge.ip_policy import AddressPolicy
from fidelity_gateway.bridge.keys import BridgeApiKey
from fidelity_gateway.bridge.notifications import Notifications
from fidelity_gateway.bridge.order_reports import OrderReports
from fidelity_gateway.bridge.protocol import (
    BRIDGE_PATH,
    MAX_PAYLOAD_LENGTH,
    PROTOCOL,
    Channel,
    ProtocolError,
    engine_proof,
    extension_proof,
    is_nonce,
    new_nonce,
    proofs_match,
    session_key,
)
from fidelity_gateway.bridge.versions import expected_extension_versions, version_advice
from fidelity_gateway.session import tab_state

DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8765
HANDSHAKE_TIMEOUT_SECONDS = 10.0
EVENT_BACKLOG = 1000

# Error codes the extension only ever returns BEFORE sending anything to
# Fidelity (see the extension's PROTOCOL.md). Refusals, not failures.
PRE_SEND_CODES = frozenset(
    {
        "blocked_endpoint",
        "blocked_header",
        "blocked_url",
        "bad_request",
        "unknown_command",
        "no_fidelity_tab",
        "reloading",
    }
)

# The refusals that mean "not now" rather than "never": no extension
# connected, no Fidelity tab open, the extension's own switch says no
# (trading turned off in its settings), or the extension is reloading or
# reconnecting on purpose (an update, new settings) and answers anything
# that arrives meanwhile with a refusal instead of dropping it. Nothing was
# sent, and each clears without anyone touching the engine -- so these are
# also BrokerUnavailableError, which the live loop waits out.
UNAVAILABLE_CODES = frozenset({"not_connected", "no_fidelity_tab", "blocked_endpoint", "reloading"})

_WEB_ORIGINS = ("http://", "https://")

# bind()'s "address already in use", on POSIX and on Windows.
_ADDRESS_IN_USE = frozenset(
    code for code in (errno.EADDRINUSE, getattr(errno, "WSAEADDRINUSE", None)) if code is not None
)


class BridgeError(RuntimeError):
    """The bridge could not complete a request -- and it MAY have reached
    Fidelity: the extension timed out, disconnected mid-request, or the
    request failed inside the page. For an order, the outcome is unknown."""


class BridgeRefusal(ConfigurationError):
    """Refused before anything was sent to Fidelity: no extension is
    connected, or the extension's own rules said no. Nothing happened at
    the venue, so this is a ConfigurationError -- the type the placing
    broker already knows is not an ambiguous submission."""

    def __init__(self, message: str, code: str = "refused") -> None:
        super().__init__(message)
        self.code = code


class BridgeUnavailable(BridgeRefusal, BrokerUnavailableError):
    """A refusal that clears on its own: the extension is not connected,
    no Fidelity tab is open, or trading is switched off in the extension.

    Still a BridgeRefusal -- nothing was sent, so an order refused this
    way is not ambiguous -- and also a BrokerUnavailableError, so the
    live loop skips the tick and tries again instead of stopping. Turning
    trading off in the extension therefore pauses the engine's orders;
    turning it back on resumes them.
    """


class _Disconnected:
    """Delivered to anyone still waiting when the extension goes away."""


_DISCONNECTED = _Disconnected()


class _Session:
    """One authenticated extension connection."""

    def __init__(self, connection: Any, channel: Channel, peer: str, client: Any) -> None:
        self.connection = connection
        self.channel = channel
        self.peer = peer
        self.client = client if isinstance(client, dict) else {}
        # Sealing assigns the sequence number, so seal and send happen
        # under one lock: otherwise two threads could seal 5 and 6 and
        # send 6 first, and the extension would rightly drop the line.
        self._send_lock = threading.Lock()

    def send(self, message: dict) -> None:
        with self._send_lock:
            self.connection.send(json.dumps(self.channel.seal(message)))


class BridgeServer:
    """Listens for the extension and relays requests to it."""

    def __init__(
        self,
        api_key: BridgeApiKey,
        *,
        host: str = DEFAULT_HOST,
        port: int = DEFAULT_PORT,
        policy: AddressPolicy | None = None,
        extension_origin: str | None = None,
        handshake_timeout: float = HANDSHAKE_TIMEOUT_SECONDS,
        log: Callable[[str], None] | None = None,
        order_reports: OrderReports | None = None,
        extension_versions: dict | None = None,
        on_event: Callable[[str, dict], None] | None = None,
        notifications: Notifications | None = None,
    ) -> None:
        """`notifications`: the hub apps hear this bridge through
        (notifications.py). Whoever runs the apps' listener owns it -- the
        bridge host, or `serve --notify` -- so it outlives this server."""
        if not isinstance(api_key, BridgeApiKey):
            raise ConfigurationError("BridgeServer needs a BridgeApiKey (see bridge/keys.py).")
        self._key = api_key
        self._host = host
        self._requested_port = port
        self._policy = policy or AddressPolicy(["127.0.0.1", "::1"])
        self._extension_origin = extension_origin
        self._handshake_timeout = handshake_timeout
        self._log = log or (lambda _message: None)
        self._order_reports = (
            order_reports if order_reports is not None else OrderReports(log=self._log)
        )
        # {"minimum", "latest"}: what every connecting extension is told,
        # and checked against.
        self._extension_versions = (
            dict(extension_versions)
            if extension_versions is not None
            else expected_extension_versions()
        )
        # Every event the extension sends, to one listener instead of the
        # queue next_event() reads: the bridge host (host.py) fans them out
        # to the trader attached to it. The server still keeps what it keeps
        # of its own (permissions, order reports, the tab).
        self._on_event = on_event
        self._lock = threading.Lock()
        self._session: _Session | None = None
        self._connected = threading.Event()
        self._pending: dict[str, tuple[_Session, queue.Queue]] = {}
        self._events: queue.Queue = queue.Queue(maxsize=EVENT_BACKLOG)
        self._permissions: dict | None = None
        self._engine_status: dict | None = None
        self._calls: dict[str, Callable[[dict], dict]] = {}
        self._server: Any = None
        self._thread: threading.Thread | None = None
        # For connection_report(): when the extension connected, was last
        # heard from, and last went away (epoch seconds).
        self._clock = time.time
        self._connected_at: float | None = None
        self._heard_at: float | None = None
        self._disconnected_at: float | None = None
        # The last connection turned away, and why -- an address not
        # allowed, a key that does not match: the reason an extension that
        # "never connects" gives nowhere else (10-22).
        self._last_refused: dict | None = None
        # How the last connection ended: {"at", "client", "code", "reason"}.
        self._last_disconnect: dict | None = None
        # The connected extension's Fidelity tab, from its `tab` events:
        # {"url", "state" (session.tab_state), "since"}. None until it says.
        self._tab: dict | None = None
        # What apps hear. Without a hub nothing is enabled, so every publish
        # is a no-op and nothing is kept.
        self._notifications = notifications if notifications is not None else Notifications(())
        self._order_reports.add_listener(self._on_order_report)
        # Taken around reading the status and handing it over, so two
        # threads' snapshots cannot land in the wrong order.
        self._status_lock = threading.Lock()
        self._stopping = False

    # -- lifecycle ----------------------------------------------------------

    def start(self) -> None:
        try:
            from websockets.sync.server import serve
        except ImportError as exc:
            raise ConfigurationError(
                f"The bridge needs the websockets package: {exc}\n"
                "    pip install -r requirements-fidelity.txt"
            ) from exc
        self._publish_status()
        try:
            self._server = serve(
                self._handle,
                self._host,
                self._requested_port,
                process_request=self._process_request,
                max_size=MAX_PAYLOAD_LENGTH + 4096,
                compression=None,
                server_header=None,
            )
        except OSError as exc:
            if exc.errno not in _ADDRESS_IN_USE:
                raise
            # A bridge or trading loop started by hand holds the port (10-23,
            # all day): say so, as a wait -- it clears when that one stops.
            raise BridgeUnavailable(
                f"Port {self._requested_port} on {self._host} is already in use: another "
                "program on this machine is listening there -- a bridge or trading loop "
                "started by hand (`cli.py live`, `python -m fidelity_gateway.bridge serve` "
                "or `check`), or the fidelity-bridge service. Only one can listen at a "
                "time; stop the other one.",
                code="port_in_use",
            ) from exc
        self._thread = threading.Thread(
            target=self._server.serve_forever, name="fidelity-bridge", daemon=True
        )
        self._thread.start()

    def stop(self) -> None:
        with self._lock:
            # The extension leaving because the engine stops is not news:
            # the apps are told goodbye instead.
            self._stopping = True
            session = self._session
        if session is not None:
            with contextlib.suppress(Exception):
                session.connection.close(1001, "engine shutting down")
        if self._server is not None:
            self._server.shutdown()
        if self._thread is not None:
            self._thread.join(timeout=5)

    @property
    def port(self) -> int:
        """The port actually bound -- useful when started on port 0."""
        if self._server is None:
            return self._requested_port
        return self._server.socket.getsockname()[1]

    @property
    def url(self) -> str:
        host = f"[{self._host}]" if ":" in self._host else self._host
        return f"ws://{host}:{self.port}{BRIDGE_PATH}"

    @property
    def connected(self) -> bool:
        return self._connected.is_set()

    @property
    def extension(self) -> dict:
        """What the connected extension said about itself, or {}."""
        session = self._session
        return dict(session.client) if session is not None else {}

    @property
    def permissions(self) -> dict | None:
        """What the extension last said it allows -- {"preview", "place"}
        -- or None before it has said. It tells the engine the moment its
        trading switch changes, so this is never staler than a click."""
        return dict(self._permissions) if self._permissions is not None else None

    @property
    def extension_versions(self) -> dict:
        """{"minimum", "latest"}: the extension versions this engine expects."""
        return dict(self._extension_versions)

    @property
    def engine_status(self) -> dict | None:
        """What the engine last said about itself, or None."""
        status = self._engine_status
        return dict(status) if status is not None else None

    def notify_through(self, notifications: Notifications) -> None:
        """Tell apps through `notifications` from now on: the bridge host
        hands its own hub to every BridgeServer it builds, so one restarted
        with new settings keeps the apps' stream."""
        self._notifications = notifications
        self._publish_status()

    def _on_order_report(self, report, previous, resent: bool) -> None:
        self._notifications.order_report(report, previous, resent)

    @property
    def notifications(self) -> Notifications:
        """What apps are told (notifications.py): with no notifier, a hub
        with nothing enabled."""
        return self._notifications

    def connection_report(self) -> dict:
        """The extension's side of the bridge, for whoever watches the engine
        (the Live page, through the trader's status file): connected or not,
        since when, when it was last heard from, which version against the
        ones this engine expects, and what its switches allow -- "place" is
        its "Allow trading". Never the API key."""

        def iso(seconds: float | None) -> str | None:
            return datetime.fromtimestamp(seconds, UTC).isoformat() if seconds else None

        session = self._session
        connected = session is not None and self.connected
        version = session.client.get("version") if connected else None
        tab = self._tab if connected else None
        return {
            "connected": connected,
            "since": iso(self._connected_at) if connected else None,
            "last_heard": iso(self._heard_at),
            "disconnected_at": None if connected else iso(self._disconnected_at),
            "client": session.peer if connected else None,
            "version": version,
            "versions": self.extension_versions,
            "advice": version_advice(version, self._extension_versions) if version else None,
            "permissions": self.permissions,
            "url": self.url,
            # Signed in or not, by the tab the extension reports.
            "fidelity_tab": (
                {"state": tab["state"], "url": tab["url"], "since": iso(tab["since"])}
                if tab is not None
                else None
            ),
            "last_refused": (
                {**self._last_refused, "at": iso(self._last_refused["at"])}
                if self._last_refused is not None
                else None
            ),
            "last_disconnect": (
                {**self._last_disconnect, "at": iso(self._last_disconnect["at"])}
                if self._last_disconnect is not None
                else None
            ),
        }

    def set_engine_status(self, status: dict) -> None:
        """Tell the extension what the engine is doing -- now, if one is
        connected, and on connecting otherwise. An unchanged status is
        not sent again."""
        with self._lock:
            if status == self._engine_status:
                return
            self._engine_status = dict(status)
            session = self._session
        if session is not None:
            self._send_status(session)
        self._notifications.engine_status(status)
        self._publish_status()

    def register_call(self, method: str, handler: Callable[[dict], dict]) -> None:
        """Let the extension call `method`. The handler gets the call's
        arguments and returns a dict. It refuses with ConfigurationError
        (code "invalid") or PermissionError ("not_allowed"); anything
        else it raises is reported as "internal_error". It runs on its
        own thread, so a slow one never holds up the connection."""
        self._calls[str(method)] = handler

    def unregister_call(self, method: str) -> None:
        """Stop offering `method`: the extension is refused it again."""
        self._calls.pop(str(method), None)

    @property
    def order_reports(self) -> OrderReports:
        """What the extension has said became of the orders it sent --
        its confirmations (order_reports.py)."""
        return self._order_reports

    def wait_for_extension(self, timeout: float) -> bool:
        return self._connected.wait(timeout)

    # -- the HTTP upgrade: address and origin -------------------------------

    def _process_request(self, connection: Any, request: Any) -> Any:
        if request.path.split("?", 1)[0] != BRIDGE_PATH:
            return connection.respond(HTTPStatus.NOT_FOUND, "Not found.\n")
        peer = str(connection.remote_address[0])
        allowed, reason = self._policy.evaluate(peer)
        if not allowed:
            self._log(f"[bridge] refused a connection: {reason}")
            self._refused(
                peer,
                f"{reason} (allowed: {', '.join(self._policy.allowed) or 'none'}); add it to "
                "live.fidelity.bridge.allowed_clients to let it connect",
            )
            return connection.respond(HTTPStatus.FORBIDDEN, "This address may not connect.\n")
        origin = request.headers.get("Origin")
        if origin is not None and (origin == "null" or origin.lower().startswith(_WEB_ORIGINS)):
            self._log(f"[bridge] refused a web page's connection from {peer} (Origin {origin})")
            self._refused(peer, f"a web page (Origin {origin}) tried to connect")
            return connection.respond(HTTPStatus.FORBIDDEN, "Web pages may not connect.\n")
        if self._extension_origin is not None and origin != self._extension_origin:
            self._log(f"[bridge] refused {peer}: Origin {origin!r} is not the pinned extension")
            self._refused(peer, f"Origin {origin!r} is not the pinned extension")
            return connection.respond(HTTPStatus.FORBIDDEN, "Unknown extension.\n")
        return None

    def _refused(self, peer: str, reason: str) -> None:
        self._last_refused = {"at": self._clock(), "client": peer, "reason": reason}
        self._notifications.connection_refused(peer=peer, reason=reason)

    # -- the connection -----------------------------------------------------

    def _handle(self, connection: Any) -> None:
        from websockets.exceptions import ConnectionClosed

        peer = str(connection.remote_address[0])
        session = None
        try:
            session = self._handshake(connection, peer)
            if session is None:
                return
            for frame in connection:
                if not self._on_frame(session, frame):
                    connection.close(1008, "integrity check failed")
                    break
        except ConnectionClosed:
            pass
        finally:
            if session is not None:
                self._retire(
                    session,
                    code=getattr(connection, "close_code", None),
                    reason=getattr(connection, "close_reason", None),
                )

    def _handshake(self, connection: Any, peer: str) -> _Session | None:
        nonce = new_nonce()
        connection.send(json.dumps({"type": "challenge", "protocol": PROTOCOL, "nonce": nonce}))
        try:
            auth = json.loads(connection.recv(timeout=self._handshake_timeout))
        except TimeoutError:
            self._refused(peer, "it connected but never answered the handshake")
            connection.close(1008, "handshake timeout")
            return None
        except ValueError:
            self._refused(peer, "its greeting was not JSON")
            connection.close(1008, "not JSON")
            return None
        if (
            not isinstance(auth, dict)
            or auth.get("type") != "auth"
            or auth.get("protocol") != PROTOCOL
            or not is_nonce(auth.get("nonce"))
        ):
            self._refused(peer, f"it does not speak {PROTOCOL}")
            connection.close(1008, "not fidelity-bridge/v1")
            return None
        expected = extension_proof(self._key.value, nonce, auth["nonce"])
        if not proofs_match(expected, auth.get("proof")):
            self._log(f"[bridge] {peer} failed the API key check")
            self._refused(
                peer,
                "its API key does not match FIDELITY_BRIDGE_API_KEY: paste this engine's key "
                "into the extension's settings",
            )
            connection.send(json.dumps({"type": "denied", "reason": "bad_proof"}))
            connection.close(1008, "authentication failed")
            return None
        connection.send(
            json.dumps(
                {"type": "welcome", "proof": engine_proof(self._key.value, nonce, auth["nonce"])}
            )
        )
        channel = Channel(
            session_key(self._key.value, nonce, auth["nonce"]), sender="engine", peer="ext"
        )
        session = _Session(connection, channel, peer, auth.get("client"))
        with self._lock:
            previous, self._session = self._session, session
            self._connected_at = self._heard_at = self._clock()
            # How long it was away: None for a first connection, and for a
            # replacement -- a browser restart seen before the old socket
            # closed -- since nothing was ever without one.
            away = (
                self._connected_at - self._disconnected_at
                if previous is None and self._disconnected_at is not None
                else None
            )
        if previous is not None:
            self._log("[bridge] a new extension connection replaces the old one")
            with contextlib.suppress(Exception):
                previous.connection.close(1000, "replaced")
        self._connected.set()
        version = session.client.get("version", "?")
        self._log(f"[bridge] extension {version} connected from {peer}")
        advice = version_advice(session.client.get("version"), self._extension_versions)
        if advice:
            self._log(f"[bridge] extension {version}: {advice}")
        with contextlib.suppress(Exception):
            session.send({"type": "versions", "extension": dict(self._extension_versions)})
        self._send_status(session)
        if previous is None:
            self._notifications.extension_connected(
                version=session.client.get("version"), peer=peer, away_seconds=away
            )
        self._publish_status()
        return session

    def _on_frame(self, session: _Session, frame: Any) -> bool:
        """Handle one sealed frame. False means close the connection."""
        try:
            message = session.channel.open(json.loads(frame))
        except (ProtocolError, ValueError, TypeError) as exc:
            self._log(f"[bridge] dropped the extension: {exc}")
            return False
        self._heard_at = self._clock()
        kind = message.get("type")
        if kind == "response":
            with self._lock:
                waiting = self._pending.pop(str(message.get("id")), None)
            if waiting is not None and waiting[0] is session:
                waiting[1].put(message)
        elif kind == "event":
            self._on_extension_event(str(message.get("event")), message.get("data"))
        elif kind == "call":
            self._start_call(session, message)
        elif kind == "ping":
            session.send({"type": "pong", "id": message.get("id")})
        return True

    # -- the engine's status, and the extension's calls -----------------------

    def _send_status(self, session: _Session) -> None:
        status = self._engine_status
        if status is None:
            return
        with contextlib.suppress(Exception):
            session.send({"type": "status", "engine": status})

    def _start_call(self, session: _Session, message: dict) -> None:
        call_id = message.get("id")
        if not isinstance(call_id, str) or not call_id or len(call_id) > 100:
            return  # nothing to address an answer to
        method = message.get("method")
        args = message.get("args") if isinstance(message.get("args"), dict) else {}
        handler = self._calls.get(method) if isinstance(method, str) else None
        if handler is None:
            self._answer(
                session,
                call_id,
                error={
                    "code": "unknown_method",
                    "message": f"This engine does not offer {method!r}.",
                },
            )
            return
        threading.Thread(
            target=self._run_call,
            args=(session, call_id, method, handler, args),
            name=f"fidelity-bridge-call-{method}",
            daemon=True,
        ).start()

    def _run_call(
        self, session: _Session, call_id: str, method: str, handler: Callable, args: dict
    ) -> None:
        try:
            result = handler(args)
        except ConfigurationError as exc:
            self._answer(session, call_id, error={"code": "invalid", "message": str(exc)})
        except PermissionError as exc:
            self._answer(session, call_id, error={"code": "not_allowed", "message": str(exc)})
        except Exception as exc:
            self._log(f"[bridge] {method} failed: {type(exc).__name__}: {exc}")
            self._answer(
                session,
                call_id,
                error={"code": "internal_error", "message": f"{type(exc).__name__}: {exc}"},
            )
        else:
            self._answer(session, call_id, result=result if isinstance(result, dict) else {})

    @staticmethod
    def _answer(
        session: _Session, call_id: str, *, result: dict | None = None, error: dict | None = None
    ) -> None:
        reply = {"type": "result", "id": call_id, "ok": error is None}
        if error is None:
            reply["result"] = result or {}
        else:
            reply["error"] = error
        with contextlib.suppress(Exception):
            session.send(reply)

    def _note_permissions(self, data: Any) -> None:
        """Record what the extension allows, and say so when it changes:
        the trading switch is the operator's off button, and an engine
        that kept quiet about it being pressed would look broken."""
        if not isinstance(data, dict):
            return
        permissions = {"preview": data.get("preview") is True, "place": data.get("place") is True}
        if permissions == self._permissions:
            return
        previous, self._permissions = self._permissions, permissions
        # Its first word after the bridge starts is how things are, not a
        # change; a switch flipped while it was away still is one.
        if previous is not None and previous["place"] != permissions["place"]:
            self._notifications.trading_switch(allowed=permissions["place"])
        self._publish_status()
        if permissions["place"]:
            self._log("[bridge] the extension allows trading: orders will be placed")
        else:
            self._log(
                "[bridge] trading is switched OFF in the extension: the engine keeps reading, "
                "and every order is refused until it is switched back on"
            )

    def _on_extension_event(self, name: str, data: Any) -> None:
        if name == "permissions":
            self._note_permissions(data)
        elif name == "order":
            self._order_reports.note(data)
        elif name == "orders":
            self._order_reports.note_all(data)
        elif name == "tab":
            self._note_tab(data)
        if self._on_event is not None:
            with contextlib.suppress(Exception):  # a listener's fault is not the line's
                self._on_event(name, data if isinstance(data, dict) else {})
        elif name not in ("permissions", "order", "orders"):
            self._push_event(name, data)

    def _note_tab(self, data: Any) -> None:
        """Keep where the Fidelity tab is, for connection_report: signed in,
        signed out, or none -- since when it last changed."""
        url = data.get("url") if isinstance(data, dict) else None
        url = url if isinstance(url, str) and url else None
        state = tab_state(url)
        previous = self._tab
        if previous is not None and previous["state"] == state:
            self._tab = {**previous, "url": url}
            return
        self._tab = {"url": url, "state": state, "since": self._clock()}
        self._notifications.fidelity_tab(state)
        self._publish_status()

    def _push_event(self, name: str, data: Any) -> None:
        item = (name, data if isinstance(data, dict) else {})
        while True:
            try:
                self._events.put_nowait(item)
                return
            except queue.Full:
                with contextlib.suppress(queue.Empty):
                    self._events.get_nowait()

    def _retire(
        self, session: _Session, code: int | None = None, reason: str | None = None
    ) -> None:
        with self._lock:
            current = self._session is session
            if current:
                self._session = None
                self._connected.clear()
                self._disconnected_at = self._clock()
                self._tab = None  # the next extension says where its tab is
                self._last_disconnect = {
                    "at": self._disconnected_at,
                    "client": session.peer,
                    "code": code,
                    "reason": reason or None,
                }
            abandoned = [key for key, (owner, _) in self._pending.items() if owner is session]
            waiters = [self._pending.pop(key)[1] for key in abandoned]
            stopping = self._stopping
        for waiter in waiters:
            waiter.put(_DISCONNECTED)
        self._log(f"[bridge] extension at {session.peer} disconnected")
        if current and not stopping:
            self._notifications.extension_disconnected(peer=session.peer, code=code, reason=reason)
            self._publish_status()

    def _publish_status(self) -> None:
        """The bridge's part of what apps are shown: the extension's
        connection, switches and Fidelity tab, and an engine's own words --
        None while only the bridge's standby status (mode "bridge") stands
        in for one. Sent when it changes; never the key, nor the bridge's
        own address. The bridge host adds its own part (readiness)."""
        with self._status_lock:
            report = self.connection_report()
            permissions = report["permissions"] or {}
            engine = self.engine_status
            last_disconnect = report.get("last_disconnect") or {}
            self._notifications.update_status(
                extension={
                    "connected": report["connected"],
                    "since": report["since"],
                    "disconnectedAt": report["disconnected_at"],
                    "disconnectCode": None if report["connected"] else last_disconnect.get("code"),
                    "version": report["version"],
                    "advice": report["advice"],
                    "trading": permissions.get("place"),
                    "previews": permissions.get("preview"),
                    "fidelity": (report.get("fidelity_tab") or {}).get("state"),
                },
                engine=engine if engine is not None and engine.get("mode") != "bridge" else None,
            )

    # -- what callers use ---------------------------------------------------

    def next_event(self, timeout: float = 0.0) -> tuple[str, dict] | None:
        """The next event from the extension, waiting up to `timeout`."""
        try:
            if timeout <= 0:
                return self._events.get_nowait()
            return self._events.get(timeout=timeout)
        except queue.Empty:
            return None

    def request(self, command: str, args: dict, *, timeout: float = 45.0) -> dict:
        """Ask the extension to run `command`, and return its result.

        BridgeRefusal: nothing was sent to Fidelity (BridgeUnavailable when
            it will clear on its own).
        BridgeError: something may have been.
        """
        with self._lock:
            session = self._session
            if session is None:
                raise BridgeUnavailable(
                    "No browser extension is connected to the bridge. Open the browser with "
                    "Fidelity Bridge installed; its badge shows ON once it has connected.",
                    code="not_connected",
                )
            request_id = uuid.uuid4().hex
            waiter: queue.Queue = queue.Queue(maxsize=1)
            self._pending[request_id] = (session, waiter)
        try:
            session.send({"type": "request", "id": request_id, "command": command, "args": args})
        except Exception as exc:
            with self._lock:
                self._pending.pop(request_id, None)
            raise BridgeError(
                f"Sending {command} to the extension failed part-way: {exc}. It may or may "
                "not have arrived."
            ) from exc
        try:
            response = waiter.get(timeout=timeout)
        except queue.Empty:
            with self._lock:
                self._pending.pop(request_id, None)
            raise BridgeError(
                f"The extension did not answer {command} within {timeout:.0f}s. It may "
                "still have run it."
            ) from None
        if response is _DISCONNECTED:
            raise BridgeError(
                f"The extension disconnected before answering {command}. It may have run it."
            )
        if response.get("ok") is True:
            result = response.get("result")
            return result if isinstance(result, dict) else {}
        error = response.get("error") if isinstance(response.get("error"), dict) else {}
        code = str(error.get("code") or "internal_error")
        detail = str(error.get("message") or "no reason given")
        if code in UNAVAILABLE_CODES:
            raise BridgeUnavailable(
                f"The browser extension refused {command}: {detail} ({code})", code
            )
        if code in PRE_SEND_CODES:
            raise BridgeRefusal(f"The browser extension refused {command}: {detail} ({code})", code)
        raise BridgeError(f"The browser extension could not complete {command}: {detail} ({code})")
