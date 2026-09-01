"""
Task 7.3 acceptance tests (L2).

1. The implementation uses the canonical SQLite backend and exposes
   the required minimum tables/records.
2. Simulating a process restart mid-run reconstructs the exact same
   open-lot state that existed before the restart.
3. A deliberately corrupted/mismatched persistent store (vs. the
   broker's real positions) is detected and surfaced rather than
   silently trusted.
"""

import sqlite3

import pytest

from src.exceptions import PersistenceError, ReconciliationError
from src.ledger import AssetLotLedger
from src.persistence import SCHEMA_VERSION, LedgerStore


@pytest.fixture
def db_path(tmp_path):
    return str(tmp_path / "ledger.db")


def _seed(store: LedgerStore):
    """Two lots: one partially closed (6 of 10 remaining), one fully
    closed. Returns the in-memory ledger for before/after comparison."""
    ledger = AssetLotLedger()
    l1 = ledger.register_buy("o1", "TQQQ", 50.0, 10.0, 0.01)
    store.record_open_lot(l1)
    l2 = ledger.register_buy("o2", "TQQQ", 48.0, 20.0, 0.01)
    store.record_open_lot(l2)
    ledger.close_lot(l1, sell_qty=4.0)
    store.sync_lot(ledger, l1)
    ledger.close_lot(l2)
    store.sync_lot(ledger, l2)
    store.save_last_buy_price(48.0)
    return ledger


def test_uses_sqlite_and_creates_the_required_minimum_tables(db_path):
    with LedgerStore(db_path):
        pass
    conn = sqlite3.connect(db_path)
    tables = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    conn.close()
    for required in ("ledger_lots", "revisions", "processed_events"):
        assert required in tables, f"Minimum persistence schema is missing {required}"


def test_every_durable_record_carries_a_schema_version(db_path):
    with LedgerStore(db_path) as store:
        _seed(store)
        store.record_processed_event("evt-1")
        conn = store._conn
        for table in ("ledger_lots", "revisions", "processed_events"):
            rows = conn.execute(f"SELECT schema_version FROM {table}").fetchall()
            assert rows, f"{table} has no rows to check"
            assert all(r["schema_version"] == SCHEMA_VERSION for r in rows)


def test_revisions_are_monotonically_increasing(db_path):
    with LedgerStore(db_path) as store:
        _seed(store)
        revisions = [
            r["revision"]
            for r in store._conn.execute("SELECT revision FROM revisions ORDER BY rowid")
        ]
        assert revisions == sorted(revisions)
        assert len(set(revisions)) == len(revisions)
        assert store.current_revision() == max(revisions)


def test_correctness_does_not_depend_on_wal_mode(db_path):
    # The default journal mode is used; recovery must work regardless.
    with LedgerStore(db_path) as store:
        mode = store._conn.execute("PRAGMA journal_mode").fetchone()[0]
        _seed(store)
    with LedgerStore(db_path) as store2:
        assert len(store2.load_ledger().open_lots) == 1
    assert mode is not None


def test_restart_reconstructs_the_exact_open_lot_state(db_path):
    store = LedgerStore(db_path)
    ledger = _seed(store)
    before_open = sorted((lot_.order_id, lot_.shares) for lot_ in ledger.open_lots)
    before_closed = sorted(lot_.order_id for lot_ in ledger.closed_lots)
    store.close()  # simulate process death

    store2 = LedgerStore(db_path)  # fresh process, same store
    recovered = store2.load_ledger()
    after_open = sorted((lot_.order_id, lot_.shares) for lot_ in recovered.open_lots)
    after_closed = sorted(lot_.order_id for lot_ in recovered.closed_lots)
    store2.close()

    assert after_open == before_open
    assert after_closed == before_closed


def test_restart_preserves_cost_basis_and_target_sell_price(db_path):
    store = LedgerStore(db_path)
    ledger = _seed(store)
    original = {
        lot_.order_id: (lot_.buy_price, lot_.target_sell_price) for lot_ in ledger.open_lots
    }
    store.close()

    with LedgerStore(db_path) as store2:
        for lot in store2.load_ledger().open_lots:
            assert (lot.buy_price, lot.target_sell_price) == original[lot.order_id]


def test_restart_restores_last_buy_price(db_path):
    store = LedgerStore(db_path)
    _seed(store)
    store.close()
    with LedgerStore(db_path) as store2:
        assert store2.load_last_buy_price() == pytest.approx(48.0)


def test_recovery_is_idempotent(db_path):
    with LedgerStore(db_path) as store:
        _seed(store)
        first = [(lot_.order_id, lot_.shares) for lot_ in store.load_ledger().open_lots]
        second = [(lot_.order_id, lot_.shares) for lot_ in store.load_ledger().open_lots]
        third = [(lot_.order_id, lot_.shares) for lot_ in store.load_ledger().open_lots]
        assert first == second == third


def test_replaying_a_processed_event_creates_no_second_mutation(db_path):
    with LedgerStore(db_path) as store:
        assert store.record_processed_event("evt-1", "buy_fill") is True
        assert store.record_processed_event("evt-1", "buy_fill") is False
        count = store._conn.execute(
            "SELECT COUNT(*) AS c FROM processed_events WHERE event_id = 'evt-1'"
        ).fetchone()["c"]
        assert count == 1
        assert store.has_processed("evt-1")
        assert not store.has_processed("evt-never-seen")


def test_processed_events_survive_a_restart(db_path):
    store = LedgerStore(db_path)
    store.record_processed_event("evt-1")
    store.close()
    with LedgerStore(db_path) as store2:
        assert store2.has_processed("evt-1")
        assert store2.record_processed_event("evt-1") is False


def test_lot_mutation_and_its_revision_commit_atomically(db_path):
    with LedgerStore(db_path) as store:
        ledger = AssetLotLedger()
        lot = ledger.register_buy("o1", "TQQQ", 50.0, 10.0, 0.01)
        store.record_open_lot(lot)
        revisions_before = store.current_revision()

        # Updating a lot that isn't persisted must roll the whole
        # transaction back -- no orphan revision row left behind.
        orphan = ledger.register_buy("never-persisted", "TQQQ", 50.0, 5.0, 0.01)
        with pytest.raises(PersistenceError):
            store.record_lot_shares(orphan, is_open=True)
        assert store.current_revision() == revisions_before


def test_updating_an_unknown_lot_is_rejected(db_path):
    with LedgerStore(db_path) as store:
        ledger = AssetLotLedger()
        lot = ledger.register_buy("ghost", "TQQQ", 50.0, 5.0, 0.01)
        with pytest.raises(PersistenceError, match="No persisted lot"):
            store.record_lot_shares(lot, is_open=True)


def test_matching_broker_positions_reconcile_cleanly(db_path):
    with LedgerStore(db_path) as store:
        _seed(store)
        report = store.compare_with_broker({"TQQQ": 6.0})
        assert report.agrees
        report.raise_if_mismatched()  # must not raise


def test_quantity_mismatch_is_detected_and_surfaced(db_path):
    with LedgerStore(db_path) as store:
        _seed(store)
        report = store.compare_with_broker({"TQQQ": 99.0})
        assert not report.agrees
        assert report.quantity_mismatches["TQQQ"] == {"local": 6.0, "broker": 99.0}
        with pytest.raises(ReconciliationError, match="disagrees"):
            report.raise_if_mismatched()


def test_position_present_at_broker_but_absent_locally_is_detected(db_path):
    with LedgerStore(db_path) as store:
        _seed(store)
        report = store.compare_with_broker({"TQQQ": 6.0, "SPXL": 10.0})
        assert not report.agrees
        assert report.missing_locally == {"SPXL": 10.0}


def test_position_held_locally_but_absent_at_broker_is_detected(db_path):
    with LedgerStore(db_path) as store:
        _seed(store)
        report = store.compare_with_broker({})
        assert not report.agrees
        assert report.missing_at_broker == {"TQQQ": 6.0}


def test_reconciliation_never_mutates_either_side(db_path):
    with LedgerStore(db_path) as store:
        _seed(store)
        revision_before = store.current_revision()
        before = [(lot_.order_id, lot_.shares) for lot_ in store.load_ledger().open_lots]
        store.compare_with_broker({"TQQQ": 99.0})
        after = [(lot_.order_id, lot_.shares) for lot_ in store.load_ledger().open_lots]
        assert before == after
        assert store.current_revision() == revision_before


def test_corrupted_target_sell_price_is_detected_on_load(db_path):
    # Deliberately corrupt the store so persisted target_sell_price no
    # longer agrees with buy_price/profit_target.
    with LedgerStore(db_path) as store:
        _seed(store)
        store._conn.execute(
            "UPDATE ledger_lots SET target_sell_price = 999.0 WHERE order_id = 'o1'"
        )
        store._conn.commit()
        with pytest.raises(PersistenceError, match="disagrees"):
            store.load_ledger()


def test_a_restored_ledger_reports_the_right_share_total(tmp_path):
    """The LIVE-path safety property for the incremental share total.

    load_ledger populates open_lots by direct append, bypassing
    register_buy, so the ledger's running total never sees any of it.
    Without the explicit resync load_ledger calls, a restarted live
    daemon would mark its entire book to market as ZERO -- reporting no
    exposure while holding real positions, which is materially worse
    than a slow backtest.

    Tested end to end through the real store rather than by calling
    resync directly, because the bug would be a MISSING call, and a
    direct test of resync cannot catch that.
    """
    store = LedgerStore(str(tmp_path / "ledger.db"))
    ledger = AssetLotLedger()

    a = ledger.register_buy("A", "TQQQ", 100.0, 2.0, 0.05)
    store.record_open_lot(a)
    b = ledger.register_buy("B", "TQQQ", 101.0, 3.5, 0.05)
    store.record_open_lot(b)
    c = ledger.register_buy("C", "TQQQ", 102.0, 1.0, 0.05)
    store.record_open_lot(c)
    ledger.close_lot(c, completed=True)
    store.record_lot_shares(c, is_open=False)

    restored = store.load_ledger()
    recomputed = sum(lot.shares for lot in restored.open_lots)

    assert len(restored.open_lots) == 2
    assert recomputed == pytest.approx(5.5)
    assert restored.total_open_shares == pytest.approx(recomputed), (
        "restored ledger's running share total disagrees with its own lots -- "
        "load_ledger is not resyncing"
    )
    assert restored.total_open_shares == pytest.approx(ledger.total_open_shares)


def test_a_restored_ledger_with_a_partially_filled_lot_totals_correctly(tmp_path):
    """Partial closes mutate lot.shares in place, so the persisted value
    is the REMAINDER. The restored total must reflect that, not the
    original size."""
    store = LedgerStore(str(tmp_path / "ledger.db"))
    ledger = AssetLotLedger()
    lot = ledger.register_buy("A", "TQQQ", 100.0, 4.0, 0.05)
    store.record_open_lot(lot)
    ledger.close_lot(lot, sell_qty=1.5, completed=False)
    store.record_lot_shares(lot, is_open=True)

    restored = store.load_ledger()
    assert restored.total_open_shares == pytest.approx(2.5)
    assert restored.total_open_shares == pytest.approx(
        sum(lot.shares for lot in restored.open_lots)
    )
