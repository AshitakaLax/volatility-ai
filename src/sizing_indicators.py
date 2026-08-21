"""
Incremental indicators shared by the sizing strategies.

Extracted rather than inlined per strategy for one specific reason:
backtest/live parity. src/live_trading_loop.py and
optimization_controller.py drive the SAME strategy objects through the
same src/decision_cycle.py functions, so a second copy of the RSI or
rolling-high arithmetic would be a place where simulated and live
sizing could silently disagree. There is exactly one implementation of
each.

--------------------------------------------------------------------
EVERYTHING HERE IS INCREMENTAL AND BOUNDED.

No indicator retains the full price history. A sweep constructs one
strategy per combination and Task 4.6's params capture reads the
strategy's attributes, so an unbounded list would be both a memory
cost per combination and a 400k-element object hanging off a result
record. Rolling maxima use a monotonic deque (amortized O(1), evicted
by age); RSI carries two floats.
--------------------------------------------------------------------
ON WINDOW LENGTHS -- the mistake this module exists to make hard:

A "252-bar" window is one trading YEAR on daily bars and about
FORTY MINUTES on 1-minute bars. Measured against this repo's own
5-year TQQQ minute dataset, a 252-bar "52-week high" put 62% of all
bars into a Gaussian multiplier between 0.10 and 0.20 -- a near
constant, not a model, because the drawdown-from-high never got
anywhere near the distribution's centre.

So windows are specified in TRADING DAYS and converted through an
explicit bars_per_day. Callers must state the bar frequency; there is
no default that silently means something different on different data.
"""

from __future__ import annotations

from collections import deque

from src.exceptions import ConfigurationError


def bars_from_days(days: float, bars_per_day: int) -> int:
    """Convert a window expressed in trading days into a bar count.

    Both arguments are required and validated. The whole point is that
    a window length is meaningless without knowing the bar frequency --
    see the module docstring for what happens when that is assumed.
    """
    if days <= 0:
        raise ConfigurationError(f"window in days must be positive, got {days}")
    if bars_per_day <= 0:
        raise ConfigurationError(f"bars_per_day must be positive, got {bars_per_day}")
    # round() on a float already returns an int; max(1, ...) is what
    # keeps a sub-bar window (e.g. 0.001 days) from becoming zero.
    return max(1, round(days * bars_per_day))


def clamp(value: float, low: float, high: float) -> float:
    """Constrain value to [low, high]."""
    return max(low, min(high, value))


class RollingMax:
    """Maximum over the most recent `window` observations.

    Monotonic deque: values that can never again be the maximum are
    discarded on insert, so the structure stays far smaller than the
    window on real price data while remaining exact. Entries are
    evicted by age rather than by a maxlen, because the eviction
    condition is "older than the window", not "more than N candidates".
    """

    def __init__(self, window: int) -> None:
        if window <= 0:
            raise ConfigurationError(f"RollingMax window must be positive, got {window}")
        self.window = window
        self._entries: deque[tuple[int, float]] = deque()
        self._index = -1

    def update(self, value: float) -> float:
        """Add one observation and return the current window maximum."""
        self._index += 1
        # Anything <= the incoming value can never be the max again.
        while self._entries and self._entries[-1][1] <= value:
            self._entries.pop()
        self._entries.append((self._index, value))
        cutoff = self._index - self.window + 1
        while self._entries and self._entries[0][0] < cutoff:
            self._entries.popleft()
        return self._entries[0][1]

    @property
    def value(self) -> float | None:
        """Current maximum, or None before the first observation."""
        return self._entries[0][1] if self._entries else None

    @property
    def count(self) -> int:
        """Observations seen. Lets a caller distinguish a full window
        from a partially-warmed one without a separate flag."""
        return self._index + 1


class WilderRSI:
    """Wilder's RSI, updated one price at a time.

    Wilder's smoothing (not a simple moving average) is the standard
    definition, and the one every charting package means by "RSI(14)".
    The first `period` changes seed the averages with a simple mean;
    after that each update is the recursive smoothing step.

    Returns None until seeded rather than emitting a provisional value.
    A partially-warmed RSI is not a small error -- with fewer than
    `period` changes it can sit at an extreme -- and a caller that
    treats None explicitly cannot mistake it for a real reading.
    """

    def __init__(self, period: int = 14) -> None:
        if period < 2:
            raise ConfigurationError(f"RSI period must be >= 2, got {period}")
        self.period = period
        self._prev_price: float | None = None
        self._avg_gain: float | None = None
        self._avg_loss: float | None = None
        self._seed_gains = 0.0
        self._seed_losses = 0.0
        self._changes_seen = 0

    def update(self, price: float) -> float | None:
        """Add one close and return the current RSI, or None if unseeded."""
        if self._prev_price is None:
            self._prev_price = price
            return None

        change = price - self._prev_price
        self._prev_price = price
        gain = max(0.0, change)
        loss = max(0.0, -change)

        if self._avg_gain is None:
            self._seed_gains += gain
            self._seed_losses += loss
            self._changes_seen += 1
            if self._changes_seen < self.period:
                return None
            self._avg_gain = self._seed_gains / self.period
            self._avg_loss = self._seed_losses / self.period
        else:
            n = self.period
            self._avg_gain = (self._avg_gain * (n - 1) + gain) / n
            self._avg_loss = (self._avg_loss * (n - 1) + loss) / n

        return self._rsi()

    def _rsi(self) -> float:
        # An all-gains window has no downside to divide by. RSI is 100
        # by definition there; computing RS first would divide by zero.
        if self._avg_loss == 0:
            return 100.0 if self._avg_gain > 0 else 50.0
        rs = self._avg_gain / self._avg_loss
        return 100.0 - (100.0 / (1.0 + rs))

    @property
    def value(self) -> float | None:
        """Current RSI, or None before the seeding window completes."""
        if self._avg_gain is None:
            return None
        return self._rsi()
