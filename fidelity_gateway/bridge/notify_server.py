"""
The bridge's notification listener: where apps connect to hear what the
bridge sees (notifications.py). The one this repository ships is the
Fidelity Bridge Notifier for Android, fidelity-bridge-notifier-android/.

It is a second WebSocket server beside the extension's, and separate from
it on purpose:

  * its own PORT (8766 by default) and ADDRESS rules, so a phone on the
    home network can reach it while the extension's socket stays on this
    computer;
  * its own KEY, FIDELITY_BRIDGE_NOTIFY_KEY (keys.py), which only ever
    reads notifications;
  * READ-ONLY. After the handshake an app may ask for a test notification
    -- to check the phone shows one -- and nothing else; whatever else it
    sends is ignored. Nothing an app sends reaches the extension, the
    engine or Fidelity.

Each connection must pass, in order, the client ADDRESS policy, the
ORIGIN check (no web page), and the HANDSHAKE (notify_protocol.py); after
that every frame, both ways, is sealed. An app is then sent a "hello" --
this run's stream, the kinds it sends, the status now -- then every kept
notification after the (stream, id) it says it last saw, marked as a
replay, then each one as it happens and the status whenever it changes.
When the bridge stops it says "goodbye" first, so an app can tell a
deliberate stop from a lost connection.

An app that cannot keep up is disconnected rather than allowed to hold
anything up; it reconnects and catches up from what is kept.

The websockets package is imported inside start(), as BridgeServer does.
"""

from __future__ import annotations

import contextlib
import json
import queue
import threading
import time
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from http import HTTPStatus
from typing import Any

from engine.core.exceptions import ConfigurationError
from fidelity_gateway.bridge.ip_policy import AddressPolicy
from fidelity_gateway.bridge.keys import BridgeApiKey
from fidelity_gateway.bridge.notifications import DEFAULT_EVENTS, Notification, Notifications
from fidelity_gateway.bridge.notify_protocol import (
    NOTIFY_PATH,
    NOTIFY_PROTOCOL,
    app_channel,
    app_proof,
    bridge_proof,
)
from fidelity_gateway.bridge.protocol import (
    Channel,
    ProtocolError,
    is_nonce,
    new_nonce,
    proofs_match,
)

DEFAULT_NOTIFY_HOST = "127.0.0.1"
DEFAULT_NOTIFY_PORT = 8766
HANDSHAKE_TIMEOUT_SECONDS = 10.0
#: Apps connected at once: a phone and a tablet, with room to spare.
MAX_APPS = 8
#: Messages waiting for one app before it counts as unable to keep up.
APP_BACKLOG = 500
#: An app sends nothing large; the bridge refuses anything that is.
MAX_APP_FRAME = 64 * 1024
#: Seconds between test notifications one app may ask for.
TEST_INTERVAL_SECONDS = 2.0
#: Seconds between pings, and to wait for each answer (PROTOCOL.md, Liveness).
PING_SECONDS = 20.0
_WEB_ORIGINS = ("http://", "https://")


@dataclass(frozen=True)
class NotifySettings:
    """Where the notification listener listens, who may connect, and what
    it sends. live.fidelity.bridge.notifications in a config; `serve
    --notify` on the command line."""

    host: str = DEFAULT_NOTIFY_HOST
    port: int = DEFAULT_NOTIFY_PORT
    allowed_clients: tuple[str, ...] = ("127.0.0.1", "::1")
    blocked_clients: tuple[str, ...] = ()
    events: tuple[str, ...] = DEFAULT_EVENTS

    @classmethod
    def from_config(cls, notifications) -> NotifySettings | None:
        """live.fidelity.bridge.notifications (engine/core/config.py's
        FidelityNotificationsConfig) as settings, or None when not enabled."""
        if notifications is None or not notifications.enabled:
            return None
        return cls(
            host=notifications.host,
            port=notifications.port,
            allowed_clients=tuple(notifications.allowed_clients),
            blocked_clients=tuple(notifications.blocked_clients),
            events=tuple(notifications.events),
        )


def _client_text(value: Any, limit: int = 60) -> str:
    """What an app says about itself, safe for one log line."""
    if not isinstance(value, str):
        return ""
    return "".join(ch if ch.isprintable() else " " for ch in value).strip()[:limit]


def _since(value: Any) -> tuple[str, int] | None:
    """The (stream, id) an app last saw, or None."""
    if not isinstance(value, dict):
        return None
    stream, last = value.get("stream"), value.get("id")
    if not isinstance(stream, str) or not 0 < len(stream) <= 64:
        return None
    if isinstance(last, bool) or not isinstance(last, int) or last < 0:
        return None
    return stream, last


class _App:
    """One authenticated app connection."""

    def __init__(self, connection: Any, channel: Channel, peer: str, client: Any, since) -> None:
        self.connection = connection
        self.channel = channel
        self.peer = peer
        client = client if isinstance(client, dict) else {}
        self.name = _client_text(client.get("name")) or "an app"
        self.version = _client_text(client.get("version"))
        self.since = since
        self.queue: queue.Queue = queue.Queue()
        self.lagging = False
        self.last_test = float("-inf")
        self._send_lock = threading.Lock()

    @property
    def label(self) -> str:
        return f"{self.name} {self.version}".strip() + f" at {self.peer}"

    def send(self, message: dict) -> None:
        with self._send_lock:
            self.connection.send(json.dumps(self.channel.seal(message)))

    def offer(self, kind: str, payload: Any) -> None:
        """A Notifications listener: never blocks. An app this far behind
        is let go (by its writer) and catches up when it reconnects."""
        if self.lagging:
            return
        if self.queue.qsize() >= APP_BACKLOG:
            self.lagging = True
            self.queue.put(("lagging", None))  # wakes its writer to let it go
            return
        self.queue.put((kind, payload))


class NotificationServer:
    """Listens for apps and sends them the bridge's notifications."""

    def __init__(
        self,
        api_key: BridgeApiKey,
        notifications: Notifications,
        *,
        host: str = DEFAULT_NOTIFY_HOST,
        port: int = DEFAULT_NOTIFY_PORT,
        policy: AddressPolicy | None = None,
        handshake_timeout: float = HANDSHAKE_TIMEOUT_SECONDS,
        log: Callable[[str], None] | None = None,
        max_apps: int = MAX_APPS,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        if not isinstance(api_key, BridgeApiKey):
            raise ConfigurationError(
                "NotificationServer needs a BridgeApiKey (see bridge/keys.py)."
            )
        self._key = api_key
        self._notifications = notifications
        self._host = host
        self._requested_port = port
        self._policy = policy or AddressPolicy(["127.0.0.1", "::1"])
        self._handshake_timeout = handshake_timeout
        self._log = log or (lambda _message: None)
        self._max_apps = max_apps
        self._clock = clock
        self._lock = threading.Lock()
        self._apps: set[_App] = set()
        self._writers: dict[_App, threading.Thread] = {}
        self._stopping = False
        self._server: Any = None
        self._thread: threading.Thread | None = None

    @property
    def notifications(self) -> Notifications:
        return self._notifications

    # -- lifecycle ----------------------------------------------------------

    def start(self) -> None:
        try:
            from websockets.sync.server import serve
        except ImportError as exc:
            raise ConfigurationError(
                f"The notification listener needs the websockets package: {exc}\n"
                "    pip install -r requirements-fidelity.txt"
            ) from exc
        self._server = serve(
            self._handle,
            self._host,
            self._requested_port,
            process_request=self._process_request,
            max_size=MAX_APP_FRAME,
            compression=None,
            server_header=None,
            # A phone that walked out of Wi-Fi range never says goodbye: the
            # pings are what notice, and free its place.
            ping_interval=PING_SECONDS,
            ping_timeout=PING_SECONDS,
        )
        self._thread = threading.Thread(
            target=self._server.serve_forever, name="fidelity-bridge-notify", daemon=True
        )
        self._thread.start()

    def stop(self, reason: str = "the bridge is shutting down") -> None:
        """Say goodbye to every app, then stop listening."""
        with self._lock:
            self._stopping = True
            writers = list(self._writers.items())
        for app, _ in writers:
            app.queue.put(("goodbye", reason))
        for _, writer in writers:
            writer.join(timeout=2)
        for app, _ in writers:
            with contextlib.suppress(Exception):
                app.connection.close(1001, "the bridge is stopping")
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
        return f"ws://{host}:{self.port}{NOTIFY_PATH}"

    @property
    def app_count(self) -> int:
        with self._lock:
            return len(self._apps)

    # -- the HTTP upgrade: address and origin -------------------------------

    def _process_request(self, connection: Any, request: Any) -> Any:
        if request.path.split("?", 1)[0] != NOTIFY_PATH:
            return connection.respond(HTTPStatus.NOT_FOUND, "Not found.\n")
        peer = str(connection.remote_address[0])
        allowed, reason = self._policy.evaluate(peer)
        if not allowed:
            self._log(f"[notify] refused an app's connection: {reason}")
            return connection.respond(HTTPStatus.FORBIDDEN, "This address may not connect.\n")
        origin = request.headers.get("Origin")
        if origin is not None and (origin == "null" or origin.lower().startswith(_WEB_ORIGINS)):
            self._log(f"[notify] refused a web page's connection from {peer} (Origin {origin})")
            return connection.respond(HTTPStatus.FORBIDDEN, "Web pages may not connect.\n")
        return None

    # -- the connection -----------------------------------------------------

    def _handle(self, connection: Any) -> None:
        from websockets.exceptions import ConnectionClosed

        peer = str(connection.remote_address[0])
        app = self._handshake(connection, peer)
        if app is None:
            return
        subscription = self._notifications.subscribe(app.offer, since=app.since)
        hello = {
            "type": "hello",
            "protocol": NOTIFY_PROTOCOL,
            "stream": self._notifications.stream,
            "events": list(self._notifications.events),
            "status": subscription.status,
        }
        writer = threading.Thread(
            target=self._write,
            args=(app, hello, subscription.backlog),
            name="fidelity-bridge-notify-writer",
            daemon=True,
        )
        with self._lock:
            self._writers[app] = writer
            if self._stopping:  # stop() began after the handshake let this one in
                app.queue.put(("goodbye", "the bridge is shutting down"))
        writer.start()
        self._log(f"[notify] {app.label} connected")
        try:
            for frame in connection:
                if not self._on_frame(app, frame):
                    connection.close(1008, "integrity check failed")
                    break
        except ConnectionClosed:
            pass
        finally:
            subscription.close()
            app.queue.put(None)
            writer.join(timeout=5)
            with self._lock:
                self._apps.discard(app)
                self._writers.pop(app, None)
            self._log(f"[notify] {app.label} disconnected")

    def _handshake(self, connection: Any, peer: str) -> _App | None:
        nonce = new_nonce()
        connection.send(
            json.dumps({"type": "challenge", "protocol": NOTIFY_PROTOCOL, "nonce": nonce})
        )
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
            or auth.get("protocol") != NOTIFY_PROTOCOL
            or not is_nonce(auth.get("nonce"))
        ):
            connection.close(1008, f"not {NOTIFY_PROTOCOL}")
            return None
        expected = app_proof(self._key.value, nonce, auth["nonce"])
        if not proofs_match(expected, auth.get("proof")):
            self._log(f"[notify] {peer} failed the API key check")
            connection.send(json.dumps({"type": "denied", "reason": "bad_proof"}))
            connection.close(1008, "authentication failed")
            return None
        app = _App(
            connection,
            app_channel(self._key.value, nonce, auth["nonce"]),
            peer,
            auth.get("client"),
            _since(auth.get("since")),
        )
        with self._lock:
            refusal = (
                "stopping"
                if self._stopping
                else "too_many_apps"
                if len(self._apps) >= self._max_apps
                else None
            )
            if refusal is None:
                self._apps.add(app)
        if refusal is not None:
            self._log(f"[notify] refused {app.label}: {refusal}")
            connection.send(json.dumps({"type": "denied", "reason": refusal}))
            connection.close(1013, refusal)
            return None
        connection.send(
            json.dumps(
                {"type": "welcome", "proof": bridge_proof(self._key.value, nonce, auth["nonce"])}
            )
        )
        return app

    def _on_frame(self, app: _App, frame: Any) -> bool:
        """One sealed frame from an app. False means close the connection.
        A test request is the only thing an app can ask for."""
        try:
            message = app.channel.open(json.loads(frame))
        except (ProtocolError, ValueError, TypeError) as exc:
            self._log(f"[notify] dropped {app.label}: {exc}")
            return False
        if message.get("type") == "test":
            now = self._clock()
            if now - app.last_test >= TEST_INTERVAL_SECONDS:
                app.last_test = now
                app.queue.put(("test", None))
        return True

    def _test_notification(self, app: _App) -> dict:
        return Notification(
            id=0,
            stream=self._notifications.stream,
            kind="test",
            severity="info",
            title="Test notification",
            body=f"The bridge reached {app.name}. Notifications will look like this.",
            at=datetime.now(UTC).isoformat(timespec="seconds"),
        ).to_wire()

    def _write(self, app: _App, hello: dict, backlog: list[Notification]) -> None:
        """Everything an app is sent, in order, on its own thread: a slow
        app holds up nobody but itself."""
        from websockets.exceptions import ConnectionClosed

        try:
            app.send(hello)
            for notification in backlog:
                app.send(
                    {"type": "notification", "notification": notification.to_wire(), "replay": True}
                )
            while True:
                item = app.queue.get()
                if item is None:
                    return
                if app.lagging:
                    self._log(f"[notify] {app.label} fell behind; it will catch up on reconnecting")
                    app.connection.close(1013, "fell behind: reconnect to catch up")
                    return
                kind, payload = item
                if kind == "notification":
                    app.send({"type": "notification", "notification": payload.to_wire()})
                elif kind == "status":
                    app.send({"type": "status", "status": payload})
                elif kind == "test":
                    app.send({"type": "notification", "notification": self._test_notification(app)})
                elif kind == "goodbye":
                    app.send({"type": "goodbye", "reason": payload})
                    app.connection.close(1001, "the bridge is stopping")
                    return
        except ConnectionClosed:
            pass
        except Exception as exc:
            self._log(f"[notify] sending to {app.label} failed: {type(exc).__name__}: {exc}")
            with contextlib.suppress(Exception):
                app.connection.close(1011, "internal error")
