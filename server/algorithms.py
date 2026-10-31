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
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field

from engine.core.exceptions import ConfigurationError
from engine.promotion_record import build_record, evaluate
from research.strategies import live_profiles
from server import history, live_control, live_registry

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
    return {
        **candidate,
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
    stem = f"{names[0]}-x-{names[1]}" if names else model
    candidate_id = _slug(f"{stem}-{body.ticker}-{body.run[:6]}-{body.cell}")[:60].strip("-")
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
    if _stage(candidate) in ("paper_trial", "published"):
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
    record = build_record(
        deployment.id,
        started_at=float(trial["started_at"]),
        bars=inbox.bars(sessions=_SESSIONS_KEPT),
        fills=inbox.fills(sessions=_SESSIONS_KEPT),
        orders=inbox.orders(sessions=_SESSIONS_KEPT),
        halted_for_reconciliation=_halted_for_reconciliation(inbox.status() or {}),
    )
    verdict = {**evaluate(record), "evaluated_at": _now()}
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
