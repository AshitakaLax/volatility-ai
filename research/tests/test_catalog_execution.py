"""research/catalog/execution.py -- schedules and learners on the AC simulator."""

from __future__ import annotations

import numpy as np
import pytest

from engine.core.exceptions import ConfigurationError
from research.catalog.execution import (
    AttentiveExecutionPolicy,
    DeepMarkovVolume,
    LiquidationEnv,
    NeuralOperatorExecution,
    bdf_volume_forecast,
    evolve_execution,
    iceberg_fills,
    mean_field_execution,
    mfg_venue_split,
    pov_schedule,
    run_schedule,
    stackelberg_execution,
    static_volume_profile,
    train_dqn_liquidation,
    train_maddpg_router,
    train_multi_agent_liquidation,
    twap_schedule,
    venue_cost,
    vwap_schedule,
    wdro_execution,
)


def _u_shape(bins=13):
    x = np.linspace(-1, 1, bins)
    return 1 + 2 * x**2


def test_schedules_and_iceberg():
    assert twap_schedule(100, 4).tolist() == [25.0] * 4
    with pytest.raises(ConfigurationError):
        twap_schedule(0, 4)
    v = vwap_schedule(100, _u_shape())
    assert v.sum() == pytest.approx(100) and v[0] > v[6]
    pov = pov_schedule(100, [200, 400, 600, 800], 0.1)
    assert pov.tolist() == [20.0, 40.0, 40.0, 0.0]
    ice = iceberg_fills(1000, 100, np.full(20, 1000.0), participation=0.05)
    assert ice["visible"].max() <= 100 and ice["fills"].sum() + ice["remaining"] == pytest.approx(
        1000
    )


def test_volume_forecasts():
    rng = np.random.default_rng(0)
    curve = _u_shape()
    vols = curve * rng.lognormal(0, 0.1, (40, 13))
    assert static_volume_profile(vols) == pytest.approx(curve / curve.sum(), abs=0.01)
    market = rng.lognormal(0, 0.1, (40, 1, 1)) * curve[None, :, None]
    turnover = market * rng.lognormal(0, 0.05, (40, 13, 5))
    out = bdf_volume_forecast(turnover, 0)
    assert out["forecast"].shape == (13,) and out["forecast"][0] > out["forecast"][6]
    assert out["update"](0.0, 10).shape == (2,)
    dmm = DeepMarkovVolume(seed=0)
    hist = dmm.fit(np.log(vols[:20]), steps=60)
    assert hist[-1] < hist[0] and dmm.forecast(np.log(vols[0, :5]), 13).shape == (8,)


def test_dqn_liquidation_matches_twap_and_expert_guidance_runs():
    out = train_dqn_liquidation(episodes=150, env_kw={"steps": 5})
    dump = run_schedule(LiquidationEnv(steps=5, rng=1), [1000, 0, 0, 0, 0])
    assert out["dqn_shortfall"] < dump and out["dqn_shortfall"] < 1.5 * out["twap_shortfall"]
    guided = train_dqn_liquidation(episodes=20, env_kw={"steps": 5}, expert_episodes=20)
    assert guided["dqn_shortfall"] < dump
    robust = train_dqn_liquidation(
        episodes=10, env_kw={"steps": 5}, models=[(0.5, 0.002), (0.8, 0.004)]
    )
    assert np.isfinite(robust["dqn_shortfall"])
    multi = train_multi_agent_liquidation(2, episodes=20, env_kw={"steps": 5})
    assert multi["schedules"].shape == (2, 5)


def test_mean_field_and_venue_equilibria():
    alone = mean_field_execution(alpha=0.0)
    crowd = mean_field_execution(alpha=0.5)
    with pytest.raises(ConfigurationError):
        mean_field_execution(alpha=0.5, damping=1.0)
    assert alone["inventory"][0] == 1.0 and abs(alone["inventory"][-1]) < 0.05
    assert crowd["rates"][0] > alone["rates"][0]  # the crowd's selling makes everyone sell sooner
    m = mfg_venue_split([0.0, 0.1], [1.0, 1.0], crowd=1.0)
    cost = np.array([0.0, 0.1]) + m
    assert m[0] > m[1] and abs(cost[0] - cost[1]) < 0.02


def test_stackelberg_robust_and_evolved_schedules():
    out = stackelberg_execution(1000, 10, 0.5, 0.01, 0.002, 0.005, 0.0)
    assert out["trades"].sum() == pytest.approx(1000) and (out["follower_phi"] >= 0).all()
    base = wdro_execution(1000, 10, 0.5, 0.01, 1e-4)
    vol = wdro_execution(1000, 10, 0.5, 0.01, 1e-4, radius_sigma=0.3)
    imp = wdro_execution(1000, 10, 0.5, 0.01, 1e-4, radius_eta=0.05)
    assert vol["trades"][0] > base["trades"][0] > imp["trades"][0]
    cost = venue_cost([0.01, 0.02], [0.001, 0.0001])
    ev = evolve_execution(100, 2, 2, cost, gens=30, rng=0)
    assert ev["allocation"].sum() == pytest.approx(100) and ev["allocation"][:, 1].sum() > 50


def test_learned_routers_and_operators():
    router = train_maddpg_router(2, episodes=200)
    split = router["split"]([2.0, 0.5])
    assert split.sum() == pytest.approx(1.0)
    op = NeuralOperatorExecution(periods=6, seed=0)
    hist = op.fit(steps=150, rng=0)
    assert hist[-1] < hist[0]
    flat = op.schedule(np.ones((1, 6))).data[0]
    assert flat.sum() == pytest.approx(1.0)
    rng = np.random.default_rng(1)
    paths = [rng.uniform(50, 150, (6, 5)) for _ in range(4)]
    pol = AttentiveExecutionPolicy(levels=5, steps=6, seed=0)
    hist = pol.fit(paths, epochs=15)
    assert hist[-1] < hist[0] and len(pol.act(paths[0])) == 6
