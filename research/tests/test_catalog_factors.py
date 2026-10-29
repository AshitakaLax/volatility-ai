"""research/catalog/factors.py -- factor scores and event rules."""

from __future__ import annotations

import numpy as np
import pytest

from engine.core.exceptions import ConfigurationError
from research.catalog.factors import (
    accruals,
    activist_score,
    asset_growth,
    bab_betas,
    bab_weights,
    dividend_capture,
    event_drift_trades,
    factor_momentum,
    factor_regression,
    gross_profitability,
    industry_reversal,
    intangible_capital,
    intangibles_adjusted,
    low_pe_screen,
    market_model_car,
    momentum_12_1,
    net_issuance,
    operating_profitability,
    predict_index_changes,
    price_earnings_momentum,
    quality_score,
    quantile_weights,
    rank_z,
    residual_momentum,
    revision_score,
    shareholder_yield,
    size_with_quality,
    sue,
    two_by_three_factor,
    value_momentum_composite,
)


def test_rank_z_and_quantile_weights():
    z = rank_z([3.0, 1.0, np.nan, 2.0])
    assert np.isnan(z[2]) and z[0] > z[3] > z[1] and np.nanmean(z) == pytest.approx(0)
    w = quantile_weights([5, 4, 3, 2, 1], 0.4, long_short=True)
    assert w.tolist() == [0.5, 0.5, 0, -0.5, -0.5]


def test_fama_french_sort_and_regression():
    rng = np.random.default_rng(0)
    bm = rng.normal(size=400)
    cap = np.exp(rng.normal(size=400))
    nxt = 0.01 * bm + 0.001 * rng.normal(size=400)  # value pays
    out = two_by_three_factor(bm, cap, nxt)
    assert out["factor"] > 0 and set(out["portfolios"]) == {"SL", "SM", "SH", "BL", "BM", "BH"}
    f = rng.normal(size=(300, 2))
    y = 0.001 + f @ np.array([1.2, -0.5]) + 0.01 * rng.normal(size=300)
    reg = factor_regression(y, f)
    assert reg["betas"] == pytest.approx([1.2, -0.5], abs=0.05) and reg["r2"] > 0.9


def test_momentum_value_and_residual_momentum():
    rng = np.random.default_rng(1)
    p = np.exp(np.cumsum(rng.normal(0, 0.01, (300, 5)), axis=0))
    p[:, 0] *= np.exp(np.linspace(0, 0.5, 300))[:, None][:, 0]
    mom = momentum_12_1(p)
    assert np.argmax(mom) == 0
    with pytest.raises(ConfigurationError):
        momentum_12_1(p[:100])
    vm = value_momentum_composite(np.array([0.1, 0.2, 0.9, 0.5, 0.3]), p, q=0.4)
    assert vm["weights"].sum() == pytest.approx(1.0)
    f = rng.normal(size=(36, 1)) * 0.04
    r = f @ np.ones((1, 3)) + 0.01 * rng.normal(size=(36, 3))
    r[-12:-1, 2] += 0.02  # stock 2 drifts beyond its factor exposure
    assert np.argmax(residual_momentum(r, f)) == 2


def test_betting_against_beta():
    rng = np.random.default_rng(2)
    m = 0.01 * rng.normal(size=1300)
    true_beta = np.array([0.5, 1.0, 1.5])
    r = m[:, None] * true_beta + 0.005 * rng.normal(size=(1300, 3))
    b = bab_betas(r, m)
    assert b[0] < b[1] < b[2] and b[0] > 0.5 * 0.6 + 0.4 - 0.1
    w = bab_weights(b)
    assert w["long"] @ b == pytest.approx(1.0) and w["short"] @ b == pytest.approx(1.0)
    assert w["long_only"][0] == 1.0


def test_fundamental_scores():
    assert gross_profitability([100], [60], [200]).tolist() == [0.2]
    assert operating_profitability([100], [60], [10], [5], [50]).tolist() == [0.5]
    assert asset_growth([110], [100]) == pytest.approx([0.1])
    assert accruals([10], [6], [100]) == pytest.approx([0.04])
    assert net_issuance([100], [100]).tolist() == [0.0]
    assert shareholder_yield([2], [3], [1], [100], [1]) == pytest.approx([0.05])
    assert revision_score([2.2], [2.0], [100]) == pytest.approx([0.002])
    q = quality_score(
        {"gp": [0.3, 0.1, 0.2]},
        {"g": [0.1, 0.0, 0.05]},
        {"lev": [-0.1, -0.9, -0.5]},
        {"payout": [0.5, 0.0, 0.2]},
    )
    assert np.argmax(q["quality"]) == 0 and np.argmin(q["quality"]) == 1
    k = intangible_capital(np.ones((50, 1)) * 10, 0.15)
    assert k[0] == pytest.approx(10 / 0.15, rel=0.01)
    adj = intangibles_adjusted(
        [100], [200], np.ones((10, 1)) * 10, np.ones((10, 1)) * 20, [50], [300]
    )
    assert adj["adj_book_to_market"][0] > 0.5 and adj["intangibles"][0] > 0


def test_screens_and_rotations():
    w = low_pe_screen(
        [10, 10, 10, 10], [2, 1, -1, 3], [0.5, 0.5, 0.5, 2.0], [0.1, 0.1, 0.1, 0.1], q=0.25
    )
    assert w.tolist() == [1, 0, 0, 0]
    s = size_with_quality([1, 2, 100], [-1.0, 0.5, 0.5], q=0.34)
    assert s.tolist() == [0, 1, 0]
    rev = industry_reversal(
        [-0.5, -0.4, 0.3, 0.6, 0.1], [0.9, 0.1, 0.5, 0.2, 0.3], [0.1, 0.1, 0, 0, 0], q=0.4
    )
    assert rev.tolist() == [1, 0, 0, 0, 0]
    fr = np.array([[0.01, -0.01, 0.0]] * 12)
    assert factor_momentum(fr).tolist() == [1, 0, 0]
    assert factor_momentum(fr, top=2).tolist() == [0.5, 0, 0.5]


def test_earnings_events_and_event_studies():
    eps = np.r_[np.tile([1.0, 1.1, 0.9, 1.2], 4) + 0.01 * np.arange(16), [2.0]]
    s = sue(eps)
    assert np.isnan(s[10]) and s[-1] > 5
    rng = np.random.default_rng(3)
    p = np.exp(np.cumsum(rng.normal(0, 0.01, (300, 4)), axis=0))
    p[:, 1] *= np.exp(np.linspace(0, 0.4, 300))
    w = price_earnings_momentum(p, np.array([0.0, 3.0, 1.0, -1.0]), q=0.25)
    assert w[1] == 1.0
    m = 0.01 * rng.normal(size=400)
    r = 1.2 * m + 0.002 * rng.normal(size=400)
    r[300:305] += 0.02
    car = market_model_car(r, m, 300, window=(0, 4))
    assert car["car"] == pytest.approx(0.1, abs=0.02) and car["beta"] == pytest.approx(1.2, abs=0.1)
    with pytest.raises(ConfigurationError):
        market_model_car(r, m, 100)
    trades = event_drift_trades([10, 100], [2.0, 0.5], np.full(200, 0.001), threshold=1.0, hold=10)
    assert len(trades) == 1 and trades[0] == pytest.approx(1.001**10 - 1)
    assert activist_score(0.08, "seek board seats and a sale of the company") > activist_score(
        0.08, "investment"
    )


def test_index_and_dividend_events():
    caps = np.array([100, 90, 80, 70, 60, 50, 5])
    members = np.array([1, 1, 1, 0, 0, 0, 1], bool)
    out = predict_index_changes(caps, members, index_size=4, buffer=0.25)
    assert out["additions"].tolist() == [] and out["deletions"].tolist() == [6]
    out = predict_index_changes(caps, members, index_size=5, buffer=0.2)
    assert 3 in out["additions"]
    dc = dividend_capture([100.0], [99.1], [1.0])
    assert dc["return"][0] == pytest.approx(0.001) and dc["drop_ratio"][0] == pytest.approx(0.9)
