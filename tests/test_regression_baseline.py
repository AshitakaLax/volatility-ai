"""
Task 0.1 -- regression test pinning OptimizationController.run_sweep's
CURRENT behavior on a small, fixed dataset.

This test is deliberately not asserting "correct" behavior, only
"unchanged" behavior -- optimization_controller.py has confirmed bugs
(B1-B5 in architecture_overview.md) that Phase 1 fixes intentionally.
Do not "fix" this test to match Phase 1's new output. Task 1.6
re-captures the baseline once Phase 1 lands and documents the deltas.
"""

import math

import pytest

from tests.fixtures.regression_baseline import BASELINE, run_baseline_sweep

# architecture_overview.md Section 2.2 "Money and quantities":
# MONEY_EPSILON = 1e-8. Reused here rather than inventing a new
# tolerance for this test.
MONEY_EPSILON = 1e-8

# Confirmed directly from optimization_controller.py source (not a
# guess): "Max Drawdown %" is assigned explicitly onto the metrics
# dict, and "Capital Velocity Index" is the column run_sweep() sorts
# its results by. Task 0.1's acceptance criteria also requires final
# equity and trade count in the baseline; those come from
# PerformanceAnalyzer.calculate_metrics(), whose exact column names
# were not confirmed against source at implementation time, so they
# are not asserted by name here -- but they are still covered, along
# with every other column, by the full-row comparison below.
REQUIRED_BASELINE_COLUMNS = ("Max Drawdown %", "Capital Velocity Index")


def _assert_matches_baseline(expected: dict, actual: dict) -> None:
    missing = set(expected) - set(actual)
    extra = set(actual) - set(expected)
    assert not missing, f"Baseline columns missing from fresh run: {sorted(missing)}"
    assert not extra, f"Fresh run produced columns not present in baseline: {sorted(extra)}"

    mismatches = []
    for key, expected_value in expected.items():
        actual_value = actual[key]
        both_numeric = isinstance(expected_value, (int, float)) and isinstance(actual_value, (int, float))
        if both_numeric:
            exp_nan = isinstance(expected_value, float) and math.isnan(expected_value)
            act_nan = isinstance(actual_value, float) and math.isnan(actual_value)
            if exp_nan or act_nan:
                if exp_nan and act_nan:
                    continue
                mismatches.append((key, expected_value, actual_value))
                continue
            if not math.isclose(actual_value, expected_value, rel_tol=0.0, abs_tol=MONEY_EPSILON):
                mismatches.append((key, expected_value, actual_value))
        elif actual_value != expected_value:
            mismatches.append((key, expected_value, actual_value))

    if mismatches:
        lines = [f"  {k}: baseline={exp!r} vs fresh={act!r}" for k, exp, act in mismatches]
        pytest.fail(
            "Regression detected -- run_sweep() output diverged from the Task 0.1 "
            "baseline:\n" + "\n".join(lines)
        )


def test_run_sweep_matches_pinned_baseline():
    if BASELINE is None:
        pytest.fail(
            "No baseline captured yet. Run `python -m tests.fixtures.regression_baseline` "
            "in an environment with the real src/ package on disk, then paste the printed "
            "dict in as BASELINE in tests/fixtures/regression_baseline.py."
        )

    for required_key in REQUIRED_BASELINE_COLUMNS:
        assert required_key in BASELINE, (
            f"Baseline is missing required column {required_key!r} -- Task 0.1's "
            "acceptance criteria requires it in the captured baseline."
        )

    fresh_result = run_baseline_sweep()
    _assert_matches_baseline(BASELINE, fresh_result)
