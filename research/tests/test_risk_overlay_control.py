"""The archive, the week's cap and the two commands, as a trader applies them
(research/risk_overlay/archive.py, control.py, live.py)."""

from __future__ import annotations

import copy
import json
from dataclasses import replace
from datetime import UTC, date, datetime, timedelta
from pathlib import Path

import pytest
import yaml

from engine.core.config import BacktestConfig, OverlayWeeklyConfig, RiskOverlayConfig
from engine.core.risk_overlay import SessionOverlay
from engine.core.risk_report import parse_report
from engine.trading.control_inbox import Command, ControlInbox
from engine.trading.operator_control import CommandRejected, ControlApplier
from research.risk_overlay.archive import (
    ReportArchive,
    schedule_from_entries,
    session_overlay,
    week_cap,
    week_start,
)
from research.risk_overlay.baselines import Baseline
from research.risk_overlay.control import first_window, risk_report_handlers
from research.risk_overlay.inputs import build_inputs
from research.risk_overlay.live import SessionRisk

ROOT = Path(__file__).resolve().parents[2]
FIXTURE = ROOT / "tests/fixtures/risk_reports/tqqq_2026-11-20.json"
FRIDAY = date(2026, 11, 20)
EVENING = datetime(2026, 11, 20, 2, 40, tzinfo=UTC)  # 21:40 ET Thursday
BASELINE = Baseline("TQQQ", 4.2, {"next_month": -30.0, "next_quarter": -45.0})


def raw(**changes) -> dict:
    data = json.loads(FIXTURE.read_text(encoding="utf-8"))
    signals = data["execution_signals"]
    for key, value in changes.items():
        signals[key] = value
    return data


def calm() -> dict:
    """The same report on a quiet evening: tier 0."""
    data = raw(
        expected_1d_move_pct=4.0,
        overnight_gap_risk="low",
        regime="low_vol_uptrend",
        skew_bias="bullish_tail",
    )
    for catalyst in data["execution_signals"]["next_day_catalysts"]:
        catalyst["impact"] = "low"
    return data


def config_for(path: str, *, mode: str = "advisory") -> BacktestConfig:
    data = yaml.safe_load((ROOT / path).read_text(encoding="utf-8"))
    data.setdefault("risk", {})["overlay"] = {"mode": mode}
    data["live"].setdefault("control", {})["risk_reports"] = True
    config = BacktestConfig.from_dict(data)
    config.validate()
    return config


PAPER = "config/paper_aggressive.yaml"
REAL_MONEY = "config/production.yaml"


class Clock:
    def __init__(self, moment: datetime) -> None:
        self.moment = moment

    def __call__(self) -> float:
        return self.moment.timestamp()


def inputs_for(report, session, received_at):
    return build_inputs("TQQQ", session, received_at=received_at, baseline=BASELINE, live=False)


@pytest.fixture
def trader(tmp_path):
    """A paper trader's two handlers over a fresh control directory."""

    def build(path: str = PAPER, clock_at: datetime = EVENING, mode: str = "advisory"):
        config = config_for(path, mode=mode)
        clock = Clock(clock_at)
        archive = ReportArchive.in_control_dir(tmp_path)
        changed: list[date] = []
        handlers = risk_report_handlers(
            config, archive=archive, inputs_for=inputs_for, clock=clock, on_change=changed.append
        )
        return config, clock, archive, handlers, changed

    return build


def command(kind: str, args: dict, operator: str = "owner") -> Command:
    return Command.new(
        kind, reason="tonight's report", operator=operator, args=args, client="10.0.0.5"
    )


class TestApplying:
    def test_before_the_open_it_becomes_the_sessions_report(self, trader):
        _config, _clock, archive, handlers, changed = trader()
        detail = handlers["apply_risk_report"](command("apply_risk_report", {"report": raw()}))
        assert "no new grid buys" in detail and "advisory" in detail
        entry = archive.current(FRIDAY)
        assert entry["outcome"] == "applied" and entry["operator"] == "owner"
        assert entry["client"] == "10.0.0.5" and entry["mapping_id"] == "v1"
        assert entry["sha256"] == parse_report(raw()).report.sha256
        assert entry["report"] == raw(), "the raw report is kept as it came"
        assert SessionOverlay.from_dict(entry["overlay"]).pause
        assert changed == [FRIDAY]

    def test_a_newer_one_replaces_it_and_the_old_is_kept(self, trader):
        _config, clock, archive, handlers, _changed = trader()
        handlers["apply_risk_report"](command("apply_risk_report", {"report": raw()}))
        clock.moment += timedelta(minutes=20)
        handlers["apply_risk_report"](command("apply_risk_report", {"report": calm()}))
        entry = archive.current(FRIDAY)
        assert entry["outcome"] == "applied"
        assert not SessionOverlay.from_dict(entry["overlay"]).pause
        assert len(entry["receipts"]) == 2
        assert len(archive.superseded()) == 1

    def test_the_same_report_twice_changes_nothing(self, trader):
        _config, _clock, archive, handlers, _ = trader()
        handlers["apply_risk_report"](command("apply_risk_report", {"report": raw()}))
        again = handlers["apply_risk_report"](command("apply_risk_report", {"report": raw()}))
        assert "already the one in force" in again
        assert len(archive.current(FRIDAY)["receipts"]) == 1

    def test_after_the_open_a_tighter_one_tightens(self, trader):
        _config, clock, archive, handlers, _ = trader()
        handlers["apply_risk_report"](command("apply_risk_report", {"report": calm()}))
        clock.moment = datetime(2026, 11, 20, 15, 0, tzinfo=UTC)  # 10:00 ET Friday
        stamped = raw()
        stamped["as_of"] = "2026-11-20T03:10:00Z"  # still for Friday, a different report
        handlers["apply_risk_report"](command("apply_risk_report", {"report": stamped}))
        entry = archive.current(FRIDAY)
        assert entry["outcome"] == "tightened"
        assert SessionOverlay.from_dict(entry["overlay"]).pause

    def test_after_the_open_a_looser_one_is_archived_not_applied(self, trader):
        _config, clock, archive, handlers, changed = trader()
        handlers["apply_risk_report"](command("apply_risk_report", {"report": raw()}))
        clock.moment = datetime(2026, 11, 20, 15, 0, tzinfo=UTC)
        later = calm()
        later["as_of"] = "2026-11-20T03:10:00Z"
        detail = handlers["apply_risk_report"](command("apply_risk_report", {"report": later}))
        assert "not applied" in detail
        entry = archive.current(FRIDAY)
        assert SessionOverlay.from_dict(entry["overlay"]).pause, "never loosened"
        assert [r["outcome"] for r in entry["receipts"]] == ["applied", "not_applied"]
        assert changed == [FRIDAY]

    def test_every_audit_problem_is_named(self, trader):
        *_, handlers, _ = trader()
        broken = copy.deepcopy(raw())
        broken["symbol"] = ""
        broken["execution_signals"]["regime"] = "bullish"
        with pytest.raises(CommandRejected, match=r"2 problem\(s\).*symbol.*regime"):
            handlers["apply_risk_report"](command("apply_risk_report", {"report": broken}))

    def test_a_session_that_has_ended(self, trader):
        *_, handlers, _ = trader(clock_at=datetime(2026, 11, 20, 21, 30, tzinfo=UTC))
        with pytest.raises(CommandRejected, match="already ended"):
            handlers["apply_risk_report"](command("apply_risk_report", {"report": raw()}))

    def test_real_money_takes_one_report_a_session(self, trader):
        _config, clock, _archive, handlers, _ = trader(REAL_MONEY)
        handlers["apply_risk_report"](command("apply_risk_report", {"report": raw()}))
        clock.moment += timedelta(minutes=10)
        with pytest.raises(CommandRejected, match="one report a session"):
            handlers["apply_risk_report"](command("apply_risk_report", {"report": calm()}))

    @pytest.mark.parametrize(
        "sessions, opens",
        [
            (["regular"], datetime(2026, 11, 20, 14, 30, tzinfo=UTC)),  # 09:30 ET
            (["pre_market", "regular"], datetime(2026, 11, 20, 9, 0, tzinfo=UTC)),  # Alpaca 04:00
        ],
    )
    def test_a_session_opens_at_its_first_traded_window(self, sessions, opens):
        data = yaml.safe_load((ROOT / PAPER).read_text(encoding="utf-8"))
        data["live"]["sessions"] = sessions
        data["live"]["extended_hours"] = False
        assert first_window(BacktestConfig.from_dict(data), FRIDAY) == opens


class TestClearing:
    def test_before_the_open(self, trader):
        _config, _clock, archive, handlers, _ = trader()
        handlers["apply_risk_report"](command("apply_risk_report", {"report": raw()}))
        detail = handlers["clear_risk_report"](
            command("clear_risk_report", {"session": "2026-11-20"})
        )
        assert "trades as configured" in detail
        assert archive.current(FRIDAY) is None
        assert archive.superseded()[0]["outcome"] == "cleared"

    def test_not_once_it_is_trading(self, trader):
        _config, clock, _archive, handlers, _ = trader()
        handlers["apply_risk_report"](command("apply_risk_report", {"report": raw()}))
        clock.moment = datetime(2026, 11, 20, 15, 0, tzinfo=UTC)
        with pytest.raises(CommandRejected, match="would loosen"):
            handlers["clear_risk_report"](command("clear_risk_report", {"session": "2026-11-20"}))


class TestThroughTheInbox:
    def test_the_applier_runs_them_and_supersedes_an_older_queued_one(self, tmp_path):
        config = config_for(PAPER)
        inbox = ControlInbox(tmp_path, clock=lambda: EVENING.timestamp())
        handlers = risk_report_handlers(
            config,
            archive=ReportArchive.in_control_dir(tmp_path),
            inputs_for=inputs_for,
            clock=lambda: EVENING.timestamp(),
        )
        first = Command.new(
            "apply_risk_report",
            reason="first",
            operator="o",
            args={"report": raw()},
            now=EVENING.timestamp(),
        )
        second = Command.new(
            "apply_risk_report",
            reason="second",
            operator="o",
            args={"report": calm()},
            now=EVENING.timestamp() + 1,
        )
        inbox.enqueue(first)
        inbox.enqueue(second)
        results = ControlApplier(inbox, handlers, clock=lambda: EVENING.timestamp() + 2).poll()
        assert [r["status"] for r in results] == ["superseded", "applied"]


class TestTheWeek:
    SETTINGS = RiskOverlayConfig()

    def test_its_first_session(self):
        assert week_start(date(2026, 11, 20)) == date(2026, 11, 16)
        # Martin Luther King Day: the week starts on Tuesday.
        assert week_start(date(2027, 1, 21)) == date(2027, 1, 19)
        five = week_start(date(2026, 11, 20), "five_sessions")
        assert five <= date(2026, 11, 20)

    def receipt(self, when: str, ceiling: float | None) -> dict:
        return {"received_at": when, "weekly_ceiling": ceiling}

    def test_set_by_the_newest_report_before_the_week(self):
        rows = [
            self.receipt("2026-11-12T02:00:00+00:00", 0.4),  # too old by Monday
            self.receipt("2026-11-14T02:00:00+00:00", 0.7),  # Friday evening
        ]
        cap, reasons = week_cap(rows, date(2026, 11, 18), self.SETTINGS)
        assert cap == 0.7 and "set by" in reasons[0]

    def test_a_lower_one_mid_week_tightens_and_a_higher_one_waits(self):
        rows = [
            self.receipt("2026-11-14T02:00:00+00:00", 0.7),
            self.receipt("2026-11-17T02:00:00+00:00", 0.9),  # Monday evening: higher, waits
            self.receipt("2026-11-18T02:00:00+00:00", 0.5),  # Tuesday evening: lower
        ]
        assert week_cap(rows, date(2026, 11, 17), self.SETTINGS)[0] == 0.7
        assert week_cap(rows, date(2026, 11, 18), self.SETTINGS)[0] == 0.5
        # Next week, the newest report before it sets the cap afresh.
        assert week_cap(rows, date(2026, 11, 23), self.SETTINGS)[0] == 0.5

    def test_no_report_no_cap(self):
        assert week_cap([], date(2026, 11, 18), self.SETTINGS) == (None, [])
        off = replace(self.SETTINGS, weekly=OverlayWeeklyConfig(enabled=False))
        assert (
            week_cap([self.receipt("2026-11-14T02:00:00+00:00", 0.5)], date(2026, 11, 18), off)[0]
            is None
        )

    def test_a_backtest_schedule_reads_the_archive_as_a_trader_would(self, trader):
        _config, _clock, archive, handlers, _ = trader()
        handlers["apply_risk_report"](command("apply_risk_report", {"report": raw()}))
        sessions = [FRIDAY, date(2026, 11, 23), date(2026, 11, 24)]
        built = schedule_from_entries(archive.entries(), sessions, self.SETTINGS)
        for session in sessions:
            expected, _ = session_overlay(archive, session, self.SETTINGS)
            assert (
                built.get(session).to_dict() == expected.to_dict() or not expected.changes_trading
            )
        assert built.get(FRIDAY).pause
        # Monday is a new week, and this Thursday report is the newest before it.
        assert built.get(date(2026, 11, 23)).exposure_ceiling == pytest.approx(0.601, abs=1e-3)
        assert not built.get(date(2026, 11, 23)).pause


class TestTheTrader:
    def test_status_says_suggested_in_advisory_mode(self, trader, tmp_path):
        config, _clock, _archive, handlers, _ = trader()
        handlers["apply_risk_report"](command("apply_risk_report", {"report": raw()}))
        morning = Clock(datetime(2026, 11, 20, 11, 30, tzinfo=UTC))
        risk = SessionRisk(config, tmp_path, clock=morning, log=lambda _m: None)
        risk._inputs_for = inputs_for
        overlay = risk.start()
        assert overlay.pause and risk.enforced() is None, "advisory: nothing reaches trading"
        status = risk.status()
        assert status["state"] == "suggested" and status["session"] == "2026-11-20"
        assert status["report"]["tier"] == 3
        assert ReportArchive.in_control_dir(tmp_path).current(FRIDAY)["start"]["overlay"]["pause"]

    def test_no_report_is_trading_as_configured(self, tmp_path):
        config = config_for(PAPER)
        risk = SessionRisk(
            config,
            tmp_path,
            clock=Clock(datetime(2026, 11, 20, 11, 30, tzinfo=UTC)),
            log=lambda _m: None,
        )
        risk.start()
        assert risk.status()["state"] == "none"
        assert risk.describe() == "no report: trading as configured"

    def test_enforce_mode_hands_the_overlay_over(self, trader, tmp_path):
        config, _clock, _archive, handlers, _ = trader(mode="enforce")
        handlers["apply_risk_report"](command("apply_risk_report", {"report": raw()}))
        risk = SessionRisk(
            config,
            tmp_path,
            clock=Clock(datetime(2026, 11, 20, 11, 30, tzinfo=UTC)),
            log=lambda _m: None,
        )
        risk._inputs_for = inputs_for
        risk.start()
        assert risk.enforced() is not None and risk.enforced().pause
        assert risk.status()["state"] == "in_force"
