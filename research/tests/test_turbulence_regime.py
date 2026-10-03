"""research/strategies/turbulence_regime.py."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from engine.core.exceptions import ConfigurationError
from research.strategies.turbulence_regime import basket_closes, calm_by_date, turbulence_index


def _returns(n=400, rho=-0.6, seed=1) -> pd.DataFrame:
    """Two assets with correlation rho (stocks vs bonds, say)."""
    rng = np.random.default_rng(seed)
    cov = 0.01**2 * np.array([[1.0, rho], [rho, 1.0]])
    values = rng.multivariate_normal([0, 0], cov, n)
    index = pd.date_range("2016-01-04", periods=n, freq="B", tz="UTC")
    return pd.DataFrame(values, columns=["stocks", "bonds"], index=index)


def test_index_is_the_mahalanobis_distance_from_strictly_prior_days():
    r = _returns()
    turb = turbulence_index(r, lookback=250)
    t = 300
    hist = r.iloc[t - 250 : t].to_numpy()
    diff = r.iloc[t].to_numpy() - hist.mean(axis=0)
    expected = diff @ np.linalg.inv(np.cov(hist, rowvar=False)) @ diff
    assert turb.iloc[t] == pytest.approx(expected)
    assert turb.iloc[:250].isna().all()


def test_falling_together_is_far_more_turbulent_than_the_usual_pattern():
    """Same size moves, two shapes. With rho = -0.6, stocks down / bonds
    up is the normal pattern; both down is the correlation break."""
    r = _returns()
    usual, broken = r.copy(), r.copy()
    usual.iloc[-1] = [-0.015, 0.015]
    broken.iloc[-1] = [-0.015, -0.015]
    d_usual = turbulence_index(usual, 250).iloc[-1]
    d_broken = turbulence_index(broken, 250).iloc[-1]
    assert d_broken > 3 * d_usual


def _closes(r: pd.DataFrame) -> pd.DataFrame:
    return 100 * np.exp(r.cumsum())


def test_calm_share_tracks_the_quantile_on_stationary_data():
    regime = calm_by_date(
        _closes(_returns(900)), lookback=250, quantile=0.9, threshold_lookback=250
    )
    share = sum(regime.values()) / len(regime)
    assert 0.8 < share < 0.97


def test_lag1_never_sees_the_session_it_is_applied_to():
    closes = _closes(_returns(700))
    shocked = closes.copy()
    target = shocked.index[600]
    shocked.loc[target:, "stocks"] *= 0.9  # a 10% gap on one day, persisting
    shocked.loc[target:, "bonds"] *= 0.97
    same_day = calm_by_date(shocked, lag=0)
    assert same_day[target.date()] is False  # lag 0 knows on the day itself
    before = calm_by_date(closes, lag=1)
    after = calm_by_date(shocked, lag=1)
    assert {d: v for d, v in after.items() if d <= target.date()} == {
        d: v for d, v in before.items() if d <= target.date()
    }


def test_basket_closes_inner_joins_sessions():
    idx = pd.date_range("2024-01-02 14:30", periods=3, freq="1D", tz="UTC")
    a = pd.DataFrame({"open": 1.0, "high": 1.0, "low": 1.0, "close": [1.0, 2.0, 3.0]}, index=idx)
    b = a.iloc[[0, 2]] * 10
    out = basket_closes({"A": a, "B": b})
    assert len(out) == 2 and list(out.columns) == ["A", "B"]
    with pytest.raises(ConfigurationError):
        basket_closes({"A": a})


@pytest.mark.parametrize(
    "kwargs", [{"quantile": 1.0}, {"quantile": 0.0}, {"threshold_lookback": 1}, {"lag": 2}]
)
def test_validation(kwargs):
    with pytest.raises(ConfigurationError):
        calm_by_date(_closes(_returns(400)), **kwargs)


def test_lookback_must_exceed_the_basket_size():
    with pytest.raises(ConfigurationError):
        turbulence_index(_returns(), lookback=2)
