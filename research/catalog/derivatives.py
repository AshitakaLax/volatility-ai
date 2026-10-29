"""
Option and volatility entries of the ranked list beyond research.catalog.
options (ledger RK87, RK240, RK283, RK285, RK286, RK302, RK303, RK309,
RK324, RK325, RK329, RK350, RK352, RK374, RK377, RK379, RK391). Options
are outside the owner's rules; this is pricing and hedging research code
on simulated markets.

Sources:

  * Implied correlation and dispersion -- Driessen, Maenhout & Vilkov, "The
    price of correlation risk", J. Finance 64, 2009.
  * Heston, RFS 6, 1993, with the "little Heston trap" form of Albrecher et
    al., Wilmott 2007; rough Heston and its fractional Riccati equation --
    El Euch & Rosenbaum, Math. Finance 29, 2019, solved by the fractional
    Adams scheme of Diethelm, Ford & Freed, Nonlinear Dyn. 29, 2002; Lewis's
    single-integral call formula (Lewis, "Option Valuation under Stochastic
    Volatility", 2000); Merton jumps, J. Financial Econ. 3, 1976.
  * Rough Bergomi -- Bayer, Friz & Gatheral, Quantitative Finance 16, 2016
    (here with a left-point Riemann-sum Volterra scheme, adequate on coarse grids).
  * Deep learning calibration -- Horvath, Muguruza & Tomas, "Deep learning
    volatility", Quantitative Finance 21, 2021 (learn the parameter -> smile
    map offline, then calibrate on the surrogate).
  * Deep hedging -- Buehler, Gonon, Teichmann & Wood, Quantitative Finance
    19, 2019 (minimise a convex risk measure -- CVaR here, in its
    Rockafellar-Uryasev form -- of the hedged P&L with costs).
  * DGM -- Sirignano & Spiliopoulos, J. Comput. Phys. 375, 2018; PINNs --
    Raissi, Perdikaris & Karniadakis, J. Comput. Phys. 378, 2019 (Burgers and
    nonlinear Schrodinger examples). Derivatives in the residuals are central
    finite differences of the network, since the autodiff is first-order.
  * Neural SDE price bounds -- Gierjatowicz, Sabate-Vidales, Siska, Szpruch &
    Zuric, "Robust pricing and hedging via neural SDEs", 2020 (an ensemble of
    calibrated models brackets the price).
  * Iron condor/butterfly benchmarks -- Cboe CNDR and BFLY index
    methodologies; gamma scalping P&L 1/2 Gamma S^2 (sigma_real^2 -
    sigma_impl^2) dt -- Bakshi & Kapadia, RFS 16, 2003 (delta-hedged gains).
"""

from __future__ import annotations

import math

import numpy as np
from scipy.integrate import quad
from scipy.optimize import minimize
from scipy.special import gamma as gamma_fn

from engine.core.exceptions import ConfigurationError
from research.catalog.autodiff import MLP, Tensor, concat, fit, mse
from research.catalog.cross_section import spectral_features
from research.catalog.options import bs_greeks, bs_price, implied_vol
from research.catalog.point_processes import path_signature_features

# ---------------------------------------------------------------- dispersion (RK87)


def implied_correlation(index_vol: float, weights, component_vols) -> float:
    """rho such that sigma_I^2 = sum w_i^2 s_i^2 + rho sum_{i != j} w_i w_j s_i s_j."""
    w, s = np.asarray(weights, float), np.asarray(component_vols, float)
    ws = w * s
    cross = ws.sum() ** 2 - (ws**2).sum()
    return float((index_vol**2 - (ws**2).sum()) / cross)


def realized_correlation(index_returns, component_returns, weights) -> float:
    """The same identity applied to realised variances."""
    r = np.asarray(component_returns, float)
    return implied_correlation(np.std(index_returns), weights, r.std(0))


def dispersion_pnl(
    weights, comp_strikes, comp_realized, index_strike, index_realized, index_notional: float = 1.0
) -> float:
    """Short index variance, long component variances (variance-swap legs,
    strikes and realised values as variances): sum w_i (RV_i - K_i) - (RV_I - K_I)."""
    w = np.asarray(weights, float)
    legs = w @ (np.asarray(comp_realized, float) - np.asarray(comp_strikes, float))
    return float(index_notional * (legs - (index_realized - index_strike)))


# ---------------------------------------------------------------- iron condor / butterfly (RK285, RK286)


def iron_strikes(spot: float, short_otm: float, wing: float) -> tuple[float, float, float, float]:
    """(long put, short put, short call, long call) strikes at short_otm and
    short_otm + wing fractions from spot; short_otm = 0 is the iron butterfly."""
    return (
        spot * (1 - short_otm - wing),
        spot * (1 - short_otm),
        spot * (1 + short_otm),
        spot * (1 + short_otm + wing),
    )


def iron_credit(spot, strikes, t, r, iv) -> float:
    lp, sp, sc, lc = strikes
    return (
        bs_price(spot, sp, t, r, iv, "put")
        - bs_price(spot, lp, t, r, iv, "put")
        + bs_price(spot, sc, t, r, iv, "call")
        - bs_price(spot, lc, t, r, iv, "call")
    )


def iron_payoff(spot_at_expiry, strikes) -> np.ndarray:
    """Value owed at expiry by the seller (>= 0; capped by the wings)."""
    s = np.asarray(spot_at_expiry, float)
    lp, sp, sc, lc = strikes
    return np.clip(sp - s, 0, sp - lp) + np.clip(s - sc, 0, lc - sc)


def iron_backtest(
    closes, ivs, hold: int = 21, short_otm: float = 0.05, wing: float = 0.05, r: float = 0.0
) -> np.ndarray:
    """Sell one condor (butterfly if short_otm = 0) every `hold` days at the
    day's implied vol and settle at expiry; P&L per trade per unit spot."""
    c, v = np.asarray(closes, float), np.asarray(ivs, float)
    out = []
    for t in range(0, len(c) - hold, hold):
        k = iron_strikes(c[t], short_otm, wing)
        credit = iron_credit(c[t], k, hold / 252, r, v[t])
        out.append((credit - float(iron_payoff(c[t + hold], k))) / c[t])
    return np.array(out)


# ---------------------------------------------------------------- gamma scalping (RK309)


def gamma_scalp_pnl(
    prices, implied: float, strike: float, maturity: float, r: float = 0.0, dt: float = 1 / 252
) -> dict:
    """Buy a straddle at `implied` vol and delta-hedge it at each price;
    returns the total P&L and the theoretical 1/2 Gamma S^2 (r^2 - sigma^2 dt) sum."""
    p = np.asarray(prices, float)
    t_left = maturity
    value0 = bs_price(p[0], strike, t_left, r, implied) + bs_price(
        p[0], strike, t_left, r, implied, "put"
    )
    cash, delta, approx = -value0, 0.0, 0.0
    for k in range(len(p) - 1):
        g_c = bs_greeks(p[k], strike, t_left, r, implied)
        g_p = bs_greeks(p[k], strike, t_left, r, implied, "put")
        new_delta = -(g_c["delta"] + g_p["delta"])  # hedge shares
        cash -= (new_delta - delta) * p[k]
        delta = new_delta
        ret = p[k + 1] / p[k] - 1
        approx += 0.5 * (g_c["gamma"] + g_p["gamma"]) * p[k] ** 2 * (ret**2 - implied**2 * dt)
        t_left -= dt
    final = (
        max(p[-1] - strike, 0) + max(strike - p[-1], 0)
        if t_left <= 1e-9
        else (
            bs_price(p[-1], strike, t_left, r, implied)
            + bs_price(p[-1], strike, t_left, r, implied, "put")
        )
    )
    return {"pnl": float(cash + delta * p[-1] + final), "approx": float(approx)}


# ---------------------------------------------------------------- Heston and rough Heston (RK240, RK303)


def heston_call(s, k, t, r, kappa, theta, xi, rho, v0) -> float:
    """Heston call by the two-probability formula with the stable char function."""

    def phi(u):
        iu = 1j * u
        d = np.sqrt((rho * xi * iu - kappa) ** 2 + xi**2 * (iu + u**2))
        g = (kappa - rho * xi * iu - d) / (kappa - rho * xi * iu + d)
        e = np.exp(-d * t)
        c = (
            kappa
            * theta
            / xi**2
            * ((kappa - rho * xi * iu - d) * t - 2 * np.log((1 - g * e) / (1 - g)))
        )
        dd = v0 / xi**2 * (kappa - rho * xi * iu - d) * (1 - e) / (1 - g * e)
        return np.exp(iu * (np.log(s) + r * t) + c + dd)

    lk = np.log(k)
    fwd = s * np.exp(r * t)
    p1 = (
        0.5
        + quad(
            lambda u: (np.exp(-1j * u * lk) * phi(u - 1j) / (1j * u * fwd)).real,
            1e-8,
            200,
            limit=200,
        )[0]
        / np.pi
    )
    p2 = (
        0.5
        + quad(lambda u: (np.exp(-1j * u * lk) * phi(u) / (1j * u)).real, 1e-8, 200, limit=200)[0]
        / np.pi
    )
    return float(s * p1 - k * np.exp(-r * t) * p2)


def rough_heston_cf(
    u,
    t,
    hurst,
    lam,
    theta,
    nu,
    rho,
    v0,
    steps: int = 100,
    jump_intensity: float = 0.0,
    jump_mean: float = 0.0,
    jump_sd: float = 0.0,
):
    """E exp(i u log(S_t / S_0)) for rough Heston (zero rates), by the
    fractional Adams scheme for D^alpha h = F(u, h), alpha = H + 1/2; with
    optional (martingale-corrected) Merton jumps."""
    a = np.atleast_1d(np.asarray(u, complex))
    alpha = hurst + 0.5
    dt = t / steps
    c1, c2 = dt**alpha / gamma_fn(alpha + 2), dt**alpha / gamma_fn(alpha + 1)

    def f(h):
        return 0.5 * (-(a**2) - 1j * a) + (1j * rho * nu * a - lam) * h + 0.5 * nu**2 * h**2

    h = np.zeros((steps + 1, len(a)), complex)
    fh = np.zeros_like(h)
    fh[0] = f(h[0])
    for k in range(steps):
        j = np.arange(k + 1)
        b = c2 * ((k + 1 - j) ** alpha - (k - j) ** alpha)
        pred = b @ fh[: k + 1]
        aw = c1 * (
            (k - j + 2) ** (alpha + 1) + (k - j) ** (alpha + 1) - 2 * (k - j + 1) ** (alpha + 1)
        )
        aw[0] = c1 * (k ** (alpha + 1) - (k - alpha) * (k + 1) ** alpha)
        h[k + 1] = aw @ fh[: k + 1] + c1 * f(pred)
        fh[k + 1] = f(h[k + 1])
    i1 = np.trapezoid(h, dx=dt, axis=0)
    if alpha >= 1.0:  # I^0 h = h: the classical Heston limit (H = 1/2)
        i_frac = h[-1]
    else:
        mid = 0.5 * (h[1:] + h[:-1])
        n = np.arange(steps)
        w = (
            dt ** (1 - alpha)
            / gamma_fn(2 - alpha)
            * ((steps - n) ** (1 - alpha) - (steps - n - 1) ** (1 - alpha))
        )
        i_frac = w @ mid
    out = np.exp(theta * lam * i1 + v0 * i_frac)
    if jump_intensity:
        jump = np.exp(1j * a * jump_mean - 0.5 * a**2 * jump_sd**2) - 1
        drift = np.exp(jump_mean + 0.5 * jump_sd**2) - 1
        out *= np.exp(t * jump_intensity * (jump - 1j * a * drift))
    return out


_LEWIS_U = np.linspace(1e-6, 60.0, 400)


def _lewis_price(s: float, k: float, phi_shifted) -> float:
    """Lewis: C = S - sqrt(S K) / pi int_0^inf Re[e^{i u x} phi(u - i/2)] / (u^2 + 1/4) du,
    x = log(S / K); phi_shifted = phi(u - i/2) on _LEWIS_U (zero rates)."""
    u = _LEWIS_U
    vals = (np.exp(1j * u * np.log(s / k)) * phi_shifted).real / (u**2 + 0.25)
    return float(s - np.sqrt(s * k) / np.pi * np.trapezoid(vals, u))


def lewis_call(s: float, k: float, cf) -> float:
    """Call price from the char function cf of log(S_T / S_0) (zero rates)."""
    return _lewis_price(s, k, cf(_LEWIS_U - 0.5j))


def rough_heston_smile(s, strikes, t, params: dict, **cf_kw) -> np.ndarray:
    """RK303: implied vols of rough Heston (+ jumps) calls across strikes; the
    fractional Riccati solve is shared by every strike."""
    phi = rough_heston_cf(_LEWIS_U - 0.5j, t, **params, **cf_kw)
    out = []
    for k in strikes:
        price = _lewis_price(s, k, phi)
        out.append(implied_vol(max(price, max(s - k, 0.0) + 1e-10), s, k, t, 0.0))
    return np.array(out)


def fit_smile(s, strikes, t, market_vols, model_smile, x0: dict, bounds: dict) -> dict:
    """Least-squares fit of a smile model's parameters to market implied vols;
    the 'predictor' carries the fitted parameters to the next date."""
    names = list(x0)

    def loss(v):
        p = dict(zip(names, v, strict=True))
        return float(((model_smile(s, strikes, t, p) - np.asarray(market_vols)) ** 2).sum())

    res = minimize(
        loss,
        [x0[n] for n in names],
        method="L-BFGS-B",
        bounds=[bounds[n] for n in names],
        options={"maxiter": 60},
    )
    return {"params": dict(zip(names, res.x, strict=True)), "sse": float(res.fun)}


class NeuralCalibrator:
    """RK240: learn the parameter -> implied-vol-grid map of any pricer with an
    MLP (offline, on random parameters), then calibrate to a market grid by
    optimising the parameters through the surrogate."""

    def __init__(
        self,
        pricer,
        bounds: dict,
        grid: list[tuple[float, float]],
        spot: float = 100.0,
        seed: int = 0,
    ):
        self.pricer, self.bounds, self.grid, self.spot = pricer, bounds, grid, spot
        self.names = list(bounds)
        self.rng = np.random.default_rng(seed)

    def _vols(self, p: dict) -> np.ndarray:
        out = []
        for k, t in self.grid:
            price = self.pricer(self.spot, k, t, **p)
            out.append(implied_vol(max(price, max(self.spot - k, 0) + 1e-10), self.spot, k, t, 0.0))
        return np.array(out)

    def train(self, n_samples: int = 200, steps: int = 500, lr: float = 0.01) -> list[float]:
        lo = np.array([self.bounds[n][0] for n in self.names])
        hi = np.array([self.bounds[n][1] for n in self.names])
        self.lo, self.hi = lo, hi
        xs = self.rng.uniform(lo, hi, (n_samples, len(lo)))
        ys = np.array([self._vols(dict(zip(self.names, x, strict=True))) for x in xs])
        self.y_mu, self.y_sd = ys.mean(0), ys.std(0) + 1e-12
        self.net = MLP([len(lo), 32, 32, len(self.grid)], self.rng)
        z = (xs - lo) / (hi - lo)
        target = (ys - self.y_mu) / self.y_sd
        return fit(lambda: mse(self.net(Tensor(z)), target), self.net.params, steps, lr)

    def surrogate(self, x) -> np.ndarray:
        z = (np.asarray(x, float) - self.lo) / (self.hi - self.lo)
        return self.net(Tensor(z[None])).data[0] * self.y_sd + self.y_mu

    def calibrate(self, market_vols) -> dict:
        mv = np.asarray(market_vols, float)
        res = minimize(
            lambda x: float(((self.surrogate(x) - mv) ** 2).sum()),
            (self.lo + self.hi) / 2,
            method="L-BFGS-B",
            bounds=list(zip(self.lo, self.hi, strict=True)),
        )
        return dict(zip(self.names, res.x, strict=True))


def delay_sv_call(
    s, k, t, kappa, theta, xi, delay, v0=0.04, paths: int = 4000, steps: int = 50, seed: int = 0
) -> float:
    """RK240's 'delay' model, as constructed here (no paper defines it):
    variance mean-reverts toward its own value `delay` years ago,
    dv = kappa (blend(theta, v_{t - delay}) - v) dt + xi sqrt(v) dW, priced by
    Monte Carlo with common random numbers (so the map is smooth in parameters)."""
    rng = np.random.default_rng(seed)
    dt = t / steps
    lag = max(round(delay / dt), 1)
    v = np.full((steps + 1, paths), v0)
    logs = np.zeros(paths)
    z1, z2 = rng.normal(size=(2, steps, paths))
    for i in range(steps):
        anchor = 0.5 * theta + 0.5 * v[max(i - lag, 0)]
        vi = np.maximum(v[i], 0)
        logs += -0.5 * vi * dt + np.sqrt(vi * dt) * z1[i]
        v[i + 1] = vi + kappa * (anchor - vi) * dt + xi * np.sqrt(vi * dt) * z2[i]
    return float(np.mean(np.maximum(s * np.exp(logs) - k, 0)))


# ---------------------------------------------------------------- path simulators


def gbm_paths(
    n: int, steps: int, sigma, s0: float = 100.0, t: float = 1 / 12, rng=None
) -> np.ndarray:
    """(n, steps + 1) GBM paths; sigma may be one value or one per path."""
    rng = np.random.default_rng(rng)
    dt = t / steps
    sig = np.broadcast_to(np.asarray(sigma, float), (n,))[:, None]
    z = rng.normal(size=(n, steps))
    return s0 * np.exp(
        np.cumsum(np.c_[np.zeros(n), -0.5 * sig**2 * dt + sig * np.sqrt(dt) * z], axis=1)
    )


def rough_bergomi_paths(
    n: int,
    steps: int,
    hurst: float,
    eta: float,
    rho: float,
    xi0: float = 0.04,
    s0: float = 100.0,
    t: float = 1 / 12,
    rng=None,
) -> np.ndarray:
    """rBergomi: V_t = xi0 exp(eta W~_t - eta^2 t^{2H} / 2), W~ the Volterra
    process sqrt(2H) int (t - s)^{H - 1/2} dW (left-point sum), and the price
    driven by rho dW + sqrt(1 - rho^2) dB."""
    rng = np.random.default_rng(rng)
    dt = t / steps
    tg = dt * np.arange(1, steps + 1)
    dw = rng.normal(size=(n, steps)) * np.sqrt(dt)
    db = rng.normal(size=(n, steps)) * np.sqrt(dt)
    kern = np.sqrt(2 * hurst) * np.array(
        [
            [((tg[i] - dt * j) ** (hurst - 0.5) if j <= i else 0.0) for j in range(steps)]
            for i in range(steps)
        ]
    )
    wt = dw @ kern.T  # (n, steps)
    v = xi0 * np.exp(eta * wt - 0.5 * eta**2 * tg ** (2 * hurst))
    v = np.c_[np.full(n, xi0), v[:, :-1]]
    dz = rho * dw + np.sqrt(1 - rho**2) * db
    logs = np.cumsum(-0.5 * v * dt + np.sqrt(v) * dz, axis=1)
    return s0 * np.exp(np.c_[np.zeros(n), logs])


def mc_call(paths, k: float) -> float:
    return float(np.maximum(np.asarray(paths)[:, -1] - k, 0).mean())


def rough_vol_surface(
    s0, strikes, t, hurst, eta, rho, xi0=0.04, n: int = 4000, steps: int = 30, seed: int = 0
) -> np.ndarray:
    """RK379: rBergomi implied vols (common random numbers)."""
    p = rough_bergomi_paths(n, steps, hurst, eta, rho, xi0, s0, t, rng=seed)
    return np.array(
        [implied_vol(max(mc_call(p, k), max(s0 - k, 0) + 1e-10), s0, k, t, 0.0) for k in strikes]
    )


def surface_relative_value(market_vols, model_vols, threshold: float = 0.01) -> np.ndarray:
    """+1 = buy (market vol cheap vs model), -1 = sell (rich), 0 = inside threshold."""
    gap = np.asarray(market_vols, float) - np.asarray(model_vols, float)
    return np.where(gap < -threshold, 1, np.where(gap > threshold, -1, 0))


# ---------------------------------------------------------------- deep hedging (RK283, RK324, RK325, RK329, RK352, RK391)


class DeepHedger:
    """Hedge a short call: shares held over each step = NN(features), P&L =
    -payoff + sum delta (S_{k+1} - S_k) - cost sum |d delta| S. The loss is
    CVaR_alpha of -P&L (Rockafellar-Uryasev with a learned w); being
    cash-invariant, that loss is also the indifference price of the call.
    features: 'markov' (time, log-moneyness, last delta); 'signature' adds
    the depth-2 signature of the (time, log price) path so far (RK391);
    'operator' adds Fourier features of the path so far (RK325)."""

    def __init__(
        self,
        strike: float,
        features: str = "markov",
        hidden: int = 16,
        alpha: float = 0.9,
        cost: float = 0.0,
        seed: int = 0,
    ):
        if features not in ("markov", "signature", "operator"):
            raise ConfigurationError("features must be markov, signature or operator")
        self.k, self.kind, self.alpha, self.cost = strike, features, alpha, cost
        extra = {"markov": 0, "signature": 6, "operator": 8}[features]
        self.net = MLP([3 + extra, hidden, hidden, 1], np.random.default_rng(seed))
        self.w = Tensor(0.0, requires_grad=True)

    def _features(self, paths, k):
        n, m = paths.shape
        base = [np.full(n, k / (m - 1)), np.log(paths[:, k] / self.k)]
        if self.kind == "signature":
            tg = np.linspace(0, k / (m - 1), k + 1)
            sig = np.array(
                [
                    path_signature_features(np.column_stack([tg, np.log(p[: k + 1] / p[0])]))
                    if k
                    else np.zeros(6)
                    for p in paths
                ]
            )
            return base, sig
        if self.kind == "operator":
            hist = np.log(paths[:, : k + 1] / paths[:, :1])
            hist = np.pad(hist, ((0, 0), (0, m - 1 - k)), mode="edge")
            return base, spectral_features(hist, 4)
        return base, None

    def pnl(self, paths) -> Tensor:
        p = np.asarray(paths, float)
        n, m = p.shape
        delta = Tensor(np.zeros(n))
        total = Tensor(np.zeros(n))
        for k in range(m - 1):
            base, extra = self._features(p, k)
            cols = [Tensor(np.column_stack(base)), delta.reshape(n, 1)]
            if extra is not None:
                cols.append(Tensor(extra))
            new = self.net(concat(cols, axis=1))[:, 0].tanh() * 0.5 + 0.5
            total = total + new * Tensor(p[:, k + 1] - p[:, k])
            if self.cost:
                total = total - ((new - delta) ** 2 + 1e-8).sqrt() * Tensor(self.cost * p[:, k])
            delta = new
        return total - Tensor(np.maximum(p[:, -1] - self.k, 0))

    def loss(self, paths) -> Tensor:
        loss = -self.pnl(paths)
        return self.w + (loss - self.w).relu().mean() * (1 / (1 - self.alpha))

    def fit(self, path_sampler, steps: int = 200, lr: float = 0.01) -> list[float]:
        """path_sampler() returns a fresh batch of paths each step; for the
        Wasserstein-robust variants it returns the worst batch in its ball."""
        return fit(lambda: self.loss(path_sampler()), [*self.net.params, self.w], steps, lr)

    def price(self, paths) -> float:
        """Indifference price: the CVaR of the hedged liability."""
        loss = -self.pnl(paths).data
        var = np.quantile(loss, self.alpha)
        return float(var + np.maximum(loss - var, 0).mean() / (1 - self.alpha))


def worst_case_sampler(hedger: DeepHedger, generators, n: int = 256, rng=None):
    """RK283/RK324/RK329: each call draws a batch from every model in the
    ambiguity set (e.g. volatilities or Hurst exponents inside the ball) and
    returns the one with the highest hedging risk for the current policy."""
    rng = np.random.default_rng(rng)

    def sample():
        batches = [g(n, int(rng.integers(2**31))) for g in generators]
        risks = [float(hedger.loss(b).data) for b in batches]
        return batches[int(np.argmax(risks))]

    return sample


# ---------------------------------------------------------------- PDE solvers (RK302, RK350, RK374)


class FDResidualNet:
    """An MLP u(t, x) whose PDE residual is formed from central finite
    differences of the network itself (differentiable in the weights).
    `transform(t, x, raw)` can build constraints into u (e.g. a terminal
    condition)."""

    def __init__(
        self, n_out: int = 1, width: int = 32, h: float = 1e-2, seed: int = 0, transform=None
    ):
        self.net = MLP([2, width, width, n_out], np.random.default_rng(seed))
        self.h, self.transform = h, transform

    def __call__(self, t, x) -> Tensor:
        raw = self.net(Tensor(np.column_stack([t, x])))
        return raw if self.transform is None else self.transform(np.asarray(t), np.asarray(x), raw)

    def derivs(self, t, x) -> dict:
        h = self.h
        u = self(t, x)
        up, um = self(t, x + h), self(t, x - h)
        return {
            "u": u,
            "u_t": (self(t + h, x) - self(t - h, x)) * (1 / (2 * h)),
            "u_x": (up - um) * (1 / (2 * h)),
            "u_xx": (up - u * 2.0 + um) * (1 / h**2),
        }


def smooth_call_payoff(x, sharpness: float = 40.0):
    """(x - 1)^+ smoothed by a softplus, so finite-difference u_xx stays bounded."""
    return np.logaddexp(0.0, sharpness * (np.asarray(x, float) - 1.0)) / sharpness


def dgm_black_scholes(
    maturity: float,
    r: float,
    sigma: float,
    payoff=smooth_call_payoff,
    steps: int = 400,
    batch: int = 128,
    lr: float = 1e-2,
    x_range=(0.3, 2.0),
    seed: int = 0,
) -> FDResidualNet:
    """RK302: Deep Galerkin for the Black-Scholes PDE in x = S / K,
    u_t + 1/2 sigma^2 x^2 u_xx + r x u_x - r u = 0 at random interior points,
    with the terminal condition built in: u = payoff(x) + (T - t) N(t, x).
    Returns the network; the price is K u(0, S / K). A kinked payoff makes
    the residual stiff near the strike at expiry, so convergence is slow
    (the pages call DGM a numerical method, not a strategy)."""
    rng = np.random.default_rng(seed)

    def transform(t, x, raw):
        return Tensor(payoff(x)[:, None]) + raw * Tensor((maturity - t)[:, None])

    model = FDResidualNet(seed=seed, transform=transform)

    def loss():
        t = rng.uniform(0, maturity, batch)
        x = rng.uniform(*x_range, batch)
        d = model.derivs(t, x)
        res = (
            d["u_t"]
            + d["u_xx"] * Tensor((0.5 * sigma**2 * x**2)[:, None])
            + d["u_x"] * Tensor((r * x)[:, None])
            - d["u"] * r
        )
        return (res**2).mean()

    fit(loss, model.net.params, steps, lr)
    return model


def fit_pinn(
    data_t,
    data_x,
    data_u,
    residual,
    n_out: int = 1,
    steps: int = 400,
    weight: float = 1.0,
    domain=((0.0, 1.0), (-1.0, 1.0)),
    seed: int = 0,
    readout=None,
) -> dict:
    """Fit an FDResidualNet to observations (t, x, u) plus `weight` times a
    PDE residual at random collocation points. `readout` maps the network's
    outputs to the observed quantity (identity by default)."""
    rng = np.random.default_rng(seed)
    model = FDResidualNet(n_out, seed=seed)
    read = readout or (lambda out: out[:, 0])
    u_obs = np.asarray(data_u, float)

    def loss():
        data = mse(read(model(np.asarray(data_t), np.asarray(data_x))), u_obs)
        t = rng.uniform(*domain[0], 128)
        x = rng.uniform(*domain[1], 128)
        return data + (residual(model.derivs(t, x)) ** 2).mean() * weight

    hist = fit(loss, model.net.params, steps, 5e-3)
    return {"model": model, "history": hist}


def burgers_residual(nu: float = 0.01):
    """RK374: u_t + u u_x - nu u_xx."""
    return lambda d: d["u_t"] + d["u"] * d["u_x"] - d["u_xx"] * nu


def schrodinger_residual(d) -> Tensor:
    """RK350: nonlinear Schrodinger i h_t + 1/2 h_xx + |h|^2 h = 0 with
    h = u + i v (two outputs); returns both residual parts stacked."""
    u, v = d["u"][:, 0], d["u"][:, 1]
    mod = u * u + v * v
    real = -d["u_t"][:, 1] + d["u_xx"][:, 0] * 0.5 + mod * u
    imag = d["u_t"][:, 0] + d["u_xx"][:, 1] * 0.5 + mod * v
    return concat([real, imag], axis=0)


def modulus(out: Tensor) -> Tensor:
    return (out[:, 0] ** 2 + out[:, 1] ** 2 + 1e-12).sqrt()


# ---------------------------------------------------------------- neural SDE bounds (RK377)


class NeuralLocalVol:
    """dS = sigma_theta(t, log(S/S0)) S dW (zero rates), sigma_theta a small MLP
    (softplus). Calibrated to call prices by Monte Carlo through the Euler
    scheme with fixed noise, so prices are differentiable in theta."""

    def __init__(
        self, s0: float = 100.0, t: float = 0.5, steps: int = 20, paths: int = 2000, seed: int = 0
    ):
        self.s0, self.t, self.steps = s0, t, steps
        rng = np.random.default_rng(seed)
        self.net = MLP([2, 16, 1], rng)
        self.z = rng.normal(size=(steps, paths))

    def terminal(self) -> Tensor:
        dt = self.t / self.steps
        logs = Tensor(np.zeros(self.z.shape[1]))
        for i in range(self.steps):
            x = concat([Tensor(np.full((self.z.shape[1], 1), i * dt)), logs.reshape(-1, 1)], axis=1)
            sig = self.net(x)[:, 0].softplus() * 0.2 + 0.05
            logs = logs - sig * sig * (0.5 * dt) + sig * Tensor(self.z[i] * math.sqrt(dt))
        return logs.exp() * self.s0

    def prices(self, strikes) -> Tensor:
        st = self.terminal()
        return concat([(st - k).relu().mean().reshape(1) for k in strikes], axis=0)

    def calibrate(self, strikes, market, steps: int = 150, lr: float = 0.02) -> list[float]:
        return fit(
            lambda: mse(self.prices(strikes), np.asarray(market, float)), self.net.params, steps, lr
        )


def robust_price_bounds(models, strike: float) -> tuple[float, float]:
    """Price an exotic-free check: the range of one strike's price across an
    ensemble of separately calibrated neural SDEs."""
    p = [float(m.prices([strike]).data[0]) for m in models]
    return min(p), max(p)


def bounds_signal(market_price: float, bounds: tuple[float, float]) -> int:
    """+1 buy if the market is below every calibrated model, -1 sell if above."""
    lo, hi = bounds
    return 1 if market_price < lo else -1 if market_price > hi else 0
