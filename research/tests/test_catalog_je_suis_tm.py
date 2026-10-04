"""research/catalog/je_suis_tm.py -- je-suis-tm/quant-trading's trades."""

from __future__ import annotations

from datetime import datetime, timedelta

import numpy as np
import pandas as pd
import pytest

from engine.core.exceptions import ConfigurationError
from research.catalog.je_suis_tm import (
    awesome_trades,
    bollinger_bands,
    bollinger_w_trades,
    dual_thrust_range,
    dual_thrust_trades,
    eg_method,
    heikin_ashi_candles,
    heikin_ashi_trades,
    london_breakout_trades,
    macd_crossover,
    pair_trading_signals,
    psar_script,
    rsi_head_shoulders_trades,
    rsi_overbought_oversold,
    rsi_script,
    shooting_star_conditions,
    shooting_star_trades,
    smma,
)


def _ohlc(closes, spread=0.5):
    c = np.asarray(closes, dtype=float)
    o = np.concatenate([[c[0]], c[:-1]])
    return pd.DataFrame(
        {"open": o, "high": np.maximum(o, c) + spread, "low": np.minimum(o, c) - spread, "close": c}
    )


# ---------------------------------------------------------------- MACD


def test_macd_uses_simple_averages_and_goes_long_or_flat():
    closes = np.concatenate([np.linspace(100, 120, 40), np.linspace(120, 95, 40)])
    out = macd_crossover(closes, 5, 10)
    s = pd.Series(closes)
    expected = np.where(
        s.rolling(5, min_periods=1).mean() >= s.rolling(10, min_periods=1).mean(), 1, 0
    )
    assert (out.positions.to_numpy()[5:] == expected[5:]).all()
    assert (out.positions.to_numpy()[:5] == 0).all()
    assert set(np.unique(out.positions)) <= {0, 1}
    assert out.signals.sum() == out.positions.iloc[-1] - out.positions.iloc[0]
    with pytest.raises(ConfigurationError):
        macd_crossover(closes, 10, 5)


# ---------------------------------------------------------------- Awesome


def test_awesome_trades_long_while_ao_positive_and_flat_once_negative():
    closes = np.concatenate([np.linspace(100, 140, 80), np.linspace(140, 90, 80)])
    df = _ohlc(closes)
    out = awesome_trades(df)
    median = (df.high + df.low) / 2
    ao = median.rolling(5).mean() - median.rolling(34).mean()
    pos = out.positions.to_numpy()
    assert set(np.unique(pos)) <= {0, 1}  # the cumsum clamps keep it long-or-flat
    assert pos[70] == 1 and ao.iloc[70] > 0
    assert pos[-1] == 0 and ao.iloc[-1] < 0


# ---------------------------------------------------------------- Heikin-Ashi


def test_heikin_ashi_candle_formulas():
    df = _ohlc([10, 11, 10.5, 12, 11])
    ha = heikin_ashi_candles(df)
    o, h, lo, c = (df[k].to_numpy() for k in ("open", "high", "low", "close"))
    assert ha.ha_close.to_numpy() == pytest.approx((o + c + h + lo) / 4)
    assert ha.ha_open.iloc[0] == o[0]
    assert ha.ha_open.iloc[2] == pytest.approx((ha.ha_open.iloc[1] + ha.ha_close.iloc[1]) / 2)
    assert (ha.ha_high >= np.maximum(ha.ha_open, ha.ha_close)).all()


def test_heikin_ashi_buys_after_strong_red_candles_up_to_the_limit():
    # A steady decline with no upper wicks makes red HA candles growing in body.
    closes = 100 * 0.97 ** np.arange(30)
    df = pd.DataFrame({"open": closes * 1.0, "close": closes * 0.97})
    df["high"], df["low"] = df["open"], df["close"] * 0.999
    out = heikin_ashi_trades(df, stls=3)
    assert out.positions.max() <= 3 and (out.signals == 1).sum() >= 1
    assert out.positions.iloc[-1] == 3


# ---------------------------------------------------------------- PSAR


def test_psar_script_quirks_and_trend_following():
    up = _ohlc(np.linspace(100, 130, 30), spread=0.2)
    out = psar_script(up)
    assert out.positions.iloc[0] == 1  # real sar is 0 at bar 0: 0 < close
    assert (out.positions.iloc[5:] == 1).all()
    assert (out.af <= 0.2 + 1e-12).all() and out.af.max() == pytest.approx(0.2)
    down = _ohlc(np.linspace(130, 100, 30), spread=0.2)
    assert (psar_script(down).positions.iloc[5:] == 0).all()


# ---------------------------------------------------------------- Bollinger W


def test_bollinger_bands_formula():
    p = np.linspace(1, 30, 30)
    b = bollinger_bands(p)
    s = pd.Series(p)
    assert b["mid"].iloc[-1] == pytest.approx(s.iloc[-20:].mean())
    assert b["upper"].iloc[-1] == pytest.approx(s.iloc[-20:].mean() + 2 * s.iloc[-20:].std())


def test_bollinger_w_fires_on_a_w_bottom_breakout_with_loose_tolerance():
    rng = np.random.default_rng(0)
    base = 100 + rng.normal(0, 0.2, 40)
    w = np.concatenate(
        [
            np.linspace(100, 96, 8),
            np.linspace(96, 100, 6),
            np.linspace(100, 96.3, 6),
            np.linspace(96.3, 104, 6),
        ]
    )
    out = bollinger_w_trades(np.concatenate([base, w]), period=30, alpha=1.5, beta=0.0)
    hits = np.flatnonzero(out.signals == 1)
    assert hits.size >= 1
    lnode, knode, jnode, mnode, inode = map(int, out.coordinates.iloc[hits[0]].split(","))
    assert lnode <= knode <= jnode < mnode <= inode == hits[0]


def test_bollinger_exit_when_bandwidth_collapses():
    rng = np.random.default_rng(0)
    base = 100 + rng.normal(0, 0.2, 40)
    w = np.concatenate(
        [
            np.linspace(100, 96, 8),
            np.linspace(96, 100, 6),
            np.linspace(100, 96.3, 6),
            np.linspace(96.3, 104, 6),
        ]
    )
    flat = np.full(30, 104.0)  # the band std falls to zero
    out = bollinger_w_trades(np.concatenate([base, w, flat]), period=30, alpha=1.5, beta=0.5)
    assert (out.signals == 1).any() and (out.signals == -1).any()
    assert out.positions.iloc[-1] == 0


# ---------------------------------------------------------------- RSI


def test_smma_and_rsi_follow_the_script():
    assert smma([2.0, 4.0, 6.0], 2) == pytest.approx([2.0, 3.0, 4.5])
    close = np.array([10, 11, 10.5, 11.5, 12, 11, 11.5, 12.5, 13, 12])
    out = rsi_script(close, 3)
    delta = np.diff(close)
    up, down = np.where(delta > 0, delta, 0), np.where(delta < 0, -delta, 0)
    with np.errstate(divide="ignore"):  # smma(down) starts at 0, as in the script
        rs = np.array(smma(up, 3)) / np.array(smma(down, 3))
    assert out == pytest.approx((100 - 100 / (1 + rs))[2:])
    assert out.size == close.size - 3


def test_rsi_overbought_oversold_positions():
    close = np.concatenate([np.linspace(100, 80, 30), np.linspace(80, 120, 30)])
    out = rsi_overbought_oversold(close)
    assert (out.positions[out.rsi < 30] == 1).all() and (out.positions[out.rsi > 70] == -1).all()


def _head_and_shoulders():
    lead = 10 + np.linspace(-0.5, 0.0, 40)
    pattern = [
        10.0,
        10.25,
        10.5,
        10.25,
        10.0,
        10.5,
        11.0,
        10.5,
        10.05,
        10.25,
        10.5,
        10.25,
        10.1,
        10.0,
        10.0,
        10.05,
        10.0,
        10.02,
        10.0,
        10.03,
        10.0,
        10.01,
        10.0,
        10.02,
        10.0,
    ]
    return np.concatenate([lead, pattern, [10.0, 10.0]])


def test_rsi_head_shoulders_shorts_on_the_pattern_and_covers_later():
    out = rsi_head_shoulders_trades(_head_and_shoulders())
    shorts = np.flatnonzero(out.signals == -1)
    assert shorts.size >= 1
    m, n, ll, j, k, o, i = map(int, out.coordinates.iloc[shorts[0]].split(","))
    c = out.close.to_numpy()
    assert c[j] == c[i - 25 : i].max()  # the head is the window's maximum
    assert c[n] - c[i] > 1.1 * 0.2 and c[j] - c[n] > 1.1 * 0.2  # shoulder rules
    assert m < n < ll <= j <= k <= o < i


# ---------------------------------------------------------------- Shooting star


def _star_frame():
    # Bar 3 is the star: bearish body 0.01 (below half the |mean| body), lower
    # shadow 0.001 (< 0.2 * body), upper shadow far above 2 * body, after two
    # non-falling closes; bar 4 confirms (lower high, lower close).
    rows = [
        (100, 101, 99.8, 100.8),
        (100.8, 102, 100.6, 101.8),
        (101.8, 103, 101.6, 102.5),
        (102.51, 106.0, 102.499, 102.5),
        (102.4, 102.6, 101.0, 101.2),
    ]
    rows += [(101.2, 101.5, 100.5, 101.0)] * 10
    return pd.DataFrame(rows, columns=["open", "high", "low", "close"])


def test_verbatim_shooting_star_confirms_with_the_next_bar():
    df = _star_frame()
    assert shooting_star_conditions(df).tolist()[3] == 1


def test_causal_shooting_star_signals_one_bar_later():
    df = _star_frame()
    causal = shooting_star_conditions(df, causal=True)
    assert causal.iloc[3] == 0 and causal.iloc[4] == 1


def test_shooting_star_short_is_covered_after_the_holding_period():
    out = shooting_star_trades(_star_frame(), holding_period=3)
    assert out.signals.iloc[3] == -1 and out.signals.iloc[6] == 1
    assert out.positions.iloc[-1] == 0


# ---------------------------------------------------------------- Dual Thrust


def _dual_thrust_data():
    days = pd.date_range("2024-01-01", periods=7, freq="D")
    daily = pd.DataFrame(
        {
            "high": [11, 12, 11.5, 12.5, 12, 13, 13],
            "low": [9, 10, 9.5, 10.5, 10, 11, 11],
            "close": [10, 11, 10.5, 11.5, 11, 12, 12],
        },
        index=days,
    )
    session = pd.date_range("2024-01-07 03:00", "2024-01-07 12:00", freq="h")
    prices = pd.Series([12.0, 12.5, 15.0, 15.2, 14.0, 9.0, 9.1, 9.0, 9.2, 9.3], index=session)
    return prices, daily


def test_dual_thrust_range_is_the_max_of_the_two_spans():
    _, daily = _dual_thrust_data()
    rng = dual_thrust_range(daily, rg=5)
    last5 = daily.iloc[2:7]
    expected = max(last5.high.max() - last5.close.min(), last5.close.max() - last5.low.min())
    assert rng.iloc[-1] == pytest.approx(expected)
    assert dual_thrust_range(daily, rg=5, causal=True).iloc[-1] == pytest.approx(rng.iloc[-2])


def test_dual_thrust_goes_long_flips_short_and_flattens_at_the_close():
    prices, daily = _dual_thrust_data()
    out = dual_thrust_trades(prices, daily)
    rng = dual_thrust_range(daily).iloc[-1]
    assert out.upper.iloc[0] == pytest.approx(12.0 + 0.5 * rng)
    assert out.lower.iloc[0] == pytest.approx(12.0 - 0.5 * rng)
    assert out.signals.iloc[2] == 1  # 15 breaks the upper band
    assert out.signals.iloc[5] == -2  # 9 breaks the lower band: flip
    assert out.positions.iloc[-1] == 0  # 12:00 flattens


# ---------------------------------------------------------------- London Breakout


def _london_day(prices_after_open):
    start = datetime(2024, 3, 4, 2, 0)
    tokyo = [(start + timedelta(minutes=m), 1.1000 + 0.0001 * (m % 5)) for m in range(60)]
    after = [
        (datetime(2024, 3, 4, 3, 0) + timedelta(minutes=m), p)
        for m, p in enumerate(prices_after_open)
    ]
    close = [(datetime(2024, 3, 4, 12, 0), prices_after_open[-1])]
    idx, vals = zip(*(tokyo + after + close), strict=True)
    return pd.Series(vals, index=pd.DatetimeIndex(idx))


def test_london_breakout_trades_a_break_and_exits_at_the_target():
    # Break at 3:01; the source checks stop/target only once the 30-minute
    # entry window has passed, so the jump at 3:35 is what closes it.
    path = [1.1002, 1.1006] + [1.1007] * 33 + [1.1070]
    s = _london_day(path)
    out = london_breakout_trades(s)
    assert out.signals.iloc[61] == 1  # 3:01: above the 1.1004 range high
    assert out.signals.iloc[60 + 35] == -1  # 3:35: beyond executed + risky_stop / 2
    assert (out.signals.iloc[62 : 60 + 30] == 0).all()  # no exit inside the window
    assert out.positions.iloc[-1] == 0


def test_london_breakout_skips_an_abnormal_break():
    s = _london_day([1.1002, 1.1200, 1.1201])  # overshoots by more than risky_stop
    assert (london_breakout_trades(s).signals == 0).all()


def test_london_breakout_flattens_at_the_close_hour():
    s = _london_day([1.1002, 1.1006, 1.1007])
    out = london_breakout_trades(s)
    assert out.positions.iloc[-2] == 1 and out.positions.iloc[-1] == 0


# ---------------------------------------------------------------- Pair trading


def test_eg_method_accepts_a_cointegrated_pair_and_rejects_walks():
    rng = np.random.default_rng(1)
    x = 50 + np.cumsum(rng.normal(0, 1, 300))
    y = 5 + 1.5 * x + rng.normal(0, 1, 300)
    ok, params, _ = eg_method(x, y)
    assert ok and params[1] == pytest.approx(1.5, abs=0.1)
    assert not eg_method(x, 50 + np.cumsum(np.random.default_rng(2).normal(0, 1, 300)))[0]


def test_pair_trading_trades_opposite_legs():
    rng = np.random.default_rng(3)
    x = 50 + np.cumsum(rng.normal(0, 1, 500))
    y = 5 + 1.5 * x + rng.normal(0, 2, 500)
    out = pair_trading_signals(x, y, bandwidth=250)
    assert (out.signals1 != 0).any()
    assert (out.signals2 == -out.signals1).all()
