"""Algorithm management: a backtest cell becomes a candidate, a candidate
runs a paper trial, and one that is promoted is published as a live profile.

THE ONLY SERVER MODULE THAT WRITES profiles. It writes exactly two places and
nothing it is handed names a path:

  output/algorithms/<id>/candidate.json   the library (git-ignored, ours)
  config/live_profiles/<id>.yaml          a published profile, with
  config/live_profiles/promotions/<id>.json   the evaluation it names

The profile folder is mounted read-write into `web` alone (docker-compose.yml);
the traders see the same folder read-only. A published profile is plain
uncommitted work in git, headed to say so: the operator reviews and commits it.
Real money still needs `Profile.promoted()` (a passing evaluation in that
promotions folder), the typed deployment id and the once-a-day limit.

A candidate's figures come from the stored run, never from the browser.
"""

from __future__ import annotations

import json
import os
import re
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal

import yaml
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel, Field

from engine.core.exceptions import ConfigurationError
from engine.promotion_record import build_record, evaluate, unmeasured
from research.strategies import live_profiles
from server import history, history_query, live_control, live_registry

router = APIRouter(prefix="/api/algorithms", tags=["algorithms"])

_ROOT = Path(__file__).resolve().parent.parent
_ID = re.compile(r"^[a-z0-9][a-z0-9-]{0,60}$")
_SESSIONS_KEPT = 60
_HEADER = (
    "# Published from the web on {when} by {who}: review it and commit it.\n"
    "# Real money may switch to it only while evidence.promotion names a passing\n"
    "# evaluation ({kind}).\n"
)


def library_dir() -> Path:
    configured = os.environ.get("VAI_ALGORITHMS_DIR")
    return Path(configured) if configured else _ROOT / "output" / "algorithms"


# -- storage ---------------------------------------------------------------------------


def _slug(text: str) -> str:
    return re.sub(r"-+", "-", re.sub(r"[^a-z0-9-]+", "-", text.lower())).strip("-")


def _candidate_path(candidate_id: str) -> Path:
    # Built here from a validated id: no request supplies a path.
    if not _ID.match(candidate_id):
        raise HTTPException(status_code=404, detail="No such candidate.")
    return library_dir() / candidate_id / "candidate.json"


def _read(candidate_id: str) -> dict[str, Any]:
    path = _candidate_path(candidate_id)
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise HTTPException(status_code=404, detail="No such candidate.") from exc


def _write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(temporary, path)


def _save(candidate: dict[str, Any]) -> None:
    _write_json(_candidate_path(candidate["id"]), candidate)


def _now() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds")


def candidates() -> list[dict[str, Any]]:
    root = library_dir()
    if not root.is_dir():
        return []
    found = []
    for path in sorted(root.glob("*/candidate.json")):
        try:
            found.append(json.loads(path.read_text(encoding="utf-8")))
        except (OSError, ValueError):
            continue
    return found


# The commands that change which algorithm a deployment trades: the next one
# applied after a trial's own switch ends that trial's window.
_ALGORITHM_COMMANDS = ("switch_algorithm", "revert_algorithm")
_COMMANDS_READ = 1000


def _epoch(iso: str | None) -> float | None:
    try:
        return datetime.fromisoformat(str(iso)).timestamp() if iso else None
    except ValueError:
        return None


def _iso(seconds: float | None) -> str | None:
    if seconds is None:
        return None
    return datetime.fromtimestamp(seconds, UTC).isoformat(timespec="seconds")


def _trial_window(trial: dict[str, Any]) -> dict[str, Any]:
    """When the trial's algorithm actually traded its deployment, from the
    deployment's own command record: from the moment its switch was APPLIED
    (not queued -- a next-session switch leaves the old algorithm trading
    until then) until the next algorithm change applied after it, by another
    trial or by hand. A deployment's journals hold every algorithm it ran, so
    this window is all a trial may count.

    state: pending (its switch is still queued), running, ended, never_ran
    (its switch was rejected, expired, superseded or cancelled) or unknown
    (the deployment or its control directory is gone). A trial recorded
    without its command id counts from when it was queued, as before."""
    window: dict[str, Any] = {"state": "unknown", "from": None, "until": None, "detail": ""}
    try:
        inbox = live_registry.get(trial["deployment"]).inbox()
    except live_registry.UnknownDeployment:
        return {**window, "detail": "Its deployment is gone."}
    if inbox is None:
        return {**window, "detail": "The deployment has no control directory."}
    history = inbox.history(limit=_COMMANDS_READ)
    command_id = trial.get("command")
    own = next((row for row in history if row["id"] == command_id), None)
    if command_id and own is None:
        return {**window, "detail": "Its switch command is no longer on record."}
    if own is not None and own["status"] in ("queued", "applying"):
        return {
            **window,
            "state": "pending",
            "detail": f"Its switch is {own['status']} ({own.get('timing')}); nothing counts yet.",
        }
    if own is not None and own["status"] != "applied":
        return {
            **window,
            "state": "never_ran",
            "detail": f"Its switch was {own['status']}"
            + (f": {own['detail']}" if own.get("detail") else "."),
        }
    start = _epoch(own.get("finished_at")) if own is not None else float(trial["started_at"])
    if start is None:
        return {**window, "detail": "Its switch has no applied time."}
    later = sorted(
        (
            (moment, row)
            for row in history
            if row["type"] in _ALGORITHM_COMMANDS
            and row["status"] == "applied"
            and row["id"] != command_id
            and (moment := _epoch(row.get("finished_at"))) is not None
            and moment > start
        ),
        key=lambda pair: pair[0],
    )
    if later:
        moment, row = later[0]
        return {
            "state": "ended",
            "from": start,
            "until": moment,
            "detail": f"Ended {_iso(moment)}: {row.get('reason') or row['type']}"
            f" (by {row.get('operator') or 'unknown'}).",
        }
    return {"state": "running", "from": start, "until": None, "detail": ""}


def _trial_over(candidate: dict[str, Any]) -> bool:
    trial = candidate.get("trial")
    return bool(trial) and _trial_window(trial)["state"] in ("ended", "never_ran")


def _stage(candidate: dict[str, Any]) -> str:
    if (live_profiles.profiles_dir() / f"{candidate['id']}.yaml").exists():
        return "published"
    if (candidate.get("promotion") or {}).get("passed") is True:
        return "promoted"
    if candidate.get("trial"):
        return "paper_trial"
    return "candidate"


def _change(candidate: dict[str, Any]) -> dict[str, Any]:
    return {
        "strategy_id": candidate["strategy_id"],
        "strategy_params": candidate["strategy_params"],
        "step": candidate["step"],
        "profit_target": candidate["profit_target"],
    }


def _wire(candidate: dict[str, Any]) -> dict[str, Any]:
    """The candidate, its stage, and the paper deployments that would take it.

    "Would take it" is the TRADER's own check (AlgorithmControl.check, as
    live_control dry-runs a switch), not the fund alone: a composite whose
    sell policy may sell below cost needs execution.allow_signal_exit in the
    deployment's file, a regular-session buyer refuses extended hours, and
    the page cannot change either. A paper deployment on the right fund that
    refuses it is listed under `paper_refused` with the trader's reason."""
    symbol = candidate["symbols"][0]
    fits, refused = [], []
    for deployment in live_registry.registry().values():
        try:
            if not deployment.paper or deployment.config().backtest.symbol != symbol:
                continue
            live_control.algorithm_control(deployment).check(_change(candidate))
        except ConfigurationError as exc:
            refused.append({"deployment": deployment.id, "reason": str(exc)})
            continue
        except Exception:  # a deployment whose config is missing fits nothing
            continue
        fits.append(deployment.id)
    trial = candidate.get("trial")
    if trial:
        window = _trial_window(trial)
        trial = {
            **trial,
            "window": {**window, "from": _iso(window["from"]), "until": _iso(window["until"])},
        }
    return {
        **candidate,
        "trial": trial,
        "stage": _stage(candidate),
        "paper_deployments": fits,
        **({"paper_refused": refused} if refused else {}),
    }


def _composed_names(cell_params: dict[str, Any]) -> tuple[str, str] | None:
    buy, sell = cell_params.get("buy"), cell_params.get("sell")
    if isinstance(buy, dict) and isinstance(sell, dict):
        return str(buy.get("id")), str(sell.get("id"))
    return None


# -- candidates ------------------------------------------------------------------------


class CandidateRequest(BaseModel):
    run: str = Field(..., min_length=1, max_length=40)
    ticker: str = Field(..., min_length=1, max_length=12)
    cell: int = Field(0, ge=0)
    operator: str = Field(..., min_length=1, max_length=80)


def _candidate_id(model: str, params: dict[str, Any], ticker: str, run: str, cell: int) -> str:
    names = _composed_names(params) if model == "composed" else None
    stem = f"{names[0]}-x-{names[1]}" if names else model
    return _slug(f"{stem}-{ticker}-{run[:6]}-{cell}")[:60].strip("-")


@router.get("/picks")
def engine_picks(
    ticker: str | None = Query(None, max_length=16),
    model: str | None = Query(None, max_length=80),
    name: str = Query("", max_length=80),
    traded_only: bool = True,
    limit: int = Query(100, ge=1, le=500),
) -> dict[str, Any]:
    """The engine's pick of every stored run (rank 0), filtered, for the tab's
    menu. Each carries the id it would be added under and whether it is."""
    found = history_query.picks(ticker, model, name, traded_only, limit)
    kept = {c["id"] for c in candidates()}
    for pick in found["picks"]:
        pick["candidate_id"] = _candidate_id(
            str(pick["model"] or ""), pick.pop("params"), pick["ticker"], pick["run"], pick["rank"]
        )
        pick["added"] = pick["candidate_id"] in kept
    return found


@router.get("")
def list_algorithms() -> dict[str, Any]:
    return {"candidates": [_wire(c) for c in candidates()]}


@router.post("/candidates", status_code=201, dependencies=[Depends(live_control.same_origin)])
def add_candidate(body: CandidateRequest) -> dict[str, Any]:
    """Keep one cell of a finished run as a candidate. Its algorithm and
    figures are read from the stored run."""
    run = history.load_summary(body.run)
    summary = (run or {}).get("report") or {}
    fund = (summary.get("funds") or {}).get(body.ticker)
    if not summary or fund is None or body.cell >= len(fund.get("cells") or []):
        raise HTTPException(status_code=404, detail="No such backtest, fund or cell.")
    cell = fund["cells"][body.cell]
    model = str(summary.get("model") or "")
    metrics = cell.get("m") or {}
    names = _composed_names(cell.get("params") or {}) if model == "composed" else None
    candidate_id = _candidate_id(model, cell.get("params") or {}, body.ticker, body.run, body.cell)
    if not model or not _ID.match(candidate_id):
        raise HTTPException(status_code=422, detail="This run has no usable strategy id.")
    if _candidate_path(candidate_id).exists():
        raise HTTPException(status_code=409, detail=f"{candidate_id} is already a candidate.")
    if names:
        from research.strategies.strategy_registry import may_realize_loss

        loss = may_realize_loss("composed", cell.get("params") or {})
    candidate = {
        "id": candidate_id,
        "label": (
            f"{names[0]} buying, {names[1]} selling, on {body.ticker} (backtest {body.run})"
            if names
            else f"{model} on {body.ticker} (backtest {body.run})"
        ),
        "symbols": [body.ticker.upper()],
        "strategy_id": model,
        "strategy_params": dict(cell.get("params") or {}),
        "step": cell.get("grid"),
        "profit_target": cell.get("target"),
        "evidence": {
            "backtest": {
                "run": body.run,
                "name": summary.get("name"),
                "cell": body.cell,
                **{
                    key: metrics.get(key)
                    for key in (
                        "net_yield_pct",
                        "cagr_pct",
                        "max_drawdown_pct",
                        "return_over_drawdown",
                    )
                    if metrics.get(key) is not None
                },
                "window": f"{(fund.get('bars') or {}).get('start')} to "
                f"{(fund.get('bars') or {}).get('end')}",
            }
        },
        **({"composition": {"buy": names[0], "sell": names[1], "loss": loss}} if names else {}),
        "created_at": _now(),
        "created_by": body.operator,
        "trial": None,
        "promotion": None,
    }
    _save(candidate)
    return _wire(candidate)


@router.delete("/candidates/{candidate_id}", dependencies=[Depends(live_control.same_origin)])
def delete_candidate(candidate_id: str) -> dict[str, Any]:
    candidate = _read(candidate_id)
    stage = _stage(candidate)
    if stage == "published" or (stage == "paper_trial" and not _trial_over(candidate)):
        raise HTTPException(status_code=409, detail="It is on trial or published; it stays.")
    path = _candidate_path(candidate_id)
    path.unlink()
    path.parent.rmdir()
    return {"deleted": candidate_id}


# -- the paper trial -------------------------------------------------------------------


class TrialRequest(BaseModel):
    deployment: str = Field(..., min_length=1, max_length=80)
    operator: str = Field(..., min_length=1, max_length=80)
    legacy_lots: Literal["keep", "exit_at_cost", "wait"] = "keep"
    timing: Literal["now", "next_session", "when_flat"] = "next_session"


@router.post("/{candidate_id}/trial", dependencies=[Depends(live_control.same_origin)])
def start_trial(candidate_id: str, body: TrialRequest, request: Request) -> dict[str, Any]:
    """Switch a PAPER deployment to the candidate, through the Live page's own
    switch command, and start counting the trial from the moment it is queued."""
    candidate = _read(candidate_id)
    try:
        deployment = live_registry.get(body.deployment)
    except live_registry.UnknownDeployment as exc:
        raise HTTPException(status_code=404, detail="No such deployment.") from exc
    if not deployment.paper:
        raise HTTPException(status_code=403, detail="A trial runs on a paper deployment.")
    if deployment.config().backtest.symbol not in candidate["symbols"]:
        raise HTTPException(status_code=422, detail="That deployment trades another fund.")
    command = live_control.CommandRequest(
        type="switch_algorithm",
        args={
            "strategy_id": candidate["strategy_id"],
            "strategy_params": candidate["strategy_params"],
            "step": candidate["step"],
            "profit_target": candidate["profit_target"],
            "legacy_lots": body.legacy_lots,
        },
        timing=body.timing,
        reason=f"Paper trial of {candidate_id}",
        operator=body.operator,
        idempotency_key=f"trial-{candidate_id}-{int(time.time())}",
    )
    queued = live_control.queue_command(deployment.id, command, request)
    candidate["trial"] = {
        "deployment": deployment.id,
        "started_at": time.time(),
        "started": _now(),
        "command": (queued.get("command") or {}).get("id"),
        "evaluation": None,
    }
    candidate["promotion"] = None
    _save(candidate)
    return {**_wire(candidate), "warning": queued.get("warning")}


def _halted_for_reconciliation(status: dict[str, Any]) -> bool:
    text = f"{status.get('state')} {status.get('detail')}".lower()
    return "halt" in text and "reconcil" in text


@router.post("/{candidate_id}/evaluate", dependencies=[Depends(live_control.same_origin)])
def evaluate_trial(candidate_id: str) -> dict[str, Any]:
    """Judge the trial against the promotion criteria, from the trader's
    journals. A counter nobody journals fails it (engine/promotion_record.py)."""
    candidate = _read(candidate_id)
    trial = candidate.get("trial")
    if not trial:
        raise HTTPException(status_code=409, detail="It is not on a paper trial.")
    try:
        deployment = live_registry.get(trial["deployment"])
    except live_registry.UnknownDeployment as exc:
        raise HTTPException(status_code=404, detail="Its deployment is gone.") from exc
    inbox = deployment.inbox()
    if inbox is None:
        raise HTTPException(status_code=409, detail="The deployment has no control directory.")
    window = _trial_window(trial)
    if window["state"] in ("pending", "never_ran", "unknown"):
        raise HTTPException(status_code=409, detail=f"Nothing to evaluate: {window['detail']}")
    started_at, ended_at = float(window["from"]), window["until"]
    bars = inbox.bars(sessions=_SESSIONS_KEPT)
    incidents = inbox.incidents(sessions=_SESSIONS_KEPT)
    record = build_record(
        deployment.id,
        started_at=started_at,
        ended_at=ended_at,
        bars=bars,
        fills=inbox.fills(sessions=_SESSIONS_KEPT),
        orders=inbox.orders(sessions=_SESSIONS_KEPT),
        incidents=incidents,
        # A halt the deployment is in now is this trial's only while it trades.
        halted_for_reconciliation=ended_at is None
        and _halted_for_reconciliation(inbox.status() or {}),
    )
    gaps = unmeasured(started_at=started_at, ended_at=ended_at, bars=bars, incidents=incidents)
    verdict = {
        **evaluate(record, unmeasured=gaps),
        "window": {"from": _iso(started_at), "until": _iso(ended_at), "state": window["state"]},
        "evaluated_at": _now(),
    }
    trial["evaluation"] = verdict
    candidate["trial"] = trial
    candidate["promotion"] = verdict if verdict["passed"] else None
    _save(candidate)
    return _wire(candidate)


class OverrideRequest(BaseModel):
    reason: str = Field(..., min_length=3, max_length=500)
    operator: str = Field(..., min_length=1, max_length=80)
    confirm: str = Field(..., max_length=80)


@router.post("/{candidate_id}/override", dependencies=[Depends(live_control.same_origin)])
def owner_sign_off(candidate_id: str, body: OverrideRequest) -> dict[str, Any]:
    """The owner's own promotion, for a candidate with no passing paper trial.
    Marked manual wherever it is shown, and it invents no paper figures."""
    candidate = _read(candidate_id)
    if body.confirm != candidate_id:
        raise HTTPException(status_code=409, detail=f"Type {candidate_id} to confirm.")
    candidate["promotion"] = {
        "passed": True,
        "manual": True,
        "reason": body.reason,
        "by": body.operator,
        "at": _now(),
        "failures": [],
        "backtest": (candidate["evidence"].get("backtest") or {}).get("run"),
        "paper_trial": "none" if not candidate.get("trial") else "see trial",
    }
    _save(candidate)
    return _wire(candidate)


# -- publishing ------------------------------------------------------------------------


class PublishRequest(BaseModel):
    operator: str = Field(..., min_length=1, max_length=80)
    confirm: str = Field(..., max_length=80)


@router.post("/{candidate_id}/publish", dependencies=[Depends(live_control.same_origin)])
def publish(candidate_id: str, body: PublishRequest) -> dict[str, Any]:
    """Copy a promoted candidate into config/live_profiles/, where every
    deployment's profile list finds it. Switches nothing."""
    candidate = _read(candidate_id)
    promotion = candidate.get("promotion")
    if not promotion or promotion.get("passed") is not True:
        raise HTTPException(status_code=409, detail="It has no passing promotion.")
    if body.confirm != candidate_id:
        raise HTTPException(status_code=409, detail=f"Type {candidate_id} to confirm.")
    directory = live_profiles.profiles_dir()
    profile_path = directory / f"{candidate_id}.yaml"
    promotion_path = directory / "promotions" / f"{candidate_id}.json"
    if profile_path.exists():
        raise HTTPException(status_code=409, detail=f"{profile_path.name} already exists.")
    document = {
        "id": candidate_id,
        "label": candidate["label"],
        "symbols": candidate["symbols"],
        "strategy_id": candidate["strategy_id"],
        "strategy_params": candidate["strategy_params"],
        "step": candidate["step"],
        "profit_target": candidate["profit_target"],
        "evidence": {
            **candidate["evidence"],
            "promotion": f"promotions/{candidate_id}.json",
        },
    }
    kind = "owner sign-off, no paper trial" if promotion.get("manual") else "paper trial"
    try:
        _write_json(promotion_path, promotion)
        profile_path.write_text(
            _HEADER.format(when=_now(), who=body.operator, kind=kind)
            + yaml.safe_dump(document, sort_keys=False),
            encoding="utf-8",
        )
        loaded = live_profiles.load_profiles().get(candidate_id)
        if loaded is None or not loaded.promoted():
            raise ValueError("the loader does not accept it as a promoted profile")
    except (OSError, ValueError) as exc:
        profile_path.unlink(missing_ok=True)
        promotion_path.unlink(missing_ok=True)
        raise HTTPException(status_code=500, detail=f"Not published: {exc}") from exc
    candidate["published"] = {"at": _now(), "by": body.operator}
    _save(candidate)
    return _wire(candidate)
