"""
The day's real close, from Alpaca's calendar, for engine/core/venue_sessions.py.

venue_sessions knows the windows; it needs to know, for a given day,
whether there is a session and when it closes. Its own default reads the
holiday rules, which do not know the early closes. Alpaca's calendar does
-- 13:00 on the day after Thanksgiving, Christmas Eve and July 3rd -- and
the supervisor and the trading loop each already hold a trading client.

One request per day asked about, kept for the process's life. A calendar
that cannot be read falls back to the holiday rules (and says so once):
wrong only on an early-close day, and only by the three hours a half day
lacks, which is the safe direction -- the loop's after-hours ends on the
venue's own refusal rather than on a window it thought it had.
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from datetime import date, time

from engine.core.venue_sessions import default_close_for

logger = logging.getLogger("Optimizer")


def alpaca_close_for(trading_client) -> Callable[[date], time | None]:
    """A close_for(day) reading `trading_client`'s calendar."""
    cache: dict[date, time | None] = {}
    warned = {"said": False}

    def close_for(day: date) -> time | None:
        if day in cache:
            return cache[day]
        try:
            from alpaca.trading.requests import GetCalendarRequest

            close = None
            for entry in trading_client.get_calendar(GetCalendarRequest(start=day, end=day)):
                entry_day = entry.date.date() if hasattr(entry.date, "date") else entry.date
                if entry_day == day:
                    close = _as_time(entry.close)
            cache[day] = close
        except Exception as exc:
            if not warned["said"]:
                logger.warning(
                    f"Alpaca's calendar could not be read ({type(exc).__name__}: {exc}); "
                    "using the holiday rules, which do not know early closes."
                )
                warned["said"] = True
            return default_close_for(day)
        return cache[day]

    return close_for


def _as_time(value) -> time:
    """Alpaca's calendar gives the close as a time or a datetime."""
    if isinstance(value, time):
        return value.replace(tzinfo=None)
    return time(value.hour, value.minute)
