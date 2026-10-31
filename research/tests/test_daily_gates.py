"""research/strategies/daily_gates.py -- the ADX gate's ADX and DIs are
TA-Lib's, a session's value governs only the next session, the Hurst lever
is the documented clamp of the C-MR4 estimator, and hf_entry_gated uses
both (off, it is exactly hf_entry_gated)."""

from __future__ import annotations

from types import SimpleNamespace

import numpy as np
import pandas as pd
import pytest
import talib

from engine.core.exceptions import ConfigurationError
from research.strategies.daily_gates import AdxTrendGate, HurstStep
from research.strategies.mean_reversion import hurst_exponent


def _days(n: int = 120, seed: int = 4):
    rng = np.random.default_rng(seed)
    drift = np.r_[np.full(n // 2, 0.004), np.full(n - n // 2, -0.006)]
    close = 100 * np.exp(np.cumsum(drift + rng.normal(0, 0.01, n)))
    high = close * (1 + rng.uniform(0.001, 0.02, n))
    low = close * (1 - rng.uniform(0.001, 0.02, n))
    return high, low, close


def _bars(high, low, close):
    """Two regular-session bars a day; the second carries the day's range."""
    out = []
    for k, day in enumerate(pd.bdate_range("2023-01-02", periods=len(close))):
        ts = pd.Timestamp(day).tz_localize("America/New_York") + pd.Timedelta(hours=9, minutes=30)
        mid = (high[k] + low[k]) / 2
        out.append(SimpleNamespace(timestamp=ts, time_of_day_flag=0, high=mid, low=mid, close=mid))
        out.append(
            SimpleNamespace(
                timestamp=ts + pd.Timedelta(minutes=1),
                time_of_day_flag=1,
                high=high[k],
                low=low[k],
                close=close[k],
            )
        )
    return out


def test_the_adx_and_its_dis_are_ta_libs():
    high, low, close = _days()
    gate = AdxTrendGate("strong_trend", period=14)
    adx, pdi, mdi = [], [], []
    for bar in _bars(high, low, close):
        gate.observe(bar)
        if bar.time_of_day_flag == 0:  # a new session: the previous one has closed
            adx.append(gate.adx)
            pdi.append(gate.plus_di)
            mdi.append(gate.minus_di)
    # adx[k] is read at the start of session k: through session k - 1.
    want = talib.ADX(high, low, close, timeperiod=14)[:-1]
    got = np.array([np.nan if v is None else v for v in adx[1:]])
    np.testing.assert_allclose(got, want, rtol=1e-9, equal_nan=True)
    np.testing.assert_allclose(
        [np.nan if v is None else v for v in pdi[1:]],
        talib.PLUS_DI(high, low, close, timeperiod=14)[:-1],
        rtol=1e-9,
        equal_nan=True,
    )
    np.testing.assert_allclose(
        [np.nan if v is None else v for v in mdi[1:]],
        talib.MINUS_DI(high, low, close, timeperiod=14)[:-1],
        rtol=1e-9,
        equal_nan=True,
    )


def test_a_strong_trend_pauses_the_next_session_whole():
    high, low, close = _days()
    gate = AdxTrendGate("strong_trend", period=14, threshold=20.0)
    by_session: dict = {}
    for bar in _bars(high, low, close):
        gate.observe(bar)
        by_session.setdefault(bar.timestamp.date(), set()).add(gate.suppressed)
    assert all(len(states) == 1 for states in by_session.values())  # set once a session
    assert any(True in states for states in by_session.values())
    assert gate.episodes >= 1


def test_downtrend_mode_pauses_only_when_minus_di_leads():
    high, low, close = _days()
    gate = AdxTrendGate("strong_downtrend", period=14, threshold=20.0)
    for bar in _bars(high, low, close):
        gate.observe(bar)
        if gate.suppressed:
            assert gate.minus_di > gate.plus_di


@pytest.mark.parametrize("bad", [{"mode": "up"}, {"threshold": 0.0}, {"period": 1}])
def test_bad_adx_parameters(bad):
    with pytest.raises(ConfigurationError):
        AdxTrendGate(**{"mode": "strong_trend", **bad})


def test_the_hurst_multiplier_is_the_clamped_ratio_from_completed_sessions():
    high, low, close = _days(200)
    lever = HurstStep(1.5, window=60, max_lag=20, lo=0.5, hi=2.0)
    bars = _bars(high, low, close)
    for k, bar in enumerate(bars):
        lever.observe(bar)
        session = k // 2
        if bar.time_of_day_flag == 0 and session >= 61:
            h = hurst_exponent(np.log(close[session - 60 : session]), 20)
            assert lever.hurst == pytest.approx(h)
            assert lever.multiplier == pytest.approx(float(np.clip((h / 0.5) ** 1.5, 0.5, 2.0)))


def test_hurst_lever_is_one_until_its_window_fills_and_refuses_a_bad_clamp():
    lever = HurstStep(1.0, window=60)
    assert lever.multiplier == 1.0
    with pytest.raises(ConfigurationError):
        HurstStep(1.0, lo=1.5, hi=2.0)


def test_hf_entry_gated_wires_both_levers():
    from research.strategies.gated_local_reference_sizing import GatedLocalReferenceSizing

    base = {"per_lot_pct": 0.001, "lookback_days": 0.5, "bars_per_day": 390}
    off = GatedLocalReferenceSizing(**base)
    on = GatedLocalReferenceSizing(**base, adx_gate="strong_trend", hurst_step_exponent=1.0)
    assert on.adx in on._gates and off.adx not in off._gates
    assert on.hurst_step.enabled and not off.hurst_step.enabled
    assert on.live_history_sessions() >= 101
    ctx = SimpleNamespace(high=100.0, low=99.0, close=99.5, open=99.8)
    on.hurst_step.multiplier = 2.0
    wide = on._grid_trigger_level(ctx, 100.0, 0.01)
    on.hurst_step.multiplier = 1.0
    plain = on._grid_trigger_level(ctx, 100.0, 0.01)
    assert plain == off._grid_trigger_level(ctx, 100.0, 0.01)
    assert wide < plain  # a wider step buys lower
