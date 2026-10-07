"""
Helpers for the bridge tests: the extension's half of the protocol in
Python, for driving the real BridgeServer over a real socket.

Built from the same protocol.py the server uses, so on its own it could
only prove the server agrees with itself. What proves the server agrees
with the REAL extension is test_bridge_extension.py, which runs the
extension's own JavaScript against this server, and the shared vectors
both implementations reproduce.
"""

from __future__ import annotations

import json
import threading
from pathlib import Path

from fidelity_gateway.bridge.protocol import (
    PROTOCOL,
    Channel,
    engine_proof,
    extension_proof,
    new_nonce,
    proofs_match,
    session_key,
)

API_KEY = "bridge-test-key-0123456789abcdefghijklmnopqrstuv"
REPO_ROOT = Path(__file__).resolve().parents[2]
EXTENSION_ROOT = REPO_ROOT / "fidelity-bridge-chrome-extension"
VECTORS = EXTENSION_ROOT / "tests" / "vectors"


class FakeExtension:
    """Connects to a BridgeServer the way the extension does."""

    def __init__(
        self,
        url: str,
        api_key: str = API_KEY,
        *,
        origin: str | None = None,
        version: str | None = "9.9.9",
    ) -> None:
        from websockets.sync.client import connect

        self.api_key = api_key
        self.version = version
        self.ws = connect(url, origin=origin, proxy=None, open_timeout=5)
        self.channel: Channel | None = None
        self._thread: threading.Thread | None = None
        self.errors: list[BaseException] = []

    def handshake(self, *, proof: str | None = None) -> dict:
        """Answer the challenge; return the engine's reply (welcome/denied)."""
        challenge = json.loads(self.ws.recv(timeout=5))
        assert challenge["type"] == "challenge" and challenge["protocol"] == PROTOCOL
        self.engine_nonce = challenge["nonce"]
        self.nonce = new_nonce()
        self.ws.send(
            json.dumps(
                {
                    "type": "auth",
                    "protocol": PROTOCOL,
                    "nonce": self.nonce,
                    "proof": proof or extension_proof(self.api_key, self.engine_nonce, self.nonce),
                    "client": {"name": "fake-extension"}
                    | ({"version": self.version} if self.version is not None else {}),
                }
            )
        )
        reply = json.loads(self.ws.recv(timeout=5))
        if reply.get("type") == "welcome":
            expected = engine_proof(self.api_key, self.engine_nonce, self.nonce)
            assert proofs_match(expected, reply["proof"]), "the engine could not prove the key"
            self.channel = Channel(
                session_key(self.api_key, self.engine_nonce, self.nonce),
                sender="ext",
                peer="engine",
            )
            # The engine's first sealed message: the extension versions it
            # expects. Kept for the tests that look at it.
            self.versions = self.receive()
            assert self.versions["type"] == "versions", self.versions
        return reply

    def send(self, message: dict) -> None:
        self.ws.send(json.dumps(self.channel.seal(message)))

    def receive(self, timeout: float = 5) -> dict:
        return self.channel.open(json.loads(self.ws.recv(timeout=timeout)))

    def serve(self, answer) -> None:
        """Answer requests in a background thread: answer(command, args)
        returns a result dict, or raises ValueError("code: message") to
        refuse."""

        def loop() -> None:
            from websockets.exceptions import ConnectionClosed

            try:
                while True:
                    message = self.receive(timeout=30)
                    if message.get("type") != "request":
                        continue
                    try:
                        result = answer(message["command"], message.get("args", {}))
                        reply = {
                            "type": "response",
                            "id": message["id"],
                            "ok": True,
                            "result": result,
                        }
                    except ValueError as exc:
                        code, _, text = str(exc).partition(": ")
                        reply = {
                            "type": "response",
                            "id": message["id"],
                            "ok": False,
                            "error": {"code": code, "message": text},
                        }
                    self.send(reply)
            except ConnectionClosed:
                pass
            except BaseException as exc:  # surfaced by the test via .errors
                self.errors.append(exc)

        self._thread = threading.Thread(target=loop, daemon=True)
        self._thread.start()

    def close(self) -> None:
        self.ws.close()
        if self._thread is not None:
            self._thread.join(timeout=5)
