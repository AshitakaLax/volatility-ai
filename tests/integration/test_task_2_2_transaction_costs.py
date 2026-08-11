"""
Task 2.2 acceptance tests.

Acceptance criteria (implementation_task_specs.md):
1. cost_model=None (or ZeroCostModel()) -> Task 1.6's regression
   fixture output is unchanged.
2. SlippageCommissionModel(commission_per_trade=1.0, slippage_bps=5)
   -> lower final equity than the zero-cost run, explainable by
   (trade count x commission) + slippage drag.

Plus: costs applied exactly once, and the no-loss check reflects
actual cost-adjusted proceeds rather than quoted price alone (Cost-
model contract).
"""

from pathlib import Path

import pandas as pd
import pytest

from optimization_controller import OptimizationController
from src.cost_models import SlippageCommissionModel, TransactionCostModel, ZeroCostModel
from src.size_calculators import FixedPortfolioPercentage
from tests.fixtures.regression_baseline import BASELINE

FIXTURE_PATH = Path(__file__).resolve().parents[1] / "fixtures" / "regression_ohlcv.csv"


def _load_fixture() -> pd.DataFrame:
    df = pd.read_csv(FIXTURE_PATH, parse_dates=["timestamp"])
    df.set_index("timestamp", inplace=True)
    return df


def _run(df, cost_model=None):
    controller = OptimizationController(historical_data=df)
    kwargs = {}
    if cost_model is not None:
        kwargs["cost_model"] = cost_model
    return controller.run_sweep(
        grid_steps=[0.01],
        profit_targets=[0.005],
        strategy_class=FixedPortfolioPercentage,
        strategy_params_grid=[{"allocation_pct": 0.05}],
        **kwargs,
    ).iloc[0]


def test_cost_model_omitted_defaults_to_zero_cost_matches_baseline():
    df = _load_fixture()
    row = _run(df)  # no cost_model kwarg at all
    for key, expected in BASELINE.items():
        assert row[key] == expected, f"{key}: {row[key]!r} != baseline {expected!r} with default cost_model"


def test_explicit_zero_cost_model_matches_baseline():
    df = _load_fixture()
    row = _run(df, cost_model=ZeroCostModel())
    for key, expected in BASELINE.items():
        assert row[key] == expected, f"{key}: {row[key]!r} != baseline {expected!r} with explicit ZeroCostModel"


def test_slippage_commission_produces_lower_final_equity_explainable_by_drag():
    df = _load_fixture()
    zero_cost_row = _run(df, cost_model=ZeroCostModel())
    costed_row = _run(df, cost_model=SlippageCommissionModel(commission_per_trade=1.0, slippage_bps=5))

    assert costed_row["Final Equity"] < zero_cost_row["Final Equity"]

    trade_count = zero_cost_row["Trade Count"]
    assert costed_row["Trade Count"] == trade_count, "Cost model must not change which/how many trades fire"

    commission_drag = trade_count * 2 * 1.0  # commission charged on both the buy and the matching sell
    # Slippage drag: ~5bps adverse move applied on both buy (pay more)
    # and sell (receive less) legs of each round-trip, roughly
    # 2 * 0.0005 * notional per trade. Bound loosely (order of
    # magnitude), not to the cent, since exact notional varies per lot.
    approx_notional_per_trade = zero_cost_row["Final Equity"] * 0.05  # allocation_pct
    slippage_drag_estimate = trade_count * 2 * 0.0005 * approx_notional_per_trade

    total_drag = zero_cost_row["Final Equity"] - costed_row["Final Equity"]
    assert total_drag >= commission_drag, (
        f"Observed drag {total_drag:.4f} is less than commission alone {commission_drag:.4f} -- "
        "commission does not appear to be applied to both legs."
    )
    # Sanity bound: drag shouldn't be wildly larger than commission + a
    # generous slippage estimate (catches accidental double-application).
    assert total_drag < commission_drag + slippage_drag_estimate * 3


def test_costs_applied_exactly_once_per_leg():
    # A custom model that records every call lets us confirm apply_buy
    # and apply_sell are each invoked exactly once per fill, not zero
    # or two-plus times (which would silently double- or zero-charge).
    calls = {"buy": 0, "sell": 0}

    class CountingCostModel(TransactionCostModel):
        def apply_buy(self, price, qty, context=None, prev_close=None):
            calls["buy"] += 1
            return price, 0.5

        def apply_sell(self, price, qty, context=None, prev_close=None):
            calls["sell"] += 1
            return price, 0.5

    df = _load_fixture()
    row = _run(df, cost_model=CountingCostModel())

    assert calls["buy"] == row["Trade Count"]
    assert calls["sell"] == row["Closed Trade Count"]


def test_no_loss_check_uses_cost_adjusted_proceeds_not_quoted_price():
    # profit_target=0.005 (0.5%) is a thin margin. A cost model with a
    # commission large enough to exceed that margin must cause the
    # no-loss check to reject the sell, even though the *quoted* price
    # (target_sell_price) shows a nominal profit.
    class MarginEatingCostModel(TransactionCostModel):
        def apply_buy(self, price, qty, context=None, prev_close=None):
            return price, 0.0  # no buy-side cost, isolate the sell-side check

        def apply_sell(self, price, qty, context=None, prev_close=None):
            return price, 100.0  # commission larger than any single lot's profit margin

    df = _load_fixture()
    row = _run(df, cost_model=MarginEatingCostModel())

    assert row["Trade Count"] == 4  # buys still fire, unaffected
    assert row["Closed Trade Count"] == 0, (
        "Sells should be rejected by the no-loss check once realized "
        "proceeds (after the $100 commission) fall below cost basis, "
        "even though the quoted target_sell_price alone looks profitable."
    )
