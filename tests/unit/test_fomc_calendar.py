"""Tests for src/fomc_calendar.py.

Pins a sample of the sourced dates directly (not exhaustively -- the
full list is a data-entry artifact verified against federalreserve.gov,
not logic to re-derive), plus the join semantics the module docstring
documents: Eastern-date conversion, naive-timestamp-as-UTC handling,
and the 2020 emergency-action special cases.
"""

from __future__ import annotations

from datetime import UTC, date, datetime
from zoneinfo import ZoneInfo

import pytest

from src.fomc_calendar import is_fomc_day, is_fomc_day_at

EASTERN = ZoneInfo("America/New_York")


@pytest.mark.parametrize(
    "d",
    [
        date(2016, 3, 16),  # first date in the calendar (quarterly-only era)
        date(2018, 12, 19),  # last quarterly-only-era date
        date(2019, 1, 30),  # first date of the every-meeting era
        date(2020, 3, 3),  # unscheduled emergency 50bp cut
        date(2020, 3, 16),  # market's first session after the Sunday zero-rate/QE announcement
        date(2024, 9, 18),
        date(2026, 7, 29),  # most recent date in the calendar at write time
    ],
)
def test_known_fomc_decision_dates_are_flagged(d):
    assert is_fomc_day(d) is True


@pytest.mark.parametrize(
    "d",
    [
        date(2016, 3, 15),  # day 1 of a 2-day meeting -- not the decision day
        date(2020, 3, 17),  # the regular meeting the emergency actions superseded
        date(2020, 3, 15),  # the Sunday announcement itself, not the next trading session
        date(2016, 1, 27),  # 2016 meeting WITHOUT a press conference (quarterly-only era)
        date(2024, 6, 13),  # an ordinary non-FOMC day
        date(2030, 1, 1),  # outside the calendar's covered range
    ],
)
def test_non_decision_dates_are_not_flagged(d):
    assert is_fomc_day(d) is False


def test_every_quarterly_era_year_has_exactly_four_dates():
    """2016-2018: only the SEP-projection meetings (Mar/Jun/Sep/Dec)
    had a press conference -- four per year, not eight."""
    from src.fomc_calendar import FOMC_DECISION_DATES

    for year in (2016, 2017, 2018):
        assert sum(1 for d in FOMC_DECISION_DATES if d.year == year) == 4


def test_every_meeting_era_year_has_eight_dates():
    """2021 onward (a full, non-pandemic year): every regular meeting
    has a press conference -- eight per year."""
    from src.fomc_calendar import FOMC_DECISION_DATES

    for year in (2021, 2022, 2023, 2024, 2025):
        assert sum(1 for d in FOMC_DECISION_DATES if d.year == year) == 8


# --- is_fomc_day_at: the timestamp -> Eastern-date join ---


def test_a_utc_timestamp_before_eastern_midnight_rollover_is_still_the_prior_day():
    """9:30am ET market open on an FOMC day, expressed in UTC (EST,
    UTC-5 in January), must still resolve to the Eastern date."""
    ts = datetime(2019, 1, 30, 14, 30, tzinfo=UTC)  # 2019-01-30 09:30 ET
    assert is_fomc_day_at(ts) is True


def test_a_late_utc_timestamp_that_has_already_rolled_to_the_next_utc_day():
    """Just before UTC midnight is still the SAME Eastern trading day
    (market closes at 16:00 ET = 21:00 UTC in winter, well before
    midnight) -- this pins that the conversion, not a bare .date() on
    the UTC value, is what determines the match."""
    ts = datetime(2019, 1, 30, 23, 0, tzinfo=UTC)  # still 2019-01-30 18:00 ET
    assert is_fomc_day_at(ts) is True
    # But 2019-01-31 00:30 UTC is 2019-01-30 19:30 ET -- same Eastern day,
    # different UTC calendar date. A naive UTC .date() would wrongly say "no".
    ts2 = datetime(2019, 1, 31, 0, 30, tzinfo=UTC)
    assert is_fomc_day_at(ts2) is True


def test_a_naive_timestamp_is_treated_as_utc_not_local_time():
    """Reproducibility: a naive input must resolve identically
    regardless of the host machine's local timezone."""
    naive = datetime(2019, 1, 30, 14, 30)  # no tzinfo
    aware = datetime(2019, 1, 30, 14, 30, tzinfo=UTC)
    assert is_fomc_day_at(naive) == is_fomc_day_at(aware) is True


def test_matches_hand_computed_eastern_conversion():
    """Cross-check against an independently constructed Eastern
    timestamp for the same instant, rather than only against this
    module's own conversion logic."""
    eastern_ts = datetime(2020, 3, 3, 10, 0, tzinfo=EASTERN)  # 2020-03-03 10:00 ET
    utc_ts = eastern_ts.astimezone(UTC)
    assert is_fomc_day_at(utc_ts) is True
