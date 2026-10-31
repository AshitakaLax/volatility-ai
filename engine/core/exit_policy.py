"""
How much of a lot to sell: the quantity half of a sell decision.

Until partial selling existed every sale was a whole lot, so "which lot" was
the entire decision. A strategy may now also say how much of it -- a
scale-out ladder sells half at one target and the rest at another, a
partial regime exit sells a fraction of every lot's shares. This module is
the one place that quantity is shaped into something sellable, so the
backtest, the intrabar replay and the live loop cannot round it three ways.

--------------------------------------------------------------------
WHY IN core/

The SizingStrategy port (core/sizing.py) is where a strategy says how much
to sell, and a strategy in research/ builds the ExitOrder it returns. Both
need these names without importing engine/trading/, which core/ never does
at import time. So the reason is carried as the SAME STRINGS
engine/trading/no_loss_guard.SellReason uses (a StrEnum: SellReason(value)
round-trips them); engine/tests/test_exit_policy.py pins that they agree.

--------------------------------------------------------------------
THE NO-LOSS GUARD IS UNTOUCHED

Nothing here decides whether a sale may realise a loss. A quantity reaches
no_loss_guard.validate_sell like any other, and the guard's proportional
basis (buy_price * quantity) is already correct for part of a lot.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from decimal import ROUND_FLOOR, Decimal
from typing import Any

from engine.core.ledger import SHARE_EPSILON

# no_loss_guard.SellReason's values, as strings (see the module docstring).
PROFIT_TARGET = "profit_target"
SIGNAL_EXIT = "signal_exit"
REASONS = (PROFIT_TARGET, SIGNAL_EXIT)

__all__ = [
    "PROFIT_TARGET",
    "REASONS",
    "SIGNAL_EXIT",
    "ExitOrder",
    "floor_shares",
    "sellable_quantity",
]


def floor_shares(qty: float) -> float:
    """Down to the nine decimals a fractional order may carry, never up: an
    order for more shares than a lot holds would sell what is not owned."""
    return float(Decimal(str(qty)).quantize(Decimal("0.000000001"), rounding=ROUND_FLOOR))


@dataclass(frozen=True, eq=False)
class ExitOrder:
    """Sell `quantity` shares of `lot`, for `reason`.

    PROFIT_TARGET orders are the harvest: the lot reached its target and
    fills there (or better). SIGNAL_EXIT orders are a strategy's
    lots_to_liquidate: they fill at the bar's price and may realise a loss,
    which is why decision_cycle.collect_liquidations only ever produces them
    behind execution.allow_signal_exit.

    Identity equality, like Lot: two orders for the same lot and quantity
    are still two orders, and a set of them must not merge them.
    """

    lot: Any
    quantity: float
    reason: str = SIGNAL_EXIT

    def __post_init__(self) -> None:
        if self.reason not in REASONS:
            raise ValueError(f"reason must be one of {REASONS}, got {self.reason!r}")
        if not (isinstance(self.quantity, (int, float)) and math.isfinite(self.quantity)):
            raise ValueError(f"quantity must be a finite number, got {self.quantity!r}")
        if self.quantity <= 0:
            raise ValueError(f"quantity must be positive, got {self.quantity}")

    @property
    def whole(self) -> bool:
        """Whether this order sells everything the lot holds."""
        return self.quantity >= self.lot.shares - SHARE_EPSILON


def sellable_quantity(requested: float, shares: float, *, whole_shares: bool = False) -> float:
    """`requested` shares of a lot holding `shares`, as a quantity a venue
    accepts -- or 0.0, meaning "not this bar".

      * A request for the whole lot (or more) returns `shares` exactly, so
        the caller takes the whole-lot path it has always taken and a lot
        sold whole is booked exactly as before partial selling existed.
      * Otherwise the request is floored: to whole shares where the venue
        sells only whole shares (Fidelity outside the regular session), else
        to nine decimals. Never rounded up.
      * A floor of zero returns 0.0: the tranche waits for a bar where it
        can be sold, rather than the lot being sold whole early.
      * A floor that would leave less than SHARE_EPSILON behind is the whole
        lot, so no dust lot is left open.
    """
    if not (isinstance(requested, (int, float)) and math.isfinite(requested)) or requested <= 0:
        return 0.0
    if shares <= SHARE_EPSILON:
        return 0.0
    if requested >= shares - SHARE_EPSILON:
        return shares
    qty = float(math.floor(requested + SHARE_EPSILON)) if whole_shares else floor_shares(requested)
    if qty <= 0:
        return 0.0
    if shares - qty <= SHARE_EPSILON:
        return shares
    return qty
