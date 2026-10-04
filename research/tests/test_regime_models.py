"""research/strategies/regime_models.py -- catalog C-R3."""

from __future__ import annotations

import itertools
import math
from itertools import pairwise

import numpy as np
import pytest

from engine.core.exceptions import ConfigurationError
from research.strategies.regime_models import GaussianHMM, GaussianMixture, causal_turbulence


def _planted(n=6000, seed=0, p_stay=0.98, sds=(0.005, 0.02)):
    rng = np.random.default_rng(seed)
    states = np.empty(n, dtype=int)
    states[0] = 0
    for t in range(1, n):
        states[t] = states[t - 1] if rng.random() < p_stay else 1 - states[t - 1]
    x = rng.normal(0.0, np.array(sds)[states])
    return x, states


def _hand_model():
    m = GaussianHMM(2)
    m.start = np.array([0.6, 0.4])
    m.trans = np.array([[0.9, 0.1], [0.2, 0.8]])
    m.mu = np.array([0.0, 0.0])
    m.var = np.array([1.0, 4.0])
    return m


def _density(x, mu, var):
    return math.exp(-0.5 * (math.log(2 * math.pi * var) + (x - mu) ** 2 / var))


def test_forward_filter_matches_brute_force_enumeration():
    m = _hand_model()
    x = np.array([0.3, -2.1, 1.7, 0.2])
    joint = {}
    for path in itertools.product(range(2), repeat=x.size):
        p = m.start[path[0]] * _density(x[0], m.mu[path[0]], m.var[path[0]])
        for t in range(1, x.size):
            p *= m.trans[path[t - 1], path[t]] * _density(x[t], m.mu[path[t]], m.var[path[t]])
        joint[path] = p
    assert m.log_likelihood(x) == pytest.approx(math.log(sum(joint.values())))
    # Filtered P(s_3 | x_0..x_3) and smoothed P(s_1 | all) by enumeration.
    total = sum(joint.values())
    filtered_last = [sum(p for path, p in joint.items() if path[-1] == k) / total for k in range(2)]
    assert m.filter(x)[-1] == pytest.approx(filtered_last)
    smoothed_1 = [sum(p for path, p in joint.items() if path[1] == k) / total for k in range(2)]
    assert m.smooth(x)[1] == pytest.approx(smoothed_1)


def test_filtered_probabilities_use_no_future_observation():
    x, _ = _planted(800, seed=1)
    m = GaussianHMM(2).fit(x[:500])
    full = m.filter(x)
    for t in (50, 300, 799):
        assert m.filter(x[: t + 1])[-1] == pytest.approx(full[t])


def test_em_never_decreases_the_likelihood():
    x, _ = _planted(2000, seed=2)
    hist = GaussianHMM(2, n_iter=50, tol=0.0).fit(x).loglik_history
    assert all(b >= a - 1e-6 for a, b in pairwise(hist))


def test_fit_recovers_planted_calm_and_turbulent_states():
    x, states = _planted(8000, seed=3)
    m = GaussianHMM(2).fit(x)
    assert math.sqrt(m.var[0]) == pytest.approx(0.005, rel=0.1)
    assert math.sqrt(m.var[1]) == pytest.approx(0.02, rel=0.1)
    assert np.diag(m.trans) == pytest.approx([0.98, 0.98], abs=0.02)
    assert (m.viterbi(x) == states).mean() > 0.9


def test_state_zero_is_always_the_calm_one():
    x, _ = _planted(3000, seed=4)
    for seed in range(3):
        m = GaussianHMM(2, seed=seed).fit(x)
        assert m.var[0] < m.var[1]


def test_causal_turbulence_rises_in_the_turbulent_regime():
    x, states = _planted(6000, seed=5)
    p = causal_turbulence(x, train_end=3000)
    oos = np.arange(x.size) >= 3000  # after the training window
    assert p[oos & (states == 1)].mean() > 0.7
    assert p[oos & (states == 0)].mean() < 0.3


def test_gaussian_mixture_recovers_the_components():
    rng = np.random.default_rng(6)
    x = np.concatenate([rng.normal(0, 0.01, 7000), rng.normal(0, 0.04, 3000)])
    g = GaussianMixture(2).fit(x)
    assert g.weights == pytest.approx([0.7, 0.3], abs=0.05)
    assert np.sqrt(g.var) == pytest.approx([0.01, 0.04], rel=0.1)
    proba = g.predict_proba(x[:10])
    assert proba.sum(axis=1) == pytest.approx(np.ones(10))


@pytest.mark.parametrize(
    "call",
    [
        lambda: GaussianHMM(1),
        lambda: GaussianHMM(2).filter([0.1, 0.2]),
        lambda: GaussianHMM(3).fit(np.zeros(5)),
        lambda: GaussianMixture(1),
        lambda: causal_turbulence(np.zeros(100), train_end=0),
    ],
)
def test_bad_inputs_are_rejected(call):
    with pytest.raises(ConfigurationError):
        call()
