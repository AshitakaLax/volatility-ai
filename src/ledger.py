"""In-memory lot accounting used by the simulation engine.

The ledger owns open-lot state and realized trade history.  It deliberately
contains no broker/account cash state; cash is mutated by the simulation only
from confirmed OMS fills.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List

SHARE_EPSILON = 1e-12


@dataclass
class InventoryLot:
    order_id: str
    symbol: str
    buy_price: float
    shares: float
    target_sell_price: float

    @property
    def cost_basis(self) -> float:
        return self.buy_price * self.shares


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
    ) -> InventoryLot:
        if qty <= 0:
            raise ValueError("qty must be positive")
        if filled_avg_price <= 0:
            raise ValueError("filled_avg_price must be positive")
        if profit_target < 0:
            raise ValueError("profit_target must be non-negative")

        lot = InventoryLot(
            order_id=str(order_id),
            symbol=symbol,
            buy_price=float(filled_avg_price),
            shares=float(qty),
            target_sell_price=float(filled_avg_price) * (1.0 + float(profit_target)),
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
        """
        if lot not in self.open_lots:
            raise ValueError("lot is not an open ledger lot")

        qty = lot.shares if sell_qty is None else float(sell_qty)
        if qty <= 0:
            raise ValueError("sell_qty must be positive")
        if qty > lot.shares + SHARE_EPSILON:
            raise ValueError("sell_qty exceeds remaining lot shares")

        # execution_price is intentionally informational at this layer.  The
        # ledger owns inventory/cost basis; realized proceeds are computed by
        # the account/performance layer from confirmed fills.
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
