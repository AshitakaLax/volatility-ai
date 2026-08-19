"""
Task 1.3 acceptance test (B4): sizing_engine.record_tick(current_price)
must be called exactly once per bar of historical data, unconditionally
-- not only on bars that also trigger a grid buy.

Reuses tests/fixtures/regression_ohlcv.csv (35 bars, only 4 of which
trigger a grid buy at grid_step=0.01) specifically because most bars
are non-trigger bars -- record_tick firing only on the 4 trigger bars
would be immediately visible against firing on all 35.
"""

from pathlib import Path

import pandas as pd

from optimization_controller import OptimizationController
from src.market_context import MarketContext
from src.size_calculators import FixedPortfolioPercentage, SizingStrategy

FIXTURE_PATH = Path(__file__).resolve().parents[1] / "fixtures" / "regression_ohlcv.csv"


class RecordTickCountingStrategy(SizingStrategy):
    """Test double only -- wraps a real FixedPortfolioPercentage for its
    actual sizing math, and additionally counts record_tick calls and
    the context passed each time. Not a production sizing strategy."""

    def __init__(self, allocation_pct: float):
        self._inner = FixedPortfolioPercentage(allocation_pct=allocation_pct)
        self.record_tick_contexts: list[MarketContext] = []

    def record_tick(self, context: MarketContext) -> None:
        self.record_tick_contexts.append(context)

    def calculate_trade_value(self, context: MarketContext) -> float:
        return self._inner.calculate_trade_value(context)


def _load_fixture() -> pd.DataFrame:
    df = pd.read_csv(FIXTURE_PATH, parse_dates=["timestamp"])
    df.set_index("timestamp", inplace=True)
    return df


def test_record_tick_called_exactly_once_per_bar_including_non_trigger_bars():
    df = _load_fixture()
    n_bars = len(df)

    # Instantiated indirectly through strategy_class(**params) inside
    # run_sweep -- capture the instance via a params dict trick isn't
    # possible (run_sweep constructs it internally), so instead assert
    # the invariant using a strategy_class wrapper that stashes the
    # instance it creates onto a shared list.
    created: list[RecordTickCountingStrategy] = []

    class _CapturingFactory:
        def __call__(self, **params):
            instance = RecordTickCountingStrategy(**params)
            created.append(instance)
            return instance

    controller = OptimizationController(historical_data=df)
    controller.run_sweep(
        grid_steps=[0.01],
        profit_targets=[0.005],
        strategy_class=_CapturingFactory(),
        strategy_params_grid=[{"allocation_pct": 0.05}],
    )

    assert len(created) == 1, (
        "Expected exactly one sweep combination to instantiate exactly one strategy"
    )
    strategy = created[0]

    assert len(strategy.record_tick_contexts) == n_bars, (
        f"record_tick was called {len(strategy.record_tick_contexts)} times, expected exactly "
        f"{n_bars} (once per bar) -- it should fire unconditionally, not only on trigger bars."
    )
    # The prices passed must be the actual per-bar close prices, in order,
    # and bar_index must be sequential.
    assert [c.close for c in strategy.record_tick_contexts] == list(df["close"])
    assert [c.bar_index for c in strategy.record_tick_contexts] == list(range(n_bars))


def test_calculate_trade_value_behavior_unchanged_for_strategies_ignoring_record_tick():
    # FixedPortfolioPercentage doesn't use record_tick's data at all --
    # Task 0.1's baseline (captured before this fix) already proves its
    # output is unaffected; this just re-confirms that guarantee here.
    df = _load_fixture()
    controller = OptimizationController(historical_data=df)
    result = controller.run_sweep(
        grid_steps=[0.01],
        profit_targets=[0.005],
        strategy_class=FixedPortfolioPercentage,
        strategy_params_grid=[{"allocation_pct": 0.05}],
    )
    assert result.iloc[0]["Final Equity"] == 100099.81489816227
