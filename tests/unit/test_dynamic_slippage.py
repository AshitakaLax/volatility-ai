"""
Task 7.5 tests (L6).

Acceptance criteria:
1. With DynamicSlippageModel, a fixture containing one unusually large
   single-bar move shows a visibly wider effective fill spread on that
   bar than on calmer bars.
2. ZeroCostModel and SlippageCommissionModel behavior is completely
   unchanged by the signature extension.

Spread ratios below were verified empirically before being written as
assertions (a 5% move produces a ~33x wider spread than a 0.1% move at
base_bps=5, vol_multiplier=1).
"""

from datetime import UTC, datetime

import pandas as pd
import pytest

from optimization_controller import OptimizationController
from src.cost_models import DynamicSlippageModel, SlippageCommissionModel, ZeroCostModel
from src.market_context import MarketContext
from src.size_calculators import FixedPortfolioPercentage
from tests.fixtures.regression_baseline import BASELINE


def _context(close: float) -> MarketContext:
    return MarketContext(
        timestamp=datetime(2024, 1, 1, tzinfo=UTC),
        open=close,
        high=close,
        low=close,
        close=close,
        cash=100_000.0,
        equity=100_000.0,
        peak_equity=100_000.0,
        drawdown=0.0,
        open_lot_count=0,
        bar_index=0,
    )


def _spread(model, prev_close, close, price=100.0):
    buy, _ = model.apply_buy(price, 1, context=_context(close), prev_close=prev_close)
    sell, _ = model.apply_sell(price, 1, context=_context(close), prev_close=prev_close)
    return buy - sell


def test_large_single_bar_move_produces_a_visibly_wider_spread():
    model = DynamicSlippageModel(base_bps=5.0, vol_multiplier=1.0)
    calm = _spread(model, prev_close=100.0, close=100.1)  # 0.1% move
    volatile = _spread(model, prev_close=100.0, close=105.0)  # 5% move
    assert volatile > calm
    assert volatile > calm * 10, (
        f"Expected a visibly wider spread; got calm={calm}, volatile={volatile}"
    )


def test_spread_scales_monotonically_with_bar_move():
    model = DynamicSlippageModel(base_bps=5.0, vol_multiplier=1.0)
    spreads = [_spread(model, 100.0, 100.0 + move) for move in (0.1, 0.5, 1.0, 5.0)]
    assert spreads == sorted(spreads)
    assert len(set(spreads)) == len(spreads)


def test_direction_of_move_does_not_matter_only_magnitude():
    # abs() in the formula: a -5% bar is as costly as a +5% bar.
    model = DynamicSlippageModel(base_bps=5.0, vol_multiplier=1.0)
    up = _spread(model, prev_close=100.0, close=105.0)
    down = _spread(model, prev_close=100.0, close=95.0)
    assert up == pytest.approx(down)


def test_buy_is_worse_and_sell_is_worse_never_better():
    model = DynamicSlippageModel(base_bps=5.0, vol_multiplier=1.0)
    buy, _ = model.apply_buy(100.0, 1, context=_context(105.0), prev_close=100.0)
    sell, _ = model.apply_sell(100.0, 1, context=_context(105.0), prev_close=100.0)
    assert buy > 100.0, "Slippage must make a buy cost more, never less"
    assert sell < 100.0, "Slippage must make a sell receive less, never more"


def test_vol_multiplier_scales_the_volatility_component():
    low = DynamicSlippageModel(base_bps=5.0, vol_multiplier=1.0)
    high = DynamicSlippageModel(base_bps=5.0, vol_multiplier=3.0)
    assert _spread(high, 100.0, 105.0) > _spread(low, 100.0, 105.0)


def test_commission_is_returned_independently_of_volatility():
    model = DynamicSlippageModel(base_bps=5.0, vol_multiplier=1.0, commission_per_trade=2.5)
    _, calm_cost = model.apply_buy(100.0, 1, context=_context(100.1), prev_close=100.0)
    _, volatile_cost = model.apply_buy(100.0, 1, context=_context(105.0), prev_close=100.0)
    assert calm_cost == volatile_cost == 2.5


def test_falls_back_to_base_bps_without_prev_close():
    model = DynamicSlippageModel(base_bps=5.0, vol_multiplier=1.0)
    price, _ = model.apply_buy(100.0, 1, context=_context(105.0), prev_close=None)
    assert price == pytest.approx(100.0 * (1 + 5 / 10_000))


def test_falls_back_to_base_bps_without_context():
    model = DynamicSlippageModel(base_bps=5.0, vol_multiplier=1.0)
    price, _ = model.apply_buy(100.0, 1, context=None, prev_close=100.0)
    assert price == pytest.approx(100.0 * (1 + 5 / 10_000))


def test_zero_prev_close_does_not_divide_by_zero():
    model = DynamicSlippageModel(base_bps=5.0, vol_multiplier=1.0)
    price, _ = model.apply_buy(100.0, 1, context=_context(105.0), prev_close=0.0)
    assert price == pytest.approx(100.0 * (1 + 5 / 10_000))


def test_no_move_costs_only_base_bps():
    model = DynamicSlippageModel(base_bps=5.0, vol_multiplier=1.0)
    price, _ = model.apply_buy(100.0, 1, context=_context(100.0), prev_close=100.0)
    assert price == pytest.approx(100.0 * (1 + 5 / 10_000))


def test_defaults_are_a_complete_no_op():
    model = DynamicSlippageModel()  # base_bps=0, vol_multiplier=1, commission=0
    price, cost = model.apply_buy(100.0, 1, context=_context(100.0), prev_close=100.0)
    assert price == pytest.approx(100.0)
    assert cost == 0.0


def test_zero_cost_model_unchanged_by_the_signature_extension():
    model = ZeroCostModel()
    assert model.apply_buy(50.0, 10.0) == (50.0, 0.0)
    assert model.apply_sell(50.0, 10.0) == (50.0, 0.0)
    # And identical when the new arguments ARE supplied.
    assert model.apply_buy(50.0, 10.0, context=_context(99.0), prev_close=50.0) == (50.0, 0.0)
    assert model.apply_sell(50.0, 10.0, context=_context(99.0), prev_close=50.0) == (50.0, 0.0)


def test_slippage_commission_model_ignores_context_and_prev_close():
    model = SlippageCommissionModel(commission_per_trade=1.5, slippage_bps=10)
    without = model.apply_buy(100.0, 5.0)
    with_extras = model.apply_buy(100.0, 5.0, context=_context(150.0), prev_close=100.0)
    assert without == with_extras


def test_regression_baseline_unchanged_after_threading_context_through():
    df = pd.read_csv("tests/fixtures/regression_ohlcv.csv", parse_dates=["timestamp"]).set_index(
        "timestamp"
    )
    row = (
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
        assert row[key] == expected


def test_dynamic_slippage_eats_thin_margins_and_the_no_loss_check_blocks_those_harvests():
    """Dynamic slippage interacting with the no-loss invariant (Task 1.5).

    The fixture's profit_target is 0.5%, but a volatile bar's dynamic
    slippage exceeds that margin -- so realized proceeds would fall
    below cost basis and the no-loss check correctly REJECTS those
    sells. Verified before writing this assertion.

    Deliberately not asserting "dynamic Final Equity < zero-cost Final
    Equity", which is intuitive but false here and would have been a
    misleading test: with every harvest blocked, the lots stay open and
    mark to market at this fixture's rallying final close (57.34 vs a
    ~47-49 cost basis), so dynamic actually ends HIGHER. That's an
    artifact of mark-to-market on a rising fixture, not of slippage
    being free -- the real, checkable cost signal is that the thin
    harvests stop happening at all.
    """
    df = pd.read_csv("tests/fixtures/regression_ohlcv.csv", parse_dates=["timestamp"]).set_index(
        "timestamp"
    )
    controller = OptimizationController(historical_data=df)
    common = dict(
        grid_steps=[0.01],
        profit_targets=[0.005],
        strategy_class=FixedPortfolioPercentage,
        strategy_params_grid=[{"allocation_pct": 0.05}],
    )
    zero = controller.run_sweep(cost_model=ZeroCostModel(), **common).iloc[0]
    dynamic = controller.run_sweep(
        cost_model=DynamicSlippageModel(base_bps=5.0, vol_multiplier=1.0), **common
    ).iloc[0]

    assert zero["Closed Trade Count"] == 4 and zero["Realized PnL"] > 0
    assert dynamic["Closed Trade Count"] < zero["Closed Trade Count"], (
        "Dynamic slippage should make thin-margin harvests unprofitable, so fewer close"
    )
    assert dynamic["Realized PnL"] == 0, (
        "No harvest should clear the no-loss check at this slippage"
    )
    assert dynamic["Trade Count"] == zero["Trade Count"], (
        "Buys still fire; only the exits are blocked"
    )


def test_a_generous_profit_target_still_harvests_under_dynamic_slippage():
    # Counterpart to the above: the blocking is margin-dependent, not a
    # blanket refusal to ever sell under a dynamic cost model.
    df = pd.read_csv("tests/fixtures/regression_ohlcv.csv", parse_dates=["timestamp"]).set_index(
        "timestamp"
    )
    result = (
        OptimizationController(historical_data=df)
        .run_sweep(
            grid_steps=[0.01],
            profit_targets=[0.10],  # 10% target, far above the slippage
            strategy_class=FixedPortfolioPercentage,
            strategy_params_grid=[{"allocation_pct": 0.05}],
            cost_model=DynamicSlippageModel(base_bps=5.0, vol_multiplier=1.0),
        )
        .iloc[0]
    )
    assert result["Closed Trade Count"] > 0
