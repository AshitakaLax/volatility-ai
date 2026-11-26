"""The forecast database (research/risk_overlay/forecasts.py): every risk
report checked, each session's closes and each report's score."""

from __future__ import annotations

import copy
import json
import sqlite3
from datetime import UTC, date, datetime
from pathlib import Path

import pytest

from engine.core.risk_report import report_sha256
from research.risk_overlay.forecasts import (
    ForecastRefused,
    ForecastStore,
    InputsRefused,
    as_the_page_sends,
    default_path,
    horizon_end,
)

ROOT = Path(__file__).resolve().parents[2]
FIXTURES = ROOT / "tests/fixtures/risk_reports"
FRIDAY = date(2026, 11, 20)
MONDAY = date(2026, 11, 23)
SATURDAY_NIGHT = datetime(2026, 11, 22, 1, 30, tzinfo=UTC)


def thursday() -> dict:
    return json.loads((FIXTURES / "tqqq_2026-11-20.json").read_text(encoding="utf-8"))


def weekend() -> dict:
    return json.loads((FIXTURES / "tqqq_2026-11-23.json").read_text(encoding="utf-8"))


@pytest.fixture
def store(tmp_path) -> ForecastStore:
    return ForecastStore(tmp_path / "forecasts" / "risk_reports.db")


class TestRecording:
    def test_a_report_is_stored_once_and_each_adding_is_a_receipt(self, store):
        first = store.record(thursday(), via="check", operator="owner", at=SATURDAY_NIGHT)
        again = store.record(
            thursday(), via="check", operator="owner", at=SATURDAY_NIGHT.replace(minute=40)
        )
        assert first["new"] is True and again["new"] is False
        assert first["sha256"] == report_sha256(as_the_page_sends(thursday())) == again["sha256"]
        assert first["session"] == "2026-11-20" and first["symbol"] == "TQQQ"
        assert len(store.receipts(first["sha256"])) == 2
        assert [row["session"] for row in store.sessions("TQQQ")] == ["2026-11-20"]

    def test_the_session_comes_from_as_of_a_weekend_report_is_for_monday(self, store):
        stored = store.record(weekend(), via="import", at=SATURDAY_NIGHT)
        assert stored["session"] == MONDAY.isoformat()

    def test_a_report_that_fails_the_audit_is_not_stored(self, store):
        broken = thursday()
        broken["horizons"]["tomorrow"]["summary"]["quantiles_pct"]["p05"] = 50.0
        with pytest.raises(ForecastRefused) as refused:
            store.record(broken, via="check")
        assert not refused.value.audit.ok
        assert store.sessions("TQQQ") == []

    def test_the_first_arrival_is_kept_when_an_archive_says_it_came_earlier(self, store):
        store.record(thursday(), via="check", at=SATURDAY_NIGHT)
        trader = datetime(2026, 11, 20, 3, 0, tzinfo=UTC)
        store.record(thursday(), via="archive:paper-ultimate", operator="owner", at=trader)
        row = store.sessions("TQQQ")[0]
        assert row["received_at"] == trader.isoformat()
        assert [r["via"] for r in store.receipts(row["sha256"])] == [
            "archive:paper-ultimate",
            "check",
        ]

    def test_a_files_copy_and_the_pages_copy_are_one_report(self, store):
        """The browser writes -22.0 as -22. Monday's report applied from the
        page was archived by its trader as e65c4060431e; the same report read
        from its file must land on that id, not beside it."""
        from_file = store.record(weekend(), via="import")
        from_page = store.record(json.loads(json.dumps(as_the_page_sends(weekend()))), via="check")
        assert from_file["sha256"] == from_page["sha256"]
        assert from_file["sha256"].startswith("e65c4060431e")
        assert from_page["new"] is False
        assert store.record(json.dumps(weekend()), via="import")["new"] is False

    def test_whole_number_floats_become_integers_and_nothing_else_changes(self):
        assert as_the_page_sends({"a": [-22.0, 0.5, 3], "b": {"c": 1.0}, "d": True, "e": "x"}) == {
            "a": [-22, 0.5, 3],
            "b": {"c": 1},
            "d": True,
            "e": "x",
        }
        assert isinstance(as_the_page_sends(-22.0), int)

    def test_the_raw_report_is_kept_whole(self, store):
        stored = store.record(thursday(), via="check")
        with sqlite3.connect(store.path) as con:
            raw = con.execute(
                "SELECT raw FROM reports WHERE sha256 = ?", [stored["sha256"]]
            ).fetchone()[0]
        assert json.loads(raw) == thursday()


class TestSessions:
    def test_each_session_shows_its_newest_report_oldest_session_first(self, store):
        store.record(weekend(), via="import")
        store.record(thursday(), via="import")
        later = copy.deepcopy(thursday())
        later["as_of"] = "2026-11-20T03:30:00Z"
        later["execution_signals"]["expected_1d_move_pct"] = 7.0
        store.record(later, via="check")
        rows = store.sessions("TQQQ")
        assert [row["session"] for row in rows] == ["2026-11-20", "2026-11-23"]
        assert rows[0]["sha256"] == report_sha256(as_the_page_sends(later))
        assert rows[0]["reports"] == 2
        assert rows[0]["expected_move_pct"] == 7.0
        assert rows[0]["quantiles"]["p05"] == -13.42 and rows[0]["median_pct"] == -0.19
        assert store.sessions("TQQQ", limit=1)[0]["session"] == "2026-11-23"
        assert store.sessions("RSP") == []

    def test_symbols_newest_first(self, store):
        store.record(thursday(), via="import", at=SATURDAY_NIGHT)
        rsp = thursday()
        rsp["symbol"] = "RSP"
        store.record(rsp, via="import", at=SATURDAY_NIGHT.replace(hour=2))
        assert store.symbols() == ["RSP", "TQQQ"]

    def test_an_absent_database_is_empty_and_not_created_by_a_read(self, tmp_path):
        store = ForecastStore(tmp_path / "none" / "risk_reports.db")
        assert store.sessions("TQQQ") == [] and store.symbols() == []
        assert store.unclosed(SATURDAY_NIGHT) == [] and store.unscored() == []
        assert not store.path.exists()


class TestClosesAndScores:
    def test_a_session_waits_for_its_close(self, store):
        store.record(thursday(), via="import")
        store.record(weekend(), via="import")
        before_close = datetime(2026, 11, 20, 20, 0, tzinfo=UTC)
        assert store.unclosed(before_close) == []
        assert store.unclosed(SATURDAY_NIGHT) == [("TQQQ", FRIDAY)]

    def test_a_close_and_a_score_reach_the_session(self, store):
        store.record(thursday(), via="import")
        store.record_close(
            "TQQQ",
            FRIDAY,
            close=40.99,
            prior_session=date(2026, 11, 19),
            prior_close=48.99,
            source="warehouse",
            at=SATURDAY_NIGHT,
        )
        assert store.unclosed(SATURDAY_NIGHT) == []
        [(report, close)] = store.unscored()
        assert report.session == FRIDAY and close == {"close": 40.99, "prior_close": 48.99}
        store.record_score(
            report.sha256,
            {
                "return_pct": -16.33,
                "in_90": False,
                "in_50": False,
                "pit": 0.0,
                "pinball": 2.1,
                "move_ratio": 1.95,
            },
        )
        assert store.unscored() == []
        row = store.sessions("TQQQ")[0]
        assert row["actual"]["return_pct"] == pytest.approx(-16.33, abs=0.01)
        assert row["actual"]["prior_session"] == "2026-11-19"
        assert row["score"] == {
            "in_90": False,
            "in_50": False,
            "pit": 0.0,
            "pinball": 2.1,
            "move_ratio": 1.95,
        }

    def test_a_close_is_written_once(self, store):
        store.record(thursday(), via="import")
        for close in (40.99, 45.0):
            store.record_close(
                "TQQQ",
                FRIDAY,
                close=close,
                prior_session=date(2026, 11, 19),
                prior_close=48.99,
                source="warehouse",
            )
        assert store.sessions("TQQQ")[0]["actual"]["close"] == 40.99


class TestWhereItLives:
    def test_the_environment_names_it(self, monkeypatch, tmp_path):
        monkeypatch.setenv("VAI_FORECAST_DB", str(tmp_path / "x.db"))
        assert default_path() == tmp_path / "x.db"

    def test_else_the_warehouse_holds_it(self, monkeypatch, tmp_path):
        monkeypatch.delenv("VAI_FORECAST_DB", raising=False)
        monkeypatch.setenv("VAI_WAREHOUSE_DIR", str(tmp_path / "wh"))
        assert default_path() == tmp_path / "wh" / "forecasts" / "risk_reports.db"

    def test_tests_never_reach_the_real_one(self):
        """Root conftest.py points it at a temporary directory."""
        assert "vai-tests-" in str(default_path())


def inputs_for(report: dict, session: str, **extra) -> dict:
    return {
        "snapshot": {"symbol": report["symbol"], "target_session": session, "vix_level": 24.1},
        "diagnostics": {"engine": "chronos", "simulation_paths": 2000},
        "sources": [{"name": "Yahoo Finance chart API"}],
        **extra,
    }


class TestEveryReport:
    """reports() and report(): what the Forecast tab's review reads."""

    def test_every_report_newest_first_with_who_added_it(self, store):
        evening = store.record(thursday(), via="import", at=SATURDAY_NIGHT)
        morning_report = copy.deepcopy(thursday())
        morning_report["as_of"] = "2026-11-20T12:44:00Z"
        morning = store.record(morning_report, via="check", operator="forecast service")
        monday = store.record(weekend(), via="archive:paper")
        rows = store.reports("TQQQ")
        assert [row["sha256"] for row in rows] == [
            monday["sha256"],
            morning["sha256"],
            evening["sha256"],
        ]
        assert [row["newest"] for row in rows] == [True, True, False]
        assert rows[1]["receipts"][0]["operator"] == "forecast service"
        assert rows[2]["receipts"][0]["via"] == "import" and rows[2]["receipt_count"] == 1
        assert rows[1]["reports"] == 2, "two reports for the 20th"
        assert rows[0]["model"] and rows[0]["has_inputs"] is False
        assert store.reports("TQQQ", limit=1)[0]["sha256"] == monday["sha256"]

    def test_each_longer_horizon_names_its_last_session_before_it_is_scored(self, store):
        store.record(thursday(), via="import")
        (row,) = store.reports("TQQQ")
        assert row["horizons"]["next_week"] == {"end_session": "2026-11-27", "score": None}
        assert set(row["horizons"]) == {"next_week", "next_month", "next_quarter", "next_year"}

    def test_one_report_whole_with_its_receipts_and_inputs(self, store):
        kept = store.record(
            thursday(), via="check", operator="owner", inputs=inputs_for(thursday(), "2026-11-20")
        )
        store.record(thursday(), via="check")
        found = store.report(kept["sha256"])
        assert found["report"]["symbol"] == "TQQQ" and "horizons" in found["report"]
        assert [r["operator"] for r in found["receipts"]] == ["owner", None]
        assert found["inputs"]["snapshot"]["vix_level"] == 24.1
        assert found["has_inputs"] is True
        assert store.report("0" * 64) is None

    def test_inputs_are_kept_once_the_first_ones_stand(self, store):
        first = inputs_for(thursday(), "2026-11-20")
        kept = store.record(thursday(), via="check", inputs=first)
        later = inputs_for(thursday(), "2026-11-20")
        later["snapshot"]["vix_level"] = 99.0
        store.record(thursday(), via="check", inputs=later)
        assert store.report(kept["sha256"])["inputs"]["snapshot"]["vix_level"] == 24.1

    def test_another_reports_inputs_are_refused_and_nothing_is_stored(self, store):
        with pytest.raises(InputsRefused, match="2026-11-23"):
            store.record(thursday(), via="check", inputs=inputs_for(thursday(), "2026-11-23"))
        with pytest.raises(InputsRefused, match="only snapshot"):
            store.record(
                thursday(), via="check", inputs=inputs_for(thursday(), "2026-11-20", extra=1)
            )
        with pytest.raises(InputsRefused, match="no snapshot"):
            store.record(thursday(), via="check", inputs={"diagnostics": {}})
        assert store.reports("TQQQ") == []

    def test_a_week_ends_four_sessions_after_its_own_thanksgiving_skipped(self):
        assert horizon_end(FRIDAY, "tomorrow") == FRIDAY
        assert horizon_end(FRIDAY, "next_week") == date(2026, 11, 27)
        assert horizon_end(MONDAY, "next_week") == date(2026, 11, 30)

    def test_a_longer_horizon_is_due_once_its_last_session_closed_and_scored_once(self, store):
        kept = store.record(thursday(), via="import")
        assert store.unscored_horizons(datetime(2026, 12, 1, tzinfo=UTC)) == [], "no close yet"
        store.record_close(
            "TQQQ",
            FRIDAY,
            close=40.99,
            prior_session=date(2026, 11, 19),
            prior_close=48.99,
            source="warehouse",
        )
        assert store.unscored_horizons(datetime(2026, 11, 27, 20, 0, tzinfo=UTC)) == []
        (due,) = store.unscored_horizons(datetime(2026, 11, 27, 21, 1, tzinfo=UTC))
        report, prior_close, horizon, end = due
        assert (report.sha256, prior_close, horizon, end) == (
            kept["sha256"],
            48.99,
            "next_week",
            date(2026, 11, 27),
        )
        score = {"return_pct": 1.5, "in_90": True, "in_50": False, "pit": 0.6, "pinball": 2.0}
        store.record_horizon_score(
            kept["sha256"], "next_week", score, end_session=end, end_close=49.72
        )
        assert store.unscored_horizons(datetime(2026, 11, 28, tzinfo=UTC)) == []
        week = store.reports("TQQQ")[0]["horizons"]["next_week"]
        assert week["score"]["in_90"] is True and week["score"]["end_close"] == 49.72
        with pytest.raises(ValueError, match="not a longer horizon"):
            store.record_horizon_score(
                kept["sha256"], "tomorrow", score, end_session=FRIDAY, end_close=1.0
            )

    def test_a_database_made_before_the_new_tables_gets_them(self, store):
        store.record(thursday(), via="import")
        with sqlite3.connect(store.path) as con:
            con.execute("DROP TABLE inputs")
            con.execute("DROP TABLE horizon_scores")
            con.execute("PRAGMA user_version = 1")
        assert store.reports("TQQQ")[0]["has_inputs"] is False
        store.record(weekend(), via="check", inputs=inputs_for(weekend(), "2026-11-23"))
        assert store.reports("TQQQ")[0]["has_inputs"] is True

    def test_an_absent_database_is_not_created_by_reading_it(self, tmp_path):
        absent = ForecastStore(tmp_path / "none" / "risk_reports.db")
        assert absent.reports("TQQQ") == [] and absent.report("0" * 64) is None
        assert absent.unscored_horizons(SATURDAY_NIGHT) == []
        assert not absent.path.exists()
