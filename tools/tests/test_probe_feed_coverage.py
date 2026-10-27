"""tools/probe_feed_coverage.py: minutes with a bar, per Fidelity window."""

from __future__ import annotations

from datetime import UTC, date, datetime, time, timedelta

from engine.core.trading_calendar import EASTERN
from engine.core.venue_sessions import SESSIONS, VenueCalendar
from tools.probe_feed_coverage import coverage, last_days, on_days

DAY = date(2026, 10, 27)


def _at(hour, minute):
    return datetime.combine(DAY, time(hour, minute), EASTERN).astimezone(UTC)


def test_minutes_are_counted_in_the_window_they_fall_in():
    stamps = [_at(7, 0), _at(7, 1), _at(8, 30), _at(9, 28), _at(10, 0), _at(16, 0), _at(19, 59)]
    stamps += [_at(4, 0)]  # before Fidelity's pre-market: in no window of its
    table = coverage(stamps, VenueCalendar("fidelity", SESSIONS))
    assert table[(DAY, "pre_market")] == (3, 148)
    assert table[(DAY, "regular")] == (1, 390)
    assert table[(DAY, "after_hours")] == (2, 240)


def test_a_day_with_no_bar_in_a_window_reads_zero():
    regular = [_at(9, 30) + timedelta(minutes=m) for m in range(390)]
    table = coverage(regular, VenueCalendar("fidelity", SESSIONS))
    assert table[(DAY, "regular")] == (390, 390)
    assert table[(DAY, "pre_market")][0] == 0 and table[(DAY, "after_hours")][0] == 0


def test_both_feeds_are_counted_on_the_same_finished_days():
    yesterday = DAY - timedelta(days=1)
    before = DAY - timedelta(days=2)
    primary = [_at(10, 0) - timedelta(days=2), _at(10, 0) - timedelta(days=1)]
    other = [*primary, _at(7, 5)]  # a bar this morning: the day is not over
    days = last_days(primary, 2, DAY)
    assert days == {before, yesterday}
    assert last_days(other, 2, DAY) == days
    assert on_days(other, days) == primary
