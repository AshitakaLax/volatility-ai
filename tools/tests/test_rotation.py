"""tools/rotation.py: the assignment rules and grid scaling."""

from __future__ import annotations

import numpy as np
import pandas as pd

from tools.rotation import (
    CASH,
    aligned_closes,
    assign_defensive,
    assign_relative_strength,
    count_switches,
    grid_scales,
    trailing_returns,
)

IDX = pd.date_range("2024-01-02", periods=6, freq="B", tz="UTC")
DAYS = [ts.date() for ts in IDX]


def test_trailing_returns_end_at_the_previous_session():
    closes = pd.DataFrame({"a": [100, 110, 121, 133.1, 146.41, 161.051]}, index=IDX)
    rs = trailing_returns(closes, 1)
    assert np.isnan(rs["a"].iloc[1])
    assert rs["a"].iloc[2] == 0.1 or abs(rs["a"].iloc[2] - 0.1) < 1e-12


def test_defensive_holds_the_lead_when_risk_on_else_the_best_calm_defensive():
    closes = pd.DataFrame(
        {"xlp": [100, 101, 102, 103, 104, 105], "gld": [100, 103, 106, 109, 112, 115]}, index=IDX
    )
    risk_on = dict(zip(DAYS, [True, False, False, False, False, False], strict=True))
    calm = {"xlp": dict.fromkeys(DAYS, True), "gld": {d: d != DAYS[4] for d in DAYS}}
    a = assign_defensive(risk_on, "TQQQ", closes, calm, days=1)
    assert a[DAYS[0]] == "TQQQ"
    assert a[DAYS[1]] == CASH  # no trailing return yet
    assert a[DAYS[2]] == a[DAYS[3]] == "gld"
    assert a[DAYS[4]] == "xlp"  # gld's own regime is turbulent that session


def test_defensive_falls_back_to_cash_when_nothing_is_calm():
    closes = pd.DataFrame({"xlp": [100, 101, 102, 103, 104, 105]}, index=IDX)
    a = assign_defensive(
        dict.fromkeys(DAYS, False), "TQQQ", closes, {"xlp": dict.fromkeys(DAYS, False)}, 1
    )
    assert set(a.values()) == {CASH}


def test_dual_momentum_picks_the_leader_and_goes_to_cash_when_all_fall():
    closes = pd.DataFrame(
        {"qqq": [100, 102, 104, 100, 96, 92], "xlp": [100, 101, 102, 101, 100, 99]}, index=IDX
    )
    a = assign_relative_strength(closes, 1)
    assert a[DAYS[2]] == "qqq"
    assert a[DAYS[5]] == CASH
    assert count_switches(a) >= 1


def test_grid_scales_are_relative_daily_ranges():
    idx = pd.date_range("2024-01-02 14:30", periods=10, freq="1D", tz="UTC")
    lead = pd.DataFrame({"open": 100.0, "high": 102.0, "low": 98.0, "close": 100.0}, index=idx)
    calm = pd.DataFrame({"open": 100.0, "high": 101.0, "low": 99.0, "close": 100.0}, index=idx)
    scales = grid_scales({"L": lead, "C": calm}, "L", warmup=10)
    assert scales["L"] == 1.0 and abs(scales["C"] - 0.5) < 1e-12


def test_aligned_closes_accepts_a_single_instrument():
    """The defensive mode used to reuse the turbulence basket helper and
    refused a single defensive candidate."""
    idx = pd.date_range("2024-01-02 14:30", periods=3, freq="1D", tz="UTC")
    frame = pd.DataFrame(
        {"open": 1.0, "high": 1.0, "low": 1.0, "close": [1.0, 2.0, 3.0]}, index=idx
    )
    out = aligned_closes({"XLP": frame}, ["XLP"])
    assert list(out.columns) == ["XLP"] and len(out) == 3
