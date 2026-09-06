#!/usr/bin/env python
"""Drop partial-length runs, and re-run the best of each algorithm in full.

--------------------------------------------------------------------
WHY PARTIAL RUNS ARE WORTH DELETING

Most of the stored history was produced while building the UI: 500-bar
smoke tests, 20,000-bar submissions, 60,000-bar seeds. They were fine
for proving plumbing and they are actively misleading in a ranking
table, because a configuration's CAGR over three days of 2026 says
nothing about the same configuration over ten years -- and the table
sorts them side by side as though it did.

"Full" is decided PER TICKER. The files differ in length (TQQQ has
1,035,332 minute bars, QQQ 1,044,165), so a single bar-count threshold
would keep some partial runs and discard some complete ones.

--------------------------------------------------------------------
"TOP TEN" NEEDS A METRIC, AND THE CHOICE IS STATED RATHER THAN HIDDEN

Ranked by CAGR, which is the ordinary reading of "best". It is not the
only defensible one -- this project's own results repeatedly show the
CAGR leader carrying a drawdown nobody would accept -- which is exactly
why the UI lets a reader re-rank. What this script decides is only which
configurations are worth the engine time to measure properly; the
judgement about which is BEST stays with whoever reads the table.

Configurations that never traded are excluded. A book that sits in cash
has no drawdown and no losing year, and it would otherwise occupy
ranking slots without having done anything.

--------------------------------------------------------------------
ONE CONFIGURATION PER RUN, DELIBERATELY

A sweep holds every combination's blotter and equity curve in memory at
once when full results are requested. At full length that is a ~1M-row
equity curve plus a blotter that reaches hundreds of thousands of rows
for the high-frequency sizing -- tens of MB each, and ten at a time is
how a machine runs out of memory.

Running them separately costs the cross-combination parallelism and
buys a bounded footprint. It also makes each one its own history entry,
which is more useful in the table than a ten-cell blob.

    python tools/rerun_top_configurations.py --dry-run
    python tools/rerun_top_configurations.py
"""

from __future__ import annotations

import argparse
import sys
import time
from collections import defaultdict
from pathlib import Path
from typing import Any

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from server import history
from server.backtest import KNOWN_DATA, STRATEGY_DEFAULTS, run_backtest

# A file read once per ticker; these are 60 MB and the length is all we
# need, so only one column is parsed.
_LENGTHS: dict[str, int] = {}


def full_length(ticker: str) -> int | None:
    """How many bars the whole file holds, or None if it is absent."""
    if ticker in _LENGTHS:
        return _LENGTHS[ticker]
    path = KNOWN_DATA.get(ticker)
    if path is None or not Path(path).exists():
        return None
    _LENGTHS[ticker] = len(pd.read_csv(path, usecols=["close"]))
    return _LENGTHS[ticker]


def is_full(ticker: str, bars: int | None) -> bool:
    """Within a whisker of the whole file.

    Not an equality check: a run windowed by date can legitimately land
    a few bars short of the file if the file grew since, and re-running
    it would be busywork.
    """
    total = full_length(ticker)
    if total is None or not bars:
        return False
    return bars >= total * 0.99


def collect(runs: list[dict]) -> tuple[list[str], dict[str, list[dict]]]:
    """Partial run ids to delete, and candidate configurations by model."""
    partial: list[str] = []
    by_model: dict[str, dict[tuple, dict]] = defaultdict(dict)

    for run in runs:
        report = run.get("report") or {}
        parameters = report.get("parameters") or {}
        model = parameters.get("sizing_model")
        funds = report.get("funds") or {}
        if not funds:
            partial.append(run["run_id"])
            continue

        run_is_full = all(
            is_full(ticker, (fund.get("bars") or {}).get("count")) for ticker, fund in funds.items()
        )
        if not run_is_full:
            partial.append(run["run_id"])

        if not model:
            continue
        for ticker, fund in funds.items():
            for cell in fund.get("configurations") or []:
                metrics = cell.get("metrics") or {}
                if not metrics.get("total_trades"):
                    # Never traded. It would occupy a ranking slot
                    # without having done anything.
                    continue
                step, target = cell.get("grid_step"), cell.get("profit_target")
                if step is None or target is None:
                    continue
                key = (ticker, round(step, 8), round(target, 8))
                # DEDUPED. The same configuration appears in many
                # partial runs; re-running it ten times would spend the
                # budget on one cell.
                existing = by_model[model].get(key)
                candidate = {
                    "ticker": ticker,
                    "grid_step": step,
                    "profit_target": target,
                    "cagr": float(metrics.get("cagr_pct", 0.0)),
                    "trades": int(metrics.get("total_trades", 0)),
                }
                if existing is None or candidate["cagr"] > existing["cagr"]:
                    by_model[model][key] = candidate

    return partial, {model: list(cells.values()) for model, cells in by_model.items()}


# The grid a screening pass explores when history does not hold enough
# distinct configurations for a model. Spans two orders of magnitude on
# each axis, because the interesting differences between these
# strategies show up across that range rather than within a tight one.
SCREEN_STEPS = [0.001, 0.0025, 0.005, 0.0075, 0.01, 0.02]
SCREEN_TARGETS = [0.003, 0.005, 0.0075, 0.01, 0.02]
SCREEN_TICKER = "TQQQ"


def screen(model: str, bars: int, have: list[dict]) -> list[dict]:
    """Measure a grid cheaply, so "top ten" has ten things to choose from.

    History only holds what happened to be run while building the UI --
    two configurations for one model, five for another. Ranking ten out
    of two is not ranking. This runs the grid at reduced length purely
    to ORDER the candidates; every winner is then measured properly at
    full length, so nothing partial reaches the results.

    Existing candidates are passed in and excluded, so the screen only
    spends time on cells history cannot already order.
    """
    known = {(c["ticker"], round(c["grid_step"], 8), round(c["profit_target"], 8)) for c in have}
    found: list[dict] = []

    # BayesianDualScaleSizing estimates P(reaching ONE target_return),
    # and the engine refuses to sweep several against it -- so its grid
    # has to be walked one target at a time rather than in one request.
    batches = (
        [([step], [target]) for step in SCREEN_STEPS for target in SCREEN_TARGETS]
        if model == "bayesian_dual_scale"
        else [(SCREEN_STEPS, [target]) for target in SCREEN_TARGETS]
    )

    for steps, targets in batches:
        try:
            report = run_backtest(
                {
                    "tickers": [SCREEN_TICKER],
                    "grid_steps": steps,
                    "profit_targets": targets,
                    "sizing_model": model,
                    "strategy_params": STRATEGY_DEFAULTS.get(model, {}),
                    "limit": bars,
                },
                lambda fraction, note: None,
            )
        except Exception as exc:
            print(f"      screen batch failed: {type(exc).__name__}: {exc}"[:110])
            continue

        fund = report["funds"][SCREEN_TICKER]
        for cell in fund.get("configurations") or []:
            metrics = cell.get("metrics") or {}
            if not metrics.get("total_trades"):
                continue
            key = (SCREEN_TICKER, round(cell["grid_step"], 8), round(cell["profit_target"], 8))
            if key in known:
                continue
            known.add(key)
            found.append(
                {
                    "ticker": SCREEN_TICKER,
                    "grid_step": cell["grid_step"],
                    "profit_target": cell["profit_target"],
                    "cagr": float(metrics.get("cagr_pct", 0.0)),
                    "trades": int(metrics.get("total_trades", 0)),
                }
            )
    return found


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--top", type=int, default=10, help="Configurations per algorithm.")
    parser.add_argument("--dry-run", action="store_true", help="Show the plan, change nothing.")
    parser.add_argument(
        "--screen-bars",
        type=int,
        default=200_000,
        help=(
            "Bars used to ORDER candidates when history holds fewer than --top for a "
            "model. Only the ordering comes from this; every winner is then measured "
            "at full length."
        ),
    )
    parser.add_argument("--no-screen", action="store_true", help="Use history only.")
    parser.add_argument(
        "--keep-partial",
        action="store_true",
        help="Re-run the winners without deleting the partial history.",
    )
    args = parser.parse_args(argv)

    runs = history.load_all()
    print(f"{len(runs)} stored runs in {history.directory()}\n")

    # RANKED BEFORE ANYTHING IS DELETED. The partial runs are the only
    # record of which configurations are worth measuring properly, so
    # losing them first would leave nothing to choose from.
    partial, by_model = collect(runs)

    plan: list[tuple[str, dict]] = []
    for model in sorted(by_model):
        candidates = by_model[model]
        if len(candidates) < args.top and not args.no_screen:
            print(
                f"{model}: only {len(candidates)} in history, screening a grid at "
                f"{args.screen_bars:,} bars to find more ..."
            )
            candidates = candidates + screen(model, args.screen_bars, candidates)
        best = sorted(candidates, key=lambda c: c["cagr"], reverse=True)[: args.top]
        print(f"{model}: {len(candidates)} distinct configurations, taking top {len(best)}")
        for cell in best:
            print(
                f"    {cell['ticker']:<5} step {cell['grid_step'] * 100:6.3f}%  "
                f"target {cell['profit_target'] * 100:6.3f}%   "
                f"CAGR {cell['cagr']:7.2f}% ({cell['trades']} trades, partial)"
            )
            plan.append((model, cell))

    print(f"\n{len(partial)} partial runs to delete, {len(runs) - len(partial)} full ones kept")
    print(f"{len(plan)} configurations to re-run at full length\n")
    if args.dry_run:
        print("--dry-run: nothing changed")
        return 0

    if not args.keep_partial:
        directory = history.directory()
        removed = 0
        for run_id in partial:
            path = directory / f"{run_id}.json"
            try:
                path.unlink()
                removed += 1
            except OSError as exc:
                print(f"  could not delete {run_id}: {exc}")
        print(f"deleted {removed} partial runs\n")

    started = time.time()
    done = failed = 0
    for index, (model, cell) in enumerate(plan, 1):
        request: dict[str, Any] = {
            "tickers": [cell["ticker"]],
            "grid_steps": [cell["grid_step"]],
            "profit_targets": [cell["profit_target"]],
            "sizing_model": model,
            "strategy_params": STRATEGY_DEFAULTS.get(model, {}),
            # No limit: the whole file, which is the point.
            "limit": None,
        }
        label = (
            f"[{index:>2}/{len(plan)}] {model:<20} {cell['ticker']:<5} "
            f"{cell['grid_step'] * 100:6.3f}% / {cell['profit_target'] * 100:6.3f}%"
        )
        print(f"{label} ... ", end="", flush=True)

        began = time.time()
        try:
            report = run_backtest(request, lambda fraction, note: None)
        except Exception as exc:
            failed += 1
            print(f"FAILED {type(exc).__name__}: {exc}"[:110])
            continue

        run_id = (
            f"full-{model}-{cell['ticker']}-"
            f"{cell['grid_step'] * 100:.4f}-{cell['profit_target'] * 100:.4f}".replace(".", "p")
        )
        report["run_id"] = run_id
        history.save(
            run_id,
            {
                "run_id": run_id,
                "status": "complete",
                "progress": 1.0,
                "message": f"full-length rerun: {model}",
                "report": report,
                "error": None,
            },
        )
        done += 1
        fund = report["funds"][cell["ticker"]]
        metrics = fund["metrics"]
        print(
            f"{time.time() - began:6.1f}s  {fund['bars']['count']:>9,} bars  "
            f"CAGR {metrics['cagr_pct']:7.2f}%  DD {metrics['max_drawdown_pct']:6.2f}%  "
            f"worst yr {metrics.get('worst_year_pct', 0):7.2f}%  trades {metrics['total_trades']}"
        )

    print(f"\n{done} re-run, {failed} failed, {(time.time() - started) / 60:.1f} min")
    return 0


if __name__ == "__main__":
    sys.exit(main())
