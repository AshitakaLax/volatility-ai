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

Apps -- the Fidelity Bridge Notifier for Android -- can hear what the
bridge sees through a listener of their own, with a key of their own
(notify_server.py):

    python -m fidelity_gateway.bridge keygen --notify    # the app's key into .env
    python -m fidelity_gateway.bridge serve --notify --notify-host 0.0.0.0 \
        --notify-allow-client 192.168.1.0/24
"""

from __future__ import annotations

import sys
from collections.abc import Callable, Sequence
from pathlib import Path

from engine.core.exceptions import ConfigurationError
from fidelity_gateway.bridge.ip_policy import AddressPolicy
from fidelity_gateway.bridge.keys import (
    API_KEY_ENV_VAR,
    NOTIFY_KEY_ENV_VAR,
    BridgeApiKey,
    load_api_key,
)
from fidelity_gateway.bridge.notifications import Notification, Notifications
from fidelity_gateway.bridge.notify_server import NotificationServer, NotifySettings
from fidelity_gateway.bridge.order_reports import OrderReport, OrderReports
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
    "NOTIFY_KEY_ENV_VAR",
    "AddressPolicy",
    "BridgeApiKey",
    "BridgeError",
    "BridgePage",
    "BridgeRefusal",
    "BridgeServer",
    "BridgeUnavailable",
    "Notification",
    "NotificationServer",
    "Notifications",
    "NotifySettings",
    "OrderReport",
    "OrderReports",
    "build_notifier",
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
    order_reports: OrderReports | None = None,
    notify: NotifySettings | None = None,
) -> tuple[BridgeServer, BridgePage]:
    """Start the bridge, wait for the extension, and return (server, page).

    Call server.stop() when done. Raises ConfigurationError -- with what
    to check -- if the key is missing or the extension does not connect.
    `order_reports` receives the extension's order confirmations; pass
    one with a path to keep them on disk (server.order_reports either way).
    `notify` also starts the listener apps connect to (notify_server.py),
    which stops with the bridge.
    """
    key = load_api_key(env_file=env_file)
    policy = AddressPolicy.from_entries(allow, block)
    notifier = build_notifier(notify, key, env_file=env_file, log=log) if notify else None
    server = BridgeServer(
        key,
        host=host,
        port=port,
        policy=policy,
        log=log,
        order_reports=order_reports,
        notifier=notifier,
    )
    server.start()
    if notifier is not None:
        log(
            f"[notify] apps may connect at {notifier.url} "
            f"(allowed: {', '.join(notify.allowed_clients)}; "
            f"events: {', '.join(notifier.notifications.events) or 'none'})"
        )
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


def build_notifier(
    settings: NotifySettings,
    extension_key: BridgeApiKey,
    *,
    env_file: Path | None = None,
    log: Callable[[str], None] = _stderr,
) -> NotificationServer:
    """The listener apps connect to, not yet started. Its key is
    FIDELITY_BRIDGE_NOTIFY_KEY, and must not be the extension's: a phone
    holding that one could pose as the extension."""
    key = load_api_key(env_file=env_file, name=NOTIFY_KEY_ENV_VAR)
    if key.value == extension_key.value:
        raise ConfigurationError(
            f"{NOTIFY_KEY_ENV_VAR} is the same as {API_KEY_ENV_VAR}. Give apps a key of their "
            "own -- `python -m fidelity_gateway.bridge keygen --notify` -- so a phone never "
            "holds the key that lets the extension in."
        )
    return NotificationServer(
        key,
        Notifications(settings.events, log=log),
        host=settings.host,
        port=settings.port,
        policy=AddressPolicy.from_entries(settings.allowed_clients, settings.blocked_clients),
        log=log,
    )
