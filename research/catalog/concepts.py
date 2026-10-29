"""
The 34 researched concepts shared by ranks 426-700 of the ranked list
(docs/algorithms/concepts/): twelve approaches to momentum/trend
forecasting, eleven to factor risk-parity allocation, five to covariance
estimation, four to tail-risk hedging, and one model each for sector and
regime-aware allocation. Each function is keyed to its concept page by
the CONCEPTS table at the bottom. Trend and tail functions are
single-instrument and long-only (1 = hold, 0 = flat, fractions = scaled
exposure); the allocation and covariance ones need a multi-asset book.
Research code only: the pages record that most of these approaches have
no study behind them.

Sources (beyond the catalog modules reused here):

  * Trend filters -- Bruder, Dao, Richard & Roncalli, "Trend filtering
    methods for momentum strategies", Lyxor 2011; L1 trend filtering -- Kim,
    Koh, Boyd & Gorinevsky, SIAM Rev. 51, 2009 (solved by ADMM here).
  * Adaptive speed -- Kaufman, "Smarter Trading", 1995 (efficiency-ratio
    moving average); Garg, Goulding, Harvey & Mazzoleni, "Momentum turning
    points", J. Financial Econ. 141, 2021 (slow/fast blends by cycle state).
  * Adaptive conformal inference -- Gibbs & Candes, NeurIPS 2021.
  * Momentum crashes -- Daniel & Moskowitz, J. Financial Econ. 122, 2016;
    Clayton lower-tail dependence 2^(-1/theta) -- Nelsen, 2006.
  * ARFIMA prediction from the AR(infinity) form of (1 - L)^d -- Hosking 1981.
  * Factor risk parity -- Roncalli & Weisang, "Risk parity portfolios with
    risk factors", Quantitative Finance 16, 2016.
  * Robust covariance -- Rousseeuw's minimum covariance determinant (sklearn)
    and Tyler, Ann. Statist. 15, 1987 (shape M-estimator); DeMiguel &
    Nogales, Oper. Res. 57, 2009.
  * Lead-lag signatures recover quadratic covariation -- Flint, Hambly &
    Lyons, Stoch. Proc. Appl. 126, 2016.
  * CAViaR -- Engle & Manganelli, J. Bus. Econ. Stat. 22, 2004 (symmetric
    absolute value specification, fitted by the quantile loss); peaks over
    threshold -- McNeil & Frey, J. Empirical Finance 7, 2000.
  * Wavelet variance -- Percival & Walden, "Wavelet Methods for Time Series
    Analysis", 2000.
  * Early warnings of critical transitions (rising autocorrelation and
    variance) -- Scheffer et al., Nature 461, 2009.
  * Industry momentum -- Moskowitz & Grinblatt, J. Finance 54, 1999.
"""

from __future__ import annotations

import numpy as np
from scipy import stats
from scipy.linalg import cho_factor, cho_solve
from scipy.optimize import minimize
from sklearn.covariance import LedoitWolf, MinCovDet
from sklearn.decomposition import KernelPCA
from sklearn.kernel_ridge import KernelRidge

from engine.core.exceptions import ConfigurationError
from research.catalog.allocation import cvar_risk_parity, min_variance_weights, simplex_minimize
from research.catalog.autodiff import Tensor, fit, mse, param
from research.catalog.deep_rl import genetic_search
from research.catalog.econometrics import (
    dcc_fit,
    empirical_quantile,
    fit_cvine,
    fracdiff_weights,
    garch11_fit,
    garch11_forecast,
    gph_d,
    pseudo_observations,
    simulate_cvine,
)
from research.catalog.generative import DDPM
from research.catalog.koopman import edmd, koopman_predict, poly_dictionary
from research.catalog.neural_models import causal_haar
from research.catalog.spd_covariance import (
    GATShrinkage,
    geodesic_smoothed_covariances,
    karcher_mean,
    rolling_covariances,
    spd_exp,
    spd_log,
)
from research.catalog.topology import landscape_norm_series
from research.strategies.position_sizing import split_conformal_interval
from research.strategies.regime_models import GaussianHMM

# ================================================================ momentum / trend forecasting


def kalman_trend(prices, q_level: float = 1e-5, q_slope: float = 1e-7, r: float = 1e-4) -> dict:
    """Stochastic-process trend: local linear trend model on log prices,
    level_{t+1} = level + slope + w, slope_{t+1} = slope + v; returns the
    filtered slope (drift) and long-only positions on its sign."""
    y = np.log(np.asarray(prices, float))
    x, p = np.array([y[0], 0.0]), np.eye(2)
    f = np.array([[1.0, 1.0], [0.0, 1.0]])
    q = np.diag([q_level, q_slope])
    slopes = np.empty(len(y))
    for t, obs in enumerate(y):
        x, p = f @ x, f @ p @ f.T + q
        s = p[0, 0] + r
        k = p[:, 0] / s
        x, p = x + k * (obs - x[0]), p - np.outer(k, p[0])
        slopes[t] = x[1]
    return {"slope": slopes, "positions": (slopes > 0).astype(float)}


def l1_trend_filter(series, lam: float = 10.0, rho: float = 1.0, iters: int = 500) -> np.ndarray:
    """Kim et al.'s l1 trend filter, min 1/2 ||y - x||^2 + lam ||D2 x||_1, by
    ADMM (z = D2 x): a piecewise-linear trend whose kinks mark regime changes."""
    y = np.asarray(series, float)
    n = len(y)
    d = np.diff(np.eye(n), 2, axis=0)
    factor = cho_factor(np.eye(n) + rho * d.T @ d)  # constant across iterations
    z = np.zeros(n - 2)
    u = np.zeros(n - 2)
    for _ in range(iters):
        x = cho_solve(factor, y + rho * d.T @ (z - u))
        dx = d @ x
        z = np.sign(dx + u) * np.maximum(np.abs(dx + u) - lam / rho, 0)
        u += dx - z
    return x


def l1_trend_positions(prices, window: int = 120, lam: float = 5.0) -> np.ndarray:
    """Causal use of the l1 filter: on each trailing window of log prices, hold
    while the fitted trend's final slope is positive."""
    lp = np.log(np.asarray(prices, float))
    out = np.zeros(len(lp))
    for t in range(window, len(lp)):
        x = l1_trend_filter(lp[t - window : t + 1], lam, iters=200)
        out[t] = float(x[-1] > x[-2])
    return out


def kama(prices, n: int = 10, fast: int = 2, slow: int = 30) -> np.ndarray:
    """Adaptive: Kaufman's moving average, smoothing constant
    (ER (2/(fast+1) - 2/(slow+1)) + 2/(slow+1))^2 with ER the efficiency ratio."""
    p = np.asarray(prices, float)
    out = np.full(len(p), np.nan)
    out[n - 1] = p[n - 1]
    fs, ss = 2 / (fast + 1), 2 / (slow + 1)
    for t in range(n, len(p)):
        change = abs(p[t] - p[t - n])
        vol = np.abs(np.diff(p[t - n : t + 1])).sum()
        er = change / vol if vol > 0 else 0.0
        sc = (er * (fs - ss) + ss) ** 2
        out[t] = out[t - 1] + sc * (p[t] - out[t - 1])
    return out


def cycle_blended_momentum(
    prices, fast: int = 21, slow: int = 252, train: int | None = None
) -> dict:
    """Adaptive (Garg et al.): states Bull (slow+, fast+), Bear (-, -),
    Correction (+, -) and Rebound (-, +). Agreeing states take the common
    sign; in Correction and Rebound the blend a x slow + (1 - a) x fast uses
    the a in {0, 0.5, 1} with the best training-period conditional return.
    Long-only positions = max(blend, 0)."""
    p = np.asarray(prices, float)
    sig_s = np.r_[np.zeros(slow), np.sign(p[slow:] / p[:-slow] - 1)]
    sig_f = np.r_[np.zeros(fast), np.sign(p[fast:] / p[:-fast] - 1)]
    nxt = np.r_[np.diff(np.log(p)), 0.0]
    train = train or len(p) // 2
    alphas = {}
    for name, mask in (
        ("correction", (sig_s > 0) & (sig_f < 0)),
        ("rebound", (sig_s < 0) & (sig_f > 0)),
    ):
        m = mask[:train]
        scores = {
            a: float(((a * sig_s + (1 - a) * sig_f)[:train][m] * nxt[:train][m]).mean())
            if m.any()
            else 0.0
            for a in (0.0, 0.5, 1.0)
        }
        alphas[name] = max(scores, key=scores.get)
    blend = np.where(sig_s == sig_f, sig_s, 0.0)
    corr, reb = (sig_s > 0) & (sig_f < 0), (sig_s < 0) & (sig_f > 0)
    blend[corr] = (alphas["correction"] * sig_s + (1 - alphas["correction"]) * sig_f)[corr]
    blend[reb] = (alphas["rebound"] * sig_s + (1 - alphas["rebound"]) * sig_f)[reb]
    return {"blend": blend, "alphas": alphas, "positions": np.clip(blend, 0, None)}


def hmm_trend(returns, n_states: int = 2, seed: int = 0) -> dict:
    """Markov-state: fit a Gaussian HMM; the one-step forecast is
    sum_j P(state_{t+1} = j | data to t) mu_j; hold when it is positive.
    (Parameters are fitted on the whole sample here -- pass a training
    slice to keep it causal.)"""
    r = np.asarray(returns, float)
    hmm = GaussianHMM(n_states, seed=seed).fit(r)
    filt = hmm.filter(r)
    forecast = (filt @ hmm.trans) @ hmm.mu
    return {"forecast": forecast, "positions": (forecast > 0).astype(float), "model": hmm}


def adaptive_conformal_positions(
    predictions, outcomes, alpha: float = 0.1, gamma: float = 0.01, calibration: int = 100
) -> dict:
    """Conformal: adaptive conformal inference around a trend forecast. Each
    day the interval uses the trailing `calibration` absolute residuals at
    level alpha_t, updated alpha_{t+1} = alpha_t + gamma (alpha - miss_t);
    hold (size 1 / width, capped at 1) when the interval excludes zero
    from below."""
    pred, y = np.asarray(predictions, float), np.asarray(outcomes, float)
    a = alpha
    pos, cover = np.zeros(len(pred)), []
    for t in range(calibration, len(pred)):
        resid = y[t - calibration : t] - pred[t - calibration : t]
        lo, hi = split_conformal_interval(pred[t], resid, float(np.clip(a, 1e-3, 0.999)))
        if lo > 0:
            pos[t] = min(1.0, (abs(pred[t]) + 1e-12) / (hi - lo))
        miss = float(not lo <= y[t] <= hi)
        cover.append(1 - miss)
        a += gamma * (alpha - miss)
    return {"positions": pos, "coverage": float(np.mean(cover)) if cover else np.nan}


def spectral_trend_positions(prices, window: int = 128, keep: int = 3) -> np.ndarray:
    """Spectral: on each trailing window of detrended log prices, keep the
    lowest `keep` Fourier modes and add the linear trend back; hold while the
    reconstruction rises at the window's end (an end-of-window estimate,
    with the usual edge effect)."""
    lp = np.log(np.asarray(prices, float))
    out = np.zeros(len(lp))
    tt = np.arange(window + 1)
    for t in range(window, len(lp)):
        seg = lp[t - window : t + 1]
        b, a = np.polyfit(tt, seg, 1)
        resid = seg - (a + b * tt)
        coef = np.fft.rfft(resid)
        coef[keep + 1 :] = 0
        smooth = np.fft.irfft(coef, n=len(seg)) + a + b * tt
        out[t] = float(smooth[-1] > smooth[-2])
    return out


def bayesian_drift(
    returns,
    prior_mean: float = 0.0,
    prior_strength: float = 20.0,
    discount: float = 0.99,
    threshold: float = 0.6,
) -> dict:
    """Bayesian: Normal-inverse-gamma posterior on the drift with exponential
    forgetting; P(mu > 0) is a Student-t probability; hold above `threshold`."""
    r = np.asarray(returns, float)
    k, m, a, b = prior_strength, prior_mean, 2.0, 2.0 * np.var(r[: min(50, len(r))]) + 1e-12
    prob = np.empty(len(r))
    for t, x in enumerate(r):
        k, a, b = discount * k, discount * a, discount * b
        k_new = k + 1
        m_new = (k * m + x) / k_new
        a, b = a + 0.5, b + k * (x - m) ** 2 / (2 * k_new)
        k, m = k_new, m_new
        scale = np.sqrt(b / (a * k))
        prob[t] = stats.t.cdf(m / scale, df=2 * a)
    return {"p_positive": prob, "positions": (prob > threshold).astype(float)}


def robust_momentum(prices, lookback: int = 126, method: str = "theil_sen") -> np.ndarray:
    """Robust: trailing trend from the Theil-Sen slope of log prices (or the
    median daily return); outliers cannot flip it. Long when positive."""
    lp = np.log(np.asarray(prices, float))
    if method not in ("theil_sen", "median"):
        raise ConfigurationError("method must be theil_sen or median")
    out = np.zeros(len(lp))
    for t in range(lookback, len(lp)):
        seg = lp[t - lookback : t + 1]
        slope = stats.theilslopes(seg)[0] if method == "theil_sen" else np.median(np.diff(seg))
        out[t] = float(slope > 0)
    return out


def clayton_lower_tail(u, v) -> float:
    tau = stats.kendalltau(u, v)[0]
    return float(2 ** (-1 / (2 * tau / (1 - tau)))) if tau > 0 else 0.0


def copula_momentum_positions(
    prices, market_prices, lookback: int = 252, window: int = 250, bear_lookback: int = 504
) -> dict:
    """Copula: time-series momentum, cut by the Clayton lower-tail dependence
    with the market (from trailing pseudo-observations) whenever the market's
    two-year return is negative -- Daniel and Moskowitz's crash state."""
    p, mk = np.asarray(prices, float), np.asarray(market_prices, float)
    rp, rm = np.diff(np.log(p)), np.diff(np.log(mk))
    pos, lam = np.zeros(len(p)), np.zeros(len(p))
    for t in range(max(lookback, window, bear_lookback) + 1, len(p)):
        base = float(p[t] > p[t - lookback])
        if mk[t] < mk[t - bear_lookback]:
            u = pseudo_observations(np.column_stack([rp[t - window : t], rm[t - window : t]]))
            lam[t] = clayton_lower_tail(u[:, 0], u[:, 1])
            base *= 1 - lam[t]
        pos[t] = base
    return {"positions": pos, "tail_dependence": lam}


def kernel_trend_forecast(
    prices,
    horizons=(5, 21, 63, 126),
    target: int = 21,
    train: int | None = None,
    alpha: float = 1.0,
) -> dict:
    """Nonlinear: kernel ridge (RBF) from multi-horizon past returns to the
    next `target`-day return, trained on the first `train` rows; hold when the
    forecast is positive."""
    lp = np.log(np.asarray(prices, float))
    m = max(horizons)
    idx = np.arange(m, len(lp) - target)
    x = np.column_stack([lp[idx] - lp[idx - h] for h in horizons])
    y = lp[idx + target] - lp[idx]
    train = train or len(idx) // 2
    mu, sd = x[:train].mean(0), x[:train].std(0) + 1e-12
    model = KernelRidge(alpha=alpha, kernel="rbf").fit((x[:train] - mu) / sd, y[:train])
    f = model.predict((x[train:] - mu) / sd)
    return {"forecast": f, "positions": (f > 0).astype(float), "actual": y[train:]}


def arfima_forecast(returns, window: int = 100) -> dict:
    """Fractional-order: estimate d by GPH, then forecast the next return from
    the AR(infinity) form of (1 - L)^d, x_{t+1} = -sum_{k>=1} pi_k x_{t+1-k},
    with the binomial weights pi truncated at `window`."""
    r = np.asarray(returns, float) - np.mean(returns)
    d = float(np.clip(gph_d(r), -0.45, 0.45))
    pi = fracdiff_weights(d, window)
    forecast = np.full(len(r), np.nan)
    for t in range(window - 1, len(r)):
        forecast[t] = -(pi[1:] @ r[t - window + 2 : t + 1][::-1])
    return {
        "d": d,
        "forecast": forecast + np.mean(returns),
        "positions": (np.nan_to_num(forecast) > 0).astype(float),
    }


def diffusion_trend(
    returns,
    window: int = 10,
    horizon: int = 5,
    train: int | None = None,
    n_samples: int = 200,
    steps: int = 300,
    seed: int = 0,
) -> dict:
    """Diffusion-model: a conditional DDPM learns the next `horizon`-day
    cumulative return given the last `window` returns; P(cumulative > 0) from
    its samples drives a long-only position (hold above 0.5)."""
    r = np.asarray(returns, float)
    xs = np.array([r[t - window : t] for t in range(window, len(r) - horizon)])
    ys = np.array([r[t : t + horizon].sum() for t in range(window, len(r) - horizon)])[:, None]
    train = train or len(xs) * 2 // 3
    model = DDPM(1, cond_dim=window, hidden=32, seed=seed)
    model.fit(ys[:train], xs[:train], steps=steps)
    p_up = np.array(
        [(model.sample(n_samples, cond=c, rng=seed).ravel() > 0).mean() for c in xs[train:]]
    )
    return {"p_up": p_up, "positions": (p_up > 0.5).astype(float), "actual": ys[train:, 0]}


def topology_filtered_trend(
    prices, panel_returns, lookback: int = 126, window: int = 30, z: float = 2.0
) -> dict:
    """Topology-aware: time-series momentum held only while the persistence-
    landscape norm of the multi-asset point cloud is not in a stress spike
    (trailing z-score above z)."""
    p = np.asarray(prices, float)
    norms = landscape_norm_series(panel_returns, window=window)
    pos = np.zeros(len(p))
    for t in range(max(lookback, 2 * window), len(p)):
        hist = norms[t - window : t]
        hist = hist[np.isfinite(hist)]
        stressed = len(hist) > 2 and (norms[t] - hist.mean()) / (hist.std() + 1e-12) > z
        pos[t] = float(p[t] > p[t - lookback] and not stressed)
    return {"positions": pos, "landscape_norm": norms}


# ================================================================ factor risk parity


def factor_risk_contributions(w, loadings, factor_cov, specific_var=None) -> np.ndarray:
    """Roncalli-Weisang: with exposures y = B'w, factor j's contribution to
    variance is y_j (Sigma_f y)_j; the specific part is sum w_i^2 s_i (last)."""
    w, b, cf = (np.asarray(a, float) for a in (w, loadings, factor_cov))
    y = b.T @ w
    rc = y * (cf @ y)
    spec = 0.0 if specific_var is None else float((w**2 * np.asarray(specific_var, float)).sum())
    return np.r_[rc, spec] / (rc.sum() + spec)


def factor_risk_parity(
    loadings, factor_cov, specific_var=None, budgets=None, x0=None
) -> np.ndarray:
    """Long-only weights whose factor risk contributions match `budgets`
    (equal by default), solved by SLSQP on squared deviations."""
    b = np.asarray(loadings, float)
    k = b.shape[1]
    bud = np.full(k, 1.0 / k) if budgets is None else np.asarray(budgets, float) / np.sum(budgets)

    def obj(w):
        rc = factor_risk_contributions(w, b, factor_cov, specific_var)[:k]
        rc = rc / (rc.sum() + 1e-16)
        return float(((rc - bud) ** 2).sum()) * 1e3

    return simplex_minimize(obj, b.shape[0], x0=x0)


def loadings_from_returns(asset_returns, factor_returns) -> tuple[np.ndarray, np.ndarray]:
    """OLS loadings (assets x factors) and specific variances."""
    r, f = np.asarray(asset_returns, float), np.asarray(factor_returns, float)
    x = np.column_stack([np.ones(len(f)), f])
    coef = np.linalg.lstsq(x, r, rcond=None)[0]
    resid = r - x @ coef
    return coef[1:].T, resid.var(0)


def robust_factor_risk_parity(asset_returns, factor_returns, seed: int = 0) -> np.ndarray:
    """Robust: factor covariance by minimum covariance determinant."""
    b, s = loadings_from_returns(asset_returns, factor_returns)
    cf = MinCovDet(random_state=seed).fit(np.asarray(factor_returns, float)).covariance_
    return factor_risk_parity(b, cf, s)


def attention_budgets(factor_features, v) -> np.ndarray:
    """Softmax attention over factors: budgets = softmax(features @ v)."""
    z = np.asarray(factor_features, float) @ np.asarray(v, float)
    e = np.exp(z - z.max())
    return e / e.sum()


def attention_factor_risk_parity(
    asset_returns, factor_returns, window: int = 60, gens: int = 10, rng=None
) -> dict:
    """Attention-weighted: factor features (trailing mean, volatility,
    Sharpe) are scored by attention vector v, whose softmax sets the risk
    budgets; v is evolved for the in-sample Sharpe of the budgeted book."""
    r, f = np.asarray(asset_returns, float), np.asarray(factor_returns, float)
    b, s = loadings_from_returns(r, f)
    cf = np.cov(f.T)
    tail = f[-window:]
    feats = np.column_stack([tail.mean(0), tail.std(0), tail.mean(0) / (tail.std(0) + 1e-12)])
    feats = (feats - feats.mean(0)) / (feats.std(0) + 1e-12)

    def fitness(v):
        w = factor_risk_parity(b, cf, s, attention_budgets(feats, v))
        pr = r @ w
        return float(pr.mean() / (pr.std() + 1e-12))

    out = genetic_search(fitness, 3, pop=8, gens=gens, rng=rng)
    budgets = attention_budgets(feats, out["best"])
    return {"budgets": budgets, "weights": factor_risk_parity(b, cf, s, budgets)}


def geodesic_factor_risk_parity(
    asset_returns, factor_returns, window: int = 60, alpha: float = 0.2
) -> np.ndarray:
    """Dynamical-systems/geometric: the factor covariance smoothed along
    affine-invariant geodesics through time (the last smoothed estimate)."""
    b, s = loadings_from_returns(asset_returns, factor_returns)
    cf = geodesic_smoothed_covariances(factor_returns, window, alpha, step=5)[-1]
    return factor_risk_parity(b, cf, s)


def copula_factor_risk_parity(
    asset_returns, factor_returns, alpha: float = 0.95, n_sim: int = 4000, rng=None
) -> dict:
    """Copula: simulate factor scenarios from a truncated Clayton C-vine with
    empirical margins, find factor exposures with equal CVaR contributions,
    and map them to long-only asset weights by least squares on B'w."""
    r, f = np.asarray(asset_returns, float), np.asarray(factor_returns, float)
    b, _ = loadings_from_returns(r, f)
    u = pseudo_observations(f)
    scen = empirical_quantile(f, simulate_cvine(fit_cvine(u), n_sim, rng))
    target = cvar_risk_parity(scen, alpha)

    def obj(w):
        y = b.T @ w
        return float(((y / (np.abs(y).sum() + 1e-12) - target) ** 2).sum())

    return {"factor_exposures": target, "weights": simplex_minimize(obj, b.shape[0])}


def kernel_pca_factor_risk_parity(
    asset_returns, k: int = 2, gamma: float | None = None
) -> np.ndarray:
    """Nonlinear: factors are kernel-PCA (RBF) scores of the asset cross-
    sections; loadings by regression; then factor risk parity."""
    r = np.asarray(asset_returns, float)
    z = (r - r.mean(0)) / (r.std(0) + 1e-12)
    f = KernelPCA(n_components=k, kernel="rbf", gamma=gamma).fit_transform(z)
    b, s = loadings_from_returns(r, f)
    return factor_risk_parity(b, np.cov(f.T), s)


def vae_factors(
    asset_returns, k: int = 2, steps: int = 300, lr: float = 0.02, seed: int = 0
) -> dict:
    """Variational: a linear-Gaussian VAE (encoder mean and log-variance,
    linear decoder) trained by the reparameterised ELBO; returns the factor
    means (T x k) and decoder loadings (assets x k)."""
    r = np.asarray(asset_returns, float)
    mu_r, sd_r = r.mean(0), r.std(0) + 1e-12
    x = (r - mu_r) / sd_r
    rng = np.random.default_rng(seed)
    n = x.shape[1]
    enc_mu, enc_lv, dec = param((n, k), rng), param((n, k), rng, scale=0.01), param((k, n), rng)
    noise = rng.normal(size=(steps, len(x), k))
    counter = iter(range(steps))

    def loss():
        i = next(counter)
        m, lv = Tensor(x) @ enc_mu, (Tensor(x) @ enc_lv).clip(-6, 2)
        z = m + (lv * 0.5).exp() * Tensor(noise[i])
        kl = ((m * m + lv.exp() - lv - 1.0) * 0.5).sum(axis=1).mean()
        return mse(z @ dec, x) * n + kl * 0.1

    hist = fit(loss, [enc_mu, enc_lv, dec], steps, lr)
    factors = x @ enc_mu.data
    return {"factors": factors, "loadings": (dec.data * sd_r).T, "history": hist}


def variational_factor_risk_parity(asset_returns, k: int = 2, **kw) -> np.ndarray:
    """Variational: factor risk parity on VAE factors."""
    v = vae_factors(asset_returns, k, **kw)
    b, s = loadings_from_returns(asset_returns, v["factors"])
    return factor_risk_parity(b, np.cov(v["factors"].T), s)


def karcher_factor_risk_parity(
    asset_returns, factor_returns, window: int = 60, step: int = 20
) -> np.ndarray:
    """Geometry-aware: the factor covariance is the Karcher (affine-invariant)
    mean of rolling estimates."""
    b, s = loadings_from_returns(asset_returns, factor_returns)
    return factor_risk_parity(b, karcher_mean(rolling_covariances(factor_returns, window, step)), s)


def lead_lag_signature_covariance(returns) -> np.ndarray:
    """Path-signature: the antisymmetric level-2 signature of the lead-lag
    path of cumulative returns equals half the quadratic covariation, so
    2 x (Levy area of lead_i vs lag_j) recovers the realised covariance."""
    x = np.vstack(
        [np.zeros(np.asarray(returns).shape[1]), np.cumsum(np.asarray(returns, float), axis=0)]
    )
    lead = np.repeat(x, 2, axis=0)[1:]
    lag = np.repeat(x, 2, axis=0)[:-1]
    d_lead, d_lag = np.diff(lead, axis=0), np.diff(lag, axis=0)
    run_lead, run_lag = lead[:-1] - lead[0], lag[:-1] - lag[0]
    s_ab = run_lead.T @ d_lag + 0.5 * d_lead.T @ d_lag
    s_ba = run_lag.T @ d_lead + 0.5 * d_lag.T @ d_lead
    cov = s_ab - s_ba.T  # Levy area x 2 between lead and lag
    cov = 0.5 * (cov + cov.T)
    return np.abs(np.diag(np.diag(cov))) + (cov - np.diag(np.diag(cov)))


def signature_factor_risk_parity(asset_returns, factor_returns) -> np.ndarray:
    """Path-signature: factor risk budgeted on the lead-lag signature covariance."""
    b, s = loadings_from_returns(asset_returns, factor_returns)
    return factor_risk_parity(b, lead_lag_signature_covariance(factor_returns), s)


def kernel_conditional_covariance(
    returns, states, current_state, bandwidth: float = 1.0
) -> np.ndarray:
    """Kernel-based: Nadaraya-Watson covariance, each past day weighted by an
    RBF kernel on the distance between its state vector and today's."""
    r, s = np.asarray(returns, float), np.atleast_2d(np.asarray(states, float).T).T
    d2 = ((s - np.asarray(current_state, float)) ** 2).sum(1)
    w = np.exp(-0.5 * d2 / bandwidth**2)
    w /= w.sum()
    mu = w @ r
    c = r - mu
    return (c * w[:, None]).T @ c


def kernel_factor_risk_parity(
    asset_returns, factor_returns, states, current_state, bandwidth: float = 1.0
) -> np.ndarray:
    b, s = loadings_from_returns(asset_returns, factor_returns)
    cf = kernel_conditional_covariance(factor_returns, states, current_state, bandwidth)
    return factor_risk_parity(b, cf, s)


def evolutionary_factor_risk_parity(
    loadings, factor_cov, specific_var=None, gens: int = 40, rng=None
) -> np.ndarray:
    """Evolutionary: genetic search over softmax-parameterised weights for the
    smallest dispersion of factor risk contributions (no convex solver)."""
    b = np.asarray(loadings, float)
    k = b.shape[1]

    def decode(x):
        e = np.exp(x - x.max())
        return e / e.sum()

    def fitness(x):
        rc = factor_risk_contributions(decode(x), b, factor_cov, specific_var)[:k]
        rc = rc / rc.sum()
        return -float(((rc - 1.0 / k) ** 2).sum())

    return decode(genetic_search(fitness, b.shape[0], pop=24, gens=gens, rng=rng)["best"])


def koopman_factor_risk_parity(
    asset_returns, factor_returns, window: int = 20, horizon: int = 5
) -> np.ndarray:
    """Koopman: EDMD on the factors' rolling log volatilities forecasts their
    volatility `horizon` steps ahead; the factor covariance is rebuilt from
    those forecasts and the sample correlation, then factor risk parity."""
    f = np.asarray(factor_returns, float)
    lv = np.log(np.array([f[t - window : t].std(0) for t in range(window, len(f) + 1)]) + 1e-12)
    model = edmd(lv, dictionary=lambda z: poly_dictionary(z, 1))
    vol = np.exp(koopman_predict(model, lv[-1], horizon)[-1])
    corr = np.corrcoef(f.T)
    b, s = loadings_from_returns(asset_returns, f)
    return factor_risk_parity(b, corr * np.outer(vol, vol), s)


# ================================================================ covariance estimation


def dcc_garch_covariance(returns) -> np.ndarray:
    """Model (baseline): GARCH(1,1) variances per asset and Engle's DCC
    correlation, as a one-step covariance forecast."""
    r = np.asarray(returns, float)
    fits = [garch11_fit(r[:, i]) for i in range(r.shape[1])]
    std = np.column_stack([r[:, i] / np.sqrt(fit_i["variance"]) for i, fit_i in enumerate(fits)])
    corr = dcc_fit(std)["correlations"][-1]
    vol = np.sqrt([garch11_forecast(fit_i, r[-1, i])[0] for i, fit_i in enumerate(fits)])
    return corr * np.outer(vol, vol)


def tyler_shape(returns, iters: int = 100) -> np.ndarray:
    """Robust: Tyler's M-estimator of scatter (shape, trace = dimension),
    rescaled by the median Mahalanobis radius to a covariance."""
    x = np.asarray(returns, float) - np.median(returns, axis=0)
    n, p = x.shape
    s = np.eye(p)
    for _ in range(iters):
        inv = np.linalg.inv(s)
        d = np.einsum("ij,jk,ik->i", x, inv, x) + 1e-12
        s_new = p / n * (x / d[:, None]).T @ x
        s_new *= p / np.trace(s_new)
        if np.abs(s_new - s).max() < 1e-10:
            s = s_new
            break
        s = s_new
    d = np.einsum("ij,jk,ik->i", x, np.linalg.inv(s), x)
    return s * np.median(d) / stats.chi2.ppf(0.5, p)


def robust_covariance(returns, method: str = "mcd", seed: int = 0) -> np.ndarray:
    """Robust: minimum covariance determinant or Tyler's estimator."""
    if method == "mcd":
        return MinCovDet(random_state=seed).fit(np.asarray(returns, float)).covariance_
    if method == "tyler":
        return tyler_shape(returns)
    raise ConfigurationError("method must be mcd or tyler")


def attention_covariance(returns, **fit_kw) -> np.ndarray:
    """Attention-weighted: research.catalog.spd_covariance.GATShrinkage."""
    model = GATShrinkage()
    model.fit(returns, **fit_kw)
    return model.covariance(returns)


def geodesic_covariance(returns, window: int = 60, alpha: float = 0.2) -> np.ndarray:
    """Dynamical-systems/geometric: the latest geodesically smoothed estimate."""
    return geodesic_smoothed_covariances(returns, window, alpha, step=5)[-1]


def _vech(m):
    return m[np.triu_indices(len(m))]


def _unvech(v, n):
    m = np.zeros((n, n))
    m[np.triu_indices(n)] = v
    return m + np.triu(m, 1).T


def koopman_covariance(returns, window: int = 40, step: int = 5, horizon: int = 1) -> np.ndarray:
    """Koopman: EDMD on vech(log C_t) of rolling covariances (log-Euclidean
    coordinates), forecast `horizon` steps, map back with the matrix exponential."""
    covs = rolling_covariances(returns, window, step)
    n = covs[0].shape[0]
    z = np.array([_vech(spd_log(c)) for c in covs])
    model = edmd(z, dictionary=lambda q: poly_dictionary(q, 1), ridge=1e-4)
    return spd_exp(_unvech(koopman_predict(model, z[-1], horizon)[-1], n))


def covariance_horse_race(returns, train: int, estimators: dict) -> dict:
    """Out-of-sample variance of the minimum-variance portfolio built from each
    estimator on the first `train` rows (the comparison the pages ask for)."""
    r = np.asarray(returns, float)
    out = {}
    for name, est in estimators.items():
        w = min_variance_weights(est(r[:train]))
        out[name] = float(np.var(r[train:] @ w))
    out["ledoit_wolf"] = float(
        np.var(r[train:] @ min_variance_weights(LedoitWolf().fit(r[:train]).covariance_))
    )
    return out


# ================================================================ tail risk


def pot_var_es(returns, alpha: float = 0.99, threshold_q: float = 0.9) -> dict:
    """Model: peaks over threshold -- fit a generalised Pareto to losses above
    their `threshold_q` quantile and read VaR and ES at alpha."""
    loss = -np.asarray(returns, float)
    u = np.quantile(loss, threshold_q)
    exc = loss[loss > u] - u
    xi, _, beta = stats.genpareto.fit(exc, floc=0.0)
    n, nu = len(loss), len(exc)
    if abs(xi) > 1e-6:
        var = u + beta / xi * (((n / nu) * (1 - alpha)) ** (-xi) - 1)
    else:
        var = u - beta * np.log((n / nu) * (1 - alpha))
    es = (var + beta - xi * u) / (1 - xi) if xi < 1 else np.inf
    return {"var": float(var), "es": float(es), "xi": float(xi), "beta": float(beta)}


def tail_budget_exposure(
    returns, es_budget: float, window: int = 500, alpha: float = 0.99
) -> np.ndarray:
    """Exposure = min(1, budget / ES forecast) from a trailing POT fit."""
    r = np.asarray(returns, float)
    out = np.ones(len(r))
    for t in range(window, len(r)):
        es = pot_var_es(r[t - window : t], alpha)["es"]
        out[t] = min(1.0, es_budget / es) if np.isfinite(es) and es > 0 else 1.0
    return out


def caviar(returns, alpha: float = 0.05, train: int | None = None) -> dict:
    """Recursive: CAViaR symmetric absolute value, q_t = b0 + b1 q_{t-1} +
    b2 |r_{t-1}|, fitted by the quantile (pinball) loss; q is the alpha-quantile
    of returns (negative), so VaR = -q."""
    r = np.asarray(returns, float)
    train = train or len(r)
    q0 = np.quantile(r[: min(100, train)], alpha)

    def path(b):
        q = np.empty(len(r))
        q[0] = q0
        for t in range(1, len(r)):
            q[t] = b[0] + b[1] * q[t - 1] + b[2] * abs(r[t - 1])
        return q

    def loss(b):
        e = r[:train] - path(b)[:train]
        return float(np.mean(np.maximum(alpha * e, (alpha - 1) * e)))

    res = minimize(loss, [q0 * 0.1, 0.8, -0.1], method="Nelder-Mead", options={"maxiter": 3000})
    q = path(res.x)
    return {
        "params": res.x,
        "quantile": q,
        "var": -q,
        "hit_rate": float((r[:train] < q[:train]).mean()),
    }


def var_exposure(var_path, var_budget: float) -> np.ndarray:
    """De-risk when the VaR forecast exceeds the budget: min(1, budget / VaR)."""
    v = np.asarray(var_path, float)
    return np.minimum(1.0, var_budget / np.maximum(v, 1e-12))


def wavelet_tail_risk(returns, levels: int = 4, window: int = 250, alpha: float = 0.01) -> dict:
    """Wavelet: causal Haar details of returns per scale; per-scale variance
    over a trailing window gives a wavelet VaR, z_alpha x sqrt(sum_j var_j),
    and the share of risk at the finest scale flags short-horizon stress."""
    r = np.asarray(returns, float)
    _, details = causal_haar(r, levels)
    d = np.column_stack(details)
    z = -stats.norm.ppf(alpha)
    var, fine_share = np.full(len(r), np.nan), np.full(len(r), np.nan)
    for t in range(window, len(r)):
        wv = d[t - window : t].var(0)
        var[t] = z * np.sqrt(wv.sum())
        fine_share[t] = wv[0] / wv.sum()
    return {"var": var, "fine_share": fine_share}


def critical_slowing_down(series, window: int = 100, trend_window: int = 50) -> dict:
    """Dynamical-systems: rolling lag-1 autocorrelation and variance of the
    detrended series; their Kendall-tau trends over `trend_window` are the
    early-warning indicators (both rising before a critical transition)."""
    x = np.asarray(series, float)
    ar1, var = np.full(len(x), np.nan), np.full(len(x), np.nan)
    tt = np.arange(window)
    for t in range(window, len(x)):
        seg = x[t - window : t]
        resid = seg - np.polyval(np.polyfit(tt, seg, 1), tt)
        ar1[t] = np.corrcoef(resid[:-1], resid[1:])[0, 1]
        var[t] = resid.var()
    warn_ar, warn_var = np.full(len(x), np.nan), np.full(len(x), np.nan)
    for t in range(window + trend_window, len(x)):
        warn_ar[t] = stats.kendalltau(np.arange(trend_window), ar1[t - trend_window : t])[0]
        warn_var[t] = stats.kendalltau(np.arange(trend_window), var[t - trend_window : t])[0]
    return {"ar1": ar1, "variance": var, "tau_ar1": warn_ar, "tau_variance": warn_var}


def early_warning_exposure(series, threshold: float = 0.5, **kw) -> np.ndarray:
    """Cut exposure to zero while both early-warning trends exceed `threshold`."""
    ews = critical_slowing_down(series, **kw)
    alarm = (np.nan_to_num(ews["tau_ar1"]) > threshold) & (
        np.nan_to_num(ews["tau_variance"]) > threshold
    )
    return np.where(alarm, 0.0, 1.0)


# ================================================================ sector and regime allocation


def sector_momentum(
    prices, lookback: int = 126, skip: int = 0, top: int = 3, risk_adjusted: bool = False
) -> np.ndarray:
    """Sector allocation: industry momentum -- hold the `top` sector ETFs by
    trailing return (or return / volatility) equally; long-only."""
    p = np.asarray(prices, float)
    if len(p) <= lookback + skip:
        raise ConfigurationError("not enough history")
    ret = p[-1 - skip] / p[-1 - skip - lookback] - 1
    if risk_adjusted:
        ret = ret / (np.diff(np.log(p[-lookback:]), axis=0).std(0) + 1e-12)
    w = np.zeros(p.shape[1])
    w[np.argsort(-ret)[:top]] = 1.0 / top
    return w


def regime_allocation(
    signal_returns,
    n_states: int = 2,
    risk_on=(1.0, 0.0),
    risk_off=(0.0, 1.0),
    train: int | None = None,
    seed: int = 0,
) -> dict:
    """Regime-aware allocation: a Gaussian HMM on the signal series (fitted on
    the first `train` rows); each day's filtered probability of the high-
    volatility state blends the risk-on and risk-off allocations (e.g.
    (risky, safe) weights)."""
    r = np.asarray(signal_returns, float)
    train = train or len(r)
    hmm = GaussianHMM(n_states, seed=seed).fit(r[:train])
    p_off = hmm.filter(r)[:, int(np.argmax(hmm.var))]
    on, off = np.asarray(risk_on, float), np.asarray(risk_off, float)
    weights = (1 - p_off)[:, None] * on + p_off[:, None] * off
    return {"p_risk_off": p_off, "weights": weights}


# ================================================================ concept index

CONCEPTS = {
    "stochastic-process-based-approach-to-momentum-trend-forecasting": (
        "kalman_trend",
        "l1_trend_filter",
        "l1_trend_positions",
    ),
    "adaptive-approach-to-momentum-trend-forecasting": ("kama", "cycle_blended_momentum"),
    "markov-state-based-approach-to-momentum-trend-forecasting": ("hmm_trend",),
    "conformal-prediction-based-approach-to-momentum-trend-forecasting": (
        "adaptive_conformal_positions",
    ),
    "spectral-approach-to-momentum-trend-forecasting": ("spectral_trend_positions",),
    "bayesian-approach-to-momentum-trend-forecasting": ("bayesian_drift",),
    "robust-approach-to-momentum-trend-forecasting": ("robust_momentum",),
    "copula-based-approach-to-momentum-trend-forecasting": (
        "copula_momentum_positions",
        "clayton_lower_tail",
    ),
    "nonlinear-approach-to-momentum-trend-forecasting": ("kernel_trend_forecast",),
    "fractional-order-approach-to-momentum-trend-forecasting": ("arfima_forecast",),
    "diffusion-model-based-approach-to-momentum-trend-forecasting": ("diffusion_trend",),
    "topology-aware-approach-to-momentum-trend-forecasting": ("topology_filtered_trend",),
    "robust-approach-to-factor-risk-parity-allocation": (
        "robust_factor_risk_parity",
        "factor_risk_parity",
    ),
    "attention-weighted-approach-to-factor-risk-parity-allocation": (
        "attention_factor_risk_parity",
        "attention_budgets",
    ),
    "dynamical-systems-geometric-approach-to-factor-risk-parity-allocation": (
        "geodesic_factor_risk_parity",
    ),
    "copula-based-approach-to-factor-risk-parity-allocation": ("copula_factor_risk_parity",),
    "nonlinear-approach-to-factor-risk-parity-allocation": ("kernel_pca_factor_risk_parity",),
    "variational-approach-to-factor-risk-parity-allocation": (
        "variational_factor_risk_parity",
        "vae_factors",
    ),
    "geometry-aware-approach-to-factor-risk-parity-allocation": ("karcher_factor_risk_parity",),
    "path-signature-based-approach-to-factor-risk-parity-allocation": (
        "signature_factor_risk_parity",
        "lead_lag_signature_covariance",
    ),
    "kernel-based-approach-to-factor-risk-parity-allocation": (
        "kernel_factor_risk_parity",
        "kernel_conditional_covariance",
    ),
    "evolutionary-optimization-based-approach-to-factor-risk-parity-allocation": (
        "evolutionary_factor_risk_parity",
    ),
    "koopman-operator-based-approach-to-factor-risk-parity-allocation": (
        "koopman_factor_risk_parity",
    ),
    "model-for-covariance-estimation-for-portfolio-risk": (
        "dcc_garch_covariance",
        "covariance_horse_race",
    ),
    "robust-approach-to-covariance-estimation-for-portfolio-risk": (
        "robust_covariance",
        "tyler_shape",
    ),
    "attention-weighted-approach-to-covariance-estimation-for-portfolio-risk": (
        "attention_covariance",
    ),
    "dynamical-systems-geometric-approach-to-covariance-estimation-for-portfolio-risk": (
        "geodesic_covariance",
    ),
    "koopman-operator-based-approach-to-covariance-estimation-for-portfolio-risk": (
        "koopman_covariance",
    ),
    "model-for-tail-risk-hedging-and-allocation": ("pot_var_es", "tail_budget_exposure"),
    "recursive-approach-to-tail-risk-hedging-and-allocation": ("caviar", "var_exposure"),
    "wavelet-based-approach-to-tail-risk-hedging-and-allocation": ("wavelet_tail_risk",),
    "dynamical-systems-geometric-approach-to-tail-risk-hedging-and-allocation": (
        "critical_slowing_down",
        "early_warning_exposure",
    ),
    "model-for-sector-allocation": ("sector_momentum",),
    "model-for-regime-aware-allocation": ("regime_allocation",),
}
