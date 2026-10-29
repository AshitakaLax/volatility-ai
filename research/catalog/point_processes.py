"""
Self-exciting point processes and the ranked list's Hawkes entries (ledger
RK248, RK259, RK277, RK280, RK289, RK304, RK314, RK333, RK338, RK342,
RK353, RK355-RK357, RK367, RK371, RK411, RK412, RK414, RK424). Research
code; the warehouse has no event-level data, so every function here runs on
event times or daily returns the caller supplies.

Sources:

  * Exponential Hawkes processes, Ogata's thinning simulation and the
    closed-form log-likelihood -- Hawkes, "Spectra of some self-exciting and
    mutually exciting point processes", Biometrika 58, 1971; Ogata, "On
    Lewis' simulation method for point processes", IEEE Trans. Inf. Theory
    27, 1981; review: Bacry, Mastromatteo & Muzy, "Hawkes processes in
    finance", Market Microstructure and Liquidity 1, 2015.
  * Mutually exciting jumps in daily returns, filtered jump intensity as a
    stress gauge -- Ait-Sahalia, Cacho-Diaz & Laeven, "Modeling financial
    contagion using mutually exciting jump processes", JFE 117, 2015.
  * Neural Hawkes (continuous-time LSTM intensity) -- Mei & Eisner,
    NeurIPS 2017; attention intensities -- Zuo et al., "Transformer Hawkes
    Process", ICML 2020; neural jump SDEs -- Jia & Benson, NeurIPS 2019.
    Here: a small recurrent intensity model trained on the exact
    log-likelihood with a Monte Carlo compensator.
  * Optimal execution with Hawkes order flow and transient impact --
    Alfonsi & Blanc, "Dynamic optimal execution in a mixed-market-impact
    Hawkes price model", Finance and Stochastics 20, 2016 (discretised:
    the trader offsets the expected price drift that other traders' Hawkes
    flow creates, on top of an Almgren-Chriss schedule).
  * Distributionally robust variants (RK371, RK424) widen the branching
    ratio to the worst case inside a ball around the estimate.
"""

from __future__ import annotations

import math

import numpy as np
from scipy.optimize import minimize

from engine.core.exceptions import ConfigurationError
from research.catalog.autodiff import Tensor, fit, param
from research.catalog.leads import almgren_chriss

# ---------------------------------------------------------------- univariate exponential Hawkes


def hawkes_intensity(times, t, mu: float, alpha: float, beta: float) -> np.ndarray:
    """lambda(t) = mu + sum_{t_i < t} alpha exp(-beta (t - t_i)) at each t."""
    times, t = np.asarray(times, float), np.atleast_1d(np.asarray(t, float))
    out = np.full(t.shape, mu)
    for k, s in enumerate(t):
        past = times[times < s]
        out[k] += alpha * np.exp(-beta * (s - past)).sum()
    return out


def simulate_hawkes(mu: float, alpha: float, beta: float, horizon: float, rng) -> np.ndarray:
    """Ogata thinning; stationary when the branching ratio alpha / beta < 1."""
    if alpha / beta >= 1:
        raise ConfigurationError("branching ratio alpha / beta must be below 1")
    t, events, excite = 0.0, [], 0.0
    while True:
        lam_bar = mu + excite
        w = rng.exponential(1.0 / lam_bar)
        excite *= math.exp(-beta * w)
        t += w
        if t > horizon:
            return np.array(events)
        if rng.uniform() * lam_bar <= mu + excite:
            events.append(t)
            excite += alpha


def hawkes_loglik(times, horizon: float, mu: float, alpha: float, beta: float) -> float:
    """Exact log-likelihood with the recursive A_i = exp(-beta dt) (1 + A_{i-1})."""
    times = np.asarray(times, float)
    a, ll = 0.0, 0.0
    for i, s in enumerate(times):
        if i:
            a = math.exp(-beta * (s - times[i - 1])) * (1.0 + a)
        ll += math.log(mu + alpha * a)
    comp = mu * horizon + (alpha / beta) * np.sum(1.0 - np.exp(-beta * (horizon - times)))
    return ll - comp


def fit_hawkes(times, horizon: float) -> dict:
    """Maximum likelihood (mu, alpha, beta) with the branching ratio below 1."""
    times = np.asarray(times, float)
    if times.size < 5:
        raise ConfigurationError("need at least five events")

    def nll(z):
        mu, beta, ratio = np.exp(z[0]), np.exp(z[1]), 1.0 / (1.0 + np.exp(-z[2]))
        return -hawkes_loglik(times, horizon, mu, ratio * beta, beta)

    rate = times.size / horizon
    res = minimize(
        nll,
        np.array([np.log(rate / 2), 0.0, 0.0]),
        method="Nelder-Mead",
        options={"maxiter": 4000, "xatol": 1e-6, "fatol": 1e-8},
    )
    mu, beta, ratio = np.exp(res.x[0]), np.exp(res.x[1]), 1.0 / (1.0 + np.exp(-res.x[2]))
    return {"mu": mu, "alpha": ratio * beta, "beta": beta, "branching": ratio, "loglik": -res.fun}


def expected_count(mu: float, alpha: float, beta: float, lam_now: float, h: float) -> float:
    """E[N(t, t+h)] given the current intensity: the excess decays at beta - alpha."""
    kappa = beta - alpha
    stat = mu * beta / kappa
    excess = lam_now - stat
    return stat * h + excess * (1.0 - math.exp(-kappa * h)) / kappa


# ---------------------------------------------------------------- multivariate exponential Hawkes


def simulate_multivariate_hawkes(mu, alpha, beta: float, horizon: float, rng) -> list[np.ndarray]:
    """lambda_i(t) = mu_i + sum_j alpha_ij sum_{t_jk < t} exp(-beta (t - t_jk))."""
    mu, alpha = np.asarray(mu, float), np.asarray(alpha, float)
    if np.max(np.abs(np.linalg.eigvals(alpha / beta))) >= 1:
        raise ConfigurationError("spectral radius of alpha / beta must be below 1")
    d, t = len(mu), 0.0
    excite = np.zeros(d)
    events: list[list[float]] = [[] for _ in range(d)]
    while True:
        lam_bar = (mu + excite).sum()
        w = rng.exponential(1.0 / lam_bar)
        excite *= math.exp(-beta * w)
        t += w
        if t > horizon:
            return [np.array(e) for e in events]
        lam = mu + excite
        u = rng.uniform() * lam_bar
        if u <= lam.sum():
            i = int(np.searchsorted(np.cumsum(lam), u))
            events[i].append(t)
            excite += alpha[:, i]


def multivariate_intensity(events, mu, alpha, beta: float, t: float) -> np.ndarray:
    mu, alpha = np.asarray(mu, float), np.asarray(alpha, float)
    lam = mu.copy()
    for j, e in enumerate(events):
        e = np.asarray(e)
        lam += alpha[:, j] * np.exp(-beta * (t - e[e < t])).sum()
    return lam


def fit_multivariate_hawkes(events, horizon: float, beta: float) -> dict:
    """MLE of (mu, alpha) for a fixed decay beta (RK277's order-flow model)."""
    d = len(events)
    allt = np.concatenate([np.asarray(e, float) for e in events])
    lab = np.concatenate([np.full(len(e), j) for j, e in enumerate(events)])
    order = np.argsort(allt)
    allt, lab = allt[order], lab[order]

    def nll(z):
        mu = np.exp(z[:d])
        alpha = np.exp(z[d:]).reshape(d, d)
        state, last, ll = np.zeros(d), 0.0, 0.0
        for s, j in zip(allt, lab, strict=True):
            state *= math.exp(-beta * (s - last))
            ll += math.log(mu[j] + alpha[j] @ state)
            state[j] += 1.0
            last = s
        tails = np.array([np.sum(1 - np.exp(-beta * (horizon - np.asarray(e)))) for e in events])
        comp = mu.sum() * horizon + (alpha @ tails).sum() / beta
        return comp - ll

    z0 = np.r_[
        np.log(np.array([len(e) for e in events]) / horizon / 2 + 1e-9),
        np.full(d * d, np.log(0.1 * beta)),
    ]
    res = minimize(nll, z0, method="L-BFGS-B")
    return {"mu": np.exp(res.x[:d]), "alpha": np.exp(res.x[d:]).reshape(d, d), "loglik": -res.fun}


# ---------------------------------------------------------------- RK248, RK259, RK277: order flow


def order_flow_forecast(
    buy_times, sell_times, now: float, horizon: float, beta: float = 1.0
) -> dict:
    """RK248: fit a bivariate Hawkes to buy and sell events and forecast the
    expected net order flow over the next `horizon` (approximating each side's
    excess intensity as decaying at beta)."""
    fit_ = fit_multivariate_hawkes([buy_times, sell_times], now, beta)
    lam = multivariate_intensity([buy_times, sell_times], fit_["mu"], fit_["alpha"], beta, now)
    exp_counts = fit_["mu"] * horizon + (lam - fit_["mu"]) * (1 - math.exp(-beta * horizon)) / beta
    return {
        "buy": exp_counts[0],
        "sell": exp_counts[1],
        "imbalance": (exp_counts[0] - exp_counts[1]) / exp_counts.sum(),
        **fit_,
    }


def toxicity_score(times, now: float, window: float, mu: float, alpha: float, beta: float) -> float:
    """RK259: how far the current intensity sits above its stationary level, in
    units of that level (0 = calm); a market maker halts above a threshold."""
    stat = mu / (1.0 - alpha / beta)
    return float(
        hawkes_intensity(np.asarray(times)[np.asarray(times) > now - window], now, mu, alpha, beta)[
            0
        ]
        / stat
        - 1.0
    )


def halt_quoting(score: float, threshold: float = 1.0) -> bool:
    return score > threshold


# ---------------------------------------------------------------- RK314: jumps in daily returns


def detect_jumps(returns, window: int = 60, k: float = 4.0) -> np.ndarray:
    """Flag |r_t| > k sigma_t with sigma from trailing bipower variation
    (robust to the jumps themselves); causal: uses returns before t."""
    r = np.asarray(returns, float)
    flags = np.zeros(r.size, dtype=bool)
    for t in range(window + 1, r.size):
        past = r[t - window : t]
        bv = (np.pi / 2) * np.mean(np.abs(past[1:]) * np.abs(past[:-1]))
        flags[t] = abs(r[t]) > k * math.sqrt(bv)
    return flags


def mutually_exciting_jump_intensity(jumps, mu, alpha, beta: float) -> np.ndarray:
    """RK314: filtered intensities lambda_i(t) of jumps in d markets (columns of
    `jumps`, daily 0/1), excited by every market's past jumps; the stress gauge."""
    j = np.asarray(jumps, float)
    mu, alpha = np.asarray(mu, float), np.asarray(alpha, float)
    n, d = j.shape
    lam, state = np.zeros((n, d)), np.zeros(d)
    decay = math.exp(-beta)
    for t in range(n):
        lam[t] = mu + alpha @ state
        state = decay * (state + j[t])
    return lam


def fit_jump_excitation(jumps, beta: float = 0.1) -> dict:
    """Discrete-time MLE (Bernoulli per day) of mu and the excitation matrix."""
    j = np.asarray(jumps, float)
    d = j.shape[1]

    def nll(z):
        mu, alpha = np.exp(z[:d]), np.exp(z[d:]).reshape(d, d)
        lam = np.clip(mutually_exciting_jump_intensity(j, mu, alpha, beta), 1e-9, 1 - 1e-9)
        return -(j * np.log(lam) + (1 - j) * np.log(1 - lam)).sum()

    z0 = np.r_[np.log(j.mean(0) + 1e-4), np.full(d * d, np.log(0.01))]
    res = minimize(nll, z0, method="L-BFGS-B")
    return {"mu": np.exp(res.x[:d]), "alpha": np.exp(res.x[d:]).reshape(d, d)}


# ---------------------------------------------------------------- neural Hawkes (RK304, RK333, RK338, RK342, RK414)


class NeuralHawkes:
    """A recurrent intensity model in the spirit of Mei & Eisner's neural
    Hawkes process: a hidden state jumps at each event and decays toward a
    target in between; lambda_k(t) = softplus(w_k . h(t)). Trained on the exact
    point-process log-likelihood, with the compensator integral estimated by
    Monte Carlo. `attention=True` (RK414) replaces the recurrence with a
    softmax-weighted sum over past events' embeddings (a one-head version of
    Zuo et al.'s Transformer Hawkes process)."""

    def __init__(self, n_types: int, hidden: int = 8, attention: bool = False, seed: int = 0):
        rng = np.random.default_rng(seed)
        self.k, self.h, self.attention = n_types, hidden, attention
        self.emb = param((n_types, hidden), rng)
        self.decay = Tensor(np.full(hidden, -1.0), requires_grad=True)  # log-rate
        self.out = param((hidden, n_types), rng)
        self.bias = Tensor(np.full(n_types, -1.0), requires_grad=True)
        self.query = param((hidden,), rng, scale=0.5)
        self.rng = rng

    @property
    def params(self) -> list[Tensor]:
        return [self.emb, self.decay, self.out, self.bias, self.query]

    def _state(self, times, types, t: float) -> Tensor:
        past = np.asarray(times) < t
        if not past.any():
            return Tensor(np.zeros(self.h))
        dt = Tensor((t - np.asarray(times)[past])[:, None])
        e = self.emb[np.asarray(types)[past]]  # (m, h)
        decayed = e * (-(dt * self.decay.exp())).exp()
        if not self.attention:
            return decayed.sum(axis=0).tanh()
        scores = decayed @ self.query
        w = (scores - Tensor(scores.data.max())).exp()
        return ((decayed * (w / w.sum()).reshape(-1, 1)).sum(axis=0)).tanh()

    def intensity(self, times, types, t: float) -> Tensor:
        return (self._state(times, types, t) @ self.out + self.bias).softplus()

    def loglik(self, times, types, horizon: float, n_mc: int = 40) -> Tensor:
        ll = Tensor(0.0)
        for s, k in zip(times, types, strict=True):
            ll = ll + self.intensity(times, types, s)[int(k)].log()
        grid = self.rng.uniform(0, horizon, size=n_mc)
        comp = None
        for s in grid:
            v = self.intensity(times, types, s).sum()
            comp = v if comp is None else comp + v
        return ll - comp * (horizon / n_mc)

    def fit(self, times, types, horizon: float, steps: int = 60, lr: float = 0.05) -> list[float]:
        return fit(
            lambda: -self.loglik(times, types, horizon) / max(len(times), 1), self.params, steps, lr
        )


def neural_hawkes_alert(
    model: NeuralHawkes, times, types, now: float, baseline: np.ndarray, k: float = 2.0
) -> bool:
    """RK304/RK338: alert when any event type's intensity exceeds k times its baseline."""
    lam = model.intensity(times, types, now).data
    return bool((lam > k * np.asarray(baseline)).any())


def neural_jump_sde_path(model: NeuralHawkes, times, types, grid) -> np.ndarray:
    """RK333: the latent intensity path between and at events (a neural jump
    process in the sense of Jia & Benson); shocks are its spikes."""
    return np.array([model.intensity(times, types, t).data for t in grid])


def path_signature_features(path, depth: int = 2) -> np.ndarray:
    """Truncated path signature (levels 1..2) of a piecewise-linear path in R^d."""
    x = np.asarray(path, float)
    inc = np.diff(x, axis=0)
    s1 = inc.sum(0)
    d = x.shape[1]
    s2 = np.zeros((d, d))
    run = np.zeros(d)
    for dx in inc:
        s2 += np.outer(run, dx) + 0.5 * np.outer(dx, dx)
        run += dx
    return np.r_[s1, s2.ravel()] if depth >= 2 else s1


def signature_hawkes_forecast(paths, counts) -> np.ndarray:
    """RK342: regress next-window event counts on the signature of the
    preceding order-flow path (ridge least squares); returns coefficients."""
    x = np.array([path_signature_features(p) for p in paths])
    x = np.column_stack([np.ones(len(x)), x])
    y = np.asarray(counts, float)
    return np.linalg.solve(x.T @ x + 1e-6 * np.eye(x.shape[1]), x.T @ y)


# ---------------------------------------------------------------- execution and hedging uses


def hawkes_execution_schedule(
    shares: float,
    n: int,
    sigma: float,
    eta: float,
    risk_aversion: float,
    flow_imbalance: float,
    impact: float,
    resilience: float,
) -> np.ndarray:
    """RK367 (Alfonsi & Blanc, discretised): start from the Almgren-Chriss path,
    then trade ahead of the expected price drift that other traders' net Hawkes
    flow creates: the drift impact * imbalance decays at the book's resilience,
    and the trader front-loads sells when that drift is adverse (imbalance < 0)."""
    base = almgren_chriss(shares, 1.0, n, sigma, eta, risk_aversion=risk_aversion)["trades"]
    decay = np.exp(-resilience * np.arange(n) / n)
    tilt = -impact * flow_imbalance * decay
    trades = base * (1.0 + tilt)
    return trades * shares / trades.sum()


def robust_branching(estimate: float, radius: float) -> float:
    """RK371/RK424: the worst-case branching ratio in [estimate - r, estimate + r], capped below 1."""
    return float(min(estimate + radius, 0.99))


def robust_hawkes_schedule(
    shares,
    n,
    sigma,
    eta,
    risk_aversion,
    flow_imbalance,
    impact,
    resilience,
    branching: float,
    radius: float,
) -> np.ndarray:
    """RK371/RK424: size the flow tilt by the worst-case branching ratio
    (excess flow scales as 1 / (1 - n)), so the schedule is robust to an
    underestimated self-excitation."""
    worst = robust_branching(branching, radius)
    scale = (1 - branching) / (1 - worst)
    return hawkes_execution_schedule(
        shares, n, sigma, eta, risk_aversion, flow_imbalance * scale, impact, resilience
    )


def hawkes_timed_slices(intensity_forecast, shares: float) -> np.ndarray:
    """RK353: split a parent order in proportion to forecast liquidity-taking
    intensity per interval (trade more when counterparties are expected)."""
    f = np.clip(np.asarray(intensity_forecast, float), 0, None)
    if f.sum() <= 0:
        raise ConfigurationError("need a positive intensity forecast")
    return shares * f / f.sum()


def toxic_flow_execution(
    intensity_forecast, toxicity, shares: float, threshold: float, pause: bool
) -> np.ndarray:
    """RK355 (slow down) and RK357 (pause): scale or zero slices whose forecast
    toxicity exceeds the threshold, re-spreading the volume over the others."""
    f = np.clip(np.asarray(intensity_forecast, float), 0, None)
    tox = np.asarray(toxicity, float)
    w = np.where(tox > threshold, 0.0 if pause else 0.5, 1.0) * f
    if w.sum() <= 0:
        raise ConfigurationError("every slice is paused")
    return shares * w / w.sum()


def hawkes_inventory_quotes(
    mid: float, inventory: float, buy_rate: float, sell_rate: float, half_spread: float, skew: float
) -> tuple[float, float]:
    """RK356: quotes skewed against inventory and against the forecast flow
    imbalance (widen the side the flow is hitting)."""
    imb = (buy_rate - sell_rate) / max(buy_rate + sell_rate, 1e-12)
    centre = mid - skew * inventory + half_spread * imb
    return centre - half_spread * (1 + max(-imb, 0)), centre + half_spread * (1 + max(imb, 0))


def hedge_rebalance_times(lam_path, grid, base_interval: float, k: float = 2.0) -> np.ndarray:
    """RK411: rebalance a delta hedge on a fixed clock, plus whenever forecast
    intensity exceeds k times its median (bursts move the underlying)."""
    lam = (
        np.asarray(lam_path, float).sum(axis=-1)
        if np.ndim(lam_path) > 1
        else np.asarray(lam_path, float)
    )
    grid = np.asarray(grid, float)
    clock = np.floor(grid / base_interval)
    scheduled = np.r_[True, np.diff(clock) > 0]
    return grid[scheduled | (lam > k * np.median(lam))]


def hedge_budget_allocation(toxicity_by_book, budget: float) -> np.ndarray:
    """RK412: split a hedging budget across books in proportion to forecast toxicity."""
    t = np.clip(np.asarray(toxicity_by_book, float), 0, None)
    return budget * t / t.sum() if t.sum() > 0 else np.full(t.size, budget / t.size)


def neural_hawkes_hedge_trigger(
    model: NeuralHawkes, times, types, now: float, baseline, k: float = 2.0
) -> bool:
    """RK280: trigger an option-hedge rebalance on a forecast toxic-flow surge."""
    return neural_hawkes_alert(model, times, types, now, baseline, k)


def delay_hawkes_intensity(
    times, t, mu: float, alpha: float, beta: float, delay: float
) -> np.ndarray:
    """RK289: excitation that starts only after a reaction delay (the delay-
    differential version of the exponential kernel)."""
    times = np.asarray(times, float)
    return hawkes_intensity(times + delay, t, mu, alpha, beta)


def concat_types(*streams) -> tuple[np.ndarray, np.ndarray]:
    """Merge per-type event streams into (times, types) sorted by time."""
    t = np.concatenate([np.asarray(s, float) for s in streams])
    k = np.concatenate([np.full(len(s), i) for i, s in enumerate(streams)])
    o = np.argsort(t)
    return t[o], k[o]
