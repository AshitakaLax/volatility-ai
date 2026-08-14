"""In-memory lot accounting used by the simulation engine.

The ledger owns open-lot state and realized trade history.  It deliberately
contains no broker/account cash state; cash is mutated by the simulation only
from confirmed OMS fills.

No-loss guard (Rule One, §2.1)
--------------------------------
``validate_sell`` is the **single** canonical exit-boundary guard.  Every sell
path — backtest, live, shutdown, reconciliation — must call it before crediting
cash or closing a lot.  No other module may re-implement the
``net_sell_proceeds < allocated_cost_basis`` comparison.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, List

from src.exceptions import SellEconomicsError

if TYPE_CHECKING:
    from src.cost_models import TransactionCostModel

# Canonical tolerances (§2.2).  MONEY_EPSILON is used by the no-loss guard;
# SHARE_EPSILON is used for lot-quantity comparisons.
MONEY_EPSILON: float = 1e-8
SHARE_EPSILON: float = 1e-12


@dataclass
class InventoryLot:
    order_id: str
    symbol: str
    buy_price: float
    shares: float
    target_sell_price: float
    # buy_costs holds the total transaction costs incurred at acquisition
    # (commission + slippage notional) for the original lot quantity.  Defaults
    # to 0.0 so existing callers that omit it (e.g. ZeroCostModel paths) are
    # identical to prior behaviour.
    buy_costs: float = field(default=0.0)

    @property
    def cost_basis(self) -> float:
        """Total acquisition cost including buy-side transaction costs."""
        return self.buy_price * self.shares + self.buy_costs

    def allocated_cost_basis_for(self, qty: float) -> float:
        """Proportional cost basis allocated to *qty* shares.

        For a partial lot sale the basis is allocated proportionally to the
        quantity sold, as required by §2.1 canonical accounting formulas.

        Raises ``ValueError`` if *qty* exceeds remaining lot shares (beyond
        SHARE_EPSILON tolerance).
        """
        if self.shares <= SHARE_EPSILON:
            raise ValueError("lot has no remaining shares")
        if qty > self.shares + SHARE_EPSILON:
            raise ValueError(
                f"qty {qty} exceeds remaining lot shares {self.shares}"
            )
        fraction = min(qty, self.shares) / self.shares
        return self.cost_basis * fraction


# ---------------------------------------------------------------------------
# Canonical no-loss sell domain object (§2.5)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class SellEconomics:
    """Immutable result of a pre-sell economics calculation.

    Fields map exactly to the canonical accounting formulas in §2.1:

        allocated_cost_basis = acquisition_notional + allocated_buy_costs
        net_sell_proceeds    = filled_quantity * effective_sell_price - sell_costs
        realized_pnl         = net_sell_proceeds - allocated_cost_basis
    """

    quantity: float
    allocated_cost_basis: float
    sell_costs: float
    net_sell_proceeds: float
    realized_pnl: float


# ---------------------------------------------------------------------------
# Canonical no-loss guard (Rule One §2.1)
# ---------------------------------------------------------------------------

def validate_sell(
    lot: "InventoryLot",
    quantity: float,
    quoted_price: float,
    cost_model: "TransactionCostModel",
) -> SellEconomics:
    """Evaluate sell economics and enforce the no-loss invariant.

    This is the **one** place the no-loss comparison is evaluated.  Task 1.5's
    fill validation and Task 7.2's partial-fill accounting feed confirmed
    quantities and prices here; they do not re-implement the comparison
    themselves.

    Parameters
    ----------
    lot:
        The ``InventoryLot`` being (partially) sold.
    quantity:
        Number of shares proposed to sell.  Must be positive and ≤ lot.shares.
    quoted_price:
        The reference/quoted sell price (e.g. target_sell_price or broker
        fill price).
    cost_model:
        ``TransactionCostModel`` instance to compute effective sell price and
        sell-side costs.

    Returns
    -------
    SellEconomics
        Filled-in economics dataclass when the sell is permitted.

    Raises
    ------
    SellEconomicsError
        If ``net_sell_proceeds < allocated_cost_basis - MONEY_EPSILON``.
    ValueError
        If *quantity* is non-positive or exceeds *lot.shares*.
    """
    quantity = float(quantity)
    quoted_price = float(quoted_price)

    if quantity <= 0:
        raise ValueError("quantity must be positive")
    if quantity > lot.shares + SHARE_EPSILON:
        raise ValueError(
            f"quantity {quantity} exceeds remaining lot shares {lot.shares}"
        )

    effective_sell_price, sell_costs = cost_model.apply_sell(quoted_price, quantity)
    net_sell_proceeds = quantity * float(effective_sell_price) - float(sell_costs)
    allocated_cost_basis = lot.allocated_cost_basis_for(quantity)
    realized_pnl = net_sell_proceeds - allocated_cost_basis

    econ = SellEconomics(
        quantity=quantity,
        allocated_cost_basis=allocated_cost_basis,
        sell_costs=float(sell_costs),
        net_sell_proceeds=net_sell_proceeds,
        realized_pnl=realized_pnl,
    )

    if net_sell_proceeds < allocated_cost_basis - MONEY_EPSILON:
        raise SellEconomicsError(
            f"sell rejected — Rule One violation: "
            f"net_sell_proceeds={net_sell_proceeds:.10f} < "
            f"allocated_cost_basis={allocated_cost_basis:.10f} "
            f"(realized_pnl={realized_pnl:.10f}, "
            f"qty={quantity}, quoted_price={quoted_price})"
        )

    return econ


# ---------------------------------------------------------------------------
# Ledger
# ---------------------------------------------------------------------------

class AssetLotLedger:
    """Track open inventory lots and completed harvests for one simulation."""

    def __init__(self) -> None:
        self.open_lots: List[InventoryLot] = []
        self.closed_lots: List[InventoryLot] = []

    def register_buy(
        self,
        order_id: str,
        symbol: str,
        filled_avg_price: float,
        qty: float,
        profit_target: float,
        buy_costs: float = 0.0,
    ) -> InventoryLot:
        """Register a confirmed buy fill as a new open lot.

        Parameters
        ----------
        order_id:
            Stable identifier for the originating order.
        symbol:
            Ticker symbol.
        filled_avg_price:
            Confirmed average fill price (post-slippage).
        qty:
            Confirmed fill quantity.
        profit_target:
            Fractional profit target (e.g. 0.05 for 5 %).
        buy_costs:
            Total buy-side transaction costs (commission + slippage notional).
            Defaults to 0.0 for backward compatibility.  When provided, the
            costs are included in ``allocated_cost_basis_for()`` so that the
            no-loss guard accounts for acquisition costs correctly.
        """
        if qty <= 0:
            raise ValueError("qty must be positive")
        if filled_avg_price <= 0:
            raise ValueError("filled_avg_price must be positive")
        if profit_target < 0:
            raise ValueError("profit_target must be non-negative")
        if buy_costs < 0:
            raise ValueError("buy_costs must be non-negative")

        lot = InventoryLot(
            order_id=str(order_id),
            symbol=symbol,
            buy_price=float(filled_avg_price),
            shares=float(qty),
            target_sell_price=float(filled_avg_price) * (1.0 + float(profit_target)),
            buy_costs=float(buy_costs),
        )
        self.open_lots.append(lot)
        return lot

    def get_marketable_lots(self, current_price: float) -> list[InventoryLot]:
        """Return a stable snapshot of lots whose target has been reached."""
        return [
            lot
            for lot in self.open_lots
            if float(current_price) >= lot.target_sell_price
        ]

    def close_lot(
        self,
        lot: InventoryLot,
        sell_qty: float | None = None,
        execution_price: float | None = None,
        completed: bool = True,
    ) -> None:
        """Close all or part of a lot.

        The default call ``close_lot(lot)`` preserves the existing simulation
        call contract.  Partial-close support is included in a backward-
        compatible form for later live-fill handling.

        Note: callers should validate economics via ``validate_sell`` *before*
        calling ``close_lot``; this method mutates shares without repeating the
        no-loss check.
        """
        if lot not in self.open_lots:
            raise ValueError("lot is not an open ledger lot")

        qty = lot.shares if sell_qty is None else float(sell_qty)
        if qty <= 0:
            raise ValueError("sell_qty must be positive")
        if qty > lot.shares + SHARE_EPSILON:
            raise ValueError("sell_qty exceeds remaining lot shares")

        # execution_price is informational at this layer; the no-loss guard
        # (validate_sell) is responsible for economics enforcement before this
        # point.
        _ = execution_price
        lot.shares -= min(qty, lot.shares)

        if completed or lot.shares <= SHARE_EPSILON:
            if lot.shares > SHARE_EPSILON:
                return
            lot.shares = 0.0
            self.open_lots.remove(lot)
            self.closed_lots.append(lot)

    @property
    def total_open_cost_basis(self) -> float:
        return sum(lot.cost_basis for lot in self.open_lots)

    @property
    def open_share_count(self) -> float:
        return sum(lot.shares for lot in self.open_lots)
