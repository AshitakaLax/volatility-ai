"""research/catalog/quantum.py -- QUBOs, annealing and statevector simulation."""

from __future__ import annotations

import numpy as np
import pytest

from engine.core.exceptions import ConfigurationError
from research.catalog.quantum import (
    QNNRegressor,
    adiabatic_evolution,
    amplitude_estimate,
    annealed_execution,
    apply_cnot,
    apply_gate,
    binary_matrix_factorization,
    bitstrings,
    brute_force,
    covariance_mask_qubo,
    evar,
    evar_selection,
    execution_qubo,
    gnn_adiabatic_portfolio,
    masked_covariance,
    mps_minimize,
    mps_portfolio,
    portfolio_qubo,
    qaoa,
    qsvm_predict,
    qsvr_predict,
    quantum_kernel,
    quantum_var,
    qubo_energy,
    rebalance_qubo,
    rx,
    sgc_scores,
    simulated_annealing,
)


def _problem(n=6, seed=0):
    rng = np.random.default_rng(seed)
    mu = rng.normal(0.05, 0.03, n)
    a = rng.normal(size=(n, n)) * 0.1
    return mu, a @ a.T + 0.01 * np.eye(n)


def test_portfolio_qubo_solvers_agree_with_brute_force():
    mu, cov = _problem()
    q, off = portfolio_qubo(mu, cov, k=3)
    x, e = brute_force(q, off)
    assert x.sum() == 3
    w = x / 3
    assert e == pytest.approx(w @ cov @ w - mu @ w)
    assert simulated_annealing(q, off, rng=0)[1] == pytest.approx(e)
    assert (
        qaoa(q, off, layers=2, rng=0)["expected_energy"] < qubo_energy(q, bitstrings(6), off).mean()
    )
    ad = adiabatic_evolution(q, off, total_time=40.0, steps=400)
    assert ad["energy"] == pytest.approx(e) and ad["ground_probability"] > 2 / 64
    feasible = bitstrings(6)[bitstrings(6).sum(1) == 3]
    tn = mps_minimize(q, off, bond_dim=2, rng=0)
    assert tn["energy"] < qubo_energy(q, feasible, off).mean() and tn["x"].sum() == 3
    separable = np.diag([0.3, -0.5, 0.8, -0.2]) + 0.01 * np.ones((4, 4))
    assert mps_minimize(separable, rng=0)["energy"] == pytest.approx(brute_force(separable)[1])
    assert mps_portfolio(mu, cov, 3, rng=0)["x"].sum() == 3
    with pytest.raises(ConfigurationError):
        bitstrings(20)


def test_slow_adiabatic_evolution_ends_in_the_ground_state():
    q = np.diag([0.3, -0.5, 0.8, -0.2, 0.4]) + 0.1 * np.ones((5, 5))
    fast = adiabatic_evolution(q, total_time=1.0, steps=20)["ground_probability"]
    slow = adiabatic_evolution(q, total_time=200.0, steps=2000)
    assert slow["ground_probability"] > 0.9 > fast
    assert slow["energy"] == pytest.approx(brute_force(q)[1])


def test_gates_and_cnot_follow_the_convention():
    psi = np.zeros((1, 2, 2), complex)
    psi[0, 1, 0] = 1.0  # |10>: qubit 0 set
    assert np.abs(apply_cnot(psi, 0, 1))[0, 1, 1] == pytest.approx(1.0)
    assert np.abs(apply_cnot(psi, 1, 0))[0, 1, 0] == pytest.approx(1.0)
    flipped = apply_gate(psi, rx(np.pi), 1)
    assert np.abs(flipped)[0, 1, 1] == pytest.approx(1.0)


def test_rebalance_and_graph_qubos():
    mu, cov = _problem(3)
    q, off, decode = rebalance_qubo(np.full(3, 1 / 3), mu, cov, lots=3, cost=0.0)
    x, _ = brute_force(q, off)
    assert decode(x).sum() == pytest.approx(1.0, abs=0.15)
    adj = np.ones((6, 6)) - np.eye(6)
    assert sgc_scores(np.arange(6.0), adj, 3).std() < np.arange(6.0).std()
    mu6, cov6 = _problem(6)
    assert gnn_adiabatic_portfolio(mu6, cov6, adj, 2)["x"].sum() == 2


def test_amplitude_estimation_and_quantum_var():
    assert amplitude_estimate(0.3, shots=200, rng=0) == pytest.approx(0.3, abs=0.02)
    losses = np.linspace(-1, 1, 41)
    probs = np.exp(-(losses**2) / 0.1)
    probs /= probs.sum()
    var = quantum_var(losses, probs, 0.95, rng=0, shots=500)
    exact = losses[np.argmax(np.cumsum(probs) >= 0.95)]
    assert abs(var - exact) <= 0.1


def test_binary_factorization_and_evar():
    rng = np.random.default_rng(1)
    b_true = rng.integers(0, 2, (8, 2))
    f_true = rng.normal(size=(2, 30))
    b, f = binary_matrix_factorization(b_true @ f_true, 2, rng=0)
    assert np.abs(b @ f - b_true @ f_true).max() < 1e-6
    loss = rng.normal(size=5000)
    assert 1.6 < evar(loss, 0.05) < 2.6  # sqrt(2 log 20) for a standard normal
    r = rng.normal(0, 0.01, (300, 5))
    r[:, 4] *= 5  # a much riskier asset
    assert evar_selection(r, 2, rng=0)[4] == 0


def test_covariance_mask_keeps_true_correlations():
    rng = np.random.default_rng(2)
    z = rng.normal(size=(400, 4))
    z[:, 1] += z[:, 0]
    train, val = np.cov(z[:200].T), np.cov(z[200:].T)
    q, pairs = covariance_mask_qubo(train, val, np.ones((4, 4)) - np.eye(4), coupling=0.0)
    keep, _ = brute_force(q)
    assert keep[pairs.index((0, 1))] == 1
    cov = masked_covariance(train, pairs, keep)
    assert np.linalg.eigvalsh(cov).min() > 0


def test_annealed_execution_sells_everything():
    q, off, decode = execution_qubo(1000.0, 4, 0.5, 0.1, 0.0)
    out = annealed_execution(1000.0, 4, 0.5, 0.1, 0.01, rng=0)
    assert out["trades"].sum() == pytest.approx(1000.0, rel=0.08)
    assert len(out["almgren_chriss"]) == 4 and q.shape == (12, 12) and off > 0
    x, _ = brute_force(q, off)
    assert decode(x).sum() == pytest.approx(1000.0, rel=0.08)


def test_quantum_kernel_learners_and_qnn():
    rng = np.random.default_rng(3)
    x = rng.uniform(0, np.pi, (40, 2))
    k = quantum_kernel(x)
    assert np.diag(k) == pytest.approx(1.0) and np.linalg.eigvalsh(k).min() > -1e-9
    y = (np.sin(x[:, 0]) > 0.7).astype(int)
    fit = qsvm_predict(x[:30], y[:30], x[:30], c=10.0, bandwidth=0.5)
    assert (fit == y[:30]).mean() > 0.9
    assert qsvr_predict(x[:30], np.sin(x[:30, 0]), x[30:], bandwidth=0.5).shape == (10,)
    net = QNNRegressor(2, layers=2, seed=0)
    target = np.cos(x[:20, 0])
    w = rng.normal(size=20)
    g = net.gradient(x[:20], w)
    eps = 1e-6
    th = net.theta.copy()
    th[0, 1, 0] += eps
    num = (w @ net.circuit(x[:20], th) - w @ net.circuit(x[:20])) / eps
    assert g[0, 1, 0] == pytest.approx(num, abs=1e-4)
    hist = net.fit(x[:20], target, steps=40)
    assert hist[-1] < hist[0] and net.predict(x[:3]).shape == (3,)
