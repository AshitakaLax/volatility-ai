"""
TrailingTargetPolicy -- an exit target that follows the peak price a
lot has already reached, instead of staying where it was at entry.

--------------------------------------------------------------------
THE PROBLEM THIS EXISTS TO FIX

Every lot in this system gets target_sell_price fixed at creation from
a single profit_target (src/ledger.py). That is correct and safe, but
it has one consequence the sweeps made concrete: the best configuration
found across every sweep to date runs profit_target=0.75, meaning a lot
only becomes marketable once it has gained 75%. Measured on the
10.63-year TQQQ SIP dataset, that configuration ended with 6,000 lots
still open at the end of the run -- capital committed to targets that
the price never came back to.

A lot that rose 60% and then fell back is, under a fixed target, worth
exactly as little as a lot that never moved: neither is sellable. The
unrealized gain is real but structurally unreachable.

--------------------------------------------------------------------
WHAT THIS DOES

Track the peak price each lot has seen since entry, and set its target
to trail that peak by trail_pct:

    trailed_price = peak_price * (1 - trail_pct)
    new_target    = max(trailed_price, buy_price * (1 + min_profit_target))

converted back into a profit_target so src/ledger.Lot.retarget can keep
target_sell_price and profit_target consistent (see that method for why
the derivation must be preserved).

TRAILING ONLY ENGAGES ONCE THE TRAILED PRICE BEATS THE FLOOR. A lot
sits at its full original target -- exactly as if trailing were off --
until its peak has risen enough that trailing off that peak lands
somewhere genuinely better than min_profit_target.

That guard is stricter than it first appears necessary to be, and the
reason is a bug that took two attempts to kill. observe() seeds a fresh
lot's peak from buy_price, so trailed_price on a lot's very first tick
is buy_price * (1 - trail_pct) -- already below cost for any trail_pct
> 0. The first fix guarded on trailed_price > buy_price, which stopped
the collapse on tick one but left the shape of the bug intact: with
new_target = max(trailed_price, floor_price) underneath, the floor was
an ATTRACTOR rather than a bound. The moment that guard released,
trailed_price was by construction barely above buy_price and so far
below the floor, max() picked the floor, and ratchet-down-only locked
the lot there permanently. Every trail_pct collapsed to the same
target, differing only in when.

Both failures were caught from sweep output rather than by inspection,
which is worth remembering: identical results across a swept parameter
are the symptom to watch for. See propose() for the full history.

--------------------------------------------------------------------
RATCHET-DOWN ONLY, which is the safety property that makes this simple

A target may only ever move DOWN, never up. Three things fall out of
that single rule, none of which need extra machinery:

  - A lot can only become MORE likely to sell, never less. Nothing
    this policy does can strand a lot that was previously sellable.
  - No thrash. The target is monotonic per lot, so a price oscillating
    around a level cannot walk the target up and down repeatedly.
  - Live in-flight sells stay safe. A resting sell was submitted at the
    old target; since targets only fall, a resting order can never be
    left above a newly-RAISED target and fill below what the lot now
    asks. (src/live_trading_loop.py additionally skips lots with a sell
    in flight -- belt and braces, not redundancy: that skip is what
    keeps the ledger and the broker's resting order agreeing on one
    price.)

--------------------------------------------------------------------
THE FLOOR IS NOT THE NO-LOSS GUARD

min_profit_target floors how far the target may fall. It is a
POLICY floor ("do not bother exiting for less than this"), NOT a safety
mechanism -- src/no_loss_guard.py is the safety mechanism, it reads
buy_price rather than any target, and it rejects a losing sell no
matter what target this policy computed. Setting min_profit_target to
something tiny does not make a loss possible; it just makes the policy
willing to ask for very little.

State ownership: this object owns the per-lot peak prices and nothing
else. It mutates no lot -- propose() returns a number and the caller
decides whether to apply it via Lot.retarget.
"""

from __future__ import annotations

from src.exceptions import ConfigurationError


class TrailingTargetPolicy:
    """Peak-trailing exit targets, ratcheting down only.

    Not a SizingStrategy: this governs EXITS, while SizingStrategy
    governs entries and size. Strategies compose one of these rather
    than inheriting from it, so a strategy can opt into trailing exits
    without changing how it sizes.
    """

    def __init__(self, trail_pct: float, min_profit_target: float = 0.001) -> None:
        """Configure the trail.

        trail_pct is measured from the peak, so 0.10 means "exit once
        price falls 10% below the best level this lot has seen".
        """
        if not 0.0 < trail_pct < 1.0:
            raise ConfigurationError(f"trail_pct must be in (0, 1), got {trail_pct}")
        if min_profit_target <= 0:
            raise ConfigurationError(
                f"min_profit_target must be positive, got {min_profit_target}"
            )
        self.trail_pct = trail_pct
        self.min_profit_target = min_profit_target
        # order_id -> highest price seen while this lot was open.
        self._peaks: dict[str, float] = {}

    def observe(self, lot, price: float) -> float:
        """Record a price for this lot and return its running peak.

        Seeded from buy_price rather than from the first observed price:
        a lot that only ever falls should trail from what it cost, not
        from wherever it happened to be first looked at.
        """
        peak = self._peaks.get(lot.order_id)
        if peak is None:
            peak = lot.buy_price
        if price > peak:
            peak = price
        self._peaks[lot.order_id] = peak
        return peak

    def propose(self, lot, price: float) -> float | None:
        """The profit_target this lot should now carry, or None to leave
        it alone.

        None rather than "the current value" so the caller can tell a
        deliberate no-change from a coincidental one, and skip both the
        mutation and its durable write.
        """
        if price <= 0 or lot.buy_price <= 0:
            return None
        peak = self.observe(lot, price)

        trailed_price = peak * (1.0 - self.trail_pct)
        floor_price = lot.buy_price * (1.0 + self.min_profit_target)

        # NOT YET ACTIVE: the trailed price must clear the FLOOR, not
        # merely the cost basis, before this policy proposes anything.
        #
        # observe() seeds a fresh lot's peak from buy_price (see that
        # method's docstring -- a lot that only ever falls should trail
        # from what it cost, not wherever it was first looked at). So on
        # a lot's very first tick, before price has moved at all,
        # trailed_price is buy_price * (1 - trail_pct): below cost for
        # any trail_pct > 0.
        #
        # This guard was originally `trailed_price <= lot.buy_price`,
        # which fixed the most violent form of the bug (collapse on tick
        # one) but not the bug itself. With `new_target_price =
        # max(trailed_price, floor_price)` underneath it, the floor was
        # an ATTRACTOR rather than a bound: the instant the guard
        # released -- at peak = buy_price / (1 - trail_pct), where
        # trailed_price is by construction barely above buy_price and
        # therefore far below the floor -- max() picked floor_price, and
        # ratchet-down-only locked the lot there forever. Every
        # trail_pct produced the same target, differing only in WHEN it
        # snapped. Verified twice from sweep output, a month apart:
        # first with a fixed 0.10 floor across profit_targets 0.30-1.00
        # (all four byte-identical), then again after scaling the floor
        # per-target to 50% of it, where trail_pct 0.05 and 0.10 still
        # returned identical results (2621.31% return, 91,608 trades) --
        # because scaling an attractor just moves it.
        #
        # Requiring trailed_price > floor_price makes the floor mean what
        # its docstring always claimed: a level the target may never fall
        # BELOW, never a level it is dragged DOWN TO. A lot now sits at
        # its full original target -- exactly as if trailing were off --
        # until the peak has risen enough that trailing off it lands
        # somewhere genuinely better than the floor. Since floor_price >
        # buy_price for any positive min_profit_target, this strictly
        # subsumes the old cost-basis guard.
        if trailed_price <= floor_price:
            return None

        # max() is now redundant given the guard, but kept as an
        # invariant: no proposal may ever land below the floor.
        new_target_price = max(trailed_price, floor_price)

        # Ratchet down only -- see the module docstring.
        if new_target_price >= lot.target_sell_price:
            return None

        return new_target_price / lot.buy_price - 1.0

    def forget(self, order_id: str) -> None:
        """Drop one closed lot's peak."""
        self._peaks.pop(order_id, None)

    def retain_lots(self, open_order_ids) -> None:
        """Drop the peaks of every lot that is no longer open.

        Without this the peak map grows for the life of the process --
        a 10-year minute backtest opens ~86k lots, and a live daemon
        closes them indefinitely. Guarded by a cheap size check because
        it runs every bar: rebuilding a 6,000-entry dict on each of a
        million bars would cost far more than the memory it reclaims,
        so it only rebuilds once the dead entries actually outnumber
        the live ones.
        """
        if len(self._peaks) <= 2 * len(open_order_ids) + 64:
            return
        self._peaks = {k: v for k, v in self._peaks.items() if k in open_order_ids}
