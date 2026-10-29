"""research/catalog/carry_rates.py -- carry, futures and curve models."""

from __future__ import annotations

import numpy as np
import pytest

from engine.core.exceptions import ConfigurationError
from research.catalog.carry_rates import (
    LatentForceGP,
    NeuralDelayCurve,
    basis_factor,
    basis_signal,
    bond_carry_rolldown,
    calendar_spread_positions,
    carry_composite,
    cash_venue,
    dns_forecast,
    double_sort,
    duration_momentum,
    dv01,
    fit_musiela_pinn,
    fpca,
    fpca_forecast,
    fx_carry,
    fx_carry_portfolio,
    index_carry,
    index_fair_value,
    inflation_regimes,
    musiela_curve,
    nelson_siegel_loadings,
    rank_weights,
    regime_rotation,
    roll_yield,
    slope_signal,
    steepener_notionals,
    steepener_pnl,
)

MATS = np.array([3.0, 6, 12, 24, 36, 60, 84, 120])


def test_carry_measures_and_rank_weights():
    assert fx_carry([1.0], [0.98], 1.0)[0] == pytest.approx(0.0204, abs=1e-4)
    assert roll_yield([100], [95], 0.5)[0] > 0 and index_carry([100], [101], 1.0)[0] < 0
    out = bond_carry_rolldown([1, 2, 5, 10], [0.02, 0.025, 0.03, 0.035], horizon=0.25)
    assert (out["rolldown"] > 0).all() and out["total"][-1] > out["total"][0]
    w = rank_weights([0.01, 0.03, 0.02])
    assert (
        w.sum() == pytest.approx(0.0) and np.argmax(w) == 1 and np.abs(w).sum() == pytest.approx(2)
    )
    comp = carry_composite({"fx": [0.01, 0.05], "cmdty": [0.1, -0.1, 0.0]}, long_only=True)
    assert comp["fx"].tolist() == [0.0, 0.5] and comp["cmdty"][0] == 0.5
    fxw = fx_carry_portfolio([0.05, 0.01, 0.03, -0.01], k=1)
    assert fxw.tolist() == [1, 0, 0, -1]
    calm_then_wild = np.r_[np.full(260, 0.1), [0.5]]
    assert not fx_carry_portfolio([0.05, 0.01], 1, calm_then_wild, vol_z_exit=2.0).any()


def test_commodity_sorts_and_futures_rules():
    w = double_sort([0.2, 0.1, -0.1, -0.2, 0.0, 0.05], [0.1, 0.05, -0.05, -0.1, 0.0, -0.02])
    assert w.tolist() == [0.5, 0.5, -0.5, -0.5, 0.0, 0.0]
    assert basis_factor([0.1, -0.1, 0.0, 0.05], 0.25).tolist() == [1, -1, 0, 0]
    assert basis_factor([0.1, -0.1, 0.0, 0.05], 0.25, long_only=True).tolist() == [1, 0, 0, 0]
    fair = index_fair_value(100.0, 0.05, 0.02, 1.0)
    assert basis_signal([fair * 1.01, fair, fair * 0.99], 100.0, 0.05, 0.02, 1.0).tolist() == [
        -1,
        0,
        1,
    ]
    rng = np.random.default_rng(0)
    far = 100 + np.cumsum(rng.normal(size=400))
    noise = np.zeros(400)
    for t in range(399):
        noise[t + 1] = 0.8 * noise[t] + rng.normal()
    out = calendar_spread_positions(1.1 * far + 0.3 * noise, far, window=200)
    assert out["hedge"][-1] == pytest.approx(1.1, abs=0.15) and set(out["positions"]) <= {-1, 0, 1}


def test_duration_momentum_and_steepeners():
    up = np.exp(np.linspace(0, 0.3, 400) + 0.002 * np.random.default_rng(1).normal(size=400))
    pos = duration_momentum(up)
    assert pos[-1] > 0 and (pos >= 0).all()
    d2, d10 = dv01(0.04, 2), dv01(0.045, 10)
    assert d10 > d2 > 0
    n = steepener_notionals(d2, d10)
    assert n["short_long_maturity"] * d10 == pytest.approx(1e6 * d2)
    assert steepener_pnl(d2, d10, [0.0], [10.0])[0] > 0
    assert steepener_pnl(d2, d10, [10.0], [10.0])[0] == pytest.approx(0.0, abs=1e-6)
    ys = np.full(300, 0.04)
    yl = np.r_[np.full(299, 0.05) + 0.0005 * np.random.default_rng(2).normal(size=299), [0.04]]
    assert slope_signal(ys, yl)[-1] == 1


def test_regimes_and_cash_venue():
    cpi = np.r_[np.full(24, 0.02), np.linspace(0.02, 0.08, 24), np.linspace(0.08, 0.03, 24)]
    states = inflation_regimes(cpi)
    assert states[0] == -1 and 3 in states and 2 in states
    rng = np.random.default_rng(3)
    rets = rng.normal(0, 0.01, (72, 2))
    rets[states == 3, 1] += 0.05  # asset 1 wins in high-and-rising inflation
    w = regime_rotation(rets, states, train=60)
    assert w[60:][states[60:] == 3, 1].all() if (states[60:] == 3).any() else True
    choice = cash_venue(0.050, 0.053, 0.052)
    assert choice["choice"] == "money_fund" and choice["bills_below_floor"]
    assert cash_venue(0.050, 0.053, 0.052, rrp_access=True)["choice"] == "on_rrp"


def test_curve_models():
    rng = np.random.default_rng(4)
    load = nelson_siegel_loadings(MATS)
    assert load[:, 0].tolist() == [1.0] * len(MATS) and load[0, 1] > load[-1, 1]
    f = np.cumsum(rng.normal(0, 0.01, (120, 3)), axis=0) + np.array([0.04, -0.01, 0.0])
    curves = f @ load.T + 0.0001 * rng.normal(size=(120, len(MATS)))
    assert dns_forecast(curves, MATS).shape == (len(MATS),)
    pc = fpca(curves, MATS)
    assert pc["explained"].sum() > 0.95 and pc["scores"].shape == (120, 3)
    fc = fpca_forecast(curves, MATS)
    assert np.abs(fc - curves[-1]).max() < 0.01
    t = np.arange(80)
    series = np.sin(t / 8.0) + 0.05 * rng.normal(size=80)
    gp = LatentForceGP().fit(series)
    out = gp.forecast(5)
    assert out["mean"].shape == (5,) and (out["sd"] > 0).all()
    assert abs(out["mean"][0] - np.sin(80 / 8.0)) < 0.5
    ndc = NeuralDelayCurve(3, delay=3, seed=0)
    hist = ndc.fit(pc["scores"], steps=150)
    assert hist[-1] < hist[0] and ndc.forecast(pc["scores"], 2).shape == (2, 3)
    with pytest.raises(ConfigurationError):
        NeuralDelayCurve(3, delay=10).fit(pc["scores"][:5])


def test_musiela_pinn_fits_forward_curves():
    times = np.linspace(0, 1, 6)
    mats = np.linspace(0.5, 10, 8)
    sigma = 0.01
    # a curve satisfying df/dt = df/dx + sigma^2 x: f = a + b (x + t) + sigma^2 (x t + t^2 / 2)
    tt, xx = np.meshgrid(times, mats, indexing="ij")
    fwd = 0.02 + 0.002 * (xx + tt) + sigma**2 * (xx * tt + tt**2 / 2)
    out = fit_musiela_pinn(times, mats, fwd, sigma, steps=300)
    assert out["history"][-1] < out["history"][0]
    assert np.abs(musiela_curve(out["model"], 0.5, mats) - fwd[3]).max() < 0.01
