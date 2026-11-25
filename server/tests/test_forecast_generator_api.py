"""The Forecast tab's routes (server/forecast_generator.py) through the real
app: a run starts, reports its progress and lands its report beside the
audit; it is refused when no honest report can be made; one runs at a time.
The generator, the thread and the clock are injected -- no network, no
sleeps."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from fastapi.testclient import TestClient

from research.forecast_generator import generator
from server import forecast_generator as routes
from server.app import app

PRE_MARKET = datetime(2026, 11, 24, 9, 20, tzinfo=UTC)  # 04:20 ET, a session day
REGULAR_HOURS = datetime(2026, 11, 24, 15, 0, tzinfo=UTC)  # 10:00 ET


def made(symbol: str = "TQQQ") -> generator.Generated:
    return generator.Generated(
        report={"symbol": symbol, "schema_version": "1.2.0"},
        audit={"ok": True, "errors": [], "warnings": [], "session": "2026-11-24", "sha256": "ab"},
        snapshot={"symbol": symbol, "overnight_futures_change_pct": 0.5},
        sources=[],
        diagnostics={"engine": "bootstrap"},
    )


@pytest.fixture
def harness(monkeypatch):
    routes.RUNS.clear()
    state = {"now": PRE_MARKET, "calls": [], "pending": []}
    monkeypatch.setattr(routes, "_now", lambda: state["now"])
    # Runs inline unless a test holds them back.
    monkeypatch.setattr(
        routes,
        "_spawn",
        lambda work: state["pending"].append(work) if state.get("hold") else work(),
    )
    monkeypatch.setattr(routes.model, "chronos_available", lambda: (True, "fake on cpu"))

    def fake_generate(symbol, engine, progress=None, **_):
        state["calls"].append((symbol, engine))
        progress("Fetching daily history")
        if state.get("refuse"):
            raise generator.ForecastRefused(state["refuse"])
        if state.get("explode"):
            raise RuntimeError("Yahoo answered 503")
        return made(symbol)

    monkeypatch.setattr(routes, "_generate", fake_generate)
    yield state
    routes.RUNS.clear()


@pytest.fixture
def client():
    return TestClient(app)


def test_status_says_what_can_run_and_for_which_session(client, harness):
    body = client.get("/api/forecast/status").json()
    assert body["can_generate"] is True and body["target_session"] == "2026-11-24"
    assert {e["id"]: e["available"] for e in body["engines"]} == {
        "chronos": True,
        "bootstrap": True,
    }
    assert "TQQQ" in body["symbols"] and body["runs"] == []


def test_a_run_lands_its_report_audit_and_snapshot(client, harness):
    started = client.post("/api/forecast/runs", json={"symbol": "tqqq", "engine": "bootstrap"})
    assert started.status_code == 202, started.text
    assert started.json()["target_session"] == "2026-11-24"
    assert harness["calls"] == [("TQQQ", "bootstrap")]
    [run] = client.get("/api/forecast/runs").json()["runs"]
    assert run["state"] == "done" and run["symbol"] == "TQQQ" and run["error"] is None
    assert run["progress"][0]["message"] == "Fetching daily history"
    assert run["result"]["report"]["symbol"] == "TQQQ"
    assert run["result"]["audit"]["ok"] is True
    assert run["result"]["snapshot"]["overnight_futures_change_pct"] == 0.5


def test_one_run_at_a_time(client, harness):
    harness["hold"] = True
    assert client.post("/api/forecast/runs", json={"symbol": "TQQQ"}).status_code == 202
    busy = client.post("/api/forecast/runs", json={"symbol": "SPY", "engine": "bootstrap"})
    assert busy.status_code == 409 and "still running" in busy.json()["detail"]
    harness["pending"].pop()()
    assert (
        client.post("/api/forecast/runs", json={"symbol": "SPY", "engine": "bootstrap"}).status_code
        == 202
    )


def test_no_run_starts_inside_regular_hours(client, harness):
    harness["now"] = REGULAR_HOURS
    status = client.get("/api/forecast/status").json()
    assert status["can_generate"] is False and "regular" in status["why_not"]
    answer = client.post("/api/forecast/runs", json={"symbol": "TQQQ"})
    assert answer.status_code == 422 and "regular" in answer.json()["detail"]
    assert harness["calls"] == []


def test_chronos_is_refused_where_it_is_not_installed(client, harness, monkeypatch):
    monkeypatch.setattr(routes.model, "chronos_available", lambda: (False, "torch not installed"))
    answer = client.post("/api/forecast/runs", json={"symbol": "TQQQ", "engine": "chronos"})
    assert answer.status_code == 422 and "torch" in answer.json()["detail"]
    assert (
        client.post(
            "/api/forecast/runs", json={"symbol": "TQQQ", "engine": "bootstrap"}
        ).status_code
        == 202
    )


def test_a_refusal_and_a_failure_are_shown_not_raised(client, harness):
    harness["refuse"] = "The data source has not posted it yet."
    client.post("/api/forecast/runs", json={"symbol": "TQQQ", "engine": "bootstrap"})
    [refused] = client.get("/api/forecast/runs").json()["runs"]
    assert refused["state"] == "refused" and "not posted" in refused["error"]
    harness.pop("refuse")
    harness["explode"] = True
    client.post("/api/forecast/runs", json={"symbol": "TQQQ", "engine": "bootstrap"})
    failed = client.get("/api/forecast/runs").json()["runs"][0]
    assert failed["state"] == "failed" and failed["error"] == "RuntimeError: Yahoo answered 503"


def test_only_the_last_runs_are_kept(client, harness):
    for _ in range(routes.RUNS_KEPT + 2):
        client.post("/api/forecast/runs", json={"symbol": "TQQQ", "engine": "bootstrap"})
    assert len(client.get("/api/forecast/runs").json()["runs"]) == routes.RUNS_KEPT


@pytest.mark.parametrize(
    "body",
    [
        {"symbol": "../x"},
        {"symbol": ""},
        {"symbol": "TQQQ", "engine": "oracle"},
        {"symbol": "A" * 13},
    ],
)
def test_a_bad_request_is_refused_before_anything_runs(client, harness, body):
    assert client.post("/api/forecast/runs", json=body).status_code == 422
    assert harness["calls"] == []


def test_another_sites_page_cannot_start_one(client, harness):
    answer = client.post(
        "/api/forecast/runs",
        json={"symbol": "TQQQ", "engine": "bootstrap"},
        headers={"sec-fetch-site": "cross-site"},
    )
    assert answer.status_code == 403
    assert harness["calls"] == []


def test_health_lists_the_forecast_capability(client):
    assert "forecast" in client.get("/api/health").json()["caps"]
