from dataclasses import FrozenInstanceError

import pandas as pd

from optimization_controller import OptimizationController
from src.market_context import MarketContext, SimulationResult
from src.size_calculators import FixedPortfolioPercentage, SizingStrategy


class ContextRecordingStrategy(SizingStrategy):
    def __init__(self):
        self.contexts = []

    def record_tick(self, context: MarketContext) -> None:
        self.contexts.append(context)

    def calculate_trade_value(self, context: MarketContext) -> float:
        return 0.0


def make_ohlcv():
    index = pd.date_range("2024-01-01", periods=5, freq="D")
    return pd.DataFrame(
        {
            "open": [100, 99, 98, 101, 100],
            "high": [101, 100, 99, 102, 101],
            "low": [99, 98, 97, 100, 99],
            "close": [100, 99, 98, 101, 100],
            "volume": [1000, 1100, 1200, 1300, 1400],
        },
        index=index,
    )


def test_market_context_is_frozen_and_exposes_close_as_price():
    context = MarketContext(pd.Timestamp("2024-01-01").to_pydatetime(), 1, 2, 0, 1.5, 100, 100, 100, 0, 0, 0)
    assert context.price == 1.5
    try:
        context.close = 2.0
    except FrozenInstanceError:
        pass
    else:
        raise AssertionError("MarketContext must be immutable")


def test_simulate_single_returns_canonical_result_and_context_per_bar():
    controller = OptimizationController(make_ohlcv())
    strategy = ContextRecordingStrategy()
    result = controller._simulate_single(
        0.01, 0.01, strategy, "TQQQ", 100_000.0,
        __import__("src.cost_models", fromlist=["ZeroCostModel"]).ZeroCostModel(),
        __import__("src.risk_manager", fromlist=["RiskManager"]).RiskManager(),
    )
    assert isinstance(result, SimulationResult)
    assert set(result.metrics)
    assert len(strategy.contexts) == len(controller.data)
    assert all(isinstance(context, MarketContext) for context in strategy.contexts)
    assert [context.bar_index for context in strategy.contexts] == list(range(5))


def test_run_sweep_uses_extracted_single_simulation():
    controller = OptimizationController(make_ohlcv())
    result = controller.run_sweep(
        [0.01], [0.01], FixedPortfolioPercentage, [{"percentage": 0.01}]
    )
    assert len(result) == 1
    assert "Final Portfolio Value" in result.columns
    assert "Max Drawdown %" in result.columns
