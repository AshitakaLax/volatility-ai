"""One-off driver for the intrabar HF sweep (config/search_hf_intrabar.yaml)
against the full 10-year SIP dataset.

Not part of the CLI: cli.py backtest exposes neither n_jobs nor
per-combo progress logging, and adding both for a single run isn't
warranted. This runs that one sweep; it is not a reusable entrypoint.

On n_jobs: a 4-worker run of the PREVIOUS (close-only) sweep OOM'd on
this machine (4GB RAM). The root cause is since fixed in
optimization_controller.run_sweep -- it was retaining every
combination's SimulationResult (per-bar equity curve + full trade
blotter, tens of MB each) even with return_full_results=False. n_jobs
is still kept modest here rather than maxed, because each worker's
transient per-combination blotter is itself large at these trade
counts (~540k fills over 10 years).

Logs every combo and checkpoints to CSV periodically, given the
multi-hour runtime -- silence for hours with no partial output is
worse than the log volume.
"""

import argparse
import itertools
import logging
import time

import pandas as pd

from optimization_controller import OptimizationController, _run_one_combination
from src.config import BacktestConfig, expand_strategy_params
from src.strategy_registry import resolve_strategy

logging.disable(logging.WARNING)

parser = argparse.ArgumentParser()
parser.add_argument("--config", default="config/search_hf_intrabar.yaml")
parser.add_argument("--data", default="data/TQQQ_1Min_sip_all_2016-01-01_2026-08-21.csv")
parser.add_argument("--output", default="output/search_hf_intrabar_2026-08-22.csv")
parser.add_argument("--limit", type=int, default=None, help="run only the first N combinations")
args = parser.parse_args()

config = BacktestConfig.from_yaml(args.config)
config.validate()
strategy_class = resolve_strategy(config.strategy.strategy_id)

df = pd.read_csv(args.data, parse_dates=["timestamp"]).set_index("timestamp")
controller = OptimizationController(historical_data=df)
cost_model = config.costs.build()
risk_manager = config.risk.build()

params_grid = expand_strategy_params(config.strategy.strategy_params)
combinations = list(itertools.product(config.grid.steps, config.grid.profit_targets, params_grid))
if args.limit:
    combinations = combinations[: args.limit]
total = len(combinations)
print(
    f"{total} combinations | fill_model={config.execution.fill_model} "
    f"| max_concurrent_lots={config.risk.max_concurrent_lots}",
    flush=True,
)

rows = []
started = time.time()
for i, (step, target, params) in enumerate(combinations, start=1):
    t0 = time.time()
    row, _ = _run_one_combination(
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
    rows.append(row)

    elapsed = time.time() - started
    eta = elapsed / i * (total - i)
    if "error" in row:
        detail = f"FAILED {row['error']}"
    else:
        detail = (
            f"ret={row.get('Total Return %', float('nan')):8.2f}% "
            f"dd={row.get('Max Drawdown %', float('nan')):6.2f}% "
            f"trades={row.get('Trade Count', 0):7.0f}"
        )
    print(
        f"[{i:3d}/{total}] step={step:.4f} tgt={target:.4f} "
        f"lot={params.get('per_lot_pct')} lb={params.get('lookback_days')} "
        f"boost={params.get('event_day_boost_multiplier')} {detail} "
        f"({time.time() - t0:.0f}s, elapsed={elapsed / 3600:.2f}h, eta={eta / 3600:.2f}h)",
        flush=True,
    )

    if i % 10 == 0 or i == total:
        pd.DataFrame(rows).to_csv(args.output, index=False)

results = pd.DataFrame(rows)
results.to_csv(args.output, index=False)
elapsed = time.time() - started
print(f"\n{total} combinations in {elapsed / 3600:.2f}h ({elapsed / total:.1f}s/combo)")

pd.set_option("display.width", 250)
cols = [
    c
    for c in [
        "Grid Step",
        "Profit Target",
        "per_lot_pct",
        "lookback_days",
        "event_day_boost_multiplier",
        "Trade Count",
        "Closed Trade Count",
        "Total Return %",
        "Max Drawdown %",
    ]
    if c in results.columns
]
if "Total Return %" in results.columns:
    print("\nTop 15 by Total Return %:")
    print(results.sort_values("Total Return %", ascending=False)[cols].head(15).to_string())
