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
