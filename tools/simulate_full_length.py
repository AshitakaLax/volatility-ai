#!/usr/bin/env python
"""Run a small grid, full length, on a ticker -- for a brand-new instrument.

--------------------------------------------------------------------
WHY THIS IS ITS OWN SCRIPT, AND NOT rerun_top_configurations.py AGAIN

That script ranks EXISTING history to decide what is worth re-running
properly. A ticker that was just downloaded has none: there is nothing
to rank yet. This runs a small, explicit grid directly, full length,
which is the thing rerun_top_configurations.py does only after it has
something to select from.

--------------------------------------------------------------------
THE PREDICTION, RECORDED BEFORE RUNNING

The last full-length pass on this project's existing tickers found that
four of five sizing models strand: the grid buys relative to
last_buy_price, which only ratchets DOWN, so once the book goes flat in
a persistently rising market the reference is left behind and the book
never reopens. hf_local_reference is immune because it maintains a
ROLLING local reference rather than a fixed one -- which is why it is
the only model this project's real deployment uses.

Both models run here on purpose. `fixed` is included as a labelled
comparison, not because it is expected to work: on an instrument that
has risen for a decade, the prediction is that it strands early and
reports a suspiciously flat worst-year figure, the same signature found
last time. That prediction is checked against the result rather than
being asserted after the fact.

--------------------------------------------------------------------
ONE CONFIGURATION PER RUN

Matches rerun_top_configurations.py's own reasoning: a full-length
result holds a ~1M-row equity curve and a blotter that can reach into
the hundreds of thousands of rows, and holding several in memory at
once is how a machine runs out of it.
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from server import history
from server.backtest import KNOWN_DATA, STRATEGY_DEFAULTS, run_backtest

# A modest grid: enough for the sweep matrix to show a real surface
# without turning "run full simulations" into a research program.
GRID_STEPS = [0.0025, 0.005, 0.01]
PROFIT_TARGETS = [0.003, 0.005, 0.01]


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--tickers", nargs="+", required=True)
    parser.add_argument(
        "--models",
        nargs="+",
        default=["hf_local_reference", "fixed"],
        help="Sizing models to run. hf_local_reference is this project's real strategy.",
    )
    args = parser.parse_args(argv)

    for ticker in args.tickers:
        if ticker not in KNOWN_DATA or not Path(KNOWN_DATA[ticker]).exists():
            print(f"SKIP {ticker}: no data file registered in KNOWN_DATA")
            continue

    plan = [
        (ticker, model, step, target)
        for ticker in args.tickers
        if ticker in KNOWN_DATA and Path(KNOWN_DATA[ticker]).exists()
        for model in args.models
        for step in GRID_STEPS
        for target in PROFIT_TARGETS
    ]
    print(f"{len(plan)} full-length runs planned\n")

    started = time.time()
    done = failed = 0
    for index, (ticker, model, step, target) in enumerate(plan, 1):
        label = f"[{index:>3}/{len(plan)}] {ticker:<5} {model:<20} {step * 100:6.3f}% / {target * 100:6.3f}%"
        print(f"{label} ... ", end="", flush=True)

        began = time.time()
        try:
            report = run_backtest(
                {
                    "tickers": [ticker],
                    "grid_steps": [step],
                    "profit_targets": [target],
                    "sizing_model": model,
                    "strategy_params": STRATEGY_DEFAULTS.get(model, {}),
                    "limit": None,  # the whole file
                },
                lambda fraction, note: None,
            )
        except Exception as exc:
            failed += 1
            print(f"FAILED {type(exc).__name__}: {exc}"[:110])
            continue

        run_id = f"full-{model}-{ticker}-{step * 100:.4f}-{target * 100:.4f}".replace(".", "p")
        report["run_id"] = run_id
        history.save(
            run_id,
            {
                "run_id": run_id,
                "status": "complete",
                "progress": 1.0,
                "message": f"full-length: {model} on {ticker}",
                "report": report,
                "error": None,
            },
        )
        done += 1
        fund = report["funds"][ticker]
        metrics = fund["metrics"]
        print(
            f"{time.time() - began:6.1f}s  {fund['bars']['count']:>9,} bars  "
            f"CAGR {metrics['cagr_pct']:7.2f}%  DD {metrics['max_drawdown_pct']:6.2f}%  "
            f"worst yr {metrics.get('worst_year_pct', 0):7.2f}%  trades {metrics['total_trades']}"
        )

    print(f"\n{done} run, {failed} failed, {(time.time() - started) / 60:.1f} min")
    return 0


if __name__ == "__main__":
    sys.exit(main())
