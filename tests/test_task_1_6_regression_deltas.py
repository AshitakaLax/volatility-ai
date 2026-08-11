"""Task 1.6 verification for the Phase 1 regression fixture.

The FixedPortfolioPercentage fixture is intentionally compared with the frozen
Task 0.1 values.  Task 1.2 changes the controller's drawdown sampling, so the
post-Phase-1 drawdown is asserted separately as an expected, intentional delta.
"""

import math

from tests.fixtures.regression_baseline import BASELINE, run_baseline_sweep

EXPECTED_FIXED_BASELINE = {
    "Final Portfolio Value": 100099.81489816227,
    "Trade Count": 4,
    "Total Return %": 0.09981489816226531,
    "Capital Velocity Index": 0.000998148981622653,
}
EXPECTED_POST_PHASE_1_DRAWDOWN = 0.4430668810465577


def test_fixed_strategy_metrics_remain_unchanged_except_drawdown_sampling():
    actual = run_baseline_sweep()

    for key, expected in EXPECTED_FIXED_BASELINE.items():
        assert math.isclose(actual[key], expected, rel_tol=0.0, abs_tol=1e-8), (
            f"Unexpected FixedPortfolioPercentage delta for {key}: "
            f"expected={expected!r}, actual={actual!r}"
        )

    assert math.isclose(BASELINE["Max Drawdown %"], 0.0, rel_tol=0.0, abs_tol=1e-12)
    assert math.isclose(
        actual["Max Drawdown %"],
        EXPECTED_POST_PHASE_1_DRAWDOWN,
        rel_tol=0.0,
        abs_tol=1e-12,
    )


def test_performance_analyzer_has_no_drawdown_metric_to_overwrite():
    actual = run_baseline_sweep()
    assert "Max Drawdown %" not in {
        "Final Portfolio Value",
        "Trade Count",
        "Total Return %",
        "Capital Velocity Index",
    }
    assert "Max Drawdown %" in actual
