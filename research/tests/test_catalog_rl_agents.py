"""research/catalog/rl_agents.py -- MLP/Adam, tabular Q, the huseinzol05
agents, evolution strategies, FinRL's environment and ensemble, and the
policy-gradient update rules."""

from __future__ import annotations

import numpy as np
import pytest

from engine.core.exceptions import ConfigurationError
from research.catalog.rl_agents import (
    MLP,
    Adam,
    DeepEvolutionStrategy,
    FinRLStockTradingEnv,
    HuseinQAgent,
    LinearA2C,
    QTable,
    ddpg_target,
    es_agent_reward,
    es_model_weights,
    finrl_ensemble_pick,
    finrl_ensemble_windows,
    finrl_turbulence_threshold,
    finrl_validation_sharpe,
    gae,
    ppo_clip_loss,
    sac_target,
    sign_pattern_state,
    soft_update,
    td3_smoothed_action,
    td3_target,
    window_state,
)


def test_mlp_backward_matches_finite_differences():
    rng = np.random.default_rng(0)
    net = MLP(4, 6, 3, rng)
    x, y = rng.normal(size=(5, 4)), rng.normal(size=(5, 3))

    def loss():
        return 0.5 * ((net.predict(x) - y) ** 2).sum()

    out, cache = net.forward(x)
    grads = net.backward(cache, out - y)
    for k in ("w1", "b1", "w2", "b2"):
        p, num = net.params[k], np.zeros_like(net.params[k])
        for idx in np.ndindex(p.shape):
            old = p[idx]
            p[idx] = old + 1e-6
            up = loss()
            p[idx] = old - 1e-6
            num[idx] = (up - loss()) / 2e-6
            p[idx] = old
        assert grads[k] == pytest.approx(num, abs=1e-6)


def test_adam_first_step_is_lr_times_sign():
    params = {"w": np.array([1.0, -2.0])}
    Adam(0.01).step(params, {"w": np.array([0.3, -5.0])})
    assert params["w"] == pytest.approx([0.99, -1.99], abs=1e-6)


def test_q_table_converges_to_the_bellman_fixed_point():
    q = QTable(1, 2, alpha=0.5, gamma=0.5)
    for _ in range(200):
        q.update(0, 0, 1.0, 0)
        q.update(0, 1, 0.0, 0)
    assert q.q[0] == pytest.approx([2.0, 1.0])  # Q(a0) = 1 + 0.5 * 2
    assert q.act(0, greedy=True) == 0
    assert sign_pattern_state([0.1, -0.2, 0.3], 3, 1) == 0b101 * 2 + 1


def test_window_state_matches_the_notebook():
    assert list(window_state([1, 2, 4, 7], 1, 3)) == [0, 0, 1]
    assert list(window_state([1, 2, 4, 7], 3, 3)) == [1, 2, 3]


def _trend(n=40):
    return list(100 + np.cumsum(np.random.default_rng(1).normal(0, 1, n)))


def test_q_agent_targets_follow_the_bellman_rule():
    agent = HuseinQAgent(_trend(), window=5, hidden=8, seed=0)
    s, s2 = np.ones(5), np.zeros(5)
    _, y = agent._targets([(s, 1, 0.2, s2, False), (s, 2, -0.1, s2, True)])
    q, q_new = agent.model.predict(s[None])[0], agent.model.predict(s2[None])[0]
    assert y[0][1] == pytest.approx(0.2 + 0.95 * q_new.max())
    assert y[0][[0, 2]] == pytest.approx(q[[0, 2]])
    assert y[1][2] == pytest.approx(-0.1)


def test_q_agent_epsilon_schedules_and_target_sync():
    trend = _trend(30)
    a = HuseinQAgent(trend, window=5, hidden=8, seed=0)
    a.train(1)
    assert a.epsilon == pytest.approx(0.5 * 0.999**29)  # one decay per replay
    d = HuseinQAgent(trend, window=5, hidden=8, preset="double_q_learning", copy_every=7, seed=0)
    d.train(2)
    assert d.epsilon == pytest.approx(0.1 + 0.9 * np.exp(-0.005 * 1))
    assert d.steps == 58
    # last sync at step 55 (the 56th step), three Adam steps ago: no longer equal
    assert not np.allclose(d.target.params["w2"], d.model.params["w2"])
    result = d.trade()
    assert set(result) == {"buys", "sells", "total_gains", "invest"}
    with pytest.raises(ConfigurationError):
        HuseinQAgent(trend, preset="nope")


def test_q_agent_reward_counts_cash_only():
    a = HuseinQAgent([10.0, 11.0, 12.0, 13.0], window=2, hidden=4, seed=0)
    cash, gain = a._step_trade(1, 0, 100.0, inv := [])
    assert (cash, gain, inv) == (90.0, 0.0, [10.0])
    cash, gain = a._step_trade(2, 1, cash, inv)
    assert (cash, gain) == (101.0, 1.0)


def test_evolution_strategy_update_and_ascent():
    def reward(ws):
        return -float(((ws[0] - 3.0) ** 2).sum())

    es = DeepEvolutionStrategy(
        [np.zeros(2)], reward, population_size=4, sigma=0.1, learning_rate=0.03, seed=5
    )
    w0 = es.weights[0].copy()
    rng = np.random.default_rng(5)
    eps = [rng.standard_normal(2) for _ in range(4)]
    r = np.array([reward([w0 + 0.1 * e]) for e in eps])
    z = (r - r.mean()) / (r.std() + 1e-7)
    expect = w0 + 0.03 / (4 * 0.1) * sum(zi * e for zi, e in zip(z, eps, strict=True))
    es.step()
    assert es.weights[0] == pytest.approx(expect)
    es2 = DeepEvolutionStrategy([np.zeros(2)], reward, population_size=15, seed=1)
    hist = es2.train(150)
    assert hist[-1] > reward([np.zeros(2)]) * 0.2


def test_es_agent_reward_simulates_cash():
    w = es_model_weights(3, layer_size=4, seed=0)
    w[1] = np.zeros((4, 3))
    w[1][:, 1] = 0.0
    w[2] = np.zeros((1, 4))
    w[0] = np.zeros((3, 4))  # all-zero decision -> argmax 0 -> hold every bar
    assert es_agent_reward(w, [10, 11, 12, 13], window=3, initial_money=100) == 0.0
    w[2] = np.ones((1, 4))
    w[1][:, 1] = 1.0  # always 'buy': three buys at 10, 11, 12
    assert es_agent_reward(w, [10, 11, 12, 13], window=3, initial_money=100) == pytest.approx(-33.0)


# ---------------------------------------------------------------- FinRL


def test_finrl_env_buys_after_sells_with_costs():
    env = FinRLStockTradingEnv(
        [[10.0, 20.0], [11.0, 19.0], [12.0, 18.0]], initial_amount=1000, hmax=10
    )
    _, r, done = env.step([0.5, 0.3])  # 5 and 3 shares
    assert env.holdings.tolist() == [5, 3]
    assert env.cash == pytest.approx(1000 - 50 * 1.001 - 60 * 1.001)
    end = env.cash + 11 * 5 + 19 * 3
    assert r == pytest.approx((end - 1000) * 1e-4) and not done
    _, r, done = env.step([-1.0, 0.0])  # sell all 5 of the first
    assert env.holdings.tolist() == [0, 3] and done
    assert env.step([1, 1])[2]  # terminal: no trading


def test_finrl_env_turbulence_liquidates_and_blocks_buys():
    env = FinRLStockTradingEnv(
        [[10.0], [10.0], [10.0], [10.0]],
        turbulence=[0, 50, 0, 0],
        turbulence_threshold=40,
        initial_amount=1000,
        hmax=10,
    )
    env.step([1.0])
    assert env.holdings[0] == 10 and env.turbulence == 50
    env.step([1.0])  # turbulent day: forced sell-all, no buy
    assert env.holdings[0] == 0
    assert env.cash == pytest.approx(1000 - 100 * 1.001 + 100 * 0.999)


def test_finrl_ensemble_pieces():
    assert finrl_validation_sharpe([0.01, 0.02, 0.0]) == pytest.approx(2 * 0.01 / 0.01)
    assert finrl_validation_sharpe([0.01, 0.01]) == float("inf")
    ins = np.arange(101.0)
    assert finrl_turbulence_threshold(ins) == pytest.approx(99.0)
    assert finrl_turbulence_threshold(ins, recent=[95.0], adaptive=True) == pytest.approx(90.0)
    assert finrl_turbulence_threshold(ins, recent=[10.0], adaptive=True) == 100.0
    w = finrl_ensemble_windows(300)
    assert w[0] == {"train_end": 0, "validation": (0, 63), "trade": (63, 126)}
    assert w[1]["trade"] == (126, 189) and len(w) == 3
    assert finrl_ensemble_pick({"a2c": 0.5, "ppo": 1.2, "ddpg": 1.2}) == "ppo"


# ---------------------------------------------------------------- update rules


def test_gae_matches_its_recursion():
    adv, ret = gae([1.0, 0.0, 2.0], [0.5, 0.4, 0.3], [0, 0, 1], last_value=9.0, gamma=0.9, lam=0.8)
    d2 = 2.0 - 0.3
    d1 = 0.0 + 0.9 * 0.3 - 0.4
    d0 = 1.0 + 0.9 * 0.4 - 0.5
    a2, a1 = d2, d1 + 0.9 * 0.8 * d2
    assert adv == pytest.approx([d0 + 0.72 * a1, a1, a2])
    assert ret == pytest.approx(adv + np.array([0.5, 0.4, 0.3]))


def test_ppo_clip_loss_and_gradient():
    ratio, adv = np.array([0.5, 1.1, 1.5, 0.7]), np.array([1.0, 1.0, 1.0, -1.0])
    loss, grad = ppo_clip_loss(ratio, adv)
    assert loss == pytest.approx(-(0.5 + 1.1 + 1.2 - 0.8) / 4)
    for i in range(4):
        r2 = ratio.copy()
        r2[i] += 1e-6
        assert grad[i] == pytest.approx((ppo_clip_loss(r2, adv)[0] - loss) / 1e-6, abs=1e-5)


def test_value_targets_and_soft_update():
    assert ddpg_target([1.0], [0], [2.0], 0.9) == pytest.approx([2.8])
    assert td3_target([1.0, 1.0], [0, 1], [3.0, 3.0], [2.0, 5.0], 0.9) == pytest.approx([2.8, 1.0])
    assert sac_target([0.0], [0], [1.0], [2.0], [-1.0], alpha=0.5, gamma=1.0) == pytest.approx(
        [1.5]
    )
    t, s = {"w": np.zeros(2)}, {"w": np.ones(2)}
    soft_update(t, s, 0.1)
    assert t["w"] == pytest.approx([0.1, 0.1])
    a = td3_smoothed_action(np.array([0.95, -0.95]), np.random.default_rng(0), sigma=10)
    assert (np.abs(a) <= 1).all()


def test_linear_a2c_learns_a_contextual_bandit():
    agent = LinearA2C(2, 2, seed=0)
    rng = np.random.default_rng(1)
    for _ in range(400):
        ctx = int(rng.integers(2))
        s = np.eye(2)[ctx]
        a = agent.act(s)
        agent.update([s], [a], [1.0 if a == ctx else 0.0])
    assert agent.policy(np.eye(2)[0])[0] > 0.9 and agent.policy(np.eye(2)[1])[1] > 0.9
