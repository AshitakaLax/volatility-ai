"""
Which client addresses may connect to the bridge.

The engine's half of the address rules the extension also applies (its
src/lib/ip-policy.js): an allowlist and a blocklist of IP addresses and
CIDR ranges. The blocklist wins; an empty allowlist allows nothing; an
entry that does not parse refuses everything rather than being skipped.

The two implementations must agree on every decision, which
fidelity_gateway/tests/test_bridge_ip_policy.py checks against the
extension's tests/vectors/ip-policy.json. Python's ipaddress is more
lenient than that contract in three places, each closed here:

  * a prefix written with a leading zero ("/08") or as a netmask
    ("/255.255.255.0") is refused, as the extension refuses it;
  * a zone id ("fe80::1%eth0") is refused -- it names an interface on one
    machine and means nothing in a shared rule;
  * an IPv4-mapped address or range (::ffff:192.0.2.1) is treated as the
    IPv4 address it carries, which is also how a dual-stack socket
    reports an IPv4 client.
"""

from __future__ import annotations

import ipaddress
import re
from collections.abc import Iterable

from engine.core.exceptions import ConfigurationError

IPAddress = ipaddress.IPv4Address | ipaddress.IPv6Address
IPNetwork = ipaddress.IPv4Network | ipaddress.IPv6Network

_PREFIX = re.compile(r"0|[1-9][0-9]{0,2}")


def _unbracket(text: str) -> str:
    text = text.strip()
    if text.startswith("[") and text.endswith("]"):
        text = text[1:-1]
    return text


def parse_ip(text: object) -> IPAddress | None:
    """An IP literal, or None. Host names are not IP literals."""
    if not isinstance(text, str):
        return None
    value = _unbracket(text)
    if "%" in value:
        return None
    try:
        ip = ipaddress.ip_address(value)
    except ValueError:
        return None
    if isinstance(ip, ipaddress.IPv6Address) and ip.ipv4_mapped is not None:
        return ip.ipv4_mapped
    return ip


def parse_network(text: object) -> IPNetwork | None:
    """An address or CIDR range, or None. Host bits are cleared."""
    if not isinstance(text, str):
        return None
    value = text.strip()
    address, slash, prefix = value.partition("/")
    address = _unbracket(address)
    if "%" in address or (slash and _PREFIX.fullmatch(prefix) is None):
        return None
    try:
        network = ipaddress.ip_network(f"{address}/{prefix}" if slash else address, strict=False)
    except ValueError:
        return None
    if isinstance(network, ipaddress.IPv6Network) and network.prefixlen >= 96:
        mapped = network.network_address.ipv4_mapped
        if mapped is not None:
            return ipaddress.IPv4Network((mapped, network.prefixlen - 96))
    return network


def canonical_entry(text: str) -> str | None:
    network = parse_network(text)
    if network is None:
        return None
    if network.prefixlen == network.max_prefixlen:
        return str(network.network_address)
    return str(network)


class AddressPolicy:
    """Allowed and blocked client addresses, decided the extension's way."""

    def __init__(self, allowed: Iterable[str] = (), blocked: Iterable[str] = ()) -> None:
        self.allowed = tuple(allowed)
        self.blocked = tuple(blocked)

    @classmethod
    def from_entries(cls, allowed: Iterable[str], blocked: Iterable[str] = ()) -> AddressPolicy:
        """Validate up front, for a policy built from the command line:
        a typo should stop the server starting, not quietly refuse every
        connection later."""
        allowed, blocked = list(allowed), list(blocked)
        bad = [entry for entry in [*allowed, *blocked] if parse_network(entry) is None]
        if bad:
            raise ConfigurationError(
                f"Not an IP address or CIDR range: {bad}. Host names are not accepted -- "
                "a name is resolved at connect time, so a rule written against one "
                "could be steered elsewhere."
            )
        if not allowed:
            raise ConfigurationError(
                "No allowed client addresses. An empty allowlist allows nothing; name "
                "the browser's computer, e.g. 127.0.0.1 when it is this one."
            )
        return cls([canonical_entry(e) for e in allowed], [canonical_entry(e) for e in blocked])

    def evaluate(self, address: object) -> tuple[bool, str]:
        ip = parse_ip(address)
        if ip is None:
            return False, f"{address!r} is not an IP address"
        for entry in self.blocked:
            network = parse_network(entry)
            if network is None:
                return False, f"blocked entry {entry!r} is invalid"
            if ip.version == network.version and ip in network:
                return False, f"{ip} is blocked by {entry}"
        if not self.allowed:
            return False, "no allowed client addresses are configured"
        for entry in self.allowed:
            network = parse_network(entry)
            if network is None:
                return False, f"allowed entry {entry!r} is invalid"
            if ip.version == network.version and ip in network:
                return True, f"{ip} is allowed by {entry}"
        return False, f"{ip} is not in the allowed client addresses"
