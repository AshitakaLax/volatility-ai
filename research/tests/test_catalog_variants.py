"""The unbuilt variants from docs/algorithm_ledger.md's catalog
cross-reference: R1 (SMA regime), MR3 (Engle-Granger + Kalman hedge ratio),
R4 (VIX bands), M6 (PSAR profit-only exit) and S5 (probability and
conformal sizing)."""

from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import date
from statistics import NormalDist

import numpy as np
import pandas as pd
import pytest

from engine.core.exceptions import ConfigurationError
from engine.execution.cost_models import ZeroCostModel
from research.strategies import trend_regimes
from research.strategies.grid_lifecycle import psar_profit_exits
from research.strategies.natr_regime import apply_lag
from research.strategies.pairs import (
    KalmanHedgeRatio,
    engle_granger,
    engle_granger_critical_values,
    spread_long_signal,
)
from research.strategies.position_sizing import (
    bet_size_from_probability,
    conformal_long_size,
    split_conformal_interval,
)
from research.strategies.vix_bands import bands_by_session, vix_band


def _daily(closes):
    closes = np.asarray(closes, dtype=float)
    idx = pd.bdate_range("2024-01-01", periods=closes.size)
    return pd.DataFrame(
        {"open": closes, "high": closes * 1.01, "low": closes * 0.99, "close": closes}, index=idx
    )


# ---------------------------------------------------------------- R1


def test_sma_flag_is_close_above_its_moving_average():
    closes = np.concatenate([np.linspace(100, 120, 30), np.linspace(120, 90, 30)])
    d = _daily(closes)
    flags = trend_regimes.sma_risk_on(d, window=10)
    sma = d["close"].rolling(10).mean()
    expected = (d["close"] > sma).iloc[9:]
    pd.testing.assert_series_equal(flags, expected)
    assert flags.iloc[5] and not flags.iloc[-1]


def test_sma_is_a_trend_method_and_a_step_down_regime():
    from tools.leverage_stepdown import REGIMES

    assert "sma" in trend_regimes.TREND_METHODS and "sma" in REGIMES


def test_sma_regime_is_applied_the_next_session():
    d = _daily(np.linspace(100, 140, 260) + np.sin(np.arange(260)) * 3)
    same = trend_regimes.risk_on_by_date(d, "sma", lag=0, window=50)
    assert trend_regimes.risk_on_by_date(d, "sma", lag=1, window=50) == apply_lag(same, 1)


def test_sma_window_is_validated():
    with pytest.raises(ConfigurationError):
        trend_regimes.sma_risk_on(_daily(np.arange(1, 30)), window=0)


# ---------------------------------------------------------------- MR3


def test_engle_granger_critical_values_tend_to_the_two_variable_table():
    cv = engle_granger_critical_values(10**9)
    assert (round(cv["1%"], 2), round(cv["5%"], 2), round(cv["10%"], 2)) == (-3.90, -3.34, -3.04)


def test_engle_granger_finds_a_planted_pair_and_rejects_independent_walks():
    rng = np.random.default_rng(0)
    x = np.cumsum(rng.normal(0, 1, 1500))
    y = 0.5 + 2.0 * x + rng.normal(0, 1, 1500)
    pair = engle_granger(y, x)
    assert pair["beta"] == pytest.approx(2.0, abs=0.05) and pair["cointegrated_5pct"]
    other = np.cumsum(np.random.default_rng(1).normal(0, 1, 1500))
    assert not engle_granger(other, x)["cointegrated_5pct"]


def test_kalman_steps_match_a_hand_written_filter():
    kf = KalmanHedgeRatio()
    obs = [(10.0, 4.0), (10.6, 4.2), (11.1, 4.5)]
    m, p = np.ones(2), np.ones((2, 2))
    q, r = np.eye(2) * 0.01**2, 0.001
    for i, (y, x) in enumerate(obs):
        if i > 0:
            p = p + q
        h = np.array([1.0, x])
        e = y - h @ m
        s = h @ p @ h + r
        k = p @ h / s
        m = m + k * e
        p = p - np.outer(k, h) @ p
        got_e, got_s = kf.update(y, x)
        assert (got_e, got_s) == pytest.approx((e, s))
    assert (kf.alpha, kf.beta) == pytest.approx(tuple(m))


def test_kalman_recovers_a_constant_hedge_ratio():
    rng = np.random.default_rng(2)
    x = 50 + np.cumsum(rng.normal(0, 0.5, 3000))
    y = 3.0 + 1.5 * x + rng.normal(0, 0.03, 3000)
    kf = KalmanHedgeRatio()
    for yi, xi in zip(y, x, strict=True):
        kf.update(yi, xi)
    assert kf.beta == pytest.approx(1.5, abs=0.05)
    assert kf.z is not None and math.isfinite(kf.z)


def test_long_only_spread_signal():
    assert spread_long_signal(-1.2, holding=False) == "open"
    assert spread_long_signal(-0.8, holding=False) == "none"
    assert spread_long_signal(-0.3, holding=True) == "hold"
    assert spread_long_signal(0.1, holding=True) == "close"
    with pytest.raises(ConfigurationError):
        spread_long_signal(0.0, False, entry=0.5, exit_=1.0)


# ---------------------------------------------------------------- R4


def test_vix_bands_follow_the_catalog_edges():
    assert [vix_band(v) for v in (12.0, 19.99, 20.0, 29.9, 30.0, 80.0)] == [0, 0, 1, 1, 2, 2]


def test_bands_apply_to_the_next_session():
    s = pd.Series(
        [15.0, 25.0, 35.0], index=pd.to_datetime(["2024-03-01", "2024-03-04", "2024-03-05"])
    )
    assert bands_by_session(s, lag=0) == {
        date(2024, 3, 1): 0,
        date(2024, 3, 4): 1,
        date(2024, 3, 5): 2,
    }
    assert bands_by_session(s, lag=1) == {date(2024, 3, 4): 0, date(2024, 3, 5): 1}


def test_vix_band_inputs_are_validated():
    with pytest.raises(ConfigurationError):
        vix_band(20.0, edges=(30.0, 20.0))
    with pytest.raises(ConfigurationError):
        bands_by_session(pd.Series([10.0]), lag=2)


# ---------------------------------------------------------------- M6


@dataclass
class _Lot:
    buy_price: float
    quantity: float


def test_psar_exit_waits_for_the_falling_phase():
    rising = _daily(np.linspace(100, 130, 40))
    lots = [_Lot(100.0, 10)]
    assert psar_profit_exits(lots, rising, 130.0, ZeroCostModel()) == []


def test_psar_exit_only_ever_returns_lots_the_guard_permits():
    closes = np.concatenate([np.linspace(100, 130, 30), np.linspace(130, 115, 8)])
    d = _daily(closes)
    winner, loser = _Lot(100.0, 10), _Lot(120.0, 10)
    assert psar_profit_exits([winner, loser], d, 115.0, ZeroCostModel()) == [winner]


# ---------------------------------------------------------------- S5


def test_bet_size_is_two_phi_z_minus_one():
    p = 0.7
    z = (p - 0.5) / math.sqrt(p * (1 - p))
    assert bet_size_from_probability(p) == pytest.approx(2 * NormalDist().cdf(z) - 1)
    assert bet_size_from_probability(0.5) == pytest.approx(0.0)
    assert bet_size_from_probability(0.3) == pytest.approx(-bet_size_from_probability(0.7))


def test_bet_size_rises_with_confidence_and_respects_the_floor():
    sizes = [bet_size_from_probability(p) for p in (0.55, 0.65, 0.8, 0.95)]
    assert sizes == sorted(sizes)
    assert bet_size_from_probability(0.6, min_probability=0.7) == 0.0


def test_split_conformal_quantile_is_exact():
    residuals = [0.1, -0.4, 0.2, 0.9, -0.3, 0.5, -0.7, 0.6, 0.8]
    # n = 9, alpha = 0.2: k = ceil(10 * 0.8) = 8 -> the 8th smallest |r| = 0.8
    assert split_conformal_interval(1.0, residuals, alpha=0.2) == pytest.approx((0.2, 1.8))
    # alpha = 0.05: k = ceil(9.5) = 10 > n -> an infinite interval
    low, high = split_conformal_interval(1.0, residuals, alpha=0.05)
    assert low == -math.inf and high == math.inf


def test_conformal_interval_covers_at_its_nominal_rate():
    rng = np.random.default_rng(3)
    calib = rng.normal(0, 1, 500)
    test = rng.normal(0, 1, 5000)
    low, high = split_conformal_interval(0.0, calib, alpha=0.1)
    assert ((test >= low) & (test <= high)).mean() == pytest.approx(0.9, abs=0.02)


def test_conformal_long_size_needs_the_whole_interval_above_zero():
    calib = [0.1] * 20
    assert conformal_long_size(0.5, calib, alpha=0.1) == 1.0
    assert conformal_long_size(0.05, calib, alpha=0.1) == 0.0
