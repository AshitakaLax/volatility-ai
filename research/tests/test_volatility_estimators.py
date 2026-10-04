"""research/strategies/volatility_estimators.py."""

from __future__ import annotations

import math
from datetime import UTC, datetime, timedelta

import numpy as np
import pandas as pd
import pytest

from engine.core.exceptions import ConfigurationError
from engine.core.market_context import MarketContext
from research.strategies.volatility_estimators import (
    VOL_ESTIMATORS,
    SessionVolatility,
    estimate_series,
    window_variance,
)


def _daily(n=60, seed=3, gap_sd=0.01, range_sd=0.01):
    rng = np.random.default_rng(seed)
    close = np.empty(n)
    open_ = np.empty(n)
    prev = 100.0
    for i in range(n):
        open_[i] = prev * math.exp(rng.normal(0, gap_sd))
        close[i] = open_[i] * math.exp(rng.normal(0, range_sd))
        prev = close[i]
    wick = np.abs(rng.normal(0, range_sd, n)) * open_
    high = np.maximum(open_, close) + wick
    low = np.minimum(open_, close) - wick
    index = pd.date_range("2024-01-02", periods=n, freq="B", tz="UTC")
    return pd.DataFrame({"open": open_, "high": high, "low": low, "close": close}, index=index)


def _window(daily, end, n):
    o, h, lo, c = (daily[k].to_numpy() for k in ("open", "high", "low", "close"))
    s = slice(end - n + 1, end + 1)
    return o[s], h[s], lo[s], c[s], c[end - n : end]


class TestFormulas:
    def test_close_to_close_is_the_sample_variance_of_log_returns(self):
        d = _daily()
        o, h, lo, c, pc = _window(d, 30, 20)
        expected = np.var(np.log(c / pc), ddof=1)
        assert window_variance("close_to_close", o, h, lo, c, pc) == pytest.approx(expected)

    def test_yang_zhang_is_its_three_weighted_parts(self):
        d = _daily()
        o, h, lo, c, pc = _window(d, 30, 20)
        n = 20
        k = 0.34 / (1.34 + (n + 1) / (n - 1))
        rs = np.log(h / c) * np.log(h / o) + np.log(lo / c) * np.log(lo / o)
        expected = (
            np.var(np.log(o / pc), ddof=1) + k * np.var(np.log(c / o), ddof=1) + (1 - k) * rs.mean()
        )
        assert window_variance("yang_zhang", o, h, lo, c, pc) == pytest.approx(expected)

    def test_parkinson_and_garman_klass(self):
        d = _daily()
        o, h, lo, c, pc = _window(d, 30, 20)
        hl, co = np.log(h / lo), np.log(c / o)
        assert window_variance("parkinson", o, h, lo, c, pc) == pytest.approx(
            (hl**2).sum() / (4 * 20 * math.log(2))
        )
        assert window_variance("garman_klass", o, h, lo, c, pc) == pytest.approx(
            np.mean(0.5 * hl**2 - (2 * math.log(2) - 1) * co**2)
        )

    def test_only_yang_zhang_and_close_to_close_see_a_pure_gap_market(self):
        """Every session opens, trades and closes at one price; all the
        movement is overnight. The range estimators read zero."""
        n = 40
        rng = np.random.default_rng(5)
        price = 100 * np.exp(np.cumsum(rng.normal(0, 0.02, n)))
        index = pd.date_range("2024-01-02", periods=n, freq="B", tz="UTC")
        d = pd.DataFrame({"open": price, "high": price, "low": price, "close": price}, index=index)
        o, h, lo, c, pc = _window(d, 30, 20)
        for blind in ("parkinson", "garman_klass", "rogers_satchell"):
            assert window_variance(blind, o, h, lo, c, pc) == pytest.approx(0.0, abs=1e-15)
        yz = window_variance("yang_zhang", o, h, lo, c, pc)
        cc = window_variance("close_to_close", o, h, lo, c, pc)
        assert yz > 0 and yz == pytest.approx(cc, rel=1e-9)

    def test_bad_inputs(self):
        d = _daily()
        o, h, lo, c, pc = _window(d, 30, 20)
        with pytest.raises(ConfigurationError):
            window_variance("garch", o, h, lo, c, pc)
        with pytest.raises(ConfigurationError):
            window_variance("yang_zhang", o[:1], h[:1], lo[:1], c[:1], pc[:1])


def _minute_bars(daily):
    """Three minute bars per session reproducing each session's OHLC."""
    for day, row in daily.iterrows():
        start = datetime(day.year, day.month, day.day, 14, 30, tzinfo=UTC)
        bars = [
            (row.open, row.high, min(row.open, row.close), row.high),
            (row.high, row.high, row.low, row.low),
            (row.low, max(row.low, row.close), row.low, row.close),
        ]
        for m, (o, h, lo, c) in enumerate(bars):
            yield MarketContext(
                timestamp=start + timedelta(minutes=m),
                open=o,
                high=h,
                low=lo,
                close=c,
                cash=1e5,
                equity=1e5,
                peak_equity=1e5,
                drawdown=0.0,
                open_lot_count=0,
                bar_index=0,
                time_of_day_flag=m,
            )


@pytest.mark.parametrize("estimator", VOL_ESTIMATORS)
def test_session_tracker_equals_the_vectorized_reference_one_session_late(estimator):
    d = _daily(40)
    reference = estimate_series(d, estimator, 10)
    tracker = SessionVolatility(estimator, 10)
    dates = list(d.index)
    seen = {}
    for ctx in _minute_bars(d):
        tracker.observe(ctx)
        if ctx.time_of_day_flag == 0:
            seen[ctx.timestamp.date()] = tracker.value
    for i in range(11, len(dates)):
        # At the first bar of session i, the tracker reflects through i-1.
        assert seen[dates[i].date()] == pytest.approx(reference.iloc[i - 1]), i
    assert seen[dates[10].date()] is None


def test_the_current_session_never_moves_the_estimate():
    d = _daily(30)
    a, b = SessionVolatility("yang_zhang", 10), SessionVolatility("yang_zhang", 10)
    bars = list(_minute_bars(d))
    for ctx in bars:
        a.observe(ctx)
        b.observe(ctx)
    # A wild final bar in the still-open last session changes nothing yet.
    last = bars[-1]
    b.observe(MarketContext(**{**last.__dict__, "high": 1e6, "low": 1e-3, "close": 1e-3}))
    assert a.value == b.value


@pytest.mark.parametrize("kwargs", [{"estimator": "atr"}, {"n": 1}, {"n": 2.5}])
def test_tracker_validation(kwargs):
    with pytest.raises(ConfigurationError):
        SessionVolatility(**kwargs)
