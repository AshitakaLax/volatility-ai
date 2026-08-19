"""
Canonical order lifecycle / state machine. Task 7.10.

Verified first (this task's step 1 / agent contract): there was NO
existing state machine in src/order_management_system.py -- only the
ad-hoc OrderStatus string constants added for Task 1.5's fill
contract. The task's default transition table therefore applies, and
is implemented here exactly as written.

Scope, per this task's Non-goals: this defines the states and their
transitions ONLY. It does not implement reconciliation (Task 7.11) or
retry (Task 7.13); both consume these states. The UNKNOWN escape hatch
below is deliberately shaped so 7.11 can plug into it without this
module needing to know how reconciliation works.

--------------------------------------------------------------------
OBSERVATION ON THE SPECIFIED TABLE -- flagged, not unilaterally
changed:

The table permits SUBMITTED -> UNKNOWN but does NOT permit
ACCEPTED -> UNKNOWN (or PARTIALLY_FILLED -> UNKNOWN). In practice an
already-accepted order can absolutely become unknown -- the connection
drops, or a status query times out, after acceptance. Under the table
as written, that transition is rejected, so such an order stays
recorded as ACCEPTED even though its true state is genuinely unknown.

The table is implemented AS SPECIFIED rather than silently extended,
since the task says to implement it and reject anything not listed.
Raised for a decision rather than quietly patched -- see the chat this
was produced in.
--------------------------------------------------------------------
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Optional

from src.exceptions import ExecutionError

logger = logging.getLogger("Optimizer")


class OrderState(str, Enum):
    """The nine canonical internal states named by Task 7.10 step 1."""

    CREATED = "CREATED"
    SUBMITTED = "SUBMITTED"
    ACCEPTED = "ACCEPTED"
    PARTIALLY_FILLED = "PARTIALLY_FILLED"
    FILLED = "FILLED"
    CANCELED = "CANCELED"
    REJECTED = "REJECTED"
    EXPIRED = "EXPIRED"
    UNKNOWN = "UNKNOWN"


TERMINAL_STATES = frozenset(
    {OrderState.FILLED, OrderState.CANCELED, OrderState.REJECTED, OrderState.EXPIRED}
)

# The task's default transition table, implemented literally. Anything
# not listed here is rejected and logged.
ALLOWED_TRANSITIONS: dict = {
    OrderState.CREATED: frozenset({OrderState.SUBMITTED}),
    OrderState.SUBMITTED: frozenset({OrderState.ACCEPTED, OrderState.REJECTED, OrderState.UNKNOWN}),
    OrderState.ACCEPTED: frozenset(
        {OrderState.PARTIALLY_FILLED, OrderState.FILLED, OrderState.CANCELED, OrderState.EXPIRED}
    ),
    OrderState.PARTIALLY_FILLED: frozenset(
        {OrderState.PARTIALLY_FILLED, OrderState.FILLED, OrderState.CANCELED}
    ),
    OrderState.FILLED: frozenset(),
    OrderState.CANCELED: frozenset(),
    OrderState.REJECTED: frozenset(),
    OrderState.EXPIRED: frozenset(),
    # UNKNOWN -> any state, but ONLY through resolve_from_unknown().
    # Deliberately empty here so the ordinary transition path cannot
    # reach it: "never via inference" is enforced structurally rather
    # than by documentation.
    OrderState.UNKNOWN: frozenset(),
}


# Step 3: broker-specific statuses mapped into canonical internal
# states at the adapter boundary. Covers ALL 18 values of the real
# alpaca-py OrderStatus enum -- enumerated from the installed SDK, not
# guessed, and a test asserts none is ever missed.
#
# Safety principle applied to every judgment call below: when a broker
# status is ambiguous, map to a NON-terminal working state rather than
# a terminal one. A terminal state stops further processing, so
# wrongly marking a live order terminal loses track of real exposure;
# wrongly keeping a finished order "working" merely causes a redundant
# status query, which reconciliation (Task 7.11) resolves harmlessly.
_ALPACA_STATUS_MAP: dict = {
    # Received but not yet working at the venue.
    "pending_new": OrderState.SUBMITTED,
    "pending_review": OrderState.SUBMITTED,
    # Live/working at the broker.
    "new": OrderState.ACCEPTED,
    "accepted": OrderState.ACCEPTED,
    "accepted_for_bidding": OrderState.ACCEPTED,
    "held": OrderState.ACCEPTED,
    "stopped": OrderState.ACCEPTED,
    "suspended": OrderState.ACCEPTED,
    "calculated": OrderState.ACCEPTED,
    "done_for_day": OrderState.ACCEPTED,
    "pending_cancel": OrderState.ACCEPTED,
    "pending_replace": OrderState.ACCEPTED,
    # Fills.
    "partially_filled": OrderState.PARTIALLY_FILLED,
    "filled": OrderState.FILLED,
    # Terminal, unambiguous.
    "canceled": OrderState.CANCELED,
    "expired": OrderState.EXPIRED,
    "rejected": OrderState.REJECTED,
    # The original order is finished; a NEW order carries on in its
    # place. CANCELED is the closest canonical fit for the original.
    "replaced": OrderState.CANCELED,
}


def map_broker_status(broker_status) -> OrderState:
    """Translate a broker status into a canonical internal state.

    An unrecognized status maps to UNKNOWN rather than being guessed
    at or silently dropped -- which then requires explicit
    reconciliation (Task 7.11) to resolve, exactly as the transition
    contract demands.
    """
    raw = getattr(broker_status, "value", broker_status)
    key = str(raw).lower()
    state = _ALPACA_STATUS_MAP.get(key)
    if state is None:
        logger.warning(
            f"Unrecognized broker order status {raw!r} -- mapping to UNKNOWN; "
            "explicit reconciliation is required to resolve it."
        )
        return OrderState.UNKNOWN
    return state


@dataclass
class OrderRecord:
    """One order's lifecycle state and quantities.

    Step 4: requested / filled / remaining quantity, average fill
    price, client order ID, broker order ID and timestamps are all
    SEPARATE fields -- never derived on the fly from each other in a
    way that could disagree.

    State ownership: this object owns its own state and quantities.
    Nothing else may write them; callers go through apply_broker_update
    or transition_to, both of which enforce the table.
    """

    client_order_id: str
    requested_qty: float
    symbol: str = ""
    broker_order_id: Optional[str] = None
    state: OrderState = OrderState.CREATED
    filled_qty: float = 0.0
    avg_fill_price: float = 0.0
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    submitted_at: Optional[datetime] = None
    last_update_at: Optional[datetime] = None

    @property
    def remaining_qty(self) -> float:
        """Never negative: a broker over-reporting fills is a
        reconciliation problem, not a reason to produce a nonsensical
        negative remainder that downstream sizing might act on."""
        return max(0.0, self.requested_qty - self.filled_qty)

    @property
    def is_terminal(self) -> bool:
        """Whether this order has reached a state it can never leave."""
        return self.state in TERMINAL_STATES

    def can_transition_to(self, new_state: OrderState) -> bool:
        """Whether the table permits this move, without attempting it.

        Lets a caller check first rather than catching ExecutionError,
        which matters where an invalid transition is expected and
        routine rather than exceptional.
        """
        return new_state in ALLOWED_TRANSITIONS[self.state]

    def transition_to(self, new_state: OrderState, *, at: Optional[datetime] = None) -> None:
        """Move to new_state, enforcing the transition table.

        Raises ExecutionError WITHOUT mutating any field on an invalid
        transition -- the acceptance criterion is explicit that invalid
        transitions must not mutate accounting, so the check happens
        before any write.
        """
        if not self.can_transition_to(new_state):
            allowed = sorted(s.value for s in ALLOWED_TRANSITIONS[self.state])
            detail = (
                f"Invalid order transition {self.state.value} -> {new_state.value} "
                f"for client_order_id={self.client_order_id!r}. Allowed from "
                f"{self.state.value}: {allowed or '(terminal -- none)'}."
            )
            if self.state is OrderState.UNKNOWN:
                detail += " Resolve an UNKNOWN order via resolve_from_unknown() (Task 7.11), not inference."
            logger.error(detail)
            raise ExecutionError(detail)

        self.state = new_state
        now = at or datetime.now(timezone.utc)
        if new_state is OrderState.SUBMITTED and self.submitted_at is None:
            self.submitted_at = now
        self.last_update_at = now

    def resolve_from_unknown(
        self, new_state: OrderState, *, resolution_source: str, at: Optional[datetime] = None
    ) -> None:
        """The ONLY path out of UNKNOWN, per the transition contract's
        "only via an explicit reconciliation/query resolution (Task
        7.11), never via inference".

        resolution_source is required and must name where the
        authoritative answer came from (e.g. a broker query), so an
        UNKNOWN order can never be cleared by a bare guess.
        """
        if self.state is not OrderState.UNKNOWN:
            raise ExecutionError(
                f"resolve_from_unknown is only valid from UNKNOWN; order "
                f"{self.client_order_id!r} is {self.state.value}."
            )
        if not resolution_source or not str(resolution_source).strip():
            raise ExecutionError(
                "resolve_from_unknown requires a non-empty resolution_source naming the "
                "authoritative query/reconciliation that produced this answer -- an UNKNOWN "
                "order may not be resolved by inference."
            )
        self.state = new_state
        self.last_update_at = at or datetime.now(timezone.utc)
        logger.info(
            f"Order {self.client_order_id!r} resolved UNKNOWN -> {new_state.value} "
            f"via {resolution_source}."
        )

    def apply_broker_update(
        self,
        broker_status,
        filled_qty: Optional[float] = None,
        avg_fill_price: Optional[float] = None,
        broker_order_id: Optional[str] = None,
        at: Optional[datetime] = None,
    ) -> OrderState:
        """Apply one broker status update: map the status, enforce the
        transition, then record quantities.

        Ordering is deliberate -- the transition is validated FIRST, so
        an invalid update leaves quantities untouched (acceptance
        criterion: "invalid transitions are rejected without mutating
        accounting").

        filled_qty is the broker's CUMULATIVE figure (see
        src/fill_accounting.py); this stores it as-is. Deriving the
        incremental delta that may actually move cash is Task 7.2's
        FillTracker, deliberately not duplicated here.
        """
        new_state = map_broker_status(broker_status)
        if new_state is self.state and new_state is not OrderState.PARTIALLY_FILLED:
            # An idempotent repeat of the current state (a duplicate
            # broker message) is a no-op, not an invalid transition.
            # PARTIALLY_FILLED is excluded because the table explicitly
            # allows it to recur with new quantities.
            self._record_quantities(filled_qty, avg_fill_price, broker_order_id, at)
            return self.state

        self.transition_to(new_state, at=at)
        self._record_quantities(filled_qty, avg_fill_price, broker_order_id, at)
        return self.state

    def _record_quantities(self, filled_qty, avg_fill_price, broker_order_id, at) -> None:
        """Write the quantity fields an update supplied.

        Every argument is optional and None means "unchanged", so a
        status-only update cannot blank out quantities it said nothing
        about. Called only AFTER the transition is validated, so a
        rejected update leaves accounting untouched.
        """
        if filled_qty is not None:
            self.filled_qty = float(filled_qty)
        if avg_fill_price is not None:
            self.avg_fill_price = float(avg_fill_price)
        if broker_order_id is not None:
            self.broker_order_id = str(broker_order_id)
        self.last_update_at = at or datetime.now(timezone.utc)
