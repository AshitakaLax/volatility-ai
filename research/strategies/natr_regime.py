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

from collections import deque
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


def debounce(flags_by_date: Mapping[date, bool], min_hold: int) -> dict[date, bool]:
    """Hold each regime for at least `min_hold` sessions before it may
    flip again. Causal: walks the dates in order and only ever looks
    back. min_hold <= 1 returns the map unchanged.

    Every flip liquidates whichever sleeve is leaving, and plan.md found
    that liquidating costs return almost every time -- a fast regime
    pays that cost on every whipsaw. This trades responsiveness for
    fewer flips.
    """
    if min_hold <= 1:
        return dict(flags_by_date)
    out: dict[date, bool] = {}
    state: bool | None = None
    held = 0
    for d in sorted(flags_by_date):
        raw = bool(flags_by_date[d])
        if state is None or (raw != state and held >= min_hold):
            state, held = raw, 1
        else:
            held += 1
        out[d] = state
    return out


def count_flips(regime: dict[date, bool]) -> int:
    """Calm/turbulent transitions, in date order. Each one is a
    liquidation for whichever sleeve is leaving the market."""
    values = [regime[d] for d in sorted(regime)]
    return sum(1 for a, b in pairwise(values) if a != b)


class IncrementalNatrRegime:
    """The same causal calm flag as calm_by_date(lag=1) + debounce, computed
    bar by bar for a strategy that sees the run one bar at a time (the
    server and the live loop cannot inject a precomputed map).

    Feed every bar to `observe`; `calm` is the flag for the session the
    latest bar belongs to (None until the warm-up has passed). Sessions are
    calendar days of the bar timestamps, exactly as daily_bars buckets
    them; NATR is Wilder's with TA-Lib seeding (wilder_natr); the threshold
    is the median of the last `lookback` NATR values; the first
    max(250, 5 * period, lookback) sessions carry no flag; each flag is the
    previous session's reading (lag 1); `min_hold` debounces exactly like
    debounce(). research/tests/test_natr_regime_incremental.py checks the
    flags against calm_by_date + debounce date for date.

    Two optional BEAR FILTERS (Ultimate algorithm, exp5), ANDed into the
    raw flag before debouncing and also read at the previous session's
    close: `bear_dd` -- calm only within that fraction of the highest close
    of the last `bear_window` sessions; `bear_sma` -- calm only above that
    many sessions' simple moving average of closes.
    """

    def __init__(
        self,
        period: int = 10,
        lookback: int = 100,
        min_hold: int = 1,
        bear_dd: float | None = None,
        bear_window: int = 60,
        bear_sma: int | None = None,
    ) -> None:
        if period < 1 or lookback < 1:
            raise ConfigurationError("period and lookback must be >= 1")
        if bear_dd is not None and not 0 < bear_dd < 1:
            raise ConfigurationError(f"bear_dd must be in (0, 1), got {bear_dd}")
        if bear_window < 1 or (bear_sma is not None and bear_sma < 1):
            raise ConfigurationError("bear_window and bear_sma must be >= 1")
        self.period, self.lookback, self.min_hold = period, lookback, max(1, int(min_hold))
        self.bear_dd, self.bear_window, self.bear_sma = bear_dd, bear_window, bear_sma
        self._skip = max(_WARMUP_FLOOR, 5 * period, lookback)
        self._day: date | None = None
        self._o = self._h = self._l = self._c = None
        self._sessions = 0  # completed sessions
        self._prev_close: float | None = None
        self._trs: list[float] = []
        self._atr: float | None = None
        self._natrs: deque = deque(maxlen=lookback)
        self._closes: deque = deque(maxlen=max(bear_window, bear_sma or 1))
        self._pending: bool | None = None  # raw flag for the next session
        self._state: bool | None = None
        self._held = 0
        self.calm: bool | None = None

    def observe(self, timestamp, high: float, low: float, close: float) -> None:
        day = timestamp.date()
        if day != self._day:
            if self._day is not None:
                self._close_session()
                self._open_session()
            self._day = day
            self._h, self._l, self._c = high, low, close
            return
        self._h = max(self._h, high)
        self._l = min(self._l, low)
        self._c = close

    def _close_session(self) -> None:
        i = self._sessions  # index of the session just completed
        h, lo, c = self._h, self._l, self._c
        natr = None
        if self._prev_close is not None:
            pc = self._prev_close
            tr = max(h - lo, abs(h - pc), abs(lo - pc))
            if self._atr is None:
                self._trs.append(tr)
                if len(self._trs) == self.period:
                    self._atr = sum(self._trs) / self.period
                    natr = 100.0 * self._atr / c
            else:
                self._atr = (self._atr * (self.period - 1) + tr) / self.period
                natr = 100.0 * self._atr / c
        if natr is None:
            self._natrs.clear()  # the rolling median needs `lookback` CONSECUTIVE values
        else:
            self._natrs.append(natr)
        self._closes.append(c)
        calm = False
        if natr is not None and len(self._natrs) == self.lookback:
            calm = natr < float(np.median(np.fromiter(self._natrs, float)))
        if calm and self.bear_dd is not None:
            recent = list(self._closes)[-self.bear_window :]
            calm = c >= (1.0 - self.bear_dd) * max(recent)
        if calm and self.bear_sma is not None:
            recent = list(self._closes)[-self.bear_sma :]
            calm = len(recent) == self.bear_sma and c > sum(recent) / self.bear_sma
        self._pending = bool(calm) if i >= self._skip else None
        self._prev_close = c
        self._sessions += 1

    def _open_session(self) -> None:
        raw = self._pending
        if raw is None:
            self.calm = None
            return
        if self._state is None or (raw != self._state and self._held >= self.min_hold):
            self._state, self._held = raw, 1
        else:
            self._held += 1
        self.calm = self._state


__all__ = [
    "IncrementalNatrRegime",
    "apply_lag",
    "calm_by_date",
    "count_flips",
    "daily_bars",
    "debounce",
    "shift_to_next_session",
    "wilder_natr",
]
