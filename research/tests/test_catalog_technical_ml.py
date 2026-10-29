"""research/catalog/technical_ml.py -- technical rules, ML pipeline and text."""

from __future__ import annotations

import numpy as np
import pytest

from engine.core.exceptions import ConfigurationError
from research.catalog.technical_ml import (
    SentenceClassifier,
    atr,
    average_uniqueness,
    causal_impact,
    emd,
    emd_scalper_positions,
    event_sentiment_trades,
    indicator_matrix,
    instantaneous_phase,
    lag_feature_matrix,
    lexicon_score,
    multi_timeframe_trend,
    pessimism_index,
    random_forest_signal,
    rank_select,
    relevance_labels,
    sequential_bootstrap,
    supertrend,
    tetlock_positions,
    train_ranker,
    volatility_expansion_breakout,
    williams_breakout,
    zweig_breadth_thrust,
)


def _ohlc(close):
    c = np.asarray(close, float)
    return c * 1.01, c * 0.99, c


def test_atr_and_supertrend_follow_the_trend():
    up = np.linspace(100, 150, 60)
    down = np.linspace(150, 100, 60)
    h, lo, c = _ohlc(np.r_[up, down])
    a = atr(h, lo, c, 10)
    assert np.isnan(a[8]) and a[20] > 0
    st = supertrend(h, lo, c, 10, 3.0)
    assert st["positions"][50] == 1 and st["positions"][-1] == 0
    assert (st["line"][20:55] < c[20:55]).all()


def test_breakouts_and_multi_horizon_trend():
    o = np.full(5, 100.0)
    h = np.array([102, 101, 104, 100.5, 103.0])
    lo = np.array([98, 99, 99, 99.5, 99.0])
    assert williams_breakout(o, h, lo, 0.5).tolist() == [False, False, True, False, True]
    rng = np.random.default_rng(0)
    flat = 100 + 0.1 * rng.normal(size=80)
    burst = flat[-1] + np.cumsum(np.abs(rng.normal(1.0, 2.0, 30)))
    hh, ll, cc = np.r_[flat, burst] + 0.5, np.r_[flat, burst] - 0.5, np.r_[flat, burst]
    hh[80:] += np.linspace(0, 5, 30)
    ll[80:] -= np.linspace(0, 5, 30)
    pos = volatility_expansion_breakout(hh, ll, cc, 20, 14, 1.1)
    assert pos[:80].sum() == 0 and pos[-1] == 1
    trend = np.exp(np.linspace(0, 1, 400))
    assert (
        multi_timeframe_trend(trend)[-1] == 1
        and multi_timeframe_trend(trend, mode="average")[-1] == 1
    )
    with pytest.raises(ConfigurationError):
        multi_timeframe_trend(trend, mode="x")


def test_breadth_thrust_fires_once_on_a_washout_and_recovery():
    adv = np.r_[np.full(15, 300), np.full(10, 2500), np.full(10, 1500)]
    dec = np.r_[np.full(15, 2700), np.full(10, 500), np.full(10, 1500)]
    out = zweig_breadth_thrust(adv, dec)
    assert out["signal"].sum() == 1 and out["ema"][14] < 0.4


def test_ranker_random_forest_and_bootstrap():
    rng = np.random.default_rng(1)
    dates, n = 60, 10
    x = rng.normal(size=(dates * n, 3))
    y = 0.02 * x[:, 0] + 0.002 * rng.normal(size=dates * n)
    groups = [n] * dates
    assert set(relevance_labels(y, groups)) == {0, 1, 2, 3, 4}
    model = train_ranker(x, y, groups)
    test_x = rng.normal(size=(n, 3))
    w = rank_select(model, test_x, 3)
    assert w.sum() == pytest.approx(1.0) and np.argmax(test_x[:, 0]) in np.flatnonzero(w)
    ret = np.where(np.arange(500) % 2 == 0, 0.01, -0.01) + 0.001 * rng.normal(size=500)
    close = 100 * np.cumprod(1 + ret)
    feats, labels = lag_feature_matrix(close)
    assert feats.shape[0] == labels.shape[0]
    rf = random_forest_signal(close, 300)
    assert rf["hit_rate"] > 0.9
    ind = indicator_matrix(6, [(0, 2), (1, 3), (4, 5)])
    u = average_uniqueness(ind)
    assert u[2] == 1.0 and u[0] < 1.0
    draws = sequential_bootstrap(ind, 300, rng=0)
    assert np.bincount(draws, minlength=3)[2] > np.bincount(draws, minlength=3)[0]


def test_causal_impact_detects_an_intervention():
    rng = np.random.default_rng(2)
    x = np.cumsum(rng.normal(size=150))
    y = 2.0 + 0.8 * x + 0.3 * rng.normal(size=150)
    y[100:] += 3.0
    out = causal_impact(y, x, 100)
    assert out["effect"].mean() == pytest.approx(3.0, abs=0.8) and out["significant"]
    none = causal_impact(2.0 + 0.8 * x + 0.3 * rng.normal(size=150), x, 100)
    assert abs(none["effect"].mean()) < 1.0


def test_text_scoring_and_event_trades():
    s = lexicon_score("Profit growth was strong, not weak; no losses this quarter")
    assert s["positive"] > s["negative"]
    assert lexicon_score("record loss and a lawsuit")["negative"] == 2
    pess = pessimism_index(["markets fell on recession risk", "strong gains"])
    assert pess[0] > pess[1] == 0
    p = np.r_[np.full(60, 0.01), [0.2], np.full(10, 0.01)]
    pos = tetlock_positions(p, window=60, z=1.5, wait=2, hold=3)
    assert pos[63:66].tolist() == [1, 1, 1] and pos[:63].sum() == 0
    clf = SentenceClassifier().fit(
        [
            "revenue beat expectations",
            "profit surged to a record",
            "the company missed estimates",
            "shares plunged on fraud",
            "the meeting is on tuesday",
            "the report was filed",
        ],
        [1, 1, -1, -1, 0, 0],
    )
    sc = clf.score(["profit beat expectations", "fraud and missed estimates"])
    assert sc[0] > 0 > sc[1]
    r = np.full(100, 0.001)
    r[11:16] = 0.02
    out = event_sentiment_trades([10, 50], [0.9, -0.5], r, hold=5)
    assert len(out["trades"]) == 1 and out["car"] > 0


def test_emd_separates_two_tones():
    t = np.arange(512)
    fast, slow = np.sin(2 * np.pi * t / 16), 2 * np.sin(2 * np.pi * t / 128)
    imfs = emd(fast + slow + 0.01 * t)
    assert len(imfs) >= 3
    assert np.corrcoef(imfs[0], fast)[0, 1] > 0.9
    phase = instantaneous_phase(fast)
    assert phase.min() >= -np.pi and phase.max() <= np.pi
    prices = np.exp(0.01 * (fast + slow)[:200])
    pos = emd_scalper_positions(prices, window=128, imf_index=0)
    assert set(np.unique(pos)) <= {0.0, 1.0} and pos[128:].sum() > 0
