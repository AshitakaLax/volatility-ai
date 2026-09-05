"""
Cumulative-to-incremental fill accounting. Task 7.2 (L4).

Alpaca reports filled_qty and filled_avg_price as CUMULATIVE values
for the whole order, not per-update deltas. Applying them directly
double-counts shares and cash. FillTracker converts a stream of
cumulative broker updates into the incremental quantity/notional that
may actually mutate cash, shares, cost basis, or realized P&L.

Formula (implementation_task_specs.md Task 7.2, Implementation step 2):
    new_fill_qty      = current_qty - previous_qty
    new_fill_notional = current_qty * current_avg - previous_qty * previous_avg
    new_fill_avg_price = new_fill_notional / new_fill_qty   (when qty > 0)

--------------------------------------------------------------------
SPEC CONTRADICTION -- resolved deliberately, flagged rather than
silently picked:

Task 7.2 states the delta notionals for the sequence
4@150 -> 7@151 -> 10@152 twice, with DIFFERENT numbers:

  "Cumulative-fill arithmetic fixture":  600, 457, 463
  "Cumulative-fill invariant":           600, 453, 456

This module implements 600 / 457 / 463 (the fixture's numbers), for
three independently verified reasons:

  1. They are what the spec's OWN formula above produces:
     7*151 - 4*150 = 1057 - 600 = 457, and 10*152 - 7*151 = 463.
  2. The invariant's numbers are exactly delta_qty * cumulative_avg
     (3*151 = 453, 3*152 = 456) -- which the very next sentence of
     that same paragraph explicitly forbids: "Never calculate the
     second increment as 3 * 151 merely because 151 is the cumulative
     average price." The invariant's stated numbers contradict the
     invariant's own stated rule.
  3. The deltas must sum to the final cumulative notional.
     600+457+463 = 1520 = 10*152 exactly. The invariant's
     600+453+456 = 1509 loses $11 of a $1,520 order -- money that
     would simply vanish from the books.

Both are asserted in the tests, with the invariant's figures
explicitly documented there as incorrect rather than quietly dropped.
--------------------------------------------------------------------

Non-goals honored: this module handles in-memory accounting only.
Durable write-through of these mutations is Task 7.3's scope.
"""

from __future__ import annotations

from dataclasses import dataclass

from src.exceptions import ReconciliationError

QTY_EPSILON = 1e-9


@dataclass(frozen=True)
class FillDelta:
    """One increment of confirmed execution. qty/notional are the ONLY
    values permitted to mutate cash, shares, or P&L."""

    qty: float
    notional: float
    avg_price: float

    @property
    def is_empty(self) -> bool:
        """Whether this delta carries no new fill -- a duplicate or
        no-progress broker update. Callers should skip such deltas
        entirely rather than applying a zero-value mutation."""
        return self.qty <= QTY_EPSILON


class FillTracker:
    """Tracks one order's cumulative broker state and yields increments.

    One tracker per order id. Owns only its own last-seen cumulative
    values -- it never touches the ledger, cash, or lots; callers apply
    the returned FillDelta.
    """

    def __init__(self, order_id: str):
        """One tracker per order id.

        Starts at zero cumulative quantity and notional, so the first
        update's delta equals its full reported value.
        """
        self.order_id = order_id
        self._cumulative_qty = 0.0
        self._cumulative_notional = 0.0

    @property
    def cumulative_qty(self) -> float:
        """Total quantity filled so far, as last reported by the broker."""
        return self._cumulative_qty

    @property
    def cumulative_notional(self) -> float:
        """Total notional filled so far (cumulative_qty * cumulative avg
        price at the time of the last update)."""
        return self._cumulative_notional

    def restore(self, cumulative_qty: float, cumulative_notional: float) -> None:
        """Re-seed the baseline from durable state after a restart.

        A tracker rebuilt at zero would read the broker's CUMULATIVE
        figures as one enormous first increment and re-apply a fill that
        was already booked. This sets the baseline back to what was
        already accounted for, so the next apply_update yields only what
        actually happened while the process was down.

        Deliberately not a constructor argument: a fresh order must
        start at zero, and making the baseline optional-at-construction
        would let a typo silently suppress a real first fill.
        """
        self._cumulative_qty = float(cumulative_qty)
        self._cumulative_notional = float(cumulative_notional)

    def apply_update(self, filled_qty: float, filled_avg_price: float) -> FillDelta:
        """Consume one cumulative broker status update, returning the
        incremental fill it represents.

        A decrease in cumulative quantity or notional raises
        ReconciliationError rather than auto-reversing prior accounting
        (Cumulative-fill invariant: "If broker-reported cumulative
        quantity or notional decreases, enter reconciliation/error
        handling; never automatically reverse prior accounting").
        """
        filled_qty = float(filled_qty)
        filled_avg_price = float(filled_avg_price)
        new_cumulative_notional = filled_qty * filled_avg_price

        if filled_qty < self._cumulative_qty - QTY_EPSILON:
            raise ReconciliationError(
                f"Order {self.order_id!r}: broker-reported cumulative filled_qty decreased "
                f"({self._cumulative_qty} -> {filled_qty}). Not auto-reversing prior accounting."
            )
        if new_cumulative_notional < self._cumulative_notional - QTY_EPSILON:
            raise ReconciliationError(
                f"Order {self.order_id!r}: broker-reported cumulative notional decreased "
                f"({self._cumulative_notional} -> {new_cumulative_notional}). "
                "Not auto-reversing prior accounting."
            )

        delta_qty = filled_qty - self._cumulative_qty
        delta_notional = new_cumulative_notional - self._cumulative_notional

        self._cumulative_qty = filled_qty
        self._cumulative_notional = new_cumulative_notional

        if delta_qty <= QTY_EPSILON:
            return FillDelta(qty=0.0, notional=0.0, avg_price=0.0)
        return FillDelta(
            qty=delta_qty, notional=delta_notional, avg_price=delta_notional / delta_qty
        )


def extract_alpaca_fill(order) -> tuple[float, float]:
    """Pull (filled_qty, filled_avg_price) off an Alpaca Order as floats.

    Both arrive as strings from the SDK (verified against the real
    alpaca-py Order model, not assumed), and filled_avg_price is None
    until the first fill lands.
    """
    filled_qty = float(order.filled_qty or 0)
    filled_avg_price = float(order.filled_avg_price or 0)
    return filled_qty, filled_avg_price
