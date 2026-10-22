"""tools/sweep_brute_force.py: the regime thresholds it plans fire at the
model's own output levels, and MLRegimeScaledSizing accepts them.

On 2026-10-21 the planner rounded to the nearest: half of both RSP
ml_regime sweeps were refused on their first bar, and the other half could
latch only at the model's top level.
"""

from __future__ import annotations

import pytest

from tools import sweep_brute_force as tool

# RSP's crash model, retrained 2026-10-19: its scores sit on a few exact
# levels, so p75 through p95 are one level and p99 is the top one.
RSP_CRASH = {
    "min": 0.22077143410586025,
    "p50": 0.22929022513118824,
    "p75": 0.23805447063302002,
    "p90": 0.23805447063302002,
    "p95": 0.23805447063302002,
    "p99": 0.24787478110170563,
    "max": 0.24787478110170563,
}
RSP_FWDVOL = {"p50": 0.15011, "p75": 0.16072}


@pytest.fixture
def space(monkeypatch):
    monkeypatch.setattr(
        tool, "_quantiles", lambda _fund, head: RSP_CRASH if head == "crash" else RSP_FWDVOL
    )
    return tool._regime_space("RSP")


def test_each_entry_fires_at_its_level_and_none_is_above_p99(space):
    """The latch enters at score >= enter. Rounded to the nearest, the p90
    level (0.238054) became 0.2381 -- above it, so that entry fired only at
    the top level -- and p99 (0.247875) became 0.2479, above every score,
    which the strategy refuses."""
    assert space["regime_enter_threshold"] == [0.238, 0.2478]
    assert space["regime_enter_threshold"][0] <= RSP_CRASH["p90"]
    assert space["regime_enter_threshold"][1] <= RSP_CRASH["p99"]


def test_the_exit_fires_at_the_median_level(space):
    """The latch leaves at score <= exit, so the exit must not round below
    the median level -- and it must stay below every entry."""
    assert space["regime_exit_threshold"] == [0.2293]
    assert space["regime_exit_threshold"][0] >= RSP_CRASH["p50"]
    assert all(enter > 0.2293 for enter in space["regime_enter_threshold"])


def test_a_level_already_on_four_places_stays_put():
    """No float noise: 0.238 * 10_000 is 2379.9999999999995."""
    assert tool._at_most(0.238) == 0.238
    assert tool._at_least(0.2293) == 0.2293


@pytest.mark.skipif(
    not (tool.MODELS / "RSP_regime_crash.json").exists(),
    reason="no RSP regime model on this machine",
)
def test_the_strategy_accepts_every_planned_entry():
    """Against the model itself: the check that refused the 2026-10-21
    configurations, on each threshold the planner now chooses."""
    from research.ml.regime_scaled_sizing import MLRegimeScaledSizing

    space = tool._regime_space("RSP")
    for enter in space["regime_enter_threshold"]:
        MLRegimeScaledSizing(
            max_trade_pct=0.05,
            ticker="RSP",
            regime_enter_threshold=enter,
            regime_exit_threshold=space["regime_exit_threshold"][0],
        ).ensure_model_available()
