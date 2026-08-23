"""One-off driver for the HF sweeps (config/search_hf_intrabar.yaml for
the exhaustive grid, config/search_hf_bayesian.yaml for TPE) against the
full 10-year SIP dataset.

Not part of the CLI: cli.py backtest exposes neither n_jobs nor
per-combo progress logging, and cli.py search -- which does drive
BayesianSearch -- calls _run_one_combination without fill_model, so it
silently runs the CLOSE-only fill model no matter what
execution.fill_model says. That is exactly defect 1 from
search_hf_intrabar.yaml's header (close-only undercounts fills ~1.85x),
so neither entrypoint can run these configs correctly.

On n_jobs: a 4-worker run of an early close-only sweep OOM'd on the
original 4GB machine. The root cause is since fixed in
optimization_controller.run_sweep -- it was retaining every
combination's SimulationResult even with return_full_results=False.
Measured peak for ONE combination at the heaviest settings
(per_lot_pct=0.0002, ~904k trades over 10 years) is 1.30GB working set
/ 1.67GB commit, so budget ~1.7GB per worker plus headroom for the OS
and this parent process.

WINDOWS NOTE: everything runs under `if __name__ == "__main__"`.
ProcessPoolExecutor uses spawn (not fork) on Windows, so each worker
re-imports this module; without the guard every worker would re-parse
args, re-read the 59MB CSV, and recursively spawn its own pool.

Workers return metrics only, never the SimulationResult itself.
BayesianSearch.report() reads result.metrics and nothing else, and
shipping a ~900k-row trade blotter back through pickle for every trial
would dominate both runtime and parent memory.

Logs every combo and checkpoints to CSV periodically, given the
multi-hour runtime -- silence for hours with no partial output is
worse than the log volume.
"""

import argparse
import concurrent.futures
import itertools
import logging
import time

import pandas as pd

from optimization_controller import OptimizationController, _run_one_combination
from src.config import BacktestConfig, expand_strategy_params
from src.search_strategies import BayesianSearch
from src.strategy_registry import resolve_strategy

logging.disable(logging.WARNING)


class _Metrics:
    """Picklable stand-in carrying only what BayesianSearch.report reads.

    report() touches result.metrics and nothing else, so returning this
    instead of the real SimulationResult keeps the trade blotter and
    equity curve inside the worker process where they were built.
    """

    __slots__ = ("metrics",)

    def __init__(self, metrics):
        self.metrics = metrics


def _evaluate(payload):
    """Run one combination in a worker. Module-level so it is picklable."""
    row, sim_result = _run_one_combination(*payload)
    return row, (None if sim_result is None else _Metrics(sim_result.metrics))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="config/search_hf_intrabar.yaml")
    parser.add_argument("--data", default="data/TQQQ_1Min_sip_all_2016-01-01_2026-08-21.csv")
    parser.add_argument("--output", default="output/search_hf_intrabar_2026-08-22.csv")
    parser.add_argument("--limit", type=int, default=None, help="run only the first N combinations")
    parser.add_argument(
        "--search",
        choices=("grid", "bayesian"),
        default=None,
        help="override the config's search.strategy",
    )
    parser.add_argument(
        "--trials", type=int, default=200, help="bayesian trial budget (default: 200)"
    )
    parser.add_argument(
        "--n-jobs",
        type=int,
        default=1,
        help="worker processes (default: 1). Budget ~1.7GB of RAM each.",
    )
    parser.add_argument(
        "--max-drawdown",
        type=float,
        default=None,
        help=(
            "reject combinations whose Max Drawdown %% exceeds this. The search still "
            "MEASURES them (the true numbers are written to the output CSV) but is told "
            "a penalized objective, so it stops exploring that region."
        ),
    )
    args = parser.parse_args()

    config = BacktestConfig.from_yaml(args.config)
    config.validate()
    strategy_class = resolve_strategy(config.strategy.strategy_id)
    mode = args.search or config.search.strategy

    df = pd.read_csv(args.data, parse_dates=["timestamp"]).set_index("timestamp")
    controller = OptimizationController(historical_data=df)
    cost_model = config.costs.build()
    risk_manager = config.risk.build()

    params_grid = expand_strategy_params(config.strategy.strategy_params)
    space = len(config.grid.steps) * len(config.grid.profit_targets) * len(params_grid)

    def payload_for(step, target, params):
        return (
            controller,
            step,
            target,
            strategy_class,
            params,
            config.backtest.symbol,
            config.backtest.initial_cash,
            cost_model,
            risk_manager,
            config.execution.on_flat_reentry,
            config.execution.fill_model,
            config.execution.intrabar_priority,
        )

    search = None
    pending = None
    if mode == "bayesian":
        search = BayesianSearch(
            list(config.grid.steps),
            list(config.grid.profit_targets),
            params_grid,
            rank_by=config.search.rank_by,
            direction=config.search.direction,
            n_trials=args.trials,
            seed=config.search.seed,
        )
        total = args.trials
    else:
        combos = list(itertools.product(config.grid.steps, config.grid.profit_targets, params_grid))
        if args.limit:
            combos = combos[: args.limit]
        total = len(combos)
        pending = iter(combos)

    print(
        f"search={mode} | space={space:,} combinations | budget={total} "
        f"({100 * total / space:.2f}%) | n_jobs={args.n_jobs}\n"
        f"data={args.data} ({len(df):,} bars, {df.index.normalize().nunique():,} sessions)\n"
        f"fill_model={config.execution.fill_model} "
        f"| max_concurrent_lots={config.risk.max_concurrent_lots} "
        f"| rank_by={config.search.rank_by}",
        flush=True,
    )
    if search is not None and not search.decomposed:
        print(
            "WARNING: params grid is not a cartesian product -- strategy params "
            "fall back to an OPAQUE INDEX and cannot converge.",
            flush=True,
        )
    print(flush=True)

    def next_suggestion():
        """One suggestion, or None when the budget/grid is exhausted."""
        if search is not None:
            return search.suggest()
        combo = next(pending, None)
        if combo is None:
            return None
        step, target, params = combo
        return {"grid_step": step, "profit_target": target, "strategy_params": params}

    rows = []
    started = time.time()
    state = {"done": 0, "best": None, "cached": 0}

    # A simulation is deterministic in its inputs, so evaluating a
    # combination twice returns bit-identical metrics. TPE re-proposes
    # freely once it converges -- a 200-trial run over the 6,272-point
    # space spent 140 of those trials re-measuring 60 unique
    # combinations, verified identical -- so without this the majority
    # of a budget can go to recomputing known answers. Optuna is still
    # told the cached value (it asked, and the answer is real), it just
    # is not made to wait ~130s to hear it again.
    memo = {}

    def memo_key(suggestion):
        params = suggestion["strategy_params"]
        return (
            suggestion["grid_step"],
            suggestion["profit_target"],
            tuple(sorted(params.items())),
        )

    # Far below any objective this strategy can actually produce (returns
    # are percentages), so a capped-out combination ranks beneath every
    # legitimate one without being told to Optuna as FAILED -- a failure
    # means "never measured", which would teach the sampler the wrong
    # thing about a region that WAS measured and was simply too risky.
    _OVER_CAP_PENALTY = -1e6

    def _penalize_if_over_cap(row, result):
        """Substitute a penalized objective when a combination breaches
        --max-drawdown. Only what the SEARCH sees is altered; `row` --
        and therefore the output CSV -- keeps the real measurements.

        A ratio metric is not a substitute for this. Measured on the
        first 200-trial run, Return/Drawdown ranks the same
        configurations as raw return (9 of the top 10 identical) and
        RISES with lot size, because on a 3x instrument drawdown
        saturates near 80% while return keeps scaling. Only a hard cap
        actually removes that corner from the search.
        """
        if args.max_drawdown is None or result is None:
            return result
        drawdown = row.get("Max Drawdown %")
        if drawdown is None or drawdown <= args.max_drawdown:
            return result
        penalized = dict(result.metrics)
        penalized[config.search.rank_by] = _OVER_CAP_PENALTY
        return _Metrics(penalized)

    def record(suggestion, row, result, t0, cached=False):
        if search is not None:
            search.report(suggestion, _penalize_if_over_cap(row, result))
        state["done"] += 1
        if cached:
            state["cached"] += 1
        done = state["done"]
        rows.append(row)

        params = suggestion["strategy_params"]
        objective = None if "error" in row else row.get(config.search.rank_by)
        over_cap = (
            args.max_drawdown is not None
            and row.get("Max Drawdown %") is not None
            and row["Max Drawdown %"] > args.max_drawdown
        )
        # "best" tracks the best ADMISSIBLE result. Letting a capped-out
        # combination set it would report a headline number the run is
        # explicitly refusing to select.
        if (
            objective is not None
            and not over_cap
            and (state["best"] is None or objective > state["best"])
        ):
            state["best"] = objective
        if "error" in row:
            detail = f"FAILED {row['error']}"
        elif over_cap:
            detail = (
                f"OVER-CAP dd={row['Max Drawdown %']:6.2f}% "
                f"(ret={row.get('Total Return %', float('nan')):8.2f}%)"
            )
        else:
            detail = (
                f"ret={row.get('Total Return %', float('nan')):8.2f}% "
                f"dd={row.get('Max Drawdown %', float('nan')):6.2f}% "
                f"trades={row.get('Trade Count', 0):7.0f}"
            )
        elapsed = time.time() - started
        eta = elapsed / done * (total - done)
        best = state["best"]
        best_str = f"{best:8.2f}%" if best is not None else "     n/a"
        print(
            f"[{done:4d}/{total}] step={suggestion['grid_step']:.5f} "
            f"tgt={suggestion['profit_target']:.5f} "
            f"lot={params.get('per_lot_pct')} lb={params.get('lookback_days')} "
            f"boost={params.get('event_day_boost_multiplier')} "
            f"earn={params.get('earnings_day_boost_multiplier')} {detail} "
            f"best={best_str} ({'CACHED' if cached else f'{time.time() - t0:.0f}s'}, "
            f"elapsed={elapsed / 3600:.2f}h, eta={eta / 3600:.2f}h)",
            flush=True,
        )
        if done % 10 == 0 or done == total:
            pd.DataFrame(rows).to_csv(args.output, index=False)

    if args.n_jobs == 1:
        while True:
            suggestion = next_suggestion()
            if suggestion is None:
                break
            key = memo_key(suggestion)
            if key in memo:
                row, result = memo[key]
                record(suggestion, row, result, time.time(), cached=True)
                continue
            t0 = time.time()
            row, sim_result = _run_one_combination(
                *payload_for(
                    suggestion["grid_step"],
                    suggestion["profit_target"],
                    suggestion["strategy_params"],
                )
            )
            result = None if sim_result is None else _Metrics(sim_result.metrics)
            memo[key] = (row, result)
            record(suggestion, row, result, t0)
    else:
        # Batches of n_jobs so a Bayesian run tells Optuna each batch's
        # results before asking for the next -- suggestions within a
        # batch are necessarily made blind to each other (standard
        # parallel TPE), but the sampler is never more than one batch
        # behind.
        with concurrent.futures.ProcessPoolExecutor(max_workers=args.n_jobs) as executor:
            exhausted = False
            while not exhausted:
                # Keep pulling until there are n_jobs combinations that
                # actually need a worker. A cache hit is recorded on the
                # spot and does not consume a slot, so a converged
                # search fills batches with genuinely new work instead
                # of parking workers on answers already known.
                batch, batch_keys, deferred = [], set(), []
                while len(batch) < args.n_jobs:
                    suggestion = next_suggestion()
                    if suggestion is None:
                        exhausted = True
                        break
                    key = memo_key(suggestion)
                    if key in memo:
                        row, result = memo[key]
                        record(suggestion, row, result, time.time(), cached=True)
                    elif key in batch_keys:
                        # Same combination twice in one batch -- it is
                        # in flight, so its result is not memoized yet.
                        # Hold it and serve it once the batch lands.
                        deferred.append(suggestion)
                    else:
                        batch_keys.add(key)
                        batch.append(suggestion)
                if not batch:
                    if deferred:
                        continue
                    break
                t0 = time.time()
                futures = {
                    executor.submit(
                        _evaluate,
                        payload_for(s["grid_step"], s["profit_target"], s["strategy_params"]),
                    ): s
                    for s in batch
                }
                for future in concurrent.futures.as_completed(futures):
                    suggestion = futures[future]
                    row, result = future.result()
                    memo[memo_key(suggestion)] = (row, result)
                    record(suggestion, row, result, t0)
                for suggestion in deferred:
                    row, result = memo[memo_key(suggestion)]
                    record(suggestion, row, result, time.time(), cached=True)

    results = pd.DataFrame(rows)
    results.to_csv(args.output, index=False)
    elapsed = time.time() - started
    done = state["done"]
    simulated = done - state["cached"]
    print(f"\n{done} evaluations in {elapsed / 3600:.2f}h ({elapsed / max(1, done):.1f}s each)")
    print(
        f"  {simulated} simulated, {state['cached']} served from cache "
        f"({100 * state['cached'] / max(1, done):.0f}% of the budget was repeat suggestions)"
    )
    print(f"Wrote {args.output}")

    pd.set_option("display.width", 250)
    cols = [
        c
        for c in [
            "Grid Step",
            "Profit Target",
            "per_lot_pct",
            "lookback_days",
            "event_day_boost_multiplier",
            "earnings_day_boost_multiplier",
            "Trade Count",
            "Closed Trade Count",
            "Total Return %",
            "Max Drawdown %",
            "Return/Drawdown",
        ]
        if c in results.columns
    ]
    if "Total Return %" in results.columns:
        # Deduplicated for DISPLAY only -- the CSV keeps one row per
        # trial (including cache hits), which is the honest record of
        # what the search did, but a leaderboard that lists the same
        # configuration fifteen times tells the reader nothing.
        axis_cols = [
            c
            for c in [
                "Grid Step",
                "Profit Target",
                "per_lot_pct",
                "lookback_days",
                "event_day_boost_multiplier",
                "earnings_day_boost_multiplier",
            ]
            if c in results.columns
        ]
        distinct = results.drop_duplicates(subset=axis_cols) if axis_cols else results
        admissible = distinct
        if args.max_drawdown is not None and "Max Drawdown %" in distinct.columns:
            admissible = distinct[distinct["Max Drawdown %"] <= args.max_drawdown]
            print(
                f"\n{len(admissible)} of {len(distinct)} distinct combinations are within "
                f"the {args.max_drawdown}% drawdown cap."
            )
        print(f"\nTop 15 distinct combinations by Total Return % (of {len(distinct)} evaluated):")
        print(
            admissible.sort_values("Total Return %", ascending=False)[cols].head(15).to_string()
        )


if __name__ == "__main__":
    main()
