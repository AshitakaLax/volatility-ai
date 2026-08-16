import pytest

from src.audit import (
    AuditEvent,
    MarketContextPayload,
    generate_event_id,
)


def test_generate_event_id():
    eid = generate_event_id()
    assert isinstance(eid, str)
    assert len(eid) > 0


def test_audit_event_envelope():
    payload = MarketContextPayload(
        timestamp="2026-01-01T00:00:00Z",
        symbol="TQQQ",
        OHLCV={"open": 100, "high": 105, "low": 99, "close": 104, "volume": 1000},
        bar_event_id="1",
    )
    event = AuditEvent(
        event_id="SIM-000001",
        timestamp="2026-01-01T00:00:00Z",
        event_type="MARKET_CONTEXT",
        schema_version=1,
        deployment_id="test",
        payload=payload.__dict__,
        sequence=1,
    )
    assert event.event_type == "MARKET_CONTEXT"
    assert event.sequence == 1
    assert event.event_id == "SIM-000001"


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
