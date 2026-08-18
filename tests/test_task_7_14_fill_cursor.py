from src.fill_cursor import FillCursor
from src.persistence import SQLiteStateStore
from src.exceptions import ReconciliationError


def test_fill_cursor_survives_restart(tmp_path):
    path = tmp_path / "state.db"
    store = SQLiteStateStore(path)
    cursor = FillCursor()
    try:
        assert cursor.delta(4.0, 420.0) == (4.0, 420.0)
        cursor.advance(4.0, 420.0)
        cursor.persist(store, "sell-1")
    finally:
        store.close()

    store = SQLiteStateStore(path)
    try:
        restored = FillCursor.load(store, "sell-1")
        assert restored.cumulative_qty == 4.0
        assert restored.cumulative_notional == 420.0
        assert restored.delta(10.0, 1050.0) == (6.0, 630.0)
    finally:
        store.close()


def test_fill_cursor_rejects_regression():
    cursor = FillCursor(cumulative_qty=4.0, cumulative_notional=420.0)
    try:
        cursor.delta(3.0, 315.0)
    except ReconciliationError:
        pass
    else:
        raise AssertionError("cumulative broker fill regression must be rejected")


def test_fill_cursor_duplicate_is_zero_delta():
    cursor = FillCursor(cumulative_qty=4.0, cumulative_notional=420.0)
    assert cursor.delta(4.0, 420.0) == (0.0, 0.0)
