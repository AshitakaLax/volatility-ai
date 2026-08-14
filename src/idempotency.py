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
- LIVE-mode fills: NOT YET CONFIRMED. This task's own instructions say
  to use the broker's own order/event ID "if the SDK guarantees it's
  stable and unique per event -- confirm this against alpaca-py's
  actual fields rather than assuming." This repo's LIVE mode isn't
  implemented (OrderManagementSystem raises NotImplementedError for
  it), so there's no real alpaca-py integration to confirm this
  against yet. Task 7.1's real broker adapter must confirm the actual
  field (candidates: Alpaca's own order.id, or a client_order_id set
  at submission time) before wiring LIVE fills through this module.
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

import logging
from typing import Callable, Hashable, MutableSet, Optional, TypeVar

logger = logging.getLogger("Optimizer")

T = TypeVar("T")


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
