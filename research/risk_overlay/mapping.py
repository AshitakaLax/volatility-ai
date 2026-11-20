"""
Mappings: a risk report in, one session's overlay out.

docs/daily_risk_report_plan.md ("The daily tiers (mapping v1,
pre-registered here)") is the specification; this is its code. Not the LLM
but these functions decide what a report does, inside bounds the
deployment's YAML sets (risk.overlay). They are what get backtested and
promoted, so they are:

  pure and deterministic   the same report and inputs give the same overlay,
                           in the trader, the server's preview and a backtest
  versioned by id          MAPPINGS["v1"]; a changed rule is a new id, never
                           an edit under the old one
  monotone                 raising any risk input -- the expected move, gap
                           risk, the regime's rank, a catalyst's impact, the
                           skew, a horizon's tail -- never loosens the overlay
  bounded                  they can only take risk away (engine/core/risk_overlay.py)

--------------------------------------------------------------------
MAPPING v1

1. ABSTAIN to NEUTRAL -- the session trades as configured -- when the report
   is for another fund or another session, arrived after its session ended,
   has a confidence below 0.6 or `degraded` coverage, has a base price more
   than 5% from our last close, or there is no baseline for the fund. When
   its expected move is outside 0.5x-2x the move the options index implies,
   the proxy's move replaces it (for the tiers and for spacing), and the
   reasons say so.
2. SCORE S in [0, 1], the weighted mean of five components (WEIGHTS).
3. TIER by S (TIER_THRESHOLDS, PROVISIONAL until calibrated by frequency on
   the proxy over 2011-2018 and frozen): 0 as configured; 1 buys x0.75; 2
   buys x0.5 and open lots held to 50% of equity; 3 no new grid buys.

Beside the tiers, two levers of their own:

  B, spacing   step x clip((move / baseline) ^ exponent, 1, max_multiplier)
  G, weekly    ceiling = clip(1 - slope x (|ES5| / |baseline ES5| - 1), floor, 1)
               for the configured horizon: this report's candidate for the
               week; archive.py decides which report sets the week.

Fields no mapping reads: mean_pct and prob_positive (a directional call no
evidence here supports), suggested_strategy_weights (each deployment trades
one strategy), kelly_fraction_cap (unanchored).
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass, field, replace
from datetime import date, datetime, timedelta
from typing import Any

from engine.core.config import RiskOverlayConfig
from engine.core.risk_overlay import SessionOverlay, neutral_for
from engine.core.risk_report import DEGRADED, Catalyst, RiskReport, day_bounds, regular_bounds
from research.risk_overlay.baselines import Baseline

DEFAULT_MAPPING = "v1"

MIN_CONFIDENCE = 0.6
MAX_BASE_PRICE_GAP = 0.05
# The report's move against the options index's: outside this band the
# proxy's volatility replaces it.
IMPLIED_BAND = (0.5, 2.0)

WEIGHTS: Mapping[str, float] = {
    "volatility": 0.35,
    "gap": 0.20,
    "regime": 0.20,
    "catalyst": 0.15,
    "tail": 0.10,
}
GAP_SCORES = {"low": 0.0, "moderate": 0.5, "high": 1.0}
REGIME_SCORES = {
    "low_vol_uptrend": 0.0,
    "mean_reverting_range": 0.2,
    "breakout_expansion": 0.5,
    "event_driven": 0.6,
    "high_vol_downtrend": 1.0,
}
IMPACT_SCORES = {"low": 0.0, "medium": 0.5, "high": 1.0}
TAIL_SCORES = {"bullish_tail": 0.0, "neutral": 0.5, "bearish_tail": 1.0}
# The volatility component: 0 at the baseline move, 1 at 2.5x it.
VOL_FULL_RATIO = 2.5

# PROVISIONAL (the plan's numbers before calibration): tier 1 from S 0.35,
# tier 2 from 0.55, tier 3 from 0.75.
TIER_THRESHOLDS: tuple[float, float, float] = (0.35, 0.55, 0.75)
THRESHOLDS_PROVISIONAL = True


@dataclass(frozen=True)
class Tier:
    """What one tier does to a session's buying."""

    pause: bool = False
    buy_multiplier: float = 1.0
    exposure_ceiling: float | None = None


TIERS: tuple[Tier, ...] = (
    Tier(),
    Tier(buy_multiplier=0.75),
    Tier(buy_multiplier=0.5, exposure_ceiling=0.5),
    Tier(pause=True, buy_multiplier=1.0),
)


@dataclass(frozen=True)
class MappingInputs:
    """What a mapping reads besides the report (research/risk_overlay/inputs.py
    builds it).

    symbol            the fund the deployment trades
    session           the session the overlay is for
    received_at       when the report arrived (None: a backtest's replay)
    last_close        our own last close before the session
    implied_move_pct  the 1-day move the options index implies for the fund
                      (3 x VXN / sqrt(252) for TQQQ), None when unknown or stale
    implied_source    what that came from, in words ("VXN 24.10 on 2026-11-19")
    proxy_move_pct    the proxy's expected move, None when unknown
    calendar          the engine's own FOMC and earnings catalysts for the session
    baseline          the fund's frozen baselines (baselines.py)
    """

    symbol: str
    session: date
    received_at: datetime | None = None
    last_close: float | None = None
    implied_move_pct: float | None = None
    implied_source: str | None = None
    proxy_move_pct: float | None = None
    calendar: tuple[Catalyst, ...] = ()
    baseline: Baseline | None = None


@dataclass(frozen=True)
class Mapped:
    """A report mapped for one session: the daily overlay (the week's cap
    is composed in by archive.session_overlay) and how it was reached."""

    overlay: SessionOverlay
    abstained: bool
    mapping_id: str
    score: float | None = None
    components: Mapping[str, float] = field(default_factory=dict)
    tier: int | None = None
    move_pct: float | None = None
    move_source: str | None = None
    step_multiplier: float = 1.0
    weekly_ceiling: float | None = None
    weekly_ratio: float | None = None
    catalysts: tuple[Catalyst, ...] = ()
    reasons: tuple[str, ...] = ()
    provisional: bool = THRESHOLDS_PROVISIONAL

    def to_dict(self) -> dict[str, Any]:
        return {
            "overlay": self.overlay.to_dict(),
            "abstained": self.abstained,
            "mapping_id": self.mapping_id,
            "score": self.score,
            "components": dict(self.components),
            "tier": self.tier,
            "move_pct": self.move_pct,
            "move_source": self.move_source,
            "step_multiplier": self.step_multiplier,
            "weekly_ceiling": self.weekly_ceiling,
            "weekly_ratio": self.weekly_ratio,
            "catalysts": [c.to_dict() for c in self.catalysts],
            "reasons": list(self.reasons),
            "provisional": self.provisional,
            "summary": self.overlay.describe(),
        }


def _clip(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def _round(value: float | None, places: int = 4) -> float | None:
    return round(value, places) if value is not None else None


def tier_of(score: float, thresholds: tuple[float, float, float] | None = None) -> int:
    """The tier score S falls in (TIER_THRESHOLDS, or a research variant's)."""
    return sum(1 for threshold in (thresholds or TIER_THRESHOLDS) if score >= threshold)


def session_catalysts(report: RiskReport, inputs: MappingInputs) -> tuple[Catalyst, ...]:
    """The report's catalysts that fall in the session's day (from the
    previous close to this close; one without a time counts), merged with
    the engine's own calendar: an FOMC decision or a megacap reaction
    session the report missed is added as high."""
    start, end = day_bounds(inputs.session)
    found = [c for c in report.catalysts if c.at is None or start <= c.at < end]
    found.extend(c for c in inputs.calendar if c.at is None or start <= c.at < end)
    return tuple(found)


def _abstain(
    report: RiskReport | None,
    inputs: MappingInputs,
    settings: RiskOverlayConfig,
    mapping_id: str,
    reasons: list[str],
) -> Mapped:
    overlay = replace(
        neutral_for(inputs.session, mode=settings.mode, reasons=reasons),
        mapping_id=mapping_id,
        report_sha256=report.sha256 if report is not None else None,
    )
    return Mapped(overlay=overlay, abstained=True, mapping_id=mapping_id, reasons=tuple(reasons))


def weekly_candidate(
    report: RiskReport, baseline: Baseline, settings: RiskOverlayConfig
) -> tuple[float | None, float | None, str | None]:
    """(ceiling, tail ratio, why) this report proposes for its week, or
    Nones when the baseline lacks the horizon."""
    weekly = settings.weekly
    horizons = ("next_month", "next_quarter") if weekly.horizon == "max" else (weekly.horizon,)
    ratios = []
    for horizon in horizons:
        base = baseline.es5(horizon)
        summary = report.horizons.get(horizon)
        if base is None or summary is None or base == 0:
            continue
        ratios.append((abs(summary.es5_pct) / abs(base), horizon, summary.es5_pct, base))
    if not ratios:
        return None, None, None
    ratio, horizon, es5, base = max(ratios)
    ceiling = _clip(1.0 - float(weekly.slope) * (ratio - 1.0), float(settings.exposure_floor), 1.0)
    why = (
        f"{horizon} ES5 {es5:.1f}% is {ratio:.2f}x the fund's median {base:.1f}%: "
        f"week's cap {ceiling:.0%}"
    )
    return round(ceiling, 4), round(ratio, 4), why


def map_v1(
    report: RiskReport,
    inputs: MappingInputs,
    settings: RiskOverlayConfig,
    variant: Mapping[str, Any] | None = None,
) -> Mapped:
    """Mapping v1 (module docstring). `variant` is for the robustness stage
    only (tools/probe_risk_overlay.py) -- `thresholds_delta` moves every tier
    threshold, `drop` leaves one component out and reweights the rest; a
    trader never passes one."""
    variant = variant or {}
    mapping_id = "v1"
    reasons: list[str] = []
    if report.symbol != inputs.symbol.upper():
        return _abstain(
            report,
            inputs,
            settings,
            mapping_id,
            [f"the report is for {report.symbol}; this deployment trades {inputs.symbol}"],
        )
    if report.session != inputs.session:
        return _abstain(
            report,
            inputs,
            settings,
            mapping_id,
            [f"the report is for {report.session}, not {inputs.session}"],
        )
    if inputs.received_at is not None and inputs.received_at >= regular_bounds(inputs.session)[1]:
        return _abstain(
            report, inputs, settings, mapping_id, ["it arrived after its session ended"]
        )
    if report.confidence < MIN_CONFIDENCE:
        reasons.append(f"its confidence {report.confidence:.2f} is below {MIN_CONFIDENCE}")
    if report.coverage == DEGRADED:
        reasons.append("its sources are degraded")
    if inputs.last_close:
        gap = abs(report.base_price / inputs.last_close - 1.0)
        if gap > MAX_BASE_PRICE_GAP:
            reasons.append(
                f"its base price {report.base_price:.2f} is {gap:.1%} from our last close "
                f"{inputs.last_close:.2f}"
            )
    baseline = inputs.baseline
    if baseline is None:
        reasons.append(f"there is no frozen baseline for {inputs.symbol} yet")
    if reasons:
        return _abstain(report, inputs, settings, mapping_id, reasons)

    move = report.expected_move_pct
    move_source = "the report"
    if inputs.implied_move_pct:
        ratio = move / inputs.implied_move_pct
        low, high = IMPLIED_BAND
        if not low <= ratio <= high:
            replacement = inputs.proxy_move_pct or inputs.implied_move_pct
            which = "the proxy's" if inputs.proxy_move_pct else "the implied"
            reasons.append(
                f"its expected move {move:.2f}% is {ratio:.2f}x the {inputs.implied_move_pct:.2f}% "
                f"{inputs.implied_source or 'the options index'} implies; {which} "
                f"{replacement:.2f}% is used"
            )
            move, move_source = replacement, which.removeprefix("the ").removesuffix("'s")

    catalysts = session_catalysts(report, inputs)
    move_ratio = move / baseline.move_pct
    components = {
        "volatility": _clip((move_ratio - 1.0) / (VOL_FULL_RATIO - 1.0), 0.0, 1.0),
        "gap": GAP_SCORES[report.gap_risk],
        "regime": REGIME_SCORES[report.regime],
        "catalyst": max((IMPACT_SCORES[c.impact] for c in catalysts), default=0.0),
        "tail": TAIL_SCORES[report.skew_bias],
    }
    weights = dict(WEIGHTS)
    if variant.get("drop"):
        weights.pop(variant["drop"])
        total = sum(weights.values())
        weights = {k: v / total for k, v in weights.items()}
    score = sum(weights[name] * value for name, value in components.items() if name in weights)
    thresholds = None
    if variant.get("thresholds_delta"):
        thresholds = tuple(t + float(variant["thresholds_delta"]) for t in TIER_THRESHOLDS)
    tier = tier_of(score, thresholds)
    reasons.append(
        f"S {score:.2f}: tier {tier}"
        + (" (provisional thresholds)" if THRESHOLDS_PROVISIONAL else "")
    )

    daily = TIERS[tier] if settings.daily else TIERS[0]
    step_multiplier = 1.0
    if settings.spacing.enabled:
        step_multiplier = _clip(
            move_ratio ** float(settings.spacing.exponent),
            1.0,
            float(settings.spacing.max_multiplier),
        )
        if step_multiplier > 1.0:
            reasons.append(
                f"expected move {move:.2f}% against a median {baseline.move_pct:.2f}%: "
                f"grid step x{step_multiplier:.2f}"
            )
    ceiling = ratio_ = None
    if settings.weekly.enabled:
        ceiling, ratio_, why = weekly_candidate(report, baseline, settings)
        if why:
            reasons.append(why)
    blackouts: list[tuple[datetime, datetime]] = []
    if settings.blackout_minutes and float(settings.blackout_minutes) > 0:
        span = timedelta(minutes=float(settings.blackout_minutes))
        for catalyst in catalysts:
            if catalyst.impact == "high" and catalyst.at is not None:
                blackouts.append((catalyst.at - span, catalyst.at + span))

    exposure = daily.exposure_ceiling
    if exposure is not None:
        exposure = max(exposure, float(settings.exposure_floor))
    overlay = SessionOverlay(
        session=inputs.session,
        pause=daily.pause,
        buy_multiplier=daily.buy_multiplier,
        exposure_ceiling=exposure,
        step_multiplier=round(step_multiplier, 4),
        target_multiplier=(round(step_multiplier, 4) if settings.spacing.target_follows else 1.0),
        blackouts=tuple(sorted(blackouts)),
        supersedes=frozenset(settings.supersedes),
        mode=settings.mode,
        tier=tier,
        weekly_ceiling=ceiling,
        reasons=tuple(reasons),
        mapping_id=mapping_id,
        report_sha256=report.sha256,
        exempt=tuple(settings.exempt),
    )
    return Mapped(
        overlay=overlay,
        abstained=False,
        mapping_id=mapping_id,
        score=round(score, 4),
        components={k: round(v, 4) for k, v in components.items()},
        tier=tier,
        move_pct=_round(move),
        move_source=move_source,
        step_multiplier=round(step_multiplier, 4),
        weekly_ceiling=ceiling,
        weekly_ratio=ratio_,
        catalysts=catalysts,
        reasons=tuple(reasons),
    )


MAPPINGS: dict[str, Callable[[RiskReport, MappingInputs, RiskOverlayConfig], Mapped]] = {
    "v1": map_v1,
}


def map_report(
    report: RiskReport,
    inputs: MappingInputs,
    settings: RiskOverlayConfig,
    mapping_id: str | None = None,
    variant: Mapping[str, Any] | None = None,
) -> Mapped:
    """The overlay `settings.mapping` (or `mapping_id`) makes of `report`;
    `variant` as map_v1's (research only)."""
    mapping_id = mapping_id or settings.mapping
    try:
        mapping = MAPPINGS[mapping_id]
    except KeyError:
        raise ValueError(
            f"unknown risk overlay mapping {mapping_id!r}; known: {', '.join(MAPPINGS)}"
        ) from None
    return (
        mapping(report, inputs, settings, variant) if variant else mapping(report, inputs, settings)
    )


__all__ = [
    "DEFAULT_MAPPING",
    "IMPLIED_BAND",
    "MAPPINGS",
    "MIN_CONFIDENCE",
    "THRESHOLDS_PROVISIONAL",
    "TIERS",
    "TIER_THRESHOLDS",
    "WEIGHTS",
    "Mapped",
    "MappingInputs",
    "Tier",
    "map_report",
    "map_v1",
    "session_catalysts",
    "tier_of",
    "weekly_candidate",
]
