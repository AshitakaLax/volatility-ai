import pytest

from src.data_validation import validate
from src.exceptions import (
    ConfigurationError,
    DataValidationError,
    ExecutionError,
    PersistenceError,
    ReconciliationError,
    RiskError,
    StrategyError,
    TradingSystemError,
)


def test_domain_exceptions_form_stable_hierarchy():
    for exc_type in (
        ConfigurationError,
        DataValidationError,
        StrategyError,
        RiskError,
        ExecutionError,
        ReconciliationError,
        PersistenceError,
    ):
        assert issubclass(exc_type, TradingSystemError)


def test_data_validation_exposes_domain_type_without_message_matching():
    with pytest.raises(DataValidationError) as caught:
        validate(None)
    assert isinstance(caught.value, TradingSystemError)


def test_exception_chaining_preserves_original_cause():
    original = RuntimeError("underlying broker failure")
    with pytest.raises(ExecutionError) as caught:
        try:
            raise original
        except RuntimeError as exc:
            raise ExecutionError("order execution failed") from exc
    assert caught.value.__cause__ is original


def test_successful_data_validation_remains_unchanged():
    import pandas as pd

    data = pd.DataFrame(
        {"close": [100.0, 101.0]},
        index=pd.date_range("2024-01-01", periods=2),
    )
    validate(data)
