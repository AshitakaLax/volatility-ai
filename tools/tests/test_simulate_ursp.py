"""tools/simulate_ursp.py -- the 2x daily-reset formula, its costs, the
bad-print clip, calibration and the splice, on synthetic inputs (no
network)."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from tools import simulate_ursp as S


def _rsp(n=300, seed=3) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    idx = pd.bdate_range("2020-01-02", periods=n)
    close = 50 * np.exp(np.cumsum(0.01 * rng.standard_normal(n)))
    opn = close * (1 + 0.002 * rng.standard_normal(n))
    high = np.maximum(opn, close) * (1 + 0.004 * rng.random(n))
    low = np.minimum(opn, close) * (1 - 0.004 * rng.random(n))
    return pd.DataFrame(
        {
            "open": opn,
            "high": high,
            "low": low,
            "close": close,
            "volume": rng.integers(10_000, 90_000, n).astype(float),
            "adjclose": close,
        },
        index=idx,
    )


def test_close_to_close_is_twice_the_index_less_the_daily_drag():
    rsp = S.adjusted(_rsp(), clean=False)
    rate = pd.Series(0.03, index=pd.date_range("2019-12-01", "2021-06-30"))
    sim = S.simulate(rsp, rate, spread=0.01)
    r_sim = sim["close"].pct_change().iloc[1:].to_numpy()
    r_rsp = rsp["close"].pct_change().iloc[1:].to_numpy()
    days = rsp.index.to_series().diff().dt.days.iloc[1:].to_numpy()
    drag = (0.03 + 0.01) * days / 360 + S.ER_URSP * days / 365 - 2 * S.ER_RSP * days / 365
    np.testing.assert_allclose(r_sim, 2 * r_rsp - drag, rtol=1e-10, atol=1e-12)


def test_intraday_prices_keep_their_order():
    sim = S.simulate(
        S.adjusted(_rsp(), clean=False),
        pd.Series(0.02, index=pd.date_range("2019-12-01", "2021-06-30")),
        0.0,
    )
    assert (sim["high"] >= sim[["open", "close"]].max(axis=1) - 1e-9).all()
    assert (sim["low"] <= sim[["open", "close"]].min(axis=1) + 1e-9).all()


def test_the_bad_print_clip_touches_only_absurd_extremes():
    raw = _rsp()
    raw.iloc[100, raw.columns.get_loc("low")] = raw["close"].iloc[100] * 0.4  # a Flash-Crash print
    clean, kept = S.adjusted(raw), S.adjusted(raw, clean=False)
    changed = clean.index[(clean[["low", "high"]] != kept[["low", "high"]]).any(axis=1)]
    assert list(changed) == [raw.index[100]]
    assert clean["low"].iloc[100] > raw["close"].iloc[100] * 0.85


def test_calibration_recovers_a_known_spread_and_the_splice_starts_at_the_real_fund():
    raw = _rsp()
    rsp = S.adjusted(raw, clean=False)
    rate = pd.Series(0.04, index=pd.date_range("2019-12-01", "2021-06-30"))
    truth = S.simulate(rsp, rate, spread=0.015)
    real_idx = rsp.index[-60:]
    ursp = truth.loc[real_idx].copy() * 0.5  # a different price level, same returns
    ursp["volume"] = raw["volume"].loc[real_idx] * 0.002
    ursp["adjclose"] = ursp["close"]
    assert S.calibrate_spread(rsp, ursp, rate) == pytest.approx(0.015, abs=1e-6)
    out = S.splice(truth, raw, ursp)
    assert (out["source"].iloc[:-60] == "simulated").all() and (
        out["source"].iloc[-60:] == "actual"
    ).all()
    np.testing.assert_allclose(out["close"].iloc[-60:].to_numpy(), ursp["close"].to_numpy())
    # the simulated history ends where the real fund begins (returns preserved)
    r_hist = out["close"].iloc[:-59].pct_change().iloc[1:].to_numpy()
    np.testing.assert_allclose(
        r_hist, truth["close"].iloc[: len(out) - 59].pct_change().iloc[1:].to_numpy()
    )
    assert out["volume"].iloc[:-60].median() == pytest.approx(
        (raw["volume"] * 0.002).iloc[:-60].median(), rel=1e-9
    )


def test_minute_bars_aggregate_exactly_to_the_daily_bars():
    rng = np.random.default_rng(0)
    n_days = 3
    o = 100 + rng.standard_normal((n_days, 390)).cumsum(axis=1) * 0.05
    lib = {
        "pos": {},
        "o": o,
        "h": o + 0.02,
        "l": o - 0.02,
        "c": o + 0.01,
        "share": np.full((n_days, 390), 1 / 390),
    }
    lib["DO"], lib["DH"], lib["DL"], lib["DC"] = (
        o[:, 0],
        lib["h"].max(1),
        lib["l"].min(1),
        lib["c"][:, -1],
    )
    rng_ = lib["DH"] - lib["DL"]
    lib["u"], lib["v"] = (lib["DO"] - lib["DL"]) / rng_, (lib["DC"] - lib["DL"]) / rng_
    daily = pd.DataFrame(
        {
            "open": [10.0, 11.0],
            "high": [10.6, 11.2],
            "low": [9.7, 10.1],
            "close": [10.4, 10.3],
            "volume": [39_000, 78_000],
        },
        index=pd.to_datetime(["2005-03-01", "2005-03-02"]),
    )
    bars = S.minute_bars(daily, lib, seed=1)
    et = bars.index.tz_convert("America/New_York")
    g = bars.groupby(et.normalize().tz_localize(None))
    back = pd.DataFrame(
        {
            "open": g["open"].first(),
            "high": g["high"].max(),
            "low": g["low"].min(),
            "close": g["close"].last(),
        }
    )
    np.testing.assert_allclose(back.to_numpy(), daily[["open", "high", "low", "close"]].to_numpy())
    assert et[0].hour == 9 and et[0].minute == 30 and len(bars) == 780
    assert bars["volume"].dtype.kind == "i"
