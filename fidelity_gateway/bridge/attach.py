"""
A trading process's end of the bridge host (host.py): BridgeServer's surface,
over the host's Unix socket instead of a listening port.

    bridge = AttachedBridge.attach("/app/bridge/bridge.sock", client={"process": "loop"})
    page = BridgePage(bridge)            # FidelitySession works unchanged
    ...
    bridge.stop()                        # detaches; the host and the extension stay up

open_bridge() returns one of these whenever VAI_BRIDGE_SOCKET names the host's
socket, so connect_live, `bridge check` and place_test_order attach without
knowing it. Everything the extension said before this process attached -- its
auth headers, its tab, its switches, its order log -- arrives first, replayed
by the host, so a session needs neither the wait for the extension nor a
navigation to provoke the headers.

The errors mean what BridgeServer's mean: BridgeUnavailable when nothing was
sent and it clears on its own (no host, no extension, the host holding another
process's attachment), BridgeRefusal when nothing was sent, BridgeError when a
request may have reached Fidelity -- including the link to the host failing
while one was in flight.
"""

from __future__ import annotations

import contextlib
import os
import queue
import socket
import threading
import uuid
from collections.abc import Callable
from typing import Any

from engine.core.exceptions import ConfigurationError
from fidelity_gateway.bridge.local import Line, LinkClosed, error_from
from fidelity_gateway.bridge.order_reports import OrderReports
from fidelity_gateway.bridge.server import EVENT_BACKLOG, BridgeError, BridgeUnavailable

SOCKET_ENV_VAR = "VAI_BRIDGE_SOCKET"
CONNECT_TIMEOUT_SECONDS = 5.0
# The socket's timeout: bounds a send to a host that stopped reading. A
# receive that times out just looks again.
SEND_TIMEOUT_SECONDS = 10.0
# On top of a request's own timeout: the host's round trip to the extension.
LINK_SLACK_SECONDS = 15.0

_CLOSED = object()


class AttachedBridge:
    """What BridgeServer offers its callers, from a process attached to the
    bridge host."""

    def __init__(
        self,
        line: Line,
        welcome: dict,
        *,
        path: str,
        log: Callable[[str], None] | None = None,
        order_reports: OrderReports | None = None,
    ) -> None:
        self._line = line
        self.path = path
        self._log = log or (lambda _message: None)
        self._order_reports = order_reports if order_reports is not None else OrderReports()
        self._events: queue.Queue = queue.Queue(maxsize=EVENT_BACKLOG)
        self._pending: dict[str, queue.Queue] = {}
        self._pending_lock = threading.Lock()
        self._calls: dict[str, Callable[[dict], dict]] = {}
        self._permissions: dict | None = None
        self._engine_status: dict | None = None
        self._report: dict = {}
        self._extension = threading.Event()
        self._closed = threading.Event()
        self._stopping = False
        self._note_connection(welcome.get("connection"))
        for item in welcome.get("replay") or []:
            if isinstance(item, list) and len(item) == 2 and isinstance(item[1], dict):
                self._on_event(str(item[0]), item[1])
        self._reader = threading.Thread(target=self._read, name="bridge-attached", daemon=True)
        self._reader.start()

    @classmethod
    def attach(
        cls,
        path: str | os.PathLike,
        *,
        client: dict | None = None,
        log: Callable[[str], None] | None = None,
        order_reports: OrderReports | None = None,
    ) -> AttachedBridge:
        """Attach to the bridge host at `path`. BridgeUnavailable when no host
        answers there, or it holds another process's attachment."""
        path = str(path)
        sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        sock.settimeout(CONNECT_TIMEOUT_SECONDS)
        try:
            sock.connect(path)
        except OSError as exc:
            sock.close()
            raise BridgeUnavailable(
                f"The bridge host is not running: nothing answers at {path} ({exc}). Start it "
                "with `docker compose --profile fidelity up -d fidelity-bridge`.",
                code="no_host",
            ) from exc
        line = Line(sock)
        hello = {
            "process": "tool",
            "pid": os.getpid(),
            "deployment": os.environ.get("VAI_DEPLOYMENT"),
            **(client or {}),
        }
        try:
            line.send({"type": "hello", "client": hello})
            first = line.receive()
        except (LinkClosed, TimeoutError) as exc:
            line.close()
            raise BridgeUnavailable(
                f"The bridge host at {path} did not let this process attach: {exc}",
                code="no_host",
            ) from exc
        if first.get("type") == "refused":
            line.close()
            raise BridgeUnavailable(
                f"The bridge host refused to attach this process: {first.get('reason')}",
                code="attached_elsewhere",
            )
        if first.get("type") != "welcome":
            line.close()
            raise ConfigurationError(f"The bridge host at {path} answered {first.get('type')!r}.")
        sock.settimeout(SEND_TIMEOUT_SECONDS)
        return cls(line, first, path=path, log=log, order_reports=order_reports)

    # -- what the host sends -----------------------------------------------------

    def _read(self) -> None:
        try:
            while True:
                try:
                    message = self._line.receive()
                except TimeoutError:
                    continue
                kind = message.get("type")
                if kind == "response":
                    with self._pending_lock:
                        waiter = self._pending.pop(str(message.get("id")), None)
                    if waiter is not None:
                        waiter.put(message)
                elif kind == "event":
                    data = message.get("data")
                    self._on_event(
                        str(message.get("event")), data if isinstance(data, dict) else {}
                    )
                elif kind == "connection":
                    self._note_connection(message.get("report"))
                elif kind == "call":
                    threading.Thread(
                        target=self._run_call,
                        args=(message,),
                        name="bridge-attached-call",
                        daemon=True,
                    ).start()
        except LinkClosed:
            pass
        finally:
            self._closed.set()
            self._extension.clear()
            with self._pending_lock:
                waiters, self._pending = list(self._pending.values()), {}
            for waiter in waiters:
                waiter.put(_CLOSED)
            if not self._stopping:
                self._log("[bridge] the link to the bridge host closed")

    def _on_event(self, name: str, data: dict) -> None:
        """As BridgeServer keeps them: the switches and the order reports
        here, everything else (auth headers, the tab) for next_event()."""
        if name == "permissions":
            self._permissions = {
                "preview": data.get("preview") is True,
                "place": data.get("place") is True,
            }
        elif name == "order":
            self._order_reports.note(data)
        elif name == "orders":
            self._order_reports.note_all(data)
        else:
            item = (name, data)
            while True:
                try:
                    self._events.put_nowait(item)
                    return
                except queue.Full:
                    with contextlib.suppress(queue.Empty):
                        self._events.get_nowait()

    def _note_connection(self, report: Any) -> None:
        if not isinstance(report, dict):
            return
        self._report = dict(report)
        if report.get("connected"):
            self._extension.set()
        else:
            self._extension.clear()

    def _run_call(self, message: dict) -> None:
        """The extension's call, answered by the handler this process registered
        -- with BridgeServer._run_call's codes."""
        call_id = message.get("id")
        method = message.get("method")
        args = message.get("args") if isinstance(message.get("args"), dict) else {}
        handler = self._calls.get(method) if isinstance(method, str) else None
        reply: dict = {"type": "result", "id": call_id}
        try:
            if handler is None:
                raise PermissionError(f"This engine does not offer {method!r}.")
            result = handler(args)
        except ConfigurationError as exc:
            reply.update(ok=False, error={"code": "invalid", "message": str(exc)})
        except PermissionError as exc:
            reply.update(ok=False, error={"code": "not_allowed", "message": str(exc)})
        except Exception as exc:
            reply.update(
                ok=False,
                error={"code": "internal_error", "message": f"{type(exc).__name__}: {exc}"},
            )
        else:
            reply.update(ok=True, result=result if isinstance(result, dict) else {})
        with contextlib.suppress(LinkClosed):
            self._line.send(reply)

    # -- BridgeServer's surface ----------------------------------------------------

    @property
    def connected(self) -> bool:
        return self._extension.is_set() and not self._closed.is_set()

    def wait_for_extension(self, timeout: float) -> bool:
        return self._extension.wait(timeout) and not self._closed.is_set()

    @property
    def extension(self) -> dict:
        version = self._report.get("version") if self.connected else None
        return {"version": version} if version else {}

    @property
    def extension_versions(self) -> dict:
        return dict(self._report.get("versions") or {})

    @property
    def permissions(self) -> dict | None:
        return dict(self._permissions) if self._permissions is not None else None

    @property
    def order_reports(self) -> OrderReports:
        return self._order_reports

    @property
    def engine_status(self) -> dict | None:
        return dict(self._engine_status) if self._engine_status is not None else None

    @property
    def url(self) -> str:
        return str(self._report.get("url") or f"unix:{self.path}")

    def connection_report(self) -> dict:
        """The extension's connection, as the host last reported it."""
        return dict(self._report)

    def next_event(self, timeout: float = 0.0) -> tuple[str, dict] | None:
        try:
            if timeout <= 0:
                return self._events.get_nowait()
            return self._events.get(timeout=timeout)
        except queue.Empty:
            return None

    def set_engine_status(self, status: dict) -> None:
        if status == self._engine_status:
            return
        self._engine_status = dict(status)
        with contextlib.suppress(LinkClosed):
            self._line.send({"type": "status", "engine": dict(status)})

    def register_call(self, method: str, handler: Callable[[dict], dict]) -> None:
        self._calls[str(method)] = handler
        with contextlib.suppress(LinkClosed):
            self._line.send({"type": "register", "method": str(method)})

    def request(self, command: str, args: dict, *, timeout: float = 45.0) -> dict:
        """BridgeServer.request, through the host."""
        if self._closed.is_set():
            raise BridgeUnavailable(
                "The link to the bridge host is closed; nothing was sent.", code="not_connected"
            )
        request_id = uuid.uuid4().hex
        waiter: queue.Queue = queue.Queue(maxsize=1)
        with self._pending_lock:
            self._pending[request_id] = waiter
        try:
            self._line.send(
                {
                    "type": "request",
                    "id": request_id,
                    "command": command,
                    "args": args,
                    "timeout": timeout,
                }
            )
        except LinkClosed as exc:
            with self._pending_lock:
                self._pending.pop(request_id, None)
            raise BridgeError(
                f"Sending {command} to the bridge host failed part-way: {exc}. It may or may "
                "not have arrived."
            ) from exc
        try:
            response = waiter.get(timeout=timeout + LINK_SLACK_SECONDS)
        except queue.Empty:
            with self._pending_lock:
                self._pending.pop(request_id, None)
            raise BridgeError(
                f"The bridge host did not answer {command} within "
                f"{timeout + LINK_SLACK_SECONDS:.0f}s. It may still have run it."
            ) from None
        if response is _CLOSED:
            raise BridgeError(
                f"The link to the bridge host closed before it answered {command}. It may "
                "have run it."
            )
        if response.get("ok") is True:
            result = response.get("result")
            return result if isinstance(result, dict) else {}
        raise error_from(response.get("error"))

    def stop(self) -> None:
        """Detach. The host keeps the extension connected for the next one."""
        self._stopping = True
        with contextlib.suppress(LinkClosed):
            self._line.send({"type": "bye"})
        self._line.close()
        self._reader.join(timeout=5)


__all__ = ["SOCKET_ENV_VAR", "AttachedBridge"]
