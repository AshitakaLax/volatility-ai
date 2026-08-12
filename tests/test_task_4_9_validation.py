import pytest

from src.exceptions import ConfigurationError
from src.validation import (
    validate_exposure_pct,
    validate_grid_relationship,
    validate_mode,
    validate_positive,
    validate_positive_int,
    validate_sweep_config,
)


def test_positive_and_non_negative_boundaries():
    assert validate_positive("price", 0.01) == pytest.approx(0.01)
    assert validate_exposure_pct("exposure_pct", 0.0) == 0.0
    assert validate_exposure_pct("exposure_pct", 1.0) == 1.0
    assert validate_positive_int("lot_limit", 1) == 1


def test_invalid_numeric_boundaries_name_field_and_value():
    with pytest.raises(ConfigurationError, match=r"price.*0"):
        validate_positive("price", 0)
    with pytest.raises(ConfigurationError, match=r"exposure_pct.*1\.1"):
        validate_exposure_pct("exposure_pct", 1.1)
    with pytest.raises(ConfigurationError, match=r"n_jobs.*0"):
        validate_positive_int("n_jobs", 0)


def test_grid_target_must_exceed_grid_step():
    assert validate_grid_relationship(0.01, 0.02) == (0.01, 0.02)
    with pytest.raises(ConfigurationError, match="profit_target"):
        validate_grid_relationship(0.02, 0.02)


def test_mode_validation_is_explicit_and_pure():
    assert validate_mode("search_mode", "grid", ["grid", "random"]) == "grid"
    with pytest.raises(ConfigurationError, match="search_mode"):
        validate_mode("search_mode", "unknown", ["grid", "random"])


def test_sweep_validation_rejects_before_execution():
    with pytest.raises(ConfigurationError, match="grid_step"):
        validate_sweep_config(
            grid_steps=[0.0],
            profit_targets=[0.02],
            n_jobs=1,
            initial_cash=100_000,
        )


def test_sweep_validation_accepts_valid_boundaries():
    validate_sweep_config(
        grid_steps=[0.01],
        profit_targets=[0.02],
        n_jobs=1,
        initial_cash=100_000,
        max_concurrent_lots=1,
        max_total_exposure=1.0,
    )
