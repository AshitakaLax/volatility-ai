"""
The ranked list's single-symbol algorithms, each selectable as its own
strategy id on the champion grid.

strategy ids: rk<ledger number>_<signal>, e.g. rk44_supertrend

LibrarySizing is GatedLocalReferenceSizing (hf_entry_gated) plus ONE
component from research/strategies/signal_library.py, chosen by `signal`
and tuned by `signal_params` ("k=v,k=v"). Every library strategy id maps to
this class with its own committed default for `signal` (param_schema.py),
so each algorithm is picked from the strategy list by name. With signal="off" it is hf_entry_gated
exactly (pinned by research/tests/test_library_sizing.py).

A component is a gate (folded into the parent's entry_suppressed, so the
grid level becomes unreachable while it is shut), a sizer (each new lot
times its multiplier) or a level (the buy level moved down, never up).
None of them sells, and no exit hook is overridden here, so no
configuration realises a loss or needs execution.allow_signal_exit.

WHY A NEW CLASS. hf_entry_gated and hf_signal_gated stay exactly as they
were; nothing traded changes. UNMEASURED: none of these has been swept.
"""

from __future__ import annotations

from engine.core.market_context import MarketContext
from research.strategies.gated_local_reference_sizing import (
    NO_BUY_LEVEL,
    GatedLocalReferenceSizing,
)
from research.strategies.signal_library import SIGNALS, build_signal

SIGNAL_NAMES: tuple[str, ...] = ("off", *sorted(SIGNALS))


class LibrarySizing(GatedLocalReferenceSizing):
    """hf_entry_gated plus one signal-library component. See module docstring.

    The constructor repeats every parent parameter explicitly, as
    GatedLocalReferenceSizing does, so the run form and analyze_annual.py
    see them through inspect.signature.
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
        dd_throttle_full: float = 0.6,
        dd_throttle_floor: float = 0.25,
        implied_vol_exponent: float = 0.0,
        implied_vol_scale_min: float = 0.5,
        implied_vol_scale_max: float = 2.0,
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
        momentum_gate: str = "off",
        momentum_early_minutes: int = 30,
        momentum_late_minutes: int = 30,
        momentum_threshold: float = 0.0,
        vol_target: float | None = None,
        vol_target_days: int = 20,
        vol_target_estimator: str = "yang_zhang",
        vol_target_min: float = 0.25,
        vol_target_max: float = 2.0,
        bounce_gate: str = "off",
        bounce_candle_minutes: int = 30,
        bounce_window: int = 20,
        bounce_k: float = 2.0,
        bounce_hold_candles: int = 8,
        bounce_max_span: int = 40,
        bounce_tolerance: float = 0.01,
        rsi_gate: str = "off",
        rsi_candle_minutes: int = 30,
        rsi_period: int = 14,
        rsi_overbought: float = 70.0,
        rsi_tolerance: float = 5.0,
        rsi_hold_candles: int = 8,
        # -- the algorithm (research/strategies/signal_library.py) --------
        signal: str = "off",
        signal_params: str = "",
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
            breakdown_gate=breakdown_gate,
            breakdown_release=breakdown_release,
            dt_lookback_days=dt_lookback_days,
            dt_k=dt_k,
            orb_minutes=orb_minutes,
            pattern_gate=pattern_gate,
            pattern_candle_minutes=pattern_candle_minutes,
            pattern_hold_candles=pattern_hold_candles,
            pattern_lower_shadow=pattern_lower_shadow,
            pattern_body_size=pattern_body_size,
            pattern_body_lookback=pattern_body_lookback,
            momentum_gate=momentum_gate,
            momentum_early_minutes=momentum_early_minutes,
            momentum_late_minutes=momentum_late_minutes,
            momentum_threshold=momentum_threshold,
            vol_target=vol_target,
            vol_target_days=vol_target_days,
            vol_target_estimator=vol_target_estimator,
            vol_target_min=vol_target_min,
            vol_target_max=vol_target_max,
            bounce_gate=bounce_gate,
            bounce_candle_minutes=bounce_candle_minutes,
            bounce_window=bounce_window,
            bounce_k=bounce_k,
            bounce_hold_candles=bounce_hold_candles,
            bounce_max_span=bounce_max_span,
            bounce_tolerance=bounce_tolerance,
            rsi_gate=rsi_gate,
            rsi_candle_minutes=rsi_candle_minutes,
            rsi_period=rsi_period,
            rsi_overbought=rsi_overbought,
            rsi_tolerance=rsi_tolerance,
            rsi_hold_candles=rsi_hold_candles,
        )
        if signal != "off" and signal not in SIGNALS:
            from engine.core.exceptions import ConfigurationError

            raise ConfigurationError(f"signal must be one of {SIGNAL_NAMES}, got {signal!r}")
        self.signal = signal
        self.signal_params = signal_params
        self.component = None if signal == "off" else build_signal(signal, signal_params)
        kind = getattr(self.component, "kind", None)
        if kind == "gate":
            self._gates = (*self._gates, self.component)
        self._observed = self.component if kind in ("sizer", "level") else None

    def record_tick(self, context: MarketContext) -> None:
        """The parent's per-bar state and gates, then a sizer's or level
        component's own state. Every component changes only here."""
        super().record_tick(context)
        if self._observed is not None:
            self._observed.observe(context)

    def live_history_sessions(self) -> int:
        sessions = super().live_history_sessions()
        if self.component is not None:
            sessions = max(sessions, int(self.component.history_sessions))
        return sessions

    def _grid_trigger_level(
        self, context: MarketContext, last_buy_price: float, step: float
    ) -> float:
        """The parent's level; a level component may only move it down."""
        level = super()._grid_trigger_level(context, last_buy_price, step)
        if level == NO_BUY_LEVEL or self.component is None or self.component.kind != "level":
            return level
        return min(level, self.component.adjust_level(level, context, step))

    def calculate_trade_value(self, context: MarketContext) -> float:
        """The parent's lot, times a sizer's multiplier. A sizing change
        only: it never sells, so it adds no way to realise a loss."""
        value = super().calculate_trade_value(context)
        if value <= 0 or self.component is None or self.component.kind != "sizer":
            return value
        return value * max(0.0, float(self.component.multiplier))

    def diagnostics(self) -> dict[str, float | int | bool | str | None]:
        out = super().diagnostics()
        out["signal"] = self.signal
        if self.component is not None:
            out["signal_kind"] = self.component.kind
            out["signal_suppressed"] = bool(getattr(self.component, "suppressed", False))
            out["signal_multiplier"] = float(getattr(self.component, "multiplier", 1.0))
            out["signal_episodes"] = int(getattr(self.component, "episodes", 0))
        return out


def library_strategy_ids() -> dict[str, str]:
    """strategy id -> signal name, for every library algorithm."""
    from research.strategies.signal_library import strategy_id_for

    return {strategy_id_for(name): name for name in SIGNALS}


__all__ = ["SIGNAL_NAMES", "LibrarySizing", "library_strategy_ids"]
