"""natr_regime.IncrementalNatrRegime reproduces calm_by_date(lag=1) +
debounce date for date, with and without the bear filters."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from engine.core.exceptions import ConfigurationError
from research.strategies.natr_regime import (
    IncrementalNatrRegime,
    calm_by_date,
    daily_bars,
    debounce,
)


def _minutes(sessions: int = 420, bars: int = 6, seed: int = 0) -> pd.DataFrame:
    """Regular-hours-like bars: `bars` per session, volatility regimes that
    switch every ~40 sessions, a slow drift down then up."""
    rng = np.random.default_rng(seed)
    days = pd.bdate_range("2019-01-02", periods=sessions)
    rows, price = [], 100.0
    for k, day in enumerate(days):
        vol = 0.004 if (k // 40) % 2 == 0 else 0.015
        drift = -0.0008 if 150 < k < 260 else 0.0005
        for b in range(bars):
            ts = pd.Timestamp(day).tz_localize("UTC") + pd.Timedelta(hours=14, minutes=30 + b * 60)
            o = price
            price = price * np.exp(drift / bars + vol * rng.standard_normal())
            hi, lo = max(o, price) * (1 + vol / 4), min(o, price) * (1 - vol / 4)
            rows.append((ts, o, hi, lo, price))
    return pd.DataFrame(rows, columns=["ts", "open", "high", "low", "close"]).set_index("ts")


def _incremental_flags(frame: pd.DataFrame, **kw) -> dict:
    reg = IncrementalNatrRegime(**kw)
    out, day = {}, None
    for ts, row in frame.iterrows():
        reg.observe(ts, row["high"], row["low"], row["close"])
        if ts.date() != day:
            day = ts.date()
            if reg.calm is not None:
                out[day] = reg.calm
    return out


def _reference(frame, period, lookback, min_hold, bear_dd=None, bear_window=60, bear_sma=None):
    daily = daily_bars(frame)
    base = calm_by_date(daily, period=period, lookback=lookback, lag=1)
    close = daily["close"]
    ok = pd.Series(True, index=close.index)
    if bear_dd is not None:
        ok &= close >= (1 - bear_dd) * close.rolling(bear_window, min_periods=1).max()
    if bear_sma is not None:
        ok &= close > close.rolling(bear_sma, min_periods=bear_sma).mean()
    dates = [t.date() for t in close.index]
    nxt = {dates[i + 1]: bool(ok.iloc[i]) for i in range(len(dates) - 1)}
    raw = {d: bool(v and nxt[d]) for d, v in base.items()}
    return debounce(raw, min_hold)


@pytest.mark.parametrize("min_hold", [1, 3])
@pytest.mark.parametrize("period,lookback", [(5, 20), (10, 100)])
def test_matches_calm_by_date_and_debounce(period, lookback, min_hold):
    frame = _minutes()
    ref = _reference(frame, period, lookback, min_hold)
    got = _incremental_flags(frame, period=period, lookback=lookback, min_hold=min_hold)
    assert ref and got == ref
    assert 0 < sum(ref.values()) < len(ref)  # both states occur


@pytest.mark.parametrize("bear", [{"bear_dd": 0.05, "bear_window": 30}, {"bear_sma": 50}])
def test_bear_filters_match_their_reference(bear):
    frame = _minutes(seed=3)
    ref = _reference(frame, 5, 20, 3, **bear)
    got = _incremental_flags(frame, period=5, lookback=20, min_hold=3, **bear)
    assert got == ref
    plain = _reference(frame, 5, 20, 3)
    assert sum(ref.values()) < sum(plain.values())  # the filter removes calm days


def test_no_flag_before_the_warm_up():
    frame = _minutes(sessions=260)
    got = _incremental_flags(frame, period=10, lookback=100)
    first = min(got)
    assert sorted({t.date() for t in frame.index}).index(first) == 251  # skip 250, then lag 1


@pytest.mark.parametrize("bad", [{"period": 0}, {"bear_dd": 1.2}, {"bear_sma": 0}])
def test_bad_parameters(bad):
    with pytest.raises(ConfigurationError):
        IncrementalNatrRegime(**bad)


@pytest.mark.parametrize("bear", [{}, {"bear_dd": 0.05, "bear_window": 30}])
@pytest.mark.parametrize("partial", [False, True])
def test_warm_up_from_session_bars_matches_replaying_the_minutes(bear, partial):
    """warm_up(daily_bars(history)) then the live bars gives the same flag on
    every live bar as observing every bar from the start -- including when
    the history ends mid-session and the live feed extends that session."""
    frame = _minutes()
    cut = sorted({t.date() for t in frame.index})[300]
    split = int((frame.index.date < cut).sum()) + (3 if partial else 0)
    kw = {"period": 5, "lookback": 20, "min_hold": 3, **bear}
    full, seeded = IncrementalNatrRegime(**kw), IncrementalNatrRegime(**kw)
    history = frame.iloc[:split]
    assert seeded.warm_up(daily_bars(history)) == len(set(history.index.date))
    assert seeded.calm is not None  # flagged from the first live bar, no year-long wait
    live_flags = []
    for i, (ts, row) in enumerate(frame.iterrows()):
        full.observe(ts, row["high"], row["low"], row["close"])
        if i >= split:
            seeded.observe(ts, row["high"], row["low"], row["close"])
            assert seeded.calm == full.calm, ts
            live_flags.append(seeded.calm)
    assert 0 < sum(live_flags) < len(live_flags)  # both states occur after the cut


def test_warm_up_rejects_unordered_or_overlapping_history():
    daily = daily_bars(_minutes(sessions=30))
    with pytest.raises(ConfigurationError):
        IncrementalNatrRegime().warm_up(daily.iloc[::-1])
    with pytest.raises(ConfigurationError):
        IncrementalNatrRegime().warm_up(daily.drop(columns="low"))
    reg = IncrementalNatrRegime()
    reg.observe(daily.index[5] + pd.Timedelta(hours=15), 1.0, 1.0, 1.0)
    with pytest.raises(ConfigurationError):
        reg.warm_up(daily)  # history may not reach back into an observed session


def test_describe_says_since_when_and_how_long_until_it_may_change():
    """What the Live page shows beside a deployment that is not buying."""
    frame = _minutes()
    reg = IncrementalNatrRegime(period=10, lookback=100, min_hold=5)
    flags, day = {}, None
    for ts, row in frame.iterrows():
        reg.observe(ts, row["high"], row["low"], row["close"])
        if ts.date() != day:
            day = ts.date()
            flags[day] = reg.calm
    described = reg.describe()
    days = sorted(flags)
    # `since` is the first session of the current unbroken run of the flag.
    run_start = days[-1]
    for earlier in reversed(days[:-1]):
        if flags[earlier] != described["calm"]:
            break
        run_start = earlier
    assert described["session"] == days[-1]
    assert described["since"] == run_start
    assert described["held"] == days.index(days[-1]) - days.index(run_start) + 1
    assert described["min_hold"] == 5
    assert described["sessions_until_change"] == max(1, 5 - described["held"] + 1)
    assert isinstance(described["natr"], float) and isinstance(described["median"], float)
    assert described["reading"] in (True, False)


def test_describe_before_the_warm_up_has_no_flag_to_explain():
    reg = IncrementalNatrRegime(period=10, lookback=100, min_hold=5)
    reg.warm_up(daily_bars(_minutes(sessions=20)))
    described = reg.describe()
    assert described["calm"] is None and described["since"] is None
    assert described["held"] is None and described["sessions_until_change"] is None
