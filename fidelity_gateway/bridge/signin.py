"""
When the Fidelity sign-in began, when Fidelity will end it, and what to say.

Fidelity ends a browser session about SESSION_HOURS after the sign-in,
whatever the tab does in between -- measured from this bridge's own journal
(6 of 10 sign-ins ended 10.34-10.50 h later; the rest ended sooner, by the
browser closing or a sign-out by hand). So a sign-in the evening before is
gone by the open, and one before 05:30 ET does not reach the 16:00 close.
Nothing here signs anyone in: it works out the times and words them, so a
person is told while there is still time.

  SignInWatch   follows the extension's Fidelity tab (session.tab_state)
                through the bridge host's ticks: when the sign-in the tab is
                on began, and so when it is expected to end. The host
                restarting does not forget -- replay() reads the same story
                back from its event journal.
  outlook()     for the readiness checklist's Fidelity item: "signed in since
                08:41 ET; Fidelity ends the session about 19:11 ET", and
                whether that is before the close of a regular session still
                to trade (a warning: it trades now, and will stop).
  notices()     what a phone is told, all of the kind `fidelity_signin`:
                  - a sign-in, and when it is expected to end;
                  - REMIND_BEFORE_OPEN_MINUTES before a regular open, when
                    the tab is signed out, has no Fidelity tab, or is on a
                    sign-in that ends before that day's close;
                  - EXPIRY_WARNING_MINUTES before the expected end, when the
                    regular session is still open then.

The regular session (09:30-16:00 ET) is what these protect: every order this
deployment has placed was inside it, and one sign-in cannot span a 07:00-20:00
day anyway (13 h against 10.5). The deployment's own open, when it is
earlier, is still warned of by readiness ("Not ready for the open").

  assisted_notice()
                what the extension's own assisted sign-in did this morning
                (it pressed the button of a form the browser had filled in,
                or could not, and why), from the one word its `signin`
                event carries. The engine is told; it cannot ask.

The expected end is an estimate. A read-only account check that passes after
it proves the session outlived the estimate (a sign-in the bridge did not
see), and confirmed() then forgets the start rather than keep warning.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import datetime
from typing import Any
from zoneinfo import ZoneInfo

EASTERN = ZoneInfo("America/New_York")
#: How long Fidelity keeps a browser session, from the sign-in (measured).
SESSION_HOURS = 10.5
#: Reminders this many minutes before a regular open; the last is critical.
REMIND_BEFORE_OPEN_MINUTES = (60, 30, 10)
#: A session about to end while the market is open is said this far ahead.
EXPIRY_WARNING_MINUTES = 30
#: The tab states that mean nobody is signed in.
_SIGNED_OUT = ("signed_out", "no_tab")


def _clock_words(seconds: float, now: float) -> str:
    """'09:30 ET' today, 'Mon 09:30 ET' on another day."""
    moment = datetime.fromtimestamp(seconds, EASTERN)
    today = datetime.fromtimestamp(now, EASTERN).date()
    return f"{moment:%H:%M} ET" if moment.date() == today else f"{moment:%a %H:%M} ET"


def regular_day(now: float) -> tuple[float, float] | None:
    """Today's regular session as (open, close) epoch seconds while its close
    is still ahead; None on a day without one, and after the close."""
    from engine.core.venue_sessions import VenueCalendar

    moment = datetime.fromtimestamp(now, EASTERN)
    span = VenueCalendar("fidelity", ("regular",)).day_span(moment.date())
    if span is None or moment >= span[1]:
        return None
    return span[0].timestamp(), span[1].timestamp()


def next_regular_day(now: float) -> tuple[float, float]:
    """The next regular session after today's, as (open, close)."""
    from engine.core import trading_calendar
    from engine.core.venue_sessions import VenueCalendar

    following = trading_calendar.next_session(datetime.fromtimestamp(now, EASTERN).date())
    span = VenueCalendar("fidelity", ("regular",)).day_span(following)
    return span[0].timestamp(), span[1].timestamp()


@dataclass(frozen=True)
class Outlook:
    """The sign-in the tab is on: when it began, when it is expected to end,
    and `short` when that is before the close of a regular session still to
    trade. `detail` and `fix` are the checklist's words."""

    since: float
    expires: float
    short: bool
    detail: str
    fix: str | None = None


@dataclass(frozen=True)
class Notice:
    """One `fidelity_signin` notification the host should publish."""

    title: str
    body: str
    severity: str = "info"
    data: dict[str, Any] | None = None


class SignInWatch:
    """The sign-in the extension's Fidelity tab is on (module docstring).

    Not thread-safe: the bridge host's tick is its only caller."""

    def __init__(self, *, session_hours: float = SESSION_HOURS) -> None:
        self._seconds = session_hours * 3600.0
        self.state: str | None = None  # the tab's state, None while unknown
        self.since: float | None = None  # when this sign-in began, if seen
        self._new = False  # a sign-in began and has not been announced
        self._reminded: set[tuple[float, int]] = set()  # (open, minutes ahead)
        self._expiry_said: float | None = None  # the `since` whose end was said

    # -- what happened ---------------------------------------------------------

    @property
    def expires(self) -> float | None:
        """When Fidelity is expected to end this sign-in, or None."""
        return None if self.since is None else self.since + self._seconds

    def observe(self, state: str | None, now: float) -> None:
        """The tab's state as the extension reports it now; None while the
        extension is away (what was known is kept: a browser that reconnects
        on the signed-in site is on the sign-in it had).

        A sign-in is the tab reaching the signed-in site from the sign-in
        page. From no tab at all it is one only if the sign-in known before
        has run out -- a tab reopened inside a live session is still on it,
        and the earlier end is the safe one to expect. The first word after
        nothing was known says where the tab is, not when it got there."""
        if state is None or state == self.state:
            return
        previous, self.state = self.state, state
        if state != "signed_in":
            if state == "signed_out":
                self.since = None
            return
        if previous == "signed_out" or (
            previous == "no_tab" and (self.expires is None or now >= self.expires)
        ):
            self.since = now
            self._new = True

    def confirmed(self, at: float) -> None:
        """A read-only account check passed at `at`. Past the expected end,
        the session is one whose start was not seen: the start is forgotten."""
        expires = self.expires
        if expires is not None and at > expires:
            self.since = None

    def replay(self, events: Iterable[dict]) -> None:
        """Catch up from the host's event journal (kinds `fidelity`, with a
        `state`, and `check`), oldest first, without announcing anything: a
        restarted host knows the sign-in it was on."""
        for event in sorted(events, key=lambda e: float(e.get("t", 0))):
            kind, at = event.get("kind"), float(event.get("t", 0))
            if kind == "fidelity" and isinstance(event.get("state"), str):
                self.observe(event["state"], at)
            elif kind == "check" and event.get("ok") is True:
                self.confirmed(at)
        self._new = False
        self.state = None  # the journal's last word is not the tab's state now

    # -- what to say -------------------------------------------------------------

    def outlook(self, now: float) -> Outlook | None:
        """For the checklist, while the tab is signed in and the start of the
        sign-in is known; None otherwise."""
        expires = self.expires
        if self.state != "signed_in" or self.since is None or expires is None:
            return None
        began, ends = _clock_words(self.since, now), _clock_words(expires, now)
        if now >= expires:
            return Outlook(
                self.since,
                expires,
                True,
                f"the tab says signed in, but Fidelity ends a session about {SESSION_HOURS:g} h "
                f"after the sign-in and this one began {began}",
                "sign out of Fidelity in that browser and sign in again",
            )
        day = regular_day(now)
        if day is not None and expires < day[1]:
            return Outlook(
                self.since,
                expires,
                True,
                f"signed in since {began}; Fidelity ends the session about {ends}, before the "
                f"{_clock_words(day[1], now)} close",
                "sign out of Fidelity in that browser and sign in again, so the session "
                "lasts to the close",
            )
        return Outlook(
            self.since,
            expires,
            False,
            f"signed in since {began}; Fidelity ends the session about {ends}",
        )

    def notices(self, now: float) -> list[Notice]:
        """What is news at `now` (module docstring, notices): each said once."""
        out: list[Notice] = []
        expires = self.expires
        day = regular_day(now)
        if self._new:
            self._new = False
            if expires is not None:
                out.append(self._signed_in(now, expires, day))
        if day is None:
            return out
        opens, closes = day
        reminder = self._reminder(now, opens, closes)
        if reminder is not None:
            out.append(reminder)
        if (
            self.state == "signed_in"
            and expires is not None
            and self._expiry_said != self.since
            and opens <= now < expires < closes
            and expires - now <= EXPIRY_WARNING_MINUTES * 60
        ):
            self._expiry_said = self.since
            minutes = max(1, round((expires - now) / 60))
            out.append(
                Notice(
                    "Fidelity will sign you out soon",
                    f"Fidelity ends this session about {_clock_words(expires, now)}, in "
                    f"{minutes} min, with the market open until {_clock_words(closes, now)}. "
                    "Sign out and in again now to trade to the close.",
                    "warning",
                    self._data("expiry", expires),
                )
            )
        return out

    def _data(self, reason: str, expires: float | None) -> dict[str, Any]:
        return {
            "state": self.state,
            "reason": reason,
            "since": _iso(self.since),
            "expires": _iso(expires),
        }

    def _signed_in(self, now: float, expires: float, day: tuple[float, float] | None) -> Notice:
        ends = _clock_words(expires, now)
        if day is not None and expires < day[1]:
            return Notice(
                "Signed in to Fidelity -- not for the whole day",
                f"Fidelity ends this session about {ends}, before the "
                f"{_clock_words(day[1], now)} close. Sign in again after "
                f"{_clock_words(day[1] - self._seconds, now)} to last the day.",
                "warning",
                self._data("signed_in", expires),
            )
        body = (
            f"Fidelity ends a session about {SESSION_HOURS:g} h after the sign-in: this one "
            f"about {ends}."
        )
        if day is None:
            opens, closes = next_regular_day(now)
            if expires < closes:
                body += (
                    f" That is before the {_clock_words(closes, now)} close: sign in again "
                    f"between {_clock_words(closes - self._seconds, now)} and the "
                    f"{_clock_words(opens, now)} open."
                )
        return Notice("Signed in to Fidelity", body, "info", self._data("signed_in", expires))

    def _reminder(self, now: float, opens: float, closes: float) -> Notice | None:
        """The most urgent reminder now due before `opens`, if the tab needs a
        person. A reminder whose time has come is spent either way: the next
        one looks again."""
        due = [
            minutes
            for minutes in REMIND_BEFORE_OPEN_MINUTES
            if opens - minutes * 60 <= now < opens and (opens, minutes) not in self._reminded
        ]
        if not due:
            return None
        self._reminded = {key for key in self._reminded if key[0] >= opens}
        self._reminded.update((opens, minutes) for minutes in due)
        last = min(due) == min(REMIND_BEFORE_OPEN_MINUTES)
        left = max(1, round((opens - now) / 60))
        severity = "critical" if last else "warning"
        expires = self.expires
        if self.state in _SIGNED_OUT:
            what = "Fidelity is signed out" if self.state == "signed_out" else "No Fidelity tab"
            return Notice(
                f"Sign in to Fidelity: the market opens in {left} min",
                f"{what} in the browser the extension runs in. Sign in there before "
                f"{_clock_words(opens, now)}; nothing is traded until you do.",
                severity,
                self._data("reminder", None),
            )
        if self.state == "signed_in" and expires is not None and expires < closes:
            ends = _clock_words(expires, now)
            gone = "ended" if now >= expires else "ends"
            return Notice(
                f"Sign in to Fidelity again: the market opens in {left} min",
                f"The Fidelity session in the browser {gone} about {ends}, before the "
                f"{_clock_words(closes, now)} close. Sign out and in again before "
                f"{_clock_words(opens, now)}, so it lasts the day.",
                severity,
                self._data("reminder", expires),
            )
        return None


#: The extension's assisted sign-in (its assisted-sign-in.js), by the one word
#: it sends: (title, body, severity). The words are the engine's own -- the
#: extension sends an outcome and a time, never text to show. An outcome not
#: listed here ("opened", "wrong_page", one a newer extension invented) is
#: journaled and not sent to a phone.
ASSISTED_OUTCOMES: dict[str, tuple[str, str, str]] = {
    "submitted": (
        "Assisted sign-in: form submitted",
        "The extension pressed the button of Fidelity's filled-in sign-in form. Approve the "
        "prompt on your phone if Fidelity sends one.",
        "info",
    ),
    "succeeded": ("Assisted sign-in: signed in", "Fidelity is signed in.", "info"),
    "needs_click": (
        "Assisted sign-in needs a click",
        "The browser shows a saved password but keeps it from the page until someone clicks "
        "there. Click once on the Fidelity sign-in page, or sign in yourself.",
        "warning",
    ),
    "not_filled": (
        "Assisted sign-in: the form was not filled in",
        "The browser did not fill Fidelity's sign-in form. Sign in yourself, and check the "
        "password is saved in that browser.",
        "warning",
    ),
    "no_form": (
        "Assisted sign-in: no sign-in form found",
        "Fidelity's sign-in page showed no form to press. It may be waiting for your second "
        "factor, or the page has changed. Sign in yourself.",
        "warning",
    ),
    "failed": (
        "Assisted sign-in could not look at the page",
        "The extension could not look at Fidelity's sign-in page. Sign in yourself.",
        "warning",
    ),
    "held": (
        "Assisted sign-in stopped",
        "The sign-in form was submitted but Fidelity did not sign in. The extension will not "
        "try again until a sign-in succeeds: sign in yourself.",
        "critical",
    ),
}


def assisted_notice(data: object) -> Notice | None:
    """The extension's `signin` event as a notice, or None for an outcome a
    phone is not told (and for anything that is not such an event)."""
    outcome = data.get("outcome") if isinstance(data, dict) else None
    words = ASSISTED_OUTCOMES.get(outcome) if isinstance(outcome, str) else None
    if words is None:
        return None
    title, body, severity = words
    return Notice(title, body, severity, {"reason": "assisted", "outcome": outcome})


def _iso(seconds: float | None) -> str | None:
    if seconds is None:
        return None
    return datetime.fromtimestamp(seconds, EASTERN).isoformat(timespec="seconds")


__all__ = [
    "ASSISTED_OUTCOMES",
    "EXPIRY_WARNING_MINUTES",
    "REMIND_BEFORE_OPEN_MINUTES",
    "SESSION_HOURS",
    "Notice",
    "Outlook",
    "SignInWatch",
    "assisted_notice",
    "next_regular_day",
    "regular_day",
]
