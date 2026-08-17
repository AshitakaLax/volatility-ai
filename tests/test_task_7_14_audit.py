import pytest

from src.audit import (
    AuditEvent,
    MarketContextPayload,
    canonical_event_id,
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
    payload = MarketContextPayload(
        timestamp="2026-01-01T00:00:00Z",
        symbol="TQQQ",
        OHLCV={"open": 100, "high": 105, "low": 99, "close": 104, "volume": 1000},
        bar_event_id="1",
    )
    event = AuditEvent(
        event_id=canonical_event_id(
            deployment_id="test",
            strategy_id="grid-v6",
            symbol="TQQQ",
            market_event_id="1",
            decision_type="MARKET_CONTEXT",
            sequence_number=1,
        ),
        timestamp="2026-01-01T00:00:00Z",
        event_type="MARKET_CONTEXT",
        schema_version=1,
        deployment_id="test",
        payload=payload.__dict__,
        sequence=1,
    )
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
    event = AuditEvent(
        event_id="evt-1",
        timestamp="2026-01-01T00:00:00Z",
        event_type="TEST",
        schema_version=1,
        deployment_id="dep",
        payload={"x": 1},
        sequence=1,
    )
    with pytest.raises(Exception):
        event.event_type = "OTHER"
