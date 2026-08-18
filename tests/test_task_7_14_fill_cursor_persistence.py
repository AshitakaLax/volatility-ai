from src.persistence import SQLiteStateStore


def test_fill_cursor_survives_restart(tmp_path):
    path = tmp_path / "state.db"
    store = SQLiteStateStore(path)
    assert store.save_fill_cursor("order-1", 4.0, 420.0) > 0
    assert store.load_fill_cursor("order-1") == (4.0, 420.0)
    store.close()

    restarted = SQLiteStateStore(path)
    try:
        assert restarted.load_fill_cursor("order-1") == (4.0, 420.0)
        assert restarted.load_fill_cursors() == {"order-1": (4.0, 420.0)}
    finally:
        restarted.close()


def test_non_fill_order_state_is_not_misread_as_fill_cursor(tmp_path):
    path = tmp_path / "state.db"
    store = SQLiteStateStore(path)
    try:
        with store._conn:
            revision = store._next_revision(store._conn)
            store._conn.execute(
                "INSERT INTO order_state(order_id,payload,revision,schema_version) VALUES (?,?,?,?)",
                ("order-2", '{"type":"other","schema_version":1}', revision, 3),
            )
        assert store.load_fill_cursor("order-2") is None
        assert "order-2" not in store.load_fill_cursors()
    finally:
        store.close()
