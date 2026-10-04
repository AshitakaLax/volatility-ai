"""
Hidden-Markov and Gaussian-mixture volatility regimes -- catalog C-R3
(docs/research/correction-strategies.md, R3).

Sources: letianzj/QuantResearch notebooks #12 (hidden_markov_chain.py) and
#18 (gaussian_mixture_markov_switching.ipynb): fit two or three hidden
states to returns; the states separate by volatility (and sometimes
drift); trade the grid fully in the calm state and thin it in the
turbulent one. The catalog records two defects in those notebooks, both
avoided here: the HMM is fit AND decoded on the full sample (lookahead),
and returns are computed as P(t-1)/P(t) - 1, which flips their sign.

  GaussianHMM      one-dimensional Gaussian emissions, K states.
    fit            Baum-Welch (EM) with scaled forward-backward.
    filter         P(state_t | x_1..x_t): the forward pass alone, so the
                   value at t uses no observation after t. This is the
                   Hamilton filter, i.e. a Markov-switching model with
                   regime-dependent mean and variance.
    smooth/viterbi use the whole sample -- for analysis, never as inputs.
  GaussianMixture  K-component EM with no time dynamics (the notebook's
                   GaussianMixture counterpart).

States are relabelled after fitting so state 0 has the smallest variance
(calm) and state K-1 the largest (turbulent); without that, which state
is "turbulent" would change from fit to fit.

`causal_turbulence` is the intended use: fit on a training window, then
filter forward with the frozen parameters.
"""

from __future__ import annotations

import math

import numpy as np

from engine.core.exceptions import ConfigurationError

_LOG_2PI = math.log(2.0 * math.pi)


def _gauss_pdf(x: np.ndarray, mu: np.ndarray, var: np.ndarray) -> np.ndarray:
    """N x K densities."""
    d = x[:, None] - mu[None, :]
    return np.exp(-0.5 * (_LOG_2PI + np.log(var)[None, :] + d * d / var[None, :]))


class GaussianHMM:
    def __init__(
        self,
        n_states: int = 2,
        n_iter: int = 200,
        tol: float = 1e-6,
        min_var: float = 1e-12,
        seed: int = 0,
    ) -> None:
        if not (isinstance(n_states, int) and n_states >= 2):
            raise ConfigurationError(f"n_states must be an integer >= 2, got {n_states!r}")
        self.k = n_states
        self.n_iter = n_iter
        self.tol = tol
        self.min_var = min_var
        self.seed = seed
        self.start: np.ndarray | None = None
        self.trans: np.ndarray | None = None
        self.mu: np.ndarray | None = None
        self.var: np.ndarray | None = None
        self.loglik_history: list[float] = []

    # -- inference -------------------------------------------------------
    def _forward(self, x: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        b = _gauss_pdf(x, self.mu, self.var)
        alpha = np.empty_like(b)
        c = np.empty(x.size)
        a = self.start * b[0]
        c[0] = a.sum()
        alpha[0] = a / c[0]
        for t in range(1, x.size):
            a = (alpha[t - 1] @ self.trans) * b[t]
            c[t] = a.sum()
            alpha[t] = a / c[t]
        return alpha, c

    def _check_fitted(self) -> None:
        if self.mu is None:
            raise ConfigurationError("fit the model first")

    def log_likelihood(self, x) -> float:
        self._check_fitted()
        _, c = self._forward(np.asarray(x, dtype=float))
        return float(np.log(c).sum())

    def filter(self, x) -> np.ndarray:
        """P(state_t | x_1..x_t), N x K."""
        self._check_fitted()
        alpha, _ = self._forward(np.asarray(x, dtype=float))
        return alpha

    def smooth(self, x) -> np.ndarray:
        """P(state_t | all x): NOT causal."""
        self._check_fitted()
        x = np.asarray(x, dtype=float)
        alpha, c = self._forward(x)
        b = _gauss_pdf(x, self.mu, self.var)
        beta = np.ones_like(alpha)
        for t in range(x.size - 2, -1, -1):
            beta[t] = (self.trans @ (b[t + 1] * beta[t + 1])) / c[t + 1]
        gamma = alpha * beta
        return gamma / gamma.sum(axis=1, keepdims=True)

    def viterbi(self, x) -> np.ndarray:
        """Most likely state path: NOT causal."""
        self._check_fitted()
        x = np.asarray(x, dtype=float)
        logb = np.log(_gauss_pdf(x, self.mu, self.var) + 1e-300)
        loga = np.log(self.trans + 1e-300)
        delta = np.log(self.start + 1e-300) + logb[0]
        back = np.zeros((x.size, self.k), dtype=int)
        for t in range(1, x.size):
            scores = delta[:, None] + loga
            back[t] = scores.argmax(axis=0)
            delta = scores.max(axis=0) + logb[t]
        path = np.empty(x.size, dtype=int)
        path[-1] = int(delta.argmax())
        for t in range(x.size - 1, 0, -1):
            path[t - 1] = back[t, path[t]]
        return path

    # -- learning --------------------------------------------------------
    def fit(self, x) -> GaussianHMM:
        x = np.asarray(x, dtype=float)
        if x.size < 10 * self.k:
            raise ConfigurationError("too few observations for this many states")
        rng = np.random.default_rng(self.seed)
        qs = np.quantile(np.abs(x - x.mean()), np.linspace(0.2, 0.9, self.k))
        self.mu = np.full(self.k, x.mean()) + rng.normal(0, 1e-6, self.k)
        self.var = np.maximum(qs**2, self.min_var)
        self.start = np.full(self.k, 1.0 / self.k)
        self.trans = np.full((self.k, self.k), 0.1 / (self.k - 1))
        np.fill_diagonal(self.trans, 0.9)
        self.loglik_history = []
        prev = -math.inf
        for _ in range(self.n_iter):
            alpha, c = self._forward(x)
            b = _gauss_pdf(x, self.mu, self.var)
            beta = np.ones_like(alpha)
            for t in range(x.size - 2, -1, -1):
                beta[t] = (self.trans @ (b[t + 1] * beta[t + 1])) / c[t + 1]
            gamma = alpha * beta
            gamma /= gamma.sum(axis=1, keepdims=True)
            xi = (
                alpha[:-1, :, None] * self.trans[None, :, :] * (b[1:] * beta[1:])[:, None, :]
            ) / c[1:, None, None]
            loglik = float(np.log(c).sum())
            self.loglik_history.append(loglik)
            self.start = gamma[0]
            self.trans = xi.sum(axis=0) / gamma[:-1].sum(axis=0)[:, None]
            weights = gamma.sum(axis=0)
            self.mu = (gamma * x[:, None]).sum(axis=0) / weights
            self.var = np.maximum(
                (gamma * (x[:, None] - self.mu) ** 2).sum(axis=0) / weights, self.min_var
            )
            if abs(loglik - prev) < self.tol:
                break
            prev = loglik
        self._order_by_variance()
        return self

    def _order_by_variance(self) -> None:
        order = np.argsort(self.var)
        self.mu, self.var, self.start = self.mu[order], self.var[order], self.start[order]
        self.trans = self.trans[np.ix_(order, order)]


class GaussianMixture:
    def __init__(
        self, n_components: int = 2, n_iter: int = 500, tol: float = 1e-8, min_var: float = 1e-12
    ) -> None:
        if not (isinstance(n_components, int) and n_components >= 2):
            raise ConfigurationError(f"n_components must be an integer >= 2, got {n_components!r}")
        self.k = n_components
        self.n_iter = n_iter
        self.tol = tol
        self.min_var = min_var
        self.weights = self.mu = self.var = None

    def fit(self, x) -> GaussianMixture:
        x = np.asarray(x, dtype=float)
        if x.size < 10 * self.k:
            raise ConfigurationError("too few observations for this many components")
        qs = np.quantile(np.abs(x - x.mean()), np.linspace(0.2, 0.9, self.k))
        self.mu = np.full(self.k, x.mean())
        self.var = np.maximum(qs**2, self.min_var)
        self.weights = np.full(self.k, 1.0 / self.k)
        prev = -math.inf
        for _ in range(self.n_iter):
            dens = _gauss_pdf(x, self.mu, self.var) * self.weights
            total = dens.sum(axis=1, keepdims=True)
            resp = dens / total
            loglik = float(np.log(total).sum())
            nk = resp.sum(axis=0)
            self.weights = nk / x.size
            self.mu = (resp * x[:, None]).sum(axis=0) / nk
            self.var = np.maximum(
                (resp * (x[:, None] - self.mu) ** 2).sum(axis=0) / nk, self.min_var
            )
            if abs(loglik - prev) < self.tol:
                break
            prev = loglik
        order = np.argsort(self.var)
        self.weights, self.mu, self.var = self.weights[order], self.mu[order], self.var[order]
        return self

    def predict_proba(self, x) -> np.ndarray:
        if self.mu is None:
            raise ConfigurationError("fit the model first")
        dens = _gauss_pdf(np.asarray(x, dtype=float), self.mu, self.var) * self.weights
        return dens / dens.sum(axis=1, keepdims=True)


def causal_turbulence(returns, train_end: int, n_states: int = 2, seed: int = 0) -> np.ndarray:
    """P(most turbulent state | returns through t) for every t, with the
    HMM fitted on returns[:train_end] only and then frozen."""
    r = np.asarray(returns, dtype=float)
    if not 0 < train_end <= r.size:
        raise ConfigurationError("train_end must fall inside the series")
    model = GaussianHMM(n_states=n_states, seed=seed).fit(r[:train_end])
    return model.filter(r)[:, -1]
