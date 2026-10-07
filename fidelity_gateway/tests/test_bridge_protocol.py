"""fidelity_gateway/bridge/protocol.py -- the handshake and sealed messages.

The vector values below are the ones in the extension's
tests/vectors/protocol-v1.json, which its own suite reproduces in
JavaScript. Both sides matching the same numbers is what proves they
speak the same protocol. When the submodule is checked out, the file
itself is read as well, so the two copies cannot drift apart.
"""

from __future__ import annotations

import json

import pytest

from fidelity_gateway.bridge.protocol import (
    BRIDGE_PATH,
    MAX_PAYLOAD_LENGTH,
    PROTOCOL,
    Channel,
    ProtocolError,
    engine_proof,
    extension_proof,
    is_nonce,
    message_mac,
    new_nonce,
    proofs_match,
    session_key,
)
from fidelity_gateway.tests.bridge_support import VECTORS

VECTOR = {
    "protocol": "fidelity-bridge/v1",
    "apiKey": "vectors-only-key-0123456789abcdefghijklmnop",
    "engineNonce": "0fb672b9fef11c3c14dc513aaee5f06619e2830f5525c244ee5d26e2949ac8f1",
    "extensionNonce": "c50835b20daa3f83b568c4fcd3a72291fce7e7eb600b6492acb304c439b12b39",
    "extensionProof": "271ddeb0d789c5e125b33d612e24d4e7a0809bd673de51d50b2a5860880643fb",
    "engineProof": "76ac5d66d7e563aa354744b741c27f410f3c94132adea009fbb15dab2ed4c2e1",
    "sessionKey": "96b769df75614084ae33331cf4ccd686b1220912f144c20852840e21f2bcdf8e",
    "envelopes": [
        {
            "sender": "engine",
            "seq": 1,
            "payload": '{"type":"request","id":"1","command":"status","args":{}}',
            "mac": "3ba308b89899a8d9c4e082680e8cf4deb87c1b807a2ea0787e6ddcb47a6bb2ee",
        },
        {
            "sender": "ext",
            "seq": 1,
            "payload": '{"type":"response","id":"1","ok":true,"result":{"extensionVersion":"0.1.0"}}',
            "mac": "8e51ba59e587f5ece2e6e27b637e6e55438499f286f5b44fe2af563157c67eb5",
        },
    ],
}


def _check_vector(v: dict) -> None:
    assert v["protocol"] == PROTOCOL
    key, ne, nx = v["apiKey"], v["engineNonce"], v["extensionNonce"]
    assert extension_proof(key, ne, nx) == v["extensionProof"]
    assert engine_proof(key, ne, nx) == v["engineProof"]
    assert session_key(key, ne, nx).hex() == v["sessionKey"]
    for envelope in v["envelopes"]:
        mac = message_mac(
            bytes.fromhex(v["sessionKey"]), envelope["sender"], envelope["seq"], envelope["payload"]
        )
        assert mac == envelope["mac"]


def test_the_shared_vectors():
    _check_vector(VECTOR)


@pytest.mark.skipif(
    not (VECTORS / "protocol-v1.json").is_file(), reason="extension submodule not checked out"
)
def test_the_extensions_own_vector_file_matches_too():
    on_disk = json.loads((VECTORS / "protocol-v1.json").read_text(encoding="utf-8"))
    _check_vector(on_disk)
    assert {k: on_disk[k] for k in VECTOR} == VECTOR, "the inline copy has drifted from the file"


def test_the_engine_seals_its_vector_envelope_exactly():
    channel = Channel(bytes.fromhex(VECTOR["sessionKey"]), sender="engine", peer="ext")
    sealed = channel.seal({"type": "request", "id": "1", "command": "status", "args": {}})
    first = VECTOR["envelopes"][0]
    assert sealed == {"seq": first["seq"], "payload": first["payload"], "mac": first["mac"]}


def test_the_engine_opens_the_extensions_vector_envelope():
    channel = Channel(bytes.fromhex(VECTOR["sessionKey"]), sender="engine", peer="ext")
    reply = VECTOR["envelopes"][1]
    message = channel.open({"seq": reply["seq"], "payload": reply["payload"], "mac": reply["mac"]})
    assert message == {
        "type": "response",
        "id": "1",
        "ok": True,
        "result": {"extensionVersion": "0.1.0"},
    }


def test_constants():
    assert BRIDGE_PATH == "/fidelity-bridge"
    assert MAX_PAYLOAD_LENGTH == 8 * 1024 * 1024


def test_the_two_proofs_differ_so_neither_reflects_as_the_other():
    assert extension_proof("k" * 40, "a" * 64, "b" * 64) != engine_proof(
        "k" * 40, "a" * 64, "b" * 64
    )


def test_a_proof_depends_on_the_key_and_both_nonces():
    base = extension_proof("k" * 40, "a" * 64, "b" * 64)
    assert extension_proof("j" * 40, "a" * 64, "b" * 64) != base
    assert extension_proof("k" * 40, "c" * 64, "b" * 64) != base
    assert extension_proof("k" * 40, "a" * 64, "c" * 64) != base


def _pair():
    key = session_key("k" * 40, "a" * 64, "b" * 64)
    return Channel(key, sender="engine", peer="ext"), Channel(key, sender="ext", peer="engine")


def test_channels_round_trip_with_rising_sequence_numbers():
    engine, ext = _pair()
    for i in range(1, 4):
        sealed = engine.seal({"type": "request", "id": str(i)})
        assert sealed["seq"] == i
        assert ext.open(sealed) == {"type": "request", "id": str(i)}
    assert engine.open(ext.seal({"type": "response", "id": "1"})) == {"type": "response", "id": "1"}


def test_an_altered_payload_is_refused():
    engine, ext = _pair()
    sealed = engine.seal({"type": "request", "id": "1", "args": {"path": "/a"}})
    with pytest.raises(ProtocolError, match="integrity"):
        ext.open({**sealed, "payload": sealed["payload"].replace("/a", "/b")})


def test_a_replay_is_refused():
    engine, ext = _pair()
    sealed = engine.seal({"type": "request", "id": "1"})
    ext.open(sealed)
    with pytest.raises(ProtocolError, match="expected message 2"):
        ext.open(sealed)


def test_a_gap_is_refused():
    engine, ext = _pair()
    engine.seal({"type": "request", "id": "1"})
    with pytest.raises(ProtocolError, match="expected message 1"):
        ext.open(engine.seal({"type": "request", "id": "2"}))


def test_a_message_cannot_be_bounced_back_to_its_sender():
    engine, _ = _pair()
    mine = engine.seal({"type": "request", "id": "1"})
    other_engine = Channel(engine._key, sender="engine", peer="ext")
    with pytest.raises(ProtocolError, match="integrity"):
        other_engine.open(mine)


def test_a_failed_check_does_not_advance_the_counter():
    engine, ext = _pair()
    sealed = engine.seal({"type": "request", "id": "1"})
    with pytest.raises(ProtocolError):
        ext.open({**sealed, "mac": "0" * 64})
    assert ext.open(sealed) == {"type": "request", "id": "1"}


@pytest.mark.parametrize(
    "envelope",
    [
        None,
        "text",
        [],
        {"seq": True, "payload": "{}", "mac": "0" * 64},
        {"seq": "1", "payload": "{}", "mac": "0" * 64},
        {"seq": 1, "payload": 5, "mac": "0" * 64},
        {"seq": 1, "payload": "{}", "mac": "short"},
        {"seq": 1, "payload": "{}", "mac": "A" * 64},
        {"seq": 1, "payload": "x" * (MAX_PAYLOAD_LENGTH + 1), "mac": "0" * 64},
    ],
)
def test_malformed_envelopes_are_refused(envelope):
    _, ext = _pair()
    with pytest.raises(ProtocolError):
        ext.open(envelope)


@pytest.mark.parametrize("payload", ["not json", "[1, 2]", "null"])
def test_a_valid_mac_on_a_non_object_payload_is_still_refused(payload):
    key = session_key("k" * 40, "a" * 64, "b" * 64)
    ext = Channel(key, sender="ext", peer="engine")
    with pytest.raises(ProtocolError):
        ext.open({"seq": 1, "payload": payload, "mac": message_mac(key, "engine", 1, payload)})


def test_nonces_and_proof_comparison():
    assert is_nonce(new_nonce()) and new_nonce() != new_nonce()
    for bad in ["ab", "AB" * 32, "g" * 64, 5, None]:
        assert not is_nonce(bad)
    assert proofs_match("abc", "abc")
    assert not proofs_match("abc", "abd")
    assert not proofs_match("abc", None)


def test_non_ascii_payloads_seal_and_open():
    engine, ext = _pair()
    assert ext.open(engine.seal({"note": "café ≥ 5%"})) == {"note": "café ≥ 5%"}
