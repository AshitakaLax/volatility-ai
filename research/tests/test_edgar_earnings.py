"""Earnings releases from SEC EDGAR (research/ml/sources.py): which filings
count, the one-a-quarter rule, the contact the SEC is sent, and the pages
asked for. No network: every request goes through a patched _http_get."""

from __future__ import annotations

import json
from datetime import date

import pandas as pd
import pytest

from research.ml import sources
from tools.build_earnings_calendar import TICKERS

CONTACT = "ops desk, 1 Example Road"


def filings(*rows) -> dict:
    """EDGAR's column layout from (form, items, accepted, accession) rows."""
    return {
        "form": [r[0] for r in rows],
        "items": [r[1] for r in rows],
        "acceptanceDateTime": [r[2] for r in rows],
        "accessionNumber": [r[3] for r in rows],
    }


def stamp(text: str) -> pd.Timestamp:
    return pd.Timestamp(text, tz="UTC")


@pytest.fixture
def edgar(monkeypatch):
    """{file name: payload}; records each request's name and User-Agent."""
    pages: dict[str, dict] = {}
    asked: list[tuple[str, str | None]] = []

    def fake_get(url: str, *, retries: int = 3, user_agent: str | None = None) -> bytes:
        name = url.removeprefix(sources.SEC_SUBMISSIONS_URL)
        asked.append((name, user_agent))
        if name not in pages:
            raise sources.SourceUnavailable(f"{url}: HTTP 404")
        return json.dumps(pages[name]).encode()

    monkeypatch.setattr(sources, "_http_get", fake_get)
    monkeypatch.delenv(sources.SEC_CONTACT_ENV, raising=False)
    return pages, asked


def company(ticker: str, recent: dict, files=()) -> dict:
    return {"tickers": [ticker], "filings": {"recent": recent, "files": list(files)}}


# -- which filings ---------------------------------------------------------------


def test_only_an_8k_furnishing_results_is_a_release():
    found = sources.earnings_releases(
        filings(
            ("8-K", "2.02,9.01", "2026-08-26T20:21:19.000Z", "a-1"),
            ("8-K", "5.02", "2026-08-01T20:00:00.000Z", "a-2"),  # an officer change
            ("10-Q", "", "2026-08-27T20:30:00.000Z", "a-3"),
            ("8-K/A", "2.02", "2026-08-28T20:30:00.000Z", "a-4"),  # an amendment
            ("8-K", "12.02", "2026-08-29T20:30:00.000Z", "a-5"),  # not item 2.02
            ("8-K", "2.02", "not a time", "a-6"),
        )
    )
    assert found == [(stamp("2026-08-26 20:21:19"), "a-1")]


def test_of_two_releases_in_a_quarter_the_later_is_the_report():
    deliveries, results = (stamp("2026-10-02 13:00"), "d"), (stamp("2026-10-21 20:41"), "r")
    last_quarter = (stamp("2026-07-22 20:30"), "q")
    assert sources.quarterly([results, deliveries, last_quarter]) == [last_quarter, results]
    # Alone, the newest stands until a later one arrives inside the spacing.
    assert sources.quarterly([last_quarter, deliveries]) == [last_quarter, deliveries]


# -- the contact -----------------------------------------------------------------


def test_the_sec_is_told_who_is_asking_or_is_not_asked(edgar, monkeypatch):
    pages, asked = edgar
    with pytest.raises(sources.SourceUnavailable, match=sources.SEC_CONTACT_ENV):
        sources.fetch_edgar_earnings({"NVDA": 1045810})
    assert asked == []
    pages["CIK0001045810.json"] = company(
        "NVDA", filings(("8-K", "2.02,9.01", "2026-08-26T20:21:19.000Z", "a-1"))
    )
    monkeypatch.setenv(sources.SEC_CONTACT_ENV, CONTACT)
    sources.fetch_edgar_earnings({"NVDA": 1045810}, sleep=lambda s: None)
    assert asked == [("CIK0001045810.json", f"volatility-ai {CONTACT}")]


def test_the_contact_is_not_in_the_source():
    """It is the operator's, read from the environment at run time."""
    text = (sources.Path(sources.__file__)).read_text(encoding="utf-8")
    assert "@" not in sources.sec_user_agent("x").removeprefix("volatility-ai ")
    assert sources.SEC_CONTACT_ENV in text and "sec_user_agent" in text


# -- a fetch ---------------------------------------------------------------------


def test_releases_come_back_in_order_with_eastern_and_utc_times(edgar):
    pages, _ = edgar
    pages["CIK0001045810.json"] = company(
        "NVDA",
        filings(
            ("8-K", "2.02,9.01", "2026-08-26T20:21:19.000Z", "n-2"),
            ("8-K", "2.02,9.01", "2026-05-20T20:21:19.000Z", "n-1"),
        ),
    )
    pages["CIK0000104169.json"] = company(
        "WMT", filings(("8-K", "2.02,9.01", "2026-08-20T11:02:00.000Z", "w-1"))
    )
    slept: list[float] = []
    frame = sources.fetch_edgar_earnings(
        {"NVDA": 1045810, "WMT": 104169}, contact=CONTACT, sleep=slept.append
    )
    assert list(frame.columns) == ["symbol", "release_et", "release_utc", "accession"]
    assert list(frame["accession"]) == ["n-1", "w-1", "n-2"]
    assert frame["release_et"].iloc[1] == pd.Timestamp("2026-08-20 07:02")  # before the open
    assert frame["release_et"].iloc[2] == pd.Timestamp("2026-08-26 16:21:19")
    assert frame["release_utc"].iloc[2] == stamp("2026-08-26 20:21:19")
    assert slept == [sources.SEC_PAUSE_SECONDS]  # a pause between requests, none before the first


def test_one_registrant_is_asked_once_for_both_its_tickers(edgar):
    pages, asked = edgar
    alphabet = filings(("8-K", "2.02,9.01", "2026-10-28T20:01:33.000Z", "g-1"))
    pages["CIK0001652044.json"] = {"tickers": ["GOOGL", "GOOG"], "filings": {"recent": alphabet}}
    frame = sources.fetch_edgar_earnings(
        {"GOOGL": 1652044, "GOOG": 1652044}, contact=CONTACT, sleep=lambda s: None
    )
    assert len(asked) == 1
    assert list(frame["symbol"]) == ["GOOG", "GOOGL"] and frame["accession"].nunique() == 1


def test_older_pages_are_asked_for_only_when_the_window_reaches_them(edgar):
    pages, asked = edgar
    older = [
        {"name": "CIK0000320193-submissions-001.json", "filingTo": "2020-09-16"},
        {"name": "CIK0000320193-submissions-002.json", "filingTo": "2012-01-05"},
    ]
    pages["CIK0000320193.json"] = company(
        "AAPL", filings(("8-K", "2.02", "2026-07-30T20:30:00.000Z", "a-9")), older
    )
    pages["CIK0000320193-submissions-001.json"] = filings(
        ("8-K", "2.02", "2019-07-30T20:30:00.000Z", "a-2"),
        ("8-K", "2.02", "2015-07-21T20:30:00.000Z", "a-1"),
    )
    recent = sources.fetch_edgar_earnings(
        {"AAPL": 320193}, since=date(2021, 1, 1), contact=CONTACT, sleep=lambda s: None
    )
    assert [name for name, _ in asked] == ["CIK0000320193.json"]
    assert list(recent["accession"]) == ["a-9"]
    asked.clear()
    full = sources.fetch_edgar_earnings(
        {"AAPL": 320193}, since=date(2016, 1, 1), contact=CONTACT, sleep=lambda s: None
    )
    assert [name for name, _ in asked] == [
        "CIK0000320193.json",
        "CIK0000320193-submissions-001.json",
    ]
    assert list(full["accession"]) == ["a-2", "a-9"]  # 2015 is before the window


def test_a_cik_that_files_under_another_ticker_is_refused(edgar):
    pages, _ = edgar
    pages["CIK0000000001.json"] = company("ZZZ", filings())
    with pytest.raises(sources.SourceUnavailable, match="not NVDA"):
        sources.fetch_edgar_earnings({"NVDA": 1}, contact=CONTACT, sleep=lambda s: None)


def test_the_reporters_are_the_earnings_calendars():
    assert set(sources.EARNINGS_REPORTERS) == set(TICKERS)
    assert sources.EARNINGS_REPORTERS["GOOG"] == sources.EARNINGS_REPORTERS["GOOGL"]
