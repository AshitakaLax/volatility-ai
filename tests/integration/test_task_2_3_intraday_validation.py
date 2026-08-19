"""
Task 2.3 acceptance tests (F2).

Acceptance criteria:
1. Given a fixture where a sell target is known to be touched
   intrabar and reversed by close, the intraday pass records that
   sell while a daily-close-only run does not.
2. Default run_sweep behavior (daily-close screening) is unaffected
   -- strictly additive/opt-in.

Fixture construction (verified numerically in the chat this test was
produced in before being written here): a 1% grid step, 6% profit
target, and allocation_pct=0.05 throughout.

- Daily dataset: 3 daily closes (100.0, 95.0, 99.5). Bar 2 (95.0)
  triggers a buy at close=95 (daily fill convention); target becomes
  95 * 1.06 = 100.70. Bar 3's close (99.5) never reaches that, so the
  lot stays open through the whole daily run.
- Intraday dataset: 3 minute bars covering the same reality at finer
  granularity. Bar 2's low (94.5) touches the post-bar-1 trigger level
  (100 * 0.99 = 99), filling at that limit price -- target becomes
  99 * 1.06 = 104.94. Bar 3 spikes to a high of 106.0 (touching that
  target) before closing at 99.5 -- reversed by close, exactly as the
  daily pass would show, except the intraday pass catches the
  intrabar touch via high. Bar 3's low (98.5) is kept above the
  post-bar-2 trigger level (99 * 0.99 = 98.01) so no second buy fires,
  isolating a single-lot scenario.
"""

from pathlib import Path

import pandas as pd
import pytest

from optimization_controller import OptimizationController
from src import intraday_validation
from src.intraday_validation import IntradayValidationError, simulate_single_intraday
from src.size_calculators import FixedPortfolioPercentage

GRID_STEP = 0.01
PROFIT_TARGET = 0.06
ALLOCATION_PCT = 0.05

DAILY_ROWS = [
    {
        "timestamp": "2024-01-02T00:00:00+00:00",
        "open": 100.0,
        "high": 100.1,
        "low": 99.9,
        "close": 100.0,
        "volume": 1_000_000,
    },
    {
        "timestamp": "2024-01-03T00:00:00+00:00",
        "open": 100.0,
        "high": 100.1,
        "low": 94.905,
        "close": 95.0,
        "volume": 1_000_000,
    },
    {
        "timestamp": "2024-01-04T00:00:00+00:00",
        "open": 95.0,
        "high": 99.5995,
        "low": 94.905,
        "close": 99.5,
        "volume": 1_000_000,
    },
]
INTRADAY_ROWS = [
    {
        "timestamp": "2024-01-02T00:00:00+00:00",
        "open": 100.0,
        "high": 100.0,
        "low": 100.0,
        "close": 100.0,
        "volume": 100_000,
    },
    {
        "timestamp": "2024-01-02T00:01:00+00:00",
        "open": 100.0,
        "high": 100.2,
        "low": 94.5,
        "close": 95.0,
        "volume": 100_000,
    },
    {
        "timestamp": "2024-01-02T00:02:00+00:00",
        "open": 95.0,
        "high": 106.0,
        "low": 98.5,
        "close": 99.5,
        "volume": 100_000,
    },
]


def _to_df(rows):
    df = pd.DataFrame(rows)
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df.set_index("timestamp", inplace=True)
    return df


def test_intraday_pass_catches_reversal_daily_close_only_misses():
    daily_df = _to_df(DAILY_ROWS)
    daily_result = (
        OptimizationController(historical_data=daily_df)
        .run_sweep(
            grid_steps=[GRID_STEP],
            profit_targets=[PROFIT_TARGET],
            strategy_class=FixedPortfolioPercentage,
            strategy_params_grid=[{"allocation_pct": ALLOCATION_PCT}],
        )
        .iloc[0]
    )
    assert daily_result["Closed Trade Count"] == 0, (
        "Daily close-only pass must NOT record the reversed sell"
    )
    assert daily_result["Open Trade Count"] == 1

    intraday_df = _to_df(INTRADAY_ROWS)
    intraday_metrics = simulate_single_intraday(
        intraday_data=intraday_df,
        grid_step=GRID_STEP,
        profit_target=PROFIT_TARGET,
        strategy_class=FixedPortfolioPercentage,
        strategy_params={"allocation_pct": ALLOCATION_PCT},
    )
    assert intraday_metrics["Closed Trade Count"] == 1, (
        "Intraday pass must catch the intrabar touch via high"
    )
    assert intraday_metrics["Open Trade Count"] == 0


def test_run_sweep_default_behavior_unaffected_by_intraday_module_existing():
    # Task 0.1's baseline must still hold exactly -- this module and
    # method are additive/opt-in only.
    from tests.fixtures.regression_baseline import BASELINE

    df = pd.read_csv(
        Path(__file__).resolve().parents[1] / "fixtures" / "regression_ohlcv.csv",
        parse_dates=["timestamp"],
    )
    df.set_index("timestamp", inplace=True)
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


def test_validate_finalists_intraday_surfaces_daily_vs_intraday_comparison():
    daily_df = _to_df(DAILY_ROWS)
    intraday_df = _to_df(INTRADAY_ROWS)
    controller = OptimizationController(historical_data=daily_df)

    comparison = controller.validate_finalists_intraday(
        finalist_params=[
            {
                "grid_step": GRID_STEP,
                "profit_target": PROFIT_TARGET,
                "strategy_params": {"allocation_pct": ALLOCATION_PCT},
            }
        ],
        intraday_data=intraday_df,
        strategy_class=FixedPortfolioPercentage,
    )
    assert len(comparison) == 1
    row = comparison.iloc[0]
    assert row["Daily Closed Trades"] == 0
    assert row["Intraday Closed Trades"] == 1
    assert row["Diverges"] == True  # noqa: E712 (explicit bool comparison reads clearer here)


def test_missing_ohlc_columns_rejected():
    close_only = pd.DataFrame(
        {"close": [100.0, 101.0]}, index=pd.date_range("2024-01-01", periods=2, tz="UTC")
    )
    with pytest.raises(IntradayValidationError, match="missing required columns"):
        intraday_validation.validate_intraday_schema(close_only)


def test_invalid_intrabar_priority_rejected():
    intraday_df = _to_df(INTRADAY_ROWS)
    with pytest.raises(ValueError, match="intrabar_priority"):
        simulate_single_intraday(
            intraday_data=intraday_df,
            grid_step=GRID_STEP,
            profit_target=PROFIT_TARGET,
            strategy_class=FixedPortfolioPercentage,
            strategy_params={"allocation_pct": ALLOCATION_PCT},
            intrabar_priority="worst_first",
        )


def test_sell_first_and_buy_first_agree_when_bar_is_unambiguous():
    # Neither priority should change the outcome when a bar only ever
    # touches one side (this fixture's bar 3 low stays above the
    # post-bar-2 trigger level by design) -- order only matters on
    # genuinely ambiguous bars.
    intraday_df = _to_df(INTRADAY_ROWS)
    sell_first = simulate_single_intraday(
        intraday_data=intraday_df,
        grid_step=GRID_STEP,
        profit_target=PROFIT_TARGET,
        strategy_class=FixedPortfolioPercentage,
        strategy_params={"allocation_pct": ALLOCATION_PCT},
        intrabar_priority="sell_first",
    )
    buy_first = simulate_single_intraday(
        intraday_data=intraday_df,
        grid_step=GRID_STEP,
        profit_target=PROFIT_TARGET,
        strategy_class=FixedPortfolioPercentage,
        strategy_params={"allocation_pct": ALLOCATION_PCT},
        intrabar_priority="buy_first",
    )
    assert sell_first["Closed Trade Count"] == buy_first["Closed Trade Count"]
    assert sell_first["Final Equity"] == buy_first["Final Equity"]
