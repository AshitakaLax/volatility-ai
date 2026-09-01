"""Tests for src/implied_vol_signal.py.

The property that matters most here is NO LOOKAHEAD. This signal is
derived from a series that moves during the session it is used in, so an
off-by-one publishes tomorrow's information into today's bars and makes
any backtest built on it worthless. That is tested directly rather than
inferred from the construction.

The scalar/vectorized agreement convention
(tests/unit/test_event_calendar.py, tests/unit/test_external_index_series.py)
is followed too: both paths must return the same value on every bar.
"""

from __future__ import annotations

from datetime import timedelta

import numpy as np
import pandas as pd
import pytest

from src.exceptions import DataValidationError
from src.external_index_series import ExternalIndexSeries
from src.fomc_calendar import EASTERN_TZ
from src.implied_vol_signal import (
    CHANGE_COLUMN,
    NO_SIGNAL,
    build_session_change_series,
    change_at,
    changes_for_index,
)


def _iv_bars(session_closes: dict[str, float]) -> pd.DataFrame:
    """Minute bars whose per-session LAST close is the given value."""
    rows = []
    for day, close in session_closes.items():
        base = pd.Timestamp(f"{day} 09:30", tz=EASTERN_TZ)
        # Two bars; the later one carries the session close.
        rows.append((base, close * 0.5))
        rows.append((base + timedelta(hours=6), close))
    idx = pd.DatetimeIndex([r[0] for r in rows]).tz_convert("UTC")
    return pd.DataFrame({"close": [r[1] for r in rows]}, index=idx)


def _series(session_closes: dict[str, float]) -> ExternalIndexSeries:
    return ExternalIndexSeries(
        build_session_change_series(_iv_bars(session_closes)), value_column=CHANGE_COLUMN
    )


# -- the change itself --------------------------------------------------


def test_the_change_is_a_session_over_session_percentage():
    frame = build_session_change_series(
        _iv_bars({"2024-06-03": 100.0, "2024-06-04": 110.0, "2024-06-05": 99.0})
    )
    # 100 -> 110 is +10%, 110 -> 99 is -10%.
    assert frame[CHANGE_COLUMN].tolist() == pytest.approx([10.0, -10.0])


def test_the_first_session_produces_no_change():
    """Nothing precedes it, so there is nothing to difference against."""
    frame = build_session_change_series(_iv_bars({"2024-06-03": 100.0, "2024-06-04": 110.0}))
    assert len(frame) == 1


def test_the_session_close_is_the_LAST_bar_not_the_first():
    """A change built off opening prints would be a different, unmeasured
    quantity."""
    frame = build_session_change_series(
        _iv_bars({"2024-06-03": 100.0, "2024-06-04": 200.0})
    )
    # Session closes are 100 and 200 -> +100%. The 0.5x opening bars
    # would give the same ratio, so make them differ:
    bars = _iv_bars({"2024-06-03": 100.0, "2024-06-04": 200.0})
    bars.iloc[0, 0] = 999.0  # a wild opening print on day 1
    assert build_session_change_series(bars)[CHANGE_COLUMN].iloc[0] == pytest.approx(100.0)
    assert frame[CHANGE_COLUMN].iloc[0] == pytest.approx(100.0)


# -- NO LOOKAHEAD -------------------------------------------------------


def test_a_sessions_own_change_is_not_visible_during_that_session():
    """THE test. The change across 06-04 is known only at its close, so
    no bar during 06-04 may see it."""
    series = _series({"2024-06-03": 100.0, "2024-06-04": 110.0, "2024-06-05": 121.0})

    during_0604 = pd.Timestamp("2024-06-04 15:59", tz=EASTERN_TZ)
    # +10% happened across 06-04 itself; it must NOT be readable yet.
    assert change_at(series, during_0604) == pytest.approx(NO_SIGNAL)

    during_0605 = pd.Timestamp("2024-06-05 09:30", tz=EASTERN_TZ)
    assert change_at(series, during_0605) == pytest.approx(10.0)


def test_a_friday_close_is_read_by_mondays_bars_and_nothing_sooner():
    """The weekend gap is where a naive 'next session' rule needs a market
    calendar. Publishing at midnight-after avoids that and must still land
    on Monday."""
    series = _series(
        {"2024-05-30": 100.0, "2024-05-31": 120.0, "2024-06-03": 132.0}
    )  # Thu, Fri, Mon
    assert change_at(series, pd.Timestamp("2024-05-31 15:59", tz=EASTERN_TZ)) == pytest.approx(
        NO_SIGNAL
    )
    # +20% across Friday, readable from Monday's first bar.
    assert change_at(series, pd.Timestamp("2024-06-03 04:00", tz=EASTERN_TZ)) == pytest.approx(
        20.0
    )


def test_premarket_bars_see_the_prior_sessions_change():
    """Published at midnight so the whole next session, extended hours
    included, reads the same value -- otherwise the signal would switch
    on mid-session."""
    series = _series({"2024-06-03": 100.0, "2024-06-04": 110.0, "2024-06-05": 110.0})
    for clock in ("04:00", "09:30", "12:00", "19:59"):
        assert change_at(
            series, pd.Timestamp(f"2024-06-05 {clock}", tz=EASTERN_TZ)
        ) == pytest.approx(10.0)


def test_bars_before_the_series_starts_read_the_no_op_value():
    series = _series({"2024-06-03": 100.0, "2024-06-04": 110.0})
    assert change_at(series, pd.Timestamp("2020-01-01", tz=EASTERN_TZ)) == pytest.approx(
        NO_SIGNAL
    )


# -- scalar / vectorized agreement --------------------------------------


def test_scalar_and_vectorized_agree_on_every_bar():
    series = _series(
        {f"2024-06-{d:02d}": 100.0 + d for d in (3, 4, 5, 6, 7, 10, 11, 12)}
    )
    index = pd.date_range("2024-06-03", "2024-06-12 20:00", freq="97min", tz="UTC")
    vec = changes_for_index(series, index)
    for i, ts in enumerate(index):
        assert vec[i] == pytest.approx(change_at(series, ts)), f"mismatch at {ts}"


def test_an_absent_series_is_the_no_op_on_both_paths():
    """A deployment without an implied-vol file must behave exactly as
    before this signal existed, not crash and not read NaN."""
    index = pd.date_range("2024-06-03", periods=10, freq="h", tz="UTC")
    assert np.all(changes_for_index(None, index) == NO_SIGNAL)
    assert change_at(None, index[0]) == NO_SIGNAL


def test_nan_before_the_series_start_becomes_the_no_op_not_nan():
    """NaN reaching a multiplier would silently poison every downstream
    number; converting once here is why the caller cannot forget."""
    series = _series({"2024-06-03": 100.0, "2024-06-04": 110.0})
    index = pd.date_range("2020-01-01", periods=5, freq="D", tz="UTC")
    values = changes_for_index(series, index)
    assert not np.isnan(values).any()
    assert np.all(values == NO_SIGNAL)


# -- input validation ---------------------------------------------------


def test_a_naive_index_is_refused():
    bars = _iv_bars({"2024-06-03": 100.0, "2024-06-04": 110.0})
    bars.index = bars.index.tz_localize(None)
    with pytest.raises(DataValidationError, match="tz-aware"):
        build_session_change_series(bars)


def test_a_missing_value_column_is_named():
    bars = _iv_bars({"2024-06-03": 100.0, "2024-06-04": 110.0}).rename(
        columns={"close": "price"}
    )
    with pytest.raises(DataValidationError, match="close"):
        build_session_change_series(bars)


def test_a_single_session_cannot_produce_a_change():
    with pytest.raises(DataValidationError, match="at least two sessions"):
        build_session_change_series(_iv_bars({"2024-06-03": 100.0}))


def test_empty_input_is_refused():
    with pytest.raises(DataValidationError, match="no bars"):
        build_session_change_series(pd.DataFrame({"close": []}))
