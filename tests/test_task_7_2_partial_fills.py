from types import SimpleNamespace

import pytest

from src.exceptions import ReconciliationError
from src.ledger import AssetLotLedger
from src.live_execution import _CumulativeFill, _cumulative_fill_delta


def test_cumulative_fill_arithmetic_fixture():
    state = _CumulativeFill()
    updates = [
        (4.0, 150.0, 4.0, 600.0, 150.0),
        (7.0, 151.0, 3.0, 457.0, 152.33333333333334),
        (10.0, 152.0, 3.0, 463.0, 154.33333333333334),
    ]
    for qty, avg, expected_qty, expected_notional, expected_avg in updates:
        order = SimpleNamespace(filled_qty=str(qty), filled_avg_price=str(avg))
        new_qty, new_notional, new_avg = _cumulative_fill_delta(order, state)
        assert new_qty == pytest.approx(expected_qty)
        assert new_notional == pytest.approx(expected_notional)
        assert new_avg == pytest.approx(expected_avg)
        state.qty = qty
        state.notional = qty * avg


def test_partial_sell_mutates_only_remaining_shares():
    ledger = AssetLotLedger()
    lot = ledger.register_buy("buy-1", "TQQQ", 100.0, 10.0, 0.05)
    ledger.close_lot(lot, sell_qty=4.0, execution_price=150.0, completed=False)

    assert lot in ledger.open_lots
    assert lot.shares == pytest.approx(6.0)
    assert lot.buy_price == pytest.approx(100.0)
    assert lot.target_sell_price == pytest.approx(105.0)


def test_full_close_after_incremental_sell():
    ledger = AssetLotLedger()
    lot = ledger.register_buy("buy-1", "TQQQ", 100.0, 10.0, 0.05)
    ledger.close_lot(lot, sell_qty=4.0, execution_price=150.0, completed=False)
    ledger.close_lot(lot, sell_qty=6.0, execution_price=151.0, completed=False)

    assert lot not in ledger.open_lots
    assert lot in ledger.closed_lots
    assert lot.shares == pytest.approx(0.0)


def test_cumulative_fill_decrease_enters_reconciliation():
    state = _CumulativeFill(qty=7.0, notional=1057.0)
    order = SimpleNamespace(filled_qty="6.0", filled_avg_price="151.0")
    with pytest.raises(ReconciliationError):
        _cumulative_fill_delta(order, state)


def test_exact_alpaca_partial_fill_fixture_when_dependency_available():
    alpaca = pytest.importorskip("alpaca.trading.models")
    enums = pytest.importorskip("alpaca.trading.enums")
    order = alpaca.Order(
        id="test-123",
        status=enums.OrderStatus.PARTIALLY_FILLED,
        qty="10.0",
        filled_qty="4.0",
        filled_avg_price="150.00",
        side=enums.OrderSide.SELL,
    )
    state = _CumulativeFill()
    qty, notional, avg = _cumulative_fill_delta(order, state)
    assert qty == pytest.approx(4.0)
    assert notional == pytest.approx(600.0)
    assert avg == pytest.approx(150.0)
