"""
The Forecast tab's HTTP face (research/forecast_generator/): it makes a risk
report from public market data, and WRITES NOTHING.

  GET  /api/forecast/status   what can run here (Chronos-2 only with
                              requirements-dl.txt; the historical baseline
                              always), the funds with a profile, whether a
                              report can be made now and for which session,
                              and the last runs
  POST /api/forecast/runs     {symbol, engine}: start one run in the
                              background, 202 with the run. 409 while
                              another runs: one at a time, a Chronos-2 run
                              holds every core it can get. 422 when no
                              honest report can be made now (inside regular
                              hours, while closing prints settle), with why.
  GET  /api/forecast/runs     the last RUNS_KEPT runs, newest first: state,
                              progress, and the result -- the report, its
                              audit, the snapshot of overnight inputs, the
                              sources -- or the reason it was refused

Keeping a report is not this module's to do: the tab's Check sends it to
server/risk_forecasts.py, the one writer of the forecast database, exactly
as a pasted one is. So this reaches no ledger, no trader's inbox, no broker,
no shell and no store; runs live in memory (a restart forgets them -- the
forecast database is the record), and no route takes a path.
"""

from __future__ import annotations

import threading
import uuid
from collections import deque
from collections.abc import Callable
from datetime import UTC, datetime
from typing import Any, Literal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from research.forecast_generator import generator, model
from server.live_control import same_origin

router = APIRouter(prefix="/api/forecast", tags=["forecast"])

RUNS_KEPT = 5
PROGRESS_KEPT = 40


def _now() -> datetime:
    return datetime.now(UTC)


def _spawn(work: Callable[[], None]) -> None:
    threading.Thread(target=work, name="forecast-run", daemon=True).start()


# The generator itself; tests swap in a fake that needs no network.
_generate: Callable[..., generator.Generated] = generator.generate


def _stamp(moment: datetime) -> str:
    return moment.astimezone(UTC).isoformat(timespec="seconds")


class _Runs:
    """The last few runs, in memory, newest first. One runs at a time."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._runs: deque[dict[str, Any]] = deque(maxlen=RUNS_KEPT)

    def active(self) -> dict[str, Any] | None:
        return next((r for r in self._runs if r["state"] in ("queued", "running")), None)

    def snapshot(self) -> list[dict[str, Any]]:
        with self._lock:
            return [dict(run, progress=list(run["progress"])) for run in self._runs]

    def begin(self, symbol: str, engine: str) -> dict[str, Any]:
        with self._lock:
            busy = self.active()
            if busy is not None:
                raise HTTPException(
                    status_code=409,
                    detail=f"A {busy['engine']} forecast for {busy['symbol']} is still running.",
                )
            run: dict[str, Any] = {
                "id": uuid.uuid4().hex[:12],
                "symbol": symbol,
                "engine": engine,
                "state": "queued",
                "started_at": _stamp(_now()),
                "finished_at": None,
                "progress": [],
                "error": None,
                "result": None,
            }
            self._runs.appendleft(run)
            return dict(run)

    def note(self, run_id: str, message: str) -> None:
        with self._lock:
            for run in self._runs:
                if run["id"] == run_id:
                    run["state"] = "running"
                    run["progress"] = [
                        *run["progress"],
                        {"at": _stamp(_now()), "message": message},
                    ][-PROGRESS_KEPT:]

    def finish(self, run_id: str, *, result=None, error=None, refused=False) -> None:
        with self._lock:
            for run in self._runs:
                if run["id"] == run_id:
                    run["state"] = "refused" if refused else "failed" if error else "done"
                    run["finished_at"] = _stamp(_now())
                    run["result"] = result
                    run["error"] = error

    def clear(self) -> None:
        with self._lock:
            self._runs.clear()


RUNS = _Runs()


class RunRequest(BaseModel):
    """One forecast, as the Forecast tab asks for it."""

    symbol: str = Field(min_length=1, max_length=12, pattern=r"^[A-Za-z0-9][A-Za-z0-9.^=-]{0,11}$")
    engine: Literal["chronos", "bootstrap"] = "chronos"


def _work(run_id: str, symbol: str, engine: str) -> Callable[[], None]:
    def work() -> None:
        try:
            made = _generate(symbol, engine, progress=lambda message: RUNS.note(run_id, message))
        except generator.ForecastRefused as exc:
            RUNS.finish(run_id, error=str(exc), refused=True)
        except Exception as exc:  # a provider outage or a model failure: shown, not raised
            RUNS.finish(run_id, error=f"{type(exc).__name__}: {str(exc)[:500]}")
        else:
            RUNS.finish(run_id, result=made.to_dict())

    return work


@router.get("/status")
def status() -> dict[str, Any]:
    session, why_not = generator.window_check(_now())
    available, detail = model.chronos_available()
    return {
        "engines": [
            {"id": "chronos", "label": "Chronos-2", "available": available, "detail": detail},
            {
                "id": "bootstrap",
                "label": "Historical baseline",
                "available": True,
                "detail": "empirical quantiles of the last five years; no model",
            },
        ],
        "symbols": sorted(generator.PROFILES),
        "can_generate": session is not None,
        "target_session": session.isoformat() if session else None,
        "why_not": why_not,
        "runs": RUNS.snapshot(),
    }


@router.get("/runs")
def runs() -> dict[str, Any]:
    return {"runs": RUNS.snapshot()}


@router.post("/runs", status_code=202, dependencies=[Depends(same_origin)])
def start(body: RunRequest) -> dict[str, Any]:
    symbol = body.symbol.upper()
    session, why_not = generator.window_check(_now())
    if session is None:
        raise HTTPException(status_code=422, detail=why_not)
    if body.engine == "chronos":
        available, detail = model.chronos_available()
        if not available:
            raise HTTPException(status_code=422, detail=f"Chronos-2 is not available: {detail}.")
    run = RUNS.begin(symbol, body.engine)
    _spawn(_work(run["id"], symbol, body.engine))
    return {"run": run, "target_session": session.isoformat()}


__all__ = ["RUNS", "RunRequest", "router"]
