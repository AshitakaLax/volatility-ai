"""Unit tests for research/optimization/money_market_yield.py -- the
EFFR-proxy haircut and floor, in isolation from the full backtest loop
(see test_cash_yield_accrual.py for the integration-level tests through
OptimizationController)."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from engine.data.external_index_series import ExternalIndexSeries
from research.optimization.money_market_yield import (
    FLOOR_PCT,
    SPAXX_EXPENSE_RATIO_PCT,
    smart_cash_yield_pct_for_index,
)


def _series(dates: list[str], values: list[float]) -> ExternalIndexSeries:
    index = pd.DatetimeIndex([pd.Timestamp(d, tz="UTC") for d in dates])
    return ExternalIndexSeries(pd.DataFrame({"close": values}, index=index))


def test_no_series_returns_the_floor_everywhere():
    """series=None -- the file was never fetched -- must not crash a
    sweep; every bar gets the floor, matching implied_vol_signal's
    'exact no-op when missing' shape."""
    index = pd.date_range("2020-01-01", periods=5, freq="D", tz="UTC")
    out = smart_cash_yield_pct_for_index(None, index)
    assert np.all(out == FLOOR_PCT)


def test_normal_rate_gets_the_expense_ratio_haircut():
    """A comfortably-above-floor EFFR value nets down by exactly the
    expense ratio, not clamped -- the floor must not eat real signal."""
    series = _series(["2026-09-01"], [3.88])
    index = pd.DatetimeIndex([pd.Timestamp("2026-09-15", tz="UTC")])
    out = smart_cash_yield_pct_for_index(series, index)
    assert out[0] == pytest.approx(3.88 - SPAXX_EXPENSE_RATIO_PCT)


def test_near_zero_rate_is_floored_not_negative():
    """The whole point of a 'smart MINIMUM': a near-zero-rate era (2020
    -2021 in reality) would go negative after the expense-ratio haircut
    without a floor. A real fund does not pass a negative yield on."""
    series = _series(["2020-06-01"], [0.05])  # EFFR near-zero, ZIRP era
    index = pd.DatetimeIndex([pd.Timestamp("2020-06-15", tz="UTC")])
    out = smart_cash_yield_pct_for_index(series, index)
    assert out[0] == FLOOR_PCT
    assert out[0] > 0, "a floored rate is still positive, never negative"


def test_before_the_series_starts_is_floored():
    """A date earlier than the series' first print (EFFR's own history
    starts 2000-07-04) is exactly as unknown as a missing file."""
    series = _series(["2010-01-01"], [0.15])
    index = pd.DatetimeIndex([pd.Timestamp("2005-01-01", tz="UTC")])
    out = smart_cash_yield_pct_for_index(series, index)
    assert out[0] == FLOOR_PCT


def test_after_the_series_ends_reuses_the_last_known_rate():
    """A data/external/ snapshot a few weeks stale should not suddenly
    fall back to the floor for 'today' -- ExternalIndexSeries.vectorized's
    own as-of semantics already give the right answer here."""
    series = _series(["2026-01-01", "2026-06-01"], [4.5, 3.9])
    index = pd.DatetimeIndex([pd.Timestamp("2026-09-01", tz="UTC")])
    out = smart_cash_yield_pct_for_index(series, index)
    assert out[0] == pytest.approx(3.9 - SPAXX_EXPENSE_RATIO_PCT)


def test_rate_varies_day_to_day_across_a_real_shaped_history():
    """The whole feature, in one assertion: two different eras in the
    same series must produce two different applied rates -- a flat
    number, smart or not, would fail this."""
    series = _series(
        ["2010-01-01", "2020-06-01", "2026-09-01"],
        [0.11, 0.06, 3.88],  # a rough ZIRP-era-then-hiking-era shape
    )
    index = pd.DatetimeIndex(
        [
            pd.Timestamp("2015-01-01", tz="UTC"),  # reads the 2010 print
            pd.Timestamp("2026-09-15", tz="UTC"),  # reads the 2026 print
        ]
    )
    out = smart_cash_yield_pct_for_index(series, index)
    assert out[0] == FLOOR_PCT  # 0.11 - 0.42 < 0 -> floored
    assert out[1] == pytest.approx(3.88 - SPAXX_EXPENSE_RATIO_PCT)
    assert out[1] > out[0], "the hiking-era rate must exceed the floored ZIRP-era one"
