"""
Cross-sectional alpha models of the ranked list (ledger RK98, RK318,
RK326, RK327, RK328, RK330, RK380, RK381, RK382, RK384, RK385, RK388,
RK394). Each ranks a universe of stocks, which needs point-in-time
universe data the project does not have; research code only. Long-only
selections hold the top names equally.

Sources:

  * GCN stock ranking -- Feng et al., "Temporal relational ranking for stock
    prediction", ACM TOIS 37, 2019; graph convolution -- Kipf & Welling, ICLR
    2017.
  * Hyperbolic graph networks -- Chami, Ying, Re & Leskovec, "Hyperbolic graph
    convolutional neural networks", NeurIPS 2019 (Poincare-ball exp/log maps
    at the origin, aggregation in the tangent space); for stocks -- Sawhney
    et al., "Exploring the scale-free nature of stock markets: hyperbolic
    graph learning for algorithmic trading", WWW 2021.
  * Diffusion convolution -- Li, Yu, Shahabi & Liu, "DCRNN", ICLR 2018
    (forward and backward random-walk powers of a directed graph).
  * Customer momentum -- Cohen & Frazzini, "Economic links and predictable
    returns", J. Finance 63, 2008; attention -- Velickovic et al., ICLR 2018.
  * FactorVAE -- Duan et al., "FactorVAE: a probabilistic dynamic factor model
    based on variational autoencoder for predicting cross-sectional stock
    returns", AAAI 2022 (portfolio layer, posterior encoder, attention prior,
    alpha + beta f decoder). RK380's "FactorGNN" has no paper; this is its
    nearest published relative.
  * Domain-adversarial training (gradient reversal) -- Ganin et al., JMLR 17,
    2016; for cross-market momentum (RK98) the domains are markets/regimes.
  * Contractive autoencoders -- Rifai et al., ICML 2011 (penalty
    ||J_encoder||_F^2, closed form for a sigmoid layer).
  * Quantile networks -- Taylor, J. Forecasting 19, 2000; non-crossing via
    cumulative softplus increments; Gaussian copula on the probability
    integral transforms.
  * Fourier neural operators -- Li et al., ICLR 2021 (spectral features);
    gradient boosting -- Friedman, Ann. Statist. 29, 2001.
  * Signature trading -- Futter, Horvath & Wiese, "Signature trading: a
    path-dependent extension of the mean-variance framework with exogenous
    signals", arXiv:2308.15135, 2023 (positions linear in the signature;
    mean-variance optimal coefficients (1 / 2 lambda) Sigma^-1 mu).
  * Rough volatility -- Gatheral, Jaisson & Rosenbaum, "Volatility is rough",
    Quantitative Finance 18, 2018 (H from E|log v_{t+D} - log v_t|^q ~ D^{qH}).
"""

from __future__ import annotations

import numpy as np
from scipy import stats

from engine.core.exceptions import ConfigurationError
from research.catalog.autodiff import (
    MLP,
    Tensor,
    concat,
    dft_matrices,
    fit,
    log_softmax,
    mse,
    param,
    softmax,
    where,
)
from research.catalog.econometrics import pseudo_observations
from research.catalog.point_processes import path_signature_features


def top_k_weights(scores, k: int) -> np.ndarray:
    s = np.asarray(scores, float)
    w = np.zeros(len(s))
    w[np.argsort(-s)[:k]] = 1.0 / k
    return w


def norm_adjacency(adjacency, self_loops: bool = True) -> np.ndarray:
    """Symmetric normalisation D^-1/2 (A + I) D^-1/2."""
    a = np.asarray(adjacency, float) + (np.eye(len(adjacency)) if self_loops else 0)
    d = 1 / np.sqrt(np.maximum(a.sum(1), 1e-12))
    return d[:, None] * a * d[None, :]


# ---------------------------------------------------------------- GCN ranking (RK318)


class GCNRanker:
    """Two graph-convolution layers: H = relu(A X W1), y = A H W2. Trained on
    (features_t, returns_{t+1}) panels by mean squared error."""

    def __init__(self, n_features: int, hidden: int = 8, seed: int = 0):
        rng = np.random.default_rng(seed)
        self.w1, self.w2 = param((n_features, hidden), rng), param((hidden, 1), rng)

    def scores(self, features, adjacency) -> Tensor:
        a = Tensor(norm_adjacency(adjacency))
        h = (a @ Tensor(np.asarray(features, float)) @ self.w1).relu()
        return (a @ h @ self.w2)[..., 0]

    def fit(self, features, next_returns, adjacency, steps: int = 300, lr: float = 0.02):
        """features (T, n, f), next_returns (T, n)."""
        y = np.asarray(next_returns, float)
        return fit(lambda: mse(self.scores(features, adjacency), y), [self.w1, self.w2], steps, lr)

    def select(self, features, adjacency, k: int) -> np.ndarray:
        return top_k_weights(self.scores(features, adjacency).data, k)


# ---------------------------------------------------------------- hyperbolic GNN (RK381, RK384)


def _artanh(x: Tensor) -> Tensor:
    x = x.clip(-1 + 1e-6, 1 - 1e-6)
    return ((1.0 + x) / (1.0 - x)).log() * 0.5


def expmap0(v: Tensor, c: float = 1.0) -> Tensor:
    """Exponential map at the origin of the Poincare ball of curvature -c."""
    n = ((v * v).sum(axis=-1, keepdims=True) + 1e-12).sqrt()
    return (n * np.sqrt(c)).tanh() * v / (n * np.sqrt(c))


def logmap0(y: Tensor, c: float = 1.0) -> Tensor:
    n = ((y * y).sum(axis=-1, keepdims=True) + 1e-12).sqrt()
    return _artanh(n * np.sqrt(c)) * y / (n * np.sqrt(c))


class HyperbolicGCN:
    """HGCN: embed features on the Poincare ball, apply hyperbolic linear maps
    (log -> linear -> exp), aggregate neighbours in the tangent space at the
    origin with attention, and read a score from the tangent vector."""

    def __init__(self, n_features: int, hidden: int = 8, c: float = 1.0, seed: int = 0):
        rng = np.random.default_rng(seed)
        self.c = c
        self.w1, self.w2 = param((n_features, hidden), rng), param((hidden, hidden), rng)
        self.att = param((2 * hidden, 1), rng)
        self.out = param((hidden, 1), rng)

    @property
    def params(self) -> list[Tensor]:
        return [self.w1, self.w2, self.att, self.out]

    def scores(self, features, adjacency) -> Tensor:
        x = np.asarray(features, float)
        mask = (np.asarray(adjacency) > 0) | np.eye(len(adjacency), dtype=bool)
        h = expmap0(Tensor(x) @ self.w1 * 0.1, self.c)  # points on the ball (..., n, hidden)
        t = logmap0(h, self.c) @ self.w2  # hyperbolic linear map, kept in the tangent space
        n = t.shape[-2]
        hidden = t.shape[-1]
        left = (t @ self.att[:hidden]).reshape(*t.shape[:-1], 1)
        right = (t @ self.att[hidden:]).reshape(*t.shape[:-2], 1, n)
        e = (left + right).leaky_relu(0.2)
        alpha = softmax(where(np.broadcast_to(mask, e.shape), e, np.full(e.shape, -1e9)), axis=-1)
        agg = expmap0(alpha @ t, self.c)  # aggregated, mapped back to the ball
        return (logmap0(agg, self.c).tanh() @ self.out)[..., 0]

    def fit(self, features, next_returns, adjacency, steps: int = 300, lr: float = 0.02):
        y = np.asarray(next_returns, float)
        return fit(lambda: mse(self.scores(features, adjacency), y), self.params, steps, lr)


# ---------------------------------------------------------------- diffusion convolution (RK394)


def diffusion_features(returns, adjacency, k: int = 2) -> np.ndarray:
    """Own value plus forward (D_out^-1 A)^j and backward (D_in^-1 A')^j
    random-walk propagations, j = 1..k: shape (T, n, 2k + 1)."""
    r = np.asarray(returns, float)
    a = np.asarray(adjacency, float)
    fwd = np.divide(
        a, a.sum(1, keepdims=True), out=np.zeros_like(a), where=a.sum(1, keepdims=True) > 0
    )
    bwd = np.divide(
        a.T, a.T.sum(1, keepdims=True), out=np.zeros_like(a), where=a.T.sum(1, keepdims=True) > 0
    )
    feats, pf, pb = [r], r, r
    for _ in range(k):
        pf, pb = pf @ fwd.T, pb @ bwd.T
        feats += [pf, pb]
    return np.stack(feats, axis=2)


def diffusion_conv_alpha(returns, adjacency, k: int = 2, top: int = 3) -> dict:
    """RK394: a linear diffusion-convolution layer fitted by pooled least
    squares to next returns; hold the top forecasts."""
    x = diffusion_features(returns, adjacency, k)
    r = np.asarray(returns, float)
    xs = x[:-1].reshape(-1, x.shape[2])
    coef = np.linalg.lstsq(np.column_stack([np.ones(len(xs)), xs]), r[1:].reshape(-1), rcond=None)[
        0
    ]
    forecast = coef[0] + x[-1] @ coef[1:]
    return {"coef": coef, "forecast": forecast, "weights": top_k_weights(forecast, top)}


# ---------------------------------------------------------------- supply chain (RK385)


def customer_momentum(returns, customer_weights) -> np.ndarray:
    """Cohen-Frazzini signal: each firm's weighted average of its customers'
    latest returns (rows of customer_weights = the firm's sales shares)."""
    w = np.asarray(customer_weights, float)
    w = np.divide(
        w, w.sum(1, keepdims=True), out=np.zeros_like(w), where=w.sum(1, keepdims=True) > 0
    )
    return np.asarray(returns, float) @ w.T


class SupplyChainGAT:
    """RK385: attention over each firm's economic links (customers and
    suppliers) weights its partners' lagged returns; prediction =
    a * own lagged return + b * attended partner return."""

    def __init__(self, seed: int = 0):
        rng = np.random.default_rng(seed)
        self.att = param((2, 1), rng)
        self.coef = Tensor(np.zeros(3), requires_grad=True)

    def predict(self, lagged, links) -> Tensor:
        """lagged (T, n) returns, links (n, n) adjacency; returns (T, n)."""
        r = Tensor(np.asarray(lagged, float))
        mask = np.asarray(links) > 0
        t, n = r.shape
        left = r.reshape(t, n, 1) * self.att[0, 0]
        right = r.reshape(t, 1, n) * self.att[1, 0]
        e = (left + right).leaky_relu(0.2)
        m = np.broadcast_to(mask, (t, n, n))
        alpha = softmax(where(m, e, np.full((t, n, n), -1e9)), axis=2)
        alpha = alpha * Tensor(m.any(axis=2, keepdims=True).astype(float))
        partner = (alpha * r.reshape(t, 1, n)).sum(axis=2)
        return self.coef[0] + self.coef[1] * r + self.coef[2] * partner

    def fit(self, returns, links, steps: int = 300, lr: float = 0.05) -> list[float]:
        r = np.asarray(returns, float)
        return fit(
            lambda: mse(self.predict(r[:-1], links), r[1:]), [self.att, self.coef], steps, lr
        )


# ---------------------------------------------------------------- FactorVAE (RK380)


class FactorVAE:
    """A compact FactorVAE: per-stock hidden e = MLP(x); K portfolios with
    softmax weights over stocks give portfolio returns y_p; the posterior
    q(f | y) is Gaussian from y_p; the prior p(f | x) comes from attention
    pooling of e; returns r = alpha(e) + beta(e) f + noise. Loss: Gaussian
    reconstruction + KL(posterior || prior). Forecasts use the prior mean."""

    def __init__(
        self, n_features: int, factors: int = 2, hidden: int = 8, portfolios: int = 4, seed: int = 0
    ):
        rng = np.random.default_rng(seed)
        self.k = factors
        self.feat = MLP([n_features, hidden], rng)
        self.port = param((hidden, portfolios), rng)
        self.post = MLP([portfolios, 2 * factors], rng)
        self.query = param((hidden, factors), rng)
        self.prior = MLP([hidden, 2], rng)
        self.alpha = MLP([hidden, 1], rng)
        self.beta = param((hidden, factors), rng)
        self.rng = rng

    @property
    def params(self) -> list[Tensor]:
        return [
            *self.feat.params,
            self.port,
            *self.post.params,
            self.query,
            *self.prior.params,
            *self.alpha.params,
            self.beta,
        ]

    def _prior(self, e: Tensor) -> tuple[Tensor, Tensor]:
        att = softmax(e @ self.query, axis=0)  # (n, K): one attention head per factor
        pooled = att.T @ e  # (K, hidden)
        o = self.prior(pooled)
        return o[:, 0], o[:, 1].clip(-5, 2)

    def elbo_loss(self, x, r, noise) -> Tensor:
        e = self.feat(Tensor(x)).leaky_relu(0.1)
        w = softmax(e @ self.port, axis=0)
        y = Tensor(r) @ w  # portfolio returns (P,)
        o = self.post(y)
        mu_q, ls_q = o[: self.k], o[self.k :].clip(-5, 2)
        f = mu_q + ls_q.exp() * Tensor(noise)
        pred = self.alpha(e)[:, 0] + e @ self.beta @ f
        mu_p, ls_p = self._prior(e)
        kl = (
            ls_p
            - ls_q
            + ((2.0 * ls_q).exp() + (mu_q - mu_p) ** 2) * (0.5 * (-2.0 * ls_p).exp())
            - 0.5
        ).sum()
        return mse(pred, r) + kl * 1e-3

    def fit(self, features, returns, steps: int = 300, lr: float = 0.01) -> list[float]:
        """features (T, n, f), returns (T, n) realised over the next period."""
        x, r = np.asarray(features, float), np.asarray(returns, float)
        self.scale = r.std() + 1e-12

        def loss():
            t = int(self.rng.integers(len(x)))
            return self.elbo_loss(x[t], r[t] / self.scale, self.rng.normal(size=self.k))

        return fit(loss, self.params, steps, lr)

    def predict(self, features) -> np.ndarray:
        e = self.feat(Tensor(np.asarray(features, float))).leaky_relu(0.1)
        mu_p, _ = self._prior(e)
        return (self.alpha(e)[:, 0] + e @ self.beta @ mu_p).data * self.scale


# ---------------------------------------------------------------- domain adversarial (RK98, RK327)


def grad_reverse(x: Tensor, lam: float = 1.0) -> Tensor:
    """Identity forward, -lam * gradient backward (Ganin's gradient reversal)."""
    return Tensor(x.data, _parents=(x,), _backward=lambda g: ((x, -lam * g),))


class DomainAdversarialForecaster:
    """A shared feature extractor feeds a return regressor and, through a
    gradient-reversal layer, a domain classifier; minimising both losses
    makes the features predictive but domain-invariant."""

    def __init__(
        self, n_features: int, n_domains: int, hidden: int = 8, lam: float = 1.0, seed: int = 0
    ):
        rng = np.random.default_rng(seed)
        self.extract = MLP([n_features, hidden], rng)
        self.reg = MLP([hidden, 1], rng)
        self.dom = MLP([hidden, hidden, n_domains], rng)
        self.lam = lam

    @property
    def params(self) -> list[Tensor]:
        return [*self.extract.params, *self.reg.params, *self.dom.params]

    def features(self, x) -> Tensor:
        return self.extract(Tensor(np.asarray(x, float))).tanh()

    def loss(self, x, y, domains, labelled) -> tuple[Tensor, Tensor]:
        h = self.features(x)
        lab = np.asarray(labelled, bool)
        pred = self.reg(h)[:, 0]
        reg_loss = (
            ((pred - Tensor(np.asarray(y, float))) ** 2) * Tensor(lab.astype(float))
        ).sum() * (1 / max(lab.sum(), 1))
        d = np.asarray(domains, int)
        dom_loss = -log_softmax(self.dom(grad_reverse(h, self.lam)), axis=1)[
            np.arange(len(d)), d
        ].mean()
        return reg_loss, dom_loss

    def fit(self, x, y, domains, labelled=None, steps: int = 300, lr: float = 0.01) -> list[float]:
        """labelled marks rows with a usable target (the target market's rows
        may be unlabelled, as in DANN's transfer setting)."""
        lab = np.ones(len(x), bool) if labelled is None else labelled

        def total():
            a, b = self.loss(x, y, domains, lab)
            return a + b

        return fit(total, self.params, steps, lr)

    def predict(self, x) -> np.ndarray:
        return self.reg(self.features(x)).data[:, 0]

    def domain_accuracy(self, x, domains) -> float:
        logits = self.dom(self.features(x)).data
        return float((np.argmax(logits, 1) == np.asarray(domains)).mean())


def momentum_features(prices) -> np.ndarray:
    """RK98's inputs per stock at the last date: 12-1, 6-1 and 1-month returns
    (21-day months). prices (days, stocks), at least 253 days."""
    p = np.asarray(prices, float)
    if len(p) < 253:
        raise ConfigurationError("need at least 253 days of prices")
    return np.column_stack([p[-22] / p[-253] - 1, p[-22] / p[-127] - 1, p[-1] / p[-22] - 1])


# ---------------------------------------------------------------- contractive autoencoder (RK382)


class ContractiveAutoencoder:
    """Sigmoid encoder h = s(Wx + b), linear decoder; loss = reconstruction +
    lam ||dh/dx||_F^2 = lam sum_j (h_j (1 - h_j))^2 sum_i W_ij^2. Days whose
    cross-section it cannot reconstruct are anomalies."""

    def __init__(self, n_in: int, latent: int = 2, lam: float = 0.1, seed: int = 0):
        rng = np.random.default_rng(seed)
        self.w, self.b = param((n_in, latent), rng), param(latent)
        self.dec = MLP([latent, n_in], rng)
        self.lam = lam

    def _encode(self, x: Tensor) -> Tensor:
        return (x @ self.w + self.b).sigmoid()

    def fit(self, returns, steps: int = 300, lr: float = 0.02) -> list[float]:
        r = np.asarray(returns, float)
        self.mu, self.sd = r.mean(0), r.std(0) + 1e-12
        x = (r - self.mu) / self.sd

        def loss():
            h = self._encode(Tensor(x))
            rec = mse(self.dec(h), x)
            jac = (((h * (1.0 - h)) ** 2) * (self.w**2).sum(axis=0)).sum(axis=1).mean()
            return rec + jac * self.lam

        return fit(loss, [self.w, self.b, *self.dec.params], steps, lr)

    def anomaly_scores(self, returns) -> np.ndarray:
        x = (np.asarray(returns, float) - self.mu) / self.sd
        rec = self.dec(self._encode(Tensor(x))).data
        return ((x - rec) ** 2).mean(1)

    def jacobian_norm(self, returns) -> float:
        x = (np.asarray(returns, float) - self.mu) / self.sd
        h = self._encode(Tensor(x)).data
        return float(((h * (1 - h)) ** 2 * (self.w.data**2).sum(0)).sum(1).mean())


# ---------------------------------------------------------------- quantile network + copula (RK388)


class QuantileNetwork:
    """Non-crossing quantiles: the lowest is a free output and each higher one
    adds a softplus increment. Trained with the pinball loss."""

    def __init__(
        self,
        n_features: int,
        quantiles=(0.05, 0.25, 0.5, 0.75, 0.95),
        hidden: int = 16,
        seed: int = 0,
    ):
        self.q = np.asarray(quantiles, float)
        self.net = MLP([n_features, hidden, len(quantiles)], np.random.default_rng(seed))

    def quantiles(self, x) -> Tensor:
        o = self.net(Tensor(np.asarray(x, float)))
        parts = [o[:, :1]] + [o[:, j : j + 1].softplus() for j in range(1, len(self.q))]
        cum = [parts[0]]
        for p in parts[1:]:
            cum.append(cum[-1] + p)
        return concat(cum, axis=1)

    def fit(self, x, y, steps: int = 400, lr: float = 0.01) -> list[float]:
        target = np.asarray(y, float)[:, None]
        q = Tensor(self.q)

        def loss():
            e = Tensor(target) - self.quantiles(x)
            return where(e.data >= 0, e * q, e * (q - 1.0)).mean()

        return fit(loss, self.net.params, steps, lr)

    def cdf(self, x, y) -> np.ndarray:
        """Approximate P(Y <= y | x) by interpolating the predicted quantiles."""
        qs = self.quantiles(x).data
        return np.array(
            [
                np.interp(v, row, self.q, left=self.q[0] / 2, right=(1 + self.q[-1]) / 2)
                for row, v in zip(qs, np.atleast_1d(y), strict=True)
            ]
        )


def copula_quantile_rank(
    models, features_hist, returns_hist, features_now, n_sim: int = 2000, rng=None
) -> dict:
    """RK388: each stock's quantile network gives conditional margins; a
    Gaussian copula fitted to the historical PIT values ties them together;
    joint scenarios are simulated and stocks ranked by P(return > 0) and by
    their expected return under the joint draws."""

    rng = np.random.default_rng(rng)
    n = len(models)
    pit = np.column_stack([models[i].cdf(features_hist[i], returns_hist[:, i]) for i in range(n)])
    z = stats.norm.ppf(pseudo_observations(pit))
    corr = np.corrcoef(z.T)
    u = stats.norm.cdf(rng.multivariate_normal(np.zeros(n), corr, n_sim))
    draws = np.empty_like(u)
    for i, m in enumerate(models):
        qs = m.quantiles(np.atleast_2d(features_now[i])).data[0]
        draws[:, i] = np.interp(u[:, i], m.q, qs)
    return {"p_up": (draws > 0).mean(0), "expected": draws.mean(0), "corr": corr, "draws": draws}


# ---------------------------------------------------------------- operator boosting (RK326)


def spectral_features(histories, modes: int = 4) -> np.ndarray:
    """Real and imaginary parts of the first Fourier modes of each history
    (the input layer of a Fourier neural operator)."""
    h = np.asarray(histories, float)
    re, im = dft_matrices(h.shape[1], modes)
    return np.column_stack([h @ re.T, h @ im.T]) / h.shape[1]


def operator_boosting(
    histories,
    targets,
    stages: int = 5,
    modes: int = 4,
    shrinkage: float = 0.5,
    steps: int = 150,
    seed: int = 0,
) -> dict:
    """RK326: each stage is a small spectral operator (Fourier features ->
    tanh layer -> scalar) fitted to the current residual; predictions add up
    with shrinkage, as in gradient boosting."""
    x = spectral_features(histories, modes)
    y = np.asarray(targets, float)
    pred, models = np.zeros_like(y), []
    for s in range(stages):
        net = MLP([x.shape[1], 8, 1], np.random.default_rng(seed + s))
        resid = y - pred
        fit(lambda net=net, resid=resid: mse(net(Tensor(x))[:, 0], resid), net.params, steps, 0.02)
        pred = pred + shrinkage * net(Tensor(x)).data[:, 0]
        models.append(net)

    def predict(h):
        f = spectral_features(h, modes)
        return sum(shrinkage * m(Tensor(f)).data[:, 0] for m in models)

    return {"models": models, "fitted": pred, "predict": predict}


# ---------------------------------------------------------------- signatures and roughness (RK328, RK330)


def rough_hurst(log_vol, lags=(1, 2, 3, 5, 8, 13, 21), q: float = 2.0) -> float:
    """Gatheral-Jaisson-Rosenbaum: slope of log E|dlogv(D)|^q on log D, over q."""
    lv = np.asarray(log_vol, float)
    m = [np.mean(np.abs(lv[d:] - lv[:-d]) ** q) for d in lags]
    return float(np.polyfit(np.log(lags), np.log(m), 1)[0] / q)


def signature_feature_panel(prices, window: int = 20, delay: int = 0) -> np.ndarray:
    """Per date t, the depth-2 signature of the (time, log price) path over the
    window ending at t - delay; NaN rows before the first full window."""
    lp = np.log(np.asarray(prices, float))
    out = np.full((len(lp), 6), np.nan)
    tgrid = np.linspace(0, 1, window + 1)
    for t in range(window + delay, len(lp)):
        seg = lp[t - delay - window : t - delay + 1]
        out[t] = path_signature_features(np.column_stack([tgrid, seg - seg[0]]))
    return out


def signature_trading(prices, window: int = 20, risk_aversion: float = 1.0, delay: int = 0) -> dict:
    """RK328 (Futter-Horvath-Wiese): positions linear in the signature,
    pos_t = l'phi_t. Feature k's P&L is phi_k,t r_{t+1}; the mean-variance
    optimal coefficients are l = Sigma^-1 mu / (2 lambda). RK330: delay > 0
    uses signatures of the path ending `delay` days earlier (the delay-
    differential control, discretised)."""
    p = np.asarray(prices, float)
    phi = signature_feature_panel(p, window, delay)
    r = np.r_[np.diff(np.log(p)), np.nan]
    ok = np.isfinite(phi).all(1) & np.isfinite(r)
    pnl = phi[ok] * r[ok][:, None]
    mu, cov = pnl.mean(0), np.cov(pnl.T) + 1e-10 * np.eye(phi.shape[1])
    coef = np.linalg.solve(cov, mu) / (2 * risk_aversion)
    pos = np.where(np.isfinite(phi).all(1), np.nan_to_num(phi) @ coef, 0.0)
    return {"coef": coef, "positions": pos, "in_sample_pnl": float((pos[ok] * r[ok]).sum())}
