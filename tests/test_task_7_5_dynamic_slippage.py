import pytest

from src.cost_models import DynamicSlippageModel


def test_dynamic_slippage_increases_with_absolute_move():
    model = DynamicSlippageModel(slippage_bps=10.0)

    low_buy, _ = model.apply_buy(100.10, 1.0, prev_close=100.0)
    high_buy, _ = model.apply_buy(110.0, 1.0, prev_close=100.0)
    low_sell, _ = model.apply_sell(99.90, 1.0, prev_close=100.0)
    high_sell, _ = model.apply_sell(90.0, 1.0, prev_close=100.0)

    assert high_buy - 110.0 > low_buy - 100.10
    assert 90.0 - high_sell > 99.90 - low_sell


def test_dynamic_slippage_uses_base_rate_without_previous_close():
    model = DynamicSlippageModel(slippage_bps=10.0)

    buy, _ = model.apply_buy(100.0, 1.0)
    sell, _ = model.apply_sell(100.0, 1.0)

    assert buy == pytest.approx(100.1)
    assert sell == pytest.approx(99.9)


def test_dynamic_slippage_preserves_commission():
    model = DynamicSlippageModel(commission_per_trade=2.5, slippage_bps=10.0)
    _, buy_cost = model.apply_buy(110.0, 1.0, prev_close=100.0)
    _, sell_cost = model.apply_sell(90.0, 1.0, prev_close=100.0)

    assert buy_cost == pytest.approx(2.5)
    assert sell_cost == pytest.approx(2.5)


def test_dynamic_slippage_rejects_negative_parameters():
    with pytest.raises(ValueError):
        DynamicSlippageModel(slippage_bps=-1.0)
    with pytest.raises(ValueError):
        DynamicSlippageModel(commission_per_trade=-1.0)
