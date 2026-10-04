"""research/catalog/je_suis_tm_projects.py -- Oil Money, Monte Carlo, Smart
Farmers, Wisdom of Crowds and the graph-theory portfolio, plus the numpy
stand-ins for the solvers the sources import."""

from __future__ import annotations

import itertools

import numpy as np
import pandas as pd
import pytest

from engine.core.exceptions import ConfigurationError
from research.catalog.je_suis_tm_projects import (
    basket_index,
    clique_centrality_selection,
    constrained_demand_ols,
    core_numbers,
    correlation_graph,
    dawid_skene,
    degeneracy_selection,
    markowitz_weights,
    maximal_cliques,
    monte_carlo_direction_hit,
    monte_carlo_forecast,
    nelder_mead,
    nnls,
    oil_money_signals,
    platt_burges,
    simplex_qp,
    smart_farmers_calibrate_cost,
    smart_farmers_plan,
    smart_farmers_price,
    two_stage_least_squares,
)

# ---------------------------------------------------------------- solvers


def test_nnls_matches_brute_force_over_active_sets():
    rng = np.random.default_rng(3)
    a, b = rng.normal(size=(30, 5)), rng.normal(size=30)
    x = nnls(a, b)
    assert (x >= 0).all()
    best = min(
        (
            np.linalg.norm(a[:, list(s)] @ np.linalg.lstsq(a[:, list(s)], b, rcond=None)[0] - b),
            s,
        )
        for k in range(6)
        for s in itertools.combinations(range(5), k)
        if k == 0 or (np.linalg.lstsq(a[:, list(s)], b, rcond=None)[0] >= 0).all()
    )[0]
    assert np.linalg.norm(a @ x - b) == pytest.approx(best, abs=1e-9)


def test_nelder_mead_finds_the_rosenbrock_minimum():
    def rosen(v):
        return 100 * (v[1] - v[0] ** 2) ** 2 + (1 - v[0]) ** 2

    x = nelder_mead(rosen, [-1.2, 1.0], xatol=1e-8, fatol=1e-10, max_iter=5000)
    assert x == pytest.approx([1.0, 1.0], abs=1e-4)


def _check_simplex_kkt(p, q, w):
    assert w.sum() == pytest.approx(1.0) and (w >= -1e-12).all()
    grad = p @ w + q
    support = w > 1e-9
    nu = -grad[support].mean()
    assert grad[support] + nu == pytest.approx(0.0, abs=1e-9)
    assert (grad[~support] + nu >= -1e-9).all()


def test_simplex_qp_satisfies_kkt_on_random_problems():
    rng = np.random.default_rng(11)
    for _ in range(20):
        m = rng.normal(size=(40, 6))
        p, q = np.cov(m.T), rng.normal(scale=0.3, size=6)
        _check_simplex_kkt(p, q, simplex_qp(p, q))


# ---------------------------------------------------------------- Q6 Oil Money


def _oil_series(n=90, jump_at=60, jump=0.1):
    x = np.linspace(50.0, 80.0, n)
    y = 2.0 + 0.1 * x + np.where(np.arange(n) % 2 == 0, 0.01, -0.01)
    y[jump_at:] += jump
    return x, y


def test_oil_money_enters_above_two_sigma_and_exits_on_the_12th_bar():
    x, y = _oil_series()
    out = oil_money_signals(x, y)
    nz = np.flatnonzero(out["signals"].to_numpy()[:73])
    assert list(nz) == [60, 72]
    assert out["signals"][60] == 1 and out["signals"][72] == -1
    assert out["pos2 sigma"][61] == pytest.approx(out["forecast"][61])  # bands collapsed


def test_oil_money_shorts_and_stops_out():
    x, y = _oil_series(jump=-0.1)
    y[63:] -= 0.6
    out = oil_money_signals(x, y)
    assert out["signals"][60] == -1 and out["signals"][63] == 1
    assert (out["signals"][61:63] == 0).all()


def test_oil_money_needs_a_good_fit():
    rng = np.random.default_rng(0)
    x, y = np.linspace(0, 1, 120), rng.normal(size=120)
    assert (oil_money_signals(x, y)["signals"] == 0).all()
    with pytest.raises(ConfigurationError):
        oil_money_signals(x, y[:-1])


# ---------------------------------------------------------------- Q11 Monte Carlo


def test_monte_carlo_split_paths_and_pick():
    close = 100 * np.exp(np.cumsum(np.r_[0, np.random.default_rng(1).normal(0, 0.01, 10)]))
    res = monte_carlo_forecast(close, simulations=50, seed=7)
    assert (res["horizon"], res["n_train"]) == (6, 5)  # ceil(0.5 * 11)
    assert res["paths"].shape == (50, 11) and (res["paths"][:, 0] == close[0]).all()
    fit = np.std(res["paths"][:, :5] - close[:5], axis=1)
    assert res["pick"] == int(np.argmin(fit))
    rets = np.log(close[1:5] / close[:4])
    assert res["drift"] == pytest.approx(rets.mean() - rets.var(ddof=1) / 2)


def test_monte_carlo_paths_have_the_gbm_drift():
    close = np.linspace(100, 130, 200)
    res = monte_carlo_forecast(close, simulations=4000, seed=2)
    steps = np.diff(np.log(res["paths"]), axis=1)
    assert steps.mean() == pytest.approx(res["drift"], abs=3e-5)
    assert steps.std() == pytest.approx(res["volatility"], rel=0.01)


def test_monte_carlo_direction_hit():
    close = np.array([1, 2, 3, 4, 5.0])
    assert monte_carlo_direction_hit(close, [1, 1, 3, 3, 4.0], 2) == 1
    assert monte_carlo_direction_hit(close, [1, 1, 3, 3, 2.0], 2) == -1


# ---------------------------------------------------------------- Q14 Smart Farmers


def _farm(**kw):
    base = dict(
        price_hist=[10.0, 8.0, 12.0],
        production_hist=[100.0, 80.0, 50.0],
        area_hist=[50.0, 40.0, 30.0],
        land_per_unit=[0.5, 0.5, 0.6],
        land_total=120.0,
        alpha=[0.05, 0.04, 0.08],
        beta=[0.0, 0.0, 0.0],
        gamma=[0.0, 0.0, 0.0],
        delta_pop=0.0,
        delta_gdp=0.0,
        cost=[4.0, 5.0, 6.0],
        lower_fraction=[0.0, 0.0, 0.0],
        upper=10.0,
    )
    base.update(kw)
    return base


def test_smart_farmers_interior_plan_meets_kkt():
    f = _farm()
    q = smart_farmers_plan(**f)
    a, al = np.array(f["land_per_unit"]), np.array(f["alpha"])
    c = -np.array(f["price_hist"]) - al * np.array(f["production_hist"]) + np.array(f["cost"])
    assert a @ q == pytest.approx(120.0)
    lam = -(al * q + c) / a  # 1/2 alpha q^2 + c q: stationarity alpha q + c + lam a = 0
    assert lam == pytest.approx(np.full(3, lam[0]))


def test_smart_farmers_bounds_bind_and_infeasible_land_raises():
    f = _farm(lower_fraction=[0.0, 0.9, 0.0], upper=1.2)
    q = smart_farmers_plan(**f)
    land = np.array(f["land_per_unit"]) * q
    assert land[1] >= 0.9 * 40 - 1e-9 and (land <= 1.2 * np.array(f["area_hist"]) + 1e-9).all()
    assert land.sum() == pytest.approx(120.0)
    with pytest.raises(ConfigurationError):
        smart_farmers_plan(**_farm(land_total=1e6, upper=1.2))


def test_smart_farmers_price_keeps_the_script_sign():
    args = ([10.0], [120.0], [100.0], [0.05], [1.0], [2.0], 3.0, 0.5)
    assert smart_farmers_price(*args) == pytest.approx([10 + 3 + 1 + 1.0])
    assert smart_farmers_price(*args, consistent=True) == pytest.approx([10 + 3 + 1 - 1.0])


def test_smart_farmers_cost_calibration_recovers_the_true_cost():
    f = _farm()
    true_cost = np.array(f["cost"])
    target = smart_farmers_plan(**f)

    def plan_for(cost):
        return smart_farmers_plan(**{**f, "cost": cost})

    est = smart_farmers_calibrate_cost(plan_for, target, true_cost * 0.8)
    assert plan_for(est) == pytest.approx(target, rel=1e-3)


def test_constrained_demand_ols_clamps_negative_slopes():
    rng = np.random.default_rng(5)
    gdp, pop, prod = rng.normal(100, 10, 40), rng.normal(50, 5, 40), rng.normal(20, 4, 40)
    price = 3.0 + 0.2 * gdp + 0.5 * pop - 0.7 * prod  # alpha = 0.7 on -production
    fit = constrained_demand_ols(gdp, pop, prod, price)
    assert [fit[k] for k in ("constant", "gamma", "beta", "alpha")] == pytest.approx(
        [3.0, 0.2, 0.5, 0.7]
    )
    wrong_sign = constrained_demand_ols(gdp, pop, prod, 3.0 + 0.2 * gdp - 0.5 * pop)
    assert wrong_sign["beta"] == 0.0


def test_two_stage_least_squares_is_the_iv_estimator():
    rng = np.random.default_rng(9)
    z, u = rng.normal(size=500), rng.normal(size=500)
    x = z + u  # endogenous: shares u with the error
    y = 1.0 + 2.0 * x + u
    beta = two_stage_least_squares(y, x, None, z)
    zc, xc, yc = z - z.mean(), x - x.mean(), y - y.mean()
    assert beta[1] == pytest.approx((zc @ yc) / (zc @ xc))
    assert abs(beta[1] - 2.0) < abs(np.polyfit(x, y, 1)[0] - 2.0)


# ---------------------------------------------------------------- Q16 Wisdom of Crowds


def test_dawid_skene_reproduces_the_notebook_example():
    truth, iterations = dawid_skene([[1, 1, 0, 1, 1], [0, 0, 0, 1, 1], [1, 0, 1, 0, 0]])
    assert (truth, iterations) == ([0, 1, 0, 1, 1], 2)


def test_dawid_skene_unanimous_crowd_converges_at_once():
    assert dawid_skene([[1, 0, 1], [1, 0, 1]]) == ([1, 0, 1], 1)


def test_platt_burges_recovers_rater_biases():
    rng = np.random.default_rng(4)
    items, bias = rng.normal(0, 3, 12), np.array([-2.0, 0.0, 1.0, 3.0, -1.0])
    x = items[None, :] + bias[:, None] + rng.normal(0, 0.3, (5, 12))
    res = platt_burges(x)
    assert platt_burges(x, tolerance=1e-2)["converged"]
    centred = res["nu_r"] - res["nu_r"].mean()
    assert centred == pytest.approx(bias - bias.mean(), abs=0.1)
    assert np.corrcoef(res["mu_p"], items)[0, 1] > 0.99
    # one draw per item with a free mean: the variances keep shrinking, so
    # only the relative-change stop ends the run
    assert platt_burges(x, max_iter=400)["tau_r"].max() < res["tau_r"].min()
    with pytest.raises(ConfigurationError):
        platt_burges(np.ones((3, 3)))


# ---------------------------------------------------------------- Q13 graph portfolio


def _corr():
    names = list("ABCDEF")
    c = pd.DataFrame(np.eye(6) * 0.5 + 0.1, index=names, columns=names)
    for a, b in [("A", "B"), ("A", "C"), ("B", "C"), ("C", "D"), ("D", "F")]:
        c.loc[a, b] = c.loc[b, a] = 0.8
    return c


def test_correlation_graph_and_core_numbers():
    adj = correlation_graph(_corr(), 0.6)
    assert list(adj) == ["A", "B", "C", "D", "F"] and "E" not in adj
    assert core_numbers(adj) == {"A": 2, "B": 2, "C": 2, "D": 1, "F": 1}


def test_degeneracy_selection_picks_an_independent_set_plus_outliers():
    assert degeneracy_selection(_corr(), 0.6) == (["D", "A"], ["E"])


def test_clique_centrality_counts_maximal_cliques():
    cliques = {frozenset(c) for c in maximal_cliques(correlation_graph(_corr()))}
    assert cliques == {frozenset("ABC"), frozenset("CD"), frozenset("DF")}
    assert clique_centrality_selection(_corr(), 0.6, centrality=1) == ["C", "D"]


def test_bron_kerbosch_matches_brute_force():
    rng = np.random.default_rng(8)
    nodes = list(range(9))
    adj = {v: set() for v in nodes}
    for a, b in itertools.combinations(nodes, 2):
        if rng.random() < 0.5:
            adj[a].add(b)
            adj[b].add(a)
    cliques = [
        set(s)
        for k in range(1, 10)
        for s in itertools.combinations(nodes, k)
        if all(b in adj[a] for a, b in itertools.combinations(s, 2))
    ]
    maximal = {frozenset(c) for c in cliques if not any(c < d for d in cliques)}
    assert {frozenset(c) for c in maximal_cliques(adj)} == maximal


def test_markowitz_weights():
    rng = np.random.default_rng(6)
    r = pd.DataFrame(rng.normal([0.001, 0.0005, 0.002], [0.01, 0.02, 0.03], (500, 3)))
    w = markowitz_weights(r)
    cov, mean = np.cov(r.to_numpy().T), r.to_numpy().mean(axis=0)
    _check_simplex_kkt(cov, -mean, w["max_sharpe"])
    _check_simplex_kkt(cov, np.zeros(3), w["min_variance"])
    assert list(w["max_return"]) == [0.0, 0.0, 1.0]
    two = pd.DataFrame({"a": [0.01, -0.01] * 50, "b": [0.02, -0.02, -0.02, 0.02] * 25})
    mv = markowitz_weights(two)["min_variance"]  # uncorrelated: w_a = var_b / (var_a + var_b)
    assert mv[0] == pytest.approx(4 / 5)


def test_basket_index_sums_member_prices():
    prices = pd.DataFrame({"A": [1.0, 2.0], "B": [3.0, 4.0], "C": [9.0, 9.0]})
    assert list(basket_index(prices, ["A", "B"])) == [4.0, 6.0]
