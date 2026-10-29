"""research/catalog/information.py -- transfer entropy and trend scanning."""

from __future__ import annotations

import numpy as np
import pytest

from engine.core.exceptions import ConfigurationError
from research.catalog.information import (
    TEContagionModel,
    effective_transfer_entropy,
    fbm_trend_positions,
    hurst_dfa,
    normalised_adjacency,
    simulate_fbm,
    te_graph_alpha,
    te_lead_lag_positions,
    te_macro_allocation,
    te_matrix,
    transfer_entropy,
    trend_scan,
)


def _lead_lag(n=2000, seed=0):
    rng = np.random.default_rng(seed)
    x = rng.normal(size=n)
    y = np.r_[0.0, 0.9 * x[:-1]] + 0.3 * rng.normal(size=n)
    return x, y


def test_transfer_entropy_is_directional():
    x, y = _lead_lag()
    assert transfer_entropy(x, y) > 0.3 > transfer_entropy(y, x)
    eff = effective_transfer_entropy(x, y, shuffles=20, rng=0)
    assert eff["p_value"] == 0.0 and eff["effective"] > 0.3
    m = te_matrix(np.column_stack([x, y, np.random.default_rng(1).normal(size=2000)]))
    assert m[0, 1] == m.max() and np.diag(m).tolist() == [0, 0, 0]


def test_lead_lag_and_macro_allocation():
    x, y = _lead_lag(600)
    pos = te_lead_lag_positions(x, y, window=200)
    active = pos[200:-1] > 0
    assert active.any() and (y[201:][active] > 0).mean() > 0.8
    assert (pos >= 0).all()
    rng = np.random.default_rng(2)
    macro = rng.normal(size=(500, 1))
    driven = np.r_[0.0, 0.5 * macro[:-1, 0]] + 0.2 * rng.normal(size=500)
    assets = np.column_stack([driven, 0.2 * rng.normal(size=500)])
    macro[-1] = 2.0  # a strong macro reading: the driven asset is forecast up
    out = te_macro_allocation(macro, assets)
    assert out["inflow"][0] > out["inflow"][1] and out["weights"][0] > 0.9


def test_graph_models_on_the_te_network():
    a = normalised_adjacency(np.array([[0, 1, 0], [0, 0, 1], [1, 0, 0]], float))
    assert a.sum(0) == pytest.approx([1, 1, 1])
    rng = np.random.default_rng(3)
    r = rng.normal(size=(1500, 3))
    for t in range(1, 1500):  # shocks in 0 spread to 1 next day
        if r[t - 1, 0] < -2:
            r[t, 1] = -3.0
    model = TEContagionModel()
    hist = model.fit(r, np.array([[0, 1, 0], [0, 0, 0], [0, 0, 0]], float))
    assert hist[-1] < hist[0]
    p = model.shock_probability(np.array([-5.0, 0.0, 0.0]))
    assert p[1] > 0.5 > p[2]
    lagged = rng.normal(size=(800, 3))
    follow = np.zeros_like(lagged)
    follow[1:, 1] = 0.8 * lagged[:-1, 0]
    rr = lagged * 0.2 + follow
    out = te_graph_alpha(rr, np.array([[0, 1, 0], [0, 0, 0], [0, 0, 0]], float), top=1)
    assert out["coef"][2] > 0.5


def test_fbm_hurst_and_trend_scanning():
    persistent = np.diff(simulate_fbm(1024, 0.8, rng=0))
    anti = np.diff(simulate_fbm(1024, 0.3, rng=0))
    assert hurst_dfa(persistent) > 0.65 and hurst_dfa(anti) < 0.45
    with pytest.raises(ConfigurationError):
        simulate_fbm(10, 1.2)
    up = np.linspace(100, 110, 50) + np.random.default_rng(4).normal(0, 0.1, 50)
    scan = trend_scan(up)
    assert scan["t"] > 10 and set(scan["tvalues"]) == {5, 10, 20, 40}
    with pytest.raises(ConfigurationError):
        trend_scan([1.0, 2.0])
    prices = np.exp(np.cumsum(0.002 + 0.01 * persistent))
    pos = fbm_trend_positions(prices[:400], window=300)
    assert set(np.unique(pos)) <= {0.0, 1.0}
