"""
Task 7.14 acceptance tests.

Acceptance criteria:
1. A test run can reconstruct the causal chain from market decision ->
   risk decision -> order -> fill -> ledger mutation.
2. Duplicate events do not create duplicate side effects.
3. Audit schema versions are explicit and forward-compatible.
4. Event IDs in this schema are the SAME IDs used by Task 4.10's
   idempotency check, verifiable by cross-referencing a single event
   across both.
"""

import json
import sqlite3
from datetime import datetime, timezone

import pytest

from src.audit import AUDIT_SCHEMA_VERSION, REQUIRED_PAYLOAD_FIELDS, AuditLog, EventType
from src.exceptions import PersistenceError
from src.idempotency import ProcessedEventStore, compute_decision_id
from src.persistence import LedgerStore

DECISION_KWARGS = dict(
    deployment_id="deploy-1", strategy_id="fixed", symbol="TQQQ",
    market_event_id="bar-2024-01-01T14:30:00Z", decision_type="grid_buy", sequence_number=1,
)


@pytest.fixture
def store(tmp_path):
    s = LedgerStore(str(tmp_path / "ledger.db"))
    yield s
    s.close()


@pytest.fixture
def audit(store):
    return AuditLog(store, deployment_id="deploy-1", strategy_id="fixed")


def _payload(event_type: EventType, **overrides) -> dict:
    """A minimally valid payload for each event type, so tests exercise
    the real required-field contract."""
    base = {f: f"{f}-value" for f in REQUIRED_PAYLOAD_FIELDS[event_type]}
    numeric_fields = {
        "open", "high", "low", "close", "volume", "quantity", "limit_price",
        "cumulative_filled_qty", "incremental_fill_qty", "price", "fees",
        "quantity_delta", "cash_delta",
    }
    for f in list(base):
        if f in numeric_fields:
            base[f] = 1.0
    if "allowed" in base:
        base["allowed"] = True
    if "parameters" in base:
        base["parameters"] = {"allocation_pct": 0.05}
    if "limits" in base:
        base["limits"] = {"max_concurrent_lots": 3}
    base.update(overrides)
    return base


def test_full_causal_chain_is_reconstructable(audit):
    decision_id = compute_decision_id(**DECISION_KWARGS)
    correlation = decision_id  # the decision ties the whole chain together

    audit.record_event(f"{decision_id}:ctx", EventType.MARKET_CONTEXT,
                       _payload(EventType.MARKET_CONTEXT), correlation_id=correlation)
    audit.record_event(decision_id, EventType.STRATEGY_DECISION,
                       _payload(EventType.STRATEGY_DECISION, decision_id=decision_id),
                       correlation_id=correlation)
    audit.record_event(f"{decision_id}:risk", EventType.RISK_DECISION,
                       _payload(EventType.RISK_DECISION, decision_id=decision_id),
                       correlation_id=correlation)
    audit.record_event(f"{decision_id}:intent", EventType.ORDER_INTENT,
                       _payload(EventType.ORDER_INTENT, decision_id=decision_id),
                       correlation_id=correlation)
    audit.record_event(f"{decision_id}:fill", EventType.FILL,
                       _payload(EventType.FILL), correlation_id=correlation)
    audit.record_event(f"{decision_id}:ledger", EventType.LEDGER_MUTATION,
                       _payload(EventType.LEDGER_MUTATION), correlation_id=correlation)

    chain = audit.causal_chain(correlation)
    assert [e.event_type for e in chain] == [
        EventType.MARKET_CONTEXT,
        EventType.STRATEGY_DECISION,
        EventType.RISK_DECISION,
        EventType.ORDER_INTENT,
        EventType.FILL,
        EventType.LEDGER_MUTATION,
    ]
    assert [e.sequence for e in chain] == sorted(e.sequence for e in chain)


def test_causal_chain_excludes_unrelated_events(audit):
    audit.record_event("a", EventType.STRATEGY_DECISION, _payload(EventType.STRATEGY_DECISION), correlation_id="chain-1")
    audit.record_event("b", EventType.STRATEGY_DECISION, _payload(EventType.STRATEGY_DECISION), correlation_id="chain-2")
    assert [e.event_id for e in audit.causal_chain("chain-1")] == ["a"]


def test_duplicate_event_id_records_only_once(audit):
    payload = _payload(EventType.STRATEGY_DECISION)
    first = audit.record_event("evt-1", EventType.STRATEGY_DECISION, payload)
    second = audit.record_event("evt-1", EventType.STRATEGY_DECISION, payload)

    assert first is not None
    assert second is None, "A duplicate must be a no-op, not a second row"
    assert len(audit.read_stream()) == 1


def test_duplicate_does_not_advance_the_sequence(audit):
    audit.record_event("evt-1", EventType.STRATEGY_DECISION, _payload(EventType.STRATEGY_DECISION))
    audit.record_event("evt-1", EventType.STRATEGY_DECISION, _payload(EventType.STRATEGY_DECISION))
    third = audit.record_event("evt-2", EventType.STRATEGY_DECISION, _payload(EventType.STRATEGY_DECISION))
    assert third.sequence == 2, "A rejected duplicate must not consume a sequence number"


def test_duplicates_survive_a_restart(tmp_path):
    db = str(tmp_path / "ledger.db")
    store1 = LedgerStore(db)
    AuditLog(store1, "deploy-1", "fixed").record_event(
        "evt-1", EventType.STRATEGY_DECISION, _payload(EventType.STRATEGY_DECISION)
    )
    store1.close()

    store2 = LedgerStore(db)
    audit2 = AuditLog(store2, "deploy-1", "fixed")
    assert audit2.has_event("evt-1")
    assert audit2.record_event("evt-1", EventType.STRATEGY_DECISION, _payload(EventType.STRATEGY_DECISION)) is None
    assert len(audit2.read_stream()) == 1
    store2.close()


def test_every_event_carries_an_explicit_schema_version(audit):
    event = audit.record_event("evt-1", EventType.STRATEGY_DECISION, _payload(EventType.STRATEGY_DECISION))
    assert event.schema_version == AUDIT_SCHEMA_VERSION
    assert audit.read_stream()[0].schema_version == AUDIT_SCHEMA_VERSION


def test_unknown_extra_payload_fields_are_preserved_for_forward_compatibility(audit):
    payload = _payload(EventType.STRATEGY_DECISION, some_future_field={"nested": [1, 2, 3]})
    audit.record_event("evt-1", EventType.STRATEGY_DECISION, payload)
    stored = audit.read_stream()[0]
    assert stored.payload["some_future_field"] == {"nested": [1, 2, 3]}


def test_payloads_are_json_serializable(audit):
    event = audit.record_event("evt-1", EventType.FILL, _payload(EventType.FILL))
    json.dumps(event.to_dict())  # must not raise


def test_non_serializable_payload_is_refused(audit):
    payload = _payload(EventType.STRATEGY_DECISION, parameters=object())
    with pytest.raises(PersistenceError, match="JSON-serializable"):
        audit.record_event("evt-1", EventType.STRATEGY_DECISION, payload)
    assert audit.read_stream() == []


def test_nan_payload_is_refused(audit):
    payload = _payload(EventType.FILL, price=float("nan"))
    with pytest.raises(PersistenceError):
        audit.record_event("evt-1", EventType.FILL, payload)


def test_audit_event_ids_are_the_same_ids_task_4_10_uses(store, audit):
    """Cross-references ONE event across both subsystems, exactly as
    the acceptance criterion asks."""
    decision_id = compute_decision_id(**DECISION_KWARGS)

    # Task 4.10's idempotency subsystem.
    idempotency = ProcessedEventStore()
    idempotency.apply_once(decision_id, lambda: "applied", event_kind="strategy_decision")

    # This task's audit subsystem, same ID.
    audit.record_event(decision_id, EventType.STRATEGY_DECISION,
                       _payload(EventType.STRATEGY_DECISION, decision_id=decision_id))

    assert idempotency.has_processed(decision_id)
    assert audit.has_event(decision_id)
    assert audit.read_stream()[0].event_id == decision_id


def test_the_same_id_also_gates_task_7_4_duplicate_protection(store, audit):
    from src.duplicate_order_guard import DuplicateOrderGuard

    decision_id = compute_decision_id(**DECISION_KWARGS)
    submissions = []
    guard = DuplicateOrderGuard(store)
    guard.submit_once(decision_id, lambda cid: submissions.append(cid) or "order-1")
    audit.record_event(decision_id, EventType.STRATEGY_DECISION,
                       _payload(EventType.STRATEGY_DECISION, decision_id=decision_id))

    # One scheme across all three subsystems.
    assert store.has_processed(decision_id)
    assert audit.has_event(decision_id)
    guard.submit_once(decision_id, lambda cid: submissions.append(cid))
    assert len(submissions) == 1


@pytest.mark.parametrize("event_type", list(EventType))
def test_every_event_type_has_a_required_field_contract(event_type):
    assert event_type in REQUIRED_PAYLOAD_FIELDS
    assert REQUIRED_PAYLOAD_FIELDS[event_type], f"{event_type.value} has no required fields defined"


@pytest.mark.parametrize("event_type", list(EventType))
def test_a_valid_payload_is_accepted_for_every_event_type(audit, event_type):
    event = audit.record_event(f"evt-{event_type.value}", event_type, _payload(event_type))
    assert event is not None


@pytest.mark.parametrize("event_type", list(EventType))
def test_an_incomplete_payload_is_refused_for_every_event_type(audit, event_type):
    payload = _payload(event_type)
    dropped = REQUIRED_PAYLOAD_FIELDS[event_type][0]
    del payload[dropped]
    with pytest.raises(PersistenceError, match="missing required field"):
        audit.record_event("evt-x", event_type, payload)


def test_fill_payload_distinguishes_incremental_from_cumulative(audit):
    # The schema block is explicit that incremental_fill_qty must be
    # derived from cumulative and never confused with requested qty.
    fields = REQUIRED_PAYLOAD_FIELDS[EventType.FILL]
    assert "incremental_fill_qty" in fields
    assert "cumulative_filled_qty" in fields

    event = audit.record_event(
        "evt-fill", EventType.FILL,
        _payload(EventType.FILL, incremental_fill_qty=3.0, cumulative_filled_qty=7.0),
    )
    assert event.payload["incremental_fill_qty"] == 3.0
    assert event.payload["cumulative_filled_qty"] == 7.0


def test_ordering_is_by_sequence_not_timestamp(audit):
    same_instant = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
    for i in range(5):
        audit.record_event(f"evt-{i}", EventType.STRATEGY_DECISION,
                           _payload(EventType.STRATEGY_DECISION), timestamp=same_instant)

    stream = audit.read_stream()
    assert [e.event_id for e in stream] == [f"evt-{i}" for i in range(5)]
    assert len({e.timestamp for e in stream}) == 1, "All share one timestamp -- only sequence can order them"
    assert [e.sequence for e in stream] == [1, 2, 3, 4, 5]


def test_a_backwards_clock_cannot_reorder_history(audit):
    audit.record_event("first", EventType.STRATEGY_DECISION, _payload(EventType.STRATEGY_DECISION),
                       timestamp=datetime(2024, 1, 2, tzinfo=timezone.utc))
    audit.record_event("second", EventType.STRATEGY_DECISION, _payload(EventType.STRATEGY_DECISION),
                       timestamp=datetime(2024, 1, 1, tzinfo=timezone.utc))  # clock went backwards
    assert [e.event_id for e in audit.read_stream()] == ["first", "second"]


def test_sequence_continues_across_a_restart(tmp_path):
    db = str(tmp_path / "ledger.db")
    store1 = LedgerStore(db)
    AuditLog(store1, "deploy-1", "fixed").record_event(
        "evt-1", EventType.STRATEGY_DECISION, _payload(EventType.STRATEGY_DECISION)
    )
    store1.close()

    store2 = LedgerStore(db)
    audit2 = AuditLog(store2, "deploy-1", "fixed")
    event = audit2.record_event("evt-2", EventType.STRATEGY_DECISION, _payload(EventType.STRATEGY_DECISION))
    assert event.sequence == 2, "Sequence must keep increasing across a restart"
    store2.close()


def test_streams_have_independent_sequences(store):
    a = AuditLog(store, "deploy-1", "fixed", stream_id="stream-a")
    b = AuditLog(store, "deploy-1", "fixed", stream_id="stream-b")
    assert a.record_event("e1", EventType.STRATEGY_DECISION, _payload(EventType.STRATEGY_DECISION)).sequence == 1
    assert b.record_event("e1", EventType.STRATEGY_DECISION, _payload(EventType.STRATEGY_DECISION)).sequence == 1
    assert len(a.read_stream()) == 1 and len(b.read_stream()) == 1


def test_events_are_durable_before_record_event_returns(tmp_path):
    db = str(tmp_path / "ledger.db")
    store = LedgerStore(db)
    audit = AuditLog(store, "deploy-1", "fixed")
    audit.record_event("evt-1", EventType.STRATEGY_DECISION, _payload(EventType.STRATEGY_DECISION))

    # A SEPARATE connection can already see it -- proving it was
    # committed, not merely buffered in-process, before return.
    other = sqlite3.connect(db)
    count = other.execute("SELECT COUNT(*) FROM audit_events WHERE event_id = 'evt-1'").fetchone()[0]
    other.close()
    store.close()
    assert count == 1


def test_secrets_never_reach_the_audit_trail(audit):
    payload = _payload(EventType.STRATEGY_DECISION, api_key="sk-LEAKCANARY", parameters={"password": "hunter2"})
    audit.record_event("evt-1", EventType.STRATEGY_DECISION, payload)
    stored = json.dumps(audit.read_stream()[0].payload)
    assert "sk-LEAKCANARY" not in stored
    assert "hunter2" not in stored


def test_events_are_immutable(audit):
    import dataclasses

    event = audit.record_event("evt-1", EventType.STRATEGY_DECISION, _payload(EventType.STRATEGY_DECISION))
    with pytest.raises(dataclasses.FrozenInstanceError):
        event.payload = {"tampered": True}


def test_deployment_and_strategy_identity_are_recorded(audit):
    event = audit.record_event("evt-1", EventType.STRATEGY_DECISION, _payload(EventType.STRATEGY_DECISION))
    assert event.deployment_id == "deploy-1"
    assert event.strategy_id == "fixed"
