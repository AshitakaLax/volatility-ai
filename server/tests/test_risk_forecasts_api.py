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
