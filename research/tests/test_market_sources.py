"""research/ml/sources.py: the registry's keys, and the fetchers added for
the risk governor (OFR, CFTC, SqueezeMetrics, the FOMC calendar) against
canned answers. No network: every fetch goes through a patched _http_get."""

from __future__ import annotations

import json
from datetime import date

import pandas as pd
import pytest

from research.ml import sources


@pytest.fixture
def served(monkeypatch):
    """{url prefix: body}; records every URL asked for."""
    bodies: dict[str, bytes] = {}
    asked: list[str] = []

    def fake_get(url: str, *, retries: int = 3) -> bytes:
        asked.append(url)
        for prefix, body in bodies.items():
            if url.startswith(prefix):
                return body
        raise sources.SourceUnavailable(f"{url}: not served")

    monkeypatch.setattr(sources, "_http_get", fake_get)
    monkeypatch.setattr(sources, "_shared_bodies", {})
    return bodies, asked


def source(provider: str, key: str) -> sources.Source:
    return next(s for s in sources.registry() if s.provider == provider and s.key == key)


# -- the registry ----------------------------------------------------------------


def test_every_series_has_its_own_file_and_manifest_key():
    registry = sources.registry()
    keys = [sources.manifest_key(s) for s in registry]
    files = [s.filename for s in registry]
    assert len(set(keys)) == len(keys) and len(set(files)) == len(files)
    assert all(s.provider in sources._FETCHERS for s in registry)
    assert {"ofr", "cftc", "squeeze"} <= {s.provider for s in registry}


@pytest.mark.parametrize(
    ("symbol", "key"),
    [
        ("^VIX", "VIX"),
        ("BTC-USD", "BTCUSD"),
        ("^MOVE", "MOVE"),
        ("HG=F", "HGF"),
        ("NQ=F", "NQF"),
        ("DX-Y.NYB", "DXY"),
        ("TQQQ", "TQQQ"),
    ],
)
def test_a_yahoo_symbol_becomes_a_file_name_key(symbol, key):
    assert sources._yahoo_key(symbol) == key


def test_a_manifest_row_carries_the_lag_the_lake_needs(served):
    bodies, _ = served
    bodies[sources.OFR_FSI_URL] = (
        b"Date,OFR FSI,Credit\n2026-11-04,-2.1,-0.8\n2026-11-05,-1.4,-0.9\n"
    )
    fsi = source("ofr", "FSI")
    entry = sources.manifest_entry(fsi, sources.fetch(fsi))
    assert sources.manifest_key(fsi) == "ofr_FSI" and entry["file"] == "ofr_FSI.csv"
    assert entry["lag_days"] == 4.0 and entry["rows"] == 2 and entry["provider"] == "ofr"


# -- OFR -------------------------------------------------------------------------

OFR_CSV = (
    b"Date,OFR FSI,Credit,Equity valuation,Safe assets,Funding,Volatility,"
    b"United States,Other advanced economies,Emerging markets\n"
    b"2026-11-04,-2.162,-0.861,-0.479,-0.298,-0.123,-0.402,-1.109,-0.572,-0.481\n"
    b"2026-11-05,-1.388,-0.843,-0.444,-0.3,-0.181,0.379,-0.67,-0.239,-0.479\n"
    b"2026-11-06,,,,,,,,,\n"
)


def test_the_ofr_index_is_stamped_four_days_after_the_day_it_describes(served):
    bodies, asked = served
    bodies[sources.OFR_FSI_URL] = OFR_CSV
    frame = sources.fetch(source("ofr", "FSI"))
    assert list(frame["close"]) == [-2.162, -1.388]  # the empty row is dropped
    assert frame["timestamp"].iloc[-1] == pd.Timestamp("2026-11-09 21:00", tz="UTC")
    credit = sources.fetch(source("ofr", "FSI_CREDIT"))
    assert list(credit["close"]) == [-0.861, -0.843]
    assert len(asked) == 1  # one download serves every column


def test_an_ofr_file_without_the_column_is_unavailable_not_a_keyerror(served):
    bodies, _ = served
    bodies[sources.OFR_FSI_URL] = b"Date,Something else\n2026-11-04,1\n"
    with pytest.raises(sources.SourceUnavailable, match="OFR FSI"):
        sources.fetch(source("ofr", "FSI"))


# -- SqueezeMetrics --------------------------------------------------------------


def test_dealer_gamma_is_readable_the_evening_after_its_session(served):
    bodies, _ = served
    bodies[sources.SQUEEZE_URL] = (
        b"date,price,dix,gex\n2026-11-06,7376.86,0.4236,488458017.14\n"
        b"2026-11-09,7549.94,0.4340,4961736266.5\n"
    )
    gex = sources.fetch(source("squeeze", "GEX"))
    assert gex["close"].iloc[-1] == pytest.approx(4961736266.5)
    # After Monday's close, before Tuesday's session.
    assert gex["timestamp"].iloc[-1] == pd.Timestamp("2026-11-10 03:00", tz="UTC")
    assert sources.fetch(source("squeeze", "DIX"))["close"].iloc[0] == pytest.approx(0.4236)


# -- CFTC ------------------------------------------------------------------------


def _report(day: str, lev_long, lev_short, oi) -> dict:
    return {
        "report_date_as_yyyy_mm_dd": f"{day}T00:00:00.000",
        "open_interest_all": str(oi),
        "lev_money_positions_long": str(lev_long),
        "lev_money_positions_short": str(lev_short),
        "asset_mgr_positions_long": "100",
        "asset_mgr_positions_short": "40",
        "dealer_positions_long_all": "10",
        "dealer_positions_short_all": "70",
    }


def test_positioning_is_net_over_open_interest_and_bad_reports_are_dropped():
    rows = [
        _report("2026-11-03", 30, 80, 200),
        _report("2026-10-27", 50, 50, 0),  # no open interest
        {"report_date_as_yyyy_mm_dd": "2026-10-20T00:00:00.000"},  # no fields
        _report("2026-10-13", 60, 20, 400),
    ]
    frame = sources.cftc_net_share(rows, "lev_money_positions_long", "lev_money_positions_short")
    assert list(frame["date"].dt.strftime("%Y-%m-%d")) == ["2026-10-13", "2026-11-03"]
    assert list(frame["close"]) == [pytest.approx(0.1), pytest.approx(-0.25)]


def test_a_tuesday_report_is_stamped_the_monday_after(served):
    bodies, asked = served
    bodies[sources.CFTC_TFF_URL] = json.dumps([_report("2026-11-03", 30, 80, 200)]).encode()
    lev = sources.fetch(source("cftc", "NDX_LEV_NET"))
    assert lev["close"].iloc[0] == pytest.approx(-0.25)
    assert lev["timestamp"].iloc[0] == pd.Timestamp("2026-11-09 21:00", tz="UTC")
    assert "cftc_contract_market_code=20974%2B" in asked[0]
    managers = sources.fetch(source("cftc", "NDX_AM_NET"))
    assert managers["close"].iloc[0] == pytest.approx(0.3)
    assert len(asked) == 1  # the contract's report serves all three groups
    sources.fetch(source("cftc", "SPX_DEALER_NET"))
    assert len(asked) == 2 and "13874%2B" in asked[1]


def test_a_cftc_error_answer_is_unavailable(served):
    bodies, _ = served
    bodies[sources.CFTC_TFF_URL] = b'{"error": true, "message": "throttled"}'
    with pytest.raises(sources.SourceUnavailable, match="unexpected answer"):
        sources.fetch(source("cftc", "NDX_LEV_NET"))


# -- the FOMC calendar -----------------------------------------------------------


def _meeting(month: str, days: str) -> str:
    return (
        f'<div class="fomc-meeting__month col-xs-5"><strong>{month}</strong></div>\n'
        f'<div class="fomc-meeting__date col-xs-4">{days}</div>'
    )


FOMC_PAGE = "\n".join(
    [
        "<h4><a>2026 FOMC Meetings</a></h4>",
        _meeting("January", "27-28"),
        _meeting("March", "17-18*"),
        _meeting("Apr/May", "30-1"),
        _meeting("August", "22 (notation vote)"),
        _meeting("October", "27-28"),
        "<h4><a>2025 FOMC Meetings</a></h4>",
        _meeting("December", "9-10*"),
        "<h4><a>2027 FOMC Meetings</a></h4>",
        _meeting("Jan/Feb", "31-1"),
    ]
)


def test_the_decision_day_is_the_last_day_of_each_scheduled_meeting():
    assert sources.fomc_decision_dates(FOMC_PAGE) == [
        date(2025, 12, 10),
        date(2026, 1, 28),
        date(2026, 3, 18),
        date(2026, 5, 1),  # a meeting that spans two months ends in the second
        date(2026, 10, 28),
        date(2027, 2, 1),
    ]


def test_a_page_with_no_meetings_is_unavailable_rather_than_an_empty_calendar(served):
    bodies, _ = served
    bodies[sources.FOMC_CALENDAR_URL] = b"<html>redesigned</html>"
    with pytest.raises(sources.SourceUnavailable, match="no meeting dates"):
        sources.fetch_fomc_decision_dates()
    bodies[sources.FOMC_CALENDAR_URL] = FOMC_PAGE.encode()
    assert date(2026, 10, 28) in sources.fetch_fomc_decision_dates()
