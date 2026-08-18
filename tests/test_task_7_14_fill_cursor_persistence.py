from src.persistence import SQLiteStateStore


def test_fill_cursor_survives_restart(tmp_path):
    path = tmp_path / "state.db"
    store = SQLiteStateStore(path)
    try:
        store.save_fill_cursor("sell-1", 4.0, 420.0)
    finally:
        store.close()

    restarted = SQLiteStateStore(path)
    try:
        assert restarted.load_fill_cursor("sell-1") == (4.0, 420.0)
    finally:
        restarted.close()


def test_fill_cursor_update_is_idempotent(tmp_path):
    store = SQLiteStateStore(tmp_path / "state.db")
    try:
        store.save_fill_cursor("sell-1", 4.0, 420.0)
        store.save_fill_cursor("sell-1", 10.0, 1050.0)
        assert store.load_fill_cursor("sell-1") == (10.0, 1050.0)
    finally:
        store.close()
