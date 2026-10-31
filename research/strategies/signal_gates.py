"""
Entry gates for the ranked list's single-symbol signals (ledger RK14, RK55,
RK64, RK79, RK112, RK147, RK161, RK168, RK208, RK243, RK253, RK294, RK297).

Each gate turns a published signal into the one decision a long-only grid
can take from it: whether to allow new buys on this bar. None of them
sells; open lots still exit only at their targets through the no-loss
guard. They are used only by `signal_gated_sizing.SignalGatedSizing`
(strategy_id `hf_signal_gated`), so `hf_entry_gated`, the champion and the
Ultimate family are untouched by anything here.

The interface is entry_gates.py's: `enabled`, `suppressed`, `observe(context)`
once per bar from record_tick, `episodes`, `suppressed_bars`, plus
`history_sessions` (how many sessions a live loop must replay first).

CAUSALITY. A bar's own high, low, close and volume never decide that bar:
every gate holds a bar back until the next one arrives (the `_pending`
pattern of entry_gates.py), because the intrabar fill model compares the
grid level with the bar's LOW. Daily indicators use completed sessions
only. The one value read from the current bar is its OPEN (the gap gate),
which is known when the bar starts.

UNMEASURED. Every gate defaults to "off", and none has been swept.
"""

from __future__ import annotations

import bisect
import csv
import math
from collections import deque
from datetime import date, datetime
from itertools import pairwise
from pathlib import Path

import numpy as np

from engine.core.exceptions import ConfigurationError
from engine.core.market_context import MarketContext
from research.strategies.entry_gates import CandleStream, as_count
from research.strategies.mean_reversion import hurst_exponent

SESSION_MINUTES = 390


def _minute(context: MarketContext) -> int | None:
    minute = context.time_of_day_flag
    return minute if minute >= 0 else None


def _check_mode(name: str, mode: str, modes: tuple[str, ...]) -> None:
    if mode not in modes:
        raise ConfigurationError(f"{name} must be one of {modes}, got {mode!r}")


def _positive(name: str, value: float) -> float:
    value = float(value)
    if not value > 0:
        raise ConfigurationError(f"{name} must be > 0, got {value}")
    return value


# ---------------------------------------------------------------- shared machinery


class SessionBook:
    """Regular-session bars folded into completed daily sessions, causally.

    `push(context)` folds the PREVIOUS bar (held back one bar) and returns
    True when this bar opens a new session, i.e. when the session before it
    has just completed. Completed sessions are kept in parallel deques of at
    most `keep` entries."""

    def __init__(self, keep: int) -> None:
        self.keep = int(keep)
        self.days: deque[int] = deque(maxlen=self.keep)
        self.opens: deque[float] = deque(maxlen=self.keep)
        self.highs: deque[float] = deque(maxlen=self.keep)
        self.lows: deque[float] = deque(maxlen=self.keep)
        self.closes: deque[float] = deque(maxlen=self.keep)
        self.volumes: deque[float] = deque(maxlen=self.keep)
        self._day: int | None = None
        self._building: list[float] | None = None
        self._pending: tuple[int, float, float, float, float, float] | None = None
        self.completed = 0

    def push(self, context: MarketContext) -> bool:
        if _minute(context) is None:
            return False
        if self._pending is not None:
            day, o, h, lo, c, v = self._pending
            self._pending = None
            if self._building is None:
                self._building = [o, h, lo, c, v]
            else:
                b = self._building
                b[1], b[2], b[3], b[4] = max(b[1], h), min(b[2], lo), c, b[4] + v
        day = context.timestamp.toordinal()
        rolled = False
        if day != self._day:
            if self._building is not None and self._day is not None:
                o, h, lo, c, v = self._building
                self.days.append(self._day)
                self.opens.append(o)
                self.highs.append(h)
                self.lows.append(lo)
                self.closes.append(c)
                self.volumes.append(v)
                self.completed += 1
                rolled = True
            self._building = None
            self._day = day
        self._pending = (
            day,
            context.open,
            context.high,
            context.low,
            context.close,
            float(context.volume),
        )
        return rolled


class _Gate:
    """Bookkeeping shared by every gate: mode, counters, the suppressed flag."""

    modes: tuple[str, ...] = ("off",)
    name = "gate"

    def __init__(self, mode: str) -> None:
        _check_mode(self.name, mode, self.modes)
        self.mode = mode
        self._suppressed = False
        self.suppressed_bars = 0
        self.episodes = 0

    @property
    def enabled(self) -> bool:
        return self.mode != "off"

    @property
    def suppressed(self) -> bool:
        return self.enabled and self._suppressed

    @property
    def history_sessions(self) -> int:
        return 2

    def observe(self, context: MarketContext) -> None:
        if not self.enabled:
            return
        was = self._suppressed
        self._step(context)
        if self._suppressed and not was:
            self.episodes += 1
        if self._suppressed:
            self.suppressed_bars += 1

    def _step(self, context: MarketContext) -> None:  # pragma: no cover - abstract
        raise NotImplementedError


class _DailyGate(_Gate):
    """A gate re-evaluated once a session from completed daily bars; its
    decision holds for the whole next session."""

    keep = 2

    def __init__(self, mode: str) -> None:
        super().__init__(mode)
        self.book = SessionBook(self.keep)

    @property
    def history_sessions(self) -> int:
        return self.keep + 2

    def _step(self, context: MarketContext) -> None:
        if self.book.push(context):
            self._suppressed = bool(self._evaluate())

    def _evaluate(self) -> bool:  # pragma: no cover - abstract
        raise NotImplementedError


# ---------------------------------------------------------------- RK14


class FiftyTwoWeekHighGate(_DailyGate):
    """RK14, George & Hwang (2004): stocks near their 52-week high keep
    rising, those far below it lag. Long-only and single-symbol, the usable
    half is "do not add exposure while the fund is far below its high":
    blocked while last close / highest high of the last `window` completed
    sessions < `threshold`."""

    modes = ("off", "near_high")
    name = "high52_gate"

    def __init__(self, mode: str = "off", *, window: int = 252, threshold: float = 0.8) -> None:
        self.keep = as_count("high52_window", window, minimum=2)
        super().__init__(mode)
        if not 0 < threshold <= 1:
            raise ConfigurationError(f"high52_threshold must be in (0, 1], got {threshold}")
        self.threshold = float(threshold)
        self.ratio: float | None = None

    def _evaluate(self) -> bool:
        if len(self.book.closes) < self.keep:
            return False
        self.ratio = self.book.closes[-1] / max(self.book.highs)
        return self.ratio < self.threshold


# ---------------------------------------------------------------- RK55


class AdxTrendGate(_DailyGate):
    """RK55, Wilder's ADX filter: a trend is tradeable when ADX is high.
    Long-only, the gate blocks buys in a strong DOWNtrend: ADX(period) >=
    `threshold` and -DI > +DI on completed daily bars (Wilder smoothing)."""

    modes = ("off", "strong_downtrend")
    name = "adx_gate"

    def __init__(self, mode: str = "off", *, period: int = 14, threshold: float = 25.0) -> None:
        self.keep = 2
        super().__init__(mode)
        self.period = as_count("adx_period", period, minimum=2)
        self.threshold = _positive("adx_threshold", threshold)
        self._tr = self._pdm = self._ndm = None
        self._dx_seed: list[float] = []
        self._seed: list[tuple[float, float, float]] = []
        self.adx: float | None = None
        self.plus_di: float | None = None
        self.minus_di: float | None = None

    @property
    def history_sessions(self) -> int:
        return 3 * self.period + 5

    def _evaluate(self) -> bool:
        b = self.book
        if len(b.closes) < 2:
            return False
        h, lo, pc = b.highs[-1], b.lows[-1], b.closes[-2]
        ph, pl = b.highs[-2], b.lows[-2]
        tr = max(h - lo, abs(h - pc), abs(lo - pc))
        up, down = h - ph, pl - lo
        pdm = up if up > down and up > 0 else 0.0
        ndm = down if down > up and down > 0 else 0.0
        n = self.period
        if self._tr is None:
            self._seed.append((tr, pdm, ndm))
            if len(self._seed) < n:
                return False
            self._tr = sum(s[0] for s in self._seed)
            self._pdm = sum(s[1] for s in self._seed)
            self._ndm = sum(s[2] for s in self._seed)
        else:
            self._tr = self._tr - self._tr / n + tr
            self._pdm = self._pdm - self._pdm / n + pdm
            self._ndm = self._ndm - self._ndm / n + ndm
        if self._tr <= 0:
            return False
        self.plus_di = 100.0 * self._pdm / self._tr
        self.minus_di = 100.0 * self._ndm / self._tr
        total = self.plus_di + self.minus_di
        dx = 0.0 if total <= 0 else 100.0 * abs(self.plus_di - self.minus_di) / total
        if self.adx is None:
            self._dx_seed.append(dx)
            if len(self._dx_seed) < n:
                return False
            self.adx = sum(self._dx_seed) / n
        else:
            self.adx = (self.adx * (n - 1) + dx) / n
        return self.adx >= self.threshold and self.minus_di > self.plus_di


# ---------------------------------------------------------------- RK64


def _parse_spans(name: str, text) -> tuple[int, ...]:
    if isinstance(text, (list, tuple)):
        parts = list(text)
    else:
        parts = [p for p in str(text).replace(" ", "").split(",") if p]
    spans = tuple(as_count(name, float(p), minimum=2) for p in parts)
    if len(spans) < 2 or list(spans) != sorted(set(spans)):
        raise ConfigurationError(f"{name} needs two or more increasing spans, got {text!r}")
    return spans


class _Ema:
    def __init__(self, span: int) -> None:
        self.alpha = 2.0 / (span + 1.0)
        self.value: float | None = None

    def update(self, x: float) -> float:
        self.value = x if self.value is None else self.value + self.alpha * (x - self.value)
        return self.value


class _Tema:
    """Mulloy's triple EMA: 3*e1 - 3*e2 + e3."""

    def __init__(self, span: int) -> None:
        self.e1, self.e2, self.e3 = _Ema(span), _Ema(span), _Ema(span)
        self.value: float | None = None

    def update(self, x: float) -> float:
        a = self.e1.update(x)
        b = self.e2.update(a)
        c = self.e3.update(b)
        self.value = 3 * a - 3 * b + c
        return self.value


class RibbonGate(_DailyGate):
    """RK64, the moving-average ribbon: averages of increasing spans on
    daily closes, blocked while the ribbon is fully bearish (each shorter
    average below the next longer one). `ribbon_ma` picks EMA or Mulloy's
    TEMA. Warm-up is the longest span."""

    modes = ("off", "bearish")
    name = "ribbon_gate"

    def __init__(self, mode: str = "off", *, spans="10,20,50,100", ma: str = "ema") -> None:
        self.keep = 2
        super().__init__(mode)
        _check_mode("ribbon_ma", ma, ("ema", "tema"))
        self.spans = _parse_spans("ribbon_spans", spans)
        kind = _Ema if ma == "ema" else _Tema
        self._mas = [kind(s) for s in self.spans]
        self._seen = 0

    @property
    def history_sessions(self) -> int:
        return 3 * max(self.spans) + 2

    def _evaluate(self) -> bool:
        close = self.book.closes[-1]
        values = [m.update(close) for m in self._mas]
        self._seen += 1
        if self._seen < max(self.spans):
            return False
        return all(a < b for a, b in pairwise(values))


# ---------------------------------------------------------------- RK79


class GapGate(_Gate):
    """RK79, opening-gap continuation (Gao et al. 2018; Plastun et al.
    2020): a large gap tends to continue intraday. Long-only, the gate
    blocks buys on a session that opened more than `threshold` below the
    previous close, until the gap fills (a completed bar trades back to
    the previous close; release="fill") or for the whole session
    (release="session")."""

    modes = ("off", "gap_down")
    name = "gap_gate"

    def __init__(
        self, mode: str = "off", *, threshold: float = 0.01, release: str = "fill"
    ) -> None:
        super().__init__(mode)
        _check_mode("gap_release", release, ("fill", "session"))
        self.threshold = _positive("gap_threshold", threshold)
        self.release = release
        self._day: int | None = None
        self._last_close: float | None = None
        self._prev_close: float | None = None
        self._pending: tuple[float, float] | None = None
        self.gap: float | None = None

    def _step(self, context: MarketContext) -> None:
        if _minute(context) is None:
            return
        if self._pending is not None:
            high, close = self._pending
            self._pending = None
            self._last_close = close
            if (
                self._suppressed
                and self.release == "fill"
                and self._prev_close is not None
                and high >= self._prev_close
            ):
                self._suppressed = False
        day = context.timestamp.toordinal()
        if day != self._day:
            self._day = day
            self._prev_close = self._last_close
            self.gap = None
            self._suppressed = False
            if self._prev_close:
                self.gap = context.open / self._prev_close - 1.0
                self._suppressed = self.gap < -self.threshold
        self._pending = (context.high, context.close)


# ---------------------------------------------------------------- RK112


class KamaTrendGate(_DailyGate):
    """RK112, Kaufman's adaptive moving average on daily closes: blocked
    while the last close is below KAMA and KAMA is falling."""

    modes = ("off", "below_falling")
    name = "kama_gate"

    def __init__(
        self, mode: str = "off", *, period: int = 10, fast: int = 2, slow: int = 30
    ) -> None:
        self.period = as_count("kama_period", period, minimum=2)
        self.keep = self.period + 1
        super().__init__(mode)
        self.fast = as_count("kama_fast", fast)
        self.slow = as_count("kama_slow", slow)
        if self.fast >= self.slow:
            raise ConfigurationError("kama_fast must be < kama_slow")
        self.kama: float | None = None
        self._prev_kama: float | None = None

    @property
    def history_sessions(self) -> int:
        return self.period + 3 * self.slow + 2

    def _evaluate(self) -> bool:
        closes = self.book.closes
        if len(closes) < self.keep:
            return False
        change = abs(closes[-1] - closes[0])
        noise = sum(abs(b - a) for a, b in pairwise(closes))
        er = 0.0 if noise <= 0 else change / noise
        fast_sc, slow_sc = 2.0 / (self.fast + 1), 2.0 / (self.slow + 1)
        sc = (er * (fast_sc - slow_sc) + slow_sc) ** 2
        self._prev_kama = self.kama
        self.kama = closes[-1] if self.kama is None else self.kama + sc * (closes[-1] - self.kama)
        if self._prev_kama is None:
            return False
        return closes[-1] < self.kama and self.kama < self._prev_kama


# ---------------------------------------------------------------- RK147 / RK161


class BandReversionGate(_Gate):
    """Mean reversion around a rolling mean on N-minute candles -- a
    PERMISSION gate: buys are allowed only on a stretch below the mean.

      z = (close - mean) / sd over the last `window` candle closes

    mode "oversold"    (RK147, moving-average z-score reversion): allowed
                       only while the last completed candle has z <= -k.
    mode "lower_band"  (RK161, Bollinger band reversion): allowed from a
                       candle closing below the lower band (z <= -k) until a
                       candle closes back at or above the middle band.
    """

    modes = ("off", "oversold", "lower_band")
    name = "band_gate"

    def __init__(
        self,
        mode: str = "off",
        *,
        name: str = "band_gate",
        modes: tuple[str, ...] = ("off", "oversold", "lower_band"),
        candle_minutes: int = 30,
        window: int = 20,
        k: float = 2.0,
    ) -> None:
        self.name = name
        self.modes = tuple(modes)
        super().__init__(mode)
        self.window = as_count(f"{name}_window", window, minimum=2)
        self.k = _positive(f"{name}_k", k)
        self._stream = CandleStream(candle_minutes)
        self._closes: deque[float] = deque(maxlen=self.window)
        self._open = False
        self._suppressed = True
        self.z: float | None = None
        self._candle_minutes = int(candle_minutes)

    @property
    def history_sessions(self) -> int:
        return math.ceil(self.window * self._candle_minutes / SESSION_MINUTES) + 2

    def _step(self, context: MarketContext) -> None:
        candle = self._stream.push(context)
        if candle is not None:
            self._closes.append(candle.close)
            if len(self._closes) == self.window:
                arr = np.fromiter(self._closes, float)
                sd = float(arr.std())
                self.z = None if sd <= 0 else (candle.close - float(arr.mean())) / sd
                if self.z is not None:
                    if self.mode == "oversold":
                        self._open = self.z <= -self.k
                    elif self.z <= -self.k:
                        self._open = True
                    elif self.z >= 0:
                        self._open = False
        self._suppressed = not self._open


# ---------------------------------------------------------------- RK168


def load_term_structure(path) -> dict[date, float]:
    """VIX / VIX3M by date from a CSV with columns date, vix, vix3m."""
    out: dict[date, float] = {}
    with Path(path).open(encoding="utf-8", newline="") as fh:
        for row in csv.DictReader(fh):
            try:
                day = datetime.fromisoformat(row["date"].strip()[:10]).date()
                vix, vix3m = float(row["vix"]), float(row["vix3m"])
            except (KeyError, ValueError) as exc:
                raise ConfigurationError(f"bad term-structure row in {path}: {row}") from exc
            if vix3m > 0:
                out[day] = vix / vix3m
    if not out:
        raise ConfigurationError(f"no term-structure rows in {path}")
    return out


class TermStructureGate(_Gate):
    """RK168, the VIX futures curve as a regime input (trading VIX futures
    is out of scope): blocked on a session whose PREVIOUS trading day had
    VIX / VIX3M (averaged over `smooth` days) at or above `threshold` --
    backwardation, the curve's stress shape. Reads a daily CSV (date, vix,
    vix3m) the operator keeps current; a session with no prior row is not
    blocked (no reading is not a stressed one)."""

    modes = ("off", "backwardation")
    name = "term_gate"

    def __init__(
        self, mode: str = "off", *, path: str = "", threshold: float = 1.0, smooth: int = 1
    ) -> None:
        super().__init__(mode)
        self.threshold = _positive("term_threshold", threshold)
        self.smooth = as_count("term_smooth", smooth)
        self._series: list[tuple[date, float]] = []
        if self.enabled:
            if not path:
                raise ConfigurationError("term_gate needs term_path (a CSV of date, vix, vix3m)")
            self._series = sorted(load_term_structure(path).items())
        self._dates = [d for d, _ in self._series]
        self._day: int | None = None
        self.ratio: float | None = None

    def ratio_before(self, day: date) -> float | None:
        """Smoothed ratio over the `smooth` rows strictly before `day`."""
        i = bisect.bisect_left(self._dates, day)
        if i < self.smooth:
            return None
        return sum(r for _, r in self._series[i - self.smooth : i]) / self.smooth

    def _step(self, context: MarketContext) -> None:
        day = context.timestamp.toordinal()
        if day != self._day:
            self._day = day
            self.ratio = self.ratio_before(context.timestamp.date())
            self._suppressed = self.ratio is not None and self.ratio >= self.threshold


# ---------------------------------------------------------------- RK208


class AnchoredVwapGate(_Gate):
    """RK208, anchored VWAP: the volume-weighted average price from an
    event, here the session holding the highest high (swing_high) or lowest
    low (swing_low) of the last `sessions` completed sessions. Blocked while
    the last completed bar closed below that anchored VWAP -- for
    swing_high, price has not reclaimed the average cost of everyone who
    bought since the top; for swing_low, it has been rejected below the
    average cost since the bottom. Typical price (h+l+c)/3 per bar."""

    modes = ("off", "swing_high", "swing_low")
    name = "avwap_gate"

    def __init__(self, mode: str = "off", *, sessions: int = 20) -> None:
        super().__init__(mode)
        self.sessions = as_count("avwap_sessions", sessions)
        self._done: deque[tuple[float, float, float, float]] = deque(maxlen=self.sessions)
        self._day: int | None = None
        self._pv = self._v = 0.0
        self._high = -math.inf
        self._low = math.inf
        self._pending: tuple[float, float, float, float] | None = None
        self.vwap: float | None = None

    @property
    def history_sessions(self) -> int:
        return self.sessions + 2

    def _step(self, context: MarketContext) -> None:
        if _minute(context) is None:
            return
        last_close = None
        if self._pending is not None:
            h, lo, c, v = self._pending
            self._pending = None
            if v > 0:
                self._pv += (h + lo + c) / 3.0 * v
                self._v += v
            self._high, self._low = max(self._high, h), min(self._low, lo)
            last_close = c
        day = context.timestamp.toordinal()
        if day != self._day:
            if self._day is not None and self._v > 0:
                self._done.append((self._high, self._low, self._pv, self._v))
            self._day = day
            self._pv = self._v = 0.0
            self._high, self._low = -math.inf, math.inf
        self.vwap = self._anchored_vwap()
        if last_close is not None and self.vwap is not None:
            self._suppressed = last_close < self.vwap
        self._pending = (context.high, context.low, context.close, float(context.volume))

    def _anchored_vwap(self) -> float | None:
        if not self._done:
            return None
        sessions = list(self._done)
        key = (lambda s: s[0]) if self.mode == "swing_high" else (lambda s: -s[1])
        anchor = max(range(len(sessions)), key=lambda i: key(sessions[i]))
        pv = sum(s[2] for s in sessions[anchor:]) + self._pv
        v = sum(s[3] for s in sessions[anchor:]) + self._v
        return None if v <= 0 else pv / v


# ---------------------------------------------------------------- RK243


class AnomalyGate(_Gate):
    """RK243, price/volume anomaly detection: an exponentially weighted
    mean and standard deviation of one-bar log returns (and of volume),
    both through the bar before, flag a bar whose return z-score is below
    -z ("price"), or whose volume z-score is above z on a down bar
    ("price_volume" flags either). A flagged bar blocks buys for the next
    `hold_bars` bars: no adding into a move the recent past cannot
    explain."""

    modes = ("off", "price", "price_volume")
    name = "anomaly_gate"

    def __init__(
        self, mode: str = "off", *, span: int = 60, z: float = 4.0, hold_bars: int = 30
    ) -> None:
        super().__init__(mode)
        self.span = as_count("anomaly_span", span, minimum=2)
        self.z = _positive("anomaly_z", z)
        self.hold_bars = as_count("anomaly_hold_bars", hold_bars)
        self._alpha = 2.0 / (self.span + 1.0)
        self._r_mean = self._r_var = self._v_mean = self._v_var = None
        self._n = 0
        self._prev_close: float | None = None
        self._pending: tuple[float, float] | None = None
        self._hold = 0

    def _ew(self, mean, var, x):
        if mean is None:
            return x, 0.0
        d = x - mean
        mean = mean + self._alpha * d
        var = (1 - self._alpha) * (var + self._alpha * d * d)
        return mean, var

    def _step(self, context: MarketContext) -> None:
        if self._pending is not None:
            close, volume = self._pending
            self._pending = None
            if self._hold > 0:
                self._hold -= 1
            if self._prev_close and close > 0:
                r = math.log(close / self._prev_close)
                if self._n >= self.span:
                    flagged = False
                    if self._r_var and self._r_var > 0:
                        flagged = (r - self._r_mean) / math.sqrt(self._r_var) < -self.z
                    if (
                        not flagged
                        and self.mode == "price_volume"
                        and r < 0
                        and self._v_var
                        and self._v_var > 0
                    ):
                        flagged = (volume - self._v_mean) / math.sqrt(self._v_var) > self.z
                    if flagged:
                        self._hold = self.hold_bars
                self._r_mean, self._r_var = self._ew(self._r_mean, self._r_var, r)
                self._v_mean, self._v_var = self._ew(self._v_mean, self._v_var, volume)
                self._n += 1
            self._prev_close = close
        self._suppressed = self._hold > 0
        self._pending = (context.close, float(context.volume))


# ---------------------------------------------------------------- RK253


class VolumeImbalanceGate(_Gate):
    """RK253, information-driven bars (López de Prado): minute bars are
    re-sampled into volume bars of 1/`bars_per_session` of the trailing
    average session volume; each minute's volume is signed by the tick
    rule. Over the last `window` volume bars, imbalance = signed volume /
    volume. Blocked while imbalance <= -threshold: selling pressure that
    has persisted in volume time, the momentum the volume clock is built
    to expose."""

    modes = ("off", "sell_imbalance")
    name = "imbalance_gate"

    def __init__(
        self,
        mode: str = "off",
        *,
        bars_per_session: int = 50,
        window: int = 20,
        threshold: float = 0.3,
        sessions: int = 5,
    ) -> None:
        super().__init__(mode)
        self.bars_per_session = as_count("imbalance_bars_per_session", bars_per_session)
        self.window = as_count("imbalance_window", window)
        if not 0 < threshold <= 1:
            raise ConfigurationError(f"imbalance_threshold must be in (0, 1], got {threshold}")
        self.threshold = float(threshold)
        self.sessions = as_count("imbalance_sessions", sessions)
        self._session_volumes: deque[float] = deque(maxlen=self.sessions)
        self._day: int | None = None
        self._day_volume = 0.0
        self._bars: deque[tuple[float, float]] = deque(maxlen=self.window)
        self._signed = self._total = 0.0
        self._prev_close: float | None = None
        self._last_sign = 1.0
        self._pending: tuple[int, float, float] | None = None
        self.imbalance: float | None = None

    @property
    def history_sessions(self) -> int:
        return self.sessions + 2

    def _step(self, context: MarketContext) -> None:
        if _minute(context) is None:
            return
        if self._pending is not None:
            day, close, volume = self._pending
            self._pending = None
            if self._prev_close is not None and close != self._prev_close:
                self._last_sign = 1.0 if close > self._prev_close else -1.0
            self._prev_close = close
            self._day_volume += volume
            if self._session_volumes:
                size = (sum(self._session_volumes) / len(self._session_volumes)) / (
                    self.bars_per_session
                )
                self._signed += self._last_sign * volume
                self._total += volume
                if size > 0 and self._total >= size:
                    self._bars.append((self._signed, self._total))
                    self._signed = self._total = 0.0
                    if len(self._bars) == self.window:
                        total = sum(b[1] for b in self._bars)
                        self.imbalance = sum(b[0] for b in self._bars) / total if total else None
        day = context.timestamp.toordinal()
        if day != self._day:
            if self._day is not None and self._day_volume > 0:
                self._session_volumes.append(self._day_volume)
            self._day, self._day_volume = day, 0.0
        self._suppressed = self.imbalance is not None and self.imbalance <= -self.threshold
        self._pending = (day, context.close, float(context.volume))


# ---------------------------------------------------------------- RK294


def _barrier_features(closes: np.ndarray, i: int) -> np.ndarray | None:
    """Features at completed session i from closes[: i + 1] only."""
    if i < 20:
        return None
    c = closes
    rets = np.diff(np.log(c[i - 20 : i + 1]))
    window = c[i - 19 : i + 1]
    sd = float(window.std())
    return np.array(
        [
            math.log(c[i] / c[i - 1]),
            math.log(c[i] / c[i - 5]),
            math.log(c[i] / c[i - 20]),
            float(rets.std()),
            0.0 if sd <= 0 else (c[i] - float(window.mean())) / sd,
        ]
    )


def _fit_logistic(x: np.ndarray, y: np.ndarray, l2: float = 1.0, iters: int = 25) -> np.ndarray:
    """L2-penalised logistic regression by Newton's method; x has a bias
    column already."""
    w = np.zeros(x.shape[1])
    reg = l2 * np.eye(x.shape[1])
    reg[0, 0] = 0.0
    for _ in range(iters):
        p = 1.0 / (1.0 + np.exp(-np.clip(x @ w, -30, 30)))
        grad = x.T @ (p - y) + reg @ w
        hess = (x * (p * (1 - p))[:, None]).T @ x + reg + 1e-9 * np.eye(x.shape[1])
        step = np.linalg.solve(hess, grad)
        w -= step
        if float(np.abs(step).max()) < 1e-8:
            break
    return w


class TripleBarrierGate(_Gate):
    """RK294, a triple-barrier-labelled classifier (López de Prado 2018).

    Each completed session i is labelled once its outcome is known: 1 if
    the daily high reaches close_i * (1 + profit) before the daily low
    reaches close_i * (1 - loss) within `horizon` sessions, 0 if the loss
    barrier comes first (or both on the same day), and at the vertical
    barrier the sign of the horizon return. A logistic regression on five
    features of the closes up to i (1/5/20-day log returns, 20-day
    volatility, 20-day z-score) is refitted every `retrain` sessions on
    every label known so far -- walk-forward, so no label it trains on
    reaches past the session being predicted. Blocked on a session whose
    predicted probability of the profit barrier is below `threshold`;
    inactive until `min_samples` labels exist."""

    modes = ("off", "classifier")
    name = "barrier_gate"

    def __init__(
        self,
        mode: str = "off",
        *,
        horizon: int = 10,
        profit: float = 0.05,
        loss: float = 0.05,
        min_samples: int = 250,
        threshold: float = 0.5,
        retrain: int = 20,
    ) -> None:
        super().__init__(mode)
        self.horizon = as_count("barrier_horizon", horizon)
        self.profit = _positive("barrier_profit", profit)
        self.loss = _positive("barrier_loss", loss)
        self.min_samples = as_count("barrier_min_samples", min_samples, minimum=20)
        if not 0 < threshold < 1:
            raise ConfigurationError(f"barrier_threshold must be in (0, 1), got {threshold}")
        self.threshold = float(threshold)
        self.retrain = as_count("barrier_retrain", retrain)
        self.book = SessionBook(10**6)
        self._labels: dict[int, int] = {}
        self._next_unlabelled = 0
        self._weights: np.ndarray | None = None
        self._scale: tuple[np.ndarray, np.ndarray] | None = None
        self._since_fit = 0
        self.probability: float | None = None

    @property
    def history_sessions(self) -> int:
        return self.min_samples + self.horizon + 25

    def _label_ready(self) -> None:
        b = self.book
        closes, highs, lows = b.closes, b.highs, b.lows
        n = len(closes)
        while self._next_unlabelled < n:
            i = self._next_unlabelled
            up, dn = closes[i] * (1 + self.profit), closes[i] * (1 - self.loss)
            label = None
            for j in range(i + 1, min(n, i + self.horizon + 1)):
                if lows[j] <= dn:
                    label = 0
                    break
                if highs[j] >= up:
                    label = 1
                    break
            if label is None:
                if n - 1 < i + self.horizon:
                    return  # outcome not yet known
                label = 1 if closes[i + self.horizon] > closes[i] else 0
            self._labels[i] = label
            self._next_unlabelled += 1

    def _step(self, context: MarketContext) -> None:
        if not self.book.push(context):
            return
        self._label_ready()
        closes = np.fromiter(self.book.closes, float)
        last = len(closes) - 1
        xs, ys = [], []
        if self._weights is None or self._since_fit >= self.retrain:
            for i, y in self._labels.items():
                f = _barrier_features(closes, i)
                if f is not None:
                    xs.append(f)
                    ys.append(y)
            if len(ys) >= self.min_samples and 0 < sum(ys) < len(ys):
                x = np.asarray(xs)
                mu, sd = x.mean(axis=0), x.std(axis=0) + 1e-12
                design = np.column_stack([np.ones(len(x)), (x - mu) / sd])
                self._weights = _fit_logistic(design, np.asarray(ys, float))
                self._scale = (mu, sd)
                self._since_fit = 0
        self._since_fit += 1
        f = _barrier_features(closes, last)
        if self._weights is None or f is None:
            self.probability = None
            self._suppressed = False
            return
        mu, sd = self._scale
        z = float(np.concatenate([[1.0], (f - mu) / sd]) @ self._weights)
        self.probability = 1.0 / (1.0 + math.exp(-max(-30.0, min(30.0, z))))
        self._suppressed = self.probability < self.threshold


# ---------------------------------------------------------------- RK297


class HurstBandGate(_Gate):
    """RK297, Hurst-adaptive mean-reversion bands: on N-minute candles,
    the Hurst exponent H of the last `window` closes (the lagged-difference
    estimator of mean_reversion.hurst_exponent) scales the band width,
    k_eff = k * clip(H / 0.5, 0.5, 2.0): narrower when the series is
    mean-reverting (H < 0.5), wider when it trends. A permission gate like
    BandReversionGate("lower_band"): buys open on a close below mean -
    k_eff * sd and close back at the mean. While H > `trend_cutoff` the
    series is trending and no reversion buy is allowed at all."""

    modes = ("off", "adaptive_band")
    name = "hurst_gate"

    def __init__(
        self,
        mode: str = "off",
        *,
        candle_minutes: int = 30,
        window: int = 100,
        max_lag: int = 20,
        k: float = 2.0,
        trend_cutoff: float = 0.65,
    ) -> None:
        super().__init__(mode)
        self.window = as_count("hurst_window", window, minimum=10)
        self.max_lag = as_count("hurst_max_lag", max_lag, minimum=4)
        if self.max_lag >= self.window:
            raise ConfigurationError("hurst_max_lag must be < hurst_window")
        self.k = _positive("hurst_k", k)
        self.trend_cutoff = _positive("hurst_trend_cutoff", trend_cutoff)
        self._stream = CandleStream(candle_minutes)
        self._candle_minutes = int(candle_minutes)
        self._closes: deque[float] = deque(maxlen=self.window)
        self._open = False
        self._suppressed = True
        self.hurst: float | None = None

    @property
    def history_sessions(self) -> int:
        return math.ceil(self.window * self._candle_minutes / SESSION_MINUTES) + 2

    def _step(self, context: MarketContext) -> None:
        candle = self._stream.push(context)
        if candle is not None:
            self._closes.append(candle.close)
            if len(self._closes) == self.window:
                arr = np.fromiter(self._closes, float)
                self.hurst = hurst_exponent(np.log(arr), max_lag=self.max_lag)
                mean, sd = float(arr.mean()), float(arr.std())
                k_eff = self.k * min(2.0, max(0.5, self.hurst / 0.5))
                if self.hurst > self.trend_cutoff:
                    self._open = False
                elif sd > 0 and candle.close <= mean - k_eff * sd:
                    self._open = True
                elif candle.close >= mean:
                    self._open = False
        self._suppressed = not self._open


__all__ = [
    "AdxTrendGate",
    "AnchoredVwapGate",
    "AnomalyGate",
    "BandReversionGate",
    "FiftyTwoWeekHighGate",
    "GapGate",
    "HurstBandGate",
    "KamaTrendGate",
    "RibbonGate",
    "SessionBook",
    "TermStructureGate",
    "TripleBarrierGate",
    "VolumeImbalanceGate",
    "load_term_structure",
]
