"""
Task 4.4 acceptance tests (A5).

1. A fixture that deliberately makes one parameter combination raise
   still returns a DataFrame with all other combinations' results
   intact, plus one row carrying an error value.
2. Regression fixture (no failing combinations) output is unchanged.
"""

import pandas as pd

from optimization_controller import OptimizationController
from src.market_context import MarketContext
from src.size_calculators import FixedPortfolioPercentage, SizingStrategy
from tests.fixtures.regression_baseline import BASELINE


def _load_fixture() -> pd.DataFrame:
    df = pd.read_csv("tests/fixtures/regression_ohlcv.csv", parse_dates=["timestamp"])
    df.set_index("timestamp", inplace=True)
    return df


class ExplodesOnZeroDivisorStrategy(SizingStrategy):
    """Test double: raises ZeroDivisionError inside calculate_trade_value
    when constructed with divisor=0, otherwise behaves like
    FixedPortfolioPercentage. Simulates 'an edge case in one strategy'
    from this task's own context."""

    def __init__(self, allocation_pct: float, divisor: float):
        self.allocation_pct = allocation_pct
        self.divisor = divisor

    def record_tick(self, context: MarketContext) -> None:
        pass

    def calculate_trade_value(self, context: MarketContext) -> float:
        return (context.equity * self.allocation_pct) / self.divisor  # raises if divisor == 0


def test_one_bad_combination_does_not_abort_the_others():
    df = _load_fixture()
    controller = OptimizationController(historical_data=df)

    result = controller.run_sweep(
        grid_steps=[0.01],
        profit_targets=[0.005],
        strategy_class=ExplodesOnZeroDivisorStrategy,
        strategy_params_grid=[
            {"allocation_pct": 0.05, "divisor": 1.0},  # succeeds
            {"allocation_pct": 0.05, "divisor": 0.0},  # raises ZeroDivisionError
            {"allocation_pct": 0.03, "divisor": 2.0},  # succeeds
        ],
    )

    assert len(result) == 3, "All 3 combinations must produce a row, including the failing one"
    assert "error" in result.columns
    error_rows = result[result["error"].notna()]
    assert len(error_rows) == 1
    assert (
        "division" in str(error_rows.iloc[0]["error"]).lower()
        or "divisor" in str(error_rows.iloc[0]["error"]).lower()
    )

    success_rows = result[result["error"].isna()]
    assert len(success_rows) == 2
    # Successful rows must have real metrics, not be contaminated by the failure.
    assert success_rows["Final Equity"].notna().all()
    assert success_rows["Trade Count"].notna().all()


def test_sorting_does_not_crash_with_an_error_row_present():
    df = _load_fixture()
    controller = OptimizationController(historical_data=df)
    # Must not raise -- pd.DataFrame + sort_values with a heterogeneous
    # error row mixed into otherwise-metric rows.
    result = controller.run_sweep(
        grid_steps=[0.01],
        profit_targets=[0.005],
        strategy_class=ExplodesOnZeroDivisorStrategy,
        strategy_params_grid=[
            {"allocation_pct": 0.05, "divisor": 1.0},
            {"allocation_pct": 0.05, "divisor": 0.0},
        ],
    )
    assert len(result) == 2


def test_regression_fixture_with_no_failures_unchanged():
    df = _load_fixture()
    result = (
        OptimizationController(historical_data=df)
        .run_sweep(
            grid_steps=[BASELINE["Grid Step"]],
            profit_targets=[BASELINE["Profit Target"]],
            strategy_class=FixedPortfolioPercentage,
            strategy_params_grid=[{"allocation_pct": BASELINE["allocation_pct"]}],
        )
        .iloc[0]
    )
    for key, expected in BASELINE.items():
        assert result[key] == expected
    assert "error" not in result or pd.isna(result.get("error"))
