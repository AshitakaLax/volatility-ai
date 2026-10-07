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

The websockets package is imported inside start(), not at module scope,
for the same reason recon.py defers Playwright: importing
fidelity_gateway must stay cheap and must work where the optional
dependencies were never installed.
"""

from __future__ import annotations

import contextlib
import json
import queue
import threading
import uuid
from collections.abc import Callable
from http import HTTPStatus
from typing import Any

from engine.core.exceptions import BrokerUnavailableError, ConfigurationError
from fidelity_gateway.bridge.ip_policy import AddressPolicy
from fidelity_gateway.bridge.keys import BridgeApiKey
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
    }
)

# The refusals that mean "not now" rather than "never": no extension
# connected, no Fidelity tab open, or the extension's own switch says no
# (trading turned off in its settings). Nothing was sent, and each
# clears without anyone touching the engine -- so these are also
# BrokerUnavailableError, which the live loop waits out.
UNAVAILABLE_CODES = frozenset({"not_connected", "no_fidelity_tab", "blocked_endpoint"})

_WEB_ORIGINS = ("http://", "https://")


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
    ) -> None:
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

    # -- lifecycle ----------------------------------------------------------

    def start(self) -> None:
        try:
            from websockets.sync.server import serve
        except ImportError as exc:
            raise ConfigurationError(
                f"The bridge needs the websockets package: {exc}\n"
                "    pip install -r requirements-fidelity.txt"
            ) from exc
        self._server = serve(
            self._handle,
            self._host,
            self._requested_port,
            process_request=self._process_request,
            max_size=MAX_PAYLOAD_LENGTH + 4096,
            compression=None,
            server_header=None,
        )
        self._thread = threading.Thread(
            target=self._server.serve_forever, name="fidelity-bridge", daemon=True
        )
        self._thread.start()

    def stop(self) -> None:
        with self._lock:
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

    def register_call(self, method: str, handler: Callable[[dict], dict]) -> None:
        """Let the extension call `method`. The handler gets the call's
        arguments and returns a dict. It refuses with ConfigurationError
        (code "invalid") or PermissionError ("not_allowed"); anything
        else it raises is reported as "internal_error". It runs on its
        own thread, so a slow one never holds up the connection."""
        self._calls[str(method)] = handler

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
            return connection.respond(HTTPStatus.FORBIDDEN, "This address may not connect.\n")
        origin = request.headers.get("Origin")
        if origin is not None and (origin == "null" or origin.lower().startswith(_WEB_ORIGINS)):
            self._log(f"[bridge] refused a web page's connection from {peer} (Origin {origin})")
            return connection.respond(HTTPStatus.FORBIDDEN, "Web pages may not connect.\n")
        if self._extension_origin is not None and origin != self._extension_origin:
            self._log(f"[bridge] refused {peer}: Origin {origin!r} is not the pinned extension")
            return connection.respond(HTTPStatus.FORBIDDEN, "Unknown extension.\n")
        return None

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
                self._retire(session)

    def _handshake(self, connection: Any, peer: str) -> _Session | None:
        nonce = new_nonce()
        connection.send(json.dumps({"type": "challenge", "protocol": PROTOCOL, "nonce": nonce}))
        try:
            auth = json.loads(connection.recv(timeout=self._handshake_timeout))
        except TimeoutError:
            connection.close(1008, "handshake timeout")
            return None
        except ValueError:
            connection.close(1008, "not JSON")
            return None
        if (
            not isinstance(auth, dict)
            or auth.get("type") != "auth"
            or auth.get("protocol") != PROTOCOL
            or not is_nonce(auth.get("nonce"))
        ):
            connection.close(1008, "not fidelity-bridge/v1")
            return None
        expected = extension_proof(self._key.value, nonce, auth["nonce"])
        if not proofs_match(expected, auth.get("proof")):
            self._log(f"[bridge] {peer} failed the API key check")
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
        return session

    def _on_frame(self, session: _Session, frame: Any) -> bool:
        """Handle one sealed frame. False means close the connection."""
        try:
            message = session.channel.open(json.loads(frame))
        except (ProtocolError, ValueError, TypeError) as exc:
            self._log(f"[bridge] dropped the extension: {exc}")
            return False
        kind = message.get("type")
        if kind == "response":
            with self._lock:
                waiting = self._pending.pop(str(message.get("id")), None)
            if waiting is not None and waiting[0] is session:
                waiting[1].put(message)
        elif kind == "event" and message.get("event") == "permissions":
            self._note_permissions(message.get("data"))
        elif kind == "event" and message.get("event") == "order":
            self._order_reports.note(message.get("data"))
        elif kind == "event" and message.get("event") == "orders":
            self._order_reports.note_all(message.get("data"))
        elif kind == "event":
            self._push_event(str(message.get("event")), message.get("data"))
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
        self._permissions = permissions
        if permissions["place"]:
            self._log("[bridge] the extension allows trading: orders will be placed")
        else:
            self._log(
                "[bridge] trading is switched OFF in the extension: the engine keeps reading, "
                "and every order is refused until it is switched back on"
            )

    def _push_event(self, name: str, data: Any) -> None:
        item = (name, data if isinstance(data, dict) else {})
        while True:
            try:
                self._events.put_nowait(item)
                return
            except queue.Full:
                with contextlib.suppress(queue.Empty):
                    self._events.get_nowait()

    def _retire(self, session: _Session) -> None:
        with self._lock:
            if self._session is session:
                self._session = None
                self._connected.clear()
            abandoned = [key for key, (owner, _) in self._pending.items() if owner is session]
            waiters = [self._pending.pop(key)[1] for key in abandoned]
        for waiter in waiters:
            waiter.put(_DISCONNECTED)
        self._log(f"[bridge] extension at {session.peer} disconnected")

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
