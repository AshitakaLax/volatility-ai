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
    # The ledger holding this lot, set by register_buy. Exists so
    # retarget() can tell it that a target moved DOWN -- see
    # AssetLotLedger.get_marketable_lots' price bound. Without it a lot
    # retargeted through any path other than the ledger would leave that
    # bound above a now-reachable target and SILENTLY SKIP A SALE, which
    # a test caught the moment the bound was introduced.
    #
    # repr=False and compare=False: Lot already uses identity equality
    # (see the class docstring), and a back-reference in a repr would
    # recurse through the whole book.
    _ledger: object | None = field(default=None, init=False, repr=False, compare=False)

    def __post_init__(self) -> None:
        """Derive the exit target once, at creation.

        Computed here rather than on each access so it is fixed for the
        lot's lifetime unless retarget() is called explicitly: partial
        closes must not move an existing lot's exit price.
        """
        self.target_sell_price = self.buy_price * (1.0 + self.profit_target)

    def retarget(self, new_profit_target: float) -> None:
        """Move this lot's exit target. The ONLY sanctioned mutation of
        profit_target/target_sell_price after creation.

        Exists for trailing-target strategies (see src/trailing_target.py):
        an absolute target fixed at entry can leave a lot unsellable
        forever, while a target that trails the price it has already
        reached converts an unrealized peak into a reachable exit.

        WHY BOTH FIELDS MOVE TOGETHER, and why that is load-bearing:
        src/persistence.py's load_ledger asserts the persisted
        target_sell_price still equals buy_price * (1 + profit_target)
        and raises PersistenceError otherwise. That assertion is a real
        drift check worth keeping, so this method preserves the
        derivation rather than breaking it -- writing target_sell_price
        alone would make every restart fail on every retargeted lot.

        buy_price and shares are NEVER touched here. The cost basis is
        what src/no_loss_guard.py evaluates against, so moving a target
        can never permit a losing sell: the guard recomputes economics
        at the real fill price and rejects independently of whatever
        this lot claims its target is. A target is an ELIGIBILITY
        signal; the guard is the safety boundary.
        """
        if new_profit_target <= 0:
            raise ValueError(
                f"new_profit_target must be positive, got {new_profit_target}. A "
                "non-positive target would mark a lot marketable at or below its own "
                "cost basis, where the no-loss guard rejects every sell anyway."
            )
        self.profit_target = new_profit_target
        self.target_sell_price = self.buy_price * (1.0 + new_profit_target)
        # Notify the owning ledger, whoever called this. Doing it here
        # rather than at the call sites is what makes the bound safe: a
        # future caller cannot forget, because there is nothing to
        # remember.
        if self._ledger is not None:
            self._ledger.note_target_lowered(self.target_sell_price)


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
        # Running sum of open_lots' shares -- see total_open_shares.
        self._total_open_shares: float = 0.0
        # A LOWER BOUND on every open lot's target_sell_price -- see
        # get_marketable_lots. inf means "no open lots", which correctly
        # makes the guard reject every price.
        self._min_target_sell_price: float = float("inf")

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
        lot._ledger = self
        self.open_lots.append(lot)
        self._total_open_shares += shares
        if lot.target_sell_price < self._min_target_sell_price:
            self._min_target_sell_price = lot.target_sell_price
        return lot

    @property
    def total_open_shares(self) -> float:
        """Sum of open lots' shares, maintained incrementally.

        WHY THIS IS NOT `sum(lot.shares for lot in self.open_lots)`.
        The backtest marks the book to market on EVERY bar, and profiling
        showed that one line at 65% of total runtime after the
        retargeting fix: 62.7 million generator steps over a ~522-lot
        book across 120,000 bars.

        Every lot is the same symbol at the same bar, so the price is a
        common factor -- `sum(shares_i * price)` is `price *
        sum(shares_i)` -- and the share total only changes when a lot
        opens or closes, not on every bar. Maintaining it turns a
        per-bar walk of the whole book into one multiply.

        The invariant is maintained at the three mutation points
        (register_buy, and both branches of close_lot) and is asserted
        against a recomputed sum by
        tests/unit/test_ledger.py::test_the_running_share_total_matches_a_recomputed_sum.

        A ledger rebuilt by src/persistence.py appends to open_lots
        directly, bypassing register_buy, so that path calls
        resync_total_open_shares() explicitly.
        """
        return self._total_open_shares

    def resync_total_open_shares(self) -> float:
        """Rebuild ALL derived state from the open lots.

        For callers that populate open_lots directly (persistence
        restore) rather than through register_buy. O(n), so it is a
        restore-time operation, never a per-bar one.

        Restores three things, not one: the share total, the
        target-price bound, and each lot's back-reference to this ledger.
        The back-reference matters most -- a restored lot without it
        would retarget silently, leaving the bound stale-high and
        skipping a sale on a live account after a restart.
        """
        self._total_open_shares = sum(lot.shares for lot in self.open_lots)
        self._min_target_sell_price = min(
            (lot.target_sell_price for lot in self.open_lots), default=float("inf")
        )
        for lot in self.open_lots:
            lot._ledger = self
        return self._total_open_shares

    def _resync_if_flat(self) -> None:
        """Snap the running total to exactly 0.0 when the book empties.

        Incremental float arithmetic leaves a residue -- adding and
        subtracting the same shares in a different order does not
        cancel exactly -- and over a 10-year run with tens of thousands
        of round trips that residue would accumulate silently. A flat
        book is the one moment the true answer is known exactly and
        costs nothing to assert, and it happens often enough to bound
        the drift rather than let it compound.
        """
        if not self.open_lots:
            self._total_open_shares = 0.0
            # No lots means no reachable target; inf makes the bound
            # reject every price, which is exactly right for an empty
            # book and stops a stale low bound surviving it.
            self._min_target_sell_price = float("inf")

    def get_marketable_lots(self, current_price: float) -> list[Lot]:
        """Open lots whose profit target is met or exceeded at current_price.

        Returned in FIFO (registration) order. Does not mutate the LOTS
        -- callers are expected to close_lot() each one after a confirmed
        sell fill. It does maintain the internal price bound below.

        THE BOUND. This walked the entire open book on every bar and
        profiled at 30% of runtime once the bigger costs were removed --
        on a 200,000-bar slice with profit_target=1.00 it scanned a
        several-hundred-lot book 200,000 times and returned a sale on
        ZERO of them. `_min_target_sell_price` is a lower bound on every
        open lot's target, so a price below it cannot possibly make
        anything marketable and the scan is skipped outright.

        The bound is only ever allowed to be TOO LOW, never too high.
        Too low costs a scan that finds nothing; too high would skip a
        real sale, which the no-loss invariant makes the most dangerous
        error this class could commit. So:

          * register_buy lowers it when a new lot undercuts it.
          * retarget lowers it via note_target_lowered -- trailing
            ratchets targets DOWN, and a bound that did not hear about
            that would be too high, so decision_cycle notifies.
          * REMOVING a lot can only raise the true minimum, so the bound
            is simply left stale-low and self-heals below.

        When a scan finds nothing marketable, every open lot's target is
        above current_price, so the smallest of them is the exact
        minimum -- computed in the same pass that was already paid for,
        and stored. That is what keeps a stale-low bound from degrading
        back into a full scan every bar.
        """
        if current_price < self._min_target_sell_price:
            return []

        marketable = []
        lowest_unsold = float("inf")
        for lot in self.open_lots:
            target = lot.target_sell_price
            if current_price >= target:
                marketable.append(lot)
            elif target < lowest_unsold:
                lowest_unsold = target

        if not marketable:
            # Nothing qualified, so lowest_unsold is the true minimum
            # across the whole book. Tighten to it.
            self._min_target_sell_price = lowest_unsold
        return marketable

    def note_target_lowered(self, new_target: float) -> None:
        """Tell the ledger a lot's exit target moved DOWN.

        Called by decision_cycle after a trailing policy retargets, so
        the bound in get_marketable_lots cannot end up above a target
        that is now reachable -- which would silently skip a sale.
        Accepts any value and takes the minimum, so a caller that
        reports a RAISED target does no harm.
        """
        if new_target < self._min_target_sell_price:
            self._min_target_sell_price = new_target

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
            self._total_open_shares -= lot.shares
            self.open_lots.remove(lot)
            self.closed_lots.append(lot)
            self._resync_if_flat()
            return

        if sell_qty <= 0:
            raise ValueError(f"sell_qty must be positive, got {sell_qty}")
        if sell_qty > lot.shares + SHARE_EPSILON:
            raise ValueError(
                f"sell_qty ({sell_qty}) exceeds lot {lot.order_id!r}'s remaining shares ({lot.shares}). "
                "This usually means a cumulative broker quantity was passed instead of an incremental one."
            )

        before = lot.shares
        lot.shares -= sell_qty
        if execution_price is not None:
            lot.last_execution_price = execution_price

        if lot.shares <= SHARE_EPSILON:
            lot.shares = 0.0
            self.open_lots.remove(lot)
            self.closed_lots.append(lot)

        # Measured from the lot itself rather than assumed to be
        # sell_qty: the snap above zeroes a sub-epsilon remainder, so a
        # closing partial removes slightly MORE than was sold. Reading
        # the actual before/after is correct in both branches -- when the
        # lot closes, lot.shares is 0.0 and the whole remainder leaves.
        self._total_open_shares -= before - lot.shares
        self._resync_if_flat()
