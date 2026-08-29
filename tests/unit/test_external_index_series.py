"""Tests for ExternalIndexSeries.

As with src/event_calendar.py, the property that matters most is
scalar() (the live path) and vectorized() (the backtest path) agreeing
on every point -- otherwise the two execution paths could read a
different external-series value for the identical timestamp.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from src.exceptions import DataValidationError
from src.external_index_series import ExternalIndexSeries


def series(*rows: tuple[str, float]) -> pd.DataFrame:
    """rows of ('YYYY-MM-DD HH:MM' UTC, value)."""
    idx = pd.to_datetime([r[0] for r in rows], utc=True)
    return pd.DataFrame({"close": [r[1] for r in rows]}, index=idx)


def minute_index(start: str, n: int) -> pd.DatetimeIndex:
    return pd.date_range(start, periods=n, freq="1min", tz="UTC")


# --- basic as-of semantics ---


def test_none_before_the_first_print():
    s = ExternalIndexSeries(series(("2024-06-03 15:00", 20.0)))
    assert s.scalar(pd.Timestamp("2024-06-03 14:59", tz="UTC")) is None


def test_returns_the_value_at_an_exact_print():
    s = ExternalIndexSeries(series(("2024-06-03 15:00", 20.0)))
    assert s.scalar(pd.Timestamp("2024-06-03 15:00", tz="UTC")) == pytest.approx(20.0)


def test_holds_the_last_known_value_until_the_next_print():
    s = ExternalIndexSeries(series(("2024-06-03 15:00", 20.0), ("2024-06-03 16:00", 25.0)))
    assert s.scalar(pd.Timestamp("2024-06-03 15:30", tz="UTC")) == pytest.approx(20.0)
    assert s.scalar(pd.Timestamp("2024-06-03 16:00", tz="UTC")) == pytest.approx(25.0)
    assert s.scalar(pd.Timestamp("2024-06-03 20:00", tz="UTC")) == pytest.approx(25.0)


def test_an_out_of_order_series_is_sorted_at_construction():
    """A caller's CSV should not have to guarantee ordering."""
    s = ExternalIndexSeries(series(("2024-06-03 16:00", 25.0), ("2024-06-03 15:00", 20.0)))
    assert s.scalar(pd.Timestamp("2024-06-03 15:30", tz="UTC")) == pytest.approx(20.0)


def test_a_naive_timestamp_is_treated_as_utc():
    import datetime as dt

    s = ExternalIndexSeries(series(("2024-06-03 15:00", 20.0)))
    naive = dt.datetime(2024, 6, 3, 15, 30)
    assert s.scalar(naive) == pytest.approx(20.0)


# --- scalar/vectorized agreement ---


def test_scalar_and_vectorized_agree_on_every_bar():
    s = ExternalIndexSeries(
        series(("2024-06-03 15:00", 20.0), ("2024-06-03 15:37", 22.5), ("2024-06-03 16:20", 19.0))
    )
    idx = minute_index("2024-06-03 14:50", 100)
    vec = s.vectorized(idx)
    for i, ts in enumerate(idx):
        scalar_val = s.scalar(ts)
        vec_val = vec[i]
        if scalar_val is None:
            assert np.isnan(vec_val), f"mismatch at {ts}"
        else:
            assert vec_val == pytest.approx(scalar_val), f"mismatch at {ts}"


def test_vectorized_is_nan_before_the_first_print():
    s = ExternalIndexSeries(series(("2024-06-03 15:00", 20.0)))
    idx = minute_index("2024-06-03 14:00", 10)
    vec = s.vectorized(idx)
    assert np.isnan(vec[:60]).all() if len(vec) >= 60 else True
    assert np.isnan(vec[0])


def test_vectorized_requires_a_tz_aware_index():
    s = ExternalIndexSeries(series(("2024-06-03 15:00", 20.0)))
    naive = pd.date_range("2024-06-03 15:00", periods=5, freq="1min")
    with pytest.raises(DataValidationError, match="tz-aware"):
        s.vectorized(naive)


# --- construction validation ---


def test_empty_series_is_rejected():
    with pytest.raises(DataValidationError, match="empty"):
        ExternalIndexSeries(pd.DataFrame(columns=["close"]))


def test_naive_index_is_rejected():
    df = pd.DataFrame({"close": [20.0]}, index=pd.to_datetime(["2024-06-03 15:00"]))
    with pytest.raises(DataValidationError, match="tz-aware"):
        ExternalIndexSeries(df)


def test_missing_value_column_is_named():
    df = pd.DataFrame({"open": [20.0]}, index=pd.to_datetime(["2024-06-03 15:00"], utc=True))
    with pytest.raises(DataValidationError, match="close"):
        ExternalIndexSeries(df)


def test_a_timestamp_column_is_accepted_in_place_of_an_index():
    df = pd.DataFrame(
        {"timestamp": pd.to_datetime(["2024-06-03 15:00"], utc=True), "close": [20.0]}
    )
    s = ExternalIndexSeries(df)
    assert s.scalar(pd.Timestamp("2024-06-03 15:30", tz="UTC")) == pytest.approx(20.0)


def test_first_and_last_timestamp_properties():
    s = ExternalIndexSeries(series(("2024-06-03 15:00", 20.0), ("2024-06-05 15:00", 22.0)))
    assert s.first_timestamp == pd.Timestamp("2024-06-03 15:00", tz="UTC")
    assert s.last_timestamp == pd.Timestamp("2024-06-05 15:00", tz="UTC")
