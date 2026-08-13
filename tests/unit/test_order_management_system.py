import pytest

from src.exceptions import ConfigurationError
from src.order_management_system import OrderManagementSystem, OrderStatus


def test_execute_buy_computes_qty_and_fills_at_requested_price():
    oms = OrderManagementSystem(mode="SIMULATION")
    result = oms.execute_buy("TQQQ", trade_value=1000.0, price=50.0)

    assert result["qty"] == pytest.approx(20.0)
    assert result["filled_qty"] == pytest.approx(20.0)
    assert result["filled_avg_price"] == 50.0
    assert result["status"] == OrderStatus.FILLED
    assert result["symbol"] == "TQQQ"
    assert result["id"]


def test_execute_sell_fills_completely_at_requested_price():
    oms = OrderManagementSystem(mode="SIMULATION")
    result = oms.execute_sell("TQQQ", qty=12.5, price=55.0)

    assert result["qty"] == 12.5
    assert result["filled_qty"] == 12.5
    assert result["filled_avg_price"] == 55.0
    assert result["status"] == OrderStatus.FILLED


def test_order_ids_are_unique_and_sequential_within_an_instance():
    oms = OrderManagementSystem(mode="SIMULATION")
    first = oms.execute_buy("TQQQ", 1000.0, 50.0)["id"]
    second = oms.execute_buy("TQQQ", 1000.0, 50.0)["id"]
    assert first != second


@pytest.mark.parametrize("trade_value,price", [(0, 50.0), (-100, 50.0), (1000.0, 0), (1000.0, -1)])
def test_execute_buy_rejects_non_positive_values(trade_value, price):
    oms = OrderManagementSystem(mode="SIMULATION")
    with pytest.raises(ValueError):
        oms.execute_buy("TQQQ", trade_value, price)


@pytest.mark.parametrize("qty,price", [(0, 50.0), (-1, 50.0), (10.0, 0), (10.0, -1)])
def test_execute_sell_rejects_non_positive_values(qty, price):
    oms = OrderManagementSystem(mode="SIMULATION")
    with pytest.raises(ValueError):
        oms.execute_sell("TQQQ", qty, price)


def test_invalid_mode_rejected_at_construction():
    with pytest.raises(ConfigurationError):
        OrderManagementSystem(mode="PAPER")


def test_live_mode_not_implemented():
    oms = OrderManagementSystem(mode="LIVE")
    with pytest.raises(NotImplementedError):
        oms.execute_buy("TQQQ", 1000.0, 50.0)
    with pytest.raises(NotImplementedError):
        oms.execute_sell("TQQQ", 10.0, 50.0)
