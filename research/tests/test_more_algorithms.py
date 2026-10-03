"""Trend regimes, debounce, LPPLS, HRP and the VIX calculator."""

from __future__ import annotations

import math
from datetime import date

import numpy as np
import pandas as pd
import pytest

from engine.core.exceptions import ConfigurationError
from research.strategies import lppls, trend_regimes
from research.strategies.hrp import hrp_weights
from research.strategies.natr_regime import apply_lag, debounce
from research.strategies.vix_calculator import expiry_variance, vix


def _daily(n=300, seed=4, drift=0.0) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    close = 100 * np.exp(np.cumsum(rng.normal(drift, 0.015, n)))
    open_ = np.r_[100.0, close[:-1]]
    wick = np.abs(rng.normal(0, 0.006, n)) * close
    index = pd.date_range("2018-01-02", periods=n, freq="B", tz="UTC")
    return pd.DataFrame(
        {
            "open": open_,
            "high": np.maximum(open_, close) + wick,
            "low": np.minimum(open_, close) - wick,
            "close": close,
        },
        index=index,
    )


# ---------------------------------------------------------------- debounce
def test_debounce_holds_each_state_for_min_hold_sessions():
    days = [date(2024, 1, d) for d in (2, 3, 4, 5, 8, 9)]
    raw = dict(zip(days, [True, False, True, False, False, True], strict=True))
    assert list(debounce(raw, 3).values()) == [True, True, True, False, False, False]
    assert debounce(raw, 1) == raw


# ---------------------------------------------------------- trend regimes
class TestTrendRegimes:
    def test_macd_matches_its_definition(self):
        d = _daily()
        flags = trend_regimes.macd_risk_on(d)
        c = d["close"]
        line = c.ewm(span=12, adjust=False).mean() - c.ewm(span=26, adjust=False).mean()
        expected = (line > line.ewm(span=9, adjust=False).mean()).iloc[35:]
        pd.testing.assert_series_equal(flags, expected)

    def test_awesome_is_the_sign_of_sma5_minus_sma34_of_the_median(self):
        d = _daily()
        mid = (d["high"] + d["low"]) / 2
        expected = (mid.rolling(5).mean() - mid.rolling(34).mean() > 0).iloc[33:]
        pd.testing.assert_series_equal(trend_regimes.awesome_risk_on(d), expected)

    def test_psar_rises_in_an_uptrend_and_reverses_on_a_collapse(self):
        n = 40
        close = np.r_[np.linspace(100, 140, 30), np.linspace(139, 100, 10)]
        idx = pd.date_range("2024-01-02", periods=n, freq="B", tz="UTC")
        d = pd.DataFrame(
            {"open": close, "high": close + 0.5, "low": close - 0.5, "close": close}, index=idx
        )
        _, rising = trend_regimes.parabolic_sar(d)
        assert rising[5:30].all()
        assert not rising[-3:].any()

    def test_psar_agrees_with_talib_on_the_trend_side(self):
        talib = pytest.importorskip("talib")
        d = _daily(500)
        _, rising = trend_regimes.parabolic_sar(d)
        theirs = talib.SAR(d["high"].to_numpy(), d["low"].to_numpy(), 0.02, 0.2)
        their_rising = d["close"].to_numpy()[1:] > theirs[1:]
        assert np.mean(rising[1:][20:] == their_rising[20:]) > 0.95

    def test_heikin_ashi_confirmation_ignores_a_single_opposite_candle(self):
        close = np.r_[np.linspace(100, 120, 20), [116.0, 122.0], np.linspace(123, 130, 8)]
        idx = pd.date_range("2024-01-02", periods=len(close), freq="B", tz="UTC")
        o = np.r_[close[0], close[:-1]]
        d = pd.DataFrame(
            {
                "open": o,
                "high": np.maximum(o, close) + 0.1,
                "low": np.minimum(o, close) - 0.1,
                "close": close,
            },
            index=idx,
        )
        # Precondition, computed independently: exactly one bearish
        # Heikin-Ashi candle after the warm-up -- or this proves nothing.
        ha_close = (d["open"] + d["high"] + d["low"] + d["close"]).to_numpy() / 4
        ha_open = np.empty_like(ha_close)
        ha_open[0] = (o[0] + close[0]) / 2
        for k in range(1, len(close)):
            ha_open[k] = (ha_open[k - 1] + ha_close[k - 1]) / 2
        assert int((ha_close[5:] <= ha_open[5:]).sum()) == 1
        loose = trend_regimes.heikin_ashi_risk_on(d, confirm=1).iloc[5:]
        strict = trend_regimes.heikin_ashi_risk_on(d, confirm=3).iloc[5:]
        assert int((~loose).sum()) == 1
        assert strict.all()

    @pytest.mark.parametrize("method", trend_regimes.TREND_METHODS)
    def test_lag1_is_lag0_shifted_and_never_sees_its_own_session(self, method):
        d = _daily()
        same = trend_regimes.risk_on_by_date(d, method, lag=0)
        assert trend_regimes.risk_on_by_date(d, method, lag=1) == apply_lag(same, 1)
        shocked = d.copy()
        shocked.iloc[-1, shocked.columns.get_loc("close")] *= 0.5
        shocked.iloc[-1, shocked.columns.get_loc("low")] *= 0.5
        assert trend_regimes.risk_on_by_date(
            shocked, method, lag=1
        ) == trend_regimes.risk_on_by_date(d, method, lag=1)

    def test_validation(self):
        with pytest.raises(ConfigurationError):
            trend_regimes.risk_on_flags(_daily(), "ichimoku")
        with pytest.raises(ConfigurationError):
            trend_regimes.macd_risk_on(_daily(), fast=30, slow=26)


# ------------------------------------------------------------------ LPPLS
def _bubble(n=250, seed=0) -> np.ndarray:
    t = np.arange(n, dtype=float)
    dt = (n - 1 + 20) - t
    f = dt**0.5
    log_p = 5.0 - 0.05 * f + 0.004 * f * np.cos(8.0 * np.log(dt))
    return log_p + np.random.default_rng(seed).normal(0, 0.001, n)


class TestLppls:
    def test_recovers_a_planted_bubble(self):
        params = lppls.fit(_bubble())
        assert params["m"] == 0.5 and params["omega"] == 8.0 and params["tc_ahead"] == 20
        assert lppls.is_bubble(params)

    def test_confidence_separates_a_bubble_from_a_random_walk(self):
        bubble = lppls.confidence(_bubble(), 249)
        walks = [
            lppls.confidence(np.cumsum(np.random.default_rng(s).normal(0, 0.015, 250)), 249)
            for s in range(5)
        ]
        assert bubble >= 0.8
        assert np.mean(walks) < 0.4

    def test_regime_is_lagged_and_validated(self):
        d = _daily(320)
        same = lppls.risk_on_by_date(d, lag=0, step=10)
        assert lppls.risk_on_by_date(d, lag=1, step=10) == apply_lag(same, 1)
        with pytest.raises(ConfigurationError):
            lppls.risk_on_by_date(d, threshold=0)


# -------------------------------------------------------------------- HRP
class TestHrp:
    def test_two_independent_assets_get_inverse_variance_weights(self):
        rng = np.random.default_rng(2)
        r = pd.DataFrame({"a": rng.normal(0, 0.01, 4000), "b": rng.normal(0, 0.02, 4000)})
        w = hrp_weights(r)
        va, vb = r["a"].var(), r["b"].var()
        assert w["a"] == pytest.approx(vb / (va + vb))
        assert w.sum() == pytest.approx(1.0)

    def test_a_duplicated_asset_does_not_double_its_allocation(self):
        rng = np.random.default_rng(3)
        a = rng.normal(0, 0.01, 4000)
        r = pd.DataFrame({"a": a, "a_copy": a, "b": rng.normal(0, 0.01, 4000)})
        w = hrp_weights(r)
        assert w["a"] + w["a_copy"] == pytest.approx(w["b"], rel=0.05)

    def test_validation(self):
        with pytest.raises(ConfigurationError):
            hrp_weights(pd.DataFrame({"a": [0.01, 0.02, 0.03]}))


# -------------------------------------------------------------------- VIX
def _bs_chain(spot, vol, t, r, strikes):
    def n(x):
        return 0.5 * (1 + math.erf(x / math.sqrt(2)))

    rows = []
    for k in strikes:
        d1 = (math.log(spot / k) + (r + vol**2 / 2) * t) / (vol * math.sqrt(t))
        d2 = d1 - vol * math.sqrt(t)
        call = spot * n(d1) - k * math.exp(-r * t) * n(d2)
        put = k * math.exp(-r * t) * n(-d2) - spot * n(-d1)
        rows.append((k, call * 0.999, call * 1.001, put * 0.999, put * 1.001))
    return pd.DataFrame(rows, columns=["strike", "call_bid", "call_ask", "put_bid", "put_ask"])


class TestVix:
    strikes = np.arange(40.0, 251.0, 1.0)

    def test_flat_black_scholes_vol_comes_back_out(self):
        chain = _bs_chain(100.0, 0.25, 23 / 365, 0.02, self.strikes)
        assert math.sqrt(expiry_variance(chain, 23 / 365, 0.02)) == pytest.approx(0.25, rel=0.015)

    def test_two_expiries_interpolate_to_the_30_day_index(self):
        near = _bs_chain(100.0, 0.25, 23 / 365, 0.02, self.strikes)
        nxt = _bs_chain(100.0, 0.25, 37 / 365, 0.02, self.strikes)
        assert vix(near, 23, nxt, 37, 0.02) == pytest.approx(25.0, abs=0.4)

    def test_expiries_must_bracket_the_target(self):
        chain = _bs_chain(100.0, 0.25, 23 / 365, 0.02, self.strikes)
        with pytest.raises(ConfigurationError):
            vix(chain, 31, chain, 37, 0.02)
