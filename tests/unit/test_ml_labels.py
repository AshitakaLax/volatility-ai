"""The MFE labels are checked against a brute-force reference.

src/ml/labels.py finds "did this lot reach its target, and when" by
binary lifting over a sparse table of forward maxima -- O(n log h)
instead of the O(n * h) scan, which matters because a 1M-bar file with
a one-day horizon is 400M comparisons per label set.

That optimisation is exactly the kind that is subtly wrong while
looking right, and a wrong label does not fail loudly: it trains a
model on a description of the past that never happened. So the fast
implementation is pinned against the obvious slow one.

This caught a real bug. The sparse table's top level spans
2**ceil(log2(horizon)), which OVERSHOOTS whenever the horizon is not a
power of two -- MFE for a 17-bar horizon was being measured over 32
bars, reporting excursions the window never contained. Hence
`test_mfe_matches_when_horizon_is_not_a_power_of_two`, which fails
against the original implementation.
"""

from __future__ import annotations

import numpy as np
import pytest

from src.ml import labels


def brute_force(high, low, entry, profit_target, horizon):
    """The definition, written the slow obvious way."""
    n = len(high)
    reached = np.full(n, np.nan)
    time_to_hit = np.full(n, np.nan)
    mfe = np.full(n, np.nan)
    mae = np.full(n, np.nan)

    for i in range(n - horizon):
        window_high = high[i + 1 : i + 1 + horizon]
        window_low = low[i + 1 : i + 1 + horizon]
        touched = np.nonzero(window_high >= entry[i] * (1 + profit_target))[0]
        reached[i] = 1.0 if touched.size else 0.0
        time_to_hit[i] = float(touched[0] + 1) if touched.size else np.nan
        mfe[i] = window_high.max() / entry[i] - 1
        mae[i] = window_low.min() / entry[i] - 1

    return reached, time_to_hit, mfe, mae


def random_bars(rng, n):
    close = 100 * np.exp(np.cumsum(rng.normal(0, 0.01, n)))
    high = close * (1 + abs(rng.normal(0, 0.004, n)))
    low = close * (1 - abs(rng.normal(0, 0.004, n)))
    return high, low, close


def assert_matches(high, low, close, target, horizon):
    computed = labels.compute(high, low, close, profit_target=target, horizon=horizon)
    expected = brute_force(high, low, close, target, horizon)
    for name, got, want in zip(
        ("reached", "time_to_hit", "mfe", "mae"),
        (computed.reached, computed.time_to_hit, computed.mfe, computed.mae),
        expected,
        strict=True,
    ):
        assert np.allclose(got, want, equal_nan=True, rtol=1e-12, atol=1e-15), name


@pytest.mark.parametrize("seed", range(25))
def test_matches_brute_force_on_random_paths(seed):
    rng = np.random.default_rng(seed)
    high, low, close = random_bars(rng, int(rng.integers(40, 200)))
    assert_matches(
        high, low, close, float(rng.choice([0.001, 0.005, 0.01])), int(rng.integers(1, 30))
    )


@pytest.mark.parametrize("horizon", [3, 5, 6, 7, 9, 17, 31, 33])
def test_mfe_matches_when_horizon_is_not_a_power_of_two(horizon):
    """The regression guard for the overshoot described above."""
    rng = np.random.default_rng(99)
    high, low, close = random_bars(rng, 200)
    assert_matches(high, low, close, 0.005, horizon)


def test_a_target_touched_exactly_counts_as_reached():
    """The engine's limit sell fills ON the target, not above it.

    Worth its own test: this is the case float32 maxima endangered, and
    random paths almost never produce an exact equality.
    """
    close = np.full(10, 100.0)
    high = np.full(10, 100.0)
    high[5] = 100.5  # exactly +0.5%
    low = np.full(10, 99.0)

    result = labels.compute(high, low, close, profit_target=0.005, horizon=6)
    assert result.reached[0] == 1.0
    assert result.time_to_hit[0] == 5.0


def test_the_entry_bar_cannot_fill_its_own_lot():
    """A lot bought at bar i may only be filled from bar i+1 onward."""
    close = np.full(10, 100.0)
    high = np.full(10, 100.0)
    high[0] = 200.0  # a huge high on the entry bar itself
    low = np.full(10, 100.0)

    result = labels.compute(high, low, close, profit_target=0.005, horizon=5)
    assert result.reached[0] == 0.0, "the entry bar's own high filled the lot"


def test_an_incomplete_window_is_nan_rather_than_a_short_one():
    """Truncating the window would bias `reached` down at the file's end."""
    rng = np.random.default_rng(3)
    high, low, close = random_bars(rng, 50)
    result = labels.compute(high, low, close, profit_target=0.005, horizon=10)

    assert np.isnan(result.reached[-10:]).all()
    assert not np.isnan(result.reached[:-10]).any()
