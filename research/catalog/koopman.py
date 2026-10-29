"""
Koopman-operator and dynamic-mode-decomposition entries of the ranked list
(ledger RK201, RK203, RK206, RK219, RK241, RK261, RK273, RK320, RK321,
RK362, RK376, RK409, RK415-RK418). Research code: the pages record no
out-of-sample trading evidence for any of these.

Sources:

  * Exact DMD -- Tu, Rowley, Luchtenburg, Brunton & Kutz, "On dynamic mode
    decomposition: theory and applications", J. Comput. Dyn. 1, 2014; DMD
    trading -- Mann & Kutz, "Dynamic mode decomposition for financial
    trading strategies", Quantitative Finance 16, 2016 (window of prices,
    low-rank modes, extrapolate one step, trade the predicted direction).
  * Extended DMD (a dictionary of observables) -- Williams, Kevrekidis &
    Rowley, J. Nonlinear Sci. 25, 2015; with inputs (EDMDc) and linear MPC
    on the lifted state -- Korda & Mezic, "Linear predictors for nonlinear
    dynamical systems: Koopman operator meets model predictive control",
    Automatica 93, 2018.
  * Deep Koopman embeddings -- Lusch, Kutz & Brunton, Nature
    Communications 9, 2018 (autoencoder whose latent state evolves
    linearly; reconstruction + prediction + linearity losses).
  * Wasserstein-robust MPC (RK409): the worst case of a quadratic tracking
    cost over a type-2 Wasserstein ball of radius r around the model's
    residuals adds r times the norm of the control's sensitivity; here a
    ridge penalty on the control path.
"""

from __future__ import annotations

import numpy as np
from scipy.optimize import minimize

from engine.core.exceptions import ConfigurationError
from research.catalog.autodiff import MLP, Tensor, fit, mse, param
from research.catalog.options import bs_price

# ---------------------------------------------------------------- DMD


def dmd(snapshots, rank: int | None = None) -> dict:
    """Exact DMD of columns x_1..x_m (variables in rows): A ~ X' X^+ through a
    rank-r SVD; returns modes, eigenvalues, amplitudes and the reduced operator."""
    x = np.asarray(snapshots, float)
    if x.ndim != 2 or x.shape[1] < 3:
        raise ConfigurationError("need a (variables, time) matrix with at least 3 snapshots")
    x1, x2 = x[:, :-1], x[:, 1:]
    u, s, vh = np.linalg.svd(x1, full_matrices=False)
    r = min(rank or len(s), int((s > 1e-10 * s[0]).sum()))
    u, s, v = u[:, :r], s[:r], vh[:r].conj().T
    a_tilde = u.conj().T @ x2 @ v / s
    lam, w = np.linalg.eig(a_tilde)
    phi = x2 @ v / s @ w
    b = np.linalg.lstsq(phi, x[:, 0].astype(complex), rcond=None)[0]
    return {"modes": phi, "eigenvalues": lam, "amplitudes": b, "a_tilde": a_tilde, "u": u}


def dmd_forecast(snapshots, steps: int = 1, rank: int | None = None) -> np.ndarray:
    """x_{m+k} = Phi diag(lambda^(m-1+k)) b for k = 1..steps (real part)."""
    x = np.asarray(snapshots, float)
    d = dmd(x, rank)
    m = x.shape[1]
    ks = np.arange(m, m + steps)
    return np.real(d["modes"] @ (d["eigenvalues"][:, None] ** ks * d["amplitudes"][:, None]))


def dmd_signal(prices, window: int = 20, rank: int = 2) -> np.ndarray:
    """RK219 (Mann & Kutz): for each day, DMD on the trailing window of the
    assets' prices, forecast one step, and hold +1/-1/0 per asset by the sign of
    the predicted change. Causal: day t uses prices up to t."""
    p = np.asarray(prices, float)
    if p.ndim == 1:
        p = p[:, None]
    sig = np.zeros_like(p)
    for t in range(window, len(p)):
        win = p[t - window : t + 1].T
        pred = dmd_forecast(win, 1, rank)[:, 0]
        sig[t] = np.sign(pred - p[t])
    return sig


# ---------------------------------------------------------------- EDMD and EDMDc


def poly_dictionary(x, degree: int = 2) -> np.ndarray:
    """Observables [1, x, x_i x_j (i <= j)] for rows of x (samples, d)."""
    x = np.atleast_2d(np.asarray(x, float))
    cols = [np.ones(len(x)), *x.T]
    if degree >= 2:
        d = x.shape[1]
        cols += [x[:, i] * x[:, j] for i in range(d) for j in range(i, d)]
    return np.column_stack(cols)


def rbf_dictionary(x, centers, width: float = 1.0) -> np.ndarray:
    x = np.atleast_2d(np.asarray(x, float))
    c = np.asarray(centers, float)
    d2 = ((x[:, None, :] - c[None]) ** 2).sum(-1)
    return np.column_stack([np.ones(len(x)), x, np.exp(-d2 / (2 * width**2))])


def edmd(states, dictionary=poly_dictionary, inputs=None, ridge: float = 1e-8) -> dict:
    """Least-squares Koopman (and input) matrices on lifted states:
    z_{t+1} ~ K z_t + B u_t, with z = dictionary(x). Rows of `states` are time."""
    x = np.asarray(states, float)
    z = dictionary(x)
    z0, z1 = z[:-1], z[1:]
    feats = z0 if inputs is None else np.column_stack([z0, np.asarray(inputs, float)[:-1]])
    g = feats.T @ feats + ridge * np.eye(feats.shape[1])
    coef = np.linalg.solve(g, feats.T @ z1).T  # (nz, nz [+ nu])
    nz = z.shape[1]
    out = {"K": coef[:, :nz], "dictionary": dictionary, "n_state": x.shape[1]}
    out["B"] = coef[:, nz:] if inputs is not None else np.zeros((nz, 0))
    return out


def koopman_predict(model: dict, x0, steps: int, controls=None) -> np.ndarray:
    """Roll the lifted linear model forward and read the state back from the
    linear observables (columns 1..d of the dictionary)."""
    z = model["dictionary"](np.atleast_2d(x0))[0]
    d = model["n_state"]
    out = []
    for k in range(steps):
        u = np.zeros(model["B"].shape[1]) if controls is None else np.atleast_1d(controls[k])
        z = model["K"] @ z + model["B"] @ u
        out.append(z[1 : 1 + d].copy())
    return np.array(out)


def linear_mpc(
    model: dict,
    x0,
    horizon: int,
    target,
    q: float = 1.0,
    r: float = 0.1,
    bounds=None,
    wdro_radius: float = 0.0,
) -> np.ndarray:
    """Choose controls u_0..u_{H-1} minimising sum q ||x_k - target||^2 + r ||u_k||^2
    (+ wdro_radius ||u||_2 for the robust version, RK409) under the lifted model;
    bounds is (lo, hi) per control. Returns the control path (H, nu)."""
    nu = model["B"].shape[1]
    if nu == 0:
        raise ConfigurationError("the model has no inputs; fit edmd(..., inputs=...)")
    tgt = np.broadcast_to(np.asarray(target, float), (horizon, model["n_state"]))

    def cost(flat):
        u = flat.reshape(horizon, nu)
        xs = koopman_predict(model, x0, horizon, u)
        c = q * ((xs - tgt) ** 2).sum() + r * (u**2).sum()
        return c + wdro_radius * np.sqrt((u**2).sum() + 1e-12)

    b = None if bounds is None else [tuple(bounds)] * (horizon * nu)
    res = minimize(cost, np.zeros(horizon * nu), method="L-BFGS-B", bounds=b)
    return res.x.reshape(horizon, nu)


# ---------------------------------------------------------------- deep Koopman (RK273, RK376)


class DeepKoopman:
    """Lusch, Kutz & Brunton's autoencoder: phi = encoder(x), phi_{t+1} = K phi_t,
    x = decoder(phi); loss = reconstruction + one-step prediction + linearity."""

    def __init__(self, n_state: int, latent: int = 4, hidden: int = 16, seed: int = 0):
        rng = np.random.default_rng(seed)
        self.enc = MLP([n_state, hidden, latent], rng)
        self.dec = MLP([latent, hidden, n_state], rng)
        self.k = param((latent, latent), rng, scale=0.3)

    @property
    def params(self) -> list[Tensor]:
        return self.enc.params + self.dec.params + [self.k]

    def loss(self, x: np.ndarray) -> Tensor:
        xt = Tensor(x)
        z = self.enc(xt)
        recon = mse(self.dec(z), x)
        z_next = z[:-1] @ self.k
        pred = mse(self.dec(z_next), x[1:])
        lin = mse(z_next, self.enc(Tensor(x[1:])).data)
        return recon + pred + lin

    def fit(self, states, steps: int = 300, lr: float = 0.01) -> list[float]:
        x = np.asarray(states, float)
        return fit(lambda: self.loss(x), self.params, steps, lr)

    def predict(self, x0, steps: int) -> np.ndarray:
        z = self.enc(Tensor(np.atleast_2d(x0))).data
        out = []
        for _ in range(steps):
            z = z @ self.k.data
            out.append(self.dec(Tensor(z)).data[0])
        return np.array(out)


def deep_koopman_allocation(model: DeepKoopman, x0, n_assets: int, steps: int = 5) -> np.ndarray:
    """RK273: long-only weights proportional to the positive part of the
    predicted cumulative returns of the first n_assets state variables."""
    pred = model.predict(x0, steps)[:, :n_assets].sum(0)
    w = np.clip(pred, 0, None)
    return w / w.sum() if w.sum() > 0 else np.zeros(n_assets)


# ---------------------------------------------------------------- trading applications


def koopman_spread_position(
    spread, horizon: int = 5, risk: float = 1.0, cost: float = 0.0
) -> float:
    """RK201/RK203: fit EDMD to the spread's own dynamics, predict its path, and
    hold the position that maximises predicted P&L minus risk and cost:
    position = (predicted change) / (risk * variance + cost) -- short the spread
    when it is predicted to fall."""
    s = np.asarray(spread, float)[:, None]
    m = edmd(s)
    path = koopman_predict(m, s[-1], horizon)[:, 0]
    move = path[-1] - s[-1, 0]
    var = np.var(np.diff(s[:, 0])) * horizon
    return float(move / (risk * var + cost + 1e-12))


def koopman_mpc_allocation(
    returns, horizon: int = 5, turnover: float = 0.1, prev=None
) -> np.ndarray:
    """RK206/RK415: EDMD on the asset returns, predicted cumulative returns over
    the horizon, then long-only weights maximising predicted return minus a
    variance penalty and a turnover penalty against `prev`."""
    r = np.asarray(returns, float)
    n = r.shape[1]
    m = edmd(r, dictionary=lambda x: poly_dictionary(x, 1))
    mu = koopman_predict(m, r[-1], horizon).sum(0)
    cov = np.cov(r.T) * horizon + 1e-9 * np.eye(n)
    prev = np.full(n, 1.0 / n) if prev is None else np.asarray(prev, float)

    def obj(w):
        return -(w @ mu) + 0.5 * w @ cov @ w + turnover * np.abs(w - prev).sum()

    cons = ({"type": "eq", "fun": lambda w: w.sum() - 1.0},)
    res = minimize(obj, prev, method="SLSQP", bounds=[(0, 1)] * n, constraints=cons)
    return res.x


def koopman_factor_drift(exposures, steps: int = 5) -> np.ndarray:
    """RK241: forecast the drift of a portfolio's factor exposures."""
    e = np.asarray(exposures, float)
    return koopman_predict(edmd(e, dictionary=lambda x: poly_dictionary(x, 1)), e[-1], steps)


def koopman_risk_scale(volatility, target_vol: float, horizon: int = 5) -> float:
    """RK261: scale exposure by target / predicted volatility (EDMD on log vol)."""
    lv = np.log(np.asarray(volatility, float))[:, None]
    pred = np.exp(koopman_predict(edmd(lv), lv[-1], horizon)[:, 0]).mean()
    return float(min(1.0, target_vol / pred))


def robust_koopman_mpc(model: dict, x0, horizon: int, target, radius: float, **kw) -> np.ndarray:
    """RK409: linear MPC with the Wasserstein-robust penalty on the control path."""
    return linear_mpc(model, x0, horizon, target, wdro_radius=radius, **kw)


def koopman_execution(
    prices, inventory: float, horizon: int, q: float = 1.0, r: float = 0.1
) -> np.ndarray:
    """RK362: state (price, inventory), control = shares sold per step; EDMDc is
    fitted on a simulated history of the caller's prices with random trades and
    MPC drives inventory to zero."""
    p = np.asarray(prices, float)
    rng = np.random.default_rng(0)
    trades = rng.uniform(0, 2 * inventory / horizon, size=len(p))
    inv = inventory - np.cumsum(np.r_[0.0, trades[:-1]])
    model = edmd(
        np.column_stack([p, inv]),
        dictionary=lambda x: poly_dictionary(x, 1),
        inputs=-trades[:, None],
    )
    u = linear_mpc(model, [p[-1], inventory], horizon, [p[-1], 0.0], q=q, r=r)
    return -u[:, 0]


def koopman_hedge_path(deltas, horizon: int, cost: float = 0.01) -> np.ndarray:
    """RK416/RK418: forecast the option book's delta with EDMD and choose hedge
    adjustments that track it with a quadratic cost on trading."""
    d = np.asarray(deltas, float)
    pred = koopman_predict(edmd(d[:, None]), d[-1:], horizon)[:, 0]
    hedge, path = -d[-1], []
    for target in -pred:
        hedge += (target - hedge) / (1.0 + cost)
        path.append(hedge)
    return np.array(path)


def koopman_curve_control(curve_factors, horizon: int, duration_target: float) -> np.ndarray:
    """RK417: forecast level/slope/curvature with EDMD and size a duration
    position against the predicted level change (sell duration ahead of rising yields)."""
    f = np.asarray(curve_factors, float)
    pred = koopman_predict(edmd(f, dictionary=lambda x: poly_dictionary(x, 1)), f[-1], horizon)
    level_change = pred[:, 0] - f[-1, 0]
    return duration_target * (1.0 - np.tanh(10.0 * level_change))


def koopman_surface_forecast(surfaces, steps: int = 1, rank: int = 3) -> np.ndarray:
    """RK320: forecast an implied-volatility surface (each row a flattened grid)
    with DMD; interpolation of a missing date is the same forecast from the prior one."""
    return dmd_forecast(np.asarray(surfaces, float).T, steps, rank).T


def koopman_surface_price(surfaces, spot, strikes, t, r=0.0, right="call") -> np.ndarray:
    """RK321: price options with tomorrow's DMD-forecast vols (one per strike)."""
    vols = np.clip(koopman_surface_forecast(surfaces, 1)[0], 1e-4, None)
    return np.array([bs_price(spot, k, t, r, v, right) for k, v in zip(strikes, vols, strict=True)])
