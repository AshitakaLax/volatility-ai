"""
NYSE trading sessions, for "how far behind is this fund's data?".

--------------------------------------------------------------------
WHY THERE IS A CALENDAR HERE AT ALL

Nothing else in the project needs one. The market-hours supervisor asks
Alpaca's calendar at run time (tools/market_hours_supervisor.py), and a
fetch simply gets no bars for a holiday. But the web server has no Alpaca
credentials, by design, and the warehouse tab still has to say whether a
fund that ends on a Friday is current on Monday morning (it is) or on
Tuesday evening (it is not). Counting weekdays would call every holiday a
missing session.

--------------------------------------------------------------------
WHAT IS MODELLED

The NYSE's recurring holidays, as pandas' holiday rules: each one moved
the way the exchange moves it. A Saturday holiday closes the Friday before
and a Sunday one the Monday after (nearest_workday) -- except New Year's
Day, which the exchange does not move back into the old year: 2021-12-31
traded. Plus the one-off closures since 2001.

Two things are NOT modelled, and both err toward "behind":

  * Early closes (13:00 around July 4th, Thanksgiving, Christmas). A half
    day counts as complete at 16:00 like any other, so for three hours a
    year a fund can read one session behind that already has it all.
  * Closures nobody has announced yet: a national day of mourning closes
    the exchange at a few days' notice. Add it to SPECIAL_CLOSURES when
    one happens -- until then that day reads as a missing session.

Checked against the warehouse itself: RSP has a bar on exactly 2,707
sessions from 2016-01-04 to 2026-10-08, and this calendar counts 2,707
(engine/tests/test_trading_calendar.py).
"""

from __future__ import annotations

from datetime import date, datetime, time, timedelta
from functools import lru_cache
from typing import Any
from zoneinfo import ZoneInfo

EASTERN = ZoneInfo("America/New_York")

# When a session's last regular-hours bar is in: the 15:59 bar closes at 16:00.
SESSION_CLOSE = time(16, 0)

# Closed by the exchange outside its holiday rules (since 2001; the oldest
# bars in the warehouse are 2003's).
SPECIAL_CLOSURES = frozenset(
    {
        # September 11.
        date(2001, 9, 11),
        date(2001, 9, 12),
        date(2001, 9, 13),
        date(2001, 9, 14),
        # National days of mourning: Reagan, Ford, G. H. W. Bush, Carter.
        date(2004, 6, 11),
        date(2007, 1, 2),
        date(2018, 12, 5),
        date(2025, 1, 9),
        # Hurricane Sandy.
        date(2012, 10, 29),
        date(2012, 10, 30),
    }
)


@lru_cache(maxsize=1)
def _calendar() -> Any:
    """The holiday rules, built once. pandas is imported here rather than at
    module scope so importing this module stays cheap."""
    from pandas.tseries.holiday import (
        AbstractHolidayCalendar,
        GoodFriday,
        Holiday,
        USLaborDay,
        USMartinLutherKingJr,
        USMemorialDay,
        USPresidentsDay,
        USThanksgivingDay,
        nearest_workday,
        sunday_to_monday,
    )

    return AbstractHolidayCalendar(
        name="NYSE",
        rules=[
            Holiday("New Year's Day", month=1, day=1, observance=sunday_to_monday),
            # The exchange's own observance began in 1998, not the federal 1986.
            Holiday(
                "Martin Luther King Jr. Day",
                month=1,
                day=1,
                start_date=date(1998, 1, 1),
                offset=USMartinLutherKingJr.offset,
            ),
            USPresidentsDay,
            GoodFriday,
            USMemorialDay,
            Holiday(
                "Juneteenth",
                month=6,
                day=19,
                start_date=date(2022, 1, 1),
                observance=nearest_workday,
            ),
            Holiday("Independence Day", month=7, day=4, observance=nearest_workday),
            USLaborDay,
            USThanksgivingDay,
            Holiday("Christmas Day", month=12, day=25, observance=nearest_workday),
        ],
    )


@lru_cache(maxsize=128)
def holidays(year: int) -> frozenset[date]:
    """Every holiday and special closure in `year` that falls on a weekday."""
    rules = _calendar().holidays(start=f"{year}-01-01", end=f"{year}-12-31")
    found = {stamp.date() for stamp in rules}
    found |= {day for day in SPECIAL_CLOSURES if day.year == year}
    return frozenset(day for day in found if day.weekday() < 5)


def is_session(day: date) -> bool:
    """True if the NYSE holds a regular session on `day`."""
    return day.weekday() < 5 and day not in holidays(day.year)


def previous_session(day: date) -> date:
    """The last session strictly before `day`."""
    day -= timedelta(days=1)
    while not is_session(day):
        day -= timedelta(days=1)
    return day


def next_session(day: date, n: int = 1) -> date:
    """The `n`-th session strictly after `day`: n=1 is the next one."""
    if n < 1:
        raise ValueError(f"n must be >= 1, got {n}")
    for _ in range(n):
        day += timedelta(days=1)
        while not is_session(day):
            day += timedelta(days=1)
    return day


def sessions_between(after: date, through: date) -> list[date]:
    """Every session strictly after `after`, up to and including `through`."""
    sessions = []
    day = after + timedelta(days=1)
    while day <= through:
        if is_session(day):
            sessions.append(day)
        day += timedelta(days=1)
    return sessions


def last_completed_session(now: datetime) -> date:
    """The most recent session whose regular hours are over at `now`
    (tz-aware): today from 16:00 Eastern on a session day, else the session
    before. A session still trading is not yet a session a fund can hold."""
    local = now.astimezone(EASTERN)
    today = local.date()
    if is_session(today) and local.time() >= SESSION_CLOSE:
        return today
    return previous_session(today)


__all__ = [
    "EASTERN",
    "SESSION_CLOSE",
    "SPECIAL_CLOSURES",
    "holidays",
    "is_session",
    "last_completed_session",
    "next_session",
    "previous_session",
    "sessions_between",
]
