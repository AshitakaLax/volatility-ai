"""
The browser-extension route into Fidelity: no debugging port needed.

The Fidelity Bridge extension (its own repository, a submodule here at
fidelity-bridge-chrome-extension/) runs in the browser you are signed into
and connects to this package's BridgeServer. BridgePage then stands in for
a Playwright page, so FidelitySession and every broker built on it work
unchanged:

    server, page = open_bridge()                 # waits for the extension
    session = FidelitySession(page)              # read-only, as ever
    session.attach(); session.wait_for_credentials()

Two independent locks guard orders: the session's endpoint allowlist here,
and the extension's own, which allows nothing beyond reads until you
switch it on in the extension's settings.

    python -m fidelity_gateway.bridge keygen     # API key into .env
    python -m fidelity_gateway.bridge serve      # run the bridge
    python -m fidelity_gateway.bridge check --account <number> --account-name "<name>"
"""

from __future__ import annotations

import sys
from collections.abc import Callable, Sequence
from pathlib import Path

from engine.core.exceptions import ConfigurationError
from fidelity_gateway.bridge.ip_policy import AddressPolicy
from fidelity_gateway.bridge.keys import API_KEY_ENV_VAR, BridgeApiKey, load_api_key
from fidelity_gateway.bridge.page import BridgePage
from fidelity_gateway.bridge.server import (
    DEFAULT_HOST,
    DEFAULT_PORT,
    BridgeError,
    BridgeRefusal,
    BridgeServer,
    BridgeUnavailable,
)

DEFAULT_ALLOWED_CLIENTS = ("127.0.0.1", "::1")

__all__ = [
    "API_KEY_ENV_VAR",
    "DEFAULT_ALLOWED_CLIENTS",
    "DEFAULT_HOST",
    "DEFAULT_PORT",
    "AddressPolicy",
    "BridgeApiKey",
    "BridgeError",
    "BridgePage",
    "BridgeRefusal",
    "BridgeServer",
    "BridgeUnavailable",
    "load_api_key",
    "open_bridge",
]


def _stderr(message: str) -> None:
    print(message, file=sys.stderr, flush=True)


def open_bridge(
    *,
    host: str = DEFAULT_HOST,
    port: int = DEFAULT_PORT,
    allow: Sequence[str] = DEFAULT_ALLOWED_CLIENTS,
    block: Sequence[str] = (),
    env_file: Path | None = None,
    wait_seconds: float = 60.0,
    log: Callable[[str], None] = _stderr,
) -> tuple[BridgeServer, BridgePage]:
    """Start the bridge, wait for the extension, and return (server, page).

    Call server.stop() when done. Raises ConfigurationError -- with what
    to check -- if the key is missing or the extension does not connect.
    """
    key = load_api_key(env_file=env_file)
    policy = AddressPolicy.from_entries(allow, block)
    server = BridgeServer(key, host=host, port=port, policy=policy, log=log)
    server.start()
    log(f"[bridge] listening on {server.url}; waiting up to {wait_seconds:.0f}s for the extension")
    if not server.wait_for_extension(wait_seconds):
        server.stop()
        raise ConfigurationError(
            f"The Fidelity Bridge extension did not connect within {wait_seconds:.0f}s. In its "
            f"settings, check the engine address and port ({port}), that the API key matches "
            f"{API_KEY_ENV_VAR}, and that the browser's address is allowed here "
            f"(allowed: {', '.join(policy.allowed)})."
        )
    return server, BridgePage(server)
