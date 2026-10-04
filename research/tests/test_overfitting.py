"""research/optimization/overfitting.py -- catalog C-ML4."""

from __future__ import annotations

import math
from statistics import NormalDist

import numpy as np
import pytest

from engine.core.exceptions import ConfigurationError
from research.optimization.overfitting import (
    deflated_sharpe,
    expected_max_sharpe,
    moments,
    probabilistic_sharpe,
    probability_of_backtest_overfitting,
    sharpe_ratio,
)

# Bailey & Lopez de Prado (2014), "A NUMERICAL EXAMPLE": N=100 trials,
# V[SR] = 1/2 annualized, T=1250 daily observations, skew -3, kurtosis 10,
# selected SR 2.5 annualized; 250 observations a year.
SR = 2.5 / math.sqrt(250)
VAR = 0.5 / 250


def test_expected_max_sharpe_matches_the_paper():
    assert round(expected_max_sharpe(VAR, 100), 4) == 0.1132


def test_deflated_sharpe_matches_the_paper():
    assert round(deflated_sharpe(SR, VAR, 100, 1250, -3, 10), 4) == 0.9004


def test_fewer_trials_would_have_passed_at_95_percent():
    # "Should the strategist have made his discovery after running only N=46
    # independent trials ... DSR would have been 0.9505".
    assert round(deflated_sharpe(SR, VAR, 46, 1250, -3, 10), 4) == 0.9505


def test_normal_returns_survive_until_88_trials():
    # "If the strategy had exhibited Normal returns ... after N=88 independent trials."
    assert deflated_sharpe(SR, VAR, 88, 1250, 0, 3) >= 0.95
    assert deflated_sharpe(SR, VAR, 89, 1250, 0, 3) < 0.95


def test_psr_with_normal_moments_and_zero_threshold():
    sr, t = 0.08, 500
    expected = NormalDist().cdf(sr * math.sqrt(t - 1) / math.sqrt(1 + (3 - 1) / 4 * sr**2))
    assert probabilistic_sharpe(sr, 0.0, t, 0.0, 3.0) == pytest.approx(expected)


def test_more_trials_raise_the_bar_and_lower_the_dsr():
    bars = [expected_max_sharpe(VAR, n) for n in (2, 10, 100, 1000)]
    dsrs = [deflated_sharpe(SR, VAR, n, 1250, -3, 10) for n in (2, 10, 100, 1000)]
    assert bars == sorted(bars) and dsrs == sorted(dsrs, reverse=True)


def test_negative_skew_and_fat_tails_lower_the_psr():
    assert probabilistic_sharpe(SR, 0.1, 1250, -3, 10) < probabilistic_sharpe(SR, 0.1, 1250, 0, 3)


def test_sample_moments():
    rng = np.random.default_rng(0)
    skew, kurt = moments(rng.normal(size=200_000))
    assert skew == pytest.approx(0.0, abs=0.02) and kurt == pytest.approx(3.0, abs=0.05)
    r = np.array([0.01, -0.02, 0.03, 0.0])
    assert sharpe_ratio(r) == pytest.approx(r.mean() / r.std(ddof=1))


def test_pbo_is_low_for_a_persistently_superior_strategy():
    rng = np.random.default_rng(1)
    perf = rng.normal(0, 0.01, (400, 10))
    perf[:, 3] += 0.004  # one strategy genuinely better in every period
    assert probability_of_backtest_overfitting(perf, n_groups=8)["pbo"] < 0.05


def test_pbo_is_near_one_half_for_pure_noise():
    rng = np.random.default_rng(2)
    result = probability_of_backtest_overfitting(rng.normal(0, 0.01, (400, 20)), n_groups=10)
    assert result["n_splits"] == math.comb(10, 5)
    assert 0.3 < result["pbo"] < 0.7


def test_pbo_is_high_when_in_sample_winners_reverse():
    rng = np.random.default_rng(3)
    perf = rng.normal(0, 0.002, (200, 6))
    half = 100
    for j in range(6):  # strategy j is good in one half and bad in the other
        sign = 1 if j % 2 == 0 else -1
        perf[:half, j] += sign * 0.003
        perf[half:, j] -= sign * 0.003
    assert probability_of_backtest_overfitting(perf, n_groups=2)["pbo"] == 1.0


@pytest.mark.parametrize(
    "call",
    [
        lambda: expected_max_sharpe(VAR, 1),
        lambda: expected_max_sharpe(-1.0, 10),
        lambda: probabilistic_sharpe(0.1, 0.0, 1, 0, 3),
        lambda: probability_of_backtest_overfitting(np.zeros((10, 3)) + 1e-3, n_groups=3),
        lambda: probability_of_backtest_overfitting(np.zeros((10, 1)), n_groups=2),
        lambda: sharpe_ratio([1.0]),
    ],
)
def test_bad_inputs_are_rejected(call):
    with pytest.raises(ConfigurationError):
        call()
