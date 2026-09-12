"""Daily regime + forward-volatility inference, driven from record_tick.

Produces the two values MarketContext now carries:

    qlib_regime_score   P(next `horizon` sessions draw down more than
                        `threshold`), in [0, 1]
    expected_volatility annualized forward realized vol over the same
                        horizon, >= 0

--------------------------------------------------------------------
THE MODELS ARE TRAINED WITH QLIB AND RUN WITHOUT IT

tools/train_qlib_regime.py may import qlib (Alpha158 expressions,
DDG-DA's concept-drift reweighting, the workflow recorder). NOTHING
here imports it, and nothing here may. requirements.txt's rule is that
the live loop and the Raspberry Pi that runs it must never need an
optional dependency to start; qlib is a heavy transitive tree and the
Pi's image does not install even requirements-ml.txt (see
docs/DEPLOY_RASPBERRY_PI.md on the two-machine split).

What crosses the boundary is a LightGBM booster in its native TEXT
format plus a JSON sidecar, exactly the artifact contract
tools/train_ml_model.py already established for reachability: no
pickle, no arbitrary code on load, and a feature order the consumer can
read rather than assume. Whatever qlib did during training is a
training-time detail by the time this file sees the result.

--------------------------------------------------------------------
DAILY CADENCE, AND WHY THAT IS THE WHOLE LATENCY STORY

Both models answer a question about the NEXT N SESSIONS from features
measured over the LAST N SESSIONS. Every input is daily. Re-running
them on each of a session's 390 minute bars would not produce 390
different answers -- it would produce the same answer 390 times, at 390
times the cost, and any intraday variation it did show would be an
artifact of a partially-formed day rather than information.

So this class folds intraday bars into sessions and runs the two models
exactly ONCE per session rollover. On a 390-bar day that is 2 model
calls per 390 bars instead of 780.

MEASURED, over 117,000 replayed bars (300 sessions x 390) with the
contexts pre-built so only record_tick is timed: 2.1us/bar, against the
~600us/bar src/ml/reachability_sizing.py records for its per-bar
inference. Nearly all of the 2.1us is the session-rollover check
(timestamp.astimezone(NY).date()), not the model. That arithmetic --
not threading -- is what makes this safe to call from a live loop.

There is deliberately NO background thread, and that is a design
decision rather than an omission. The live loop's tick budget is 60
SECONDS (docs/DEPLOY_RASPBERRY_PI.md: "372 ticks at 60s"); spending
~200us of it is not a problem worth introducing a concurrency failure
mode for. Worse, a thread would make the reading depend on wall-clock
timing, and a backtest replaying the same bars would then be unable to
reproduce what live actually saw -- which is precisely the
backtest/live parity that src/trading/decision_cycle.py exists to
enforce. Synchronous and deterministic is the requirement, not the
compromise.

--------------------------------------------------------------------
NO LOOKAHEAD, BY CONSTRUCTION RATHER THAN BY CARE

The reading in force during session D is computed AT THE ROLLOVER INTO
D, from sessions <= D-1. A session is never fed to the feature builder
until a bar belonging to the NEXT session has arrived, so the current
session's own high, low and close cannot reach the model that is
scoring it. This is the same causal-transform rule src/CLAUDE.md states
for all of src/ml/, expressed structurally: there is no shift to
forget, because the future bar is what triggers the computation.

--------------------------------------------------------------------
WHY NOT REUSE IncrementalBarFeatures

src/ml/rolling.py is minute-bar-specific in two places that would fail
SILENTLY on daily input: _rvol annualizes with sqrt(390 * 252), which
over-scales a daily series by sqrt(390), and _session_fields emits
minute-of-session, which is meaningless once a bar IS a session. A
daily feature builder is a different object, not a parameterization of
that one, so it lives here.

The rule that class exists to serve still applies, and is met the same
way: `DailyRegimeFeatures` is the ONE implementation, and the trainer
replays it bar-by-bar over history rather than writing a vectorized
twin. At daily frequency that is a few thousand iterations -- cheap
enough that "agree by construction" costs nothing, where at minute
frequency it would have cost a great deal.
"""

from __future__ import annotations

import json
import math
from collections import deque
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

import numpy as np

from src.core.exceptions import ConfigurationError
from src.ml.features import catalogue, default_directory, transformed_sources

_NY = ZoneInfo("America/New_York")

# Longest trailing window any feature below asks for. Ring buffers are
# sized to it once rather than per-feature.
_MAX_WINDOW = 250

# Trading sessions per year, for annualizing a daily realized vol. The
# minute-bar code uses 390 * 252; a daily series is just 252.
_SESSIONS_PER_YEAR = 252

# Completed sessions required before this emits anything at all. The
# widest feature is a 250-session percentile, but demanding the full
# 250 would leave a fresh deployment blind for a trading year. 60 is
# the point at which the short and medium windows (1/5/20/60d returns,
# 10/20/60d vols, SMA50) are all genuinely seeded; the 200/250-session
# features stay NaN until they fill and LightGBM routes a NaN down its
# learned default split rather than needing it imputed.
_MIN_SESSIONS = 60

DAILY_FEATURES: tuple[str, ...] = (
    "ret_1d",
    "ret_5d",
    "ret_20d",
    "ret_60d",
    "rvol_10d",
    "rvol_20d",
    "rvol_60d",
    "rvol_ratio_10_60",
    # tools/probe_vol_filtered_regime.py measured the single best regime
    # filter this project has found: 20-day realized vol below its own
    # trailing 250-day 75th percentile, ON TOP of SMA200 -- 38.98% CAGR
    # vs 34.57%, worst year -1.0% vs -19.8%, max drawdown 35.6% vs
    # 50.2%. This carries that exact quantity as a continuous feature
    # (the percentile rank itself, not the boolean) so the model can
    # learn its own cutoff instead of inheriting a hand-picked 0.75.
    "rvol_20d_pctile_250d",
    "drawdown_from_high_250d",
    "max_drawdown_20d",
    # SMA200 is the incumbent regime signal every probe in tools/ is
    # measured against. Carried as a continuous distance rather than the
    # boolean cross for the same reason as the percentile above.
    "price_vs_sma_50",
    "price_vs_sma_200",
    "sma_50_vs_200",
    "sma_200_slope_20d",
    "atr_14_pct",
    "rsi_14",
    "down_day_frac_20d",
    "gap_abs_mean_5d",
)

# The volatility block from src/ml/features.py -- VIX term structure,
# VVIX, SKEW, VXN, RVX, OVX, GVZ, SPY realized vol. Same 15 columns
# src/ml/live_features.py uses, and for the same measured reason
# (tools/ablate_ml_features.py: the vol block carried +0.039 of the
# +0.046 total AUC lift on the one fund where macro survived at all).
VOL_BLOCK: tuple[str, ...] = tuple(f.name for f in catalogue() if f.category == "vol")


@dataclass(frozen=True)
class RegimeReading:
    """One session's model output, or the explicit absence of one.

    Frozen for the same reason MarketContext is: it is handed to a
    strategy that must not be able to alter what it was shown.
    """

    crash_probability: float
    expected_volatility: float
    as_of: date | None
    warm: bool

    @property
    def known(self) -> bool:
        """True when a model actually produced these numbers."""
        return self.warm and self.crash_probability >= 0.0


NO_READING = RegimeReading(
    crash_probability=-1.0,
    expected_volatility=-1.0,
    as_of=None,
    warm=False,
)


def _percentile_rank(window: np.ndarray, value: float) -> float:
    """Fraction of `window` at or below `value`, in [0, 1]."""
    if window.size == 0 or not math.isfinite(value):
        return float("nan")
    return float(np.count_nonzero(window <= value) / window.size)


class _WilderRSI:
    """Daily Wilder RSI. A local copy rather than an import from
    src/strategies/sizing_indicators.py, which tracks price ticks for a
    sizing model and is fed every minute bar by the strategies that use
    it; this one is fed one value per SESSION. Same formula, different
    clock, and sharing the instance would mean one of the two callers
    silently getting the other's cadence."""

    def __init__(self, period: int = 14) -> None:
        self.period = period
        self._avg_gain: float | None = None
        self._avg_loss: float | None = None
        self._prev: float | None = None
        self._seen = 0

    def update(self, close: float) -> None:
        if self._prev is None:
            self._prev = close
            return
        change = close - self._prev
        self._prev = close
        gain = max(change, 0.0)
        loss = max(-change, 0.0)
        self._seen += 1
        if self._avg_gain is None:
            self._avg_gain, self._avg_loss = gain, loss
            return
        k = self.period
        self._avg_gain = (self._avg_gain * (k - 1) + gain) / k
        self._avg_loss = (self._avg_loss * (k - 1) + loss) / k

    @property
    def value(self) -> float:
        if self._avg_gain is None or self._seen < self.period:
            return float("nan")
        if self._avg_loss == 0:
            return 100.0
        rs = self._avg_gain / self._avg_loss
        return 100.0 - (100.0 / (1.0 + rs))


class DailyRegimeFeatures:
    """Causal daily features from daily OHLC.

    record() returns the vector describing sessions strictly BEFORE the
    one handed in, then folds that session into the rolling state --
    the same contract (and the same ordering trap avoided the same way)
    as src/ml/rolling.IncrementalBarFeatures.
    """

    def __init__(self) -> None:
        self._close: deque[float] = deque(maxlen=_MAX_WINDOW)
        self._high: deque[float] = deque(maxlen=_MAX_WINDOW)
        self._low: deque[float] = deque(maxlen=_MAX_WINDOW)
        self._log_return: deque[float] = deque(maxlen=_MAX_WINDOW)
        self._true_range: deque[float] = deque(maxlen=_MAX_WINDOW)
        # 250 trailing readings of the 20-day vol, for its own percentile.
        self._rvol_20_history: deque[float] = deque(maxlen=_MAX_WINDOW)
        self._rsi = _WilderRSI(14)
        self._sma_200_history: deque[float] = deque(maxlen=64)
        self._prev_close: float | None = None
        self.sessions = 0

    # --- reads over the trailing window (all exclude the new session) --

    def _rvol(self, window: int) -> float:
        """Annualized realized vol over the last `window` sessions."""
        if len(self._log_return) < max(2, window // 2):
            return float("nan")
        recent = np.fromiter(self._log_return, dtype=np.float64)[-window:]
        if recent.size < 2:
            return float("nan")
        # ddof=1 matches src/ml/features.py's pandas .std() default, so a
        # vol computed here is comparable to one computed there.
        return float(np.std(recent, ddof=1) * math.sqrt(_SESSIONS_PER_YEAR))

    def _ret(self, window: int) -> float:
        if len(self._close) <= window:
            return float("nan")
        past = self._close[-(window + 1)]
        if past <= 0:
            return float("nan")
        return float(self._close[-1] / past - 1.0)

    def _sma(self, window: int) -> float:
        if len(self._close) < window:
            return float("nan")
        return float(np.mean(np.fromiter(self._close, dtype=np.float64)[-window:]))

    def _vector(self) -> dict[str, float]:
        nan = float("nan")
        if not self._close:
            return dict.fromkeys(DAILY_FEATURES, nan)

        closes = np.fromiter(self._close, dtype=np.float64)
        last = closes[-1]
        rvol_10, rvol_20, rvol_60 = self._rvol(10), self._rvol(20), self._rvol(60)
        sma_50, sma_200 = self._sma(50), self._sma(200)

        if len(self._rvol_20_history) >= 60 and math.isfinite(rvol_20):
            pctile = _percentile_rank(np.fromiter(self._rvol_20_history, dtype=np.float64), rvol_20)
        else:
            pctile = nan

        high_250 = float(np.max(closes)) if closes.size else nan
        dd_250 = (high_250 - last) / high_250 if high_250 and high_250 > 0 else nan

        if closes.size >= 20:
            recent = closes[-20:]
            running_peak = np.maximum.accumulate(recent)
            dd_20 = float(np.max((running_peak - recent) / running_peak))
        else:
            dd_20 = nan

        if len(self._true_range) >= 14 and last > 0:
            atr = float(np.mean(np.fromiter(self._true_range, dtype=np.float64)[-14:]))
            atr_pct = atr / last
        else:
            atr_pct = nan

        if len(self._log_return) >= 20:
            recent_r = np.fromiter(self._log_return, dtype=np.float64)[-20:]
            down_frac = float(np.count_nonzero(recent_r < 0) / recent_r.size)
        else:
            down_frac = nan

        if len(self._log_return) >= 5:
            gaps = np.abs(np.fromiter(self._log_return, dtype=np.float64)[-5:])
            gap_mean = float(np.mean(gaps))
        else:
            gap_mean = nan

        if len(self._sma_200_history) >= 21 and math.isfinite(sma_200):
            past_sma = self._sma_200_history[-21]
            slope = (sma_200 / past_sma - 1.0) if past_sma > 0 else nan
        else:
            slope = nan

        return {
            "ret_1d": self._ret(1),
            "ret_5d": self._ret(5),
            "ret_20d": self._ret(20),
            "ret_60d": self._ret(60),
            "rvol_10d": rvol_10,
            "rvol_20d": rvol_20,
            "rvol_60d": rvol_60,
            "rvol_ratio_10_60": (rvol_10 / rvol_60 if math.isfinite(rvol_10) and rvol_60 else nan),
            "rvol_20d_pctile_250d": pctile,
            "drawdown_from_high_250d": dd_250,
            "max_drawdown_20d": dd_20,
            "price_vs_sma_50": (last / sma_50 - 1.0) if sma_50 and sma_50 > 0 else nan,
            "price_vs_sma_200": (last / sma_200 - 1.0) if sma_200 and sma_200 > 0 else nan,
            "sma_50_vs_200": (
                sma_50 / sma_200 - 1.0 if sma_50 and sma_200 and sma_200 > 0 else nan
            ),
            "sma_200_slope_20d": slope,
            "atr_14_pct": atr_pct,
            "rsi_14": self._rsi.value,
            "down_day_frac_20d": down_frac,
            "gap_abs_mean_5d": gap_mean,
        }

    def record(self, high: float, low: float, close: float) -> dict[str, float]:
        """Vector for sessions strictly before this one, then fold it in."""
        vector = self._vector()

        if self._prev_close is not None and self._prev_close > 0 and close > 0:
            self._log_return.append(math.log(close / self._prev_close))
        if self._prev_close is not None:
            self._true_range.append(
                max(high - low, abs(high - self._prev_close), abs(low - self._prev_close))
            )
        else:
            self._true_range.append(high - low)

        self._close.append(close)
        self._high.append(high)
        self._low.append(low)
        self._prev_close = close
        self._rsi.update(close)
        self.sessions += 1

        rvol_20 = self._rvol(20)
        if math.isfinite(rvol_20):
            self._rvol_20_history.append(rvol_20)
        sma_200 = self._sma(200)
        if math.isfinite(sma_200):
            self._sma_200_history.append(sma_200)

        return vector


def _load_booster(path: Path) -> tuple[Any, dict] | None:
    """Booster + metadata, or None when the pair is absent.

    Absent is a legitimate configuration -- a deployment may want the
    volatility forecast without the crash classifier or the other way
    round -- so this returns None rather than raising. The CALLER
    decides whether the combination it ended up with is usable, which is
    where the error message can actually name what is missing.
    """
    meta_path = path.with_suffix(".json")
    if not path.exists() or not meta_path.exists():
        return None
    try:
        import lightgbm as lgb
    except ImportError as exc:
        # Lazy, exactly as src/ml/reachability_sizing.py does it: merely
        # importing this module (strategy_registry.py does, at startup)
        # must not require lightgbm. Only SELECTING a strategy that
        # loads a model does.
        raise ConfigurationError(
            "Regime inference needs lightgbm, which is not installed. Run: "
            "pip install -r requirements-ml.txt"
        ) from exc
    return lgb.Booster(model_file=str(path)), json.loads(meta_path.read_text())


class RegimeInferenceSource:
    """Owns the two boosters and the session clock they run on.

    Constructed by a strategy, driven from its record_tick. One instance
    per run -- it holds rolling state, so sharing one across two
    concurrent backtests would interleave their sessions.
    """

    def __init__(
        self,
        ticker: str,
        *,
        model_dir: Path | str = "data/ml/models",
        external_dir: Path | str | None = None,
        min_sessions: int = _MIN_SESSIONS,
    ) -> None:
        if not ticker:
            raise ConfigurationError("RegimeInferenceSource requires a ticker")
        self.ticker = ticker
        self.min_sessions = min_sessions

        directory = Path(model_dir)
        self._crash = _load_booster(directory / f"{ticker}_regime_crash.txt")
        self._fwdvol = _load_booster(directory / f"{ticker}_regime_fwdvol.txt")
        if self._crash is None and self._fwdvol is None:
            raise ConfigurationError(
                f"RegimeInferenceSource: no regime model for {ticker!r} under {directory}. "
                f"Expected {ticker}_regime_crash.txt/.json and/or "
                f"{ticker}_regime_fwdvol.txt/.json. Run: "
                f"python tools/train_qlib_regime.py --ticker {ticker}"
            )

        # Whether the vol block is part of the feature vector is a
        # property of the TRAINED MODEL, not a runtime choice -- reading
        # it from metadata is what stops a model trained on 34 columns
        # being fed 19 and scoring whatever it likes. Both models must
        # agree, since they share one feature vector.
        self._crash_booster = self._crash[0] if self._crash is not None else None
        self._fwdvol_booster = self._fwdvol[0] if self._fwdvol is not None else None
        metas = [pair[1] for pair in (self._crash, self._fwdvol) if pair is not None]
        self.uses_vol_block = bool(metas[0].get("uses_vol_block", False))
        for meta in metas[1:]:
            if bool(meta.get("uses_vol_block", False)) != self.uses_vol_block:
                raise ConfigurationError(
                    f"RegimeInferenceSource: {ticker}'s crash and fwdvol models disagree about "
                    "uses_vol_block. They share one feature vector, so one of them would be "
                    "scoring columns it never saw in training. Retrain both together."
                )
        self.horizon_sessions = int(metas[0].get("horizon_sessions", 20))
        self.crash_threshold = float(metas[0].get("crash_threshold", 0.10))
        # Quantiles of the crash head's own held-out output, recorded by
        # tools/train_qlib_regime.py. Empty for a model trained before
        # that existed; a consumer must treat empty as "unknown" and not
        # as "unreachable". See MLRegimeScaledSizing for what reads it
        # and why -- in short, a calibrated model on a 15% base rate
        # never emits 0.65, so a threshold picked by intuition silently
        # disables the feature.
        self.score_quantiles: dict[str, float] = (
            dict(self._crash[1].get("score_quantiles", {})) if self._crash is not None else {}
        )
        self._feature_order: list[str] = list(metas[0]["feature_columns"])

        self._external: dict = {}
        if self.uses_vol_block:
            wanted = [f for f in catalogue() if f.category == "vol"]
            source_dir = Path(external_dir) if external_dir else default_directory()
            self._external = transformed_sources(wanted, directory=source_dir)
            missing = set(VOL_BLOCK) - set(self._external)
            if missing:
                raise ConfigurationError(
                    f"RegimeInferenceSource: {ticker}'s models were trained WITH the volatility "
                    f"block but source files for {sorted(missing)} are missing under "
                    f"{source_dir}. Run: python tools/fetch_market_inputs.py --category vol"
                )

        self._features = DailyRegimeFeatures()
        self._session: date | None = None
        self._high = -math.inf
        self._low = math.inf
        self._close = math.nan
        self._reading = NO_READING

    @property
    def reading(self) -> RegimeReading:
        """The reading in force right now. Never None."""
        return self._reading

    def _predict(self, timestamp: datetime, vector: dict[str, float]) -> None:
        if self.uses_vol_block:
            for name in VOL_BLOCK:
                value = self._external[name].scalar(timestamp)
                vector[name] = float("nan") if value is None else value

        row = np.array(
            [[vector.get(n, float("nan")) for n in self._feature_order]], dtype=np.float64
        )

        crash = -1.0
        if self._crash_booster is not None:
            # num_threads=1 / validate_features=False for the reasons
            # src/ml/reachability_sizing.py records: this is ONE row, so
            # LightGBM's thread-pool dispatch is pure overhead, and the
            # column count is already guaranteed by construction because
            # _feature_order came from the sidecar the booster was saved
            # next to.
            crash = float(
                self._crash_booster.predict(row, num_threads=1, validate_features=False)[0]
            )
        fwdvol = -1.0
        if self._fwdvol_booster is not None:
            fwdvol = float(
                self._fwdvol_booster.predict(row, num_threads=1, validate_features=False)[0]
            )
            # A regression head can return a negative variance-like
            # quantity near the edge of its training support. Volatility
            # cannot be negative, and passing one on would collide with
            # the -1.0 "no reading" sentinel MarketContext uses.
            fwdvol = max(fwdvol, 0.0)

        self._reading = RegimeReading(
            crash_probability=min(max(crash, 0.0), 1.0) if crash >= 0.0 else -1.0,
            expected_volatility=fwdvol,
            as_of=self._session,
            warm=True,
        )

    def observe(self, timestamp: datetime, high: float, low: float, close: float) -> RegimeReading:
        """Fold one bar in; return the reading in force FOR that bar.

        Safe to call on every bar at any frequency. The models run only
        when the session changes, and the session that just ended is
        what feeds them -- so the reading returned for a bar in session
        D was computed from sessions <= D-1 and cannot see D's own
        close. That is the no-lookahead guarantee, and it is structural:
        a session is not scored until a bar from the next one arrives.
        """
        session = timestamp.astimezone(_NY).date() if timestamp.tzinfo else timestamp.date()

        if self._session is None:
            self._session = session
        elif session != self._session:
            # The previous session is complete. Fold it into the feature
            # state and, if warm enough, score the session now starting.
            vector = self._features.record(self._high, self._low, self._close)
            self._session = session
            if self._features.sessions >= self.min_sessions:
                self._predict(timestamp, vector)
            self._high, self._low = -math.inf, math.inf

        if high > self._high:
            self._high = high
        if low < self._low:
            self._low = low
        self._close = close
        return self._reading


__all__ = [
    "DAILY_FEATURES",
    "NO_READING",
    "VOL_BLOCK",
    "DailyRegimeFeatures",
    "RegimeInferenceSource",
    "RegimeReading",
]
