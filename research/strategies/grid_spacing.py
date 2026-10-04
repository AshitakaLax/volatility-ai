"""
Volatility-scaled grid spacing -- catalog C-G3, "Grid Trading --
Simplified from GLFT" in nkaz001/hftbacktest's tutorials
(docs/research/correction-strategies.md, G3).

The tutorial drops the GLFT model's order-arrival calibration and sets the
grid interval in proportion to the short-term volatility of price
changes, never below a minimum interval. In this project's relative
terms (a step is a fraction of the reference price, as in
hf_local_reference's `reference * (1 - step)`):

    sigma_t = sample stdev of the last `window` one-bar log returns,
              scaled to `horizon_bars` by sqrt(horizon_bars)
    step_t  = max(round(vol_multiple * sigma_t / min_step) * min_step, min_step)
              capped at max_step if one is set

The rounding to a whole multiple of `min_step` is the tutorial's own
`grid_interval = max(np.round(half_spread * tick_size / min_grid_step) *
min_grid_step, min_grid_step)`, with sigma times `vol_multiple` standing
in for its `volatility * vol_to_half_spread`. `quantize=False` keeps the
unrounded value for callers that want a continuous step.

A correction raises sigma, so rungs widen on their own and the same
capital spans a deeper decline before it is fully deployed -- the
catalog's rank-1 drawdown lever, alongside S4's lot-size targeting (which
changes how BIG a lot is, not how FAR apart lots are).

WHAT IS LEFT OUT

The tutorial also centres the grid on the micro-price, which needs L1
quote sizes this project's minute bars do not carry (C-MS2 builds the
micro-price itself for when they exist), and aligns prices to the tick
grid, which a relative step does not need.

CAUSALITY

`VolatilityScaledStep.observe(close)` takes one completed bar. `sigma`
and `step` then describe returns through that bar, so a decision for the
NEXT bar that reads them uses no future data. `step_series` is the
vectorised reference: its value at bar t equals the tracker's after
observing bar t, which the tests pin.
"""

from __future__ import annotations

import math
from collections import deque

import numpy as np
import pandas as pd

from engine.core.exceptions import ConfigurationError


def _validate(
    window: int, vol_multiple: float, min_step: float, max_step: float | None, horizon_bars: int
) -> None:
    if not (isinstance(window, int) and window >= 2):
        raise ConfigurationError(f"window must be an integer >= 2, got {window!r}")
    if not vol_multiple > 0:
        raise ConfigurationError(f"vol_multiple must be > 0, got {vol_multiple}")
    if not 0 < min_step < 1:
        raise ConfigurationError(f"min_step must be in (0, 1), got {min_step}")
    if max_step is not None and not min_step <= max_step < 1:
        raise ConfigurationError(f"need min_step <= max_step < 1, got {min_step}, {max_step}")
    if not (isinstance(horizon_bars, int) and horizon_bars >= 1):
        raise ConfigurationError(f"horizon_bars must be an integer >= 1, got {horizon_bars!r}")


def volatility_scaled_step(
    sigma: float,
    vol_multiple: float,
    min_step: float,
    max_step: float | None = None,
    quantize: bool = True,
) -> float:
    """The tutorial's interval rule: vol_multiple * sigma rounded to a
    whole multiple of min_step (numpy's round-half-to-even, as the source
    uses), never below min_step; capped at max_step if one is set, so a
    single shock cannot push the next rung out of reach."""
    if sigma < 0 or not math.isfinite(sigma):
        raise ConfigurationError(f"sigma must be a finite value >= 0, got {sigma}")
    raw = vol_multiple * sigma
    if quantize:
        raw = float(np.round(raw / min_step)) * min_step
    step = max(min_step, raw)
    return step if max_step is None else min(max_step, step)


class VolatilityScaledStep:
    """Per-bar tracker of sigma and the volatility-scaled step.

    Holds the last `window` log returns. Until the window is full there is
    no estimate, and `step(base_step)` returns `base_step` unchanged --
    no estimate is not a low one."""

    def __init__(
        self,
        window: int = 30,
        vol_multiple: float = 1.0,
        min_step: float = 0.0005,
        max_step: float | None = None,
        horizon_bars: int = 1,
        quantize: bool = True,
    ):
        _validate(window, vol_multiple, min_step, max_step, horizon_bars)
        self.quantize = bool(quantize)
        self.window = window
        self.vol_multiple = float(vol_multiple)
        self.min_step = float(min_step)
        self.max_step = None if max_step is None else float(max_step)
        self.horizon_bars = horizon_bars
        self._returns: deque[float] = deque(maxlen=window)
        self._last_close: float | None = None

    def observe(self, close: float) -> None:
        """One completed bar's close. Non-positive prices are skipped."""
        if not (close > 0 and math.isfinite(close)):
            return
        if self._last_close is not None:
            self._returns.append(math.log(close / self._last_close))
        self._last_close = close

    @property
    def sigma(self) -> float | None:
        """Sample stdev (ddof=1) of the window's log returns, times
        sqrt(horizon_bars); None until `window` returns have been seen."""
        if len(self._returns) < self.window:
            return None
        return float(np.std(np.fromiter(self._returns, float), ddof=1)) * math.sqrt(
            self.horizon_bars
        )

    def step(self, base_step: float) -> float:
        """The volatility-scaled step, or `base_step` during warm-up."""
        sigma = self.sigma
        if sigma is None:
            return base_step
        return volatility_scaled_step(
            sigma, self.vol_multiple, self.min_step, self.max_step, self.quantize
        )


def step_series(
    closes: pd.Series,
    window: int = 30,
    vol_multiple: float = 1.0,
    min_step: float = 0.0005,
    max_step: float | None = None,
    horizon_bars: int = 1,
    quantize: bool = True,
) -> pd.Series:
    """Vectorised reference: the step after each bar (NaN during warm-up)."""
    _validate(window, vol_multiple, min_step, max_step, horizon_bars)
    returns = np.log(closes.astype(float)).diff()
    sigma = returns.rolling(window, min_periods=window).std(ddof=1) * math.sqrt(horizon_bars)
    raw = vol_multiple * sigma
    if quantize:
        raw = np.round(raw / min_step) * min_step
    step = raw.clip(lower=min_step)
    if max_step is not None:
        step = step.clip(upper=max_step)
    return step.where(sigma.notna())
