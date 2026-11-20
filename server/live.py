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
import os
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException, Query, WebSocket, WebSocketDisconnect

from engine.data.dashboard_data import (
    DashboardError,
    find_bar_files,
    load_activity,
    load_bars,
    load_state,
)
from research.risk_overlay.archive import ReportArchive, session_overlay
from research.risk_overlay.preview import overlay_settings, takes_reports
from research.strategies import live_profiles
from research.strategies.live_algorithm import algorithm_summary, override_path
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
        # A start that stopped: the stage it stopped in, and whether it is
        # tried again on its own (the broker could not be reached yet).
        "stage",
        "retryable",
        # Which deployment the trader says it is, and the ledger it trades
        # (its file's name and a one-way tag of its path).
        "deployment",
        "ledger",
        # On its venue's windows (live.sessions): the engine's own readiness,
        # apart from the broker's, and how the last trading window went.
        "engine",
        "last_window",
        # The session's risk report: in force (enforce) or suggested
        # (advisory), or none (research/risk_overlay/live.py).
        "risk_overlay",
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


def bridge_state(status: dict | None, now: float) -> dict[str, Any] | None:
    """A Fidelity deployment's bridge host as it last reported -- its
    readiness, the extension's connection, what is attached -- with
    `stale` when it has gone quiet (fidelity_gateway/bridge/host.py writes
    every STATUS_SECONDS). None when no bridge host has ever reported here:
    a deployment whose trading loop holds the bridge itself."""
    if not status:
        return None
    try:
        age = now - datetime.fromisoformat(status["updated_at"]).timestamp()
    except (KeyError, TypeError, ValueError):
        age = None
    heartbeat = float(status.get("heartbeat_seconds") or 15.0)
    stale = (
        age is None
        or age > max(3 * heartbeat, _STALE_FLOOR_SECONDS)
        or status.get("state") == "stopped"
    )
    report = {key: value for key, value in status.items() if key != "pid"}
    report["stale"] = stale
    report["age_s"] = round(age, 1) if age is not None else None
    return report


def command_history(deployment: Deployment, limit: int = 50) -> list[dict[str, Any]]:
    """Every command asked of the deployment, newest first: its trader's
    and -- for Fidelity -- its bridge host's (check_connection)."""
    rows: list[dict[str, Any]] = []
    for inbox in (deployment.inbox(), deployment.bridge_inbox()):
        if inbox is not None:
            rows.extend(inbox.history(limit=limit))
    rows.sort(key=lambda row: row["seq"], reverse=True)
    return [_slim_command(row) for row in rows[:limit]]


def _slim_command(row: dict[str, Any]) -> dict[str, Any]:
    """A risk report travels whole as its command's arguments (~6 KB); the
    log names it instead -- GET .../risk-reports?full=true has the report."""
    report = (row.get("args") or {}).get("report")
    if row.get("type") != "apply_risk_report" or not isinstance(report, dict):
        return row
    from engine.core.risk_report import report_sha256

    stub = {
        "symbol": report.get("symbol"),
        "as_of": report.get("as_of"),
        "sha256": report_sha256(report),
    }
    return {**row, "args": {"report": stub}}


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
        # What it does, in a line -- the same words the extension's popup
        # shows (live_algorithm.algorithm_summary).
        "summary": algorithm_summary(in_force, config.backtest.symbol),
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
    commands = command_history(deployment)
    now = time.time()
    status = run_state(inbox.status() if inbox is not None else None, now)
    bridge_inbox = deployment.bridge_inbox() if config.live.broker == "fidelity" else None
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
        "caps": {"pause_buys": True, **caps.grants()},
        # Whether the Live page may send it the nightly risk report, and how
        # its config uses one (docs/daily_risk_report_plan.md).
        "risk_reports": {**_risk_reports_summary(config, caps), "last": _last_report(commands)},
        "status": status,
        "desired": inbox.desired() if inbox is not None else dict(_NOT_CONTROLLED),
        "ledger": _ledger(deployment),
        "pending": sum(1 for command in commands if command["status"] == "queued"),
        # A Fidelity deployment's bridge host: up between sessions, so this
        # is what says whether the connection is ready when no loop runs.
        "bridge": bridge_state(bridge_inbox.status(), now) if bridge_inbox is not None else None,
    }


def _now() -> datetime:
    """The clock the risk-report routes read (tests replace it)."""
    return datetime.now().astimezone()


def _last_report(commands: list[dict[str, Any]]) -> dict[str, Any] | None:
    """The newest apply_risk_report and what came of it: a refusal is
    something the page says (web/src/lib/attention.ts)."""
    for row in commands:  # newest first
        if row.get("type") == "apply_risk_report":
            return {
                "id": row.get("id"),
                "status": row.get("status"),
                "detail": row.get("detail"),
                "created_at": row.get("created_at"),
                "finished_at": row.get("finished_at"),
                "operator": row.get("operator"),
            }
    return None


def _risk_reports_summary(config, caps) -> dict[str, Any]:
    takes, why = takes_reports(config, caps)
    return {"takes": takes, "why_not": why, "settings": overlay_settings(config)}


def upcoming_session(now: datetime):
    """The session a report sent now would be for: tomorrow's after today's
    close, today's before it (engine/core/risk_report.target_session, with a
    moment inside a session read as that session)."""
    from engine.core.trading_calendar import EASTERN, SESSION_CLOSE, is_session, next_session

    local = now.astimezone(EASTERN)
    day = local.date()
    if is_session(day) and local.time() < SESSION_CLOSE:
        return day
    return next_session(day)


def _slim_entry(entry: dict[str, Any], full: bool) -> dict[str, Any]:
    mapped = entry.get("mapped") or {}
    row = {
        "session": entry.get("session"),
        "source": entry.get("source"),
        "received_at": entry.get("received_at"),
        "operator": entry.get("operator"),
        "as_of": entry.get("as_of"),
        "sha256": entry.get("sha256"),
        "mode": entry.get("mode"),
        "mapping_id": entry.get("mapping_id"),
        "outcome": entry.get("outcome"),
        "summary": entry.get("summary"),
        "overlay": entry.get("overlay"),
        "tier": mapped.get("tier"),
        "score": mapped.get("score"),
        "components": mapped.get("components"),
        "abstained": mapped.get("abstained"),
        "reasons": mapped.get("reasons") or [],
        "warnings": sum(1 for f in entry.get("findings") or [] if f.get("level") == "warning"),
        "start": entry.get("start"),
        "receipts": entry.get("receipts") or [],
    }
    if full:
        row["report"] = entry.get("report")
        row["findings"] = entry.get("findings")
    return row


@router.get("/deployments/{deployment_id}/risk-reports")
def deployment_risk_reports(
    deployment_id: str,
    sessions: int = Query(30, ge=1, le=400),
    full: bool = False,
) -> dict[str, Any]:
    """The nightly risk reports this deployment's trader archived
    (risk_reports/ in its control directory, research/risk_overlay/archive.py),
    newest first, and the overlay the next session would trade under as the
    trader would read it now. Read-only; `full` adds each raw report."""
    found = _deployment(deployment_id)
    try:
        config = found.config()
        caps = found.caps
    except Exception as exc:
        raise HTTPException(status_code=409, detail=f"its config does not load: {exc}") from exc
    summary = _risk_reports_summary(config, caps)
    if found.control_dir is None:
        return {**summary, "next": None, "sessions": []}
    archive = ReportArchive.in_control_dir(found.control_dir)
    entries = archive.entries()[-sessions:]
    upcoming = None
    if config.risk.overlay is not None:
        now = _now()
        session = upcoming_session(now)
        overlay, entry = session_overlay(archive, session, config.risk.overlay, as_of=now)
        upcoming = {
            "session": session.isoformat(),
            "overlay": overlay.to_dict(),
            "summary": overlay.describe()
            if entry or overlay.changes_trading
            else "no report: trading as configured",
            "has_report": entry is not None,
        }
    return {
        **summary,
        "next": upcoming,
        "sessions": [_slim_entry(e, full) for e in reversed(entries)],
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
    return {
        **deployment_summary(found),
        "state": state,
        "commands": command_history(found),
    }


@router.get("/deployments/{deployment_id}/commands")
def commands(deployment_id: str, limit: int = Query(50, ge=1, le=500)) -> list[dict[str, Any]]:
    """Every command asked of this deployment, newest first, with its outcome."""
    return command_history(_deployment(deployment_id), limit)


_MAX_EVENT_HOURS = 14 * 24


@router.get("/deployments/{deployment_id}/bridge/events")
def bridge_events(
    deployment_id: str,
    hours: int = Query(48, ge=1, le=_MAX_EVENT_HOURS),
    limit: int = Query(1000, ge=1, le=5000),
) -> list[dict[str, Any]]:
    """A Fidelity deployment's bridge host's journal, oldest first: the
    extension connecting and disconnecting (with why), refusals, Fidelity
    signing in and out, the trading switch, sessions attaching, readiness
    changing, account checks. Empty for a deployment with no bridge host."""
    inbox = _deployment(deployment_id).bridge_inbox()
    if inbox is None:
        return []
    since = time.time() - hours * 3600
    rows = [row for row in inbox.events(days=hours // 24 + 2) if float(row["t"]) >= since]
    return rows[-limit:]


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
    since: float | None = Query(None, ge=0),
) -> list[dict[str, Any]]:
    """Every fill the trader booked in the last `sessions` sessions, oldest
    first, with what each sale fetched against what its lot cost -- the
    figure the ledger does not keep. With `since` (epoch seconds), only
    those booked after it: what a page that already has the rest polls for."""
    inbox = _deployment(deployment_id).inbox()
    return _after(inbox.fills(sessions) if inbox is not None else [], since)


@router.get("/deployments/{deployment_id}/orders")
def deployment_orders(
    deployment_id: str,
    sessions: int = Query(1, ge=1, le=_MAX_JOURNAL_SESSIONS),
    since: float | None = Query(None, ge=0),
) -> list[dict[str, Any]]:
    """Each moment of each order's life in the last `sessions` sessions,
    oldest first: placed (its window and limit), partly filled, filled,
    cancel requested (and why: its time-to-live, its window's end), and how
    it ended -- the proof a limit order filled or did not. `since` as for
    fills."""
    inbox = _deployment(deployment_id).inbox()
    return _after(inbox.orders(sessions) if inbox is not None else [], since)


def _after(rows: list[dict[str, Any]], since: float | None) -> list[dict[str, Any]]:
    """The journal rows after `since`: a busy paper trial books hundreds of
    fills a session, and a page polling every 15 seconds needs only the new."""
    if since is None:
        return rows
    return [row for row in rows if float(row.get("t", 0)) > since]


def _slim_risk(part: Any) -> dict[str, Any] | None:
    if not isinstance(part, dict):
        return None
    score = part.get("score") if isinstance(part.get("score"), dict) else None
    return {
        "tier": part.get("tier"),
        "abstained": part.get("abstained"),
        "mode": part.get("mode"),
        "summary": part.get("summary"),
        "followed": (part.get("followed") or {}).get("status"),
        "score": (
            {
                key: score.get(key)
                for key in ("return_pct", "in_90", "in_50", "pit", "skill", "move_ratio")
            }
            if score
            else None
        ),
        "shadows": part.get("shadows"),
    }


def _tracking_dir() -> Path:
    """Where tools/track_live.py keeps its record (its --out); the compose
    file mounts the same folder into `web`. VAI_TRACKING_DIR for tests."""
    return Path(os.environ.get("VAI_TRACKING_DIR") or "output/tracking")


@router.get("/deployments/{deployment_id}/tracking")
def deployment_tracking(
    deployment_id: str,
    sessions: int = Query(120, ge=1, le=1000),
) -> dict[str, Any]:
    """Live against backtest, session by session, oldest first: what the
    `tracking` service (tools/track_live.py) recorded for this deployment --
    whether the session was traded, its buys, sells and realised profit, how
    its orders filled, a Fidelity bridge's minutes not ready in the regular
    session, and the shadow backtest of the same days where it ran. Read
    from that tool's sessions.jsonl; `sessions` is empty, not an error,
    until it has run. The id is one config/deployments.yaml names: no route
    takes a path."""
    found = _deployment(deployment_id)
    path = _tracking_dir() / found.id / "sessions.jsonl"
    rows: list[dict[str, Any]] = []
    updated_at: float | None = None
    try:
        text = path.read_text(encoding="utf-8")
        updated_at = path.stat().st_mtime
    except OSError:
        text = ""
    for line in text.splitlines():
        try:
            row = json.loads(line)
        except ValueError:
            continue
        if not isinstance(row, dict) or not row.get("session"):
            continue
        acts = row.get("activity") or {}
        done = row.get("execution") or {}
        shadow = row.get("shadow") or None
        bridge = row.get("bridge_not_ready_regular") or None
        rows.append(
            {
                "session": str(row["session"]),
                "status": (row.get("availability") or {}).get("status", "unknown"),
                "buys": acts.get("buys", 0),
                "sells": acts.get("sells", 0),
                "realized_pnl": acts.get("realized_pnl", 0.0),
                "loss_sales": acts.get("loss_sales", 0),
                "orders_placed": acts.get("orders_placed", 0),
                "fill_share": done.get("fill_share"),
                "live_bps": done.get("live_bps"),
                "model_bps": done.get("model_bps"),
                "not_ready_minutes": bridge.get("minutes") if isinstance(bridge, dict) else None,
                # The session's risk report: its tier, whether its suggestion
                # was followed, its forecast scored (tools/score_risk_reports.py).
                "risk": _slim_risk(row.get("risk")),
                "shadow": (
                    {
                        "buys": shadow.get("buys", 0),
                        "sells": shadow.get("sells", 0),
                        "realized_pnl": shadow.get("realized_pnl", 0.0),
                        "return_pct": shadow.get("return_pct", 0.0),
                    }
                    if isinstance(shadow, dict)
                    else None
                ),
            }
        )
    rows.sort(key=lambda r: r["session"])
    return {"sessions": rows[-sessions:], "updated_at": updated_at}


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


__all__ = [
    "algorithm_in_force",
    "bridge_state",
    "command_history",
    "deployment_summary",
    "router",
    "run_state",
    "state_payload",
]
