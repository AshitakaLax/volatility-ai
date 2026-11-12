"""Tests for src/earnings_calendar.py.

Mirrors engine/tests/test_fomc_calendar.py: pins a sample of the sourced
dates rather than all 296 (the full list is a generated data artifact,
not logic to re-derive), plus the join semantics the module docstring
documents.

The distinction this module gets wrong most easily is announcement date
vs reaction session, so that is pinned explicitly in both directions
rather than left implied by a count.
"""

from __future__ import annotations

from datetime import UTC, date, datetime
from zoneinfo import ZoneInfo

import pytest

from engine.data.earnings_calendar import (
    EARNINGS_REACTION_DATES,
    MEGA_CAP_SYMBOLS,
    REACTION_FILE,
    is_earnings_reaction_day,
    is_earnings_reaction_day_at,
    is_live_earnings_reaction_day_at,
    reaction_file,
    read_later_reaction_dates,
)
from engine.data.fomc_calendar import FOMC_DECISION_DATES

EASTERN = ZoneInfo("America/New_York")


@pytest.mark.parametrize(
    "d",
    [
        date(2016, 1, 20),  # first date in the calendar
        date(2016, 1, 27),  # session after AAPL's 2016-01-26 after-close report
        date(2020, 3, 13),  # a reaction session inside the COVID crash week
        date(2023, 5, 25),  # session after NVDA's 2023-05-24 AI-guidance report
        date(2026, 7, 31),  # the last date in the calendar as generated
        date(2026, 8, 27),  # session after NVDA's 2026-08-26 report (from EDGAR)
        date(2026, 11, 3),  # session after AAPL's 2026-11-02 report (from EDGAR)
    ],
)
def test_known_reaction_sessions_are_flagged(d):
    assert is_earnings_reaction_day(d) is True


@pytest.mark.parametrize(
    "d",
    [
        date(2016, 1, 26),  # AAPL's ANNOUNCEMENT date -- the move is next morning
        date(2023, 5, 24),  # NVDA's announcement date, same reason
        date(2019, 6, 20),  # an ordinary non-earnings session
        date(2021, 12, 31),  # year-end, nowhere near a reporting cluster
    ],
)
def test_announcement_dates_and_ordinary_days_are_not_flagged(d):
    assert is_earnings_reaction_day(d) is False


def test_the_calendar_is_the_documented_size():
    """The module docstring quotes 296 sessions from 385 announcements as
    generated (through 2026-07-31), which its measured-effect numbers were
    taken on, and seven added from EDGAR since. If either changes, that
    docstring must change with it."""
    generated = [d for d in EARNINGS_REACTION_DATES if d <= date(2026, 7, 31)]
    assert len(generated) == 296
    assert len(EARNINGS_REACTION_DATES) == 296 + 7


def test_every_date_is_a_weekday():
    """A reaction session is a trading session. A Saturday or Sunday in
    here would mean the announcement-to-next-session mapping walked off
    the trading calendar instead of onto it."""
    weekend = sorted(d for d in EARNINGS_REACTION_DATES if d.weekday() >= 5)
    assert weekend == []


def test_every_date_falls_inside_the_dataset_window():
    """The calendar is only meaningful over the range it was generated
    for; a date outside it would silently never match a bar."""
    assert min(EARNINGS_REACTION_DATES) >= date(2016, 1, 1)
    assert max(EARNINGS_REACTION_DATES) <= date(2026, 11, 3)


def test_every_year_in_range_has_reaction_sessions():
    """Nine companies reporting quarterly cannot produce an empty year.
    An empty one would mean a generation gap, not a real quiet period."""
    for year in range(2016, 2027):
        assert any(d.year == year for d in EARNINGS_REACTION_DATES), (
            f"{year} has no earnings reaction sessions, which is not possible "
            f"for {len(MEGA_CAP_SYMBOLS)} quarterly reporters"
        )


def test_overlap_with_the_fomc_calendar_is_the_documented_amount():
    """Documented as 14 in both this module and high_frequency_sizing's
    docstring, and it is what makes the max()-not-multiply combination
    rule matter. Pinned so the two calendars cannot drift apart
    unnoticed."""
    overlap = EARNINGS_REACTION_DATES & FOMC_DECISION_DATES
    assert len(overlap) == 14


def test_a_utc_timestamp_before_eastern_midnight_rollover_is_still_the_prior_day():
    """22:00 UTC on 2016-01-27 is 17:00 Eastern the SAME day, so it must
    still match -- the naive UTC date and the Eastern date agree here."""
    assert is_earnings_reaction_day_at(datetime(2016, 1, 27, 22, 0, tzinfo=UTC)) is True


def test_a_late_utc_timestamp_that_has_already_rolled_to_the_next_utc_day():
    """02:00 UTC on 2016-01-28 is 21:00 Eastern on 2016-01-27. Matching
    on the raw UTC date would look up the 28th and get the wrong answer
    for the 27th's session."""
    assert is_earnings_reaction_day_at(datetime(2016, 1, 28, 2, 0, tzinfo=UTC)) is True


def test_a_naive_timestamp_is_treated_as_utc_not_local_time():
    """Same instant as above without tzinfo. The result must not depend
    on the host machine's timezone."""
    assert is_earnings_reaction_day_at(datetime(2016, 1, 28, 2, 0)) is True


def test_matches_hand_computed_eastern_conversion():
    """An explicitly Eastern-localized timestamp and the plain date
    lookup must agree."""
    eastern_noon = datetime(2016, 1, 27, 12, 0, tzinfo=EASTERN)
    assert is_earnings_reaction_day_at(eastern_noon) is is_earnings_reaction_day(date(2016, 1, 27))


def test_symbols_are_deduplicated_and_exclude_the_goog_share_class():
    """GOOG is deliberately omitted: it reports the same day as GOOGL
    and would only contribute duplicate dates (see module docstring)."""
    assert len(set(MEGA_CAP_SYMBOLS)) == len(MEGA_CAP_SYMBOLS)
    assert "GOOGL" in MEGA_CAP_SYMBOLS
    assert "GOOG" not in MEGA_CAP_SYMBOLS


# --- live: the list, and the sessions after it ---------------------------------

LAST = max(EARNINGS_REACTION_DATES)


def _file(tmp_path, *rows) -> object:
    path = tmp_path / REACTION_FILE
    path.write_text("date,symbols\n" + "".join(f"{day},{symbols}\n" for day, symbols in rows))
    return path


def test_the_file_adds_only_sessions_after_the_list_and_only_for_its_companies(tmp_path):
    path = _file(
        tmp_path,
        ("2016-01-21", "NFLX"),  # before the list's end: the list already decides it
        (str(LAST), "AAPL"),
        ("2026-11-20", "NVDA"),
        ("2026-11-21", "NVDA"),  # a Saturday: not a session
        ("2026-12-11", "AVGO COST"),
        ("2026-12-17", "MU"),  # not one of the nine
        ("not a date", "NVDA"),
        ("2027-01-28", ""),
    )
    assert read_later_reaction_dates(path) == {date(2026, 11, 20), date(2026, 12, 11)}


def test_no_file_leaves_the_list_as_it_is(tmp_path):
    assert read_later_reaction_dates(tmp_path / "absent.csv") == frozenset()
    assert read_later_reaction_dates(tmp_path) == frozenset()  # a directory, not a file


def test_a_live_loop_sees_a_later_session_and_a_backtest_does_not(tmp_path):
    later = read_later_reaction_dates(_file(tmp_path, ("2026-11-20", "NVDA")))
    morning = datetime(2026, 11, 20, 15, 0, tzinfo=UTC)  # 10:00 Eastern
    assert is_live_earnings_reaction_day_at(morning, later) is True
    assert is_earnings_reaction_day_at(morning) is False
    assert date(2026, 11, 20) not in EARNINGS_REACTION_DATES
    # A session in the list is flagged with or without the file.
    listed = datetime(2026, 11, 3, 15, 0, tzinfo=UTC)
    assert is_live_earnings_reaction_day_at(listed, frozenset()) is True
    assert is_live_earnings_reaction_day_at(morning, frozenset()) is False


def test_the_file_is_looked_for_where_the_refresh_writes_it(tmp_path, monkeypatch):
    monkeypatch.setenv("VAI_EXTERNAL_DIR", str(tmp_path))
    assert reaction_file() == tmp_path / REACTION_FILE
    monkeypatch.delenv("VAI_EXTERNAL_DIR")
    assert reaction_file().parts[-3:] == ("data", "external", REACTION_FILE)
