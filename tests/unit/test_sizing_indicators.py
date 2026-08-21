"""Tests for the shared incremental indicators.

These are validated against pandas rather than against hand-computed
constants where possible: the point is that the incremental
implementations agree with the obvious batch definition, which is what
a reader assumes when they see "rolling max" or "RSI(14)".
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from src.exceptions import ConfigurationError
from src.sizing_indicators import RollingMax, WilderRSI, bars_from_days, clamp

# --- window conversion ---


def test_the_same_day_count_is_a_different_bar_count_per_frequency():
    """The whole reason this helper exists. A 252-BAR lookback is a
    trading year on daily bars and about forty minutes on 1-minute
    bars; measured on this repo's own TQQQ minute data that collapsed
    the bell curve into a near-constant multiplier."""
    assert bars_from_days(252, 1) == 252
    assert bars_from_days(252, 390) == 98_280


def test_sub_day_windows_round_to_at_least_one_bar():
    assert bars_from_days(0.001, 1) == 1


@pytest.mark.parametrize("days,bpd", [(0, 10), (-1, 10), (10, 0), (10, -5)])
def test_non_positive_window_arguments_are_rejected(days, bpd):
    with pytest.raises(ConfigurationError):
        bars_from_days(days, bpd)


def test_clamp_bounds_both_ways():
    assert clamp(-1, 0, 1) == 0
    assert clamp(2, 0, 1) == 1
    assert clamp(0.5, 0, 1) == 0.5


# --- rolling maximum ---


def test_rolling_max_matches_pandas_on_random_data():
    rng = np.random.default_rng(0)
    values = rng.normal(100, 5, 3000)
    rm = RollingMax(50)
    mine = [rm.update(v) for v in values]
    reference = pd.Series(values).rolling(50, min_periods=1).max().tolist()
    assert np.allclose(mine, reference)


def test_rolling_max_matches_pandas_on_a_monotonic_decline():
    """The worst case for a monotonic deque -- every element is a
    candidate, so nothing gets discarded on insert."""
    values = list(np.linspace(200, 100, 500))
    rm = RollingMax(30)
    mine = [rm.update(v) for v in values]
    reference = pd.Series(values).rolling(30, min_periods=1).max().tolist()
    assert np.allclose(mine, reference)


def test_rolling_max_drops_values_that_age_out_of_the_window():
    rm = RollingMax(3)
    rm.update(100.0)
    rm.update(1.0)
    rm.update(2.0)
    assert rm.value == 100.0
    rm.update(3.0)  # the 100 is now 4 bars back
    assert rm.value == 3.0


def test_rolling_max_is_none_before_any_observation():
    assert RollingMax(10).value is None


def test_rolling_max_window_must_be_positive():
    with pytest.raises(ConfigurationError):
        RollingMax(0)


# --- Wilder RSI ---


def test_rsi_is_none_until_the_seeding_window_completes():
    """A partially-warmed RSI can sit at an extreme; returning None
    makes it impossible to mistake for a real reading."""
    r = WilderRSI(14)
    for i in range(14):
        assert r.update(100.0 + i) is None
    assert r.update(115.0) is not None


def test_rsi_is_100_when_every_change_is_a_gain():
    r = WilderRSI(5)
    value = None
    for i in range(20):
        value = r.update(100.0 + i)
    assert value == pytest.approx(100.0)


def test_rsi_is_near_zero_when_every_change_is_a_loss():
    r = WilderRSI(5)
    value = None
    for i in range(20):
        value = r.update(100.0 - i)
    assert value == pytest.approx(0.0, abs=1e-9)


def test_rsi_of_a_flat_series_is_neutral():
    """No gains and no losses. Computing RS first would divide zero by
    zero; 50 is the neutral reading."""
    r = WilderRSI(5)
    value = None
    for _ in range(20):
        value = r.update(100.0)
    assert value == pytest.approx(50.0)


def test_rsi_stays_within_bounds_on_random_data():
    rng = np.random.default_rng(7)
    r = WilderRSI(14)
    values = [v for v in (r.update(p) for p in rng.normal(100, 3, 2000)) if v is not None]
    assert values, "precondition: RSI produced readings"
    assert all(0.0 <= v <= 100.0 for v in values)


def test_rsi_falls_when_a_rising_series_turns_down():
    r = WilderRSI(14)
    for i in range(40):
        r.update(100.0 + i)
    high = r.value
    for i in range(20):
        r.update(140.0 - i * 2)
    assert r.value < high


def test_rsi_period_must_be_at_least_two():
    with pytest.raises(ConfigurationError):
        WilderRSI(1)


def test_rsi_state_is_two_floats_not_a_price_history():
    """Bounded state: an unbounded history would ride along into
    SimulationResult.params for every sweep combination."""
    r = WilderRSI(14)
    for i in range(10_000):
        r.update(100.0 + (i % 7))
    assert not any(isinstance(v, (list, tuple, dict, set)) for v in vars(r).values())
