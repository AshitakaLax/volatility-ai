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

TRAILING ONLY ENGAGES ONCE THERE IS A REAL GAIN TO TRAIL. observe()
seeds a fresh lot's peak from buy_price, so trailed_price on a lot's
very first tick -- before price has moved at all -- is buy_price * (1
- trail_pct), already BELOW cost for any trail_pct > 0. Combined with
ratchet-down-only below, an earlier version of this method proposed
collapsing straight to the floor on that first tick, regardless of
trail_pct or whether price had moved, and the ratchet then locked it
there permanently -- verified directly against a config sweep before
being caught: every profit_target from 0.30 to 1.00 produced identical
results once any trail_pct was set. propose() now requires
trailed_price > buy_price before proposing anything at all, so a lot
sits at its full original target, exactly as if trailing were off,
until its peak has genuinely earned that.

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

        # NOT YET ACTIVE: observe() seeds a fresh lot's peak from
        # buy_price (see that method's docstring -- a lot that only
        # ever falls should trail from what it cost, not wherever it
        # was first looked at). That means on a lot's very first tick,
        # BEFORE price has moved at all, trailed_price is buy_price *
        # (1 - trail_pct) -- already BELOW cost for any trail_pct > 0.
        # Without this guard, max(trailed_price, floor_price) would
        # pick floor_price on that very first call regardless of
        # trail_pct or how wide the original target was, and the
        # ratchet-down-only rule would lock every lot there permanently
        # -- verified directly: with profit_target=0.30, this proposed
        # collapsing to a 0.10 floor on tick one, price unchanged from
        # buy_price. Trailing must only engage once the peak has risen
        # enough that trailing off it would still clear cost basis --
        # i.e. there is an actual gain to protect -- not from a
        # peak that is, so far, just the entry price relabeled.
        if trailed_price <= lot.buy_price:
            return None

        floor_price = lot.buy_price * (1.0 + self.min_profit_target)
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
