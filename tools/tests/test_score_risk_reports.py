"""The nightly scorecard and the followed log (tools/score_risk_reports.py),
and the tracking service's `risk` part of a session (tools/track_live.py)."""

from __future__ import annotations

import json
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from types import SimpleNamespace
from typing import ClassVar

import pytest
import yaml

from engine.core.config import BacktestConfig
from engine.core.risk_report import parse_report
from engine.core.trading_calendar import EASTERN
from engine.trading.control_inbox import Command, ControlInbox
from research.risk_overlay.archive import ReportArchive
from tools import score_risk_reports as S
from tools import track_live as T

ROOT = Path(__file__).resolve().parents[2]
FIXTURE = ROOT / "tests/fixtures/risk_reports/tqqq_2026-11-20.json"
FRIDAY = date(2026, 11, 20)
OPENS = datetime(2026, 11, 20, 14, 30, tzinfo=UTC)


def report():
    return parse_report(json.loads(FIXTURE.read_text(encoding="utf-8"))).require()


class TestTheScore:
    def test_a_quiet_session_inside_the_bands(self):
        score = S.score_session(report(), prior_close=48.26, close=48.50, implied_move_pct=4.0)
        assert score["return_pct"] == pytest.approx(0.4973, abs=1e-3)
        assert score["in_90"] and score["in_50"]
        assert 0.25 < score["pit"] < 0.75
        assert score["move_ratio"] == pytest.approx(0.4973 / 8.38, abs=1e-3)
        assert score["skill"] is not None

    def test_a_crash_outside_them(self):
        score = S.score_session(report(), prior_close=48.26, close=38.0)
        assert not score["in_90"] and score["pit"] < 0.05
        assert "skill" not in score, "no implied move, no naive baseline"

    def test_the_week_once_its_close_exists(self):
        score = S.score_session(report(), prior_close=48.26, close=48.5, week_close=50.0)
        assert score["week"]["in_90"] is True

    def test_no_closes_no_score(self):
        assert S.score_session(report(), prior_close=None, close=48.5) is None

    def test_pinball_is_zero_at_a_perfect_point_and_grows(self):
        quantiles = dict.fromkeys(S.LEVELS, 0.0)
        assert S.pinball(quantiles, 0.0) == 0.0
        assert S.pinball(quantiles, 5.0) > S.pinball(quantiles, 1.0) > 0

    def test_the_summary(self):
        scores = [
            S.score_session(report(), prior_close=48.26, close=c, implied_move_pct=4.0)
            for c in (48.5, 47.0, 49.9, 45.0, 48.3, 52.0, 46.5, 48.0, 50.5, 47.5, 48.1, 44.0)
        ]
        summary = S.summarize(scores)
        assert summary["sessions"] == 12
        assert 0 <= summary["coverage_90"] <= 1 and summary["skill_interval"] is not None
        assert summary["accuracy_move"] is None or -1 <= summary["accuracy_move"] <= 1
        assert S.summarize([]) == {"sessions": 0}

    def test_spearman(self):
        assert S.spearman([1, 2, 3, 4], [10, 20, 30, 40]) == pytest.approx(1.0)
        assert S.spearman([1, 2, 3, 4], [40, 30, 20, 10]) == pytest.approx(-1.0)


def pause_row(minutes_after_open: float, kind: str = "pause_buys") -> dict:
    when = OPENS + timedelta(minutes=minutes_after_open)
    return {
        "type": kind,
        "status": "applied",
        "finished_at": when.isoformat(),
        "seq": int(when.timestamp() * 1e9),
    }


class TestFollowed:
    PAUSE: ClassVar[dict] = {"pause": True, "tier": 3}

    @pytest.mark.parametrize(
        "rows, status",
        [
            ([pause_row(-600)], "followed"),
            ([pause_row(10)], "followed"),
            ([pause_row(90)], "late"),
            ([], "not_followed"),
            ([pause_row(-600), pause_row(-300, "resume_buys")], "not_followed"),
        ],
    )
    def test_a_suggested_pause(self, rows, status):
        assert S.followed(self.PAUSE, rows, session=FRIDAY, opens=OPENS)["status"] == status

    def test_no_button_and_enforced(self):
        assert (
            S.followed({"pause": False, "tier": 1}, [], session=FRIDAY, opens=OPENS)["status"]
            == "not_actionable"
        )
        assert (
            S.followed(self.PAUSE, [], session=FRIDAY, opens=OPENS, mode="enforce")["status"]
            == "enforced"
        )
        assert S.followed(None, [], session=FRIDAY, opens=OPENS) is None


class TestTracking:
    def test_a_session_with_a_report_gets_its_risk_part(self, tmp_path):
        raw = yaml.safe_load((ROOT / "config/paper_aggressive.yaml").read_text(encoding="utf-8"))
        raw.setdefault("risk", {})["overlay"] = {"mode": "advisory"}
        raw["live"]["sessions"] = ["regular"]
        raw["live"]["extended_hours"] = False
        config = BacktestConfig.from_dict(raw)
        paused_at = (OPENS - timedelta(hours=10)).timestamp()  # the evening before
        inbox = ControlInbox(tmp_path / "control", clock=lambda: paused_at)
        for day, close in ((date(2026, 11, 19), 48.26), (FRIDAY, 47.0)):
            stamp = datetime.combine(
                day, datetime.min.time().replace(hour=15, minute=59), tzinfo=EASTERN
            )
            inbox.record_bars(
                [{"t": stamp.timestamp(), "o": close, "h": close, "l": close, "c": close, "v": 1}]
            )
        entry = {
            "report": json.loads(FIXTURE.read_text(encoding="utf-8")),
            "sha256": "abc",
            "mode": "advisory",
            "outcome": "applied",
            "overlay": {"pause": True, "tier": 3},
            "mapped": {"tier": 3, "abstained": False},
            "summary": "Fri Nov 20: no new grid buys",
            "inputs": {"implied_move_pct": 4.0},
            "receipts": [],
        }
        ReportArchive.in_control_dir(inbox.root).write(FRIDAY, entry)
        pause = Command.new("pause_buys", reason="tier 3 tonight", operator="owner", now=paused_at)
        inbox.enqueue(pause)
        inbox.claim(pause)
        inbox.record(pause, "applied", "paused")
        deployment = SimpleNamespace(inbox=lambda: inbox)
        rows = [{"session": "2026-11-19"}, {"session": "2026-11-20"}]
        T.add_risk(deployment, config, rows)
        assert "risk" not in rows[0], "no report: it traded as configured"
        risk = rows[1]["risk"]
        assert risk["tier"] == 3 and risk["followed"] == {"status": "followed", "minutes": 0}
        assert risk["score"]["return_pct"] == pytest.approx(100 * (47.0 / 48.26 - 1), abs=1e-3)


def test_the_shadows_run_with_every_report_enforced_and_with_none(tmp_path, monkeypatch):
    raw = yaml.safe_load((ROOT / "config/paper_aggressive.yaml").read_text(encoding="utf-8"))
    raw.setdefault("risk", {})["overlay"] = {"mode": "advisory"}
    config = BacktestConfig.from_dict(raw)
    inbox = ControlInbox(tmp_path / "control")
    ReportArchive.in_control_dir(inbox.root).write(FRIDAY, {"sha256": "abc", "receipts": []})
    seen = []

    def fake(cfg, since, load=None):
        seen.append(cfg.risk.overlay)
        return {"2026-11-20": {"realized_pnl": 1.0 if cfg.risk.overlay else 2.0, "return_pct": 0.1}}

    monkeypatch.setattr(T, "shadow_sessions", fake)
    rows = {
        "2026-11-20": {"session": "2026-11-20", "risk": {"tier": 3}},
        "2026-11-19": {"session": "2026-11-19"},
    }
    algorithm = {
        "strategy_id": config.strategy.strategy_id,
        "strategy_params": {},
        "step": 0.00075,
        "profit_target": 0.003,
    }
    T.add_risk_shadows(SimpleNamespace(inbox=lambda: inbox), config, algorithm, rows)
    suggested, none = seen
    assert suggested.mode == "enforce" and suggested.path.endswith("risk_reports")
    assert none is None
    shadows = rows["2026-11-20"]["risk"]["shadows"]
    assert shadows["as_suggested"]["realized_pnl"] == 1.0
    assert shadows["no_report"]["realized_pnl"] == 2.0
    assert shadows["as_traded"] == shadows["no_report"], "advisory traded the YAML"
    assert "risk" not in rows["2026-11-19"]
