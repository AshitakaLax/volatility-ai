"""LiveExecutionLoop actually drives AlpacaBroker through the protocol.

The unit tests exercise the adapter directly. These assert the thing
that made the adapter worth writing: that the loop, which is coded
against src.live_execution.LiveBroker and knows nothing about Alpaca,
really does reach alpaca-py request objects through it. A protocol
satisfied only in theory would pass every unit test here and still
fail at the first live tick.
"""

from __future__ import annotations

import pytest

from src.alpaca_broker import AlpacaBroker, alpaca_broker_factory
from src.config import BacktestConfig
from src.live_execution import LiveExecutionLoop
from src.retry_policy import RetryConfig
from src.size_calculators import FixedPortfolioPercentage
from tests.unit.test_alpaca_broker import FakeClient

FAST_RETRY = RetryConfig(base_delay=0.001, max_attempts=2)


@pytest.fixture
def credentials_in_env(monkeypatch):
    """LiveExecutionLoop.start() loads credentials itself before it will
    build a broker, so the env has to be populated for the wiring to be
    exercised at all."""
    monkeypatch.setenv("APCA_API_KEY_ID", "PKTEST")
    monkeypatch.setenv("APCA_API_SECRET_KEY", "secret")


def build_config(paper=True):
    return BacktestConfig.from_dict(
        {
            "strategy": {"strategy_id": "fixed", "strategy_params": {"allocation_pct": 0.05}},
            "grid": {"steps": [0.01], "profit_targets": [0.005]},
            "backtest": {"symbol": "TQQQ", "initial_cash": 100_000.0},
            "live": {"enabled": True, "paper_trading": paper},
        }
    )


def build_loop(client, credentials_in_env, paper=True, live_capital_promotion=None):
    loop = LiveExecutionLoop(
        config=build_config(paper),
        strategy=FixedPortfolioPercentage(allocation_pct=0.05),
        broker_factory=alpaca_broker_factory(paper=paper, client=client, retry_config=FAST_RETRY),
        live_capital_promotion=live_capital_promotion,
    )
    loop.start()
    return loop


def test_start_builds_an_alpaca_broker_through_the_factory(credentials_in_env):
    loop = build_loop(FakeClient(), credentials_in_env)
    assert isinstance(loop.broker, AlpacaBroker)


def test_loop_submit_buy_reaches_a_notional_alpaca_request(credentials_in_env):
    """The full path: LiveDecision -> loop -> protocol -> adapter ->
    alpaca-py request object."""
    from src.live_execution import LiveDecision

    client = FakeClient()
    loop = build_loop(client, credentials_in_env)
    decision = LiveDecision(
        context=None, triggered=True, proposed_trade_value=500.0, clamped_trade_value=250.0
    )

    loop.submit_buy(decision)

    (request,) = client.submitted
    assert request.symbol == "TQQQ", "the loop supplies the symbol from config"
    assert request.notional == 250.0, "the RISK-CLAMPED value must be what reaches the broker"
    assert request.side.value == "buy"


def test_loop_submits_the_clamped_value_not_the_strategy_proposal(credentials_in_env):
    """A risk clamp that the adapter ignored would be no clamp at all."""
    from src.live_execution import LiveDecision

    client = FakeClient()
    loop = build_loop(client, credentials_in_env)
    loop.submit_buy(
        LiveDecision(
            context=None,
            triggered=True,
            proposed_trade_value=10_000.0,
            clamped_trade_value=100.0,
        )
    )
    (request,) = client.submitted
    assert request.notional == 100.0
    assert request.notional != 10_000.0


def test_a_fully_clamped_decision_never_contacts_the_broker(credentials_in_env):
    """Zero clamped value must end quietly, not as a rejected order."""
    from src.live_execution import LiveDecision

    client = FakeClient()
    loop = build_loop(client, credentials_in_env)
    result = loop.submit_buy(
        LiveDecision(
            context=None, triggered=False, proposed_trade_value=500.0, clamped_trade_value=0.0
        )
    )
    assert result is None
    assert client.submitted == [], "a suppressed decision must not reach the broker at all"


def test_loop_submit_sell_reaches_a_limit_alpaca_request(credentials_in_env):
    """The harvest path must arrive at the venue as a LIMIT order, or
    the no-loss guard's decision is lost between here and the fill."""
    client = FakeClient()
    loop = build_loop(client, credentials_in_env)

    loop.submit_sell(qty=2.5, target_price=101.004)

    (request,) = client.submitted
    assert request.type.value == "limit"
    assert request.qty == 2.5
    assert request.limit_price == 101.01
    assert request.side.value == "sell"


def test_paper_config_produces_a_paper_broker(credentials_in_env):
    """config.live.paper_trading is what decides real capital, so it has
    to survive all the way to the adapter's endpoint routing."""
    assert build_loop(FakeClient(), credentials_in_env, paper=True).broker.paper is True


def test_a_live_config_without_promotion_evidence_is_refused(credentials_in_env):
    """The adapter does not weaken the Task 7.7 gate.

    Having a working broker adapter is exactly the moment that gate
    starts to matter: before this module existed, nothing could have
    reached real capital anyway. Asserted here so a future change that
    routes around the gate fails loudly.
    """
    from src.exceptions import ConfigurationError

    with pytest.raises(ConfigurationError, match="promotion"):
        build_loop(FakeClient(), credentials_in_env, paper=False)


def test_a_live_config_with_passing_promotion_evidence_reaches_the_live_endpoint(
    credentials_in_env,
):
    """The other half: with real evidence, paper=False must actually
    route to the real-capital endpoint rather than silently staying on
    paper."""
    from src.promotion import PromotionEvaluation

    promotion = PromotionEvaluation(passed=True, failures=(), criteria={}, record={})
    loop = build_loop(
        FakeClient(), credentials_in_env, paper=False, live_capital_promotion=promotion
    )
    assert loop.broker.paper is False
