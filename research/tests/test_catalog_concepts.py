"""research/catalog/concepts.py -- the 34 concepts of ranks 426-700."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

from engine.core.exceptions import ConfigurationError
from research.catalog import concepts as c

ROOT = Path(__file__).resolve().parents[2]


def _trend(n=600, drift=0.001, seed=0):
    rng = np.random.default_rng(seed)
    return 100 * np.exp(np.cumsum(drift + 0.01 * rng.normal(size=n)))


def _factor_panel(t=400, seed=0):
    rng = np.random.default_rng(seed)
    f = rng.normal(0, 0.01, (t, 2)) * np.array([1.0, 2.0])
    b = np.array([[1.0, 0.0], [0.8, 0.2], [0.0, 1.0], [0.2, 0.9], [0.5, 0.5]])
    r = f @ b.T + 0.003 * rng.normal(size=(t, 5))
    return r, f, b


def test_every_researched_concept_page_has_functions():
    pages = {p.stem for p in (ROOT / "docs/algorithms/concepts").glob("*.md")}
    for slug, names in c.CONCEPTS.items():
        assert slug in pages
        assert all(callable(getattr(c, n)) for n in names)
    assert len(c.CONCEPTS) == 34


def test_trend_filters():
    up = 100 * np.exp(np.linspace(0, 0.6, 600) + 0.002 * np.random.default_rng(0).normal(size=600))
    k = c.kalman_trend(up)
    assert k["slope"][-1] > 0 and k["positions"][-1] == 1
    y = np.r_[np.linspace(0, 1, 50), np.linspace(1, 0, 50)]
    x = c.l1_trend_filter(y + 0.01 * np.random.default_rng(1).normal(size=100), lam=1.0)
    assert np.argmax(x) in range(45, 56)
    assert c.l1_trend_positions(up[:200], window=120).max() == 1
    ka = c.kama(up)
    assert np.isnan(ka[5]) and abs(ka[-1] / up[-1] - 1) < 0.1
    cb = c.cycle_blended_momentum(up)
    assert set(cb["alphas"]) == {"correction", "rebound"} and (cb["positions"] >= 0).all()


def test_state_conformal_spectral_bayes_robust():
    rng = np.random.default_rng(2)
    r = np.r_[0.002 + 0.005 * rng.normal(size=300), -0.003 + 0.02 * rng.normal(size=300)]
    h = c.hmm_trend(r)
    assert h["positions"][250] == 1 and h["positions"][-1] == 0
    pred = 0.01 + 0.001 * rng.normal(size=400)
    out = c.adaptive_conformal_positions(pred, pred + 0.002 * rng.normal(size=400))
    assert out["positions"][-1] > 0 and 0.8 < out["coverage"] <= 1.0
    up = _trend()
    assert c.spectral_trend_positions(up[:300])[-1] in (0.0, 1.0)
    bd = c.bayesian_drift(np.full(200, 0.01) + 0.001 * rng.normal(size=200))
    assert bd["p_positive"][-1] > 0.9 and bd["positions"][-1] == 1
    noisy = up.copy()
    noisy[-5] *= 0.5  # one outlier
    assert c.robust_momentum(noisy)[-1] == 1
    with pytest.raises(ConfigurationError):
        c.robust_momentum(up, method="mean")


def test_copula_nonlinear_fractional_diffusion_topology():
    rng = np.random.default_rng(3)
    m = 100 * np.exp(np.cumsum(-0.002 + 0.01 * rng.normal(size=620)))  # a bear market
    a = m * np.exp(0.002 * rng.normal(size=620)) * np.exp(np.linspace(0, 0.5, 620))
    out = c.copula_momentum_positions(a, m)
    assert out["tail_dependence"].max() > 0.3 and (out["positions"] <= 1).all()
    kt = c.kernel_trend_forecast(_trend(800, 0.002))
    assert len(kt["forecast"]) == len(kt["actual"])
    lm = np.convolve(rng.normal(size=3000), np.r_[1.0, -np.cumprod(np.full(200, 0.0)) + 0.0][:1])
    ar = c.arfima_forecast(lm)
    assert -0.45 <= ar["d"] <= 0.45 and np.isfinite(ar["forecast"][-1])
    up = np.diff(np.log(_trend(400, 0.003)))
    dt = c.diffusion_trend(up, steps=100, n_samples=50)
    assert dt["positions"].shape == dt["actual"].shape
    panel = 0.01 * rng.normal(size=(200, 3))
    tf = c.topology_filtered_trend(_trend(200), panel, lookback=50, window=20)
    assert set(np.unique(tf["positions"])) <= {0.0, 1.0}


def test_factor_risk_parity_family():
    r, f, b = _factor_panel()
    cf = np.cov(f.T)
    w = c.factor_risk_parity(b, cf)
    rc = c.factor_risk_contributions(w, b, cf)[:2]
    assert rc[0] == pytest.approx(rc[1], rel=0.05) and w.sum() == pytest.approx(1.0)
    budgeted = c.factor_risk_parity(b, cf, budgets=[0.8, 0.2])
    rcb = c.factor_risk_contributions(budgeted, b, cf)[:2]
    assert rcb[0] / rcb.sum() == pytest.approx(0.8, abs=0.05)
    for wt in (
        c.robust_factor_risk_parity(r, f),
        c.geodesic_factor_risk_parity(r, f),
        c.karcher_factor_risk_parity(r, f),
        c.signature_factor_risk_parity(r, f),
        c.kernel_factor_risk_parity(r, f, f, f[-1], 0.02),
        c.koopman_factor_risk_parity(r, f),
        c.kernel_pca_factor_risk_parity(r),
        c.variational_factor_risk_parity(r, steps=100),
        c.evolutionary_factor_risk_parity(b, cf, gens=15, rng=0),
        c.copula_factor_risk_parity(r, f, n_sim=1000, rng=0)["weights"],
        c.attention_factor_risk_parity(r, f, gens=3, rng=0)["weights"],
    ):
        assert wt.sum() == pytest.approx(1.0, abs=1e-6) and (wt > -1e-8).all()
    sig = c.lead_lag_signature_covariance(f)
    assert sig == pytest.approx((f.T @ f), rel=1e-6)


def test_covariance_estimators():
    r, _, _ = _factor_panel(300)
    for cov in (
        c.dcc_garch_covariance(r[:, :3]),
        c.robust_covariance(r),
        c.robust_covariance(r, "tyler"),
        c.attention_covariance(r, steps=20),
        c.geodesic_covariance(r),
        c.koopman_covariance(r),
    ):
        assert np.allclose(cov, cov.T) and np.linalg.eigvalsh(cov).min() > 0
    with pytest.raises(ConfigurationError):
        c.robust_covariance(r, "bad")
    race = c.covariance_horse_race(r, 200, {"sample": lambda x: np.cov(x.T)})
    assert set(race) == {"sample", "ledoit_wolf"}


def test_tail_risk_tools():
    rng = np.random.default_rng(4)
    r = 0.01 * rng.standard_t(3, size=3000)
    pot = c.pot_var_es(r, 0.99)
    assert pot["es"] > pot["var"] > np.quantile(-r, 0.95)
    exp = c.tail_budget_exposure(r[:530], es_budget=0.02, window=500)
    assert (exp <= 1).all() and exp[-1] < 1
    cv = c.caviar(r[:1000], 0.05)
    assert 0.02 < cv["hit_rate"] < 0.08
    assert c.var_exposure([0.01, 0.04], 0.02).tolist() == [1.0, 0.5]
    wt = c.wavelet_tail_risk(r[:600])
    assert np.isfinite(wt["var"][-1]) and 0 < wt["fine_share"][-1] < 1
    x = np.zeros(600)
    for t in range(599):
        phi = 0.2 + 0.75 * t / 600  # slowing down: autocorrelation rises
        x[t + 1] = phi * x[t] + rng.normal()
    ews = c.critical_slowing_down(x, window=100, trend_window=200)
    assert ews["tau_ar1"][-1] > 0.3
    assert set(np.unique(c.early_warning_exposure(x, window=100, trend_window=200))) <= {0.0, 1.0}


def test_sector_and_regime_allocation():
    rng = np.random.default_rng(5)
    p = np.exp(
        np.cumsum(rng.normal(0, 0.01, (300, 5)) + np.array([0.002, 0, 0, 0, -0.002]), axis=0)
    )
    w = c.sector_momentum(p, top=2)
    assert w[0] == 0.5 and w.sum() == pytest.approx(1.0)
    assert c.sector_momentum(p, top=1, risk_adjusted=True).sum() == pytest.approx(1.0)
    with pytest.raises(ConfigurationError):
        c.sector_momentum(p[:50])
    r = np.r_[0.001 + 0.005 * rng.normal(size=300), 0.03 * rng.normal(size=100)]
    out = c.regime_allocation(r)
    assert out["p_risk_off"][-1] > 0.5 > out["p_risk_off"][200]
    assert out["weights"].sum(1) == pytest.approx(1.0)
