"""
Task 4.7 acceptance tests (A7).

1. Default call (rank_by="Capital Velocity Index", no ties, no error
   rows) reproduces the existing regression baseline exactly.
2. A results set containing one error row sorts without raising, with
   the error row at the bottom.
3. A nonexistent rank_by column raises a clear error, not a raw
   pandas KeyError.
"""

import pandas as pd
import pytest

from optimization_controller import OptimizationController
from src.exceptions import ConfigurationError
from src.market_context import MarketContext
from src.size_calculators import FixedPortfolioPercentage, SizingStrategy
from tests.fixtures.regression_baseline import BASELINE


def _load_fixture() -> pd.DataFrame:
    df = pd.read_csv("tests/fixtures/regression_ohlcv.csv", parse_dates=["timestamp"])
    df.set_index("timestamp", inplace=True)
    return df


def test_default_rank_by_reproduces_baseline_exactly():
    df = _load_fixture()
    row = OptimizationController(historical_data=df).run_sweep(
        grid_steps=[BASELINE["Grid Step"]],
        profit_targets=[BASELINE["Profit Target"]],
        strategy_class=FixedPortfolioPercentage,
        strategy_params_grid=[{"allocation_pct": BASELINE["allocation_pct"]}],
        # rank_by/tie_break_by both omitted -> defaults, must match exactly.
    ).iloc[0]
    for key, expected in BASELINE.items():
        assert row[key] == expected


class _ExplodingStrategy(SizingStrategy):
    def __init__(self, divisor: float):
        self.divisor = divisor

    def record_tick(self, context: MarketContext) -> None:
        pass

    def calculate_trade_value(self, context: MarketContext) -> float:
        return context.equity * 0.05 / self.divisor


def test_error_row_sorts_to_the_bottom_without_raising(caplog):
    df = _load_fixture()
    with caplog.at_level("WARNING", logger="Optimizer"):
        result = OptimizationController(historical_data=df).run_sweep(
            grid_steps=[0.01],
            profit_targets=[0.005],
            strategy_class=_ExplodingStrategy,
            strategy_params_grid=[{"divisor": 1.0}, {"divisor": 2.0}, {"divisor": 0.0}],
        )
    assert len(result) == 3
    assert pd.notna(result.iloc[-1].get("error"))  # error row is last
    assert pd.isna(result.iloc[0].get("error")) if "error" in result.columns else True
    assert pd.isna(result.iloc[1].get("error")) if "error" in result.columns else True
    assert any("excluded from ranking" in record.message for record in caplog.records)


def test_nonexistent_rank_by_raises_clear_error_not_keyerror():
    df = _load_fixture()
    with pytest.raises(ConfigurationError, match="rank_by column"):
        OptimizationController(historical_data=df).run_sweep(
            grid_steps=[0.01],
            profit_targets=[0.005],
            strategy_class=FixedPortfolioPercentage,
            strategy_params_grid=[{"allocation_pct": 0.05}],
            rank_by="Sharpe Ratio",  # doesn't exist
        )


def test_nonexistent_tie_break_by_raises_clear_error():
    df = _load_fixture()
    with pytest.raises(ConfigurationError, match="tie_break_by column"):
        OptimizationController(historical_data=df).run_sweep(
            grid_steps=[0.01],
            profit_targets=[0.005],
            strategy_class=FixedPortfolioPercentage,
            strategy_params_grid=[{"allocation_pct": 0.05}],
            tie_break_by="Sortino Ratio",  # doesn't exist
        )


def test_tie_break_by_produces_deterministic_secondary_ordering():
    df = _load_fixture()
    # Two combinations sharing the same allocation_pct (hence identical
    # Capital Velocity Index on this fixture, both harvest all 4 lots)
    # but different profit targets -- tie_break_by should order them
    # deterministically by that secondary column.
    result = OptimizationController(historical_data=df).run_sweep(
        grid_steps=[0.01],
        profit_targets=[0.005, 0.006],
        strategy_class=FixedPortfolioPercentage,
        strategy_params_grid=[{"allocation_pct": 0.05}],
        tie_break_by="Profit Target",
    )
    assert len(result) == 2
    # Both tied on Capital Velocity Index (1.0) -- tie_break_by
    # (descending, matching the primary sort direction) puts the
    # higher Profit Target first.
    if result.iloc[0]["Capital Velocity Index"] == result.iloc[1]["Capital Velocity Index"]:
        assert result.iloc[0]["Profit Target"] >= result.iloc[1]["Profit Target"]


def test_rank_by_and_full_results_stay_paired_with_error_rows_present():
    df = _load_fixture()
    summary_df, full_results = OptimizationController(historical_data=df).run_sweep(
        grid_steps=[0.01],
        profit_targets=[0.005],
        strategy_class=_ExplodingStrategy,
        strategy_params_grid=[{"divisor": 1.0}, {"divisor": 0.0}],
        return_full_results=True,
    )
    for i in range(len(summary_df)):
        row = summary_df.iloc[i]
        sim_result = full_results[i]
        if pd.notna(row.get("error")):
            assert sim_result is None
        else:
            assert sim_result is not None
