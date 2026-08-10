"""
Lot-based position ledger for the grid-harvesting strategy.

This is an original, from-scratch implementation written because no
existing src/ledger.py was available to read (see the chat this was
produced in). It targets exactly the public interface
optimization_controller.py currently calls:

    ledger.register_buy(order_id, symbol, buy_price, shares, profit_target)
    ledger.get_marketable_lots(current_price)
    ledger.close_lot(lot)
    ledger.open_lots

`close_lot`'s `completed: bool = True` parameter follows
architecture_overview.md Appendix 8's repository-adaptive note ("might
hint at partial-close support"). Only the completed=True path (a full
close) is implemented -- Task 7.2 is expected to define the real
sell_qty/execution_price semantics for a partial close, which aren't
specified anywhere in the architecture or task-spec documents, so this
implementation does not guess at them.

Not implemented here (out of scope for this pass, belongs to later
phases): SQLite persistence (architecture_overview.md Section 2.6,
Task 7.3), a cap on concurrent open lots (finding R1), and the
canonical frozen execution_models.Lot/OrderIntent/Fill dataclasses
(Section 2.5, Task 4.1+) -- this module's Lot is the simpler mutable
record the current (pre-Phase-4) controller flow needs.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Lot:
    """A single open or closed position lot.

    target_sell_price is computed once at registration from buy_price
    and profit_target and does not change afterward.
    """

    order_id: str
    symbol: str
    buy_price: float
    shares: float
    profit_target: float
    target_sell_price: float = field(init=False)

    def __post_init__(self) -> None:
        self.target_sell_price = self.buy_price * (1.0 + self.profit_target)


class AssetLotLedger:
    """Tracks open and closed lots for a single simulation/live run.

    Not thread-safe; matches optimization_controller.py's current usage
    of one ledger instance per sequential run_sweep() iteration.
    """

    def __init__(self) -> None:
        self.open_lots: list[Lot] = []
        self.closed_lots: list[Lot] = []

    def register_buy(
        self,
        order_id: str,
        symbol: str,
        buy_price: float,
        shares: float,
        profit_target: float,
    ) -> Lot:
        """Open a new lot after a confirmed buy fill."""
        if shares <= 0:
            raise ValueError(f"shares must be positive, got {shares}")
        if buy_price <= 0:
            raise ValueError(f"buy_price must be positive, got {buy_price}")
        if profit_target <= 0:
            raise ValueError(f"profit_target must be positive, got {profit_target}")

        lot = Lot(
            order_id=order_id,
            symbol=symbol,
            buy_price=buy_price,
            shares=shares,
            profit_target=profit_target,
        )
        self.open_lots.append(lot)
        return lot

    def get_marketable_lots(self, current_price: float) -> list[Lot]:
        """Open lots whose profit target is met or exceeded at current_price.

        Returned in FIFO (registration) order. Does not mutate state --
        callers are expected to close_lot() each one after a confirmed
        sell fill.
        """
        return [lot for lot in self.open_lots if current_price >= lot.target_sell_price]

    def close_lot(self, lot: Lot, completed: bool = True) -> None:
        """Move a lot from open to closed after a confirmed sell fill.

        completed=True (the default, and the only path
        optimization_controller.py currently exercises) fully closes the
        lot. completed=False is not implemented -- see module docstring.
        """
        if not completed:
            raise NotImplementedError(
                "Partial lot closes (completed=False) are not specified anywhere "
                "in architecture_overview.md or implementation_task_specs.md -- "
                "see Appendix 8. Task 7.2 is expected to define sell_qty/"
                "execution_price semantics for this before it's implemented."
            )
        if lot not in self.open_lots:
            raise ValueError(f"Lot {lot.order_id!r} is not an open lot in this ledger")
        self.open_lots.remove(lot)
        self.closed_lots.append(lot)
