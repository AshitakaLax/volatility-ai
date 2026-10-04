"""
One sleeve of a regime-switched book: the champion grid, trading only
while its regime is on, and closing its book when the regime turns off.

  sleeve="calm"       e.g. TQQQ, while NATR is below its median
  sleeve="turbulent"  e.g. QQQ, while NATR is above it -- the leverage
                      step-down: keep harvesting volatility through a
                      correction at a third of the exposure
  sleeve="always"     no regime; identical to GatedLocalReferenceSizing
                      (and so to the champion with gates off)

Two sleeves fed the SAME regime map are active on complementary sessions,
so their books never overlap except on the single bar where one
liquidates and the other may start buying. tools/leverage_stepdown.py
runs each sleeve through the real engine on its own instrument and
stitches the two P&L streams into one account -- see that tool for what
the stitch assumes.

--------------------------------------------------------------------
THE REGIME IS INJECTED, AND MUST ALREADY BE CAUSAL

regime_by_date maps a session date to True (calm) / False (turbulent).
The entry for D is read at D's first regular-session bar, so it must be
knowable before D opens -- research/strategies/natr_regime.calm_by_date
with its default lag=1 builds exactly that. This class cannot check it
and does not try: a map built from D's own bar (lag=0) is lookahead, and
the result will look better for it.

A date missing from the map keeps the last known regime (a gap in the
daily series is not a regime call -- tools/probe_stage3_engine made the
same choice for the same reason). Before the first known date the
sleeve is inactive: no position, rather than a guess.

--------------------------------------------------------------------
THE EXIT IS A REGIME EXIT, AND IT CAN REALIZE A LOSS

On the first regular-session bar of a session where the sleeve goes
from active to inactive, lots_to_liquidate returns every open lot. That
is the edge, not the level: it fires once per flip, so a lot the sleeve
could somehow still hold afterwards is not condemned again every bar.
Those sells go through engine/trading/no_loss_guard.py as
SellReason.SIGNAL_EXIT, at the bar's price -- the one path in this
system allowed to sell below cost basis -- and only when
`execution.allow_signal_exit` is also True. Without it the hook is inert
and the sleeve simply stops buying while it holds what it has.

While inactive, the trigger level is NO_BUY_LEVEL, through the same
seam the entry gates use (see gated_local_reference_sizing.py for why it
must be the level and not the boolean).

--------------------------------------------------------------------
RE-ENTRY IS MEASURED FROM THE MARKET, NOT FROM A STALE FILL

The champion's reference is max(last_buy_price, rolling_high). A sleeve
that sat out weeks of a crash comes back with last_buy_price still at
its pre-crash fill, so the level is far ABOVE the market and the first
buys trigger immediately -- and under fill_model="intrabar" they are
booked AT that level, a price the bar never traded (measured on
synthetic data: every buy of a re-entering sleeve filled above its
bar's high, by up to 734%). So from activation until the sleeve holds a
lot again, the reference is the rolling high alone. After that, the
champion's rule applies unchanged.

The underlying fill problem is not this class's: optimization_controller
fills an intrabar buy at the trigger level even when the whole bar
traded below it, which also hits the champion on ordinary bars and
gaps. That is an engine decision; see tools/leverage_stepdown.py
--fill-model.

--------------------------------------------------------------------
NOT REGISTERED YET

Deliberately absent from strategy_registry.py. A sleeve is half of a
two-instrument book, and the engine is single-symbol: the only honest
way to evaluate one today is alongside its counterpart, which is what
the tool does. Registering it would invite a single-sleeve YAML sweep
whose result means nothing on its own. When a portfolio-level allocator
exists, this class gets an explicit constructor signature (the run form
and analyze_annual both read signatures) and a registry entry together.
"""

from __future__ import annotations

from collections.abc import Mapping
from datetime import date

from engine.core.exceptions import ConfigurationError
from engine.core.market_context import MarketContext
from research.strategies.gated_local_reference_sizing import (
    NO_BUY_LEVEL,
    GatedLocalReferenceSizing,
)

SLEEVES: tuple[str, ...] = ("always", "calm", "turbulent")


class RegimeSleeveSizing(GatedLocalReferenceSizing):
    """The champion, gated to one regime. See module docstring."""

    def __init__(
        self,
        *,
        sleeve: str = "always",
        regime_by_date: Mapping[date, bool] | None = None,
        **params,
    ) -> None:
        super().__init__(**params)
        if sleeve not in SLEEVES:
            raise ConfigurationError(f"sleeve must be one of {SLEEVES}, got {sleeve!r}")
        if sleeve != "always" and not regime_by_date:
            raise ConfigurationError(f"sleeve={sleeve!r} needs a non-empty regime_by_date")
        self.sleeve = sleeve
        self._regime: dict[date, bool] = dict(regime_by_date or {})
        self._calm: bool | None = None
        self._day: int | None = None
        self._active = sleeve == "always"
        self._flipped_out = False
        self._fresh = False  # True from activation until a lot is held
        self.flips_out = 0
        self.active_sessions = 0
        self.sessions = 0

    def record_tick(self, context: MarketContext) -> None:
        super().record_tick(context)
        if self.sleeve == "always":
            return
        # The flip is an EDGE: true for exactly one bar.
        self._flipped_out = False
        if self._fresh and context.open_lot_count > 0:
            self._fresh = False  # a real, recent fill now anchors the reference
        # time_of_day_flag is read here only as a session boundary (-1 =
        # outside regular hours), never as a signal -- the same use
        # entry_gates.py makes of it. Its documented signal consumer
        # remains high_frequency_sizing's time-of-day scaler.
        minute = context.time_of_day_flag
        if minute < 0:
            return  # out of session: the regime is a per-session call
        day = context.timestamp.toordinal()
        if day == self._day:
            return
        self._day = day
        self.sessions += 1
        self._calm = self._regime.get(context.timestamp.date(), self._calm)
        was_active = self._active
        if self._calm is None:
            self._active = False
        else:
            self._active = self._calm if self.sleeve == "calm" else not self._calm
        if was_active and not self._active:
            self._flipped_out = True
            self.flips_out += 1
        if self._active and not was_active:
            self._fresh = True
        if self._active:
            self.active_sessions += 1

    @property
    def active(self) -> bool:
        return self._active

    def lots_to_liquidate(self, open_lots, context: MarketContext) -> list:
        """Every open lot, on the bar the regime turns this sleeve off."""
        return list(open_lots) if self._flipped_out else []

    def _grid_trigger_level(
        self, context: MarketContext, last_buy_price: float, step: float
    ) -> float:
        if not self._active:
            return NO_BUY_LEVEL
        if self._fresh and not self._entry_suppressed:
            rolling_high = self._trigger_rolling_high()
            reference = context.open if rolling_high is None else rolling_high
            return reference * (1.0 - step)
        return super()._grid_trigger_level(context, last_buy_price, step)

    def diagnostics(self) -> dict:
        out = super().diagnostics()
        out.update(
            sleeve=self.sleeve,
            sleeve_active=self._active,
            sleeve_flips_out=self.flips_out,
            sleeve_active_sessions=self.active_sessions,
            sleeve_sessions=self.sessions,
        )
        return out


__all__ = ["SLEEVES", "RegimeSleeveSizing"]
