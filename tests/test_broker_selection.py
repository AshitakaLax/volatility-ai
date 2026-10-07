"""
Broker dispatch. The place a misconfiguration turns into trading at the
wrong venue, so the tests are mostly about refusals.
"""

from __future__ import annotations

import re

import pytest

from engine.brokers.broker_selection import build_broker
from engine.core.config import BacktestConfig
from engine.core.exceptions import ConfigurationError
from engine.core.secrets import LiveCredentials
from fidelity_gateway.broker import FidelityBroker
from fidelity_gateway.placing_broker import FidelityPlacingBroker
from fidelity_gateway.tests.test_fidelity_broker import ACCOUNT, FakeSession

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


FIDELITY_OK = {
    "allowed_accounts": [ACCOUNT],
    "account": ACCOUNT,
    "account_name": "Traditional IRA",
    "dry_run": True,
}
PENDING = "/ftgw/digital/activityapi/api/v1/transactions/pending"


# --- venue selection ---------------------------------------------------


def test_the_default_is_still_alpaca():
    """Every config written before Fidelity existed keeps its meaning."""
    broker = build_broker(_config(), credentials=CREDS, client=object())
    assert type(broker).__name__ == "AlpacaBroker"


def test_fidelity_is_selected_when_named():
    broker = build_broker(_config("fidelity", FIDELITY_OK), fidelity_session=FakeSession())
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


def test_fidelity_without_an_account_name_refuses():
    """transactions/pending answers 400 "filter.accounts.0.acctName should
    not be empty" without it, so a broker built without one could preview
    orders and then never read them back."""
    settings = dict(FIDELITY_OK, account_name=None)
    with pytest.raises(ConfigurationError, match="account_name is not set"):
        build_broker(_config("fidelity", settings), fidelity_session=FakeSession())


def test_the_account_name_reaches_the_order_list_filter():
    session = FakeSession({PENDING: {"data": {"orders": []}}})
    broker = build_broker(_config("fidelity", FIDELITY_OK), fidelity_session=session)
    broker._orders()
    payload = next(p for path, p in session.calls if path == PENDING)
    assert payload["filter"]["accounts"][0]["acctName"] == "Traditional IRA"


# --- dry_run decides the adapter, and nothing falls back -----------------

FIDELITY_LIVE = dict(FIDELITY_OK, dry_run=False, allowed_symbols=["TQQQ"], max_order_value=500.0)


class OrderSession(FakeSession):
    """A session built to allow order endpoints, as connect_live builds it."""

    allows_orders = True


def test_dry_run_true_builds_the_preview_only_adapter():
    broker = build_broker(_config("fidelity", FIDELITY_OK), fidelity_session=FakeSession())
    assert isinstance(broker, FidelityBroker)
    assert not isinstance(broker, FidelityPlacingBroker)


def test_dry_run_false_builds_the_placing_adapter(tmp_path):
    journal = tmp_path / "orders.jsonl"
    broker = build_broker(
        _config("fidelity", FIDELITY_LIVE, paper=False),
        fidelity_session=OrderSession(),
        fidelity_journal_path=str(journal),
    )
    assert isinstance(broker, FidelityPlacingBroker)
    assert broker._allowed_symbols == ("TQQQ",)
    assert broker._max_order_value == 500.0
    assert broker._journal._path == str(journal)


def test_the_extensions_order_reports_reach_either_adapter(tmp_path):
    """The browser extension's confirmations: something the adapter checks
    its own readings against, handed through unchanged."""
    reports = object()
    preview = build_broker(
        _config("fidelity", FIDELITY_OK),
        fidelity_session=FakeSession(),
        fidelity_order_reports=reports,
    )
    live = build_broker(
        _config("fidelity", FIDELITY_LIVE, paper=False),
        fidelity_session=OrderSession(),
        fidelity_journal_path=str(tmp_path / "orders.jsonl"),
        fidelity_order_reports=reports,
    )
    assert preview._order_reports is reports
    assert live._order_reports is reports
    assert (
        build_broker(
            _config("fidelity", FIDELITY_OK), fidelity_session=FakeSession()
        )._order_reports
        is None
    )


def test_the_config_journal_path_is_used_when_none_is_passed(tmp_path):
    settings = dict(FIDELITY_LIVE, journal_path=str(tmp_path / "from-config.jsonl"))
    broker = build_broker(
        _config("fidelity", settings, paper=False), fidelity_session=OrderSession()
    )
    assert broker._journal._path.endswith("from-config.jsonl")


def test_real_orders_with_paper_trading_on_are_refused(tmp_path):
    """A Fidelity account has no paper mode. A file that says paper while
    placing real orders is a contradiction to stop on, not to resolve."""
    with pytest.raises(ConfigurationError, match="no paper mode"):
        build_broker(
            _config("fidelity", FIDELITY_LIVE, paper=True),
            fidelity_session=OrderSession(),
            fidelity_journal_path=str(tmp_path / "j.jsonl"),
        )


def test_real_orders_over_a_session_that_cannot_place_are_refused(tmp_path):
    """Silently previewing while the config says orders are placed is the
    worst outcome available -- so the session must agree with the file."""
    with pytest.raises(ConfigurationError, match="transport would refuse every order"):
        build_broker(
            _config("fidelity", FIDELITY_LIVE, paper=False),
            fidelity_session=FakeSession(),
            fidelity_journal_path=str(tmp_path / "j.jsonl"),
        )


def test_real_orders_need_a_journal():
    with pytest.raises(ConfigurationError, match="journal"):
        build_broker(
            _config("fidelity", FIDELITY_LIVE, paper=False), fidelity_session=OrderSession()
        )


def test_the_snapshot_is_scoped_to_the_traded_symbol():
    """A shared account's other holdings must not stop the loop starting,
    and its other orders must not either."""
    session = FakeSession(
        {
            PENDING: {
                "data": {
                    "orders": [
                        {
                            "orderNum": "A1",
                            "acctNum": ACCOUNT,
                            "symbol": "TQQQ",
                            "cancelableInd": True,
                        },
                        {
                            "orderNum": "B2",
                            "acctNum": ACCOUNT,
                            "symbol": "VTI",
                            "cancelableInd": True,
                        },
                    ]
                }
            },
            "/ftgw/digital/trade-equity/positions": [
                {"symbol": "TQQQ", "quantity": 3.0},
                {"symbol": "VTI", "quantity": 40.0},
            ],
            "/ftgw/digital/trade-equity/balance": {},
        }
    )
    snapshot = build_broker(_config("fidelity", FIDELITY_OK), fidelity_session=session).snapshot()
    assert snapshot.positions == {"TQQQ": 3.0}
    assert set(snapshot.orders) == {"A1"}


# --- the account rule lives in exactly one place -----------------------


def test_an_account_outside_the_allowlist_is_still_refused_through_this_path():
    settings = dict(FIDELITY_OK, account="999999999")
    with pytest.raises(ConfigurationError, match="allowed_accounts"):
        build_broker(_config("fidelity", settings), fidelity_session=FakeSession())


def test_the_symbol_comes_from_the_backtest_section():
    broker = build_broker(_config("fidelity", FIDELITY_OK), fidelity_session=FakeSession())
    assert broker._symbol == "TQQQ"
