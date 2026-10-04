"""research/strategies/intraday_gates.py -- catalog C-M1, C-MS3, C-X4, C-MR7."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import numpy as np
import pytest

from engine.core.exceptions import ConfigurationError
from engine.core.market_context import MarketContext
from research.strategies.intraday_gates import (
    NoiseAreaGate,
    RBreakerGate,
    SessionLotThrottle,
    VwapGate,
    noise_bounds,
    r_breaker_levels,
    session_vwap,
)


def ctx(day, minute, o, h=None, lo=None, c=None, volume=0.0, lots=0):
    """A regular-session bar: `day` is a day offset, `minute` minutes since 09:30 ET."""
    ts = datetime(2026, 1, 5, 14, 30, tzinfo=UTC) + timedelta(days=day, minutes=minute)
    h = max(o, c if c is not None else o) if h is None else h
    c = o if c is None else c
    lo = min(o, c) if lo is None else lo
    return MarketContext(
        timestamp=ts,
        open=o,
        high=h,
        low=lo,
        close=c,
        cash=0.0,
        equity=1.0,
        peak_equity=1.0,
        drawdown=0.0,
        open_lot_count=lots,
        bar_index=0,
        time_of_day_flag=minute,
        volume=volume,
    )


# ------------------------------------------------------------------ C-M1


def test_noise_bounds_adjust_for_an_overnight_gap():
    # Gap down (prior close 102 above today's open 100): the UPPER bound moves up.
    lower, upper = noise_bounds(100.0, 102.0, 0.01)
    assert lower == pytest.approx(100.0 * 0.99)
    assert upper == pytest.approx(102.0 * 1.01)
    # Gap up: the LOWER bound moves down.
    lower, upper = noise_bounds(100.0, 98.0, 0.01)
    assert lower == pytest.approx(98.0 * 0.99)
    assert upper == pytest.approx(100.0 * 1.01)


def _session(gate, day, moves_at, open_=100.0, minutes=(0, 15, 30, 45, 60, 90)):
    """Feed one session whose bar at minute m opens at open_*(1+moves_at.get(m, 0))."""
    for m in minutes:
        price = open_ * (1 + moves_at.get(m, 0.0))
        gate.observe(ctx(day, m, price))


def test_sigma_is_the_mean_absolute_move_over_the_lookback():
    gate = NoiseAreaGate("below_lower", lookback_days=3)
    for day, move in enumerate((0.010, -0.020, 0.006)):
        _session(gate, day, {30: move})
    gate.observe(ctx(3, 0, 100.0))  # a new session completes the third
    assert gate.sigma(30) == pytest.approx(np.mean([0.010, 0.020, 0.006]))


def test_no_gating_until_the_lookback_is_full():
    gate = NoiseAreaGate("below_lower", lookback_days=3)
    for day in range(2):
        _session(gate, day, {30: 0.01})
    _session(gate, 2, {30: -0.5})  # far below, but only 2 sessions of history
    assert not gate.suppressed and gate.episodes == 0


def test_gate_decides_only_at_half_hour_checks_and_resets_each_session():
    gate = NoiseAreaGate("below_lower", lookback_days=2)
    for day in range(2):
        _session(gate, day, {15: 0.01, 30: 0.01, 45: 0.01, 60: 0.01})
    # sigma = 0.01 at every minute; lower bound = 100 * 0.99 = 99 (no gap).
    gate.observe(ctx(2, 0, 100.0))
    gate.observe(ctx(2, 15, 98.0))  # below, but 09:45 is not a check
    assert not gate.suppressed
    gate.observe(ctx(2, 30, 98.0))  # 10:00 check: below -> blocked
    assert gate.suppressed and gate.episodes == 1
    gate.observe(ctx(2, 45, 99.5))  # back inside, but not a check: still blocked
    assert gate.suppressed
    gate.observe(ctx(2, 60, 99.5))  # 10:30 check: inside -> released
    assert not gate.suppressed
    gate.observe(ctx(2, 90, 90.0))
    assert gate.suppressed
    gate.observe(ctx(3, 0, 90.0))  # new session starts unblocked
    assert not gate.suppressed


def test_noise_gate_off_and_bad_parameters():
    gate = NoiseAreaGate()
    gate.observe(ctx(0, 30, 1.0))
    assert not gate.enabled and not gate.suppressed
    with pytest.raises(ConfigurationError):
        NoiseAreaGate("short")
    with pytest.raises(ConfigurationError):
        NoiseAreaGate("below_lower", lookback_days=0)


# ------------------------------------------------------------------ C-MS3


def test_session_vwap_is_volume_weighted_typical_price():
    highs, lows, closes, vols = [11, 13], [9, 11], [10, 12], [100, 300]
    expected = ((11 + 9 + 10) / 3 * 100 + (13 + 11 + 12) / 3 * 300) / 400
    assert session_vwap(highs, lows, closes, vols) == pytest.approx(expected)
    assert session_vwap([1], [1], [1], [0]) is None


def _vwap_warmup(gate, n=12, price=100.0):
    rng = np.random.default_rng(4)
    for m in range(n):
        p = price * (1 + rng.normal(0, 0.001))
        gate.observe(ctx(0, m, p, p * 1.0005, p * 0.9995, p, volume=1000))
    return gate


def test_vwap_property_uses_completed_bars_only():
    gate = VwapGate("far_falling", vol_window=3)
    bars = [(100, 101, 99, 100.5, 10), (100.5, 102, 100, 101, 30), (101, 101.5, 100.5, 101.2, 20)]
    for m, (o, h, lo, c, v) in enumerate(bars):
        gate.observe(ctx(0, m, o, h, lo, c, volume=v))
    # After observing bar 2, VWAP covers bars 0 and 1 (bar 2 is not history yet).
    expected = session_vwap([101, 102], [99, 100], [100.5, 101], [10, 30])
    assert gate.vwap == pytest.approx(expected)


def test_far_below_and_falling_blocks_but_far_below_and_rising_does_not():
    gate = _vwap_warmup(VwapGate("far_falling", far_k=3.0, vol_window=10))
    sigma, vwap = gate.sigma, gate.vwap
    far = vwap * (1 - 5 * sigma)
    gate.observe(ctx(0, 12, far, far, far * 0.999, far * 0.999, volume=1000))  # falling into it
    assert gate.suppressed and gate.episodes == 1
    rising = far * 1.0005  # above the previous close: a bounce
    gate.observe(ctx(0, 13, rising, rising, rising, rising, volume=1000))
    assert not gate.suppressed


def test_band_mode_also_requires_price_below_vwap():
    gate = _vwap_warmup(VwapGate("band", far_k=3.0, near_k=1.0, vol_window=10))
    above = gate.vwap * 1.001
    gate.observe(ctx(0, 12, above, volume=1000))
    assert gate.suppressed  # not cheap enough to buy


def test_no_volume_means_no_vwap_and_no_gating():
    gate = VwapGate("band", vol_window=2)
    for m in range(10):
        gate.observe(ctx(0, m, 100.0 - m))
    assert gate.vwap is None and not gate.suppressed


def test_vwap_gate_rejects_bad_parameters():
    with pytest.raises(ConfigurationError):
        VwapGate("band", far_k=1.0, near_k=2.0)
    with pytest.raises(ConfigurationError):
        VwapGate("far_falling", far_k=0.0)


# ------------------------------------------------------------------ C-X4


def test_lot_cap_blocks_for_the_rest_of_the_session_then_resets():
    gate = SessionLotThrottle("on", max_lots_per_session=2)
    gate.observe(ctx(0, 0, 100.0, lots=0))
    gate.observe(ctx(0, 1, 100.0, lots=1))
    assert not gate.suppressed
    gate.observe(ctx(0, 2, 100.0, lots=2))
    assert gate.suppressed and gate.buys_this_session == 2
    gate.observe(ctx(0, 3, 100.0, lots=1))  # a sell does not free the cap
    assert gate.suppressed
    gate.observe(ctx(1, 0, 100.0, lots=1))
    assert not gate.suppressed and gate.buys_this_session == 0


def test_minimum_spacing_between_buys():
    gate = SessionLotThrottle("on", min_bars_between_buys=2)
    gate.observe(ctx(0, 0, 100.0, lots=0))
    gate.observe(ctx(0, 1, 100.0, lots=1))  # buy on this bar
    assert gate.suppressed
    gate.observe(ctx(0, 2, 100.0, lots=1))
    assert gate.suppressed
    gate.observe(ctx(0, 3, 100.0, lots=1))
    assert not gate.suppressed


def test_adverse_buys_trigger_a_cooldown_that_doubles():
    gate = SessionLotThrottle("on", adverse_run=2, cooldown_bars=3)
    gate.observe(ctx(0, 0, 100.0, lots=0))
    gate.observe(ctx(0, 1, 100.0, c=100.0, lots=1))
    gate.observe(ctx(0, 2, 99.0, c=99.0, lots=2))  # adverse 1
    gate.observe(ctx(0, 3, 98.0, c=98.0, lots=3))  # adverse 2 -> 3-bar cooldown
    blocked = []
    for m in range(4, 9):
        gate.observe(ctx(0, m, 98.0, lots=3))
        blocked.append(gate.suppressed)
    assert blocked == [True, True, True, False, False]
    gate.observe(ctx(0, 9, 97.0, c=97.0, lots=4))  # adverse again
    gate.observe(ctx(0, 10, 96.0, c=96.0, lots=5))  # run of 2 -> cooldown doubles to 6
    blocked = []
    for m in range(11, 18):
        gate.observe(ctx(0, m, 96.0, lots=5))
        blocked.append(gate.suppressed)
    assert blocked == [True] * 6 + [False]


def test_throttle_off_never_blocks():
    gate = SessionLotThrottle(max_lots_per_session=1)
    for m, lots in enumerate((0, 1, 2, 3)):
        gate.observe(ctx(0, m, 100.0, lots=lots))
    assert not gate.suppressed


# ------------------------------------------------------------------ C-MR7


def test_r_breaker_levels_match_the_source():
    lv = r_breaker_levels(high=110.0, low=100.0, close=104.0)
    pivot = (110 + 104 + 100) / 3
    assert lv == pytest.approx(
        {
            "pivot": pivot,
            "r1": 2 * pivot - 100,
            "r2": pivot + 10,
            "r3": 110 + 2 * (pivot - 100),
            "s1": 2 * pivot - 110,
            "s2": pivot - 10,
            "s3": 100 - 2 * (110 - pivot),
        }
    )
    assert lv["s3"] < lv["s2"] < lv["s1"] < lv["pivot"] < lv["r1"] < lv["r2"] < lv["r3"]


def _prior_session(gate, h=110.0, lo=100.0, c=104.0):
    gate.observe(ctx(0, 0, 105.0, h, lo, c))


def test_breakdown_below_s3_pauses_buys_and_the_failed_breakdown_reopens():
    gate = RBreakerGate("short_pauses")
    _prior_session(gate)
    lv = r_breaker_levels(110.0, 100.0, 104.0)
    gate.observe(ctx(1, 0, lv["s1"] + 0.5))
    assert gate.state == "flat" and not gate.suppressed
    gate.observe(ctx(1, 1, lv["s3"] - 0.5, lo=lv["s3"] - 1))  # below S3: short -> paused
    assert gate.state == "short" and gate.suppressed and gate.episodes == 1
    gate.observe(ctx(1, 2, lv["s1"] - 0.1))  # the low pierced S2, but not back above S1 yet
    assert gate.suppressed
    gate.observe(ctx(1, 3, lv["s1"] + 0.1))  # failed breakdown: low < S2 and price > S1
    assert gate.state == "long" and not gate.suppressed


def test_long_flips_to_short_after_a_failed_breakout():
    gate = RBreakerGate("short_pauses")
    _prior_session(gate)
    lv = r_breaker_levels(110.0, 100.0, 104.0)
    gate.observe(ctx(1, 0, lv["r3"] + 0.5, h=lv["r3"] + 1))  # breakout: long
    assert gate.state == "long"
    gate.observe(ctx(1, 1, lv["r1"] - 0.1))  # today's high > R2 and price < R1
    assert gate.state == "short" and gate.suppressed


def test_every_session_starts_flat_and_the_first_has_no_levels():
    gate = RBreakerGate("short_pauses")
    gate.observe(ctx(0, 0, 105.0, 110.0, 100.0, 104.0))
    assert gate.levels is None and gate.state == "flat"
    lv = r_breaker_levels(110.0, 100.0, 104.0)
    gate.observe(ctx(1, 0, lv["s3"] - 1.0, lo=lv["s3"] - 2.0))
    assert gate.levels == pytest.approx(lv) and gate.state == "short"
    # Next session: reset to flat, then decided against day 1's levels. Day 1 was
    # one bar (H = open, L = open - 1, C = open); opening at its pivot breaks
    # neither R3 nor S3, so the reset is visible.
    o = lv["s3"] - 1.0
    day1 = r_breaker_levels(o, o - 1.0, o)
    gate.observe(ctx(2, 0, day1["pivot"]))
    assert gate.levels == pytest.approx(day1)
    assert gate.state == "flat" and not gate.suppressed


def test_r_breaker_rejects_bad_input():
    with pytest.raises(ConfigurationError):
        r_breaker_levels(100.0, 110.0, 105.0)
    with pytest.raises(ConfigurationError):
        RBreakerGate("short")
