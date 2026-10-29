"""Algorithm management: candidate -> paper trial -> promoted -> published
(server/algorithms.py), through the real router. Every write is confined to
the library and the profiles folder, and real money's gates are untouched."""

from __future__ import annotations

import json
import time

import pytest
import yaml
from fastapi.testclient import TestClient

from research.strategies import live_profiles
from server import algorithms
from server.app import app
from server.tests.test_history_api import cell, save_run
from server.tests.test_live_control_api import deployments  # noqa: F401  (a fixture)


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("VAI_RUN_HISTORY_DIR", str(tmp_path / "runs"))
    monkeypatch.setenv("VAI_ALGORITHMS_DIR", str(tmp_path / "library"))
    monkeypatch.setenv("VAI_LIVE_PROFILES", str(tmp_path / "profiles"))
    (tmp_path / "profiles").mkdir()
    return TestClient(app)


def add(client, run="abc123def456", ticker="TQQQ", index=0, **fund):
    save_run(
        run,
        ticker=ticker,
        model="fixed",
        cells=[cell(0.002, 0.03, {"allocation_pct": 0.05}, net_yield_pct=12.5, cagr_pct=3.0)],
    )
    return client.post(
        "/api/algorithms/candidates",
        json={"run": run, "ticker": ticker, "cell": index, "operator": "tester"},
    )


def test_a_candidate_is_read_from_the_stored_run(client):
    body = add(client).json()
    assert body["id"] == "fixed-tqqq-abc123-0"
    assert body["strategy_id"] == "fixed" and body["symbols"] == ["TQQQ"]
    assert body["strategy_params"] == {"allocation_pct": 0.05}
    assert (body["step"], body["profit_target"]) == (0.002, 0.03)
    assert body["evidence"]["backtest"]["net_yield_pct"] == 12.5
    assert body["stage"] == "candidate"
    assert client.get("/api/algorithms").json()["candidates"][0]["id"] == body["id"]


def test_the_same_cell_is_one_candidate_and_an_unknown_one_is_refused(client):
    assert add(client).status_code == 201
    assert add(client).status_code == 409
    assert add(client, run="zzz999", index=5).status_code == 404


def test_a_candidate_id_cannot_name_a_path(client):
    for bad in ("..", "a/../b", "A B"):
        assert client.post(f"/api/algorithms/{bad}/evaluate").status_code in (404, 405)


def test_a_trial_switches_a_paper_deployment_and_refuses_real_money(client, deployments):  # noqa: F811
    candidate_id = add(client).json()["id"]
    refused = client.post(
        f"/api/algorithms/{candidate_id}/trial", json={"deployment": "money", "operator": "tester"}
    )
    assert refused.status_code == 403
    started = client.post(
        f"/api/algorithms/{candidate_id}/trial",
        json={"deployment": "paper", "operator": "tester", "legacy_lots": "exit_at_cost"},
    )
    assert started.status_code == 200, started.text
    assert started.json()["stage"] == "paper_trial"
    commands = client.get("/api/live/deployments/paper").json()["commands"]
    (command,) = [c for c in commands if c["type"] == "switch_algorithm"]
    assert command["args"]["legacy_lots"] == "exit_at_cost"
    assert command["args"]["strategy_id"] == "fixed"
    assert command["reason"] == f"Paper trial of {candidate_id}"


def test_a_trial_cannot_pass_while_the_incident_counters_are_unmeasured(
    client,
    deployments,  # noqa: F811
):
    candidate_id = add(client).json()["id"]
    client.post(
        f"/api/algorithms/{candidate_id}/trial", json={"deployment": "paper", "operator": "tester"}
    )
    body = client.post(f"/api/algorithms/{candidate_id}/evaluate").json()
    verdict = body["trial"]["evaluation"]
    assert verdict["passed"] is False and body["promotion"] is None
    assert any("not measured" in failure for failure in verdict["failures"])
    assert any("paper_trading_days" in failure for failure in verdict["failures"])


def promote(client, candidate_id, reason="my own call"):
    return client.post(
        f"/api/algorithms/{candidate_id}/override",
        json={"reason": reason, "operator": "tester", "confirm": candidate_id},
    )


def test_an_owner_sign_off_needs_the_id_typed_and_is_marked_manual(client):
    candidate_id = add(client).json()["id"]
    wrong = client.post(
        f"/api/algorithms/{candidate_id}/override",
        json={"reason": "my own call", "operator": "tester", "confirm": "nope"},
    )
    assert wrong.status_code == 409
    body = promote(client, candidate_id).json()
    assert body["promotion"]["manual"] is True and body["stage"] == "promoted"


def publish(client, candidate_id, confirm=None):
    return client.post(
        f"/api/algorithms/{candidate_id}/publish",
        json={"operator": "tester", "confirm": confirm or candidate_id},
    )


def test_publishing_needs_a_promotion_and_writes_a_profile_the_loader_accepts(client, tmp_path):
    candidate_id = add(client).json()["id"]
    assert publish(client, candidate_id).status_code == 409  # not promoted
    promote(client, candidate_id)
    assert publish(client, candidate_id, confirm="nope").status_code == 409
    body = publish(client, candidate_id)
    assert body.status_code == 200, body.text
    assert body.json()["stage"] == "published"

    text = (tmp_path / "profiles" / f"{candidate_id}.yaml").read_text()
    assert text.startswith("# Published from the web") and "owner sign-off" in text
    profile = live_profiles.get(candidate_id)
    assert profile.promoted() and profile.promotion_kind() == "manual"
    assert profile.change()["strategy_params"] == {"allocation_pct": 0.05}
    assert yaml.safe_load(text)["evidence"]["promotion"] == f"promotions/{candidate_id}.json"
    assert json.loads((tmp_path / "profiles" / "promotions" / f"{candidate_id}.json").read_text())[
        "manual"
    ]
    assert publish(client, candidate_id).status_code == 409  # never overwrites


def test_a_published_profile_is_offered_to_real_money_as_promoted(client, deployments):  # noqa: F811
    candidate_id = add(client).json()["id"]
    promote(client, candidate_id)
    publish(client, candidate_id)
    rows = client.get("/api/live/deployments/money/algorithm").json()["profiles"]
    row = next(r for r in rows if r["id"] == candidate_id)
    assert row["promoted"] is True and row["promotion_kind"] == "manual"


def test_a_candidate_on_trial_or_published_cannot_be_deleted(client, deployments):  # noqa: F811
    candidate_id = add(client).json()["id"]
    client.post(
        f"/api/algorithms/{candidate_id}/trial", json={"deployment": "paper", "operator": "tester"}
    )
    assert client.delete(f"/api/algorithms/candidates/{candidate_id}").status_code == 409
    other = add(client, run="fff000aaa111").json()["id"]
    assert client.delete(f"/api/algorithms/candidates/{other}").status_code == 200
    assert other not in [c["id"] for c in client.get("/api/algorithms").json()["candidates"]]


def test_the_library_and_profiles_are_the_only_places_it_writes(client, tmp_path):
    candidate_id = add(client).json()["id"]
    promote(client, candidate_id)
    publish(client, candidate_id)
    written = {
        str(path.relative_to(tmp_path))
        for path in tmp_path.rglob("*")
        if path.is_file() and not path.is_relative_to(tmp_path / "runs")
    }
    assert written == {
        f"library/{candidate_id}/candidate.json",
        f"profiles/{candidate_id}.yaml",
        f"profiles/promotions/{candidate_id}.json",
    }, written


def test_time_since_the_trial_started_is_what_is_counted():
    from engine.promotion_record import build_record

    t0 = time.time() - 10 * 86400
    bars = [{"t": t0 - 86400 * 3}] + [{"t": t0 + 86400 * d + 3600} for d in range(1, 4)]
    fills = [{"t": t0 - 5}, {"t": t0 + 100}]
    orders = [{"t": t0 + 50, "event": "placed"}, {"t": t0 + 60, "event": "filled"}]
    record = build_record(
        "x",
        started_at=t0,
        bars=bars,
        fills=fills,
        orders=orders,
        halted_for_reconciliation=True,
    )
    assert (record.paper_trading_days, record.fill_count, record.decision_count) == (3.0, 1, 1)
    assert record.unresolved_reconciliations == 1


def test_the_module_is_the_only_writer(client):
    assert algorithms.router.prefix == "/api/algorithms"
