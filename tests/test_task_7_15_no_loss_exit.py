import pytest

from src.cost_models import ZeroCostModel
from src.exceptions import SellEconomicsError
from src.ledger import AssetLotLedger, validate_sell


def make_lot():
    ledger = AssetLotLedger()
    return ledger.register_buy(
        "buy-1", "TQQQ", filled_avg_price=100.0, qty=10.0,
        profit_target=0.05, buy_costs=1.0,
    )


def test_sell_below_cost_basis_is_rejected():
    lot = make_lot()
    with pytest.raises(SellEconomicsError):
        validate_sell(lot, 10.0, 99.0, ZeroCostModel())
    assert lot.shares == 10.0


def test_profitable_sell_is_allowed():
    lot = make_lot()
    economics = validate_sell(lot, 10.0, 105.0, ZeroCostModel())
    assert economics.allocated_cost_basis == pytest.approx(1001.0)
    assert economics.net_sell_proceeds == pytest.approx(1050.0)
    assert economics.realized_pnl == pytest.approx(49.0)


def test_partial_sell_uses_proportional_cost_basis():
    lot = make_lot()
    economics = validate_sell(lot, 5.0, 101.0, ZeroCostModel())
    assert economics.quantity == pytest.approx(5.0)
    assert economics.allocated_cost_basis == pytest.approx(500.5)
    assert economics.net_sell_proceeds == pytest.approx(505.0)
    assert economics.realized_pnl == pytest.approx(4.5)
    assert lot.shares == pytest.approx(10.0)


def test_invalid_quantities_are_rejected():
    lot = make_lot()
    with pytest.raises(ValueError):
        validate_sell(lot, 0.0, 110.0, ZeroCostModel())
    with pytest.raises(ValueError):
        validate_sell(lot, -1.0, 110.0, ZeroCostModel())
    with pytest.raises(ValueError):
        validate_sell(lot, 11.0, 110.0, ZeroCostModel())
