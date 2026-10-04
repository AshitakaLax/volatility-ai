"""
Pairs relationships, long-only -- the unbuilt variant of catalog MR3
(docs/research/correction-strategies.md; ledger Q2 is the long/short form,
out of scope, and X3 its rotation form).

  engle_granger      Engle-Granger two-step: OLS hedge ratio y = a + b*x,
                     then an ADF test (constant, no lag augmentation by
                     default) on the residual, judged against MacKinnon
                     (2010)'s critical values for TWO variables -- the
                     residual's estimated hedge ratio makes the single-
                     series ADF table too lenient. je-suis-tm's Pair
                     trading backtest.py re-tests the relation on a rolling
                     window because, as its README warns, it breaks.
  KalmanHedgeRatio   letianzj/QuantResearch notebooks/pairs_trading_kalman_
                     filter.py, transcribed from its pykalman setup:
                       state (alpha, beta), transition = identity,
                       observation y_t = alpha_t + beta_t * x_t,
                       transition_covariance = 0.01^2 * I,
                       observation_covariance = 0.001,
                       initial mean ones(2), initial covariance ones((2, 2))
                     run as pykalman's `filter`: the first observation updates
                     the initial state directly; every later step predicts
                     (P <- P + Q) and then updates.
  spread_long_signal the catalog's long-only reading of the +/-1 sigma rule:
                     hold the cheap leg y while the standardised forecast
                     error is below -entry, release it once the error is back
                     at or above -exit.

TQQQ against QQQ is a poor pair (leverage decay drifts the spread); the
catalog says so and these functions do not pretend otherwise.
"""

from __future__ import annotations

import math

import numpy as np

from engine.core.exceptions import ConfigurationError
from research.strategies.mean_reversion import adf

# MacKinnon (2010) response surface, N = 2 variables, constant term.
MACKINNON_C_N2 = {
    "1%": (-3.89644, -10.9519, -22.527),
    "5%": (-3.33613, -6.1101, -6.823),
    "10%": (-3.04445, -4.2412, -2.720),
}


def engle_granger_critical_values(nobs: int) -> dict[str, float]:
    t = float(nobs)
    return {k: b0 + b1 / t + b2 / t**2 for k, (b0, b1, b2) in MACKINNON_C_N2.items()}


def engle_granger(y, x, maxlag: int = 0) -> dict[str, object]:
    """{'alpha', 'beta', 'stat', 'critical_values', 'cointegrated_5pct'}."""
    yv, xv = (np.asarray(a, dtype=float) for a in (y, x))
    if yv.shape != xv.shape or yv.size < 20:
        raise ConfigurationError("need two equal-length series of at least 20 points")
    design = np.column_stack([np.ones(xv.size), xv])
    (alpha, beta), *_ = np.linalg.lstsq(design, yv, rcond=None)
    resid = yv - (alpha + beta * xv)
    test = adf(resid, maxlag=maxlag, autolag=False)
    crit = engle_granger_critical_values(test["nobs"])
    return {
        "alpha": float(alpha),
        "beta": float(beta),
        "stat": test["stat"],
        "critical_values": crit,
        "cointegrated_5pct": test["stat"] < crit["5%"],
    }


class KalmanHedgeRatio:
    """Time-varying (alpha, beta) for y = alpha + beta * x."""

    def __init__(
        self,
        state_cov: float = 0.01**2,
        obs_cov: float = 0.001,
        initial_mean=(1.0, 1.0),
        initial_cov=None,
    ) -> None:
        if not state_cov >= 0 or not obs_cov > 0:
            raise ConfigurationError("need state_cov >= 0 and obs_cov > 0")
        self.Q = np.eye(2) * state_cov
        self.R = float(obs_cov)
        self.m = np.asarray(initial_mean, dtype=float)
        self.P = np.ones((2, 2)) if initial_cov is None else np.asarray(initial_cov, dtype=float)
        self._first = True
        self.error: float | None = None
        self.error_var: float | None = None

    @property
    def alpha(self) -> float:
        return float(self.m[0])

    @property
    def beta(self) -> float:
        return float(self.m[1])

    def update(self, y: float, x: float) -> tuple[float, float]:
        """One observation. Returns (forecast error e, its variance S):
        e = y - H m_pred, S = H P_pred H' + R, before the update."""
        if not self._first:
            self.P = self.P + self.Q  # predict: transition is the identity
        self._first = False
        h = np.array([1.0, x])
        error = y - h @ self.m
        s = float(h @ self.P @ h + self.R)
        gain = self.P @ h / s
        self.m = self.m + gain * error
        self.P = self.P - np.outer(gain, h) @ self.P
        self.error, self.error_var = float(error), s
        return float(error), s

    @property
    def z(self) -> float | None:
        """The last forecast error in standard deviations."""
        if self.error is None:
            return None
        return self.error / math.sqrt(self.error_var)


def spread_long_signal(z: float, holding: bool, entry: float = 1.0, exit_: float = 0.0) -> str:
    """'open' when z < -entry, 'close' when holding and z >= -exit_, else
    'hold' or 'none'. Long-only: y is held only when it is cheap to x."""
    if not entry > exit_ >= 0:
        raise ConfigurationError(f"need entry > exit_ >= 0, got {entry}, {exit_}")
    if not holding:
        return "open" if z < -entry else "none"
    return "close" if z >= -exit_ else "hold"
