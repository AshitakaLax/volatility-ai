"""Read-only views of a live deployment.

--------------------------------------------------------------------
THIS MODULE CANNOT TRADE, AND THAT IS ENFORCED RATHER THAN INTENDED

Three independent layers, the same three dashboard.py established:

  1. Every read goes through src/dashboard_data, which opens SQLite with
     `file:...?mode=ro`. The DRIVER refuses a write -- not this code, and
     not a convention someone could forget.
  2. Nothing here imports a broker, a session, or an order type. There
     is no code path to an order to be reached by accident.
  3. tests/unit/test_server_capability.py walks this file's AST and
     fails if either of those stops being true.

The halt lives in server/control.py, deliberately in a different module,
because it is the ONE write this application performs and mixing it in
here would make the paragraph above false.

--------------------------------------------------------------------
WHAT THIS DATA IS, AND WHAT IT IS NOT

The live loop holds its working state in memory and writes through to
the store once per tick, so everything served here is up to one poll
interval behind -- 60 seconds by default. `write_age_s` and
`last_tick` are both returned so a client can SAY so rather than
imply currency. A dashboard that looks real-time and is not will
eventually be trusted at the wrong moment.

--------------------------------------------------------------------
WHY THE WEBSOCKET POLLS

`rev` is a monotonic counter the store bumps on every mutation, so
a change is detectable by comparing one integer. Polling it here, in a
reader process, is what lets the trading process stay untouched --
pushing from the loop itself would mean a socket inside the process that
places orders, which dashboard.py's own docstring considered and
rejected. The cost is one integer read per second against a file the OS
has cached.
"""

from __future__ import annotations

import asyncio
from typing import Any

from fastapi import APIRouter, HTTPException, Query, WebSocket, WebSocketDisconnect

from engine.data.dashboard_data import (
    DashboardError,
    find_bar_files,
    find_stores,
    load_activity,
    load_bars,
    load_state,
)
from research.strategies.sizing_indicators import WilderRSI

router = APIRouter(prefix="/api/live", tags=["live"])

# One second. The loop writes at most once per poll interval (60s by
# default), so this is far finer than the data can actually change --
# deliberately, so that a manual halt or an operator restart shows up
# immediately rather than up to a minute later.
POLL_SECONDS = 1.0


def state_payload(path: str) -> dict[str, Any]:
    """One deployment's state as the wire's LiveState.

    Lots are flattened with their derived figures already computed, so
    the client is not re-deriving `to_target` from `target_px` and
    getting a different answer than the Python side would. There is one
    definition of that number and it is
    src/dashboard_data.Lot.distance_to_target. (A lot's market value is
    NOT sent: qty x last_px is a multiplication, not a definition.)

    No `path`: the caller named the store it asked for.
    """
    state = load_state(path)
    price = state.last_price

    def lot_payload(lot) -> dict[str, Any]:
        return {
            "id": lot.order_id,
            "symbol": lot.symbol,
            "px": lot.buy_price,
            "qty": lot.shares,
            "target": lot.profit_target,
            "target_px": lot.target_sell_price,
            "to_target": lot.distance_to_target(price),
            # How far BELOW the last mark this lot was bought. Not a
            # grid-step distance -- the step is a strategy parameter this
            # module deliberately knows nothing about -- but it is the
            # figure an operator reads to see how deep the book is.
            "vs_mark": (lot.buy_price / price - 1.0) if price and price > 0 else None,
        }

    return {
        "exists": state.exists,
        "rev": state.revision,
        "cash": state.cash,
        "unsettled": state.unsettled,
        "buying_power": state.buying_power,
        "peak_equity": state.peak_equity,
        # Non-null exactly when halted -- the reason IS the flag. Blocks
        # new buys only; nothing here force-liquidates.
        "halt": state.halt_reason if state.halted else None,
        "lots": [lot_payload(lot) for lot in state.lots],
        "closed": [lot_payload(lot) for lot in state.closed_lots],
        "settling": [list(entry) for entry in state.pending_settlement],
        "write_age_s": state.last_write_age,
        "last_px": state.last_price,
        "last_tick": state.last_tick_at,
        # WHAT THIS LOOP IS ACTUALLY TRADING. Empty on a store written
        # before the loop recorded it, which the UI renders as unknown
        # rather than as zeros. The 30%-instead-of-0.3% profit target
        # that stranded 94 lots was invisible here until this existed.
        "params": state.parameters,
    }


@router.get("/stores")
def stores(root: str = ".") -> list[str]:
    """Paths of the ledger stores available to switch between.

    Paths only. The picker's label is the basename and its paper/live
    badge is whether the path says "paper" -- a NAMING CONVENTION, NOT A
    FACT ABOUT THE ACCOUNT (the store does not record it), so both are
    derived where they are displayed and nothing may gate a decision on
    either.
    """
    return list(find_stores(root))


@router.get("/state")
def state(path: str = Query(..., description="Path to a ledger store")) -> dict[str, Any]:
    try:
        return state_payload(path)
    except DashboardError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/activity")
def activity(
    path: str = Query(...),
    limit: int = Query(200, ge=1, le=2000),
) -> list[dict[str, Any]]:
    """The revision log, newest first -- every mutation the loop made."""
    try:
        return load_activity(path, limit=limit)
    except DashboardError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/bars")
def bars(
    symbol: str = Query(...),
    limit: int = Query(780, ge=1, le=20_000),
    root: str = Query("data"),
) -> dict[str, Any]:
    """Recent minute bars for charting, as the same Bars shape
    /api/backtest/bars serves: [t, o, h, l, c, v] tuples, t in epoch
    seconds. A file with only a close column fills o/h/l from it and v
    with 0.

    Capped at 20,000 rows. These files are 60 MB and a million rows;
    serving one whole would stall the event loop for seconds and the
    browser for longer.
    """
    files = find_bar_files(symbol, root)
    if not files:
        raise HTTPException(status_code=404, detail=f"No bar file for {symbol!r} under {root!r}.")
    try:
        frame = load_bars(files[0], limit=limit)
    except DashboardError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    return {
        "bucket_s": 60,
        "rows": len(frame),
        # The bars are a FILE, which can lag a running deployment.
        "source": files[0],
        "bars": [
            [
                int(row.timestamp.timestamp()),
                float(getattr(row, "open", row.close)),
                float(getattr(row, "high", row.close)),
                float(getattr(row, "low", row.close)),
                float(row.close),
                float(getattr(row, "volume", 0.0)),
            ]
            for row in frame.itertuples()
        ],
    }


@router.get("/indicators")
def indicators(
    symbol: str = Query(...),
    period: int = Query(14, ge=2, le=200),
    root: str = Query("data"),
) -> dict[str, Any]:
    """The current reading of the indicators an operator watches.

    WilderRSI, the SAME class RsiMomentumSizing trades on and the same
    one the backtest blotter records. A second implementation here would
    be free to disagree with the strategy's own, and the number on the
    dashboard would then be describing a different indicator than the one
    making decisions.

    Computed from the most recent session of minute bars rather than
    stored, because the loop does not persist it -- and adding a field to
    the trading path for a number a reader can derive would be the wrong
    trade.

    `rsi` is null until the period seeds. That is honest: an unseeded
    Wilder average is a partial mean, and this project has already been
    caught once trading a moving average that had not warmed up. The
    symbol and period are the caller's own query, not echoed back.
    """
    files = find_bar_files(symbol, root)
    if not files:
        raise HTTPException(status_code=404, detail=f"No bar file for {symbol!r} under {root!r}.")
    try:
        frame = load_bars(files[0], limit=max(period * 20, 390))
    except DashboardError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    tracker = WilderRSI(period=period)
    value: float | None = None
    for close in frame["close"]:
        value = tracker.update(float(close))

    return {
        "rsi": None if value is None else round(value, 2),
        "n": len(frame),
        "as_of": frame["timestamp"].iloc[-1].isoformat() if len(frame) else None,
        # The bars are a FILE, not the loop's own feed. They can lag a
        # running deployment, and saying so is cheaper than someone
        # discovering it during a fast market.
        "source": files[0],
    }


@router.websocket("/ws")
async def live_socket(socket: WebSocket, path: str) -> None:
    """Push Frame<LiveState> whenever the store's revision changes.

    Sends once on connect so a client is never staring at an empty page
    waiting for the deployment to do something -- which, outside market
    hours, could be sixteen hours.

    A read failure is reported and the socket STAYS OPEN. The store being
    momentarily unreadable (a checkpoint, a restart) is not a reason to
    drop a client that will otherwise reconnect and ask the same
    question a second later.
    """
    await socket.accept()
    last_revision: int | None = None
    try:
        while True:
            try:
                payload = state_payload(path)
            except DashboardError as exc:
                await socket.send_json({"t": "err", "msg": str(exc)})
                await asyncio.sleep(POLL_SECONDS)
                continue

            if payload["rev"] != last_revision:
                last_revision = payload["rev"]
                await socket.send_json({"t": "data", "d": payload})
            else:
                # A heartbeat, so a client can distinguish "nothing has
                # changed" from "this connection is dead". Without it the
                # two look identical for as long as the market is shut.
                await socket.send_json({"t": "hb"})
            await asyncio.sleep(POLL_SECONDS)
    except WebSocketDisconnect:
        return


__all__ = ["router", "state_payload"]
