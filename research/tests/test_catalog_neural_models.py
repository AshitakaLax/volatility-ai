"""research/catalog/neural_models.py -- each forecaster learns a toy signal."""

from __future__ import annotations

import numpy as np
import pytest

from engine.core.exceptions import ConfigurationError
from research.catalog.autodiff import Tensor
from research.catalog.neural_models import (
    CDEClassifier,
    CDEIntensityExecution,
    CDEJumpPricer,
    DeepLOB,
    NeuralCDE,
    NeuralJumpODE,
    PSRNeuralODE,
    SpikingGCN,
    SpikingScalper,
    TCNForecaster,
    TemporalFusionTransformer,
    WaveletScalper,
    causal_haar,
    delta_spike_encode,
    lob_labels,
    log_signature_steps,
    quantile_loss,
    spike,
    windows,
)


def test_ops_and_windows():
    v = Tensor(np.array([-1.0, 0.5]), requires_grad=True)
    s = spike(v)
    s.sum().backward()
    assert s.data.tolist() == [0.0, 1.0] and (v.grad > 0).all()
    pred = Tensor(np.zeros((2, 1, 3)), requires_grad=True)
    loss = quantile_loss(pred, np.ones((2, 1, 1)), [0.1, 0.5, 0.9])
    assert float(loss.data) == pytest.approx(0.5)
    x, y = windows(np.arange(10.0), 3, 2)
    assert x[0].tolist() == [0, 1, 2] and y[0].tolist() == [3, 4] and len(x) == 6
    with pytest.raises(ConfigurationError):
        windows(np.arange(3.0), 3, 1)


def test_tcn_learns_a_sine():
    s = np.sin(np.arange(200) * 0.3)
    model = TCNForecaster(seed=0)
    hist = model.fit(s, steps=200)
    assert hist[-1] < 0.1 * hist[0]
    assert model.predict_next(s) == pytest.approx(np.sin(200 * 0.3), abs=0.2)


def test_tft_quantiles_and_interpretability():
    rng = np.random.default_rng(0)
    t = np.arange(300)
    signal = np.sin(t * 0.2)
    noise = rng.normal(size=300)
    x, y = windows(signal + 0.1 * rng.normal(size=300), 10, 2)
    feats = np.stack([x, windows(noise, 10, 2)[0]], axis=2)  # a useful and a useless input
    model = TemporalFusionTransformer(2, hidden=8, horizons=2, seed=0)
    hist = model.fit(feats[:150], y[:150], steps=120)
    assert hist[-1] < 0.5 * hist[0]
    out, att, vw = model.forward(feats[:5])
    assert out.shape == (5, 2, 3) and att.data.sum(1) == pytest.approx(1.0)
    assert vw.data[..., 0].mean() > vw.data[..., 1].mean()


def test_deeplob_learns_imbalance_driven_moves():
    rng = np.random.default_rng(1)
    n, w = 400, 8
    imb = rng.normal(size=n)
    mid = 100 + np.cumsum(0.01 * np.r_[0.0, imb[:-1]] + 0.001 * rng.normal(size=n))
    labels = lob_labels(mid, horizon=1, alpha=0.002)
    feats = np.column_stack([imb, rng.normal(size=n)])
    x = np.array([feats[t - w + 1 : t + 1] for t in range(w - 1, n - 1)])
    lab = labels[w - 1 : n - 1]
    model = DeepLOB(2, seed=0)
    model.fit(x[:300], lab[:300], steps=150)
    assert (model.predict(x[300:]) == lab[300:]).mean() > 0.6
    assert set(np.unique(lob_labels(mid))) <= {0, 1, 2}


def test_neural_cde_family():
    rng = np.random.default_rng(2)
    t = np.linspace(0, 1, 12)
    drift = rng.choice([-1.0, 1.0], size=80)
    paths = np.stack([np.column_stack([t, d * t + 0.05 * rng.normal(size=12)]) for d in drift])
    assert len(NeuralCDE(2).states(paths[:3])) == 12
    clf = CDEClassifier(2, seed=0)
    clf.fit(paths[:60], drift[:60] > 0, steps=120)
    assert ((clf.predict_proba(paths[60:]) > 0.5) == (drift[60:] > 0)).mean() > 0.8
    ls = log_signature_steps(paths[0], 4)
    assert ls.shape == (4, 3) and ls[-1, 1] == pytest.approx(
        paths[0][-1, 1] - paths[0][0, 1], abs=0.2
    )
    nxt = 0.01 * drift + 0.001 * rng.normal(size=80)
    pricer = CDEJumpPricer(2, seed=0)
    hist = pricer.fit(paths, nxt, steps=100)
    assert hist[-1] < hist[0] and np.corrcoef(pricer.expected_return(paths), nxt)[0, 1] > 0.5
    counts = np.stack([(rng.random(12) < (0.2 if d < 0 else 0.8)).astype(float) for d in drift])
    ex = CDEIntensityExecution(2, seed=0)
    hist = ex.fit(paths, counts, steps=100)
    assert hist[-1] < hist[0] and ex.trade_signal(paths[:2]).shape == (2, 12)


def test_neural_odes():
    s = np.sin(np.arange(150) * 0.25)
    node = PSRNeuralODE(dim=3, seed=0)
    hist = node.fit(s, steps=200)
    assert hist[-1] < 0.1 * hist[0]
    assert node.forecast(s, 1)[0] == pytest.approx(np.sin(150 * 0.25), abs=0.25)
    rng = np.random.default_rng(3)
    steps, dt = 30, 0.1
    vals = np.repeat(rng.normal(1.0, 0.1, (40, 1)), steps, axis=1)
    mask = rng.random((40, steps)) < 0.3
    mask[:, 0] = True
    njode = NeuralJumpODE(seed=0)
    hist = njode.fit(vals, mask, dt, steps=80)
    assert hist[-1] < hist[0]
    pred = njode.predict(vals[:2], mask[:2], dt)
    assert pred.shape == (2, steps) and abs(pred[0, -1] - vals[0, -1]) < 0.5


def test_spiking_models_and_wavelets():
    enc = delta_spike_encode([0.0, 0.5, 1.1, 0.0], 1.0)
    assert enc.tolist() == [[0, 0], [0, 0], [1, 0], [0, 1]]
    rng = np.random.default_rng(4)
    up = rng.random(120) < 0.5
    spikes = np.stack(
        [
            np.column_stack(
                [
                    (rng.random(10) < (0.8 if u else 0.1)),
                    rng.random(10) < 0.1,
                    rng.random(10) < 0.1,
                    rng.random(10) < 0.1,
                ]
            ).astype(float)
            for u in up
        ]
    )
    scalper = SpikingScalper(seed=0)
    hist = scalper.fit(spikes[:90], up[:90], steps=150)
    assert (
        hist[-1] < hist[0] and ((scalper.predict_proba(spikes[90:]) > 0.5) == up[90:]).mean() > 0.7
    )
    shocks = (rng.random((60, 6, 3)) < 0.2).astype(float)
    target = shocks[:, -1, [0, 0, 2]]  # node 1 follows node 0
    sgcn = SpikingGCN(seed=0)
    hist = sgcn.fit(shocks, np.array([[0, 1, 0], [0, 0, 0], [0, 0, 0]], float), target, steps=100)
    assert hist[-1] < hist[0]
    p = 100 * np.exp(np.cumsum(0.01 * rng.normal(size=200)))
    smooth, details = causal_haar(np.log(p), 3)
    p2 = p.copy()
    p2[150:] *= 2
    s2, d2 = causal_haar(np.log(p2), 3)
    assert np.allclose(s2[:150], smooth[:150]) and np.allclose(d2[2][:150], details[2][:150])
    ws = WaveletScalper(seed=0)
    ws.fit(p, steps=50)
    assert set(np.unique(ws.positions(p))) <= {0.0, 1.0}
