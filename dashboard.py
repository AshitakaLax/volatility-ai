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

import altair as alt  # noqa: E402
import pandas as pd  # noqa: E402
import streamlit as st  # noqa: E402

from src.dashboard_data import (  # noqa: E402
    DashboardError,
    find_bar_files,
    find_stores,
    load_activity,
    load_bars,
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

    tick_age = state.tick_age()
    if tick_age is not None:
        # The loop's own tick, which moves only when it SAW a price --
        # so this separates "running, market closed" from "not running",
        # which the file-mtime proxy below could never do.
        freshness = (
            f"last tick {tick_age:.0f}s ago at ${state.last_price:,.4f}"
            if tick_age < 120
            else f"**last tick {tick_age / 60:.0f} min ago** at ${state.last_price:,.4f}"
        )
        age = tick_age
    else:
        age = state.last_write_age
        if age is None:
            freshness = "no tick recorded yet"
        elif age < 120:
            freshness = f"last write {age:.0f}s ago (no tick recorded)"
        else:
            freshness = f"**last write {age / 60:.0f} min ago** (no tick recorded)"
    st.caption(
        f"`{state.path}` · revision {state.revision:,} · {freshness} · persisted "
        "state, so up to one poll interval behind the running loop."
    )
    if age is not None and age > 900:
        st.warning(
            f"No tick for {age / 60:.0f} minutes. Outside market hours that is "
            "expected — the loop ticks but skips, and only records a tick when it "
            "actually sees a price. During the session it means the loop has "
            "stopped or is wedged.",
            icon="⏱️",
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

    drawdown = state.drawdown(price)
    unrealized = state.unrealized(price)
    e, f, g = st.columns(3)
    e.metric(
        "Peak equity",
        money(state.peak_equity),
        help="The high-water mark the circuit breaker measures drawdown against.",
    )
    f.metric(
        "Drawdown from peak",
        "--" if drawdown is None else f"{drawdown:.2%}",
        help="What the circuit breaker acts on. It was persisted and never "
        "displayed, so a deployment approaching its halt threshold looked "
        "exactly like one that was not.",
    )
    g.metric(
        "Unrealized on open lots",
        money(unrealized),
        delta=None if unrealized is None else f"{unrealized:+,.2f}",
        delta_color="normal",
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


def render_ladder(state, price: float | None) -> None:
    """What a price move actually releases."""
    rows = state.ladder(price)
    if not rows:
        st.info("Set a mark price to see what a move would release.")
        return
    st.subheader("If price moves")
    st.caption(
        "How much of the book becomes sellable at each move, and what it returns. "
        "Proceeds are at each lot's own TARGET, not at the probe price — a resting "
        "limit sell fills at its limit."
    )
    frame = pd.DataFrame(rows)
    st.dataframe(
        frame,
        width="stretch",
        hide_index=True,
        column_config={
            "move": st.column_config.NumberColumn("move", format="%+.0f%%"),
            "price": st.column_config.NumberColumn(format="$%.4f"),
            "lots": st.column_config.NumberColumn("lots sellable"),
            "shares": st.column_config.NumberColumn(format="%.4f"),
            "proceeds": st.column_config.NumberColumn(format="$%.2f"),
        },
    )


def render_closed(state) -> None:
    """The trading history, which the store keeps and nothing read back."""
    if not state.closed_lots:
        return
    st.subheader(f"Closed lots ({len(state.closed_lots)})")
    st.caption(
        "Retained in the store and never surfaced before. **Realized P&L is not "
        "shown because it is not derivable**: a closed lot records shares and "
        "status but NOT its execution price, so the store cannot say what any "
        "of these actually sold for. The targets below are what they were "
        "offered at, which is a floor for profit-target exits and nothing at "
        "all for signal exits."
    )
    rows = [
        {
            "order id": lot.order_id[:12],
            "symbol": lot.symbol,
            "shares": lot.shares,
            "buy": lot.buy_price,
            "offered at": lot.target_sell_price,
            "cost basis": lot.shares * lot.buy_price,
        }
        for lot in state.closed_lots[:200]
    ]
    st.dataframe(
        pd.DataFrame(rows),
        width="stretch",
        hide_index=True,
        height=260,
        column_config={
            "buy": st.column_config.NumberColumn(format="$%.4f"),
            "offered at": st.column_config.NumberColumn(format="$%.4f"),
            "cost basis": st.column_config.NumberColumn(format="$%.2f"),
        },
    )


def render_chart(state, bar_path: str | None, mark: float | None) -> None:
    """Price, with every lot's exit drawn on it.

    THE POINT OF THIS CHART is not the price line -- it is the grid.
    A lot table gives a distance per row and leaves the reader to build
    the picture; drawn against price, the whole book's structure is one
    glance: where the exits cluster, how far the nearest one is, and
    whether a move would release one lot or twenty.
    """
    if not bar_path:
        st.info(
            "No minute-bar file found in `data/`. The chart reads recorded bars "
            "from disk rather than fetching them, so this page needs no "
            "credentials and makes no network calls."
        )
        return
    try:
        bars = load_bars(bar_path)
    except DashboardError as exc:
        st.warning(str(exc))
        return
    if bars.empty:
        st.info("That bar file is empty.")
        return

    st.subheader("Price and the lot grid")
    latest = bars["timestamp"].iloc[-1]
    st.caption(
        f"`{Path(bar_path).name}` · {len(bars)} bars to {latest:%Y-%m-%d %H:%M} UTC. "
        "**Recorded history, not a quote** -- the live mark comes from the loop's "
        "own last tick, shown above."
    )

    price = (
        alt.Chart(bars)
        .mark_line(strokeWidth=1.4)
        .encode(
            x=alt.X("timestamp:T", title=None),
            y=alt.Y(
                "close:Q",
                title="price",
                scale=alt.Scale(zero=False),  # a grid is basis points wide
            ),
            tooltip=[
                alt.Tooltip("timestamp:T", title="time"),
                alt.Tooltip("close:Q", title="close", format="$.4f"),
            ],
        )
    )
    layers = [price]

    if state.lots:
        ready = {lot.order_id for lot in state.marketable(mark)}
        targets = pd.DataFrame(
            {
                "target": [lot.target_sell_price for lot in state.lots],
                "status": ["ready" if lot.order_id in ready else "waiting" for lot in state.lots],
                "shares": [lot.shares for lot in state.lots],
            }
        )
        layers.append(
            alt.Chart(targets)
            .mark_rule(strokeDash=[4, 3], strokeWidth=1)
            .encode(
                y="target:Q",
                color=alt.Color(
                    "status:N",
                    scale=alt.Scale(domain=["ready", "waiting"], range=["#2ca02c", "#888888"]),
                    legend=alt.Legend(title="lot exit"),
                ),
                tooltip=[
                    alt.Tooltip("target:Q", title="exit at", format="$.4f"),
                    alt.Tooltip("shares:Q", title="shares"),
                    alt.Tooltip("status:N", title="status"),
                ],
            )
        )

    if mark:
        layers.append(
            alt.Chart(pd.DataFrame({"mark": [mark]}))
            .mark_rule(strokeWidth=2, color="#d62728")
            .encode(y="mark:Q", tooltip=[alt.Tooltip("mark:Q", format="$.4f")])
        )

    st.altair_chart(alt.layer(*layers).interactive(), width="stretch")
    if state.lots and mark:
        st.caption(
            "Dashed lines are lot exits — green where price has already reached "
            "them. The solid red line is the live mark."
        )


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
        st.divider()
        st.header("Mark")
        price = st.number_input(
            "Override the mark",
            min_value=0.0,
            value=0.0,
            step=0.01,
            help="0 uses the loop's OWN last tick price, which the store now "
            "records. Set a value here only to ask what-if. Nothing is "
            "fetched either way: this view makes no network calls.",
        )
        st.divider()
        st.header("Chart")
        bar_files = find_bar_files("TQQQ")
        bar_path = (
            st.selectbox("Minute bars", bar_files, format_func=lambda p: Path(p).name)
            if bar_files
            else None
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

    # The loop's own last tick is the default mark. Before it existed the
    # page opened with equity blank and every lot at an unknown distance
    # until someone typed a number -- for a figure the store already had.
    mark = price if price > 0 else state.last_price
    render_header(state)
    render_cash(state, mark)
    st.divider()
    render_lots(state, mark)
    st.divider()
    render_chart(state, bar_path, mark)
    st.divider()
    render_ladder(state, mark)
    st.divider()
    render_closed(state)
    st.divider()
    render_activity(db_path)
    render_journal(args.journal)


if __name__ == "__main__":
    main()
