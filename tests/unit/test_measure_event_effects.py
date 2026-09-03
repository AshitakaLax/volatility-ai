"""Tests for tools/measure_event_effects.py.

The statistics are validated at runtime against known answers -- the
script's own `--validate` re-derives the recorded FOMC and earnings
figures and refuses to be trusted otherwise. What is tested HERE is the
part that has no known answer to check itself against: the nth-weekday
date arithmetic, which is new logic (the repo had none) and is exactly
the kind of thing that is silently off by a week.
"""

from __future__ import annotations

from datetime import date

import numpy as np
import pandas as pd
import pytest

from tools.measure_event_effects import (
    month_end_sessions,
    nth_weekday,
    opex_dates,
    quarter_end_sessions,
    third_friday,
    welch_t,
    witching_dates,
)

# -- nth-weekday arithmetic --------------------------------------------


@pytest.mark.parametrize(
    ("year", "month", "expected"),
    [
        (2024, 1, date(2024, 1, 19)),  # Jan 1 2024 was a Monday
        (2025, 6, date(2025, 6, 20)),  # Jun 1 2025 was a Sunday
        (2026, 1, date(2026, 1, 16)),  # Jan 1 2026 was a Thursday
        (2020, 2, date(2020, 2, 21)),  # Feb 1 2020 was a Saturday
        (2021, 10, date(2021, 10, 15)),  # Oct 1 2021 was a Friday -> 1st Friday IS the 1st
    ],
)
def test_third_friday_against_known_dates(year, month, expected):
    """Hand-checked against a real calendar. The month-starts-on-a-Friday
    case (2021-10) is the one an off-by-one gets wrong."""
    assert third_friday(year, month) == expected


def test_every_third_friday_is_actually_a_friday():
    for year in range(2016, 2027):
        for month in range(1, 13):
            d = third_friday(year, month)
            assert d.weekday() == 4, f"{d} is not a Friday"


def test_the_third_friday_falls_in_the_expected_date_range():
    """A third Friday is always between the 15th and the 21st. If the
    off-by-one this test exists to catch were present, dates would land
    on the 8th-14th or the 22nd-28th."""
    for year in range(2016, 2027):
        for month in range(1, 13):
            assert 15 <= third_friday(year, month).day <= 21


def test_nth_weekday_handles_the_first_occurrence():
    # 2021-10-01 was itself a Friday, so the 1st Friday is the 1st.
    assert nth_weekday(2021, 10, weekday=4, n=1) == date(2021, 10, 1)
    assert nth_weekday(2021, 10, weekday=4, n=2) == date(2021, 10, 8)


def test_nth_weekday_supports_other_weekdays():
    # First Friday of a month is the NFP release convention.
    assert nth_weekday(2024, 3, weekday=4, n=1) == date(2024, 3, 1)
    # Monday=0.
    assert nth_weekday(2024, 1, weekday=0, n=1) == date(2024, 1, 1)


# -- derived calendars -------------------------------------------------


def test_opex_yields_twelve_dates_a_year():
    years = [2020, 2021]
    assert len(opex_dates(years)) == 24


def test_witching_is_the_quarterly_subset_of_opex():
    """Triple witching must be a strict subset -- it is the same third
    Friday, in four specific months, not a separate rule."""
    years = [2019, 2020, 2021]
    monthly, quarterly = opex_dates(years), witching_dates(years)
    assert quarterly < monthly
    assert len(quarterly) == 12
    assert {d.month for d in quarterly} == {3, 6, 9, 12}


# -- month/quarter end derived from real sessions ----------------------


def _sessions(*days: str) -> pd.Index:
    return pd.Index([date.fromisoformat(d) for d in days])


def test_month_end_uses_the_last_SESSION_not_the_calendar_last_day():
    """2021-01-31 was a Sunday; the last session was Friday the 29th.
    Deriving from the calendar would produce a date the market was shut."""
    sessions = _sessions("2021-01-27", "2021-01-28", "2021-01-29", "2021-02-01", "2021-02-02")
    assert month_end_sessions(sessions) == {date(2021, 1, 29), date(2021, 2, 2)}


def test_quarter_end_groups_by_calendar_quarter():
    sessions = _sessions("2021-03-30", "2021-03-31", "2021-04-01", "2021-06-29", "2021-06-30")
    assert quarter_end_sessions(sessions) == {date(2021, 3, 31), date(2021, 6, 30)}


def test_month_end_and_quarter_end_agree_on_a_quarter_boundary():
    sessions = _sessions("2021-03-30", "2021-03-31", "2021-04-01")
    assert date(2021, 3, 31) in month_end_sessions(sessions)
    assert date(2021, 3, 31) in quarter_end_sessions(sessions)


# -- Welch's t ---------------------------------------------------------


def test_welch_t_is_zero_for_identical_samples():
    a = np.array([1.0, 2.0, 3.0, 4.0])
    assert welch_t(a, a.copy()) == pytest.approx(0.0)


def test_welch_t_sign_follows_the_first_sample():
    high = np.array([10.0, 11.0, 12.0, 13.0])
    low = np.array([1.0, 2.0, 3.0, 4.0])
    assert welch_t(high, low) > 0
    assert welch_t(low, high) < 0


def test_welch_t_matches_a_hand_computed_value():
    """Unequal variances AND unequal n -- the case Student's t gets
    wrong and Welch's is for."""
    a = np.array([1.0, 2.0, 3.0, 4.0, 5.0])  # mean 3, var 2.5, n 5
    b = np.array([2.0, 4.0, 6.0])  # mean 4, var 4.0, n 3
    expected = (3.0 - 4.0) / np.sqrt(2.5 / 5 + 4.0 / 3)
    assert welch_t(a, b) == pytest.approx(expected)


def test_welch_t_is_nan_rather_than_a_crash_on_a_degenerate_sample():
    """A candidate calendar with one matching session must not take the
    whole report down."""
    assert np.isnan(welch_t(np.array([1.0]), np.array([1.0, 2.0, 3.0])))
    assert np.isnan(welch_t(np.array([2.0, 2.0]), np.array([2.0, 2.0])))
