"""
Task 7.4 acceptance tests (L5).

1. Deliberately reconnecting the live loop mid-session (simulated) does
   not result in a duplicate order for a trigger already acted on
   before the reconnect.
2. The idempotency key scheme is confirmed to actually map onto a real
   alpaca-py deduplication mechanism, not assumed to exist.

Plus the idempotency contract's explicitly required ambiguous case:
local state says SUBMITTED while broker state says FILLED.
"""

import subprocess
import sys
import textwrap
import uuid
from datetime import datetime, timezone
from pathlib import Path

import pytest

from src.duplicate_order_guard import DecisionState, DuplicateOrderGuard
from src.exceptions import ReconciliationError
from src.idempotency import compute_decision_id
from src.persistence import LedgerStore

REPO_ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture
def store(tmp_path):
    s = LedgerStore(str(tmp_path / "ledger.db"))
    yield s
    s.close()


DECISION_KWARGS = dict(
    deployment_id="deploy-1",
    strategy_id="fixed",
    symbol="TQQQ",
    market_event_id="bar-2024-01-01T14:30:00Z",
    decision_type="grid_buy",
    sequence_number=1,
)


def test_decision_id_is_deterministic_across_calls():
    assert compute_decision_id(**DECISION_KWARGS) == compute_decision_id(**DECISION_KWARGS)


def test_decision_id_is_sha256_lowercase_hex():
    digest = compute_decision_id(**DECISION_KWARGS)
    assert len(digest) == 64
    assert digest == digest.lower()
    int(digest, 16)  # valid hex


@pytest.mark.parametrize(
    "field,value",
    [
        ("deployment_id", "deploy-2"),
        ("strategy_id", "rsi"),
        ("symbol", "SPXL"),
        ("market_event_id", "bar-2024-01-02T14:30:00Z"),
        ("decision_type", "grid_sell"),
        ("sequence_number", 2),
    ],
)
def test_changing_any_identity_field_changes_the_decision_id(field, value):
    other = dict(DECISION_KWARGS)
    other[field] = value
    assert compute_decision_id(**DECISION_KWARGS) != compute_decision_id(**other)


def test_decision_id_stable_across_processes():
    # Must not depend on hash randomization, time, or object identity.
    script = textwrap.dedent(
        f"""
        import sys
        sys.path.insert(0, {str(REPO_ROOT)!r})
        from src.idempotency import compute_decision_id
        print(compute_decision_id(**{DECISION_KWARGS!r}))
        """
    )
    result = subprocess.run(
        [sys.executable, "-c", script],
        capture_output=True,
        text=True,
        timeout=60,
        env={"PYTHONHASHSEED": "random", "PATH": "/usr/bin:/bin"},
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == compute_decision_id(**DECISION_KWARGS)


def test_separator_in_a_field_is_rejected_not_silently_ambiguous():
    bad = dict(DECISION_KWARGS)
    bad["symbol"] = "TQ|QQ"
    with pytest.raises(ValueError, match="separator"):
        compute_decision_id(**bad)


def test_negative_sequence_number_rejected():
    bad = dict(DECISION_KWARGS)
    bad["sequence_number"] = -1
    with pytest.raises(ValueError):
        compute_decision_id(**bad)


def test_alpaca_sdk_genuinely_supports_client_order_id():
    from alpaca.trading.client import TradingClient
    from alpaca.trading.models import Order
    from alpaca.trading.requests import LimitOrderRequest, MarketOrderRequest

    assert "client_order_id" in MarketOrderRequest.model_fields
    assert "client_order_id" in LimitOrderRequest.model_fields
    assert "client_order_id" in Order.model_fields
    assert hasattr(TradingClient, "get_order_by_client_id"), (
        "alpaca-py must expose lookup-by-client-order-id for this dedup scheme to be real"
    )


def test_a_real_decision_id_is_accepted_as_an_alpaca_client_order_id():
    from alpaca.trading.enums import OrderSide, TimeInForce
    from alpaca.trading.requests import MarketOrderRequest

    decision_id = compute_decision_id(**DECISION_KWARGS)
    request = MarketOrderRequest(
        symbol="TQQQ",
        qty=1,
        side=OrderSide.BUY,
        time_in_force=TimeInForce.DAY,
        client_order_id=decision_id,
    )
    assert request.client_order_id == decision_id


def test_replayed_decision_does_not_submit_a_second_order(store):
    guard = DuplicateOrderGuard(store)
    decision_id = compute_decision_id(**DECISION_KWARGS)
    submissions = []

    def submit(cid):
        submissions.append(cid)
        return f"broker-order-for-{cid[:8]}"

    first = guard.submit_once(decision_id, submit)
    second = guard.submit_once(decision_id, submit)  # the replay

    assert len(submissions) == 1, "The broker must be called exactly once for one decision"
    assert first.submitted_now is True
    assert second.submitted_now is False
    assert second.order_ref == first.order_ref


def test_duplicate_protection_survives_a_process_restart(tmp_path):
    db = str(tmp_path / "ledger.db")
    decision_id = compute_decision_id(**DECISION_KWARGS)
    submissions = []

    def submit(cid):
        submissions.append(cid)
        return "broker-order-1"

    store1 = LedgerStore(db)
    DuplicateOrderGuard(store1).submit_once(decision_id, submit)
    store1.close()  # simulate the disconnect/crash

    store2 = LedgerStore(db)  # reconnect: fresh process, same store
    outcome = DuplicateOrderGuard(store2).submit_once(decision_id, submit)
    store2.close()

    assert len(submissions) == 1, "Reconnect must not re-submit an already-acted-on decision"
    assert outcome.submitted_now is False
    assert outcome.order_ref == "broker-order-1"


def test_a_genuinely_new_decision_still_submits(store):
    guard = DuplicateOrderGuard(store)
    submissions = []

    def submit(cid):
        submissions.append(cid)
        return f"order-{len(submissions)}"

    guard.submit_once(compute_decision_id(**DECISION_KWARGS), submit)
    other = dict(DECISION_KWARGS)
    other["sequence_number"] = 2
    guard.submit_once(compute_decision_id(**other), submit)

    assert len(submissions) == 2, "A genuinely different decision must still be submitted"


def test_decision_id_is_passed_to_the_broker_as_client_order_id(store):
    guard = DuplicateOrderGuard(store)
    decision_id = compute_decision_id(**DECISION_KWARGS)
    seen = {}

    def submit(cid):
        seen["client_order_id"] = cid
        return "order-1"

    guard.submit_once(decision_id, submit)
    assert seen["client_order_id"] == decision_id


def test_crash_between_claim_and_submission_still_blocks_a_duplicate(tmp_path):
    db = str(tmp_path / "ledger.db")
    decision_id = compute_decision_id(**DECISION_KWARGS)

    store1 = LedgerStore(db)
    guard1 = DuplicateOrderGuard(store1)

    def submit_then_crash(cid):
        raise RuntimeError("network died mid-submission")

    with pytest.raises(RuntimeError):
        guard1.submit_once(decision_id, submit_then_crash)
    store1.close()

    store2 = LedgerStore(db)
    guard2 = DuplicateOrderGuard(store2)
    # The claim landed before the broker call, so the decision is
    # SUBMITTED-with-unknown-outcome, NOT free to blindly re-submit.
    assert guard2.state_of(decision_id) is DecisionState.SUBMITTED
    store2.close()


def _alpaca_order(client_order_id: str):
    from alpaca.trading.enums import OrderSide, OrderStatus, TimeInForce
    from alpaca.trading.models import Order

    now = datetime(2024, 1, 1, tzinfo=timezone.utc)
    return Order(
        id=str(uuid.UUID(int=99)),
        client_order_id=client_order_id,
        created_at=now,
        updated_at=now,
        submitted_at=now,
        status=OrderStatus.FILLED,
        qty="10.0",
        filled_qty="10.0",
        filled_avg_price="150.00",
        side=OrderSide.BUY,
        time_in_force=TimeInForce.DAY,
        extended_hours=False,
    )


def test_local_submitted_but_broker_filled_adopts_the_broker_order(store):
    """The idempotency contract's explicitly required ambiguous case."""
    guard = DuplicateOrderGuard(store)
    decision_id = compute_decision_id(**DECISION_KWARGS)

    store.record_processed_event(decision_id, "order_submission")  # claimed, no result_ref
    assert guard.state_of(decision_id) is DecisionState.SUBMITTED

    resolved = guard.resolve_ambiguous_submission(decision_id, lambda cid: _alpaca_order(cid))

    assert resolved == decision_id  # adopted the broker's client_order_id
    assert guard.state_of(decision_id) is DecisionState.ACKNOWLEDGED

    # And now a replay must NOT submit -- broker state was adopted, not re-ordered.
    submissions = []
    outcome = guard.submit_once(decision_id, lambda cid: submissions.append(cid))
    assert submissions == []
    assert outcome.submitted_now is False


def test_local_submitted_and_broker_has_nothing_halts_rather_than_guessing(store):
    guard = DuplicateOrderGuard(store)
    decision_id = compute_decision_id(**DECISION_KWARGS)
    store.record_processed_event(decision_id, "order_submission")

    with pytest.raises(ReconciliationError, match="UNKNOWN"):
        guard.resolve_ambiguous_submission(decision_id, lambda cid: None)


def test_state_of_reports_new_for_an_unseen_decision(store):
    guard = DuplicateOrderGuard(store)
    assert guard.state_of("never-seen") is DecisionState.NEW


def test_oms_accepts_and_echoes_client_order_id():
    from src.order_management_system import OrderManagementSystem

    oms = OrderManagementSystem(mode="SIMULATION")
    decision_id = compute_decision_id(**DECISION_KWARGS)
    buy = oms.execute_buy("TQQQ", 1000.0, 50.0, client_order_id=decision_id)
    sell = oms.execute_sell("TQQQ", 10.0, 55.0, client_order_id=decision_id)
    assert buy["client_order_id"] == decision_id
    assert sell["client_order_id"] == decision_id


def test_oms_client_order_id_is_optional_for_existing_callers():
    from src.order_management_system import OrderManagementSystem

    oms = OrderManagementSystem(mode="SIMULATION")
    result = oms.execute_buy("TQQQ", 1000.0, 50.0)  # no client_order_id
    assert result["client_order_id"] is None
    assert result["filled_qty"] == pytest.approx(20.0)
