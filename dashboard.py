#!/usr/bin/env python
"""
A read-only window onto a live deployment.

    streamlit run dashboard.py -- --db live_ledger.db

--------------------------------------------------------------------
WHY THIS EXISTS

The live loop's state was visible only in logs. Cash, settled buying
power, unsettled proceeds, open lots and their distance to target, and
whether the circuit breaker has halted -- all of it existed, none of it
was legible without grepping a log file at the moment something looked
wrong. That is the worst time to be parsing logs.

--------------------------------------------------------------------
IT CANNOT TRADE, AND THAT IS ENFORCED THREE WAYS

  1. src/dashboard_data.py opens the SQLite store with
     `file:...?mode=ro`, so the DRIVER refuses a write.
  2. Neither module imports a broker, a session, or an order type.
     There is no code path to an order to be reached by accident.
  3. This file contains no button, form or input that submits anything.
     Every control selects what to LOOK at.

A test asserts all three, because a dashboard is exactly the kind of
thing that grows a "just one quick action" button later.

--------------------------------------------------------------------
IT SHOWS PERSISTED STATE, WHICH LAGS BY ONE TICK

LiveTradingLoop holds its working state in memory and writes through to
the store each tick, so this is up to one poll interval behind. That is
said on the page rather than implied, because a dashboard that looks
real-time and is not will eventually be trusted at the wrong moment.

The alternative -- reading the loop's memory -- would need the loop to
serve it, which means a socket in the process that trades. Not worth it
for one tick of latency.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

import pandas as pd  # noqa: E402
import streamlit as st  # noqa: E402

from src.dashboard_data import (  # noqa: E402
    DashboardError,
    find_stores,
    load_activity,
    load_order_journal,
    load_state,
)

DEFAULT_JOURNAL = Path.home() / ".fidelity_recon" / "placed_orders.jsonl"


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Streamlit passes script arguments after a bare `--`."""
    parser = argparse.ArgumentParser(description="Read-only live deployment view.")
    parser.add_argument("--db", default=None, help="Path to the ledger store (.db).")
    parser.add_argument("--journal", default=str(DEFAULT_JOURNAL))
    known, _ = parser.parse_known_args(argv if argv is not None else sys.argv[1:])
    return known


def money(value: float | None, dash: str = "--") -> str:
    return dash if value is None else f"${value:,.2f}"


def render_header(state) -> None:
    st.title("Live deployment")
    if state.halted:
        st.error(
            f"**HALTED** — {state.halt_reason or 'no reason recorded'}. "
            "New buys are blocked. Harvest sells continue, so lots stay exitable.",
            icon="🛑",
        )
    else:
        st.success("Circuit breaker ACTIVE — trading normally.", icon="✅")

    st.caption(
        f"`{state.path}` · revision {state.revision:,} · persisted state, so up to "
        "one poll interval behind the running loop."
    )


def render_cash(state, price: float | None) -> None:
    st.subheader("Cash")
    a, b, c, d = st.columns(4)
    a.metric("Total cash", money(state.cash))
    b.metric(
        "Settled — spendable",
        money(state.buying_power),
        help="What a buy can actually use. In a cash account, proceeds settle "
        "T+1 and unsettled funds are yours but not spendable.",
    )
    c.metric(
        "Unsettled",
        money(state.unsettled),
        delta=None if not state.unsettled else "not spendable yet",
        delta_color="off",
    )
    d.metric(
        "Equity",
        money(state.equity(price)),
        help="Cash plus lots marked to market. Blank until a mark price is "
        "set, because valuing held shares at nothing would report an "
        "equity figure identical to cash.",
    )

    if state.pending_settlement:
        rows = [
            {"settles on session": day, "amount": amount}
            for day, amount in sorted(state.pending_settlement)
        ]
        st.dataframe(pd.DataFrame(rows), width="stretch", hide_index=True)


def render_lots(state, price: float | None) -> None:
    st.subheader(f"Open lots ({len(state.lots)})")
    if not state.lots:
        st.info("No open lots. The book is flat.")
        return

    ready = {lot.order_id for lot in state.marketable(price)}
    if ready:
        st.warning(
            f"**{len(ready)} of {len(state.lots)} lots are at or above their "
            "target** and would be offered on the next tick.",
            icon="🎯",
        )

    rows = []
    for lot in state.lots:
        gap = lot.distance_to_target(price)
        rows.append(
            {
                "": "READY" if lot.order_id in ready else "",
                "order id": lot.order_id[:12],
                "symbol": lot.symbol,
                "shares": lot.shares,
                "buy": lot.buy_price,
                "target": lot.target_sell_price,
                "to target": None if gap is None else gap,
                "cost basis": lot.shares * lot.buy_price,
            }
        )
    frame = pd.DataFrame(rows)
    st.dataframe(
        frame,
        width="stretch",
        hide_index=True,
        column_config={
            "buy": st.column_config.NumberColumn(format="$%.4f"),
            "target": st.column_config.NumberColumn(format="$%.4f"),
            "cost basis": st.column_config.NumberColumn(format="$%.2f"),
            "to target": st.column_config.NumberColumn(
                format="%.2f%%",
                help="How far price must rise for this lot to become marketable. "
                "NEGATIVE means the target is already passed -- those rows are "
                "flagged READY. Blank when no mark price was supplied.",
            ),
        },
    )
    left, right = st.columns(2)
    left.metric("Shares held", f"{state.open_shares:,.4f}")
    right.metric("Cost basis", money(state.cost_basis))


def render_activity(db_path: str) -> None:
    st.subheader("Activity")
    st.caption(
        "The store's own revision log — every mutation the loop made. It has "
        "always been written and never read back until now."
    )
    entries = load_activity(db_path, limit=300)
    if not entries:
        st.info("No recorded activity.")
        return
    st.dataframe(pd.DataFrame(entries), width="stretch", hide_index=True, height=320)


def render_journal(path: str) -> None:
    entries = load_order_journal(path)
    if not entries:
        return
    st.subheader(f"Placed-order journal ({len(entries)})")
    st.caption(
        "confNums recorded BEFORE each order was committed, which is what makes "
        "a submission timeout recoverable rather than ambiguous."
    )
    st.dataframe(pd.DataFrame(entries), width="stretch", hide_index=True)


def main() -> None:
    args = parse_args()
    st.set_page_config(page_title="Live deployment", page_icon="📉", layout="wide")

    with st.sidebar:
        st.header("Source")
        candidates = find_stores(".")
        default = args.db or (candidates[0] if candidates else "")
        options = sorted({*candidates, *([default] if default else [])})
        db_path = (
            st.selectbox("Ledger store", options, index=options.index(default))
            if options
            else st.text_input("Ledger store path", value="")
        )
        price = st.number_input(
            "Mark price",
            min_value=0.0,
            value=0.0,
            step=0.01,
            help="Used only to mark open lots to market and compute distance to "
            "target. Nothing is fetched: this view makes no network calls.",
        )
        st.divider()
        st.caption(
            "**Read-only.** The store is opened `mode=ro`, so SQLite itself "
            "refuses a write. No broker module is imported here, so there is no "
            "code path to an order."
        )

    if not db_path:
        st.warning("No ledger store found. Point --db at one.")
        return

    try:
        state = load_state(db_path)
    except DashboardError as exc:
        st.error(str(exc))
        return

    mark = price if price > 0 else None
    render_header(state)
    render_cash(state, mark)
    st.divider()
    render_lots(state, mark)
    st.divider()
    render_activity(db_path)
    render_journal(args.journal)


if __name__ == "__main__":
    main()
