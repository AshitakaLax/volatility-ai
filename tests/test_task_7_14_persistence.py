import pytest
import sqlite3
import tempfile
from pathlib import Path
from src.persistence import SQLiteStateStore
from src.audit import AuditEvent, generate_event_id

def test_audit_event_persistence():
    with tempfile.TemporaryDirectory() as temp_dir:
        db_path = Path(temp_dir) / "test.db"
        store = SQLiteStateStore(db_path)
        
        event = AuditEvent(
            event_id=generate_event_id(),
            timestamp="2026-01-01T12:00:00Z",
            event_type="TEST_EVENT",
            schema_version=1,
            deployment_id="dep123",
            payload={"key": "value"}
        )
        
        rev = store.record_audit(event)
        
        # Verify the record is saved with sequence
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        row = conn.execute("SELECT * FROM audit_events WHERE event_id=?", (event.event_id,)).fetchone()
        
        assert row is not None
        assert row["sequence"] is not None
        assert row["timestamp"] == "2026-01-01T12:00:00Z"
        assert row["deployment_id"] == "dep123"
        assert row["event_type"] == "TEST_EVENT"
        
        conn.close()
        store.close()

def test_duplicate_events():
    with tempfile.TemporaryDirectory() as temp_dir:
        db_path = Path(temp_dir) / "test.db"
        store = SQLiteStateStore(db_path)
        
        event_id = generate_event_id()
        event = AuditEvent(
            event_id=event_id,
            timestamp="2026-01-01T12:00:00Z",
            event_type="TEST_EVENT",
            schema_version=1,
            deployment_id="dep123",
            payload={"key": "value"}
        )
        
        store.record_audit(event)
        
        with pytest.raises(Exception):
            store.record_audit(event)
            
        store.close()
