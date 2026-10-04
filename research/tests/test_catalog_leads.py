"""research/catalog/leads.py -- the catalog's gap-analysis leads."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from engine.core.exceptions import ConfigurationError
from research.catalog.leads import (
    almgren_chriss,
    almgren_chriss_objective,
    cppi_path,
    fit_har,
    grossman_zhou_multiplier,
    har_features,
    har_forecast,
    hayashi_yoshida,
    hy_lead_lag,
    lagged_cross_correlation,
    olmar_weights,
    overnight_intraday,
    pamr_weights,
    portfolio_wealth,
    project_to_simplex,
    realized_variance,
    same_interval_signal,
    vix_term_structure_regime,
)


def test_simplex_projection_is_the_nearest_point():
    v = np.array([0.8, 0.6, -0.2])
    b = project_to_simplex(v)
    assert b.sum() == pytest.approx(1.0) and (b >= 0).all()
    assert b == pytest.approx([0.6, 0.4, 0.0])
    rng = np.random.default_rng(0)
    for _ in range(200):  # no random simplex point is closer
        w = rng.dirichlet(np.ones(3))
        assert np.linalg.norm(w - v) >= np.linalg.norm(b - v) - 1e-12


def _seesaw(n=60):
    a = np.cumprod(np.r_[1.0, np.tile([1.1, 1 / 1.1], n // 2)])
    return np.column_stack([a, np.ones_like(a)])


def test_olmar_and_pamr_profit_from_a_mean_reverting_pair():
    p = _seesaw()
    w_ol, w_pa = olmar_weights(p, window=2), pamr_weights(p, epsilon=0.5)
    assert (w_ol.sum(1) == pytest.approx(1.0)) and (w_pa >= 0).all()
    assert portfolio_wealth(p, w_ol)[-1] > 1.5 and portfolio_wealth(p, w_pa)[-1] > 1.5
    # after the asset rises, PAMR moves toward the other one
    assert w_pa[1][0] < 0.5
    with pytest.raises(ConfigurationError):
        pamr_weights(p, variant=3)


def test_cppi_holds_the_floor_and_grossman_zhou_ratchets():
    r = np.r_[np.full(10, 0.05), np.full(30, -0.04)]
    plain = cppi_path(r, multiplier=4, floor_fraction=0.7)
    assert plain["exposure"].iloc[0] == pytest.approx(min(4 * 0.3, 1.0))
    assert plain["value"].min() > 0.7 - 0.02  # small gap risk at discrete steps
    gz = cppi_path(r, multiplier=4, floor_fraction=0.7, ratchet_alpha=0.85)
    peak = gz["value"].cummax()
    assert (gz["value"] >= 0.85 * peak.shift(1).fillna(1.0) - 0.03).all()
    assert gz["value"].iloc[-1] > plain["value"].iloc[-1]
    assert grossman_zhou_multiplier(0.08, 0.02, 0.2, 2.0) == pytest.approx(0.75)


def test_har_recovers_its_own_coefficients():
    rng = np.random.default_rng(1)
    rv = list(np.full(22, 1.0))
    for _ in range(3000):
        s = pd.Series(rv)
        nxt = 0.1 + 0.4 * s.iloc[-1] + 0.3 * s.iloc[-5:].mean() + 0.2 * s.iloc[-22:].mean()
        rv.append(nxt * np.exp(rng.normal(0, 0.1)))
    coef = fit_har(rv)
    assert coef == pytest.approx([0.1, 0.4, 0.3, 0.2], abs=0.08)
    f = har_features(rv).iloc[-1]
    assert har_forecast(rv, coef) == pytest.approx(coef @ [1, f.rv_d, f.rv_w, f.rv_m])
    idx = pd.to_datetime(["2024-01-02 10:00", "2024-01-02 11:00", "2024-01-03 10:00"])
    assert realized_variance(pd.Series([0.01, -0.02, 0.03], index=idx)).tolist() == pytest.approx(
        [0.0005, 0.0009]
    )


def test_vix_term_structure_regime_is_lagged():
    out = vix_term_structure_regime([15, 25, 18], [18, 20, 19])
    assert out["ratio"].tolist() == pytest.approx([15 / 18, 1.25, 18 / 19])
    assert np.isnan(out["risk_on"].iloc[0]) and out["risk_on"].tolist()[1:] == [1.0, 0.0]


def test_cross_correlation_and_hayashi_yoshida_find_the_lead():
    rng = np.random.default_rng(2)
    x = rng.normal(size=500)
    y = np.r_[np.zeros(2), x[:-2]] + 0.1 * rng.normal(size=500)  # x leads by 2
    cc = lagged_cross_correlation(x, y, 4)
    assert cc.idxmax() == 2
    # HY on synchronous grids equals the realised covariance
    t = np.arange(6.0)
    px, py = np.array([0, 1, 3, 2, 4, 5.0]), np.array([0, 2, 1, 1, 3, 2.0])
    assert hayashi_yoshida(t, px, t, py) == pytest.approx(np.diff(px) @ np.diff(py))
    # asynchronous: y observed every other tick
    assert hayashi_yoshida(t, px, t[::2], py[::2]) == pytest.approx(
        (1 + 2) * (1 - 0) + (-1 + 2) * (3 - 1)
    )
    tx = np.arange(400.0)
    path = np.cumsum(rng.normal(size=400))
    best, _ = hy_lead_lag(tx, path, tx + 3, path, shifts=range(-5, 6))
    assert best == 3.0


def test_same_interval_signal_and_overnight_split():
    r = pd.DataFrame(np.tile([0.01, -0.02, 0.0], (30, 1)))
    sig = same_interval_signal(r, lookback_days=5)
    assert sig.iloc[:5].isna().all().all() and sig.iloc[5].tolist() == pytest.approx(
        [0.01, -0.02, 0.0]
    )
    s = overnight_intraday([100, 102, 99], [101, 100, 103])
    assert ((1 + s.overnight) * (1 + s.intraday)).iloc[1:].tolist() == pytest.approx(
        (1 + s.close_to_close).iloc[1:].tolist()
    )


def test_almgren_chriss_trajectory():
    twap = almgren_chriss(1000, 1.0, 10, sigma=0.3, eta=0.01)
    assert twap["holdings"] == pytest.approx(np.linspace(1000, 0, 11))
    ac = almgren_chriss(1000, 1.0, 10, sigma=0.3, eta=0.01, gamma=0.002, risk_aversion=1e-3)
    assert ac["holdings"][0] == 1000 and ac["holdings"][-1] == pytest.approx(0, abs=1e-9)
    assert ac["trades"][0] > ac["trades"][-1]  # front-loaded when risk-averse
    base = almgren_chriss_objective(ac["holdings"], 1.0, 0.3, 0.01, 0.002, 0.0, 1e-3)
    rng = np.random.default_rng(3)
    for _ in range(50):  # the closed form beats nearby paths
        x = ac["holdings"].copy()
        x[1:-1] += rng.normal(0, 5, 9)
        assert almgren_chriss_objective(x, 1.0, 0.3, 0.01, 0.002, 0.0, 1e-3) >= base - 1e-9
    assert ac["expected_cost"] + 1e-3 * ac["variance"] == pytest.approx(base)
    with pytest.raises(ConfigurationError):
        almgren_chriss(10, 1.0, 2, sigma=0.1, eta=0.001, gamma=1.0)
