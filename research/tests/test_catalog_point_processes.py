"""research/catalog/point_processes.py -- Hawkes models and their uses."""

from __future__ import annotations

import numpy as np
import pytest

from engine.core.exceptions import ConfigurationError
from research.catalog.point_processes import (
    NeuralHawkes,
    concat_types,
    delay_hawkes_intensity,
    detect_jumps,
    expected_count,
    fit_hawkes,
    fit_jump_excitation,
    fit_multivariate_hawkes,
    halt_quoting,
    hawkes_execution_schedule,
    hawkes_intensity,
    hawkes_inventory_quotes,
    hawkes_loglik,
    hawkes_timed_slices,
    hedge_budget_allocation,
    hedge_rebalance_times,
    multivariate_intensity,
    mutually_exciting_jump_intensity,
    neural_hawkes_alert,
    neural_jump_sde_path,
    order_flow_forecast,
    path_signature_features,
    robust_hawkes_schedule,
    signature_hawkes_forecast,
    simulate_hawkes,
    simulate_multivariate_hawkes,
    toxic_flow_execution,
    toxicity_score,
)


def test_simulation_matches_the_stationary_rate_and_mle_recovers_parameters():
    rng = np.random.default_rng(0)
    t = simulate_hawkes(0.5, 0.8, 1.6, 4000.0, rng)
    assert len(t) / 4000.0 == pytest.approx(0.5 / (1 - 0.5), rel=0.1)
    est = fit_hawkes(t, 4000.0)
    assert est["branching"] == pytest.approx(0.5, abs=0.08)
    assert est["mu"] == pytest.approx(0.5, rel=0.25)
    assert hawkes_loglik(t, 4000.0, 0.5, 0.8, 1.6) > hawkes_loglik(t, 4000.0, 1.0, 0.0, 1.6)
    with pytest.raises(ConfigurationError):
        simulate_hawkes(1.0, 2.0, 1.0, 10.0, rng)


def test_intensity_jumps_and_decays_and_expected_count_is_consistent():
    lam = hawkes_intensity([1.0], [0.5, 1.0001, 3.0], 0.2, 1.0, 2.0)
    assert lam[0] == pytest.approx(0.2) and lam[1] == pytest.approx(1.2, abs=1e-3)
    assert lam[2] == pytest.approx(0.2 + np.exp(-4.0))
    stat = 0.2 * 2.0 / (2.0 - 1.0)
    assert expected_count(0.2, 1.0, 2.0, stat, 5.0) == pytest.approx(stat * 5.0)
    assert expected_count(0.2, 1.0, 2.0, stat + 1, 5.0) > stat * 5.0


def test_multivariate_simulation_and_fit_capture_cross_excitation():
    rng = np.random.default_rng(1)
    alpha = np.array([[0.2, 0.6], [0.0, 0.2]])
    ev = simulate_multivariate_hawkes([0.3, 0.3], alpha, 1.5, 1500.0, rng)
    est = fit_multivariate_hawkes(ev, 1500.0, 1.5)
    assert est["alpha"][0, 1] > est["alpha"][1, 0]
    lam = multivariate_intensity(ev, est["mu"], est["alpha"], 1.5, 100.0)
    assert lam.shape == (2,) and (lam > 0).all()
    with pytest.raises(ConfigurationError):
        simulate_multivariate_hawkes([0.1, 0.1], np.eye(2) * 3, 1.0, 10.0, rng)


def test_order_flow_forecast_and_toxicity_filter():
    rng = np.random.default_rng(2)
    buys, sells = simulate_multivariate_hawkes([0.6, 0.2], [[0.3, 0], [0, 0.3]], 1.0, 400.0, rng)
    f = order_flow_forecast(buys, sells, 400.0, 10.0)
    assert f["buy"] > f["sell"] and f["imbalance"] > 0
    burst = np.r_[np.linspace(90, 99.9, 40)]
    s = toxicity_score(burst, 100.0, 20.0, 0.2, 0.5, 1.0)
    assert s > 1.0 and halt_quoting(s) and not halt_quoting(0.2)


def test_jump_detection_and_mutual_excitation():
    rng = np.random.default_rng(3)
    r = rng.normal(0, 0.01, size=(400, 2))
    r[200, 0] = -0.12
    r[202, 1] = -0.10
    flags = np.column_stack([detect_jumps(r[:, i]) for i in range(2)])
    assert flags[200, 0] and flags[202, 1] and flags.sum() < 10
    lam = mutually_exciting_jump_intensity(flags, [0.01, 0.01], [[0.2, 0.0], [0.5, 0.2]], 0.3)
    assert lam[201, 1] > lam[199, 1]  # market 0's jump excites market 1
    est = fit_jump_excitation(flags, beta=0.3)
    assert est["alpha"].shape == (2, 2)


def test_neural_hawkes_learns_and_its_variants_run():
    rng = np.random.default_rng(4)
    t = simulate_hawkes(0.5, 0.5, 1.0, 60.0, rng)
    times, types = concat_types(t[::2], t[1::2])
    for attention in (False, True):
        m = NeuralHawkes(2, hidden=4, attention=attention, seed=0)
        hist = m.fit(times, types, 60.0, steps=25, lr=0.05)
        assert hist[-1] < hist[0]
    lam = m.intensity(times, types, 30.0).data
    assert neural_hawkes_alert(m, times, types, 30.0, lam / 3)
    assert neural_jump_sde_path(m, times, types, [10.0, 20.0]).shape == (2, 2)


def test_signatures_and_signature_regression():
    sig = path_signature_features(np.array([[0.0, 0.0], [1.0, 0.0], [1.0, 1.0]]))
    assert sig[:2] == pytest.approx([1.0, 1.0])
    assert sig[2 + 1] - sig[2 + 2] == pytest.approx(1.0)  # Levy area of the L-shaped path
    rng = np.random.default_rng(5)
    paths = [np.cumsum(rng.normal(size=(10, 2)), 0) for _ in range(40)]
    counts = [p[-1, 0] - p[0, 0] for p in paths]
    coef = signature_hawkes_forecast(paths, counts)
    assert coef[1] == pytest.approx(1.0, abs=1e-6)


def test_execution_hedging_and_quoting_rules():
    base = hawkes_execution_schedule(1000, 10, 0.02, 0.1, 1.0, 0.0, 0.5, 2.0)
    adverse = hawkes_execution_schedule(1000, 10, 0.02, 0.1, 1.0, -1.0, 0.5, 2.0)
    assert base.sum() == pytest.approx(1000) and adverse[0] > base[0]
    rob = robust_hawkes_schedule(1000, 10, 0.02, 0.1, 1.0, -1.0, 0.5, 2.0, 0.5, 0.2)
    assert rob[0] > adverse[0]
    assert hawkes_timed_slices([1, 3], 100) == pytest.approx([25, 75])
    assert toxic_flow_execution([1, 1, 1], [0, 2, 0], 90, 1.0, pause=True) == pytest.approx(
        [45, 0, 45]
    )
    bid, ask = hawkes_inventory_quotes(100.0, 10.0, 5.0, 1.0, 0.05, 0.001)
    assert bid < ask and (bid + ask) / 2 < 100.05
    grid = np.arange(0, 10, 0.5)
    lam = np.ones_like(grid)
    lam[7] = 10.0
    assert 3.5 in hedge_rebalance_times(lam, grid, 2.0)
    assert hedge_budget_allocation([1, 3], 8) == pytest.approx([2, 6])
    assert delay_hawkes_intensity([1.0], [1.5], 0.1, 1.0, 1.0, 1.0)[0] == pytest.approx(0.1)
    with pytest.raises(ConfigurationError):
        hawkes_timed_slices([0, 0], 10)
