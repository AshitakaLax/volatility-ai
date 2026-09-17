"""The wire contract's legacy readers. Pure functions, no I/O, no state.

--------------------------------------------------------------------
WHY THIS EXISTS

The contract with web/ was condensed (see web/src/types/backtest.ts):
shorter names, run-level fields stated once, derivable fields dropped.
Two things on disk were written in the OLD shape and must keep loading:

  output/queue/state.json   pending requests, restored at startup -- a
                            multi-day sweep can be sitting in it
  output/runs/<id>.json     every archived run, and the static export

So the old shapes are translated HERE, at the read boundary, once. The
rest of the server and the whole of web/ only ever see the new shape,
which is what lets the frontend types drop their "optional because an
older server" hedges.

Every function is idempotent: handed something already in the new shape
it returns it unchanged, so callers never need to know which they have.
"""

from __future__ import annotations

from typing import Any

# Old RunRequest key -> new. search_strategy / n_trials / search_seed /
# search_direction are folded separately (see request()).
_REQUEST_RENAMES = {
    "sizing_model": "model",
    "strategy_params": "params",
    "fill_model": "fill",
    "enforce_no_loss": "no_loss",
    "profit_targets": "targets",
    "n_jobs": "jobs",
}


def request(raw: dict[str, Any]) -> dict[str, Any]:
    """A submitted request in the new field names.

    `bayes` replaces search_strategy + n_trials + search_seed: its
    presence IS the choice of Optuna. A legacy bayesian request with no
    n_trials keeps `trials: None`, so build_config still refuses it with
    the same message rather than it silently becoming a grid sweep.
    """
    out = {_REQUEST_RENAMES.get(key, key): value for key, value in raw.items()}
    strategy = out.pop("search_strategy", None)
    trials = out.pop("n_trials", None)
    seed = out.pop("search_seed", None)
    if strategy == "bayesian" and "bayes" not in out:
        out["bayes"] = {"trials": trials, **({"seed": seed} if seed is not None else {})}
    direction = out.pop("search_direction", None)
    if direction == "minimize":
        out.setdefault("minimize", True)
    return out


def status(value: str, stop_requested: str | None) -> str:
    """A running job with a pending stop reports it as its status.

    `pausing` / `cancelling` replace a separate stop_requested field: the
    run is still running (its in-flight batch finishes first), and the
    status says what it is about to become.
    """
    if value == "running" and stop_requested in ("pause", "cancel"):
        return "pausing" if stop_requested == "pause" else "cancelling"
    return value


def metrics(raw: dict[str, Any] | None) -> dict[str, Any]:
    """FundPerformanceMetrics without the ticker -- it is the fund's key."""
    return {key: value for key, value in (raw or {}).items() if key != "ticker"}


def fill(raw: dict[str, Any]) -> dict[str, Any]:
    """A legacy BacktestExecution as a Fill.

    order_id was `${lot}-${side}-${bar}`, so the bar index is recovered
    from it; matched_buy_id was that same lot id and is dropped.
    """
    if "lot" in raw:
        return raw
    lot, side, index = raw.get("order_id", "--0").rsplit("-", 2)
    out: dict[str, Any] = {
        "lot": raw.get("matched_buy_id") or lot,
        "side": raw.get("type") or side.upper(),
        "i": int(index) if index.lstrip("-").isdigit() else 0,
        "px": raw.get("price"),
        "qty": raw.get("shares"),
        "ts": raw.get("timestamp"),
    }
    for old, new in (("rsi_at_entry", "rsi"), ("profit_realized", "pnl"), ("sell_reason", "why")):
        if raw.get(old) is not None:
            out[new] = raw[old]
    return out


def cell(raw: dict[str, Any], fallback_params: dict[str, Any]) -> dict[str, Any]:
    if "m" in raw:
        return raw
    return {
        "grid": raw.get("grid_step"),
        "target": raw.get("profit_target"),
        # A report from before per-cell params carried only the run-level
        # snapshot; {} for one archived before either existed.
        "params": raw.get("strategy_params") or fallback_params,
        "m": metrics(raw.get("metrics")),
    }


def report(raw: dict[str, Any] | None, detail: bool = True) -> dict[str, Any] | None:
    """A legacy MultiFundBacktestReport as a Report.

    `detail=False` skips translating fills and the equity curve (left
    empty) -- a history listing reads only cells, and translating every
    archived run's thousands of fills made it slower than before.
    """
    if not isinstance(raw, dict) or "parameters" not in raw:
        return raw
    parameters = raw.get("parameters") or {}
    timeframe = raw.get("timeframe") or {}
    run_params = parameters.get("strategy_params") or {}
    # Per-cell params are scalars; a run-level snapshot of a swept argument
    # is a list, which is no cell's value.
    scalar_params = {k: v for k, v in run_params.items() if not isinstance(v, list)}
    funds: dict[str, Any] = {}
    for ticker, fund in (raw.get("funds") or {}).items():
        cells = [cell(c, scalar_params) for c in fund.get("configurations") or []]
        if not cells:
            # Headline metrics only (a static export, or a report from
            # before configurations were carried): one synthesised cell.
            cells = [
                {
                    "grid": parameters.get("grid_step_pct"),
                    "target": parameters.get("profit_target_pct"),
                    "params": scalar_params,
                    "m": metrics(fund.get("metrics")),
                }
            ]
        curve = fund.get("equity_curve") or {}
        funds[ticker] = {
            "cells": cells,
            "fills": [fill(e) for e in fund.get("executions") or []] if detail else [],
            "equity": {
                "dates": (curve.get("dates") or []) if detail else [],
                "equity": (curve.get("equity") or []) if detail else [],
            },
            "bars": fund.get("bars") or {"start": None, "end": None, "count": 0},
        }
    out = {
        "id": raw.get("run_id") or "",
        "name": parameters.get("name"),
        "model": parameters.get("sizing_model"),
        "fill": parameters.get("fill_model"),
        "no_loss": parameters.get("enforce_no_loss", True),
        "params": run_params,
        "grid": parameters.get("grid_step_pct"),
        "target": parameters.get("profit_target_pct"),
        "start": timeframe.get("start"),
        "end": timeframe.get("end"),
        "interval": timeframe.get("interval") or "1Min",
        "funds": funds,
    }
    if parameters.get("n_jobs") is not None:
        out["jobs"] = parameters["n_jobs"]
    return out


def _request_from_report(rep: dict[str, Any] | None, raw: dict[str, Any]) -> dict[str, Any]:
    """The request an archived run predating the request echo must have had.

    Rebuilt from its report so every Run carries a `req` -- the fields a
    client describes a run by, not a replayable submission.
    """
    rep = rep or {}
    cells = [c for fund in (rep.get("funds") or {}).values() for c in fund.get("cells") or []]
    return {
        "name": raw.get("name") or rep.get("name"),
        "tickers": list(rep.get("funds") or {}),
        "grid_steps": sorted({c["grid"] for c in cells if c.get("grid") is not None}),
        "targets": sorted({c["target"] for c in cells if c.get("target") is not None}),
        "model": rep.get("model") or "fixed",
        "params": rep.get("params") or {},
        "fill": rep.get("fill") or "close",
    }


def run(raw: dict[str, Any], detail: bool = True) -> dict[str, Any]:
    """A legacy job snapshot (archived or live) as a Run. See report()."""
    if "run_id" not in raw:
        return raw
    legacy_report = report(raw.get("report"), detail)
    out = {
        "id": raw["run_id"],
        "status": status(raw.get("status") or "complete", raw.get("stop_requested")),
        "progress": raw.get("progress", 1.0),
        "pos": raw.get("queue_position"),
        "msg": raw.get("message"),
        "error": raw.get("error"),
        "rev": raw.get("revision", 0),
        "submitted_at": raw.get("submitted_at"),
        "req": request(raw.get("request") or _request_from_report(legacy_report, raw)),
        "report": legacy_report,
    }
    if out["report"] is not None and not out["report"].get("id"):
        out["report"]["id"] = raw["run_id"]
    if raw.get("saved_at") is not None:
        out["saved_at"] = raw["saved_at"]
    return out


__all__ = ["cell", "fill", "metrics", "report", "request", "run", "status"]
