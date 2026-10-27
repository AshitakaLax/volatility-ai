"""
A venue's trading windows, and the ones a deployment trades.

--------------------------------------------------------------------
WHY THE WINDOWS ARE THE VENUE'S

"Extended hours" is not one thing. Alpaca takes orders from 04:00 ET to
four hours after the close, without a break. Fidelity takes them from
07:00 to 09:28 ET, then not until the 09:30 open, and after the close
until 20:00 ET -- two minutes of every morning in which an order is
refused. A deployment that trades Fidelity's pre-market on Alpaca's clock
would place orders for three hours that Fidelity rejects, and one on the
regular clock never wakes for the 08:30 ET releases at all.

So each venue names its windows here, and a deployment names which of
them it trades (live.sessions): `pre_market`, `regular`, `after_hours`.

--------------------------------------------------------------------
WHAT DECIDES A DAY

Whether a day has a session at all, and when it closes, come from
`close_for(day)`: the day's close, or None for a day without a session.
The default reads engine/core/trading_calendar.py, which knows the
holidays but not the early closes (13:00 around July 4th, Thanksgiving,
Christmas); a caller with Alpaca's calendar passes its real closes
(engine/trading/session_clock.py). After-hours ends four hours after
whatever close the day has, so a half day's ends at 17:00.

All times are Eastern. 07:00 ET is 05:00 Mountain on both sides of a
daylight-saving change, because both zones change together.

Pure: no I/O and no imports beyond the calendar, so the supervisor, the
trading loop, the bridge host and the tests all ask the same thing.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta

from engine.core.exceptions import ConfigurationError
from engine.core.trading_calendar import EASTERN, SESSION_CLOSE, is_session, next_session

PRE_MARKET = "pre_market"
REGULAR = "regular"
AFTER_HOURS = "after_hours"
SESSIONS = (PRE_MARKET, REGULAR, AFTER_HOURS)
CLOSED = "closed"

REGULAR_OPEN = time(9, 30)
AFTER_HOURS_LENGTH = timedelta(hours=4)
# How many days ahead next_window() looks for a session: the longest run of
# days without one (a holiday weekend, a closure) is far shorter.
_SEARCH_DAYS = 10


@dataclass(frozen=True)
class Venue:
    """When a venue takes orders outside the regular session."""

    name: str
    pre_market_start: time
    pre_market_end: time


VENUES = {
    # Alpaca: 04:00 to the open, then after the close for four hours.
    "alpaca": Venue("alpaca", time(4, 0), REGULAR_OPEN),
    # Fidelity: 07:00 to 09:28, and after the close until 20:00. The two
    # minutes before the open take no orders.
    "fidelity": Venue("fidelity", time(7, 0), time(9, 28)),
}


@dataclass(frozen=True)
class Window:
    """One trading window on one day, in Eastern time; [start, end)."""

    session: str
    start: datetime
    end: datetime

    def contains(self, moment: datetime) -> bool:
        return self.start <= moment < self.end

    def to_dict(self) -> dict:
        return {
            "session": self.session,
            "start": self.start.isoformat(),
            "end": self.end.isoformat(),
        }


def default_close_for(day: date) -> time | None:
    """The regular close by the holiday calendar: 16:00, or None on a day
    without a session. Early closes are not known here."""
    return SESSION_CLOSE if is_session(day) else None


def venue(name: str) -> Venue:
    try:
        return VENUES[name]
    except KeyError:
        raise ConfigurationError(f"No trading windows known for venue {name!r}") from None


def check_sessions(sessions: Iterable[str], where: str = "live.sessions") -> tuple[str, ...]:
    """The sessions as a tuple in the day's order, or ConfigurationError."""
    given = tuple(sessions)
    if not given:
        raise ConfigurationError(f"{where} must name at least one of {list(SESSIONS)}")
    unknown = [s for s in given if s not in SESSIONS]
    if unknown:
        raise ConfigurationError(
            f"{where} has unknown session(s) {unknown}; known: {list(SESSIONS)}"
        )
    if len(set(given)) != len(given):
        raise ConfigurationError(f"{where} names a session twice: {list(given)}")
    return tuple(s for s in SESSIONS if s in given)


def day_windows(venue_name: str, day: date, close: time | None) -> tuple[Window, ...]:
    """Every window the venue has on `day` whose regular session closes at
    `close`, in order; () on a day without a session."""
    if close is None:
        return ()
    v = venue(venue_name)
    at = lambda t: datetime.combine(day, t, EASTERN)  # noqa: E731
    closes = at(close)
    return (
        Window(PRE_MARKET, at(v.pre_market_start), at(v.pre_market_end)),
        Window(REGULAR, at(REGULAR_OPEN), closes),
        Window(AFTER_HOURS, closes, closes + AFTER_HOURS_LENGTH),
    )


class VenueCalendar:
    """The windows a deployment trades at its venue.

    `close_for(day)` gives the day's regular close, or None for a day
    without a session (default_close_for unless a caller knows better).
    """

    def __init__(
        self,
        venue_name: str,
        sessions: Iterable[str] = (REGULAR,),
        close_for: Callable[[date], time | None] = default_close_for,
    ) -> None:
        venue(venue_name)  # refuse an unknown venue now, not at the first question
        self.venue = venue_name
        self.sessions = check_sessions(sessions)
        self._close_for = close_for

    def windows(self, day: date) -> tuple[Window, ...]:
        """All of the venue's windows on `day`, traded or not."""
        return day_windows(self.venue, day, self._close_for(day))

    def traded(self, day: date) -> tuple[Window, ...]:
        """The windows this deployment trades on `day`."""
        return tuple(w for w in self.windows(day) if w.session in self.sessions)

    def session_at(self, moment: datetime) -> str:
        """The venue's session at `moment` (traded or not), or CLOSED."""
        found = self._window_at(self.windows(_eastern(moment).date()), moment)
        return found.session if found is not None else CLOSED

    def window_at(self, moment: datetime) -> Window | None:
        """The TRADED window containing `moment`, or None."""
        return self._window_at(self.traded(_eastern(moment).date()), moment)

    def day_span(self, day: date) -> tuple[datetime, datetime] | None:
        """From the first traded window's start to the last's end on `day`;
        None on a day without one."""
        traded = self.traded(day)
        if not traded:
            return None
        return traded[0].start, traded[-1].end

    def observing(self, moment: datetime) -> bool:
        """Whether `moment` is within the venue's whole day -- from its
        pre-market's start to its after-hours' end -- on a session day:
        when there are bars to watch, traded or not."""
        windows = self.windows(_eastern(moment).date())
        return bool(windows) and windows[0].start <= moment < windows[-1].end

    def next_window(self, moment: datetime) -> Window | None:
        """The traded window containing `moment`, or else the next one to
        start; None if none starts within the next _SEARCH_DAYS."""
        day = _eastern(moment).date()
        for _ in range(_SEARCH_DAYS):
            for window in self.traded(day):
                if moment < window.end:
                    return window
            day = next_session(day)
        return None

    @staticmethod
    def _window_at(windows: tuple[Window, ...], moment: datetime) -> Window | None:
        for window in windows:
            if window.contains(moment):
                return window
        return None


def _eastern(moment: datetime) -> datetime:
    if moment.tzinfo is None:
        raise ConfigurationError("a trading window needs a timezone-aware time")
    return moment.astimezone(EASTERN)
