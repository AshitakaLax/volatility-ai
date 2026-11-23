"""Reports at a chosen accuracy (research/risk_overlay/synthetic.py): the
accuracy achieved is the accuracy asked for, the tier frequencies are the
proxy's at every accuracy (unless the bias knob moves them), and a seed
reproduces its reports exactly."""

from __future__ import annotations

from datetime import date

import numpy as np
import pandas as pd
import pytest
from scipy import stats

from engine.core.config import RiskOverlayConfig
from engine.core.risk_report import parse_report
from engine.core.trading_calendar import sessions_between
from research.risk_overlay.baselines import Baseline
from research.risk_overlay.proxy import build_archive
from research.risk_overlay.schedules import entry_inputs
from research.risk_overlay.synthetic import (
    Knobs,
    _rank_normal,
    latents,
    proxy_fields,
    synthetic_reports,
    synthetic_schedule,
    truths,
)

SESSIONS = sessions_between(date(2022, 1, 1), date(2025, 6, 30))
BASELINE = Baseline("TQQQ", 4.0, {"next_month": -30.0, "next_quarter": -45.0})


@pytest.fixture(scope="module")
def history():
    rng = np.random.default_rng(11)
    closes = pd.Series(
        50 * np.exp(np.cumsum(rng.normal(0, 0.03, len(SESSIONS)))), index=pd.DatetimeIndex(SESSIONS)
    )

    def series(level, spread):
        stamps = pd.DatetimeIndex(
            [pd.Timestamp(d).tz_localize("UTC") + pd.Timedelta(hours=21) for d in SESSIONS]
        )
        return pd.Series(
            level * np.exp(np.cumsum(rng.normal(0, spread, len(SESSIONS)))), index=stamps
        )

    outside = {
        "cboe_VXN": series(22, 0.05),
        "cboe_VIX": series(17, 0.05),
        "cboe_VIX9D": series(16, 0.06),
        "cboe_VIX3M": series(19, 0.03),
        "cboe_VIX6M": series(21, 0.02),
        "cboe_SKEW": series(135, 0.01),
        "yahoo_QQQ": series(400, 0.012),
    }
    entries = build_archive("TQQQ", closes, outside, SESSIONS[260:])
    reports = [parse_report(e["report"]).require() for e in entries]
    days = [r.session for r in reports]
    by_day = {d.date(): float(c) for d, c in closes.items()}
    opens = {d: c * (1 + rng.normal(0, 0.01)) for d, c in by_day.items()}
    lows = {d: min(c, opens[d]) * 0.98 for d, c in by_day.items()}
    truth = truths(days, opens, by_day, lows)
    inputs = [entry_inputs(e, r, "TQQQ", BASELINE) for e, r in zip(entries, reports, strict=True)]
    received = [e["received_at"] for e in entries]
    return reports, truth, inputs, received


def test_noisy_hits_its_rank_correlation(history):
    reports, truth, _inputs, _received = history
    for rho in (0.2, 0.5, 0.9):
        z = latents(truth, proxy_fields(reports), Knobs(family="noisy", accuracy=rho, seed=3))
        achieved = stats.spearmanr(z["move"], _rank_normal(truth.move))[0]
        assert achieved == pytest.approx(rho, abs=0.1), (rho, achieved)


def test_the_mixture_tells_the_truth_on_its_share_of_sessions(history):
    reports, truth, _inputs, _received = history
    z = latents(truth, proxy_fields(reports), Knobs(family="mixture", accuracy=0.3, seed=5))
    share = float(np.mean(np.isclose(z["move"], _rank_normal(truth.move))))
    assert share == pytest.approx(0.3, abs=0.06)


def test_accuracy_one_reproduces_the_truths_ranking(history):
    reports, truth, _inputs, _received = history
    synthetic = synthetic_reports(reports, truth, Knobs(family="noisy", accuracy=1.0, seed=1))
    moves = [r.expected_move_pct for r in synthetic]
    assert stats.spearmanr(moves, truth.move)[0] > 0.99


def test_the_values_are_the_proxys_and_the_shortfall_stays_below_its_quantile(history):
    reports, truth, _inputs, _received = history
    synthetic = synthetic_reports(reports, truth, Knobs(family="noisy", accuracy=0.4, seed=2))
    assert sorted(r.expected_move_pct for r in synthetic) == pytest.approx(
        sorted(r.expected_move_pct for r in reports)
    )
    for report in synthetic:
        month = report.horizon("next_month")
        assert month.es5_pct <= month.quantiles["p05"] + 1e-9


def test_a_seed_reproduces_its_reports(history):
    reports, truth, _inputs, _received = history
    knobs = Knobs(family="noisy", accuracy=0.3, seed=9, persistence=0.8, shared=0.7, bias=0.5)
    first = [r.expected_move_pct for r in synthetic_reports(reports, truth, knobs)]
    again = [r.expected_move_pct for r in synthetic_reports(reports, truth, knobs)]
    other = [
        r.expected_move_pct
        for r in synthetic_reports(reports, truth, Knobs(family="noisy", accuracy=0.3, seed=10))
    ]
    assert first == again != other


def test_the_tier_frequencies_are_the_proxys_at_every_accuracy(history):
    reports, truth, inputs, received = history
    settings = RiskOverlayConfig(mode="enforce")
    from research.risk_overlay.mapping import map_report

    proxy = sorted(
        m.tier for m in (map_report(r, x, settings) for r, x in zip(reports, inputs, strict=True))
    )
    for accuracy in (0.0, 0.5, 1.0):
        schedule = synthetic_schedule(
            reports,
            inputs,
            received,
            truth,
            Knobs(family="noisy", accuracy=accuracy, seed=4),
            settings,
        )
        tiers = sorted(schedule.get(r.session).tier or 0 for r in reports)
        assert tiers == proxy, accuracy


def test_a_bias_moves_the_values_and_how_often_the_tiers_come(history):
    """z + beta alone would change nothing, since a quantile map keeps only
    ranks: the bias moves each rank's quantile, in the fields and the tiers."""
    reports, truth, inputs, received = history
    settings = RiskOverlayConfig(mode="enforce")

    def run(bias):
        knobs = Knobs(family="noisy", accuracy=0.5, seed=6, bias=bias)
        moves = [r.expected_move_pct for r in synthetic_reports(reports, truth, knobs)]
        schedule = synthetic_schedule(reports, inputs, received, truth, knobs, settings)
        tiers = [schedule.get(r.session).tier or 0 for r in reports]
        return float(np.mean(moves)), float(np.mean(tiers))

    complacent, plain, alarmist = run(-0.5), run(0.0), run(0.5)
    assert complacent[0] < plain[0] < alarmist[0]
    assert complacent[1] < plain[1] < alarmist[1]
