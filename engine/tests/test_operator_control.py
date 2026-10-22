"""The Live page's commands, from the inbox to the trading process.

engine/trading/control_inbox.py (the files) and operator_control.py (the
trader applying them). The loop side runs a real LiveTradingLoop with the
fakes test_live_trading_loop.py drives it with, so "pause" is proven by the
buy that does not happen, not by a flag.
"""

from __future__ import annotations

import os
from datetime import timedelta
from pathlib import Path

import pytest

from engine.core.persistence import LedgerStore
from engine.tests.test_live_trading_loop import BASE_TS, FakeBroker, FakeMarketData, make_loop
from engine.trading.control_inbox import (
    NOW_TTL_SECONDS,
    Command,
    ControlInbox,
    InvalidCommand,
)
from engine.trading.operator_control import (
    CommandRejected,
    ControlApplier,
    LoopControl,
    SupervisorControl,
)
from engine.trading.risk_manager import CircuitBreaker, CircuitBreakerState

T0 = 1_800_000_000.0


class Clock:
    def __init__(self, now: float = T0) -> None:
        self.now = now

    def __call__(self) -> float:
        return self.now


def command(type_: str = "pause_buys", *, now: float = T0, **kw) -> Command:
    kw.setdefault("reason", "a test reason")
    kw.setdefault("operator", "tester")
    return Command.new(type_, now=now, **kw)


@pytest.fixture
def clock():
    return Clock()


@pytest.fixture
def inbox(tmp_path, clock):
    return ControlInbox(tmp_path / "control", clock=clock)


# --------------------------------------------------------------------
# The inbox
# --------------------------------------------------------------------


class TestCommands:
    def test_a_command_needs_a_reason_and_an_operator(self):
        with pytest.raises(InvalidCommand, match="reason"):
            command(reason="no")
        with pytest.raises(InvalidCommand, match="operator"):
            command(operator="  ")

    def test_only_known_commands_and_timings(self):
        with pytest.raises(InvalidCommand, match="unknown command"):
            command("liquidate_all")
        with pytest.raises(InvalidCommand, match="timing"):
            command(timing="eventually")

    def test_now_expires_sooner_than_later(self):
        soon = command(now=T0)
        later = command(timing="next_session", now=T0)
        assert soon.expired(T0 + NOW_TTL_SECONDS)
        assert not later.expired(T0 + NOW_TTL_SECONDS)


class TestInbox:
    def test_queued_in_the_order_they_were_asked(self, inbox):
        first, second = command(now=T0), command("resume_buys", now=T0 + 1)
        inbox.enqueue(second)
        inbox.enqueue(first)
        assert [c.id for c in inbox.queued()] == [first.id, second.id]

    def test_a_repeated_idempotency_key_queues_once(self, inbox):
        original, new = inbox.enqueue(command(idempotency_key="click-1"))
        again, new_again = inbox.enqueue(command(idempotency_key="click-1"))
        assert new and not new_again and again.id == original.id
        assert len(inbox.queued()) == 1

    def test_claim_and_cancel_race_has_one_winner(self, inbox):
        queued, _ = inbox.enqueue(command())
        assert inbox.claim(queued)
        assert inbox.cancel(queued.id, "someone") is None, "already claimed"
        other, _ = inbox.enqueue(command())
        assert inbox.cancel(other.id, "someone")["status"] == "cancelled"
        assert not inbox.claim(other), "already cancelled"

    def test_history_says_what_became_of_each(self, inbox, clock):
        applied, _ = inbox.enqueue(command(now=T0))
        inbox.claim(applied)
        inbox.record(applied, "applied", "done")
        taken, _ = inbox.enqueue(command(now=T0 + 1))
        inbox.claim(taken)
        cancelled, _ = inbox.enqueue(command(now=T0 + 2))
        inbox.cancel(cancelled.id, "op")
        stale, _ = inbox.enqueue(command(now=T0 + 3))
        clock.now = T0 + NOW_TTL_SECONDS + 10
        fresh, _ = inbox.enqueue(command(now=clock.now))

        statuses = {row["id"]: row["status"] for row in inbox.history()}
        assert statuses == {
            applied.id: "applied",
            taken.id: "applying",
            cancelled.id: "cancelled",
            stale.id: "expired",
            fresh.id: "queued",
        }
        assert inbox.history(limit=2)[0]["id"] == fresh.id

    def test_writes_leave_no_temporary_files(self, inbox):
        inbox.enqueue(command())
        inbox.set_desired(enabled=False, wind_down=False, by="op", reason="test")
        inbox.write_status(state="trading")
        leftovers = [p for p in inbox.root.rglob("*") if p.name.endswith(".tmp")]
        assert leftovers == []

    def test_enabled_unless_an_operator_said_otherwise(self, inbox):
        assert inbox.desired()["enabled"] is True
        inbox.set_desired(enabled=False, wind_down=False, by="op", reason="weekend")
        assert inbox.desired() | {"at": None} == {
            "enabled": False,
            "wind_down": False,
            "by": "op",
            "reason": "weekend",
            "at": None,
        }


# --------------------------------------------------------------------
# Applying
# --------------------------------------------------------------------


class TestApplier:
    def test_each_command_gets_an_outcome(self, inbox):
        good, _ = inbox.enqueue(command("pause_buys", now=T0))
        refused, _ = inbox.enqueue(command("resume_buys", now=T0 + 1))
        broken, _ = inbox.enqueue(command("enable", now=T0 + 2))
        unknown, _ = inbox.enqueue(command("rewarm", now=T0 + 3))

        def refuse(_c):
            raise CommandRejected("not now")

        def explode(_c):
            raise RuntimeError("boom")

        applier = ControlApplier(
            inbox,
            {"pause_buys": lambda _c: "paused", "resume_buys": refuse, "enable": explode},
            clock=inbox._clock,
        )
        outcome = {result["id"]: (result["status"], result["detail"]) for result in applier.poll()}
        assert outcome == {
            good.id: ("applied", "paused"),
            refused.id: ("rejected", "not now"),
            broken.id: ("rejected", "RuntimeError: boom"),
            unknown.id: ("rejected", "rewarm cannot be applied by this trader"),
        }
        assert inbox.queued() == []

    def test_an_expired_command_is_not_applied_late(self, inbox, clock):
        stale, _ = inbox.enqueue(command(now=T0))
        clock.now = T0 + NOW_TTL_SECONDS + 1
        applied = []
        ControlApplier(inbox, {"pause_buys": applied.append}, clock=clock).poll()
        assert applied == [] and inbox.result(stale.id)["status"] == "expired"

    def test_a_newer_switch_supersedes_an_older_one(self, inbox):
        old, _ = inbox.enqueue(command("switch_algorithm", now=T0))
        revert, _ = inbox.enqueue(command("revert_algorithm", now=T0 + 1))
        seen = []
        ControlApplier(
            inbox,
            {"switch_algorithm": seen.append, "revert_algorithm": lambda c: seen.append(c) or "ok"},
            clock=inbox._clock,
        ).poll()
        assert [c.id for c in seen] == [revert.id]
        assert inbox.result(old.id)["status"] == "superseded"

    def test_a_command_that_is_not_ready_stays_queued(self, inbox):
        waiting, _ = inbox.enqueue(command(timing="when_flat"))
        ControlApplier(inbox, {"pause_buys": lambda _c: "x"}, ready=lambda _c: False).poll()
        assert [c.id for c in inbox.queued()] == [waiting.id]


# --------------------------------------------------------------------
# The running loop's side
# --------------------------------------------------------------------


@pytest.fixture
def store(tmp_path):
    s = LedgerStore(str(tmp_path / "ledger.db"))
    yield s
    s.close()


class Rig:
    """A real loop, its breaker, and the LoopControl cli.py would build."""

    def __init__(self, store, inbox):
        self.broker = FakeBroker()
        self.market = FakeMarketData()
        self.breaker = CircuitBreaker(store=store)
        self.loop = make_loop(store, self.broker, self.market, circuit_breaker=self.breaker)
        self.stopped: list[str] = []
        self.control = LoopControl(
            inbox,
            breaker=self.breaker,
            loop=lambda: self.loop,
            stop=self.stopped.append,
            heartbeat_seconds=60.0,
        )
        self.minute = 0

    def tick(self, price: float) -> int:
        """One loop tick at `price`, then the control hook -- the order
        cli.py runs them in. Returns the buys this tick submitted."""
        self.minute += 1
        self.market.push(price, ts=BASE_TS + timedelta(minutes=self.minute))
        buys = self.loop.run_once().buys_submitted
        self.control.tick()
        return buys


@pytest.fixture
def rig(store, inbox):
    return Rig(store, inbox)


class TestLoopControl:
    def test_a_pause_stops_the_very_next_buy(self, rig, inbox):
        rig.tick(100.0)
        inbox.enqueue(command("pause_buys"))
        rig.control.tick()  # between ticks
        assert rig.tick(98.0) == 0, "a 2% drop would have bought"
        assert rig.breaker.state is CircuitBreakerState.MANUAL_RESET_REQUIRED
        assert inbox.status()["state"] == "buys_paused"
        assert "paused by tester" in inbox.status()["detail"]

    def test_resume_buys_again(self, rig, inbox):
        rig.tick(100.0)
        inbox.enqueue(command("pause_buys", now=T0))
        inbox.enqueue(command("resume_buys", now=T0 + 1))
        rig.control.tick()
        assert rig.breaker.allows_new_buys
        assert rig.tick(98.0) == 1

    def test_resume_can_reset_the_drawdown_baseline(self, rig, inbox):
        rig.tick(100.0)
        rig.loop.state.peak_equity = 1e9  # a deep drawdown on paper
        inbox.enqueue(command("pause_buys", now=T0))
        inbox.enqueue(command("resume_buys", now=T0 + 1, args={"reset_drawdown_baseline": True}))
        rig.control.tick()
        assert rig.loop.state.peak_equity == 0.0
        rig.tick(100.0)
        assert rig.loop.state.peak_equity == pytest.approx(rig.loop.state.cash)

    def test_disable_now_stops_after_this_tick(self, rig, inbox):
        rig.tick(100.0)
        inbox.enqueue(command("disable"))
        rig.control.tick()
        assert rig.stopped and inbox.desired()["enabled"] is False
        assert inbox.status()["state"] == "stopping"

    def test_a_wind_down_disables_once_flat(self, rig, inbox):
        rig.tick(100.0)
        assert rig.tick(98.0) == 1  # an order in flight
        inbox.enqueue(command("disable", args={"mode": "wind_down"}))
        rig.control.tick()
        assert not rig.breaker.allows_new_buys and not rig.stopped
        assert inbox.status()["state"] == "winding_down"

        rig.loop.state.open_orders.clear()  # the order resolved, nothing open
        rig.control.tick()
        assert rig.stopped == ["wound down: no lots or orders left"]
        assert inbox.desired()["enabled"] is False

    def test_enable_cancels_a_wind_down(self, rig, inbox):
        rig.tick(100.0)
        rig.tick(98.0)
        inbox.enqueue(command("disable", now=T0, args={"mode": "wind_down"}))
        inbox.enqueue(command("enable", now=T0 + 1))
        rig.control.tick()
        assert inbox.desired() | {"at": None, "by": None, "reason": None} == {
            "enabled": True,
            "wind_down": False,
            "at": None,
            "by": None,
            "reason": None,
        }
        assert not rig.breaker.allows_new_buys, "buys stay paused until resumed"

    def test_next_session_and_when_flat_wait(self, rig, inbox):
        rig.tick(100.0)
        rig.tick(98.0)
        later, _ = inbox.enqueue(command("pause_buys", timing="next_session"))
        flat, _ = inbox.enqueue(command("pause_buys", timing="when_flat"))
        rig.control.tick()
        assert {c.id for c in inbox.queued()} == {later.id, flat.id}
        assert rig.breaker.allows_new_buys

    def test_a_broken_control_directory_never_stops_trading(self, rig, inbox, monkeypatch):
        monkeypatch.setattr(inbox, "queued", lambda: (_ for _ in ()).throw(OSError("gone")))
        rig.tick(100.0)
        assert rig.tick(98.0) == 1

    def test_the_status_names_the_account_it_is_given(self, rig, inbox, monkeypatch):
        """cli.py gives a Fidelity loop its own account's tag (account_tag)
        beside the Fidelity fields of its status; without one, the Alpaca
        key's."""
        from engine.trading.operator_control import account_fingerprint

        monkeypatch.setenv("APCA_API_KEY_ID", "PKTESTKEY")
        rig.tick(100.0)
        assert inbox.status()["account"] == account_fingerprint()
        rig.control = LoopControl(
            inbox,
            breaker=rig.breaker,
            loop=lambda: rig.loop,
            stop=rig.stopped.append,
            heartbeat_seconds=60.0,
            status_fields=lambda: {"broker": "fidelity", "fidelity": {"connected": True}},
            account=lambda: "fidelity-0123456789ab",
        )
        rig.tick(100.0)
        status = inbox.status()
        assert (status["state"], status["account"]) == ("trading", "fidelity-0123456789ab")
        assert status["fidelity"] == {"connected": True}


# --------------------------------------------------------------------
# The supervisor's side, between sessions
# --------------------------------------------------------------------


@pytest.fixture
def ledger(tmp_path):
    path = str(tmp_path / "ledger.db")
    LedgerStore(path).close()
    return path


def supervisor(inbox, ledger, **kw) -> SupervisorControl:
    return SupervisorControl(inbox, state_db=ledger, clock=inbox._clock, **kw)


def breaker_in(ledger) -> CircuitBreaker:
    store = LedgerStore(ledger)
    try:
        return CircuitBreaker(store=store)
    finally:
        store.close()


class TestSupervisorControl:
    def test_pause_and_resume_reach_the_ledger(self, inbox, ledger):
        control = supervisor(inbox, ledger)
        inbox.enqueue(command("pause_buys"))
        control.poll()
        assert breaker_in(ledger).state is CircuitBreakerState.MANUAL_RESET_REQUIRED
        inbox.enqueue(command("resume_buys", args={"reset_drawdown_baseline": True}))
        control.poll()
        assert breaker_in(ledger).allows_new_buys
        store = LedgerStore(ledger)
        assert store.get_meta("live.peak_equity") == "0.0"
        store.close()

    def test_never_beside_a_running_loop(self, inbox, ledger):
        """A lock held by a live process -- this one, standing in for a loop."""
        with open(f"{ledger}.lock", "w", encoding="utf-8") as handle:
            handle.write(str(os.getpid()))
        queued, _ = inbox.enqueue(command("pause_buys"))
        supervisor(inbox, ledger).poll()
        assert inbox.result(queued.id)["status"] == "rejected"
        assert breaker_in(ledger).allows_new_buys

    def test_disable_and_enable(self, inbox, ledger):
        control = supervisor(inbox, ledger)
        inbox.enqueue(command("disable"))
        control.poll()
        assert not control.enabled()
        inbox.enqueue(command("enable"))
        control.poll()
        assert control.enabled()

    def test_winding_down_a_flat_book_disables_at_once(self, inbox, ledger):
        control = supervisor(inbox, ledger)
        queued, _ = inbox.enqueue(command("disable", args={"mode": "wind_down"}))
        control.poll()
        assert not control.enabled()
        assert inbox.result(queued.id)["detail"] == "nothing open: disabled now"

    def test_serve_answers_commands_while_it_waits(self, inbox, ledger, clock):
        slept = []

        def sleep(seconds):
            slept.append(seconds)
            clock.now += seconds
            if len(slept) == 2:  # an operator enables it mid-wait
                inbox.enqueue(command("enable", now=clock.now))

        control = supervisor(inbox, ledger, sleep=sleep)
        inbox.set_desired(enabled=False, wind_down=False, by="op", reason="test")
        assert control.serve(600, state="waiting_for_open", until=control.enabled)
        assert slept == [15.0, 15.0]

    def test_a_disabled_deployment_says_so_while_waiting(self, inbox, ledger, clock):
        control = supervisor(inbox, ledger, sleep=lambda s: None)
        inbox.set_desired(enabled=False, wind_down=False, by="op", reason="test")
        assert not control.serve(0, state="waiting_for_open")
        assert inbox.status()["state"] == "disabled"


# --------------------------------------------------------------------
# The fresh paper ledger, and which account a trader trades
# --------------------------------------------------------------------


class TestFreshPaperLedger:
    def _handler(self, inbox, ledger, *, paper=True, book=None):
        from engine.trading.operator_control import reset_paper_ledger_handler

        return reset_paper_ledger_handler(
            inbox,
            state_db=ledger,
            paper=paper,
            broker_book=lambda: book or {"positions": 0, "open_orders": 0, "cash": 123456.78},
            clock=inbox._clock,
        )

    def test_only_while_disabled_and_flat_at_the_broker(self, inbox, ledger):
        handler = self._handler(inbox, ledger)
        with pytest.raises(CommandRejected, match="disable it first"):
            handler(command("reset_paper_ledger"))
        inbox.set_desired(enabled=False, wind_down=False, by="op", reason="test")
        busy = self._handler(inbox, ledger, book={"positions": 2, "open_orders": 1, "cash": 1.0})
        with pytest.raises(CommandRejected, match="2 position"):
            busy(command("reset_paper_ledger"))
        with pytest.raises(CommandRejected, match="real-money"):
            self._handler(inbox, ledger, paper=False)(command("reset_paper_ledger"))

    def test_the_old_ledger_is_archived_and_the_new_one_seeded(self, inbox, ledger):
        old = LedgerStore(ledger)
        old.set_meta("live.cash", "5.0")
        CircuitBreaker(store=old).halt_by_operator("op", "old halt")
        old.close()
        inbox.set_desired(enabled=False, wind_down=False, by="op", reason="test")

        detail = self._handler(inbox, ledger)(command("reset_paper_ledger"))
        assert "123,456.78" in detail
        archived = list((Path(ledger).parent / "archive").rglob("ledger.db"))
        assert len(archived) == 1, "the old ledger was moved, not deleted"
        moved = LedgerStore(str(archived[0]))
        assert moved.get_meta("live.cash") == "5.0"
        moved.close()
        fresh = LedgerStore(ledger)
        assert fresh.get_meta("live.cash") == "123456.78"
        assert fresh.get_meta("live.peak_equity") == "0.0"
        assert CircuitBreaker(store=fresh).allows_new_buys, "the old halt went with the old ledger"
        fresh.close()

    def test_a_running_loop_never_takes_it(self, rig, inbox):
        rig.tick(100.0)
        queued, _ = inbox.enqueue(command("reset_paper_ledger"))
        rig.control.tick()
        assert [c.id for c in inbox.queued()] == [queued.id]


def test_the_account_tag_is_one_way_and_reported(monkeypatch, inbox, ledger):
    from engine.trading.operator_control import account_fingerprint

    monkeypatch.setenv("APCA_API_KEY_ID", "PKTESTKEY")
    tag = account_fingerprint()
    assert len(tag) == 12 and "PKTESTKEY" not in tag
    supervisor(inbox, ledger, sleep=lambda s: None).report("closed")
    assert inbox.status()["account"] == tag
    monkeypatch.delenv("APCA_API_KEY_ID")
    assert account_fingerprint() is None


def test_a_fidelity_deployment_is_tagged_by_its_own_account(monkeypatch, inbox, ledger):
    """Its Alpaca key reads prices and the clock only: tagged by that key, it
    would share a tag with the paper trader holding the same key, and the
    Live page would refuse to enable either beside the other."""
    from engine.core.config import FidelityConfig, LiveConfig
    from engine.trading.operator_control import account_fingerprint, account_tag

    monkeypatch.setenv("APCA_API_KEY_ID", "PKTESTKEY")
    assert account_tag(LiveConfig()) == account_fingerprint()
    tag = account_tag(LiveConfig(broker="fidelity", fidelity=FidelityConfig(account="999888777")))
    assert tag.startswith("fidelity-") and len(tag) == len("fidelity-") + 12
    assert "999888777" not in tag and tag != account_fingerprint()
    supervisor(inbox, ledger, sleep=lambda s: None, account=lambda: tag).report("closed")
    assert inbox.status()["account"] == tag


# --------------------------------------------------------------------
# The journals: the bars the trader traded on, the fills it booked
# --------------------------------------------------------------------

DAY = 24 * 3600


def bar(t: float, close: float = 100.0) -> dict:
    return {"t": int(t), "o": close, "h": close, "l": close, "c": close, "v": 1.0}


class TestJournals:
    def test_bars_are_kept_per_eastern_session_oldest_first(self, inbox):
        yesterday, today = T0 - DAY, T0
        assert inbox.record_bars([bar(today, 101.0), bar(yesterday, 100.0)]) == 2
        names = sorted(p.name for p in (inbox.root / "bars").iterdir())
        assert names == ["2027-01-14.jsonl", "2027-01-15.jsonl"]
        assert [row["c"] for row in inbox.bars(2)] == [100.0, 101.0]
        assert [row["c"] for row in inbox.bars(1)] == [101.0]

    def test_a_minute_recorded_twice_keeps_its_later_record(self, inbox):
        inbox.record_bars([bar(T0, 100.0)])
        inbox.record_bars([bar(T0, 100.5)])
        assert [row["c"] for row in inbox.bars()] == [100.5]

    def test_replayed_history_leaves_a_whole_past_session_alone(self, inbox):
        inbox.record_bars([bar(T0 - DAY, 100.0)])
        inbox.record_bars([bar(T0 - DAY, 99.0), bar(T0, 101.0)], keep_past=True)
        rows = inbox.bars(2)
        assert [row["c"] for row in rows] == [100.0, 101.0], "the past session kept as it was"

    def test_only_the_newest_sessions_are_kept(self, inbox):
        for day in range(12):
            inbox.record_bars([bar(T0 - day * DAY)])
        assert len(list((inbox.root / "bars").iterdir())) == 10
        assert len(inbox.bars(30)) == 10

    def test_a_half_written_line_is_skipped(self, inbox):
        inbox.record_bars([bar(T0)])
        with open(inbox.root / "bars" / "2027-01-15.jsonl", "a", encoding="utf-8") as handle:
            handle.write('{"t": 18000')
        assert len(inbox.bars()) == 1

    def test_fills_are_kept_in_booking_order(self, inbox):
        inbox.record_fill({"t": T0 + 60, "side": "sell", "qty": 1.0, "price": 101.0, "pnl": 1.0})
        inbox.record_fill({"t": T0, "side": "buy", "qty": 1.0, "price": 100.0})
        assert [row["side"] for row in inbox.fills()] == ["buy", "sell"]

    def test_a_journal_that_cannot_be_written_never_raises(self, tmp_path, clock):
        blocked = tmp_path / "file"
        blocked.write_text("not a directory")
        assert ControlInbox(blocked, clock=clock).record_bars([bar(T0)]) == 0

    def test_the_supervisor_reports_the_code_it_runs(self, inbox, ledger):
        supervisor(inbox, ledger, sleep=lambda s: None).report("closed")
        build = inbox.status()["build"]
        assert set(build) == {"commit", "code", "python", "pid", "started_at"}
