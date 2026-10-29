"""
Shared econometric tools for the catalog's allocation and statistical-
arbitrage entries: GARCH(1,1), DCC, the Kalman filter, Johansen
cointegration and the VECM, fractional differencing, VAR, OU half-life,
and copulas (Gaussian, Clayton, Gumbel) with a C-vine. statsmodels and
arch are not installed, so these are written out on numpy/scipy.

Sources:

  * GARCH -- Bollerslev, J. Econometrics 31, 1986; DCC -- Engle, "Dynamic
    conditional correlation", J. Bus. Econ. Stat. 20, 2002 (two-step QML).
  * Kalman filter -- Kalman, 1960; time-varying hedge ratio as a random-walk
    coefficient -- Chan, "Algorithmic Trading", Wiley 2013, ch. 3.
  * Johansen, "Statistical analysis of cointegration vectors", J. Econ.
    Dyn. Control 12, 1988; trace critical values (constant, det_order 0) as
    tabulated by MacKinnon, Haug & Michelis, J. Appl. Econometrics 14, 1999.
  * Fractional differencing -- Hosking, Biometrika 68, 1981; the GPH
    log-periodogram estimator of d -- Geweke & Porter-Hudak, J. Time Ser.
    Anal. 4, 1983; fixed-width window -- Lopez de Prado, "Advances in
    Financial Machine Learning", 2018, ch. 5.
  * Copulas -- Nelsen, "An Introduction to Copulas", 2006; C-vines,
    h-functions and the simulation algorithm -- Aas, Czado, Frigessi &
    Bakken, Insurance Math. Econ. 44, 2009; truncation as regularisation --
    Kraus & Czado, Comput. Stat. Data Anal. 110, 2017.
"""

from __future__ import annotations

import numpy as np
from scipy import stats
from scipy.optimize import minimize

from engine.core.exceptions import ConfigurationError

# ---------------------------------------------------------------- volatility


def garch11_filter(returns, omega: float, alpha: float, beta: float) -> np.ndarray:
    """Conditional variances s2_t = omega + alpha r_{t-1}^2 + beta s2_{t-1},
    started at the sample variance."""
    r = np.asarray(returns, float)
    s2 = np.empty(len(r))
    s2[0] = r.var()
    for t in range(1, len(r)):
        s2[t] = omega + alpha * r[t - 1] ** 2 + beta * s2[t - 1]
    return s2


def garch11_fit(returns) -> dict:
    """Gaussian QML for a zero-mean GARCH(1,1) (alpha + beta < 1)."""
    r = np.asarray(returns, float)
    var = r.var()

    def unpack(p):
        a, b = 1 / (1 + np.exp(-p[1])), 1 / (1 + np.exp(-p[2]))
        alpha, beta = a * b, (1 - a) * b * 0.999  # alpha + beta = b * (a + 0.999 (1 - a)) < 1
        return np.exp(p[0]), alpha, beta

    def nll(p):
        omega, alpha, beta = unpack(p)
        s2 = garch11_filter(r, omega, alpha, beta)
        return 0.5 * np.sum(np.log(2 * np.pi * s2) + r**2 / s2)

    res = minimize(
        nll,
        [np.log(0.05 * var), 0.0, 2.0],
        method="Nelder-Mead",
        options={"maxiter": 2000, "xatol": 1e-8, "fatol": 1e-10},
    )
    omega, alpha, beta = unpack(res.x)
    return {
        "omega": omega,
        "alpha": alpha,
        "beta": beta,
        "loglik": -res.fun,
        "variance": garch11_filter(r, omega, alpha, beta),
    }


def garch11_forecast(fit: dict, last_return: float, horizon: int = 1) -> np.ndarray:
    """h-step variance forecasts, mean-reverting to omega / (1 - alpha - beta)."""
    o, a, b = fit["omega"], fit["alpha"], fit["beta"]
    s2 = o + a * last_return**2 + b * fit["variance"][-1]
    out = [s2]
    for _ in range(horizon - 1):
        s2 = o + (a + b) * s2
        out.append(s2)
    return np.array(out)


def dcc_fit(std_resid) -> dict:
    """Engle's DCC on standardised residuals (rows = time):
    Q_t = (1 - a - b) Qbar + a e_{t-1} e_{t-1}' + b Q_{t-1}, R_t = Q_t normalised."""
    e = np.asarray(std_resid, float)
    qbar = np.cov(e.T, bias=True)

    def path(a, b):
        q = qbar.copy()
        rs = np.empty((len(e), *qbar.shape))
        for t in range(len(e)):
            if t:
                q = (1 - a - b) * qbar + a * np.outer(e[t - 1], e[t - 1]) + b * q
            d = 1 / np.sqrt(np.diag(q))
            rs[t] = q * np.outer(d, d)
        return rs

    def nll(p):
        a, b = 1 / (1 + np.exp(-p[0])), 1 / (1 + np.exp(-p[1]))
        a, b = a * b, (1 - a) * b * 0.999
        rs = path(a, b)
        _, logdet = np.linalg.slogdet(rs)
        quad = np.einsum("ti,tij,tj->t", e, np.linalg.inv(rs), e)
        return 0.5 * np.sum(logdet + quad)

    res = minimize(nll, [-2.0, 2.0], method="Nelder-Mead")
    a, b = 1 / (1 + np.exp(-res.x[0])), 1 / (1 + np.exp(-res.x[1]))
    a, b = a * b, (1 - a) * b * 0.999
    return {"a": a, "b": b, "correlations": path(a, b), "qbar": qbar}


# ---------------------------------------------------------------- state space


def kalman_filter(y, f, h, q, r, x0, p0) -> dict:
    """Linear Gaussian filter: x_t = F x_{t-1} + w (Q), y_t = H_t x_t + v (R).
    `h` may be one (k, n) matrix or a (T, k, n) array of time-varying ones."""
    y = np.atleast_2d(np.asarray(y, float).T).T
    f, q, r = np.atleast_2d(f), np.atleast_2d(q), np.atleast_2d(r)
    h = np.asarray(h, float)
    x, p = np.asarray(x0, float), np.atleast_2d(p0)
    xs, ps, innov, loglik = [], [], [], 0.0
    for t in range(len(y)):
        ht = h[t] if h.ndim == 3 else np.atleast_2d(h)
        x, p = f @ x, f @ p @ f.T + q
        v = y[t] - ht @ x
        s = ht @ p @ ht.T + r
        k = np.linalg.solve(s, ht @ p).T
        x, p = x + k @ v, (np.eye(len(x)) - k @ ht) @ p
        loglik -= 0.5 * (np.log(np.linalg.det(2 * np.pi * s)) + v @ np.linalg.solve(s, v))
        xs.append(x.copy())
        ps.append(p.copy())
        innov.append(v)
    return {
        "state": np.array(xs),
        "cov": np.array(ps),
        "innovation": np.array(innov),
        "loglik": float(loglik),
    }


def kalman_hedge_ratio(y, x, delta: float = 1e-4, obs_var: float = 1e-3) -> dict:
    """Time-varying regression y_t = beta_t x_t + alpha_t + v, (beta, alpha) a
    random walk with covariance delta / (1 - delta) I (Chan's pairs filter).
    Returns beta, alpha and the one-step forecast error and its variance."""
    x, y = np.asarray(x, float), np.asarray(y, float)
    hs = np.stack([np.column_stack([x, np.ones_like(x)])], axis=1)  # (T, 1, 2)
    out = kalman_filter(
        y[:, None],
        np.eye(2),
        hs,
        delta / (1 - delta) * np.eye(2),
        [[obs_var]],
        np.zeros(2),
        np.eye(2),
    )
    return {
        "beta": out["state"][:, 0],
        "alpha": out["state"][:, 1],
        "error": out["innovation"][:, 0],
    }


# ---------------------------------------------------------------- cointegration

# 90/95/99% trace critical values, constant (det_order 0), by n - r = 1..5.
_TRACE_CV = np.array(
    [
        [2.7055, 3.8415, 6.6349],
        [13.4294, 15.4943, 19.9349],
        [27.0669, 29.7961, 35.4628],
        [44.4929, 47.8545, 54.6815],
        [65.8202, 69.8189, 77.8202],
    ]
)


def _lagged_diffs(y, k):
    dy = np.diff(y, axis=0)
    rows = len(dy) - k
    z = [dy[k - i - 1 : k - i - 1 + rows] for i in range(k)]
    return dy[k:], y[k:-1], (np.column_stack(z) if z else np.empty((rows, 0)))


def johansen(y, k_ar_diff: int = 1) -> dict:
    """Johansen trace test with a constant: eigenvalues, trace statistics for
    r = 0..n-1, 95% critical values, the implied rank and the eigenvectors."""
    y = np.asarray(y, float)
    n = y.shape[1]
    if n > len(_TRACE_CV):
        raise ConfigurationError("critical values are tabulated for up to 5 series")
    dy, ylag, z = _lagged_diffs(y, k_ar_diff)
    z = np.column_stack([z, np.ones(len(dy))])

    def resid(a):
        return a - z @ np.linalg.lstsq(z, a, rcond=None)[0]

    r0, r1 = resid(dy), resid(ylag)
    t = len(dy)
    s00, s01, s11 = r0.T @ r0 / t, r0.T @ r1 / t, r1.T @ r1 / t
    m = np.linalg.solve(s11, s01.T @ np.linalg.solve(s00, s01))
    lam, vec = np.linalg.eig(m)
    order = np.argsort(-lam.real)
    lam, vec = lam.real[order], vec.real[:, order]
    trace = np.array([-t * np.log(1 - lam[r:]).sum() for r in range(n)])
    cv = _TRACE_CV[n - 1 - np.arange(n), 1]
    rank = int(np.argmax(trace < cv)) if (trace < cv).any() else n
    return {"eigenvalues": lam, "trace": trace, "crit_95": cv, "rank": rank, "vectors": vec}


def fit_vecm(y, rank: int, k_ar_diff: int = 1) -> dict:
    """VECM dy_t = alpha beta' y_{t-1} + sum Gamma_i dy_{t-i} + c + e with beta
    from Johansen and alpha, Gamma, c by OLS."""
    y = np.asarray(y, float)
    beta = johansen(y, k_ar_diff)["vectors"][:, :rank]
    dy, ylag, z = _lagged_diffs(y, k_ar_diff)
    x = np.column_stack([ylag @ beta, z, np.ones(len(dy))])
    coef = np.linalg.lstsq(x, dy, rcond=None)[0]
    return {
        "beta": beta,
        "alpha": coef[:rank].T,
        "gamma": coef[rank:-1].T,
        "const": coef[-1],
        "k_ar_diff": k_ar_diff,
    }


def vecm_forecast(model: dict, y, steps: int = 1) -> np.ndarray:
    y = list(np.asarray(y, float))
    k = model["k_ar_diff"]
    out = []
    for _ in range(steps):
        lags = [y[-1 - i] - y[-2 - i] for i in range(k)]
        dy = model["alpha"] @ (model["beta"].T @ y[-1]) + model["const"]
        if k:
            dy = dy + model["gamma"] @ np.concatenate(lags)
        y.append(y[-1] + dy)
        out.append(y[-1])
    return np.array(out)


def half_life(spread) -> float:
    """OU half-life from ds_t = a + b s_{t-1}: -log 2 / log(1 + b)."""
    s = np.asarray(spread, float)
    b = np.polyfit(s[:-1], np.diff(s), 1)[0]
    return float(-np.log(2) / np.log1p(b)) if -1 < b < -1e-10 else np.inf


# ---------------------------------------------------------------- long memory and VAR


def fracdiff_weights(d: float, size: int) -> np.ndarray:
    """Binomial weights of (1 - L)^d: w_0 = 1, w_k = -w_{k-1} (d - k + 1) / k."""
    w = [1.0]
    for k in range(1, size):
        w.append(-w[-1] * (d - k + 1) / k)
    return np.array(w)


def fracdiff(x, d: float, window: int = 50) -> np.ndarray:
    """Fixed-window fractional difference; NaN for the first window - 1 values."""
    x = np.asarray(x, float)
    w = fracdiff_weights(d, window)
    out = np.full(len(x), np.nan)
    for t in range(window - 1, len(x)):
        out[t] = w @ x[t - window + 1 : t + 1][::-1]
    return out


def gph_d(x, power: float = 0.5) -> float:
    """Geweke-Porter-Hudak: regress the log periodogram on -log(4 sin^2(f/2))
    over the m = n^power lowest Fourier frequencies; the slope is d."""
    x = np.asarray(x, float) - np.mean(x)
    n = len(x)
    m = int(n**power)
    freqs = 2 * np.pi * np.arange(1, m + 1) / n
    pgram = np.abs(np.fft.fft(x)[1 : m + 1]) ** 2 / (2 * np.pi * n)
    reg = -np.log(4 * np.sin(freqs / 2) ** 2)
    return float(np.polyfit(reg, np.log(pgram), 1)[0])


def fit_var(y, p: int = 1) -> dict:
    """VAR(p) by OLS: y_t = c + sum A_i y_{t-i} + e."""
    y = np.asarray(y, float)
    rows = len(y) - p
    x = np.column_stack([np.ones(rows)] + [y[p - i - 1 : p - i - 1 + rows] for i in range(p)])
    coef = np.linalg.lstsq(x, y[p:], rcond=None)[0]
    resid = y[p:] - x @ coef
    return {
        "const": coef[0],
        "lags": [coef[1 + i * y.shape[1] : 1 + (i + 1) * y.shape[1]].T for i in range(p)],
        "sigma": np.cov(resid.T),
    }


def var_forecast(model: dict, y, steps: int = 1) -> np.ndarray:
    hist = list(np.asarray(y, float))
    out = []
    for _ in range(steps):
        nxt = model["const"] + sum(a @ hist[-1 - i] for i, a in enumerate(model["lags"]))
        hist.append(nxt)
        out.append(nxt)
    return np.array(out)


# ---------------------------------------------------------------- copulas


def pseudo_observations(x) -> np.ndarray:
    """Ranks scaled into (0, 1): rank / (n + 1), column by column."""
    x = np.asarray(x, float)
    return stats.rankdata(x, axis=0) / (len(x) + 1)


def clayton_theta(tau: float) -> float:
    return 2 * tau / (1 - tau)


def gumbel_theta(tau: float) -> float:
    return 1 / (1 - tau)


def clayton_h(u, v, theta: float):
    """h(u | v) = dC(u, v)/dv for the Clayton copula."""
    u, v = np.clip(u, 1e-10, 1 - 1e-10), np.clip(v, 1e-10, 1 - 1e-10)
    return v ** (-theta - 1) * (u**-theta + v**-theta - 1) ** (-1 / theta - 1)


def clayton_h_inv(w, v, theta: float):
    """u with h(u | v) = w."""
    w, v = np.clip(w, 1e-10, 1 - 1e-10), np.clip(v, 1e-10, 1 - 1e-10)
    return ((w * v ** (theta + 1)) ** (-theta / (theta + 1)) + 1 - v**-theta) ** (-1 / theta)


def clayton_density(u, v, theta: float):
    u, v = np.clip(u, 1e-10, 1 - 1e-10), np.clip(v, 1e-10, 1 - 1e-10)
    return (1 + theta) * (u * v) ** (-theta - 1) * (u**-theta + v**-theta - 1) ** (-2 - 1 / theta)


def gumbel_cdf(u, v, theta: float):
    a = (-np.log(u)) ** theta + (-np.log(v)) ** theta
    return np.exp(-(a ** (1 / theta)))


def gaussian_copula_corr(u) -> np.ndarray:
    """Correlation of the normal scores of pseudo-observations."""
    return np.corrcoef(stats.norm.ppf(np.asarray(u, float)).T)


def fit_cvine(u, min_tau: float = 0.05) -> dict:
    """Clayton C-vine with the variable order as given (root first in each
    tree). Pair copulas with Kendall tau below `min_tau` are set to
    independence (theta = 0) -- the truncation that regularises the vine."""
    v = np.asarray(u, float)
    n = v.shape[1]
    theta = np.zeros((n, n))
    for j in range(n - 1):
        nxt = v.copy()
        for i in range(j + 1, n):
            tau = stats.kendalltau(v[:, j], v[:, i])[0]
            theta[j, i] = clayton_theta(tau) if tau >= min_tau else 0.0
            if theta[j, i] > 0:
                nxt[:, i] = clayton_h(v[:, i], v[:, j], theta[j, i])
        v = nxt
    return {"theta": theta, "n": n}


def simulate_cvine(vine: dict, size: int, rng=None) -> np.ndarray:
    """Aas et al.'s C-vine sampler: draw w ~ U(0,1)^n and invert the
    h-functions tree by tree."""
    rng = np.random.default_rng(rng)
    n, th = vine["n"], vine["theta"]
    w = rng.uniform(size=(size, n))
    x = np.empty_like(w)
    vv = np.zeros((size, n, n))
    x[:, 0] = vv[:, 0, 0] = w[:, 0]
    for i in range(1, n):
        vv[:, i, 0] = w[:, i]
        for k in range(i - 1, -1, -1):
            t = th[k, i]
            if t > 0:
                vv[:, i, 0] = clayton_h_inv(vv[:, i, 0], vv[:, k, k], t)
        x[:, i] = vv[:, i, 0]
        if i == n - 1:
            break
        for j in range(i):
            t = th[j, i]
            vv[:, i, j + 1] = clayton_h(vv[:, i, j], vv[:, j, j], t) if t > 0 else vv[:, i, j]
    return x


def empirical_quantile(sample, u) -> np.ndarray:
    """Map uniforms back through each column's empirical quantile function."""
    s = np.asarray(sample, float)
    return np.column_stack([np.quantile(s[:, j], u[:, j]) for j in range(s.shape[1])])
