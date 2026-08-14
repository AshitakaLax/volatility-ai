"""Immutable deterministic audit event schema for volatility-ai."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Any


def generate_event_id() -> str:
    """Generate a canonical UUIDv4 event identifier.
    
    This fulfills the shared event-ID contract for Tasks 4.10, 7.4, and 7.14.
    """
    return str(uuid.uuid4())


@dataclass(frozen=True)
class AuditEvent:
    """Envelope for all deterministic audit events."""
    event_id: str
    timestamp: str
    event_type: str
    schema_version: int
    deployment_id: str
    payload: dict[str, Any]
    sequence: int = 0


@dataclass(frozen=True)
class MarketContextPayload:
    timestamp: str
    symbol: str
    OHLCV: dict[str, float]
    bar_event_id: str | int


@dataclass(frozen=True)
class StrategyDecisionPayload:
    decision_id: str
    strategy_id: str
    proposed_action: str
    parameters: dict[str, Any]


@dataclass(frozen=True)
class RiskDecisionPayload:
    decision_id: str
    allowed: bool
    reason: str
    relevant_limits: dict[str, Any]


@dataclass(frozen=True)
class OrderIntentPayload:
    intent_id: str
    decision_id: str
    symbol: str
    side: str
    quantity: float
    limit_price: float | None = None


@dataclass(frozen=True)
class OrderStatusPayload:
    intent_id: str
    broker_order_id: str
    status: str
    cumulative_filled_qty: float


@dataclass(frozen=True)
class FillPayload:
    fill_id: str
    order_id: str
    incremental_fill_qty: float
    cumulative_filled_qty: float
    price: float
    fees: float
    timestamp: str


@dataclass(frozen=True)
class LedgerMutationPayload:
    event_id: str
    lot_id: str
    mutation_type: str
    quantity_delta: float
    cash_delta: float


@dataclass(frozen=True)
class ReconciliationPayload:
    correlation_id: str
    local_state_summary: dict[str, Any]
    broker_state_summary: dict[str, Any]
    resolution: str


@dataclass(frozen=True)
class RiskHaltPayload:
    halt_reason: str
    previous_state: str
    new_state: str


@dataclass(frozen=True)
class StartupShutdownPayload:
    deployment_id: str
    runtime_state: str
    reconciliation_result: str | None = None
