from datetime import UTC, datetime

import pytest

from src.config import BacktestConfig
from src.exceptions import ConfigurationError
from src.live_execution import LiveExecutionLoop
from src.size_calculators import FixedPortfolioPercentage


def live_config():
    return BacktestConfig.from_dict(
        {
            "strategy": {"strategy_id": "fixed", "strategy_params": {"percentage": 0.1}},
            "backtest": {"symbol": "TQQQ", "initial_cash": 100000.0},
            "grid": {"steps": [0.01], "profit_targets": [0.02]},
            "live": {"enabled": True, "paper_trading": True},
        }
    )


def test_live_loop_uses_market_context_and_same_strategy_sequence(monkeypatch):
    monkeypatch.setenv("APCA_API_KEY_ID", "key")
    monkeypatch.setenv("APCA_API_SECRET_KEY", "secret")
    strategy = FixedPortfolioPercentage(percentage=0.1)
    loop = LiveExecutionLoop(live_config(), strategy, broker_factory=lambda credentials: object())
    loop.start()
    context = loop.build_context(
        timestamp=datetime(2025, 1, 1, tzinfo=UTC),
        open=99,
        high=100,
        low=98,
        close=99,
        cash=100000,
        equity=100000,
        peak_equity=100000,
        drawdown=0,
        open_lot_count=0,
        bar_index=0,
    )
    decision = loop.decision_cycle(context, step=0.01, last_buy_price=100)
    assert decision.triggered
    assert decision.proposed_trade_value == pytest.approx(10000)
    assert decision.clamped_trade_value == pytest.approx(10000)


def test_missing_credentials_fails_before_broker_factory(monkeypatch):
    monkeypatch.delenv("APCA_API_KEY_ID", raising=False)
    monkeypatch.delenv("APCA_API_SECRET_KEY", raising=False)
    called = False

    def factory(_credentials):
        nonlocal called
        called = True
        return object()

    loop = LiveExecutionLoop(
        live_config(), FixedPortfolioPercentage(percentage=0.1), broker_factory=factory
    )
    with pytest.raises(ConfigurationError):
        loop.start()
    assert not called


def test_live_config_can_supply_parameters_without_code_changes(monkeypatch):
    monkeypatch.setenv("APCA_API_KEY_ID", "key")
    monkeypatch.setenv("APCA_API_SECRET_KEY", "secret")
    config = live_config()
    strategy = FixedPortfolioPercentage(**config.strategy.strategy_params)
    loop = LiveExecutionLoop(config, strategy, broker_factory=lambda credentials: object())
    loop.start()
    assert loop.config.backtest.symbol == "TQQQ"
    assert config.grid.steps == (0.01,)
