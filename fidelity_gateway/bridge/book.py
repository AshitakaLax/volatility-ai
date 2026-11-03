"""
The trading book an app is shown: open lots, the last sales, today's profit.

The bridge host puts it in the status apps hear (`book`, PROTOCOL.md in
fidelity-bridge-notifier-android), refreshed every BOOK_SECONDS. It is read,
never written, from two things the trader already keeps:

  the ledger      the open lots, their cost and target, and the last price
                  (engine.data.dashboard_data.load_state, as the Live page
                  reads it; the bridge mounts the trader's state read-only)
  the fill journal  every booked fill (ControlInbox.fills, in the control
                  directory the bridge and trader share): when each lot was
                  bought, every sale with what it fetched and made

Nothing here can change an order, a lot or the ledger. Either source missing
leaves its part empty rather than failing: "nothing yet" is an answer.
"""

from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

# How often the host re-reads the book; a sale or a buy reaches the app as a
# notification at once, so this only paces the figures.
BOOK_SECONDS = 30.0
CLOSED_SHOWN = 20
# Sessions of fill journal read: enough to find when an open lot was bought
# and to fill the last CLOSED_SHOWN sales on a quiet week.
JOURNAL_SESSIONS = 30
_MARKET = ZoneInfo("America/New_York")


def _iso(t: float | None) -> str | None:
    if t is None:
        return None
    return datetime.fromtimestamp(t, UTC).isoformat(timespec="seconds")


def _money(value: float) -> float:
    return round(float(value), 2)


def read_book(
    state_db: str | Path | None,
    inbox: Any,
    *,
    symbol: str | None,
    now: float,
    load_state: Callable[[str], Any] | None = None,
) -> dict[str, Any] | None:
    """The book as of `now`, or None when there is neither a ledger nor a
    journal to read. `inbox` is the trader's ControlInbox (or None)."""
    state = None
    if state_db is not None and Path(state_db).exists():
        if load_state is None:
            from engine.data.dashboard_data import load_state
        try:
            state = load_state(str(state_db))
        except Exception:
            state = None
    try:
        fills = inbox.fills(JOURNAL_SESSIONS) if inbox is not None else []
    except Exception:
        fills = []
    if state is None and not fills:
        return None

    bought_at: dict[str, float] = {}
    for fill in fills:
        if fill.get("side") == "buy" and fill.get("lot"):
            bought_at.setdefault(str(fill["lot"]), float(fill["t"]))

    last = getattr(state, "last_price", None) if state is not None else None
    if not last:
        try:
            bars = inbox.bars(1) if inbox is not None else []
            last = float(bars[-1]["c"]) if bars else None
        except Exception:
            last = None

    lots = list(getattr(state, "lots", []) or []) if state is not None else []
    open_lots = [
        {
            "id": lot.order_id,
            "qty": float(lot.shares),
            "buyPrice": float(lot.buy_price),
            "targetPrice": float(lot.target_sell_price),
            "boughtAt": _iso(bought_at.get(lot.order_id)),
        }
        for lot in lots
    ]
    open_lots.sort(key=lambda lot: (lot["boughtAt"] or "", lot["buyPrice"]), reverse=True)
    unrealized = (
        _money(sum((last - lot["buyPrice"]) * lot["qty"] for lot in open_lots))
        if last and open_lots
        else None
    )

    today = datetime.fromtimestamp(now, _MARKET).date()

    def is_today(fill: dict) -> bool:
        return datetime.fromtimestamp(float(fill["t"]), _MARKET).date() == today

    sales = [fill for fill in fills if fill.get("side") == "sell"]
    closed = []
    for fill in sorted(sales, key=lambda f: f["t"], reverse=True)[:CLOSED_SHOWN]:
        qty = float(fill.get("qty") or 0.0)
        cost = fill.get("cost")
        closed.append(
            {
                "id": fill.get("lot"),
                "qty": qty,
                "buyPrice": float(cost) / qty if cost is not None and qty > 0 else None,
                "sellPrice": float(fill.get("price") or 0.0),
                "pnl": _money(fill["pnl"]) if fill.get("pnl") is not None else None,
                "reason": fill.get("reason"),
                "boughtAt": _iso(bought_at.get(str(fill.get("lot")))),
                "soldAt": _iso(float(fill["t"])),
            }
        )
    sold_today = [fill for fill in sales if is_today(fill)]
    return {
        "symbol": symbol,
        "asOf": _iso(now),
        "lastPrice": float(last) if last else None,
        "open": open_lots,
        "openCost": _money(sum(lot["buyPrice"] * lot["qty"] for lot in open_lots)),
        "unrealized": unrealized,
        "closed": closed,
        "today": {
            "realized": _money(sum(float(f.get("pnl") or 0.0) for f in sold_today)),
            "sales": len(sold_today),
            "buys": sum(1 for f in fills if f.get("side") == "buy" and is_today(f)),
        },
    }


__all__ = ["BOOK_SECONDS", "CLOSED_SHOWN", "read_book"]
