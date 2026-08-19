"""
Durable audit/event schema. Task 7.14.

Ordinary logs cannot reconstruct why an order existed, what the
strategy saw, what risk decided, and what actually filled. This is the
canonical audit trail.

Shared event-ID contract: the event ID here is the SAME identifier
Task 4.10 defines for idempotency and Task 7.4 checks before
resubmitting -- src.idempotency.compute_decision_id, implementing
architecture_overview.md 2.5. This task does NOT define a second
scheme; 4.10 landed first and this adopts it, exactly as the contract
requires. Verified by a test that cross-references one event across
both subsystems.

Scope (Non-goals): this RECORDS events. It does not generate the
idempotency mechanism producing their IDs (Task 4.10) nor the ledger
persistence they correlate against (Task 7.3) -- it reuses both.

Durability (step 4): "durable" means committed, not buffered. Writes
go through Task 7.3's LedgerStore, whose _transaction() wraps a real
SQLite commit, and record_event returns only after that commit
acknowledges. Callers that must not proceed until an event is durable
therefore simply call it synchronously.

Ordering (step 3): determinism comes from a monotonically increasing
per-stream sequence number, NOT timestamps. Two events written in the
same clock tick still order correctly, and a clock adjustment cannot
reorder history.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum

from src.exceptions import PersistenceError
from src.secrets import redact_secrets

logger = logging.getLogger("Optimizer")

AUDIT_SCHEMA_VERSION = 1


class EventType(StrEnum):
    """The event types step 2 requires recording."""

    MARKET_CONTEXT = "MARKET_CONTEXT"
    STRATEGY_DECISION = "STRATEGY_DECISION"
    RISK_DECISION = "RISK_DECISION"
    ORDER_INTENT = "ORDER_INTENT"
    ORDER_STATUS = "ORDER_STATUS"
    FILL = "FILL"
    LEDGER_MUTATION = "LEDGER_MUTATION"
    RECONCILIATION = "RECONCILIATION"
    RISK_HALT = "RISK_HALT"
    STARTUP = "STARTUP"
    SHUTDOWN = "SHUTDOWN"


# Required payload fields per event type, from the "Required event
# payload schemas" block. Enforced at write time so an incomplete
# audit record is impossible rather than merely discouraged -- an
# audit trail you discover is incomplete after an incident is worth
# very little.
REQUIRED_PAYLOAD_FIELDS: dict = {
    EventType.MARKET_CONTEXT: (
        "timestamp",
        "symbol",
        "open",
        "high",
        "low",
        "close",
        "volume",
        "bar_event_id",
    ),
    EventType.STRATEGY_DECISION: ("decision_id", "strategy_id", "proposed_action", "parameters"),
    EventType.RISK_DECISION: ("decision_id", "allowed", "reason", "limits"),
    EventType.ORDER_INTENT: (
        "intent_id",
        "decision_id",
        "symbol",
        "side",
        "quantity",
        "limit_price",
    ),
    EventType.ORDER_STATUS: ("intent_id", "broker_order_id", "status", "cumulative_filled_qty"),
    EventType.FILL: (
        "fill_id",
        "order_id",
        "incremental_fill_qty",
        "cumulative_filled_qty",
        "price",
        "fees",
        "timestamp",
    ),
    EventType.LEDGER_MUTATION: (
        "event_id",
        "lot_id",
        "mutation_type",
        "quantity_delta",
        "cash_delta",
    ),
    EventType.RECONCILIATION: ("correlation_id", "local_state", "broker_state", "resolution"),
    EventType.RISK_HALT: ("halt_reason", "previous_state", "new_state"),
    EventType.STARTUP: ("deployment_id", "runtime_state", "reconciliation_result"),
    EventType.SHUTDOWN: ("deployment_id", "runtime_state", "reconciliation_result"),
}

_AUDIT_SCHEMA = """
CREATE TABLE IF NOT EXISTS audit_events (
    event_id       TEXT NOT NULL,
    stream_id      TEXT NOT NULL,
    sequence       INTEGER NOT NULL,
    timestamp      TEXT NOT NULL,
    event_type     TEXT NOT NULL,
    schema_version INTEGER NOT NULL,
    deployment_id  TEXT NOT NULL,
    strategy_id    TEXT NOT NULL,
    correlation_id TEXT,
    payload        TEXT NOT NULL,
    PRIMARY KEY (stream_id, event_id)
);
CREATE INDEX IF NOT EXISTS idx_audit_stream_seq ON audit_events (stream_id, sequence);
CREATE INDEX IF NOT EXISTS idx_audit_correlation ON audit_events (correlation_id);
"""


@dataclass(frozen=True)
class AuditEvent:
    """Immutable audit record (step 1). Frozen so a recorded event
    cannot be edited after the fact -- an audit trail that can be
    rewritten is not an audit trail."""

    event_id: str
    stream_id: str
    sequence: int
    timestamp: str
    event_type: EventType
    deployment_id: str
    strategy_id: str
    payload: dict
    correlation_id: str | None = None
    schema_version: int = AUDIT_SCHEMA_VERSION

    def to_dict(self) -> dict:
        """JSON-serializable form of this event, for export or inspection."""
        return {
            "event_id": self.event_id,
            "stream_id": self.stream_id,
            "sequence": self.sequence,
            "timestamp": self.timestamp,
            "event_type": self.event_type.value,
            "schema_version": self.schema_version,
            "deployment_id": self.deployment_id,
            "strategy_id": self.strategy_id,
            "correlation_id": self.correlation_id,
            "payload": self.payload,
        }


class AuditLog:
    """Durable, append-only event log backed by Task 7.3's LedgerStore.

    State ownership: this owns the audit_events table and the
    per-stream sequence counter. It never mutates ledger lots, order
    state, or the circuit breaker -- it only records what those
    components report.
    """

    def __init__(self, store, deployment_id: str, strategy_id: str, stream_id: str = "default"):
        """Attach an append-only event log to a durable store.

        Creates the audit tables if absent, so construction is safe to
        repeat. stream_id partitions independent sequences; separate
        streams number their events independently.
        """
        self.store = store
        self.deployment_id = deployment_id
        self.strategy_id = strategy_id
        self.stream_id = stream_id
        with store._transaction() as conn:
            conn.executescript(_AUDIT_SCHEMA)

    def _next_sequence(self, conn) -> int:
        """Monotonic per-stream sequence (step 3). Derived from the
        durable table, not an in-memory counter, so it keeps
        increasing correctly across a restart."""
        row = conn.execute(
            "SELECT COALESCE(MAX(sequence), 0) AS s FROM audit_events WHERE stream_id = ?",
            (self.stream_id,),
        ).fetchone()
        return row["s"] + 1

    def record_event(
        self,
        event_id: str,
        event_type: EventType,
        payload: dict,
        correlation_id: str | None = None,
        timestamp: datetime | None = None,
    ) -> AuditEvent | None:
        """Append one event, durably.

        Returns the recorded AuditEvent, or None if this event_id was
        already recorded on this stream -- duplicates are a no-op
        rather than a second row, enforced by the PRIMARY KEY so the
        guarantee is the database's rather than the caller's.

        Returns only after the write is COMMITTED (step 4): callers
        that must not proceed until an event is durable get that by
        calling this synchronously.

        Secrets are redacted from the payload before writing (Task
        6.4) -- an audit trail is exactly the kind of long-lived
        artifact a credential must never end up in.
        """
        missing = [f for f in REQUIRED_PAYLOAD_FIELDS.get(event_type, ()) if f not in payload]
        if missing:
            raise PersistenceError(
                f"{event_type.value} audit payload is missing required field(s): {missing}. "
                "An incomplete audit record is refused rather than written."
            )

        safe_payload = redact_secrets(payload)
        try:
            serialized = json.dumps(
                safe_payload, sort_keys=True, separators=(",", ":"), allow_nan=False
            )
        except (TypeError, ValueError) as e:
            raise PersistenceError(
                f"{event_type.value} audit payload is not JSON-serializable: {e}"
            ) from e

        when = (timestamp or datetime.now(UTC)).isoformat()
        with self.store._transaction() as conn:
            existing = conn.execute(
                "SELECT 1 FROM audit_events WHERE stream_id = ? AND event_id = ?",
                (self.stream_id, event_id),
            ).fetchone()
            if existing:
                logger.info(
                    f"Duplicate audit event_id={event_id!r} on stream {self.stream_id!r} -- not re-recording."
                )
                return None

            sequence = self._next_sequence(conn)
            conn.execute(
                "INSERT INTO audit_events (event_id, stream_id, sequence, timestamp, event_type, "
                "schema_version, deployment_id, strategy_id, correlation_id, payload) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    event_id,
                    self.stream_id,
                    sequence,
                    when,
                    event_type.value,
                    AUDIT_SCHEMA_VERSION,
                    self.deployment_id,
                    self.strategy_id,
                    correlation_id,
                    serialized,
                ),
            )

        return AuditEvent(
            event_id=event_id,
            stream_id=self.stream_id,
            sequence=sequence,
            timestamp=when,
            event_type=event_type,
            deployment_id=self.deployment_id,
            strategy_id=self.strategy_id,
            payload=safe_payload,
            correlation_id=correlation_id,
        )

    # --- reading ---

    def _row_to_event(self, row) -> AuditEvent:
        """Rebuild an AuditEvent from a database row, deserializing the
        JSON payload back into a dict."""
        return AuditEvent(
            event_id=row["event_id"],
            stream_id=row["stream_id"],
            sequence=row["sequence"],
            timestamp=row["timestamp"],
            event_type=EventType(row["event_type"]),
            deployment_id=row["deployment_id"],
            strategy_id=row["strategy_id"],
            payload=json.loads(row["payload"]),
            correlation_id=row["correlation_id"],
            schema_version=row["schema_version"],
        )

    def read_stream(self) -> list:
        """Every event on this stream, ordered by SEQUENCE (step 3) --
        never by timestamp, which cannot break ties within a clock tick
        and can be moved by a clock adjustment."""
        rows = self.store._conn.execute(
            "SELECT * FROM audit_events WHERE stream_id = ? ORDER BY sequence ASC",
            (self.stream_id,),
        ).fetchall()
        return [self._row_to_event(r) for r in rows]

    def causal_chain(self, correlation_id: str) -> list:
        """Every event sharing a correlation ID, in sequence order --
        the causal chain from market context through decision, risk,
        order, fill, and ledger mutation."""
        rows = self.store._conn.execute(
            "SELECT * FROM audit_events WHERE stream_id = ? AND correlation_id = ? ORDER BY sequence ASC",
            (self.stream_id, correlation_id),
        ).fetchall()
        return [self._row_to_event(r) for r in rows]

    def has_event(self, event_id: str) -> bool:
        """Whether this event id is already recorded on this stream."""
        row = self.store._conn.execute(
            "SELECT 1 FROM audit_events WHERE stream_id = ? AND event_id = ?",
            (self.stream_id, event_id),
        ).fetchone()
        return row is not None
