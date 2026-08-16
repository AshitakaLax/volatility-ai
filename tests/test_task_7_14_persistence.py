import sqlite3
import tempfile
from pathlib import Path

import pytest

from src.audit import AuditEvent, generate_event_id
from src.exceptions import PersistenceError
from src.persistence import SQLiteStateStore


def make_event(event_id: str, sequence: int = 0, payload=None) -> AuditEvent:
    return AuditEvent(
        event_id=event_id,
        timestamp="2026-01-01T12:00:00Z",
        event_type="TEST_EVENT",
        schema_version=1,
        deployment_id="dep123",
        payload=payload if payload is not None else {"key": "value"},
        sequence=sequence,
    )


def test_audit_event_persistence():
    with tempfile.TemporaryDirectory() as temp_dir:
        db_path = Path(temp_dir) / "test.db"
        store = SQLiteStateStore(db_path)
        event = make_event(generate_event_id())

        rev = store.record_audit(event)

        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        row = conn.execute(
            "SELECT * FROM audit_events WHERE event_id=?", (event.event_id,)
        ).fetchone()

        assert rev > 0
        assert row is not None
        assert row["sequence"] == 1
        assert row["timestamp"] == "2026-01-01T12:00:00Z"
        assert row["deployment_id"] == "dep123"
        assert row["event_type"] == "TEST_EVENT"

        conn.close()
        store.close()


def test_duplicate_events_are_idempotent():
    with tempfile.TemporaryDirectory() as temp_dir:
        store = SQLiteStateStore(Path(temp_dir) / "test.db")
        event = make_event("SIM-000001")

        first = store.record_audit(event)
        second = store.record_audit(event)

        assert first == second
        assert len(store.load_audit_events()) == 1
        store.close()


def test_conflicting_duplicate_event_is_rejected_without_overwrite():
    with tempfile.TemporaryDirectory() as temp_dir:
        store = SQLiteStateStore(Path(temp_dir) / "test.db")
        store.record_audit(make_event("SIM-000001", payload={"value": 1}))

        with pytest.raises(PersistenceError):
            store.record_audit(make_event("SIM-000001", payload={"value": 2}))

        assert store.load_audit_events()[0].payload == {"value": 1}
        store.close()


def test_audit_sequence_order_survives_restart():
    with tempfile.TemporaryDirectory() as temp_dir:
        db_path = Path(temp_dir) / "test.db"
        store = SQLiteStateStore(db_path)
        for idx in range(1, 4):
            store.record_audit(make_event(f"SIM-{idx:06d}"))
        store.close()

        reopened = SQLiteStateStore(db_path)
        events = reopened.load_audit_events()
        assert [event.sequence for event in events] == [1, 2, 3]
        assert [event.event_id for event in events] == [
            "SIM-000001", "SIM-000002", "SIM-000003"
        ]
        reopened.close()


def test_explicit_sequence_must_be_next_in_stream():
    with tempfile.TemporaryDirectory() as temp_dir:
        store = SQLiteStateStore(Path(temp_dir) / "test.db")
        store.record_audit(make_event("SIM-000001", sequence=1))
        with pytest.raises(PersistenceError):
            store.record_audit(make_event("SIM-000002", sequence=3))
        store.close()


def test_audit_payload_round_trips_as_json():
    with tempfile.TemporaryDirectory() as temp_dir:
        store = SQLiteStateStore(Path(temp_dir) / "test.db")
        payload = {"decision_id": "d1", "parameters": {"allocation_pct": 0.01}}
        store.record_audit(make_event("SIM-000001", payload=payload))
        assert store.load_audit_events()[0].payload == payload
        store.close()


def test_legacy_audit_rows_survive_schema_upgrade():
    with tempfile.TemporaryDirectory() as temp_dir:
        db_path = Path(temp_dir) / "legacy.db"
        conn = sqlite3.connect(db_path)
        conn.executescript(
            """
            CREATE TABLE schema_meta (schema_version INTEGER NOT NULL);
            INSERT INTO schema_meta(schema_version) VALUES (2);
            CREATE TABLE revisions (
                revision INTEGER PRIMARY KEY AUTOINCREMENT,
                schema_version INTEGER NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE ledger_lots (
                order_id TEXT PRIMARY KEY, symbol TEXT NOT NULL, buy_price REAL NOT NULL,
                shares REAL NOT NULL, target_sell_price REAL NOT NULL,
                closed INTEGER NOT NULL DEFAULT 0, revision INTEGER NOT NULL,
                schema_version INTEGER NOT NULL
            );
            CREATE TABLE order_state (
                order_id TEXT PRIMARY KEY, payload TEXT NOT NULL, revision INTEGER NOT NULL,
                schema_version INTEGER NOT NULL
            );
            CREATE TABLE processed_events (
                event_id TEXT PRIMARY KEY, revision INTEGER NOT NULL, schema_version INTEGER NOT NULL
            );
            CREATE TABLE audit_events (
                sequence INTEGER PRIMARY KEY AUTOINCREMENT,
                event_id TEXT NOT NULL UNIQUE, timestamp TEXT NOT NULL,
                event_type TEXT NOT NULL, schema_version INTEGER NOT NULL,
                deployment_id TEXT NOT NULL, payload TEXT NOT NULL, revision INTEGER NOT NULL
            );
            INSERT INTO audit_events
              (sequence,event_id,timestamp,event_type,schema_version,deployment_id,payload,revision)
            VALUES (1,'legacy-1','2026-01-01T00:00:00Z','TEST_EVENT',1,'dep','{"legacy":true}',1);
            """
        )
        conn.commit()
        conn.close()

        store = SQLiteStateStore(db_path)
        events = store.load_audit_events()
        assert len(events) == 1
        assert events[0].event_id == "legacy-1"
        assert events[0].payload == {"legacy": True}
        store.close()
