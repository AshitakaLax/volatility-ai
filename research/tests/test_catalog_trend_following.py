"""research/catalog/trend_following.py -- PyTrendFollow, the Turtle trade,
time-series momentum, Ghost Trader and the opening range breakout."""

from __future__ import annotations

import itertools

import numpy as np
import pandas as pd
import pytest

from engine.core.exceptions import ConfigurationError
from research.catalog.trend_following import (
    breakout_forecast,
    chunk_trades,
    ewmac_forecasts,
    ghost_trader,
    letianzj_turtle_trades,
    norm_forecast,
    orb_trade,
    pytrendfollow_position,
    stocks_in_play,
    talib_ema,
    talib_rsi,
    tsmom_weights,
    turtle_n,
    turtle_original_trades,
    weather_rule,
    weighted_forecast,
)


def _walk(n=400, seed=0, drift=0.0):
    rng = np.random.default_rng(seed)
    return 100 * np.exp(np.cumsum(rng.normal(drift, 0.01, n)))


def _ohlc(close, spread=0.005):
    c = np.asarray(close, dtype=float)
    return c * (1 + spread), c * (1 - spread), c


def test_ema_and_rsi_match_talib():
    talib = pytest.importorskip("talib")
    c = _walk(120, 3)
    assert talib_ema(c, 21) == pytest.approx(talib.EMA(c, 21), nan_ok=True)
    assert talib_rsi(c, 9) == pytest.approx(talib.RSI(c, 9), nan_ok=True)


# ---------------------------------------------------------------- S2 PyTrendFollow


def test_ewmac_is_fast_minus_slow_ewma_normalised_to_ten():
    p = pd.Series(_walk(600, 1, 0.001))
    f = ewmac_forecasts(p)
    assert list(f.columns) == ["ewmac8", "ewmac16", "ewmac32", "ewmac64"]
    assert f["ewmac8"].iloc[:31].isna().all() and f["ewmac8"].iloc[31:].notna().all()
    d = p * 10 / p.std()
    raw = d.ewm(span=16, min_periods=64).mean() - d.ewm(span=64, min_periods=64).mean()
    expect = (raw * 10 / raw.abs().mean()).clip(-20, 20)
    assert f["ewmac16"].to_numpy() == pytest.approx(expect.to_numpy(), nan_ok=True)
    assert f.abs().max().max() <= 20
    assert f["ewmac8"].iloc[-200:].mean() > 0  # an uptrend reads long


def test_norm_forecast_absolute_mean_and_clip():
    f = norm_forecast(pd.Series([1.0, -1.0, 1.0, -1.0, 50.0]))
    assert f.iloc[0] == pytest.approx(10 / (54 / 5)) and f.iloc[-1] == 20


def test_breakout_forecast_range_position():
    p = pd.Series(np.r_[np.linspace(100, 110, 40), np.full(40, 110.0)])
    b = breakout_forecast(p, 40, smooth=1)
    assert b.iloc[39] == pytest.approx(0.5)  # at the top of its range
    assert b.abs().max() <= 0.5 + 1e-12


def test_weather_rule_and_weighting():
    assert list(weather_rule([1, 2, 1, 1])[1:]) == [10, -10, pytest.approx(np.nan, nan_ok=True)]
    fc = pd.DataFrame({"a": [10.0, -10.0, 10.0], "b": [5.0, 5.0, -5.0]})
    w = weighted_forecast(fc, {"a": 1.0, "b": 1.0})
    raw = (fc["a"] + fc["b"]) / 2
    assert w.to_numpy() == pytest.approx((raw * 10 / raw.abs().mean()).to_numpy())


def test_position_scales_with_forecast_over_volatility():
    p = pd.Series(_walk(100, 2))
    pos = pytrendfollow_position(pd.Series(10.0, index=p.index), p, capital=1_000_000)
    vol = p.diff().ewm(span=36, min_periods=36).std()
    expect = np.around(10 * (0.125 / np.sqrt(252) * 1_000_000 / 10) / vol)
    assert pos.to_numpy() == pytest.approx(expect.to_numpy(), nan_ok=True)
    # exp(round(ln x, 1)): 100 and 104 both land on exp(4.6) = 99.48 -> 99
    assert list(chunk_trades([100, 104, -100, 110])) == [99.0, 99.0, -99.0, 110.0]


# ---------------------------------------------------------------- C-G5 Turtle


def _breakout_series():
    flat = 100 + 0.5 * np.sin(np.arange(30))
    up = 100.5 + np.arange(1, 16) * 0.8
    down = up[-1] - np.arange(1, 21) * 1.5
    return np.r_[flat, up, down]


def test_letianzj_turtle_enters_adds_and_exits_like_the_script():
    h, lo, c = _ohlc(_breakout_series(), 0.002)
    out = letianzj_turtle_trades(h, lo, c, equity=100_000)
    acts = [a for a in out["action"] if a]
    assert acts[0] == "enter" and "add" in acts
    assert sum(a == "add" for a in acts[: acts.index("exit") if "exit" in acts else None]) <= 3
    first = int(np.flatnonzero(out["action"] == "enter")[0])
    assert c[first] > h[first - 20 : first].max()
    # the script's 'low' is the max of highs: it exits on the first close
    # below the recent highest high, well before a true 10-day low
    quirk = out["action"].tolist().index("exit")
    textbook = letianzj_turtle_trades(h, lo, c, textbook_exit=True)["action"].tolist()
    assert quirk < textbook.index("exit") if "exit" in textbook else True
    assert out["shares"].iloc[quirk] == 0


def test_turtle_n_is_wilders_twenty_day_average():
    h, lo, c = _ohlc(_walk(60, 4))
    n = turtle_n(h, lo, c)
    tr = np.maximum.reduce([h[1:] - lo[1:], abs(h[1:] - c[:-1]), abs(lo[1:] - c[:-1])])
    assert np.isnan(n[:20]).all() and n[20] == pytest.approx(tr[:20].mean())
    assert n[21] == pytest.approx((19 * n[20] + tr[20]) / 20)


def test_turtle_original_system_two_pyramids_and_stops():
    c = np.r_[np.full(60, 100.0) + 0.2 * np.sin(np.arange(60)), 100 + np.arange(1, 21) * 1.0]
    c = np.r_[c, c[-1] - np.arange(1, 15) * 2.5]
    h, lo, _ = _ohlc(c, 0.003)
    trades = turtle_original_trades(h, lo, c, system=2)
    t = trades[0]
    assert t.direction == 1 and len(t.fills) == 4  # entry + three 1/2 N adds
    assert np.all(np.diff(t.fills) > 0)
    assert t.reason in {"stop", "exit"} and t.exit_bar is not None
    with pytest.raises(ConfigurationError):
        turtle_original_trades(h, lo, c, system=3)


def test_turtle_system_one_skips_the_breakout_after_a_winner():
    rng = np.random.default_rng(7)
    c = 100 * np.exp(np.cumsum(rng.normal(0.0005, 0.015, 900)))
    h, lo, _ = _ohlc(c, 0.004)
    s1 = turtle_original_trades(h, lo, c, system=1)
    no_filter_entries = 0
    hi20 = pd.Series(h).rolling(20).max().shift(1).to_numpy()
    lo20 = pd.Series(lo).rolling(20).min().shift(1).to_numpy()
    no_filter_entries = int(np.sum((h > hi20) | (lo < lo20)))
    assert 0 < len(s1) < no_filter_entries
    for a, b in itertools.pairwise(s1):
        assert b.entry_bar > a.exit_bar  # one position at a time


# ---------------------------------------------------------------- X7 TSMOM


def test_tsmom_sign_and_inverse_volatility():
    idx = pd.RangeIndex(400)
    r = pd.DataFrame(
        {"up": np.r_[np.full(300, 0.001), np.full(100, 0.002)], "dn": np.full(400, -0.001)},
        index=idx,
    )
    r["up"] += np.where(np.arange(400) % 2, 0.01, -0.01)
    r["dn"] += np.where(np.arange(400) % 2, 0.02, -0.02)
    w = tsmom_weights(r)
    assert w.iloc[:252].isna().all().all()
    assert (w["up"].iloc[260:] > 0).all() and (w["dn"].iloc[260:] < 0).all()
    assert abs(w["up"].iloc[-1]) > abs(w["dn"].iloc[-1])  # half the volatility, larger weight


# ---------------------------------------------------------------- C-RJ5 Ghost Trader


def test_ghost_trader_waits_for_the_ghost_to_lose():
    c = np.r_[np.linspace(100, 90, 25), np.linspace(90.5, 99, 18)]
    c = np.r_[c, [99.5, 100.2, 99.8, 100.9, 101.5, 102.0]]
    h, lo = c + 0.3, c - 0.3
    h[-6:] = c[-6:] + np.array([0.6, 0.9, 1.4, 1.6, 1.7, 1.8])
    out = ghost_trader(h, lo, c)
    pos = out["position"].to_numpy()
    first_signal = next(
        t
        for t in range(21, len(c))
        if out["ema_short"][t] > out["ema_long"][t] and out["rsi"][t] < 70 and h[t] > h[t - 1]
    )
    assert pos[first_signal] == 0  # the first signal only arms the ghost
    entries = np.flatnonzero(np.diff(np.r_[0, pos]) == 1)
    if entries.size:
        assert c[entries[0]] < c[first_signal]  # real long only below the ghost price


def test_ghost_trader_is_flat_before_the_lookback():
    h, lo, c = _ohlc(_walk(200, 9))
    pos = ghost_trader(h, lo, c)["position"].to_numpy()
    assert (pos[:20] == 0).all() and set(np.unique(pos)) <= {-1, 0, 1}


# ---------------------------------------------------------------- C-M2 ORB


def _session(opens, highs, lows, closes):
    return pd.DataFrame({"open": opens, "high": highs, "low": lows, "close": closes})


def test_orb_long_hits_the_ten_r_target():
    s = _session(
        [100, 101, 102, 110],
        [101.5, 102, 111, 112],
        [99.5, 100.8, 101.5, 109],
        [101, 101.8, 110.5, 111],
    )
    t = orb_trade(s, equity=100_000)
    assert t["side"] == 1 and t["entry"] == 101 and t["stop"] == 99.5
    assert t["target"] == pytest.approx(101 + 10 * 1.5) and t["reason"] == "close"
    assert t["shares"] == int(min(100_000 * 0.01 / 1.5, 4 * 100_000 / 101))
    t2 = orb_trade(s, equity=100_000, target_r=3)
    assert t2["reason"] == "target" and t2["exit"] == pytest.approx(105.5)


def test_orb_short_stop_doji_and_atr_mode():
    s = _session([100, 99, 99.5], [100.2, 100.5, 99.8], [98.9, 98.8, 99.2], [99, 99.4, 99.6])
    t = orb_trade(s, equity=50_000)
    assert t["side"] == -1 and t["reason"] == "stop" and t["exit"] == 100.2
    assert orb_trade(_session([100, 100], [101, 101], [99, 99], [100, 100]), 1e5) is None
    t3 = orb_trade(s, equity=50_000, stop_mode="atr", atr14=4.0, atr_fraction=0.05)
    assert t3["stop"] == pytest.approx(99 + 0.2)
    with pytest.raises(ConfigurationError):
        orb_trade(s, equity=1, stop_mode="atr")


def test_stocks_in_play_filter():
    df = pd.DataFrame(
        {
            "price": [10, 4, 20, 30],
            "adv14": [2e6, 2e6, 5e5, 3e6],
            "atr14": [1.0, 1.0, 1.0, 2.0],
            "opening_volume": [300, 300, 300, 150],
            "avg_opening_volume14": [100, 100, 100, 100],
        },
        index=list("ABCD"),
    )
    assert list(stocks_in_play(df).index) == ["A", "D"]
    assert list(stocks_in_play(df, top=1).index) == ["A"]
