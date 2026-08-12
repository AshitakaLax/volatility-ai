"""Canonical SQLite persistence for live ledger/order/event state."""

from __future__ import annotations

import json
import sqlite3
from dataclasses import asdict
from pathlib import Path
from typing import Iterable

from src.exceptions import PersistenceError, ReconciliationError
from src.ledger import AssetLotLedger, InventoryLot

SCHEMA_VERSION = 1


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
                    event_id TEXT PRIMARY KEY,
                    event_type TEXT NOT NULL,
                    payload TEXT NOT NULL,
                    revision INTEGER NOT NULL,
                    schema_version INTEGER NOT NULL
                );
                """
            )
            row = self._conn.execute("SELECT schema_version FROM schema_meta LIMIT 1").fetchone()
            if row is None:
                self._conn.execute("INSERT INTO schema_meta(schema_version) VALUES (?)", (SCHEMA_VERSION,))
                self._conn.commit()
            elif int(row[0]) != SCHEMA_VERSION:
                raise PersistenceError(f"unsupported persistence schema version {row[0]}")
        except sqlite3.Error as exc:
            self._conn.rollback()
            raise PersistenceError("failed to initialize SQLite schema") from exc

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

    def record_audit(self, event_id: str, event_type: str, payload: dict) -> int:
        try:
            with self._conn:
                revision = self._next_revision(self._conn)
                self._conn.execute(
                    "INSERT OR REPLACE INTO audit_events(event_id,event_type,payload,revision,schema_version) VALUES (?,?,?,?,?)",
                    (event_id, event_type, json.dumps(payload, sort_keys=True, separators=(",", ":"), allow_nan=False), revision, SCHEMA_VERSION),
                )
                return revision
        except (sqlite3.Error, ValueError) as exc:
            raise PersistenceError("failed to persist audit event") from exc

    def load_open_lots(self) -> AssetLotLedger:
        ledger = AssetLotLedger()
        try:
            rows = self._conn.execute(
                "SELECT order_id,symbol,buy_price,shares,target_sell_price FROM ledger_lots WHERE closed=0 AND shares>0 ORDER BY revision,order_id"
            ).fetchall()
        except sqlite3.Error as exc:
            raise PersistenceError("failed to load open lots") from exc
        for row in rows:
            lot = InventoryLot(str(row["order_id"]), str(row["symbol"]), float(row["buy_price"]), float(row["shares"]), float(row["target_sell_price"]))
            ledger.open_lots.append(lot)
        return ledger

    def persist_ledger(self, ledger: AssetLotLedger) -> int:
        """Atomically replace the persisted lot snapshot with the current ledger state."""
        try:
            with self._conn:
                revision = self._next_revision(self._conn)
                self._conn.execute("DELETE FROM ledger_lots")
                for lot in ledger.open_lots:
                    self._conn.execute(
                        "INSERT INTO ledger_lots(order_id,symbol,buy_price,shares,target_sell_price,closed,revision,schema_version) VALUES (?,?,?,?,?,?,?,?)",
                        (lot.order_id, lot.symbol, lot.buy_price, lot.shares, lot.target_sell_price, 0, revision, SCHEMA_VERSION),
                    )
                for lot in ledger.closed_lots:
                    self._conn.execute(
                        "INSERT OR REPLACE INTO ledger_lots(order_id,symbol,buy_price,shares,target_sell_price,closed,revision,schema_version) VALUES (?,?,?,?,?,?,?,?)",
                        (lot.order_id, lot.symbol, lot.buy_price, lot.shares, lot.target_sell_price, 1, revision, SCHEMA_VERSION),
                    )
                return revision
        except sqlite3.Error as exc:
            raise PersistenceError("failed to persist ledger snapshot") from exc

    def reconcile_position(self, ledger: AssetLotLedger, broker_qty: float) -> None:
        local_qty = ledger.open_share_count
        if abs(float(broker_qty) - local_qty) > 1e-9:
            raise ReconciliationError(
                f"position mismatch: local_qty={local_qty}, broker_qty={float(broker_qty)}"
            )
