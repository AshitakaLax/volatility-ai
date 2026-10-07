"""
Connect `python cli.py live` to Fidelity, through the browser extension.

The live loop decides every trade itself. What it needs from here is one
broker object that satisfies the same LiveBroker shape AlpacaBroker does
-- and getting one for Fidelity takes a running bridge, a connected
extension, an authenticated session, and a broker built on that session
with the config's permissions. That sequence lives here, once, so
cli.py stays a list of steps and every step is testable without a
browser.

    connection = connect_live(config, state_db="state/ledger.db")
    broker = connection.broker     # hand to RuntimeLifecycle / the loop
    ...
    connection.close()             # stops the bridge; never the browser

What the config decides, and nothing else:
  * live.fidelity.dry_run false  -> a session that may place orders, and
    the placing broker (engine/brokers/broker_selection.py checks every
    condition);
  * live.fidelity.dry_run true   -> a preview-only session and broker.
The extension's trading switch is a lock on top that this code cannot
open: with it off, every order is refused before it reaches Fidelity,
and the loop waits rather than stopping.

The extension also reports back what became of every order it sent --
accepted, filled, rejected, refused. Those reports are appended to
fidelity_order_reports.jsonl beside the state database, and the broker
checks its own reading of each fill against them (bridge/order_reports.py).
"""

from __future__ import annotations

import sys
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from engine.brokers.broker_selection import build_broker
from fidelity_gateway.bridge import open_bridge
from fidelity_gateway.bridge.order_reports import OrderReports
from fidelity_gateway.session import FidelitySession, FidelitySessionError

JOURNAL_FILENAME = "fidelity_orders.jsonl"
REPORTS_FILENAME = "fidelity_order_reports.jsonl"
CREDENTIALS_WAIT_SECONDS = 10.0
PRIMED_CREDENTIALS_WAIT_SECONDS = 60.0


def _stderr(message: str) -> None:
    print(message, file=sys.stderr, flush=True)


@dataclass
class FidelityLiveConnection:
    """A connected broker, and the bridge it runs through."""

    broker: Any
    session: FidelitySession
    server: Any
    journal_path: Path | None
    reports_path: Path | None = None

    def close(self) -> None:
        """Stop the bridge. The browser and its Fidelity session are the
        user's, and stay as they are."""
        self.server.stop()


def default_journal_path(state_db: str | Path) -> Path:
    """Beside the live state database, so the two travel together."""
    return Path(state_db).with_name(JOURNAL_FILENAME)


def default_reports_path(state_db: str | Path) -> Path:
    """The extension's order reports, beside the state database too."""
    return Path(state_db).with_name(REPORTS_FILENAME)


def connect_live(
    config,
    *,
    state_db: str | Path,
    log: Callable[[str], None] = _stderr,
    bridge_opener: Callable[..., tuple[Any, Any]] = open_bridge,
    env_file: Path | None = None,
) -> FidelityLiveConnection:
    """Start the bridge, wait for the extension, and build the broker.

    Raises (ConfigurationError, FidelitySessionError, ...) with what to
    check -- RuntimeLifecycle turns any of them into RECOVERY_REQUIRED.
    The bridge is stopped again on every failure.
    """
    settings = config.live.fidelity
    bridge = settings.bridge
    places_orders = not settings.dry_run
    # Made before the bridge starts: the extension sends its whole order
    # log the moment it connects, and what the file already holds is not
    # logged or written again.
    reports_path = default_reports_path(state_db)
    reports_path.parent.mkdir(parents=True, exist_ok=True)
    order_reports = OrderReports(path=reports_path, log=log)
    server, page = bridge_opener(
        host=bridge.host,
        port=bridge.port,
        allow=bridge.allowed_clients,
        block=bridge.blocked_clients,
        env_file=env_file,
        wait_seconds=float(bridge.connect_timeout_seconds),
        log=log,
        order_reports=order_reports,
    )
    try:
        session = FidelitySession(
            page, allow_preview_endpoints=True, allow_order_endpoints=places_orders
        )
        session.attach()
        try:
            session.wait_for_credentials(timeout_seconds=CREDENTIALS_WAIT_SECONDS)
        except FidelitySessionError:
            log("[fidelity] no auth headers seen yet; loading Trader+ in the Fidelity tab")
            session.prime()
            session.wait_for_credentials(timeout_seconds=PRIMED_CREDENTIALS_WAIT_SECONDS)
        session.assert_authenticated()

        journal = None
        if places_orders:
            journal = Path(settings.journal_path or default_journal_path(state_db))
            journal.parent.mkdir(parents=True, exist_ok=True)
        broker = build_broker(
            config,
            fidelity_session=session,
            fidelity_journal_path=str(journal) if journal else None,
            fidelity_order_reports=order_reports,
        )
        broker.ping()
    except BaseException:
        server.stop()
        raise
    log(
        "[fidelity] connected through the extension: "
        + ("PLACING REAL ORDERS" if places_orders else "preview only, no orders")
        + (f"; journal {journal}" if journal else "")
        + f"; the extension's order reports go to {reports_path}"
    )
    return FidelityLiveConnection(
        broker=broker,
        session=session,
        server=server,
        journal_path=journal,
        reports_path=reports_path,
    )
