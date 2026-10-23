"""
Pick the broker a config asks for, and refuse anything it cannot honour.

`LiveTradingLoop` takes an already-constructed broker, so nothing in
this project previously decided WHICH one from `live.broker`. That was
fine while there was one venue. With two it becomes the place a
misconfiguration turns into trading at the wrong place, so it is one
function with the checks written down.

--------------------------------------------------------------------
THE TWO VENUES ARE NOT CONSTRUCTED THE SAME WAY, AND CANNOT BE

Alpaca is built from credentials: an API key and secret, loadable from
the environment with no human present. That is why
LiveExecutionLoop takes a `broker_factory(credentials)`.

Fidelity is built from a LIVE, ALREADY-AUTHENTICATED BROWSER SESSION.
There is no credential that produces one: Fidelity refuses a
Playwright-launched browser outright, so the only working path attaches
to a browser a human has logged into. A `broker_factory(credentials)`
shape cannot express that, and pretending it could -- by having the
factory launch a browser and log in -- is exactly the thing that does
not work.

So this dispatcher takes both, requires the right one for the venue
named, and says which is missing rather than failing later with an
attribute error.

--------------------------------------------------------------------
dry_run DECIDES WHICH FIDELITY ADAPTER, AND NOTHING IS INFERRED

  dry_run: true   fidelity_gateway/broker.py's FidelityBroker: preview
                  only. It holds no place-order capability and the
                  transport refuses one.
  dry_run: false  fidelity_gateway/placing_broker.py's
                  FidelityPlacingBroker: REAL orders. Built only when
                  every one of these holds, each checked here rather than
                  assumed:
                    * live.paper_trading is false -- the file must say it
                      trades real money, not merely stop saying it doesn't;
                    * the session was built to allow order endpoints, so
                      the transport agrees with the config;
                    * live.fidelity names allowed_symbols and a positive
                      max_order_value (config validation), and a journal
                      path is known.
                  The extension in the user's browser is a further lock
                  this code cannot open: its trading switch refuses every
                  order until the user turns it on.

Silently previewing while the config says orders are being placed would
be the worst outcome available -- the operator believes orders are
live, the strategy believes its sells are resting, and nothing trades.
So nothing here falls back from one adapter to the other; a missing
condition raises.
"""

from __future__ import annotations

import logging
from typing import Any

from engine.core.exceptions import ConfigurationError

logger = logging.getLogger("Optimizer")

SUPPORTED_BROKERS = ("alpaca", "fidelity")


def build_broker(
    config,
    *,
    credentials: Any = None,
    fidelity_session: Any = None,
    fidelity_journal_path: str | None = None,
    fidelity_order_reports: Any = None,
    **alpaca_kwargs: Any,
) -> Any:
    """Construct the broker `config.live.broker` names.

    Imports each adapter lazily, inside its own branch. An Alpaca-only
    deployment must not need a browser automation stack installed, and a
    Fidelity-only one must not need alpaca-py -- the same reasoning that
    made `retry_policy.classify_error`'s alpaca import optional.

    `fidelity_order_reports` is the browser extension's confirmations,
    which the Fidelity adapter checks its own order readings against
    (fidelity_gateway/bridge/order_reports.py). Optional, and never a
    source of fills.
    """
    broker = getattr(config.live, "broker", "alpaca")
    if broker not in SUPPORTED_BROKERS:
        raise ConfigurationError(f"live.broker must be one of {SUPPORTED_BROKERS}, got {broker!r}")

    if broker == "alpaca":
        if credentials is None:
            raise ConfigurationError(
                "live.broker='alpaca' needs credentials. Load them with "
                "engine.core.secrets.load_live_credentials() and pass credentials=..."
            )
        from engine.brokers.alpaca_broker import AlpacaBroker

        # extended_hours comes from config rather than being left to a
        # caller's kwargs. It changes the SHAPE of every buy (share-sized
        # limit instead of notional market), so a deployment that means
        # to trade extended hours must say so in the file that describes
        # the deployment, not in whatever happened to construct it.
        alpaca_kwargs.setdefault("extended_hours", config.live.extended_hours)
        return AlpacaBroker(credentials, paper=config.live.paper_trading, **alpaca_kwargs)

    return _build_fidelity(config, fidelity_session, fidelity_journal_path, fidelity_order_reports)


def _build_fidelity(
    config, session: Any, journal_path: str | None = None, order_reports: Any = None
):
    settings = getattr(config.live, "fidelity", None)
    if settings is None:
        raise ConfigurationError(
            "live.broker='fidelity' requires a live.fidelity section naming "
            "allowed_accounts and the account to trade."
        )
    if not settings.dry_run and config.live.paper_trading:
        raise ConfigurationError(
            "live.fidelity.dry_run=false places REAL orders, but live.paper_trading is "
            "true. A Fidelity account has no paper mode; set paper_trading: false so the "
            "config says what it does."
        )
    if session is None:
        raise ConfigurationError(
            "live.broker='fidelity' needs an authenticated FidelitySession, not "
            "credentials. Fidelity refuses a Playwright-launched browser, so the "
            "session must come from a browser a human has logged into -- through the "
            "Fidelity Bridge extension (fidelity_gateway/bridge/) -- and be passed as "
            "fidelity_session=..."
        )
    if settings.account is None:
        raise ConfigurationError(
            "live.fidelity.account is not set. It must name the exact account "
            "to trade, and that account must also appear in allowed_accounts."
        )
    if settings.account_name is None:
        raise ConfigurationError(
            "live.fidelity.account_name is not set. Fidelity's order list "
            "(transactions/pending) refuses an account filter without the "
            "account's display name -- 400 'filter.accounts.0.acctName should not "
            "be empty' -- so the adapter could not read its own orders back. Set "
            "it to the name Fidelity shows for the account, e.g. 'Traditional IRA'."
        )

    # allowed_accounts is passed through unchanged; the adapter does the
    # exact-match check itself and re-checks on every call. Validating it
    # here as well would put the account rule in two places, which is how
    # they drift. The snapshot is scoped to the traded symbol: the account
    # may hold other investments, and reconciliation would otherwise
    # refuse to start over every one of them.
    common = {
        "symbol": config.backtest.symbol,
        "account_name": settings.account_name,
        "position_scope": (config.backtest.symbol,),
        "order_reports": order_reports,
    }

    if settings.dry_run:
        from fidelity_gateway.broker import FidelityBroker

        logger.warning(
            "Building the Fidelity adapter in PREVIEW-ONLY mode. It can price, "
            "enumerate and reconcile orders, and it cannot place one."
        )
        return FidelityBroker(session, settings.account, settings.allowed_accounts, **common)

    if not getattr(session, "allows_orders", False):
        raise ConfigurationError(
            "live.fidelity.dry_run=false, but the FidelitySession was built read-only or "
            "preview-only, so its transport would refuse every order. Build it with "
            "allow_order_endpoints=True -- the config and the transport must agree."
        )
    path = journal_path or settings.journal_path
    if not path:
        raise ConfigurationError(
            "Placing real orders needs a journal for each order's confirmation number, "
            "written before the order is committed. Set live.fidelity.journal_path or pass "
            "fidelity_journal_path=..."
        )

    from fidelity_gateway.placing_broker import FidelityPlacingBroker, FileConfNumJournal

    logger.warning(
        "Building the Fidelity adapter in LIVE mode: it PLACES REAL ORDERS in account "
        f"...{str(settings.account)[-4:]}, symbols {list(settings.allowed_symbols)}, "
        f"at most ${float(settings.max_order_value):,.2f} per buy."
    )
    # confirm_live_orders=True stands for live.fidelity.dry_run: false --
    # the deliberate, committed act this branch is reached by.
    return FidelityPlacingBroker(
        session,
        settings.account,
        settings.allowed_accounts,
        confirm_live_orders=True,
        allowed_symbols=settings.allowed_symbols,
        max_order_value=float(settings.max_order_value),
        journal=FileConfNumJournal(str(path)),
        **common,
    )
