"""
Durable ledger persistence and crash recovery. Task 7.3 (L2).

Confirmed first (this task's own step 1) that AssetLotLedger did not
already persist to anything -- it held plain in-memory lists, with
only a docstring note deferring persistence to this task.

Canonical backend per architecture_overview.md 2.6: SQLite. JSONL,
pickle, ad-hoc files, and a second database are explicitly not
interchangeable and are not used here.

Tables implemented (2.6's canonical responsibilities). This task's
"Minimum persistence schema" requires ledger_lots, revisions, and
processed_events; those three are implemented. order_state and
audit_events also appear in 2.6's list but belong to Tasks 7.10 and
7.14 respectively -- not created here, per this task's Non-goals
("do not implement behavior belonging to another task").

    ledger_lots       -> open/closed lot state and cost basis
    revisions         -> monotonically increasing state revisions
    processed_events  -> idempotency/event application records

Durability contract:
- Every logical state transition is one SQLite transaction: the lot
  mutation AND its revision row commit together or not at all, so a
  crash cannot expose a half-written mutation to recovery.
- Every durable record carries schema_version.
- Revisions are monotonically increasing (AUTOINCREMENT, which in
  SQLite guarantees monotonicity even across deletes -- plain ROWID
  reuse does not).
- Recovery is idempotent: replaying an already-processed event id is a
  no-op, enforced by a PRIMARY KEY on processed_events.event_id, so
  the guarantee is the database's rather than the caller's.
- Correctness does not depend on WAL: journal_mode is left at SQLite's
  default and the tests pass either way.

Reconciliation (2.7 precedence) is deliberately NOT auto-resolving:
compare_with_broker reports disagreements; it never silently picks a
side, invents a fill, or rewrites cost basis.
"""

from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Iterator, Optional

from src.exceptions import PersistenceError, ReconciliationError
from src.ledger import AssetLotLedger, Lot

SCHEMA_VERSION = 1

_SCHEMA = """
CREATE TABLE IF NOT EXISTS ledger_lots (
    order_id          TEXT PRIMARY KEY,
    symbol            TEXT NOT NULL,
    buy_price         REAL NOT NULL,
    shares            REAL NOT NULL,
    profit_target     REAL NOT NULL,
    target_sell_price REAL NOT NULL,
    status            TEXT NOT NULL CHECK (status IN ('open', 'closed')),
    schema_version    INTEGER NOT NULL,
    revision          INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS revisions (
    revision       INTEGER PRIMARY KEY AUTOINCREMENT,
    operation      TEXT NOT NULL,
    order_id       TEXT,
    detail         TEXT,
    schema_version INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS processed_events (
    event_id       TEXT PRIMARY KEY,
    event_kind     TEXT NOT NULL,
    revision       INTEGER NOT NULL,
    schema_version INTEGER NOT NULL,
    -- Task 7.4: the broker/client order id this decision resolved to,
    -- so a replay after reconnect returns the EXISTING order rather
    -- than submitting a second one. NULL for events with no order.
    result_ref     TEXT
);

CREATE TABLE IF NOT EXISTS ledger_meta (
    key   TEXT PRIMARY KEY,
    value TEXT
);
"""


@dataclass(frozen=True)
class ReconciliationReport:
    """Outcome of comparing persisted state against broker state. Never
    resolves the disagreement itself (2.7: a disagreement is not
    resolved by silently overwriting one side)."""

    agrees: bool
    local_shares: dict
    broker_shares: dict
    missing_locally: dict
    missing_at_broker: dict
    quantity_mismatches: dict

    def raise_if_mismatched(self) -> None:
        if not self.agrees:
            raise ReconciliationError(
                "Persisted ledger state disagrees with broker positions -- "
                f"missing_locally={self.missing_locally}, missing_at_broker={self.missing_at_broker}, "
                f"quantity_mismatches={self.quantity_mismatches}. Not auto-resolving; "
                "halt affected trading and reconcile."
            )


class LedgerStore:
    """SQLite-backed durable store for AssetLotLedger state.

    Owns the database only. It never mutates an AssetLotLedger in
    place; load_ledger() builds a fresh one, and callers persist
    mutations explicitly. That keeps the in-memory ledger (Task 7.2's
    owner of lot.shares) and the durable record from silently drifting
    through hidden writes.
    """

    def __init__(self, db_path: str = ":memory:"):
        self.db_path = db_path
        self._conn = sqlite3.connect(db_path)
        self._conn.row_factory = sqlite3.Row
        self._conn.execute("PRAGMA foreign_keys = ON")
        with self._transaction() as conn:
            conn.executescript(_SCHEMA)
            conn.execute(
                "INSERT OR IGNORE INTO ledger_meta (key, value) VALUES ('schema_version', ?)",
                (str(SCHEMA_VERSION),),
            )

    def close(self) -> None:
        self._conn.close()

    def __enter__(self) -> "LedgerStore":
        return self

    def __exit__(self, *exc) -> None:
        self.close()

    @contextmanager
    def _transaction(self) -> Iterator[sqlite3.Connection]:
        """One logical state transition = one atomic transaction."""
        try:
            with self._conn:
                yield self._conn
        except sqlite3.Error as e:
            raise PersistenceError(f"Durable write failed and was rolled back: {e}") from e

    # --- revisions ---

    def _next_revision(self, conn, operation: str, order_id: Optional[str], detail: str = "") -> int:
        cursor = conn.execute(
            "INSERT INTO revisions (operation, order_id, detail, schema_version) VALUES (?, ?, ?, ?)",
            (operation, order_id, detail, SCHEMA_VERSION),
        )
        return cursor.lastrowid

    def current_revision(self) -> int:
        row = self._conn.execute("SELECT COALESCE(MAX(revision), 0) AS r FROM revisions").fetchone()
        return row["r"]

    # --- lot mutations (each atomic with its revision row) ---

    def record_open_lot(self, lot: Lot) -> int:
        with self._transaction() as conn:
            revision = self._next_revision(conn, "open_lot", lot.order_id, f"shares={lot.shares}")
            conn.execute(
                "INSERT OR REPLACE INTO ledger_lots "
                "(order_id, symbol, buy_price, shares, profit_target, target_sell_price, status, schema_version, revision) "
                "VALUES (?, ?, ?, ?, ?, ?, 'open', ?, ?)",
                (
                    lot.order_id, lot.symbol, lot.buy_price, lot.shares, lot.profit_target,
                    lot.target_sell_price, SCHEMA_VERSION, revision,
                ),
            )
            return revision

    def record_lot_shares(self, lot: Lot, is_open: bool) -> int:
        """Persist a lot's current share count and open/closed status --
        used after a full OR partial close (Task 7.2).

        is_open is passed explicitly rather than inferred from
        lot.shares. A full close via close_lot(lot) moves the lot to
        closed_lots WITHOUT zeroing lot.shares (PerformanceAnalyzer's
        realized-P&L calculation depends on those shares surviving), so
        inferring status from the share count silently resurrected
        fully-closed lots as open on restart -- caught by the
        crash-recovery check before this was committed. The ledger, not
        the share count, is the authority on open vs closed.
        """
        status = "open" if is_open else "closed"
        with self._transaction() as conn:
            revision = self._next_revision(conn, "update_lot", lot.order_id, f"shares={lot.shares},status={status}")
            cursor = conn.execute(
                "UPDATE ledger_lots SET shares = ?, status = ?, revision = ? WHERE order_id = ?",
                (lot.shares, status, revision, lot.order_id),
            )
            if cursor.rowcount == 0:
                raise PersistenceError(f"No persisted lot with order_id {lot.order_id!r} to update")
            return revision

    def sync_lot(self, ledger: AssetLotLedger, lot: Lot) -> int:
        """Convenience wrapper deriving is_open from the ledger itself,
        so callers can't get the flag backwards."""
        return self.record_lot_shares(lot, is_open=lot in ledger.open_lots)

    # --- processed events (idempotent recovery) ---

    def has_processed(self, event_id: str) -> bool:
        row = self._conn.execute(
            "SELECT 1 FROM processed_events WHERE event_id = ?", (event_id,)
        ).fetchone()
        return row is not None

    def record_processed_event(self, event_id: str, event_kind: str = "event", result_ref: str = None) -> bool:
        """Returns True if newly recorded, False if already present.
        The PRIMARY KEY makes replay a no-op at the database level, so
        idempotency doesn't depend on callers checking first."""
        with self._transaction() as conn:
            if conn.execute("SELECT 1 FROM processed_events WHERE event_id = ?", (event_id,)).fetchone():
                return False
            revision = self._next_revision(conn, "processed_event", None, event_id)
            conn.execute(
                "INSERT INTO processed_events (event_id, event_kind, revision, schema_version, result_ref) "
                "VALUES (?, ?, ?, ?, ?)",
                (event_id, event_kind, revision, SCHEMA_VERSION, result_ref),
            )
            return True

    def get_event_result_ref(self, event_id: str) -> Optional[str]:
        """The broker/client order id a previously-recorded decision
        resolved to, or None if the decision is unknown."""
        row = self._conn.execute(
            "SELECT result_ref FROM processed_events WHERE event_id = ?", (event_id,)
        ).fetchone()
        return row["result_ref"] if row else None

    def set_event_result_ref(self, event_id: str, result_ref: str) -> None:
        """Attach a broker order reference to an already-claimed
        decision (claim-then-submit: the claim lands durably BEFORE the
        broker call, so a crash between the two still blocks a
        duplicate submission on restart -- it just leaves result_ref
        NULL, which recovery treats as 'submitted, outcome unknown')."""
        with self._transaction() as conn:
            self._next_revision(conn, "event_result_ref", None, f"{event_id}={result_ref}")
            cursor = conn.execute(
                "UPDATE processed_events SET result_ref = ? WHERE event_id = ?", (result_ref, event_id)
            )
            if cursor.rowcount == 0:
                raise PersistenceError(f"No processed event with id {event_id!r} to attach a result to")

    # --- recovery ---

    def load_ledger(self) -> AssetLotLedger:
        """Reconstruct an AssetLotLedger from durable state. Idempotent:
        calling it repeatedly yields equivalent ledgers and mutates
        nothing."""
        ledger = AssetLotLedger()
        rows = self._conn.execute(
            "SELECT * FROM ledger_lots ORDER BY revision ASC"
        ).fetchall()
        for row in rows:
            lot = Lot(
                order_id=row["order_id"], symbol=row["symbol"], buy_price=row["buy_price"],
                shares=row["shares"], profit_target=row["profit_target"],
            )
            # target_sell_price is recomputed identically by Lot.__post_init__
            # from the persisted buy_price/profit_target; assert rather than
            # trust, so a schema/logic drift surfaces loudly.
            if abs(lot.target_sell_price - row["target_sell_price"]) > 1e-9:
                raise PersistenceError(
                    f"Lot {row['order_id']!r}: persisted target_sell_price {row['target_sell_price']} "
                    f"disagrees with the value recomputed from buy_price/profit_target ({lot.target_sell_price})."
                )
            if row["status"] == "open":
                ledger.open_lots.append(lot)
            else:
                ledger.closed_lots.append(lot)
        return ledger

    def load_last_buy_price(self) -> Optional[float]:
        row = self._conn.execute("SELECT value FROM ledger_meta WHERE key = 'last_buy_price'").fetchone()
        return float(row["value"]) if row and row["value"] is not None else None

    def save_last_buy_price(self, price: float) -> None:
        with self._transaction() as conn:
            self._next_revision(conn, "last_buy_price", None, str(price))
            conn.execute(
                "INSERT OR REPLACE INTO ledger_meta (key, value) VALUES ('last_buy_price', ?)", (str(price),)
            )

    # --- reconciliation (2.7 precedence -- reports, never auto-resolves) ---

    def compare_with_broker(self, broker_positions: dict) -> ReconciliationReport:
        """broker_positions: {symbol: total_shares} as the broker reports
        them. Aggregates persisted OPEN lots by symbol and compares.
        Reports only -- never invents a fill or rewrites cost basis."""
        ledger = self.load_ledger()
        local: dict = {}
        for lot in ledger.open_lots:
            local[lot.symbol] = local.get(lot.symbol, 0.0) + lot.shares

        missing_locally = {s: q for s, q in broker_positions.items() if s not in local}
        missing_at_broker = {s: q for s, q in local.items() if s not in broker_positions}
        quantity_mismatches = {
            s: {"local": local[s], "broker": broker_positions[s]}
            for s in set(local) & set(broker_positions)
            if abs(local[s] - broker_positions[s]) > 1e-9
        }
        agrees = not (missing_locally or missing_at_broker or quantity_mismatches)
        return ReconciliationReport(
            agrees=agrees, local_shares=local, broker_shares=dict(broker_positions),
            missing_locally=missing_locally, missing_at_broker=missing_at_broker,
            quantity_mismatches=quantity_mismatches,
        )
