"""research/strategies/grid_spacing.py -- catalog C-G3."""

from __future__ import annotations

import math

import numpy as np
import pandas as pd
import pytest

from engine.core.exceptions import ConfigurationError
from research.strategies.grid_spacing import (
    VolatilityScaledStep,
    step_series,
    volatility_scaled_step,
)


def _closes(n=200, sd=0.002, seed=7):
    rng = np.random.default_rng(seed)
    return pd.Series(100.0 * np.exp(np.cumsum(rng.normal(0.0, sd, n))))


def test_step_is_proportional_to_sigma_above_the_floor():
    assert volatility_scaled_step(0.002, 2.0, 0.0005) == pytest.approx(0.004)
    assert volatility_scaled_step(0.004, 2.0, 0.0005) == pytest.approx(0.008)


def test_the_minimum_step_is_a_floor():
    # The tutorial's max(interval, minimum): calm tape never collapses the grid.
    assert volatility_scaled_step(0.0, 2.0, 0.0005) == 0.0005
    assert volatility_scaled_step(0.0001, 2.0, 0.0005) == 0.0005


def test_the_step_rounds_to_a_whole_multiple_of_the_minimum():
    # The source's grid_interval = max(round(half_spread / min_step) * min_step, min_step).
    assert volatility_scaled_step(0.0042, 1.0, 0.0005) == pytest.approx(0.004)  # 8.4 -> 8
    assert volatility_scaled_step(0.0048, 1.0, 0.0005) == pytest.approx(0.005)  # 9.6 -> 10
    assert volatility_scaled_step(0.0011, 1.0, 0.0005) == pytest.approx(0.001)  # 2.2 -> 2
    # numpy's half-to-even, as in the source: 2.5 -> 2, 3.5 -> 4
    assert volatility_scaled_step(0.00125, 1.0, 0.0005) == pytest.approx(0.001)
    assert volatility_scaled_step(0.00175, 1.0, 0.0005) == pytest.approx(0.002)


def test_rounding_below_one_unit_still_returns_the_minimum():
    assert volatility_scaled_step(0.0002, 1.0, 0.0005) == 0.0005  # round(0.4) = 0 -> floor


def test_quantize_off_keeps_the_continuous_step():
    assert volatility_scaled_step(0.0042, 1.0, 0.0005, quantize=False) == pytest.approx(0.0042)


def test_the_optional_ceiling_caps_a_shock():
    assert volatility_scaled_step(0.05, 2.0, 0.0005, max_step=0.02) == 0.02


def test_tracker_returns_the_base_step_until_the_window_fills():
    tracker = VolatilityScaledStep(window=5, vol_multiple=1.0, min_step=0.0005)
    for close in (100.0, 100.5, 100.2, 100.9, 100.1):  # 4 returns: still warming up
        tracker.observe(close)
    assert tracker.sigma is None
    assert tracker.step(0.003) == 0.003
    tracker.observe(100.4)
    assert tracker.sigma is not None


def test_sigma_is_the_sample_stdev_of_log_returns():
    closes = [100.0, 101.0, 100.0, 102.0, 101.0, 103.0]
    tracker = VolatilityScaledStep(window=5, vol_multiple=1.0, min_step=0.0001)
    for c in closes:
        tracker.observe(c)
    expected = float(np.std(np.diff(np.log(closes)), ddof=1))
    assert tracker.sigma == pytest.approx(expected)


def test_horizon_scales_sigma_by_its_square_root():
    closes = _closes(60)
    one = VolatilityScaledStep(window=30, horizon_bars=1)
    nine = VolatilityScaledStep(window=30, horizon_bars=9)
    for c in closes:
        one.observe(c)
        nine.observe(c)
    assert nine.sigma == pytest.approx(3.0 * one.sigma)


def test_doubling_return_magnitude_doubles_the_unrounded_step():
    calm = VolatilityScaledStep(window=30, quantize=False)
    wild = VolatilityScaledStep(window=30, quantize=False)
    rng = np.random.default_rng(1)
    r = rng.normal(0.0, 0.003, 80)
    for a, b in zip(100 * np.exp(np.cumsum(r)), 100 * np.exp(np.cumsum(2 * r)), strict=True):
        calm.observe(a)
        wild.observe(b)
    assert wild.step(0.001) == pytest.approx(2.0 * calm.step(0.001))


def test_constant_prices_give_the_floor():
    tracker = VolatilityScaledStep(window=5, vol_multiple=3.0, min_step=0.0007)
    for _ in range(10):
        tracker.observe(50.0)
    assert tracker.sigma == 0.0
    assert tracker.step(0.01) == 0.0007


def test_tracker_matches_the_vectorised_reference_bar_for_bar():
    closes = _closes(150, sd=0.004)
    series = step_series(closes, window=20, vol_multiple=1.5, min_step=0.001, max_step=0.02)
    tracker = VolatilityScaledStep(window=20, vol_multiple=1.5, min_step=0.001, max_step=0.02)
    for i, c in enumerate(closes):
        tracker.observe(c)
        if math.isnan(series.iloc[i]):
            assert tracker.sigma is None
        else:
            assert tracker.step(0.0) == pytest.approx(series.iloc[i])


def test_the_value_after_bar_t_uses_no_later_bar():
    closes = _closes(80)
    full = step_series(closes, window=20)
    truncated = step_series(closes.iloc[:50], window=20)
    pd.testing.assert_series_equal(full.iloc[:50], truncated)


def test_non_positive_prices_are_skipped():
    tracker = VolatilityScaledStep(window=2)
    for c in (100.0, 0.0, -1.0, float("nan"), 101.0, 102.0):
        tracker.observe(c)
    expected = float(np.std([math.log(101 / 100), math.log(102 / 101)], ddof=1))
    assert tracker.sigma == pytest.approx(expected)


@pytest.mark.parametrize(
    "kwargs",
    [
        {"window": 1},
        {"vol_multiple": 0.0},
        {"min_step": 0.0},
        {"min_step": 1.0},
        {"min_step": 0.01, "max_step": 0.005},
        {"horizon_bars": 0},
    ],
)
def test_bad_parameters_are_rejected(kwargs):
    with pytest.raises(ConfigurationError):
        VolatilityScaledStep(**kwargs)


def test_negative_sigma_is_rejected():
    with pytest.raises(ConfigurationError):
        volatility_scaled_step(-0.1, 1.0, 0.001)
