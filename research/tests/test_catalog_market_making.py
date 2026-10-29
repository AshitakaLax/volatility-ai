"""research/catalog/market_making.py -- quoting rules on the AS simulator."""

from __future__ import annotations

import numpy as np
import pytest

from engine.core.exceptions import ConfigurationError
from research.catalog.market_making import (
    as_policy,
    as_quotes,
    duopoly_payoffs,
    evolve_market_maker,
    fictitious_play,
    fill_probability,
    nash_spread,
    replicator_dynamics,
    simulate_market_maker,
    stackelberg_spread,
    trader_demand_response,
    train_competing_dqn_makers,
    train_rl_market_maker,
    undercutting_follower,
    xemm_fill_pnl,
    xemm_quotes,
)


def test_avellaneda_stoikov_quotes_skew_against_inventory():
    bid0, ask0 = as_quotes(100, 0, 0, 1, 2, 0.1, 1.5)
    bid1, ask1 = as_quotes(100, 5, 0, 1, 2, 0.1, 1.5)
    assert bid0 < 100 < ask0 and bid1 < bid0 and ask1 < ask0
    assert ask0 - bid0 == pytest.approx(0.1 * 4 + 2 / 0.1 * np.log1p(0.1 / 1.5))
    assert fill_probability(0.0, 140, 1.5, 0.005) == pytest.approx(0.7)


def test_as_quoter_controls_inventory_better_than_a_fixed_quote():
    fixed = [
        simulate_market_maker(lambda t, m, q: (0.7, 0.7), rng=s)["inventory"] for s in range(20)
    ]
    skewed = [simulate_market_maker(as_policy(gamma=1.0), rng=s)["inventory"] for s in range(20)]
    assert np.mean([np.abs(x).mean() for x in skewed]) < np.mean([np.abs(x).mean() for x in fixed])


def test_adaptive_mesh_and_robust_q_learning():
    out = train_rl_market_maker(episodes=90, refinements=2, rng=0)
    assert len(out["actions"]) == 25 and len(out["history"]) == 90
    db, da = out["policy"](0.0, 100.0, 5)
    assert db > 0 and da > 0
    robust = train_rl_market_maker(
        episodes=30, refinements=0, robust=True, models=[(140.0, 1.5), (60.0, 2.0)], rng=0
    )
    assert robust["q"].shape == (21, 25)


def test_games_between_quoters():
    grid = np.round(np.arange(0.1, 1.6, 0.1), 2)
    pay = duopoly_payoffs(grid)
    assert pay[3, 5] > 0 and pay[5, 3] == 0
    m1, m2 = fictitious_play(pay)
    assert m1.sum() == pytest.approx(1.0) and m2.sum() == pytest.approx(1.0)
    d_nash = nash_spread(grid)
    monopoly = grid[np.argmax([2 * d * 140 * np.exp(-1.5 * d) for d in grid])]
    assert d_nash < monopoly  # competition narrows the spread
    demand = trader_demand_response()
    leader = stackelberg_spread(grid, demand, lambda d, rate: 2 * d * rate)
    assert leader["leader"] == pytest.approx(monopoly)
    follower = undercutting_follower(grid)
    duo = stackelberg_spread(grid, follower, lambda d, f: duopoly_payoffs([d, f])[0, 1])
    assert duo["follower"] <= duo["leader"]


def test_replicator_dynamics_find_the_dominant_strategy():
    payoff = np.array([[3.0, 0.0], [5.0, 1.0]])  # prisoner's dilemma: defect dominates
    assert replicator_dynamics(payoff)[1] > 0.99


def test_evolutionary_and_competing_learners_run():
    out = evolve_market_maker(generations=3, pop=6, episodes=2, rng=0)
    assert len(out["history"]) == 3 and out["policy"](0.0, 100.0, 0)[0] > 0
    duo = train_competing_dqn_makers(episodes=3, steps=40)
    assert len(duo["makers"]) == 2 and 0 <= duo["makers"][0].act([0.0, 0.6]) < 4


def test_cross_exchange_quotes_lock_in_the_margin():
    bid, ask = xemm_quotes(99.0, 101.0, 0.002)
    assert bid < 99.0 and ask > 101.0
    assert xemm_fill_pnl("bid", bid, 99.0) > 0 and xemm_fill_pnl("ask", ask, 101.0) > 0
    with pytest.raises(ConfigurationError):
        xemm_quotes(101.0, 99.0)
