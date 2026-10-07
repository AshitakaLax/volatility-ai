"""
fidelity-bridge/v1 -- the engine's half of the protocol spoken with the
Fidelity Bridge browser extension.

The full description is PROTOCOL.md in the extension's repository
(fidelity-bridge-chrome-extension/, a submodule here). In short:

  * Neither side ever sends the API key. Each proves it holds the key by
    answering the other's random challenge with an HMAC. Both proofs bind
    both nonces and carry different labels, so an answer can be neither
    replayed into another connection nor reflected back at its sender.
  * After the handshake every message is sealed: a sequence number and an
    HMAC under a key derived for that connection alone. The MAC covers the
    exact payload TEXT, so the two languages never have to agree on how to
    serialise a float.

The values in the extension's tests/vectors/protocol-v1.json are
reproduced by fidelity_gateway/tests/test_bridge_protocol.py, which is
what keeps this module and the extension's protocol.js speaking the same
language.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import re
import secrets
from typing import Any

PROTOCOL = "fidelity-bridge/v1"
BRIDGE_PATH = "/fidelity-bridge"
MAX_PAYLOAD_LENGTH = 8 * 1024 * 1024

_HEX64 = re.compile(r"[0-9a-f]{64}")


class ProtocolError(Exception):
    """A frame that is anything short of a perfect, in-order, untampered message."""


def new_nonce() -> str:
    """32 random bytes as lower-case hex."""
    return secrets.token_hex(32)


def is_nonce(value: Any) -> bool:
    return isinstance(value, str) and _HEX64.fullmatch(value) is not None


def _hmac(key: bytes, message: str) -> bytes:
    return hmac.new(key, message.encode("utf-8"), hashlib.sha256).digest()


def extension_proof(api_key: str, engine_nonce: str, extension_nonce: str) -> str:
    """What the extension must send to prove it holds the key."""
    return _hmac(
        api_key.encode("utf-8"), f"{PROTOCOL}|ext-proof|{engine_nonce}|{extension_nonce}"
    ).hex()


def engine_proof(api_key: str, engine_nonce: str, extension_nonce: str) -> str:
    """What the engine sends back, so the extension knows it is talking to
    something that holds the key too -- not merely to whatever answers at
    the address it was given."""
    return _hmac(
        api_key.encode("utf-8"), f"{PROTOCOL}|engine-proof|{engine_nonce}|{extension_nonce}"
    ).hex()


def session_key(api_key: str, engine_nonce: str, extension_nonce: str) -> bytes:
    """This connection's sealing key. Fresh nonces make it unique per
    connection, so nothing recorded from one can be played into another."""
    return _hmac(api_key.encode("utf-8"), f"{PROTOCOL}|session|{engine_nonce}|{extension_nonce}")


def message_mac(key: bytes, sender: str, seq: int, payload: str) -> str:
    return _hmac(key, f"{sender}|{seq}|{payload}").hex()


def proofs_match(expected: str, given: Any) -> bool:
    """Constant-time comparison, so the time taken says nothing about
    where a forged proof first went wrong."""
    return isinstance(given, str) and hmac.compare_digest(expected, given)


class Channel:
    """One authenticated connection's sealing and checking.

    Sequence numbers start at 1 in each direction and must arrive exactly
    in order. A failed check raises and does not advance the counter.
    """

    def __init__(self, key: bytes, *, sender: str = "engine", peer: str = "ext") -> None:
        self._key = key
        self.sender = sender
        self.peer = peer
        self.sent = 0
        self.received = 0

    def seal(self, message: dict) -> dict:
        payload = json.dumps(message, separators=(",", ":"), ensure_ascii=False)
        self.sent += 1
        return {
            "seq": self.sent,
            "payload": payload,
            "mac": message_mac(self._key, self.sender, self.sent, payload),
        }

    def open(self, envelope: Any) -> dict:
        if not isinstance(envelope, dict):
            raise ProtocolError("not an envelope")
        seq, payload, mac = envelope.get("seq"), envelope.get("payload"), envelope.get("mac")
        if not isinstance(seq, int) or isinstance(seq, bool) or seq != self.received + 1:
            raise ProtocolError(f"expected message {self.received + 1}, got {seq!r}")
        if not isinstance(payload, str) or len(payload) > MAX_PAYLOAD_LENGTH:
            raise ProtocolError("missing or oversized payload")
        if not isinstance(mac, str) or _HEX64.fullmatch(mac) is None:
            raise ProtocolError("missing MAC")
        if not hmac.compare_digest(message_mac(self._key, self.peer, seq, payload), mac):
            raise ProtocolError(f"message {seq} failed its integrity check")
        try:
            message = json.loads(payload)
        except ValueError as exc:
            raise ProtocolError(f"message {seq} is not JSON") from exc
        if not isinstance(message, dict):
            raise ProtocolError(f"message {seq} is not an object")
        self.received = seq
        return message
