"""
Task 3.3 acceptance test (part of R2's family): on_flat_reentry
controls what last_buy_price becomes the moment the portfolio goes
fully flat (last open lot harvested).

Fixture (verified numerically before being written here): buy triggers
at 95 (5% drop from 100, grid_step=0.05); harvests at 102.6 (8% profit
target) -- fully flat. Price continues to 105, then declines to 97.
- stale_reference (default): last_buy_price stays 95 -> next trigger
  needs <= 90.25. 97 doesn't reach it -> no re-entry.
- reset_to_market: last_buy_price resets to 102.6 (the harvest price)
  -> next trigger needs <= 97.47. 97 clears it -> re-enters sooner.
"""

from pathlib import Path

import pandas as pd
import pytest

from optimization_controller import OptimizationController
from src.exceptions import ConfigurationError
from src.size_calculators import FixedPortfolioPercentage
from tests.fixtures.regression_baseline import BASELINE

GRID_STEP = 0.05
PROFIT_TARGET = 0.08
ALLOCATION_PCT = 0.05

CLOSES = [100.0, 95.0, 102.6, 105.0, 97.0, 96.0]


def _flat_reentry_fixture() -> pd.DataFrame:
    idx = pd.date_range("2024-01-01", periods=len(CLOSES), freq="D", tz="UTC")
    return pd.DataFrame(
        {
            "open": [100.0] + CLOSES[:-1],
            "high": [c * 1.001 for c in CLOSES],
            "low": [c * 0.999 for c in CLOSES],
            "close": CLOSES,
            "volume": [1_000_000] * len(CLOSES),
        },
        index=idx,
    )


def _run(df, **kwargs):
    return OptimizationController(historical_data=df).run_sweep(
        grid_steps=[GRID_STEP],
        profit_targets=[PROFIT_TARGET],
        strategy_class=FixedPortfolioPercentage,
        strategy_params_grid=[{"allocation_pct": ALLOCATION_PCT}],
        **kwargs,
    ).iloc[0]


def test_stale_reference_default_does_not_reenter():
    df = _flat_reentry_fixture()
    row = _run(df)  # on_flat_reentry omitted -> default stale_reference
    assert row["Trade Count"] == 1
    assert row["Open Trade Count"] == 0


def test_reset_to_market_reenters_sooner():
    df = _flat_reentry_fixture()
    row = _run(df, on_flat_reentry="reset_to_market")
    assert row["Trade Count"] == 2
    assert row["Open Trade Count"] == 1


def test_explicit_stale_reference_matches_default():
    df = _flat_reentry_fixture()
    default_row = _run(df)
    explicit_row = _run(df, on_flat_reentry="stale_reference")
    assert default_row["Trade Count"] == explicit_row["Trade Count"]
    assert default_row["Final Equity"] == explicit_row["Final Equity"]


def test_default_matches_task_0_1_baseline():
    df = pd.read_csv(
        Path(__file__).resolve().parents[1] / "fixtures" / "regression_ohlcv.csv", parse_dates=["timestamp"]
    )
    df.set_index("timestamp", inplace=True)
    row = OptimizationController(historical_data=df).run_sweep(
        grid_steps=[BASELINE["Grid Step"]],
        profit_targets=[BASELINE["Profit Target"]],
        strategy_class=FixedPortfolioPercentage,
        strategy_params_grid=[{"allocation_pct": BASELINE["allocation_pct"]}],
    ).iloc[0]
    for key, expected in BASELINE.items():
        assert row[key] == expected


def test_invalid_policy_rejected():
    df = _flat_reentry_fixture()
    with pytest.raises(ConfigurationError, match="on_flat_reentry"):
        _run(df, on_flat_reentry="something_else")
