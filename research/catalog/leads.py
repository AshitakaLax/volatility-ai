"""
The correction-strategy catalog's gap-analysis LEADS (ledger section 8A,
"Leads ... (not catalogued)"): searches the catalog named but did not
verify. Each is implemented from its standard reference so the database
covers them; none is wired in, and none has been measured here.

  * Online mean-reversion portfolios: OLMAR -- Li & Hoi, "On-Line
    Portfolio Selection with Moving Average Reversion", ICML 2012
    (Algorithm 1, epsilon = 10, window 5); PAMR -- Li, Zhao, Hoi &
    Gopalkrishnan, "PAMR: Passive aggressive mean reversion strategy for
    portfolio selection", Machine Learning 87, 2012 (epsilon = 0.5, C =
    500); simplex projection -- Duchi, Shalev-Shwartz, Singer & Chandra,
    ICML 2008.
  * Drawdown-constrained investing: CPPI -- Perold 1986; Black & Jones,
    "Simplifying portfolio insurance", JPM 1987; Grossman & Zhou,
    "Optimal investment strategies for controlling drawdowns",
    Mathematical Finance 3, 1993 (risky exposure proportional to
    W - alpha * max W).
  * HAR-RV -- Corsi, "A Simple Approximate Long-Memory Model of Realized
    Volatility", Journal of Financial Econometrics 7, 2009.
  * VIX term structure as a data-only regime input: the VIX/VIX3M ratio
    (backwardation above 1 marks stress).
  * Futures -> ETF lead-lag: lagged cross-correlation; Hayashi & Yoshida,
    "On covariance estimation of non-synchronously observed diffusion
    processes", Bernoulli 11, 2005; the shifted-HY lead-lag estimator of
    Hoffmann, Rosenbaum & Yoshida, Bernoulli 19, 2013.
  * Intraday periodicity -- Heston, Korajczyk & Sadka, "Intraday Patterns
    in the Cross-section of Stock Returns", Journal of Finance 65, 2010;
    overnight vs intraday -- Cliff, Cooper & Gulen, "Return differences
    between trading and non-trading hours", 2008.
  * Optimal execution (the Cartea-Jaimungal-Penalva and Gueant books both
    start here) -- Almgren & Chriss, "Optimal execution of portfolio
    transactions", Journal of Risk 3, 2000.
"""

from __future__ import annotations

import math

import numpy as np
import pandas as pd

from engine.core.exceptions import ConfigurationError

# ---------------------------------------------------------------- online portfolios


def project_to_simplex(v) -> np.ndarray:
    """Euclidean projection onto {b >= 0, sum b = 1} (Duchi et al.)."""
    v = np.asarray(v, dtype=float)
    u = np.sort(v)[::-1]
    css = np.cumsum(u)
    rho = np.nonzero(u * np.arange(1, len(v) + 1) > css - 1)[0][-1]
    theta = (css[rho] - 1) / (rho + 1.0)
    return np.maximum(v - theta, 0.0)


def olmar_weights(prices, epsilon: float = 10.0, window: int = 5) -> np.ndarray:
    """OLMAR: predict next price relatives as MA_window(p) / p_t, then move
    the portfolio the least distance that makes its predicted return at
    least epsilon: b += max(0, (eps - b.x~) / ||x~ - mean(x~)||^2) (x~ -
    mean(x~)), projected onto the simplex. Row t is the portfolio held over
    period t+1; uniform until a full window exists."""
    p = np.asarray(prices, dtype=float)
    t_n, m = p.shape
    b = np.full(m, 1.0 / m)
    out = np.zeros((t_n, m))
    for t in range(t_n):
        if t >= window - 1:
            x = p[t - window + 1 : t + 1].mean(axis=0) / p[t]
            dev = x - x.mean()
            denom = float(dev @ dev)
            lam = max(0.0, (epsilon - b @ x) / denom) if denom > 0 else 0.0
            b = project_to_simplex(b + lam * dev)
        out[t] = b
    return out


def pamr_weights(prices, epsilon: float = 0.5, variant: int = 0, c: float = 500.0) -> np.ndarray:
    """PAMR: after observing price relatives x_t, loss = max(0, b.x_t - eps);
    tau = loss / ||x_t - mean||^2 (PAMR), min(C, that) (PAMR-1) or
    loss / (||x_t - mean||^2 + 1/(2C)) (PAMR-2); b -= tau (x_t - mean),
    projected. A portfolio that just did well moves toward the losers."""
    p = np.asarray(prices, dtype=float)
    t_n, m = p.shape
    b = np.full(m, 1.0 / m)
    out = np.zeros((t_n, m))
    out[0] = b
    for t in range(1, t_n):
        x = p[t] / p[t - 1]
        dev = x - x.mean()
        denom = float(dev @ dev)
        loss = max(0.0, b @ x - epsilon)
        if variant == 0:
            tau = loss / denom if denom > 0 else 0.0
        elif variant == 1:
            tau = min(c, loss / denom) if denom > 0 else 0.0
        elif variant == 2:
            tau = loss / (denom + 1 / (2 * c))
        else:
            raise ConfigurationError("variant must be 0 (PAMR), 1 or 2")
        b = project_to_simplex(b - tau * dev)
        out[t] = b
    return out


def portfolio_wealth(prices, weights) -> np.ndarray:
    """Wealth of rebalancing to weights[t] at t's close (no costs)."""
    p = np.asarray(prices, dtype=float)
    rel = p[1:] / p[:-1]
    growth = np.einsum("ij,ij->i", np.asarray(weights)[:-1], rel)
    return np.r_[1.0, np.cumprod(growth)]


# ---------------------------------------------------------------- CPPI / Grossman-Zhou


def cppi_path(
    risky_returns,
    multiplier: float = 3.0,
    floor_fraction: float = 0.8,
    rf: float = 0.0,
    max_leverage: float = 1.0,
    ratchet_alpha: float | None = None,
) -> pd.DataFrame:
    """Constant-proportion portfolio insurance: at each rebalance hold
    E = clip(multiplier * (V - F), 0, max_leverage * V) in the risky asset,
    the rest at rf. The floor F starts at floor_fraction * V_0 and accrues
    rf; with ratchet_alpha it is max(that, alpha * running max of V) -- the
    Grossman-Zhou drawdown constraint (never below alpha of the peak, in
    continuous time)."""
    r = np.asarray(risky_returns, dtype=float)
    v, floor, peak = 1.0, floor_fraction, 1.0
    rows = []
    for x in r:
        if ratchet_alpha is not None:
            floor = max(floor, ratchet_alpha * peak)
        exposure = min(max(multiplier * (v - floor), 0.0), max_leverage * v)
        v = exposure * (1 + x) + (v - exposure) * (1 + rf)
        floor *= 1 + rf
        peak = max(peak, v)
        rows.append((v, exposure, floor))
    return pd.DataFrame(rows, columns=["value", "exposure", "floor"])


def grossman_zhou_multiplier(mu: float, r: float, sigma: float, risk_aversion: float) -> float:
    """Grossman-Zhou's cushion multiplier for CRRA utility: the Merton
    fraction (mu - r) / (gamma sigma^2) applied to the cushion W - alpha M."""
    if sigma <= 0 or risk_aversion <= 0:
        raise ConfigurationError("sigma and risk_aversion must be positive")
    return (mu - r) / (risk_aversion * sigma**2)


# ---------------------------------------------------------------- HAR-RV


def realized_variance(intraday_returns: pd.Series) -> pd.Series:
    """Daily realised variance: the sum of squared intraday returns per
    calendar day of the index."""
    s = pd.Series(intraday_returns, dtype=float)
    return (s**2).groupby(pd.DatetimeIndex(s.index).normalize()).sum()


def har_features(rv) -> pd.DataFrame:
    """Corsi's regressors at t: RV_t, mean of the last 5 and last 22 daily
    RVs (all including t), and the target RV_{t+1}."""
    s = pd.Series(rv, dtype=float).reset_index(drop=True)
    return pd.DataFrame(
        {
            "rv_d": s,
            "rv_w": s.rolling(5).mean(),
            "rv_m": s.rolling(22).mean(),
            "target": s.shift(-1),
        }
    )


def fit_har(rv) -> np.ndarray:
    """OLS of RV_{t+1} on [1, RV_d, RV_w, RV_m]; returns the coefficients."""
    f = har_features(rv).dropna()
    x = np.column_stack([np.ones(len(f)), f[["rv_d", "rv_w", "rv_m"]].to_numpy()])
    return np.linalg.lstsq(x, f["target"].to_numpy(), rcond=None)[0]


def har_forecast(rv, coef) -> float:
    """One-day-ahead HAR forecast from the latest daily, weekly, monthly RV."""
    f = har_features(rv).iloc[-1]
    return float(coef @ np.r_[1.0, f["rv_d"], f["rv_w"], f["rv_m"]])


# ---------------------------------------------------------------- VIX term structure


def vix_term_structure_regime(vix, vix3m, threshold: float = 1.0, smooth: int = 1) -> pd.DataFrame:
    """Risk-on while VIX / VIX3M (smoothed over `smooth` days) is below
    `threshold` -- contango; backwardation marks stress. The flag is lagged
    one day so a session trades on the prior close's curve."""
    ratio = (pd.Series(vix, dtype=float) / pd.Series(vix3m, dtype=float)).rolling(smooth).mean()
    risk_on = (ratio < threshold).astype(float).where(ratio.notna())
    return pd.DataFrame({"ratio": ratio, "risk_on": risk_on.shift(1)})


# ---------------------------------------------------------------- lead-lag


def lagged_cross_correlation(x, y, max_lag: int = 5) -> pd.Series:
    """corr(x_t, y_{t+k}) for k = -max_lag..max_lag; a peak at k > 0 means x
    leads y by k bars."""
    xs, ys = pd.Series(x, dtype=float), pd.Series(y, dtype=float)
    return pd.Series({k: xs.corr(ys.shift(-k)) for k in range(-max_lag, max_lag + 1)}, name="corr")


def hayashi_yoshida(tx, x, ty, y) -> float:
    """Hayashi-Yoshida covariance of two asynchronously observed price paths:
    sum of dx_i dy_j over every pair of observation intervals that
    overlap. tx/ty are increasing timestamps (numbers), x/y the prices."""
    tx, x, ty, y = (np.asarray(v, dtype=float) for v in (tx, x, ty, y))
    dx, dy = np.diff(x), np.diff(y)
    total, j0 = 0.0, 0
    for i in range(len(dx)):
        a0, a1 = tx[i], tx[i + 1]
        while j0 < len(dy) and ty[j0 + 1] <= a0:
            j0 += 1
        j = j0
        while j < len(dy) and ty[j] < a1:
            if min(a1, ty[j + 1]) > max(a0, ty[j]):
                total += dx[i] * dy[j]
            j += 1
    return total


def hy_lead_lag(tx, x, ty, y, shifts) -> tuple[float, dict]:
    """Hoffmann-Rosenbaum-Yoshida: shift y's clock by theta and maximise
    |HY correlation|; a positive best theta means x leads y by theta."""
    var_x = float(np.sum(np.diff(np.asarray(x, dtype=float)) ** 2))
    var_y = float(np.sum(np.diff(np.asarray(y, dtype=float)) ** 2))
    scores = {
        float(s): hayashi_yoshida(tx, x, np.asarray(ty, dtype=float) - s, y)
        / math.sqrt(var_x * var_y)
        for s in shifts
    }
    best = max(scores, key=lambda s: abs(scores[s]))
    return best, scores


# ---------------------------------------------------------------- intraday periodicity


def same_interval_signal(interval_returns, lookback_days: int = 20) -> pd.DataFrame:
    """Heston-Korajczyk-Sadka periodicity: the forecast for interval k of
    day d is the mean return of interval k over the previous lookback_days
    days. Rows are days, columns the intraday intervals (13 half-hours in
    a US session)."""
    r = pd.DataFrame(interval_returns, dtype=float)
    return r.rolling(lookback_days).mean().shift(1)


def overnight_intraday(open_, close) -> pd.DataFrame:
    """Split close-to-close returns into overnight (open_t / close_{t-1})
    and intraday (close_t / open_t) parts; (1 + on)(1 + id) = 1 + cc."""
    o, c = pd.Series(open_, dtype=float), pd.Series(close, dtype=float)
    on = o / c.shift(1) - 1
    intra = c / o - 1
    return pd.DataFrame({"overnight": on, "intraday": intra, "close_to_close": c / c.shift(1) - 1})


# ---------------------------------------------------------------- Almgren-Chriss


def almgren_chriss(
    shares: float,
    horizon: float,
    n_intervals: int,
    sigma: float,
    eta: float,
    gamma: float = 0.0,
    epsilon: float = 0.0,
    risk_aversion: float = 0.0,
) -> dict:
    """Almgren-Chriss optimal liquidation of `shares` over `horizon` in
    n_intervals steps of tau, with linear temporary impact eps sgn(n) + eta
    n/tau, permanent impact gamma n/tau and price volatility sigma:

        x_j = sinh(kappa (T - t_j)) / sinh(kappa T) * X,
        cosh(kappa tau) = 1 + tau^2 lambda sigma^2 / (2 eta~),
        eta~ = eta - gamma tau / 2,

    which is linear (TWAP) when lambda = 0. Returns the holdings
    trajectory, the trade list, and the expected cost E and variance V:
        E = gamma X^2 / 2 + eps sum|n_j| + eta~/tau sum n_j^2,
        V = sigma^2 tau sum_{j>=1} x_j^2."""
    tau = horizon / n_intervals
    eta_t = eta - 0.5 * gamma * tau
    if eta_t <= 0:
        raise ConfigurationError("need eta > gamma * tau / 2")
    t = np.arange(n_intervals + 1) * tau
    if risk_aversion > 0:
        kappa = math.acosh(1 + 0.5 * tau**2 * risk_aversion * sigma**2 / eta_t) / tau
        x = np.sinh(kappa * (horizon - t)) / math.sinh(kappa * horizon) * shares
    else:
        kappa = 0.0
        x = shares * (1 - t / horizon)
    n = -np.diff(x)
    cost = 0.5 * gamma * shares**2 + epsilon * np.abs(n).sum() + eta_t / tau * (n**2).sum()
    var = sigma**2 * tau * (x[1:] ** 2).sum()
    return {"holdings": x, "trades": n, "kappa": kappa, "expected_cost": cost, "variance": var}


def almgren_chriss_objective(
    holdings, horizon, sigma, eta, gamma=0.0, epsilon=0.0, risk_aversion=0.0
):
    """E + lambda V for an arbitrary holdings path (x_0 = X ... x_N = 0)."""
    x = np.asarray(holdings, dtype=float)
    tau = horizon / (len(x) - 1)
    n = -np.diff(x)
    eta_t = eta - 0.5 * gamma * tau
    cost = 0.5 * gamma * x[0] ** 2 + epsilon * np.abs(n).sum() + eta_t / tau * (n**2).sum()
    return cost + risk_aversion * sigma**2 * tau * (x[1:] ** 2).sum()
