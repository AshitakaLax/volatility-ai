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
    python -m fidelity_gateway.bridge host --config config/fidelity_live.yaml --socket P

A Fidelity deployment runs the bridge as a host of its own (host.py, the
fidelity-bridge service), up between sessions too; with VAI_BRIDGE_SOCKET
naming its socket, open_bridge() attaches to it (attach.py) instead of
listening -- the same (server, page), so no caller changes.

Apps -- the Fidelity Bridge Notifier for Android -- hear what the bridge
sees through a listener of their own, with a key of their own
(notify_server.py). The bridge host runs it when the config's
live.fidelity.bridge.notifications is enabled; `serve --notify` runs one
to try it out:

    python -m fidelity_gateway.bridge keygen --notify    # the app's key into .env
    python -m fidelity_gateway.bridge serve --notify --notify-host 0.0.0.0 \
        --notify-allow-client 192.168.1.0/24
"""

from __future__ import annotations

import os
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
    socket_path: str | Path | None = None,
    client: dict | None = None,
) -> tuple[BridgeServer, BridgePage]:
    """Start the bridge, wait for the extension, and return (server, page).

    Call server.stop() when done. Raises ConfigurationError -- with what
    to check -- if the key is missing, and BridgeUnavailable (a
    ConfigurationError that clears on its own) if the port is taken or the
    extension does not connect.
    `order_reports` receives the extension's order confirmations; pass
    one with a path to keep them on disk (server.order_reports either way).

    With `socket_path` -- or VAI_BRIDGE_SOCKET -- naming a bridge host's
    socket, ATTACHES to that host instead (attach.py): the "server" is an
    AttachedBridge and `client` ({"process": "loop" | "check" | ...})
    says who is attaching. A host that is not running is BridgeUnavailable;
    this never falls back to listening itself.

    Apps' notifications are not started here: a session's bridge lives
    only as long as the session. The bridge host, which outlives them,
    runs their listener (build_notifier).
    """
    path = socket_path or os.environ.get("VAI_BRIDGE_SOCKET")
    if path:
        return _attach(
            path, wait_seconds=wait_seconds, log=log, order_reports=order_reports, client=client
        )
    key = load_api_key(env_file=env_file)
    policy = AddressPolicy.from_entries(allow, block)
    server = BridgeServer(
        key, host=host, port=port, policy=policy, log=log, order_reports=order_reports
    )
    server.start()
    log(f"[bridge] listening on {server.url}; waiting up to {wait_seconds:.0f}s for the extension")
    if not server.wait_for_extension(wait_seconds):
        refused = server.connection_report().get("last_refused")
        server.stop()
        raise BridgeUnavailable(
            f"The Fidelity Bridge extension did not connect within {wait_seconds:.0f}s. "
            + (f"It was turned away: {refused['client']}: {refused['reason']}. " if refused else "")
            + f"In its settings, check the engine address and port ({port}), that the API key "
            f"matches {API_KEY_ENV_VAR}, and that the browser's address is allowed here "
            f"(allowed: {', '.join(policy.allowed)}).",
            code="not_connected",
        )
    return server, BridgePage(server)


def _attach(path, *, wait_seconds: float, log, order_reports, client) -> tuple:
    from fidelity_gateway.bridge.attach import AttachedBridge

    bridge = AttachedBridge.attach(path, client=client, log=log, order_reports=order_reports)
    log(f"[bridge] attached to the bridge host at {path}")
    if not bridge.wait_for_extension(wait_seconds):
        report = bridge.connection_report()
        refused = report.get("last_refused")
        bridge.stop()
        raise BridgeUnavailable(
            f"The Fidelity Bridge extension is not connected to the bridge host (waited "
            f"{wait_seconds:.0f}s). "
            + (f"It was turned away: {refused['client']}: {refused['reason']}. " if refused else "")
            + "The Live page's Fidelity section shows what the host sees.",
            code="not_connected",
        )
    return bridge, BridgePage(bridge)


def build_notifier(
    settings: NotifySettings,
    extension_key: BridgeApiKey,
    *,
    notifications: Notifications | None = None,
    env_file: Path | None = None,
    log: Callable[[str], None] = _stderr,
) -> NotificationServer:
    """The listener apps connect to, not yet started, serving
    `notifications` (a new hub for `settings.events` if none is given). Its
    key is FIDELITY_BRIDGE_NOTIFY_KEY, and must not be the extension's: a
    phone holding that one could pose as the extension."""
    key = load_api_key(env_file=env_file, name=NOTIFY_KEY_ENV_VAR)
    if key.value == extension_key.value:
        raise ConfigurationError(
            f"{NOTIFY_KEY_ENV_VAR} is the same as {API_KEY_ENV_VAR}. Give apps a key of their "
            "own -- `python -m fidelity_gateway.bridge keygen --notify` -- so a phone never "
            "holds the key that lets the extension in."
        )
    return NotificationServer(
        key,
        notifications if notifications is not None else Notifications(settings.events, log=log),
        host=settings.host,
        port=settings.port,
        policy=AddressPolicy.from_entries(settings.allowed_clients, settings.blocked_clients),
        log=log,
    )
