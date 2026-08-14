import pytest
from src.audit import (
    AuditEvent,
    MarketContextPayload,
    StrategyDecisionPayload,
    RiskDecisionPayload,
    OrderIntentPayload,
    OrderStatusPayload,
    FillPayload,
    LedgerMutationPayload,
    ReconciliationPayload,
    RiskHaltPayload,
    StartupShutdownPayload,
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
        bar_event_id="1"
    )
    event = AuditEvent(
        event_id=generate_event_id(),
        timestamp="2026-01-01T00:00:00Z",
        event_type="MARKET_CONTEXT",
        schema_version=1,
        deployment_id="test",
        payload=payload.__dict__
    )
    assert event.event_type == "MARKET_CONTEXT"
    assert event.sequence == 0
