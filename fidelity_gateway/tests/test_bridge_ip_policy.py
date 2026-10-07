"""fidelity_gateway/bridge/ip_policy.py -- which browsers may connect.

Every decision must match the extension's (src/lib/ip-policy.js). The
cases inline here are the extension's tests/vectors/ip-policy.json; when
the submodule is checked out, the file is read too.
"""

from __future__ import annotations

import ipaddress
import json

import pytest

from engine.core.exceptions import ConfigurationError
from fidelity_gateway.bridge.ip_policy import (
    AddressPolicy,
    canonical_entry,
    parse_ip,
    parse_network,
)
from fidelity_gateway.tests.bridge_support import VECTORS

CASES = [
    ("127.0.0.1", ["127.0.0.1"], [], True),
    ("127.0.0.2", ["127.0.0.1"], [], False),
    ("172.16.0.134", ["172.16.0.0/24"], [], True),
    ("172.16.1.1", ["172.16.0.0/24"], [], False),
    ("172.16.0.134", ["172.16.0.0/24"], ["172.16.0.134"], False),
    ("10.0.0.5", [], [], False),
    ("localhost", ["127.0.0.1"], [], False),
    ("::1", ["::1"], [], True),
    ("::ffff:127.0.0.1", ["127.0.0.1"], [], True),
    ("127.0.0.1", ["::ffff:127.0.0.1"], [], True),
    ("2001:db8::1", ["2001:db8::/32"], [], True),
    ("2001:db9::1", ["2001:db8::/32"], [], False),
    ("192.168.1.10", ["0.0.0.0/0"], ["192.168.1.0/24"], False),
    ("192.168.2.10", ["0.0.0.0/0"], ["192.168.1.0/24"], True),
    ("010.0.0.1", ["0.0.0.0/0"], [], False),
    ("127.0.0.1", ["127.0.0.1"], ["not-an-ip"], False),
    ("127.0.0.1", ["127.0.0.1/33"], [], False),
    ("172.16.0.5", ["172.16.0.9/24"], [], True),
    ("fe80::1%eth0", ["fe80::/10"], [], False),
    ("1.2.3.4", ["::/0"], [], False),
    ("[::1]", ["::1"], [], True),
    (" 127.0.0.1 ", ["127.0.0.1"], [], True),
    ("64:ff9b::192.0.2.33", ["64:ff9b::/96"], [], True),
    ("1::2::3", ["::/0"], [], False),
    ("256.1.1.1", ["0.0.0.0/0"], [], False),
]


@pytest.mark.parametrize("address,allowed,blocked,expected", CASES)
def test_the_shared_cases(address, allowed, blocked, expected):
    verdict, reason = AddressPolicy(allowed, blocked).evaluate(address)
    assert verdict is expected, reason


@pytest.mark.skipif(
    not (VECTORS / "ip-policy.json").is_file(), reason="extension submodule not checked out"
)
def test_every_case_in_the_extensions_vector_file():
    cases = json.loads((VECTORS / "ip-policy.json").read_text(encoding="utf-8"))["cases"]
    for case in cases:
        verdict, reason = AddressPolicy(case["allowed"], case["blocked"]).evaluate(case["address"])
        assert verdict is case["expect"], f"{case['name']}: {reason}"
    inline = [(a, al, bl, ex) for a, al, bl, ex in CASES]
    on_disk = [(c["address"], c["allowed"], c["blocked"], c["expect"]) for c in cases]
    assert inline == on_disk, "the inline cases have drifted from the extension's file"


def test_blocked_wins_and_says_by_what():
    verdict, reason = AddressPolicy(["0.0.0.0/0"], ["10.0.0.0/8"]).evaluate("10.1.2.3")
    assert verdict is False and "blocked by 10.0.0.0/8" in reason


def test_an_empty_allowlist_allows_nothing():
    verdict, reason = AddressPolicy([]).evaluate("127.0.0.1")
    assert verdict is False and "no allowed" in reason


def test_python_leniencies_are_closed():
    """ipaddress accepts these; the extension refuses them, so must we."""
    assert ipaddress.ip_network("10.0.0.0/08")  # Python alone would take it
    assert parse_network("10.0.0.0/08") is None
    assert parse_network("10.0.0.0/255.255.255.0") is None
    assert parse_ip("fe80::1%eth0") is None
    assert parse_network("fe80::1%eth0/64") is None


def test_mapped_addresses_and_ranges_are_ipv4():
    assert parse_ip("::ffff:10.0.0.1") == ipaddress.IPv4Address("10.0.0.1")
    assert parse_network("::ffff:10.0.0.0/120") == ipaddress.IPv4Network("10.0.0.0/24")
    assert parse_network("::ffff:0:0/95").version == 6, "below /96 it is not a mapped range"


def test_non_strings_are_not_addresses():
    assert parse_ip(None) is None and parse_ip(1234) is None
    assert parse_network(None) is None


def test_canonical_entries():
    assert canonical_entry("10.0.0.9/8") == "10.0.0.0/8"
    assert canonical_entry("2001:DB8::1") == "2001:db8::1"
    assert canonical_entry("::ffff:10.0.0.1") == "10.0.0.1"
    assert canonical_entry("nope") is None


def test_from_entries_validates_up_front():
    policy = AddressPolicy.from_entries(["172.16.0.9/24", "::1"], ["172.16.0.200"])
    assert policy.allowed == ("172.16.0.0/24", "::1")
    assert policy.blocked == ("172.16.0.200",)
    with pytest.raises(ConfigurationError, match="Host names are not accepted"):
        AddressPolicy.from_entries(["my-pc"])
    with pytest.raises(ConfigurationError, match="Not an IP"):
        AddressPolicy.from_entries(["127.0.0.1"], ["10.0.0.0/33"])
    with pytest.raises(ConfigurationError, match="allows nothing"):
        AddressPolicy.from_entries([])


def test_an_invalid_entry_at_evaluation_refuses_everything():
    assert AddressPolicy(["garbage", "127.0.0.1"]).evaluate("127.0.0.1")[0] is False
    assert AddressPolicy(["127.0.0.1"], ["garbage"]).evaluate("127.0.0.1")[0] is False
