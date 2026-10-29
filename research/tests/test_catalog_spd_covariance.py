"""research/catalog/spd_covariance.py -- SPD geometry and covariance estimators."""

from __future__ import annotations

import numpy as np
import pytest

from engine.core.exceptions import ConfigurationError
from research.catalog.spd_covariance import (
    GATShrinkage,
    airm_distance,
    entropic_risk,
    entropic_weights,
    gat_dynamic_allocation,
    gat_graph_diffusion_covariance,
    gat_log_spectral_covariance,
    gat_riemannian_shrinkage,
    gat_spectral_covariance,
    gelbrich_worst_variance,
    geodesic,
    geodesic_smoothed_covariances,
    graph_diffusion_covariance,
    karcher_mean,
    ledoit_wolf,
    log_euclidean_mean,
    log_spectral_shrinkage,
    metric_diffusion_risk_parity,
    nearest_spd,
    riemannian_entropic_weights,
    riemannian_gat_weights,
    riemannian_min_variance,
    riemannian_wdro_weights,
    rmt_clip,
    spd_exp,
    spd_log,
)


def _spd(n=3, seed=0):
    a = np.random.default_rng(seed).normal(size=(n, n))
    return a @ a.T + n * np.eye(n)


def _block_returns(t=240, seed=0):
    rng = np.random.default_rng(seed)
    f = rng.normal(size=(t, 2))
    load = np.array([[1, 0], [1, 0], [1, 0], [0, 1], [0, 1], [0, 1]], float)
    return 0.01 * (f @ load.T + rng.normal(size=(t, 6)))


def test_geometry_identities():
    a, b = _spd(seed=0), _spd(seed=1)
    assert spd_exp(spd_log(a)) == pytest.approx(a)
    assert geodesic(a, b, 0.0) == pytest.approx(a) and geodesic(a, b, 1.0) == pytest.approx(b)
    mid = geodesic(a, b, 0.5)
    assert airm_distance(a, mid) == pytest.approx(airm_distance(mid, b), rel=1e-6)
    assert airm_distance(a, b) == pytest.approx(airm_distance(b, a), rel=1e-6)
    assert karcher_mean([a, b]) == pytest.approx(mid, rel=1e-6)
    assert karcher_mean([a]) == pytest.approx(a)
    assert np.linalg.det(log_euclidean_mean([a, b])) == pytest.approx(
        np.sqrt(np.linalg.det(a) * np.linalg.det(b)), rel=1e-6
    )
    assert np.linalg.eigvalsh(nearest_spd(np.diag([1.0, -1.0]))).min() > 0


def test_classical_cleaning_and_diffusion_keep_matrices_spd():
    r = _block_returns()
    assert ledoit_wolf(r).shape == (6, 6)
    corr = np.corrcoef(r[:30].T)
    clipped = rmt_clip(corr, 30)
    assert np.diag(clipped) == pytest.approx(1.0) and np.linalg.eigvalsh(clipped).min() > 0
    c = _spd(4)
    shrunk = log_spectral_shrinkage(c, 1.0)
    assert (
        np.allclose(shrunk, shrunk[0, 0] * np.eye(4)) or np.ptp(np.linalg.eigvalsh(shrunk)) < 1e-9
    )
    adj = np.ones((4, 4)) - np.eye(4)
    d = graph_diffusion_covariance(c, adj, t=0.5, lam=0.5)
    assert np.linalg.eigvalsh(d).min() > 0
    assert graph_diffusion_covariance(c, adj, lam=0.0) == pytest.approx(c)


def test_gat_shrinkage_learns_and_feeds_every_variant():
    r = _block_returns()
    model = GATShrinkage(seed=0)
    hist = model.fit(r, steps=150)
    assert hist[-1] < hist[0]
    for cov in (
        model.covariance(r),
        gat_spectral_covariance(model, r),
        gat_riemannian_shrinkage(model, r),
        gat_graph_diffusion_covariance(model, r),
        gat_log_spectral_covariance(model, r),
    ):
        assert cov.shape == (6, 6) and np.linalg.eigvalsh(cov).min() > 0
    alpha = model.attention(np.random.default_rng(0).normal(size=(6, 4))).data
    assert alpha.sum(1) == pytest.approx(1.0)
    with pytest.raises(ConfigurationError):
        model.fit(r[:4])
    dyn = gat_dynamic_allocation(r, window=120, step=60, steps=30)
    assert len(dyn) == 3 and all(w.sum() == pytest.approx(1.0) for w in dyn.values())
    assert riemannian_gat_weights(r, steps=30).sum() == pytest.approx(1.0)


def test_manifold_allocations():
    r = _block_returns()
    w = riemannian_min_variance(r, 60, 30)
    assert w.sum() == pytest.approx(1.0) and (w > -1e-9).all()
    smooth = geodesic_smoothed_covariances(r, 60, 0.3, step=10)
    assert all(np.linalg.eigvalsh(c).min() > 0 for c in smooth)
    rp = metric_diffusion_risk_parity(r, 60, 0.3, step=30)
    assert rp.shape[1] == 6 and rp.sum(1) == pytest.approx(1.0)
    c = _spd(3)
    eq = np.full(3, 1 / 3)
    assert gelbrich_worst_variance(eq, c, 0.0) == pytest.approx(eq @ c @ eq)
    robust = riemannian_wdro_weights(r, radius=0.05, window=60, step=30)
    assert np.abs(robust - 1 / 6).sum() < np.abs(w - 1 / 6).sum() + 1e-6


def test_entropic_risk_penalises_the_left_tail():
    x = np.random.default_rng(1).normal(0, 0.01, 1000)
    assert entropic_risk(x, 10.0) == pytest.approx(-x.mean() + 5.0 * x.var(), abs=1e-4)
    r = _block_returns()
    r[:, 5] -= 0.02 * (np.random.default_rng(2).random(len(r)) < 0.05)  # crash-prone asset
    assert entropic_weights(r, 20.0)[5] < 1 / 6
    assert riemannian_entropic_weights(r, 20.0, 60, 30).sum() == pytest.approx(1.0)
