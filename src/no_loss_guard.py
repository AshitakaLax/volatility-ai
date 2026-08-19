"""
The no-loss sell guard. Task 7.15.

The system's primary invariant is that it never intentionally sells at
a loss. That cannot be a strategy convention: transaction costs,
slippage, partial fills, reconnects, risk halts, and live execution
can all bypass a convention. This is the enforcement point.

SINGLE-GUARD CONTRACT: this is the ONE place the no-loss comparison is
evaluated. Two independent inline implementations existed before this
task -- one in optimization_controller._simulate_single (added by Task
1.5, extended by Task 2.2) and one in
intraday_validation.simulate_single_intraday. Both are now folded into
calls to validate_sell(); neither retains its own copy of the formula,
so they cannot silently drift apart.

Formulas are taken verbatim from implementation_task_specs.md's
"Canonical money/accounting formulas" (identical to
architecture_overview.md 2.1) -- deliberately NOT re-derived:

    allocated_cost_basis = acquisition_notional + allocated_buy_costs
    net_sell_proceeds    = filled_quantity * effective_sell_price - sell_costs
    realized_pnl         = net_sell_proceeds - allocated_cost_basis
    sell_permitted iff net_sell_proceeds >= allocated_cost_basis

MONEY_EPSILON = 1e-8, per overview 2.2's money-comparison rule -- the
same tolerance already used elsewhere in this repo, not a new one.

Cost basis at partial-lot granularity (step 1): a lot's buy_price is
already a PER-SHARE cost basis with buy-side commission folded in (see
optimization_controller._simulate_single's per_share_cost_basis, Task
2.2), so allocating proportionally is simply buy_price * quantity. The
remaining quantity keeps the remaining basis untouched -- step 5's
"never mark the remaining lot as realized".

State ownership: this module is PURE. It computes and decides; it
mutates no lot, no cash, and no ledger. Callers apply the outcome.
That is what makes it safe for every exit path -- risk halt, shutdown,
reconciliation, retry -- to call the same function.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Optional

from src.exceptions import ExecutionError

logger = logging.getLogger("Optimizer")

# architecture_overview.md 2.2: money comparisons use 1e-8.
MONEY_EPSILON = 1e-8


class NoLossViolation(ExecutionError):
    """A proposed sell would realize a loss.

    Its own type (under Task 4.8's ExecutionError) so callers can
    distinguish "this exit is forbidden" from a broker/execution
    failure -- they are handled very differently.
    """


@dataclass(frozen=True)
class SellEconomics:
    """Result of evaluating one proposed sell. Frozen: an evaluated
    outcome must not be edited by whoever acts on it."""

    quantity: float
    allocated_cost_basis: float
    sell_costs: float
    net_sell_proceeds: float
    realized_pnl: float

    @property
    def permitted(self) -> bool:
        """Whether this sell clears the no-loss invariant.

        Uses `>= basis - MONEY_EPSILON`, so a break-even exit passes and
        a difference smaller than float noise is not treated as a loss.
        """
        return self.net_sell_proceeds >= self.allocated_cost_basis - MONEY_EPSILON


def compute_sell_economics(
    lot,
    quantity: float,
    quoted_price: float,
    cost_model,
    context=None,
    prev_close=None,
) -> SellEconomics:
    """Compute the economics of a proposed sell WITHOUT raising.

    Exposed separately from validate_sell so a caller that needs to
    inspect or log the numbers for a rejected exit can do so without
    catching an exception -- and so the decision and the reporting use
    the identical computation.

    context/prev_close are forwarded to the cost model for
    volatility-aware slippage (Task 7.5's DynamicSlippageModel); static
    models ignore them.
    """
    if quantity <= 0:
        raise ValueError(f"quantity must be positive, got {quantity}")
    if quoted_price <= 0:
        raise ValueError(f"quoted_price must be positive, got {quoted_price}")

    effective_price, sell_costs = cost_model.apply_sell(
        quoted_price, quantity, context=context, prev_close=prev_close
    )
    net_sell_proceeds = quantity * effective_price - sell_costs
    allocated_cost_basis = lot.buy_price * quantity  # proportional allocation (step 1)
    return SellEconomics(
        quantity=quantity,
        allocated_cost_basis=allocated_cost_basis,
        sell_costs=sell_costs,
        net_sell_proceeds=net_sell_proceeds,
        realized_pnl=net_sell_proceeds - allocated_cost_basis,
    )


def validate_sell(
    lot,
    quantity: float,
    quoted_price: float,
    cost_model,
    context=None,
    prev_close=None,
) -> SellEconomics:
    """The canonical exit-boundary guard.

    Returns the SellEconomics when the sell is permitted; raises
    NoLossViolation when net proceeds would not cover the allocated
    cost basis (step 4: rejected BEFORE submission).

    Every exit path calls this -- normal harvest, intraday replay,
    partial fills, and any future shutdown/reconciliation exit. None of
    them re-implement the comparison.
    """
    economics = compute_sell_economics(
        lot, quantity, quoted_price, cost_model, context=context, prev_close=prev_close
    )
    if not economics.permitted:
        detail = (
            f"No-loss guard REJECTED sell of {quantity} share(s) of lot "
            f"{getattr(lot, 'order_id', '?')!r} at quoted {quoted_price}: net proceeds "
            f"{economics.net_sell_proceeds:.6f} < allocated cost basis "
            f"{economics.allocated_cost_basis:.6f} (sell costs {economics.sell_costs:.6f}, "
            f"realized PnL would be {economics.realized_pnl:+.6f})."
        )
        logger.warning(detail)
        raise NoLossViolation(detail)
    return economics
