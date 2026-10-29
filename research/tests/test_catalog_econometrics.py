"""research/catalog/econometrics.py -- estimators recover simulated truths."""

from __future__ import annotations

import numpy as np
import pytest
from scipy import stats

from engine.core.exceptions import ConfigurationError
from research.catalog.econometrics import (
    clayton_density,
    clayton_h,
    clayton_h_inv,
    dcc_fit,
    empirical_quantile,
    fit_cvine,
    fit_var,
    fit_vecm,
    fracdiff,
    fracdiff_weights,
    garch11_filter,
    garch11_fit,
    garch11_forecast,
    gaussian_copula_corr,
    gph_d,
    gumbel_cdf,
    half_life,
    johansen,
    kalman_filter,
    kalman_hedge_ratio,
    pseudo_observations,
    simulate_cvine,
    var_forecast,
    vecm_forecast,
)


def test_garch_recovers_its_parameters_and_forecasts_mean_reversion():
    rng = np.random.default_rng(0)
    n, (o, a, b) = 4000, (0.05, 0.1, 0.85)
    r, s2 = np.empty(n), o / (1 - a - b)
    for t in range(n):
        r[t] = np.sqrt(s2) * rng.normal()
        s2 = o + a * r[t] ** 2 + b * s2
    fit = garch11_fit(r)
    assert fit["alpha"] == pytest.approx(a, abs=0.04) and fit["beta"] == pytest.approx(b, abs=0.06)
    f = garch11_forecast(fit, r[-1], 500)
    assert f[-1] == pytest.approx(fit["omega"] / (1 - fit["alpha"] - fit["beta"]), rel=0.05)
    assert garch11_filter(r, o, a, b).shape == (n,)


def test_dcc_tracks_a_correlation_shift():
    rng = np.random.default_rng(1)
    low = rng.multivariate_normal([0, 0], [[1, 0.0], [0.0, 1]], 400)
    high = rng.multivariate_normal([0, 0], [[1, 0.9], [0.9, 1]], 400)
    out = dcc_fit(np.vstack([low, high]))
    rho = out["correlations"][:, 0, 1]
    assert rho[390] < 0.4 < 0.6 < rho[-1] and 0 < out["a"] + out["b"] < 1


def test_kalman_filters_a_random_walk_and_a_drifting_hedge_ratio():
    rng = np.random.default_rng(2)
    level = np.cumsum(rng.normal(0, 0.1, 300))
    y = level + rng.normal(0, 1.0, 300)
    out = kalman_filter(y, [[1.0]], [[1.0]], [[0.01]], [[1.0]], [0.0], [[1.0]])
    assert np.mean((out["state"][:, 0] - level) ** 2) < np.mean((y - level) ** 2)
    x = 50 + np.cumsum(rng.normal(0, 1, 500))
    beta = np.linspace(1.0, 2.0, 500)
    hr = kalman_hedge_ratio(beta * x + rng.normal(0, 0.5, 500), x, delta=1e-4, obs_var=0.25)
    assert hr["beta"][-1] == pytest.approx(2.0, abs=0.1)


def test_johansen_finds_one_cointegrating_relation_and_the_vecm_forecasts():
    rng = np.random.default_rng(3)
    common = np.cumsum(rng.normal(size=600))
    y = np.column_stack(
        [
            common + rng.normal(0, 0.5, 600),
            0.5 * common + rng.normal(0, 0.5, 600),
            np.cumsum(rng.normal(size=600)),
        ]
    )
    out = johansen(y)
    assert out["rank"] == 1 and out["trace"][0] > out["crit_95"][0]
    vec = out["vectors"][:, 0]
    assert vec[0] / vec[1] == pytest.approx(-0.5, abs=0.1)
    model = fit_vecm(y, 1)
    assert vecm_forecast(model, y, 3).shape == (3, 3)
    with pytest.raises(ConfigurationError):
        johansen(rng.normal(size=(50, 6)))


def test_half_life_fracdiff_gph_and_var():
    rng = np.random.default_rng(4)
    s = np.zeros(2000)
    for t in range(1999):
        s[t + 1] = 0.9 * s[t] + rng.normal()
    assert half_life(s) == pytest.approx(np.log(2) / -np.log(0.9), rel=0.25)
    assert half_life(np.cumsum(np.ones(10))) == np.inf
    assert fracdiff_weights(1.0, 3).tolist() == [1.0, -1.0, 0.0]
    x = np.cumsum(rng.normal(size=300))
    assert np.allclose(fracdiff(x, 1.0, window=2)[1:], np.diff(x))
    # an ARFIMA(0, d, 0) series: fractionally integrate white noise
    eps = rng.normal(size=6000)
    psi = fracdiff_weights(-0.3, 1000)
    lm = np.convolve(eps, psi)[: len(eps)][1000:]
    assert gph_d(lm, 0.6) == pytest.approx(0.3, abs=0.12)
    a = np.array([[0.5, 0.1], [0.0, 0.3]])
    y = np.zeros((3000, 2))
    for t in range(2999):
        y[t + 1] = a @ y[t] + rng.normal(size=2)
    m = fit_var(y, 1)
    assert m["lags"][0] == pytest.approx(a, abs=0.05)
    assert var_forecast(m, y, 2).shape == (2, 2)


def test_copulas_and_the_c_vine_reproduce_dependence():
    rng = np.random.default_rng(5)
    theta = 2.0
    u = rng.uniform(size=1000)
    w = rng.uniform(size=1000)
    v = clayton_h_inv(w, u, theta)
    assert clayton_h(v, u, theta) == pytest.approx(w, abs=1e-8)
    assert stats.kendalltau(u, v)[0] == pytest.approx(theta / (theta + 2), abs=0.05)
    assert clayton_density(0.5, 0.5, 2.0) > 1.0 and 0 < gumbel_cdf(0.5, 0.5, 2.0) < 0.5
    z = rng.multivariate_normal([0, 0, 0], [[1, 0.6, 0.3], [0.6, 1, 0.2], [0.3, 0.2, 1]], 2000)
    pobs = pseudo_observations(z)
    assert pobs.min() > 0 and pobs.max() < 1
    assert gaussian_copula_corr(pobs)[0, 1] == pytest.approx(0.6, abs=0.05)
    vine = fit_cvine(pobs)
    sim = simulate_cvine(vine, 4000, rng=0)
    tau_data, tau_sim = (
        stats.kendalltau(z[:, 0], z[:, 1])[0],
        stats.kendalltau(sim[:, 0], sim[:, 1])[0],
    )
    assert tau_sim == pytest.approx(tau_data, abs=0.06)
    assert empirical_quantile(z, sim).shape == (4000, 3)
