import pandas as pd
import pytest

from src.data_validation import DataValidationError, validate


def _df(closes, start="2024-01-01"):
    idx = pd.date_range(start, periods=len(closes), freq="D", tz="UTC")
    return pd.DataFrame({"close": closes}, index=idx)


def test_empty_frame_rejected():
    with pytest.raises(DataValidationError, match="empty"):
        validate(pd.DataFrame())


def test_missing_close_column_rejected():
    idx = pd.date_range("2024-01-01", periods=3, freq="D", tz="UTC")
    df = pd.DataFrame({"open": [1.0, 2.0, 3.0]}, index=idx)
    with pytest.raises(DataValidationError, match="missing required columns"):
        validate(df)


def test_nan_close_rejected():
    df = _df([100.0, float("nan"), 102.0])
    with pytest.raises(DataValidationError, match="NaN/inf"):
        validate(df)


def test_inf_close_rejected():
    df = _df([100.0, float("inf"), 102.0])
    with pytest.raises(DataValidationError, match="NaN/inf"):
        validate(df)


def test_negative_close_rejected():
    df = _df([100.0, -5.0, 102.0])
    with pytest.raises(DataValidationError, match="non-positive"):
        validate(df)


def test_zero_close_rejected():
    df = _df([100.0, 0.0, 102.0])
    with pytest.raises(DataValidationError, match="non-positive"):
        validate(df)


def test_duplicate_timestamp_rejected():
    idx = pd.to_datetime(["2024-01-01", "2024-01-02", "2024-01-02"], utc=True)
    df = pd.DataFrame({"close": [100.0, 101.0, 102.0]}, index=idx)
    with pytest.raises(DataValidationError, match="duplicate timestamps"):
        validate(df)


def test_descending_timestamp_rejected():
    idx = pd.to_datetime(["2024-01-03", "2024-01-02", "2024-01-01"], utc=True)
    df = pd.DataFrame({"close": [100.0, 101.0, 102.0]}, index=idx)
    with pytest.raises(DataValidationError, match="not sorted ascending"):
        validate(df)


def test_valid_large_move_warns_but_does_not_raise(caplog):
    # 100 -> 130 is a 30% single-bar jump, above the default 15% threshold.
    df = _df([100.0, 130.0, 131.0])
    with caplog.at_level("WARNING", logger="Optimizer"):
        validate(df)  # must not raise
    assert any("single-bar move" in record.message for record in caplog.records)


def test_valid_normal_data_succeeds_silently(caplog):
    df = _df([100.0, 100.5, 99.8, 101.2, 100.9])
    with caplog.at_level("WARNING", logger="Optimizer"):
        validate(df)
    assert caplog.records == []


def test_error_message_identifies_offending_index():
    df = _df([100.0, float("nan"), 102.0])
    with pytest.raises(DataValidationError) as exc_info:
        validate(df)
    assert str(df.index[1]) in str(exc_info.value) or "2024-01-02" in str(exc_info.value)
