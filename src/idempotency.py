"""
Idempotent event application. Task 4.10.

Duplicate callbacks are possible in reconnecting or replayed systems.
A handler that applies a fill twice can corrupt cash and lot state
even when order submission itself is idempotent. This module defines
and applies the idempotency mechanism -- it does not build the
persistence layer (Task 7.3) or the reconnect/resubmission logic
(Task 7.4) that plug into it, per this task's own Non-goals.

--------------------------------------------------------------------
Idempotency scope contract (implementation_task_specs.md Task 4.10):
this module, Task 7.4 (idempotent reconnect/duplicate-order
protection), and Task 7.14 (durable audit/event schema) must share
ONE event-ID scheme. This task lands before 7.4/7.14, so the scheme
is documented here for them to adopt rather than re-derive:

- SIMULATION-mode fills: the event ID is exactly the "id" field
  OrderManagementSystem.execute_buy/execute_sell already generates
  (e.g. "SIM-000001") -- confirmed stable and unique per simulated
  fill by reading order_management_system.py directly.
- LIVE-mode decisions: RESOLVED by Task 7.4. compute_decision_id()
  below implements architecture_overview.md 2.5's canonical scheme,
  and it is used as the Alpaca client_order_id. Verified against the
  installed alpaca-py rather than assumed: MarketOrderRequest/
  LimitOrderRequest accept an optional client_order_id, Order returns
  it as a required field, TradingClient.get_order_by_client_id
  provides lookup, and a 64-char SHA-256 hex digest is accepted.
- Internally generated pre-submission events (e.g. an order intent
  created before submission): NOT YET APPLICABLE. This codebase has
  no OrderIntent/pre-submission-intent concept yet (that's Task
  4.1/2.5's canonical execution_models.py, explicitly deferred when
  the src/ package was first built -- see src/ledger.py). Once it
  exists, this task's own instruction applies as written: generate a
  UUID at creation time, persist it before dispatch, not after.

Persistence: an in-process set is used here, matching this task's own
statement that it's sufficient for SIMULATION mode ("bounded by the
run's lifetime, no restart to survive"). LIVE mode needs this to
survive restart via Task 7.3's persistence layer, which doesn't exist
in this repo -- per this task's Non-goals, no persistent backend is
built here. ProcessedEventStore takes an injectable `backend`
(anything supporting `in` and `.add`, e.g. a set) specifically so
Task 7.3's real store can be swapped in later without touching this
module's logic; demonstrated in tests via a plain set standing in for
that backend, and via reusing one store across two
ProcessedEventStore instances to simulate "restart, replay an
already-processed ID."
--------------------------------------------------------------------
"""

from __future__ import annotations

import hashlib
import logging
from typing import Callable, Hashable, MutableSet, Optional, TypeVar

logger = logging.getLogger("Optimizer")

T = TypeVar("T")

# architecture_overview.md 2.5's canonical field separator.
_FIELD_SEPARATOR = "|"


def compute_decision_id(
    deployment_id: str,
    strategy_id: str,
    symbol: str,
    market_event_id: str,
    decision_type: str,
    sequence_number: int,
) -> str:
    """Canonical logical decision/event ID -- architecture_overview.md
    2.5's "Event identity" scheme, resolving the LIVE-mode question
    this module's docstring left open for Task 7.4.

    SHA-256 lowercase hex over a UTF-8 canonical serialization of
    deployment_id | strategy_id | symbol | market_event_id |
    decision_type | sequence_number, with explicit separators and no
    insignificant whitespace.

    The same logical decision produces the same ID across reconnects
    and process restarts -- it is derived purely from the decision's
    own identity, never from wall-clock time, randomness, or object
    identity. Generating a fresh ID for a replayed decision is
    forbidden, so nothing here may vary between runs.

    Used as the Alpaca client_order_id (verified: the installed
    alpaca-py accepts a 64-char client_order_id on
    MarketOrderRequest/LimitOrderRequest, returns it on Order, and
    exposes TradingClient.get_order_by_client_id for lookup), and as
    the processed_events key for Task 7.14's audit records.
    """
    if sequence_number < 0:
        raise ValueError(f"sequence_number must be non-negative, got {sequence_number}")
    parts = [
        str(deployment_id), str(strategy_id), str(symbol),
        str(market_event_id), str(decision_type), str(int(sequence_number)),
    ]
    for part in parts:
        if _FIELD_SEPARATOR in part:
            raise ValueError(
                f"decision-ID field {part!r} contains the reserved separator {_FIELD_SEPARATOR!r}, "
                "which would make the serialization ambiguous."
            )
    canonical = _FIELD_SEPARATOR.join(parts)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


class ProcessedEventStore:
    """Applies a given event's effect at most once per event_id."""

    def __init__(self, backend: Optional[MutableSet] = None):
        self._processed: MutableSet = backend if backend is not None else set()
        self._results: dict = {}

    def has_processed(self, event_id: Hashable) -> bool:
        return event_id in self._processed

    def apply_once(self, event_id: Hashable, apply_fn: Callable[[], T], *, event_kind: str = "event") -> Optional[T]:
        """Calls apply_fn() and returns its result exactly once per
        event_id. A repeated event_id returns the cached result from
        the first application without calling apply_fn again -- the
        side effect inside apply_fn (cash/ledger mutation) happens at
        most once. Event IDs are logged on every application,
        including duplicates, satisfying "event IDs are included in
        audit logs" without a separate audit-log module this repo
        doesn't have yet (Task 7.14).

        Only the event_id set itself is part of the injectable
        `backend` (what Task 7.3's real persistence layer would back);
        cached return values live in a local, in-process-only dict.
        After a restart, an event_id can be "already processed" per a
        persisted backend while this process has no locally-cached
        result for it -- that's None here, not a KeyError. The no-op
        guarantee this task requires is about the side effect
        (apply_fn not re-running), not about the return value being
        recoverable across a restart."""
        if event_id in self._processed:
            logger.info(f"Duplicate {event_kind} event_id={event_id!r} -- already applied, skipping re-application.")
            return self._results.get(event_id)
        result = apply_fn()
        self._processed.add(event_id)
        self._results[event_id] = result
        logger.info(f"Applied {event_kind} event_id={event_id!r}")
        return result
