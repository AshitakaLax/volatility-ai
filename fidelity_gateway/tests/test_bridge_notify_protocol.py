"""bridge/notify_protocol.py -- fidelity-bridge-notify/v1, the bridge's half.

The vectors live with the app (fidelity-bridge-notifier-android/, kept as
if it were its own repository) and its ProtocolVectorsTest reproduces the
same values: these tests are what keep the two speaking one language.
They skip when the app's folder is not checked out.
"""

from __future__ import annotations

import json

import pytest

from fidelity_gateway.bridge.notify_protocol import (
    NOTIFY_PROTOCOL,
    app_channel,
    app_proof,
    bridge_proof,
    notify_session_key,
)
from fidelity_gateway.bridge.protocol import (
    PROTOCOL,
    ProtocolError,
    extension_proof,
    message_mac,
    session_key,
)
from fidelity_gateway.tests.bridge_support import NOTIFY_KEY, NOTIFY_VECTORS

BRIDGE_NONCE = "a" * 64
APP_NONCE = "b" * 64


@pytest.fixture(scope="module")
def vectors() -> dict:
    path = NOTIFY_VECTORS / "notify-protocol-v1.json"
    if not path.is_file():
        pytest.skip(f"the app's vectors are not checked out at {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def test_the_vectors_are_for_this_protocol(vectors):
    assert vectors["protocol"] == NOTIFY_PROTOCOL


def test_the_handshake_reproduces_the_apps_vectors(vectors):
    args = (vectors["apiKey"], vectors["bridgeNonce"], vectors["appNonce"])
    assert app_proof(*args) == vectors["appProof"]
    assert bridge_proof(*args) == vectors["bridgeProof"]
    assert notify_session_key(*args).hex() == vectors["sessionKey"]


def test_every_sealed_message_reproduces_the_apps_vectors(vectors):
    key = bytes.fromhex(vectors["sessionKey"])
    assert any(not m["payload"].isascii() for m in vectors["messages"]), "UTF-8 must be pinned"
    for message in vectors["messages"]:
        expected = message_mac(key, message["sender"], message["seq"], message["payload"])
        assert expected == message["mac"], message


def test_the_vectors_open_on_the_side_that_receives_them(vectors):
    args = (vectors["apiKey"], vectors["bridgeNonce"], vectors["appNonce"])
    at_app, at_bridge = app_channel(*args, side="app"), app_channel(*args)
    for message in vectors["messages"]:
        envelope = {k: message[k] for k in ("seq", "payload", "mac")}
        receiver = at_app if message["sender"] == "bridge" else at_bridge
        assert receiver.open(envelope) == json.loads(message["payload"])


def test_the_two_proofs_and_the_session_key_all_differ():
    args = (NOTIFY_KEY, BRIDGE_NONCE, APP_NONCE)
    values = {app_proof(*args), bridge_proof(*args), notify_session_key(*args).hex()}
    assert len(values) == 3, "a proof reflected back must not pass as the other"


def test_nothing_proved_to_the_extension_counts_here():
    """The same key and nonces on the extension's protocol prove nothing on
    this one: the labels differ."""
    args = (NOTIFY_KEY, BRIDGE_NONCE, APP_NONCE)
    assert PROTOCOL != NOTIFY_PROTOCOL
    assert extension_proof(*args) != app_proof(*args)
    assert session_key(*args) != notify_session_key(*args)


def test_a_sealed_message_from_one_side_opens_on_the_other_only():
    bridge = app_channel(NOTIFY_KEY, BRIDGE_NONCE, APP_NONCE)
    app = app_channel(NOTIFY_KEY, BRIDGE_NONCE, APP_NONCE, side="app")
    sealed = bridge.seal({"type": "status", "status": {}})
    assert app.open(sealed) == {"type": "status", "status": {}}
    with pytest.raises(ProtocolError):
        # Reflected back at its sender, it fails: the MAC names the sender.
        app_channel(NOTIFY_KEY, BRIDGE_NONCE, APP_NONCE).open(sealed)


def test_a_tampered_or_replayed_message_is_refused():
    bridge = app_channel(NOTIFY_KEY, BRIDGE_NONCE, APP_NONCE)
    app = app_channel(NOTIFY_KEY, BRIDGE_NONCE, APP_NONCE, side="app")
    sealed = bridge.seal({"type": "notification", "notification": {"title": "Sold 3 TQQQ"}})
    forged = dict(sealed, payload=sealed["payload"].replace("Sold", "Bought"))
    with pytest.raises(ProtocolError, match="integrity"):
        app.open(forged)
    app.open(sealed)
    with pytest.raises(ProtocolError, match="expected message 2"):
        app.open(sealed)
