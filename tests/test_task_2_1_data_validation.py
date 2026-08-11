import logging

import pandas as pd
import pytest

from optimization_controller import OptimizationController
from src.data_validation import DataValidationError, validate


def frame(closes, index=None):
    if index is None:
        index = pd.date_range("2024-01-01", periods=len(closes), freq="D")
    return pd.DataFrame({"close": closes}, index=index)


def test_rejects_empty_frame():
    with pytest.raises(DataValidationError, match="empty"):
        validate(pd.DataFrame(columns=["close"]))


def test_rejects_missing_close():
    with pytest.raises(DataValidationError, match="missing required columns"):
        validate(pd.DataFrame({"open": [1.0]}))


def test_rejects_nan_close():
    with pytest.raises(DataValidationError, match="NaN"):
        validate(frame([100.0, float("nan")]))


def test_rejects_unsorted_index():
    index = pd.to_datetime(["2024-01-02", "2024-01-01"])
    with pytest.raises(DataValidationError, match="not sorted"):
        validate(frame([100.0, 99.0], index=index))


def test_rejects_duplicate_timestamps():
    index = pd.to_datetime(["2024-01-01", "2024-01-01"])
    with pytest.raises(DataValidationError, match="duplicate"):
        validate(frame([100.0, 99.0], index=index))


def test_warns_on_large_single_bar_move(caplog):
    with caplog.at_level(logging.WARNING, logger="Optimizer"):
        validate(frame([100.0, 120.0]))
    assert ">15%" in caplog.text


def test_controller_validates_before_storing_data():
    bad = frame([100.0, float("nan")])
    with pytest.raises(DataValidationError):
        OptimizationController(bad)
