"""Read-only views of a live deployment.

--------------------------------------------------------------------
THIS MODULE CANNOT TRADE, AND THAT IS ENFORCED RATHER THAN INTENDED

Three independent layers, the same three dashboard.py established:

  1. Every read goes through src/dashboard_data, which opens SQLite with
     `file:...?mode=ro`. The DRIVER refuses a write -- not this code, and
     not a convention someone could forget.
  2. Nothing here imports a broker, a session, or an order type. There
     is no code path to an order to be reached by accident.
  3. server/tests/test_server_capability.py walks this file's AST and
     fails if either of those stops being true.

The controls live in server/live_control.py, deliberately in a different module,
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
import json
import threading
import time
from datetime import datetime
from typing import Any

from fastapi import APIRouter, HTTPException, Query, WebSocket, WebSocketDisconnect

from engine.data.dashboard_data import (
    DashboardError,
    find_bar_files,
    load_activity,
    load_bars,
    load_state,
)
from research.strategies import live_profiles
from research.strategies.live_algorithm import override_path
from research.strategies.sizing_indicators import WilderRSI
from server import live_registry
from server.live_registry import Deployment, UnknownDeployment

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


# --------------------------------------------------------------------
# DEPLOYMENTS, BY ID
#
# Every deployment in server/live_registry.py's registry. A browser names one
# by id -- never by path -- and gets what its ledger holds (read mode=ro, as
# above) beside what its trader reports through its control directory
# (engine/trading/control_inbox.py): run state, desired state, commands.
# --------------------------------------------------------------------

# A trader that has not reported in three heartbeats (and at least this
# long) is called not running, rather than trusted for what it last said.
_STALE_FLOOR_SECONDS = 90.0

_NOT_CONTROLLED = {"enabled": True, "wind_down": False, "by": None, "reason": None, "at": None}


def run_state(status: dict | None, now: float) -> dict[str, Any]:
    """The trader's own report, or "not_running" when it has none or it is
    stale. The page shows this as one chip."""
    fields = (
        "state",
        "detail",
        "process",
        "next_open",
        "last_tick_at",
        "open_lots",
        "open_orders",
        "algorithm",
        "updated_at",
        "heartbeat_seconds",
        # A one-way tag of the Alpaca account it trades (never the key).
        "account",
        "cash",
        "breaker",
        # What the loop will do next and why; while an override trades, what
        # switching back would do now; and which code the trader runs.
        "now",
        "shadow",
        "build",
        # The venue, why it cannot be reached while it cannot, and -- for
        # Fidelity -- the browser extension's connection.
        "broker",
        "broker_unavailable",
        "fidelity",
    )
    if not status:
        return {
            **dict.fromkeys(fields),
            "state": "not_running",
            "detail": "no trader has reported here yet",
            "stale": True,
        }
    report = {field: status.get(field) for field in fields}
    try:
        age = now - datetime.fromisoformat(status["updated_at"]).timestamp()
    except (KeyError, TypeError, ValueError):
        age = None
    heartbeat = float(status.get("heartbeat_seconds") or 60.0)
    stale = age is None or age > max(3 * heartbeat, _STALE_FLOOR_SECONDS)
    if stale:
        report["state"] = "not_running"
        report["detail"] = (
            f"last report {age / 60:.0f} min ago: {status.get('state')}"
            if age is not None
            else "its last report is unreadable"
        )
    report["stale"] = stale
    return report


def _ledger(deployment: Deployment) -> dict[str, Any]:
    try:
        state = load_state(str(deployment.state_db))
    except DashboardError as exc:
        return {"exists": False, "error": str(exc)}
    return {
        "exists": state.exists,
        "halt": state.halt_reason if state.halted else None,
        "open_lots": len(state.lots),
        "cash": state.cash,
        "last_px": state.last_price,
        "last_tick": state.last_tick_at,
    }


_ALGORITHM_FIELDS = ("strategy_id", "strategy_params", "step", "profit_target")
_profiles_cache: dict[tuple, list] = {}
_profiles_lock = threading.Lock()


def _profiles() -> list:
    """The committed profiles, re-read only when a file in their directory
    changes: the strip asks every few seconds."""
    directory = live_profiles.profiles_dir()
    try:
        key = tuple(sorted((p.name, p.stat().st_mtime) for p in directory.glob("*.yaml")))
    except OSError:
        return []
    with _profiles_lock:
        cached = _profiles_cache.get(key)
    if cached is None:
        try:
            cached = list(live_profiles.load_profiles().values())
        except Exception:
            cached = []
        with _profiles_lock:
            _profiles_cache.clear()
            _profiles_cache[key] = cached
    return cached


def _override(deployment: Deployment, config) -> dict | None:
    """The algorithm override beside the ledger, when this deployment lets
    one apply (live_algorithm.AlgorithmControl): read, never written."""
    bridge = config.live.fidelity.bridge if config.live.fidelity else None
    if not (deployment.caps.algorithm_changes or (bridge and bridge.allow_algorithm_changes)):
        return None
    try:
        data = json.loads(override_path(deployment.state_db).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    return data if isinstance(data, dict) else None


def algorithm_in_force(deployment: Deployment, config, status: dict) -> dict[str, Any]:
    """What the deployment trades, for its card. While its trader reports,
    what the trader says it is trading; otherwise what its next session
    will trade -- the config file's algorithm with any override laid over
    it. With where it came from, a profile's label when it is one, and the
    config file's own algorithm to compare against."""
    config_file = {
        "strategy_id": config.strategy.strategy_id,
        "strategy_params": dict(config.strategy.strategy_params or {}),
        "step": config.live.step,
        "profit_target": config.live.profit_target,
    }
    reported = status.get("algorithm") if not status.get("stale") else None
    override = _override(deployment, config)
    in_force = {key: (override or config_file).get(key) for key in _ALGORITHM_FIELDS}
    provenance = override
    if reported:
        if reported.get("strategy_id") != in_force["strategy_id"]:
            in_force["strategy_params"] = None  # the report names no parameters
        in_force.update(
            {key: reported.get(key) for key in ("strategy_id", "step", "profit_target")}
        )
        provenance = reported.get("override")
    provenance = provenance or {}
    profile = provenance.get("profile")
    label = None
    for candidate in _profiles():
        if candidate.id == profile or (
            profile is None
            and candidate.strategy_id == in_force["strategy_id"]
            and candidate.step == in_force["step"]
            and candidate.profit_target == in_force["profit_target"]
            and dict(candidate.strategy_params) == (in_force.get("strategy_params") or {})
        ):
            label = candidate.label
            break
    return {
        **in_force,
        "source": provenance.get("channel", "extension") if provenance else "config",
        "profile": profile,
        "label": label,
        "changed_by": provenance.get("changedBy"),
        "changed_at": provenance.get("changedAt"),
        "reason": provenance.get("reason"),
        # True when this is the trader's own report, not the files' account
        # of what its next session will trade.
        "reported": bool(reported),
        "config_file": config_file,
    }


def deployment_summary(deployment: Deployment) -> dict[str, Any]:
    """One deployment as the page's deployment strip shows it."""
    head = {
        "id": deployment.id,
        "label": deployment.label,
        "service": deployment.service,
        # The venue -- from the config, or the registry's word for it while
        # there is no config to say (a deployment not set up yet).
        "broker": deployment.broker or "alpaca",
    }
    if not deployment.config_path.exists():
        # Not a failure: a deployment registered before it was set up, like
        # a Fidelity one whose config (it names the account) is git-ignored.
        return {**head, "error": None, "setup": live_registry.setup_hint(deployment)}
    try:
        config = deployment.config()
        caps = deployment.caps
    except Exception as exc:
        return {**head, "error": f"its config does not load: {exc}"}
    head["broker"] = config.live.broker
    inbox = deployment.inbox()
    commands = inbox.history(limit=50) if inbox is not None else []
    status = run_state(inbox.status() if inbox is not None else None, time.time())
    return {
        **head,
        "error": None,
        "paper": config.live.paper_trading,
        "symbol": config.backtest.symbol,
        # The CONFIG FILE's algorithm; `algorithm` is the one in force.
        "strategy_id": config.strategy.strategy_id,
        "step": config.live.step,
        "profit_target": config.live.profit_target,
        "algorithm": algorithm_in_force(deployment, config, status),
        "controllable": inbox is not None,
        # Pausing new buys only reduces exposure, so it is always allowed.
        "caps": {"pause_buys": True, **caps.to_dict()},
        "status": status,
        "desired": inbox.desired() if inbox is not None else dict(_NOT_CONTROLLED),
        "ledger": _ledger(deployment),
        "pending": sum(1 for command in commands if command["status"] == "queued"),
    }


def _deployment(deployment_id: str) -> Deployment:
    try:
        return live_registry.get(deployment_id)
    except UnknownDeployment as exc:
        raise HTTPException(
            status_code=404, detail=f"No live deployment {deployment_id!r}."
        ) from exc


@router.get("/deployments")
def deployments() -> list[dict[str, Any]]:
    """Every deployment, for the strip across the top of the Live page."""
    return [deployment_summary(d) for d in live_registry.registry().values()]


@router.get("/deployments/{deployment_id}")
def deployment(deployment_id: str) -> dict[str, Any]:
    """One deployment: its summary, its ledger's full LiveState (null when
    it has no ledger yet) and its recent commands."""
    found = _deployment(deployment_id)
    try:
        state = state_payload(str(found.state_db))
    except DashboardError:
        state = None
    inbox = found.inbox()
    return {
        **deployment_summary(found),
        "state": state,
        "commands": inbox.history(limit=50) if inbox is not None else [],
    }


@router.get("/deployments/{deployment_id}/commands")
def commands(deployment_id: str, limit: int = Query(50, ge=1, le=500)) -> list[dict[str, Any]]:
    """Every command asked of this deployment, newest first, with its outcome."""
    inbox = _deployment(deployment_id).inbox()
    return inbox.history(limit=limit) if inbox is not None else []


_MAX_JOURNAL_SESSIONS = 10


@router.get("/deployments/{deployment_id}/bars")
def deployment_bars(
    deployment_id: str,
    sessions: int = Query(2, ge=1, le=_MAX_JOURNAL_SESSIONS),
) -> dict[str, Any]:
    """The minute bars this deployment's trader traded on -- its own feed,
    from its bar journal -- in /api/backtest/bars' shape. Empty, not an
    error, for a trader that has recorded none yet."""
    inbox = _deployment(deployment_id).inbox()
    rows = inbox.bars(sessions) if inbox is not None else []
    return {
        "bucket_s": 60,
        "rows": len(rows),
        "source": "the trader's own feed",
        "bars": [
            [int(r["t"]), r.get("o"), r.get("h"), r.get("l"), r.get("c"), r.get("v", 0.0)]
            for r in rows
        ],
    }


@router.get("/deployments/{deployment_id}/fills")
def deployment_fills(
    deployment_id: str,
    sessions: int = Query(1, ge=1, le=_MAX_JOURNAL_SESSIONS),
) -> list[dict[str, Any]]:
    """Every fill the trader booked in the last `sessions` sessions, oldest
    first, with what each sale fetched against what its lot cost -- the
    figure the ledger does not keep."""
    inbox = _deployment(deployment_id).inbox()
    return inbox.fills(sessions) if inbox is not None else []


@router.get("/deployments/{deployment_id}/activity")
def activity(
    deployment_id: str,
    limit: int = Query(200, ge=1, le=2000),
) -> list[dict[str, Any]]:
    """The revision log, newest first -- every mutation the loop made."""
    try:
        return load_activity(str(_deployment(deployment_id).state_db), limit=limit)
    except DashboardError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


# Bar files for the chart and the indicators. A constant, not a parameter:
# the server reads what is under data/, not a directory a browser names.
_BAR_ROOT = "data"


@router.get("/bars")
def bars(
    symbol: str = Query(..., min_length=1, max_length=16),
    limit: int = Query(780, ge=1, le=20_000),
) -> dict[str, Any]:
    """Recent minute bars for charting, as the same Bars shape
    /api/backtest/bars serves: [t, o, h, l, c, v] tuples, t in epoch
    seconds. A file with only a close column fills o/h/l from it and v
    with 0.

    Capped at 20,000 rows. These files are 60 MB and a million rows;
    serving one whole would stall the event loop for seconds and the
    browser for longer.
    """
    files = find_bar_files(symbol, _BAR_ROOT)
    if not files:
        raise HTTPException(status_code=404, detail=f"No bar file for {symbol!r}.")
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
    symbol: str = Query(..., min_length=1, max_length=16),
    period: int = Query(14, ge=2, le=200),
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
    files = find_bar_files(symbol, _BAR_ROOT)
    if not files:
        raise HTTPException(status_code=404, detail=f"No bar file for {symbol!r}.")
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
async def live_socket(socket: WebSocket, deployment: str) -> None:
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
    try:
        path = str(live_registry.get(deployment).state_db)
    except UnknownDeployment:
        await socket.send_json({"t": "err", "msg": f"No live deployment {deployment!r}."})
        await socket.close()
        return
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


__all__ = ["algorithm_in_force", "deployment_summary", "router", "run_state", "state_payload"]
