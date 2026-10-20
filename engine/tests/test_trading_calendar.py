"""engine/core/trading_calendar.py: the NYSE sessions a fund's bars should cover."""

from __future__ import annotations

from datetime import UTC, date, datetime

import pytest

from engine.core.trading_calendar import (
    EASTERN,
    holidays,
    is_session,
    last_completed_session,
    previous_session,
    sessions_between,
)

# The exchange's published closures.
NYSE_HOLIDAYS = {
    2024: [
        "2024-01-01", "2024-01-15", "2024-02-19", "2024-03-29", "2024-05-27",
        "2024-06-19", "2024-07-04", "2024-09-02", "2024-11-28", "2024-12-25",
    ],
    2025: [
        "2025-01-01", "2025-01-09", "2025-01-20", "2025-02-17", "2025-04-18",
        "2025-05-26", "2025-06-19", "2025-07-04", "2025-09-01", "2025-11-27",
        "2025-12-25",
    ],
    2026: [
        "2026-01-01", "2026-01-19", "2026-02-16", "2026-04-03", "2026-05-25",
        "2026-06-19", "2026-07-03", "2026-09-07", "2026-11-26", "2026-12-25",
    ],
    2027: [
        "2027-01-01", "2027-01-18", "2027-02-15", "2027-03-26", "2027-05-31",
        "2027-06-18", "2027-07-05", "2027-09-06", "2027-11-25", "2027-12-24",
    ],
}  # fmt: skip


@pytest.mark.parametrize("year", sorted(NYSE_HOLIDAYS))
def test_holidays_match_the_exchange(year):
    assert sorted(day.isoformat() for day in holidays(year)) == NYSE_HOLIDAYS[year]


@pytest.mark.parametrize(
    ("day", "trades"),
    [
        (date(2021, 12, 24), False),  # Christmas on a Saturday closes the Friday
        (date(2021, 12, 31), True),  # ...but New Year's on a Saturday does not
        (date(2022, 6, 20), False),  # the first Juneteenth, a Sunday, closed the Monday
        (date(2021, 6, 18), True),  # and there was none before it
        (date(2018, 12, 5), False),  # a national day of mourning
        (date(2012, 10, 30), False),  # Hurricane Sandy
        (date(2026, 10, 12), True),  # Columbus Day trades
        (date(2026, 10, 17), False),  # a Saturday
    ],
)
def test_the_rules_the_exchange_moves_by(day, trades):
    assert is_session(day) is trades


def test_every_session_rsp_holds_in_the_warehouse():
    """RSP has bars on exactly 2,707 dates from 2016-01-04 to 2026-10-08."""
    assert len(sessions_between(date(2016, 1, 3), date(2026, 10, 8))) == 2707


def test_sessions_between_excludes_the_start_and_includes_the_end():
    assert sessions_between(date(2026, 10, 8), date(2026, 10, 19)) == [
        date(2026, 10, 9),
        date(2026, 10, 12),
        date(2026, 10, 13),
        date(2026, 10, 14),
        date(2026, 10, 15),
        date(2026, 10, 16),
        date(2026, 10, 19),
    ]
    assert sessions_between(date(2026, 10, 19), date(2026, 10, 19)) == []


def test_previous_session_skips_weekends_and_holidays():
    assert previous_session(date(2026, 10, 19)) == date(2026, 10, 16)
    assert previous_session(date(2026, 7, 6)) == date(2026, 7, 2)


def _eastern(*args) -> datetime:
    return datetime(*args, tzinfo=EASTERN)


@pytest.mark.parametrize(
    ("now", "expected"),
    [
        (_eastern(2026, 10, 19, 9, 0), date(2026, 10, 16)),  # Monday, before the open
        (_eastern(2026, 10, 19, 15, 59), date(2026, 10, 16)),  # still trading
        (_eastern(2026, 10, 19, 16, 0), date(2026, 10, 19)),  # closed
        (_eastern(2026, 10, 18, 12, 0), date(2026, 10, 16)),  # Sunday
        (_eastern(2026, 7, 3, 17, 0), date(2026, 7, 2)),  # a holiday
        (datetime(2026, 10, 20, 1, 30, tzinfo=UTC), date(2026, 10, 19)),  # Monday 21:30 ET
    ],
)
def test_last_completed_session(now, expected):
    assert last_completed_session(now) == expected
