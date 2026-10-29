"""
Carry, futures and interest-rate entries of the ranked list (ledger RK4,
RK8, RK20, RK25, RK28, RK30, RK32, RK34, RK41, RK42, RK86, RK92, RK224,
RK226, RK287, RK323). Futures, forwards, currencies and short legs are
outside the owner's rules; the long-only readings (duration momentum on a
bond ETF, inflation-regime rotation among ETFs, cash-venue choice) are
marked. Research code only.

Sources:

  * Carry everywhere -- Koijen, Moskowitz, Pedersen & Vrugt, "Carry", J.
    Financial Econ. 127, 2018 (carry = return if prices do not move; rank
    weights w ~ rank - mean).
  * Commodity momentum and term structure -- Fuertes, Miffre & Rallis, J.
    Banking Finance 34, 2010 (double sort); the basis factor -- Szymanowska,
    de Roon, Nijman & van den Goorbergh, J. Finance 69, 2014; Erb & Harvey,
    Financial Analysts J. 62, 2006.
  * Time-series momentum -- Moskowitz, Ooi & Pedersen, J. Financial Econ.
    104, 2012 (volatility-scaled positions).
  * Index arbitrage -- MacKinlay & Ramaswamy, RFS 1, 1988 (fair value S e^{(r-q)T}
    and a no-arbitrage band set by costs).
  * FX carry and crashes -- Brunnermeier, Nagel & Pedersen, NBER Macro Annual
    23, 2008; Lustig, Roussanov & Verdelhan, RFS 24, 2011.
  * Inflation regimes -- Neville, Draaisma, Funnell, Harvey & Van Hemert,
    "The best strategies for inflationary times", 2021.
  * Dynamic Nelson-Siegel -- Diebold & Li, J. Econometrics 130, 2006 (lambda
    0.0609 for maturities in months); functional PCA of curves -- Hays, Shen
    & Huang, Ann. Appl. Stat. 6, 2012.
  * Latent force models -- Alvarez, Luengo & Lawrence, AISTATS 2009 (a GP
    force driving dy/dt + D y = S f; here the ODE's Green's operator is
    applied to a discretised GP, so the output covariance is G K G').
  * Musiela parametrisation of HJM -- Musiela, 1993: df/dt = df/dx + sigma(x)
    int_0^x sigma(u) du; constant sigma gives the drift sigma^2 x.
  * Neural delay ODEs -- Zhu, Guo & Lin, "Neural delay differential
    equations", ICLR 2021.
  * Reverse repo floor -- Federal Reserve Bank of New York ON RRP
    documentation (RK92 has no trading study).
"""

from __future__ import annotations

import numpy as np
from scipy.interpolate import CubicSpline
from scipy.optimize import minimize

from engine.core.exceptions import ConfigurationError
from research.catalog.autodiff import MLP, Tensor, concat, fit, mse
from research.catalog.derivatives import FDResidualNet
from research.catalog.stat_arb import band_positions, zscore

# ---------------------------------------------------------------- carry measures (RK4, RK28, RK30, RK32)


def fx_carry(spot, forward, years: float) -> np.ndarray:
    """Annualised FX carry (S - F) / F / T: positive when the foreign rate is higher."""
    s, f = np.asarray(spot, float), np.asarray(forward, float)
    return (s - f) / f / years


def roll_yield(near, far, years_between: float) -> np.ndarray:
    """Annualised commodity roll yield log(near / far) / T (positive = backwardation)."""
    return np.log(np.asarray(near, float) / np.asarray(far, float)) / years_between


def index_carry(spot, future, years: float) -> np.ndarray:
    """Equity-index carry (dividend yield minus financing): (S - F) / F / T."""
    return fx_carry(spot, future, years)


def curve_yield(maturities, yields, m) -> np.ndarray:
    return CubicSpline(np.asarray(maturities, float), np.asarray(yields, float))(m)


def bond_carry_rolldown(maturities, yields, horizon: float = 0.25, funding: float = 0.0) -> dict:
    """RK28: for each maturity m, carry = (y(m) - funding) h and roll-down =
    (y(m) - y(m - h)) x duration(m - h), with modified duration ~ m - h for a
    zero-coupon bond; the total is the return if the curve does not move."""
    m, y = np.asarray(maturities, float), np.asarray(yields, float)
    rolled = np.maximum(m - horizon, 1e-6)
    roll = (y - curve_yield(m, y, rolled)) * rolled
    carry = (y - funding) * horizon
    return {"carry": carry, "rolldown": roll, "total": carry + roll}


def rank_weights(signal) -> np.ndarray:
    """KMPV rank weights: w ~ rank - mean rank, scaled to one dollar long and short."""
    s = np.asarray(signal, float)
    d = np.argsort(np.argsort(s)) - (len(s) - 1) / 2
    return d / (np.abs(d).sum() / 2)


def carry_composite(carry_by_class: dict, long_only: bool = False) -> dict:
    """RK4: rank weights inside each asset class, the classes equally weighted
    (long-only: positive-carry assets only, normalised)."""
    out = {}
    for name, c in carry_by_class.items():
        w = rank_weights(c)
        if long_only:
            w = np.clip(w, 0, None)
            w = w / w.sum() if w.sum() else w
        out[name] = w / len(carry_by_class)
    return out


def fx_carry_portfolio(
    rate_differentials, k: int = 3, fx_vol=None, vol_z_exit: float | None = None, window: int = 250
) -> np.ndarray:
    """RK30: long the k highest-yielding currencies, short the k lowest; with
    fx_vol (a history) and vol_z_exit, flat when FX volatility's trailing
    z-score exceeds the exit level (the unwind risk Brunnermeier et al. document)."""
    d = np.asarray(rate_differentials, float)
    w = np.zeros(len(d))
    order = np.argsort(d)
    w[order[-k:]], w[order[:k]] = 1.0 / k, -1.0 / k
    if fx_vol is not None and vol_z_exit is not None:
        z = zscore(np.asarray(fx_vol, float), window)[-1]
        if np.isfinite(z) and z > vol_z_exit:
            return np.zeros(len(d))
    return w


# ---------------------------------------------------------------- commodity sorts (RK8, RK32, RK42)


def double_sort(momentum, roll, q: float = 1 / 3) -> np.ndarray:
    """RK8: long commodities in the top q of both momentum and roll yield,
    short those in the bottom q of both; each leg equally weighted."""
    m, r = np.asarray(momentum, float), np.asarray(roll, float)
    longs = (m >= np.quantile(m, 1 - q)) & (r >= np.quantile(r, 1 - q))
    shorts = (m <= np.quantile(m, q)) & (r <= np.quantile(r, q))
    w = np.zeros(len(m))
    if longs.any():
        w[longs] = 1.0 / longs.sum()
    if shorts.any():
        w[shorts] = -1.0 / shorts.sum()
    return w


def basis_factor(roll, q: float = 0.25, long_only: bool = False) -> np.ndarray:
    """RK32 (long-only: hold the most backwardated) and RK42 (market-neutral:
    long the top q, short the bottom q)."""
    r = np.asarray(roll, float)
    n = max(round(float(q * len(r))), 1)
    order = np.argsort(r)
    w = np.zeros(len(r))
    w[order[-n:]] = 1.0 / n
    if not long_only:
        w[order[:n]] = -1.0 / n
    return w


# ---------------------------------------------------------------- futures relative value (RK25, RK34)


def index_fair_value(spot, rate: float, dividend_yield: float, years: float) -> np.ndarray:
    return np.asarray(spot, float) * np.exp((rate - dividend_yield) * years)


def basis_signal(
    future, spot, rate: float, dividend_yield: float, years: float, cost: float = 0.002
) -> np.ndarray:
    """RK25: -1 (sell future, buy basket) when the future is above fair value
    by more than `cost` (relative), +1 the reverse, 0 inside the band."""
    fair = index_fair_value(spot, rate, dividend_yield, years)
    gap = np.asarray(future, float) / fair - 1
    return np.where(gap > cost, -1, np.where(gap < -cost, 1, 0))


def calendar_spread_positions(
    near, far, window: int = 60, entry: float = 2.0, exit: float = 0.5
) -> dict:
    """RK34: hedge ratio from a trailing regression of near on far, spread =
    near - h far, then the z-score band rule (+1 = long the spread)."""
    n, f = np.asarray(near, float), np.asarray(far, float)
    h = np.full(len(n), np.nan)
    for t in range(window, len(n)):
        h[t] = np.polyfit(f[t - window : t], n[t - window : t], 1)[0]
    spread = n - np.nan_to_num(h) * f
    z = zscore(np.where(np.isfinite(h), spread, np.nan), window)
    return {"hedge": h, "spread": spread, "positions": band_positions(z, entry, exit)}


# ---------------------------------------------------------------- duration and the curve (RK20, RK86)


def duration_momentum(
    bond_prices,
    lookback: int = 252,
    vol_window: int = 63,
    vol_target: float = 0.10,
    long_only: bool = True,
) -> np.ndarray:
    """RK20: position = sign(trailing return) x vol_target / realised vol
    (capped at 1); long-only holds a bond ETF only when the trend is up."""
    p = np.asarray(bond_prices, float)
    r = np.diff(np.log(p))
    pos = np.zeros(len(p))
    for t in range(max(lookback, vol_window) + 1, len(p)):
        sig = np.sign(p[t] / p[t - lookback] - 1)
        vol = r[t - vol_window : t].std() * np.sqrt(252)
        size = min(vol_target / (vol + 1e-12), 1.0)
        pos[t] = max(sig, 0) * size if long_only else sig * size
    return pos


def dv01(yield_: float, maturity: float, coupon: float = 0.0, freq: int = 2) -> float:
    """Price change per 1bp for a bullet bond (per 100 face)."""

    def price(y):
        n = round(maturity * freq)
        c = 100 * coupon / freq
        t = np.arange(1, n + 1)
        return float((c / (1 + y / freq) ** t).sum() + 100 / (1 + y / freq) ** n)

    return (price(yield_ - 1e-4) - price(yield_ + 1e-4)) / 2


def steepener_notionals(dv01_short: float, dv01_long: float, notional_short: float = 1e6) -> dict:
    """RK86: DV01-matched steepener (long the short maturity, short the long)."""
    return {
        "long_short_maturity": notional_short,
        "short_long_maturity": notional_short * dv01_short / dv01_long,
    }


def steepener_pnl(
    dv01_short: float, dv01_long: float, d_short_bp, d_long_bp, notional_short: float = 1e6
) -> np.ndarray:
    """P&L (DV01-matched, per 100 face scaling) for yield changes in bp: gains
    when the long yield rises relative to the short one."""
    n = steepener_notionals(dv01_short, dv01_long, notional_short)
    scale = notional_short / 100
    long_leg = scale * (-dv01_short * np.asarray(d_short_bp, float))
    return long_leg + n["short_long_maturity"] / 100 * dv01_long * np.asarray(d_long_bp, float)


def slope_signal(y_short, y_long, window: int = 250, z: float = 1.5) -> np.ndarray:
    """+1 steepener when the slope is unusually flat (z < -z), -1 flattener
    when unusually steep; a mean-reversion rule, no published edge (RK86)."""
    s = zscore(np.asarray(y_long, float) - np.asarray(y_short, float), window)
    return np.where(s < -z, 1, np.where(s > z, -1, 0))


# ---------------------------------------------------------------- regimes and cash (RK41, RK92)


def inflation_regimes(cpi_yoy, high: float = 0.03, lag: int = 1) -> np.ndarray:
    """Four states from published (lagged) YoY inflation: 0 low & falling,
    1 low & rising, 2 high & falling, 3 high & rising."""
    x = (
        np.r_[np.full(lag, np.nan), np.asarray(cpi_yoy, float)[:-lag]]
        if lag
        else np.asarray(cpi_yoy, float)
    )
    rising = np.r_[False, np.diff(x) > 0]
    state = (np.nan_to_num(x) > high).astype(int) * 2 + rising.astype(int)
    state[~np.isfinite(x)] = -1
    return state


def regime_rotation(asset_returns, regimes, train: int, top: int = 1) -> np.ndarray:
    """RK41 (long-only): per regime, the assets with the best mean return in
    the training rows; afterwards hold those for the current regime."""
    r, s = np.asarray(asset_returns, float), np.asarray(regimes, int)
    best = {}
    for st in np.unique(s[:train]):
        if st < 0:
            continue
        mean = r[:train][s[:train] == st].mean(0)
        best[st] = np.argsort(-mean)[:top]
    w = np.zeros_like(r)
    for t in range(train, len(r)):
        if s[t] in best:
            w[t, best[s[t]]] = 1.0 / top
    return w


def cash_venue(
    bill_yield: float,
    rrp_rate: float,
    mmf_yield: float,
    bill_cost: float = 0.0005,
    rrp_access: bool = False,
) -> dict:
    """RK92 for a retail account: the best net yield among T-bills (after
    trading cost), a money-market fund (which can reach the ON RRP floor)
    and, for eligible counterparties only, the ON RRP itself."""
    options = {"t_bill": bill_yield - bill_cost, "money_fund": mmf_yield}
    if rrp_access:
        options["on_rrp"] = rrp_rate
    best = max(options, key=options.get)
    return {"choice": best, "yield": options[best], "bills_below_floor": bill_yield < rrp_rate}


# ---------------------------------------------------------------- curve models (RK224, RK226, RK287, RK323)


def nelson_siegel_loadings(maturities, lam: float = 0.0609) -> np.ndarray:
    """Diebold-Li loadings (maturities in months): level, slope, curvature."""
    m = np.asarray(maturities, float)
    x = lam * m
    slope = (1 - np.exp(-x)) / x
    return np.column_stack([np.ones(len(m)), slope, slope - np.exp(-x)])


def dns_forecast(curves, maturities, steps: int = 1, lam: float = 0.0609) -> np.ndarray:
    """Dynamic Nelson-Siegel: OLS factors per date, AR(1) per factor, curve forecast."""
    load = nelson_siegel_loadings(maturities, lam)
    f = np.linalg.lstsq(load, np.asarray(curves, float).T, rcond=None)[0].T
    nxt = f[-1].copy()
    for _ in range(steps):
        for j in range(3):
            b, a = np.polyfit(f[:-1, j], f[1:, j], 1)
            nxt[j] = a + b * nxt[j]
    return load @ nxt


def fpca(curves, maturities, n_components: int = 3, grid: int = 50) -> dict:
    """RK226: interpolate each curve to a dense maturity grid (cubic spline),
    eigen-decompose the covariance operator with trapezoid weights, and
    return mean function, component functions and scores."""
    m = np.asarray(maturities, float)
    g = np.linspace(m.min(), m.max(), grid)
    dense = np.array([CubicSpline(m, c)(g) for c in np.asarray(curves, float)])
    w = np.gradient(g)
    mean = dense.mean(0)
    x = (dense - mean) * np.sqrt(w)
    vals, vecs = np.linalg.eigh(x.T @ x / len(x))
    order = np.argsort(-vals)[:n_components]
    phi = vecs[:, order] / np.sqrt(w)[:, None]
    scores = (dense - mean) @ (phi * w[:, None])
    return {
        "grid": g,
        "mean": mean,
        "components": phi,
        "scores": scores,
        "explained": vals[order] / vals.sum(),
    }


def fpca_forecast(curves, maturities, steps: int = 1, n_components: int = 3) -> np.ndarray:
    """AR(1) on each FPCA score; the forecast curve back on the input maturities."""
    out = fpca(curves, maturities, n_components)
    s = out["scores"]
    nxt = s[-1].copy()
    for _ in range(steps):
        for j in range(s.shape[1]):
            b, a = np.polyfit(s[:-1, j], s[1:, j], 1)
            nxt[j] = a + b * nxt[j]
    dense = out["mean"] + out["components"] @ nxt
    return CubicSpline(out["grid"], dense)(np.asarray(maturities, float))


class LatentForceGP:
    """RK224: y solves dy/dt + D y = S f(t) with f ~ GP(0, RBF(l)). On a time
    grid, y = G f with G the discretised Green's operator S e^{-D (t - s)} dt,
    so y ~ N(0, G K G' + noise I). Hyperparameters by marginal likelihood;
    forecasts by conditioning on the observed part of an extended grid."""

    def fit(self, series, dt: float = 1.0) -> LatentForceGP:
        y = np.asarray(series, float)
        self.mu, self.dt, self.n = y.mean(), dt, len(y)
        z = y - self.mu

        def nll(p):
            c = self._cov(self.n, *np.exp(p))
            sign, logdet = np.linalg.slogdet(c)
            if sign <= 0:
                return 1e12
            return 0.5 * (logdet + z @ np.linalg.solve(c, z))

        res = minimize(
            nll,
            np.log([0.1, 1.0, 5.0, 0.1 * z.var() + 1e-6]),
            method="Nelder-Mead",
            options={"maxiter": 2000},
        )
        self.params = np.exp(res.x)
        self.z = z
        return self

    def _cov(self, n, decay, sens, length, noise):
        t = np.arange(n) * self.dt
        lag = t[:, None] - t[None, :]
        g = np.where(lag >= 0, sens * np.exp(-decay * np.maximum(lag, 0.0)) * self.dt, 0.0)
        k = np.exp(-0.5 * (lag / length) ** 2)
        return g @ k @ g.T + noise * np.eye(n)

    def forecast(self, steps: int) -> dict:
        c = self._cov(self.n + steps, *self.params)
        coo, cfo = c[: self.n, : self.n], c[self.n :, : self.n]
        mean = cfo @ np.linalg.solve(coo, self.z) + self.mu
        cov = c[self.n :, self.n :] - cfo @ np.linalg.solve(coo, cfo.T)
        return {"mean": mean, "sd": np.sqrt(np.clip(np.diag(cov), 0, None))}


class NeuralDelayCurve:
    """RK287: curve factors (FPCA scores or DNS factors) follow a neural delay
    ODE z_{t+1} = z_t + f(z_t, z_{t - delay}) (Euler, unit step); f is an MLP
    trained on one-step prediction."""

    def __init__(self, dim: int, delay: int = 5, hidden: int = 16, seed: int = 0):
        self.dim, self.delay = dim, delay
        self.f = MLP([2 * dim, hidden, dim], np.random.default_rng(seed))

    def fit(self, factors, steps: int = 300, lr: float = 0.01) -> list[float]:
        z = np.asarray(factors, float)
        if len(z) <= self.delay + 1:
            raise ConfigurationError("series shorter than the delay")
        self.mu, self.sd = z.mean(0), z.std(0) + 1e-12
        x = (z - self.mu) / self.sd
        d = self.delay
        cur, lagged, nxt = x[d:-1], x[: -d - 1], x[d + 1 :]
        return fit(
            lambda: mse(Tensor(cur) + self.f(concat([Tensor(cur), Tensor(lagged)], axis=1)), nxt),
            self.f.params,
            steps,
            lr,
        )

    def forecast(self, factors, steps: int = 1) -> np.ndarray:
        hist = list((np.asarray(factors, float) - self.mu) / self.sd)
        out = []
        for _ in range(steps):
            cur, lag = hist[-1], hist[-1 - self.delay]
            nxt = cur + self.f(Tensor(np.r_[cur, lag][None])).data[0]
            hist.append(nxt)
            out.append(nxt * self.sd + self.mu)
        return np.array(out)


def fit_musiela_pinn(
    times, maturities, forwards, sigma: float, steps: int = 300, weight: float = 1.0, seed: int = 0
) -> dict:
    """RK323: a network f(t, x) for the forward curve, fitted to observed
    forwards (rows = dates `times`, columns = `maturities`) plus the HJM drift
    condition in Musiela form with constant volatility,
    df/dt - df/dx - sigma^2 x = 0, at random collocation points; derivatives
    are finite differences of the network (research.catalog.derivatives)."""
    t, m = np.asarray(times, float), np.asarray(maturities, float)
    f = np.asarray(forwards, float)
    tt, mm = np.meshgrid(t, m, indexing="ij")
    rng = np.random.default_rng(seed)
    model = FDResidualNet(seed=seed)

    def loss():
        data = mse(model(tt.ravel(), mm.ravel())[:, 0], f.ravel())
        tc = rng.uniform(t.min(), t.max(), 128)
        xc = rng.uniform(m.min(), m.max(), 128)
        d = model.derivs(tc, xc)
        res = d["u_t"][:, 0] - d["u_x"][:, 0] - Tensor(sigma**2 * xc)
        return data + (res**2).mean() * weight

    return {"model": model, "history": fit(loss, model.net.params, steps, 5e-3)}


def musiela_curve(model, t: float, maturities) -> np.ndarray:
    """The fitted forward curve at date t (beyond the data it is an
    extrapolation held to the drift condition)."""
    m = np.asarray(maturities, float)
    return model(np.full(len(m), t), m).data[:, 0]
