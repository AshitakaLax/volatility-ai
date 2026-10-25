"""
fidelity-bridge-notify/v1 -- the bridge's half of the protocol spoken with
apps that listen for its notifications (the Fidelity Bridge Notifier for
Android, fidelity-bridge-notifier-android/, kept as if it were its own
repository).

The full description is PROTOCOL.md in the app's folder. It is
protocol.py's design with its own labels, so nothing proved on one
connection means anything on the other:

  * Neither side ever sends the key. The app answers the bridge's random
    challenge with an HMAC, and the bridge answers back. Both proofs bind
    both nonces and carry different labels.
  * After the handshake every message, both ways, is sealed with
    protocol.Channel: a sequence number and an HMAC under a key derived
    for that connection alone. Over a plain ws:// on a home network, that
    is what stops anyone on it from forging a "Sold" notification.

The values in the app's core/src/test/resources/vectors/notify-protocol-v1.json
are reproduced by fidelity_gateway/tests/test_bridge_notify_protocol.py,
which is what keeps this module and the app's Protocol.kt in agreement.
"""

from __future__ import annotations

import hashlib
import hmac

from fidelity_gateway.bridge.protocol import Channel

NOTIFY_PROTOCOL = "fidelity-bridge-notify/v1"
NOTIFY_PATH = "/notifications"

__all__ = [
    "NOTIFY_PATH",
    "NOTIFY_PROTOCOL",
    "app_channel",
    "app_proof",
    "bridge_proof",
    "notify_session_key",
]


def _hmac(api_key: str, message: str) -> bytes:
    return hmac.new(api_key.encode("utf-8"), message.encode("utf-8"), hashlib.sha256).digest()


def app_proof(api_key: str, bridge_nonce: str, app_nonce: str) -> str:
    """What an app must send to prove it holds the key."""
    return _hmac(api_key, f"{NOTIFY_PROTOCOL}|app-proof|{bridge_nonce}|{app_nonce}").hex()


def bridge_proof(api_key: str, bridge_nonce: str, app_nonce: str) -> str:
    """What the bridge sends back, so the app knows it reached something
    that holds the key -- not merely whatever answers at that address."""
    return _hmac(api_key, f"{NOTIFY_PROTOCOL}|bridge-proof|{bridge_nonce}|{app_nonce}").hex()


def notify_session_key(api_key: str, bridge_nonce: str, app_nonce: str) -> bytes:
    """This connection's sealing key."""
    return _hmac(api_key, f"{NOTIFY_PROTOCOL}|session|{bridge_nonce}|{app_nonce}")


def app_channel(
    api_key: str, bridge_nonce: str, app_nonce: str, *, side: str = "bridge"
) -> Channel:
    """The sealed channel for one app connection, from `side`'s end."""
    key = notify_session_key(api_key, bridge_nonce, app_nonce)
    if side == "bridge":
        return Channel(key, sender="bridge", peer="app")
    return Channel(key, sender="app", peer="bridge")
