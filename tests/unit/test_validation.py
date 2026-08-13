"""
Task 4.9 acceptance tests.

1. Every invalid boundary listed in the task has a focused test.
2. Valid minimum/maximum boundary values are accepted.
3. Validation runs before the first simulation or live order
   submission -- verified by confirming a bad config raises before
   any _simulate_single call happens.
"""

import pandas as pd
import pytest

from optimization_controller import OptimizationController
from src.exceptions import ConfigurationError
from src.size_calculators import FixedPortfolioPercentage
from src.validation import (
    validate_grid_steps,
    validate_non_negative,
    validate_one_of,
    validate_positive,
    validate_positive_int,
    validate_profit_targets,
    validate_run_sweep_config,
    validate_unit_interval,
)


def _load_fixture() -> pd.DataFrame:
    df = pd.read_csv("tests/fixtures/regression_ohlcv.csv", parse_dates=["timestamp"])
    df.set_index("timestamp", inplace=True)
    return df


def test_validate_positive_rejects_zero_and_negative():
    with pytest.raises(ConfigurationError, match="x"):
        validate_positive(0.0, "x")
    with pytest.raises(ConfigurationError, match="x"):
        validate_positive(-0.01, "x")


def test_validate_non_negative_rejects_negative_only():
    with pytest.raises(ConfigurationError):
        validate_non_negative(-0.01, "x")


def test_validate_unit_interval_rejects_outside_0_1():
    with pytest.raises(ConfigurationError):
        validate_unit_interval(-0.01, "x")
    with pytest.raises(ConfigurationError):
        validate_unit_interval(1.01, "x")


def test_validate_positive_int_rejects_zero_negative_and_non_int():
    with pytest.raises(ConfigurationError):
        validate_positive_int(0, "x")
    with pytest.raises(ConfigurationError):
        validate_positive_int(-1, "x")
    with pytest.raises(ConfigurationError):
        validate_positive_int(1.5, "x")


def test_validate_one_of_rejects_unlisted_value():
    with pytest.raises(ConfigurationError):
        validate_one_of("bogus", ("a", "b"), "x")


def test_validate_grid_steps_rejects_empty():
    with pytest.raises(ConfigurationError, match="empty"):
        validate_grid_steps([])


def test_validate_grid_steps_rejects_non_positive_entry():
    with pytest.raises(ConfigurationError):
        validate_grid_steps([0.01, 0.0])


def test_validate_grid_steps_rejects_100_percent_or_more_cross_field():
    with pytest.raises(ConfigurationError, match="grid strategy's semantics"):
        validate_grid_steps([1.0])
    with pytest.raises(ConfigurationError):
        validate_grid_steps([1.5])


def test_validate_profit_targets_rejects_empty_and_non_positive():
    with pytest.raises(ConfigurationError):
        validate_profit_targets([])
    with pytest.raises(ConfigurationError):
        validate_profit_targets([0.005, -0.001])


def test_validate_positive_accepts_small_positive():
    validate_positive(1e-9, "x")


def test_validate_unit_interval_accepts_0_and_1_inclusive():
    validate_unit_interval(0.0, "x")
    validate_unit_interval(1.0, "x")


def test_validate_positive_int_accepts_1():
    validate_positive_int(1, "x")


def test_validate_grid_steps_accepts_value_just_under_1():
    validate_grid_steps([0.9999999])


def test_validate_one_of_accepts_listed_value():
    validate_one_of("a", ("a", "b"), "x")


def test_validate_run_sweep_config_accepts_valid_input():
    validate_run_sweep_config(
        grid_steps=[0.01], profit_targets=[0.005], n_jobs=1,
        on_flat_reentry="stale_reference", initial_cash=100_000.0,
    )


@pytest.mark.parametrize(
    "kwargs",
    [
        dict(grid_steps=[]),
        dict(profit_targets=[]),
        dict(n_jobs=0),
        dict(on_flat_reentry="bogus"),
        dict(initial_cash=0.0),
        dict(initial_cash=-1.0),
    ],
)
def test_validate_run_sweep_config_rejects_each_invalid_field(kwargs):
    base = dict(grid_steps=[0.01], profit_targets=[0.005], n_jobs=1, on_flat_reentry="stale_reference", initial_cash=100_000.0)
    base.update(kwargs)
    with pytest.raises(ConfigurationError):
        validate_run_sweep_config(**base)


def test_run_sweep_rejects_bad_config_before_any_simulation_runs(monkeypatch):
    df = _load_fixture()
    controller = OptimizationController(historical_data=df)

    called = {"count": 0}
    original = OptimizationController._simulate_single

    def spy(self, *args, **kwargs):
        called["count"] += 1
        return original(self, *args, **kwargs)

    monkeypatch.setattr(OptimizationController, "_simulate_single", spy)

    with pytest.raises(ConfigurationError):
        controller.run_sweep(
            grid_steps=[0.01],
            profit_targets=[0.005],
            strategy_class=FixedPortfolioPercentage,
            strategy_params_grid=[{"allocation_pct": 0.05}],
            n_jobs=0,
        )
    assert called["count"] == 0, "_simulate_single must not run when config validation fails"


def test_run_sweep_with_valid_config_matches_baseline():
    from tests.fixtures.regression_baseline import BASELINE

    df = _load_fixture()
    row = OptimizationController(historical_data=df).run_sweep(
        grid_steps=[BASELINE["Grid Step"]],
        profit_targets=[BASELINE["Profit Target"]],
        strategy_class=FixedPortfolioPercentage,
        strategy_params_grid=[{"allocation_pct": BASELINE["allocation_pct"]}],
    ).iloc[0]
    for key, expected in BASELINE.items():
        assert row[key] == expected
