"""research/catalog/koopman.py -- DMD, EDMD, MPC and their applications."""

from __future__ import annotations

import numpy as np
import pytest

from engine.core.exceptions import ConfigurationError
from research.catalog.koopman import (
    DeepKoopman,
    deep_koopman_allocation,
    dmd,
    dmd_forecast,
    dmd_signal,
    edmd,
    koopman_curve_control,
    koopman_execution,
    koopman_factor_drift,
    koopman_hedge_path,
    koopman_mpc_allocation,
    koopman_predict,
    koopman_risk_scale,
    koopman_spread_position,
    koopman_surface_forecast,
    koopman_surface_price,
    linear_mpc,
    poly_dictionary,
    rbf_dictionary,
    robust_koopman_mpc,
)


def _rotation(n=40, theta=0.2, decay=0.99):
    a = decay * np.array([[np.cos(theta), -np.sin(theta)], [np.sin(theta), np.cos(theta)]])
    x = [np.array([1.0, 0.0])]
    for _ in range(n - 1):
        x.append(a @ x[-1])
    return np.array(x), a


def test_dmd_recovers_a_linear_system_and_forecasts_it():
    x, a = _rotation()
    d = dmd(x.T, rank=2)
    assert sorted(np.abs(d["eigenvalues"])) == pytest.approx([0.99, 0.99])
    pred = dmd_forecast(x.T, 3)
    assert pred[:, 0] == pytest.approx(a @ x[-1], abs=1e-8)
    with pytest.raises(ConfigurationError):
        dmd(np.ones((2, 2)))


def test_dmd_signal_follows_a_trend():
    p = np.exp(np.linspace(0, 1, 60))[:, None] * np.array([1.0, 2.0])
    sig = dmd_signal(p, window=10, rank=1)
    assert (sig[20:] == 1).all()


def test_edmd_is_exact_for_a_quadratic_map_in_its_dictionary():
    x = [np.array([0.5])]
    for _ in range(30):
        x.append(0.9 * x[-1])
    m = edmd(np.array(x))
    pred = koopman_predict(m, x[-1], 2)
    assert pred[:, 0] == pytest.approx([0.9 * x[-1][0], 0.81 * x[-1][0]], abs=1e-6)
    assert rbf_dictionary(np.zeros((3, 2)), np.ones((4, 2))).shape == (3, 7)
    assert poly_dictionary(np.ones((2, 2))).shape == (2, 6)


def test_mpc_drives_a_controlled_state_to_target_and_robust_mpc_is_gentler():
    rng = np.random.default_rng(0)
    u = rng.normal(size=60)
    x = np.zeros(60)
    for t in range(59):
        x[t + 1] = 0.8 * x[t] + u[t]
    m = edmd(x[:, None], dictionary=lambda s: poly_dictionary(s, 1), inputs=u[:, None])
    path = linear_mpc(m, [5.0], 4, [0.0], q=1.0, r=1e-3)
    assert koopman_predict(m, [5.0], 4, path)[-1, 0] == pytest.approx(0.0, abs=0.05)
    rob = robust_koopman_mpc(m, [5.0], 4, [0.0], radius=5.0, q=1.0, r=1e-3)
    assert np.abs(rob).sum() < np.abs(path).sum()
    with pytest.raises(ConfigurationError):
        linear_mpc(edmd(x[:, None]), [1.0], 2, [0.0])


def test_deep_koopman_learns_and_allocates():
    x, _ = _rotation(60)
    model = DeepKoopman(2, latent=2, hidden=8, seed=0)
    hist = model.fit(x, steps=200, lr=0.02)
    assert hist[-1] < 0.5 * hist[0]
    assert model.predict(x[-1], 3).shape == (3, 2)
    w = deep_koopman_allocation(model, x[-1], 2)
    assert w.sum() == pytest.approx(1.0) or w.sum() == 0


def test_trading_applications_have_the_right_signs():
    rng = np.random.default_rng(1)
    spread = np.zeros(200)
    for i in range(199):
        spread[i + 1] = 0.8 * spread[i] + rng.normal(0, 0.1)
    spread[-1] = 1.0  # a shock above the mean: predicted to revert, so short the spread
    assert koopman_spread_position(spread) < 0 < koopman_spread_position(-spread)
    r = rng.normal(0, 0.01, size=(120, 3)) + np.array([0.003, 0.0, -0.003])
    w = koopman_mpc_allocation(r, horizon=5, turnover=0.0)
    assert w.sum() == pytest.approx(1.0) and w[0] > w[2]
    assert koopman_factor_drift(np.cumsum(rng.normal(size=(50, 2)), 0), 3).shape == (3, 2)
    vol = np.r_[np.full(40, 0.1), np.linspace(0.1, 0.4, 20)]
    assert koopman_risk_scale(vol, 0.15) < 1.0
    sells = koopman_execution(100 + np.cumsum(rng.normal(0, 0.1, 60)), 1000.0, 5)
    assert sells.sum() == pytest.approx(1000.0, rel=0.25)
    assert koopman_hedge_path(np.linspace(0.3, 0.6, 30), 3).shape == (3,)
    f = np.column_stack([np.linspace(0.02, 0.05, 40), np.zeros(40), np.zeros(40)])
    assert koopman_curve_control(f, 3, 5.0)[-1] < 5.0
    surf = 0.2 + 0.01 * np.sin(np.arange(30)[:, None] * 0.3 + np.arange(5))
    assert koopman_surface_forecast(surf).shape == (1, 5)
    px = koopman_surface_price(surf, 100.0, [90, 95, 100, 105, 110], 0.5)
    assert (np.diff(px) < 0).all()
