"""fidelity_gateway/options_capture.py: the readings formed from Trader+'s
option replies, the replies found in a HAR, and the series they append to.
The HAR here is built in the test: no capture of a real session is read."""

from __future__ import annotations

import json
import math
from datetime import UTC, datetime

import pytest

from fidelity_gateway import options_capture as O

SPOT = 56.0
BASE = "https://digital.fidelity.com/ftgw/digital"


def row(dte: int, strike: float, call_delta: float, call_iv: float, put_iv: float, **over) -> dict:
    data = {
        "expirationData": {"date": f"Nov {10 + dte} 2026", "daysToExpiration": dte},
        "strike": strike,
        "callImpliedVolatility": call_iv,
        "putImpliedVolatility": put_iv,
        "callDelta": call_delta,
        "putDelta": call_delta - 1.0,
        "callGamma": 0.04,
        "putGamma": 0.04,
        "callOpenInterest": 1000,
        "putOpenInterest": 400,
        "callIntrinsicValue": max(0.0, SPOT - strike),
        "putIntrinsicValue": max(0.0, strike - SPOT),
    }
    data.update(over)
    return data


def chain() -> dict:
    """Two expirations, five strikes each; puts richer than calls."""
    rows = []
    for dte in (1, 6):
        rows += [
            row(dte, 52, 0.90, 0.95, 1.05),
            row(dte, 54, 0.75, 0.85, 0.95),  # the 25-delta put (-0.25)
            row(dte, 56, 0.50, 0.80, 0.82),  # at the money
            row(dte, 58, 0.25, 0.78, 0.80),  # the 25-delta call
            row(dte, 60, 0.10, 0.79, 0.81),
        ]
    for r in rows:
        if r["expirationData"]["daysToExpiration"] == 1:
            r["callImpliedVolatility"] *= 1.25
            r["putImpliedVolatility"] *= 1.25
    return {"underlyingSymbol": "TQQQ", "callsAndPuts": rows}


STATISTICS = {
    "underlyingsymbol": "TQQQ",
    "iv30percentile": 56,
    "hv30percentile": 100,
    "callVolume": 40000,
    "putVolume": 30000,
    "avgCallVolume": 150000,
    "avgPutVolume": 150000,
    "callOpenInterest": 1000000,
    "putOpenInterest": 650000,
}


def entry(path: str, body, started: str, query: str = "") -> dict:
    return {
        "startedDateTime": started,
        "request": {
            "url": f"{BASE}{path}{'?' + query if query else ''}",
            "headers": [{"name": "Cookie", "value": "SECRET-SESSION"}],
        },
        "response": {"content": {"mimeType": "application/json", "text": json.dumps(body)}},
    }


def har(*entries) -> dict:
    return {"log": {"entries": list(entries)}}


# -- the readings ----------------------------------------------------------------


def test_the_underlying_is_read_from_the_chains_own_intrinsic_values():
    legs = O.parse_chain(chain())
    assert len(legs) == 10 and legs[0].dte == 1 and legs[-1].dte == 6
    assert O.spot(legs) == pytest.approx(SPOT)
    out_of_the_money = [leg for leg in legs if leg.strike == 56]
    assert math.isnan(O.spot(out_of_the_money))


def test_the_readings_are_the_ones_the_module_names():
    found = O.readings(chain(), STATISTICS)
    assert found["IV30_PCTL"] == 56 and found["HV30_PCTL"] == 100
    assert found["PC_VOLUME"] == pytest.approx(0.75)
    assert found["PC_VOLUME_REL"] == pytest.approx(0.75)  # against a usual ratio of 1
    assert found["PC_OI"] == pytest.approx(0.65)
    assert found["SPOT"] == pytest.approx(SPOT)
    # The expiration nearest a week out is the 6-day one.
    assert found["ATM_IV_7D"] == pytest.approx(81.0)
    assert found["SKEW_25D"] == pytest.approx(100 * (0.95 - 0.78))
    assert found["TERM_NEAR_FAR"] == pytest.approx(1.25)
    # (calls 1000 - puts 400) x 0.04 gamma x 10 strikes x 100 x 56^2 x 1%
    assert found["GEX_NEAR"] == pytest.approx(600 * 0.04 * 10 * 100 * SPOT * SPOT * 0.01)


def test_a_slice_without_a_25_delta_strike_forms_no_skew():
    narrow = {"callsAndPuts": [row(6, 56, 0.50, 0.80, 0.82), row(6, 57, 0.45, 0.80, 0.82)]}
    found = O.readings(narrow, None)
    assert math.isnan(found["SKEW_25D"]) and math.isnan(found["TERM_NEAR_FAR"])
    assert found["ATM_IV_7D"] == pytest.approx(81.0)
    assert "IV30_PCTL" not in found


def test_missing_and_malformed_fields_are_not_numbers_not_errors():
    broken = chain()
    broken["callsAndPuts"][0]["callImpliedVolatility"] = None
    broken["callsAndPuts"].append({"strike": "n/a", "expirationData": {"date": "x"}})
    broken["callsAndPuts"].append({"strike": 50})
    assert len(O.parse_chain(broken)) == 10
    found = O.readings(broken, {"underlyingsymbol": "TQQQ", "callVolume": 0, "putVolume": 5})
    assert math.isnan(found["PC_VOLUME"]) and math.isnan(found["IV30_PCTL"])
    assert O.readings(None, None) == {}


# -- a capture -------------------------------------------------------------------


def test_the_newest_reply_for_the_symbol_is_the_capture():
    other = {"underlyingSymbol": "SPY", "callsAndPuts": [row(6, 500, 0.5, 0.2, 0.2)]}
    stale = {**STATISTICS, "iv30percentile": 10}
    capture = O.read_capture(
        har(
            entry(O.STATISTICS_PATH, stale, "2026-11-10T15:00:00.000Z", "underlying=TQQQ"),
            entry(O.STATISTICS_PATH, STATISTICS, "2026-11-10T15:28:42.585Z", "underlying=TQQQ"),
            entry(O.CHAIN_PATH, other, "2026-11-10T15:28:47.000Z", "strikes=10"),
            entry(O.CHAIN_PATH, chain(), "2026-11-10T15:28:48.057Z", "strikes=10"),
            entry(
                O.EXPIRATIONS_PATH,
                {"expirations": [{"date": "2026-11-11"}, {"date": "2026-11-13"}]},
                "2026-11-10T15:28:45.275Z",
                "symbol=TQQQ",
            ),
            entry("/traderplus-api/api/quotes/v1", {"quotes": []}, "2026-11-10T15:28:50.000Z"),
        ),
        "tqqq",
    )
    assert capture.symbol == "TQQQ"
    assert capture.statistics["iv30percentile"] == 56
    assert capture.chain["underlyingSymbol"] == "TQQQ"
    assert capture.expirations == ["2026-11-11", "2026-11-13"]
    assert capture.at == datetime(2026, 11, 10, 15, 28, 48, 57000, tzinfo=UTC)


def test_a_capture_of_another_fund_holds_nothing_for_this_one(tmp_path, capsys):
    path = tmp_path / "download.devtools"
    path.write_text(json.dumps(har(entry(O.CHAIN_PATH, chain(), "2026-11-10T15:28:48.057Z"))))
    assert O.main(["--input", str(path), "--symbol", "SOXL"]) == 1
    assert "no option replies for SOXL" in capsys.readouterr().err


def test_nothing_but_the_three_replies_is_read_or_printed(tmp_path, capsys):
    path = tmp_path / "download.devtools"
    path.write_text(
        json.dumps(
            har(
                entry(O.STATISTICS_PATH, STATISTICS, "2026-11-10T15:28:42.585Z"),
                entry(O.CHAIN_PATH, chain(), "2026-11-10T15:28:48.057Z"),
                entry("/portfolio/api/positions", {"account": "X12345678"}, "2026-11-10T15:29:00Z"),
            )
        )
    )
    out = tmp_path / "external"
    assert O.main(["--input", str(path), "--symbol", "TQQQ", "--out", str(out)]) == 0
    printed = capsys.readouterr().out
    assert "SECRET-SESSION" not in printed and "X12345678" not in printed
    assert "10 strikes over 2 expirations" in printed and "IV30_PCTL" in printed
    written = "".join(p.read_text() for p in out.iterdir())
    assert "SECRET-SESSION" not in written and "X12345678" not in written


# -- the series ------------------------------------------------------------------


def test_each_reading_is_one_row_stamped_when_it_was_captured(tmp_path):
    capture = O.read_capture(
        har(
            entry(O.STATISTICS_PATH, STATISTICS, "2026-11-10T15:28:42.585Z"),
            entry(O.CHAIN_PATH, chain(), "2026-11-10T15:28:48.057Z"),
        ),
        "TQQQ",
    )
    written = O.store(tmp_path, capture, O.readings(capture.chain, capture.statistics))
    assert "fidelity_TQQQ_SKEW_25D" in written and len(written) == 10
    text = (tmp_path / "fidelity_TQQQ_IV30_PCTL.csv").read_text()
    assert text == "timestamp,close\n2026-11-10 15:28:48+00:00,56.0\n"
    # The same capture again adds nothing; a later one is appended in order.
    assert O.store(tmp_path, capture, O.readings(capture.chain, capture.statistics)) == []
    later = datetime(2026, 11, 11, 15, 30, tzinfo=UTC)
    earlier = datetime(2026, 11, 9, 15, 30, tzinfo=UTC)
    assert O.append_reading(tmp_path, "fidelity_TQQQ_IV30_PCTL", later, 60)
    assert O.append_reading(tmp_path, "fidelity_TQQQ_IV30_PCTL", earlier, 50)
    stamps = [
        line.split(",")[0]
        for line in (tmp_path / "fidelity_TQQQ_IV30_PCTL.csv").read_text().splitlines()[1:]
    ]
    assert stamps == sorted(stamps) and len(stamps) == 3


def test_the_series_is_the_shape_every_outside_series_has(tmp_path):
    """`timestamp,close` with a UTC stamp: research/ml/sources.py's shape,
    which the risk governor reads. (Read here with pandas alone: this
    package does not import the strategies.)"""
    import pandas as pd

    at = datetime(2026, 11, 10, 15, 28, 48, tzinfo=UTC)
    O.append_reading(tmp_path, O.series_name("tqqq", "SKEW_25D"), at, 15.6)
    frame = pd.read_csv(tmp_path / "fidelity_TQQQ_SKEW_25D.csv")
    assert list(frame.columns) == ["timestamp", "close"]
    stamp = pd.to_datetime(frame["timestamp"], utc=True).iloc[0]
    assert stamp.to_pydatetime() == at and frame["close"].iloc[0] == 15.6


def test_readings_that_were_not_formed_are_not_stored(tmp_path):
    capture = O.Capture("TQQQ", datetime(2026, 11, 10, 15, 0, tzinfo=UTC), None, STATISTICS, [])
    written = O.store(tmp_path, capture, {"IV30_PCTL": 56.0, "SKEW_25D": math.nan})
    assert written == ["fidelity_TQQQ_IV30_PCTL"]
    with pytest.raises(ValueError, match="no time"):
        O.store(tmp_path, O.Capture("TQQQ", None, None, STATISTICS, []), {"IV30_PCTL": 56.0})
