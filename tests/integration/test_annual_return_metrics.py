"""Average/Best/Worst Year Return %, wired end to end through a real sweep.

tests/unit/test_performance_analyzer.py covers annual_returns() in
isolation. This confirms optimization_controller.py actually calls it
correctly on the equity curve a real run produces, rather than on some
other series, and that the three new metrics agree with an independent
computation over the SAME equity curve the run returned.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from optimization_controller import OptimizationController
from src.performance_analyzer import annual_returns
from src.size_calculators import FixedPortfolioPercentage


def _flat_price_series(years: int = 3) -> pd.DataFrame:
    """A price series that never drops, so the grid never triggers a buy
    and equity stays at initial_cash for the whole run -- a case whose
    expected annual returns (all exactly 0%) do not depend on trade
    logic, only on the wiring being correct."""
    idx = pd.date_range("2020-01-02", periods=years * 365 + 1, freq="D", tz="UTC")
    price = pd.Series(100.0, index=idx)
    return pd.DataFrame(
        {"open": price, "high": price, "low": price, "close": price}, index=idx
    )


def test_a_never_triggered_run_reports_zero_for_all_three_years():
    df = _flat_price_series()
    controller = OptimizationController(historical_data=df)

    result = controller.run_sweep(
        grid_steps=[0.10],  # never reached -- price never falls
        profit_targets=[0.05],
        strategy_class=FixedPortfolioPercentage,
        strategy_params_grid=[{"allocation_pct": 0.05}],
    )
    row = result.iloc[0]

    assert row["Trade Count"] == 0
    assert row["Average Annual Return %"] == pytest.approx(0.0)
    assert row["Best Year Return %"] == pytest.approx(0.0)
    assert row["Worst Year Return %"] == pytest.approx(0.0)


def test_the_three_metrics_agree_with_an_independent_annual_returns_call():
    """Rebuild a strategy whose equity does move (a downward sawtooth that
    repeatedly triggers the grid), then check the controller's three
    metrics against annual_returns() applied directly to the SAME
    equity curve the run reports -- not a hand-derived expectation, a
    cross-check against the shared function under test elsewhere."""
    idx = pd.date_range("2020-01-02", periods=3 * 365 + 1, freq="D", tz="UTC")
    n = len(idx)
    # Saw-tooth: repeated gentle declines (triggering buys) with periodic
    # sharp recoveries (triggering harvests), so both trade types fire
    # and the equity curve is genuinely non-flat across all three years.
    t = np.arange(n)
    price = 100.0 + 20.0 * np.sin(t / 15.0) - 0.01 * t
    df = pd.DataFrame(
        {"open": price, "high": price + 0.5, "low": price - 0.5, "close": price}, index=idx
    )
    controller = OptimizationController(historical_data=df)

    summary, full_results = controller.run_sweep(
        grid_steps=[0.01],
        profit_targets=[0.03],
        strategy_class=FixedPortfolioPercentage,
        strategy_params_grid=[{"allocation_pct": 0.02}],
        return_full_results=True,
    )
    row = summary.iloc[0]
    assert row["Trade Count"] > 0  # otherwise this isn't exercising the interesting path

    equity = full_results[0].equity_curve
    expected = annual_returns(equity)

    assert row["Average Annual Return %"] == pytest.approx(expected.mean())
    assert row["Best Year Return %"] == pytest.approx(expected.max())
    assert row["Worst Year Return %"] == pytest.approx(expected.min())
    # And the ordering invariant that must hold for any non-degenerate series.
    assert row["Worst Year Return %"] <= row["Average Annual Return %"] <= row["Best Year Return %"]
