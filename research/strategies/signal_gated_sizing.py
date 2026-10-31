"""
hf_entry_gated plus the ranked list's single-symbol signal gates.

strategy_id: hf_signal_gated

Identical to GatedLocalReferenceSizing (hf_entry_gated) in every respect
-- the champion's trigger, sizing, scalers and exits, and that class's own
gates -- except that it may also refuse to buy while one of the gates in
research/strategies/signal_gates.py is shut. Every new gate defaults to
"off", and with all of them off it is hf_entry_gated exactly:
research/tests/test_signal_gated_sizing.py runs both over the regression
fixture under both fill models and asserts identical results.

WHY A NEW STRATEGY ID. hf_entry_gated is traded (config/live_profiles/
hf-entry-gated-rsp.yaml), and its class, defaults and parameter form stay
byte-for-byte as they were. These gates are new and unmeasured; putting
them on a separate id keeps them off every running deployment until one
is chosen on purpose.

HOW A GATE BLOCKS A BUY is the parent's mechanism: the gates are appended
to the parent's `_gates`, so record_tick folds them into the same
entry_suppressed flag and _grid_trigger_level returns NO_BUY_LEVEL while
any is shut. Gates govern NEW exposure only; open lots exit at their
targets through the no-loss guard, so no configuration realises a loss
and none needs execution.allow_signal_exit.

    RK14   high52_gate="near_high"            52-week-high proximity
    RK55   adx_gate="strong_downtrend"        ADX with -DI > +DI
    RK64   ribbon_gate="bearish"              moving-average ribbon
    RK79   gap_gate="gap_down"                opening-gap continuation
    RK112  kama_gate="below_falling"          Kaufman adaptive MA
    RK147  zscore_gate="oversold"             MA z-score reversion (permission)
    RK161  band_gate="lower_band"             Bollinger reversion (permission)
    RK168  term_gate="backwardation"          VIX / VIX3M curve (needs term_path)
    RK208  avwap_gate="swing_high"|"swing_low" anchored VWAP
    RK243  anomaly_gate="price"|"price_volume" EWM anomaly bars
    RK253  imbalance_gate="sell_imbalance"     volume-clock order imbalance
    RK294  barrier_gate="classifier"          triple-barrier logistic model
    RK297  hurst_gate="adaptive_band"         Hurst-scaled reversion bands

UNMEASURED: none of these has been swept.
"""

from __future__ import annotations

from research.strategies.gated_local_reference_sizing import GatedLocalReferenceSizing
from research.strategies.signal_gates import (
    AdxTrendGate,
    AnchoredVwapGate,
    AnomalyGate,
    BandReversionGate,
    FiftyTwoWeekHighGate,
    GapGate,
    HurstBandGate,
    KamaTrendGate,
    RibbonGate,
    TermStructureGate,
    TripleBarrierGate,
    VolumeImbalanceGate,
)


class SignalGatedSizing(GatedLocalReferenceSizing):
    """hf_entry_gated with the signal gates. See module docstring.

    The constructor repeats every parent parameter explicitly, for the
    reason GatedLocalReferenceSizing gives: the backtest form and
    analyze_annual.py read inspect.signature, which a **kwargs passthrough
    would hide. test_signature_mirrors_the_parent fails when the parent
    gains a parameter this class does not repeat.
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
        # -- RK14 52-week high (signal_gates.FiftyTwoWeekHighGate) ---------
        high52_gate: str = "off",
        high52_window: int = 252,
        high52_threshold: float = 0.8,
        # -- RK55 ADX trend filter (AdxTrendGate) -----------------------------
        adx_gate: str = "off",
        adx_period: int = 14,
        adx_threshold: float = 25.0,
        # -- RK64 moving-average ribbon (RibbonGate) --------------------------
        ribbon_gate: str = "off",
        ribbon_spans: str = "10,20,50,100",
        ribbon_ma: str = "ema",
        # -- RK79 opening gap (GapGate) ---------------------------------------
        gap_gate: str = "off",
        gap_threshold: float = 0.01,
        gap_release: str = "fill",
        # -- RK112 KAMA trend (KamaTrendGate) ---------------------------------
        kama_gate: str = "off",
        kama_period: int = 10,
        kama_fast: int = 2,
        kama_slow: int = 30,
        # -- RK147 moving-average z-score reversion (BandReversionGate) -------
        zscore_gate: str = "off",
        zscore_candle_minutes: int = 30,
        zscore_window: int = 20,
        zscore_k: float = 2.0,
        # -- RK161 Bollinger band reversion (BandReversionGate) ---------------
        band_gate: str = "off",
        band_candle_minutes: int = 30,
        band_window: int = 20,
        band_k: float = 2.0,
        # -- RK168 VIX term structure (TermStructureGate) ---------------------
        term_gate: str = "off",
        term_path: str = "",
        term_threshold: float = 1.0,
        term_smooth: int = 1,
        # -- RK208 anchored VWAP (AnchoredVwapGate) ---------------------------
        avwap_gate: str = "off",
        avwap_sessions: int = 20,
        # -- RK243 price/volume anomalies (AnomalyGate) -----------------------
        anomaly_gate: str = "off",
        anomaly_span: int = 60,
        anomaly_z: float = 4.0,
        anomaly_hold_bars: int = 30,
        # -- RK253 volume-clock imbalance (VolumeImbalanceGate) ---------------
        imbalance_gate: str = "off",
        imbalance_bars_per_session: int = 50,
        imbalance_window: int = 20,
        imbalance_threshold: float = 0.3,
        # -- RK294 triple-barrier classifier (TripleBarrierGate) --------------
        barrier_gate: str = "off",
        barrier_horizon: int = 10,
        barrier_profit: float = 0.05,
        barrier_loss: float = 0.05,
        barrier_min_samples: int = 250,
        barrier_threshold: float = 0.5,
        barrier_retrain: int = 20,
        # -- RK297 Hurst-adaptive bands (HurstBandGate) -----------------------
        hurst_gate: str = "off",
        hurst_candle_minutes: int = 30,
        hurst_window: int = 100,
        hurst_max_lag: int = 20,
        hurst_k: float = 2.0,
        hurst_trend_cutoff: float = 0.65,
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
        # Every gate is built, so validated, even when off -- the parent's
        # convention.
        self.high52 = FiftyTwoWeekHighGate(
            high52_gate, window=high52_window, threshold=high52_threshold
        )
        self.adx = AdxTrendGate(adx_gate, period=adx_period, threshold=adx_threshold)
        self.ribbon = RibbonGate(ribbon_gate, spans=ribbon_spans, ma=ribbon_ma)
        self.gap = GapGate(gap_gate, threshold=gap_threshold, release=gap_release)
        self.kama = KamaTrendGate(kama_gate, period=kama_period, fast=kama_fast, slow=kama_slow)
        self.zscore = BandReversionGate(
            zscore_gate,
            name="zscore_gate",
            modes=("off", "oversold"),
            candle_minutes=zscore_candle_minutes,
            window=zscore_window,
            k=zscore_k,
        )
        self.band = BandReversionGate(
            band_gate,
            name="band_gate",
            modes=("off", "lower_band"),
            candle_minutes=band_candle_minutes,
            window=band_window,
            k=band_k,
        )
        self.term = TermStructureGate(
            term_gate, path=term_path, threshold=term_threshold, smooth=term_smooth
        )
        self.avwap = AnchoredVwapGate(avwap_gate, sessions=avwap_sessions)
        self.anomaly = AnomalyGate(
            anomaly_gate, span=anomaly_span, z=anomaly_z, hold_bars=anomaly_hold_bars
        )
        self.imbalance = VolumeImbalanceGate(
            imbalance_gate,
            bars_per_session=imbalance_bars_per_session,
            window=imbalance_window,
            threshold=imbalance_threshold,
        )
        self.barrier = TripleBarrierGate(
            barrier_gate,
            horizon=barrier_horizon,
            profit=barrier_profit,
            loss=barrier_loss,
            min_samples=barrier_min_samples,
            threshold=barrier_threshold,
            retrain=barrier_retrain,
        )
        self.hurst = HurstBandGate(
            hurst_gate,
            candle_minutes=hurst_candle_minutes,
            window=hurst_window,
            max_lag=hurst_max_lag,
            k=hurst_k,
            trend_cutoff=hurst_trend_cutoff,
        )
        self.signal_gates = (
            self.high52,
            self.adx,
            self.ribbon,
            self.gap,
            self.kama,
            self.zscore,
            self.band,
            self.term,
            self.avwap,
            self.anomaly,
            self.imbalance,
            self.barrier,
            self.hurst,
        )
        self._gates = self._gates + tuple(g for g in self.signal_gates if g.enabled)

    def live_history_sessions(self) -> int:
        """The parent's, or the longest enabled signal gate's history."""
        sessions = super().live_history_sessions()
        for gate in self.signal_gates:
            if gate.enabled:
                sessions = max(sessions, gate.history_sessions)
        return sessions

    def diagnostics(self) -> dict[str, float | int | bool | str | None]:
        out = super().diagnostics()
        for gate in self.signal_gates:
            out[f"{gate.name}"] = gate.mode
            out[f"{gate.name}_suppressed_bars"] = gate.suppressed_bars
            out[f"{gate.name}_episodes"] = gate.episodes
        return out


__all__ = ["SignalGatedSizing"]
