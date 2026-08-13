import pytest

from src.exceptions import ReconciliationError
from src.ledger import AssetLotLedger
from src.reconciliation import BrokerReconciler


def _ledger(qty=10.0):
    ledger = AssetLotLedger()
    ledger.register_buy("lot-1", "TQQQ", 100.0, qty, 0.05)
    return ledger


def test_matching_position_allows_resume():
    reconciler = BrokerReconciler(position_reader=lambda symbol: 10.0)
    result = reconciler.reconcile("TQQQ", _ledger())
    assert result.matched is True
    assert result.reason == "matched"


def test_position_mismatch_fails_closed():
    reconciler = BrokerReconciler(position_reader=lambda symbol: 7.0)
    with pytest.raises(ReconciliationError):
        reconciler.reconcile("TQQQ", _ledger())


def test_open_order_mismatch_fails_closed():
    reconciler = BrokerReconciler(
        position_reader=lambda symbol: 10.0,
        open_orders_reader=lambda symbol: 1,
    )
    with pytest.raises(ReconciliationError):
        reconciler.reconcile("TQQQ", _ledger(), local_open_orders=0)


def test_reconciliation_does_not_mutate_ledger():
    ledger = _ledger()
    reconciler = BrokerReconciler(position_reader=lambda symbol: 10.0)
    reconciler.reconcile("TQQQ", ledger)
    assert ledger.open_share_count == 10.0
    assert ledger.total_open_cost_basis == pytest.approx(1000.0)
