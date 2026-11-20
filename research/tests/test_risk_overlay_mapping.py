"""Mapping v1 (research/risk_overlay/mapping.py): tonight's report pinned,
monotone in every risk input, bounded, and abstaining as specified."""

from __future__ import annotations

import copy
import json
import random
from dataclasses import replace
from datetime import UTC, date, datetime
from pathlib import Path

import pytest

from engine.core.config import OverlaySpacingConfig, OverlayWeeklyConfig, RiskOverlayConfig
from engine.core.risk_report import Catalyst, parse_report
from research.risk_overlay.baselines import Baseline, read_baselines, write_baselines
from research.risk_overlay.inputs import calendar_catalysts, proxy_move, realised_sigma_pct
from research.risk_overlay.mapping import (
    GAP_SCORES,
    REGIME_SCORES,
    TAIL_SCORES,
    THRESHOLDS_PROVISIONAL,
    TIER_THRESHOLDS,
    MappingInputs,
    map_report,
    tier_of,
)

FIXTURE = Path(__file__).resolve().parents[2] / "tests/fixtures/risk_reports/tqqq_2026-11-20.json"
FRIDAY = date(2026, 11, 20)
RECEIVED = datetime(2026, 11, 20, 2, 40, tzinfo=UTC)
SETTINGS = RiskOverlayConfig()


def raw() -> dict:
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def report(data=None):
    return parse_report(data or raw()).require()


def inputs(baseline_move: float = 4.2, **fields) -> MappingInputs:
    base = Baseline("TQQQ", baseline_move, {"next_month": -30.0, "next_quarter": -45.0})
    values = {
        "symbol": "TQQQ",
        "session": FRIDAY,
        "received_at": RECEIVED,
        "last_close": 48.26,
        "baseline": base,
    }
    values.update(fields)
    return MappingInputs(**values)


class TestTonight:
    @pytest.mark.parametrize("baseline", [3.5, 4.0, 4.5, 5.0])
    def test_tier_3_and_a_step_of_1_7_to_2_4(self, baseline):
        mapped = map_report(report(), inputs(baseline), SETTINGS)
        assert not mapped.abstained
        assert mapped.tier == 3
        assert 0.80 <= mapped.score <= 0.98
        assert 1.67 <= mapped.step_multiplier <= 2.40
        overlay = mapped.overlay
        assert overlay.pause and overlay.session == FRIDAY
        assert overlay.supersedes == frozenset({"governor", "event_boosts"})
        assert overlay.mode == "advisory"

    def test_the_weekly_cap_at_the_plans_illustrative_baseline(self):
        # ES5 -53.9% against a -30% baseline: a ratio of 1.8, a ceiling of 60%.
        mapped = map_report(report(), inputs(), SETTINGS)
        assert mapped.weekly_ratio == pytest.approx(1.7977, abs=1e-3)
        assert mapped.weekly_ceiling == pytest.approx(0.601, abs=1e-3)

    def test_every_component_but_the_move_is_at_its_worst(self):
        components = map_report(report(), inputs(), SETTINGS).components
        assert {k: v for k, v in components.items() if k != "volatility"} == {
            "gap": 1.0,
            "regime": 1.0,
            "catalyst": 1.0,
            "tail": 1.0,
        }


class TestAbstaining:
    @pytest.mark.parametrize(
        "change, why",
        [
            (lambda d: d.update(symbol="SOXL"), "trades TQQQ"),
            (
                lambda d: d["execution_signals"]["data_quality"].update(confidence_score=0.5),
                "confidence",
            ),
            (
                lambda d: d["execution_signals"]["data_quality"].update(source_coverage="degraded"),
                "degraded",
            ),
            (lambda d: d.update(base_price=60.0), "from our last close"),
        ],
    )
    def test_to_neutral(self, change, why):
        data = raw()
        change(data)
        mapped = map_report(report(data), inputs(), SETTINGS)
        assert mapped.abstained and not mapped.overlay.changes_trading
        assert mapped.overlay.supersedes == frozenset(), "an abstaining session keeps the governor"
        assert any(why in reason for reason in mapped.reasons)

    def test_another_session(self):
        mapped = map_report(report(), inputs(session=date(2026, 11, 23)), SETTINGS)
        assert mapped.abstained and "not 2026-11-23" in mapped.reasons[0]

    def test_after_its_session_ended(self):
        late = datetime(2026, 11, 20, 21, 30, tzinfo=UTC)
        assert map_report(report(), inputs(received_at=late), SETTINGS).abstained

    def test_without_a_baseline(self):
        mapped = map_report(report(), inputs(baseline=None), SETTINGS)
        assert mapped.abstained and "baseline" in mapped.reasons[0]


class TestTheImpliedMoveCrossCheck:
    def test_a_move_far_from_vxn_is_replaced_by_the_proxys(self):
        mapped = map_report(report(), inputs(implied_move_pct=3.0, proxy_move_pct=3.6), SETTINGS)
        assert mapped.move_pct == 3.6 and mapped.move_source == "proxy"
        assert any("is used" in reason for reason in mapped.reasons)

    def test_a_move_inside_the_band_is_kept(self):
        mapped = map_report(report(), inputs(implied_move_pct=6.0, proxy_move_pct=5.0), SETTINGS)
        assert mapped.move_pct == 8.38 and mapped.move_source == "the report"


def perturbed(data: dict, rng: random.Random) -> dict:
    data = copy.deepcopy(data)
    signals = data["execution_signals"]
    signals["expected_1d_move_pct"] = round(rng.uniform(1.0, 12.0), 2)
    signals["overnight_gap_risk"] = rng.choice(list(GAP_SCORES))
    signals["regime"] = rng.choice(list(REGIME_SCORES))
    signals["skew_bias"] = rng.choice(list(TAIL_SCORES))
    for catalyst in signals["next_day_catalysts"]:
        catalyst["impact"] = rng.choice(["low", "medium", "high"])
    return data


def _next_up(order: list[str], value: str) -> str:
    return order[min(len(order) - 1, order.index(value) + 1)]


REGIMES_BY_RISK = sorted(REGIME_SCORES, key=REGIME_SCORES.get)
RISKIER = {
    "expected_1d_move_pct": lambda v, rng: round(v + rng.uniform(0.01, 3.0), 2),
    "overnight_gap_risk": lambda v, rng: _next_up(["low", "moderate", "high"], v),
    "regime": lambda v, rng: _next_up(REGIMES_BY_RISK, v),
    "skew_bias": lambda v, rng: _next_up(["bullish_tail", "neutral", "bearish_tail"], v),
}


class TestMonotone:
    """Raising any risk input never loosens the overlay."""

    @pytest.mark.parametrize("field", sorted(RISKIER))
    def test_in_each_input(self, field):
        rng = random.Random(field)
        for _ in range(60):
            base = perturbed(raw(), rng)
            riskier = copy.deepcopy(base)
            signals = riskier["execution_signals"]
            signals[field] = RISKIER[field](signals[field], rng)
            before = map_report(report(base), inputs(), SETTINGS).overlay
            after = map_report(report(riskier), inputs(), SETTINGS).overlay
            assert after.no_looser_than(before), (
                field,
                base["execution_signals"][field],
                signals[field],
            )

    def test_in_a_catalysts_impact(self):
        rng = random.Random(3)
        for _ in range(60):
            base = perturbed(raw(), rng)
            riskier = copy.deepcopy(base)
            riskier["execution_signals"]["next_day_catalysts"][1]["impact"] = "high"
            before = map_report(report(base), inputs(), SETTINGS).overlay
            after = map_report(report(riskier), inputs(), SETTINGS).overlay
            assert after.no_looser_than(before)

    def test_in_a_horizons_tail(self):
        ceilings = []
        for es5 in (-20.0, -30.0, -45.0, -60.0, -90.0):
            data = raw()
            summary = data["horizons"]["next_month"]["summary"]
            summary["expected_shortfall_5pct"] = es5
            quantiles = summary["quantiles_pct"]
            quantiles["p05"] = max(quantiles["p05"], es5)  # a shortfall is below its quantile
            quantiles["p01"] = min(quantiles["p01"], es5)
            ceilings.append(map_report(report(data), inputs(), SETTINGS).weekly_ceiling)
        assert ceilings[0] == 1.0, "a tail better than the median sets no cap"
        assert ceilings == sorted(ceilings, reverse=True)


class TestBounded:
    def test_never_grows_a_buy_or_narrows_the_step(self):
        rng = random.Random(11)
        for _ in range(200):
            overlay = map_report(
                report(perturbed(raw(), rng)), inputs(rng.uniform(2, 8)), SETTINGS
            ).overlay
            assert 0.0 <= overlay.buy_multiplier <= 1.0
            assert 1.0 <= overlay.step_multiplier <= SETTINGS.spacing.max_multiplier
            assert (
                overlay.exposure_ceiling is None
                or overlay.exposure_ceiling >= SETTINGS.exposure_floor
            )
            assert overlay.target_multiplier == 1.0, (
                "the target follows only where the YAML opts in"
            )

    def test_the_floor_holds_the_weekly_ceiling(self):
        data = raw()
        data["horizons"]["next_month"]["summary"]["expected_shortfall_5pct"] = -95.0
        data["horizons"]["next_month"]["summary"]["quantiles_pct"]["p01"] = -96.0
        assert (
            map_report(report(data), inputs(), SETTINGS).weekly_ceiling == SETTINGS.exposure_floor
        )

    def test_the_target_follows_when_set(self):
        settings = replace(SETTINGS, spacing=OverlaySpacingConfig(target_follows=True))
        overlay = map_report(report(), inputs(), settings).overlay
        assert overlay.target_multiplier == overlay.step_multiplier > 1.0

    def test_levers_switched_off(self):
        settings = replace(
            SETTINGS,
            daily=False,
            spacing=OverlaySpacingConfig(enabled=False),
            weekly=OverlayWeeklyConfig(enabled=False),
        )
        mapped = map_report(report(), inputs(), settings)
        assert not mapped.overlay.pause and mapped.overlay.step_multiplier == 1.0
        assert mapped.weekly_ceiling is None
        assert mapped.tier == 3, "the tier is still reported"

    def test_blackouts_around_high_impact_catalysts(self):
        settings = replace(SETTINGS, blackout_minutes=15)
        overlay = map_report(report(), inputs(), settings).overlay
        ((start, end),) = overlay.blackouts  # the 15:00 UTC Michigan release
        assert (start.hour, start.minute, end.hour, end.minute) == (14, 45, 15, 15)


class TestTheCalendar:
    def test_an_fomc_day_the_report_missed_is_added_as_high(self):
        data = raw()
        for catalyst in data["execution_signals"]["next_day_catalysts"]:
            catalyst["impact"] = "low"
        fomc = Catalyst("FOMC decision (engine calendar)", "high", source="engine")
        plain = map_report(report(data), inputs(), SETTINGS)
        with_fomc = map_report(report(data), inputs(calendar=(fomc,)), SETTINGS)
        assert plain.components["catalyst"] == 0.0
        assert with_fomc.components["catalyst"] == 1.0

    def test_the_engine_knows_its_fomc_days(self):
        (fomc,) = calendar_catalysts(date(2026, 12, 9), live=False)
        assert fomc.impact == "high" and fomc.at.hour == 19  # 14:00 EST
        assert calendar_catalysts(date(2026, 12, 10), live=False) == ()


class TestPieces:
    def test_tiers_by_score(self):
        # v1's frozen thresholds: a change is a new mapping id, never an edit.
        assert TIER_THRESHOLDS == (0.1002, 0.30075, 0.4618) and not THRESHOLDS_PROVISIONAL
        scores = (0.0, 0.1, 0.1002, 0.3, 0.30075, 0.46, 0.4618, 1.0)
        assert [tier_of(s) for s in scores] == [0, 0, 1, 1, 2, 2, 3, 3]

    def test_realised_volatility_and_the_proxy_move(self):
        closes = [100.0, 101.0, 99.0, 102.0, 100.0, 103.0, 101.0]
        sigma = realised_sigma_pct(closes)
        assert 1.5 < sigma < 3.5
        assert realised_sigma_pct(closes[:5]) is None
        assert proxy_move(4.0, 2.0) == 3.0 and proxy_move(None, 2.0) == 2.0
        assert proxy_move(None, None) is None

    def test_baselines_round_trip(self, tmp_path):
        path = tmp_path / "baselines.json"
        write_baselines(
            {"TQQQ": Baseline("TQQQ", 4.2, {"next_month": -30.0}, ("2016-01-04", "2026-11-19"))},
            path,
        )
        loaded = read_baselines(path)["TQQQ"]
        assert loaded.move_pct == 4.2 and loaded.es5("next_month") == -30.0
        assert read_baselines(tmp_path / "missing.json") == {}
