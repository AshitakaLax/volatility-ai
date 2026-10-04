"""research/strategies/mean_reversion.py -- catalog C-MR4, C-MR2, C-MR1."""

from __future__ import annotations

import math

import numpy as np
import pandas as pd
import pytest

from engine.core.exceptions import ConfigurationError
from research.strategies.mean_reversion import (
    adf,
    contrarian_weights,
    decayed_reversal_scores,
    half_life,
    hurst_exponent,
    mackinnon_critical_values,
    s_score,
    s_score_long_signal,
    variance_ratio,
)


def _ar1(phi, n=3000, seed=0, sd=1.0):
    rng = np.random.default_rng(seed)
    e = rng.normal(0, sd, n)
    y = np.empty(n)
    y[0] = 0.0
    for t in range(1, n):
        y[t] = phi * y[t - 1] + e[t]
    return y


def _random_walk(n=3000, seed=0):
    return np.cumsum(np.random.default_rng(seed).normal(0, 1, n))


# ---------------------------------------------------------------- ADF


def test_mackinnon_critical_values_tend_to_the_textbook_asymptotes():
    cv = mackinnon_critical_values(10**9)
    assert cv["1%"] == pytest.approx(-3.43035, abs=1e-6)
    assert cv["5%"] == pytest.approx(-2.86154, abs=1e-6)
    assert cv["10%"] == pytest.approx(-2.56677, abs=1e-6)


def test_mackinnon_finite_sample_correction():
    t = 100
    assert mackinnon_critical_values(t)["5%"] == pytest.approx(
        -2.86154 - 2.8903 / t - 4.234 / t**2 - 40.040 / t**3
    )


def test_adf_statistic_is_the_t_value_on_lagged_level():
    y = _random_walk(400, seed=3)
    out = adf(y, maxlag=1, autolag=False)
    dy = np.diff(y)
    target = dy[1:]
    x = np.column_stack([np.ones(target.size), y[1:-1], dy[:-1]])
    beta, *_ = np.linalg.lstsq(x, target, rcond=None)
    resid = target - x @ beta
    cov = (resid @ resid) / (target.size - 3) * np.linalg.inv(x.T @ x)
    assert out["stat"] == pytest.approx(beta[1] / math.sqrt(cov[1, 1]))
    assert out["lag"] == 1 and out["nobs"] == target.size


def test_adf_rejects_a_stationary_series_and_not_a_random_walk():
    stationary = adf(_ar1(0.5, 1000, seed=1))
    assert stationary["stat"] < stationary["critical_values"]["1%"]
    walk = adf(_random_walk(1000, seed=2))
    assert walk["stat"] > walk["critical_values"]["5%"]


def test_adf_autolag_picks_the_lag_the_differences_need():
    rng = np.random.default_rng(4)
    dy = np.empty(2000)
    dy[0] = 0.0
    for t in range(1, 2000):
        dy[t] = 0.8 * dy[t - 1] + rng.normal()
    assert adf(np.cumsum(dy), maxlag=1)["lag"] == 1


# ---------------------------------------------------------------- Hurst


def test_hurst_matches_the_notebook_computation():
    x = _random_walk(500, seed=5)
    lags = range(2, 100)
    tau = [np.sqrt(np.std(np.subtract(x[lag:], x[:-lag]))) for lag in lags]
    expected = np.polyfit(np.log(lags), np.log(tau), 1)[0] * 2.0
    assert hurst_exponent(x) == pytest.approx(expected)


def _fbm(hurst, n=2048, seed=0):
    """Exact fractional Brownian motion: Cholesky of the fGn autocovariance
    0.5 * (|k+1|^2H - 2|k|^2H + |k-1|^2H), cumulated."""
    k = np.arange(n, dtype=float)
    gamma = 0.5 * (
        np.abs(k + 1) ** (2 * hurst) - 2 * k ** (2 * hurst) + np.abs(k - 1) ** (2 * hurst)
    )
    cov = gamma[np.abs(np.subtract.outer(np.arange(n), np.arange(n)))]
    noise = np.linalg.cholesky(cov) @ np.random.default_rng(seed).normal(size=n)
    return np.cumsum(noise)


@pytest.mark.parametrize("true_h", [0.25, 0.5, 0.75])
def test_hurst_recovers_the_exponent_of_fractional_brownian_motion(true_h):
    estimates = [hurst_exponent(_fbm(true_h, seed=s)) for s in range(4)]
    assert np.mean(estimates) == pytest.approx(true_h, abs=0.07)


def test_a_stationary_series_reads_strongly_mean_reverting():
    assert hurst_exponent(_ar1(0.5, 5000, seed=7)) < 0.2


# ---------------------------------------------------------------- variance ratio


def test_variance_ratio_is_exactly_one_at_q_equals_one():
    assert variance_ratio(_random_walk(200), 1)["vr"] == pytest.approx(1.0)


def test_variance_ratio_matches_lo_mackinlay_by_hand():
    x = _random_walk(300, seed=9) * 0.01
    q, nq = 5, 299
    r = np.diff(x)
    mu = (x[-1] - x[0]) / nq
    var_a = ((r - mu) ** 2).sum() / (nq - 1)
    m = q * (nq - q + 1) * (1 - q / nq)
    var_c = ((x[q:] - x[:-q] - q * mu) ** 2).sum() / m
    vr = var_c / var_a
    out = variance_ratio(x, q)
    assert out["vr"] == pytest.approx(vr)
    assert out["z"] == pytest.approx((vr - 1) / math.sqrt(2 * (2 * q - 1) * (q - 1) / (3 * q * nq)))


def test_variance_ratio_flags_mean_reversion_and_accepts_a_random_walk():
    walk = variance_ratio(_random_walk(4000, seed=10), 20)
    assert walk["vr"] == pytest.approx(1.0, abs=0.15) and abs(walk["z_het"]) < 2.5
    reverting = variance_ratio(_ar1(0.5, 4000, seed=11), 20)
    assert reverting["vr"] < 0.5 and reverting["z_het"] < -2


# ---------------------------------------------------------------- half-life


def test_half_life_recovers_an_ar1_decay():
    phi = 0.9
    assert half_life(_ar1(phi, 20_000, seed=12)) == pytest.approx(math.log(2) / (1 - phi), rel=0.1)


def test_half_life_is_infinite_without_mean_reversion():
    assert half_life(np.arange(50, dtype=float) ** 1.5) == math.inf


# ---------------------------------------------------------------- C-MR2 s-score


def _pair(b=0.8, n=60, seed=13, beta=1.2):
    rng = np.random.default_rng(seed)
    etf = rng.normal(0, 0.01, n)
    x = _ar1(b, n, seed=seed + 1, sd=0.005)
    resid = np.diff(np.concatenate([[0.0], x]))
    return beta * etf + resid, etf


def test_s_score_components_follow_the_appendix():
    stock, etf = _pair()
    out = s_score(stock, etf)
    assert out["beta"] == pytest.approx(1.2, abs=0.25)
    assert out["kappa"] == pytest.approx(-math.log(out["b"]) * 252)
    assert out["m"] == pytest.approx(out["a"] / (1 - out["b"]))
    # Residuals of an OLS fit with an intercept sum to zero: X ends at 0.
    assert out["s"] == pytest.approx(-out["m"] / out["sigma_eq"], abs=1e-9)


def test_long_only_signal_thresholds_and_speed_filter():
    fast = 252 / 30 + 1
    assert s_score_long_signal(-1.3, False, fast) == "open"
    assert s_score_long_signal(-1.2, False, fast) == "none"
    assert s_score_long_signal(-1.3, False, 252 / 30 - 1) == "none"  # reverts too slowly
    assert s_score_long_signal(-0.4, True, fast) == "close"
    assert s_score_long_signal(-0.6, True, fast) == "hold"


# ---------------------------------------------------------------- C-MR1 reversal


def test_contrarian_weights_are_lo_mackinlay():
    r = pd.Series({"A": 0.03, "B": -0.01, "C": -0.05, "D": 0.01})
    w = contrarian_weights(r)
    assert w.to_dict() == pytest.approx((-(r - r.mean()) / 4).to_dict())
    assert w.sum() == pytest.approx(0.0)
    assert w["C"] > w["B"] > 0 > w["D"] > w["A"]


def test_long_only_projection_buys_only_losers():
    r = pd.Series({"A": 0.03, "B": -0.01, "C": -0.05, "D": 0.01})
    w = contrarian_weights(r, long_only=True)
    assert w.sum() == pytest.approx(1.0)
    assert w["A"] == 0 and w["D"] == 0 and w["C"] > w["B"] > 0


def test_decayed_scores_weight_recent_residuals_most():
    e = pd.DataFrame({"X": [1.0, 0.0, 0.0, 0.0, 0.0, 0.0]})
    scores = decayed_reversal_scores(e, half_life=2.0, formation=3)
    assert scores["X"].isna().tolist()[:2] == [True, True]
    assert scores["X"].iloc[2] == pytest.approx(0.5 ** (2 / 2.0))  # e_0 at lag 2
    assert scores["X"].iloc[3] == pytest.approx(0.0)  # e_0 has left the window


@pytest.mark.parametrize(
    "call",
    [
        lambda: adf(np.arange(5.0)),
        lambda: hurst_exponent(np.arange(50.0), max_lag=100),
        lambda: variance_ratio(np.arange(10.0), 8),
        lambda: s_score(np.zeros(5), np.zeros(5)),
        lambda: contrarian_weights(pd.Series([0.1])),
        lambda: decayed_reversal_scores(pd.DataFrame({"x": [0.0]}), half_life=0.0),
    ],
)
def test_bad_inputs_are_rejected(call):
    with pytest.raises(ConfigurationError):
        call()
