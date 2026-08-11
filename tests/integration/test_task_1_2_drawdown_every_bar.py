"""
Task 1.2 acceptance test (B3): peak equity / drawdown must be tracked
every bar, not only on bars where a grid buy triggers.

tests/fixtures/drawdown_non_trigger_bar.csv is a crafted 7-bar series
where bar 4 (price 94.50) is the deepest point of the whole series but
is NOT a trigger bar (94.50 > last_buy_price(95) * (1 - 0.01) = 94.05).
Verified independently in the chat this test was produced in: the
correct (every-bar) max drawdown is ~0.2048%, versus ~0.1531% if only
trigger bars are sampled -- the exact shape of bug B3.

profit_target=0.10 is deliberately high so no lot is ever harvested
during this short series, isolating drawdown tracking from harvest
interaction.
"""

import math
from pathlib import Path

import pandas as pd
import pytest

from optimization_controller import OptimizationController
from src.size_calculators import FixedPortfolioPercentage

FIXTURE_PATH = Path(__file__).resolve().parents[1] / "fixtures" / "drawdown_non_trigger_bar.csv"
MONEY_EPSILON = 1e-8

GRID_STEP = 0.01
PROFIT_TARGET = 0.10  # high enough that nothing harvests in this short series
ALLOCATION_PCT = 0.05


def _load_fixture() -> pd.DataFrame:
    df = pd.read_csv(FIXTURE_PATH, parse_dates=["timestamp"])
    df.set_index("timestamp", inplace=True)
    return df


def _expected_max_drawdown_pct(df: pd.DataFrame) -> float:
    """Independent reference computation: peak/drawdown recomputed every
    bar, buy-sizing/trigger logic mirrored exactly from
    optimization_controller.py's documented rules. Does not import or
    call the controller -- this is a from-scratch cross-check, not a
    restatement of its (possibly still-buggy) code."""
    cash = 100_000.0
    lots: list[tuple[float, float]] = []  # (buy_price, shares)
    last_buy_price = df["close"].iloc[0]
    peak = cash
    max_dd = 0.0

    for price in df["close"]:
        equity = cash + sum(shares * price for _, shares in lots)
        if equity > peak:
            peak = equity
        dd = (peak - equity) / peak
        if dd > max_dd:
            max_dd = dd

        if price <= last_buy_price * (1.0 - GRID_STEP):
            trade_value = equity * ALLOCATION_PCT
            if cash >= trade_value and trade_value > 0:
                shares = trade_value / price
                lots.append((price, shares))
                cash -= trade_value
                last_buy_price = price

    return max_dd * 100.0


def test_max_drawdown_reflects_deepest_bar_even_when_not_a_trigger_bar():
    df = _load_fixture()
    expected_pct = _expected_max_drawdown_pct(df)
    assert expected_pct == pytest.approx(0.204847, abs=1e-4), (
        "Fixture's own reference computation drifted from the value verified "
        "when this fixture was built -- check drawdown_non_trigger_bar.csv wasn't edited."
    )

    controller = OptimizationController(historical_data=df)
    result = controller.run_sweep(
        grid_steps=[GRID_STEP],
        profit_targets=[PROFIT_TARGET],
        strategy_class=FixedPortfolioPercentage,
        strategy_params_grid=[{"allocation_pct": ALLOCATION_PCT}],
    )
    actual_pct = result.iloc[0]["Max Drawdown %"]

    assert math.isclose(actual_pct, expected_pct, rel_tol=0.0, abs_tol=MONEY_EPSILON), (
        f"Max Drawdown % = {actual_pct} does not match the true every-bar "
        f"figure {expected_pct} -- drawdown is still only being sampled on "
        f"trigger bars (bug B3), missing the deeper non-trigger bar."
    )


def test_existing_trigger_and_buy_behavior_is_otherwise_unchanged():
    # Same fixture: confirm the fix didn't change *which* bars trigger a
    # buy or how many lots get opened -- only the drawdown bookkeeping.
    df = _load_fixture()
    controller = OptimizationController(historical_data=df)
    result = controller.run_sweep(
        grid_steps=[GRID_STEP],
        profit_targets=[PROFIT_TARGET],
        strategy_class=FixedPortfolioPercentage,
        strategy_params_grid=[{"allocation_pct": ALLOCATION_PCT}],
    )
    row = result.iloc[0]
    # Bars 1 and 2 (98.00, 95.00) trigger; 3/4/5/6 do not (verified above).
    assert row["Trade Count"] == 2
    assert row["Open Trade Count"] == 2  # profit_target=0.10 never harvests here
