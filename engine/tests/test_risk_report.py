"""The nightly risk report's parser and audit (engine/core/risk_report.py).

Tonight's report (tests/fixtures/risk_reports/tqqq_2026-11-20.json) is the
reference: docs/daily_risk_report_plan.md audited it by hand, and the parser
must agree -- whole arithmetic, nearly empty bins, three inputs missing.
"""

from __future__ import annotations

import copy
import json
from datetime import UTC, date, datetime
from pathlib import Path

import pytest

from engine.core.risk_report import (
    MAX_REPORT_BYTES,
    canonical_json,
    day_bounds,
    parse_report,
    report_sha256,
    target_session,
)

FIXTURE = Path(__file__).resolve().parents[2] / "tests/fixtures/risk_reports/tqqq_2026-11-20.json"


@pytest.fixture
def raw() -> dict:
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def errors_of(data) -> list[str]:
    return [f"{f.where}: {f.message}" for f in parse_report(data).errors]


class TestTonightsReport:
    def test_it_parses_for_friday_nov_20(self, raw):
        audit = parse_report(raw)
        assert audit.ok, audit.errors
        report = audit.report
        assert report.symbol == "TQQQ"
        assert report.session == date(2026, 11, 20)
        assert report.expected_move_pct == 8.38
        assert (report.regime, report.gap_risk, report.skew_bias) == (
            "high_vol_downtrend",
            "high",
            "bearish_tail",
        )
        assert report.cash_defensive == 0.45
        assert report.horizon("next_month").es5_pct == -53.93

    def test_its_bins_hold_little_and_it_lacked_three_inputs(self, raw):
        audit = parse_report(raw)
        bins = [f for f in audit.warnings if f.where.endswith(".bins")]
        assert len(bins) == 5, "every horizon's bins are the SPY template"
        tomorrow = audit.report.horizon("tomorrow")
        assert round(1 - tomorrow.bin_coverage, 2) == 0.72
        assert any("lacked 3 input" in f.message for f in audit.warnings)

    def test_its_catalysts_are_timed_on_the_session(self, raw):
        report = parse_report(raw).report
        times = {c.event: c.at for c in report.catalysts}
        michigan = next(at for event, at in times.items() if "Michigan" in event)
        assert michigan == datetime(2026, 11, 20, 15, 0, tzinfo=UTC)

    def test_it_fits_in_a_command(self, raw):
        assert len(canonical_json(raw).encode()) < MAX_REPORT_BYTES
        assert 5_700 < len(canonical_json(raw).encode()) < 6_000  # the plan's 5.8 KB

    def test_its_hash_ignores_key_order(self, raw):
        reordered = json.loads(json.dumps(raw, sort_keys=False))
        reordered = dict(reversed(list(reordered.items())))
        assert report_sha256(reordered) == report_sha256(raw)
        assert parse_report(json.dumps(raw)).report.sha256 == report_sha256(raw)


class TestWhatItRefuses:
    def test_every_problem_is_listed_not_the_first(self, raw):
        broken = copy.deepcopy(raw)
        broken["symbol"] = ""
        broken["execution_signals"]["regime"] = "bullish"
        broken["horizons"]["tomorrow"]["bins"][0]["prob"] = 0.5
        broken["horizons"]["next_week"]["summary"]["quantiles_pct"]["p25"] = 50.0
        found = errors_of(broken)
        assert any(e.startswith("symbol") for e in found)
        assert any("regime" in e and "must be one of" in e for e in found)
        assert any("tomorrow" in e and "sum to" in e for e in found)
        assert any("next_week" in e and "not in order" in e for e in found)
        assert parse_report(broken).report is None

    def test_a_cdf_that_does_not_chain(self, raw):
        raw["horizons"]["next_month"]["bins"][3]["cdf"] += 0.05
        assert any("next_month.bins[3].cdf" in e for e in errors_of(raw))

    def test_an_expected_shortfall_above_its_quantile(self, raw):
        raw["horizons"]["tomorrow"]["summary"]["expected_shortfall_5pct"] = -1.0
        assert any("expected_shortfall_5pct" in e for e in errors_of(raw))

    def test_prob_positive_must_match_the_bins(self, raw):
        raw["horizons"]["tomorrow"]["summary"]["prob_positive"] = 0.7
        assert any("prob_positive" in e for e in errors_of(raw))

    def test_weights_must_sum_to_one(self, raw):
        raw["execution_signals"]["suggested_strategy_weights"]["cash_defensive"] = 0.9
        assert any("suggested_strategy_weights" in e for e in errors_of(raw))

    @pytest.mark.parametrize(
        "field, value",
        [
            ("overnight_gap_risk", "extreme"),
            ("skew_bias", "left"),
            ("volatility_state", "calm"),
        ],
    )
    def test_each_enum(self, raw, field, value):
        raw["execution_signals"][field] = value
        assert any(field in e for e in errors_of(raw))

    def test_a_catalyst_impact_and_time(self, raw):
        raw["execution_signals"]["next_day_catalysts"][0]["impact"] = "huge"
        raw["execution_signals"]["next_day_catalysts"][1]["time_utc"] = "3pm"
        found = errors_of(raw)
        assert any("next_day_catalysts[0].impact" in e for e in found)
        assert any("next_day_catalysts[1].time_utc" in e for e in found)

    def test_an_as_of_without_a_zone(self, raw):
        raw["as_of"] = "2026-11-20T02:38:15"
        assert any(e.startswith("as_of") for e in errors_of(raw))

    def test_an_as_of_inside_the_session(self, raw):
        raw["as_of"] = "2026-11-19T17:00:00Z"  # 12:00 ET
        assert any("not an end-of-day report" in e for e in errors_of(raw))

    def test_a_declared_session_that_disagrees(self, raw):
        raw["target_session"] = "2026-11-23"
        assert any(e.startswith("target_session") for e in errors_of(raw))

    def test_a_missing_horizon(self, raw):
        del raw["horizons"]["next_quarter"]
        assert any("horizons.next_quarter" in e for e in errors_of(raw))

    def test_not_json(self):
        assert parse_report("{nope").errors[0].message.startswith("is not JSON")

    def test_too_large(self, raw):
        raw["padding"] = "x" * MAX_REPORT_BYTES
        assert any("bytes" in e for e in errors_of(raw))


class TestSchema120:
    def test_iso_catalyst_times_and_the_new_fields(self, raw):
        raw["schema_version"] = "1.2.0"
        raw["target_session"] = "2026-11-20"
        raw["prompt_version"] = "2026-11-20.1"
        raw["model"] = "gemini"
        raw["execution_signals"]["next_day_catalysts"][1]["time_utc"] = "2026-11-20T15:00:00Z"
        report = parse_report(raw).require()
        assert report.declared_session == date(2026, 11, 20)
        assert report.prompt_version == "2026-11-20.1"
        assert report.catalysts[1].at == datetime(2026, 11, 20, 15, tzinfo=UTC)


class TestTheSessionAReportIsFor:
    @pytest.mark.parametrize(
        "as_of, session",
        [
            # Thursday evening, Eastern: Friday.
            ("2026-11-20T02:38:15Z", date(2026, 11, 20)),
            # Friday evening: Monday.
            ("2026-11-20T22:00:00Z", date(2026, 11, 23)),
            # Sunday: Monday.
            ("2026-11-22T20:00:00Z", date(2026, 11, 23)),
            # The evening before Thanksgiving (closed Thursday the 26th): Friday.
            ("2026-11-25T23:00:00Z", date(2026, 11, 27)),
            # Before the open: that session.
            ("2026-11-23T12:00:00Z", date(2026, 11, 23)),
            # Across the November DST change (Sunday Nov 1): 21:30 ET Friday Oct 30.
            ("2026-10-31T01:30:00Z", date(2026, 11, 2)),
            # March: 21:30 EDT on Monday Mar 9 is 01:30 UTC Tuesday.
            ("2026-03-10T01:30:00Z", date(2026, 3, 10)),
        ],
    )
    def test_weekends_holidays_and_dst(self, as_of, session):
        moment = datetime.fromisoformat(as_of.replace("Z", "+00:00"))
        assert target_session(moment) == session

    def test_inside_regular_hours_is_refused(self):
        with pytest.raises(ValueError, match="not an end-of-day report"):
            target_session(datetime(2026, 11, 20, 15, 0, tzinfo=UTC))

    def test_the_day_a_report_covers_starts_at_the_previous_close(self):
        start, end = day_bounds(date(2026, 11, 23))
        assert start == datetime(2026, 11, 20, 21, 0, tzinfo=UTC)  # Friday 16:00 EST
        assert end == datetime(2026, 11, 23, 21, 0, tzinfo=UTC)
