"""tools/refresh_external.py's earnings step and tools/preflight.py's check of
what a strategy reads from outside its bars. No network; the clock is given."""

from __future__ import annotations

from datetime import date, timedelta
from types import SimpleNamespace

import pandas as pd
import pytest

from engine.data.earnings_calendar import EARNINGS_REACTION_DATES
from engine.data.event_calendar import EarningsEventTable
from engine.data.fomc_calendar import FOMC_DECISION_DATES
from research.ml import sources
from research.strategies.risk_governor import CORE_SIGNALS, SIGNALS
from tools import preflight
from tools import refresh_external as R

LAST_KNOWN = max(EARNINGS_REACTION_DATES)


def releases(*rows) -> pd.DataFrame:
    """(symbol, 'YYYY-MM-DD HH:MM' Eastern) rows as fetch_edgar_earnings returns them."""
    et = pd.to_datetime([r[1] for r in rows])
    frame = pd.DataFrame(
        {
            "symbol": [r[0] for r in rows],
            "release_et": et,
            "release_utc": et.tz_localize("America/New_York").tz_convert("UTC"),
            "accession": [f"acc-{i}" for i in range(len(rows))],
        }
    )
    return frame.sort_values(["release_utc", "symbol"]).reset_index(drop=True)


# -- reaction sessions -----------------------------------------------------------


@pytest.mark.parametrize(
    ("release", "session"),
    [
        ("2026-08-26 16:21", date(2026, 8, 27)),  # after the close: the next session
        ("2026-08-20 07:02", date(2026, 8, 20)),  # before the open: that day
        ("2026-08-20 11:30", date(2026, 8, 20)),  # during the session
        ("2026-08-21 16:05", date(2026, 8, 24)),  # a Friday evening: Monday
        ("2026-08-22 09:00", date(2026, 8, 24)),  # a Saturday
    ],
)
def test_the_session_that_first_trades_on_a_release(release, session):
    assert R.reaction_day(pd.Timestamp(release)) == session


def test_the_engine_reads_the_file_this_writes(tmp_path):
    """One name and one shape on both sides: the live loop's later reaction
    sessions are exactly what a refresh wrote, for the engine's companies."""
    from engine.data import earnings_calendar

    assert R.REACTION_FILE == earnings_calendar.REACTION_FILE
    assert set(R.REACTION_REPORTERS) == set(earnings_calendar.MEGA_CAP_SYMBOLS)
    after = LAST_KNOWN + timedelta(days=30)
    while after.weekday() != 2:
        after += timedelta(days=1)
    fresh = releases(
        ("NVDA", f"{after} 16:21"), ("AAPL", f"{LAST_KNOWN - timedelta(days=400)} 16:30")
    )
    R.earnings_lines(tmp_path, after + timedelta(days=5), lambda: fresh)
    later = earnings_calendar.read_later_reaction_dates(tmp_path / R.REACTION_FILE)
    assert later == {after + timedelta(days=1)}


def test_reaction_days_are_the_listed_reporters_only():
    found = R.reaction_days(
        releases(
            ("GOOGL", "2026-10-28 16:01"),
            ("MSFT", "2026-10-28 16:04"),
            ("WMT", "2026-08-20 07:02"),  # not one of the engine's nine
            ("GOOG", "2026-10-28 16:01"),  # the same report as GOOGL
        )
    )
    assert found == {date(2026, 10, 29): ["GOOGL", "MSFT"]}
    assert "WMT" not in R.REACTION_REPORTERS
    assert set(R.REACTION_REPORTERS) <= set(sources.EARNINGS_REPORTERS)


# -- the calendar the event table loads -----------------------------------------

CALENDAR = (
    "symbol,release_et,release_utc,postclose_peak_volume\n"
    "NVDA,2026-05-20T16:20:00,2026-05-20T20:20:00+00:00,1200000\n"
    "MSFT,2026-07-28T16:05:00,2026-07-28T20:05:00+00:00,800000\n"
    "AAPL,2026-07-30T16:30:00,2026-07-30T20:30:00+00:00,900000\n"
)
FRESH = releases(
    ("NVDA", "2026-05-20 16:21"),  # the same release, a minute apart: not again
    ("MSFT", "2026-07-28 16:04"),
    ("NVDA", "2026-08-26 16:21"),
    ("COST", "2026-09-24 16:15"),  # not a reporter the file holds
    ("MSFT", "2026-10-28 16:04"),
)


def test_only_new_releases_are_appended_and_nothing_stored_is_rewritten(tmp_path):
    path = tmp_path / "earnings_releases_derived.csv"
    path.write_text(CALENDAR)
    assert R.extend_releases(path, FRESH) == 2
    text = path.read_text()
    assert text.startswith(CALENDAR)
    assert text[len(CALENDAR) :].splitlines() == [
        "NVDA,2026-08-26T16:21:00,2026-08-26T20:21:00+00:00,",
        "MSFT,2026-10-28T16:04:00,2026-10-28T20:04:00+00:00,",
    ]
    assert R.extend_releases(path, FRESH) == 0  # a second run adds nothing
    assert path.read_text() == text


def test_the_engines_event_table_loads_the_extended_calendar(tmp_path):
    path = tmp_path / "earnings_releases_derived.csv"
    path.write_text(CALENDAR)
    before = EarningsEventTable.from_csv(path).event_count
    R.extend_releases(path, FRESH)
    table = EarningsEventTable.from_csv(path)
    assert table.event_count == before + 2
    stamps = pd.to_datetime(pd.read_csv(path)["release_utc"], utc=True)
    assert stamps.is_monotonic_increasing


def test_a_file_that_is_not_an_earnings_calendar_is_refused(tmp_path):
    path = tmp_path / "other.csv"
    path.write_text("date,value\n2026-01-01,1\n")
    with pytest.raises(ValueError, match="symbol and release_utc"):
        R.extend_releases(path, FRESH)


# -- the step --------------------------------------------------------------------


def test_the_step_stores_the_releases_and_names_what_the_engine_lacks(tmp_path):
    calendar = tmp_path / "earnings_releases_derived.csv"
    calendar.write_text(CALENDAR)
    after = LAST_KNOWN + timedelta(days=30)
    while after.weekday() != 2:  # a Wednesday, so the reaction session is Thursday
        after += timedelta(days=1)
    fresh = releases(("NVDA", f"{after} 16:21"), ("WMT", f"{after} 07:02"))
    today = after + timedelta(days=5)
    lines = R.earnings_lines(tmp_path, today, lambda: fresh, calendar)
    assert lines[0] == f"earnings: 2 releases from the SEC, to {after}"
    assert "1 release(s) appended" in lines[1]
    assert f"ends {LAST_KNOWN} and lacks 1 reaction session(s)" in lines[2]
    assert str(after + timedelta(days=1)) in lines[2]
    stored = pd.read_csv(tmp_path / R.EARNINGS_FILE)
    assert list(stored["symbol"]) == ["WMT", "NVDA"]
    reactions = (tmp_path / R.REACTION_FILE).read_text().splitlines()
    assert reactions == ["date,symbols", f"{after + timedelta(days=1)},NVDA"]


def test_a_release_still_ahead_of_today_is_not_called_missed(tmp_path):
    fresh = releases(("NVDA", f"{LAST_KNOWN - timedelta(days=200)} 16:21"))
    lines = R.earnings_lines(tmp_path, LAST_KNOWN, lambda: fresh)
    assert lines[-1] == f"  the engine's earnings list is current to {LAST_KNOWN}"


def test_the_sec_being_down_is_one_line_and_nothing_is_written(tmp_path):
    def down():
        raise sources.SourceUnavailable("HTTP 503")

    assert R.earnings_lines(tmp_path, date(2026, 11, 10), down) == [
        "earnings releases not fetched: HTTP 503"
    ]
    assert list(tmp_path.iterdir()) == []


def test_a_missing_calendar_is_said_not_made(tmp_path):
    fresh = releases(("NVDA", "2026-08-26 16:21"))
    lines = R.earnings_lines(tmp_path, date(2026, 11, 10), lambda: fresh, tmp_path / "none.csv")
    assert "is not there to extend" in lines[1]
    assert not (tmp_path / "none.csv").exists()


# -- preflight -------------------------------------------------------------------


def config(**params) -> SimpleNamespace:
    return SimpleNamespace(strategy=SimpleNamespace(strategy_params=params))


def rows(report: preflight.Report) -> dict[str, tuple[str, str]]:
    return {name: (status, detail) for status, name, detail in report.rows}


def test_preflight_warns_when_a_calendar_a_boost_reads_has_run_out():
    report = preflight.Report()
    boosted = config(event_day_boost_multiplier=2.5, earnings_day_boost_multiplier=1.5)
    preflight.check_outside_data(report, boosted, today=LAST_KNOWN + timedelta(days=10))
    found = rows(report)
    assert found["FOMC calendar"][0] == preflight.PASS
    assert found["earnings calendar"] == (preflight.PASS, f"to {LAST_KNOWN}")

    report = preflight.Report()
    late = max(max(FOMC_DECISION_DATES), LAST_KNOWN) + timedelta(days=200)
    preflight.check_outside_data(report, boosted, today=late)
    found = rows(report)
    assert found["FOMC calendar"][0] == preflight.WARN
    assert "event-day sizing (x2.5) is off" in found["FOMC calendar"][1]
    assert found["earnings calendar"][0] == preflight.WARN
    assert "market-inputs" in found["earnings calendar"][1]
    assert report.render() == 0  # a warning never fails the run


def test_preflight_counts_the_sessions_the_refresh_service_has_added(tmp_path, monkeypatch):
    """A live loop reads the list and the file; so does the check."""
    recent = LAST_KNOWN + timedelta(days=150)
    while recent.weekday() >= 5:
        recent += timedelta(days=1)
    (tmp_path / R.REACTION_FILE).write_text(f"date,symbols\n{recent},NVDA\n")
    monkeypatch.setenv("VAI_EXTERNAL_DIR", str(tmp_path))
    report = preflight.Report()
    preflight.check_outside_data(
        report, config(earnings_day_boost_multiplier=1.5), today=recent + timedelta(days=20)
    )
    status, detail = rows(report)["earnings calendar"]
    assert status == preflight.PASS
    assert detail == f"to {recent}, 1 session(s) from {R.REACTION_FILE}"


def test_preflight_says_nothing_about_a_calendar_no_boost_reads():
    report = preflight.Report()
    preflight.check_outside_data(report, config(per_lot_pct=0.01), today=date(2030, 1, 2))
    assert report.rows == []


def test_preflight_reads_the_governor_and_names_what_is_stale(tmp_path):
    sessions = pd.bdate_range("2025-01-02", "2026-10-22")
    stamps = sessions.tz_localize("UTC") + pd.Timedelta(hours=21)
    for key in {k for name in CORE_SIGNALS for k in SIGNALS[name].inputs}:
        pd.DataFrame({"timestamp": stamps, "close": 100.0}).to_csv(
            tmp_path / f"{key}.csv", index=False
        )
    governed = config(caution_min_votes=4, caution_dir=str(tmp_path))
    report = preflight.Report()
    preflight.check_outside_data(report, governed, today=date(2026, 10, 23))
    status, detail = rows(report)["risk governor"]
    assert status == preflight.PASS and detail == "0 of 5 warnings raised for 2026-10-23"

    report = preflight.Report()
    preflight.check_outside_data(report, governed, today=date(2026, 12, 1))
    status, detail = rows(report)["risk governor"]
    assert status == preflight.WARN and "STALE" in detail and "market-inputs" in detail

    report = preflight.Report()
    preflight.check_outside_data(
        report, config(caution_min_votes=4, caution_dir=str(tmp_path / "none")), today=date.today()
    )
    assert rows(report)["risk governor"][0] == preflight.FAIL
