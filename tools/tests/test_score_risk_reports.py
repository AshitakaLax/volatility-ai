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


# --------------------------------------------------------------------
# The forecast database's nightly step
# --------------------------------------------------------------------

WEEKEND = ROOT / "tests/fixtures/risk_reports/tqqq_2026-11-23.json"
SATURDAY_NIGHT = datetime(2026, 11, 22, 1, 30, tzinfo=UTC)


def minute_bars(sessions: dict[date, tuple[float, str]]):
    """A few bars a session: the open, midday, and the last regular bar
    (its time given) at `close`, then an after-hours bar that must be
    ignored."""
    import pandas as pd

    stamps, closes = [], []
    for day, (close, last) in sorted(sessions.items()):
        hour, minute = (int(part) for part in last.split(":"))
        for at, value in (
            ((9, 30), close + 1),
            ((12, 0), close + 2),
            ((hour, minute), close),
            ((17, 0), close + 9),
        ):
            stamps.append(
                datetime.combine(
                    day, datetime.min.time().replace(hour=at[0], minute=at[1]), tzinfo=EASTERN
                )
            )
            closes.append(value)
    index = pd.DatetimeIndex(stamps, name="timestamp").tz_convert("UTC")
    return pd.DataFrame({"close": closes}, index=index)


THROUGH_FRIDAY = {
    date(2026, 11, 18): (52.47, "15:59"),
    date(2026, 11, 19): (48.99, "15:59"),
    FRIDAY: (40.99, "15:59"),
}


@pytest.fixture
def store(tmp_path):
    from research.risk_overlay.forecasts import ForecastStore

    found = ForecastStore(tmp_path / "risk_reports.db")
    found.record(json.loads(FIXTURE.read_text(encoding="utf-8")), via="import")
    found.record(json.loads(WEEKEND.read_text(encoding="utf-8")), via="import")
    return found


class TestSessionCloses:
    def test_the_last_regular_bar_of_each_finished_session(self):
        closes = S.session_closes(minute_bars(THROUGH_FRIDAY))
        assert closes == {date(2026, 11, 18): 52.47, date(2026, 11, 19): 48.99, FRIDAY: 40.99}

    def test_a_session_cut_off_mid_day_is_not_finished(self):
        bars = minute_bars({**THROUGH_FRIDAY, FRIDAY: (44.0, "13:10")})
        assert FRIDAY not in S.session_closes(bars)

    def test_an_early_close_counts_once_a_later_session_has_bars(self):
        bars = minute_bars(
            {date(2026, 11, 27): (50.0, "12:59"), date(2026, 11, 30): (51.0, "15:59")}
        )
        assert S.session_closes(bars) == {date(2026, 11, 27): 50.0, date(2026, 11, 30): 51.0}

    def test_no_bars_no_closes(self):
        assert S.session_closes(None) == {}


class TestScoreForecasts:
    def test_a_finished_session_gets_its_closes_and_its_report_a_score(self, store):
        asked = []

        def load(symbol, since):
            asked.append((symbol, since))
            return minute_bars(THROUGH_FRIDAY)

        counts = S.score_forecasts(store, SATURDAY_NIGHT, load=load)
        assert counts == {"closes": 1, "scored": 1, "waiting": 0, "horizons": 0}
        assert asked[0][0] == "TQQQ" and asked[0][1].tzinfo is not None
        friday, monday = store.sessions("TQQQ")
        assert friday["actual"]["return_pct"] == pytest.approx(100 * (40.99 / 48.99 - 1), abs=1e-3)
        assert friday["score"]["in_90"] is False and friday["score"]["in_50"] is False
        assert monday["actual"] is None, "its session has not happened"
        assert S.score_forecasts(store, SATURDAY_NIGHT, load=load) == {
            "closes": 0,
            "scored": 0,
            "waiting": 0,
            "horizons": 0,
        }

    def test_a_session_the_warehouse_lacks_waits_for_the_next_night(self, store):
        partial = {day: value for day, value in THROUGH_FRIDAY.items() if day != FRIDAY}
        counts = S.score_forecasts(
            store, SATURDAY_NIGHT, load=lambda s, since: minute_bars(partial)
        )
        assert counts == {"closes": 0, "scored": 0, "waiting": 1, "horizons": 0}
        assert store.sessions("TQQQ")[0]["actual"] is None
        counts = S.score_forecasts(
            store, SATURDAY_NIGHT, load=lambda s, since: minute_bars(THROUGH_FRIDAY)
        )
        assert counts["closes"] == 1 and counts["scored"] == 1

    def test_a_week_is_scored_once_its_last_session_has_closed(self, store):
        bars = {
            **THROUGH_FRIDAY,
            date(2026, 11, 23): (44.0, "15:59"),
            date(2026, 11, 24): (45.0, "15:59"),
            date(2026, 11, 25): (46.0, "15:59"),
            date(2026, 11, 27): (47.0, "12:59"),  # the early close after Thanksgiving
        }

        def night(month, day):
            return S.score_forecasts(
                store,
                datetime(2026, month, day, 2, 0, tzinfo=UTC),
                load=lambda s, since: minute_bars(bars),
            )

        assert night(11, 26)["horizons"] == 0, "the 20th's week ends on the 27th"
        assert night(11, 28)["horizons"] == 0, "an early close counts once a later session has bars"
        bars[date(2026, 11, 30)] = (48.0, "15:59")
        assert night(12, 1)["horizons"] == 2, (
            "the 20th's week, to the 27th; the 23rd's, to the 30th"
        )
        monday, friday = store.reports("TQQQ")
        week = friday["horizons"]["next_week"]
        assert week["end_session"] == "2026-11-27"
        assert week["score"]["return_pct"] == pytest.approx(100 * (47.0 / 48.99 - 1), abs=1e-3)
        assert week["score"]["end_close"] == 47.0
        assert monday["horizons"]["next_week"]["score"]["return_pct"] == pytest.approx(
            100 * (48.0 / 40.99 - 1), abs=1e-3
        )
        assert friday["horizons"]["next_month"]["score"] is None
        assert night(12, 1)["horizons"] == 0, "scored once"

    def test_score_horizon_reads_that_horizons_bands(self):
        parsed = report()
        q = parsed.horizon("next_week").quantiles
        inside = S.score_horizon(parsed, "next_week", prior_close=100.0, close=100.0 + q["p25"])
        assert inside["in_90"] and inside["in_50"]
        outside = S.score_horizon(
            parsed, "next_week", prior_close=100.0, close=100.0 + q["p01"] - 1
        )
        assert not outside["in_90"] and outside["pit"] < 0.05

    def test_the_description_names_where_each_close_landed(self, store):
        S.score_forecasts(store, SATURDAY_NIGHT, load=lambda s, since: minute_bars(THROUGH_FRIDAY))
        friday, monday = S.describe_forecasts(store)
        assert "2026-11-20" in friday and "outside its 90%" in friday
        assert "2026-11-23" in monday and "waiting for its close" in monday


class TestArchivesAndImports:
    def test_every_archived_report_is_copied_in_once(self, tmp_path):
        from research.risk_overlay.forecasts import ForecastStore

        store = ForecastStore(tmp_path / "risk_reports.db")
        inbox = ControlInbox(tmp_path / "control")
        archive = ReportArchive.in_control_dir(inbox.root)
        received = "2026-11-20T02:50:00+00:00"
        archive.write(
            FRIDAY,
            {
                "report": json.loads(FIXTURE.read_text(encoding="utf-8")),
                "received_at": received,
                "operator": "owner",
                "sha256": "x",
                "receipts": [],
            },
        )
        deployment = SimpleNamespace(id="paper-ultimate", inbox=lambda: inbox)
        assert S.collect_archives(store, [deployment]) == 1
        assert S.collect_archives(store, [deployment]) == 0
        row = store.sessions("TQQQ")[0]
        assert row["received_at"] == received
        assert [r["via"] for r in store.receipts(row["sha256"])] == ["archive:paper-ultimate"]

    def test_a_deployment_without_a_control_directory_adds_nothing(self, tmp_path):
        from research.risk_overlay.forecasts import ForecastStore

        store = ForecastStore(tmp_path / "risk_reports.db")
        assert S.collect_archives(store, [SimpleNamespace(id="x", inbox=lambda: None)]) == 0

    def test_import_from_the_command_line(self, tmp_path, capsys):
        db = tmp_path / "risk_reports.db"
        assert S.main(["--import", str(FIXTURE), str(WEEKEND), "--db", str(db)]) == 0
        out = capsys.readouterr().out
        assert "TQQQ 2026-11-20 stored" in out and "TQQQ 2026-11-23 stored" in out
        assert S.main(["--import", str(FIXTURE), "--db", str(db)]) == 0
        assert "already stored" in capsys.readouterr().out

    def test_a_file_that_fails_the_audit_is_named_and_not_stored(self, tmp_path, capsys):
        broken = json.loads(FIXTURE.read_text(encoding="utf-8"))
        broken["horizons"]["tomorrow"]["summary"]["quantiles_pct"]["p05"] = 50.0
        path = tmp_path / "broken.json"
        path.write_text(json.dumps(broken), encoding="utf-8")
        assert S.main(["--import", str(path), "--db", str(tmp_path / "db.db")]) == 1
        assert "NOT stored" in capsys.readouterr().out


class TestTheNightlyRun:
    def test_it_reports_what_it_did(self, store):
        lines = []
        ok = T.run_forecasts(
            [],
            SATURDAY_NIGHT,
            store=store,
            load=lambda s, since: minute_bars(THROUGH_FRIDAY),
            report_to=lines.append,
        )
        assert ok
        assert lines == [
            "[tracking] forecasts: 0 archived report(s) copied in, 1 close(s), 1 score(s), "
            "0 longer horizon(s) scored, 0 session(s) waiting for bars"
        ]

    def test_a_failure_is_a_line_and_fails_the_run(self, store):
        lines = []

        def broken(symbol, since):
            raise OSError("warehouse unreadable")

        assert not T.run_forecasts(
            [], SATURDAY_NIGHT, store=store, load=broken, report_to=lines.append
        )
        assert lines[0].startswith("[tracking] forecasts: FAILED OSError")
