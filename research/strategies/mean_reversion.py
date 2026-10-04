"""
Mean-reversion diagnostics and signals from the correction-strategy
catalog (docs/research/correction-strategies.md): C-MR4, C-MR2, C-MR1.

C-MR4  diagnostics, after letianzj/QuantResearch notebooks/mean_reversion.py:

  adf             augmented Dickey-Fuller t-statistic with a constant,
                  Delta y_t = a + g*y_{t-1} + sum_i c_i*Delta y_{t-i} + e_t,
                  lag chosen by AIC up to `maxlag` (the notebook calls
                  statsmodels' adfuller(series, 1)). Critical values from
                  MacKinnon (2010)'s response surface for one variable with a
                  constant: crit(T) = b0 + b1/T + b2/T^2 + b3/T^3.
  hurst_exponent  the notebook's estimator, verbatim:
                    tau = sqrt(std(x[lag:] - x[:-lag])) for lag in 2..99
                    H   = 2 * slope of log(tau) on log(lag)
                  H < 0.5 mean-reverting, ~0.5 random walk, > 0.5 trending.
  variance_ratio  Lo & MacKinlay (1988) VR(q) on overlapping q-period log
                  returns, with the homoskedastic z and the
                  heteroskedasticity-robust z* (the notebook uses cor='het').
  half_life       regress Delta y_t on y_{t-1} (with an intercept, as
                  sklearn's LinearRegression does): half-life = -ln 2 / slope.

C-MR2  Avellaneda & Lee, "Statistical Arbitrage in the US Equities Market",
       Quantitative Finance 10(7), 2010, Appendix A: regress the stock's
       returns on its sector ETF's over the window, cumulate the residuals
       X_k, fit X_{k+1} = a + b*X_k + zeta, and
           kappa = -ln(b) * 252,  m = a / (1 - b),
           sigma_eq = sqrt(var(zeta) / (1 - b^2)),  s = (X_end - m) / sigma_eq
       (X_end = 0 because OLS residuals sum to zero, so s = -m / sigma_eq).
       Long-only rules from the paper: open at s < -1.25, close at
       s > -0.50; trade only when kappa > 252 / (window / 2), i.e. the
       mean-reversion time is under half the estimation window.

C-MR1  short-term reversal as liquidity provision. Nagel, "Evaporating
       Liquidity", RFS 2012, uses the Lehmann / Lo-MacKinlay contrarian
       weights w_i = -(R_i,t-1 - R_m,t-1) / N (R_m the equal-weighted
       mean); Collin-Dufresne & Daniel (2014) weight past residual returns
       with an exponential decay of half-life ~2.4 days. `contrarian_weights`
       is the former and its long-only projection; `decayed_reversal_scores`
       the latter. Both look only at returns through the scoring bar.
"""

from __future__ import annotations

import math

import numpy as np
import pandas as pd

from engine.core.exceptions import ConfigurationError

# MacKinnon (2010) response-surface coefficients, one variable, constant
# ("c"): (b0, b1, b2, b3) per significance level.
MACKINNON_C = {
    "1%": (-3.43035, -6.5393, -16.786, -79.433),
    "5%": (-2.86154, -2.8903, -4.234, -40.040),
    "10%": (-2.56677, -1.5384, -2.809, 0.0),
}


def _ols(y: np.ndarray, x: np.ndarray) -> tuple[np.ndarray, np.ndarray, float]:
    """(beta, standard errors, rss) for y = x @ beta + e."""
    beta, *_ = np.linalg.lstsq(x, y, rcond=None)
    resid = y - x @ beta
    rss = float(resid @ resid)
    dof = y.size - x.shape[1]
    if dof <= 0:
        raise ConfigurationError("too few observations for the regression")
    cov = rss / dof * np.linalg.inv(x.T @ x)
    return beta, np.sqrt(np.diag(cov)), rss


def mackinnon_critical_values(nobs: int) -> dict[str, float]:
    """crit(T) = b0 + b1/T + b2/T^2 + b3/T^3 for each level."""
    t = float(nobs)
    return {k: b0 + b1 / t + b2 / t**2 + b3 / t**3 for k, (b0, b1, b2, b3) in MACKINNON_C.items()}


def _adf_design(y: np.ndarray, lag: int, start: int) -> tuple[np.ndarray, np.ndarray]:
    dy = np.diff(y)
    rows = range(start, dy.size)  # dy index t is y_{t+1} - y_t
    target = dy[start:]
    cols = [np.ones(len(rows)), y[start : dy.size]]
    for i in range(1, lag + 1):
        cols.append(dy[start - i : dy.size - i])
    return target, np.column_stack(cols)


def adf(series, maxlag: int = 1, autolag: bool = True) -> dict[str, object]:
    """{'stat', 'lag', 'nobs', 'critical_values'}. With autolag, AIC picks
    the lag in 0..maxlag on a common sample, then the chosen lag is refitted
    on its full sample (statsmodels' procedure)."""
    y = np.asarray(series, dtype=float)
    if not (isinstance(maxlag, int) and maxlag >= 0):
        raise ConfigurationError(f"maxlag must be an integer >= 0, got {maxlag!r}")
    if y.size < maxlag + 10:
        raise ConfigurationError("series too short for the ADF regression")
    lag = maxlag
    if autolag and maxlag > 0:
        best = None
        for p in range(maxlag + 1):
            target, x = _adf_design(y, p, maxlag)
            _, _, rss = _ols(target, x)
            n = target.size
            aic = n * math.log(rss / n) + 2 * x.shape[1]
            if best is None or aic < best[0]:
                best = (aic, p)
        lag = best[1]
    target, x = _adf_design(y, lag, lag)
    beta, se, _ = _ols(target, x)
    return {
        "stat": float(beta[1] / se[1]),
        "lag": lag,
        "nobs": target.size,
        "critical_values": mackinnon_critical_values(target.size),
    }


def hurst_exponent(series, max_lag: int = 100) -> float:
    """The notebook's lagged-difference estimator (lags 2..max_lag-1)."""
    x = np.asarray(series, dtype=float)
    if not (isinstance(max_lag, int) and max_lag >= 4) or x.size <= max_lag:
        raise ConfigurationError("need max_lag >= 4 and more points than max_lag")
    lags = range(2, max_lag)
    tau = [np.sqrt(np.std(np.subtract(x[lag:], x[:-lag]))) for lag in lags]
    poly = np.polyfit(np.log(lags), np.log(tau), 1)
    return float(poly[0] * 2.0)


def variance_ratio(log_prices, q: int) -> dict[str, float]:
    """Lo-MacKinlay VR(q) with overlapping returns: {'vr', 'z', 'z_het'}."""
    x = np.asarray(log_prices, dtype=float)
    if not (isinstance(q, int) and q >= 1):
        raise ConfigurationError(f"q must be an integer >= 1, got {q!r}")
    nq = x.size - 1
    if nq < 2 * q:
        raise ConfigurationError("series too short for this q")
    r = np.diff(x)
    mu = (x[-1] - x[0]) / nq
    var_a = float(((r - mu) ** 2).sum()) / (nq - 1)
    m = q * (nq - q + 1) * (1 - q / nq)
    var_c = float(((x[q:] - x[:-q] - q * mu) ** 2).sum()) / m
    vr = var_c / var_a
    if q == 1:
        return {"vr": vr, "z": 0.0, "z_het": 0.0}
    z = (vr - 1) / math.sqrt(2 * (2 * q - 1) * (q - 1) / (3 * q * nq))
    d = (r - mu) ** 2
    denom = float(d.sum()) ** 2
    theta = 0.0
    for j in range(1, q):
        delta = float((d[j:] * d[:-j]).sum()) / denom * nq
        theta += (2 * (q - j) / q) ** 2 * delta
    z_het = (vr - 1) / math.sqrt(theta / nq) if theta > 0 else 0.0
    return {"vr": vr, "z": z, "z_het": z_het}


def half_life(series) -> float:
    """-ln 2 / slope of Delta y_t on y_{t-1}; inf when there is no pull
    back toward a mean (slope >= 0)."""
    y = np.asarray(series, dtype=float)
    if y.size < 3:
        raise ConfigurationError("need at least 3 points")
    x = np.column_stack([np.ones(y.size - 1), y[:-1]])
    beta, _, _ = _ols(np.diff(y), x)
    slope = float(beta[1])
    return math.inf if slope >= 0 else -math.log(2) / slope


# ---------------------------------------------------------------- C-MR2


def s_score(stock_returns, etf_returns, periods_per_year: int = 252) -> dict[str, float]:
    """Avellaneda-Lee s-score over the given window (pass the last 60
    sessions for the paper's setting)."""
    r = np.asarray(stock_returns, dtype=float)
    i = np.asarray(etf_returns, dtype=float)
    if r.shape != i.shape or r.size < 10:
        raise ConfigurationError("need equal-length return windows of at least 10")
    beta, _, _ = _ols(r, np.column_stack([np.ones(r.size), i]))
    resid = r - (beta[0] + beta[1] * i)
    x = np.cumsum(resid)
    ab, _, _ = _ols(x[1:], np.column_stack([np.ones(x.size - 1), x[:-1]]))
    a, b = float(ab[0]), float(ab[1])
    if not 0 < b < 1:
        return {
            "beta": float(beta[1]),
            "a": a,
            "b": b,
            "kappa": 0.0,
            "m": math.nan,
            "sigma_eq": math.nan,
            "s": math.nan,
        }
    zeta = x[1:] - (a + b * x[:-1])
    kappa = -math.log(b) * periods_per_year
    m = a / (1 - b)
    sigma_eq = math.sqrt(float(np.var(zeta, ddof=1)) / (1 - b**2))
    return {
        "beta": float(beta[1]),
        "a": a,
        "b": b,
        "kappa": kappa,
        "m": m,
        "sigma_eq": sigma_eq,
        "s": (x[-1] - m) / sigma_eq,
    }


def s_score_long_signal(
    s: float,
    holding: bool,
    kappa: float,
    window: int = 60,
    open_below: float = -1.25,
    close_above: float = -0.50,
    periods_per_year: int = 252,
) -> str:
    """'open', 'close', 'hold' or 'none' for the long-only side."""
    fast_enough = kappa > periods_per_year / (window / 2)
    if not holding:
        return "open" if fast_enough and math.isfinite(s) and s < open_below else "none"
    return "close" if math.isfinite(s) and s > close_above else "hold"


# ---------------------------------------------------------------- C-MR1


def contrarian_weights(prior_returns: pd.Series, long_only: bool = False) -> pd.Series:
    """Lo-MacKinlay weights -(R_i - R_m)/N from the previous period's
    returns (long-short, summing to zero). long_only keeps the losers'
    side, rescaled to sum to 1."""
    r = prior_returns.astype(float)
    if r.size < 2:
        raise ConfigurationError("need at least two assets")
    w = -(r - r.mean()) / r.size
    if not long_only:
        return w
    pos = w.clip(lower=0.0)
    total = pos.sum()
    return pos / total if total > 0 else pos


def decayed_reversal_scores(
    residual_returns: pd.DataFrame, half_life: float = 2.4, formation: int = 5
) -> pd.DataFrame:
    """Score_t = sum_{k<formation} 0.5^(k / half_life) * e_{t-k} per asset;
    a LOW score is a recent loser (a reversal buy candidate)."""
    if not half_life > 0:
        raise ConfigurationError(f"half_life must be > 0, got {half_life}")
    if not (isinstance(formation, int) and formation >= 1):
        raise ConfigurationError(f"formation must be an integer >= 1, got {formation!r}")
    decay = 0.5 ** (1.0 / half_life)
    out = residual_returns * 0.0
    for k in range(formation):
        out = out + (decay**k) * residual_returns.shift(k)
    return out.where(residual_returns.shift(formation - 1).notna())
