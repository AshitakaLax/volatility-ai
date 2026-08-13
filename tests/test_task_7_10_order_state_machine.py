import pytest

from src.order_management_system import InvalidOrderTransition, OrderManagementSystem, OrderStatus


def test_canonical_lifecycle_and_partial_fill_remaining_quantity():
    oms = OrderManagementSystem()
    order = oms._simulation_order("BUY", "TQQQ", 10, 100, 1000)
    record = oms.order_states[order["id"]]
    assert record.status is OrderStatus.FILLED
    assert record.remaining_qty == pytest.approx(0)


def test_partial_fill_preserves_remaining_quantity():
    oms = OrderManagementSystem()
    order_id = "manual-1"
    from src.order_management_system import OrderRecord
    oms.order_states[order_id] = OrderRecord(order_id, "TQQQ", "BUY", 10, remaining_qty=10)
    oms.transition(order_id, OrderStatus.SUBMITTED)
    oms.transition(order_id, OrderStatus.ACCEPTED)
    oms.update_fill(order_id, 4, 100)
    assert oms.order_states[order_id].status is OrderStatus.PARTIALLY_FILLED
    assert oms.order_states[order_id].remaining_qty == pytest.approx(6)
    oms.update_fill(order_id, 10, 101)
    assert oms.order_states[order_id].status is OrderStatus.FILLED
    assert oms.order_states[order_id].remaining_qty == pytest.approx(0)


def test_invalid_terminal_transition_does_not_mutate_state():
    oms = OrderManagementSystem()
    order_id = "manual-2"
    from src.order_management_system import OrderRecord
    oms.order_states[order_id] = OrderRecord(order_id, "TQQQ", "BUY", 1, remaining_qty=1)
    oms.transition(order_id, OrderStatus.SUBMITTED)
    oms.transition(order_id, OrderStatus.REJECTED)
    with pytest.raises(InvalidOrderTransition):
        oms.transition(order_id, OrderStatus.FILLED)
    assert oms.order_states[order_id].status is OrderStatus.REJECTED


def test_broker_status_mapping_is_canonical():
    assert OrderManagementSystem.map_broker_status("new") is OrderStatus.ACCEPTED
    assert OrderManagementSystem.map_broker_status("partially_filled") is OrderStatus.PARTIALLY_FILLED
    assert OrderManagementSystem.map_broker_status("done_for_day") is OrderStatus.EXPIRED
    assert OrderManagementSystem.map_broker_status("unexpected") is OrderStatus.UNKNOWN
