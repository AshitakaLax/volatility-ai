from types import SimpleNamespace

from src.cost_models import ZeroCostModel
from src.live_execution import LiveExecutionLoop
from src.persistence import SQLiteStateStore
from src.ledger import AssetLotLedger


def _loop(store):
    loop = LiveExecutionLoop.__new__(LiveExecutionLoop)
    loop.state_store = store
    loop.oms = SimpleNamespace(process_event_once=lambda event_id, fn: (True, fn()))
    loop.ledger = AssetLotLedger()
    loop._fill_state = {}
    loop.no_loss_guard_violations = 0
    return loop


def test_task_7_14_fill_delta_and_ledger_mutation_are_causal(tmp_path):
    store = SQLiteStateStore(tmp_path / "state.db")
    try:
        loop = _loop(store)
        lot = loop.ledger.register_buy("buy-1", "TQQQ", 100.0, 10.0, 0.05)
        first = SimpleNamespace(id="sell-1", filled_qty=4.0, filled_avg_price=105.0)
        cash, proceeds = loop.apply_sell_fill(first, lot, cash=0.0, cost_model=ZeroCostModel())
        assert cash == proceeds == 420.0
        assert lot.shares == 6.0

        second = SimpleNamespace(id="sell-1", filled_qty=10.0, filled_avg_price=105.0)
        cash, proceeds = loop.apply_sell_fill(second, lot, cash=cash, cost_model=ZeroCostModel())
        assert proceeds == 630.0
        assert cash == 1050.0
        assert lot.shares == 0.0

        events = store.load_audit_events()
        assert [event.event_type for event in events] == [
            "ORDER_STATUS", "FILL", "LEDGER_MUTATION",
            "ORDER_STATUS", "FILL", "LEDGER_MUTATION",
        ]
        fills = [event for event in events if event.event_type == "FILL"]
        assert fills[0].payload["incremental_fill_qty"] == 4.0
        assert fills[0].payload["cumulative_filled_qty"] == 4.0
        assert fills[1].payload["incremental_fill_qty"] == 6.0
        assert fills[1].payload["cumulative_filled_qty"] == 10.0
        assert events[-1].payload["quantity_delta"] == -6.0
    finally:
        store.close()


def test_task_7_14_duplicate_fill_does_not_mutate_ledger_twice(tmp_path):
    store = SQLiteStateStore(tmp_path / "state.db")
    try:
        loop = _loop(store)
        lot = loop.ledger.register_buy("buy-1", "TQQQ", 100.0, 10.0, 0.05)
        order = SimpleNamespace(id="sell-1", filled_qty=4.0, filled_avg_price=105.0)
        loop.apply_sell_fill(order, lot, cash=0.0, cost_model=ZeroCostModel())
        loop.apply_sell_fill(order, lot, cash=0.0, cost_model=ZeroCostModel())
        assert lot.shares == 6.0
        fills = [event for event in store.load_audit_events() if event.event_type == "FILL"]
        assert len(fills) == 1
    finally:
        store.close()
