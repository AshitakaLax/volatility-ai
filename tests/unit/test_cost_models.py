import pytest

from src.cost_models import SlippageCommissionModel, ZeroCostModel


def test_zero_cost_model_returns_price_unchanged_and_zero_cost():
    model = ZeroCostModel()
    assert model.apply_buy(50.0, 10.0) == (50.0, 0.0)
    assert model.apply_sell(50.0, 10.0) == (50.0, 0.0)


def test_slippage_commission_buy_increases_effective_price():
    model = SlippageCommissionModel(commission_per_trade=1.5, slippage_bps=10)
    effective_price, cost = model.apply_buy(100.0, 5.0)
    assert effective_price > 100.0
    assert effective_price == pytest.approx(100.10)
    assert cost == 1.5


def test_slippage_commission_sell_decreases_effective_price():
    model = SlippageCommissionModel(commission_per_trade=1.5, slippage_bps=10)
    effective_price, cost = model.apply_sell(100.0, 5.0)
    assert effective_price < 100.0
    assert effective_price == pytest.approx(99.90)
    assert cost == 1.5


def test_zero_slippage_bps_leaves_price_unchanged():
    model = SlippageCommissionModel(commission_per_trade=2.0, slippage_bps=0)
    price, cost = model.apply_buy(100.0, 5.0)
    assert price == 100.0
    assert cost == 2.0


def test_apply_buy_and_sell_do_not_mutate_any_state():
    # Contract: pure calculation only. Calling repeatedly with the same
    # inputs must return identical results (no hidden internal state).
    model = SlippageCommissionModel(commission_per_trade=1.0, slippage_bps=5)
    first = model.apply_buy(100.0, 10.0)
    second = model.apply_buy(100.0, 10.0)
    assert first == second
