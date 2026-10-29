"""
Portfolio-construction entries of the ranked list (ledger RK53, RK63,
RK66, RK88, RK95, RK205, RK216, RK218, RK222, RK225, RK296, RK392). Every
one needs a multi-asset book, which the engine does not trade (ledger
section 11 is unbuilt), so this is research code only. All weights are
long-only and fully invested unless a function says otherwise.

Sources:

  * CVaR as a linear programme -- Rockafellar & Uryasev, "Optimization of
    conditional value-at-risk", J. Risk 2, 2000.
  * Wasserstein-robust CVaR -- Mohajerin Esfahani & Kuhn, Math. Program.
    171, 2018: for a loss with Lipschitz constant L in the returns, the
    worst case over a type-1 ball of radius eps is the empirical value plus
    eps L; for CVaR, L = ||w||_* / (1 - alpha) (dual of the ground norm).
  * Black & Litterman, Financial Analysts J. 48, 1992; He & Litterman,
    "The intuition behind Black-Litterman model portfolios", 1999 (Omega).
  * Choueifaty & Coignard, "Toward maximum diversification", J. Portfolio
    Mgmt 35, 2008.
  * Downside (semi)covariance -- Estrada, "Mean-semivariance optimization: a
    heuristic approach", J. Applied Finance 18, 2008; risk budgeting by the
    convex programme of Spinu, "An algorithm for computing risk parity
    weights", SSRN 2297383, 2013; CVaR risk budgets -- Boudt, Carl & Peterson,
    J. Risk 15, 2013.
  * Wasserstein-robust mean-variance -- Blanchet, Chen & Zhou,
    "Distributionally robust mean-variance portfolio selection with
    Wasserstein distances", Management Science 68, 2022.
  * CP/PARAFAC by alternating least squares -- Kolda & Bader, "Tensor
    decompositions and applications", SIAM Review 51, 2009.
  * Top-K with dropout -- Qlib's TopkDropoutStrategy (Microsoft, 2020).
  * Sparse Bayesian learning / ARD -- Tipping, J. Mach. Learn. Res. 1, 2001.
  * Maximum-entropy diversification -- Bera & Park, "Optimal portfolio
    diversification using the maximum entropy principle", Econometric
    Reviews 27, 2008 (RK222's "entropy production" has no finance source;
    here it is read as the entropy the weights lose to drift between
    rebalances).
  * Clayton C-vine CVaR allocation -- per RK296's page; vine tools in
    research.catalog.econometrics.
"""

from __future__ import annotations

import numpy as np
from scipy import stats
from scipy.optimize import linprog, minimize
from sklearn.linear_model import ARDRegression

from engine.core.exceptions import ConfigurationError
from research.catalog.econometrics import (
    empirical_quantile,
    fit_cvine,
    fit_var,
    fracdiff,
    fracdiff_weights,
    gph_d,
    pseudo_observations,
    simulate_cvine,
    var_forecast,
)

# ---------------------------------------------------------------- helpers


def simplex_minimize(objective, n: int, x0=None, constraints=(), long_only: bool = True):
    """Minimise objective(w) over sum w = 1 (and w >= 0 when long_only)."""
    x0 = np.full(n, 1.0 / n) if x0 is None else np.asarray(x0, float)
    cons = ({"type": "eq", "fun": lambda w: w.sum() - 1.0}, *constraints)
    bounds = [(0.0, 1.0)] * n if long_only else None
    res = minimize(
        objective,
        x0,
        method="SLSQP",
        bounds=bounds,
        constraints=cons,
        options={"maxiter": 500, "ftol": 1e-12},
    )
    return res.x


def min_variance_weights(cov, long_only: bool = True) -> np.ndarray:
    c = np.asarray(cov, float)
    return simplex_minimize(lambda w: w @ c @ w, len(c), long_only=long_only)


def mean_variance_weights(mu, cov, risk_aversion: float = 1.0) -> np.ndarray:
    mu, c = np.asarray(mu, float), np.asarray(cov, float)
    return simplex_minimize(lambda w: 0.5 * risk_aversion * w @ c @ w - mu @ w, len(mu))


def erc_weights(cov, budgets=None) -> np.ndarray:
    """Risk budgeting (equal risk contribution by default) by Spinu's convex
    programme min 1/2 y'Cy - sum b_i log y_i, w = y / sum y."""
    c = np.asarray(cov, float)
    n = len(c)
    b = np.full(n, 1.0 / n) if budgets is None else np.asarray(budgets, float)
    res = minimize(
        lambda y: 0.5 * y @ c @ y - b @ np.log(y),
        np.full(n, 1.0),
        jac=lambda y: c @ y - b / y,
        method="L-BFGS-B",
        bounds=[(1e-10, None)] * n,
    )
    return res.x / res.x.sum()


def risk_contributions(w, cov) -> np.ndarray:
    w, c = np.asarray(w, float), np.asarray(cov, float)
    return w * (c @ w) / (w @ c @ w)


# ---------------------------------------------------------------- CVaR (RK53, RK88)


def portfolio_cvar(scenarios, w, alpha: float = 0.95) -> float:
    """Average loss in the worst (1 - alpha) share of scenarios."""
    loss = -np.asarray(scenarios, float) @ np.asarray(w, float)
    var = np.quantile(loss, alpha)
    return float(var + np.maximum(loss - var, 0).mean() / (1 - alpha))


def cvar_weights(
    scenarios, alpha: float = 0.95, target_return: float | None = None, radius: float = 0.0
) -> np.ndarray:
    """RK53 (Rockafellar-Uryasev LP): min zeta + sum u_t / ((1 - alpha) T)
    with u_t >= -r_t'w - zeta, u >= 0. RK88: radius > 0 adds the
    Wasserstein worst case radius ||w||_inf / (1 - alpha) (l1 ground metric),
    as one more LP variable s >= w_i. Long-only, fully invested."""
    r = np.asarray(scenarios, float)
    t, n = r.shape
    nv = n + 1 + t + 1  # w, zeta, u, s
    c = np.zeros(nv)
    c[n] = 1.0
    c[n + 1 : n + 1 + t] = 1.0 / ((1 - alpha) * t)
    c[-1] = radius / (1 - alpha)
    a_ub = np.zeros((t + n, nv))
    a_ub[:t, :n] = -r
    a_ub[:t, n] = -1.0
    a_ub[:t, n + 1 : n + 1 + t] = -np.eye(t)
    a_ub[t:, :n] = np.eye(n)
    a_ub[t:, -1] = -1.0
    b_ub = np.zeros(t + n)
    if target_return is not None:
        row = np.zeros(nv)
        row[:n] = -r.mean(0)
        a_ub, b_ub = np.vstack([a_ub, row]), np.r_[b_ub, -target_return]
    a_eq = np.zeros((1, nv))
    a_eq[0, :n] = 1.0
    bounds = [(0, None)] * n + [(None, None)] + [(0, None)] * t + [(0, None)]
    res = linprog(c, a_ub, b_ub, a_eq, [1.0], bounds=bounds, method="highs")
    if not res.success:
        raise ConfigurationError(f"CVaR programme infeasible: {res.message}")
    return res.x[:n]


# ---------------------------------------------------------------- Black-Litterman (RK63)


def black_litterman(
    cov, market_weights, p, q, tau: float = 0.05, delta: float = 2.5, omega=None
) -> dict:
    """Posterior mean and covariance: prior pi = delta Cov w_mkt, views P mu = Q
    with uncertainty Omega (default diag(P tau Cov P'))."""
    c = np.asarray(cov, float)
    p, q = np.atleast_2d(np.asarray(p, float)), np.atleast_1d(np.asarray(q, float))
    pi = delta * c @ np.asarray(market_weights, float)
    tc = tau * c
    om = np.diag(np.diag(p @ tc @ p.T)) if omega is None else np.atleast_2d(omega)
    m = np.linalg.inv(np.linalg.inv(tc) + p.T @ np.linalg.solve(om, p))
    mu = m @ (np.linalg.solve(tc, pi) + p.T @ np.linalg.solve(om, q))
    return {"prior": pi, "mu": mu, "cov": c + m}


def black_litterman_weights(cov, market_weights, p, q, delta: float = 2.5, **kw) -> np.ndarray:
    post = black_litterman(cov, market_weights, p, q, delta=delta, **kw)
    return mean_variance_weights(post["mu"], post["cov"], delta)


# ---------------------------------------------------------------- diversification and tails


def diversification_ratio(w, cov) -> float:
    w, c = np.asarray(w, float), np.asarray(cov, float)
    return float(w @ np.sqrt(np.diag(c)) / np.sqrt(w @ c @ w))


def max_diversification_weights(cov) -> np.ndarray:
    """RK66: min w'Cw subject to sigma'w = 1, w >= 0, then rescale to sum 1 --
    equivalent to maximising the diversification ratio."""
    c = np.asarray(cov, float)
    sig = np.sqrt(np.diag(c))
    n = len(c)
    res = minimize(
        lambda w: w @ c @ w,
        np.full(n, 1.0 / sig.sum()),
        method="SLSQP",
        bounds=[(0, None)] * n,
        constraints=({"type": "eq", "fun": lambda w: w @ sig - 1.0},),
    )
    return res.x / res.x.sum()


def semicovariance(returns, benchmark: float = 0.0) -> np.ndarray:
    """Estrada's semicovariance E[min(r_i - B, 0) min(r_j - B, 0)]."""
    d = np.minimum(np.asarray(returns, float) - benchmark, 0.0)
    return d.T @ d / len(d)


def downside_risk_parity(returns, benchmark: float = 0.0) -> np.ndarray:
    """RK95 (semivariance form): equal contributions to downside semivariance."""
    return erc_weights(semicovariance(returns, benchmark))


def cvar_contributions(scenarios, w, alpha: float = 0.95) -> np.ndarray:
    """Component CVaR: w_i E[-r_i | portfolio loss >= VaR] (sums to CVaR)."""
    r, w = np.asarray(scenarios, float), np.asarray(w, float)
    loss = -r @ w
    tail = loss >= np.quantile(loss, alpha)
    return w * (-r[tail]).mean(0)


def cvar_risk_parity(scenarios, alpha: float = 0.95, iters: int = 300) -> np.ndarray:
    """RK95 (expected-shortfall form): equalise component CVaR by the
    multiplicative fixed point w_i <- w_i (mean / contribution_i)^(1/2)."""
    n = np.asarray(scenarios).shape[1]
    w = np.full(n, 1.0 / n)
    for _ in range(iters):
        cc = np.maximum(cvar_contributions(scenarios, w, alpha), 1e-12)
        w = w * np.sqrt(cc.mean() / cc)
        w /= w.sum()
    return w


# ---------------------------------------------------------------- Wasserstein mean-variance (RK225)


def wdro_mean_variance(
    returns, radius: float, target_return: float | None = None, long_only: bool = True
) -> np.ndarray:
    """Blanchet, Chen & Zhou: min (sqrt(w'Sw) + sqrt(delta) ||w||_2)^2 subject to
    w'mu - sqrt(delta) ||w||_2 >= target -- empirical variance plus a norm
    penalty, with the worst-case mean as the return constraint."""
    r = np.asarray(returns, float)
    mu, s = r.mean(0), np.cov(r.T)
    rd = np.sqrt(radius)

    def obj(w):
        return (np.sqrt(w @ s @ w + 1e-16) + rd * np.linalg.norm(w)) ** 2

    cons = ()
    if target_return is not None:
        cons = ({"type": "ineq", "fun": lambda w: w @ mu - rd * np.linalg.norm(w) - target_return},)
    return simplex_minimize(obj, len(mu), constraints=cons, long_only=long_only)


# ---------------------------------------------------------------- tensor factor rotation (RK205)


def cp_als(tensor, rank: int, iters: int = 200, rng=None) -> tuple[np.ndarray, ...]:
    """CP decomposition X_ijk ~ sum_r A_ir B_jr C_kr by alternating least squares."""
    x = np.asarray(tensor, float)
    rng = np.random.default_rng(rng)
    a, b, c = (rng.normal(size=(d, rank)) for d in x.shape)
    for _ in range(iters):
        a = np.einsum("ijk,jr,kr->ir", x, b, c) @ np.linalg.pinv((b.T @ b) * (c.T @ c))
        b = np.einsum("ijk,ir,kr->jr", x, a, c) @ np.linalg.pinv((a.T @ a) * (c.T @ c))
        c = np.einsum("ijk,ir,jr->kr", x, a, b) @ np.linalg.pinv((a.T @ a) * (b.T @ b))
    return a, b, c


def cp_reconstruct(a, b, c) -> np.ndarray:
    return np.einsum("ir,jr,kr->ijk", a, b, c)


def tensor_factor_rotation(
    tensor, rank: int = 2, target: int = 0, top: int = 2, rng=None
) -> np.ndarray:
    """RK205: tensor (time x sector x characteristic). Decompose, forecast each
    component's next time loading with an AR(1), rebuild next period's
    `target` characteristic (e.g. the return) per sector, and hold the `top`
    sectors equally (long-only)."""
    a, b, c = cp_als(tensor, rank, rng=rng)
    nxt = np.empty(rank)
    for r in range(rank):
        phi = np.polyfit(a[:-1, r], a[1:, r], 1)
        nxt[r] = np.polyval(phi, a[-1, r])
    score = (b * nxt) @ c[target]
    w = np.zeros(len(score))
    w[np.argsort(-score)[:top]] = 1.0 / top
    return w


# ---------------------------------------------------------------- Top-K dropout (RK216)


def topk_dropout(scores, holdings, k: int, n_drop: int) -> tuple[set, set, set]:
    """Qlib's rule: candidates = best (n_drop + k - held) non-holdings; sell the
    holdings that rank in the bottom n_drop of holdings+candidates; buy enough
    of the best candidates to get back to k. Returns (new holdings, sells, buys)."""
    s = np.asarray(scores, float)
    last = sorted(holdings, key=lambda i: -s[i])
    others = [int(i) for i in np.argsort(-s) if int(i) not in holdings]
    today = others[: max(n_drop + k - len(last), 0)]
    comb = sorted(last + today, key=lambda i: -s[i])
    bottom = set(comb[-n_drop:]) if n_drop else set()
    sell = {i for i in last if i in bottom}
    buy = set(today[: len(sell) + k - len(last)])
    return (set(last) - sell) | buy, sell, buy


# ---------------------------------------------------------------- sparse Bayesian factors (RK218)


def ard_factor_loadings(returns, factors, prune: float = 1e-3) -> np.ndarray:
    """ARD regression of each asset on the factors; loadings whose posterior
    precision prunes them are set to zero. Returns (assets x factors)."""
    r, f = np.atleast_2d(np.asarray(returns, float).T).T, np.asarray(factors, float)
    out = np.zeros((r.shape[1], f.shape[1]))
    for i in range(r.shape[1]):
        coef = ARDRegression(fit_intercept=True).fit(f, r[:, i]).coef_
        out[i] = np.where(np.abs(coef) > prune, coef, 0.0)
    return out


def dynamic_ard_loadings(returns, factors, window: int = 120, step: int = 20) -> dict:
    """Rolling ARD: {end index: loadings}, so factors can enter and leave."""
    r, f = np.asarray(returns, float), np.asarray(factors, float)
    return {
        t: ard_factor_loadings(r[t - window : t], f[t - window : t])
        for t in range(window, len(r) + 1, step)
    }


# ---------------------------------------------------------------- maximum entropy (RK222)


def entropy(w) -> float:
    w = np.clip(np.asarray(w, float), 1e-300, None)
    return float(-(w * np.log(w)).sum())


def maxent_weights(
    mu, cov=None, target_return: float | None = None, max_variance: float | None = None
) -> np.ndarray:
    """Bera & Park: the most diversified (maximum Shannon entropy) weights
    meeting a return floor and a variance cap."""
    mu = np.asarray(mu, float)
    cons = []
    if target_return is not None:
        cons.append({"type": "ineq", "fun": lambda w: w @ mu - target_return})
    if max_variance is not None:
        c = np.asarray(cov, float)
        cons.append({"type": "ineq", "fun": lambda w: max_variance - w @ c @ w})
    return simplex_minimize(lambda w: -entropy(w), len(mu), constraints=tuple(cons))


def drifted_weights(w, returns) -> np.ndarray:
    """Weights path when holdings are left alone: w_{t+1} ~ w_t (1 + r_t)."""
    out = [np.asarray(w, float)]
    for r in np.asarray(returns, float):
        x = out[-1] * (1 + r)
        out.append(x / x.sum())
    return np.array(out)


def entropy_production_rate(weights_path) -> np.ndarray:
    """dS/dt of a weights path (negative while drift concentrates the book)."""
    return np.diff([entropy(w) for w in np.asarray(weights_path, float)])


def mep_rebalance(returns, mu, cov=None, threshold: float = 0.02, **kw) -> dict:
    """RK222 as constructed here: hold the max-entropy weights and rebalance
    back to them whenever the entropy lost to drift since the last rebalance
    exceeds `threshold` nats."""
    target = maxent_weights(mu, cov, **kw)
    w, s0 = target.copy(), entropy(target)
    path, flags = [], []
    for r in np.asarray(returns, float):
        x = w * (1 + r)
        w = x / x.sum()
        flag = s0 - entropy(w) > threshold
        if flag:
            w = target.copy()
        path.append(w.copy())
        flags.append(flag)
    return {"weights": np.array(path), "rebalanced": np.array(flags), "target": target}


# ---------------------------------------------------------------- vine-copula CVaR (RK296)


def vine_cvar_weights(
    returns, alpha: float = 0.95, n_sim: int = 5000, min_tau: float = 0.05, rng=None
) -> np.ndarray:
    """Fit a truncated Clayton C-vine to the returns' pseudo-observations
    (root order: most-dependent variable first), simulate scenarios with the
    empirical marginals, and minimise their CVaR."""
    r = np.asarray(returns, float)
    u = pseudo_observations(r)
    n = r.shape[1]
    tau = np.array(
        [
            [stats.kendalltau(u[:, i], u[:, j])[0] if i != j else 0.0 for j in range(n)]
            for i in range(n)
        ]
    )
    order = np.argsort(-np.abs(tau).sum(1))
    sim = simulate_cvine(fit_cvine(u[:, order], min_tau), n_sim, rng)
    scen = np.empty_like(sim)
    scen[:, order] = empirical_quantile(r[:, order], sim)
    return cvar_weights(scen, alpha)


# ---------------------------------------------------------------- fractional VAR (RK392)


def fractional_var_allocation(log_prices, macro=None, window: int = 50) -> dict:
    """RK392: estimate each series' memory d (GPH, clipped to [0, 1]),
    fractionally difference it, fit a VAR(1) to the differenced panel
    (asset log prices + optional macro series), forecast one step and
    integrate back to a predicted log-price change per asset. Long-only
    weights proportional to the positive predicted changes."""
    p = np.asarray(log_prices, float)
    panel = p if macro is None else np.column_stack([p, np.asarray(macro, float)])
    n_assets = p.shape[1]
    ds = np.array([np.clip(gph_d(np.diff(col)) + 1.0, 0.0, 1.0) for col in panel.T])
    fd = np.column_stack([fracdiff(col, d, window) for col, d in zip(panel.T, ds, strict=True)])
    fd = fd[window - 1 :]
    nxt = var_forecast(fit_var(fd, 1), fd, 1)[0]
    pred = np.empty(panel.shape[1])
    for j, d in enumerate(ds):
        w = fracdiff_weights(d, window)
        pred[j] = nxt[j] - w[1:] @ panel[::-1, j][: window - 1]
    change = pred[:n_assets] - p[-1]
    pos = np.clip(change, 0, None)
    weights = pos / pos.sum() if pos.sum() > 0 else np.zeros(n_assets)
    return {"d": ds, "predicted_change": change, "weights": weights}
