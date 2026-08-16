"""Immutable deterministic audit event schema for volatility-ai."""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass
from typing import Any


# Task 4.10 owns the shared event-ID contract. AuditEvent deliberately accepts
# the producer-supplied ID rather than deriving a second ID scheme here.
def generate_event_id() -> str:
    """Generate an ID for event producers that need a new local event ID.

    Existing Task 4.10 producers remain authoritative for event IDs. In
    particular, simulation fill IDs come from the OMS fill ID and must be
    passed into AuditEvent unchanged.
    """
    return str(uuid.uuid4())


@dataclass(frozen=True)
class AuditEvent:
    """Immutable envelope for all canonical audit events."""
    event_id: str
    timestamp: str
    event_type: str
    schema_version: int
    deployment_id: str
    payload: dict[str, Any]
    sequence: int = 0

    def __post_init__(self) -> None:
        if not self.event_id:
            raise ValueError("event_id must not be empty")
        if not self.timestamp:
            raise ValueError("timestamp must not be empty")
        if not self.event_type:
            raise ValueError("event_type must not be empty")
        if self.schema_version < 1:
            raise ValueError("schema_version must be positive")
        if self.sequence < 0:
            raise ValueError("sequence must be non-negative")
        if not isinstance(self.payload, dict):
            raise TypeError("audit payload must be a dictionary")
        # Fail at the event boundary instead of allowing a non-JSON payload to
        # reach durable persistence.
        json.dumps(
            self.payload,
            ensure_ascii=False,
            allow_nan=False,
            sort_keys=True,
            separators=(",", ":"),
        )


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
