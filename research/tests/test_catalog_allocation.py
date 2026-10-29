"""research/catalog/allocation.py -- portfolio construction on synthetic data."""

from __future__ import annotations

import numpy as np
import pytest

from research.catalog.allocation import (
    ard_factor_loadings,
    black_litterman,
    black_litterman_weights,
    cp_als,
    cp_reconstruct,
    cvar_contributions,
    cvar_risk_parity,
    cvar_weights,
    diversification_ratio,
    downside_risk_parity,
    drifted_weights,
    dynamic_ard_loadings,
    entropy,
    entropy_production_rate,
    erc_weights,
    fractional_var_allocation,
    max_diversification_weights,
    maxent_weights,
    mep_rebalance,
    min_variance_weights,
    portfolio_cvar,
    risk_contributions,
    semicovariance,
    tensor_factor_rotation,
    topk_dropout,
    vine_cvar_weights,
    wdro_mean_variance,
)


def _returns(t=500, seed=0):
    rng = np.random.default_rng(seed)
    vols = np.array([0.01, 0.02, 0.03])
    corr = np.array([[1, 0.3, 0.2], [0.3, 1, 0.5], [0.2, 0.5, 1]])
    cov = corr * np.outer(vols, vols)
    return rng.multivariate_normal([0.0005, 0.0007, 0.001], cov, t), cov


def test_cvar_lp_matches_its_definition_and_robustness_spreads_the_book():
    r, _ = _returns()
    w = cvar_weights(r, 0.95)
    assert w.sum() == pytest.approx(1.0) and (w >= -1e-9).all()
    for other in (np.full(3, 1 / 3), np.array([0.0, 0.5, 0.5])):
        assert portfolio_cvar(r, w) <= portfolio_cvar(r, other) + 1e-9
    robust = cvar_weights(r, 0.95, radius=0.05)
    assert robust.max() < w.max()  # the ||w||_inf penalty diversifies
    goal = r.mean(0).max() * 0.9
    assert cvar_weights(r, 0.95, target_return=goal) @ r.mean(0) >= goal - 1e-9
    assert cvar_contributions(r, w).sum() == pytest.approx(portfolio_cvar(r, w), rel=0.05)


def test_black_litterman_moves_toward_the_view():
    _, cov = _returns()
    mkt = np.array([0.5, 0.3, 0.2])
    post = black_litterman(cov, mkt, [[1, -1, 0]], [0.02])
    assert post["mu"][0] - post["mu"][1] > post["prior"][0] - post["prior"][1]
    w = black_litterman_weights(cov, mkt, [[1, -1, 0]], [0.02])
    assert w.sum() == pytest.approx(1.0) and w[0] > 0


def test_diversification_and_risk_parity_properties():
    r, cov = _returns()
    w = max_diversification_weights(cov)
    for other in (np.full(3, 1 / 3), min_variance_weights(cov)):
        assert diversification_ratio(w, cov) >= diversification_ratio(other, cov) - 1e-6
    erc = erc_weights(cov)
    assert risk_contributions(erc, cov) == pytest.approx(np.full(3, 1 / 3), abs=1e-4)
    semi = semicovariance(r)
    assert np.all(np.diag(semi) < np.diag(np.cov(r.T)))
    assert downside_risk_parity(r).sum() == pytest.approx(1.0)
    cc = cvar_contributions(r, cvar_risk_parity(r))
    assert cc.max() / cc.min() < 1.1


def test_wasserstein_mean_variance_shrinks_toward_equal_weight():
    r, _ = _returns()
    plain = wdro_mean_variance(r, 0.0)
    robust = wdro_mean_variance(r, 1e-3)
    assert np.abs(robust - 1 / 3).sum() < np.abs(plain - 1 / 3).sum()
    goal = r.mean(0).max() * 0.5
    constrained = wdro_mean_variance(r, 1e-8, target_return=goal)
    assert constrained @ r.mean(0) >= goal - 1e-6


def test_cp_decomposition_and_sector_rotation():
    rng = np.random.default_rng(1)
    a, b, c = rng.normal(size=(20, 2)), rng.normal(size=(5, 2)), rng.normal(size=(3, 2))
    x = cp_reconstruct(a, b, c)
    fa, fb, fc = cp_als(x, 2, rng=0)
    assert np.abs(cp_reconstruct(fa, fb, fc) - x).max() < 1e-6
    t = np.arange(30)
    trend = np.column_stack([np.ones(30), 0.9**t])
    sector = np.array([[1.0, 0.0], [0.5, 0.0], [0.0, 1.0], [-1.0, 0.0]])
    w = tensor_factor_rotation(
        cp_reconstruct(trend, sector, np.array([[1.0, 1.0], [0.2, 0.1]])), rank=2, top=1, rng=0
    )
    assert w[0] == 1.0


def test_topk_dropout_limits_turnover():
    scores = np.array([0.9, 0.1, 0.8, 0.7, 0.2, 0.95])
    new, sell, buy = topk_dropout(scores, {0, 1, 4}, k=3, n_drop=1)
    assert sell == {1} and buy == {5} and new == {0, 4, 5}
    new, sell, buy = topk_dropout(scores, set(), k=2, n_drop=1)
    assert new == {5, 0} and not sell


def test_ard_prunes_irrelevant_factors_dynamically():
    rng = np.random.default_rng(2)
    f = rng.normal(size=(400, 4))
    r = np.column_stack(
        [1.5 * f[:, 0] + 0.1 * rng.normal(size=400), -f[:, 2] + 0.1 * rng.normal(size=400)]
    )
    load = ard_factor_loadings(r, f, prune=0.05)
    assert load[0, 0] == pytest.approx(1.5, abs=0.05) and load[0, [1, 2, 3]].tolist() == [0, 0, 0]
    assert load[1, 2] == pytest.approx(-1.0, abs=0.05)
    assert len(dynamic_ard_loadings(r, f, window=200, step=100)) == 3


def test_maximum_entropy_allocation_and_its_drift_rebalancing():
    mu = np.array([0.01, 0.02, 0.05])
    assert maxent_weights(mu) == pytest.approx(np.full(3, 1 / 3), abs=1e-5)
    w = maxent_weights(mu, target_return=0.035)
    assert w @ mu >= 0.035 - 1e-6 and entropy(w) < entropy(np.full(3, 1 / 3))
    path = drifted_weights(np.full(3, 1 / 3), np.tile([0.0, 0.0, 0.05], (10, 1)))
    assert (entropy_production_rate(path) < 0).all()
    out = mep_rebalance(np.tile([0.0, 0.0, 0.05], (20, 1)), mu, threshold=0.05)
    assert out["rebalanced"].any() and not out["rebalanced"].all()


def test_vine_cvar_and_fractional_var_allocation():
    r, _ = _returns(300)
    w = vine_cvar_weights(r, n_sim=2000, rng=0)
    assert w.sum() == pytest.approx(1.0) and w[0] > w[2]  # the low-vol asset carries the book
    rng = np.random.default_rng(3)
    up = np.cumsum(0.01 + 0.01 * rng.normal(size=300))
    down = np.cumsum(-0.01 + 0.01 * rng.normal(size=300))
    out = fractional_var_allocation(np.column_stack([up, down]), window=30)
    assert out["weights"][0] == pytest.approx(1.0) and out["d"].shape == (2,)
