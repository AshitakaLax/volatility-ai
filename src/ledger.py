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

# Floating-point drift tolerance for share quantities (Task 7.2 step 5).
SHARE_EPSILON = 1e-9


@dataclass(eq=False)
class Lot:
    """A single open or closed position lot.

    target_sell_price is computed once at registration from buy_price
    and profit_target and does not change afterward -- including across
    partial closes (Task 7.2's State Mutation Scope forbids mutating
    either during a partial split).

    eq=False -- IDENTITY equality, not the dataclass default of
    field-wise equality. Two reasons, one correctness and one cost.

    Correctness: close_lot asks `if lot not in self.open_lots` and then
    `self.open_lots.remove(lot)`. Under field-wise equality those match
    the FIRST lot with equal fields, which is not necessarily the lot
    passed in -- two lots bought at the same price for the same size
    with the same target are field-identical and genuinely
    indistinguishable. A grid strategy produces exactly that
    constantly. Identity is what those two call sites actually mean.

    Cost: field-wise __eq__ made `in`/`remove` compare every field of
    every open lot on every close. Profiled on a 60-day minute slice
    with ~620 concurrent lots, that was 19.6M __eq__ calls and ~55% of
    total simulation runtime. Identity comparison is a pointer check.
    """

    order_id: str
    symbol: str
    buy_price: float
    shares: float
    profit_target: float
    target_sell_price: float = field(init=False)
    # Audit-only: the price of the most recent confirmed fill applied to
    # this lot. Never feeds cost basis or the exit target.
    last_execution_price: float | None = field(default=None, init=False)

    def __post_init__(self) -> None:
        """Derive the exit target once, at creation.

        Computed here rather than on each access so it is fixed for the
        lot's lifetime: partial closes must not move an existing lot's
        exit price.
        """
        self.target_sell_price = self.buy_price * (1.0 + self.profit_target)


class AssetLotLedger:
    """Tracks open and closed lots for a single simulation/live run.

    Not thread-safe; matches optimization_controller.py's current usage
    of one ledger instance per sequential run_sweep() iteration.
    """

    def __init__(self) -> None:
        """Start with no lots.

        A fresh ledger per simulated combination is what keeps sweeps
        isolated from each other.
        """
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

    def close_lot(
        self,
        lot: Lot,
        sell_qty: float | None = None,
        execution_price: float | None = None,
        completed: bool = True,
    ) -> None:
        """Apply a confirmed sell fill to a lot. Task 7.2.

        Backward compatible with the original close_lot(lot) call site
        (optimization_controller.py's SIMULATION path, unchanged since
        Phase 0): with sell_qty omitted, this is a full close, exactly
        as before.

        sell_qty is the NEWLY filled (incremental) quantity, never the
        broker's cumulative filled_qty -- see
        src/fill_accounting.py, which derives the increment. Passing a
        cumulative value here would double-count shares.

        Mutates lot.shares only. lot.buy_price and lot.target_sell_price
        are never modified during a partial close (State Mutation Scope),
        so the remaining shares keep their original cost basis and exit
        target. execution_price is accepted per the task's proposed
        signature and recorded on the lot for audit; it deliberately
        does NOT alter buy_price/target_sell_price.

        The lot is removed from open_lots only when its remaining shares
        fall to <= SHARE_EPSILON (floating-point drift), or on an
        omitted-sell_qty full close.
        """
        if lot not in self.open_lots:
            raise ValueError(f"Lot {lot.order_id!r} is not an open lot in this ledger")

        if sell_qty is None:
            # Original behavior: full close.
            if not completed:
                raise ValueError(
                    "close_lot(completed=False) with no sell_qty is ambiguous -- pass sell_qty "
                    "to record a partial fill, or completed=True for a full close."
                )
            self.open_lots.remove(lot)
            self.closed_lots.append(lot)
            return

        if sell_qty <= 0:
            raise ValueError(f"sell_qty must be positive, got {sell_qty}")
        if sell_qty > lot.shares + SHARE_EPSILON:
            raise ValueError(
                f"sell_qty ({sell_qty}) exceeds lot {lot.order_id!r}'s remaining shares ({lot.shares}). "
                "This usually means a cumulative broker quantity was passed instead of an incremental one."
            )

        lot.shares -= sell_qty
        if execution_price is not None:
            lot.last_execution_price = execution_price

        if lot.shares <= SHARE_EPSILON:
            lot.shares = 0.0
            self.open_lots.remove(lot)
            self.closed_lots.append(lot)
