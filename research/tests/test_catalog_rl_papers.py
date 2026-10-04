"""research/catalog/rl_papers.py -- Moody-Saffell RRL and the differential
Sharpe ratio, Huang's action-augmented DRQN, and the EIIE portfolio
policy."""

from __future__ import annotations

import numpy as np
import pytest

from research.catalog.rl_papers import (
    ActionAugmentedDRQN,
    EIIEPolicy,
    ElmanQNetwork,
    RRLTrader,
    augmented_rewards,
    differential_sharpe,
    drift_weights,
    price_relatives,
    transaction_remainder,
)

# ---------------------------------------------------------------- C-RL5


def test_differential_sharpe_is_the_first_order_sharpe_change():
    r = np.random.default_rng(0).normal(0.001, 0.01, 50)
    eta = 1e-7
    d, a, b = differential_sharpe(r, eta=eta)
    a_prev, b_prev = np.r_[r[:10].mean(), a[:-1]], np.r_[(r[:10] ** 2).mean(), b[:-1]]
    s, s_prev = a / np.sqrt(b - a * a), a_prev / np.sqrt(b_prev - a_prev**2)
    assert (s - s_prev) / eta == pytest.approx(d, rel=1e-4, abs=1e-6)


def test_rrl_sharpe_gradient_matches_finite_differences():
    r = np.random.default_rng(1).normal(0.0, 0.01, 120)
    trader = RRLTrader(m=4, delta=0.002, seed=2, scale=0.5)
    s, g = trader.sharpe_and_gradient(r)
    num = np.zeros_like(g)
    for i in range(len(g)):
        w = trader.w.copy()
        w[i] += 1e-6
        up = trader.sharpe_and_gradient(r, w)[0]
        w[i] -= 2e-6
        num[i] = (up - trader.sharpe_and_gradient(r, w)[0]) / 2e-6
    assert g == pytest.approx(num, rel=1e-4, abs=1e-7)
    f = trader.positions(r)
    rs = trader.trading_returns(r, f)
    assert s == pytest.approx(rs.mean() / rs.std())


def _momentum_returns(n=600, phi=0.3, seed=3):
    rng = np.random.default_rng(seed)
    r = np.zeros(n)
    for t in range(1, n):
        r[t] = phi * r[t - 1] + rng.normal(0, 0.01)
    return r


def test_rrl_batch_training_raises_the_in_sample_sharpe():
    r = _momentum_returns()
    trader = RRLTrader(m=3, delta=0.0005, seed=4, input_scale=r.std())
    history = trader.fit(r, epochs=150, lr=0.1)
    assert history[-1] > history[0] + 0.1  # AR(1) momentum is learnable


def test_rrl_online_dsr_learns_a_persistent_drift():
    r = np.full(800, 0.002) + np.random.default_rng(5).normal(0, 0.001, 800)
    trader = RRLTrader(m=3, delta=0.0, seed=6)
    out = trader.fit_online(r, rho=0.01, eta=0.05)
    assert np.isfinite(out["dsr"]).all()
    assert out["positions"][-100:].mean() > 0.5


# ---------------------------------------------------------------- C-RL4


def test_elman_bptt_matches_finite_differences():
    rng = np.random.default_rng(7)
    net = ElmanQNetwork(3, 5, rng)
    xs, pos = rng.normal(size=(6, 3)), rng.integers(0, 3, 6)
    y, mask = rng.normal(size=(6, 3)), np.r_[np.ones(5), 0.0]
    _, grads = net.loss_and_grads(xs, pos, y, mask)
    for k, p in net.params.items():
        num = np.zeros_like(p)
        for idx in np.ndindex(p.shape):
            old = p[idx]
            p[idx] = old + 1e-6
            up = net.loss_and_grads(xs, pos, y, mask)[0]
            p[idx] = old - 1e-6
            num[idx] = (up - net.loss_and_grads(xs, pos, y, mask)[0]) / 2e-6
            p[idx] = old
        assert grads[k] == pytest.approx(num, abs=1e-6), k


def test_augmented_rewards_score_every_action():
    r = augmented_rewards([10.0, 12.0, 11.0], [0, 1, 1], lot=2.0, cost=0.5)
    # step 0 from flat: short -4 - 0.5, neutral 0, long +4 - 0.5
    assert r[0] == pytest.approx([-4.5, 0.0, 3.5])
    # step 1 from long: short +2 - 1.0, neutral 0 - 0.5, long -2
    assert r[1] == pytest.approx([1.0, -0.5, -2.0])


def test_drqn_targets_reduce_to_rewards_with_a_zero_target_net():
    agent = ActionAugmentedDRQN(2, hidden=4, seed=0)
    for k in agent.target.params:
        agent.target.params[k] = np.zeros_like(agent.target.params[k])
    feats, prices, pos = np.ones((3, 2)), [1.0, 2.0, 4.0], [0, 1, -1]
    assert agent.targets(feats, prices, pos) == pytest.approx(augmented_rewards(prices, pos))


def test_drqn_learns_to_be_long_in_a_rising_market():
    agent = ActionAugmentedDRQN(2, hidden=8, gamma=0.5, tau=0.05, lr=0.01, seed=1)
    prices = np.arange(40, dtype=float)
    feats = np.column_stack([np.ones(40), np.r_[0.0, np.diff(prices)]])
    for _ in range(300):
        pos = agent.rollout_positions(feats)
        agent.train_sequence(feats, prices, pos)
    greedy = agent.rollout_positions(feats, greedy=True)
    assert (greedy[1:] == 1.0).mean() > 0.9


# ---------------------------------------------------------------- RL3 EIIE


def test_drift_and_transaction_remainder():
    w = np.array([0.2, 0.5, 0.3])
    wp = drift_weights(w, np.array([1.0, 1.1, 0.9]))
    assert wp.sum() == pytest.approx(1.0) and wp[1] > w[1]
    assert transaction_remainder(wp, wp) == pytest.approx(1.0)
    assert transaction_remainder(wp, w, 0.0, 0.0) == pytest.approx(1.0)
    mu = transaction_remainder(wp, w)
    c = 0.0025
    rhs = (1 - c * wp[0] - (2 * c - c * c) * np.clip(wp[1:] - mu * w[1:], 0, None).sum()) / (
        1 - c * w[0]
    )
    assert mu == pytest.approx(rhs) and 0 < mu < 1
    assert mu == pytest.approx(1 - c * np.abs(wp[1:] - w[1:]).sum(), abs=2e-4)


def _toy_market(n=260):
    t = np.arange(n)
    up = 100 * 1.01**t * (1 + 0.002 * np.sin(t))
    down = 100 * 0.99**t * (1 + 0.002 * np.cos(t))
    return np.column_stack([up, down])


def test_eiie_gradient_matches_finite_differences():
    close = _toy_market(120)
    y = price_relatives(close)
    pol = EIIEPolicy(2, window=10, seed=0)
    pol.beta, pol.cash_bias = 0.3, 0.2
    base = np.tile([0.4, 0.3, 0.3], (len(close), 1))
    ts = [30, 50, 70]
    _, (gt, gb, gc) = pol.batch_objective(close, y, ts, base.copy())

    def f():
        return pol.batch_objective(close, y, ts, base.copy(), grad=False)[0]

    h = 1e-6
    pol.theta[3] += h
    up = f()
    pol.theta[3] -= 2 * h
    assert gt[3] == pytest.approx((up - f()) / (2 * h), rel=1e-4)
    pol.theta[3] += h
    pol.beta += h
    up = f()
    pol.beta -= 2 * h
    assert gb == pytest.approx((up - f()) / (2 * h), rel=1e-4)
    pol.beta += h
    pol.cash_bias += h
    up = f()
    pol.cash_bias -= 2 * h
    assert gc == pytest.approx((up - f()) / (2 * h), rel=1e-4)


def test_eiie_learns_to_hold_the_rising_asset():
    close = _toy_market()
    pol = EIIEPolicy(2, window=10, commission=0.0025, seed=1)
    hist = pol.train(close, steps=300, batch=30, lr=20.0, seed=2)
    assert np.mean(hist[-20:]) > np.mean(hist[:20]) + 0.005
    assert np.mean(hist[-20:]) == pytest.approx(np.log(1.01), abs=5e-4)  # nearly all-in
    value = pol.backtest(close)
    assert value[-1] > 0.8 * 1.01 ** (len(close) - 10)
