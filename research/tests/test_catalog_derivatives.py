"""research/catalog/derivatives.py -- pricing identities and hedging learners."""

from __future__ import annotations

import numpy as np
import pytest

from engine.core.exceptions import ConfigurationError
from research.catalog.derivatives import (
    DeepHedger,
    NeuralCalibrator,
    NeuralLocalVol,
    bounds_signal,
    burgers_residual,
    delay_sv_call,
    dgm_black_scholes,
    dispersion_pnl,
    fit_pinn,
    fit_smile,
    gamma_scalp_pnl,
    gbm_paths,
    heston_call,
    implied_correlation,
    iron_backtest,
    iron_credit,
    iron_payoff,
    iron_strikes,
    lewis_call,
    modulus,
    realized_correlation,
    robust_price_bounds,
    rough_bergomi_paths,
    rough_heston_cf,
    rough_heston_smile,
    rough_vol_surface,
    schrodinger_residual,
    surface_relative_value,
    worst_case_sampler,
)
from research.catalog.options import bs_price


def test_dispersion_identities():
    w, s = np.array([0.5, 0.5]), np.array([0.2, 0.3])
    index_vol = np.sqrt(w @ (np.outer(s, s) * np.array([[1, 0.6], [0.6, 1]])) @ w)
    assert implied_correlation(index_vol, w, s) == pytest.approx(0.6)
    rng = np.random.default_rng(0)
    comp = rng.multivariate_normal([0, 0], [[1, 0.3], [0.3, 1]], 20000) * 0.01
    assert realized_correlation(comp @ w, comp, w) == pytest.approx(0.3, abs=0.03)
    assert dispersion_pnl(w, [0.04, 0.09], [0.05, 0.10], 0.05, 0.05) == pytest.approx(0.01)


def test_iron_condor_and_butterfly():
    k = iron_strikes(100, 0.05, 0.05)
    assert k == pytest.approx((90, 95, 105, 110))
    assert iron_payoff([100, 80, 120, 97], k).tolist() == pytest.approx([0, 5, 5, 0])
    credit = iron_credit(100, k, 30 / 365, 0.0, 0.2)
    assert 0 < credit < 5
    fly = iron_strikes(100, 0.0, 0.05)
    assert iron_credit(100, fly, 30 / 365, 0.0, 0.2) > credit
    calm = 100 * np.ones(200)
    assert (iron_backtest(calm, np.full(200, 0.2)) > 0).all()


def test_gamma_scalping_tracks_realised_minus_implied():
    rng = np.random.default_rng(1)
    dt = 1 / 252
    p = 100 * np.exp(np.cumsum(np.r_[0, 0.4 * np.sqrt(dt) * rng.normal(size=63)]))
    out = gamma_scalp_pnl(p, 0.2, 100, 0.25)
    assert out["pnl"] > 0 and np.sign(out["approx"]) == np.sign(out["pnl"])
    quiet = 100 * np.exp(np.cumsum(np.r_[0, 0.05 * np.sqrt(dt) * rng.normal(size=63)]))
    assert gamma_scalp_pnl(quiet, 0.2, 100, 0.25)["pnl"] < 0


def test_heston_rough_heston_and_jumps():
    args = (2.0, 0.04, 0.3, -0.7, 0.04)
    for k in (90, 100, 110):
        rough_half = lewis_call(100, k, lambda u: rough_heston_cf(u, 0.5, 0.5, *args))
        assert rough_half == pytest.approx(heston_call(100, k, 0.5, 0.0, *args), rel=1e-3)
    bs_like = heston_call(100, 100, 0.5, 0.0, 2.0, 0.04, 1e-3, 0.0, 0.04)
    assert bs_like == pytest.approx(bs_price(100, 100, 0.5, 0.0, 0.2), rel=1e-3)
    params = dict(hurst=0.1, lam=0.3, theta=0.04, nu=0.3, rho=-0.7, v0=0.04)
    smile = rough_heston_smile(100, [90, 100, 110], 0.5, params)
    assert smile[0] > smile[1] > smile[2]  # negative skew
    jumpy = rough_heston_smile(
        100, [80, 100], 0.5, params, jump_intensity=1.0, jump_mean=-0.1, jump_sd=0.05
    )
    assert jumpy[0] > smile[0] * 0.9
    fitted = fit_smile(
        100,
        [90, 100, 110],
        0.5,
        smile,
        rough_heston_smile,
        {"hurst": 0.2, "lam": 0.3, "theta": 0.04, "nu": 0.2, "rho": -0.5, "v0": 0.04},
        {
            "hurst": (0.05, 0.45),
            "lam": (0.3, 0.3),
            "theta": (0.04, 0.04),
            "nu": (0.05, 0.6),
            "rho": (-0.9, 0.0),
            "v0": (0.04, 0.04),
        },
    )
    assert fitted["sse"] < 1e-4


def test_neural_calibrator_recovers_parameters_and_delay_model_prices():
    grid = [(90.0, 0.5), (100.0, 0.5), (110.0, 0.5)]
    cal = NeuralCalibrator(
        lambda s, k, t, v0, rho: heston_call(s, k, t, 0.0, 2.0, 0.04, 0.4, rho, v0),
        {"v0": (0.02, 0.08), "rho": (-0.9, 0.0)},
        grid,
        seed=0,
    )
    hist = cal.train(n_samples=80, steps=300)
    assert hist[-1] < 0.1 * hist[0]
    true = {"v0": 0.05, "rho": -0.5}
    out = cal.calibrate(cal._vols(true))
    assert out["v0"] == pytest.approx(0.05, abs=0.01) and out["rho"] == pytest.approx(-0.5, abs=0.2)
    c1 = delay_sv_call(100, 100, 0.5, 2.0, 0.04, 0.3, delay=0.1, paths=2000)
    assert 3 < c1 < 8


def test_rough_bergomi_surface_and_relative_value():
    p = rough_bergomi_paths(2000, 20, 0.1, 1.5, -0.7, rng=0)
    assert p.shape == (2000, 21) and p[:, -1].mean() == pytest.approx(100, rel=0.02)
    vols = rough_vol_surface(100, [95, 100, 105], 1 / 12, 0.1, 1.5, -0.7, n=2000, steps=20)
    assert vols[0] > vols[2]
    assert surface_relative_value([0.18, 0.2, 0.25], [0.2, 0.2, 0.2]).tolist() == [1, 0, -1]


def test_deep_hedger_beats_no_hedge_and_robust_sampler_picks_the_worst():
    rng = np.random.default_rng(2)
    hedger = DeepHedger(100.0, seed=0)
    hist = hedger.fit(lambda: gbm_paths(256, 10, 0.2, rng=rng), steps=150)
    test = gbm_paths(2000, 10, 0.2, rng=9)
    unhedged = np.maximum(test[:, -1] - 100, 0)
    cvar_unhedged = np.sort(unhedged)[int(0.9 * 2000) :].mean()
    assert hedger.price(test) < cvar_unhedged and hist[-1] < hist[0]
    for kind in ("signature", "operator"):
        h = DeepHedger(100.0, features=kind, cost=0.001, seed=0)
        h.fit(lambda: gbm_paths(64, 6, 0.2, rng=rng), steps=10)
        assert np.isfinite(h.price(gbm_paths(64, 6, 0.2, rng=1)))
    with pytest.raises(ConfigurationError):
        DeepHedger(100.0, features="bad")
    gens = [lambda n, s: gbm_paths(n, 10, 0.1, rng=s), lambda n, s: gbm_paths(n, 10, 0.4, rng=s)]
    sampler = worst_case_sampler(hedger, gens, n=256, rng=0)
    batch = sampler()
    assert np.log(batch[:, -1] / batch[:, 0]).std() > 0.05  # the high-volatility model


def test_pde_solvers():
    # payoff x^2 has the closed form u(0, x) = x^2 exp((r + sigma^2) T)
    model = dgm_black_scholes(0.5, 0.05, 0.2, payoff=lambda x: x**2, steps=300)
    got = model(np.zeros(3), np.array([0.9, 1.0, 1.1])).data[:, 0]
    assert got == pytest.approx(np.array([0.81, 1.0, 1.21]) * np.exp(0.045), rel=0.02)
    t = np.linspace(0, 1, 20)
    x = np.linspace(-1, 1, 20)
    tt, xx = np.meshgrid(t, x)
    vol = 0.2 + 0.05 * np.tanh(xx.ravel() - tt.ravel())
    burg = fit_pinn(tt.ravel(), xx.ravel(), vol, burgers_residual(0.05), steps=200)
    assert burg["history"][-1] < burg["history"][0]
    schr = fit_pinn(
        tt.ravel(), xx.ravel(), vol, schrodinger_residual, n_out=2, steps=100, readout=modulus
    )
    assert schr["history"][-1] < schr["history"][0]


def test_neural_sde_bounds():
    strikes = [95.0, 100.0, 105.0]
    market = [bs_price(100, k, 0.5, 0.0, 0.2) for k in strikes]
    models = []
    for seed in range(2):
        m = NeuralLocalVol(paths=1000, steps=10, seed=seed)
        hist = m.calibrate(strikes, market, steps=80)
        assert hist[-1] < hist[0]
        models.append(m)
    lo, hi = robust_price_bounds(models, 100.0)
    assert (
        lo <= hi and bounds_signal(lo - 1, (lo, hi)) == 1 and bounds_signal(hi + 1, (lo, hi)) == -1
    )
