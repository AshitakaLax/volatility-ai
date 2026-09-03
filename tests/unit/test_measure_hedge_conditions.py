"""Tests for tools/measure_hedge_conditions.py.

The centrepiece is right-censoring. The first version of this tool
counted entries whose forward window ran past the end of the data as
FAILURES rather than as unknown, because `NaN > x` is False in pandas.
That manufactured a decline in the hit rate at long horizons, which was
then read as leveraged decay -- a real phenomenon, which is exactly what
made the artifact survive review. It also made the final partial year
look like a regime collapse.

So the censoring behaviour is pinned directly, not inferred.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from tools.measure_hedge_conditions import profitable_exit_available, rsi


def _bars(highs, closes=None):
    closes = closes if closes is not None else highs
    return pd.DataFrame(
        {"high": highs, "close": closes},
        index=pd.date_range("2024-01-01", periods=len(highs), freq="D"),
    )


# -- right-censoring: the bug that produced a false conclusion ----------


def test_entries_without_a_full_forward_window_are_unknown_not_failures():
    """THE regression. The last `horizon` entries cannot be judged, and
    scoring them False understates the hit rate at exactly the horizons
    where the sample is thinnest."""
    bars = _bars([10.0, 11.0, 12.0, 13.0, 14.0])
    result = profitable_exit_available(bars, horizon=3, cost_pct=0.0)

    assert result.iloc[-1] != 0.0, "the final entry has no forward data at all"
    assert np.isnan(result.iloc[-1])
    assert result.notna().sum() < len(bars), "something must be censored here"


def test_a_censored_entry_does_not_drag_the_mean_down():
    """A rising series should read 100% among the entries that CAN be
    judged. If censored rows counted as failures it would read lower,
    which is precisely how the false 'decay signature' appeared."""
    bars = _bars([float(x) for x in range(10, 30)])
    result = profitable_exit_available(bars, horizon=5, cost_pct=0.0)
    assert result.dropna().mean() == pytest.approx(1.0)
    assert result.isna().sum() > 0, "fixture must actually censor something"


def test_a_longer_horizon_censors_more_entries():
    bars = _bars([float(x) for x in range(10, 40)])
    few = profitable_exit_available(bars, horizon=2, cost_pct=0.0).isna().sum()
    many = profitable_exit_available(bars, horizon=10, cost_pct=0.0).isna().sum()
    assert many > few


# -- the outcome definition --------------------------------------------


def test_an_entry_cannot_be_exited_on_its_own_bar():
    """The high on the entry bar is not an exit -- the position is opened
    at that bar's close. Allowing it would score a profit that could not
    have been taken."""
    # A huge high on bar 0, then a permanently lower series.
    bars = _bars(highs=[100.0, 5.0, 5.0, 5.0], closes=[10.0, 5.0, 5.0, 5.0])
    result = profitable_exit_available(bars, horizon=3, cost_pct=0.0)
    assert result.iloc[0] == 0.0, "entry bar's own high was counted as an exit"


def test_the_forward_high_counts_not_the_forward_close():
    """A resting limit order fills on a touch, so an intraday high above
    the target is a real exit even if the close falls back."""
    bars = _bars(highs=[10.0, 12.0, 9.0, 9.0], closes=[10.0, 9.0, 9.0, 9.0])
    result = profitable_exit_available(bars, horizon=2, cost_pct=0.0)
    assert result.iloc[0] == 1.0


def test_the_cost_must_be_cleared_not_merely_matched():
    """A move that exactly equals the round trip is not a profit."""
    bars = _bars(highs=[10.0, 10.10, 10.10], closes=[10.0, 10.0, 10.0])
    assert profitable_exit_available(bars, 2, cost_pct=0.01).iloc[0] == 0.0
    assert profitable_exit_available(bars, 2, cost_pct=0.005).iloc[0] == 1.0


def test_a_bigger_target_is_never_easier_to_hit():
    """Monotonicity -- the property the +2/+5/+10/+20% table depends on."""
    rng = np.random.default_rng(0)
    highs = 100 * np.cumprod(1 + rng.normal(0, 0.03, 300))
    bars = _bars(highs.tolist())
    rates = [
        profitable_exit_available(bars, 60, t).dropna().mean() for t in (0.02, 0.05, 0.10, 0.20)
    ]
    assert rates == sorted(rates, reverse=True)


# -- RSI ---------------------------------------------------------------


def test_rsi_is_100_for_a_monotonically_rising_series():
    values = rsi(pd.Series([float(x) for x in range(1, 60)]))
    assert values.iloc[-1] == pytest.approx(100.0, abs=1e-6)


def test_rsi_is_low_for_a_monotonically_falling_series():
    values = rsi(pd.Series([float(x) for x in range(60, 1, -1)]))
    assert values.iloc[-1] < 1.0


def test_rsi_stays_within_bounds_on_noisy_input():
    rng = np.random.default_rng(3)
    values = rsi(pd.Series(100 + np.cumsum(rng.normal(0, 1, 500))))
    assert values.min() >= 0.0
    assert values.max() <= 100.0


def test_rsi_seeds_a_flat_series_at_neutral_rather_than_nan():
    """A flat series has no gains and no losses, so the ratio is 0/0.
    Neutral is the honest answer; NaN would propagate into every bucket."""
    values = rsi(pd.Series([50.0] * 40))
    assert values.notna().all()
    assert values.iloc[-1] == pytest.approx(50.0)
