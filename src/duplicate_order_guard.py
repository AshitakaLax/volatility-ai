"""
Idempotent reconnect / duplicate-order protection. Task 7.4 (L5).

If the live loop reconnects after a network blip or restart, it must
not re-submit an order for a grid trigger it already acted on.

Idempotency-key contract: the identifier here is the SAME one Task
4.10 consumes and Task 7.14 records --
src/idempotency.compute_decision_id(), implementing
architecture_overview.md 2.5's canonical scheme. It is derived purely
from the decision's own identity (deployment/strategy/symbol/market
event/type/sequence), never from wall-clock time or randomness, so a
replayed decision recomputes to the identical ID across reconnects
and restarts. A newly generated ID for a replayed decision is
forbidden and structurally impossible here.

Broker-side mechanism CONFIRMED against the installed alpaca-py, not
assumed (this task requires exactly that, and requires stopping and
reporting if the SDK lacks the facility):
  - MarketOrderRequest/LimitOrderRequest accept client_order_id
    (Optional[str])
  - Order returns client_order_id as a required field
  - TradingClient.get_order_by_client_id(...) provides lookup
  - a 64-char SHA-256 hex digest is accepted as a client_order_id
So the decision_id is used directly as the Alpaca client_order_id,
giving broker-side deduplication in addition to the local guard.

Claim-then-submit ordering: the durable claim is written BEFORE the
broker call, never after. A crash between the two leaves a claimed
decision with result_ref=NULL, which recovery reads as "submitted,
outcome unknown" and routes to reconciliation -- rather than the
reverse ordering, where a crash after submission but before the write
would let a restart submit the same order twice.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Callable, Optional

from src.exceptions import ReconciliationError


class DecisionState(str, Enum):
    NEW = "NEW"                    # never seen; safe to submit
    SUBMITTED = "SUBMITTED"        # claimed, but no broker reference recorded (outcome unknown)
    ACKNOWLEDGED = "ACKNOWLEDGED"  # claimed and a broker order reference is on file


@dataclass(frozen=True)
class SubmissionOutcome:
    decision_id: str
    state: DecisionState
    order_ref: Optional[str]
    submitted_now: bool  # False means a prior submission was reused, not repeated


class DuplicateOrderGuard:
    """Wraps a LedgerStore (Task 7.3) to make order submission
    idempotent per decision_id.

    Owns no order state of its own -- the durable store is the single
    source of truth, so the guarantee survives process death rather
    than living in a process-local set.
    """

    def __init__(self, store):
        self.store = store

    def state_of(self, decision_id: str) -> DecisionState:
        if not self.store.has_processed(decision_id):
            return DecisionState.NEW
        return (
            DecisionState.ACKNOWLEDGED
            if self.store.get_event_result_ref(decision_id)
            else DecisionState.SUBMITTED
        )

    def submit_once(
        self,
        decision_id: str,
        submit_fn: Callable[[str], object],
        event_kind: str = "order_submission",
    ) -> SubmissionOutcome:
        """Submit at most once per decision_id, ever.

        submit_fn receives the decision_id (to pass through as the
        broker's client_order_id) and returns a broker order reference.
        It is NOT called at all when the decision was already claimed --
        that is the duplicate-order protection.
        """
        existing_state = self.state_of(decision_id)
        if existing_state is not DecisionState.NEW:
            return SubmissionOutcome(
                decision_id=decision_id,
                state=existing_state,
                order_ref=self.store.get_event_result_ref(decision_id),
                submitted_now=False,
            )

        # Claim durably FIRST -- see module docstring on ordering.
        self.store.record_processed_event(decision_id, event_kind)
        order_ref = submit_fn(decision_id)
        if order_ref is not None:
            self.store.set_event_result_ref(decision_id, str(order_ref))
        return SubmissionOutcome(
            decision_id=decision_id,
            state=DecisionState.ACKNOWLEDGED if order_ref is not None else DecisionState.SUBMITTED,
            order_ref=str(order_ref) if order_ref is not None else None,
            submitted_now=True,
        )

    def resolve_ambiguous_submission(self, decision_id: str, broker_lookup: Callable[[str], object]):
        """Resolve the local-says-SUBMITTED / broker-says-FILLED case
        the idempotency contract explicitly requires handling.

        Local state says a decision was claimed but carries no broker
        reference (a crash landed between claim and acknowledgement).
        The broker is queried by the SAME decision_id used as
        client_order_id. Per architecture_overview.md 2.7, broker state
        is authoritative for what actually exists -- so a found order
        is adopted and recorded, never re-submitted. If the broker
        cannot find it either, the decision is genuinely UNKNOWN and
        raises rather than being silently retried or silently dropped.
        """
        state = self.state_of(decision_id)
        if state is not DecisionState.SUBMITTED:
            return self.store.get_event_result_ref(decision_id)

        broker_order = broker_lookup(decision_id)
        if broker_order is None:
            raise ReconciliationError(
                f"Decision {decision_id!r} is locally SUBMITTED but the broker has no order "
                "with that client_order_id. Marking UNKNOWN -- halt affected trading and "
                "reconcile manually; not auto-resubmitting (that risks a duplicate) and not "
                "auto-clearing (that risks losing a real position)."
            )
        order_ref = getattr(broker_order, "client_order_id", None) or getattr(broker_order, "id", None)
        self.store.set_event_result_ref(decision_id, str(order_ref))
        return str(order_ref)
