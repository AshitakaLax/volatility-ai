"""research/catalog/generative.py -- generators reproduce simple distributions."""

from __future__ import annotations

import numpy as np
import pytest

from engine.core.exceptions import ConfigurationError
from research.catalog.autodiff import Tensor
from research.catalog.generative import (
    DDPM,
    GMMN,
    ConditionalWGANGP,
    FactorDiffusion,
    FlowMatching,
    TimeGAN,
    decode_messages,
    decode_tabular,
    encode_tabular,
    expected_shortfall,
    mmd2,
    operator_flow_alpha,
    order_messages,
    ranks_to_scores,
    scenario_portfolio,
    scores_to_ranks,
    synthesize_rankings,
)


def _corr_data(n=1500, rho=0.8, seed=0):
    rng = np.random.default_rng(seed)
    return rng.multivariate_normal([0.01, -0.01], [[1, rho], [rho, 1]], n) * 0.02


def test_ddpm_and_flow_matching_learn_a_correlated_gaussian():
    data = _corr_data()
    for model in (DDPM(2, seed=0), FlowMatching(2, seed=0)):
        hist = model.fit(data, steps=400)
        assert np.mean(hist[-50:]) < np.mean(hist[:50])
        s = model.sample(1500, rng=1)
        assert np.corrcoef(s.T)[0, 1] > 0.5
        assert s.std(0) == pytest.approx(data.std(0), rel=0.35)
    with pytest.raises(ConfigurationError):
        DDPM(2, cond_dim=1).fit(data, steps=1)


def test_conditional_generation_follows_the_condition():
    rng = np.random.default_rng(1)
    cond = rng.choice([-1.0, 1.0], size=(1500, 1))
    x = cond * 1.0 + 0.2 * rng.normal(size=(1500, 1))
    model = DDPM(1, cond_dim=1, seed=0)
    model.fit(x, cond, steps=500)
    assert (
        model.sample(300, cond=[1.0], rng=0).mean()
        > model.sample(300, cond=[-1.0], rng=0).mean() + 1
    )


def test_scenarios_factors_rankings_tables_and_messages():
    data = _corr_data(800)
    fm = FlowMatching(2, seed=0)
    fm.fit(data, steps=200)
    out = scenario_portfolio(fm, 500, rng=0)
    assert out["weights"].sum() == pytest.approx(1.0)
    rng = np.random.default_rng(2)
    f = rng.normal(size=(600, 1))
    r = f @ np.ones((1, 6)) * 0.01 + 0.002 * rng.normal(size=(600, 6))
    fd = FactorDiffusion(1, seed=0)
    fd.fit(r, steps=200)
    sim = fd.sample(500, rng=0)
    assert sim.shape == (500, 6) and np.corrcoef(sim.T)[0, 1] > 0.7
    ranks = np.array([rng.permutation(5) + 1 for _ in range(10)])
    assert (scores_to_ranks(ranks_to_scores(ranks)) == ranks).all()
    rk = DDPM(5, seed=0)
    rk.fit(ranks_to_scores(ranks), steps=50)
    syn = synthesize_rankings(rk, 4, rng=0)
    assert (np.sort(syn, axis=1) == np.arange(1, 6)).all()
    tab = encode_tabular([1.5, 2.5], [0, 2], 3)
    assert tab.tolist() == [[1.5, 1, 0, 0], [2.5, 0, 0, 1]]
    num, cat = decode_tabular(tab, 1)
    assert num[:, 0].tolist() == [1.5, 2.5] and cat.tolist() == [0, 2]
    msg = order_messages([0.0, 0.5, 2.0], [100, 200, 50], [1, -1, 1], [0, 1, 2])
    back = decode_messages(msg)
    assert back["size"] == pytest.approx([100, 200, 50]) and back["side"].tolist() == [1, -1, 1]


def test_operator_flow_alpha_ranks_by_the_learned_conditional():
    rng = np.random.default_rng(3)
    h = rng.normal(size=(600, 16))
    nxt = 0.5 * h[:, -1] + 0.1 * rng.normal(size=600)
    now = np.zeros((3, 16))
    now[:, -1] = [-2.0, 0.0, 2.0]
    out = operator_flow_alpha(h, nxt, now, top=1, rng=0, steps=300)
    assert out["weights"][2] == 1.0


def test_gmmn_and_expected_shortfall():
    data = _corr_data(800)
    x = Tensor(np.zeros((5, 2)))
    assert float(mmd2(x, np.zeros((5, 2))).data) == pytest.approx(0.0, abs=1e-12)
    g = GMMN(2, seed=0)
    hist = g.fit(data, steps=300)
    assert hist[-1] < hist[0]
    s = g.sample(1024, rng=0)
    assert np.corrcoef(s.T)[0, 1] > 0.4
    assert expected_shortfall(np.arange(100.0), 0.9) == pytest.approx(94.5)


def test_conditional_wgan_and_timegan_train():
    rng = np.random.default_rng(4)
    level = np.cumsum(0.01 * rng.normal(size=300))
    curves = level[:, None] + np.array([0.0, 0.5, 1.0]) + 0.01 * rng.normal(size=(300, 3))
    gan = ConditionalWGANGP(3, seed=0)
    hist = gan.fit(curves, steps=60)
    assert len(hist["critic"]) == 60 and np.isfinite(hist["critic"]).all()
    nxt = gan.sample(curves[-1], 50, rng=0)
    assert nxt.shape == (50, 3) and np.abs(nxt.mean(0) - curves[-1]).max() < 1.0
    t = np.arange(12)
    seqs = np.stack([np.sin(t * 0.5 + p)[:, None] for p in rng.uniform(0, 6, 30)])
    tg = TimeGAN(1, seed=0)
    h = tg.fit(seqs, steps=30)
    assert h["autoencoder"][-1] < h["autoencoder"][0]
    assert tg.sample(4, 12, rng=0).shape == (4, 12, 1)
