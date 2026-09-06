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

import asyncio
import os
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pandas as pd
from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from pydantic import BaseModel, Field

from optimization_controller import OptimizationController
from server import history
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

# PARALLELISM IS SAFE HERE BECAUSE THIS IS NOT THE TRADING MACHINE.
#
# An earlier version of this server pinned every sweep to one core, on
# the reasoning that saturating a box which might also be running the
# live loop would starve the thing that actually matters. That premise
# is wrong for this deployment: the loop runs on separate hardware, so
# the only process competing for these cores is this API.
#
# One core is still left free -- not caution about the trading loop, but
# so the event loop keeps serving the read-only live socket and the
# run's own progress frames while a sweep saturates everything else.
#
# VAI_MAX_JOBS OVERRIDES BOTH, AND THE RASPBERRY PI SETS IT TO 1.
# The paragraph above is true of the development box and FALSE of the
# Pi, which runs the trading loop and this server on the same four
# cores. The premise is a property of the HOST, so it is a setting
# rather than a constant -- and the compose file that puts this next to
# a live loop is the thing that has to say so.
_CONFIGURED = os.environ.get("VAI_MAX_JOBS")
_CORES = os.cpu_count() or 2
if _CONFIGURED and _CONFIGURED.isdigit() and int(_CONFIGURED) >= 1:
    MAX_JOBS = int(_CONFIGURED)
    DEFAULT_JOBS = MAX_JOBS
else:
    DEFAULT_JOBS = max(1, _CORES - 1)
    MAX_JOBS = max(1, _CORES)

# BUT A POOL IS NOT FREE, AND BELOW A CERTAIN SIZE IT IS A LOSS.
#
# Windows spawns rather than forks, so every worker is a fresh
# interpreter that re-imports pandas and this module tree, and each task
# pickles the whole price frame across. Measured on this machine (12
# cores, 11 workers):
#
#     13,260 bars x 12 configs   4.2s serial   ->  0.69x   SLOWER
#    100,000 bars x  6 configs   8.2s serial   ->  1.35x
#    300,000 bars x  6 configs  19.8s serial   ->  2.25x
#
# The overhead is roughly fixed, so the pool pays for itself once the
# serial run would take longer than it. The threshold below sits just
# under the break-even in bar-configurations -- the product is a decent
# proxy for the work, since the engine is a per-bar loop.
#
# The small case is the interactive one: a single configuration over a
# recent window, run to look at a chart. Making THAT slower to speed up
# a sweep nobody is watching would be the wrong trade.
PARALLEL_THRESHOLD_BAR_CONFIGS = 500_000


def choose_jobs(bars: int, combinations: int, requested: int | None) -> int:
    """How many workers this run should use.

    An explicit request is honoured (capped), because someone who has
    measured their own machine knows more than this heuristic does.
    """
    ceiling = max(1, min(MAX_JOBS, combinations))
    if requested is not None:
        return max(1, min(requested, ceiling))
    if bars * combinations < PARALLEL_THRESHOLD_BAR_CONFIGS:
        return 1
    return max(1, min(DEFAULT_JOBS, ceiling))


class RunRequest(BaseModel):
    """The shape of a submitted run. Semantics are BacktestConfig's."""

    tickers: list[str] = Field(..., min_length=1, max_length=8)
    grid_steps: list[float] = Field(..., min_length=1, max_length=12)
    profit_targets: list[float] = Field(..., min_length=1, max_length=12)
    sizing_model: str = "fixed"
    strategy_params: dict[str, Any] = Field(default_factory=dict)
    fill_model: str = "close"
    enforce_no_loss: bool = True
    # A DATE WINDOW, applied before the engine sees anything. `limit` is
    # the backstop that remains: these files are a million rows and a
    # sweep over all of them is minutes per configuration.
    #
    # The two compose in that order -- window first, then cap the tail --
    # so "the last 20k bars of 2022" means what it says.
    start: str | None = Field(default=None, description="ISO date, inclusive.")
    end: str | None = Field(default=None, description="ISO date, inclusive of the whole day.")
    limit: int | None = Field(default=200_000, ge=500, le=2_000_000)
    # None means "decide for me" -- DEFAULT_JOBS. Explicit 1 forces the
    # sequential path, which is worth keeping reachable: a single
    # configuration gains nothing from a process pool and pays the cost
    # of pickling the frame to a worker.
    n_jobs: int | None = Field(default=None, ge=1, le=64)


def window(
    frame: pd.DataFrame, start: str | None, end: str | None, limit: int | None
) -> pd.DataFrame:
    """Apply the date window, then the bar cap. In that order.

    The end bound covers the WHOLE day: a picker gives "2026-03-27", and
    someone selecting one day means that day, not the instant midnight
    begins it. Slicing on the bare timestamp would return nothing.

    CAPPING FIRST WOULD BE A REAL BUG. It would take the tail of the
    FILE and then filter it, so any window that is not recent comes back
    empty -- indistinguishable, on screen, from "the strategy made no
    trades in that period".
    """
    if start:
        frame = frame[frame.index >= pd.Timestamp(start, tz="UTC")]
    if end:
        frame = frame[frame.index < pd.Timestamp(end, tz="UTC") + pd.Timedelta(days=1)]
    if limit:
        frame = frame.tail(limit)
    return frame


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
    jobs = 1
    for index, ticker in enumerate(available):
        report(index / len(available), f"running {ticker}")
        frame = pd.read_csv(KNOWN_DATA[ticker], parse_dates=["timestamp"]).set_index("timestamp")
        frame = window(frame, parsed.start, parsed.end, parsed.limit)
        if frame.empty:
            raise ValueError(
                f"{ticker} has no bars between {parsed.start} and {parsed.end}. "
                "Widen the window, or check what the file covers."
            )

        kwargs = config.to_run_sweep_kwargs(strategy_class)
        kwargs["return_full_results"] = True
        kwargs["symbol"] = ticker
        combinations = len(config.grid.steps) * len(config.grid.profit_targets)
        jobs = choose_jobs(len(frame), combinations, parsed.n_jobs)
        kwargs["n_jobs"] = jobs
        summary, full = OptimizationController(historical_data=frame).run_sweep(**kwargs)

        # The best configuration by the engine's own default ranking.
        # run_sweep sorted summary and full_results together, so index 0
        # is that row and the UI is not re-ranking by a metric of its own
        # invention.
        result = full[0]
        funds[ticker] = {
            "metrics": fund_metrics(result.metrics, ticker),
            "executions": executions(result.trade_blotter, ticker),
            "equity_curve": equity_series(result.equity_curve),
            # EVERY configuration, for the sweep matrix -- metrics only.
            # Carrying each one's executions as well would multiply the
            # payload by the size of the grid to draw a heatmap that
            # needs one number per cell.
            "configurations": [
                {
                    "grid_step": float(row["Grid Step"]),
                    "profit_target": float(row["Profit Target"]),
                    "metrics": fund_metrics(dict(row), ticker),
                }
                for _, row in summary.iterrows()
            ],
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
            # What the run ACTUALLY used, not what was asked for, so a
            # reader can tell a slow sweep from a serial one.
            "n_jobs": jobs,
        },
        "timeframe": {
            "start": min((f["bars"]["start"] for f in funds.values()), default=None),
            "end": max((f["bars"]["end"] for f in funds.values()), default=None),
            "interval": "1Min",
        },
        "funds": funds,
    }


def _archive(job) -> None:
    """Write a completed run to the history directory.

    Stamped with its own id first: run_backtest cannot know the id --
    the queue mints it after the request is built -- and a stored report
    whose run_id was the empty string would be unloadable by the very
    endpoint that serves it back.
    """
    history.save(job.run_id, _with_id(job.snapshot(), job.run_id))


queue = JobQueue(runner=run_backtest, on_complete=_archive)


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


@router.get("/bars")
def bars(
    ticker: str,
    start: str | None = None,
    end: str | None = None,
    max_points: int = 3000,
) -> dict[str, Any]:
    """OHLC for a window, downsampled SERVER-SIDE.

    Distinct from /api/live/bars, which serves the tail of a file for a
    running deployment. This one takes a date range, which is what a
    historical chart needs and what the live endpoint deliberately does
    not offer.

    THE DOWNSAMPLE IS OHLC, NOT SAMPLING. Buckets are sized so the
    result lands near max_points, and each keeps first open, max high,
    min low, last close. Taking every Nth row instead would drop the
    extremes -- and under the engine's "intrabar" fill model a level
    TOUCHED during a bar is a fill, so the wicks are exactly where the
    executions are. A chart that dropped them would show markers hanging
    off a candle that never reached them.

    A ten-year minute file is a million rows and roughly 60 MB. Sending
    it whole would stall this process serialising it and the browser
    parsing it, to draw a few thousand pixels.
    """
    path = KNOWN_DATA.get(ticker)
    if path is None or not Path(path).exists():
        raise HTTPException(
            status_code=404,
            detail=f"No data file for {ticker!r}. Known: {sorted(KNOWN_DATA)}.",
        )

    frame = pd.read_csv(path, parse_dates=["timestamp"]).set_index("timestamp")
    frame = window(frame, start, end, None)
    if frame.empty:
        return {"ticker": ticker, "bars": [], "bucket_seconds": 60, "source_rows": 0}

    source_rows = len(frame)
    # Round the bucket up to a whole number of minutes so the result is
    # a recognisable timeframe rather than an arbitrary 137-second bar.
    minutes = max(1, -(-source_rows // max_points))
    rule = f"{minutes}min"
    rolled = frame.resample(rule).agg(
        {"open": "first", "high": "max", "low": "min", "close": "last", "volume": "sum"}
    )
    # Gaps -- nights, weekends, holidays -- resample into empty rows.
    # Dropping them keeps the axis continuous across sessions, which is
    # what every trading chart does.
    rolled = rolled.dropna(subset=["close"])

    return {
        "ticker": ticker,
        "bucket_seconds": minutes * 60,
        "source_rows": source_rows,
        "bars": [
            {
                "time": int(timestamp.timestamp()),
                "open": float(row.open),
                "high": float(row.high),
                "low": float(row.low),
                "close": float(row.close),
                "volume": float(row.volume),
            }
            for timestamp, row in rolled.iterrows()
        ],
    }


@router.get("/history")
def history_rows() -> dict[str, Any]:
    """Every completed run, flattened to one row PER CONFIGURATION.

    A run can hold several funds and each fund several configurations,
    so "rank the runs" is the wrong shape -- the thing worth comparing
    is a (run, fund, grid step, profit target) tuple and its metrics.
    Flattening here means the client sorts an array rather than walking
    a tree to find comparable numbers.

    Ranking itself is deliberately NOT done here. The metric is the
    reader's choice and changing it should be instant, not a round trip.
    """
    rows: list[dict[str, Any]] = []
    for run in history.load_all():
        report = run.get("report") or {}
        parameters = report.get("parameters") or {}
        timeframe = report.get("timeframe") or {}
        for ticker, fund in (report.get("funds") or {}).items():
            configurations = fund.get("configurations") or []
            if not configurations:
                # A report from before configurations were carried still
                # has its headline metrics. Synthesised as a single cell
                # so old runs stay comparable rather than disappearing.
                configurations = [
                    {
                        "grid_step": parameters.get("grid_step_pct"),
                        "profit_target": parameters.get("profit_target_pct"),
                        "metrics": fund.get("metrics") or {},
                    }
                ]
            for index, cell in enumerate(configurations):
                rows.append(
                    {
                        "run_id": run.get("run_id"),
                        "saved_at": run.get("saved_at"),
                        "ticker": ticker,
                        "grid_step": cell.get("grid_step"),
                        "profit_target": cell.get("profit_target"),
                        "sizing_model": parameters.get("sizing_model"),
                        "fill_model": parameters.get("fill_model"),
                        # The engine ranked these; index 0 is its own
                        # pick, and saying so lets a reader see when
                        # their chosen metric disagrees with it.
                        "engine_rank": index,
                        "start": timeframe.get("start"),
                        "end": timeframe.get("end"),
                        "bars": (fund.get("bars") or {}).get("count"),
                        "metrics": cell.get("metrics") or {},
                    }
                )
    return {"rows": rows, "runs": len({row["run_id"] for row in rows})}


@router.get("/history/{run_id}")
def history_run(run_id: str) -> dict[str, Any]:
    """One persisted run in full, for loading back into the view."""
    run = history.load(run_id)
    if run is None:
        raise HTTPException(status_code=404, detail=f"No stored run {run_id!r}.")
    return run


@router.get("/runs")
def runs() -> dict[str, Any]:
    """Every run this server has seen, newest first."""
    return {"runs": [job.snapshot() for job in queue.all()]}


@router.get("/runs/{run_id}")
def run(run_id: str) -> dict[str, Any]:
    job = queue.get(run_id)
    if job is not None:
        return _with_id(job.snapshot(), run_id)
    # Not in memory. A completed run outlives the process that made it,
    # so a restart must not turn a link someone saved into a 404.
    stored = history.load(run_id)
    if stored is None:
        raise HTTPException(status_code=404, detail=f"No run {run_id!r}.")
    return stored


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
            # OFF THE EVENT LOOP. wait_for_change blocks on a
            # threading.Condition for up to HEARTBEAT_SECONDS, and
            # calling it directly from this coroutine would stall every
            # other request for that whole period -- including the
            # read-only live socket an operator may be watching a real
            # deployment through. asyncio.to_thread hands the block to a
            # worker and lets the loop keep serving.
            current = await asyncio.to_thread(
                queue.wait_for_change, run_id, seen, HEARTBEAT_SECONDS
            )
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
