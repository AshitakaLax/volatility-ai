"""The forecast database through the real router (server/risk_forecasts.py):
a checked report is kept, and served back beside the sessions before it."""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from research.risk_overlay.forecasts import ForecastStore
from server.app import app

ROOT = Path(__file__).resolve().parents[2]
FIXTURES = ROOT / "tests/fixtures/risk_reports"


def report(name: str = "tqqq_2026-11-20.json") -> dict:
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


@pytest.fixture
def db(tmp_path, monkeypatch) -> Path:
    path = tmp_path / "forecasts" / "risk_reports.db"
    monkeypatch.setenv("VAI_FORECAST_DB", str(path))
    return path


@pytest.fixture
def client():
    return TestClient(app)


def test_a_checked_report_is_kept_once_and_each_check_counted(client, db):
    first = client.post("/api/live/risk-forecasts", json={"report": report(), "operator": "owner"})
    assert first.status_code == 201, first.text
    body = first.json()
    assert body["new"] is True and body["session"] == "2026-11-20" and body["symbol"] == "TQQQ"
    again = client.post("/api/live/risk-forecasts", json={"report": report()}).json()
    assert again["new"] is False and again["receipts"] == 2
    assert [r["via"] for r in ForecastStore(db).receipts(body["sha256"])] == ["check", "check"]


def test_a_report_that_fails_the_audit_is_refused_with_its_reason(client, db):
    broken = report()
    broken["horizons"]["tomorrow"]["summary"]["quantiles_pct"]["p05"] = 50.0
    answer = client.post("/api/live/risk-forecasts", json={"report": broken})
    assert answer.status_code == 422
    assert isinstance(answer.json()["detail"], str)
    assert "does not pass the audit" in answer.json()["detail"]
    assert ForecastStore(db).symbols() == []


def test_another_sites_page_cannot_store_one(client, db):
    answer = client.post(
        "/api/live/risk-forecasts",
        json={"report": report()},
        headers={"sec-fetch-site": "cross-site"},
    )
    assert answer.status_code == 403


def test_the_sessions_oldest_first_with_the_actual_once_recorded(client, db):
    client.post("/api/live/risk-forecasts", json={"report": report("tqqq_2026-11-23.json")})
    client.post("/api/live/risk-forecasts", json={"report": report()})
    store = ForecastStore(db)
    store.record_close(
        "TQQQ",
        date(2026, 11, 20),
        close=40.99,
        prior_session=date(2026, 11, 19),
        prior_close=48.99,
        source="warehouse",
    )
    body = client.get("/api/live/risk-forecasts?symbol=tqqq").json()
    assert body["symbol"] == "TQQQ" and body["symbols"] == ["TQQQ"]
    friday, monday = body["sessions"]
    assert friday["session"] == "2026-11-20" and monday["session"] == "2026-11-23"
    assert friday["quantiles"] == {
        "p01": -22.01,
        "p05": -13.42,
        "p25": -5.04,
        "p75": 4.55,
        "p95": 11.95,
        "p99": 18.85,
    }
    assert friday["actual"]["return_pct"] == pytest.approx(-16.33, abs=0.01)
    assert friday["score"] is None, "scored by the nightly run, not by a read"
    assert monday["actual"] is None


def test_without_a_symbol_the_one_most_recently_received(client, db):
    assert client.get("/api/live/risk-forecasts").json() == {
        "symbol": None,
        "symbols": [],
        "sessions": [],
    }
    client.post("/api/live/risk-forecasts", json={"report": report()})
    body = client.get("/api/live/risk-forecasts").json()
    assert body["symbol"] == "TQQQ" and len(body["sessions"]) == 1


def test_a_symbol_is_a_ticker_not_a_path(client, db):
    assert client.get("/api/live/risk-forecasts?symbol=../../etc").status_code == 422


def snapshot_inputs(session: str = "2026-11-20") -> dict:
    return {
        "snapshot": {"symbol": "TQQQ", "target_session": session, "vix_level": 24.1},
        "diagnostics": {"engine": "chronos"},
        "sources": [],
    }


def test_the_forecast_tabs_keep_sends_what_it_read(client, db):
    answer = client.post(
        "/api/live/risk-forecasts",
        json={"report": report(), "operator": "owner", "inputs": snapshot_inputs()},
    )
    assert answer.status_code == 201, answer.text
    found = client.get(f"/api/live/risk-forecasts/report?sha256={answer.json()['sha256']}").json()
    assert found["inputs"]["snapshot"]["vix_level"] == 24.1
    assert found["report"]["symbol"] == "TQQQ" and found["receipts"][0]["operator"] == "owner"


def test_another_reports_inputs_are_refused_with_the_reason(client, db):
    answer = client.post(
        "/api/live/risk-forecasts",
        json={"report": report(), "inputs": snapshot_inputs("2026-11-23")},
    )
    assert answer.status_code == 422
    assert "2026-11-23" in answer.json()["detail"]
    assert ForecastStore(db).symbols() == []


def test_every_report_newest_first_and_the_session_one_sent_now_is_for(client, db, monkeypatch):
    from datetime import UTC, datetime

    from server import risk_forecasts

    monkeypatch.setattr(risk_forecasts, "_now", lambda: datetime(2026, 11, 26, 17, 0, tzinfo=UTC))
    assert client.get("/api/live/risk-forecasts/reports").json() == {
        "symbol": None,
        "symbols": [],
        "upcoming_session": "2026-11-27",
        "reports": [],
    }
    client.post("/api/live/risk-forecasts", json={"report": report()})
    client.post("/api/live/risk-forecasts", json={"report": report("tqqq_2026-11-23.json")})
    body = client.get("/api/live/risk-forecasts/reports?symbol=tqqq&limit=5").json()
    assert body["symbol"] == "TQQQ" and body["upcoming_session"] == "2026-11-27"
    assert [row["session"] for row in body["reports"]] == ["2026-11-23", "2026-11-20"]
    first = body["reports"][0]
    assert first["newest"] is True and first["has_inputs"] is False and first["model"]
    assert first["horizons"]["next_week"]["end_session"] == "2026-11-30"


def test_an_unknown_report_is_404_and_an_id_is_hex_not_a_path(client, db):
    assert client.get(f"/api/live/risk-forecasts/report?sha256={'a' * 64}").status_code == 404
    assert client.get("/api/live/risk-forecasts/report?sha256=../../etc").status_code == 422
    assert client.get("/api/live/risk-forecasts/reports?symbol=../x").status_code == 422
