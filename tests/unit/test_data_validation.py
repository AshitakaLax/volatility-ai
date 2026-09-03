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


# --- the report: making the >15% finding reachable by callers ---


def _frame(closes):
    return pd.DataFrame(
        {"close": closes},
        index=pd.date_range("2024-01-01", periods=len(closes), freq="D", tz="UTC"),
    )


def test_clean_data_reports_no_suspect_bars():
    report = validate(_frame([100.0, 101.0, 100.5, 102.0]))
    assert report.has_suspect_bars is False
    assert report.suspect_bars == ()


def test_a_large_move_is_returned_not_merely_logged():
    """THE point of the report. Before this, the only output was a log
    line, so a caller could not ask 'did anything look unadjusted?',
    count it, record it, or refuse to proceed."""
    report = validate(_frame([100.0, 101.0, 50.0, 51.0]))
    assert report.has_suspect_bars is True
    assert len(report.suspect_bars) == 1
    timestamp, change = report.suspect_bars[0]
    assert timestamp == pd.Timestamp("2024-01-03", tz="UTC")
    assert change == pytest.approx(-0.5050, abs=1e-4)


def test_the_sign_is_preserved_because_direction_is_diagnostic():
    """A split is a single large NEGATIVE step; a crash or squeeze goes
    either way. Taking the absolute value discarded the cheapest signal
    for telling them apart."""
    down = validate(_frame([100.0, 50.0, 50.0]))
    up = validate(_frame([100.0, 200.0, 200.0]))
    assert down.suspect_bars[0][1] < 0
    assert up.suspect_bars[0][1] > 0


def test_a_large_move_still_does_not_raise():
    """It can be a genuine event -- COVID, Brexit, a yen-carry unwind --
    so rejecting real data outright would be worse than flagging it.
    Returning a value must not have quietly turned this fatal."""
    frame = _frame([100.0, 30.0, 31.0])
    report = validate(frame)  # must not raise
    assert report.has_suspect_bars is True


def test_describe_renders_timestamps_and_magnitudes():
    """'3 bars moved >15%' is not actionable; the values are what let a
    human tell a split from a crash."""
    text = validate(_frame([100.0, 50.0, 100.0, 50.0])).describe()
    assert "2024-01-02" in text
    assert "%" in text
    assert "-" in text and "+" in text


def test_describe_truncates_a_systematically_broken_dataset():
    closes = [100.0]
    for _ in range(20):
        closes.extend([50.0, 100.0])
    text = validate(_frame(closes)).describe(limit=3)
    assert "more)" in text
    assert text.count(";") == 2, "should show exactly `limit` entries"


def test_every_flagged_bar_is_reported_not_just_the_first():
    report = validate(_frame([100.0, 50.0, 100.0, 50.0, 100.0]))
    assert len(report.suspect_bars) == 4


def test_the_threshold_is_configurable_and_respected():
    closes = [100.0, 108.0, 108.0]  # +8%
    assert validate(_frame(closes)).has_suspect_bars is False
    assert validate(_frame(closes), warn_on_gap_pct=0.05).has_suspect_bars is True
