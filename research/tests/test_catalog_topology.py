"""research/catalog/topology.py -- persistent homology and its summaries."""

from __future__ import annotations

import numpy as np
import pytest

from engine.core.exceptions import ConfigurationError
from research.catalog.topology import (
    betti0_contagion,
    betti2_macro_stress,
    betti_curve,
    correlation_distance,
    delay_embedding,
    diagram_clusters,
    diagram_distance,
    finite,
    landscape_norm,
    landscape_norm_series,
    multiscale_rips_score,
    persistence_landscape,
    rips_persistence,
    stress_alert,
    tda_exposure,
    total_persistence,
)


def _circle(n=12, r=1.0, noise=0.0, seed=0):
    t = np.linspace(0, 2 * np.pi, n, endpoint=False)
    pts = r * np.column_stack([np.cos(t), np.sin(t)])
    return pts + np.random.default_rng(seed).normal(0, noise, pts.shape)


def test_circle_has_one_loop_and_one_component():
    dg = rips_persistence(_circle(), max_dim=1)
    assert np.isinf(dg[0][:, 1]).sum() == 1 and len(dg[0]) == 12
    assert len(dg[1]) == 1
    birth, death = dg[1][0]
    assert birth == pytest.approx(2 * np.sin(np.pi / 12))  # neighbour chord
    assert death == pytest.approx(np.sqrt(3), abs=0.3)  # triangle that fills it
    with pytest.raises(ConfigurationError):
        rips_persistence()


def test_sphere_has_a_void():
    n = 20
    i = np.arange(n) + 0.5
    phi, theta = np.arccos(1 - 2 * i / n), np.pi * (1 + 5**0.5) * i
    pts = np.column_stack([np.cos(theta) * np.sin(phi), np.sin(theta) * np.sin(phi), np.cos(phi)])
    dg = rips_persistence(pts, max_dim=2)
    life = dg[2][:, 1] - dg[2][:, 0]
    assert life.max() > 0.3 and (life > 0.3).sum() == 1


def test_landscape_betti_curve_and_distance():
    dg = np.array([[0.0, 2.0], [0.5, np.inf]])
    grid = np.linspace(0, 2, 201)
    land = persistence_landscape(dg, grid, k=2)
    assert land[0].max() == pytest.approx(1.0) and land[1].max() == 0.0
    assert landscape_norm(land, grid, 2) == pytest.approx(np.sqrt(2 / 3), rel=1e-3)
    assert list(betti_curve(dg, [0.25, 1.0, 3.0])) == [1, 2, 1]
    assert total_persistence(dg) == 2.0 and finite(dg, cap=3.0)[1, 1] == 3.0
    assert diagram_distance(dg, dg) == 0.0
    assert diagram_distance([[0.0, 2.0]], np.empty((0, 2))) == pytest.approx(1.0)
    assert diagram_distance([[0.0, 2.0]], [[0.0, 2.5]]) == pytest.approx(0.5)


def test_embedding_and_correlation_distance():
    assert delay_embedding(np.arange(10.0), 3, 2).tolist()[0] == [0.0, 2.0, 4.0]
    with pytest.raises(ConfigurationError):
        delay_embedding(np.arange(3.0), 3, 2)
    r = np.random.default_rng(0).normal(size=(100, 3))
    d = correlation_distance(np.column_stack([r, r[:, 0]]))
    assert d[0, 3] == pytest.approx(0.0, abs=1e-6) and d[0, 1] == pytest.approx(np.sqrt(2), abs=0.3)


def test_landscape_series_is_causal_and_alerts_on_a_regime_change():
    rng = np.random.default_rng(1)
    calm = rng.normal(0, 1, size=(60, 3)) * 0.01
    loops = np.column_stack([_circle(30, noise=0.05), rng.normal(0, 0.01, 30)])
    r = np.vstack([calm, loops])
    s = landscape_norm_series(r, window=15)
    r2 = r.copy()
    r2[70:] *= 5
    assert np.allclose(landscape_norm_series(r2, window=15)[:70], s[:70], equal_nan=True)
    score = np.r_[np.ones(50) + 0.01 * rng.normal(size=50), [5.0]]
    alerts = stress_alert(score, lookback=40)
    assert alerts[-1] and not alerts[:-1].any()
    assert tda_exposure(score, lookback=40, floor=0.25)[-1] == 0.25


def test_contagion_clusters_and_multiscale_scores():
    rng = np.random.default_rng(2)
    indep = rng.normal(size=(60, 5))
    common = rng.normal(size=(60, 1)) + 0.1 * rng.normal(size=(60, 5))
    b0 = betti0_contagion(np.vstack([indep, common]), window=60)
    assert b0[59] == 5 and b0[-1] == 1
    small = [rips_persistence(rng.normal(0, 0.05, (10, 2)))[1] for _ in range(3)]
    big = [rips_persistence(_circle(10, r=3, noise=0.05, seed=s))[1] for s in range(3)]
    labels, crisis = diagram_clusters(small + big, 2)
    assert (labels[3:] == crisis).all() and (labels[:3] != crisis).all()
    macro = np.sin(np.arange(60) * 0.4) + 0.05 * rng.normal(size=60)
    stress = betti2_macro_stress(macro, dim=3, window=15)
    assert np.isfinite(stress[-1]) and (stress[np.isfinite(stress)] >= 0).all()
    score = multiscale_rips_score(rng.normal(size=(90, 3)), windows=(10, 15), lookback=30)
    assert np.isnan(score[:30]).all() and np.isfinite(score[-1])
