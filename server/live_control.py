"""The Live page's controls: commands queued for a deployment's trader.

--------------------------------------------------------------------
THIS MODULE CHANGES NOTHING ITSELF

It validates a command and queues it in the deployment's control directory
(engine/trading/control_inbox.py). The trader -- the only process that
writes its ledger -- applies it between ticks or between sessions, through
the circuit breaker and loop it trades with (engine/trading/operator_control.py),
and records what came of it. Nothing here opens a ledger, a breaker, a broker
or a shell; server/tests/test_server_capability.py holds it to that.

The module it replaces, control.py, wrote the halt into the ledger itself.
In the compose deployment that failed outright (the ledgers are mounted
read-only here), and where it succeeded the running loop never saw it: the
loop reads the halt once, at startup.

--------------------------------------------------------------------
WHAT THE BROWSER MAY ASK, AND OF WHOM

Deployments are named by id (server/live_registry.py), never by path. What
each may be asked is its own config's live.control, with the real-money
rules applied (LiveControlConfig.effective) -- a browser can do here exactly
what the reviewable file says, and pausing new buys, which only ever reduces
exposure, is always allowed. There is no liquidation command.

There is no login: the operator chose that (the UI is on a trusted LAN).
Two things stand in for it. Every command names its operator and records the
client address -- the control directory is the audit trail. And a request a
web page in some other tab sends from the operator's browser is refused:
browsers mark cross-site requests (Origin, Sec-Fetch-Site), and this checks.
A command with large consequences must also carry the deployment's id typed
back (`confirm`), checked here as well as asked by the page.
"""

from __future__ import annotations

import threading
import time
from typing import Any, Literal
from urllib.parse import urlparse

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field

from engine.core.exceptions import ConfigurationError
from engine.data.dashboard_data import DashboardError, load_state
from engine.trading.control_inbox import Command, InvalidCommand
from research.strategies import live_profiles
from research.strategies.live_algorithm import LEGACY_MODES, AlgorithmControl, impact
from research.strategies.param_schema import describe_params
from research.strategies.strategy_registry import STRATEGIES
from server import live_registry
from server.live import bridge_state, run_state
from server.live_registry import Deployment, UnknownDeployment

router = APIRouter(prefix="/api/live/deployments", tags=["control"])

# The Vite dev server's origins (server/app.py's CORS list): in development
# the page is served from there and proxied here.
_DEV_ORIGINS = {"http://127.0.0.1:5173", "http://localhost:5173"}

# Which config grant each command needs. None: always allowed.
_GRANT: dict[str, str | None] = {
    "pause_buys": None,
    "resume_buys": "resume_buys",
    "disable": "enable_disable",
    "enable": "enable_disable",
    "switch_algorithm": "algorithm_changes",
    "revert_algorithm": "algorithm_changes",
    "rewarm": "algorithm_changes",
    "reset_paper_ledger": "ledger_reset",
    # Read-only, through a Fidelity deployment's bridge host: never a grant.
    "check_connection": None,
}

# Commands the bridge host applies, not the trader: queued in its own inbox.
_BRIDGE_COMMANDS = {"check_connection"}

# Real money changes algorithm at most this often: a switch is a decision to
# watch play out, not a dial to turn while it trades.
REAL_MONEY_SWITCH_INTERVAL_SECONDS = 24 * 3600

# Trader states that mean a loop may be trading, or about to.
_ACTIVE = {
    "trading",
    "buys_paused",
    "winding_down",
    "starting",
    "restarting",
    "waiting_for_open",
    "waiting_for_broker",
}


def same_origin(request: Request) -> None:
    """Refuse a request another site's page made from the operator's
    browser. Scripts and curl send neither header and are let through: the
    controls have no login, by the operator's choice; this stops drive-by
    requests, not people on the LAN."""
    site = request.headers.get("sec-fetch-site")
    if site is not None and site not in ("same-origin", "none"):
        raise HTTPException(status_code=403, detail="Cross-site requests cannot control trading.")
    origin = request.headers.get("origin")
    if (
        origin is not None
        and origin not in _DEV_ORIGINS
        and urlparse(origin).netloc != request.headers.get("host")
    ):
        raise HTTPException(status_code=403, detail="Cross-site requests cannot control trading.")


class CommandRequest(BaseModel):
    """One command, as the Live page sends it."""

    type: Literal[
        "pause_buys",
        "resume_buys",
        "disable",
        "enable",
        "switch_algorithm",
        "revert_algorithm",
        "rewarm",
        "reset_paper_ledger",
        "check_connection",
    ]
    args: dict[str, Any] = Field(default_factory=dict)
    timing: Literal["now", "next_session", "when_flat"] = "now"
    reason: str = Field(..., min_length=3, max_length=500)
    operator: str = Field(..., min_length=1, max_length=80)
    idempotency_key: str | None = Field(None, max_length=100)
    # The deployment's id typed back, for a command with large consequences.
    confirm: str | None = Field(None, max_length=80)


class CancelRequest(BaseModel):
    operator: str = Field(..., min_length=1, max_length=80)


def _deployment(deployment_id: str) -> Deployment:
    try:
        deployment = live_registry.get(deployment_id)
    except UnknownDeployment as exc:
        raise HTTPException(
            status_code=404, detail=f"No live deployment {deployment_id!r}."
        ) from exc
    if not deployment.config_path.exists():
        raise HTTPException(status_code=409, detail=live_registry.setup_hint(deployment))
    return deployment


def _open_lots(deployment: Deployment) -> int:
    try:
        return len(load_state(str(deployment.state_db)).lots)
    except DashboardError:
        return 0


def _checked_args(body: CommandRequest, deployment: Deployment) -> dict[str, Any]:
    """Each command's own arguments, and nothing else."""
    args = body.args
    if body.type == "switch_algorithm":
        result = check_change(deployment, args)
        if not result["ok"]:
            raise HTTPException(status_code=422, detail="; ".join(result["errors"]))
        legacy = {"legacy_lots": result["legacy_lots"]}
        if "profile_id" in args:
            return {"profile_id": str(args["profile_id"]), **legacy}
        return {**result["change"], **legacy}
    if body.type == "disable":
        mode = args.get("mode", "now")
        if mode not in ("now", "wind_down"):
            raise HTTPException(status_code=422, detail="disable mode must be now or wind_down")
        return {"mode": mode}
    if body.type == "resume_buys":
        reset = args.get("reset_drawdown_baseline", False)
        if not isinstance(reset, bool):
            raise HTTPException(
                status_code=422, detail="reset_drawdown_baseline must be true or false"
            )
        return {"reset_drawdown_baseline": reset}
    if args:
        raise HTTPException(status_code=422, detail=f"{body.type} takes no arguments")
    return {}


def confirmation_needed(deployment: Deployment, kind: str, args: dict[str, Any]) -> str | None:
    """Why this command needs the deployment's id typed back, or None.

    The page asks for the same thing; checking it here as well means a
    script or a stale page cannot skip it."""
    if not deployment.paper and kind not in ("pause_buys", "check_connection"):
        return "this deployment trades real money"
    if kind == "reset_paper_ledger":
        return "the ledger it has is archived and a fresh one started"
    if kind == "disable" and args.get("mode") == "now":
        lots = _open_lots(deployment)
        if lots:
            return f"{lots} open lot{'' if lots == 1 else 's'} would get no exits while disabled"
    return None


def _check_preconditions(deployment: Deployment, kind: str) -> None:
    """What must already be true for a command to make sense (409 if not).
    The trader checks again when it applies it."""
    inbox = deployment.inbox()
    if kind == "check_connection":
        bridge = deployment.bridge_inbox()
        if deployment.config().live.broker != "fidelity" or bridge is None:
            raise HTTPException(
                status_code=409,
                detail=f"{deployment.id} has no Fidelity bridge host to check a connection with.",
            )
        return
    if kind == "reset_paper_ledger" and inbox is not None and inbox.desired()["enabled"]:
        raise HTTPException(
            status_code=409,
            detail=(
                f"Disable {deployment.id} first: a ledger is reset only while no session can start."
            ),
        )
    if kind == "switch_algorithm" and not deployment.paper and inbox is not None:
        horizon = (time.time() - REAL_MONEY_SWITCH_INTERVAL_SECONDS) * 1e9
        recent = [
            row
            for row in inbox.history(limit=500)
            if row["type"] == "switch_algorithm"
            and row["seq"] >= horizon
            and row["status"] in ("queued", "applying", "applied")
        ]
        if recent:
            raise HTTPException(
                status_code=409,
                detail=(
                    "Real money switches algorithm at most once a day; the last was asked "
                    f"{recent[0]['created_at']} by {recent[0]['operator']}."
                ),
            )
    if kind == "enable":
        other = _same_account_trading(deployment)
        if other is not None:
            raise HTTPException(
                status_code=409,
                detail=(
                    f"{other.id} trades the same Alpaca account and is enabled. Two loops on "
                    "one account diverge both ledgers from the venue -- disable it first."
                ),
            )


def _same_account_trading(deployment: Deployment) -> Deployment | None:
    """Another enabled deployment whose trader reports the same account tag
    (operator_control.account_fingerprint), or None. Unknown -- a trader
    that has not reported -- is not a match: this guards what can be seen."""
    now = time.time()
    inbox = deployment.inbox()
    mine = run_state(inbox.status(), now) if inbox is not None else None
    account = (mine or {}).get("account")
    if not account:
        return None
    for other in live_registry.registry().values():
        if other.id == deployment.id or other.inbox() is None:
            continue
        theirs = run_state(other.inbox().status(), now)
        if (
            not theirs["stale"]
            and theirs.get("account") == account
            and theirs["state"] in _ACTIVE
            and other.inbox().desired()["enabled"]
        ):
            return other
    return None


def new_pause(deployment: Deployment) -> bool:
    """Whether a pause would change anything: buying is not already halted."""
    try:
        return not load_state(str(deployment.state_db)).halted
    except DashboardError:
        return True


# --------------------------------------------------------------------
# The algorithm: what is traded, what it could be, and what a change does
# --------------------------------------------------------------------


def algorithm_control(deployment: Deployment) -> AlgorithmControl:
    """The deployment's algorithm as its trader would build it -- used here
    to READ (the override beside its ledger, read-only in this container)
    and to dry-run a change. Never to set one: the trader does that."""
    config = deployment.config()
    grants = deployment.caps
    fidelity = config.live.fidelity
    return AlgorithmControl(
        config,
        state_db=deployment.state_db,
        registry=STRATEGIES,
        allowed=bool(fidelity and fidelity.bridge.allow_algorithm_changes),
        web_allowed=grants.algorithm_changes,
        profiles_only=grants.profiles_only,
        config_path=deployment.config_path,
    )


_capable_cache: dict[tuple, list[dict[str, Any]]] = {}
_capable_lock = threading.Lock()


def _strategies(deployment: Deployment, control: AlgorithmControl) -> list[dict[str, Any]]:
    """Every strategy with its parameter schema and whether it can trade
    live HERE -- cached per config version: building one per strategy loads
    the ML ones' models."""
    key = (str(deployment.config_path), deployment.config_path.stat().st_mtime)
    with _capable_lock:
        cached = _capable_cache.get(key)
    if cached is not None:
        return cached
    out = []
    for strategy_id in sorted(STRATEGIES):
        capable, why = control.live_capable(strategy_id)
        try:
            params = describe_params(strategy_id, STRATEGIES[strategy_id])
        except Exception:
            params = []
        out.append({"id": strategy_id, "params": params, "live_capable": capable, "why": why})
    with _capable_lock:
        _capable_cache[key] = out
    return out


def _profiles(deployment: Deployment) -> list[dict[str, Any]]:
    symbol = deployment.config().backtest.symbol
    out = []
    for profile in live_profiles.load_profiles().values():
        why = None
        if not profile.fits(symbol):
            why = f"researched on {', '.join(profile.symbols)}, not {symbol}"
        elif not deployment.paper and not profile.promoted():
            why = "real money needs a passing paper promotion, and it names none"
        out.append({**profile.to_wire(), "usable": why is None, "why": why})
    return out


def _open_lots_detail(deployment: Deployment) -> list[dict[str, Any]]:
    try:
        lots = load_state(str(deployment.state_db)).lots
    except DashboardError:
        return []
    return [{"px": lot.buy_price, "qty": lot.shares, "target": lot.profit_target} for lot in lots]


def check_change(deployment: Deployment, args: dict[str, Any]) -> dict[str, Any]:
    """A proposed switch, validated as the trader will validate it -- and
    what it would do to the open book. Writes nothing."""
    caps = deployment.caps
    if not caps.algorithm_changes:
        return {"ok": False, "errors": ["its config does not grant live.control.algorithm_changes"]}
    control = algorithm_control(deployment)
    legacy_lots = args.get("legacy_lots") or "keep"
    if legacy_lots not in LEGACY_MODES:
        return {"ok": False, "errors": [f"legacy_lots must be one of {', '.join(LEGACY_MODES)}"]}
    profile_id = args.get("profile_id")
    if profile_id:
        try:
            profile = live_profiles.get(str(profile_id))
        except ConfigurationError as exc:
            return {"ok": False, "errors": [str(exc)]}
        usable = next(p for p in _profiles(deployment) if p["id"] == profile.id)
        if not usable["usable"]:
            return {"ok": False, "errors": [f"profile {profile.id}: {usable['why']}"]}
        proposed = profile.change()
    elif caps.profiles_only:
        return {"ok": False, "errors": ["this deployment switches only to committed profiles"]}
    else:
        proposed = {
            key: args.get(key)
            for key in ("strategy_id", "strategy_params", "step", "profit_target")
        }
    try:
        change, _config = control.check(proposed)
    except ConfigurationError as exc:
        return {"ok": False, "errors": [str(exc)]}
    current = control.current()
    return {
        "ok": True,
        "errors": [],
        "change": change,
        "current": current,
        "legacy_lots": legacy_lots,
        "impact": impact(current, change, _open_lots_detail(deployment), legacy_lots),
        "typed": confirmation_needed(deployment, "switch_algorithm", change),
    }


@router.get("/{deployment_id}/algorithm")
def algorithm(deployment_id: str) -> dict[str, Any]:
    """What the deployment trades, what its config file says, who changed it,
    the profiles it may switch to and every strategy's live capability."""
    deployment = _deployment(deployment_id)
    control = algorithm_control(deployment)
    inbox = deployment.inbox()
    status = run_state(inbox.status(), time.time()) if inbox is not None else None
    live = (status or {}).get("algorithm") if status and not status["stale"] else None
    current = control.current()
    override = control.override_info()
    return {
        "editable": deployment.caps.algorithm_changes,
        "profiles_only": deployment.caps.profiles_only,
        "paper": deployment.paper,
        "symbol": deployment.config().backtest.symbol,
        "current": current,
        "config_file": control.config_file_algorithm(),
        "source": override["channel"] if override else "config",
        "override": override,
        # What the running loop reports trading -- differs from `current`
        # between a change being written and the loop's next tick.
        "live": live,
        "pending": bool(
            live
            and (
                live.get("strategy_id") != current["strategy_id"]
                or live.get("step") != current["step"]
                or live.get("profit_target") != current["profit_target"]
            )
        ),
        "profiles": _profiles(deployment),
        "strategies": _strategies(deployment, control),
    }


class ChangeRequest(BaseModel):
    """A switch to check: a committed profile, or (paper) the change itself."""

    profile_id: str | None = Field(None, max_length=80)
    strategy_id: str | None = Field(None, max_length=80)
    strategy_params: dict[str, Any] = Field(default_factory=dict)
    step: float | None = None
    profit_target: float | None = None
    # What to do with the lots held at the switch (live_algorithm.LEGACY_MODES).
    legacy_lots: Literal["keep", "exit_at_cost", "wait"] = "keep"


@router.post("/{deployment_id}/algorithm/check", dependencies=[Depends(same_origin)])
def algorithm_check(deployment_id: str, body: ChangeRequest) -> dict[str, Any]:
    """Dry-run a switch: the errors the trader would refuse it with, or what
    it would do to the book. Writes nothing and queues nothing."""
    deployment = _deployment(deployment_id)
    args = (
        {"profile_id": body.profile_id, "legacy_lots": body.legacy_lots}
        if body.profile_id
        else body.model_dump(exclude={"profile_id"})
    )
    return check_change(deployment, args)


@router.post("/{deployment_id}/commands", status_code=202, dependencies=[Depends(same_origin)])
def queue_command(deployment_id: str, body: CommandRequest, request: Request) -> dict[str, Any]:
    """Queue a command for the deployment's trader. 202: accepted, not yet
    applied -- the command's own status says when it is."""
    deployment = _deployment(deployment_id)
    inbox = deployment.bridge_inbox() if body.type in _BRIDGE_COMMANDS else deployment.inbox()
    if inbox is None:
        raise HTTPException(
            status_code=409,
            detail=f"{deployment.id} has no control directory in config/deployments.yaml.",
        )
    grant = _GRANT[body.type]
    if grant is not None and not getattr(deployment.caps, grant):
        raise HTTPException(
            status_code=403,
            detail=(
                f"{deployment.id} does not take {body.type} from the Live page: set "
                f"live.control.{grant}: true in {deployment.config_path.name} to allow it."
            ),
        )
    args = _checked_args(body, deployment)
    _check_preconditions(deployment, body.type)
    reason = confirmation_needed(deployment, body.type, args)
    if reason and body.confirm != deployment.id:
        raise HTTPException(
            status_code=409,
            detail=f"Type {deployment.id} to confirm: {reason}.",
        )
    client = request.client.host if request.client else None
    try:
        pause = None
        if body.type == "switch_algorithm" and body.timing == "when_flat" and new_pause(deployment):
            # A deployment that keeps buying is never flat: pause first --
            # created first too, so it is first in the queue and the log.
            pause = Command.new(
                "pause_buys",
                reason=f"winding down to switch algorithms: {body.reason}",
                operator=body.operator,
                client=client,
            )
        command = Command.new(
            body.type,
            reason=body.reason,
            operator=body.operator,
            args=args,
            timing=body.timing,
            client=client,
            idempotency_key=body.idempotency_key,
        )
        if pause is not None and inbox.find_by_key(body.idempotency_key or "\0") is None:
            inbox.enqueue(pause)
        queued, new = inbox.enqueue(command)
    except InvalidCommand as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    if body.type in _BRIDGE_COMMANDS:
        host = bridge_state(inbox.status(), command.seq / 1e9)
        warning = (
            f"{deployment.id}'s bridge host is not running; this applies when it next starts, "
            "if it has not expired by then (docker compose --profile fidelity up -d "
            "fidelity-bridge)."
            if host is None or host["stale"]
            else None
        )
    else:
        status = run_state(inbox.status(), command.seq / 1e9)
        # Queued all the same: it applies when the trader next runs, unless it
        # expires first. Said, rather than left for the operator to wonder.
        warning = (
            f"{deployment.id}'s trader is not running ({status['detail']}); this applies "
            "when it next starts, if it has not expired by then."
            if status["stale"]
            else None
        )
    return {
        "command": next(row for row in inbox.history(limit=500) if row["id"] == queued.id),
        "new": new,
        "warning": warning,
    }


@router.post(
    "/{deployment_id}/commands/{command_id}/cancel",
    dependencies=[Depends(same_origin)],
)
def cancel_command(deployment_id: str, command_id: str, body: CancelRequest) -> dict[str, Any]:
    """Withdraw a queued command. 409 once a trader has taken it."""
    deployment = _deployment(deployment_id)
    result = None
    for inbox in (deployment.inbox(), deployment.bridge_inbox()):
        if inbox is not None and result is None:
            result = inbox.cancel(command_id, body.operator)
    if result is None:
        raise HTTPException(status_code=409, detail="That command is not queued any more.")
    return result


__all__ = ["CommandRequest", "confirmation_needed", "router", "same_origin"]
