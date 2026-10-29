"""research/catalog/cross_section.py -- cross-sectional models on toy panels."""

from __future__ import annotations

import numpy as np
import pytest

from engine.core.exceptions import ConfigurationError
from research.catalog.autodiff import Tensor
from research.catalog.cross_section import (
    ContractiveAutoencoder,
    DomainAdversarialForecaster,
    FactorVAE,
    GCNRanker,
    HyperbolicGCN,
    QuantileNetwork,
    SupplyChainGAT,
    copula_quantile_rank,
    customer_momentum,
    diffusion_conv_alpha,
    expmap0,
    grad_reverse,
    logmap0,
    momentum_features,
    norm_adjacency,
    operator_boosting,
    rough_hurst,
    signature_feature_panel,
    signature_trading,
    spectral_features,
    top_k_weights,
)

CHAIN = np.array([[0, 1, 0, 0], [1, 0, 1, 0], [0, 1, 0, 1], [0, 0, 1, 0]], float)


def _panel(t=200, n=4, seed=0):
    rng = np.random.default_rng(seed)
    x = rng.normal(size=(t, n, 2))
    y = 0.5 * x[..., 0] + 0.1 * rng.normal(size=(t, n))  # feature 0 predicts next return
    return x, y


def test_helpers():
    assert top_k_weights([0.1, 0.5, 0.3], 2).tolist() == [0.0, 0.5, 0.5]
    a = norm_adjacency(CHAIN)
    assert a == pytest.approx(a.T) and np.linalg.eigvalsh(a).max() == pytest.approx(1.0)
    v = Tensor(np.array([[0.3, -0.2]]))
    assert logmap0(expmap0(v)).data == pytest.approx(v.data)
    assert np.linalg.norm(expmap0(Tensor(np.array([[50.0, 0.0]]))).data) < 1.0
    x = Tensor(np.ones(2), requires_grad=True)
    (grad_reverse(x, 0.5) * 2.0).sum().backward()
    assert x.grad.tolist() == [-1.0, -1.0]


def test_graph_rankers_learn_the_signal():
    x, y = _panel()
    for model in (GCNRanker(2, seed=0), HyperbolicGCN(2, seed=0)):
        hist = model.fit(x[:150], y[:150], CHAIN, steps=200)
        assert hist[-1] < 0.6 * hist[0]
        pred = model.scores(x[150:], CHAIN).data
        assert np.corrcoef(pred.ravel(), y[150:].ravel())[0, 1] > 0.5
    assert GCNRanker(2).select(x[0], CHAIN, 2).sum() == pytest.approx(1.0)


def test_diffusion_conv_and_supply_chain():
    rng = np.random.default_rng(1)
    r = rng.normal(size=(600, 3)) * 0.01
    for t in range(1, 600):
        r[t, 1] += 0.8 * r[t - 1, 0]  # 0 supplies 1
    links = np.array([[0, 1, 0], [0, 0, 0], [0, 0, 0]], float)
    out = diffusion_conv_alpha(r, links, k=1, top=1)
    assert max(abs(out["coef"][2]), abs(out["coef"][3])) > 0.3
    cm = customer_momentum(r[-1:], np.array([[0, 0, 0], [1, 0, 0], [0, 0, 0]], float))
    assert cm[0, 1] == pytest.approx(r[-1, 0])
    gat = SupplyChainGAT(seed=0)
    hist = gat.fit(r, links + links.T, steps=200)
    assert hist[-1] < hist[0] and gat.coef.data[2] > 0.2


def test_factor_vae_forecasts_the_cross_section():
    x, y = _panel(300, 6)
    model = FactorVAE(2, seed=0)
    hist = model.fit(x[:250], y[:250], steps=400)
    assert np.mean(hist[-50:]) < np.mean(hist[:50])
    preds = np.array([model.predict(x[t]) for t in range(250, 300)])
    assert np.corrcoef(preds.ravel(), y[250:].ravel())[0, 1] > 0.5


def test_domain_adversarial_features_hide_the_market():
    rng = np.random.default_rng(2)
    n = 400
    dom = rng.integers(0, 2, n)
    signal = rng.normal(size=n)
    x = np.column_stack([signal, dom + 0.5 * rng.normal(size=n)])  # feature 1 hints at the market
    y = 0.5 * signal + 0.05 * rng.normal(size=n)
    losses = {}
    for lam in (0.0, 1.0):
        model = DomainAdversarialForecaster(2, 2, lam=lam, seed=0)
        model.fit(x, y, dom, steps=400)
        assert np.corrcoef(model.predict(x), y)[0, 1] > 0.9
        losses[lam] = float(model.loss(x, y, dom, np.ones(n, bool))[1].data)
    assert losses[1.0] > losses[0.0] + 0.1  # reversal makes the market harder to tell apart
    assert 0.0 <= model.domain_accuracy(x, dom) <= 1.0
    prices = np.exp(np.cumsum(np.random.default_rng(3).normal(0, 0.01, (260, 3)), axis=0))
    assert momentum_features(prices).shape == (3, 3)
    with pytest.raises(ConfigurationError):
        momentum_features(prices[:100])


def test_contractive_autoencoder_flags_anomalies():
    rng = np.random.default_rng(4)
    f = rng.normal(size=(300, 1))
    r = f @ np.ones((1, 5)) + 0.1 * rng.normal(size=(300, 5))
    r[-1] = [3, -3, 3, -3, 3]  # breaks the common-factor structure
    cae = ContractiveAutoencoder(5, latent=1, lam=0.1, seed=0)
    cae.fit(r[:-1], steps=300)
    s = cae.anomaly_scores(r)
    assert s[-1] == s.max() and cae.jacobian_norm(r) >= 0
    plain = ContractiveAutoencoder(5, latent=1, lam=0.0, seed=0)
    plain.fit(r[:-1], steps=300)
    assert cae.jacobian_norm(r[:-1]) < plain.jacobian_norm(r[:-1])


def test_quantile_networks_and_copula_ranking():
    rng = np.random.default_rng(5)
    x = rng.normal(size=(500, 1))
    y = x[:, 0] + (0.5 + 0.5 * np.abs(x[:, 0])) * rng.normal(size=500)
    qn = QuantileNetwork(1, seed=0)
    qn.fit(x, y, steps=300)
    qs = qn.quantiles(x).data
    assert (np.diff(qs, axis=1) > 0).all()
    cover = (y < qs[:, 4]).mean()
    assert 0.85 < cover < 1.0
    models = [qn, QuantileNetwork(1, seed=1)]
    models[1].fit(x, -y, steps=100)
    out = copula_quantile_rank(models, [x, x], np.column_stack([y, -y]), [[2.0], [2.0]], rng=0)
    assert out["p_up"][0] > out["p_up"][1] and out["corr"][0, 1] < 0


def test_operator_boosting_and_signature_trading():
    rng = np.random.default_rng(6)
    h = rng.normal(size=(200, 16))
    target = h[:, -1] - h[:, -2]
    assert spectral_features(h, 4).shape == (200, 8)
    out = operator_boosting(h, target, stages=3, steps=100)
    resid = [np.mean((target - out["fitted"]) ** 2), np.var(target)]
    assert resid[0] < resid[1] and out["predict"](h[:3]).shape == (3,)
    lv = np.cumsum(rng.normal(size=2000)) * 0.1
    assert 0.3 < rough_hurst(lv) < 0.7  # Brownian log-vol: H = 0.5
    trend = np.exp(np.cumsum(0.001 + 0.01 * rng.normal(size=400)))
    panel = signature_feature_panel(trend, 20)
    assert np.isnan(panel[:20]).all() and np.isfinite(panel[20:]).all()
    st = signature_trading(trend, 20)
    assert st["in_sample_pnl"] > 0 and st["coef"].shape == (6,)
    assert signature_trading(trend, 20, delay=5)["positions"].shape == (400,)
