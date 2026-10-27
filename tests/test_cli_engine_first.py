"""cli.py's engine-first start (_EngineFirst): on its venue's windows the
engine is ready before the broker, then waits for it in-process -- watching
the market, answering the page -- until the broker is ready or the day ends.

The pieces around the wait are faked; the wait itself is the real one.
"""

from __future__ import annotations

from itertools import pairwise
from types import SimpleNamespace

import pytest

import cli
from engine.core.exceptions import BrokerUnavailableError


class Control:
    """LoopControl's surface the wait uses: apply commands, write status, and
    `stopping` once a disable was applied."""

    def __init__(self, disable_after=None):
        self.written, self.polls, self.stopping = [], 0, None
        self.disable_after = disable_after
        self.applier = self

    def poll(self):
        self.polls += 1
        if self.disable_after is not None and self.polls >= self.disable_after:
            self.stopping = "disabled by tester"

    def write_status(self, state=None, detail=None):
        self.written.append((state, detail))


def _engine(monkeypatch, verdicts, *, control=None, end=10_000.0):
    clock = {"now": 0.0}
    monkeypatch.setattr("time.time", lambda: clock["now"])
    monkeypatch.setattr("time.sleep", lambda s: clock.__setitem__("now", clock["now"] + s))
    engine = cli._EngineFirst.__new__(cli._EngineFirst)
    engine.config = SimpleNamespace(live=SimpleNamespace(poll_interval_seconds=60.0))
    engine.engine = {"state": "ready", "detail": "history replayed"}
    engine.inbox = None
    engine._stop = False
    engine._recorded = None
    watched = []
    engine._watch = lambda: watched.append(clock["now"])
    answers = iter(verdicts)
    engine._gate = lambda: lambda: next(answers)
    control = control if control is not None else Control()
    engine._control = lambda: control
    engine._day_end = lambda: end
    return engine, clock, watched, control


def test_it_waits_for_the_broker_watching_the_market_and_saying_why(monkeypatch, capsys):
    waiting = (False, "Fidelity is not ready: Fidelity signed you out")
    engine, _clock, watched, control = _engine(monkeypatch, [waiting] * 8 + [(True, "ready")])
    engine.wait_for_broker()
    assert control.polls == 8, "the page's commands are applied while it waits"
    assert watched and watched[0] == 0.0, "the market is watched from the start of the wait"
    assert all(b - a >= 60.0 for a, b in pairwise(watched)), "once a poll interval"
    assert set(control.written) == {("waiting_for_broker", waiting[1])}
    assert "waiting for the broker" in capsys.readouterr().out


def test_a_deployment_without_a_bridge_host_does_not_wait(monkeypatch):
    engine, _clock, _watched, control = _engine(monkeypatch, [])
    engine._gate = lambda: None
    engine.wait_for_broker()
    assert control.polls == 0


def test_a_broker_never_ready_ends_the_wait_at_the_days_end(monkeypatch):
    engine, *_ = _engine(monkeypatch, [(False, "no extension")] * 1000, end=300.0)
    with pytest.raises(BrokerUnavailableError, match="not ready all day: no extension"):
        engine.wait_for_broker()


def test_disabled_from_the_page_while_waiting_ends_it(monkeypatch):
    engine, *_ = _engine(monkeypatch, [(False, "signed out")] * 100, control=Control(2))
    with pytest.raises(BrokerUnavailableError, match="disabled by tester"):
        engine.wait_for_broker()


def test_a_stop_while_waiting_ends_it(monkeypatch):
    engine, *_ = _engine(monkeypatch, [(False, "signed out")] * 100)
    engine._on_signal(15, None)
    with pytest.raises(BrokerUnavailableError, match="stopped"):
        engine.wait_for_broker()


def test_only_the_extended_windows_make_an_alpaca_broker_extended():
    def config(sessions=(), extended=False):
        traded = sessions or (
            ("pre_market", "regular", "after_hours") if extended else ("regular",)
        )
        return SimpleNamespace(
            live=SimpleNamespace(extended_hours=extended, traded_sessions=traded)
        )

    assert cli._trades_extended(config()) is False
    assert cli._trades_extended(config(extended=True)) is True
    assert cli._trades_extended(config(sessions=("pre_market", "regular"))) is True
    assert cli._trades_extended(config(sessions=("regular",))) is False
