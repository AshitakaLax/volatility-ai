"""
Broker dispatch. The place a misconfiguration turns into trading at the
wrong venue, so the tests are mostly about refusals.
"""

from __future__ import annotations

import re

import pytest

from src.broker_selection import build_broker
from src.config import BacktestConfig
from src.exceptions import ConfigurationError
from src.fidelity_broker import FidelityBroker
from src.secrets import LiveCredentials
from tests.unit.test_fidelity_broker import ACCOUNT, FakeSession

CREDS = LiveCredentials(api_key_id="PKTEST", api_secret_key="secret")


def _config(broker="alpaca", fidelity=None, paper=True):
    live = {
        "enabled": True,
        "paper_trading": paper,
        "step": 0.01,
        "profit_target": 0.005,
        "broker": broker,
    }
    if fidelity is not None:
        live["fidelity"] = fidelity
    return BacktestConfig.from_dict(
        {
            "strategy": {"strategy_id": "fixed", "strategy_params": {"allocation_pct": 0.05}},
            "grid": {"steps": [0.01], "profit_targets": [0.005]},
            "backtest": {"symbol": "TQQQ", "initial_cash": 100_000.0},
            "live": live,
        }
    )


FIDELITY_OK = {"allowed_accounts": [ACCOUNT], "account": ACCOUNT, "dry_run": True}


# --- venue selection ---------------------------------------------------


def test_the_default_is_still_alpaca():
    """Every config written before Fidelity existed keeps its meaning."""
    broker = build_broker(_config(), credentials=CREDS, client=object())
    assert type(broker).__name__ == "AlpacaBroker"


def test_fidelity_is_selected_when_named():
    broker = build_broker(
        _config("fidelity", FIDELITY_OK), fidelity_session=FakeSession()
    )
    assert isinstance(broker, FidelityBroker)


def test_an_unknown_venue_is_refused():
    config = _config()
    object.__setattr__(config.live, "broker", "etrade")
    with pytest.raises(ConfigurationError, match=re.escape("live.broker must be one of")):
        build_broker(config, credentials=CREDS)


# --- the two venues need different things ------------------------------


def test_alpaca_without_credentials_says_so():
    with pytest.raises(ConfigurationError, match="needs credentials"):
        build_broker(_config(), credentials=None)


def test_fidelity_without_a_session_says_credentials_are_not_enough():
    """The asymmetry that matters. There is no credential that produces a
    Fidelity session -- the browser must already be logged in by a human,
    because Fidelity refuses a Playwright-launched one."""
    with pytest.raises(ConfigurationError, match="authenticated FidelitySession"):
        build_broker(_config("fidelity", FIDELITY_OK), credentials=CREDS)


def test_fidelity_without_its_config_section_says_so():
    with pytest.raises(ConfigurationError, match=re.escape("live.fidelity section")):
        build_broker(_config("fidelity"), fidelity_session=FakeSession())


def test_fidelity_without_a_named_account_refuses():
    settings = dict(FIDELITY_OK, account=None)
    with pytest.raises(ConfigurationError, match="account is not set"):
        build_broker(_config("fidelity", settings), fidelity_session=FakeSession())


# --- dry_run=False is a hard failure -----------------------------------


def test_dry_run_false_refuses_to_start_rather_than_previewing_silently():
    """THE IMPORTANT ONE.

    The adapter is preview-only. A config claiming otherwise must fail
    loudly: an operator who believes orders are live while nothing
    trades is the worst outcome available, worse than not starting.
    """
    settings = dict(FIDELITY_OK, dry_run=False)
    with pytest.raises(ConfigurationError, match="PREVIEW-ONLY"):
        build_broker(_config("fidelity", settings), fidelity_session=FakeSession())


def test_dry_run_false_is_refused_before_a_session_is_even_required():
    """Checked ahead of the session check on purpose: 'you asked for
    something impossible' is more useful than 'you forgot a session',
    and fixing the second would still leave the first."""
    settings = dict(FIDELITY_OK, dry_run=False)
    with pytest.raises(ConfigurationError, match="PREVIEW-ONLY"):
        build_broker(_config("fidelity", settings), fidelity_session=None)


# --- the account rule lives in exactly one place -----------------------


def test_an_account_outside_the_allowlist_is_still_refused_through_this_path():
    settings = {"allowed_accounts": [ACCOUNT], "account": "999999999", "dry_run": True}
    with pytest.raises(ConfigurationError, match="allowed_accounts"):
        build_broker(_config("fidelity", settings), fidelity_session=FakeSession())


def test_the_symbol_comes_from_the_backtest_section():
    broker = build_broker(
        _config("fidelity", FIDELITY_OK), fidelity_session=FakeSession()
    )
    assert broker._symbol == "TQQQ"
