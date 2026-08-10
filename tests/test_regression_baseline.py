"""Task 0.1: pin the current pre-Phase-1 run_sweep behavior."""

import math

import pytest

from tests.fixtures.regression_baseline import BASELINE, run_baseline_sweep

MONEY_EPSILON = 1e-8
REQUIRED_BASELINE_COLUMNS = (
    "Final Portfolio Value",
    "Trade Count",
    "Max Drawdown %",
    "Capital Velocity Index",
)


def _assert_matches_baseline(expected: dict, actual: dict) -> None:
    missing = set(expected) - set(actual)
    extra = set(actual) - set(expected)
    assert not missing, f"Baseline columns missing from fresh run: {sorted(missing)}"
    assert not extra, f"Fresh run produced unexpected columns: {sorted(extra)}"

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
            elif not math.isclose(actual_value, expected_value, rel_tol=0.0, abs_tol=MONEY_EPSILON):
                mismatches.append((key, expected_value, actual_value))
        elif actual_value != expected_value:
            mismatches.append((key, expected_value, actual_value))

    if mismatches:
        details = "\n".join(
            f"  {key}: baseline={expected!r} vs fresh={actual!r}"
            for key, expected, actual in mismatches
        )
        pytest.fail("Task 0.1 regression detected:\n" + details)


def test_run_sweep_matches_pinned_baseline():
    for required_key in REQUIRED_BASELINE_COLUMNS:
        assert required_key in BASELINE, f"Baseline missing required metric: {required_key}"

    _assert_matches_baseline(BASELINE, run_baseline_sweep())
