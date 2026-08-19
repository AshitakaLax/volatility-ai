from src.audit import AuditEvent
from src.ledger import AssetLotLedger
from src.persistence import SQLiteStateStore
from src.fill_cursor import FillCursor


def _audit(event_id, event_type, payload):
    return AuditEvent(
        event_id=event_id,
        timestamp="2026-01-01T00:00:00+00:00",
        event_type=event_type,
        schema_version=1,
        deployment_id="test-deployment",
        payload=payload,
    )


def test_fill_transaction_commits_processed_cursor_ledger_and_audit(tmp_path):
    store = SQLiteStateStore(tmp_path / "state.db")
    try:
        ledger = AssetLotLedger()
        lot = ledger.register_buy("buy-1", "TQQQ", 100.0, 10.0, 105.0)
        cursor = FillCursor()
        event_id = "fill:sell-1:4"
        events = [
            _audit(event_id + ":status", "ORDER_STATUS", {"intent_id": "sell-1", "broker_order_id": "sell-1", "status": "PARTIALLY_FILLED", "cumulative_filled_qty": 4.0}),
            _audit(event_id, "FILL", {"fill_id": event_id, "order_id": "sell-1", "incremental_fill_qty": 4.0, "cumulative_filled_qty": 4.0, "price": 105.0, "fees": 0.0, "timestamp": "2026-01-01T00:00:00+00:00"}),
            _audit(event_id + ":ledger", "LEDGER_MUTATION", {"event_id": event_id, "lot_id": "buy-1", "mutation_type": "close_lot", "quantity_delta": -4.0, "cash_delta": 420.0}),
        ]
        claimed, _ = store.apply_fill_transaction(
            event_id=event_id, ledger=ledger, order_id="sell-1",
            cumulative_qty=4.0, cumulative_notional=420.0, cursor=cursor,
            mutation=lambda: ledger.close_lot(lot, sell_qty=4.0, execution_price=105.0, completed=False),
            audit_events=events,
        )
        assert claimed
        assert lot.shares == 6.0
        assert cursor.cumulative_qty == 4.0
        assert store.load_fill_cursor("sell-1") == (4.0, 420.0)
        assert [e.event_type for e in store.load_audit_events()] == ["ORDER_STATUS", "FILL", "LEDGER_MUTATION"]
        assert store.mark_processed(event_id)[0] is False
    finally:
        store.close()


def test_fill_transaction_rolls_back_claim_ledger_cursor_and_audit(tmp_path):
    store = SQLiteStateStore(tmp_path / "state.db")
    try:
        ledger = AssetLotLedger()
        lot = ledger.register_buy("buy-1", "TQQQ", 100.0, 10.0, 105.0)
        cursor = FillCursor()
        event_id = "fill:sell-1:4"
        events = [_audit(event_id, "FILL", {"fill_id": event_id})]

        def failing_mutation():
            ledger.close_lot(lot, sell_qty=4.0, execution_price=105.0, completed=False)
            raise RuntimeError("simulated crash")

        try:
            store.apply_fill_transaction(
                event_id=event_id, ledger=ledger, order_id="sell-1",
                cumulative_qty=4.0, cumulative_notional=420.0, cursor=cursor,
                mutation=failing_mutation, audit_events=events,
            )
        except RuntimeError:
            pass
        assert lot.shares == 10.0
        assert cursor.cumulative_qty == 0.0
        assert store.load_fill_cursor("sell-1") is None
        assert store.mark_processed(event_id)[0] is True
        assert store.load_audit_events() == []
    finally:
        store.close()
