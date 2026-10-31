"""
The ranked list's single-symbol algorithms as components of the champion
grid, one per algorithm, each selectable as its own strategy id
(research/strategies/library_sizing.py, `rkNNN_<name>` in the registry).

A component is one of three kinds:

  gate   pauses new buys while `suppressed` (the entry_gates.py interface);
  sizer  scales each new lot by `multiplier` (>= 0);
  level  moves the grid's buy level, never above the champion's own.

None of them sells: open lots still exit only at their targets through the
no-loss guard, so no component can realise a loss.

CAUSALITY. Daily components read completed sessions only (signal_gates.
SessionBook); intraday ones hold each bar back until the next arrives. Any
external daily series (a leader, breadth, sentiment, events) is read for
dates strictly before the session being traded.

SIGNALS maps each component name to its class, the parameters fixed by the
algorithm, and its ledger ID; `build_signal(name, "k=v,k=v")` constructs one.
UNMEASURED: none of these has been run on real data.
"""

from __future__ import annotations

import bisect
import csv
import inspect
import math
from collections import deque
from dataclasses import dataclass, field
from datetime import date, datetime
from pathlib import Path

import numpy as np

from engine.core.exceptions import ConfigurationError
from engine.core.market_context import MarketContext
from research.strategies import signal_gates as sg
from research.strategies.entry_gates import BreakdownGate, as_count
from research.strategies.intraday_gates import VwapGate
from research.strategies.mean_reversion import hurst_exponent, variance_ratio
from research.strategies.position_sizing import split_conformal_interval

SESSION_MINUTES = 390


def _minute(context: MarketContext) -> int | None:
    m = context.time_of_day_flag
    return m if m >= 0 else None


def _pos(name: str, value) -> float:
    value = float(value)
    if not value > 0:
        raise ConfigurationError(f"{name} must be > 0, got {value}")
    return value


def _ints(name: str, text) -> tuple[int, ...]:
    parts = [p for p in str(text).replace(" ", "").split(",") if p]
    values = tuple(as_count(name, float(p)) for p in parts)
    if not values:
        raise ConfigurationError(f"{name} needs at least one integer, got {text!r}")
    return values


def load_daily_series(path, columns: tuple[str, ...]) -> list[tuple[date, tuple[float, ...]]]:
    """Rows of a CSV with a `date` column and the named numeric columns,
    sorted by date."""
    if not path:
        raise ConfigurationError(
            f"this signal reads a CSV with columns date, {', '.join(columns)}: give its path "
            "in signal_params (e.g. path=data/leader.csv)"
        )
    rows = []
    with Path(path).open(encoding="utf-8", newline="") as fh:
        for row in csv.DictReader(fh):
            try:
                day = datetime.fromisoformat(row["date"].strip()[:10]).date()
                rows.append((day, tuple(float(row[c]) for c in columns)))
            except (KeyError, ValueError) as exc:
                raise ConfigurationError(f"bad row in {path}: {row}") from exc
    if not rows:
        raise ConfigurationError(f"no rows in {path}")
    return sorted(rows)


class _Series:
    """A daily external series read strictly before a date."""

    def __init__(self, path, columns: tuple[str, ...]) -> None:
        self.rows = load_daily_series(path, columns)
        self.dates = [d for d, _ in self.rows]

    def before(self, day: date, n: int = 1) -> list[tuple[date, tuple[float, ...]]]:
        i = bisect.bisect_left(self.dates, day)
        return self.rows[max(0, i - n) : i]


# ---------------------------------------------------------------- component bases


class Component:
    """Shared bookkeeping. `kind` is gate, sizer or level."""

    kind = "gate"

    def __init__(self) -> None:
        self.mode = "on"
        self._suppressed = False
        self.multiplier = 1.0
        self.suppressed_bars = 0
        self.episodes = 0

    @property
    def enabled(self) -> bool:
        return True

    @property
    def suppressed(self) -> bool:
        return self.kind == "gate" and bool(self._suppressed)

    @property
    def history_sessions(self) -> int:
        return 2

    def observe(self, context: MarketContext) -> None:
        was = self._suppressed
        self._step(context)
        if self._suppressed and not was:
            self.episodes += 1
        if self._suppressed:
            self.suppressed_bars += 1

    def _step(self, context: MarketContext) -> None:  # pragma: no cover
        raise NotImplementedError

    def adjust_level(self, level: float, context: MarketContext, step: float) -> float:
        return level


class DailyComponent(Component):
    """Re-evaluated once per completed session from `self.book`; the result
    holds for the whole next session."""

    def __init__(self, keep: int) -> None:
        super().__init__()
        self.book = sg.SessionBook(keep)
        self._keep = keep

    @property
    def history_sessions(self) -> int:
        return self._keep + 2

    def closes(self) -> np.ndarray:
        return np.fromiter(self.book.closes, float)

    def returns(self) -> np.ndarray:
        c = self.closes()
        return np.diff(np.log(c)) if len(c) > 1 else np.zeros(0)

    def _step(self, context: MarketContext) -> None:
        if self.book.push(context):
            self._session(context)

    def _session(self, context: MarketContext) -> None:  # pragma: no cover
        raise NotImplementedError


# ---------------------------------------------------------------- trend and regime gates


class SupertrendGate(DailyComponent):
    """RK44: Supertrend on completed daily bars (ATR bands that ratchet,
    flipping when the close crosses the active band). Blocked while the trend
    is down; the long-or-cash reading of the stop-and-reverse rule."""

    def __init__(self, n: int = 10, mult: float = 3.0) -> None:
        self.n = as_count("n", n, minimum=2)
        super().__init__(max(6 * self.n, 60))
        self.mult = _pos("mult", mult)

    def _session(self, context):
        from research.catalog.technical_ml import supertrend

        b = self.book
        if len(b.closes) < 2 * self.n + 2:
            return
        out = supertrend(list(b.highs), list(b.lows), list(b.closes), self.n, self.mult)
        self._suppressed = out["trend"][-1] < 0


class MovingAverageCrossGate(DailyComponent):
    """RK62: dual moving-average crossover as a regime, blocked while the
    `fast`-session simple average of daily closes is below the `slow` one."""

    def __init__(self, fast: int = 50, slow: int = 200) -> None:
        self.fast, self.slow = as_count("fast", fast), as_count("slow", slow)
        if self.fast >= self.slow:
            raise ConfigurationError("fast must be < slow")
        super().__init__(self.slow)

    def _session(self, context):
        c = self.closes()
        if len(c) >= self.slow:
            self._suppressed = c[-self.fast :].mean() < c.mean()


class MultiTimeframeTrendGate(DailyComponent):
    """RK78: time-series momentum over several horizons; buys allowed only
    while every horizon's return is positive (Elder's triple screen read
    long-or-cash)."""

    def __init__(self, horizons: str = "21,63,252") -> None:
        self.horizons = _ints("horizons", horizons)
        super().__init__(max(self.horizons) + 1)

    def _session(self, context):
        c = self.closes()
        if len(c) > max(self.horizons):
            self._suppressed = not all(c[-1] > c[-1 - h] for h in self.horizons)


class HmmRegimeGate(DailyComponent):
    """RK102: a two-state Gaussian HMM on daily log returns, refitted every
    `refit` sessions on the last `window`; blocked while the filtered
    probability of the high-variance state exceeds `p` (Kritzman, Page &
    Turkington 2012's turbulent regime). RK106's hierarchical version adds a
    trend level: with `trend` > 0, the gate blocks only when the market is
    also below its close `trend` sessions ago."""

    def __init__(self, window: int = 500, refit: int = 20, p: float = 0.6, trend: int = 0) -> None:
        self.window = as_count("window", window, minimum=50)
        self.refit = as_count("refit", refit)
        self.trend = as_count("trend", trend, minimum=0)
        super().__init__(max(self.window, self.trend) + 1)
        if not 0 < p < 1:
            raise ConfigurationError(f"p must be in (0, 1), got {p}")
        self.p = float(p)
        self._model = None
        self._since = 0
        self.prob_high: float | None = None

    def _session(self, context):
        from research.strategies.regime_models import GaussianHMM

        r = self.returns()
        if len(r) < min(self.window, 100):
            return
        r = r[-self.window :]
        if self._model is None or self._since >= self.refit:
            try:
                self._model = GaussianHMM(n_states=2, n_iter=100).fit(r)
            except (ConfigurationError, ValueError, FloatingPointError):
                return
            self._since = 0
        self._since += 1
        probs = self._model.filter(r)
        high = int(np.argmax(self._model.var))
        self.prob_high = float(probs[-1, high])
        turbulent = self.prob_high > self.p
        if self.trend:
            c = self.closes()
            turbulent = turbulent and len(c) > self.trend and c[-1] < c[-1 - self.trend]
        self._suppressed = turbulent


class HurstRegimeGate(DailyComponent):
    """RK103: a grid buys reversion, which a trending tape punishes. On the
    last `window` daily log closes, trending means a Hurst exponent above
    `threshold` or a Lo-MacKinlay variance ratio VR(q) significantly above 1
    (z > 2); blocked while trending AND the close is below the window's mean
    (a downtrend)."""

    def __init__(self, window: int = 250, max_lag: int = 50, threshold: float = 0.6, q: int = 5):
        self.window = as_count("window", window, minimum=20)
        self.max_lag = as_count("max_lag", max_lag, minimum=4)
        if self.max_lag >= self.window:
            raise ConfigurationError("max_lag must be < window")
        self.q = as_count("q", q)
        super().__init__(self.window)
        self.threshold = _pos("threshold", threshold)
        self.hurst: float | None = None

    def _session(self, context):
        c = self.closes()
        if len(c) < self.window:
            return
        logc = np.log(c)
        self.hurst = hurst_exponent(logc, max_lag=self.max_lag)
        vr = variance_ratio(logc, self.q)
        trending = self.hurst > self.threshold or vr["z"] > 2.0
        self._suppressed = trending and c[-1] < c.mean()


class TrendScanGate(DailyComponent):
    """RK213, trend scanning (López de Prado) read causally: over each
    trailing span, the t-value of an OLS slope through the last daily
    closes; the span with the largest |t| labels the trend. Blocked while
    that best t-value is below -t_min."""

    def __init__(self, spans: str = "10,20,40", t_min: float = 2.0) -> None:
        self.spans = _ints("spans", spans)
        if min(self.spans) < 3:
            raise ConfigurationError("spans must be >= 3")
        super().__init__(max(self.spans))
        self.t_min = _pos("t_min", t_min)
        self.t_value: float | None = None

    def _session(self, context):
        from research.ml.barrier_labels import ols_slope_tvalue

        c = self.closes()
        if len(c) < max(self.spans):
            return
        best = max((ols_slope_tvalue(c[-s:]) for s in self.spans), key=abs)
        self.t_value = best
        self._suppressed = best < -self.t_min


class FracDiffGate(DailyComponent):
    """RK300, fractional differentiation (López de Prado): the log closes
    differenced to order d with fixed-width weights keep memory yet are
    stationary, so their z-score over `window` sessions is a usable
    mean-reversion level. Buys allowed only while z <= `threshold`."""

    def __init__(self, d: float = 0.4, window: int = 120, threshold: float = 0.0) -> None:
        self.window = as_count("window", window, minimum=20)
        if not 0 < d < 1:
            raise ConfigurationError(f"d must be in (0, 1), got {d}")
        self.d = float(d)
        from research.ml.info_bars import ffd_weights

        self._w = ffd_weights(self.d, threshold=1e-3)[::-1]
        super().__init__(self.window + len(self._w))
        self.threshold = float(threshold)
        self._suppressed = True
        self.z: float | None = None

    def _session(self, context):
        logc = np.log(self.closes())
        width = len(self._w)
        if len(logc) < self.window + width:
            return
        series = np.array(
            [
                self._w @ logc[i - width + 1 : i + 1]
                for i in range(len(logc) - self.window, len(logc))
            ]
        )
        sd = series.std()
        self.z = 0.0 if sd <= 0 else float((series[-1] - series.mean()) / sd)
        self._suppressed = self.z > self.threshold


# ---------------------------------------------------------------- intraday gates


class OpeningRangeGate(Component):
    """RK110, opening range breakout (Zarattini & Aziz 2023), long side: no
    buys until a completed bar closes above the high of the first `minutes`
    of the session; then buys are allowed for the rest of it. mode
    "breakdown" is instead entry_gates.BreakdownGate's opening-range rule
    (no buys while below the range's low)."""

    def __init__(self, minutes: int = 30, mode: str = "breakout") -> None:
        super().__init__()
        self.minutes = as_count("minutes", minutes)
        if mode not in ("breakout", "breakdown"):
            raise ConfigurationError("mode must be breakout or breakdown")
        self.mode = mode
        self._breakdown = BreakdownGate("opening_range", orb_minutes=self.minutes)
        self._day = None
        self._high = -math.inf
        self._open = False
        self._pending: tuple[int, float, float] | None = None

    def _step(self, context):
        if self.mode == "breakdown":
            self._breakdown.observe(context)
            self._suppressed = self._breakdown.suppressed
            return
        minute = _minute(context)
        if minute is None:
            return
        day = context.timestamp.toordinal()
        if self._pending is not None:
            pmin, phigh, pclose = self._pending
            self._pending = None
            if pmin < self.minutes:
                self._high = max(self._high, phigh)
            elif pclose > self._high:
                self._open = True
        if day != self._day:
            self._day, self._high, self._open = day, -math.inf, False
        self._suppressed = not self._open
        self._pending = (minute, context.high, context.close)


class EmaPullbackGate(DailyComponent):
    """RK115, EMA pullback continuation: buy dips inside an uptrend only.
    Uptrend: the last daily close is above its `slow`-session EMA. Pullback:
    the previous bar closed at or below the `fast`-session EMA of daily
    closes. Buys allowed only when both hold."""

    def __init__(self, fast: int = 20, slow: int = 100) -> None:
        self.fast, self.slow = as_count("fast", fast), as_count("slow", slow)
        if self.fast >= self.slow:
            raise ConfigurationError("fast must be < slow")
        super().__init__(2)
        self._ef, self._es = sg._Ema(self.fast), sg._Ema(self.slow)
        self._n = 0
        self._uptrend = False
        self._prev_close: float | None = None
        self._suppressed = True

    @property
    def history_sessions(self) -> int:
        return 3 * self.slow

    def _step(self, context):
        if _minute(context) is None:
            return
        if self.book.push(context):
            c = self.book.closes[-1]
            self._ef.update(c)
            self._es.update(c)
            self._n += 1
            self._uptrend = self._n >= self.slow and c > self._es.value
        pullback = (
            self._prev_close is not None
            and self._ef.value is not None
            and self._prev_close <= self._ef.value
        )
        self._suppressed = not (self._uptrend and pullback)
        self._prev_close = context.close


class VwapReversionGate(Component):
    """RK150, VWAP reversion via intraday_gates.VwapGate: `far_falling` pauses
    buys more than far_k sigma below session VWAP while still falling;
    `band` also requires price within near_k sigma below VWAP."""

    def __init__(self, mode: str = "far_falling", far_k: float = 3.0, near_k: float = 1.0):
        super().__init__()
        self.gate = VwapGate(mode, far_k=far_k, near_k=near_k)
        self.mode = mode

    def _step(self, context):
        self.gate.observe(context)
        self._suppressed = self.gate.suppressed


class OvernightGate(Component):
    """RK154, the overnight anomaly (Cliff, Cooper & Gulen 2008; Lou, Polk &
    Skouras 2019): equity returns accrue overnight. Buys allowed only in the
    last `minutes` of the session, so new lots carry the overnight move."""

    def __init__(self, minutes: int = 30) -> None:
        super().__init__()
        self.minutes = as_count("minutes", minutes)
        if self.minutes >= SESSION_MINUTES:
            raise ConfigurationError("minutes must be < 390")

    def _step(self, context):
        minute = _minute(context)
        self._suppressed = minute is None or minute < SESSION_MINUTES - self.minutes


class VpinGate(Component):
    """RK247, VPIN (Easley, López de Prado & O'Hara 2012) on minute bars:
    volume buckets of 1/`buckets_per_session` of the trailing average session
    volume, bulk-classified by the bar's price change; blocked while VPIN over
    the last `n_buckets` is above its own `quantile` over the last
    `history` readings. Evidence is disputed (Andersen & Bondarenko 2014)."""

    def __init__(
        self,
        buckets_per_session: int = 50,
        n_buckets: int = 50,
        quantile: float = 0.9,
        history: int = 500,
    ) -> None:
        super().__init__()
        self.bps = as_count("buckets_per_session", buckets_per_session)
        self.n_buckets = as_count("n_buckets", n_buckets, minimum=5)
        if not 0 < quantile < 1:
            raise ConfigurationError("quantile must be in (0, 1)")
        self.quantile = float(quantile)
        self._session_vols: deque[float] = deque(maxlen=5)
        self._bars: deque[tuple[float, float]] = deque(maxlen=self.bps * 6)
        self._readings: deque[float] = deque(maxlen=as_count("history", history, minimum=20))
        self._day = None
        self._day_vol = 0.0
        self._prev_close: float | None = None
        self._pending = None
        self._since = 0
        self.vpin: float | None = None

    @property
    def history_sessions(self) -> int:
        return 8

    def _step(self, context):
        from research.strategies.microstructure import vpin

        if _minute(context) is None:
            return
        if self._pending is not None:
            close, volume = self._pending
            self._pending = None
            if self._prev_close is not None:
                self._bars.append((close - self._prev_close, volume))
            self._prev_close = close
            self._day_vol += volume
            self._since += 1
            if self._session_vols and self._since >= 15 and len(self._bars) > 30:
                self._since = 0
                bucket = (sum(self._session_vols) / len(self._session_vols)) / self.bps
                changes, vols = zip(*self._bars, strict=True)
                value = vpin(np.array(changes), np.array(vols), bucket, self.n_buckets)
                if value is not None:
                    self.vpin = float(value)
                    hist = np.fromiter(self._readings, float)
                    self._suppressed = len(hist) >= 20 and self.vpin > np.quantile(
                        hist, self.quantile
                    )
                    self._readings.append(self.vpin)
        day = context.timestamp.toordinal()
        if day != self._day:
            if self._day is not None and self._day_vol > 0:
                self._session_vols.append(self._day_vol)
            self._day, self._day_vol = day, 0.0
        self._pending = (context.close, float(context.volume))


# ---------------------------------------------------------------- topological and jump gates


def _embed(returns: np.ndarray, dim: int = 3) -> np.ndarray:
    """Takens delay embedding of one return series: rows (r_t, r_t-1, ...)."""
    n = len(returns) - dim + 1
    return np.column_stack([returns[dim - 1 - k : dim - 1 - k + n] for k in range(dim)])


class LandscapeGate(DailyComponent):
    """RK254 (mode "level") and RK255 (mode "variance"), Gidea & Katz (2018):
    the L2 norm of the persistence landscape of the last `window` daily
    returns, delay-embedded in three dimensions (one fund has no
    cross-section to make a cloud of). "level" blocks while the norm's z-score
    against its last `lookback` values exceeds z; "variance" blocks while the
    z-score of the norms' rolling 20-session variance does -- their
    early-warning statistic before the 2000 and 2008 crashes."""

    def __init__(
        self,
        mode: str = "level",
        window: int = 40,
        lookback: int = 250,
        z: float = 2.0,
        every: int = 5,
    ):
        if mode not in ("level", "variance"):
            raise ConfigurationError("mode must be level or variance")
        self.window = as_count("window", window, minimum=10)
        self.lookback = as_count("lookback", lookback, minimum=20)
        super().__init__(self.window + 4)
        self.mode = mode
        self.z = _pos("z", z)
        self.every = as_count("every", every)
        self._count = 0
        self._norms: deque[float] = deque(maxlen=self.lookback + 21)
        self._stats: deque[float] = deque(maxlen=self.lookback + 1)

    @property
    def history_sessions(self) -> int:
        return self.window + self.lookback + 25

    def _session(self, context):
        from research.catalog.topology import landscape_norm_series

        r = self.returns()
        if len(r) < self.window + 2:
            return
        self._count += 1
        if (self._count - 1) % self.every:
            return  # a Rips diagram per session is slow; hold the last reading
        cloud = _embed(r)[-self.window :]
        norm = landscape_norm_series(cloud, window=len(cloud), dim=1)[-1]
        if not np.isfinite(norm):
            return
        self._norms.append(float(norm))
        if self.mode == "level":
            stat = norm
        else:
            if len(self._norms) < 8:
                return
            stat = float(np.var(list(self._norms)[-8:]))
        hist = np.fromiter(self._stats, float)
        self._stats.append(float(stat))
        if len(hist) >= 20 and hist.std() > 0:
            self._suppressed = (stat - hist.mean()) / hist.std() > self.z


class RipsScoreGate(DailyComponent):
    """RK268: a multi-scale Vietoris-Rips risk score -- for each window
    length, the total persistence (dims 0 and 1) of the delay-embedded daily
    returns, z-scored against its own last `lookback` values, averaged.
    Blocked while the score exceeds `z`; evaluated every `every` sessions."""

    def __init__(
        self, windows: str = "20,30,40", lookback: int = 120, z: float = 2.0, every: int = 5
    ):
        self.windows = _ints("windows", windows)
        self.every = as_count("every", every)
        self._count = 0
        self.lookback = as_count("lookback", lookback, minimum=20)
        super().__init__(max(self.windows) + 4)
        self.z = _pos("z", z)
        self._tp = {w: deque(maxlen=self.lookback + 1) for w in self.windows}
        self.score: float | None = None

    @property
    def history_sessions(self) -> int:
        return max(self.windows) + self.lookback + 5

    def _session(self, context):
        from research.catalog.topology import rips_persistence, total_persistence

        r = self.returns()
        if len(r) < max(self.windows) + 2:
            return
        self._count += 1
        if (self._count - 1) % self.every:
            return
        cloud_all = _embed(r)
        zs = []
        for w in self.windows:
            cloud = cloud_all[-w:]
            cloud = (cloud - cloud.mean(0)) / (cloud.std(0) + 1e-12)
            dg = rips_persistence(cloud, max_dim=1)
            now = np.array([total_persistence(dg[0]), total_persistence(dg[1])])
            hist = np.array(self._tp[w]) if self._tp[w] else np.zeros((0, 2))
            self._tp[w].append(now)
            if len(hist) > 20:
                zs.extend((now - hist.mean(0)) / (hist.std(0) + 1e-12))
        if zs:
            self.score = float(np.mean(zs))
            self._suppressed = self.score > self.z


class JumpIntensityGate(DailyComponent):
    """RK314: jumps flagged as |r| > k sigma with sigma from trailing bipower
    variation (robust to the jumps), a self-exciting jump intensity fitted
    by maximum likelihood on the last `window` sessions; blocked while the
    intensity is above `mult` times its baseline mu -- jumps clustering."""

    def __init__(self, window: int = 500, k: float = 4.0, beta: float = 0.1, mult: float = 3.0):
        self.window = as_count("window", window, minimum=100)
        super().__init__(self.window + 62)
        self.k, self.beta, self.mult = _pos("k", k), _pos("beta", beta), _pos("mult", mult)
        self._fit = None
        self._since = 0
        self.intensity: float | None = None

    def _session(self, context):
        from research.catalog.point_processes import (
            detect_jumps,
            fit_jump_excitation,
            mutually_exciting_jump_intensity,
        )

        r = self.returns()
        if len(r) < self.window:
            return
        jumps = detect_jumps(r[-self.window - 61 :], window=60, k=self.k)[61:].astype(float)
        if jumps.sum() < 3:
            self._suppressed = False
            return
        if self._fit is None or self._since >= 20:
            self._fit = fit_jump_excitation(jumps[:, None], beta=self.beta)
            self._since = 0
        self._since += 1
        mu, alpha = np.atleast_1d(self._fit["mu"]), np.atleast_2d(self._fit["alpha"])
        # the intensity for the NEXT session: run one more (empty) day
        padded = np.r_[jumps, 0.0][:, None]
        lam = mutually_exciting_jump_intensity(padded, mu, alpha, self.beta)
        self.intensity = float(lam[-1, 0])
        self._suppressed = self.intensity > self.mult * float(mu[0])


# ---------------------------------------------------------------- learned gates


def _lag_features(c: np.ndarray, lags=(1, 2, 3, 5, 10, 21)) -> tuple[np.ndarray, np.ndarray]:
    from research.catalog.technical_ml import lag_feature_matrix

    return lag_feature_matrix(c, lags)


class RandomForestGate(DailyComponent):
    """RK290 (and RK271 with `sequential_bootstrap`): a random forest on
    lagged daily returns predicts whether the next session closes up; refit
    every `refit` sessions on the last `train` labelled sessions. Blocked
    while P(up) < `threshold`. With sequential_bootstrap=True the training
    rows are drawn by López de Prado's sequential bootstrap over labels that
    span `span` sessions, so overlapping outcomes are not over-counted."""

    def __init__(
        self,
        train: int = 500,
        refit: int = 20,
        threshold: float = 0.5,
        sequential_bootstrap: bool = False,
        span: int = 5,
        seed: int = 0,
    ) -> None:
        self.train = as_count("train", train, minimum=50)
        super().__init__(self.train + 25)
        self.refit = as_count("refit", refit)
        if not 0 < threshold < 1:
            raise ConfigurationError("threshold must be in (0, 1)")
        self.threshold = float(threshold)
        self.seqboot = bool(sequential_bootstrap)
        self.span = as_count("span", span)
        self.seed = int(seed)
        self._model = None
        self._since = 0
        self.probability: float | None = None

    def _session(self, context):
        from sklearn.ensemble import RandomForestClassifier

        c = self.closes()
        if len(c) < 80:
            return
        x, y = _lag_features(c)
        if self._model is None or self._since >= self.refit:
            xs, ys = x[-self.train :], y[-self.train :]
            if self.seqboot:
                from research.catalog.technical_ml import indicator_matrix, sequential_bootstrap

                n = len(xs)
                spans = [(i, min(n - 1, i + self.span - 1)) for i in range(n)]
                ind = indicator_matrix(n, spans)
                idx = sequential_bootstrap(ind, size=max(20, n // 4), rng=self.seed)
                xs, ys = xs[idx], ys[idx]
            if len(set(ys)) < 2:
                return
            self._model = RandomForestClassifier(
                n_estimators=100, min_samples_leaf=5, random_state=self.seed
            ).fit(xs, ys)
            self._since = 0
        self._since += 1
        # features for the NEXT session: lagged returns ending at the last close
        last = np.array([[c[-1] / c[-1 - lg] - 1 for lg in (1, 2, 3, 5, 10, 21)]])
        self.probability = float(self._model.predict_proba(last)[0, 1])
        self._suppressed = self.probability < self.threshold


# ---------------------------------------------------------------- external-series gates


class LeadLagGate(DailyComponent):
    """RK204, lead-lag: a leader's previous-session return predicts the
    fund's when their lagged correlation is positive. Reads a CSV (date,
    close) of the leader; blocked on a session whose leader return on the
    prior date fell below -threshold while the trailing `window`-session
    correlation of leader(t-1) with the fund(t) exceeds `min_corr`."""

    def __init__(
        self, path: str = "", threshold: float = 0.01, window: int = 60, min_corr: float = 0.1
    ) -> None:
        self.window = as_count("window", window, minimum=10)
        super().__init__(self.window + 2)
        self.series = _Series(path, ("close",))
        self.threshold = _pos("threshold", threshold)
        self.min_corr = float(min_corr)
        self.corr: float | None = None

    def _session(self, context):
        day = context.timestamp.date()
        lead = dict(self.series.before(day, self.window + 3))
        own_days = [date.fromordinal(d) for d in self.book.days]
        own = dict(zip(own_days, self.book.closes, strict=True))
        common = sorted(set(lead) & set(own))
        if len(common) < 12:
            return
        lc = np.array([lead[d][0] for d in common])
        oc = np.array([own[d] for d in common])
        lr, orr = np.diff(np.log(lc)), np.diff(np.log(oc))
        self.corr = float(np.corrcoef(lr[:-1], orr[1:])[0, 1])
        last_lead = self.series.before(day, 2)
        if len(last_lead) < 2:
            return
        r_lead = last_lead[-1][1][0] / last_lead[-2][1][0] - 1
        self._suppressed = self.corr > self.min_corr and r_lead < -self.threshold


class TransferEntropyGate(DailyComponent):
    """RK221: transfer entropy (Schreiber 2000) from a leader's daily returns
    to the fund's, over the trailing `window`; when it exceeds `threshold`
    nats, follow the leader's latest return -- blocked after the leader
    fell. Reads a CSV (date, close) of the leader."""

    def __init__(self, path: str = "", window: int = 250, bins: int = 3, threshold: float = 0.01):
        self.window = as_count("window", window, minimum=30)
        super().__init__(self.window + 2)
        self.series = _Series(path, ("close",))
        self.bins = as_count("bins", bins, minimum=2)
        self.threshold = _pos("threshold", threshold)
        self.te: float | None = None

    def _session(self, context):
        from research.catalog.information import transfer_entropy

        day = context.timestamp.date()
        lead = dict(self.series.before(day, self.window + 3))
        own = dict(
            zip([date.fromordinal(d) for d in self.book.days], self.book.closes, strict=True)
        )
        common = sorted(set(lead) & set(own))
        if len(common) < self.window + 2:
            return
        lr = np.diff(np.log([lead[d][0] for d in common]))
        orr = np.diff(np.log([own[d] for d in common]))
        te = transfer_entropy(lr[-self.window - 1 :], orr[-self.window - 1 :], self.bins)
        self.te = float(te)
        self._suppressed = bool(te > self.threshold and lr[-1] < 0)


class SentimentGate(Component):
    """RK293, Tetlock (2007): a spike in media pessimism (its z-score over the
    last `window` days above `z`) is followed by falling prices and then a
    reversal. Reads a CSV (date, pessimism); blocked for `wait` sessions
    after a spike, then allowed (the reversal leg)."""

    def __init__(self, path: str = "", window: int = 60, z: float = 1.5, wait: int = 2) -> None:
        super().__init__()
        self.series = _Series(path, ("pessimism",))
        self.window = as_count("window", window, minimum=10)
        self.z = _pos("z", z)
        self.wait = as_count("wait", wait)
        self._day = None

    def _step(self, context):
        day = context.timestamp.toordinal()
        if day == self._day:
            return
        self._day = day
        rows = self.series.before(context.timestamp.date(), self.window + self.wait + 1)
        vals = np.array([v[0] for _, v in rows])
        self._suppressed = False
        for lag in range(1, self.wait + 1):
            if len(vals) < self.window + lag:
                break
            hist, x = vals[-self.window - lag : -lag], vals[-lag]
            if hist.std() > 0 and (x - hist.mean()) / hist.std() > self.z:
                self._suppressed = True


class EventSentimentGate(Component):
    """RK311, FinBERT-style event sentiment at the market level: reads a CSV
    (date, score) of classified news scores in [-1, 1]; blocked for `hold`
    sessions after a day scoring below -threshold."""

    def __init__(self, path: str = "", threshold: float = 0.2, hold: int = 5) -> None:
        super().__init__()
        self.series = _Series(path, ("score",))
        self.threshold = _pos("threshold", threshold)
        self.hold = as_count("hold", hold)
        self._day = None

    def _step(self, context):
        day = context.timestamp.toordinal()
        if day == self._day:
            return
        self._day = day
        rows = self.series.before(context.timestamp.date(), self.hold)
        self._suppressed = any(v[0] < -self.threshold for _, v in rows)


class CausalImpactGate(DailyComponent):
    """RK217, causal impact (Brodersen et al. 2015) after macro events: for
    an event date in `events_path` (a CSV with a `date` and a `value`
    column), the fund's closes are compared with a counterfactual from a
    control series (`control_path`, date, close) fitted on the `pre`
    sessions before it. Blocked for `hold` sessions after the event while
    the cumulative effect is significantly negative (the 95% upper band of
    the last day is below the actual close's counterfactual)."""

    def __init__(
        self, events_path: str = "", control_path: str = "", pre: int = 60, hold: int = 10
    ) -> None:
        self.pre = as_count("pre", pre, minimum=20)
        self.hold = as_count("hold", hold)
        super().__init__(self.pre + self.hold + 2)
        self.events = _Series(events_path, ("value",))
        self.control = _Series(control_path, ("close",))
        self.effect: float | None = None

    def _session(self, context):
        from research.catalog.technical_ml import causal_impact

        day = context.timestamp.date()
        recent = [d for d, _ in self.events.before(day, 50) if (day - d).days <= self.hold * 1.6]
        self._suppressed = False
        if not recent:
            return
        event = recent[-1]
        own_days = [date.fromordinal(d) for d in self.book.days]
        ctrl = dict(self.control.before(day, self.pre + self.hold + 5))
        rows = [(d, c) for d, c in zip(own_days, self.book.closes, strict=True) if d in ctrl]
        pre_end = sum(1 for d, _ in rows if d < event)
        if pre_end < 20 or pre_end >= len(rows):
            return
        y = np.log([c for _, c in rows])
        x = np.log([[ctrl[d][0]] for d, _ in rows])
        out = causal_impact(y, x, pre_end)
        self.effect = float(out["cumulative"])
        self._suppressed = bool(y[-1] < out["lower"][-1])


# ---------------------------------------------------------------- sizers


class _DailySizer(DailyComponent):
    kind = "sizer"

    def __init__(self, keep: int, floor: float = 0.0, cap: float = 2.0) -> None:
        super().__init__(keep)
        if not 0 <= floor <= cap:
            raise ConfigurationError("need 0 <= floor <= cap")
        self.floor, self.cap = float(floor), float(cap)

    def _set(self, value: float) -> None:
        if np.isfinite(value):
            self.multiplier = float(min(self.cap, max(self.floor, value)))


class AtrSizer(_DailySizer):
    """RK67, ATR position sizing (the Turtles' volatility unit): each lot is
    scaled by target / NATR, NATR = ATR(n) / close of completed daily bars,
    clipped to [floor, cap] -- equal risk per lot across calm and wild tapes."""

    def __init__(self, n: int = 14, target: float = 0.03, floor: float = 0.25, cap: float = 2.0):
        self.n = as_count("n", n, minimum=2)
        super().__init__(self.n + 2, floor, cap)
        self.target = _pos("target", target)

    def _session(self, context):
        from research.catalog.technical_ml import atr

        b = self.book
        if len(b.closes) < self.n + 1:
            return
        a = atr(list(b.highs), list(b.lows), list(b.closes), self.n)[-1]
        if a > 0:
            self._set(self.target / (a / b.closes[-1]))


class KellySizer(_DailySizer):
    """RK134, fractional Kelly: f = fraction * mean / variance of the last
    `window` daily returns, clipped to [floor, cap], scales each lot."""

    def __init__(
        self, window: int = 250, fraction: float = 0.5, floor: float = 0.0, cap: float = 2.0
    ):
        self.window = as_count("window", window, minimum=20)
        super().__init__(self.window + 1, floor, cap)
        self.fraction = _pos("fraction", fraction)

    def _session(self, context):
        r = self.returns()
        if len(r) >= self.window and r.var() > 0:
            self._set(self.fraction * r.mean() / r.var())


class GarchSizer(_DailySizer):
    """RK195: a GARCH(1,1) volatility forecast refitted every `refit`
    sessions on the last `window` daily returns; each lot scales by
    (long-run sigma / forecast sigma) ** exponent -- smaller lots when
    tomorrow is forecast to be wilder than usual."""

    def __init__(
        self,
        window: int = 750,
        refit: int = 20,
        exponent: float = 1.0,
        floor: float = 0.25,
        cap: float = 2.0,
    ):
        self.window = as_count("window", window, minimum=100)
        super().__init__(self.window + 1, floor, cap)
        self.refit = as_count("refit", refit)
        self.exponent = float(exponent)
        self._fit = None
        self._since = 0

    def _session(self, context):
        from research.catalog.econometrics import garch11_fit

        r = self.returns()
        if len(r) < min(self.window, 250):
            return
        r = r[-self.window :]
        if self._fit is None or self._since >= self.refit:
            fit = garch11_fit(r)
            if fit["alpha"] + fit["beta"] < 1:  # keep the last stationary fit
                self._fit = fit
            self._since = 0
        self._since += 1
        if self._fit is None:
            return
        o, a, b = self._fit["omega"], self._fit["alpha"], self._fit["beta"]
        longrun = o / (1 - a - b)
        s2 = longrun  # filter the fitted recursion through the latest returns
        for x in r[-250:]:
            s2 = o + a * x * x + b * s2
        if s2 > 0:
            self._set((math.sqrt(longrun) / math.sqrt(s2)) ** self.exponent)


class EvtSizer(_DailySizer):
    """RK130, extreme value theory: a peaks-over-threshold fit to the last
    `window` daily losses gives a 99% expected shortfall; each lot scales by
    min(1, es_budget / ES) -- the tail-risk governor beside the regime exit."""

    def __init__(
        self, window: int = 500, alpha: float = 0.99, es_budget: float = 0.08, floor: float = 0.0
    ):
        self.window = as_count("window", window, minimum=100)
        super().__init__(self.window + 1, floor, 1.0)
        self.alpha = float(alpha)
        self.es_budget = _pos("es_budget", es_budget)

    def _session(self, context):
        from research.catalog.concepts import pot_var_es

        r = self.returns()
        if len(r) < self.window:
            return
        es = pot_var_es(r[-self.window :], self.alpha)["es"]
        if np.isfinite(es) and es > 0:
            self._set(self.es_budget / es)


class ConformalSizer(_DailySizer):
    """RK295 (one forecaster) and RK127 (`stack=True`, alpha stacking): the
    next session's return is forecast -- by the trailing 20-session mean
    return, or by a least-squares stack of three base forecasts (5- and
    20-session means, last-session reversal) fitted on the last `train`
    sessions -- and wrapped in a split-conformal interval calibrated on the
    forecast's own last `calibration` errors. A lot is full size when the
    interval's lower bound is above zero, `floor` otherwise."""

    def __init__(
        self,
        stack: bool = False,
        train: int = 250,
        calibration: int = 120,
        alpha: float = 0.2,
        floor: float = 0.25,
    ) -> None:
        self.train = as_count("train", train, minimum=40)
        self.calibration = as_count("calibration", calibration, minimum=20)
        super().__init__(self.train + self.calibration + 25, floor, 1.0)
        self.stack = bool(stack)
        if not 0 < alpha < 1:
            raise ConfigurationError("alpha must be in (0, 1)")
        self.alpha = float(alpha)

    @staticmethod
    def _base(r: np.ndarray, t: int) -> np.ndarray:
        return np.array([r[t - 5 : t].mean(), r[t - 20 : t].mean(), -r[t - 1]])

    def _session(self, context):
        r = self.returns()
        n = len(r)
        if n < self.train + self.calibration + 21:
            return
        idx = range(n - self.train - self.calibration, n)
        feats = np.array([self._base(r, t) for t in idx])
        target = r[n - self.train - self.calibration : n]
        if self.stack:
            fit_x = np.column_stack([np.ones(self.train), feats[: self.train]])
            coef, *_ = np.linalg.lstsq(fit_x, target[: self.train], rcond=None)
            preds = np.column_stack([np.ones(len(feats)), feats]) @ coef
            now = float(np.r_[1.0, self._base(np.r_[r, 0.0], n)] @ coef)
        else:
            preds = feats[:, 1]
            now = float(r[-20:].mean())
        residuals = (target - preds)[-self.calibration :]
        low, _ = split_conformal_interval(now, residuals, self.alpha)
        self._set(1.0 if low > 0 else self.floor)


class EmvSizer(_DailySizer):
    """RK220, Wang & Zhou's exploratory mean-variance agent: trained every
    `refit` sessions by REINFORCE on episodes of `horizon` sessions drawn from
    the last `window` returns, aiming at terminal wealth 1 + target; its mean
    dollar position at wealth 1 scales each lot, clipped to [floor, cap]."""

    def __init__(
        self,
        window: int = 500,
        horizon: int = 20,
        target: float = 0.02,
        refit: int = 60,
        floor: float = 0.0,
        cap: float = 2.0,
        seed: int = 0,
    ):
        self.window = as_count("window", window, minimum=50)
        super().__init__(self.window + 1, floor, cap)
        self.horizon = as_count("horizon", horizon, minimum=2)
        self.target = float(target)
        self.refit = as_count("refit", refit)
        self.seed = int(seed)
        self._agent = None
        self._since = 0

    def _session(self, context):
        from research.catalog.deep_rl import EMVAgent

        r = self.returns()
        if len(r) < self.window:
            return
        if self._agent is None or self._since >= self.refit:
            agent = EMVAgent(
                target=1.0 + self.target, horizon=self.horizon, seed=self.seed, long_only=True
            )
            agent.train(r[-self.window :], episodes=60, batch=10)
            self._agent = agent
            self._since = 0
        self._since += 1
        mean, _ = self._agent.policy(0, 1.0)
        self._set(mean)


class BreadthThrustSizer(Component):
    """RK212, Zweig's breadth thrust: reads a CSV (date, advances, declines);
    when the 10-day EMA of advances / (advances + declines) jumps from below
    `low` to above `high` within `window` days, lots are scaled by `boost`
    for the next `hold` sessions."""

    kind = "sizer"

    def __init__(
        self,
        path: str = "",
        low: float = 0.40,
        high: float = 0.615,
        window: int = 10,
        boost: float = 1.5,
        hold: int = 20,
    ) -> None:
        super().__init__()
        self.series = _Series(path, ("advances", "declines"))
        self.low, self.high = float(low), float(high)
        self.window = as_count("window", window)
        self.boost = _pos("boost", boost)
        self.hold = as_count("hold", hold)
        self._day = None

    def _step(self, context):
        from research.catalog.technical_ml import zweig_breadth_thrust

        day = context.timestamp.toordinal()
        if day == self._day:
            return
        self._day = day
        rows = self.series.before(context.timestamp.date(), 4 * self.window + self.hold)
        self.multiplier = 1.0
        if len(rows) < 2 * self.window:
            return
        adv = [v[0] for _, v in rows]
        dec = [v[1] for _, v in rows]
        fired = zweig_breadth_thrust(adv, dec, self.low, self.high, self.window)["signal"]
        if fired[-self.hold :].any():
            self.multiplier = self.boost


class RLSizer(_DailySizer):
    """RK372 (PPO), RK347 (DDPG / TD3) and RK346 (SAC): a reinforcement-
    learning exposure policy on four daily features (1-, 5- and 20-session
    returns, 20-session volatility), retrained every `refit` sessions on the
    last `window` sessions as a one-step task: action a in [0, cap] earns
    a * r_next - risk_aversion * (a * r_next)^2. The algorithm decides how
    the linear policy learns (`algo`):

      ppo   Gaussian policy, clipped-ratio policy gradient on advantages
            (rl_agents.ppo_clip_loss / gae with gamma = 0);
      ddpg  deterministic policy improved along a quadratic-in-action
            critic's gradient (td3 = the minimum of two critics);
      sac   Gaussian policy maximising the critic plus `temperature` x entropy.

    The policy's mean action at the latest features scales each lot. The
    ledger rejects these as traders (A1); here they only size the grid."""

    def __init__(
        self,
        algo: str = "ppo",
        window: int = 750,
        refit: int = 60,
        risk_aversion: float = 2.0,
        epochs: int = 50,
        temperature: float = 0.05,
        floor: float = 0.0,
        cap: float = 2.0,
        seed: int = 0,
    ):
        if algo not in ("ppo", "ddpg", "td3", "sac"):
            raise ConfigurationError("algo must be ppo, ddpg, td3 or sac")
        self.window = as_count("window", window, minimum=60)
        super().__init__(self.window + 22, floor, cap)
        self.algo = algo
        self.refit = as_count("refit", refit)
        self.risk_aversion = float(risk_aversion)
        self.epochs = as_count("epochs", epochs)
        self.temperature = float(temperature)
        self.seed = int(seed)
        self._theta: np.ndarray | None = None
        self._scale: tuple[np.ndarray, np.ndarray] | None = None
        self._since = 0

    @staticmethod
    def _features(r: np.ndarray, t: int) -> np.ndarray:
        return np.array([r[t - 1], r[t - 5 : t].sum(), r[t - 20 : t].sum(), r[t - 20 : t].std()])

    def _reward(self, a, nxt):
        g = a * nxt
        return g - self.risk_aversion * g * g

    def _train(self, s: np.ndarray, nxt: np.ndarray) -> np.ndarray:
        from research.catalog.rl_agents import ddpg_target, ppo_clip_loss, td3_target

        rng = np.random.default_rng(self.seed)
        x = np.column_stack([np.ones(len(s)), s])
        theta = np.zeros(x.shape[1])
        theta[0] = 1.0
        lr, sigma = 0.05, 0.3
        if self.algo == "ppo":
            for _ in range(self.epochs):
                mu = np.clip(x @ theta, 0, self.cap)
                a = np.clip(mu + sigma * rng.standard_normal(len(mu)), 0, self.cap)
                rew = self._reward(a, nxt)
                adv = rew - rew.mean()
                adv /= adv.std() + 1e-12
                old_logp = -0.5 * ((a - mu) / sigma) ** 2
                for _ in range(4):
                    mu_new = np.clip(x @ theta, 0, self.cap)
                    logp = -0.5 * ((a - mu_new) / sigma) ** 2
                    ratio = np.exp(logp - old_logp)
                    _, grad_ratio = ppo_clip_loss(ratio, adv)
                    dlogp_dmu = (a - mu_new) / sigma**2
                    theta -= lr * (x.T @ (grad_ratio * ratio * dlogp_dmu))
            return theta

        # critic: Q(s, a) = w . [x, a x, a^2], fitted by least squares on
        # targets from rl_agents (gamma = 0: the target is the reward).
        def phi(a):
            return np.column_stack([x, a[:, None] * x, (a * a)[:, None]])

        done = np.ones(len(x))
        for _ in range(self.epochs):
            mu = np.clip(x @ theta, 0, self.cap)
            a = np.clip(mu + sigma * rng.standard_normal(len(mu)), 0, self.cap)
            rew = self._reward(a, nxt)
            if self.algo == "td3":
                target = td3_target(rew, done, rew, rew, gamma=0.0)
            elif self.algo == "sac":
                from research.catalog.rl_agents import sac_target

                logp = -0.5 * ((a - mu) / sigma) ** 2
                target = sac_target(rew, done, rew, rew, logp, alpha=self.temperature, gamma=0.0)
            else:
                target = ddpg_target(rew, done, rew, gamma=0.0)
            w, *_ = np.linalg.lstsq(phi(a), np.asarray(target, float), rcond=None)
            k = x.shape[1]
            dq_da = x @ w[k : 2 * k] + 2 * w[-1] * mu
            theta += lr * (x.T @ dq_da) / len(x)
        return theta

    def _session(self, context):
        r = self.returns()
        n = len(r)
        if n < self.window + 21:
            return
        if self._theta is None or self._since >= self.refit:
            ts = range(n - self.window, n - 1)
            s = np.array([self._features(r, t) for t in ts])
            nxt = np.array([r[t] for t in ts])
            mu, sd = s.mean(0), s.std(0) + 1e-12
            self._scale = (mu, sd)
            self._theta = self._train((s - mu) / sd, nxt)
            self._since = 0
        self._since += 1
        mu, sd = self._scale
        f = (self._features(r, n) - mu) / sd
        self._set(float(np.r_[1.0, f] @ self._theta))


# ---------------------------------------------------------------- level components


class InventorySkewLevel(Component):
    """RK246, inventory-skewed market making, bid side only: each open lot
    deepens the next buy rung by `skew` steps (inventory_control.
    inventory_skewed_level), capped at `max_depth`. Never above the
    champion's own level."""

    kind = "level"

    def __init__(self, skew: float = 0.5, max_depth: float = 0.2) -> None:
        super().__init__()
        self.skew = float(skew)
        if self.skew < 0:
            raise ConfigurationError("skew must be >= 0")
        self.max_depth = _pos("max_depth", max_depth)

    def _step(self, context):
        pass

    def adjust_level(self, level, context, step):
        from research.strategies.inventory_control import inventory_skewed_level

        reference = level / (1.0 - step)
        depth_cap = max(self.max_depth, step)
        new = inventory_skewed_level(reference, step, context.open_lot_count, self.skew, depth_cap)
        return min(level, new)


class AvellanedaStoikovLevel(Component):
    """RK274, Avellaneda & Stoikov (2008), bid side only: the reservation
    price r = s - q * gamma * sigma^2 * tau shifts the buy level down by
    (s - r) / s with inventory q = open lots, sigma the trailing per-minute
    return volatility (over `vol_window` bars) in price units, and tau the
    fraction of the session left. Never above the champion's own level."""

    kind = "level"

    def __init__(self, gamma: float = 0.1, vol_window: int = 60) -> None:
        super().__init__()
        self.gamma = _pos("gamma", gamma)
        self.vol_window = as_count("vol_window", vol_window, minimum=5)
        self._closes: deque[float] = deque(maxlen=self.vol_window + 1)
        self._last: float | None = None
        self._minute = 0

    def _step(self, context):
        if self._last is not None:
            self._closes.append(self._last)
        self._last = context.close
        self._minute = _minute(context) or 0

    def adjust_level(self, level, context, step):
        from research.strategies.inventory_control import as_reservation_price

        if len(self._closes) < 5 or context.open_lot_count <= 0:
            return level
        c = np.fromiter(self._closes, float)
        sigma = float(np.diff(c).std())
        if sigma <= 0:
            return level
        s = c[-1]
        tau = max(1.0, SESSION_MINUTES - self._minute)
        r = as_reservation_price(s, float(context.open_lot_count), self.gamma / s, sigma, tau)
        return min(level, level * max(0.0, r) / s)


# ---------------------------------------------------------------- the registry


@dataclass(frozen=True)
class SignalSpec:
    ledger: str
    cls: type
    fixed: dict = field(default_factory=dict)
    label: str = ""
    files: tuple[str, ...] = ()  # parameters naming a CSV the signal reads


class MissingDataComponent(Component):
    """Stands in for a signal whose CSV was not given, so the strategy can
    be built (the run form describes and seeds it) but the run stops on its
    first bar with what to supply -- never a silent no-op."""

    def __init__(self, name: str, files: tuple[str, ...], kind: str) -> None:
        super().__init__()
        self.kind = kind
        self.message = (
            f"the {name} signal reads data the warehouse does not hold: set "
            + ", ".join(f"{f}=FILE.csv" for f in files)
            + " in signal_params (see research/strategies/signal_library.py)"
        )

    def _step(self, context):
        raise ConfigurationError(self.message)


SIGNALS: dict[str, SignalSpec] = {
    # --- completed earlier as hf_signal_gated gates (signal_gates.py)
    "high52": SignalSpec("RK14", sg.FiftyTwoWeekHighGate, {"mode": "near_high"}, "52-week high"),
    "adx": SignalSpec("RK55", sg.AdxTrendGate, {"mode": "strong_downtrend"}, "ADX trend filter"),
    "ribbon": SignalSpec("RK64", sg.RibbonGate, {"mode": "bearish"}, "Moving-average ribbon"),
    "gap": SignalSpec("RK79", sg.GapGate, {"mode": "gap_down"}, "Opening gap continuation"),
    "kama": SignalSpec("RK112", sg.KamaTrendGate, {"mode": "below_falling"}, "KAMA trend"),
    "zscore": SignalSpec(
        "RK147",
        sg.BandReversionGate,
        {"mode": "oversold", "name": "zscore_gate", "modes": ("off", "oversold")},
        "Moving-average z-score reversion",
    ),
    "bollinger": SignalSpec(
        "RK161",
        sg.BandReversionGate,
        {"mode": "lower_band", "name": "band_gate", "modes": ("off", "lower_band")},
        "Bollinger band reversion",
    ),
    "vix_term": SignalSpec(
        "RK168", sg.TermStructureGate, {"mode": "backwardation"}, "VIX term structure", ("path",)
    ),
    "avwap": SignalSpec("RK208", sg.AnchoredVwapGate, {"mode": "swing_high"}, "Anchored VWAP"),
    "anomaly": SignalSpec(
        "RK243", sg.AnomalyGate, {"mode": "price_volume"}, "Price/volume anomalies"
    ),
    "imbalance": SignalSpec(
        "RK253", sg.VolumeImbalanceGate, {"mode": "sell_imbalance"}, "Volume-clock imbalance"
    ),
    "triple_barrier": SignalSpec(
        "RK294", sg.TripleBarrierGate, {"mode": "classifier"}, "Triple-barrier classifier"
    ),
    "hurst_bands": SignalSpec(
        "RK297", sg.HurstBandGate, {"mode": "adaptive_band"}, "Hurst-adaptive bands"
    ),
    # --- this module
    "supertrend": SignalSpec("RK44", SupertrendGate, {}, "Supertrend"),
    "ma_cross": SignalSpec("RK62", MovingAverageCrossGate, {}, "Dual moving-average crossover"),
    "atr_sizing": SignalSpec("RK67", AtrSizer, {}, "ATR position sizing"),
    "mtf_trend": SignalSpec("RK78", MultiTimeframeTrendGate, {}, "Multi-timeframe trend agreement"),
    "hmm": SignalSpec("RK102", HmmRegimeGate, {"trend": 0}, "HMM regime"),
    "hurst_regime": SignalSpec("RK103", HurstRegimeGate, {}, "Hurst / variance-ratio regime"),
    "hhmm": SignalSpec("RK106", HmmRegimeGate, {"trend": 100}, "Hierarchical HMM regime"),
    "orb": SignalSpec("RK110", OpeningRangeGate, {}, "Opening range breakout"),
    "ema_pullback": SignalSpec("RK115", EmaPullbackGate, {}, "EMA pullback continuation"),
    "conformal_stack": SignalSpec(
        "RK127", ConformalSizer, {"stack": True}, "Conformal alpha stacking"
    ),
    "evt": SignalSpec("RK130", EvtSizer, {}, "EVT tail-risk sizing"),
    "kelly": SignalSpec("RK134", KellySizer, {}, "Fractional Kelly sizing"),
    "vwap": SignalSpec("RK150", VwapReversionGate, {}, "VWAP reversion"),
    "overnight": SignalSpec("RK154", OvernightGate, {}, "Overnight anomaly"),
    "garch": SignalSpec("RK195", GarchSizer, {}, "GARCH volatility sizing"),
    "lead_lag": SignalSpec("RK204", LeadLagGate, {}, "Lead-lag cross-asset", ("path",)),
    "breadth_thrust": SignalSpec("RK212", BreadthThrustSizer, {}, "Breadth thrust", ("path",)),
    "trend_scan": SignalSpec("RK213", TrendScanGate, {}, "Trend scanning"),
    "causal_impact": SignalSpec(
        "RK217",
        CausalImpactGate,
        {},
        "Causal-impact macro events",
        ("events_path", "control_path"),
    ),
    "emv": SignalSpec("RK220", EmvSizer, {}, "Exploratory mean-variance RL"),
    "transfer_entropy": SignalSpec(
        "RK221", TransferEntropyGate, {}, "Transfer-entropy lead-lag", ("path",)
    ),
    "inventory_skew": SignalSpec("RK246", InventorySkewLevel, {}, "Inventory-skewed bid"),
    "vpin": SignalSpec("RK247", VpinGate, {}, "VPIN flow toxicity"),
    "tda_level": SignalSpec(
        "RK254", LandscapeGate, {"mode": "level"}, "TDA landscape crash signal"
    ),
    "tda_variance": SignalSpec(
        "RK255", LandscapeGate, {"mode": "variance"}, "TDA landscape early warning"
    ),
    "tda_rips": SignalSpec("RK268", RipsScoreGate, {}, "Multi-scale Rips risk score"),
    "rf_seqboot": SignalSpec(
        "RK271",
        RandomForestGate,
        {"sequential_bootstrap": True},
        "Random forest, sequential bootstrap",
    ),
    "avellaneda_stoikov": SignalSpec("RK274", AvellanedaStoikovLevel, {}, "Avellaneda-Stoikov bid"),
    "random_forest": SignalSpec(
        "RK290", RandomForestGate, {"sequential_bootstrap": False}, "Random forest classifier"
    ),
    "sentiment": SignalSpec("RK293", SentimentGate, {}, "News pessimism (Tetlock)", ("path",)),
    "conformal": SignalSpec("RK295", ConformalSizer, {"stack": False}, "Conformal sizing"),
    "fracdiff": SignalSpec("RK300", FracDiffGate, {}, "Fractionally differenced reversion"),
    "event_sentiment": SignalSpec("RK311", EventSentimentGate, {}, "Event sentiment", ("path",)),
    "hawkes_jumps": SignalSpec("RK314", JumpIntensityGate, {}, "Self-exciting jump intensity"),
    "rl_sac": SignalSpec("RK346", RLSizer, {"algo": "sac"}, "Soft actor-critic sizing"),
    "rl_ddpg": SignalSpec("RK347", RLSizer, {"algo": "td3"}, "DDPG / TD3 sizing"),
    "rl_ppo": SignalSpec("RK372", RLSizer, {"algo": "ppo"}, "PPO sizing"),
}


def signal_parameters(name: str) -> dict[str, inspect.Parameter]:
    """The tunable parameters of a signal: its class's keyword parameters
    minus the ones the algorithm fixes."""
    spec = SIGNALS[name]
    params = inspect.signature(spec.cls.__init__).parameters
    return {
        k: p
        for k, p in params.items()
        if k != "self" and k not in spec.fixed and p.kind is not inspect.Parameter.VAR_KEYWORD
    }


def _coerce(name: str, param: inspect.Parameter, text: str):
    default = param.default
    if isinstance(default, bool):
        return text.strip().lower() in ("1", "true", "yes", "on")
    if isinstance(default, int):
        return as_count(name, float(text), minimum=0)
    if isinstance(default, float):
        return float(text)
    return text


def parse_signal_params(name: str, text: str) -> dict:
    """ "k=v,k=v" (';' also separates) into typed keyword arguments; an
    unknown key fails naming the valid ones."""
    if name not in SIGNALS:
        raise ConfigurationError(f"unknown signal {name!r}; known: {sorted(SIGNALS)}")
    known = signal_parameters(name)
    raw: dict[str, str] = {}
    last = None
    for part in str(text or "").replace(";", ",").split(","):
        if not part.strip():
            continue
        if "=" not in part:
            # a list value ("horizons=21,63,252") continues the previous key
            if last is None:
                raise ConfigurationError(f"signal_params entry {part!r} is not key=value")
            raw[last] += "," + part.strip()
            continue
        k, v = (x.strip() for x in part.split("=", 1))
        if k not in known:
            raise ConfigurationError(f"{name} has no parameter {k!r}; it takes {sorted(known)}")
        raw[k], last = v, k
    return {k: _coerce(k, known[k], v) for k, v in raw.items()}


def build_signal(name: str, params: str = ""):
    """Construct the named component with the algorithm's fixed settings and
    any overrides from `params`."""
    spec = SIGNALS.get(name)
    if spec is None:
        raise ConfigurationError(f"unknown signal {name!r}; known: {sorted(SIGNALS)}")
    kwargs = {**spec.fixed, **parse_signal_params(name, params)}
    missing = tuple(f for f in spec.files if not kwargs.get(f))
    if missing:
        kind = "sizer" if spec.cls is BreadthThrustSizer else "gate"
        return MissingDataComponent(name, missing, kind)
    component = spec.cls(**kwargs)
    if not hasattr(component, "kind"):
        component.kind = "gate"  # signal_gates' gates
    if not hasattr(component, "adjust_level"):
        component.adjust_level = lambda level, context, step: level
    if not hasattr(component, "multiplier"):
        component.multiplier = 1.0
    return component


def strategy_id_for(name: str) -> str:
    """rk<ledger number>_<signal name>, the id the registry selects it by."""
    return f"{SIGNALS[name].ledger.lower()}_{name}"


__all__ = [
    "SIGNALS",
    "MissingDataComponent",
    "SignalSpec",
    "build_signal",
    "load_daily_series",
    "parse_signal_params",
    "signal_parameters",
    "strategy_id_for",
]
