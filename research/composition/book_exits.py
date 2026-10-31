"""
Sell policies cut out of the strategies whose buying and selling were one
design (Phase 4 of docs/research/buy-sell-composition.md): Ultimate's regime
exit, and the exposure books' rebalancing sales.

Each is a SUBCLASS of the original strategy, used for its sell side only --
its record_tick, wants_lot_retargeting, adjust_profit_target, retain_lots and
lots_to_liquidate are the original code -- so composed with its own buy side
it is the original exactly (research/tests/test_composition_books.py). It
keeps its own copy of the signal it sells on (the NATR regime, the daily
exposure target): duplicated work, accepted so neither side reads the other.

  ultimate_exit        calm lots sold at liquidate_minute of the first
                       turbulent session; reversal lots exit at
                       reversal_target, optionally sold on the flip back to
                       calm. A lot tagged by its buyer (Lot.entry_tag) is
                       classed by the tag; an untagged one by the mode it was
                       bought in, as Ultimate does.
  rsp_rebalance        whole lots, newest first, down to Ultimate-RSP's daily
  ursp_rebalance       exposure target (URSP's graded bear gate, the catalog's
  catalog_rebalance    long-or-cash signal): a "risk cap" for any buyer

All four sell at the market for reasons other than price, so they are on the
loss-capable track: execution.allow_signal_exit or they sell nothing.
"""

from __future__ import annotations

from datetime import date

from research.composition.exits import register
from research.strategies.catalog_exposure_sizing import CatalogExposureSizing
from research.strategies.gated_local_reference_sizing import GatedLocalReferenceSizing
from research.strategies.ultimate_rsp_sizing import UltimateRspSizing
from research.strategies.ultimate_sizing import TURBULENT, UltimateSizing
from research.strategies.ultimate_ursp_sizing import UltimateUrspSizing

# The buy-side parameters Ultimate's constructor requires. Its SELL side
# never reads them -- the champion's rolling windows and sizing only buy --
# so the exit fixes them rather than asking for them.
_UNUSED_BUY_PARAMS = {"per_lot_pct": 0.001, "lookback_days": 0.05, "bars_per_day": 390}


class UltimateExit(UltimateSizing):
    """Ultimate's regime exit and reversal targets, for any buyer."""

    exit_id = "ultimate_exit"
    label = "Ultimate's regime exit"
    can_realize_loss = True

    def __init__(
        self,
        regime_by_date: dict[date, bool] | None = None,
        natr_period: int = 10,
        natr_lookback: int = 100,
        regime_min_hold: int = 5,
        bear_dd: float | None = None,
        bear_window: int = 60,
        bear_sma: int | None = None,
        reversal_target: float = 0.06,
        liquidate_reversal_on_calm: bool = False,
        liquidate_minute: int = 60,
    ) -> None:
        super().__init__(
            **_UNUSED_BUY_PARAMS,
            regime_by_date=regime_by_date,
            natr_period=natr_period,
            natr_lookback=natr_lookback,
            regime_min_hold=regime_min_hold,
            bear_dd=bear_dd,
            bear_window=bear_window,
            bear_sma=bear_sma,
            reversal_target=reversal_target,
            liquidate_reversal_on_calm=liquidate_reversal_on_calm,
            liquidate_minute=liquidate_minute,
        )

    def adjust_profit_target(self, lot, context) -> float | None:
        tag = getattr(lot, "entry_tag", None)
        if tag is None:
            return super().adjust_profit_target(lot, context)
        # A tagged lot is classed by what its buyer said, not by the mode.
        proposed = GatedLocalReferenceSizing.adjust_profit_target(self, lot, context)
        if lot.order_id in self._known_ids:
            return proposed
        self._known_ids.add(lot.order_id)
        if tag == "reversal":
            self._reversal_ids.add(lot.order_id)
            self.reversal_buys += 1
            return self.reversal_target
        return proposed

    def resume(self, open_lots) -> None:
        lots = list(open_lots)
        super().resume(lots)
        for lot in lots:
            if lot.entry_tag == "reversal":
                self._reversal_ids.add(lot.order_id)
            elif lot.entry_tag is not None:
                self._reversal_ids.discard(lot.order_id)


class RspRebalance(UltimateRspSizing):
    """Ultimate-RSP's sales down to its daily exposure target."""

    exit_id = "rsp_rebalance"
    label = "Rebalance down to RSP's exposure target"
    can_realize_loss = True


class UrspRebalance(UltimateUrspSizing):
    """Ultimate-URSP's sales down to its exposure target (graded bear gate)."""

    exit_id = "ursp_rebalance"
    label = "Rebalance down to URSP's exposure target"
    can_realize_loss = True


class CatalogRebalance(CatalogExposureSizing):
    """The catalog exposure book's sales down to its signal's target."""

    exit_id = "catalog_rebalance"
    label = "Rebalance down to a catalog signal's target"
    can_realize_loss = True


register(UltimateExit, {"liquidate_minute": 60, "reversal_target": 0.06})
register(RspRebalance, {})
register(UrspRebalance, {})
register(CatalogRebalance, {"catalog_signal": "kalman_trend", "execute_minute": 60})

# Ultimate is built on regular-session bars; so is its exit (its minutes are
# the session's). The exposure books are too.
assert TURBULENT and UltimateExit.regular_session_only
