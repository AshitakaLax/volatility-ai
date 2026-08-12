import os
import tempfile

import pytest

from src.exceptions import ReconciliationError
from src.ledger import AssetLotLedger
from src.persistence import SQLiteStateStore


def test_restart_reconstructs_open_lot_exactly():
    with tempfile.TemporaryDirectory() as td:
        path = os.path.join(td, "state.sqlite")
        store = SQLiteStateStore(path)
        ledger = AssetLotLedger()
        lot = ledger.register_buy("order-1", "TQQQ", 100.0, 10.0, 0.05)
        store.persist_ledger(ledger)
        store.close()

        reopened = SQLiteStateStore(path)
        recovered = reopened.load_open_lots()
        assert len(recovered.open_lots) == 1
        restored = recovered.open_lots[0]
        assert restored.order_id == lot.order_id
        assert restored.symbol == lot.symbol
        assert restored.buy_price == lot.buy_price
        assert restored.shares == lot.shares
        assert restored.target_sell_price == lot.target_sell_price
        reopened.close()


def test_processed_event_is_idempotent():
    with tempfile.TemporaryDirectory() as td:
        store = SQLiteStateStore(os.path.join(td, "state.sqlite"))
        first, revision1 = store.mark_processed("event-1")
        second, revision2 = store.mark_processed("event-1")
        assert first is True
        assert second is False
        assert revision2 == revision1
        store.close()


def test_position_mismatch_requires_reconciliation():
    with tempfile.TemporaryDirectory() as td:
        store = SQLiteStateStore(os.path.join(td, "state.sqlite"))
        ledger = AssetLotLedger()
        ledger.register_buy("order-1", "TQQQ", 100.0, 10.0, 0.05)
        with pytest.raises(ReconciliationError):
            store.reconcile_position(ledger, 9.0)
        store.close()


def test_snapshot_persistence_is_atomic_and_recoverable():
    with tempfile.TemporaryDirectory() as td:
        path = os.path.join(td, "state.sqlite")
        store = SQLiteStateStore(path)
        ledger = AssetLotLedger()
        ledger.register_buy("order-1", "TQQQ", 100.0, 10.0, 0.05)
        store.persist_ledger(ledger)
        ledger.open_lots[0].shares = 6.0
        store.persist_ledger(ledger)
        recovered = store.load_open_lots()
        assert recovered.open_lots[0].shares == 6.0
        store.close()
