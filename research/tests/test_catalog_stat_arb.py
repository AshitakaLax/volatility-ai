"""research/catalog/stat_arb.py -- arbitrage rules on synthetic markets."""

from __future__ import annotations

import numpy as np
import pytest

from engine.core.exceptions import ConfigurationError
from research.catalog.stat_arb import (
    AutoencoderFactors,
    NeuralFCVECM,
    band_positions,
    capital_structure_signal,
    causal_pairs,
    cef_discount,
    cef_positions,
    cointegrated_triplets,
    convertible_price,
    copula_garch_positions,
    copula_positions,
    creditgrades_spread,
    creditgrades_survival,
    fcvecm_allocation,
    fit_pair_copula,
    gaussian_h,
    ggr_pairs,
    ggr_positions,
    gumbel_h,
    johansen_basket,
    lagged_causal_links,
    merger_arb_return,
    orient_v_structures,
    ou_s_score,
    pc_skeleton,
    s_score_positions,
    spread_pnl,
    wdro_threshold,
    zscore,
)


def _cointegrated(n=500, seed=0):
    rng = np.random.default_rng(seed)
    common = 100 + np.cumsum(rng.normal(size=n))
    noise = np.zeros(n)
    for t in range(n - 1):
        noise[t + 1] = 0.8 * noise[t] + rng.normal()
    return np.column_stack(
        [common + noise, 0.5 * common + rng.normal(0, 0.5, n), 100 + np.cumsum(rng.normal(size=n))]
    )


def test_band_rule_and_pnl():
    z = np.array([0, 2.5, 1.0, 0.2, -2.5, -0.1, np.nan])
    assert band_positions(z).tolist() == [0, -1, -1, 0, 1, 0, 0]
    assert spread_pnl([1, 2, 4], [1, -1, 0]).tolist() == [0.0, 1.0, -2.0]
    assert np.isnan(zscore(np.arange(5.0), 3)[1]) and zscore(np.arange(5.0), 3)[-1] > 1


def test_johansen_basket_and_triplet_search():
    p = _cointegrated()
    b = johansen_basket(p[:, :2])
    assert b["cointegrated"] and b["weights"][1] == pytest.approx(-2.0, abs=0.2)
    rng = np.random.default_rng(1)
    walks = 100 + np.cumsum(rng.normal(size=(500, 2)), axis=0)
    tri = cointegrated_triplets(np.column_stack([p[:, :2], walks]))
    assert tri and set(tri[0][0]) >= {0, 1}


def test_distance_pairs():
    rng = np.random.default_rng(2)
    base = 100 + np.cumsum(rng.normal(size=300))
    p = np.column_stack(
        [
            base,
            base * 1.01 + rng.normal(0, 0.1, 300),
            100 + np.cumsum(rng.normal(size=300)),
            50 + np.cumsum(rng.normal(size=300)),
        ]
    )
    assert ggr_pairs(p, 1)[0][:2] == (0, 1)
    with pytest.raises(ConfigurationError):
        ggr_pairs(-p)
    fa, fb = np.full(10, 1.0) + 0.01 * np.arange(10), np.full(10, 1.0)
    ta = np.array([1.0, 1.2, 1.1, 0.99])
    tb = np.ones(4)
    assert ggr_positions(fa, fb, ta, tb).tolist() == [0, -1, -1, 0]


def test_copula_h_functions_and_pair_rules():
    u = np.linspace(0.01, 0.99, 50)
    assert gaussian_h(u, 0.5, 0.0) == pytest.approx(u, abs=1e-9)
    assert (np.diff(gumbel_h(u, 0.5, 2.0)) > 0).all()
    rng = np.random.default_rng(3)
    z = rng.multivariate_normal([0, 0], [[1, 0.8], [0.8, 1]], 600) * 0.01
    cop = fit_pair_copula(*(np.argsort(np.argsort(z, axis=0), axis=0).T + 1) / 601)
    assert cop["family"] in ("gaussian", "clayton")
    trade = np.array([[0.02, -0.02], [0.0, 0.0], [-0.02, 0.02], [0.0, 0.0]])
    pos = copula_positions(z[:, 0], z[:, 1], trade[:, 0], trade[:, 1])
    assert pos[0] == -1 and pos[2] in (0, 1)
    out = copula_garch_positions(z[:, 0], z[:, 1], window=200)
    assert out["theta"][-1] > 1.0 and set(out["positions"]) <= {-1, 0, 1}


def test_wdro_threshold_prefers_less_exposure_as_radius_grows():
    rng = np.random.default_rng(4)
    s = np.zeros(800)
    for t in range(799):
        s[t + 1] = 0.9 * s[t] + rng.normal()
    plain, robust = wdro_threshold(s), wdro_threshold(s, radius=5.0)
    assert robust["threshold"] >= plain["threshold"]
    assert set(plain["scores"]) == {0.5, 1.0, 1.5, 2.0, 2.5, 3.0}


def test_pc_algorithm_finds_a_collider_and_direct_links():
    rng = np.random.default_rng(5)
    x, y = rng.normal(size=2000), rng.normal(size=2000)
    zc = x + y + 0.5 * rng.normal(size=2000)
    w = zc + 0.5 * rng.normal(size=2000)
    sk = pc_skeleton(np.column_stack([x, y, zc, w]))
    adj = sk["adjacency"]
    assert adj[0, 2] and adj[1, 2] and adj[2, 3] and not adj[0, 1] and not adj[0, 3]
    assert {(0, 2), (1, 2)} <= orient_v_structures(sk)
    assert causal_pairs(np.column_stack([x, y, zc, w]), top=1)[0][:2] in ((2, 3), (0, 2), (1, 2))
    lead = rng.normal(size=1001)
    follow = np.r_[0.0, 0.8 * lead[:-1]] + 0.3 * rng.normal(size=1001)
    links = lagged_causal_links(np.column_stack([lead, follow, rng.normal(size=1001)]))
    assert links[0][:2] == (0, 1)


def test_autoencoder_residual_s_scores():
    rng = np.random.default_rng(6)
    f = rng.normal(size=(300, 1))
    r = 0.01 * (f @ np.ones((1, 5)) + 0.3 * rng.normal(size=(300, 5)))
    ae = AutoencoderFactors(5, latent=1, seed=0)
    hist = ae.fit(r, steps=300)
    assert hist[-1] < 0.5 * hist[0]
    assert np.var(ae.residuals(r)) < 0.5 * np.var(r)
    assert ae.s_scores(r, window=60).shape == r.shape
    ou = np.zeros(300)
    for t in range(299):
        ou[t + 1] = 0.8 * ou[t] + rng.normal()
    ou[-1] = 5.0
    assert ou_s_score(ou) > 2 and ou_s_score(np.arange(10.0)) == 0.0
    assert s_score_positions([-1.5, -0.3, 1.5, 0.5]).tolist() == [1, 0, -1, 0]


def test_neural_fcvecm_fits_and_allocates():
    p = np.log(_cointegrated(400)[:, :2])
    model = NeuralFCVECM(window=30, seed=0)
    hist = model.fit(p, steps=150)
    assert hist[-1] < hist[0] and model.forecast(p).shape == (2,)
    w = fcvecm_allocation(model, p)
    assert w.sum() == pytest.approx(1.0) or w.sum() == 0.0


def test_merger_convertible_credit_and_closed_end_funds():
    m = merger_arb_return(48.0, 50.0, 40.0, 0.9, 90)
    assert (
        m["implied_p"] == pytest.approx(0.8)
        and m["expected"] > 0
        and m["annualised"] > m["expected"]
    )
    cb = convertible_price(100.0, 1.0, 100.0, 0.02, 3.0, 0.03, 0.3, 0.02)
    assert cb["price"] >= max(100.0, cb["bond_floor"]) - 1e-6 and 0 < cb["delta"] < 1
    deep = convertible_price(200.0, 1.0, 100.0, 0.02, 3.0, 0.03, 0.3, 0.02)
    assert deep["delta"] > cb["delta"] and deep["price"] >= 200.0
    assert 0 < creditgrades_survival(20.0, 30.0, 0.4, 5.0) < 1
    hi, lo = creditgrades_spread(10.0, 30.0, 0.4), creditgrades_spread(40.0, 30.0, 0.4)
    assert hi > lo > 0
    assert capital_structure_signal(0.02, 0.01) == -1 and capital_structure_signal(0.004, 0.01) == 1
    nav = np.full(400, 10.0)
    price = 9.5 + 0.02 * np.random.default_rng(7).normal(size=400)
    price[300:310] = 8.5
    price[320:] = 9.5
    assert cef_discount([9.0], [10.0])[0] == pytest.approx(-0.1)
    pos = cef_positions(price, nav, window=250)
    assert pos[300] == 1 and pos[-1] == 0
