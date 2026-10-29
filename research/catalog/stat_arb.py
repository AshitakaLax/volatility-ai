"""
Statistical- and event-arbitrage entries of the ranked list (ledger RK36,
RK39, RK72, RK74, RK80, RK81, RK82, RK89, RK93, RK94, RK97, RK100, RK239,
RK340). Most need a short leg or a non-equity instrument (CDS,
convertibles), which the owner's rules exclude; the closed-end-fund rule
(RK82) and the merger-arb long leg are long-only. Research code only.
Positions are +1 (long the spread), -1 (short it) or 0.

Sources:

  * Johansen baskets -- see research.catalog.econometrics; triplets --
    RK93's page.
  * Distance pairs -- Gatev, Goetzmann & Rouwenhorst, "Pairs trading:
    performance of a relative-value arbitrage rule", RFS 19, 2006.
  * Copula pairs -- Liew & Wu, J. Derivatives & Hedge Funds 19, 2013;
    Rad, Low & Faff, Quantitative Finance 16, 2016 (open when one
    conditional probability is below 0.05 and the other above 0.95).
  * Copula-GARCH -- Patton, "Modelling asymmetric exchange rate
    dependence", Int. Econ. Rev. 47, 2006 (time-varying copulas on GARCH
    residuals); here the Clayton parameter follows a rolling Kendall tau.
  * s-scores of residuals -- Avellaneda & Lee, "Statistical arbitrage in the
    US equities market", Quantitative Finance 10, 2010 (OU fit to cumulative
    residuals; open at |s| > 1.25, close long at s > -0.5, short at s < 0.75).
  * Autoencoder factors -- Gu, Kelly & Xiu, "Autoencoder asset pricing
    models", J. Econometrics 222, 2021.
  * PC algorithm -- Spirtes, Glymour & Scheines, "Causation, Prediction and
    Search", 2000 (Fisher-z partial-correlation tests, v-structures).
  * Fractionally cointegrated VAR -- Johansen & Nielsen, Econometrica 80,
    2012; the neural error-correction term is RK239's untested variant.
  * Merger arbitrage -- Mitchell & Pulvino, "Characteristics of risk and
    return in risk arbitrage", J. Finance 56, 2001.
  * Convertibles -- Tsiveriotis & Fernandes, "Valuing convertible bonds
    with credit risk", J. Fixed Income 8, 1998 (cash part discounted at the
    risky rate, equity part at the risk-free rate).
  * Capital structure arbitrage -- Finger et al., "CreditGrades technical
    document", RiskMetrics 2002; Yu, "How profitable is capital structure
    arbitrage?", Financial Analysts J. 62, 2006.
  * Closed-end fund discounts -- Pontiff, "Costly arbitrage: evidence from
    closed-end funds", QJE 111, 1996.
"""

from __future__ import annotations

from itertools import combinations

import numpy as np
from scipy import stats

from engine.core.exceptions import ConfigurationError
from research.catalog.autodiff import MLP, Tensor, fit, mse, param
from research.catalog.econometrics import (
    clayton_density,
    clayton_h,
    clayton_theta,
    fracdiff,
    fracdiff_weights,
    garch11_fit,
    gph_d,
    johansen,
)

# ---------------------------------------------------------------- spreads and rules


def zscore(x, window: int) -> np.ndarray:
    """Trailing z-score (NaN until a full window)."""
    x = np.asarray(x, float)
    out = np.full(len(x), np.nan)
    for t in range(window - 1, len(x)):
        w = x[t - window + 1 : t + 1]
        out[t] = (x[t] - w.mean()) / (w.std() + 1e-12)
    return out


def band_positions(z, entry: float = 2.0, exit: float = 0.5) -> np.ndarray:
    """Hysteresis rule on a z-score: short the spread above +entry, long below
    -entry, flat once |z| falls under exit."""
    pos, out = 0, []
    for v in np.asarray(z, float):
        if np.isfinite(v):
            if pos == 0 and v > entry:
                pos = -1
            elif pos == 0 and v < -entry:
                pos = 1
            elif pos != 0 and abs(v) < exit:
                pos = 0
        out.append(pos)
    return np.array(out)


def spread_pnl(spread, positions) -> np.ndarray:
    """P&L of holding positions[t-1] units of the spread over t-1 -> t."""
    s, p = np.asarray(spread, float), np.asarray(positions, float)
    return np.r_[0.0, p[:-1] * np.diff(s)]


# ---------------------------------------------------------------- Johansen baskets (RK36, RK93)


def johansen_basket(prices, k_ar_diff: int = 1) -> dict:
    """RK36: the first Johansen eigenvector, scaled so the first asset's weight
    is 1, its spread and whether the trace test finds a relation."""
    p = np.asarray(prices, float)
    out = johansen(p, k_ar_diff)
    w = out["vectors"][:, 0] / out["vectors"][0, 0]
    return {
        "weights": w,
        "spread": p @ w,
        "cointegrated": out["rank"] >= 1,
        "trace": out["trace"][0],
        "crit_95": out["crit_95"][0],
    }


def cointegrated_triplets(prices, require_no_pair: bool = False) -> list[tuple]:
    """RK93: every triple whose Johansen trace test finds a relation, ranked
    by the trace statistic's margin over its critical value; optionally only
    triples none of whose pairs is cointegrated on its own."""
    p = np.asarray(prices, float)
    found = []
    for tri in combinations(range(p.shape[1]), 3):
        b = johansen_basket(p[:, tri])
        if not b["cointegrated"]:
            continue
        if require_no_pair and any(
            johansen(p[:, pair])["rank"] >= 1 for pair in combinations(tri, 2)
        ):
            continue
        found.append((tri, b["trace"] - b["crit_95"], b["weights"]))
    return sorted(found, key=lambda x: -x[1])


# ---------------------------------------------------------------- distance pairs (RK72)


def ggr_pairs(formation_prices, top: int = 5) -> list[tuple[int, int, float]]:
    """GGR: normalise each price path to start at 1 and rank pairs by the sum
    of squared differences; returns (i, j, ssd) for the closest `top` pairs,
    each stock used at most once."""
    p = np.asarray(formation_prices, float)
    if (p <= 0).any():
        raise ConfigurationError("prices must be positive")
    norm = p / p[0]
    cands = sorted(
        (float(((norm[:, i] - norm[:, j]) ** 2).sum()), i, j)
        for i, j in combinations(range(p.shape[1]), 2)
    )
    used, out = set(), []
    for ssd, i, j in cands:
        if i not in used and j not in used:
            out.append((i, j, ssd))
            used |= {i, j}
        if len(out) == top:
            break
    return out


def ggr_positions(formation_a, formation_b, trading_a, trading_b, k: float = 2.0) -> np.ndarray:
    """Open when the normalised trading-period paths diverge by k formation
    standard deviations, close when they cross. +1 = long a / short b."""
    fa, fb = np.asarray(formation_a, float), np.asarray(formation_b, float)
    sd = np.std(fa / fa[0] - fb / fb[0])
    ta, tb = np.asarray(trading_a, float), np.asarray(trading_b, float)
    gap = ta / ta[0] - tb / tb[0]
    pos, out = 0, []
    for g in gap:
        if pos == 0 and abs(g) > k * sd:
            pos = -int(np.sign(g))
        elif pos != 0 and np.sign(g) == pos:  # crossed back through zero
            pos = 0
        out.append(pos)
    return np.array(out)


# ---------------------------------------------------------------- copula pairs (RK74, RK94)


def gaussian_h(u, v, rho: float):
    """h(u | v) for the Gaussian copula."""
    x, y = (
        stats.norm.ppf(np.clip(u, 1e-10, 1 - 1e-10)),
        stats.norm.ppf(np.clip(v, 1e-10, 1 - 1e-10)),
    )
    return stats.norm.cdf((x - rho * y) / np.sqrt(1 - rho**2))


def gumbel_h(u, v, theta: float):
    """h(u | v) = dC/dv for the Gumbel copula."""
    u, v = np.clip(u, 1e-10, 1 - 1e-10), np.clip(v, 1e-10, 1 - 1e-10)
    a = (-np.log(u)) ** theta + (-np.log(v)) ** theta
    c = np.exp(-(a ** (1 / theta)))
    return c * a ** (1 / theta - 1) * (-np.log(v)) ** (theta - 1) / v


def fit_pair_copula(u, v) -> dict:
    """Choose Gaussian or Clayton by log-likelihood (Clayton only for positive
    dependence) and return a conditional-probability function pair."""
    u, v = np.asarray(u, float), np.asarray(v, float)
    x, y = stats.norm.ppf(u), stats.norm.ppf(v)
    rho = float(np.corrcoef(x, y)[0, 1])
    ll_g = np.sum(
        -0.5 * np.log(1 - rho**2) - (rho**2 * (x**2 + y**2) - 2 * rho * x * y) / (2 * (1 - rho**2))
    )
    tau = stats.kendalltau(u, v)[0]
    if tau > 0:
        th = clayton_theta(tau)
        ll_c = np.sum(np.log(clayton_density(u, v, th)))
        if ll_c > ll_g:
            return {
                "family": "clayton",
                "theta": th,
                "loglik": float(ll_c),
                "h_uv": lambda a, b: clayton_h(a, b, th),
                "h_vu": lambda a, b: clayton_h(b, a, th),
            }
    return {
        "family": "gaussian",
        "rho": rho,
        "loglik": float(ll_g),
        "h_uv": lambda a, b: gaussian_h(a, b, rho),
        "h_vu": lambda a, b: gaussian_h(b, a, rho),
    }


def ecdf(sample):
    s = np.sort(np.asarray(sample, float))
    return lambda x: np.clip(np.searchsorted(s, x, side="right") / (len(s) + 1), 1e-6, 1 - 1e-6)


def copula_positions(
    form_ra, form_rb, trade_ra, trade_rb, lo: float = 0.05, hi: float = 0.95
) -> np.ndarray:
    """RK74: marginals = formation-period empirical CDFs of returns; open long a
    / short b when P(U <= u | V = v) < lo and P(V <= v | U = u) > hi (a cheap
    relative to b), the reverse for a short; close when both cross 0.5."""
    fa, fb = ecdf(form_ra), ecdf(form_rb)
    cop = fit_pair_copula(fa(np.asarray(form_ra)), fb(np.asarray(form_rb)))
    u, v = fa(np.asarray(trade_ra, float)), fb(np.asarray(trade_rb, float))
    return _copula_rule(cop["h_uv"](u, v), cop["h_vu"](u, v), lo, hi)


def _copula_rule(h_uv, h_vu, lo, hi) -> np.ndarray:
    pos, out = 0, []
    for a, b in zip(h_uv, h_vu, strict=True):
        if pos == 0 and a < lo and b > hi:
            pos = 1
        elif pos == 0 and a > hi and b < lo:
            pos = -1
        elif (pos == 1 and a >= 0.5 and b <= 0.5) or (pos == -1 and a <= 0.5 and b >= 0.5):
            pos = 0
        out.append(pos)
    return np.array(out)


def copula_garch_positions(ra, rb, window: int = 250, lo: float = 0.05, hi: float = 0.95) -> dict:
    """RK94: GARCH(1,1) standardised residuals of each leg, normal PIT, then a
    Clayton copula whose parameter follows the trailing Kendall tau of the
    residual pairs (independence when tau <= 0). Causal: day t's copula uses
    days t-window..t-1."""
    ra, rb = np.asarray(ra, float), np.asarray(rb, float)
    za = ra / np.sqrt(garch11_fit(ra)["variance"])
    zb = rb / np.sqrt(garch11_fit(rb)["variance"])
    u, v = stats.norm.cdf(za), stats.norm.cdf(zb)
    h_uv, h_vu, thetas = np.full(len(u), 0.5), np.full(len(u), 0.5), np.zeros(len(u))
    for t in range(window, len(u)):
        tau = stats.kendalltau(u[t - window : t], v[t - window : t])[0]
        th = clayton_theta(tau) if tau > 0 else 0.0
        thetas[t] = th
        if th > 0:
            h_uv[t], h_vu[t] = clayton_h(u[t], v[t], th), clayton_h(v[t], u[t], th)
        else:
            h_uv[t], h_vu[t] = u[t], v[t]
    return {"positions": _copula_rule(h_uv, h_vu, lo, hi), "theta": thetas}


# ---------------------------------------------------------------- robust thresholds (RK97)


def wdro_threshold(
    spread,
    grid=(0.5, 1.0, 1.5, 2.0, 2.5, 3.0),
    window: int = 60,
    radius: float = 0.0,
    exit: float = 0.0,
) -> dict:
    """RK97: pick the entry z-threshold whose strategy P&L is best in the worst
    case over a type-1 Wasserstein ball of radius eps on the spread changes:
    the P&L is linear in each change with slope |position|, so the worst case
    is mean P&L - eps * mean |position| (time in market is what an adversary
    can attack). radius = 0 is the in-sample optimum."""
    s = np.asarray(spread, float)
    z = zscore(s, window)
    scores = {}
    for k in grid:
        pos = band_positions(z, k, exit)
        pnl = spread_pnl(s, pos)
        scores[k] = float(pnl.mean() - radius * np.abs(pos[:-1]).mean())
    best = max(scores, key=scores.get)
    return {"threshold": best, "scores": scores}


# ---------------------------------------------------------------- causal discovery (RK100)


def _partial_corr(c, i, j, cond) -> float:
    idx = [i, j, *cond]
    p = np.linalg.pinv(c[np.ix_(idx, idx)])
    return float(-p[0, 1] / np.sqrt(p[0, 0] * p[1, 1]))


def pc_skeleton(data, alpha: float = 0.01, max_cond: int = 2) -> dict:
    """PC skeleton: remove edge i-j when some conditioning set (from i's
    current neighbours, size <= max_cond) makes the Fisher-z partial
    correlation insignificant. Returns adjacency, separating sets, and the
    strength (smallest |partial corr| seen) of each surviving edge."""
    x = np.asarray(data, float)
    n, d = x.shape
    c = np.corrcoef(x.T)
    adj = ~np.eye(d, dtype=bool)
    sepset, strength = {}, {}
    for size in range(max_cond + 1):
        for i, j in combinations(range(d), 2):
            if not adj[i, j]:
                continue
            others = [k for k in np.flatnonzero(adj[i]) if k != j]
            for cond in combinations(others, size):
                r = np.clip(_partial_corr(c, i, j, cond), -0.999999, 0.999999)
                zstat = np.sqrt(n - len(cond) - 3) * np.arctanh(abs(r))
                strength[(i, j)] = min(strength.get((i, j), 1.0), abs(r))
                if 2 * (1 - stats.norm.cdf(zstat)) > alpha:
                    adj[i, j] = adj[j, i] = False
                    sepset[(i, j)] = sepset[(j, i)] = set(cond)
                    break
    return {
        "adjacency": adj,
        "sepset": sepset,
        "strength": {e: s for e, s in strength.items() if adj[e]},
    }


def orient_v_structures(skeleton: dict) -> set[tuple[int, int]]:
    """Directed edges i -> k <- j for every unshielded triple i - k - j with k
    outside sepset(i, j)."""
    adj, sep = skeleton["adjacency"], skeleton["sepset"]
    arrows = set()
    for k in range(len(adj)):
        for i, j in combinations(np.flatnonzero(adj[k]), 2):
            if not adj[i, j] and k not in sep.get((i, j), set()):
                arrows |= {(int(i), k), (int(j), k)}
    return arrows


def causal_pairs(returns, alpha: float = 0.01, top: int = 5) -> list[tuple[int, int, float]]:
    """RK100: candidate pairs = direct links of the PC skeleton, strongest first."""
    sk = pc_skeleton(returns, alpha)
    return sorted(((i, j, s) for (i, j), s in sk["strength"].items()), key=lambda e: -e[2])[:top]


def lagged_causal_links(returns, alpha: float = 0.01) -> list[tuple[int, int, float]]:
    """Leader -> follower links: x_i(t-1) -> x_j(t) kept when significant given
    x_j(t-1) (and every other single lag), i.e. PC with time order imposed."""
    r = np.asarray(returns, float)
    d = r.shape[1]
    lagged = np.column_stack([r[:-1], r[1:]])  # columns 0..d-1 lags, d..2d-1 today
    c = np.corrcoef(lagged.T)
    n = len(lagged)
    links = []
    for i in range(d):
        for j in range(d):
            if i == j:
                continue
            keep, worst = True, 1.0
            for cond in [[j]] + [[j, k] for k in range(d) if k not in (i, j)]:
                pr = np.clip(_partial_corr(c, i, d + j, cond), -0.999999, 0.999999)
                worst = min(worst, abs(pr))
                if (
                    2 * (1 - stats.norm.cdf(np.sqrt(n - len(cond) - 3) * np.arctanh(abs(pr))))
                    > alpha
                ):
                    keep = False
                    break
            if keep:
                links.append((i, j, worst))
    return sorted(links, key=lambda e: -e[2])


# ---------------------------------------------------------------- autoencoder residuals (RK89)


def ou_s_score(cum_resid) -> float:
    """Avellaneda-Lee: fit X_{t+1} = a + b X_t + e to the cumulative residual;
    m = a / (1 - b), sigma_eq = sd(e) / sqrt(1 - b^2), s = (X_T - m) / sigma_eq."""
    x = np.asarray(cum_resid, float)
    b, a = np.polyfit(x[:-1], x[1:], 1)
    if not 0 < b < 1 - 1e-8:  # no mean reversion (b = 1 is a random walk or a trend)
        return 0.0
    e = x[1:] - (a + b * x[:-1])
    return float((x[-1] - a / (1 - b)) / (e.std() / np.sqrt(1 - b**2) + 1e-12))


def s_score_positions(
    s, open_: float = 1.25, close_long: float = -0.5, close_short: float = 0.75
) -> np.ndarray:
    pos, out = 0, []
    for v in np.asarray(s, float):
        if pos == 0 and v < -open_:
            pos = 1
        elif pos == 0 and v > open_:
            pos = -1
        elif (pos == 1 and v > close_long) or (pos == -1 and v < close_short):
            pos = 0
        out.append(pos)
    return np.array(out)


class AutoencoderFactors:
    """RK89: an autoencoder compresses each day's cross-section of returns to
    `latent` factors; the stat-arb signal trades each stock's residual."""

    def __init__(self, n_assets: int, latent: int = 2, hidden: int = 16, seed: int = 0):
        rng = np.random.default_rng(seed)
        self.enc = MLP([n_assets, hidden, latent], rng)
        self.dec = MLP([latent, hidden, n_assets], rng)

    def fit(self, returns, steps: int = 400, lr: float = 0.01) -> list[float]:
        r = np.asarray(returns, float)
        self.scale = r.std() + 1e-12
        x = r / self.scale
        params = self.enc.params + self.dec.params
        return fit(lambda: mse(self.dec(self.enc(Tensor(x))), x), params, steps, lr)

    def residuals(self, returns) -> np.ndarray:
        x = np.asarray(returns, float) / self.scale
        return (x - self.dec(self.enc(Tensor(x))).data) * self.scale

    def s_scores(self, returns, window: int = 60) -> np.ndarray:
        """Each stock's s-score from its trailing cumulative residual."""
        res = self.residuals(returns)
        out = np.zeros_like(res)
        for t in range(window, len(res) + 1):
            cum = np.cumsum(res[t - window : t], axis=0)
            out[t - 1] = [ou_s_score(cum[:, i]) for i in range(res.shape[1])]
        return out


# ---------------------------------------------------------------- neural fractional VECM (RK239, RK340)


class NeuralFCVECM:
    """RK239/RK340: fractionally difference each level series by its GPH
    order d, take the Johansen cointegrating vector of the levels, and fit
    D^d y_t = g(beta' y_{t-1}) + Gamma D^d y_{t-1} + e with g a small MLP (the
    neural error-correction term). Forecasts are integrated back to levels."""

    def __init__(self, hidden: int = 8, window: int = 50, seed: int = 0):
        self.hidden, self.window, self.seed = hidden, window, seed

    def fit(self, levels, steps: int = 300, lr: float = 0.01) -> list[float]:
        y = np.asarray(levels, float)
        n = y.shape[1]
        self.d = np.array([np.clip(gph_d(np.diff(col)) + 1.0, 0.0, 1.0) for col in y.T])
        self.beta = johansen(y)["vectors"][:, 0]
        fd = np.column_stack(
            [fracdiff(c, d, self.window) for c, d in zip(y.T, self.d, strict=True)]
        )
        start = self.window
        ect = (y[start - 1 : -1] @ self.beta)[:, None]
        self.ect_mu, self.ect_sd = ect.mean(), ect.std() + 1e-12
        target, prev = fd[start:], fd[start - 1 : -1]
        rng = np.random.default_rng(self.seed)
        self.g = MLP([1, self.hidden, n], rng)
        self.gamma = param((n, n), rng, scale=0.1)
        x_ect = (ect - self.ect_mu) / self.ect_sd

        def loss():
            return mse(self.g(Tensor(x_ect)) + Tensor(prev) @ self.gamma, target)

        return fit(loss, [*self.g.params, self.gamma], steps, lr)

    def forecast(self, levels) -> np.ndarray:
        """Next-step levels."""
        y = np.asarray(levels, float)
        fd_prev = np.array(
            [fracdiff(c, d, self.window)[-1] for c, d in zip(y.T, self.d, strict=True)]
        )
        ect = np.array([[(y[-1] @ self.beta - self.ect_mu) / self.ect_sd]])
        nxt = self.g(Tensor(ect)).data[0] + fd_prev @ self.gamma.data
        out = np.empty(y.shape[1])
        for j, d in enumerate(self.d):
            w = fracdiff_weights(d, self.window)
            out[j] = nxt[j] - w[1:] @ y[::-1, j][: self.window - 1]
        return out


def fcvecm_allocation(model: NeuralFCVECM, log_prices) -> np.ndarray:
    """Long-only weights proportional to the predicted positive log-price changes."""
    p = np.asarray(log_prices, float)
    change = np.clip(model.forecast(p) - p[-1], 0, None)
    return change / change.sum() if change.sum() > 0 else np.zeros(p.shape[1])


# ---------------------------------------------------------------- event and capital-structure arbitrage


def merger_implied_probability(target_price, offer_value, fallback_price) -> float:
    """Market-implied completion probability (P - fallback) / (offer - fallback)."""
    return float((target_price - fallback_price) / (offer_value - fallback_price))


def merger_arb_return(
    target_price, offer_value, fallback_price, p_success: float, days_to_close: int
) -> dict:
    """RK39: expected and annualised return of buying the target given a view
    of the completion probability; the spread is offer / price - 1. For a
    stock deal offer_value = ratio x acquirer price (hedged by shorting
    `ratio` acquirer shares per target share, outside the owner's rules)."""
    exp = (p_success * offer_value + (1 - p_success) * fallback_price) / target_price - 1
    return {
        "spread": offer_value / target_price - 1,
        "expected": exp,
        "annualised": (1 + exp) ** (365 / max(days_to_close, 1)) - 1,
        "implied_p": merger_implied_probability(target_price, offer_value, fallback_price),
    }


def convertible_price(
    spot, conversion_ratio, face, coupon_rate, maturity, r, sigma, credit_spread, steps: int = 200
) -> dict:
    """RK80: Tsiveriotis-Fernandes on a CRR tree (no calls or puts). Returns
    the price, the equity delta (shares per bond) and the bond floor."""
    dt = maturity / steps
    up = np.exp(sigma * np.sqrt(dt))
    p = (np.exp(r * dt) - 1 / up) / (up - 1 / up)
    disc_r, disc_c = np.exp(-r * dt), np.exp(-(r + credit_spread) * dt)
    s = spot * up ** (steps - 2 * np.arange(steps + 1))
    conv = conversion_ratio * s
    redeem = face * (1 + coupon_rate * dt)
    v = np.maximum(conv, redeem)
    b = np.where(conv >= redeem, 0.0, redeem)
    level = [v]
    for i in range(steps - 1, -1, -1):
        s = spot * up ** (i - 2 * np.arange(i + 1))
        eb = p * b[:-1] + (1 - p) * b[1:]
        ev = p * v[:-1] + (1 - p) * v[1:]
        coupon = face * coupon_rate * dt
        b_h = disc_c * eb + coupon
        v_h = disc_r * (ev - eb) + b_h
        conv = conversion_ratio * s
        convert = conv >= v_h
        v, b = np.where(convert, conv, v_h), np.where(convert, 0.0, b_h)
        level.append(v)
    v1 = level[-2]
    delta = (v1[0] - v1[1]) / (spot * up - spot / up)
    floor = face * np.exp(-(r + credit_spread) * maturity) + face * coupon_rate * maturity
    return {"price": float(v[0]), "delta": float(delta), "bond_floor": float(floor)}


def creditgrades_survival(
    spot, debt_per_share, sigma_s, t, recovery_mean: float = 0.5, recovery_sd: float = 0.3
) -> float:
    """CreditGrades survival probability to t."""
    ld = recovery_mean * debt_per_share
    sig = sigma_s * spot / (spot + ld)
    d = (spot + ld) / ld * np.exp(recovery_sd**2)
    a = np.sqrt(sig**2 * t + recovery_sd**2)
    return float(
        stats.norm.cdf(-a / 2 + np.log(d) / a) - d * stats.norm.cdf(-a / 2 - np.log(d) / a)
    )


def creditgrades_spread(
    spot,
    debt_per_share,
    sigma_s,
    maturity: float = 5.0,
    r: float = 0.03,
    recovery: float = 0.4,
    recovery_mean: float = 0.5,
    recovery_sd: float = 0.3,
) -> float:
    """RK81: CreditGrades' closed-form CDS spread (continuous premium)."""
    ld = recovery_mean * debt_per_share
    sig = sigma_s * spot / (spot + ld)
    d = (spot + ld) / ld * np.exp(recovery_sd**2)
    xi = recovery_sd**2 / sig**2
    z = np.sqrt(0.25 + r / sig**2)

    def g(u):
        su = sig * np.sqrt(u)
        return d ** (z + 0.5) * stats.norm.cdf(-np.log(d) / su - z * su) + d ** (
            -z + 0.5
        ) * stats.norm.cdf(-np.log(d) / su + z * su)

    p0 = creditgrades_survival(spot, debt_per_share, sigma_s, 0.0, recovery_mean, recovery_sd)
    pt = creditgrades_survival(spot, debt_per_share, sigma_s, maturity, recovery_mean, recovery_sd)
    h = np.exp(r * xi) * (g(maturity + xi) - g(xi))
    return float(r * (1 - recovery) * (1 - p0 + h) / (p0 - pt * np.exp(-r * maturity) - h))


def capital_structure_signal(market_spread, model_spread, entry: float = 0.5) -> int:
    """+1 = buy protection (and buy stock as the hedge) when the market spread is
    below the model by more than `entry` (relative); -1 = sell protection
    (short stock) when above; 0 otherwise. Yu (2006) uses relative gaps."""
    gap = (market_spread - model_spread) / model_spread
    return 1 if gap < -entry else -1 if gap > entry else 0


def cef_discount(price, nav) -> np.ndarray:
    return np.asarray(price, float) / np.asarray(nav, float) - 1.0


def cef_positions(
    price, nav, window: int = 250, entry: float = -2.0, exit: float = 0.0
) -> np.ndarray:
    """RK82 (long-only): buy when the discount's trailing z-score is below
    `entry` (unusually wide) and sell when it has narrowed back to `exit`."""
    z = zscore(cef_discount(price, nav), window)
    pos, out = 0, []
    for v in z:
        if np.isfinite(v):
            if pos == 0 and v < entry:
                pos = 1
            elif pos == 1 and v >= exit:
                pos = 0
        out.append(pos)
    return np.array(out)
