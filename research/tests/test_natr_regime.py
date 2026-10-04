"""research/strategies/natr_regime.py: the NATR-below regime, causally.

Pinned here:
  * NATR matches TA-Lib's exactly (when TA-Lib is installed).
  * lag=0 reproduces the stage harnesses' regime map date for date --
    so lag=1 is provably the SAME signal, shifted one session, rather
    than a reimplementation that might differ in some other way.
  * lag=1 cannot see the session it is applied to; lag=0 can.
"""

from __future__ import annotations

from itertools import pairwise

import numpy as np
import pandas as pd
import pytest

from engine.core.exceptions import ConfigurationError
from research.strategies.natr_regime import calm_by_date, count_flips, daily_bars, wilder_natr


def _daily(n: int = 420, seed: int = 7) -> pd.DataFrame:
    """Random-walk sessions with realistic, varying ranges."""
    rng = np.random.default_rng(seed)
    close = 100 * np.exp(np.cumsum(rng.normal(0, 0.02, n)))
    open_ = np.r_[100.0, close[:-1]] * np.exp(rng.normal(0, 0.005, n))
    spread = np.abs(rng.normal(0, 0.015, n)) * close * (1 + (np.arange(n) % 90 > 70) * 2)
    high = np.maximum(open_, close) + spread
    low = np.minimum(open_, close) - spread
    index = pd.date_range("2016-01-04", periods=n, freq="B", tz="UTC")
    return pd.DataFrame(
        {"open": open_, "high": high, "low": low, "close": close, "volume": 1e6}, index=index
    )


class TestNatr:
    def test_matches_talib_exactly(self):
        talib = pytest.importorskip("talib")
        daily = _daily()
        ours = wilder_natr(daily, 10)
        theirs = talib.NATR(daily["high"], daily["low"], daily["close"], timeperiod=10)
        assert ours.isna().sum() == theirs.isna().sum() == 10
        np.testing.assert_allclose(ours.dropna(), theirs.dropna(), rtol=1e-10)

    def test_undefined_values_are_nan_not_numbers(self):
        assert wilder_natr(_daily(8), 10).isna().all()

    def test_bad_period(self):
        with pytest.raises(ConfigurationError):
            wilder_natr(_daily(), 0)


class TestCalmByDate:
    def test_lag0_reproduces_the_stage_harness_map(self):
        """The exact construction of tools/probe_stage3_engine.daily_regime
        (indicator_library compute -> signals -> skip -> {date: flag})."""
        pytest.importorskip("talib")
        from research.strategies.indicator_library import available, compute, signals, warmup_bars

        daily = _daily()
        natr = {i.name: i for i in available()}["NATR"]
        values = compute(natr, daily, timeperiod=10)["real"]
        flags = signals(values, natr, lookback=100)["below"]
        skip = max(warmup_bars(natr, timeperiod=10), 100)
        stage_map = {ts.date(): bool(v) for ts, v in flags.iloc[skip:].items()}
        assert calm_by_date(daily, period=10, lookback=100, lag=0) == stage_map

    def test_lag1_is_lag0_shifted_one_session(self):
        daily = _daily()
        same_day = calm_by_date(daily, lag=0)
        causal = calm_by_date(daily, lag=1)
        dates = sorted(same_day)
        assert sorted(causal) == dates[1:]
        for earlier, later in pairwise(dates):
            assert causal[later] == same_day[earlier]

    def test_a_crash_session_changes_its_own_lag0_flag_but_no_lag1_flag(self):
        """The lookahead, demonstrated. Blow out one session's range:
        lag 0 reads that session as turbulent ON THAT SESSION; lag 1
        cannot know until the next one."""
        daily = _daily()
        base0 = calm_by_date(daily, lag=0)
        dates = sorted(base0)
        target = next(d for d in dates[20:] if base0[d])  # a calm session
        crashed = daily.copy()
        row = crashed.index[[ts.date() == target for ts in crashed.index]][0]
        crashed.loc[row, "low"] = crashed.loc[row, "close"] * 0.5
        assert calm_by_date(crashed, lag=0)[target] is False
        before, after = calm_by_date(daily, lag=1), calm_by_date(crashed, lag=1)
        assert {d: v for d, v in after.items() if d <= target} == {
            d: v for d, v in before.items() if d <= target
        }

    def test_weekends_and_holidays_are_skipped(self):
        """Keyed by the next session IN THE DATA, not the next calendar day."""
        daily = _daily()
        causal = calm_by_date(daily, lag=1)
        assert all(d.weekday() < 5 for d in causal)

    @pytest.mark.parametrize("lag", [-1, 2])
    def test_only_lag_0_or_1(self, lag):
        with pytest.raises(ConfigurationError):
            calm_by_date(_daily(), lag=lag)

    def test_flip_count(self):
        from datetime import date

        regime = {date(2024, 1, d): v for d, v in [(2, True), (3, True), (4, False), (5, True)]}
        assert count_flips(regime) == 2


def test_daily_bars_aggregate_minutes_per_session():
    index = pd.date_range("2024-01-02 14:30", periods=4, freq="1min", tz="UTC").append(
        pd.date_range("2024-01-03 14:30", periods=2, freq="1min", tz="UTC")
    )
    minutes = pd.DataFrame(
        {
            "open": [10, 11, 12, 13, 20, 21],
            "high": [11, 15, 13, 14, 22, 23],
            "low": [9, 10, 8, 12, 19, 18],
            "close": [11, 12, 13, 12.5, 21, 22],
        },
        index=index,
        dtype=float,
    )
    daily = daily_bars(minutes)
    assert daily.to_dict("list") == {
        "open": [10.0, 20.0],
        "high": [15.0, 23.0],
        "low": [8.0, 18.0],
        "close": [12.5, 22.0],
    }
