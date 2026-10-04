"""
Intraday buy gates from the correction-strategy catalog
(docs/research/correction-strategies.md): C-M1, C-MS3, C-X4 and C-MR7.

Each one only ever BLOCKS new buys -- it never sells -- so none of them can
realize a loss. They share entry_gates.py's interface (`mode`, `enabled`,
`suppressed`, `observe(context)`, `episodes`, `suppressed_bars`) and its
session and causality conventions: a session is keyed by the date of its
regular-session bars (time_of_day_flag >= 0), out-of-session bars are
ignored, and the decision for bar t uses only bars before t plus bar t's
OPEN, which is known when bar t starts.

C-M1  NoiseAreaGate -- Zarattini, Aziz & Barbon, "Beat the Market: An
      Effective Intraday Momentum Strategy for S&P500 ETF (SPY)", SFI
      Research Paper 24-97, 2024. Their definitions, verbatim:

        sigma_{t, 9:30-HH:MM} = (1/14) * sum_{i=1..14} |move_{t-i, 9:30-HH:MM}|
        UpperBound_{t,HH:MM}  = max(Open_{t,9:30}, Close_{t-1,16:00}) * (1 + sigma)
        LowerBound_{t,HH:MM}  = min(Open_{t,9:30}, Close_{t-1,16:00}) * (1 - sigma)

      with move = price at HH:MM / that day's 09:30 open - 1. The strategy
      goes long above the Noise Area and short below it, deciding only at
      HH:00 and HH:30, and is flat at the close. The catalog uses it as a
      GATE (rank 7): grid buys pause while price is below the lower bound
      at a check, resume when a check finds it back at or above, and every
      session starts unblocked.

C-MS3 VwapGate -- the catalog's VWAP-relative gating, after the VWAP
      trailing exit inside M1: pause buys when price is far below the
      session VWAP (by `far_k` sigma) AND still falling; optionally
      (`near_k`) also require price to sit at least `near_k` sigma below
      VWAP before buying at all. VWAP is the session's volume-weighted
      typical price (H+L+C)/3 over completed bars; sigma is the stdev of
      one-bar log returns over the last `vol_window` bars. No volume (a
      path that never populates MarketContext.volume) means no VWAP and
      no gating -- inert, never stuck shut.

C-X4  SessionLotThrottle -- riskkit's SessionManager idea as the catalog
      records it: cap new lots per session, enforce a minimum number of
      bars between buys, and after `adverse_run` consecutive buys each
      below the previous one, block buys for a cooldown that doubles each
      time it re-triggers within the session. Buys are detected from
      MarketContext.open_lot_count rising between bars, and a buy's price
      is that bar's close (the fill happened inside it).

C-MR7 RBreakerGate -- R-Breaker (letianzj/QuantResearch backtest/r_breaker.py,
      credited to Richard Saidenberg, 1994). Levels from the previous
      session, verbatim from the source:

        pivot = (H + C + L) / 3
        r1 = 2*pivot - L        s1 = 2*pivot - H
        r2 = pivot + (H - L)    s2 = pivot - (H - L)
        r3 = H + 2*(pivot - L)  s3 = L - 2*(H - pivot)

      and the source's state machine, with its SHORT state read as "grid
      buys paused" (shorting is out of scope):
        flat  -> long  if price > r3;   flat -> short if price < s3
        long  -> short if (today_high > r2 and price < r1) or price < s3
        short -> long  if (today_low < s2 and price > s1) or price > r3
      The last rule is the "failed breakdown": a probe through S2 that
      recovers above S1 re-opens buying. Every session starts flat.
"""

from __future__ import annotations

import math
from collections import deque

import numpy as np

from engine.core.exceptions import ConfigurationError
from engine.core.market_context import MarketContext
from research.strategies.entry_gates import as_count

NOISE_MODES: tuple[str, ...] = ("off", "below_lower")
VWAP_MODES: tuple[str, ...] = ("off", "far_falling", "band")
THROTTLE_MODES: tuple[str, ...] = ("off", "on")
RBREAKER_MODES: tuple[str, ...] = ("off", "short_pauses")


def _minute(context: MarketContext) -> int | None:
    minute = context.time_of_day_flag
    return minute if minute >= 0 else None


def _check_mode(name: str, mode: str, modes: tuple[str, ...]) -> None:
    if mode not in modes:
        raise ConfigurationError(f"{name} must be one of {modes}, got {mode!r}")


# ---------------------------------------------------------------- C-M1


def noise_bounds(
    session_open: float, prior_close: float | None, sigma: float
) -> tuple[float, float]:
    """(LowerBound, UpperBound) with the paper's overnight-gap adjustment.
    Without a prior close (the first session) both use the open."""
    if sigma < 0:
        raise ConfigurationError(f"sigma must be >= 0, got {sigma}")
    reference_close = session_open if prior_close is None else prior_close
    return (
        min(session_open, reference_close) * (1.0 - sigma),
        max(session_open, reference_close) * (1.0 + sigma),
    )


class NoiseAreaGate:
    """Pause buys while price is below the Noise Area's lower bound."""

    def __init__(
        self, mode: str = "off", *, lookback_days: int = 14, check_minutes: int = 30
    ) -> None:
        _check_mode("noise_gate", mode, NOISE_MODES)
        self.mode = mode
        self.lookback_days = as_count("lookback_days", lookback_days)
        self.check_minutes = as_count("check_minutes", check_minutes)
        # One {minute: |move|} map per completed session, newest last.
        self._sessions: deque[dict[int, float]] = deque(maxlen=self.lookback_days)
        self._day: int | None = None
        self._open: float | None = None
        self._moves: dict[int, float] = {}
        self._last_close: float | None = None
        self._prior_close: float | None = None
        self._suppressed = False
        self.suppressed_bars = 0
        self.episodes = 0

    @property
    def enabled(self) -> bool:
        return self.mode != "off"

    @property
    def suppressed(self) -> bool:
        return self._suppressed

    def sigma(self, minute: int) -> float | None:
        """Mean |move| at `minute` over the last lookback_days completed
        sessions; None unless every one of them has that minute."""
        if len(self._sessions) < self.lookback_days:
            return None
        values = [s[minute] for s in self._sessions if minute in s]
        if len(values) < self.lookback_days:
            return None
        return float(np.mean(values))

    def bounds(self, minute: int) -> tuple[float, float] | None:
        sigma = self.sigma(minute)
        if sigma is None or self._open is None:
            return None
        return noise_bounds(self._open, self._prior_close, sigma)

    def observe(self, context: MarketContext) -> None:
        if not self.enabled:
            return
        minute = _minute(context)
        if minute is None:
            return
        day = context.timestamp.toordinal()
        if day != self._day:
            if self._open is not None:
                self._sessions.append(self._moves)
                self._prior_close = self._last_close
            self._day = day
            self._open = context.open
            self._moves = {}
            self._suppressed = False
        # Price at HH:MM is this bar's open; it is known now and is also
        # what a later session averages for this minute.
        self._moves[minute] = abs(context.open / self._open - 1.0)
        if minute > 0 and minute % self.check_minutes == 0:
            bounds = self.bounds(minute)
            if bounds is not None:
                below = context.open < bounds[0]
                if below and not self._suppressed:
                    self.episodes += 1
                self._suppressed = below
        if self._suppressed:
            self.suppressed_bars += 1
        self._last_close = context.close


# ---------------------------------------------------------------- C-MS3


def session_vwap(highs, lows, closes, volumes) -> float | None:
    """Volume-weighted typical price (H+L+C)/3; None with no volume."""
    h, lo, c, v = (np.asarray(x, dtype=float) for x in (highs, lows, closes, volumes))
    total = v.sum()
    if total <= 0:
        return None
    return float(((h + lo + c) / 3.0 * v).sum() / total)


class VwapGate:
    """Pause buys far below VWAP while still falling (and, in `band` mode,
    also above `near_k` sigma below VWAP)."""

    def __init__(
        self,
        mode: str = "off",
        *,
        far_k: float = 3.0,
        near_k: float = 1.0,
        vol_window: int = 30,
    ) -> None:
        _check_mode("vwap_gate", mode, VWAP_MODES)
        if not far_k > 0:
            raise ConfigurationError(f"far_k must be > 0, got {far_k}")
        if mode == "band" and not 0 <= near_k < far_k:
            raise ConfigurationError(f"need 0 <= near_k < far_k, got {near_k}, {far_k}")
        self.mode = mode
        self.far_k = float(far_k)
        self.near_k = float(near_k)
        self.vol_window = as_count("vol_window", vol_window, minimum=2)
        self._returns: deque[float] = deque(maxlen=self.vol_window)
        self._day: int | None = None
        self._pv = 0.0
        self._vol = 0.0
        self._pending: tuple[float, float, float, float] | None = None
        self._prev_close: float | None = None
        self._suppressed = False
        self.suppressed_bars = 0
        self.episodes = 0

    @property
    def enabled(self) -> bool:
        return self.mode != "off"

    @property
    def suppressed(self) -> bool:
        return self._suppressed

    @property
    def vwap(self) -> float | None:
        return self._pv / self._vol if self._vol > 0 else None

    @property
    def sigma(self) -> float | None:
        if len(self._returns) < self.vol_window:
            return None
        return float(np.std(np.fromiter(self._returns, float), ddof=1))

    def observe(self, context: MarketContext) -> None:
        if not self.enabled:
            return
        if _minute(context) is None:
            return
        day = context.timestamp.toordinal()
        if day != self._day:
            self._day, self._pv, self._vol, self._pending = day, 0.0, 0.0, None
        if self._pending is not None:  # the previous bar is history now
            h, lo, c, v = self._pending
            self._pv += (h + lo + c) / 3.0 * v
            self._vol += v
        self._decide(context.open)
        if self._suppressed:
            self.suppressed_bars += 1
        self._pending = (context.high, context.low, context.close, max(context.volume, 0.0))
        if self._prev_close and self._prev_close > 0 and context.close > 0:
            self._returns.append(math.log(context.close / self._prev_close))
        self._prev_close = context.close

    def _decide(self, price: float) -> None:
        vwap, sigma = self.vwap, self.sigma
        if vwap is None or sigma is None or sigma == 0:
            self._suppressed = False
            return
        deviation = price / vwap - 1.0  # in return units, compared with sigma
        falling = self._prev_close is not None and price < self._prev_close
        blocked = deviation < -self.far_k * sigma and falling
        if self.mode == "band":
            blocked = blocked or deviation > -self.near_k * sigma
        if blocked and not self._suppressed:
            self.episodes += 1
        self._suppressed = blocked


# ---------------------------------------------------------------- C-X4


class SessionLotThrottle:
    """Per-session lot cap, minimum spacing between buys, and an escalating
    cooldown after runs of adverse buys."""

    def __init__(
        self,
        mode: str = "off",
        *,
        max_lots_per_session: int | None = None,
        min_bars_between_buys: int = 0,
        adverse_run: int | None = None,
        cooldown_bars: int = 30,
    ) -> None:
        _check_mode("session_throttle", mode, THROTTLE_MODES)
        self.mode = mode
        self.max_lots = (
            None
            if max_lots_per_session is None
            else as_count("max_lots_per_session", max_lots_per_session)
        )
        self.min_spacing = as_count("min_bars_between_buys", min_bars_between_buys, minimum=0)
        self.adverse_run = None if adverse_run is None else as_count("adverse_run", adverse_run)
        self.cooldown_bars = as_count("cooldown_bars", cooldown_bars)
        self._day: int | None = None
        self._lots_prev: int | None = None
        self._bar = 0
        self._buys = 0
        self._last_buy_bar: int | None = None
        self._last_buy_price: float | None = None
        self._run = 0
        self._cooldown_until = -1
        self._next_cooldown = self.cooldown_bars
        self._suppressed = False
        self.suppressed_bars = 0
        self.episodes = 0

    @property
    def enabled(self) -> bool:
        return self.mode != "off"

    @property
    def suppressed(self) -> bool:
        return self._suppressed

    @property
    def buys_this_session(self) -> int:
        return self._buys

    def observe(self, context: MarketContext) -> None:
        if not self.enabled:
            return
        if _minute(context) is None:
            return
        day = context.timestamp.toordinal()
        if day != self._day:
            self._day = day
            self._buys = 0
            self._last_buy_bar = self._last_buy_price = None
            self._run = 0
            self._cooldown_until = -1
            self._next_cooldown = self.cooldown_bars
        self._bar += 1
        lots = context.open_lot_count
        if self._lots_prev is not None and lots > self._lots_prev:
            self._record_buys(lots - self._lots_prev, context.close)
        self._lots_prev = lots
        blocked = (
            (self.max_lots is not None and self._buys >= self.max_lots)
            or (
                self._last_buy_bar is not None and self._bar - self._last_buy_bar < self.min_spacing
            )
            or self._bar <= self._cooldown_until
        )
        if blocked and not self._suppressed:
            self.episodes += 1
        self._suppressed = blocked
        if blocked:
            self.suppressed_bars += 1

    def _record_buys(self, count: int, price: float) -> None:
        for _ in range(count):
            if self._last_buy_price is not None and price < self._last_buy_price:
                self._run += 1
            else:
                self._run = 0
            self._last_buy_price = price
            self._buys += 1
        self._last_buy_bar = self._bar
        if self.adverse_run is not None and self._run >= self.adverse_run:
            self._cooldown_until = self._bar + self._next_cooldown
            self._next_cooldown *= 2  # escalate within the session
            self._run = 0


# ---------------------------------------------------------------- C-MR7


def r_breaker_levels(high: float, low: float, close: float) -> dict[str, float]:
    """The source's seven levels from the previous session's H, L, C."""
    if not high >= low:
        raise ConfigurationError(f"need high >= low, got {high}, {low}")
    pivot = (high + close + low) / 3.0
    return {
        "pivot": pivot,
        "r1": 2 * pivot - low,
        "r2": pivot + (high - low),
        "r3": high + 2 * (pivot - low),
        "s1": 2 * pivot - high,
        "s2": pivot - (high - low),
        "s3": low - 2 * (high - pivot),
    }


class RBreakerGate:
    """R-Breaker's state machine; its short state pauses grid buys."""

    def __init__(self, mode: str = "off") -> None:
        _check_mode("rbreaker_gate", mode, RBREAKER_MODES)
        self.mode = mode
        self._day: int | None = None
        self._levels: dict[str, float] | None = None
        self._prev_hlc: tuple[float, float, float] | None = None
        self._sess: list[float] | None = None  # [high, low, close] of completed bars
        self._today_high: float | None = None
        self._today_low: float | None = None
        self._pending: tuple[float, float, float] | None = None
        self.state = "flat"
        self.suppressed_bars = 0
        self.episodes = 0

    @property
    def enabled(self) -> bool:
        return self.mode != "off"

    @property
    def suppressed(self) -> bool:
        return self.state == "short"

    @property
    def levels(self) -> dict[str, float] | None:
        return self._levels

    def observe(self, context: MarketContext) -> None:
        if not self.enabled:
            return
        if _minute(context) is None:
            return
        day = context.timestamp.toordinal()
        if day != self._day:
            if self._pending is not None:
                self._fold(*self._pending)
            if self._sess is not None:
                self._prev_hlc = (self._sess[0], self._sess[1], self._sess[2])
            self._day = day
            self._sess = None
            self._pending = None
            self._today_high = self._today_low = None
            self.state = "flat"
            self._levels = r_breaker_levels(*self._prev_hlc) if self._prev_hlc else None
        elif self._pending is not None:
            self._fold(*self._pending)
        price = context.open
        hi = price if self._today_high is None else max(self._today_high, price)
        lo = price if self._today_low is None else min(self._today_low, price)
        if self._levels is not None:
            self._step(price, hi, lo)
        if self.suppressed:
            self.suppressed_bars += 1
        self._pending = (context.high, context.low, context.close)

    def _fold(self, high: float, low: float, close: float) -> None:
        if self._sess is None:
            self._sess = [high, low, close]
        else:
            self._sess = [max(self._sess[0], high), min(self._sess[1], low), close]
        self._today_high = high if self._today_high is None else max(self._today_high, high)
        self._today_low = low if self._today_low is None else min(self._today_low, low)

    def _step(self, price: float, today_high: float, today_low: float) -> None:
        lv = self._levels
        before = self.state
        if self.state == "flat":
            if price > lv["r3"]:
                self.state = "long"
            elif price < lv["s3"]:
                self.state = "short"
        elif self.state == "long":
            if (today_high > lv["r2"] and price < lv["r1"]) or price < lv["s3"]:
                self.state = "short"
        elif (today_low < lv["s2"] and price > lv["s1"]) or price > lv["r3"]:
            self.state = "long"
        if self.state == "short" and before != "short":
            self.episodes += 1
