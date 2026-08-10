from src.ledger import AssetLotLedger
from src.order_management_system import Mode, OrderManagementSystem, OrderStatus
from src.size_calculators import FixedPortfolioPercentage


def test_ledger_registers_and_closes_targeted_lot():
    ledger = AssetLotLedger()
    lot = ledger.register_buy("b1", "TQQQ", 50.0, 100.0, 0.005)
    assert lot.target_sell_price == 50.25
    assert ledger.get_marketable_lots(50.24) == []
    assert ledger.get_marketable_lots(50.25) == [lot]
    ledger.close_lot(lot)
    assert ledger.open_lots == []
    assert ledger.closed_lots == [lot]


def test_ledger_supports_backward_compatible_partial_close():
    ledger = AssetLotLedger()
    lot = ledger.register_buy("b1", "TQQQ", 50.0, 10.0, 0.005)
    ledger.close_lot(lot, sell_qty=4.0, execution_price=51.0, completed=False)
    assert lot.shares == 6.0
    assert lot in ledger.open_lots
    assert lot not in ledger.closed_lots


def test_simulation_oms_fills_orders_deterministically():
    oms = OrderManagementSystem(mode=Mode.SIMULATION)
    buy = oms.execute_buy("TQQQ", 1000.0, 50.0)
    assert buy["status"] == OrderStatus.FILLED.value
    assert buy["qty"] == 20.0
    sell = oms.execute_sell("TQQQ", 20.0, 50.25)
    assert sell["status"] == OrderStatus.FILLED.value
    assert sell["filled_avg_price"] == 50.25


def test_fixed_percentage_sizes_from_equity():
    strategy = FixedPortfolioPercentage(percentage=0.05)
    assert strategy.calculate_trade_value(100_000.0, 50.0) == 5_000.0
