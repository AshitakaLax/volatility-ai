"""Immutable deterministic audit event schema for volatility-ai."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any


# v6.1 shared event-ID contract. Task 4.10, 7.4, and 7.14 must use this
# exact canonicalization rather than independent identifier schemes.
def canonical_event_id(
    *,
    deployment_id: str,
    strategy_id: str,
    symbol: str,
    market_event_id: str | int,
    decision_type: str,
    sequence_number: int,
) -> str:
    """Return the v6.1 canonical SHA-256 event/decision identifier.

    The canonical object is serialized as UTF-8 JSON with sorted keys,
    compact separators, and NaN/Infinity rejected. The resulting digest is
    lowercase hexadecimal.
    """
    if sequence_number < 0:
        raise ValueError("sequence_number must be non-negative")
    canonical = {
        "deployment_id": str(deployment_id),
        "strategy_id": str(strategy_id),
        "symbol": str(symbol),
        "market_event_id": str(market_event_id),
        "decision_type": str(decision_type),
        "sequence_number": int(sequence_number),
    }
    encoded = json.dumps(
        canonical,
        ensure_ascii=False,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def canonical_order_intent_id(
    *,
    deployment_id: str,
    strategy_id: str,
    symbol: str,
    market_event_id: str | int,
    sequence_number: int,
) -> str:
    """Return the shared v6.1 ID for an ORDER_INTENT event.

    This is a named wrapper around ``canonical_event_id`` so Task 4.10's
    internally generated order-intent identity and Task 7.14's audit record
    cannot silently drift into separate identifier schemes.
    """
    return canonical_event_id(
        deployment_id=deployment_id,
        strategy_id=strategy_id,
        symbol=symbol,
        market_event_id=market_event_id,
        decision_type="ORDER_INTENT",
        sequence_number=sequence_number,
    )


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
