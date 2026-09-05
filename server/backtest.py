"""Submit and read backtest runs. The bidirectional half of the API.

--------------------------------------------------------------------
THIS ONE ACCEPTS INPUT, AND THAT IS THE POINT

Live state is read-only (server/live.py) because a UI bug there could
touch a real position. A backtest touches nothing: it is a simulation
over a CSV, in a process with no broker and no credentials. So the UI
may submit parameters here, which is what makes the backtesting view an
instrument rather than a report.

The line between the two is drawn by capability, not by convention:
this module never opens a ledger store and never imports a broker, and
tests/unit/test_server_capability.py fails if either changes.

--------------------------------------------------------------------
PARAMETERS ARE VALIDATED BY BacktestConfig, NOT BY A SECOND SCHEMA

Everything submitted is assembled into a dict and handed to
BacktestConfig.from_dict(...).validate() -- the same path cli.py and
every YAML file take. A parallel Pydantic schema of the same fields
would be a second definition of what a valid configuration is, free to
drift from the one the engine enforces, and the disagreement would show
up as a run that validates here and fails there.

Pydantic is used only for the SHAPE of the request body (types, bounds,
list lengths), which is a transport concern.

--------------------------------------------------------------------
THE SERIALISERS ARE THE EXPORTER'S

executions(), fund_metrics() and equity_series() are imported from
tools/export_ui_data.py rather than reimplemented. A static export and a
live API that disagreed about what a BacktestExecution looks like would
be a bug the UI discovers at runtime, on a field it happens to read.
"""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Any

import pandas as pd
from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from pydantic import BaseModel, Field

from optimization_controller import OptimizationController
from server.jobs import JobQueue
from src.config import BacktestConfig
from src.exceptions import ConfigurationError
from src.strategy_registry import STRATEGIES, resolve_strategy
from tools.export_ui_data import KNOWN_DATA, equity_series, executions, fund_metrics

router = APIRouter(prefix="/api/backtest", tags=["backtest"])

# How long a websocket waits for a job to change before sending a
# heartbeat. Short enough that a browser tab does not decide the
# connection is dead, long enough that a 23-second run is not producing
# dozens of pointless frames.
HEARTBEAT_SECONDS = 10.0


class RunRequest(BaseModel):
    """The shape of a submitted run. Semantics are BacktestConfig's."""

    tickers: list[str] = Field(..., min_length=1, max_length=8)
    grid_steps: list[float] = Field(..., min_length=1, max_length=12)
    profit_targets: list[float] = Field(..., min_length=1, max_length=12)
    sizing_model: str = "fixed"
    strategy_params: dict[str, Any] = Field(default_factory=dict)
    fill_model: str = "close"
    enforce_no_loss: bool = True
    # A bar cap, not a date range: these files are a million rows and a
    # sweep over all of them is minutes per configuration. The UI offers
    # presets; this is the backstop.
    limit: int | None = Field(default=200_000, ge=500, le=2_000_000)


def build_config(request: RunRequest) -> BacktestConfig:
    """Validate a request the way the engine itself would.

    Raises ConfigurationError, which the caller turns into a 400. A bad
    strategy_id fails here with the list of real ones rather than as a
    KeyError somewhere inside a worker thread.
    """
    config = BacktestConfig.from_dict(
        {
            "strategy": {
                "strategy_id": request.sizing_model,
                "strategy_params": request.strategy_params,
            },
            "grid": {
                "steps": request.grid_steps,
                "profit_targets": request.profit_targets,
            },
            "execution": {
                "fill_model": request.fill_model,
                "enforce_no_loss": request.enforce_no_loss,
            },
            # NO `live` SECTION, EVER. This process has no credentials and
            # no broker; accepting live settings from a browser would be
            # accepting them from anyone who can reach this port. The
            # capability test asserts this module names no broker.
        }
    )
    config.validate()
    resolve_strategy(config.strategy.strategy_id)  # fails loudly on a typo
    return config


def run_backtest(request: dict[str, Any], report: Callable[[float, str], None]) -> dict[str, Any]:
    """Execute one submitted run. Called on the worker thread.

    `report` is the job queue's progress callback. Progress is per
    (ticker x configuration), which is as fine as the engine's own
    reporting allows -- run_sweep returns when it returns.
    """
    parsed = RunRequest(**request)
    config = build_config(parsed)
    strategy_class = resolve_strategy(config.strategy.strategy_id)

    available = [t for t in parsed.tickers if t in KNOWN_DATA and Path(KNOWN_DATA[t]).exists()]
    if not available:
        raise ValueError(
            f"None of {parsed.tickers} has a data file. Known: {sorted(KNOWN_DATA)}. "
            "Download one with `python cli.py fetch-data --symbol <T> ...`."
        )

    funds: dict[str, Any] = {}
    for index, ticker in enumerate(available):
        report(index / len(available), f"running {ticker}")
        frame = pd.read_csv(KNOWN_DATA[ticker], parse_dates=["timestamp"]).set_index("timestamp")
        if parsed.limit:
            frame = frame.tail(parsed.limit)

        kwargs = config.to_run_sweep_kwargs(strategy_class)
        kwargs["return_full_results"] = True
        kwargs["symbol"] = ticker
        _, full = OptimizationController(historical_data=frame).run_sweep(**kwargs)

        # The best configuration by the engine's own default ranking.
        # run_sweep already sorted them, so index 0 is that row and the
        # UI is not re-ranking by a metric of its own invention.
        result = full[0]
        funds[ticker] = {
            "metrics": fund_metrics(result.metrics, ticker),
            "executions": executions(result.trade_blotter, ticker),
            "equity_curve": equity_series(result.equity_curve),
            "bars": {
                "start": pd.Timestamp(frame.index[0]).isoformat(),
                "end": pd.Timestamp(frame.index[-1]).isoformat(),
                "count": len(frame),
            },
        }

    report(1.0, "assembling report")
    return {
        "run_id": "",  # filled in by the route from the job's own id
        "parameters": {
            "grid_step_pct": config.grid.steps[0] if config.grid.steps else None,
            "profit_target_pct": (
                config.grid.profit_targets[0] if config.grid.profit_targets else None
            ),
            "sizing_model": config.strategy.strategy_id,
            "fill_model": config.execution.fill_model,
            "enforce_no_loss": config.execution.enforce_no_loss,
        },
        "timeframe": {
            "start": min((f["bars"]["start"] for f in funds.values()), default=None),
            "end": max((f["bars"]["end"] for f in funds.values()), default=None),
            "interval": "1Min",
        },
        "funds": funds,
    }


queue = JobQueue(runner=run_backtest)


@router.get("/funds")
def funds() -> dict[str, Any]:
    """What can actually be backtested on this machine.

    Reports presence rather than filtering it out: a UI that silently
    omits SPY is indistinguishable from one that has never heard of it,
    and the fix (`cli.py fetch-data`) is worth naming.
    """
    return {
        "funds": [
            {"ticker": ticker, "path": path, "available": Path(path).exists()}
            for ticker, path in sorted(KNOWN_DATA.items())
        ],
        "sizing_models": sorted(STRATEGIES),
    }


@router.get("/runs")
def runs() -> dict[str, Any]:
    """Every run this server has seen, newest first."""
    return {"runs": [job.snapshot() for job in queue.all()]}


@router.get("/runs/{run_id}")
def run(run_id: str) -> dict[str, Any]:
    job = queue.get(run_id)
    if job is None:
        raise HTTPException(status_code=404, detail=f"No run {run_id!r}.")
    return _with_id(job.snapshot(), run_id)


@router.post("/runs", status_code=202)
def submit(request: RunRequest) -> dict[str, Any]:
    """Queue a run. Returns immediately with an id.

    202, not 200: nothing has been computed yet. Validation happens HERE
    rather than on the worker so a malformed request fails as a 400 the
    caller can act on, instead of as a job that fails 20 seconds later.
    """
    try:
        build_config(request)
    except ConfigurationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Invalid run request: {exc}") from exc

    job = queue.submit(request.model_dump())
    return _with_id(job.snapshot(), job.run_id)


@router.websocket("/ws/{run_id}")
async def run_socket(socket: WebSocket, run_id: str) -> None:
    """Stream one run's progress, then its result.

    Blocks on the job queue's Condition rather than polling, so an
    update is delivered when it happens. Sends the current state first,
    because a client that connects after a fast run finished must not
    wait forever for an event that has already passed.
    """
    await socket.accept()
    job = queue.get(run_id)
    if job is None:
        await socket.send_json({"type": "error", "detail": f"No run {run_id!r}."})
        await socket.close()
        return

    try:
        seen = -1
        while True:
            current = queue.wait_for_change(run_id, since=seen, timeout=HEARTBEAT_SECONDS)
            if current is None:
                await socket.send_json({"type": "error", "detail": f"No run {run_id!r}."})
                return
            if current.revision == seen:
                await socket.send_json({"type": "heartbeat", "run_id": run_id})
                continue
            seen = current.revision
            await socket.send_json({"type": "run", "run": _with_id(current.snapshot(), run_id)})
            if current.status in {"complete", "failed"}:
                return
    except WebSocketDisconnect:
        return


def _with_id(snapshot: dict[str, Any], run_id: str) -> dict[str, Any]:
    """Stamp the job's id onto its report.

    run_backtest cannot know it -- the id is minted by the queue when
    the job is created, after the request has been built. Filling it in
    here keeps the worker free of queue concepts.
    """
    report = snapshot.get("report")
    if isinstance(report, dict):
        report["run_id"] = run_id
    return snapshot


__all__ = ["RunRequest", "build_config", "queue", "router", "run_backtest"]
