"""The features the meta-label model sees: one definition, shared by the
dataset builder (research/ml/meta_dataset.py) and the strategy that trades
the model (research/ml/meta_label_sizing.py).

--------------------------------------------------------------------
ONE CLASS, TWO CALLERS, SO TRAINING AND TRADING CANNOT DISAGREE

docs/ml_plan.md's first rule: "two implementations of 'the features' is
exactly how a model trained on one thing gets deployed predicting
another". So there is one implementation. `MetaFeatures` is fed one bar at
a time (`fold`) and asked for a feature vector at a buy (`snapshot`). The
dataset builder walks the bar history and calls the two methods in the
same order the strategy does inside the engine: `snapshot(bar t)` before
`fold(bar t)`. The vectors are equal by construction, and
research/tests/test_meta_label.py checks it through the real controller.

--------------------------------------------------------------------
CAUSAL UNDER BOTH FILL MODELS

At a buy on bar t the state holds bars up to and including t-1. Bar t
contributes only its timestamp, its open and the entry price:

  * fill_model="close": the buy is decided at the close, so the close is
    the entry price and is known.
  * fill_model="intrabar": the buy fills when the bar's low touches the
    level, somewhere inside the bar. Bar t's high, low and close are not
    known at that moment, and a feature that read them would score a
    lookahead the engine's "causal" fill exists to remove.

The strategy keeps bar t pending in record_tick and folds it at the next
bar. The builder does the same. Neither ever folds bar t before the
snapshot of bar t.

--------------------------------------------------------------------
WHAT IS IN IT

Price and time only: OHLC, the timestamp, the entry price. No volume (the
live feed carries none), no book state (cash, open lots, drawdown depend
on how a run sized its buys, so the builder could not reproduce them) and
no outside series (the warehouse's macro lake is not on the live path).
Three groups:

  entry       where this buy sits: below the rolling high, against the
              previous bar, the session's open, high and low, the day's
              move, the minute of the session and the weekday
  bars        the last session of bars: returns over a few horizons,
              realized volatility (fast, session, their ratio), mean bar
              range, RSI(14), distance from the session-window high
  sessions    completed sessions only: 1/5/20/60-session returns,
              5/20/60-session volatility, distance from the 50- and
              200-session means and from the 252-session high, daily
              RSI(14), the run of down sessions

A value with too little history is NaN; LightGBM routes missing values
down a learned branch, and the model is trained on the same NaNs at the
start of the data.

A session is a New York calendar date. The strategy reads it from each
bar's timestamp with `session_clock`; the builder converts the whole
index at once with `session_clock_arrays`. The two are pinned equal in
the tests, across both daylight-saving changes.
"""

from __future__ import annotations

import math
from collections import deque
from datetime import UTC
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd

from engine.core.exceptions import ConfigurationError
from research.strategies.sizing_indicators import (
    RollingMax,
    RollingMean,
    RollingStdev,
    WilderRSI,
)

NEW_YORK = ZoneInfo("America/New_York")
_OPEN_MINUTE = 9 * 60 + 30  # 09:30 New York
_ORDINAL_1970 = 719163  # date(1970, 1, 1).toordinal()

FEATURE_NAMES: tuple[str, ...] = (
    # entry
    "pullback",
    "ret_entry",
    "gap",
    "session_ret",
    "from_session_high",
    "from_session_low",
    "day_ret",
    "minute",
    "weekday",
    # bars, through the previous bar
    "ret_vfast",
    "ret_fast",
    "ret_session",
    "rv_fast",
    "rv_session",
    "rv_ratio",
    "range_fast",
    "rsi",
    "from_window_high",
    # completed sessions
    "d_ret_1",
    "d_ret_5",
    "d_ret_20",
    "d_ret_60",
    "d_vol_5",
    "d_vol_20",
    "d_vol_60",
    "d_sma50",
    "d_sma200",
    "d_dd_252",
    "d_rsi",
    "d_down_streak",
)

# Completed sessions the daily group needs before every value is defined.
DAILY_HISTORY_SESSIONS = 253


def session_clock(timestamp) -> tuple[int, float, int]:
    """(New York date ordinal, minutes since 09:30 New York, weekday) of
    one timestamp. A naive timestamp is read as UTC, the warehouse's
    convention."""
    if timestamp.tzinfo is None:
        timestamp = timestamp.replace(tzinfo=UTC)
    local = timestamp.astimezone(NEW_YORK)
    minute = local.hour * 60 + local.minute + local.second / 60.0 - _OPEN_MINUTE
    return local.toordinal(), minute, local.weekday()


def session_clock_arrays(index: pd.DatetimeIndex) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """`session_clock` over a whole index at once (the builder's path)."""
    if index.tz is None:
        index = index.tz_localize("UTC")
    local = index.tz_convert(NEW_YORK).tz_localize(None)
    days = local.values.astype("datetime64[D]")
    ordinal = days.astype(np.int64) + _ORDINAL_1970
    minute = (local.values - days.astype("datetime64[ns]")).astype(np.int64) / 6e10
    return ordinal, minute - _OPEN_MINUTE, np.asarray(local.day_of_week, dtype=np.int64)


def _ratio(a: float | None, b: float | None) -> float:
    if a is None or b is None or b <= 0 or not math.isfinite(a):
        return math.nan
    return a / b - 1.0


class MetaFeatures:
    """Incremental feature state. `fold` one bar, `snapshot` at a buy."""

    def __init__(self, bars_per_day: int, lookback_bars: int) -> None:
        if bars_per_day < 1:
            raise ConfigurationError(f"bars_per_day must be >= 1, got {bars_per_day}")
        if lookback_bars < 1:
            raise ConfigurationError(f"lookback_bars must be >= 1, got {lookback_bars}")
        self.bars_per_day = bars_per_day
        self.lookback_bars = lookback_bars
        self.vfast = max(2, round(bars_per_day / 78))  # ~5 minute bars
        self.fast = max(2, round(bars_per_day / 13))  # ~30 minute bars
        self.session = max(2, bars_per_day)
        self._closes: deque[float] = deque(maxlen=self.session + 1)
        self._rv_fast = RollingStdev(self.fast)
        self._rv_session = RollingStdev(self.session)
        self._range_fast = RollingMean(self.fast)
        self._reference_high = RollingMax(lookback_bars)
        self._window_high = RollingMax(self.session)
        self._rsi = WilderRSI(14)
        self._prev_close: float | None = None
        # the session in progress
        self._day: int | None = None
        self._session_open = math.nan
        self._session_high = math.nan
        self._session_low = math.nan
        # completed sessions
        self._d_closes: deque[float] = deque(maxlen=61)
        self._d_vol = {n: RollingStdev(n) for n in (5, 20, 60)}
        self._d_sma = {n: RollingMean(n) for n in (50, 200)}
        self._d_high = RollingMax(252)
        self._d_rsi = WilderRSI(14)
        self._d_down_streak = 0

    # -- sessions --------------------------------------------------------

    def _complete_session(self, close: float) -> None:
        if self._d_closes:
            prior = self._d_closes[-1]
            if prior > 0 and close > 0:
                r = math.log(close / prior)
                for window in self._d_vol.values():
                    window.update(r)
            self._d_down_streak = self._d_down_streak + 1 if close < prior else 0
        self._d_closes.append(close)
        for window in self._d_sma.values():
            window.update(close)
        self._d_high.update(close)
        self._d_rsi.update(close)

    def _enter_session(self, day: int, open_: float) -> None:
        """Bar `day` opens a new session: the previous one (ended by the
        last folded bar) is complete. Idempotent within a session, so a
        snapshot and the fold of the same bar can both call it."""
        if day == self._day:
            return
        if self._day is not None and self._prev_close is not None:
            self._complete_session(self._prev_close)
        self._day = day
        self._session_open = open_
        self._session_high = open_
        self._session_low = open_

    def warm_up(self, daily_closes) -> int:
        """Seed the completed-session group from closes before the first
        bar (a windowed backtest's history; the live loop replays bars
        instead). Returns the sessions used."""
        if self._day is not None or self._d_closes:
            raise ConfigurationError("warm_up must come before the first bar")
        used = 0
        for close in daily_closes:
            if close is not None and math.isfinite(float(close)) and float(close) > 0:
                self._complete_session(float(close))
                used += 1
        return used

    # -- the two calls ---------------------------------------------------

    def fold(self, day: int, open_: float, high: float, low: float, close: float) -> None:
        """Bar t joins the state (call after any snapshot of bar t)."""
        self._enter_session(day, open_)
        if high > self._session_high:
            self._session_high = high
        if low < self._session_low:
            self._session_low = low
        if close <= 0:
            return
        prev = self._prev_close
        if prev is not None and prev > 0:
            r = math.log(close / prev)
            self._rv_fast.update(r)
            self._rv_session.update(r)
        self._range_fast.update((high - low) / close)
        self._reference_high.update(close)
        self._window_high.update(close)
        self._rsi.update(close)
        self._closes.append(close)
        self._prev_close = close

    def snapshot(
        self, day: int, minute: float, weekday: int, open_: float, entry: float
    ) -> np.ndarray:
        """The feature vector for a buy at `entry` on the bar opening at
        `open_`, from bars before it. Order: FEATURE_NAMES."""
        self._enter_session(day, open_)
        prev = self._prev_close
        closes = self._closes
        last = closes[-1] if closes else None

        def back(k: int) -> float:
            return _ratio(last, closes[-1 - k]) if len(closes) > k else math.nan

        rv_fast = self._rv_fast.value if self._rv_fast.count >= self.fast else None
        rv_session = self._rv_session.value if self._rv_session.count >= self.session else None
        rv_ratio = (
            rv_fast / rv_session
            if rv_fast is not None and rv_session is not None and rv_session > 1e-12
            else math.nan
        )
        session_high = max(self._session_high, open_)
        session_low = min(self._session_low, open_)
        d = self._d_closes
        d_last = d[-1] if d else None

        def d_back(k: int) -> float:
            return _ratio(d_last, d[-1 - k]) if len(d) > k else math.nan

        def d_vol(n: int) -> float:
            w = self._d_vol[n]
            return w.value if w.count >= n and w.value is not None else math.nan

        def d_sma(n: int) -> float:
            w = self._d_sma[n]
            return _ratio(d_last, w.value) if w.count >= n else math.nan

        rsi = self._rsi.value
        d_rsi = self._d_rsi.value
        return np.array(
            [
                _ratio(entry, self._reference_high.value),
                _ratio(entry, prev),
                _ratio(open_, prev),
                _ratio(entry, self._session_open),
                _ratio(entry, session_high),
                _ratio(entry, session_low),
                _ratio(entry, d_last),
                minute,
                float(weekday),
                back(self.vfast),
                back(self.fast),
                back(self.session),
                math.nan if rv_fast is None else rv_fast,
                math.nan if rv_session is None else rv_session,
                rv_ratio,
                math.nan if self._range_fast.value is None else self._range_fast.value,
                math.nan if rsi is None else rsi,
                _ratio(last, self._window_high.value),
                d_back(1),
                d_back(5),
                d_back(20),
                d_back(60),
                d_vol(5),
                d_vol(20),
                d_vol(60),
                d_sma(50),
                d_sma(200),
                _ratio(d_last, self._d_high.value) if self._d_high.count >= 252 else math.nan,
                math.nan if d_rsi is None else d_rsi,
                float(self._d_down_streak) if d else math.nan,
            ],
            dtype=np.float64,
        )


__all__ = [
    "DAILY_HISTORY_SESSIONS",
    "FEATURE_NAMES",
    "MetaFeatures",
    "session_clock",
    "session_clock_arrays",
]
