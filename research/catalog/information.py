"""
Information-theoretic and long-memory entries of the ranked list (ledger
RK202, RK221, RK257, RK264, RK386): transfer entropy and the strategies
built on it, and fractional-Brownian-motion trend scanning. None has a
trading study behind it (the pages say so); research code only.

Sources:

  * Transfer entropy -- Schreiber, "Measuring information transfer", Phys.
    Rev. Lett. 85, 2000; effective transfer entropy (minus the mean over
    shuffled sources) -- Marschinski & Kantz, EPJ B 30, 2002; in finance --
    Dimpfl & Peter, "Using transfer entropy to measure information flows
    between financial markets", Stud. Nonlinear Dyn. Econom. 17, 2013.
  * Trend scanning -- Lopez de Prado, "Machine Learning for Asset Managers",
    Cambridge 2020, ch. 5 (the horizon whose linear-trend t-value is largest
    in magnitude labels the trend).
  * Hurst exponent by detrended fluctuation analysis -- Peng et al., Phys.
    Rev. E 49, 1994; fBm simulation by Cholesky of its covariance
    0.5 (|t|^2H + |s|^2H - |t - s|^2H) -- Mandelbrot & Van Ness, SIAM Rev. 10, 1968.
  * Graph models on a TE network -- the simplified (linear, parameter-free
    propagation) graph convolution of Wu et al., ICML 2019, and a logistic
    contagion layer trained on the catalog's autodiff.
"""

from __future__ import annotations

import numpy as np

from engine.core.exceptions import ConfigurationError
from research.catalog.autodiff import Tensor, bce_with_logits, fit

# ---------------------------------------------------------------- transfer entropy


def _discretise(x, bins: int) -> np.ndarray:
    edges = np.quantile(x, np.linspace(0, 1, bins + 1)[1:-1])
    return np.searchsorted(edges, x)


def transfer_entropy(source, target, bins: int = 3, lag: int = 1) -> float:
    """TE_{X->Y} = sum p(y', y, x) log[p(y' | y, x) / p(y' | y)] in nats, with
    quantile bins and one-step histories."""
    x, y = (
        _discretise(np.asarray(source, float), bins),
        _discretise(np.asarray(target, float), bins),
    )
    yn, yp, xp = y[lag:], y[:-lag], x[:-lag]
    joint = np.zeros((bins, bins, bins))
    np.add.at(joint, (yn, yp, xp), 1)
    joint /= joint.sum()
    p_yp_xp = joint.sum(0)
    p_yn_yp = joint.sum(2)
    p_yp = joint.sum((0, 2))
    te = 0.0
    for a, b, c in zip(*np.nonzero(joint), strict=True):
        te += joint[a, b, c] * np.log(joint[a, b, c] * p_yp[b] / (p_yp_xp[b, c] * p_yn_yp[a, b]))
    return float(te)


def effective_transfer_entropy(source, target, bins: int = 3, shuffles: int = 50, rng=None) -> dict:
    """TE minus the mean TE of shuffled sources, and the share of shuffles
    at least as large (a permutation p-value)."""
    rng = np.random.default_rng(rng)
    te = transfer_entropy(source, target, bins)
    null = np.array(
        [transfer_entropy(rng.permutation(source), target, bins) for _ in range(shuffles)]
    )
    return {"te": te, "effective": te - null.mean(), "p_value": float((null >= te).mean())}


def te_matrix(series, bins: int = 3) -> np.ndarray:
    """A[i, j] = TE from column i to column j (zero diagonal)."""
    x = np.asarray(series, float)
    n = x.shape[1]
    out = np.zeros((n, n))
    for i in range(n):
        for j in range(n):
            if i != j:
                out[i, j] = transfer_entropy(x[:, i], x[:, j], bins)
    return out


# ---------------------------------------------------------------- strategies on TE


def te_lead_lag_positions(
    leader,
    follower,
    window: int = 250,
    bins: int = 3,
    threshold: float = 0.01,
    long_only: bool = True,
) -> np.ndarray:
    """RK221: when the trailing TE from leader to follower exceeds `threshold`
    nats, hold the follower in the direction of the leader's latest return
    (flat instead of short when long_only). Position t is held over t -> t+1
    and uses data up to t only."""
    a, b = np.asarray(leader, float), np.asarray(follower, float)
    pos = np.zeros(len(a))
    for t in range(window, len(a)):
        if transfer_entropy(a[t - window : t + 1], b[t - window : t + 1], bins) > threshold:
            side = np.sign(a[t])
            pos[t] = max(side, 0.0) if long_only else side
    return pos


def te_macro_allocation(macro, assets, bins: int = 3) -> dict:
    """RK257: information inflow I_j = sum_m TE(macro_m -> asset_j); the
    next-period forecast of each asset is an OLS on lagged macro; long-only
    weights proportional to I_j x max(forecast_j, 0)."""
    m, r = np.asarray(macro, float), np.asarray(assets, float)
    inflow = np.array(
        [
            sum(transfer_entropy(m[:, k], r[:, j], bins) for k in range(m.shape[1]))
            for j in range(r.shape[1])
        ]
    )
    x = np.column_stack([np.ones(len(m) - 1), m[:-1]])
    coef = np.linalg.lstsq(x, r[1:], rcond=None)[0]
    forecast = np.r_[1.0, m[-1]] @ coef
    score = inflow * np.clip(forecast, 0, None)
    w = score / score.sum() if score.sum() > 0 else np.zeros(r.shape[1])
    return {"inflow": inflow, "forecast": forecast, "weights": w}


def normalised_adjacency(a) -> np.ndarray:
    """Column-normalise a directed adjacency so incoming weights sum to one."""
    a = np.asarray(a, float).copy()
    np.fill_diagonal(a, 0.0)
    col = a.sum(0)
    return np.divide(a, col, out=np.zeros_like(a), where=col > 0)


class TEContagionModel:
    """RK264: P(shock_j at t+1) = sigmoid(b + w_self s_j,t + w_nb sum_i A_ij s_i,t)
    over the transfer-entropy graph A, where s marks returns below -k
    standard deviations. Trained by logistic likelihood on the autodiff."""

    def __init__(self):
        self.theta = Tensor(np.zeros(3), requires_grad=True)

    def _logits(self, s, a) -> Tensor:
        nb = s @ a  # (T, n): shock mass flowing into each node
        th = self.theta
        return th[0] + th[1] * Tensor(s) + th[2] * Tensor(nb)

    def fit(self, returns, adjacency, k: float = 2.0, steps: int = 300, lr: float = 0.05):
        r = np.asarray(returns, float)
        s = (r < -k * r.std(0)).astype(float)
        self.a, self.k, self.sd = normalised_adjacency(adjacency), k, r.std(0)
        return fit(
            lambda: bce_with_logits(self._logits(s[:-1], self.a), s[1:]), [self.theta], steps, lr
        )

    def shock_probability(self, last_returns) -> np.ndarray:
        s = (np.atleast_2d(last_returns) < -self.k * self.sd).astype(float)
        z = self._logits(s, self.a).data[0]
        return 1 / (1 + np.exp(-z))


def te_graph_alpha(returns, adjacency, hops: int = 2, top: int = 3) -> dict:
    """RK386: linear graph convolution on the TE graph. Features per stock:
    own return and its 1..hops-step neighbourhood averages (A' r, A'^2 r, ...);
    a pooled least-squares fit predicts next returns; hold the `top`
    highest-forecast stocks equally (long-only)."""
    r = np.asarray(returns, float)
    a = normalised_adjacency(adjacency)
    feats = [r]
    for _ in range(hops):
        feats.append(feats[-1] @ a)
    x = np.stack(feats, axis=2)  # (T, n, hops + 1)
    xs = x[:-1].reshape(-1, hops + 1)
    coef = np.linalg.lstsq(np.column_stack([np.ones(len(xs)), xs]), r[1:].reshape(-1), rcond=None)[
        0
    ]
    forecast = coef[0] + x[-1] @ coef[1:]
    w = np.zeros(r.shape[1])
    w[np.argsort(-forecast)[:top]] = 1.0 / top
    return {"coef": coef, "forecast": forecast, "weights": w}


# ---------------------------------------------------------------- long memory and trend scanning (RK202)


def simulate_fbm(n: int, hurst: float, rng=None) -> np.ndarray:
    """fBm at t = 1..n by Cholesky of its covariance (fine for n <~ 2000)."""
    if not 0 < hurst < 1:
        raise ConfigurationError("hurst must be in (0, 1)")
    t = np.arange(1, n + 1, dtype=float)
    cov = 0.5 * (
        t[:, None] ** (2 * hurst)
        + t[None] ** (2 * hurst)
        - np.abs(t[:, None] - t[None]) ** (2 * hurst)
    )
    return np.linalg.cholesky(cov + 1e-12 * np.eye(n)) @ np.random.default_rng(rng).normal(size=n)


def hurst_dfa(increments, scales=None) -> float:
    """DFA-1 Hurst exponent of an increment series (0.5 = no memory)."""
    x = np.asarray(increments, float)
    prof = np.cumsum(x - x.mean())
    scales = scales or np.unique(np.logspace(np.log10(8), np.log10(len(x) // 4), 12).astype(int))
    flucts = []
    for s in scales:
        segs = len(prof) // s
        f = []
        for k in range(segs):
            seg = prof[k * s : (k + 1) * s]
            t = np.arange(s)
            f.append(np.mean((seg - np.polyval(np.polyfit(t, seg, 1), t)) ** 2))
        flucts.append(np.sqrt(np.mean(f)))
    return float(np.polyfit(np.log(scales), np.log(flucts), 1)[0])


def trend_scan(prices, horizons=(5, 10, 20, 40)) -> dict:
    """Lopez de Prado's trend scanning (backward-looking for a live signal):
    the t-value of the OLS slope of the last h prices for each h; the label is
    the sign at the horizon with the largest |t|."""
    p = np.asarray(prices, float)
    tvals = {}
    for h in horizons:
        if h > len(p) or h < 3:
            continue
        y, t = p[-h:], np.arange(h, dtype=float)
        slope, icpt = np.polyfit(t, y, 1)
        resid = y - (slope * t + icpt)
        se = np.sqrt(resid @ resid / (h - 2) / ((t - t.mean()) ** 2).sum())
        tvals[h] = slope / se if se > 0 else np.sign(slope) * np.inf
    if not tvals:
        raise ConfigurationError("no horizon fits the series")
    best = max(tvals, key=lambda h: abs(tvals[h]))
    return {"horizon": best, "t": tvals[best], "tvalues": tvals}


def fbm_trend_positions(
    prices,
    window: int = 250,
    horizons=(5, 10, 20, 40),
    t_threshold: float = 2.0,
    h_threshold: float = 0.5,
) -> np.ndarray:
    """RK202: long when the trailing window's DFA Hurst exponent of log
    returns exceeds h_threshold (persistent, fBm-like) and trend scanning
    finds a significant up-trend; flat otherwise. Causal."""
    p = np.asarray(prices, float)
    pos = np.zeros(len(p))
    for t in range(window, len(p)):
        lp = np.log(p[t - window : t + 1])
        if hurst_dfa(np.diff(lp)) > h_threshold:
            scan = trend_scan(lp, horizons)
            pos[t] = float(scan["t"] > t_threshold)
    return pos
