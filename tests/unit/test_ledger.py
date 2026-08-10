import pytest

from src.ledger import AssetLotLedger, Lot


def test_register_buy_creates_open_lot_with_computed_target():
    ledger = AssetLotLedger()
    lot = ledger.register_buy("ord-1", "TQQQ", buy_price=50.0, shares=10.0, profit_target=0.005)

    assert lot in ledger.open_lots
    assert ledger.closed_lots == []
    assert lot.target_sell_price == pytest.approx(50.25)


@pytest.mark.parametrize(
    "kwargs",
    [
        dict(shares=0),
        dict(shares=-5),
        dict(buy_price=0),
        dict(buy_price=-1),
        dict(profit_target=0),
        dict(profit_target=-0.01),
    ],
)
def test_register_buy_rejects_invalid_input(kwargs):
    ledger = AssetLotLedger()
    base = dict(order_id="ord-1", symbol="TQQQ", buy_price=50.0, shares=10.0, profit_target=0.005)
    base.update(kwargs)
    with pytest.raises(ValueError):
        ledger.register_buy(**base)


def test_get_marketable_lots_boundary_exactly_at_target_is_marketable():
    ledger = AssetLotLedger()
    lot = ledger.register_buy("ord-1", "TQQQ", buy_price=100.0, shares=1.0, profit_target=0.01)
    # target_sell_price is exactly 101.0
    assert ledger.get_marketable_lots(100.99) == []
    assert ledger.get_marketable_lots(101.00) == [lot]
    assert ledger.get_marketable_lots(101.01) == [lot]


def test_get_marketable_lots_only_returns_open_lots_meeting_target():
    ledger = AssetLotLedger()
    cheap = ledger.register_buy("ord-1", "TQQQ", buy_price=40.0, shares=1.0, profit_target=0.01)
    ledger.register_buy("ord-2", "TQQQ", buy_price=60.0, shares=1.0, profit_target=0.01)

    marketable = ledger.get_marketable_lots(current_price=41.0)
    assert marketable == [cheap]


def test_get_marketable_lots_does_not_mutate_state():
    ledger = AssetLotLedger()
    lot = ledger.register_buy("ord-1", "TQQQ", buy_price=40.0, shares=1.0, profit_target=0.01)
    ledger.get_marketable_lots(current_price=100.0)
    assert lot in ledger.open_lots
    assert lot not in ledger.closed_lots


def test_close_lot_moves_lot_from_open_to_closed():
    ledger = AssetLotLedger()
    lot = ledger.register_buy("ord-1", "TQQQ", buy_price=40.0, shares=1.0, profit_target=0.01)
    ledger.close_lot(lot)
    assert lot not in ledger.open_lots
    assert lot in ledger.closed_lots


def test_close_lot_twice_raises():
    ledger = AssetLotLedger()
    lot = ledger.register_buy("ord-1", "TQQQ", buy_price=40.0, shares=1.0, profit_target=0.01)
    ledger.close_lot(lot)
    with pytest.raises(ValueError):
        ledger.close_lot(lot)


def test_close_lot_unknown_lot_raises():
    ledger = AssetLotLedger()
    stray = Lot(order_id="ghost", symbol="TQQQ", buy_price=1.0, shares=1.0, profit_target=0.01)
    with pytest.raises(ValueError):
        ledger.close_lot(stray)


def test_close_lot_partial_close_not_implemented():
    ledger = AssetLotLedger()
    lot = ledger.register_buy("ord-1", "TQQQ", buy_price=40.0, shares=1.0, profit_target=0.01)
    with pytest.raises(NotImplementedError):
        ledger.close_lot(lot, completed=False)
    # Rejected attempt must not have mutated state.
    assert lot in ledger.open_lots
