"""
Task 1.4 acceptance test (B2): calculate_trade_value must receive the
real current_dd computed that bar, not the 0.0 default silently used
forever.

Reuses tests/fixtures/drawdown_non_trigger_bar.csv (Task 1.2) since its
per-bar drawdown values were already independently verified there --
this test checks calculate_trade_value is called with exactly those
same values on trigger bars.
"""

from pathlib import Path

import pandas as pd
import pytest

from optimization_controller import OptimizationController
from src.market_context import MarketContext
from src.size_calculators import FixedPortfolioPercentage, SizingStrategy

FIXTURE_PATH = Path(__file__).resolve().parents[1] / "fixtures" / "drawdown_non_trigger_bar.csv"
GRID_STEP = 0.01
PROFIT_TARGET = 0.10
ALLOCATION_PCT = 0.05


class DrawdownCapturingStrategy(SizingStrategy):
    """Test double: real FixedPortfolioPercentage math, plus records the
    context.drawdown value received on every calculate_trade_value call."""

    def __init__(self, allocation_pct: float):
        self._inner = FixedPortfolioPercentage(allocation_pct=allocation_pct)
        self.dd_values_seen: list[float] = []

    def record_tick(self, context: MarketContext) -> None:
        self._inner.record_tick(context)

    def calculate_trade_value(self, context: MarketContext) -> float:
        self.dd_values_seen.append(context.drawdown)
        return self._inner.calculate_trade_value(context)


def _load_fixture() -> pd.DataFrame:
    df = pd.read_csv(FIXTURE_PATH, parse_dates=["timestamp"])
    df.set_index("timestamp", inplace=True)
    return df


def test_calculate_trade_value_receives_real_drawdown_not_default_zero():
    df = _load_fixture()
    created: list[DrawdownCapturingStrategy] = []

    class _CapturingFactory:
        def __call__(self, **params):
            instance = DrawdownCapturingStrategy(**params)
            created.append(instance)
            return instance

    controller = OptimizationController(historical_data=df)
    controller.run_sweep(
        grid_steps=[GRID_STEP],
        profit_targets=[PROFIT_TARGET],
        strategy_class=_CapturingFactory(),
        strategy_params_grid=[{"allocation_pct": ALLOCATION_PCT}],
    )

    strategy = created[0]
    # Bars 1 (98.00) and 2 (95.00) are the two trigger bars in this fixture.
    assert len(strategy.dd_values_seen) == 2, "Expected exactly 2 trigger bars in this fixture"

    # Bar 1: first-ever trigger, measured before any lot is open -> 0 drawdown.
    assert strategy.dd_values_seen[0] == pytest.approx(0.0, abs=1e-9)
    # Bar 2: real drawdown after bar 1's buy, verified independently in
    # Task 1.2's test (0.1531% in the "buggy, trigger-only" reference,
    # which is exactly correct for bar 2 itself since bar 2 IS a trigger
    # bar -- the bug was only ever about *later* non-trigger bars).
    assert strategy.dd_values_seen[1] == pytest.approx(0.0015306122448979295, abs=1e-9)

    # Not the old, silently-defaulted behavior.
    assert not all(dd == 0.0 for dd in strategy.dd_values_seen), (
        "current_dd is still always 0.0 -- looks like the default is being "
        "used instead of the real computed drawdown (bug B2)."
    )


def test_fixed_portfolio_percentage_output_unaffected_by_drawdown_threading():
    # FixedPortfolioPercentage ignores current_dd entirely -- Task 0.1's
    # baseline must still hold exactly, confirming this change is a
    # true no-op for strategies that don't use it.
    df = pd.read_csv(
        Path(__file__).resolve().parents[1] / "fixtures" / "regression_ohlcv.csv",
        parse_dates=["timestamp"],
    )
    df.set_index("timestamp", inplace=True)
    controller = OptimizationController(historical_data=df)
    result = controller.run_sweep(
        grid_steps=[0.01],
        profit_targets=[0.005],
        strategy_class=FixedPortfolioPercentage,
        strategy_params_grid=[{"allocation_pct": 0.05}],
    )
    assert result.iloc[0]["Final Equity"] == 100099.81489816227
