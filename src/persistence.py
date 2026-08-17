"""Canonical SQLite persistence for live ledger/order/event state."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from src.exceptions import PersistenceError, ReconciliationError
from src.ledger import AssetLotLedger, InventoryLot
from src.audit import AuditEvent

SCHEMA_VERSION = 3


class SQLiteStateStore:
    """Atomic durable store for lots, orders, processed events, audit and revisions."""

    def __init__(self, path: str | Path):
        self.path = str(path)
        try:
            self._conn = sqlite3.connect(self.path)
            self._conn.row_factory = sqlite3.Row
            self._conn.execute("PRAGMA foreign_keys=ON")
            self._conn.execute("PRAGMA busy_timeout=5000")
            self._initialize()
        except sqlite3.Error as exc:
            raise PersistenceError(f"unable to open SQLite state store {self.path!r}") from exc

    def _initialize(self) -> None:
        try:
            self._conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS schema_meta (
                    schema_version INTEGER NOT NULL
                );
                CREATE TABLE IF NOT EXISTS revisions (
                    revision INTEGER PRIMARY KEY AUTOINCREMENT,
                    schema_version INTEGER NOT NULL,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                );
                CREATE TABLE IF NOT EXISTS ledger_lots (
                    order_id TEXT PRIMARY KEY,
                    symbol TEXT NOT NULL,
                    buy_price REAL NOT NULL,
                    shares REAL NOT NULL,
                    target_sell_price REAL NOT NULL,
                    closed INTEGER NOT NULL DEFAULT 0,
                    revision INTEGER NOT NULL,
                    schema_version INTEGER NOT NULL
                );
                CREATE TABLE IF NOT EXISTS order_state (
                    order_id TEXT PRIMARY KEY,
                    payload TEXT NOT NULL,
                    revision INTEGER NOT NULL,
                    schema_version INTEGER NOT NULL
                );
                CREATE TABLE IF NOT EXISTS processed_events (
                    event_id TEXT PRIMARY KEY,
                    revision INTEGER NOT NULL,
                    schema_version INTEGER NOT NULL
                );
                CREATE TABLE IF NOT EXISTS audit_events (
                    sequence INTEGER PRIMARY KEY,
                    event_id TEXT NOT NULL UNIQUE,
                    timestamp TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    schema_version INTEGER NOT NULL,
                    deployment_id TEXT NOT NULL,
                    payload TEXT NOT NULL,
                    revision INTEGER NOT NULL
                );
                """
            )
            row = self._conn.execute("SELECT schema_version FROM schema_meta LIMIT 1").fetchone()
            if row is None:
                self._conn.execute("INSERT INTO schema_meta(schema_version) VALUES (?)", (SCHEMA_VERSION,))
                self._conn.commit()
            elif int(row[0]) < SCHEMA_VERSION:
                self._migrate_schema(int(row[0]))
            elif int(row[0]) != SCHEMA_VERSION:
                raise PersistenceError(f"unsupported persistence schema version {row[0]}")
        except sqlite3.Error as exc:
            self._conn.rollback()
            raise PersistenceError("failed to initialize SQLite schema") from exc

    def _migrate_schema(self, current_version: int) -> None:
        """Upgrade audit storage without destroying existing audit history."""
        try:
            with self._conn:
                self._conn.execute("ALTER TABLE audit_events RENAME TO audit_events_legacy")
                self._conn.execute(
                    """
                    CREATE TABLE audit_events (
                        sequence INTEGER PRIMARY KEY,
                        event_id TEXT NOT NULL UNIQUE,
                        timestamp TEXT NOT NULL,
                        event_type TEXT NOT NULL,
                        schema_version INTEGER NOT NULL,
                        deployment_id TEXT NOT NULL,
                        payload TEXT NOT NULL,
                        revision INTEGER NOT NULL
                    )
                    """
                )
                self._conn.execute(
                    """
                    INSERT INTO audit_events
                        (sequence,event_id,timestamp,event_type,schema_version,
                         deployment_id,payload,revision)
                    SELECT sequence,event_id,timestamp,event_type,schema_version,
                           deployment_id,payload,revision
                    FROM audit_events_legacy
                    ORDER BY sequence
                    """
                )
                self._conn.execute("DROP TABLE audit_events_legacy")
                self._conn.execute("UPDATE schema_meta SET schema_version=?", (SCHEMA_VERSION,))
        except sqlite3.Error as exc:
            self._conn.rollback()
            raise PersistenceError("failed to migrate audit schema without data loss") from exc

    def close(self) -> None:
        self._conn.close()

    def _next_revision(self, conn: sqlite3.Connection) -> int:
        cur = conn.execute("INSERT INTO revisions(schema_version) VALUES (?)", (SCHEMA_VERSION,))
        return int(cur.lastrowid)

    def save_lot(self, lot: InventoryLot, *, closed: bool = False) -> int:
        try:
            with self._conn:
                revision = self._next_revision(self._conn)
                self._conn.execute(
                    """INSERT INTO ledger_lots(order_id,symbol,buy_price,shares,target_sell_price,closed,revision,schema_version)
                       VALUES (?,?,?,?,?,?,?,?)
                       ON CONFLICT(order_id) DO UPDATE SET symbol=excluded.symbol,buy_price=excluded.buy_price,
                       shares=excluded.shares,target_sell_price=excluded.target_sell_price,closed=excluded.closed,
                       revision=excluded.revision,schema_version=excluded.schema_version""",
                    (lot.order_id, lot.symbol, lot.buy_price, lot.shares, lot.target_sell_price, int(closed), revision, SCHEMA_VERSION),
                )
                return revision
        except sqlite3.Error as exc:
            raise PersistenceError("failed to persist lot mutation") from exc

    def mark_processed(self, event_id: str) -> tuple[bool, int]:
        """Atomically claim an event. Returns (claimed, revision)."""
        try:
            with self._conn:
                row = self._conn.execute("SELECT revision FROM processed_events WHERE event_id=?", (event_id,)).fetchone()
                if row is not None:
                    return False, int(row[0])
                revision = self._next_revision(self._conn)
                self._conn.execute(
                    "INSERT INTO processed_events(event_id,revision,schema_version) VALUES (?,?,?)",
                    (event_id, revision, SCHEMA_VERSION),
                )
                return True, revision
        except sqlite3.Error as exc:
            raise PersistenceError("failed to claim processed event") from exc

    def peek_next_audit_sequence(self) -> int:
        """Return the next audit sequence without mutating persistent state.

        Callers that need a canonical ID should use this only while they own the
        single decision stream; the actual insert remains authoritative and
        rejects stale sequences. This method intentionally does not reserve a
        sequence or create an audit row.
        """
        try:
            row = self._conn.execute("SELECT COALESCE(MAX(sequence), 0) AS sequence FROM audit_events").fetchone()
            return int(row["sequence"]) + 1
        except sqlite3.Error as exc:
            raise PersistenceError("failed to determine next audit sequence") from exc

    def record_audit(self, event: AuditEvent) -> int:
        """Durably append an audit event exactly once."""
        try:
            payload = json.dumps(event.payload, sort_keys=True, separators=(",", ":"), allow_nan=False)
            with self._conn:
                existing = self._conn.execute(
                    "SELECT sequence,revision,payload,event_type,schema_version,deployment_id,timestamp FROM audit_events WHERE event_id=?",
                    (event.event_id,),
                ).fetchone()
                if existing is not None:
                    if (str(existing["payload"]) != payload or str(existing["event_type"]) != event.event_type
                        or int(existing["schema_version"]) != event.schema_version
                        or str(existing["deployment_id"]) != event.deployment_id):
                        raise PersistenceError(f"conflicting duplicate audit event_id={event.event_id!r}")
                    return int(existing["revision"])

                row = self._conn.execute("SELECT COALESCE(MAX(sequence), 0) AS sequence FROM audit_events").fetchone()
                next_sequence = int(row["sequence"]) + 1
                if event.sequence not in (0, next_sequence):
                    raise PersistenceError(f"audit sequence mismatch: event={event.sequence}, expected={next_sequence}")
                revision = self._next_revision(self._conn)
                self._conn.execute(
                    """INSERT INTO audit_events(sequence,event_id,timestamp,event_type,schema_version,
                       deployment_id,payload,revision) VALUES (?,?,?,?,?,?,?,?)""",
                    (next_sequence, event.event_id, event.timestamp, event.event_type, event.schema_version,
                     event.deployment_id, payload, revision),
                )
                return revision
        except PersistenceError:
            raise
        except (sqlite3.Error, ValueError) as exc:
            raise PersistenceError("failed to persist audit event") from exc

    def load_audit_events(self, *, deployment_id: str | None = None) -> list[AuditEvent]:
        query = "SELECT sequence,event_id,timestamp,event_type,schema_version,deployment_id,payload FROM audit_events"
        params: tuple[str, ...] = ()
        if deployment_id is not None:
            query += " WHERE deployment_id=?"
            params = (deployment_id,)
        query += " ORDER BY sequence ASC"
        try:
            rows = self._conn.execute(query, params).fetchall()
        except sqlite3.Error as exc:
            raise PersistenceError("failed to load audit events") from exc
        return [AuditEvent(event_id=str(row["event_id"]), timestamp=str(row["timestamp"]),
                           event_type=str(row["event_type"]), schema_version=int(row["schema_version"]),
                           deployment_id=str(row["deployment_id"]), payload=json.loads(row["payload"]),
                           sequence=int(row["sequence"])) for row in rows]

    def load_open_lots(self) -> AssetLotLedger:
        ledger = AssetLotLedger()
        try:
            rows = self._conn.execute(
                "SELECT order_id,symbol,buy_price,shares,target_sell_price FROM ledger_lots WHERE closed=0 AND shares>0 ORDER BY revision,order_id"
            ).fetchall()
        except sqlite3.Error as exc:
            raise PersistenceError("failed to load open lots") from exc
        for row in rows:
            ledger.add_lot(InventoryLot(str(row["order_id"]), str(row["symbol"]), float(row["buy_price"]), float(row["shares"]), float(row["target_sell_price"])))
        return ledger

    def persist_ledger(self, ledger: AssetLotLedger) -> None:
        try:
            with self._conn:
                for lot in ledger.open_lots:
                    self.save_lot(lot, closed=False)
        except sqlite3.Error as exc:
            raise PersistenceError("failed to persist ledger") from exc

    def reconcile_position(self, ledger: AssetLotLedger, broker_qty: float) -> None:
        local_qty = ledger.open_share_count
        if abs(float(local_qty) - float(broker_qty)) > 1e-9:
            raise ReconciliationError(f"position mismatch: local={local_qty} broker={broker_qty}")
