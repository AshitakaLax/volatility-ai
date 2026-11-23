"""
Risk reports at a chosen accuracy, built from what actually happened next
(docs/daily_risk_report_plan.md, "Backtesting at chosen levels of report
accuracy").

LOOKAHEAD BY DESIGN. A synthetic report is a ruler for how much accuracy is
worth, never evidence that any source has it. Each is the proxy report of
its session (research/risk_overlay/proxy.py) with the fields the mappings
read replaced:

  field                     its truth (measured after the session's report)
  expected_1d_move_pct      the session's |close-to-close return|
  overnight_gap_risk        |open / previous close - 1|
  regime                    the worst drawdown over the next 21 sessions
  skew_bias                 the same, with its own noise
  next_month ES5            the worst drawdown from the open over 21 sessions
  next_quarter ES5          the same over 63 sessions
  catalysts                 the calendars' (scheduled, known either way),
                            less a `catalyst_miss` share of them

Each field gets a latent z: its truth's rank over the whole history as a
standard normal (z_truth), mixed with noise by the family's knob:

  mixture   p    the truth on a share p of sessions, another random session's
                 truth on the rest -- a wrong day carries no information
  noisy     rho  z = rho z_truth + sqrt(1 - rho^2) e: every day partly right
  proxy+    lam  z = standardise(z_proxy + lam z_resid): the proxy plus some
                 of what it missed; the LLM's real question

and is QUANTILE-MAPPED back onto the proxy's own distribution of the field:
z's rank among the sessions picks the value at that rank. So every synthetic
history has realistic values and the proxy's tier frequencies whatever its
accuracy: accuracy moves WHICH days are flagged, never how often.

The other ways a report goes wrong are knobs on the noise: persistence phi
(AR(1) errors), shared error eta (one misreading across fields), bias beta
(complacent below 0, alarmist above), a missing rate (sessions with no
report) and a catalyst miss rate. Seeds choose which days are wrong.

The bias is the one knob that changes how often: a quantile map keeps only
ranks, so z + beta would change nothing. Instead each rank's normal quantile
is moved by beta before its value is picked, in the fields and again when the
score is ranked onto the proxy's tiers. On TQQQ from 2016, an alarmist
history (beta 0.5) puts 33% of sessions in tier 3 against the proxy's 18%,
and a complacent one (-0.5) 8%.
"""

from __future__ import annotations

import math
import random
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, replace
from datetime import date
from typing import Any

import numpy as np

from engine.core.risk_report import (
    GAP_RISKS,
    SKEW_BIASES,
    HorizonSummary,
    RiskReport,
)

FAMILIES = ("mixture", "noisy", "proxy+")
FIELDS = ("move", "gap", "regime", "skew", "tail21", "tail63")
# Each field's truth, by name in Truths.
TRUTH_OF = {
    "move": "move",
    "gap": "gap",
    "regime": "tail21",
    "skew": "tail21",
    "tail21": "tail21",
    "tail63": "tail63",
}
REGIMES_BY_RISK = (
    "low_vol_uptrend",
    "mean_reverting_range",
    "breakout_expansion",
    "event_driven",
    "high_vol_downtrend",
)


@dataclass(frozen=True)
class Knobs:
    """One synthetic setting (module docstring)."""

    family: str = "noisy"
    accuracy: float = 0.5  # p, rho or lambda
    seed: int = 0
    persistence: float = 0.0  # phi
    shared: float = 0.0  # eta
    bias: float = 0.0  # beta, in z units
    missing: float = 0.0
    catalyst_miss: float = 0.0

    def __post_init__(self) -> None:
        if self.family not in FAMILIES:
            raise ValueError(f"family must be one of {FAMILIES}, got {self.family!r}")
        if not 0.0 <= self.accuracy <= 1.0:
            raise ValueError(f"accuracy must be in [0, 1], got {self.accuracy}")

    def to_dict(self) -> dict[str, Any]:
        return dict(self.__dict__)


def _rank_normal(values: Sequence[float]) -> np.ndarray:
    """Each value's rank as a standard normal quantile (ties averaged)."""
    from scipy import stats

    x = np.asarray(values, dtype=float)
    ranks = stats.rankdata(x)
    return stats.norm.ppf((ranks - 0.5) / len(x))


def _standardise(z: np.ndarray) -> np.ndarray:
    sd = z.std()
    return (z - z.mean()) / sd if sd > 0 else z - z.mean()


@dataclass(frozen=True)
class Truths:
    """What each session's report should have said, by session, aligned
    with the proxy reports (same order)."""

    sessions: tuple[date, ...]
    move: np.ndarray
    gap: np.ndarray
    tail21: np.ndarray  # positive: the size of the worst drawdown
    tail63: np.ndarray

    def of(self, name: str) -> np.ndarray:
        return getattr(self, name)


def truths(
    sessions: Sequence[date],
    opens: Mapping[date, float],
    closes: Mapping[date, float],
    lows: Mapping[date, float],
) -> Truths:
    """Each session's truths from daily open, close and low (module docstring)."""
    days = sorted(closes)
    position = {d: i for i, d in enumerate(days)}
    close = np.array([closes[d] for d in days])
    low = np.array([lows.get(d, closes[d]) for d in days])
    move, gap, t21, t63 = [], [], [], []
    for session in sessions:
        i = position.get(session)
        if i is None or i == 0:
            for out in (move, gap, t21, t63):
                out.append(np.nan)
            continue
        prior = close[i - 1]
        move.append(abs(close[i] / prior - 1.0) * 100.0)
        gap.append(abs(opens.get(session, close[i]) / prior - 1.0) * 100.0)
        start = opens.get(session, prior)
        for horizon, out in ((21, t21), (63, t63)):
            window = low[i : i + horizon]
            out.append(
                max(0.0, 1.0 - float(window.min()) / start) * 100.0 if len(window) else np.nan
            )

    def filled(values: list) -> np.ndarray:
        arr = np.asarray(values, dtype=float)
        median = np.nanmedian(arr) if np.isfinite(arr).any() else 0.0
        return np.where(np.isfinite(arr), arr, median)

    return Truths(tuple(sessions), filled(move), filled(gap), filled(t21), filled(t63))


def proxy_fields(reports: Sequence[RiskReport]) -> dict[str, np.ndarray]:
    """The proxy's value of each field, numerically (categoricals as their
    rank of risk), in the reports' order."""
    gap_rank = {g: i for i, g in enumerate(GAP_RISKS)}
    regime_rank = {r: i for i, r in enumerate(REGIMES_BY_RISK)}
    skew_rank = {s: i for i, s in enumerate(SKEW_BIASES)}
    return {
        "move": np.array([r.expected_move_pct for r in reports]),
        "gap": np.array([gap_rank[r.gap_risk] for r in reports], dtype=float),
        "regime": np.array([regime_rank[r.regime] for r in reports], dtype=float),
        "skew": np.array([skew_rank[r.skew_bias] for r in reports], dtype=float),
        "tail21": np.array([-r.horizon("next_month").es5_pct for r in reports]),
        "tail63": np.array([-r.horizon("next_quarter").es5_pct for r in reports]),
    }


def _noise(n: int, knobs: Knobs, rng: np.random.Generator, common: np.ndarray) -> np.ndarray:
    own = rng.standard_normal(n)
    e = math.sqrt(knobs.shared) * common + math.sqrt(1.0 - knobs.shared) * own
    if knobs.persistence:
        out = np.empty(n)
        out[0] = e[0]
        scale = math.sqrt(1.0 - knobs.persistence**2)
        for i in range(1, n):
            out[i] = knobs.persistence * out[i - 1] + scale * e[i]
        return out
    return e


def latents(truth: Truths, proxy: Mapping[str, np.ndarray], knobs: Knobs) -> dict[str, np.ndarray]:
    """Each field's latent z (module docstring)."""
    n = len(truth.sessions)
    rng = np.random.default_rng(knobs.seed)
    common = rng.standard_normal(n)
    draw = rng.permutation(n)  # the mixture's "other session" for each session
    keep = rng.random(n) < knobs.accuracy
    out = {}
    for field in FIELDS:
        z_truth = _rank_normal(truth.of(TRUTH_OF[field]))
        e = _noise(n, knobs, rng, common)
        if knobs.family == "mixture":
            z = np.where(keep, z_truth, z_truth[draw])
            # A mixture's wrong days carry no information, so noise is not
            # added on top; persistence and shared error act through `keep`.
        elif knobs.family == "noisy":
            rho = knobs.accuracy
            z = rho * z_truth + math.sqrt(max(0.0, 1.0 - rho * rho)) * e
        else:  # proxy+
            z_proxy = _rank_normal(proxy[field])
            beta = (
                float(np.dot(z_proxy, z_truth) / np.dot(z_proxy, z_proxy))
                if np.dot(z_proxy, z_proxy)
                else 0.0
            )
            residual = z_truth - beta * z_proxy
            z = _standardise(z_proxy + knobs.accuracy * _standardise(residual))
        out[field] = z  # the bias acts in quantile_map, where a shift survives
    return out


def quantile_map(z: np.ndarray, reference: np.ndarray, shift: float = 0.0) -> np.ndarray:
    """Each z's rank picks the value at that rank in `reference`. A `shift`
    (the bias knob, in z units) first moves each rank's normal quantile, so
    the values sit higher on the reference (shift > 0) or lower than the
    ranks alone would put them."""
    from scipy import stats

    order = np.sort(np.asarray(reference, dtype=float))
    # Ordinal ranks: with as many z as reference values this is an exact
    # permutation of the reference, so its frequencies are kept exactly.
    ranks = stats.rankdata(z, method="ordinal") - 1
    if shift:
        u = stats.norm.cdf(stats.norm.ppf((ranks + 0.5) / len(z)) + shift)
        picks = np.floor(u * len(order)).astype(int)
    else:
        picks = np.round(ranks / max(1, len(z) - 1) * (len(order) - 1)).astype(int)
    return order[np.clip(picks, 0, len(order) - 1)]


def synthetic_reports(
    reports: Sequence[RiskReport], truth: Truths, knobs: Knobs
) -> list[RiskReport | None]:
    """The proxy's reports with the mapped fields replaced; None for a
    session the `missing` knob leaves without one."""
    proxy = proxy_fields(reports)
    z = latents(truth, proxy, knobs)
    mapped = {field: quantile_map(z[field], proxy[field], knobs.bias) for field in FIELDS}
    rng = random.Random(knobs.seed * 7919 + 1)
    out: list[RiskReport | None] = []
    for i, report in enumerate(reports):
        if knobs.missing and rng.random() < knobs.missing:
            out.append(None)
            continue
        catalysts = tuple(
            c
            for c in report.catalysts
            if not (knobs.catalyst_miss and rng.random() < knobs.catalyst_miss)
        )
        horizons = dict(report.horizons)
        for name, field in (("next_month", "tail21"), ("next_quarter", "tail63")):
            summary = horizons[name]
            es5 = -float(mapped[field][i])
            ratio = es5 / summary.es5_pct if summary.es5_pct else 1.0
            quantiles = {k: v * ratio if v < 0 else v for k, v in summary.quantiles.items()}
            horizons[name] = HorizonSummary(
                name=summary.name,
                trading_days=summary.trading_days,
                mean_pct=summary.mean_pct,
                median_pct=summary.median_pct,
                std_pct=summary.std_pct * max(ratio, 1e-6),
                prob_positive=summary.prob_positive,
                es5_pct=es5,
                quantiles=quantiles,
                bin_coverage=summary.bin_coverage,
            )
        move = float(mapped["move"][i])
        out.append(
            replace(
                report,
                expected_move_pct=move,
                gap_risk=GAP_RISKS[int(mapped["gap"][i])],
                regime=REGIMES_BY_RISK[int(mapped["regime"][i])],
                skew_bias=SKEW_BIASES[int(mapped["skew"][i])],
                catalysts=catalysts,
                horizons=horizons,
                sha256=f"synthetic-{knobs.family}-{knobs.accuracy}-{knobs.seed}-{i}",
            )
        )
    return out


def achieved_accuracy(truth: Truths, reports: Sequence[RiskReport | None]) -> float | None:
    """The rank correlation of the synthetic expected moves with the
    realised moves: the scale the nightly scorecard uses."""
    from scipy import stats

    pairs = [
        (r.expected_move_pct, m) for r, m in zip(reports, truth.move, strict=True) if r is not None
    ]
    if len(pairs) < 3:
        return None
    rho, _p = stats.spearmanr([a for a, _ in pairs], [b for _, b in pairs])
    return float(rho)


def synthetic_schedule(
    proxy: Sequence[RiskReport],
    inputs: Sequence[Any],
    received: Sequence[str],
    truth: Truths,
    knobs: Knobs,
    settings,
):
    """The OverlaySchedule a synthetic history enforces under `settings`.

    Each synthetic report is mapped with the deployment's mapping; its daily
    TIER is then ranked onto the proxy's own tiers (quantile_map of the score
    onto the proxy's tier assignments), so the tiers' frequencies are the
    proxy's whatever the accuracy -- the fields' marginals alone would not
    hold them, since the score depends on how the fields move together --
    unless the bias knob moves them (module docstring). The
    step and the week's cap come from the synthetic fields, whose marginals
    are the proxy's. `inputs[i]` is proxy report i's MappingInputs,
    `received[i]` when it arrived."""
    from research.risk_overlay.archive import schedule_from_entries
    from research.risk_overlay.mapping import TIERS, map_report

    proxy_mapped = [map_report(r, x, settings) for r, x in zip(proxy, inputs, strict=True)]
    proxy_tiers = np.array([m.tier if m.tier is not None else 0 for m in proxy_mapped], dtype=float)
    reports = synthetic_reports(proxy, truth, knobs)
    mapped = [
        map_report(r, x, settings) if r is not None else None
        for r, x in zip(reports, inputs, strict=True)
    ]
    scores = np.array([m.score if m is not None and m.score is not None else -1.0 for m in mapped])
    present = scores >= 0
    tiers = np.zeros(len(scores), dtype=int)
    if present.any():
        tiers[present] = quantile_map(scores[present], proxy_tiers, knobs.bias).astype(int)
    entries = []
    for i, m in enumerate(mapped):
        if m is None or m.abstained:
            continue
        tier = TIERS[int(tiers[i])] if settings.daily else TIERS[0]
        overlay = replace(
            m.overlay,
            tier=int(tiers[i]),
            pause=tier.pause,
            buy_multiplier=tier.buy_multiplier,
            exposure_ceiling=(
                max(tier.exposure_ceiling, float(settings.exposure_floor))
                if tier.exposure_ceiling is not None
                else None
            ),
        )
        entries.append(
            {
                "session": proxy[i].session.isoformat(),
                "overlay": overlay.to_dict(),
                "receipts": [{"received_at": received[i], "weekly_ceiling": m.weekly_ceiling}],
            }
        )
    return schedule_from_entries(entries, [r.session for r in proxy], settings)


__all__ = [
    "FAMILIES",
    "FIELDS",
    "Knobs",
    "Truths",
    "achieved_accuracy",
    "latents",
    "proxy_fields",
    "quantile_map",
    "synthetic_reports",
    "synthetic_schedule",
    "truths",
]
