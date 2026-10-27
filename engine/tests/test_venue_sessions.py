"""engine/core/venue_sessions.py: a venue's windows, and the ones traded."""

from __future__ import annotations

from datetime import UTC, date, datetime, time

import pytest

from engine.core.exceptions import ConfigurationError
from engine.core.trading_calendar import EASTERN
from engine.core.venue_sessions import (
    AFTER_HOURS,
    CLOSED,
    PRE_MARKET,
    REGULAR,
    VenueCalendar,
    check_sessions,
)

TUESDAY = date(2026, 10, 27)


def _et(day: date, hour: int, minute: int = 0) -> datetime:
    return datetime.combine(day, time(hour, minute), EASTERN)


@pytest.mark.parametrize(
    "hour,minute,expected",
    [
        (6, 59, CLOSED),
        (7, 0, PRE_MARKET),  # 05:00 Mountain: Fidelity takes limit orders from here
        (9, 27, PRE_MARKET),
        (9, 28, CLOSED),  # the two minutes before the open take no orders
        (9, 30, REGULAR),
        (15, 59, REGULAR),
        (16, 0, AFTER_HOURS),
        (19, 59, AFTER_HOURS),
        (20, 0, CLOSED),
    ],
)
def test_fidelitys_day(hour, minute, expected):
    calendar = VenueCalendar("fidelity", (PRE_MARKET, REGULAR, AFTER_HOURS))
    assert calendar.session_at(_et(TUESDAY, hour, minute)) == expected


def test_alpacas_pre_market_starts_at_four_and_runs_into_the_open():
    calendar = VenueCalendar("alpaca", (PRE_MARKET, REGULAR))
    assert calendar.session_at(_et(TUESDAY, 4)) == PRE_MARKET
    assert calendar.session_at(_et(TUESDAY, 9, 29)) == PRE_MARKET
    assert calendar.session_at(_et(TUESDAY, 9, 30)) == REGULAR


def test_only_the_traded_windows_count_for_trading():
    calendar = VenueCalendar("fidelity", (PRE_MARKET, REGULAR))
    assert calendar.window_at(_et(TUESDAY, 8, 31)).session == PRE_MARKET
    assert calendar.window_at(_et(TUESDAY, 17)) is None, "after-hours is not traded"
    assert calendar.session_at(_et(TUESDAY, 17)) == AFTER_HOURS, "but it is still the venue's"
    assert calendar.day_span(TUESDAY) == (_et(TUESDAY, 7), _et(TUESDAY, 16))


def test_a_half_day_ends_after_hours_four_hours_after_its_close():
    early = lambda day: time(13, 0)  # noqa: E731
    calendar = VenueCalendar("fidelity", (REGULAR, AFTER_HOURS), close_for=early)
    assert calendar.session_at(_et(TUESDAY, 13, 30)) == AFTER_HOURS
    assert calendar.session_at(_et(TUESDAY, 17)) == CLOSED
    assert calendar.day_span(TUESDAY) == (_et(TUESDAY, 9, 30), _et(TUESDAY, 17))


def test_a_holiday_has_no_window_and_the_next_one_is_after_it():
    thanksgiving = date(2026, 11, 26)
    calendar = VenueCalendar("fidelity", (PRE_MARKET, REGULAR))
    assert calendar.traded(thanksgiving) == ()
    assert not calendar.observing(_et(thanksgiving, 12))
    upcoming = calendar.next_window(_et(thanksgiving, 12))
    assert upcoming.session == PRE_MARKET and upcoming.start == _et(date(2026, 11, 27), 7)


def test_the_next_window_is_the_current_one_while_it_lasts():
    calendar = VenueCalendar("fidelity", (PRE_MARKET, REGULAR, AFTER_HOURS))
    assert calendar.next_window(_et(TUESDAY, 8)).session == PRE_MARKET
    assert calendar.next_window(_et(TUESDAY, 9, 29)).session == REGULAR, "the gap waits for it"
    friday_evening = _et(date(2026, 10, 30), 20, 30)
    assert calendar.next_window(friday_evening).start == _et(date(2026, 11, 2), 7)


def test_eastern_holds_across_the_daylight_saving_change():
    """07:00 ET is 11:00 UTC in October and 12:00 UTC in November."""
    calendar = VenueCalendar("fidelity", (PRE_MARKET, REGULAR))
    october = datetime(2026, 10, 30, 11, 0, tzinfo=UTC)
    november = datetime(2026, 11, 2, 12, 0, tzinfo=UTC)
    assert calendar.session_at(october) == PRE_MARKET
    assert calendar.session_at(november) == PRE_MARKET
    assert calendar.session_at(datetime(2026, 11, 2, 11, 30, tzinfo=UTC)) == CLOSED


def test_observing_covers_the_venues_whole_day_traded_or_not():
    calendar = VenueCalendar("fidelity", (REGULAR,))
    assert calendar.observing(_et(TUESDAY, 7))
    assert calendar.observing(_et(TUESDAY, 19, 59))
    assert not calendar.observing(_et(TUESDAY, 6, 59))


def test_sessions_are_checked_and_put_in_the_days_order():
    assert check_sessions([AFTER_HOURS, PRE_MARKET]) == (PRE_MARKET, AFTER_HOURS)
    for bad in ([], ["overnight"], [REGULAR, REGULAR]):
        with pytest.raises(ConfigurationError):
            check_sessions(bad)
    with pytest.raises(ConfigurationError, match="venue"):
        VenueCalendar("schwab")
    with pytest.raises(ConfigurationError, match="timezone"):
        VenueCalendar("fidelity").session_at(datetime(2026, 10, 27, 8))
