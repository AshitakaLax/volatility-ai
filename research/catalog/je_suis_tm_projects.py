"""
je-suis-tm's PROJECTS (ledger section 5: Q6 Oil Money, Q11 Monte Carlo,
Q13 Portfolio Optimization, Q14 Smart Farmers, Q16 Wisdom of Crowds) --
the multi-file studies, as opposed to the single-script strategies in
je_suis_tm.py. None of them fits the platform (an FX/commodity regression
trade, a simulation used as a forecast, an agricultural planting plan,
analyst-forecast aggregation), which is why the ledger marks them ❌; they
are transcribed here so the database is complete.

Sources (quant-trading unless noted; copies in the session scratchpad):

  * Oil Money project/Oil Money Trading backtest.py -- `signal_generation`.
    Ore Money project/README.md announces the same strategy on iron ore and
    its exporters' currencies; it has no code, so it maps onto
    `oil_money_signals`.
  * Monte Carlo project/Monte Carlo backtest.py -- `monte_carlo`, `test`.
  * Smart Farmers project/forecast.py (the second `get_production`,
    `compute_price`, `ls_estimate`) and estimate demand.py
    (`create_xy`, `constrained_ols`); the README's 2SLS discussion.
  * Wisdom of Crowds project/dawid skene.ipynb and platt burges.ipynb.
  * je-suis-tm/graph-theory, Portfolio Optimization project/
    portfolio optimiziation.ipynb (`create_graph`, `degeneracy_ordering`,
    `clique_centrality`, `markowitz_optimization`) and its README.

The sources call statsmodels, scikit-learn, scipy, networkx and cvxopt.
None of those is a runtime dependency here, so the pieces are rebuilt in
numpy: OLS, a non-negative least-squares solve, Nelder-Mead, core numbers,
Bron-Kerbosch, and an active-set QP over the simplex. Each is pinned by a
test against a closed form or a brute force.

Source quirks preserved on purpose (each also documented at its function):

  * oil_money_signals: the holding counter exits on the 12th bar after
    entry (`counter > holding_threshold` checked before the increment).
  * smart_farmers_plan: the QP is handed to cvxopt as P = diag(alpha), and
    cvxopt minimises 1/2 x'Px, so the quadratic term is half the
    revenue model's. smart_farmers_price keeps the script's sign on the
    production term (`consistent=True` flips it to match the demand fit).
  * platt_burges: the script returns on convergence only when
    diagnosis=True (its default); this function always stops on
    convergence.
  * degeneracy_selection: "degeneracy ordering" is a stable sort by core
    number, not a smallest-last ordering.
"""

from __future__ import annotations

import math
from collections.abc import Callable, Sequence

import numpy as np
import pandas as pd

from engine.core.exceptions import ConfigurationError

# ---------------------------------------------------------------- shared numerics


def _ols_fit(y: np.ndarray, x: np.ndarray) -> tuple[np.ndarray, float, np.ndarray]:
    """y ~ const + x. Returns (params [const, slope...], R², fitted)."""
    design = np.column_stack([np.ones(len(y)), x])
    params = np.linalg.lstsq(design, y, rcond=None)[0]
    fitted = design @ params
    sst = float(((y - y.mean()) ** 2).sum())
    r2 = 1.0 - float(((y - fitted) ** 2).sum()) / sst if sst > 0 else 0.0
    return params, r2, fitted


def nnls(a, b, max_iter: int | None = None, tol: float = 1e-10) -> np.ndarray:
    """Lawson-Hanson non-negative least squares: argmin ||Ax - b|| s.t. x >= 0.
    Stands in for the cvxopt QP in estimate demand.py's `constrained_ols`."""
    a = np.asarray(a, dtype=float)
    b = np.asarray(b, dtype=float)
    n = a.shape[1]
    x = np.zeros(n)
    passive = np.zeros(n, dtype=bool)
    w = a.T @ (b - a @ x)
    for _ in range(max_iter or 3 * n + 10):
        if passive.all() or w[~passive].max(initial=-np.inf) <= tol:
            return x
        passive[int(np.argmax(np.where(passive, -np.inf, w)))] = True
        while True:
            z = np.zeros(n)
            if not passive.any():
                break
            z[passive] = np.linalg.lstsq(a[:, passive], b, rcond=None)[0]
            if z[passive].min() > tol:
                break
            # step back to the boundary and drop whatever hit zero
            neg = passive & (z <= tol) & (x > z)
            alpha = float(np.min(x[neg] / (x[neg] - z[neg]))) if neg.any() else 0.0
            x = x + alpha * (z - x)
            passive &= x > tol
        x = z
        w = a.T @ (b - a @ x)
    raise ConfigurationError("nnls did not converge")


def nelder_mead(
    f: Callable[[np.ndarray], float],
    x0,
    xatol: float = 1e-4,
    fatol: float = 1e-4,
    max_iter: int | None = None,
) -> np.ndarray:
    """Nelder-Mead with scipy's default (non-adaptive) coefficients and
    initial simplex (5% of each nonzero coordinate, 0.00025 for a zero
    one), stopping like scipy when both the simplex spread and the spread
    of function values are inside xatol/fatol. Smart Farmers calibrates
    its unobserved cost vector with scipy.optimize.minimize('Nelder-Mead')."""
    x0 = np.asarray(x0, dtype=float)
    n = len(x0)
    rho, chi, psi, sigma = 1.0, 2.0, 0.5, 0.5
    simplex = [x0]
    for k in range(n):
        y = x0.copy()
        y[k] = y[k] * 1.05 if y[k] != 0 else 0.00025
        simplex.append(y)
    pts = np.array(simplex)
    vals = np.array([f(p) for p in pts])
    for _ in range(max_iter or 200 * n):
        order = np.argsort(vals, kind="stable")
        pts, vals = pts[order], vals[order]
        if (
            np.max(np.abs(pts[1:] - pts[0])) <= xatol
            and np.max(np.abs(vals[1:] - vals[0])) <= fatol
        ):
            break
        centroid = pts[:-1].mean(axis=0)
        xr = centroid + rho * (centroid - pts[-1])
        fr = f(xr)
        if fr < vals[0]:
            xe = centroid + rho * chi * (centroid - pts[-1])
            fe = f(xe)
            pts[-1], vals[-1] = (xe, fe) if fe < fr else (xr, fr)
            continue
        if fr < vals[-2]:
            pts[-1], vals[-1] = xr, fr
            continue
        if fr < vals[-1]:  # outside contraction
            xc = centroid + psi * rho * (centroid - pts[-1])
            fc = f(xc)
            if fc <= fr:
                pts[-1], vals[-1] = xc, fc
                continue
        else:  # inside contraction
            xc = centroid - psi * (centroid - pts[-1])
            fc = f(xc)
            if fc < vals[-1]:
                pts[-1], vals[-1] = xc, fc
                continue
        pts[1:] = pts[0] + sigma * (pts[1:] - pts[0])  # shrink
        vals[1:] = [f(p) for p in pts[1:]]
    return pts[int(np.argmin(vals))]


def simplex_qp(p, q, tol: float = 1e-12, max_iter: int = 1000) -> np.ndarray:
    """Primal active-set solve of min 1/2 w'Pw + q'w s.t. w >= 0, sum(w) = 1
    -- the long-only, fully-invested QP that the portfolio notebook hands to
    cvxopt.solvers.qp. P must be positive definite on the simplex's tangent
    space (a covariance matrix of independent returns is)."""
    p = np.asarray(p, dtype=float)
    q = np.asarray(q, dtype=float)
    n = len(q)
    start = int(np.argmin(0.5 * np.diag(p) + q))  # best vertex: feasible
    w = np.zeros(n)
    w[start] = 1.0
    free = np.zeros(n, dtype=bool)
    free[start] = True
    for _ in range(max_iter):
        f = np.flatnonzero(free)
        m = len(f)
        kkt = np.zeros((m + 1, m + 1))
        kkt[:m, :m] = p[np.ix_(f, f)]
        kkt[:m, m] = kkt[m, :m] = 1.0
        sol = np.linalg.solve(kkt, np.concatenate([-q[f], [1.0]]))
        cand = np.zeros(n)
        cand[f] = sol[:m]
        if cand[f].min() >= -tol:
            w = np.clip(cand, 0.0, None)
            mult = p @ w + q + sol[m]  # bound multipliers on the fixed set
            fixed = np.flatnonzero(~free)
            if fixed.size == 0 or mult[fixed].min() >= -1e-10:
                return w
            free[fixed[int(np.argmin(mult[fixed]))]] = True
            continue
        block = f[cand[f] < -tol]
        ratios = w[block] / (w[block] - cand[block])
        j = int(np.argmin(ratios))
        w = w + ratios[j] * (cand - w)
        w[block[j]] = 0.0
        free[block[j]] = False
    raise ConfigurationError("simplex_qp did not converge")


# ---------------------------------------------------------------- Q6 Oil Money


def oil_money_signals(
    x,
    y,
    train_len: int = 50,
    rsquared_threshold: float = 0.7,
    holding_threshold: int = 10,
    stop: float = 0.5,
) -> pd.DataFrame:
    """Oil Money `signal_generation`: regress the currency `y` (NOK in the
    project) on the commodity `x` (Brent) over the trailing `train_len` bars
    (the current bar excluded). If R² > rsquared_threshold, project the fit
    forward with +/-1 and +/-2 sigma bands (sigma = population std of the
    training residuals). Long when y breaks above +2 sigma, short below
    -2 sigma -- the bet is that the currency's divergence from the
    commodity persists. On entry the bands collapse onto the forecast.

    Exit (signal = -holding) when the holding counter exceeds
    holding_threshold, or when |y - y_at_entry| >= stop. The counter is
    tested before it is incremented, so a position that never stops out
    closes on the 12th bar after entry with the default 10. After any exit
    the model is refitted on the next bar. Signals are +1/-1 at entries and
    the offsetting -holding at exits; positions are their cumulative sum.
    """
    xs = np.asarray(x, dtype=float)
    ys = np.asarray(y, dtype=float)
    if xs.shape != ys.shape or xs.ndim != 1:
        raise ConfigurationError("x and y must be 1-D and the same length")
    if train_len < 3:
        raise ConfigurationError(f"train_len must be >= 3, got {train_len}")
    n = len(ys)
    signals = np.zeros(n, dtype=int)
    forecast = np.zeros(n)
    bands = {k: np.zeros(n) for k in ("pos2 sigma", "neg2 sigma", "pos1 sigma", "neg1 sigma")}
    holding, trained, counter, entry_y = 0, False, 0, 0.0
    for i in range(train_len, n):
        if holding != 0:
            if counter > holding_threshold or abs(ys[i] - entry_y) >= stop:
                signals[i] = -holding
                holding, trained, counter = 0, False, 0
                continue
            counter += 1
            continue
        if not trained:
            params, r2, fitted = _ols_fit(ys[i - train_len : i], xs[i - train_len : i])
            if r2 > rsquared_threshold:
                trained = True
                sigma = float(np.std(ys[i - train_len : i] - fitted))
                forecast[i:] = params[0] + params[1] * xs[i:]
                bands["pos2 sigma"][i:] = forecast[i:] + 2 * sigma
                bands["neg2 sigma"][i:] = forecast[i:] - 2 * sigma
                bands["pos1 sigma"][i:] = forecast[i:] + sigma
                bands["neg1 sigma"][i:] = forecast[i:] - sigma
        if trained:
            side = (
                1 if ys[i] > bands["pos2 sigma"][i] else -1 if ys[i] < bands["neg2 sigma"][i] else 0
            )
            if side:
                signals[i] = side
                holding, entry_y = side, ys[i]
                for band in bands.values():
                    band[i:] = forecast[i:]
    return pd.DataFrame(
        {"forecast": forecast, **bands, "signals": signals, "positions": np.cumsum(signals)}
    )


# ---------------------------------------------------------------- Q11 Monte Carlo


def monte_carlo_forecast(
    close, test_size: float = 0.5, simulations: int = 100, seed: int | None = None
) -> dict:
    """Monte Carlo project `monte_carlo`: split the series in time
    (sklearn's train_test_split, shuffle=False: the test part is
    ceil(test_size * n) bars), estimate geometric Brownian motion on the
    training log returns -- drift = mean - var/2, volatility = std, both
    with pandas' ddof=1 -- and simulate `simulations` paths from the first
    close across train + test. The pick is the path whose residuals against
    the training closes have the smallest (population) standard deviation;
    its test segment is the forecast. The README's conclusion is that the
    best-fitted path predicts nothing -- the ledger's reason for ❌."""
    prices = np.asarray(close, dtype=float)
    n = len(prices)
    horizon = math.ceil(test_size * n)
    n_train = n - horizon
    if n_train < 3 or horizon < 1:
        raise ConfigurationError(f"cannot split {n} bars at test_size={test_size}")
    if simulations < 1:
        raise ConfigurationError("simulations must be >= 1")
    train = prices[:n_train]
    rets = np.log(train[1:] / train[:-1])
    drift = rets.mean() - rets.var(ddof=1) / 2
    vol = rets.std(ddof=1)
    rng = np.random.default_rng(seed)
    shocks = drift + vol * rng.standard_normal((simulations, n - 1))
    paths = train[0] * np.exp(
        np.concatenate([np.zeros((simulations, 1)), shocks], axis=1).cumsum(1)
    )
    fit_std = np.std(paths[:, :n_train] - train, axis=1)
    pick = int(np.argmin(fit_std))
    return {
        "horizon": horizon,
        "n_train": n_train,
        "drift": float(drift),
        "volatility": float(vol),
        "paths": paths,
        "pick": pick,
        "forecast": paths[pick, n_train:],
    }


def monte_carlo_direction_hit(close, forecast_path, n_train: int) -> int:
    """Monte Carlo project `test`: +1 if the best path's move over the test
    window has the same sign as the actual move, else -1. Both sides use the
    script's convention, close at the start of the test minus the last
    close."""
    prices = np.asarray(close, dtype=float)
    path = np.asarray(forecast_path, dtype=float)
    actual = np.sign(prices[n_train] - prices[-1])
    fitted = np.sign(path[n_train] - path[-1])
    return 1 if actual == fitted else -1


# ---------------------------------------------------------------- Q14 Smart Farmers


def smart_farmers_plan(
    price_hist,
    production_hist,
    area_hist,
    land_per_unit,
    land_total: float,
    alpha,
    beta,
    gamma,
    delta_pop: float,
    delta_gdp: float,
    cost,
    lower_fraction,
    upper: float = 1.2,
    tol: float = 1e-10,
) -> np.ndarray:
    """Smart Farmers forecast.py `get_production` (the demand-curve version):
    choose next year's production q per crop to solve

        min  sum_i 1/2 alpha_i q_i^2 + c_i q_i
        c  = -price_hist - alpha*production_hist - delta_pop*beta
             - delta_gdp*gamma + cost
        s.t. sum_i land_per_unit_i q_i = land_total
             area_hist_i * lower_fraction_i <= land_per_unit_i q_i
                                            <= area_hist_i * upper

    i.e. maximise revenue under the fitted inverse demand curve, minus the
    calibrated cost, on a fixed land budget. The lower bound is the share
    of perennial crops still inside their economic lifespan (the script's
    'eco lifespan' column), the upper the script's upperbound=1.2. The
    script passes P = diag(alpha) to cvxopt, whose objective is
    1/2 x'Px, so the quadratic term is half the revenue model's -- kept.

    The problem is separable with one coupling constraint, so instead of
    cvxopt it is solved exactly through its KKT conditions:
    q_i(lambda) = clip(-(c_i + lambda a_i) / alpha_i, bounds), with lambda
    found by bisection so the land constraint binds."""
    vec = lambda v: np.asarray(v, dtype=float)  # noqa: E731
    a, al = vec(land_per_unit), vec(alpha)
    if (a <= 0).any() or (al <= 0).any():
        raise ConfigurationError("land_per_unit and alpha must be positive")
    c = -vec(price_hist) - al * vec(production_hist) - delta_pop * vec(beta)
    c = c - delta_gdp * vec(gamma) + vec(cost)
    lo = vec(area_hist) * vec(lower_fraction) / a
    hi = vec(area_hist) * upper / a
    if (lo > hi).any() or not (a @ lo - tol <= land_total <= a @ hi + tol):
        raise ConfigurationError("land_total is outside what the bounds allow")
    land_total = min(max(land_total, a @ lo), a @ hi)

    def q_of(lam: float) -> np.ndarray:
        return np.clip(-(c + lam * a) / al, lo, hi)

    lam_lo, lam_hi = -1.0, 1.0
    while a @ q_of(lam_lo) < land_total:
        lam_lo *= 2
    while a @ q_of(lam_hi) > land_total:
        lam_hi *= 2
    for _ in range(400):
        mid = 0.5 * (lam_lo + lam_hi)
        if a @ q_of(mid) > land_total:
            lam_lo = mid
        else:
            lam_hi = mid
        if lam_hi - lam_lo <= 1e-14 * max(1.0, abs(mid)):
            break
    return q_of(0.5 * (lam_lo + lam_hi))


def smart_farmers_price(
    price_hist,
    production,
    production_hist,
    alpha,
    beta,
    gamma,
    delta_pop: float,
    delta_gdp: float,
    consistent: bool = False,
) -> np.ndarray:
    """forecast.py `compute_price`: price = price_hist + delta_pop*beta
    + delta_gdp*gamma + alpha*(production - production_hist). That raises
    price with production, opposite to the demand regression (whose
    regressor is -production with alpha >= 0); `consistent=True` uses
    -alpha*(production - production_hist) instead."""
    vec = lambda v: np.asarray(v, dtype=float)  # noqa: E731
    sign = -1.0 if consistent else 1.0
    change = vec(production) - vec(production_hist)
    return (
        vec(price_hist)
        + delta_pop * vec(beta)
        + delta_gdp * vec(gamma)
        + sign * vec(alpha) * change
    )


def smart_farmers_calibrate_cost(
    plan_for_cost: Callable[[np.ndarray], np.ndarray], actual_production, initial_cost
) -> np.ndarray:
    """forecast.py `costfunction` + `ls_estimate`: the unobserved per-crop
    cost is whatever makes the planned production match the actual, by
    Nelder-Mead on sum(((actual - planned) / actual)^2). `plan_for_cost`
    maps a cost vector to smart_farmers_plan's output for the same year.
    (The script's `find_init` restarts this from random fractions of the
    price and keeps the start with the best mean cost across years.)"""
    actual = np.asarray(actual_production, dtype=float)

    def loss(cost: np.ndarray) -> float:
        return float((((actual - plan_for_cost(cost)) / actual) ** 2).sum())

    return nelder_mead(loss, initial_cost)


def constrained_demand_ols(gdp, pop, production, price) -> dict[str, float]:
    """estimate demand.py `create_xy` + `constrained_ols`: per crop,
    price ~ constant + gamma*GDP + beta*population + alpha*(-production),
    with gamma, beta, alpha >= 0 and the constant free. Solved here as
    non-negative least squares on the demeaned data -- with a free
    intercept the two problems have the same slopes."""
    x = np.column_stack([gdp, pop, -np.asarray(production, dtype=float)]).astype(float)
    y = np.asarray(price, dtype=float)
    slopes = nnls(x - x.mean(axis=0), y - y.mean())
    const = float(y.mean() - x.mean(axis=0) @ slopes)
    return {"constant": const, "gamma": slopes[0], "beta": slopes[1], "alpha": slopes[2]}


def two_stage_least_squares(y, endog, exog, instruments) -> np.ndarray:
    """The Smart Farmers README's identification argument: price and
    quantity are simultaneous, so OLS of price on production is biased, and
    2-stage least squares with instruments for production recovers the
    demand slope. (The shipped code fits the constrained OLS above.)
    Returns [const, exog..., endog...]; instruments exclude the exogenous
    regressors, which instrument themselves."""
    col = lambda v: np.asarray(v, dtype=float).reshape(len(np.asarray(y)), -1)  # noqa: E731
    yy = np.asarray(y, dtype=float)
    ones = np.ones((len(yy), 1))
    ex = col(exog) if exog is not None else np.empty((len(yy), 0))
    en, z = col(endog), np.hstack([ones, ex, col(instruments)])
    if z.shape[1] < 1 + ex.shape[1] + en.shape[1]:
        raise ConfigurationError("2SLS needs at least as many instruments as endogenous terms")
    first = z @ np.linalg.lstsq(z, en, rcond=None)[0]
    return np.linalg.lstsq(np.hstack([ones, ex, first]), yy, rcond=None)[0]


# ---------------------------------------------------------------- Q16 Wisdom of Crowds


def dawid_skene(matrix, init_truth: Sequence[int] | None = None, max_iter: int = 100):
    """dawid skene.ipynb, hard-label EM over a forecasters x items matrix of
    class labels 0..K-1 (the notebook maps forecast directions -1/+1 to
    0/1). Initial truth is the per-item majority, ties to the smaller label
    (scipy.stats.mode). Then repeat until the truth stops changing:

      * confusion matrix per forecaster against the current truth, rows
        normalised (sklearn normalize='true'; an empty row stays zero);
      * each item's new label = argmax over classes of
        P(class) * prod_forecasters CM[class, forecast], P(class) being the
        class frequency in the current truth; ties to the smaller label.

    Returns (truth, iterations). The notebook's own example
    [[1,1,0,1,1],[0,0,0,1,1],[1,0,1,0,0]] goes from [1,0,0,1,1] to
    [0,1,0,1,1] in 2 iterations."""
    m = np.asarray(matrix)
    if m.ndim != 2 or m.size == 0:
        raise ConfigurationError("matrix must be a non-empty forecasters x items array")
    labels = m.astype(int)
    k = int(labels.max()) + 1
    if init_truth is None:
        truth = [int(np.argmax(np.bincount(col, minlength=k))) for col in labels.T]
    else:
        truth = [int(t) for t in init_truth]
    for iteration in range(1, max_iter + 1):
        t = np.asarray(truth)
        cms = []
        for row in labels:
            cm = np.zeros((k, k))
            np.add.at(cm, (t, row), 1.0)
            sums = cm.sum(axis=1, keepdims=True)
            cms.append(np.divide(cm, sums, out=np.zeros_like(cm), where=sums > 0))
        prior = np.bincount(t, minlength=k) / len(t)
        new = []
        for item in range(labels.shape[1]):
            post = prior.copy()
            for cm, row in zip(cms, labels, strict=True):
                post = post * cm[:, row[item]]
            new.append(int(np.argmax(post)))
        if new == truth:
            return truth, iteration
        truth = new
    raise ConfigurationError(f"dawid_skene did not converge in {max_iter} iterations")


def platt_burges(x, tolerance: float = 1e-3, max_iter: int = 200) -> dict:
    """platt burges.ipynb: x[r, p] = y_p + z_r + noise, rows r the raters
    (banks), columns p the items (commodities), with y_p ~ N(mu_p, sigma_p),
    z_r ~ N(nu_r, tau_r) the rater bias, noise variance fixed at the
    variance of the whole matrix (sigma_p, tau_r, sigma are variances).
    Initialised at the column/row means and population variances, then EM:

      E: s = sigma + sigma_p + tau_r, e = x - mu_p - nu_r
         E[y] = mu_p + sigma_p/s * e,   Var[y] = (tau_r + sigma) sigma_p / s
         E[z] = nu_r + tau_r/s * e,     Var[z] = (sigma_p + sigma) tau_r / s
      M: mu_p = column mean of E[y]; nu_r = row mean of E[z];
         sigma_p = column mean of Var[y] + (E[y] - mu_p)^2; tau_r likewise
         by row,

    stopping when the lower bound sum(log 1/(sigma_p tau_r) - var_y/2sigma_p
    - var_z/2tau_r) changes by less than `tolerance` relatively. Returns the
    item estimates mu_p and sigma_p, the rater biases nu_r and tau_r, the
    iteration count and whether it converged.

    Each item is one draw of y_p with its own free mean, so sigma_p and
    tau_r shrink toward zero as EM runs and the bound grows without limit;
    the relative-change stop is what ends the run (the notebook's 112 and
    121 iterations). The means settle long before that."""
    xm = np.asarray(x, dtype=float)
    if xm.ndim != 2 or min(xm.shape) < 2:
        raise ConfigurationError("x must be a raters x items matrix, at least 2 x 2")
    if (xm.var(axis=0) == 0).any() or (xm.var(axis=1) == 0).any():
        raise ConfigurationError("every row and column needs nonzero variance")
    rows, cols = xm.shape
    mu_p = np.tile(xm.mean(axis=0), (rows, 1))
    sigma_p = np.tile(xm.var(axis=0), (rows, 1))
    nu_r = np.tile(xm.mean(axis=1)[:, None], (1, cols))
    tau_r = np.tile(xm.var(axis=1)[:, None], (1, cols))
    sigma = xm.var()
    old, iteration, converged = None, 0, False
    while iteration < max_iter and not converged:
        iteration += 1
        s = sigma + sigma_p + tau_r
        e = xm - mu_p - nu_r
        ey, ez = mu_p + sigma_p / s * e, nu_r + tau_r / s * e
        vy, vz = (tau_r + sigma) * sigma_p / s, (sigma_p + sigma) * tau_r / s
        mu_p = np.tile(ey.mean(axis=0), (rows, 1))
        nu_r = np.tile(ez.mean(axis=1)[:, None], (1, cols))
        sigma_p = np.tile((vy + (ey - mu_p) ** 2).mean(axis=0), (rows, 1))
        tau_r = np.tile((vz + (ez - nu_r) ** 2).mean(axis=1)[:, None], (1, cols))
        var_y = vy + (ey - mu_p) ** 2
        var_z = vz + (ez - nu_r) ** 2
        bound = float(
            (np.log(1.0 / (sigma_p * tau_r)) - var_y / sigma_p / 2 - var_z / tau_r / 2).sum()
        )
        converged = bool(old) and abs(bound / old - 1) < tolerance
        old = bound
    return {
        "mu_p": mu_p[0],
        "sigma_p": sigma_p[0],
        "nu_r": nu_r[:, 0],
        "tau_r": tau_r[:, 0],
        "iterations": iteration,
        "converged": converged,
    }


# ---------------------------------------------------------------- Q13 graph portfolio


def correlation_graph(correlation: pd.DataFrame, threshold: float = 0.6) -> dict:
    """graph-theory `create_graph`: an undirected edge between every pair of
    components whose return correlation exceeds `threshold` (0.6 in the
    notebook). Returns {node: set(neighbours)} in networkx's node insertion
    order (pairs visited i < j); components with no edge are absent."""
    names = list(correlation.columns)
    adj: dict = {}
    for i, a in enumerate(names):
        for b in names[i + 1 :]:
            if correlation.at[a, b] > threshold:
                adj.setdefault(a, set()).add(b)
                adj.setdefault(b, set()).add(a)
    return adj


def core_numbers(adj: dict) -> dict:
    """k-core number of every vertex (networkx.core_number): peel the
    minimum-degree vertex repeatedly; its core number is the largest
    minimum degree seen so far. Keys keep `adj`'s order."""
    degree = {v: len(nb) for v, nb in adj.items()}
    remaining = set(adj)
    core: dict = {}
    k = 0
    while remaining:
        v = min(remaining, key=lambda u: degree[u])
        k = max(k, degree[v])
        core[v] = k
        remaining.discard(v)
        for u in adj[v]:
            if u in remaining:
                degree[u] -= 1
    return {v: core[v] for v in adj}


def degeneracy_selection(correlation: pd.DataFrame, threshold: float = 0.6) -> tuple[list, list]:
    """graph-theory `degeneracy_ordering`: sort the graph's vertices by core
    number (a stable sort, so ties keep insertion order), keep each vertex
    that has no neighbour already kept -- an independent set of weakly
    correlated components -- and add every component with no edge at all
    ('leftout'). Returns (independent set, leftout). The notebook's
    "Degeneracy Index" is the price sum of leftout + independent set, and
    it was the out-of-sample winner in the README."""
    adj = correlation_graph(correlation, threshold)
    chosen: list = []
    for v, _ in sorted(core_numbers(adj).items(), key=lambda kv: kv[1]):
        if not adj[v].intersection(chosen):
            chosen.append(v)
    leftout = [c for c in correlation.columns if c not in adj]
    return chosen, leftout


def maximal_cliques(adj: dict) -> list[list]:
    """All maximal cliques, Bron-Kerbosch with Tomita pivoting (what
    networkx.find_cliques runs)."""
    out: list[list] = []
    if not adj:
        return out

    def expand(r: list, p: set, x: set) -> None:
        if not p and not x:
            out.append(r)
            return
        pivot = max(p | x, key=lambda u: len(adj[u] & p))
        for v in list(p - adj[pivot]):
            expand([*r, v], p & adj[v], x & adj[v])
            p.discard(v)
            x.add(v)

    expand([], set(adj), set())
    return out


def clique_centrality_selection(
    correlation: pd.DataFrame, threshold: float = 0.6, centrality: int = 10
) -> list:
    """graph-theory `clique_centrality`: count, for every vertex, how many
    maximal cliques contain it, and keep the vertices whose count is
    strictly above `centrality` (10 in the notebook) -- the hubs of the
    correlation graph, equal-weighted into the "Clique Index"."""
    adj = correlation_graph(correlation, threshold)
    counts = dict.fromkeys(adj, 0)
    for clique in maximal_cliques(adj):
        for v in clique:
            counts[v] += 1
    return [v for v, n in counts.items() if n > centrality]


def basket_index(prices: pd.DataFrame, members: Sequence) -> pd.Series:
    """The notebook's index construction: the plain sum of member prices
    (`data[members].sum(axis=1)`), i.e. one share of each."""
    return prices[list(members)].sum(axis=1)


def markowitz_weights(returns: pd.DataFrame, risk_aversion: float = 1.0) -> dict[str, np.ndarray]:
    """graph-theory `markowitz_optimization`, long-only and fully invested:

      * max_sharpe:   min 1/2 w'(risk_aversion*Cov)w - mean'w (the README's
                      "risk aversion parameter", set to 1);
      * min_variance: min 1/2 w'Cov w;
      * max_return:   min -mean'w, a linear programme: everything in the
                      highest-mean asset (first one on a tie).

    Cov is np.cov of the returns (ddof=1), mean the column means. The README
    notes the max-Sharpe weights come out close to max-return ones and do
    worst out of sample."""
    r = np.asarray(returns, dtype=float)
    if r.ndim != 2 or r.shape[0] < 2:
        raise ConfigurationError("returns must be an observations x assets matrix")
    cov = np.cov(r.T)
    mean = r.mean(axis=0)
    max_return = np.zeros(len(mean))
    max_return[int(np.argmax(mean))] = 1.0
    return {
        "max_sharpe": simplex_qp(risk_aversion * cov, -mean),
        "min_variance": simplex_qp(cov, np.zeros(len(mean))),
        "max_return": max_return,
    }
