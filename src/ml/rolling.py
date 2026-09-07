"""Bar-local features, computed ONE BAR AT A TIME instead of over a frame.

--------------------------------------------------------------------
WHY THIS EXISTS AS WELL AS features.bar_features()

That function is offline: it is handed a whole DataFrame and returns a
whole DataFrame, which is exactly right for tools/build_ml_dataset.py.
It is exactly wrong for a SizingStrategy. A strategy is constructed
once per backtest combination with only its `strategy_params` --
src/strategy_registry.STRATEGIES maps an id straight to a class, and
optimization_controller.py constructs it as `strategy_class(**params)`
with no DataFrame in scope -- and then sees the run bar by bar through
MarketContext, in order, exactly once, exactly like a live deployment
would. There is no "give me the whole history" hook to add one without
either handing every strategy the entire backtest (defeating the
isolation _simulate_single's docstring describes) or making backtest
and live strategies work differently, which is the drift this project
has repeatedly spent effort removing (see src/strategy_registry.py's
own docstring on exactly that).

So a strategy that wants what features.bar_features() computes has to
build it up incrementally, the same way src/sizing_indicators.py's
RollingMax and WilderRSI already do for the strategies that exist
today. This is that, for the 21 of features.py's 22 bar-local columns
that MarketContext can actually supply.

--------------------------------------------------------------------
VOLUME_RATIO_390B IS DELIBERATELY MISSING, AND THAT IS NOT AN OVERSIGHT

MarketContext carries OHLC and portfolio state, not volume -- the same
gap this project already hit and deferred once before, for RSI
(architecture notes for the web UI plan: "RSI is the exception: it
exists only as a private _rsi() ... and is NOT a MarketContext field
... adding it means populating all four construction sites ...
Deferred to Phase 5"). Adding a field to a dataclass four other modules
construct is a real, separate change with its own blast radius, not a
line item inside this one. So the persisted model this feeds is
trained on 21 bar-local features, not features.py's 22 -- see
tools/train_ml_model.py, which drops the same column for the same
reason and says so.

--------------------------------------------------------------------
THE PART THAT HAS TO MATCH EXACTLY: SHIFT-BY-ONE, AND RSI's FORMULA

features.bar_features() computes every column from bars [0, i] and then
calls .shift(1) on the WHOLE frame, so the value attached to bar i
describes bars < i -- including minute_of_session/day_of_week, which
therefore describe the PREVIOUS bar's clock position, not the current
one. That is a slightly odd artifact of shifting indiscriminately, and
this class reproduces it deliberately rather than "fixing" it: the
persisted model was trained on the odd version, and matching training
is the only thing that matters here.

RSI is the other trap. features._rsi() is pandas' `ewm(alpha=1/window,
adjust=False)`, which is NOT the classic Wilder seed-with-a-simple-
average method src.sizing_indicators.WilderRSI implements -- the two
converge but differ during warmup and hold a persistent, small
difference after it. Reusing WilderRSI here would quietly feed the
model a different RSI than it was trained on, so RSI is re-derived
below to match the exact recursive formula pandas' ewm(adjust=False)
uses, not imported from sizing_indicators.

tests/unit/test_ml_rolling.py runs this bar-by-bar against
features.bar_features() over real data and asserts they agree -- the
only way subtle mismatches like the two above stay caught rather than
silently degrading a model that validates perfectly offline.
"""

from __future__ import annotations

import math
from datetime import datetime
from zoneinfo import ZoneInfo

import numpy as np

_NY = ZoneInfo("America/New_York")

# Mirrors features.py's _BAR_WINDOWS and the (60, 390, 1950) range windows.
_RETURN_WINDOWS = (5, 15, 60, 390)
_RANGE_WINDOWS = (60, 390, 1950)
_MAX_WINDOW = max(*_RETURN_WINDOWS, *_RANGE_WINDOWS)  # 1950: how much history to retain


class _Ring:
    """A fixed-capacity FIFO of floats, oldest evicted first.

    Plain numpy rather than a smarter structure: capacity tops out at
    1950 (one bar-local feature's widest window), and a strategy sees
    one push per bar -- this is not a hot enough path to justify more
    than "an array with a moving write pointer".
    """

    __slots__ = ("_buffer", "_capacity", "_count", "_head")

    def __init__(self, capacity: int) -> None:
        self._capacity = capacity
        self._buffer = np.full(capacity, np.nan, dtype=np.float64)
        self._count = 0
        self._head = 0  # next write position

    def push(self, value: float) -> None:
        self._buffer[self._head] = value
        self._head = (self._head + 1) % self._capacity
        self._count = min(self._count + 1, self._capacity)

    def window(self, size: int) -> np.ndarray:
        """The most recent `size` values, oldest first, or fewer if not
        yet available -- the caller checks `len()` against min_periods
        itself, matching pandas' own min_periods contract rather than
        silently padding."""
        size = min(size, self._count)
        if size == 0:
            return np.empty(0, dtype=np.float64)
        if size <= self._head or self._count < self._capacity:
            start = self._head - size
            if start >= 0:
                return self._buffer[start : self._head]
        # Wrapped: the window spans the end and the start of the array.
        idx = (np.arange(self._head - size, self._head)) % self._capacity
        return self._buffer[idx]

    @property
    def count(self) -> int:
        return self._count

    def last(self) -> float | None:
        if self._count == 0:
            return None
        return float(self._buffer[(self._head - 1) % self._capacity])


class _EwmRsi:
    """RSI via ewm(alpha=1/period, adjust=False) -- pandas' recursion,
    replicated exactly rather than approximated. See module docstring."""

    def __init__(self, period: int) -> None:
        self._alpha = 1.0 / period
        self._period = period
        self._prev_close: float | None = None
        self._avg_gain: float | None = None
        self._avg_loss: float | None = None
        self._seen = 0

    def update(self, close: float) -> float:
        if self._prev_close is None:
            self._prev_close = close
            # pandas' diff() makes the first delta NaN, and ewm seeds
            # its recursion on the first NON-NaN value it sees, which
            # is the SECOND close's gain/loss -- not a synthetic zero.
            return 50.0

        change = close - self._prev_close
        self._prev_close = close
        gain, loss = max(change, 0.0), max(-change, 0.0)

        if self._avg_gain is None:
            self._avg_gain, self._avg_loss = gain, loss
        else:
            self._avg_gain = self._alpha * gain + (1 - self._alpha) * self._avg_gain
            self._avg_loss = self._alpha * loss + (1 - self._alpha) * self._avg_loss
        self._seen += 1

        if self._seen < self._period:
            # matches ewm(..., min_periods=window) masking to NaN,
            # which _rsi() then .fillna(50.0)'s.
            return 50.0
        return self.peek()

    def peek(self) -> float:
        """The RSI as it currently stands, without folding in a new
        price -- what record() needs: the value as of the PREVIOUS
        close, read before this bar's close updates it."""
        if self._seen < self._period or self._avg_loss is None:
            return 50.0
        if self._avg_loss == 0.0:
            return 50.0 if self._avg_gain == 0.0 else 100.0
        strength = self._avg_gain / self._avg_loss
        return 100.0 - 100.0 / (1.0 + strength)


class IncrementalBarFeatures:
    """The live/backtest-safe twin of features.bar_features(), minus
    volume_ratio_390b (MarketContext carries no volume -- see module
    docstring). record() returns the CAUSAL feature vector -- built
    from bars strictly before this one -- then folds this bar in."""

    def __init__(self) -> None:
        self._close = _Ring(_MAX_WINDOW)
        self._high = _Ring(_MAX_WINDOW)
        self._low = _Ring(_MAX_WINDOW)
        self._log_return = _Ring(_MAX_WINDOW)
        self._rvol_15b_history = _Ring(390)  # feeds rvol_of_rvol
        self._true_range = _Ring(390)
        self._rsi_14 = _EwmRsi(14)
        self._rsi_60 = _EwmRsi(60)
        self._prev_close: float | None = None
        self._prev_timestamp: datetime | None = None

    @staticmethod
    def _rvol(log_returns: np.ndarray, window: int) -> float:
        needed = window // 2
        if log_returns.size < needed or log_returns.size < 2:
            return float("nan")
        # ddof=1: pandas' .std() default, which bar_features() relies on
        # implicitly by never passing ddof itself.
        return float(np.std(log_returns, ddof=1) * math.sqrt(390 * 252))

    def _session_fields(self, timestamp: datetime | None) -> tuple[float, float]:
        if timestamp is None:
            return float("nan"), float("nan")
        local = timestamp.astimezone(_NY)
        minute = (local.hour * 60 + local.minute) - (9 * 60 + 30)
        return float(minute), float(local.weekday())

    def record(
        self, timestamp: datetime, high: float, low: float, close: float
    ) -> dict[str, float]:
        """The feature vector describing bars strictly before `timestamp`,
        THEN folds this bar's own OHLC into the rolling state.

        The very first call has no bar before it at all -- not "not
        enough history for a wide window", genuinely nothing -- and
        every offline column is NaN there too: bar_features() shifts
        the WHOLE frame by one, so row 0 is NaN across every column
        including the ones (like RSI) whose own internal warmup
        otherwise fills with a neutral value. Trackers that default to
        a neutral reading before they are seeded (_EwmRsi.peek()
        returns 50.0) would otherwise disagree with that blanket NaN
        on this one call only.
        """
        if self._prev_timestamp is None:
            self._fold_in(timestamp, high, low, close)
            return dict.fromkeys(FEATURE_NAMES, float("nan"))

        out: dict[str, float] = {}

        closes = self._close.window(_MAX_WINDOW)
        highs = self._high.window(_MAX_WINDOW)
        lows = self._low.window(_MAX_WINDOW)
        returns = self._log_return.window(_MAX_WINDOW)

        for window in _RETURN_WINDOWS:
            out[f"return_{window}b"] = (
                float(closes[-1] / closes[-1 - window] - 1.0)
                if closes.size > window
                else float("nan")
            )
            out[f"rvol_{window}b"] = self._rvol(returns[-window:], window)

        fast, slow = out["rvol_15b"], out["rvol_390b"]
        out["rvol_ratio_15_390"] = float("nan") if slow == 0.0 or math.isnan(slow) else fast / slow

        rvol_history = self._rvol_15b_history.window(390)
        out["rvol_of_rvol"] = (
            float(np.std(rvol_history, ddof=1)) if rvol_history.size >= 100 else float("nan")
        )

        for window in _RANGE_WINDOWS:
            needed = window // 4
            window_high = highs[-window:]
            window_low = lows[-window:]
            if window_high.size < needed or window_high.size == 0:
                out[f"position_in_range_{window}b"] = float("nan")
                out[f"drawdown_from_high_{window}b"] = float("nan")
                continue
            hi, lo = float(np.max(window_high)), float(np.min(window_low))
            last_close = float(closes[-1]) if closes.size else float("nan")
            out[f"position_in_range_{window}b"] = (
                min(max((last_close - lo) / (hi - lo), 0.0), 1.0) if hi != lo else float("nan")
            )
            out[f"drawdown_from_high_{window}b"] = last_close / hi - 1.0 if hi else float("nan")

        # Read BEFORE this bar's close is folded in below, matching the
        # shift(1) contract: bar i's RSI describes bars < i.
        out["rsi_14"] = self._rsi_14.peek()
        out["rsi_60"] = self._rsi_60.peek()

        true_ranges = self._true_range.window(390)
        out["natr_390b"] = (
            float(np.mean(true_ranges) / closes[-1] * 100)
            if true_ranges.size >= 100 and closes.size
            else float("nan")
        )

        out["minute_of_session"], out["day_of_week"] = self._session_fields(self._prev_timestamp)

        self._fold_in(timestamp, high, low, close)
        return out

    def _fold_in(self, timestamp: datetime, high: float, low: float, close: float) -> None:
        """Push this bar's own OHLC into the rolling state, for the
        NEXT call to record() to describe. Safe to call when this is
        the very first bar ever seen (self._prev_close is None): the
        log-return/true-range push is skipped, since there is no prior
        close to difference against, and every tracker below already
        treats "first observation" as seeding rather than updating."""
        if self._prev_close is not None:
            self._log_return.push(
                math.log(close / self._prev_close) if close > 0 and self._prev_close > 0 else 0.0
            )
            true_range = max(high - low, abs(high - self._prev_close), abs(low - self._prev_close))
        else:
            # No prior close to difference against -- pandas' own
            # true-range computation hits the identical gap (prev_close
            # is NaN at row 0) and its .max(axis=1) SKIPS NaN by
            # default, leaving plain high-low rather than NaN. Omitting
            # this bar from the buffer entirely (as an earlier version
            # did) left every rolling mean short exactly one term for
            # as long as this bar stays inside the window -- measured
            # as an exact match from bar 391 on, and a growing-then-
            # shrinking few-hundredths-of-a-point gap before it.
            true_range = high - low
        self._true_range.push(true_range)
        self._close.push(close)
        self._high.push(high)
        self._low.push(low)
        self._prev_close = close
        self._prev_timestamp = timestamp

        new_rvol_15 = self._rvol(self._log_return.window(15), 15)
        if not math.isnan(new_rvol_15):
            self._rvol_15b_history.push(new_rvol_15)
        self._rsi_14.update(close)
        self._rsi_60.update(close)


FEATURE_NAMES: tuple[str, ...] = (
    "return_5b",
    "return_15b",
    "return_60b",
    "return_390b",
    "rvol_5b",
    "rvol_15b",
    "rvol_60b",
    "rvol_390b",
    "rvol_ratio_15_390",
    "rvol_of_rvol",
    "position_in_range_60b",
    "drawdown_from_high_60b",
    "position_in_range_390b",
    "drawdown_from_high_390b",
    "position_in_range_1950b",
    "drawdown_from_high_1950b",
    "rsi_14",
    "rsi_60",
    "natr_390b",
    "minute_of_session",
    "day_of_week",
)
