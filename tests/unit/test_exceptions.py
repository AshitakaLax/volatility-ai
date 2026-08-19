"""
Task 4.8 dedicated tests.

Acceptance criteria:
1. Tests can distinguish configuration, data, execution,
   reconciliation, and persistence failures without matching
   error-message strings.
2. Existing successful behavior is unchanged.
3. Wrapped lower-level exceptions remain inspectable through
   exception chaining.
"""

import pytest

from src.data_validation import DataValidationError, validate
from src.exceptions import (
    ConfigurationError,
    ExecutionError,
    PersistenceError,
    ReconciliationError,
    RiskError,
    StrategyError,
    TradingSystemError,
)
from src.exceptions import (
    DataValidationError as CanonicalDataValidationError,
)
from src.order_management_system import OrderManagementSystem
from src.size_calculators import FixedPortfolioPercentage


def test_all_seven_domain_exceptions_descend_from_the_common_root():
    for cls in (
        ConfigurationError,
        CanonicalDataValidationError,
        StrategyError,
        RiskError,
        ExecutionError,
        ReconciliationError,
        PersistenceError,
    ):
        assert issubclass(cls, TradingSystemError)


def test_distinguishable_by_type_not_message_string():
    # Two different domain exceptions can carry the exact same message
    # -- callers must be able to tell them apart by type alone.
    same_message = "invalid input"
    config_err = ConfigurationError(same_message)
    risk_err = RiskError(same_message)
    assert str(config_err) == str(risk_err) == same_message
    assert type(config_err) is not type(risk_err)
    assert isinstance(config_err, ConfigurationError) and not isinstance(config_err, RiskError)
    assert isinstance(risk_err, RiskError) and not isinstance(risk_err, ConfigurationError)


def test_data_validation_error_is_now_the_canonical_domain_exception():
    # src/data_validation.py's DataValidationError must be the exact
    # same class as src/exceptions.py's -- not a second, differently-
    # named lookalike -- so `except DataValidationError` (from either
    # import path) or `except TradingSystemError` both work.
    assert DataValidationError is CanonicalDataValidationError
    assert issubclass(DataValidationError, TradingSystemError)


def test_data_validation_error_still_raised_for_bad_data():
    import pandas as pd

    with pytest.raises(DataValidationError):
        validate(pd.DataFrame())


def test_configuration_error_raised_for_bad_allocation_pct():
    with pytest.raises(ConfigurationError):
        FixedPortfolioPercentage(allocation_pct=-1.0)


def test_configuration_error_raised_for_bad_oms_mode():
    with pytest.raises(ConfigurationError):
        OrderManagementSystem(mode="NOT_A_REAL_MODE")


def test_wrapped_exception_preserves_cause_for_chaining():
    original = KeyError("missing_field")
    try:
        try:
            raise original
        except KeyError as e:
            raise ConfigurationError("could not build config") from e
    except ConfigurationError as wrapped:
        assert wrapped.__cause__ is original
        assert isinstance(wrapped.__cause__, KeyError)
        assert str(wrapped.__cause__) == "'missing_field'"


def test_all_domain_exceptions_support_chaining_uniformly():
    for cls in (
        ConfigurationError,
        StrategyError,
        RiskError,
        ExecutionError,
        ReconciliationError,
        PersistenceError,
    ):
        original = ValueError("root cause")
        try:
            try:
                raise original
            except ValueError as e:
                raise cls("wrapped") from e
        except cls as wrapped:
            assert wrapped.__cause__ is original


def test_existing_successful_behavior_unchanged():
    # Valid inputs must still succeed with no exception, for the sites
    # touched by this task.
    FixedPortfolioPercentage(allocation_pct=0.5)  # doesn't raise
    OrderManagementSystem(mode="SIMULATION")  # doesn't raise
    # Task 7.7 made LIVE construction require passing promotion evidence,
    # so PAPER is the non-capital mode that stands in here now.
    OrderManagementSystem(mode="PAPER")  # doesn't raise
