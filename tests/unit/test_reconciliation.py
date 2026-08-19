"""
Task 7.11 acceptance tests.

Acceptance criteria:
1. Matching local/broker state returns READY.
2. Known recoverable differences converge to broker-confirmed state.
3. Ambiguous differences halt new buys and produce an actionable
   diagnostic naming the specific unexplained delta.

Every row of the 2.7 reconciliation decision table has a test.
"""

import pytest

from src.ledger import AssetLotLedger
from src.order_lifecycle import OrderRecord, OrderState
from src.persistence import LedgerStore
from src.reconciliation import BrokerSnapshot, Reconciler, ReconciliationOutcome
from src.risk_manager import CircuitBreaker, CircuitBreakerState


@pytest.fixture
def store(tmp_path):
    s = LedgerStore(str(tmp_path / "ledger.db"))
    yield s
    s.close()


def _seed_one_open_lot(store, shares=10.0, symbol="TQQQ"):
    ledger = AssetLotLedger()
    lot = ledger.register_buy("lot-1", symbol, 50.0, shares, 0.01)
    store.record_open_lot(lot)
    return ledger, lot


def _local_order(
    client_order_id="cid-1", state=OrderState.ACCEPTED, filled_qty=0.0, requested_qty=10.0
):
    order = OrderRecord(client_order_id=client_order_id, requested_qty=requested_qty, symbol="TQQQ")
    order.state = state
    order.filled_qty = filled_qty
    return order


def _broker_order(state=OrderState.ACCEPTED, filled_qty=0.0, avg_fill_price=50.0, symbol="TQQQ"):
    return {
        "state": state,
        "filled_qty": filled_qty,
        "avg_fill_price": avg_fill_price,
        "symbol": symbol,
    }


def test_matching_state_returns_ready(store):
    _seed_one_open_lot(store, shares=10.0)
    report = Reconciler(store).reconcile(
        BrokerSnapshot(positions={"TQQQ": 10.0}, orders={}, cash=1000.0),
        local_orders={},
        expected_cash=1000.0,
    )
    assert report.outcome is ReconciliationOutcome.READY
    assert report.ready
    assert report.discrepancies == []
    assert "READY" in report.diagnostic()


def test_ready_when_no_positions_and_no_orders(store):
    assert Reconciler(store).reconcile(BrokerSnapshot()).ready


def test_ready_does_not_halt(store):
    breaker = CircuitBreaker()
    _seed_one_open_lot(store, shares=10.0)
    Reconciler(store, circuit_breaker=breaker).reconcile(BrokerSnapshot(positions={"TQQQ": 10.0}))
    assert breaker.state is CircuitBreakerState.ACTIVE


def test_broker_order_with_a_known_decision_id_is_imported(store):
    # Unambiguous: it carries OUR stable client order ID (Task 7.4).
    store.record_processed_event("cid-known", "order_submission")
    _seed_one_open_lot(store, shares=10.0)

    report = Reconciler(store).reconcile(
        BrokerSnapshot(
            positions={"TQQQ": 10.0}, orders={"cid-known": _broker_order(filled_qty=4.0)}
        ),
        local_orders={},
    )
    assert report.ready
    assert any("Imported broker order" in r for r in report.repairs_applied)


def test_broker_order_with_no_known_decision_is_not_imported(store):
    # A trade placed outside this system: ambiguous, must halt.
    _seed_one_open_lot(store, shares=10.0)
    report = Reconciler(store).reconcile(
        BrokerSnapshot(
            positions={"TQQQ": 10.0}, orders={"cid-stranger": _broker_order(filled_qty=4.0)}
        ),
        local_orders={},
    )
    assert not report.ready
    assert "UNKNOWN_BROKER_ORDER" in [d.kind for d in report.discrepancies]
    assert "cid-stranger" in report.diagnostic()
    assert "outside this system" in report.diagnostic()


def test_live_local_order_absent_at_broker_halts(store):
    report = Reconciler(store).reconcile(
        BrokerSnapshot(orders={}),
        local_orders={"cid-1": _local_order(state=OrderState.ACCEPTED)},
    )
    assert not report.ready
    assert "ORDER_ABSENT_AT_BROKER" in [d.kind for d in report.discrepancies]
    assert "cid-1" in report.diagnostic()


def test_settled_local_order_absent_at_broker_is_expected_not_a_discrepancy(store):
    # A filled order aging out of the broker's query window is normal.
    report = Reconciler(store).reconcile(
        BrokerSnapshot(orders={}),
        local_orders={"cid-1": _local_order(state=OrderState.FILLED, filled_qty=10.0)},
    )
    assert report.ready


def test_position_quantity_mismatch_halts_and_never_invents_a_fill(store):
    _seed_one_open_lot(store, shares=10.0)
    report = Reconciler(store).reconcile(BrokerSnapshot(positions={"TQQQ": 7.0}))
    assert not report.ready
    assert "POSITION_MISMATCH" in [d.kind for d in report.discrepancies]
    diag = report.diagnostic()
    assert "10.0" in diag and "7.0" in diag, "Diagnostic must name the specific delta"
    assert "not inventing a fill" in diag.lower()


def test_position_only_at_broker_is_not_imported(store):
    _seed_one_open_lot(store, shares=10.0)
    report = Reconciler(store).reconcile(BrokerSnapshot(positions={"TQQQ": 10.0, "SPXL": 5.0}))
    assert not report.ready
    assert "POSITION_ONLY_AT_BROKER" in [d.kind for d in report.discrepancies]
    assert "SPXL" in report.diagnostic()


def test_position_only_local_does_not_delete_local_lots(store):
    _seed_one_open_lot(store, shares=10.0)
    report = Reconciler(store).reconcile(BrokerSnapshot(positions={}))
    assert not report.ready
    assert "POSITION_ONLY_LOCAL" in [d.kind for d in report.discrepancies]
    # Reconciliation reports; it never repairs by deletion.
    assert len(store.load_ledger().open_lots) == 1


def test_cash_mismatch_halts(store):
    report = Reconciler(store).reconcile(BrokerSnapshot(cash=900.0), expected_cash=1000.0)
    assert not report.ready
    assert "CASH_MISMATCH" in [d.kind for d in report.discrepancies]
    diag = report.diagnostic()
    assert "900.00" in diag and "1000.00" in diag and "-100.00" in diag


def test_cash_within_a_cent_is_not_a_mismatch(store):
    assert Reconciler(store).reconcile(BrokerSnapshot(cash=1000.005), expected_cash=1000.0).ready


def test_cash_is_skipped_when_not_supplied(store):
    assert Reconciler(store).reconcile(BrokerSnapshot(cash=None), expected_cash=1000.0).ready
    assert Reconciler(store).reconcile(BrokerSnapshot(cash=999.0), expected_cash=None).ready


def test_fill_regression_halts_and_never_auto_reverses(store):
    report = Reconciler(store).reconcile(
        BrokerSnapshot(orders={"cid-1": _broker_order(filled_qty=4.0)}),
        local_orders={"cid-1": _local_order(state=OrderState.PARTIALLY_FILLED, filled_qty=7.0)},
    )
    assert not report.ready
    assert "FILL_REGRESSION" in [d.kind for d in report.discrepancies]
    diag = report.diagnostic()
    assert "4.0" in diag and "7.0" in diag
    assert "not reversing" in diag.lower()


def test_broker_confirmed_fill_on_a_known_live_order_is_adopted(store):
    report = Reconciler(store).reconcile(
        BrokerSnapshot(
            orders={"cid-1": _broker_order(state=OrderState.PARTIALLY_FILLED, filled_qty=4.0)}
        ),
        local_orders={"cid-1": _local_order(state=OrderState.ACCEPTED, filled_qty=0.0)},
    )
    assert report.ready, report.diagnostic()
    assert any("adopted broker-confirmed fill" in r for r in report.repairs_applied)
    assert any("0.0 -> 4.0" in r for r in report.repairs_applied)


def test_fill_reported_against_a_locally_terminal_order_is_ambiguous(store):
    report = Reconciler(store).reconcile(
        BrokerSnapshot(orders={"cid-1": _broker_order(state=OrderState.FILLED, filled_qty=10.0)}),
        local_orders={"cid-1": _local_order(state=OrderState.CANCELED, filled_qty=4.0)},
    )
    assert not report.ready
    assert "FILL_ON_TERMINAL_ORDER" in [d.kind for d in report.discrepancies]


def test_locally_terminal_but_broker_still_live_is_flagged(store):
    report = Reconciler(store).reconcile(
        BrokerSnapshot(orders={"cid-1": _broker_order(state=OrderState.ACCEPTED, filled_qty=0.0)}),
        local_orders={"cid-1": _local_order(state=OrderState.CANCELED, filled_qty=0.0)},
    )
    assert not report.ready
    assert "STALE_TERMINAL_STATE" in [d.kind for d in report.discrepancies]


def test_ambiguous_discrepancy_halts_new_buys(store):
    breaker = CircuitBreaker()
    _seed_one_open_lot(store, shares=10.0)
    Reconciler(store, circuit_breaker=breaker).reconcile(BrokerSnapshot(positions={"TQQQ": 7.0}))
    assert breaker.state is CircuitBreakerState.HALTED_NEW_BUYS
    assert breaker.allows_new_buys is False
    assert "reconciliation required" in breaker.reason


def test_reconciliation_halt_requires_a_manual_reset(store):
    breaker = CircuitBreaker()
    _seed_one_open_lot(store, shares=10.0)
    reconciler = Reconciler(store, circuit_breaker=breaker)
    reconciler.reconcile(BrokerSnapshot(positions={"TQQQ": 7.0}))

    # Even a subsequent CLEAN pass must not auto-clear the halt.
    reconciler.reconcile(BrokerSnapshot(positions={"TQQQ": 10.0}))
    assert breaker.allows_new_buys is False, "A clean pass must not silently clear a halt"

    breaker.manual_reset(operator="alice")
    assert breaker.allows_new_buys is True


def test_reconciliation_halt_persists_across_restart(tmp_path):
    db = str(tmp_path / "ledger.db")
    store1 = LedgerStore(db)
    _seed_one_open_lot(store1, shares=10.0)
    Reconciler(store1, circuit_breaker=CircuitBreaker(store=store1)).reconcile(
        BrokerSnapshot(positions={"TQQQ": 7.0})
    )
    store1.close()

    store2 = LedgerStore(db)
    assert CircuitBreaker(store=store2).allows_new_buys is False
    store2.close()


def test_reconciliation_never_forces_liquidation(store):
    breaker = CircuitBreaker()
    _seed_one_open_lot(store, shares=10.0)
    Reconciler(store, circuit_breaker=breaker).reconcile(BrokerSnapshot(positions={"TQQQ": 7.0}))
    # Halted, but every local lot is untouched -- no emergency exit.
    assert len(store.load_ledger().open_lots) == 1
    assert breaker.state is CircuitBreakerState.HALTED_NEW_BUYS


def test_alerts_route_to_a_sink_when_provided(store):
    alerts = []
    _seed_one_open_lot(store, shares=10.0)
    Reconciler(store, alert_sink=alerts.append).reconcile(BrokerSnapshot(positions={"TQQQ": 7.0}))
    assert len(alerts) == 1
    assert alerts[0]["event"] == "reconciliation_required"
    assert alerts[0]["discrepancies"][0]["kind"] == "POSITION_MISMATCH"


def test_alerts_are_logged_when_no_sink_is_wired(store, caplog):
    _seed_one_open_lot(store, shares=10.0)
    with caplog.at_level("ERROR", logger="Optimizer"):
        Reconciler(store).reconcile(BrokerSnapshot(positions={"TQQQ": 7.0}))
    assert any("RECONCILIATION REQUIRED" in r.getMessage() for r in caplog.records)


def test_reconciler_has_no_way_to_manufacture_a_transaction(store):
    reconciler = Reconciler(store)
    for forbidden in (
        "create_fill",
        "invent_lot",
        "force_balance",
        "adjust_cash",
        "synthesize_trade",
    ):
        assert not hasattr(reconciler, forbidden), (
            f"Reconciler must not expose {forbidden!r} -- it may never manufacture a "
            "transaction merely to make totals match"
        )


def test_multiple_discrepancies_are_all_reported(store):
    _seed_one_open_lot(store, shares=10.0)
    report = Reconciler(store).reconcile(
        BrokerSnapshot(
            positions={"TQQQ": 7.0, "SPXL": 3.0},
            orders={"cid-stranger": _broker_order(filled_qty=1.0)},
            cash=900.0,
        ),
        local_orders={},
        expected_cash=1000.0,
    )
    kinds = {d.kind for d in report.discrepancies}
    assert {
        "POSITION_MISMATCH",
        "POSITION_ONLY_AT_BROKER",
        "UNKNOWN_BROKER_ORDER",
        "CASH_MISMATCH",
    } <= kinds
