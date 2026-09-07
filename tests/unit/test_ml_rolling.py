"""IncrementalBarFeatures, replayed bar-by-bar, against the offline batch.

The whole point of src/ml/rolling.py is to compute what
features.bar_features() computes, using only what a SizingStrategy
actually has: one bar at a time, in order, with no look-ahead. If the
two ever disagree, a persisted model (trained on the offline numbers)
would be fed silently different inputs at inference time -- exactly the
kind of mismatch that validates perfectly offline and does nothing
useful live. This is the only thing standing between "the feature
plumbing is right" and "it looks right until it is deployed".
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from src.ml.rolling import FEATURE_NAMES, IncrementalBarFeatures


def _synthetic_bars(n: int, seed: int) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    close = 100 * np.exp(np.cumsum(rng.normal(0, 0.0006, n)))
    high = close * (1 + np.abs(rng.normal(0, 0.0003, n)))
    low = close * (1 - np.abs(rng.normal(0, 0.0003, n)))
    open_ = close + rng.normal(0, 0.01, n)
    volume = rng.integers(1_000, 50_000, n).astype(float)
    index = pd.date_range("2024-06-03 13:30", periods=n, freq="1min", tz="UTC")  # a Monday
    return pd.DataFrame(
        {"open": open_, "high": high, "low": low, "close": close, "volume": volume}, index=index
    )


def _replay(bars: pd.DataFrame) -> pd.DataFrame:
    tracker = IncrementalBarFeatures()
    rows = [
        tracker.record(timestamp, row.high, row.low, row.close)
        for timestamp, row in zip(bars.index, bars.itertuples(), strict=True)
    ]
    return pd.DataFrame(rows, index=bars.index)


@pytest.mark.parametrize("seed", range(6))
def test_incremental_matches_the_offline_batch(seed):
    from src.ml.features import bar_features

    bars = _synthetic_bars(2500, seed)
    offline = bar_features(bars)
    incremental = _replay(bars)

    for name in FEATURE_NAMES:
        offline_values = offline[name].to_numpy()
        incremental_values = incremental[name].to_numpy()
        # A fresh tracker's first ~2000 bars are still filling the
        # widest (1950-bar) window; both sides are NaN there, and
        # np.allclose(equal_nan=True) already treats matching NaNs as
        # equal -- no separate warmup skip needed.
        assert np.allclose(
            offline_values, incremental_values, equal_nan=True, rtol=1e-8, atol=1e-10
        ), (
            f"{name}: mismatch. offline[:5]={offline_values[:5]} "
            f"incremental[:5]={incremental_values[:5]}; "
            f"first differing index="
            f"{next((i for i in range(len(offline_values)) if not np.isclose(offline_values[i], incremental_values[i], equal_nan=True, rtol=1e-8, atol=1e-10)), None)}"
        )


def test_the_entry_bar_cannot_see_its_own_close():
    """record() for bar i must describe bars < i -- a huge move ON bar i
    must not appear in THAT SAME CALL's returned features.

    Two trackers fed an IDENTICAL prefix, then given a DIFFERENT final
    bar: since every returned feature describes bars strictly before
    the one just passed in, the two calls must return exactly the same
    dict regardless of what that final bar's own OHLC was. Comparing
    return_5b across two DIFFERENT bar indices (as an earlier version of
    this test did) is not this claim -- return_5b naturally differs
    from one bar to the next with no leakage involved at all.
    """
    bars = _synthetic_bars(500, seed=1)
    tracker_a, tracker_b = IncrementalBarFeatures(), IncrementalBarFeatures()

    prefix = bars.iloc[:400]
    for timestamp, row in zip(prefix.index, prefix.itertuples(), strict=True):
        tracker_a.record(timestamp, row.high, row.low, row.close)
        tracker_b.record(timestamp, row.high, row.low, row.close)

    final = bars.iloc[400]
    unspiked = tracker_a.record(final.name, final.high, final.low, final.close)
    spiked = tracker_b.record(final.name, final.high * 1.5, final.low, final.high * 1.5)

    for name in FEATURE_NAMES:
        assert unspiked[name] == pytest.approx(spiked[name], abs=1e-9, nan_ok=True), (
            f"{name}: the spike on bar 400 leaked into that same call's own features"
        )


def test_feature_names_match_the_offline_set_minus_volume():
    """FEATURE_NAMES is documented as bar_features()'s 22 minus
    volume_ratio_390b -- pinned so the two cannot silently drift apart."""
    from src.ml.features import bar_features

    bars = _synthetic_bars(50, seed=2)
    offline_columns = set(bar_features(bars).columns)
    assert set(FEATURE_NAMES) == offline_columns - {"volume_ratio_390b"}
