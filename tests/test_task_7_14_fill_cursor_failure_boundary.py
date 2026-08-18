import pytest

from src.fill_cursor import FillCursor


def test_task_7_14_cursor_does_not_advance_before_successful_mutation():
    cursor = FillCursor()

    # The cursor represents the broker's durable cumulative observation.  A
    # caller must only advance it after the corresponding ledger mutation has
    # succeeded.  Simulate a failed mutation by deliberately not advancing.
    new_qty, new_notional = cursor.delta(4.0, 420.0)
    assert (new_qty, new_notional) == (4.0, 420.0)
    assert cursor.cumulative_qty == 0.0
    assert cursor.cumulative_notional == 0.0

    # Retrying the same broker observation must therefore still produce the
    # complete delta rather than silently losing the fill.
    retry_qty, retry_notional = cursor.delta(4.0, 420.0)
    assert (retry_qty, retry_notional) == (4.0, 420.0)

    cursor.advance(4.0, 420.0)
    assert cursor.delta(4.0, 420.0) == (0.0, 0.0)


def test_task_7_14_cursor_rejects_regression_before_mutation():
    cursor = FillCursor(10.0, 1050.0)

    with pytest.raises(ValueError):
        cursor.delta(9.0, 945.0)

    # A rejected observation must not alter the durable cursor state.
    assert cursor.cumulative_qty == 10.0
    assert cursor.cumulative_notional == 1050.0
