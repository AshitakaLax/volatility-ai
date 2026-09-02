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
dry_run=False IS A HARD FAILURE, NOT A NO-OP

`src/fidelity_broker.py` is preview-only by construction: it holds no
place-order capability and the transport refuses one. A config setting
`live.fidelity.dry_run = false` is therefore asking for something this
code cannot do.

Silently previewing anyway would be the worst outcome available -- the
operator believes orders are being placed, the strategy believes its
sells are resting, and the divergence is only discovered by looking at
an account that never traded. So it raises. When a real placing adapter
exists this check is what must be deliberately revisited, which is the
point of putting it here rather than leaving the flag unread.
"""

from __future__ import annotations

import logging
from typing import Any

from src.exceptions import ConfigurationError

logger = logging.getLogger("Optimizer")

SUPPORTED_BROKERS = ("alpaca", "fidelity")


def build_broker(
    config,
    *,
    credentials: Any = None,
    fidelity_session: Any = None,
    **alpaca_kwargs: Any,
) -> Any:
    """Construct the broker `config.live.broker` names.

    Imports each adapter lazily, inside its own branch. An Alpaca-only
    deployment must not need a browser automation stack installed, and a
    Fidelity-only one must not need alpaca-py -- the same reasoning that
    made `retry_policy.classify_error`'s alpaca import optional.
    """
    broker = getattr(config.live, "broker", "alpaca")
    if broker not in SUPPORTED_BROKERS:
        raise ConfigurationError(
            f"live.broker must be one of {SUPPORTED_BROKERS}, got {broker!r}"
        )

    if broker == "alpaca":
        if credentials is None:
            raise ConfigurationError(
                "live.broker='alpaca' needs credentials. Load them with "
                "src.secrets.load_live_credentials() and pass credentials=..."
            )
        from src.alpaca_broker import AlpacaBroker

        return AlpacaBroker(
            credentials, paper=config.live.paper_trading, **alpaca_kwargs
        )

    return _build_fidelity(config, fidelity_session)


def _build_fidelity(config, session: Any):
    settings = getattr(config.live, "fidelity", None)
    if settings is None:
        raise ConfigurationError(
            "live.broker='fidelity' requires a live.fidelity section naming "
            "allowed_accounts and the account to trade."
        )
    if not settings.dry_run:
        raise ConfigurationError(
            "live.fidelity.dry_run=false, but src/fidelity_broker.py is "
            "PREVIEW-ONLY: it holds no place-order capability and the transport "
            "refuses one. Refusing to start rather than previewing while the "
            "config says orders are being placed -- an operator who believes "
            "orders are live while nothing trades is the worst available "
            "outcome. Set dry_run=true, or build a placing adapter first."
        )
    if session is None:
        raise ConfigurationError(
            "live.broker='fidelity' needs an authenticated FidelitySession, not "
            "credentials. Fidelity refuses a Playwright-launched browser, so the "
            "session must come from a browser a human has logged into -- attach "
            "over CDP (see fidelity_recon.py --cdp-url) and pass "
            "fidelity_session=..."
        )
    if settings.account is None:
        raise ConfigurationError(
            "live.fidelity.account is not set. It must name the exact account "
            "to trade, and that account must also appear in allowed_accounts."
        )

    from src.fidelity_broker import FidelityBroker

    logger.warning(
        "Building the Fidelity adapter in PREVIEW-ONLY mode. It can price, "
        "enumerate and reconcile orders, and it cannot place one."
    )
    # allowed_accounts is passed through unchanged; FidelityBroker does the
    # exact-match check itself and re-checks on every call. Validating it
    # here as well would put the account rule in two places, which is how
    # they drift.
    return FidelityBroker(
        session,
        settings.account,
        settings.allowed_accounts,
        symbol=config.backtest.symbol,
    )
