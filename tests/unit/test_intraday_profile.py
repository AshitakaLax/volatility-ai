"""Tests for src/intraday_profile.py.

The profile itself is a measured data artifact, so these pin its
STRUCTURE and its join semantics rather than individual minute values:
the shape (open and close elevated, midday depressed), the
normalization that makes an exponent of 0.0 a true no-op, and the
Eastern conversion across a DST boundary.
"""

from __future__ import annotations

from datetime import UTC, datetime
from zoneinfo import ZoneInfo

import pytest

from src.intraday_profile import (
    INTRADAY_RANGE_PROFILE,
    SESSION_MINUTES,
    minutes_since_open,
    relative_range,
)

EASTERN = ZoneInfo("America/New_York")


def test_the_profile_covers_every_minute_of_the_session():
    assert len(INTRADAY_RANGE_PROFILE) == SESSION_MINUTES == 390


def test_the_profile_is_normalized_to_mean_one():
    """This is what makes time_of_day_exponent=0.0 an exact no-op
    without needing a separate enable flag, and what lets the value be
    used directly as a multiplier base."""
    mean = sum(INTRADAY_RANGE_PROFILE) / len(INTRADAY_RANGE_PROFILE)
    assert mean == pytest.approx(1.0, abs=1e-4)


def test_every_value_is_positive():
    """A zero or negative entry would produce a nonsense multiplier
    under a negative exponent (division by zero, or a sign flip)."""
    assert min(INTRADAY_RANGE_PROFILE) > 0.0


def test_the_open_is_the_most_volatile_minute():
    """The headline finding this module exists to encode."""
    assert INTRADAY_RANGE_PROFILE.index(max(INTRADAY_RANGE_PROFILE)) == 0


def test_the_open_is_substantially_more_volatile_than_midday():
    """Pinned as a ratio rather than absolute values: the exact numbers
    move if the dataset is extended, but the U-shape is the claim."""
    open_30 = sum(INTRADAY_RANGE_PROFILE[0:30]) / 30
    midday = sum(INTRADAY_RANGE_PROFILE[180:270]) / 90
    assert open_30 / midday > 1.8


def test_the_close_is_elevated_relative_to_midday():
    """The second arm of the U -- closing-auction and MOC activity."""
    close_15 = sum(INTRADAY_RANGE_PROFILE[375:390]) / 15
    midday = sum(INTRADAY_RANGE_PROFILE[180:270]) / 90
    assert close_15 > midday


def test_minutes_outside_the_session_are_neutral():
    """Not defensive padding: the backtest data is regular-hours only,
    but the live path can legitimately see an extended-hours bar, and
    1.0 is the only safe reading for a minute the profile says nothing
    about."""
    assert relative_range(-1) == 1.0
    assert relative_range(390) == 1.0
    assert relative_range(10_000) == 1.0


def test_relative_range_returns_the_profile_inside_the_session():
    assert relative_range(0) == INTRADAY_RANGE_PROFILE[0]
    assert relative_range(389) == INTRADAY_RANGE_PROFILE[389]


@pytest.mark.parametrize(
    ("moment", "expected"),
    [
        (datetime(2026, 1, 15, 14, 30, tzinfo=UTC), 0),  # winter: 09:30 EST
        (datetime(2026, 7, 15, 13, 30, tzinfo=UTC), 0),  # summer: 09:30 EDT
        (datetime(2026, 1, 15, 20, 59, tzinfo=UTC), 389),  # winter: 15:59 EST
        (datetime(2026, 7, 15, 19, 59, tzinfo=UTC), 389),  # summer: 15:59 EDT
    ],
)
def test_minutes_since_open_handles_both_sides_of_dst(moment, expected):
    """The session boundary is an Eastern-time concept and the UTC
    offset changes twice a year. Matching on UTC would put the open at
    minute 0 for half the year and minute 60 for the other half."""
    assert minutes_since_open(moment) == expected


@pytest.mark.parametrize(
    "moment",
    [
        datetime(2026, 1, 15, 13, 0, tzinfo=UTC),  # 08:00 EST -- pre-market
        datetime(2026, 1, 15, 21, 30, tzinfo=UTC),  # 16:30 EST -- after hours
    ],
)
def test_minutes_since_open_rejects_times_outside_the_session(moment):
    assert minutes_since_open(moment) == -1


def test_a_naive_timestamp_is_treated_as_utc_not_local_time():
    """Same convention fomc_calendar documents: the result must not
    depend on the host machine's timezone."""
    assert minutes_since_open(datetime(2026, 1, 15, 14, 30)) == 0
