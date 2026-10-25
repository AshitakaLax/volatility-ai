"""The Live page's controls, through the real router and a real ledger.

server/live_control.py queues; the trader applies. The end-to-end tests here
play the trader's part with the same SupervisorControl the supervisor runs
between sessions, so "the page paused it" is checked in the ledger's own
circuit breaker, not in a response body.
"""

from __future__ import annotations

import time

import pytest
import yaml
from fastapi.testclient import TestClient

from engine.core.persistence import LedgerStore
from engine.trading.control_inbox import ControlInbox
from engine.trading.operator_control import SupervisorControl
from engine.trading.risk_manager import CircuitBreaker, CircuitBreakerState
from server.app import app

PAPER = "config/paper_aggressive.yaml"
REAL_MONEY = "config/production.yaml"


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def deployments(tmp_path, monkeypatch):
    """Three deployments: a paper one that grants everything, a paper one
    whose config grants nothing, and a real-money one."""
    with open(PAPER, encoding="utf-8") as handle:
        bare = yaml.safe_load(handle)
    bare["live"].pop("control", None)
    bare_path = tmp_path / "bare.yaml"
    bare_path.write_text(yaml.safe_dump(bare), encoding="utf-8")

    entries = {}
    for deployment_id, config in (
        ("paper", PAPER),
        ("bare", str(bare_path)),
        ("money", REAL_MONEY),
    ):
        ledger = tmp_path / f"{deployment_id}.db"
        LedgerStore(str(ledger)).close()
        entries[deployment_id] = {
            "label": deployment_id,
            "config": config,
            "state_db": str(ledger),
            "control_dir": str(tmp_path / f"control-{deployment_id}"),
        }
    registry = tmp_path / "deployments.yaml"
    registry.write_text(yaml.safe_dump({"deployments": entries}), encoding="utf-8")
    monkeypatch.setenv("VAI_DEPLOYMENTS", str(registry))
    return entries


def send(client, deployment, type_, **body):
    body.setdefault("reason", "a test")
    body.setdefault("operator", "tester")
    return client.post(f"/api/live/deployments/{deployment}/commands", json={"type": type_, **body})


def trader(entry) -> SupervisorControl:
    """The supervisor's side of the control directory, as between sessions."""
    return SupervisorControl(ControlInbox(entry["control_dir"]), state_db=entry["state_db"])


def breaker(entry) -> CircuitBreaker:
    store = LedgerStore(entry["state_db"])
    try:
        return CircuitBreaker(store=store)
    finally:
        store.close()


class TestQueueing:
    def test_a_command_is_queued_not_applied(self, client, deployments):
        response = send(client, "paper", "pause_buys")
        assert response.status_code == 202
        body = response.json()
        assert body["command"]["status"] == "queued" and body["new"] is True
        assert body["command"]["operator"] == "tester"
        assert body["warning"] and "not running" in body["warning"]
        assert breaker(deployments["paper"]).allows_new_buys, "nothing applied yet"

    def test_the_trader_applies_it_and_the_page_sees_it(self, client, deployments):
        command_id = send(client, "paper", "pause_buys").json()["command"]["id"]
        trader(deployments["paper"]).poll()

        assert breaker(deployments["paper"]).state is CircuitBreakerState.MANUAL_RESET_REQUIRED
        detail = client.get("/api/live/deployments/paper").json()
        assert detail["state"]["halt"].startswith("paused by tester")
        (command,) = detail["commands"]
        assert command["id"] == command_id and command["status"] == "applied"

        send(client, "paper", "resume_buys", args={"reset_drawdown_baseline": True})
        trader(deployments["paper"]).poll()
        assert breaker(deployments["paper"]).allows_new_buys

    def test_disable_then_enable(self, client, deployments):
        def enabled() -> bool:
            listed = {d["id"]: d for d in client.get("/api/live/deployments").json()}
            return listed["paper"]["desired"]["enabled"]

        send(client, "paper", "disable")
        trader(deployments["paper"]).poll()
        assert enabled() is False
        send(client, "paper", "enable")
        trader(deployments["paper"]).poll()
        assert enabled() is True

    def test_a_double_click_queues_once(self, client, deployments):
        first = send(client, "paper", "pause_buys", idempotency_key="k1").json()
        second = send(client, "paper", "pause_buys", idempotency_key="k1").json()
        assert second["new"] is False and second["command"]["id"] == first["command"]["id"]

    def test_a_queued_command_can_be_withdrawn_once(self, client, deployments):
        command_id = send(client, "paper", "pause_buys").json()["command"]["id"]
        url = f"/api/live/deployments/paper/commands/{command_id}/cancel"
        assert client.post(url, json={"operator": "tester"}).json()["status"] == "cancelled"
        assert client.post(url, json={"operator": "tester"}).status_code == 409
        trader(deployments["paper"]).poll()
        assert breaker(deployments["paper"]).allows_new_buys


class TestWhatTheConfigAllows:
    def test_pausing_is_always_allowed(self, client, deployments):
        assert send(client, "bare", "pause_buys").status_code == 202

    def test_everything_else_needs_the_configs_grant(self, client, deployments):
        response = send(client, "bare", "resume_buys")
        assert response.status_code == 403
        assert "live.control.resume_buys" in response.json()["detail"]
        assert send(client, "bare", "disable").status_code == 403

    def test_real_money_needs_the_id_typed_back(self, client, deployments):
        refused = send(client, "money", "resume_buys")
        assert refused.status_code == 409 and "real money" in refused.json()["detail"]
        assert send(client, "money", "resume_buys", confirm="money").status_code == 202
        assert send(client, "money", "pause_buys").status_code == 202, "a pause never waits"

    def test_disabling_open_lots_needs_the_id_typed_back(self, client, deployments):
        from engine.core.ledger import Lot

        store = LedgerStore(deployments["paper"]["state_db"])
        store.record_open_lot(
            Lot(order_id="lot-1", symbol="TQQQ", buy_price=50.0, shares=10.0, profit_target=0.01)
        )
        store.close()
        refused = send(client, "paper", "disable", args={"mode": "now"})
        assert refused.status_code == 409 and "1 open lot" in refused.json()["detail"]
        assert send(client, "paper", "disable", args={"mode": "wind_down"}).status_code == 202
        assert send(client, "paper", "disable", confirm="paper").status_code == 202

    def test_arguments_are_checked(self, client, deployments):
        assert send(client, "paper", "disable", args={"mode": "sometime"}).status_code == 422
        assert send(client, "paper", "pause_buys", args={"x": 1}).status_code == 422
        assert send(client, "paper", "liquidate_all").status_code == 422
        assert send(client, "paper", "pause_buys", reason="no").status_code == 422
        assert send(client, "paper", "pause_buys", operator="").status_code == 422

    def test_an_unknown_deployment_is_a_404(self, client, deployments):
        assert send(client, "nope", "pause_buys").status_code == 404


class TestCrossSite:
    """No login, by the operator's choice -- but a page on another site,
    open in the operator's browser, cannot send commands."""

    def test_another_sites_page_is_refused(self, client, deployments):
        for headers in (
            {"Origin": "https://evil.example", "Sec-Fetch-Site": "cross-site"},
            {"Origin": "https://evil.example"},
            {"Sec-Fetch-Site": "same-site"},
        ):
            response = client.post(
                "/api/live/deployments/paper/commands",
                json={"type": "pause_buys", "reason": "a test", "operator": "x"},
                headers=headers,
            )
            assert response.status_code == 403, headers

    def test_the_page_itself_and_scripts_are_not(self, client, deployments):
        for headers in (
            {"Origin": "http://testserver", "Sec-Fetch-Site": "same-origin"},
            {"Origin": "http://127.0.0.1:5173"},
            {},
        ):
            response = client.post(
                "/api/live/deployments/paper/commands",
                json={"type": "pause_buys", "reason": "a test", "operator": "x"},
                headers=headers,
            )
            assert response.status_code == 202, headers


def trader_with_algorithms(entry) -> SupervisorControl:
    """The supervisor's side with the algorithm commands, as
    tools/market_hours_supervisor.py builds it."""
    from engine.core.config import BacktestConfig
    from research.strategies.live_algorithm import AlgorithmControl, algorithm_handlers
    from research.strategies.strategy_registry import STRATEGIES

    config = BacktestConfig.from_yaml(entry["config"])
    grants = config.live.control.effective(config.live.paper_trading)
    control = AlgorithmControl(
        config,
        state_db=entry["state_db"],
        registry=STRATEGIES,
        allowed=False,
        web_allowed=grants.algorithm_changes,
        profiles_only=grants.profiles_only,
    )
    return SupervisorControl(
        ControlInbox(entry["control_dir"]),
        state_db=entry["state_db"],
        extra=algorithm_handlers(
            control, symbol=config.backtest.symbol, paper=config.live.paper_trading
        ),
    )


class TestAlgorithm:
    def test_it_says_what_is_traded_and_what_it_could_be(self, client, deployments):
        body = client.get("/api/live/deployments/paper/algorithm").json()
        assert body["editable"] and not body["profiles_only"] and body["paper"]
        assert body["source"] == "config" and body["override"] is None
        assert body["current"]["strategy_id"] == "hf_local_reference"
        assert {p["id"] for p in body["profiles"]} >= {"champion-hf-tqqq", "ultimate-tqqq"}
        ultimate = next(s for s in body["strategies"] if s["id"] == "ultimate")
        assert not ultimate["live_capable"], "the champion deployment trades extended hours"

    def test_a_check_says_why_or_what_it_would_do(self, client, deployments):
        refused = client.post(
            "/api/live/deployments/paper/algorithm/check", json={"profile_id": "ultimate-tqqq"}
        ).json()
        assert not refused["ok"] and "allow_signal_exit" in refused["errors"][0]
        custom = client.post(
            "/api/live/deployments/paper/algorithm/check",
            json={
                "strategy_id": "fixed",
                "strategy_params": {"allocation_pct": 0.05},
                "step": 0.01,
                "profit_target": 0.005,
            },
        ).json()
        assert custom["ok"] and custom["change"]["strategy_id"] == "fixed"
        assert custom["impact"]["open_lots"] == 0 and custom["typed"] is None

    def test_real_money_takes_only_promoted_profiles(self, client, deployments):
        custom = client.post(
            "/api/live/deployments/money/algorithm/check",
            json={"strategy_id": "fixed", "step": 0.01, "profit_target": 0.005},
        ).json()
        assert not custom["ok"] and "committed profiles" in custom["errors"][0]
        profile = client.post(
            "/api/live/deployments/money/algorithm/check", json={"profile_id": "ultimate-tqqq"}
        ).json()
        assert not profile["ok"] and "promotion" in profile["errors"][0]

    def test_a_switch_is_queued_applied_by_the_trader_and_shown(self, client, deployments):
        before = client.get("/api/live/deployments/paper/algorithm").json()
        response = send(
            client,
            "paper",
            "switch_algorithm",
            args={
                "strategy_id": "fixed",
                "strategy_params": {"allocation_pct": 0.05},
                "step": 0.01,
                "profit_target": 0.005,
            },
            timing="next_session",
        )
        assert response.status_code == 202, response.text
        trader_with_algorithms(deployments["paper"]).poll()

        after = client.get("/api/live/deployments/paper/algorithm").json()
        assert before["source"] == "config" and after["source"] == "web"
        assert after["current"]["strategy_id"] == "fixed"
        assert after["override"]["changedBy"] == "tester"
        (command,) = client.get("/api/live/deployments/paper/commands").json()
        assert command["status"] == "applied" and "switching to fixed" in command["detail"]

        send(client, "paper", "revert_algorithm")
        trader_with_algorithms(deployments["paper"]).poll()
        assert client.get("/api/live/deployments/paper/algorithm").json()["source"] == "config"

    def test_a_switch_that_would_be_refused_is_refused_now(self, client, deployments):
        response = send(client, "paper", "switch_algorithm", args={"profile_id": "ultimate-tqqq"})
        assert response.status_code == 422 and "allow_signal_exit" in response.json()["detail"]

    def test_switching_when_flat_pauses_buying_first(self, client, deployments):
        send(
            client,
            "paper",
            "switch_algorithm",
            args={"profile_id": "champion-hf-tqqq"},
            timing="when_flat",
        )
        queued = client.get("/api/live/deployments/paper/commands").json()
        assert [c["type"] for c in reversed(queued)] == ["pause_buys", "switch_algorithm"]

    def test_algorithm_commands_need_the_grant(self, client, deployments):
        for kind in ("revert_algorithm", "rewarm"):
            assert send(client, "bare", kind).status_code == 403
            assert send(client, "paper", kind).status_code == 202


class TestFreshLedgerAndAccounts:
    def test_a_fresh_ledger_needs_paper_the_grant_and_a_disabled_deployment(
        self, client, deployments
    ):
        assert send(client, "bare", "reset_paper_ledger").status_code == 403
        assert send(client, "money", "reset_paper_ledger").status_code == 403, "never real money"
        enabled = send(client, "paper", "reset_paper_ledger", confirm="paper")
        assert enabled.status_code == 409 and "Disable paper first" in enabled.json()["detail"]

        ControlInbox(deployments["paper"]["control_dir"]).set_desired(
            enabled=False, wind_down=False, by="op", reason="test"
        )
        untyped = send(client, "paper", "reset_paper_ledger")
        assert untyped.status_code == 409 and "archived" in untyped.json()["detail"]
        assert send(client, "paper", "reset_paper_ledger", confirm="paper").status_code == 202

    def test_enabling_a_second_loop_on_one_account_is_refused(self, client, deployments):
        """`paper` is trading with account tag abc...; `money` reports the
        same tag. Enabling `money` would put two loops on one account."""
        ControlInbox(deployments["paper"]["control_dir"]).write_status(
            state="trading", process="loop", heartbeat_seconds=60.0, account="abc123abc123"
        )
        money = ControlInbox(deployments["money"]["control_dir"])
        unknown = send(client, "money", "enable", confirm="money")
        assert unknown.status_code == 202, "money has reported no tag: nothing to compare"

        money.write_status(
            state="disabled", process="supervisor", heartbeat_seconds=15.0, account="abc123abc123"
        )
        refused = send(client, "money", "enable", confirm="money")
        assert refused.status_code == 409 and "paper trades the same" in refused.json()["detail"]

        money.write_status(
            state="disabled", process="supervisor", heartbeat_seconds=15.0, account="ffffffffffff"
        )
        assert send(client, "money", "enable", confirm="money").status_code == 202


def test_real_money_switches_at_most_once_a_day(client, deployments, tmp_path, monkeypatch):
    """With a promoted profile, the first switch is accepted and a second the
    same day is refused."""
    import json

    profiles = tmp_path / "profiles"
    profiles.mkdir()
    (profiles / "promotion.json").write_text(json.dumps({"passed": True}))
    (profiles / "fixed-tqqq.yaml").write_text(
        "id: fixed-tqqq\nsymbols: [TQQQ]\nstrategy_id: fixed\n"
        "strategy_params: {allocation_pct: 0.05}\nstep: 0.01\nprofit_target: 0.005\n"
        "evidence: {promotion: promotion.json}\n"
    )
    monkeypatch.setenv("VAI_LIVE_PROFILES", str(profiles))
    body = {"args": {"profile_id": "fixed-tqqq"}, "confirm": "money"}
    first = send(client, "money", "switch_algorithm", **body)
    assert first.status_code == 202, first.text
    second = send(client, "money", "switch_algorithm", **body)
    assert second.status_code == 409 and "once a day" in second.json()["detail"]
    assert (
        send(client, "paper", "switch_algorithm", args={"profile_id": "fixed-tqqq"}).status_code
        == 202
    )


# -- a Fidelity deployment's bridge host --------------------------------------------


@pytest.fixture
def fidelity(tmp_path, monkeypatch, deployments):
    """The three deployments above, and a real-money Fidelity one beside them."""
    config = {
        "strategy": {"strategy_id": "fixed", "strategy_params": {"allocation_pct": 0.05}},
        "grid": {"steps": [0.01], "profit_targets": [0.005]},
        "backtest": {"symbol": "RSP", "initial_cash": 10_000.0},
        "live": {
            "enabled": True,
            "paper_trading": False,
            "step": 0.01,
            "profit_target": 0.005,
            "broker": "fidelity",
            "fidelity": {
                "allowed_accounts": ["999888777"],
                "account": "999888777",
                "account_name": "Traditional IRA",
                "dry_run": False,
                "allowed_symbols": ["RSP"],
                "max_order_value": 2_000.0,
            },
        },
    }
    path = tmp_path / "fidelity.yaml"
    path.write_text(yaml.safe_dump(config), encoding="utf-8")
    ledger = tmp_path / "fidelity.db"
    LedgerStore(str(ledger)).close()
    entries = {
        **deployments,
        "fid": {
            "label": "Fidelity",
            "config": str(path),
            "state_db": str(ledger),
            "control_dir": str(tmp_path / "control-fid"),
            "broker": "fidelity",
        },
    }
    registry = tmp_path / "deployments.yaml"
    registry.write_text(yaml.safe_dump({"deployments": entries}), encoding="utf-8")
    monkeypatch.setenv("VAI_DEPLOYMENTS", str(registry))
    return entries["fid"]


def _bridge(entry, **fields) -> ControlInbox:
    inbox = ControlInbox(f"{entry['control_dir']}/bridge", clock=fields.pop("clock", time.time))
    inbox.write_status(
        state="listening",
        process="bridge",
        heartbeat_seconds=15.0,
        listening=True,
        readiness={"ready": False, "blocking": "fidelity", "summary": "Fidelity tab: signed out"},
        **fields,
    )
    return inbox


class TestFidelityBridge:
    def test_the_bridge_hosts_report_reaches_the_strip(self, client, fidelity):
        _bridge(fidelity, connection={"connected": True, "client": "172.16.0.130"})
        listed = {d["id"]: d for d in client.get("/api/live/deployments").json()}
        bridge = listed["fid"]["bridge"]
        assert bridge["stale"] is False and bridge["readiness"]["blocking"] == "fidelity"
        assert bridge["connection"]["client"] == "172.16.0.130"
        assert "pid" not in bridge
        assert listed["paper"]["bridge"] is None, "an Alpaca deployment has no bridge"

    def test_a_silent_bridge_host_is_called_stale(self, client, fidelity):
        _bridge(fidelity, clock=lambda: 1_000_000.0)  # long ago
        listed = {d["id"]: d for d in client.get("/api/live/deployments").json()}
        assert listed["fid"]["bridge"]["stale"] is True

    def test_no_bridge_host_ever_is_none(self, client, fidelity):
        listed = {d["id"]: d for d in client.get("/api/live/deployments").json()}
        assert listed["fid"]["bridge"] is None

    def test_a_check_goes_to_the_bridge_host_without_a_typed_id(self, client, fidelity):
        """Read-only, so real money or not it needs no confirmation -- and it
        is queued where the bridge host applies it, never the trader's inbox."""
        response = send(client, "fid", "check_connection")
        assert response.status_code == 202, response.text
        body = response.json()
        assert "bridge host is not running" in body["warning"]
        assert [c.id for c in ControlInbox(f"{fidelity['control_dir']}/bridge").queued()] == [
            body["command"]["id"]
        ]
        assert ControlInbox(fidelity["control_dir"]).queued() == []
        detail = client.get("/api/live/deployments/fid").json()
        assert detail["commands"][0]["type"] == "check_connection"
        assert detail["pending"] == 1

        cancelled = client.post(
            f"/api/live/deployments/fid/commands/{body['command']['id']}/cancel",
            json={"operator": "tester"},
        )
        assert cancelled.status_code == 200 and cancelled.json()["status"] == "cancelled"

    def test_a_running_bridge_host_takes_the_check_without_a_warning(self, client, fidelity):
        _bridge(fidelity)
        assert send(client, "fid", "check_connection").json()["warning"] is None

    def test_only_a_fidelity_deployment_checks_a_connection(self, client, fidelity):
        response = send(client, "paper", "check_connection")
        assert response.status_code == 409 and "bridge host" in response.json()["detail"]

    def test_a_check_takes_no_arguments(self, client, fidelity):
        response = send(client, "fid", "check_connection", args={"deep": True})
        assert response.status_code == 422

    def test_the_bridge_journal_is_served_oldest_first_within_the_hours_asked(
        self, client, fidelity
    ):
        inbox = ControlInbox(f"{fidelity['control_dir']}/bridge")
        now = time.time()
        inbox.record_event({"t": now - 3 * 24 * 3600, "kind": "connected", "detail": "old"})
        inbox.record_event({"t": now - 120, "kind": "disconnected", "detail": "went away"})
        inbox.record_event({"t": now - 60, "kind": "connected", "detail": "came back"})
        events = client.get("/api/live/deployments/fid/bridge/events?hours=48").json()
        assert [e["detail"] for e in events] == ["went away", "came back"]
        everything = client.get("/api/live/deployments/fid/bridge/events?hours=96").json()
        assert len(everything) == 3
        assert client.get("/api/live/deployments/paper/bridge/events").json() == []
