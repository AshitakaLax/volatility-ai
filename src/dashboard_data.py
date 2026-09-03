"""
Read-only view of a live deployment's durable state.

--------------------------------------------------------------------
WHY THIS IS A SEPARATE MODULE FROM THE DASHBOARD

Nothing here imports streamlit. The dashboard is presentation; this is
the part with rules, and it is testable without a UI framework
installed -- which matters because the rules are about not touching real
money.

--------------------------------------------------------------------
READ-ONLY IS ENFORCED BY SQLITE, NOT BY INTENTION

The connection is opened with `file:...?mode=ro`, so a write raises
OperationalError from the driver. That is deliberate and is the whole
security model of this feature: a dashboard is a new process reading a
live trading deployment's state, and the failure worth designing
against is not "someone adds a bad chart" but "someone adds a button".

Three properties, each independently checkable and each tested:

  1. The connection is read-only. SQLite refuses the write.
  2. No broker module is imported here or in the dashboard, so there is
     no code path to an order at all.
  3. Every function returns plain data -- dicts, lists, DataFrames --
     never a live object with methods that could act.

--------------------------------------------------------------------
WHY IT READS THE STORE AND NOT THE RUNNING LOOP

LiveTradingLoop holds its state in memory; a separate process cannot
see it. But the LedgerStore IS the durable record -- lots, cash,
unsettled proceeds, the halt, and a full revision log -- and the loop
writes through to it on every tick. Reading the store therefore shows
what would survive a restart, which is the honest thing to show: an
in-memory figure the dashboard could not verify is worth less than a
persisted one it can.

The lag is one tick. That is stated in the UI rather than hidden.
"""

from __future__ import annotations

import json
import sqlite3
import time
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pandas as pd

# Keys written by the live loop and the circuit breaker. Imported by
# NAME rather than re-typed, so a rename in either module breaks this at
# import time instead of silently showing a blank dashboard.
from src.live_trading_loop import (
    _META_CASH,
    _META_LAST_TICK,
    _META_PEAK_EQUITY,
    _META_UNSETTLED,
)
from src.risk_manager import HALT_REASON_KEY, HALT_STATE_KEY


class DashboardError(RuntimeError):
    """The store could not be read. Never raised for an EMPTY store."""


@dataclass(frozen=True)
class Lot:
    order_id: str
    symbol: str
    buy_price: float
    shares: float
    profit_target: float
    target_sell_price: float

    def distance_to_target(self, price: float | None) -> float | None:
        """How far price must rise, as a fraction, for this lot to sell.

        None when there is no current price to compare against --
        distinct from 0.0, which would mean "already there".
        """
        if price is None or price <= 0:
            return None
        return self.target_sell_price / price - 1.0


@dataclass(frozen=True)
class DeploymentState:
    """Everything the dashboard shows, as plain data.

    Every field is optional or defaulted because a store that has never
    run is a normal state, not an error: a fresh deployment has no cash
    meta, no lots and no halt, and the dashboard should say so rather
    than fail.
    """

    path: str
    cash: float | None = None
    unsettled: float = 0.0
    peak_equity: float | None = None
    halted: bool = False
    halt_reason: str = ""
    lots: list[Lot] = field(default_factory=list)
    revision: int = 0
    pending_settlement: list[tuple[int, float]] = field(default_factory=list)
    closed_lots: list[Lot] = field(default_factory=list)
    last_write_age: float | None = None
    # The loop's OWN last observed price and tick time. A real mark and
    # a real heartbeat, where last_write_age is only a file-mtime proxy.
    last_price: float | None = None
    last_tick_at: str | None = None
    exists: bool = True

    @property
    def buying_power(self) -> float | None:
        """Cash that can actually be spent, mirroring BacktestState and
        _LoopState. Floored at zero for the same reason they floor it."""
        if self.cash is None:
            return None
        return max(0.0, self.cash - self.unsettled)

    @property
    def open_shares(self) -> float:
        return sum(lot.shares for lot in self.lots)

    @property
    def cost_basis(self) -> float:
        return sum(lot.shares * lot.buy_price for lot in self.lots)

    def market_value(self, price: float | None) -> float | None:
        if price is None:
            return None
        return self.open_shares * price

    def equity(self, price: float | None) -> float | None:
        """Cash plus marked-to-market lots, or None if unknowable.

        Unsettled proceeds ARE equity -- they are yours, just not
        spendable yet -- so they are included.

        None when there are OPEN LOTS and no price to value them at.
        The first version returned cash in that case, which rendered as
        an "Equity" figure identical to cash: a real number, quietly
        excluding every share held, presented as the account's worth.
        A blank is honest; a wrong number that looks right is not.
        """
        if self.cash is None:
            return None
        if not self.lots:
            return self.cash
        value = self.market_value(price)
        return None if value is None else self.cash + value

    def drawdown(self, price: float | None) -> float | None:
        """Current equity against the persisted high-water mark.

        THE number the circuit breaker acts on, and it was loaded and
        then never shown. An operator watching a deployment wants to
        know how close it is to halting, not to discover it halted.
        """
        equity = self.equity(price)
        if equity is None or not self.peak_equity:
            return None
        return max(0.0, (self.peak_equity - equity) / self.peak_equity)

    def unrealized(self, price: float | None) -> float | None:
        """Mark-to-market gain on open lots. None without a price."""
        value = self.market_value(price)
        return None if value is None else value - self.cost_basis

    def ladder(self, price: float | None, moves=(0.0, 0.01, 0.02, 0.05, 0.10)) -> list[dict]:
        """How many lots become sellable at each of several price moves.

        The operational question for a grid book is not "what is it worth
        now" but "what does a 2% rally actually release". That is
        answerable from the targets already on file and was not being
        asked -- the table showed a per-lot distance and left the reader
        to aggregate it in their head.

        Proceeds are computed at each lot's TARGET, not at the probe
        price: a resting limit sell fills at its limit, so the target is
        what the lot actually returns.
        """
        if price is None or price <= 0:
            return []
        rows = []
        for move in moves:
            probe = price * (1.0 + move)
            ready = [lot for lot in self.lots if probe >= lot.target_sell_price]
            rows.append(
                {
                    "move": move,
                    "price": probe,
                    "lots": len(ready),
                    "shares": sum(lot.shares for lot in ready),
                    "proceeds": sum(lot.shares * lot.target_sell_price for lot in ready),
                }
            )
        return rows

    def tick_age(self) -> float | None:
        """Seconds since the loop last accepted a tick.

        Distinct from last_write_age, which is the store's file mtime and
        moves on any write. This moves only when the loop actually SAW a
        price, so it separates "running but the market is closed" from
        "not running" -- the two the mtime proxy could not tell apart.
        """
        if not self.last_tick_at:
            return None
        try:
            seen = datetime.fromisoformat(self.last_tick_at)
        except ValueError:
            return None
        if seen.tzinfo is None:
            seen = seen.replace(tzinfo=UTC)
        return max(0.0, (datetime.now(UTC) - seen).total_seconds())

    def marketable(self, price: float | None) -> list[Lot]:
        """Lots whose target price the market has already reached.

        The single most useful thing to see at a glance, and it was
        legible only as a NEGATIVE "distance to target", which reads as
        a shortfall rather than as "this is ready to sell".
        """
        if price is None or price <= 0:
            return []
        return [lot for lot in self.lots if price >= lot.target_sell_price]


def _connect(db_path: str) -> sqlite3.Connection:
    """Open the store READ-ONLY.

    mode=ro makes the driver itself refuse writes, which is stronger
    than this module simply not calling any. uri=True is required for
    the mode parameter to be honoured at all -- without it sqlite3
    treats the whole string as a filename and silently CREATES a file
    named `file:...?mode=ro`, which would look like an empty store.
    """
    resolved = Path(db_path).resolve()
    if not resolved.exists():
        raise DashboardError(
            f"No ledger store at {resolved}. The live loop creates it on first "
            "run; point --db at an existing deployment."
        )
    try:
        return sqlite3.connect(f"file:{resolved.as_posix()}?mode=ro", uri=True)
    except sqlite3.Error as exc:  # pragma: no cover - driver-level failure
        raise DashboardError(f"Could not open {resolved} read-only: {exc}") from exc


def _write_age(db_path: str) -> float | None:
    """Seconds since the store was last written, or None if unknowable.

    A PROXY for loop liveness, and the only one available: neither
    ledger_lots nor revisions carries a timestamp, so there is no
    in-band way to ask "is the loop still running". The file's mtime
    answers it well enough -- the loop writes through on every tick, so
    a store untouched for many poll intervals means the process is gone,
    wedged, or the market is closed.

    Stated as a proxy in the UI rather than presented as a heartbeat,
    because it cannot distinguish those three.
    """
    try:
        return max(0.0, time.time() - Path(db_path).stat().st_mtime)
    except OSError:
        return None


def _meta(conn: sqlite3.Connection, key: str) -> str | None:
    row = conn.execute("SELECT value FROM ledger_meta WHERE key = ?", (key,)).fetchone()
    return row[0] if row else None


def _float(value: str | None) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def load_state(db_path: str) -> DeploymentState:
    """The current durable state of one deployment.

    An empty or brand-new store yields a DeploymentState with everything
    at its default rather than an exception -- "nothing has happened
    yet" is a real answer and the dashboard renders it.
    """
    conn = _connect(db_path)
    try:
        try:
            columns = "order_id, symbol, buy_price, shares, profit_target, target_sell_price"
            lot_rows = conn.execute(
                f"SELECT {columns} FROM ledger_lots WHERE status = 'open' ORDER BY buy_price DESC"
            ).fetchall()
            # Closed lots are RETAINED in this table and were never read
            # back. They are the deployment's entire trading history.
            closed_rows = conn.execute(
                f"SELECT {columns} FROM ledger_lots WHERE status = 'closed' "
                "ORDER BY revision DESC LIMIT 500"
            ).fetchall()
            revision = conn.execute("SELECT COALESCE(MAX(revision), 0) FROM revisions").fetchone()[
                0
            ]
            cash = _float(_meta(conn, _META_CASH))
            peak = _float(_meta(conn, _META_PEAK_EQUITY))
            halt_state = _meta(conn, HALT_STATE_KEY)
            halt_reason = _meta(conn, HALT_REASON_KEY) or ""
            unsettled_raw = _meta(conn, _META_UNSETTLED)
            tick_raw = _meta(conn, _META_LAST_TICK)
        except sqlite3.Error as exc:
            raise DashboardError(
                f"{db_path} is not a ledger store ({exc}). It exists, but has none "
                "of the expected tables."
            ) from exc

        unsettled, pending = 0.0, []
        if unsettled_raw:
            try:
                parsed = json.loads(unsettled_raw)
                unsettled = float(parsed.get("unsettled", 0.0))
                pending = [(int(d), float(a)) for d, a in parsed.get("pending", [])]
            except (TypeError, ValueError, KeyError):
                # Deliberately NOT fatal, and deliberately not silent. The
                # live loop's own recovery treats unreadable settlement
                # state as "everything is unsettled"; a read-only viewer
                # showing zero would UNDERSTATE what is tied up, so it
                # shows the whole balance as unsettled to match.
                unsettled = cash or 0.0

        last_price, last_tick_at = None, None
        if tick_raw:
            try:
                tick = json.loads(tick_raw)
                last_price = float(tick["price"])
                last_tick_at = str(tick["at"])
            except (TypeError, ValueError, KeyError):
                # Unreadable means "no mark", not "price zero". A zero
                # here would render every lot as infinitely far from its
                # target and equity as cash alone.
                last_price, last_tick_at = None, None

        return DeploymentState(
            path=str(db_path),
            last_price=last_price,
            last_tick_at=last_tick_at,
            cash=cash,
            unsettled=unsettled,
            peak_equity=peak,
            halted=bool(halt_state) and str(halt_state).upper() != "ACTIVE",
            halt_reason=halt_reason,
            lots=[Lot(*row) for row in lot_rows],
            closed_lots=[Lot(*row) for row in closed_rows],
            last_write_age=_write_age(db_path),
            revision=int(revision or 0),
            pending_settlement=pending,
        )
    finally:
        conn.close()


def load_activity(db_path: str, limit: int = 200) -> list[dict[str, Any]]:
    """The revision log, newest first. Every mutation the loop made.

    This table already exists as an audit trail and nothing has ever
    read it back. It is the closest thing the deployment has to a
    human-readable history.
    """
    conn = _connect(db_path)
    try:
        rows = conn.execute(
            "SELECT revision, operation, order_id, detail FROM revisions "
            "ORDER BY revision DESC LIMIT ?",
            (int(limit),),
        ).fetchall()
    except sqlite3.Error as exc:
        raise DashboardError(f"{db_path} has no revisions table ({exc}).") from exc
    finally:
        conn.close()
    return [{"revision": r[0], "operation": r[1], "order_id": r[2], "detail": r[3]} for r in rows]


def load_order_journal(path: str) -> list[dict[str, Any]]:
    """The placing broker's confNum journal, if one exists.

    Absent is normal -- it only exists once a real order has been
    placed -- so a missing file is an empty list, not an error.
    """
    file = Path(path)
    if not file.exists():
        return []
    entries = []
    for line in file.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            entries.append(json.loads(line))
        except json.JSONDecodeError:
            # A torn final line is expected if the process died mid-write.
            # Skipping it is right; hiding that it happened is not.
            entries.append({"conf_num": "<unparseable>", "raw": line[:120]})
    return entries


def find_stores(root: str = ".") -> list[str]:
    """Ledger stores under `root`, for a picker rather than a typed path."""
    return sorted(
        str(p)
        for p in Path(root).rglob("*.db")
        if not {".venv", "venv", "node_modules"} & set(p.parts)
    )


def find_bar_files(symbol: str, root: str = "data") -> list[str]:
    """Minute-bar CSVs for `symbol`, newest-looking first.

    The dashboard charts from a FILE rather than from a market-data API
    on purpose. Fetching live bars would put credentials into a process
    whose entire safety argument is that it holds none and imports
    nothing that can trade -- a real cost for a chart.

    So the chart shows recorded history, and the page says how stale it
    is rather than letting a two-week-old close pass for a quote. The
    LIVE price comes from the loop's own last tick, which is a fact the
    store already holds.
    """
    folder = Path(root)
    if not folder.exists():
        return []
    return sorted(
        (str(p) for p in folder.glob(f"{symbol}_*1Min*.csv")),
        key=lambda p: Path(p).stat().st_mtime,
        reverse=True,
    )


def load_bars(path: str, *, limit: int = 780) -> pd.DataFrame:
    """The last `limit` minute bars, oldest first.

    Reads the tail rather than the whole file: these are 60 MB and
    1,000,000+ rows, and a dashboard that takes three seconds to redraw
    stops being looked at. 780 rows is two regular sessions.
    """
    file = Path(path)
    if not file.exists():
        raise DashboardError(f"No bar file at {path}.")
    try:
        frame = pd.read_csv(file)
    except (OSError, ValueError) as exc:
        raise DashboardError(f"Could not read {path}: {exc}") from exc
    if "timestamp" not in frame.columns or "close" not in frame.columns:
        raise DashboardError(f"{path} has no timestamp/close columns -- not a minute-bar file.")
    frame = frame.tail(limit).copy()
    frame["timestamp"] = pd.to_datetime(frame["timestamp"], utc=True, errors="coerce")
    return frame.dropna(subset=["timestamp"]).reset_index(drop=True)
