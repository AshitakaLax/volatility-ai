"""
Covariance estimation on the manifold of symmetric positive-definite (SPD)
matrices, with graph attention and graph diffusion (ledger RK230, RK231,
RK232, RK233, RK235, RK237, RK266, RK267, RK396, RK400, RK404, RK406).

The pages note the common error in these titles: portfolio weights do not
live on the SPD manifold, the covariance matrix does. So every entry here
is a covariance estimator (or smoother) on the manifold followed by an
ordinary long-only allocation from research.catalog.allocation. None has
a finance study behind it; Ledoit-Wolf shrinkage and random-matrix
eigenvalue clipping are the classical baselines and are included.

Sources:

  * Affine-invariant metric, geodesics, log/exp maps and the Karcher mean --
    Pennec, Fillard & Ayache, Int. J. Comput. Vision 66, 2006; Moakher,
    SIAM J. Matrix Anal. Appl. 26, 2005. Log-Euclidean metric -- Arsigny et
    al., SIAM J. Matrix Anal. Appl. 29, 2007.
  * Bures-Wasserstein (Gelbrich) worst-case variance:
    max over W2(N(0, S'), N(0, S)) <= r of w'S'w = (sqrt(w'Sw) + r ||w||)^2 --
    Nguyen, Shafieezadeh-Abadeh, Kuhn & Mohajerin Esfahani, Math. Oper. Res.
    48, 2023 (Gelbrich ambiguity sets).
  * Graph attention -- Velickovic et al., "Graph attention networks", ICLR
    2018 (e_ij = LeakyReLU(a'[W h_i || W h_j]), softmax over neighbours).
  * Heat-kernel diffusion on a graph -- Kondor & Lafferty, ICML 2002.
  * Shrinkage -- Ledoit & Wolf, J. Multivariate Anal. 88, 2004 (sklearn);
    eigenvalue clipping at the Marchenko-Pastur edge -- Laloux, Cizeau,
    Bouchaud & Potters, Phys. Rev. Lett. 83, 1999.
  * Entropic risk -- Follmer & Schied, "Stochastic Finance", 2004.
"""

from __future__ import annotations

import numpy as np
from scipy.linalg import expm
from scipy.special import logsumexp
from sklearn.covariance import LedoitWolf

from engine.core.exceptions import ConfigurationError
from research.catalog.allocation import erc_weights, min_variance_weights, simplex_minimize
from research.catalog.autodiff import Tensor, fit, param, softmax, where

# ---------------------------------------------------------------- SPD geometry


def _eig_fn(a, fn) -> np.ndarray:
    vals, vecs = np.linalg.eigh((np.asarray(a, float) + np.asarray(a, float).T) / 2)
    return (vecs * fn(vals)) @ vecs.T


def spd_power(a, p: float) -> np.ndarray:
    return _eig_fn(a, lambda v: np.clip(v, 1e-300, None) ** p)


def spd_log(a) -> np.ndarray:
    return _eig_fn(a, lambda v: np.log(np.clip(v, 1e-300, None)))


def spd_exp(a) -> np.ndarray:
    return _eig_fn(a, np.exp)


def nearest_spd(a, floor: float = 1e-10) -> np.ndarray:
    """Clip eigenvalues to `floor` (projection onto the SPD cone)."""
    return _eig_fn(a, lambda v: np.clip(v, floor, None))


def airm_distance(a, b) -> float:
    """Affine-invariant distance ||log(A^-1/2 B A^-1/2)||_F."""
    ia = spd_power(a, -0.5)
    return float(np.linalg.norm(spd_log(ia @ b @ ia)))


def geodesic(a, b, t: float) -> np.ndarray:
    """Point at fraction t along the affine-invariant geodesic from A to B."""
    ra, ia = spd_power(a, 0.5), spd_power(a, -0.5)
    return ra @ spd_power(ia @ b @ ia, t) @ ra


def karcher_mean(mats, weights=None, iters: int = 50, tol: float = 1e-10) -> np.ndarray:
    """Weighted Frechet (Karcher) mean under the affine-invariant metric by the
    fixed point X <- X^1/2 exp(sum w_i log(X^-1/2 C_i X^-1/2)) X^1/2."""
    mats = [np.asarray(m, float) for m in mats]
    w = np.full(len(mats), 1.0 / len(mats)) if weights is None else np.asarray(weights, float)
    w = w / w.sum()
    x = sum(wi * m for wi, m in zip(w, mats, strict=True))
    for _ in range(iters):
        rx, ix = spd_power(x, 0.5), spd_power(x, -0.5)
        step = sum(wi * spd_log(ix @ m @ ix) for wi, m in zip(w, mats, strict=True))
        x = rx @ spd_exp(step) @ rx
        if np.linalg.norm(step) < tol:
            break
    return x


def log_euclidean_mean(mats, weights=None) -> np.ndarray:
    w = np.full(len(mats), 1.0 / len(mats)) if weights is None else np.asarray(weights, float)
    return spd_exp(sum(wi * spd_log(m) for wi, m in zip(w / w.sum(), mats, strict=True)))


def rolling_covariances(returns, window: int, step: int = 1) -> list[np.ndarray]:
    r = np.asarray(returns, float)
    return [np.cov(r[t - window : t].T) for t in range(window, len(r) + 1, step)]


# ---------------------------------------------------------------- classical baselines


def ledoit_wolf(returns) -> np.ndarray:
    return LedoitWolf().fit(np.asarray(returns, float)).covariance_


def cov_to_corr(cov) -> tuple[np.ndarray, np.ndarray]:
    sd = np.sqrt(np.diag(cov))
    return cov / np.outer(sd, sd), sd


def rmt_clip(corr, n_obs: int) -> np.ndarray:
    """RK267's classical form: eigenvalues of a correlation matrix below the
    Marchenko-Pastur edge (1 + sqrt(N/T))^2 are noise; replace them by their
    average (trace preserved) and reset the diagonal to 1."""
    c = np.asarray(corr, float)
    n = len(c)
    edge = (1 + np.sqrt(n / n_obs)) ** 2
    vals, vecs = np.linalg.eigh(c)
    noise = vals < edge
    if noise.any():
        vals = vals.copy()
        vals[noise] = vals[noise].mean()
    out = (vecs * vals) @ vecs.T
    d = np.sqrt(np.diag(out))
    return out / np.outer(d, d)


def log_spectral_shrinkage(cov, gamma: float) -> np.ndarray:
    """RK406's regulariser: shrink log-eigenvalues toward their mean by gamma
    (a geodesic step toward a multiple of the identity; stays SPD)."""
    vals, vecs = np.linalg.eigh(np.asarray(cov, float))
    lv = np.log(np.clip(vals, 1e-300, None))
    return (vecs * np.exp((1 - gamma) * lv + gamma * lv.mean())) @ vecs.T


def graph_heat_kernel(adjacency, t: float) -> np.ndarray:
    a = np.asarray(adjacency, float)
    lap = np.diag(a.sum(1)) - a
    return expm(-t * lap)


def graph_diffusion_covariance(cov, adjacency, t: float = 0.5, lam: float = 0.5) -> np.ndarray:
    """RK396: diffuse the correlation over the asset graph by congruence with
    the heat kernel (H C H' stays SPD), reset the diagonal, and move a
    fraction lam along the geodesic from the sample estimate toward it."""
    corr, sd = cov_to_corr(np.asarray(cov, float))
    h = graph_heat_kernel(adjacency, t)
    diff = h @ corr @ h.T
    d = np.sqrt(np.diag(diff))
    target = diff / np.outer(d, d) * np.outer(sd, sd)
    return geodesic(np.asarray(cov, float), target, lam)


# ---------------------------------------------------------------- graph attention shrinkage


def node_features(returns) -> np.ndarray:
    """Per-asset features for the attention layer, standardised: volatility,
    mean correlation, beta to the equal-weight book and mean return."""
    r = np.asarray(returns, float)
    corr = np.corrcoef(r.T)
    mkt = r.mean(1)
    beta = np.array([np.cov(r[:, i], mkt)[0, 1] / mkt.var() for i in range(r.shape[1])])
    f = np.column_stack([r.std(0), (corr.sum(1) - 1) / (len(corr) - 1), beta, r.mean(0)])
    return (f - f.mean(0)) / (f.std(0) + 1e-12)


class GATShrinkage:
    """RK232: a one-head graph-attention layer over the asset graph produces
    attention weights alpha; the shrinkage target is the attention-weighted
    average of neighbours' correlation rows (symmetrised, unit diagonal), and
    the estimate is (1 - lam) C + lam T. W, a and lam are trained so the
    estimate from the first part of a window predicts the sample correlation
    of the rest."""

    def __init__(self, n_features: int = 4, hidden: int = 4, seed: int = 0):
        rng = np.random.default_rng(seed)
        self.w = param((n_features, hidden), rng)
        self.a1, self.a2 = param((hidden, 1), rng), param((hidden, 1), rng)
        self.lam = Tensor(np.zeros(1), requires_grad=True)

    @property
    def params(self) -> list[Tensor]:
        return [self.w, self.a1, self.a2, self.lam]

    def attention(self, feats, adjacency=None) -> Tensor:
        n = len(feats)
        mask = np.ones((n, n), bool) if adjacency is None else (np.asarray(adjacency) > 0)
        mask = mask | np.eye(n, dtype=bool)
        z = Tensor(feats) @ self.w
        e = (z @ self.a1 + (z @ self.a2).T).leaky_relu(0.2)
        return softmax(where(mask, e, np.full((n, n), -1e9)), axis=1)

    def _estimate(self, corr, feats, adjacency=None) -> Tensor:
        n = len(corr)
        alpha = self.attention(feats, adjacency)
        t = alpha @ Tensor(corr)
        t = (t + t.T) * 0.5
        eye = np.eye(n)
        t = t * (1.0 - eye) + eye
        lam = self.lam.sigmoid()
        return Tensor(corr) * (1.0 - lam) + t * lam

    def fit(
        self, returns, split: float = 0.5, steps: int = 200, lr: float = 0.05, adjacency=None
    ) -> list[float]:
        r = np.asarray(returns, float)
        k = int(len(r) * split)
        if k < 3 or len(r) - k < 3:
            raise ConfigurationError("window too short to split into estimate and target")
        corr, feats = np.corrcoef(r[:k].T), node_features(r[:k])
        target = np.corrcoef(r[k:].T)
        return fit(
            lambda: ((self._estimate(corr, feats, adjacency) - target) ** 2).sum(),
            self.params,
            steps,
            lr,
        )

    def target(self, returns, adjacency=None) -> np.ndarray:
        """The attention target alone (correlation)."""
        r = np.asarray(returns, float)
        saved = self.lam.data.copy()
        self.lam.data[:] = 50.0
        out = self._estimate(np.corrcoef(r.T), node_features(r), adjacency).data
        self.lam.data[:] = saved
        return out

    def covariance(self, returns, adjacency=None) -> np.ndarray:
        r = np.asarray(returns, float)
        corr = self._estimate(np.corrcoef(r.T), node_features(r), adjacency).data
        sd = r.std(0, ddof=1)
        return nearest_spd(corr * np.outer(sd, sd))


def gat_dynamic_allocation(returns, window: int = 120, step: int = 20, **fit_kw) -> dict:
    """RK235: refit the attention shrinkage on each rolling window and hold
    the minimum-variance weights of its estimate until the next refit."""
    r = np.asarray(returns, float)
    out = {}
    for t in range(window, len(r) + 1, step):
        model = GATShrinkage()
        model.fit(r[t - window : t], **fit_kw)
        out[t] = min_variance_weights(model.covariance(r[t - window : t]))
    return out


def gat_spectral_covariance(model: GATShrinkage, returns) -> np.ndarray:
    """RK267: the attention-shrunk correlation, then Marchenko-Pastur clipping."""
    r = np.asarray(returns, float)
    corr, sd = cov_to_corr(model.covariance(r))
    return rmt_clip(corr, len(r)) * np.outer(sd, sd)


def gat_riemannian_shrinkage(model: GATShrinkage, returns, lam: float = 0.5) -> np.ndarray:
    """RK400: shrink along the geodesic from the sample covariance to the
    attention target (instead of the straight line), so the estimate stays SPD."""
    r = np.asarray(returns, float)
    sd = r.std(0, ddof=1)
    target = nearest_spd(model.target(r) * np.outer(sd, sd))
    return geodesic(nearest_spd(np.cov(r.T)), target, lam)


def gat_graph_diffusion_covariance(
    model: GATShrinkage, returns, t: float = 0.5, lam: float = 0.5
) -> np.ndarray:
    """RK404: graph diffusion with the learned attention (symmetrised) as the
    edge weights."""
    r = np.asarray(returns, float)
    alpha = model.attention(node_features(r)).data
    adj = (alpha + alpha.T) / 2
    np.fill_diagonal(adj, 0.0)
    return graph_diffusion_covariance(nearest_spd(np.cov(r.T)), adj, t, lam)


def gat_log_spectral_covariance(model: GATShrinkage, returns, gamma: float = 0.3) -> np.ndarray:
    """RK406: log-spectral shrinkage of the attention-shrunk estimate."""
    return log_spectral_shrinkage(model.covariance(returns), gamma)


# ---------------------------------------------------------------- allocations


def riemannian_min_variance(returns, window: int = 60, step: int = 20) -> np.ndarray:
    """RK230: Karcher mean of the rolling covariances, then minimum variance."""
    return min_variance_weights(karcher_mean(rolling_covariances(returns, window, step)))


def geodesic_smoothed_covariances(
    returns, window: int = 60, alpha: float = 0.2, step: int = 1
) -> list[np.ndarray]:
    """Exponential smoothing along geodesics: C_t = geodesic(C_{t-1}, S_t, alpha)."""
    covs = rolling_covariances(returns, window, step)
    out = [covs[0]]
    for s in covs[1:]:
        out.append(geodesic(out[-1], s, alpha))
    return out


def metric_diffusion_risk_parity(
    returns, window: int = 60, alpha: float = 0.2, step: int = 5
) -> np.ndarray:
    """RK231: equal-risk-contribution weights on the geodesically smoothed
    covariance, one row per rebalance."""
    return np.array(
        [erc_weights(c) for c in geodesic_smoothed_covariances(returns, window, alpha, step)]
    )


def gelbrich_worst_variance(w, cov, radius: float) -> float:
    w = np.asarray(w, float)
    return float((np.sqrt(w @ cov @ w) + radius * np.linalg.norm(w)) ** 2)


def riemannian_wdro_weights(returns, radius: float, window: int = 60, step: int = 20) -> np.ndarray:
    """RK233: minimise the Gelbrich (Bures-Wasserstein) worst-case variance
    around the Karcher-mean covariance."""
    c = karcher_mean(rolling_covariances(returns, window, step))
    return simplex_minimize(lambda w: gelbrich_worst_variance(w, c, radius), len(c))


def entropic_risk(portfolio_returns, theta: float) -> float:
    """rho(X) = (1/theta) log E[exp(-theta X)]."""
    x = np.asarray(portfolio_returns, float)
    return float((logsumexp(-theta * x) - np.log(len(x))) / theta)


def entropic_weights(returns, theta: float = 10.0) -> np.ndarray:
    """Minimise the empirical entropic risk of the portfolio (convex in w)."""
    r = np.asarray(returns, float)
    return simplex_minimize(lambda w: entropic_risk(r @ w, theta), r.shape[1])


def riemannian_entropic_weights(
    returns, theta: float = 10.0, window: int = 60, step: int = 20
) -> np.ndarray:
    """RK266: Gaussian entropic risk -mu'w + theta/2 w'Cw with the Karcher-mean
    covariance (the manifold enters through the covariance estimate)."""
    r = np.asarray(returns, float)
    mu, c = r.mean(0), karcher_mean(rolling_covariances(r, window, step))
    return simplex_minimize(lambda w: -mu @ w + 0.5 * theta * w @ c @ w, len(mu))


def riemannian_gat_weights(returns, lam: float = 0.5, **fit_kw) -> np.ndarray:
    """RK237: fit the attention shrinkage, take the geodesic estimate (RK400),
    and allocate by minimum variance."""
    model = GATShrinkage()
    model.fit(returns, **fit_kw)
    return min_variance_weights(gat_riemannian_shrinkage(model, returns, lam))
