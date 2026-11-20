"""The nightly risk report on the Live page, through the real routers.

server/live_control.py previews (writing nothing) and queues; the trader --
played here by the same SupervisorControl and handlers the supervisor runs
between sessions -- applies and archives; server/live.py reads the archive.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

import pytest
import yaml
from fastapi.testclient import TestClient

from engine.core.persistence import LedgerStore
from engine.trading.control_inbox import ControlInbox
from engine.trading.operator_control import SupervisorControl
from research.risk_overlay import inputs as inputs_module
from research.risk_overlay.baselines import Baseline
from research.risk_overlay.live import handlers
from server import live, live_control
from server.app import app

ROOT = Path(__file__).resolve().parents[2]
FIXTURE = ROOT / "tests/fixtures/risk_reports/tqqq_2026-11-20.json"
EVENING = datetime(2026, 11, 20, 2, 45, tzinfo=UTC)


def report() -> dict:
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def deployments(tmp_path, monkeypatch):
    """`paper` takes reports, `bare` has no overlay, `money` is real money
    that takes them advisory."""

    def config(path: str, name: str, *, overlay: bool) -> str:
        data = yaml.safe_load((ROOT / path).read_text(encoding="utf-8"))
        if overlay:
            data.setdefault("risk", {})["overlay"] = {"mode": "advisory"}
            data["live"].setdefault("control", {})["risk_reports"] = True
        else:
            (data.get("risk") or {}).pop("overlay", None)
            (data["live"].get("control") or {}).pop("risk_reports", None)
        out = tmp_path / f"{name}.yaml"
        out.write_text(yaml.safe_dump(data), encoding="utf-8")
        return str(out)

    entries = {}
    for deployment_id, path, overlay in (
        ("paper", "config/paper_aggressive.yaml", True),
        ("bare", "config/paper_aggressive.yaml", False),
        ("money", "config/production.yaml", True),
    ):
        ledger = tmp_path / f"{deployment_id}.db"
        LedgerStore(str(ledger)).close()
        entries[deployment_id] = {
            "label": deployment_id,
            "config": config(path, deployment_id, overlay=overlay),
            "state_db": str(ledger),
            "control_dir": str(tmp_path / f"control-{deployment_id}"),
        }
    registry = tmp_path / "deployments.yaml"
    registry.write_text(yaml.safe_dump({"deployments": entries}), encoding="utf-8")
    monkeypatch.setenv("VAI_DEPLOYMENTS", str(registry))
    monkeypatch.setenv("VAI_EXTERNAL_DIR", str(tmp_path / "no-outside-data"))
    monkeypatch.setattr(live_control, "_now", lambda: EVENING)
    monkeypatch.setattr(live, "_now", lambda: EVENING)
    monkeypatch.setattr(
        inputs_module, "baseline_for", lambda symbol: Baseline(symbol, 4.2, {"next_month": -30.0})
    )
    return entries


def preview(client, deployment, body=None):
    return client.post(
        f"/api/live/deployments/{deployment}/risk-report/preview",
        json={"report": body if body is not None else report()},
    )


def send(client, deployment, type_, **body):
    body.setdefault("reason", "tonight's report")
    body.setdefault("operator", "owner")
    return client.post(f"/api/live/deployments/{deployment}/commands", json={"type": type_, **body})


def apply_queued(entry, clock=EVENING) -> list[dict]:
    """The supervisor's side: claim and apply what is queued."""
    from engine.core.config import BacktestConfig

    config = BacktestConfig.from_yaml(entry["config"])
    inbox = ControlInbox(entry["control_dir"], clock=clock.timestamp)
    extra = handlers(config, entry["control_dir"], inbox=inbox, clock=clock.timestamp)
    control = SupervisorControl(
        inbox, state_db=entry["state_db"], extra=extra, clock=clock.timestamp
    )
    return control.poll()


class TestThePreview:
    def test_it_says_what_the_report_would_do_and_writes_nothing(self, client, deployments):
        body = preview(client, "paper").json()
        assert body["takes_reports"] is True and body["audit"]["ok"] is True
        assert body["session"] == "2026-11-20"
        assert body["mapped"]["tier"] == 3 and body["overlay"]["pause"] is True
        assert body["would"] == "apply" and body["typed"] is None
        assert "no new grid buys" in body["summary"]
        assert any("no implied-move cross-check" in note for note in body["notes"])
        control = Path(deployments["paper"]["control_dir"])
        assert not control.exists() or not any(control.rglob("*.json")), "a preview writes nothing"

    def test_real_money_asks_for_its_id(self, client, deployments):
        body = preview(client, "money").json()
        assert body["paper"] is False and body["typed"] == "this deployment trades real money"

    def test_a_deployment_without_an_overlay(self, client, deployments):
        body = preview(client, "bare").json()
        assert body["takes_reports"] is False and "risk.overlay" in body["why_not"]

    def test_a_broken_report_lists_its_problems(self, client, deployments):
        broken = report()
        broken["execution_signals"]["regime"] = "bullish"
        body = preview(client, "paper", broken).json()
        assert body["would"] == "refused" and body["audit"]["errors"]

    def test_it_has_the_cross_site_guard(self, client, deployments):
        response = client.post(
            "/api/live/deployments/paper/risk-report/preview",
            json={"report": report()},
            headers={"Sec-Fetch-Site": "cross-site"},
        )
        assert response.status_code == 403


class TestApplying:
    def test_queued_applied_and_shown(self, client, deployments):
        response = send(client, "paper", "apply_risk_report", args={"report": report()})
        assert response.status_code == 202, response.text
        (result,) = apply_queued(deployments["paper"])
        assert result["status"] == "applied", result
        shown = client.get("/api/live/deployments/paper/risk-reports").json()
        (entry,) = shown["sessions"]
        assert entry["session"] == "2026-11-20" and entry["tier"] == 3
        assert entry["operator"] == "owner" and "report" not in entry
        assert shown["next"]["session"] == "2026-11-20" and shown["next"]["overlay"]["pause"]
        full = client.get("/api/live/deployments/paper/risk-reports?full=true").json()
        assert full["sessions"][0]["report"] == report()

    def test_the_deployment_list_says_who_takes_reports(self, client, deployments):
        listed = {d["id"]: d for d in client.get("/api/live/deployments").json()}
        assert listed["paper"]["risk_reports"]["takes"] is True
        assert listed["paper"]["caps"]["risk_reports"] is True
        assert listed["bare"]["risk_reports"]["takes"] is False

    def test_no_overlay_no_report(self, client, deployments):
        response = send(client, "bare", "apply_risk_report", args={"report": report()})
        assert response.status_code == 403
        assert "live.control.risk_reports" in response.json()["detail"]

    def test_real_money_needs_its_id_typed(self, client, deployments):
        response = send(client, "money", "apply_risk_report", args={"report": report()})
        assert response.status_code == 409 and "Type money" in response.json()["detail"]
        typed = send(
            client, "money", "apply_risk_report", args={"report": report()}, confirm="money"
        )
        assert typed.status_code == 202

    def test_a_broken_report_is_refused_before_it_is_queued(self, client, deployments):
        broken = report()
        broken["symbol"] = ""
        response = send(client, "paper", "apply_risk_report", args={"report": broken})
        assert response.status_code == 422 and "audit" in response.json()["detail"]

    def test_clear_takes_a_session(self, client, deployments):
        assert (
            send(client, "paper", "clear_risk_report", args={"session": "soon"}).status_code == 422
        )
        assert (
            send(client, "paper", "clear_risk_report", args={"session": "2026-11-20"}).status_code
            == 202
        )
