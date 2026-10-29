"""research/catalog/deep_rl.py -- the agents learn on toy problems."""

from __future__ import annotations

import numpy as np
import pytest

from engine.core.exceptions import ConfigurationError
from research.catalog.autodiff import MLP
from research.catalog.deep_rl import (
    DQN,
    MADDPG,
    EMVAgent,
    MADDPGAllocator,
    ReplayBuffer,
    copy_params,
    evolve_portfolio_agents,
    genetic_search,
    sharpe,
    softmax_weights,
    train_wdro_policy,
)


def test_buffer_and_soft_updates():
    buf = ReplayBuffer(capacity=3)
    for i in range(5):
        buf.add(i, i * 2)
    assert len(buf) == 3 and set(buf.sample(10)[0]) <= {2, 3, 4}
    rng = np.random.default_rng(0)
    a, b = MLP([2, 3, 1], rng), MLP([2, 3, 1], rng)
    copy_params(a.params, b.params, tau=0.5)
    copy_params(a.params, b.params)
    assert all(np.allclose(x.data, y.data) for x, y in zip(a.params, b.params, strict=True))


def test_dqn_learns_a_two_armed_bandit_with_state():
    agent = DQN(1, 2, hidden=16, gamma=0.0, lr=5e-3, seed=0)
    rng = np.random.default_rng(1)
    for _ in range(400):
        s = rng.choice([-1.0, 1.0], size=1)
        a = agent.act(s, epsilon=0.5)
        r = 1.0 if (a == 1) == (s[0] > 0) else 0.0
        agent.buffer.add(s, a, r, s, 1.0)
        agent.update(32)
    assert agent.act([1.0]) == 1 and agent.act([-1.0]) == 0
    assert np.isnan(DQN(1, 2).update(32))


def test_maddpg_critics_fit_a_cooperative_reward():
    agent = MADDPG([1, 1], [1, 1], hidden=16, gamma=0.0, seed=0)
    rng = np.random.default_rng(2)
    losses = []
    for _ in range(300):
        obs = [rng.normal(size=1), rng.normal(size=1)]
        acts = agent.act(obs, noise=0.5)
        r = -((acts[0][0] - 0.5) ** 2) - (acts[1][0] + 0.5) ** 2
        agent.buffer.add(
            np.concatenate(obs), np.concatenate(acts), np.array([r, r]), np.concatenate(obs), 1.0
        )
        losses += agent.update(32)
    assert np.mean(losses[-20:]) < np.mean(losses[:20])
    a = agent.act([np.zeros(1), np.zeros(1)])
    assert a[0][0] > a[1][0]  # each actor moved toward its own target
    assert MADDPG([1], [1]).update(8) == []


def test_genetic_search_and_evolved_agents():
    out = genetic_search(lambda x: -((x - 3.0) ** 2).sum(), 2, gens=40, rng=0)
    assert out["best"] == pytest.approx([3.0, 3.0], abs=0.15)
    assert out["history"][-1] >= out["history"][0]
    rng = np.random.default_rng(3)
    sig = rng.choice([-1.0, 1.0], size=300)
    f = np.column_stack([sig, np.ones(300)])
    r = np.column_stack([0.01 * sig, -0.01 * sig]) + 0.001 * rng.normal(size=(300, 2))
    agents = evolve_portfolio_agents(f, r, pop=20, gens=20, rng=0)
    w = softmax_weights(f, agents["theta"])
    assert sharpe((w * r).sum(1)) > 5.0


def test_wdro_policy_hedges_its_concentration():
    rng = np.random.default_rng(4)
    f = np.ones((200, 1))
    r = np.column_stack([0.002 + 0.01 * rng.normal(size=200), 0.001 + 0.01 * rng.normal(size=200)])
    plain = train_wdro_policy(f, r, radius=0.0, steps=200)
    robust = train_wdro_policy(f, r, radius=0.01, steps=200)
    wp, wr = softmax_weights(f, plain["theta"])[0], softmax_weights(f, robust["theta"])[0]
    assert wp[0] > wr[0] > 0.5 - 1e-6 and plain["history"][-1] > plain["history"][0]


def test_emv_agent_steers_terminal_wealth_toward_its_target():
    rng = np.random.default_rng(5)
    r = 0.002 + 0.01 * rng.normal(size=2000)
    agent = EMVAgent(target=1.2, horizon=50, seed=0)
    means = agent.train(r, episodes=600, batch=20)
    assert abs(means[-1] - 1.2) < abs(means[0] - 1.2) and agent.k > 0
    long_only = EMVAgent(1.1, 20, long_only=True, seed=1)
    assert long_only.episode(r[:20])["wealth"] > 0
    with pytest.raises(ConfigurationError):
        agent.train(r[:10])


def test_maddpg_allocator_outputs_valid_weights():
    rng = np.random.default_rng(6)
    r = 0.01 * rng.normal(size=(120, 3))
    alloc = MADDPGAllocator(3, lookback=4, seed=0)
    losses = alloc.train(r, epochs=1, batch=32)
    w = alloc.weights(r[-4:])
    assert losses and w.sum() == pytest.approx(1.0) and (w > 0).all()
