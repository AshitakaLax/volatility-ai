"""tools/market_hours_supervisor.py and the Live page: a disabled deployment
holds instead of trading, and a stop the page asked for is not a crash.

The loop itself is faked (run_session); the control directory, the desired
state and the waits are the real ones, on an injected clock -- tests never
sleep.
"""

from __future__ import annotations

from types import SimpleNamespace

import pytest

import tools.market_hours_supervisor as supervisor
from engine.core.persistence import LedgerStore
from engine.trading.control_inbox import Command, ControlInbox
from engine.trading.operator_control import SupervisorControl

POLL = 60.0


class Clock:
    def __init__(self) -> None:
        self.now = 1_800_000_000.0
        self.slept: list[float] = []

    def time(self) -> float:
        return self.now

    def sleep(self, seconds: float) -> None:
        self.slept.append(seconds)
        self.now += seconds


@pytest.fixture
def clock(monkeypatch):
    clock = Clock()
    monkeypatch.setattr(supervisor, "time", SimpleNamespace(time=clock.time, sleep=clock.sleep))
    return clock


@pytest.fixture
def control(tmp_path, clock):
    ledger = str(tmp_path / "ledger.db")
    LedgerStore(ledger).close()
    inbox = ControlInbox(tmp_path / "control", clock=clock.time)
    return SupervisorControl(inbox, state_db=ledger, clock=clock.time, sleep=clock.sleep)


def args(**kw):
    return SimpleNamespace(max_restarts=3, control_dir=None, **kw)


def ask(control, type_, clock, **kw):
    control.inbox.enqueue(
        Command.new(type_, reason="from the page", operator="tester", now=clock.now, **kw)
    )


def test_a_disabled_deployment_holds_until_enabled(control, clock, monkeypatch):
    control.inbox.set_desired(enabled=False, wind_down=False, by="op", reason="test")
    runs = []

    def run_session(_args, ticks, deadline, _control):
        runs.append(clock.now)
        clock.now = deadline  # the loop trades the rest of the session
        return 0

    monkeypatch.setattr(supervisor, "run_session", run_session)
    original_sleep = clock.sleep

    def sleep(seconds):
        original_sleep(seconds)
        if len(clock.slept) == 4:
            ask(control, "enable", clock)

    control._sleep = sleep
    start = clock.now
    code = supervisor._run_until(args(), POLL, start + 3600, control, "session")
    assert code == 0 and control.enabled()
    assert len(runs) == 1 and runs[0] == start + 4 * 15.0, "held four slices, then traded"


def test_a_stop_the_page_asked_for_is_not_a_crash(control, clock, monkeypatch):
    calls = []

    def run_session(_args, ticks, deadline, _control):
        calls.append(clock.now)
        # The loop applied "disable": it set the desired state and exited 0.
        control.inbox.set_desired(enabled=False, wind_down=False, by="op", reason="page")
        clock.now += 600
        return 0

    monkeypatch.setattr(supervisor, "run_session", run_session)
    code = supervisor._run_until(args(), POLL, clock.now + 3600, control, "session")
    assert code == 0 and len(calls) == 1, "held, not restarted"
    assert control.inbox.status()["state"] == "disabled"


def test_crashes_are_still_capped(control, clock, monkeypatch):
    def run_session(_args, ticks, deadline, _control):
        clock.now += 60
        return 1

    monkeypatch.setattr(supervisor, "run_session", run_session)
    assert supervisor._run_until(args(), POLL, clock.now + 36000, control, "session") == 1


def test_a_broker_that_cannot_be_reached_yet_is_waited_for_not_counted(control, clock, monkeypatch):
    """10-22 and 10-23: five fast failures to reach Fidelity spent the
    restart cap, then fifteen minutes passed with the page saying "between
    sessions". A start that could not reach the broker is retried until the
    session ends, uncounted, with the trader's own reason on the page."""
    from engine.trading.runtime_lifecycle import EXIT_BROKER_UNAVAILABLE

    reported: list[tuple[str, str]] = []
    original_report = control.report

    def report(state, detail="", **fields):
        reported.append((state, detail))
        return original_report(state, detail, **fields)

    control.report = report
    calls = []

    def run_session(_args, ticks, deadline, _control):
        calls.append(clock.now)
        if len(calls) <= 5:  # more failures than max_restarts (3) allows
            control.inbox.write_status(
                state="recovery_required",
                detail="broker connection failed: Port 8765 is already in use",
                process="loop",
            )
            clock.now += 5
            return EXIT_BROKER_UNAVAILABLE
        clock.now = deadline  # then it connects and trades the session
        return 0

    monkeypatch.setattr(supervisor, "run_session", run_session)
    monkeypatch.setattr(supervisor, "log", lambda _message: None)
    start = clock.now
    assert supervisor._run_until(args(), POLL, start + 36000, control, "session") == 0
    assert len(calls) == 6, "never given up on"
    assert calls[1] - calls[0] == 5 + supervisor.BROKER_RETRY_SECONDS
    assert ("waiting_for_broker", "broker connection failed: Port 8765 is already in use") in (
        reported
    )


def test_waiting_for_the_broker_says_disabled_once_disabled(control, clock, monkeypatch):
    """Disabled from the page during the wait: the page is told "disabled",
    not that it is still waiting to trade."""
    from engine.trading.runtime_lifecycle import EXIT_BROKER_UNAVAILABLE

    states: list[str] = []
    original_report = control.report

    def report(state, detail="", **fields):
        states.append(state)
        return original_report(state, detail, **fields)

    def run_session(_args, ticks, deadline, _control):
        return EXIT_BROKER_UNAVAILABLE

    original_sleep = clock.sleep

    def sleep(seconds):
        original_sleep(seconds)
        control.inbox.set_desired(enabled=False, wind_down=False, by="op", reason="page")

    control.report = report
    control._sleep = sleep
    monkeypatch.setattr(supervisor, "run_session", run_session)
    monkeypatch.setattr(supervisor, "log", lambda _message: None)
    supervisor._run_until(args(), POLL, clock.now + 600, control, "session")
    assert states[:2] == ["waiting_for_broker", "disabled"]


def test_without_a_control_directory_it_behaves_as_before(clock, monkeypatch):
    calls = []

    def run_session(_args, ticks, deadline, _control):
        calls.append(ticks)
        clock.now = deadline
        return 0

    monkeypatch.setattr(supervisor, "run_session", run_session)
    assert supervisor._run_until(args(), POLL, clock.now + 3600, None, "session") == 0
    assert calls == [60]


def test_the_child_is_told_where_commands_arrive(monkeypatch, tmp_path):
    seen = {}

    class Process:
        returncode = 0

        def __init__(self, command, **_kw):
            seen["command"] = command

        def poll(self):
            return 0

    monkeypatch.setattr(supervisor.subprocess, "Popen", Process)
    monkeypatch.setattr(supervisor, "log", lambda _message: None)
    run_args = SimpleNamespace(
        config="c.yaml", state_db="s.db", control_dir=str(tmp_path / "control")
    )
    supervisor.run_session(run_args, 5, float("inf"))
    command = seen["command"]
    assert command[command.index("--control-dir") + 1] == str(tmp_path / "control")


def test_a_fidelity_supervisor_names_its_own_account(monkeypatch, tmp_path):
    """While it waits for the open, as the loop does while it trades: the
    Fidelity account it trades, not the Alpaca key it reads prices with --
    which the paper trader beside it may share. A config that does not load
    leaves the key's tag."""
    import yaml

    from engine.trading.operator_control import account_fingerprint

    monkeypatch.setenv("APCA_API_KEY_ID", "PKTESTKEY")
    monkeypatch.setattr(supervisor, "log", lambda _message: None)
    config = tmp_path / "fidelity_live.yaml"
    config.write_text(
        yaml.safe_dump(
            {
                "strategy": {"strategy_id": "fixed", "strategy_params": {"allocation_pct": 0.05}},
                "grid": {"steps": [0.01], "profit_targets": [0.005]},
                "backtest": {"symbol": "TQQQ", "initial_cash": 10_000.0},
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
                        "allowed_symbols": ["TQQQ"],
                        "max_order_value": 2_000.0,
                    },
                },
            }
        ),
        encoding="utf-8",
    )
    ledger = str(tmp_path / "ledger.db")
    LedgerStore(ledger).close()

    def reported(config_path) -> str | None:
        control = supervisor._control_for(
            SimpleNamespace(
                control_dir=str(tmp_path / "control"), config=str(config_path), state_db=ledger
            )
        )
        control.report("waiting_for_open")
        return control.inbox.status()["account"]

    tag = reported(config)
    assert tag.startswith("fidelity-") and "999888777" not in tag
    assert reported(tmp_path / "missing.yaml") == account_fingerprint()


# -- a Fidelity session starts when its bridge host says it is ready ------------------


def test_the_session_waits_for_the_bridge_to_be_ready_and_says_why(control, clock, monkeypatch):
    answers = iter(
        [(False, "Fidelity is not ready: Fidelity tab: Fidelity signed you out")] * 3
        + [(True, "ready")]
    )
    runs = []
    states: list[tuple[str, str]] = []
    original_report = control.report

    def report(state, detail="", **fields):
        states.append((state, detail))
        return original_report(state, detail, **fields)

    def run_session(_args, ticks, deadline, _control):
        runs.append(clock.now)
        clock.now = deadline
        return 0

    control.report = report
    monkeypatch.setattr(supervisor, "run_session", run_session)
    monkeypatch.setattr(supervisor, "log", lambda _message: None)
    start = clock.now
    code = supervisor._run_until(
        args(), POLL, start + 3600, control, "session", gate=lambda: next(answers)
    )
    assert code == 0 and len(runs) == 1
    assert runs[0] == start + 3 * control.slice_seconds, "launched as soon as it turned ready"
    assert (
        "waiting_for_broker",
        "Fidelity is not ready: Fidelity tab: Fidelity signed you out",
    ) in (states)


def test_a_bridge_never_ready_runs_no_loop(control, clock, monkeypatch):
    def run_session(*_a):
        raise AssertionError("no loop may start on a bridge that is not ready")

    monkeypatch.setattr(supervisor, "run_session", run_session)
    monkeypatch.setattr(supervisor, "log", lambda _message: None)
    gate = lambda: (False, "Fidelity is not ready: Extension: not connected")  # noqa: E731
    assert supervisor._run_until(args(), POLL, clock.now + 600, control, "session", gate=gate) == 0
    assert control.inbox.status()["state"] == "waiting_for_broker"


def test_the_bridge_verdict_reads_the_hosts_status_file():
    from datetime import UTC, datetime

    now = 1_800_000_000.0
    fresh = datetime.fromtimestamp(now - 5, UTC).isoformat()
    stale = datetime.fromtimestamp(now - 600, UTC).isoformat()
    ready = {"updated_at": fresh, "heartbeat_seconds": 15, "readiness": {"ready": True}}
    blocked = {
        "updated_at": fresh,
        "heartbeat_seconds": 15,
        "readiness": {
            "ready": False,
            "summary": "Allow trading: off: every order is refused in the browser",
            "fix": 'turn "Allow trading" on',
        },
    }
    assert supervisor.bridge_verdict(ready, now) == (True, "ready")
    ok, why = supervisor.bridge_verdict(blocked, now)
    assert not ok and "Allow trading: off" in why and 'turn "Allow trading" on' in why
    for silent in (None, {**ready, "updated_at": stale}, {**ready, "state": "stopped"}):
        ok, why = supervisor.bridge_verdict(silent, now)
        assert not ok and "fidelity-bridge" in why


def test_only_a_fidelity_deployment_with_a_bridge_host_is_gated(monkeypatch, tmp_path):
    fidelity = SimpleNamespace(live=SimpleNamespace(broker="fidelity"))
    alpaca = SimpleNamespace(live=SimpleNamespace(broker="alpaca"))
    with_dir = SimpleNamespace(control_dir=str(tmp_path))
    monkeypatch.delenv("VAI_BRIDGE_SOCKET", raising=False)
    assert supervisor._broker_gate(with_dir, fidelity) is None, "it holds its own bridge"
    monkeypatch.setenv("VAI_BRIDGE_SOCKET", "/app/bridge/bridge.sock")
    assert supervisor._broker_gate(with_dir, alpaca) is None
    gate = supervisor._broker_gate(with_dir, fidelity)
    assert gate is not None and gate()[0] is False, "no status yet: not ready"
