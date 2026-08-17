import pytest
from datetime import datetime, timezone
from types import SimpleNamespace

from src.audit import (
    AuditEvent,
    MarketContextPayload,
    canonical_event_id,
)
from src.live_execution import LiveExecutionLoop, RuntimeState
from src.market_context import MarketContext
from src.persistence import SQLiteStateStore


def _market_event(sequence: int) -> AuditEvent:
    payload = MarketContextPayload(
        timestamp="2026-01-01T00:00:00Z",
        symbol="TQQQ",
        OHLCV={"open": 100, "high": 105, "low": 99, "close": 104, "volume": 1000},
        bar_event_id="1",
    )
    return AuditEvent(
        event_id=canonical_event_id(
            deployment_id="test",
            strategy_id="grid-v6",
            symbol="TQQQ",
            market_event_id="1",
            decision_type="MARKET_CONTEXT",
            sequence_number=sequence,
        ),
        timestamp="2026-01-01T00:00:00Z",
        event_type="MARKET_CONTEXT",
        schema_version=1,
        deployment_id="test",
        payload=payload.__dict__,
        sequence=sequence,
    )


def test_canonical_event_id_is_deterministic():
    kwargs = {
        "deployment_id": "dep-1",
        "strategy_id": "grid-v6",
        "symbol": "TQQQ",
        "market_event_id": "bar-001",
        "decision_type": "STRATEGY_DECISION",
        "sequence_number": 7,
    }
    first = canonical_event_id(**kwargs)
    second = canonical_event_id(**kwargs)
    assert first == second
    assert len(first) == 64
    assert first == first.lower()
    int(first, 16)


def test_canonical_event_id_changes_when_identity_component_changes():
    base = {
        "deployment_id": "dep-1",
        "strategy_id": "grid-v6",
        "symbol": "TQQQ",
        "market_event_id": "bar-001",
        "decision_type": "STRATEGY_DECISION",
        "sequence_number": 7,
    }
    original = canonical_event_id(**base)
    changed = canonical_event_id(**{**base, "sequence_number": 8})
    assert changed != original


def test_canonical_event_id_rejects_negative_sequence():
    with pytest.raises(ValueError):
        canonical_event_id(
            deployment_id="dep",
            strategy_id="strategy",
            symbol="TQQQ",
            market_event_id="bar",
            decision_type="STRATEGY_DECISION",
            sequence_number=-1,
        )


def test_audit_event_envelope():
    event = _market_event(1)
    assert event.event_type == "MARKET_CONTEXT"
    assert event.sequence == 1
    assert len(event.event_id) == 64


def test_audit_event_rejects_non_json_payload():
    with pytest.raises((ValueError, TypeError)):
        AuditEvent(
            event_id="evt-1",
            timestamp="2026-01-01T00:00:00Z",
            event_type="MARKET_CONTEXT",
            schema_version=1,
            deployment_id="test",
            payload={"bad": float("nan")},
            sequence=1,
        )


def test_audit_event_rejects_invalid_sequence_and_schema_version():
    with pytest.raises(ValueError):
        AuditEvent("evt-1", "2026-01-01T00:00:00Z", "TEST", 1, "dep", {}, -1)
    with pytest.raises(ValueError):
        AuditEvent("evt-1", "2026-01-01T00:00:00Z", "TEST", 0, "dep", {}, 1)


def test_audit_event_is_immutable():
    event = _market_event(1)
    with pytest.raises(Exception):
        event.event_type = "OTHER"


def test_duplicate_audit_event_is_idempotent(tmp_path):
    store = SQLiteStateStore(tmp_path / "state.db")
    try:
        event = _market_event(1)
        first_revision = store.record_audit(event)
        second_revision = store.record_audit(event)
        assert second_revision == first_revision
        assert store.load_audit_events() == [event]
    finally:
        store.close()


def test_audit_sequence_and_history_survive_restart(tmp_path):
    db = tmp_path / "state.db"
    first = _market_event(1)
    second = AuditEvent(
        event_id=canonical_event_id(
            deployment_id="test",
            strategy_id="grid-v6",
            symbol="TQQQ",
            market_event_id="2",
            decision_type="STRATEGY_DECISION",
            sequence_number=2,
        ),
        timestamp="2026-01-01T00:01:00Z",
        event_type="STRATEGY_DECISION",
        schema_version=1,
        deployment_id="test",
        payload={"decision_id": "decision-1", "strategy_id": "grid-v6", "proposed_action": "BUY", "parameters": {}},
        sequence=2,
    )
    store = SQLiteStateStore(db)
    store.record_audit(first)
    store.record_audit(second)
    store.close()

    reopened = SQLiteStateStore(db)
    try:
        events = reopened.load_audit_events()
        assert [event.sequence for event in events] == [1, 2]
        assert [event.event_id for event in events] == [first.event_id, second.event_id]
    finally:
        reopened.close()


def test_audit_sequence_mismatch_is_rejected(tmp_path):
    store = SQLiteStateStore(tmp_path / "state.db")
    try:
        store.record_audit(_market_event(1))
        with pytest.raises(Exception):
            store.record_audit(_market_event(3))
        assert [event.sequence for event in store.load_audit_events()] == [1]
    finally:
        store.close()


def test_record_audit_builder_owns_sequence_atomically(tmp_path):
    store = SQLiteStateStore(tmp_path / "state.db")
    try:
        seen = []

        def build(sequence: int) -> AuditEvent:
            seen.append(sequence)
            return _market_event(sequence)

        event, revision = store.record_audit_builder(build)
        assert seen == [1]
        assert event.sequence == 1
        assert revision > 0
        assert store.load_audit_events() == [event]
    finally:
        store.close()


def test_record_audit_builder_assigns_next_sequence_after_restart(tmp_path):
    db = tmp_path / "state.db"
    first = SQLiteStateStore(db)
    try:
        first_event, _ = first.record_audit_builder(lambda sequence: _market_event(sequence))
        assert first_event.sequence == 1
    finally:
        first.close()

    reopened = SQLiteStateStore(db)
    try:
        second_event, _ = reopened.record_audit_builder(
            lambda sequence: AuditEvent(
                event_id=canonical_event_id(
                    deployment_id="test",
                    strategy_id="grid-v6",
                    symbol="TQQQ",
                    market_event_id="2",
                    decision_type="STRATEGY_DECISION",
                    sequence_number=sequence,
                ),
                timestamp="2026-01-01T00:01:00Z",
                event_type="STRATEGY_DECISION",
                schema_version=1,
                deployment_id="test",
                payload={
                    "decision_id": "decision-1",
                    "strategy_id": "grid-v6",
                    "proposed_action": "BUY",
                    "parameters": {},
                },
                sequence=sequence,
            )
        )
        assert second_event.sequence == 2
        assert [event.sequence for event in reopened.load_audit_events()] == [1, 2]
    finally:
        reopened.close()


def test_record_audit_builder_rejects_non_next_sequence_without_partial_write(tmp_path):
    store = SQLiteStateStore(tmp_path / "state.db")
    try:
        store.record_audit(_market_event(1))

        def invalid_builder(sequence: int) -> AuditEvent:
            event = _market_event(sequence)
            return AuditEvent(
                event_id=event.event_id,
                timestamp=event.timestamp,
                event_type=event.event_type,
                schema_version=event.schema_version,
                deployment_id=event.deployment_id,
                payload=event.payload,
                sequence=sequence + 1,
            )

        with pytest.raises(Exception):
            store.record_audit_builder(invalid_builder)
        assert [event.sequence for event in store.load_audit_events()] == [1]
    finally:
        store.close()


def test_task_7_14_reconstructs_market_to_strategy_to_risk_chain(tmp_path):
    """The live decision path emits a durable, sequence-ordered causal chain."""
    store = SQLiteStateStore(tmp_path / "state.db")
    try:
        loop = LiveExecutionLoop.__new__(LiveExecutionLoop)
        loop.config = SimpleNamespace(
            deployment_id="dep-test",
            backtest=SimpleNamespace(symbol="TQQQ"),
            strategy=SimpleNamespace(strategy_id="grid-v6"),
        )
        loop.state_store = store
        loop.runtime_state = RuntimeState.READY
        loop._started = True
        loop.reconciliation_required = False
        loop.circuit_store = None
        loop.circuit_breaker = SimpleNamespace(halted=False, evaluate=lambda drawdown: False)
        loop.risk_manager = SimpleNamespace(
            clamp_trade_value=lambda proposed, equity, cash, open_lot_count: proposed,
            max_concurrent_lots=5,
            max_total_exposure=10000.0,
        )
        loop.strategy = SimpleNamespace(
            record_tick=lambda context: None,
            _check_grid_trigger=lambda context, last_buy_price, step: True,
            calculate_trade_value=lambda context: 500.0,
        )

        context = MarketContext(
            timestamp=datetime(2026, 1, 1, tzinfo=timezone.utc),
            open=100.0,
            high=101.0,
            low=99.0,
            close=100.5,
            cash=10000.0,
            equity=10000.0,
            peak_equity=10000.0,
            drawdown=0.0,
            open_lot_count=0,
            bar_index=42,
            time_of_day_flag=0,
            is_macro_event_day=False,
            macro_surprise_factor=0.0,
        )

        decision = loop.decision_cycle(context, step=1.0, last_buy_price=99.0)
        events = store.load_audit_events()
        assert [event.event_type for event in events] == [
            "MARKET_CONTEXT",
            "STRATEGY_DECISION",
            "RISK_DECISION",
        ]
        assert [event.sequence for event in events] == [1, 2, 3]
        assert all(len(event.event_id) == 64 for event in events)
        assert decision.decision_id == events[1].event_id
        assert events[1].payload["decision_id"] == events[1].event_id
        assert events[2].payload["decision_id"] == events[1].event_id
        assert events[0].payload["bar_event_id"] == "42"
    finally:
        store.close()
