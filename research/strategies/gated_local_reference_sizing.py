"""
HighFrequencyLocalReferenceSizing with entry-suppression gates.

strategy_id: hf_entry_gated

Identical to hf_local_reference in every respect -- trigger reference,
sizing, every scaler, trailing exits -- except that it may refuse to buy
at all on bars a gate in research/strategies/entry_gates.py has flagged.
With both gates "off" (the defaults) it is the champion, exactly:
research/tests/test_gated_local_reference_sizing.py runs both strategies
over the regression fixture under both fill models and asserts
identical results, not merely similar ones.

--------------------------------------------------------------------
WHY A SUBCLASS AND NOT MORE KNOBS ON THE CHAMPION

hf_local_reference is what the live deployment trades. A gate added to
it would put new branches on the hot path of a running strategy, with a
default that has to be argued to be a no-op rather than shown to be
one. As a subclass, the champion's code does not change at all, and
the claim "off means identical" is a test against the real class.

--------------------------------------------------------------------
HOW A GATE BLOCKS A BUY: THE LEVEL, NOT THE BOOLEAN

When any enabled gate is suppressed, _grid_trigger_level returns
NO_BUY_LEVEL (0.0) instead of the champion's
max(last_buy, rolling_high) * (1 - step).

Overriding _check_grid_trigger would NOT work, and that is not a style
preference. optimization_controller.py's intrabar path -- the fill model
every HF sweep uses -- never calls _check_grid_trigger; it asks for the
level and compares it with the bar's LOW. A boolean override would block
buys under fill_model="close" and silently do nothing under "intrabar".
regime_scaled_sizing.py documents the same trap. A level of 0.0 is
unreachable by construction: data_validation rejects non-positive
prices, so neither `close <= 0.0` nor `low <= 0.0` can ever be true.

Gate state changes ONLY in record_tick. _grid_trigger_level stays a pure
read, because the intrabar fill model may call it on a path the close
model does not, and a method that mutated state would give the two fill
models different grids.

--------------------------------------------------------------------
WHAT THIS DELIBERATELY DOES NOT DO

It does not override lots_to_liquidate or adjust_profit_target beyond
what the parent does. A gate governs NEW exposure only. Open lots exit
exactly as they would under the champion -- at target, through
no_loss_guard -- so this strategy realizes a loss under no
configuration, and needs no `execution.allow_signal_exit`.

It does not change the reference a pullback is measured from. When a
gate releases, the next buy is measured from the same
max(last_buy, rolling_high) it would have been. The rolling high is
advanced on every bar by the parent's record_tick whether or not the
gate is shut.

--------------------------------------------------------------------
UNMEASURED

No sweep has run this. config/probe_entry_gate_*.yaml pin every
champion parameter from config/best_known_2026-08-24.yaml and vary only
the gate, so a difference in the result is the gate's.
"""

from __future__ import annotations

from engine.core.market_context import MarketContext
from research.strategies.entry_gates import BreakdownGate, ShootingStarGate
from research.strategies.high_frequency_sizing import HighFrequencyLocalReferenceSizing

# Below every real price, so no bar can touch it -- see module docstring.
NO_BUY_LEVEL = 0.0


class GatedLocalReferenceSizing(HighFrequencyLocalReferenceSizing):
    """hf_local_reference that can decline to buy. See module docstring.

    The constructor repeats the parent's parameters explicitly rather
    than taking **kwargs. server/backtest.py builds the run form from
    inspect.signature(cls.__init__), and research/analysis/
    analyze_annual.py rebuilds strategies from sweep rows the same way;
    a **kwargs passthrough would hide every inherited parameter from
    both. The cost is that a new parent parameter must be added here
    too -- test_signature_mirrors_the_parent fails the moment it is not.
    """

    def __init__(
        self,
        per_lot_pct: float,
        lookback_days: float,
        bars_per_day: int,
        event_day_boost_multiplier: float = 1.0,
        earnings_day_boost_multiplier: float = 1.0,
        vol_scale_exponent: float = 0.0,
        vol_fast_days: float = 0.5,
        vol_slow_days: float = 20.0,
        vol_scale_min: float = 0.5,
        vol_scale_max: float = 2.0,
        time_of_day_exponent: float = 0.0,
        vol_measure: str = "stdev",
        volume_scale_exponent: float = 0.0,
        trail_pct: float | None = None,
        trail_min_profit_target: float = 0.001,
        weighted_event_boost_multiplier: float = 1.0,
        dd_throttle_start: float | None = None,
        dd_throttle_full: float = 0.60,
        dd_throttle_floor: float = 0.25,
        implied_vol_exponent: float = 0.0,
        implied_vol_scale_min: float = 0.5,
        implied_vol_scale_max: float = 2.0,
        # -- entry gates (research/strategies/entry_gates.py) ----------
        breakdown_gate: str = "off",
        breakdown_release: str = "reclaim",
        dt_lookback_days: int = 5,
        dt_k: float = 0.5,
        orb_minutes: int = 30,
        pattern_gate: str = "off",
        pattern_candle_minutes: int = 30,
        pattern_hold_candles: int = 4,
        pattern_lower_shadow: float = 0.2,
        pattern_body_size: float = 0.5,
        pattern_body_lookback: int = 20,
    ) -> None:
        super().__init__(
            per_lot_pct=per_lot_pct,
            lookback_days=lookback_days,
            bars_per_day=bars_per_day,
            event_day_boost_multiplier=event_day_boost_multiplier,
            earnings_day_boost_multiplier=earnings_day_boost_multiplier,
            vol_scale_exponent=vol_scale_exponent,
            vol_fast_days=vol_fast_days,
            vol_slow_days=vol_slow_days,
            vol_scale_min=vol_scale_min,
            vol_scale_max=vol_scale_max,
            time_of_day_exponent=time_of_day_exponent,
            vol_measure=vol_measure,
            volume_scale_exponent=volume_scale_exponent,
            trail_pct=trail_pct,
            trail_min_profit_target=trail_min_profit_target,
            weighted_event_boost_multiplier=weighted_event_boost_multiplier,
            dd_throttle_start=dd_throttle_start,
            dd_throttle_full=dd_throttle_full,
            dd_throttle_floor=dd_throttle_floor,
            implied_vol_exponent=implied_vol_exponent,
            implied_vol_scale_min=implied_vol_scale_min,
            implied_vol_scale_max=implied_vol_scale_max,
        )
        # Both are built (and validated) even when off, so a typo in a
        # disabled gate's parameters still fails at construction rather
        # than the day someone switches it on.
        self.breakdown = BreakdownGate(
            breakdown_gate,
            release=breakdown_release,
            dt_lookback_days=dt_lookback_days,
            dt_k=dt_k,
            orb_minutes=orb_minutes,
        )
        self.pattern = ShootingStarGate(
            pattern_gate,
            candle_minutes=pattern_candle_minutes,
            hold_candles=pattern_hold_candles,
            lower_shadow=pattern_lower_shadow,
            body_size=pattern_body_size,
            body_lookback=pattern_body_lookback,
        )
        # Only enabled gates are walked per bar. With both off this is
        # empty and record_tick adds one truthiness check to the parent's
        # cost -- the 1M-bar sweeps pay nothing for a feature they are
        # not using, same convention as the parent's _vol_enabled.
        self._gates = tuple(gate for gate in (self.breakdown, self.pattern) if gate.enabled)
        self._entry_suppressed = False

    def record_tick(self, context: MarketContext) -> None:
        """The parent's per-bar state first (rolling high, vol windows,
        capital baseline), then each enabled gate. Every gate change
        happens here and only here -- see module docstring."""
        super().record_tick(context)
        if self._gates:
            for gate in self._gates:
                gate.observe(context)
            self._entry_suppressed = any(gate.suppressed for gate in self._gates)

    @property
    def entry_suppressed(self) -> bool:
        """True while some enabled gate is blocking new buys."""
        return self._entry_suppressed

    def _grid_trigger_level(
        self, context: MarketContext, last_buy_price: float, step: float
    ) -> float:
        """NO_BUY_LEVEL while gated, else exactly the parent's level."""
        if self._entry_suppressed:
            return NO_BUY_LEVEL
        return super()._grid_trigger_level(context, last_buy_price, step)

    def diagnostics(self) -> dict[str, float | int | bool | str | None]:
        """Gate state and counts, for logging and the UI. Outside the
        SizingStrategy contract, as in regime_scaled_sizing.py."""
        return {
            "entry_suppressed": self._entry_suppressed,
            "breakdown_gate": self.breakdown.mode,
            "breakdown_level": self.breakdown.level,
            "breakdown_suppressed_bars": self.breakdown.suppressed_bars,
            "breakdown_episodes": self.breakdown.episodes,
            "pattern_gate": self.pattern.mode,
            "pattern_suppressed_bars": self.pattern.suppressed_bars,
            "pattern_episodes": self.pattern.episodes,
        }


__all__ = ["NO_BUY_LEVEL", "GatedLocalReferenceSizing"]
