"""`ml_tft`: TemporalFusionTransformerSizer, grid buys sized by a Temporal
Fusion Transformer's quantile forecast.

--------------------------------------------------------------------
WHAT IT DECIDES, AND WHAT IT CANNOT

It answers one question per buy the grid has already triggered: how much.
It never decides to buy, never moves a target and never sells, so the
no-loss guard and the lot ledger are untouched -- a lot it sizes is held
until its target like every other lot. Every factor below lies in [0, 1]
and the result is clamped to `max_trade_pct` of equity
(_BaselineScaledStrategy), so no forecast can buy more than the
per-trade cap.

--------------------------------------------------------------------
FROM QUANTILES TO A SIZE

The TFT forecasts quantiles of the log price H bars ahead (its target is
log_close; research/ml/tft_features.py). Against the buy's entry price
they are quantiles of the lot's H-bar log return r.

1. Quantiles -> mean and standard deviation (`quantiles_to_moments`).

   For the three quantiles 10/50/90:

       mu    = 0.3 q10 + 0.4 q50 + 0.3 q90         (Swanson's 30-40-30 rule)
       sigma = (q90 - q10) / (2 z_0.9),  z_0.9 = Phi^-1(0.9) = 1.2815515655

   The sigma line is exact for a normal r, where q_p = mu + sigma z_p, so
   q90 - q10 = 2 z_0.9 sigma. The mean line is also exact for a normal r
   (the weights sum to 1 and the 10/90 terms cancel symmetrically), and
   for a skewed r it tracks the mean better than the median alone does:
   the extreme quantiles pull it toward the long tail (Hurst, Brown &
   Swanson 2000; Keefer & Bodily 1983 for three-point approximations).

   Any other set of levels is fitted to the same normal model by least
   squares on q_i = mu + sigma z_i, z_i = Phi^-1(p_i):

       sigma = sum (z_i - zbar)(q_i - qbar) / sum (z_i - zbar)^2
       mu    = qbar - sigma zbar

   which reduces to the line above when the levels are symmetric.
   Crossed quantiles (a network can emit q90 < q50) are sorted first, so
   sigma is never negative.

2. Precision-weighted confidence (`precision_weighted_confidence`):

       C = kelly_scale * mu / max(sigma, sigma_floor)^2,  clipped to [0, 1]

   mu weighted by the forecast's precision tau = 1 / sigma^2. For a
   normal return this is the growth-optimal (Kelly) fraction f* = mu /
   sigma^2 (Merton 1969; Thorp 2006), scaled by `kelly_scale` (0.5 is
   half-Kelly). Because sigma enters squared, a doubling of forecast
   uncertainty quarters the buy: allocations throttle as uncertainty
   spikes. mu <= 0 gives 0: no buy. Below `min_confidence` it is 0 too.

3. Drawdown decay (`drawdown_decay`), on the book rather than the price:

       D = exp(-(dd_decay * drawdown + duration_decay * sessions_underwater))

   drawdown is the engine's (peak equity - equity) / peak equity, and
   sessions_underwater counts the sessions since the book was last at a
   peak. A deep drawdown and a long one both taper buying power, and
   together they compound.

4. The allocation: equity * max_trade_pct * I * C * D, clamped to
   [0, equity * max_trade_pct], where I = exp(-inverse_scale_kappa *
   fall below the first price seen) is _BaselineScaledStrategy's inverse
   scaling. The engine's risk clamp applies after that, as for every
   strategy.

--------------------------------------------------------------------
THE ENCODER WINDOW AND THE LATENCY BUDGET

record_tick does O(1) work and allocates nothing: it writes the bar that
just completed into a pre-allocated ring of exactly the encoder length
(tft_features.CovariateRing). A forecast -- the only expensive step, a
TFT forward pass -- runs only when the grid has triggered a buy, at most
once per `refresh_bars` bars; between refreshes the last forecast is
reused against the new entry price. Until the ring holds a full encoder
window the sizer has no forecast and buys nothing.

At bar t the encoder ends at t-1 (bar t's high, low and close are not
known inside the bar under fill_model="intrabar"); the decoder starts at
t, with the known inputs of bars t .. t+H-1 read from the calendar and
the clock (tft_features.future_bar_times).

--------------------------------------------------------------------
IN SAMPLE IS REFUSED

The model is trained on bars before its `valid_from` (the training
cutoff plus the forecast horizon). A run that asks it about an earlier
bar would grade it on its own training data, so the first such bar
raises unless `allow_in_sample` is set; the backtest.yaml the trainer
writes starts at valid_from.

torch and pytorch-forecasting are loaded with the model, on the first
bar, never at import (research/ml/tft_model.py).
"""

from __future__ import annotations

import math
from collections.abc import Sequence
from statistics import NormalDist
from typing import Protocol

import numpy as np
import pandas as pd

from engine.core.exceptions import ConfigurationError
from engine.core.market_context import MarketContext
from research.ml.tft_features import (
    SOURCES,
    CovariateRing,
    PointInTimeSeries,
    future_bar_times,
    known_at,
)
from research.strategies.size_calculators import _BaselineScaledStrategy
from research.strategies.sizing_indicators import RollingMax, bars_from_days, clamp

DEFAULT_MODEL_DIR = "data/ml/models/tft_tqqq"
_Z90 = NormalDist().inv_cdf(0.9)  # 1.2815515655446004
_SWANSON = {0.1: 0.3, 0.5: 0.4, 0.9: 0.3}


def quantiles_to_moments(values: Sequence[float], levels: Sequence[float]) -> tuple[float, float]:
    """(mu, sigma) of a distribution given its quantiles at `levels`.
    See the module docstring, step 1, for the formulas."""
    q = np.sort(np.asarray(values, dtype=float))
    p = np.sort(np.asarray(levels, dtype=float))
    if q.shape != p.shape or q.size < 2:
        raise ConfigurationError("need at least two quantiles, one per level")
    if np.any((p <= 0) | (p >= 1)):
        raise ConfigurationError(f"quantile levels must be in (0, 1), got {list(levels)}")
    if p.size == 3 and np.allclose(p, (0.1, 0.5, 0.9)):
        mu = float(sum(w * v for w, v in zip(_SWANSON.values(), q, strict=True)))
        sigma = float((q[2] - q[0]) / (2.0 * _Z90))
        return mu, max(sigma, 0.0)
    z = np.array([NormalDist().inv_cdf(float(x)) for x in p])
    zc = z - z.mean()
    sigma = float((zc * (q - q.mean())).sum() / (zc * zc).sum())
    sigma = max(sigma, 0.0)
    return float(q.mean() - sigma * z.mean()), sigma


def precision_weighted_confidence(
    mu: float, sigma: float, kelly_scale: float, sigma_floor: float
) -> float:
    """clip(kelly_scale * mu / max(sigma, sigma_floor)^2, 0, 1)."""
    if not (math.isfinite(mu) and math.isfinite(sigma)):
        return 0.0
    s = max(sigma, sigma_floor)
    return clamp(kelly_scale * mu / (s * s), 0.0, 1.0)


def drawdown_decay(
    drawdown: float, sessions_underwater: int, dd_decay: float, duration_decay: float
) -> float:
    """exp(-(dd_decay * drawdown + duration_decay * sessions_underwater))."""
    exponent = dd_decay * max(0.0, drawdown) + duration_decay * max(0, sessions_underwater)
    return math.exp(-exponent)


class QuantileForecaster(Protocol):
    """What the sizer needs from a trained model (tft_model.TftForecaster)."""

    levels: tuple[float, ...]
    encoder_length: int
    prediction_length: int
    bars_per_day: int
    valid_from: pd.Timestamp | None
    sources: dict[str, str | None]

    def forecast(self, encoder: np.ndarray, decoder_known: np.ndarray) -> np.ndarray:
        """encoder: (encoder_length, len(ROW)) rows; decoder_known:
        (prediction_length, len(KNOWN)). Returns (prediction_length,
        len(levels)) quantiles of log_close."""
        ...


class TemporalFusionTransformerSizer(_BaselineScaledStrategy):
    """Grid buys sized by a TFT's quantile forecast. See module docstring."""

    def __init__(
        self,
        max_trade_pct: float,
        bars_per_day: int,
        model: str = DEFAULT_MODEL_DIR,
        kelly_scale: float = 0.5,
        sigma_floor: float = 1e-4,
        min_confidence: float = 0.0,
        dd_decay: float = 3.0,
        duration_decay: float = 0.01,
        refresh_bars: int = 1,
        lookback_days: float | None = None,
        macro_path: str = "",
        earnings_path: str = "",
        news_path: str = "",
        allow_in_sample: bool = False,
        baseline_price: float | None = None,
        inverse_scale_kappa: float = 0.0,
    ) -> None:
        super().__init__(max_trade_pct, baseline_price, inverse_scale_kappa)
        if bars_per_day < 1:
            raise ConfigurationError(f"bars_per_day must be >= 1, got {bars_per_day}")
        if not kelly_scale > 0:
            raise ConfigurationError(f"kelly_scale must be > 0, got {kelly_scale}")
        if not sigma_floor > 0:
            raise ConfigurationError(f"sigma_floor must be > 0, got {sigma_floor}")
        if not 0.0 <= min_confidence <= 1.0:
            raise ConfigurationError(f"min_confidence must be in [0, 1], got {min_confidence}")
        if dd_decay < 0 or duration_decay < 0:
            raise ConfigurationError("dd_decay and duration_decay must be >= 0")
        if not (isinstance(refresh_bars, int) and refresh_bars >= 1):
            raise ConfigurationError(f"refresh_bars must be an integer >= 1, got {refresh_bars!r}")
        if lookback_days is not None and lookback_days <= 0:
            raise ConfigurationError(f"lookback_days must be positive, got {lookback_days}")
        if not model:
            raise ConfigurationError("model must name a trained TFT directory")
        self.bars_per_day = bars_per_day
        self.model = model
        self.kelly_scale = kelly_scale
        self.sigma_floor = sigma_floor
        self.min_confidence = min_confidence
        self.dd_decay = dd_decay
        self.duration_decay = duration_decay
        self.refresh_bars = refresh_bars
        self.lookback_days = lookback_days
        self.macro_path = macro_path
        self.earnings_path = earnings_path
        self.news_path = news_path
        self.allow_in_sample = allow_in_sample
        # Loaded on the first bar (ensure_model_available), so construction,
        # the parameter schema and the server work without torch or a model.
        self._forecaster: QuantileForecaster | None = None
        self._ring: CovariateRing | None = None
        self._sources: dict[str, PointInTimeSeries] = {}
        self._pending: tuple | None = None
        self._rolling_high = (
            RollingMax(bars_from_days(lookback_days, bars_per_day))
            if lookback_days is not None
            else None
        )
        self._day: int | None = None
        self._underwater = 0
        self._forecast: np.ndarray | None = None
        self._forecast_bar = -(10**12)
        # Diagnostics of the last sizing decision.
        self.last_mu: float | None = None
        self.last_sigma: float | None = None
        self.last_confidence: float | None = None
        self.last_decay: float | None = None
        self.forecasts = 0

    # -- the model -------------------------------------------------------

    def _load_forecaster(self) -> QuantileForecaster:
        from research.ml.tft_model import TftForecaster

        return TftForecaster(self.model)

    def ensure_model_available(self) -> QuantileForecaster:
        """Load and check the model and its outside series (the first bar
        does this; a startup check may call it earlier)."""
        if self._forecaster is not None:
            return self._forecaster
        forecaster = self._load_forecaster()
        if int(forecaster.bars_per_day) != self.bars_per_day:
            raise ConfigurationError(
                f"{self.model} was trained on {forecaster.bars_per_day} bars a day; this run "
                f"has bars_per_day={self.bars_per_day}"
            )
        overrides = {
            "s_macro": self.macro_path,
            "s_earnings": self.earnings_path,
            "s_news": self.news_path,
        }
        paths = {}
        for name in SOURCES:
            trained = forecaster.sources.get(name)
            given = overrides[name] or trained
            if bool(trained) != bool(given):
                raise ConfigurationError(
                    f"{self.model} was trained {'with' if trained else 'without'} a {name} "
                    f"series; this run {'has one' if given else 'has none'}. The model must "
                    "see the inputs it was trained on."
                )
            paths[name] = given
        self._sources = {name: PointInTimeSeries(paths[name]) for name in SOURCES}
        self._ring = CovariateRing(int(forecaster.encoder_length))
        self._forecaster = forecaster
        return forecaster

    # -- the engine's calls ---------------------------------------------

    def live_history_sessions(self) -> int:
        """Enough regular-session history for a full encoder window (and the
        rolling high, when set), with a margin for missing minutes."""
        if self._forecaster is not None:
            encoder_length = self._forecaster.encoder_length
        else:  # asked before the first bar: the manifest says, without loading torch
            from research.ml.tft_model import read_manifest

            try:
                encoder_length = int(read_manifest(self.model)["encoder_length"])
            except (ConfigurationError, KeyError, ValueError):
                encoder_length = self.bars_per_day
        encoder_days = encoder_length / self.bars_per_day
        days = max(encoder_days, self.lookback_days or 0.0)
        return math.ceil(days * 1.25) + 2

    def record_tick(self, context: MarketContext) -> None:
        """O(1): fold the bar that completed into the ring, track the
        drawdown's duration, advance the rolling high."""
        self._capture_baseline(context.price)
        self.ensure_model_available()
        assert self._ring is not None
        if self._pending is not None:
            self._ring.push_bar(self._pending[0], self._pending[1], self._sources)
        self._pending = (context.timestamp, context.close)
        day = context.timestamp.toordinal()
        if context.drawdown <= 0:
            self._underwater = 0
        elif day != self._day:
            self._underwater += 1
        self._day = day
        if self._rolling_high is not None and context.price > 0:
            self._rolling_high.update(context.price)

    def _grid_trigger_level(
        self, context: MarketContext, last_buy_price: float, step: float
    ) -> float:
        """The last fill, or with lookback_days the higher of it and the
        rolling high (hf_local_reference's retrigger, which keeps a rising
        market from stranding the ladder)."""
        if self._rolling_high is None or self._rolling_high.value is None:
            return super()._grid_trigger_level(context, last_buy_price, step)
        return max(last_buy_price, self._rolling_high.value) * (1.0 - step)

    def _decoder_known(self, ts) -> np.ndarray:
        forecaster = self._forecaster
        assert forecaster is not None
        times = [ts, *future_bar_times(ts, forecaster.prediction_length - 1, self.bars_per_day)]
        return np.array([known_at(t) for t in times], dtype=np.float64)

    def _model_multiplier(self, context: MarketContext) -> float:
        forecaster = self.ensure_model_available()
        assert self._ring is not None
        if self._pending is None or not self._ring.full:
            self.last_confidence = None
            return 0.0  # no full encoder window yet: no forecast, no buy
        ts = self._pending[0]
        if not self.allow_in_sample and forecaster.valid_from is not None:
            bar = pd.Timestamp(ts)
            bar = bar.tz_localize("UTC") if bar.tzinfo is None else bar
            if bar < forecaster.valid_from:
                raise ConfigurationError(
                    f"{self.model} was trained on bars up to {forecaster.valid_from}; sizing a "
                    f"buy at {ts} would grade it on its own training data. Start the run at "
                    "valid_from (the backtest.yaml beside the model does), or set "
                    "allow_in_sample for a diagnostic run."
                )
        if self._forecast is None or context.bar_index - self._forecast_bar >= self.refresh_bars:
            quantiles = forecaster.forecast(self._ring.window(), self._decoder_known(ts))
            self._forecast = np.asarray(quantiles, dtype=float)[-1]
            self._forecast_bar = context.bar_index
            self.forecasts += 1
        if context.price <= 0:
            return 0.0
        returns = self._forecast - math.log(context.price)
        mu, sigma = quantiles_to_moments(returns, forecaster.levels)
        confidence = precision_weighted_confidence(mu, sigma, self.kelly_scale, self.sigma_floor)
        if confidence < self.min_confidence:
            confidence = 0.0
        decay = drawdown_decay(
            context.drawdown, self._underwater, self.dd_decay, self.duration_decay
        )
        self.last_mu, self.last_sigma = mu, sigma
        self.last_confidence, self.last_decay = confidence, decay
        return confidence * decay


__all__ = [
    "DEFAULT_MODEL_DIR",
    "QuantileForecaster",
    "TemporalFusionTransformerSizer",
    "drawdown_decay",
    "precision_weighted_confidence",
    "quantiles_to_moments",
]
