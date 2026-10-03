"""
Daily NATR regime, applied CAUSALLY: the flag for session D is computed
from sessions strictly before D.

calm on D+1  <=>  NATR(period) at the close of D  <  the median of the
                  last `lookback` NATR values, also as of the close of D

This is plan.md's "NATR below" signal (best cell: period 10, lookback
100) -- the same indicator, the same trailing-median threshold
indicator_library.signals() uses, the same warm-up rule as the stage
harnesses (max(warmup_bars, lookback)) -- with one difference, and the
difference is the reason this module exists.

--------------------------------------------------------------------
THE STAGE HARNESSES APPLY EACH FLAG ON ITS OWN DAY

tools/probe_stage3_engine.daily_regime() returns {bar.date(): flag} for
daily bars resampled from minutes, so the flag keyed D was computed
from D's OWN high, low and close. IndicatorRegime._read_regime then
looks up regime_by_date[timestamp.date()] at the FIRST bar of D. The
decision taken at 09:30 therefore already knows how wide D's range
will be by 16:00 -- for a range-based signal like NATR, that is
knowing at the open whether today is the crash day.

Verified directly, not inferred: feeding IndicatorRegime a map whose
flag alternates every day, the regime it applies at each 09:30 bar
equals the SAME day's entry, not the previous day's.

plan.md states the intended rule ("computed from data through day t
and applied to day t+1"); the stage1_grid / stage2_grid / stage3_grid /
stage4_leverage engine runs that use IndicatorRegime do not implement
it. NATR-below liquidate-on-flip (38.64% CAGR, 26.68% max DD, z=+11.99
over random regimes) was measured that way. A random regime has no such
foresight, which is one way a lookahead would show up as exactly that
kind of z-score. How much of the result survives the shift is an open
measurement; tools/leverage_stepdown.py --lag 0 versus --lag 1 is one
way to take it.

lag=0 is kept ONLY to reproduce those numbers for comparison. It is
lookahead and must never back a decision that will trade.
"""

from __future__ import annotations

from collections.abc import Mapping
from datetime import date
from itertools import pairwise

import numpy as np
import pandas as pd

from engine.core.exceptions import ConfigurationError

# indicator_library.warmup_bars: max(250, 5 * longest period). The stage
# harnesses then take max(that, lookback); mirrored so lag=0 reproduces
# their flag series date for date.
_WARMUP_FLOOR = 250


def daily_bars(minute_bars: pd.DataFrame) -> pd.DataFrame:
    """Session OHLC from minute bars, the way indicator_library.load_bars
    builds them: calendar-day buckets on the frame's own index (UTC in
    the warehouse), first/max/min/last, empty days dropped.

    A regular-session bar never crosses UTC midnight, so for a
    regular-hours dataset one bucket is one session. An extended-hours
    dataset would fold some evening bars into the next UTC day; resample
    with RTH-only data, as every sweep in this repo does.
    """
    missing = {"open", "high", "low", "close"} - set(minute_bars.columns)
    if missing:
        raise ConfigurationError(f"minute bars are missing {sorted(missing)}")
    frame = minute_bars[["open", "high", "low", "close"]].astype(float)
    return (
        frame.resample("1D")
        .agg({"open": "first", "high": "max", "low": "min", "close": "last"})
        .dropna()
    )


def wilder_natr(daily: pd.DataFrame, period: int) -> pd.Series:
    """NATR exactly as TA-Lib computes it (cross-checked in the tests):

    TR undefined on the first bar (no prior close); ATR seeded at index
    `period` with the simple mean of TR[1..period], then Wilder-smoothed;
    NATR = 100 * ATR / close. NaN until defined -- never a confident
    value during warm-up, the failure indicator_library documents for
    three other libraries.
    """
    if period < 1:
        raise ConfigurationError(f"period must be >= 1, got {period}")
    high = daily["high"].to_numpy(float)
    low = daily["low"].to_numpy(float)
    close = daily["close"].to_numpy(float)
    n = len(close)
    out = np.full(n, np.nan)
    if n <= period:
        return pd.Series(out, index=daily.index)
    prev = close[:-1]
    tr = np.maximum.reduce([high[1:] - low[1:], np.abs(high[1:] - prev), np.abs(low[1:] - prev)])
    atr = tr[:period].mean()
    out[period] = atr
    for i in range(period + 1, n):
        atr = (atr * (period - 1) + tr[i - 1]) / period
        out[i] = atr
    return pd.Series(100.0 * out / close, index=daily.index)


def calm_by_date(
    daily: pd.DataFrame,
    *,
    period: int = 10,
    lookback: int = 100,
    lag: int = 1,
) -> dict[date, bool]:
    """{session date: True if calm} for every session the flag applies to.

    lag=1 (default): the flag computed at the close of session i is keyed
    by session i+1 -- the next session IN THE DATA, so weekends and
    holidays are skipped naturally. The final session's flag applies to
    a session the data does not contain yet and is not returned.

    lag=0: keyed by its own session -- lookahead, kept only to reproduce
    the stage harnesses. See module docstring.
    """
    if lag not in (0, 1):
        raise ConfigurationError(f"lag must be 0 (lookahead, comparison only) or 1, got {lag}")
    if lookback < 1:
        raise ConfigurationError(f"lookback must be >= 1, got {lookback}")
    natr = wilder_natr(daily, period)
    reference = natr.rolling(lookback, min_periods=lookback).median()
    calm = (natr < reference).to_numpy()  # NaN on either side compares False
    skip = max(_WARMUP_FLOOR, 5 * period, lookback)
    dates = [ts.date() for ts in daily.index]
    flags = calm[skip:]
    if lag == 0:
        return dict(zip(dates[skip:], (bool(v) for v in flags), strict=True))
    return {dates[i + 1]: bool(calm[i]) for i in range(skip, len(dates) - 1)}


def shift_to_next_session(flags_by_date: Mapping[date, bool]) -> dict[date, bool]:
    """Re-key a {session: flag} map so each flag applies to the NEXT
    session in the map. For a flag computed from a session's own bar,
    this is what makes it usable at that next session's open.

    The tools/stage*_grid.py harnesses build their maps keyed by the
    session the flag was COMPUTED from and apply each at that same
    session's first bar; their --lag 1 (the default) passes the map
    through here. The final session's flag applies to a session the map
    does not contain and is dropped.
    """
    dates = sorted(flags_by_date)
    return {later: bool(flags_by_date[earlier]) for earlier, later in pairwise(dates)}


def apply_lag(flags_by_date: Mapping[date, bool], lag: int) -> dict[date, bool]:
    """lag 1: each flag applies to the NEXT session -- causal. lag 0: to
    its own session, which is how plan.md's engine stages were measured
    (a one-day lookahead; kept only to reproduce them). Used by every
    tools/stage*_grid.py regime builder behind --lag."""
    if lag not in (0, 1):
        raise ConfigurationError(f"lag must be 0 or 1, got {lag}")
    return dict(flags_by_date) if lag == 0 else shift_to_next_session(flags_by_date)


def count_flips(regime: dict[date, bool]) -> int:
    """Calm/turbulent transitions, in date order. Each one is a
    liquidation for whichever sleeve is leaving the market."""
    values = [regime[d] for d in sorted(regime)]
    return sum(1 for a, b in pairwise(values) if a != b)


__all__ = [
    "apply_lag",
    "calm_by_date",
    "count_flips",
    "daily_bars",
    "shift_to_next_session",
    "wilder_natr",
]
