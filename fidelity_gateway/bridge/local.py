"""
The bridge host's local link: how a trading process reaches the extension
through the bridge host (host.py) instead of listening for it itself.

One JSON object per line over a Unix socket that only the bridge host and the
trader's container mount (docker-compose.yml's bridge_fidelity volume; never
`web`'s). One process is attached at a time: a trading loop, or a connection
check. The messages:

  attached -> host
    hello      {client: {process, pid, ...}}      first, once
    request    {id, command, args, timeout}       BridgeServer.request
    status     {engine}                           the engine status for the extension
    register   {method}                           offer the extension a call
    result     {id, ok, result | error}           the answer to a forwarded call
    bye        {}                                 detaching on purpose

  host -> attached
    welcome    {replay, connection}               the lease is yours
    refused    {reason}                           someone else holds it
    response   {id, ok, result | error}           to a request
    event      {event, data}                      what the extension sent
    connection {report}                           its connection, on change
    call       {id, method, args}                 the extension calling

A request's error keeps the bridge's own distinction (server.py): "unavailable"
(nothing was sent; it clears on its own), "refused" (nothing was sent) and
"error" (it may have reached Fidelity) -- so an order is called ambiguous
exactly when it would have been without the host in between.
"""

from __future__ import annotations

import contextlib
import json
import socket
import threading
from typing import Any

from fidelity_gateway.bridge.protocol import MAX_PAYLOAD_LENGTH
from fidelity_gateway.bridge.server import BridgeError, BridgeRefusal, BridgeUnavailable

# A line holds at most one frame's payload, twice over for JSON escaping.
MAX_LINE_BYTES = 2 * MAX_PAYLOAD_LENGTH + 64 * 1024


class LinkClosed(ConnectionError):
    """The other end of the local link went away."""


class Line:
    """One end of the link: whole JSON objects in, whole JSON objects out."""

    def __init__(self, sock: socket.socket) -> None:
        self.sock = sock
        self._send_lock = threading.Lock()
        self._buffer = b""

    def send(self, message: dict) -> None:
        data = (json.dumps(message, separators=(",", ":")) + "\n").encode("utf-8")
        with self._send_lock:
            try:
                self.sock.sendall(data)
            except OSError as exc:
                raise LinkClosed(f"the local link is closed: {exc}") from exc

    def receive(self) -> dict:
        """The next message. LinkClosed at the end of the stream, or on a
        line that is not a JSON object -- the link is not trusted to carry
        on after a frame it could not read. TimeoutError when the socket's
        timeout passes with no whole line: what has arrived is kept, and
        the next call carries on from it."""
        while b"\n" not in self._buffer:
            if len(self._buffer) > MAX_LINE_BYTES:
                raise LinkClosed("a message on the local link is too large")
            try:
                chunk = self.sock.recv(1 << 16)
            except TimeoutError:
                raise
            except OSError as exc:
                raise LinkClosed(f"the local link is closed: {exc}") from exc
            if not chunk:
                raise LinkClosed("the other end closed the local link")
            self._buffer += chunk
        line, self._buffer = self._buffer.split(b"\n", 1)
        try:
            message = json.loads(line)
        except ValueError as exc:
            raise LinkClosed(f"an unreadable message on the local link: {exc}") from exc
        if not isinstance(message, dict):
            raise LinkClosed("a message on the local link is not an object")
        return message

    def close(self) -> None:
        for step in (lambda: self.sock.shutdown(socket.SHUT_RDWR), self.sock.close):
            with contextlib.suppress(OSError):
                step()


def error_payload(exc: BaseException) -> dict[str, Any]:
    """A bridge exception as the link carries it."""
    if isinstance(exc, BridgeUnavailable):
        kind = "unavailable"
    elif isinstance(exc, BridgeRefusal):
        kind = "refused"
    else:
        kind = "error"
    return {"kind": kind, "code": getattr(exc, "code", None), "message": str(exc)}


def error_from(payload: Any) -> Exception:
    """The exception a request's error stands for, on the attached side."""
    payload = payload if isinstance(payload, dict) else {}
    message = str(payload.get("message") or "the bridge host gave no reason")
    code = str(payload.get("code") or "refused")
    kind = payload.get("kind")
    if kind == "unavailable":
        return BridgeUnavailable(message, code)
    if kind == "refused":
        return BridgeRefusal(message, code)
    return BridgeError(message)


__all__ = ["MAX_LINE_BYTES", "Line", "LinkClosed", "error_from", "error_payload"]
