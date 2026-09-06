#!/usr/bin/env python
"""Fill the run history with a spread of configurations worth comparing.

--------------------------------------------------------------------
WHY SEED AT ALL

An empty history ranks nothing, and the ranking view is the point of
having one. More usefully, a first-time reader should see a table where
DIFFERENT METRICS PICK DIFFERENT WINNERS -- because that is the honest
shape of this problem and the reason the metric is selectable rather
than fixed. A seed of near-identical runs would teach the opposite.

So the set below spans the axes that actually change the answer:
every sizing model, a range of grid steps and profit targets, both fill
models, and more than one instrument.

--------------------------------------------------------------------
THIS RUNS THE REAL ENGINE

Nothing here is fabricated. Each entry is executed through the same
run_backtest the API uses and archived through the same history module,
so a seeded row and a row from a run someone submitted are the same
thing and cannot be told apart -- which is what makes them comparable.

    python tools/seed_run_history.py               # the default set
    python tools/seed_run_history.py --limit 50000 # faster, coarser

--------------------------------------------------------------------
THE PARAMETERS ARE THIS PROJECT'S OWN

Strategy parameters come from server/backtest.STRATEGY_DEFAULTS, which
are lifted from the committed configs the project's sweeps selected.
They are a starting position, not a claim about what is best -- the
whole point of the table is to let a reader disagree.
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from server import history
from server.backtest import STRATEGY_DEFAULTS, run_backtest

# (label, tickers, grid_steps, profit_targets, sizing_model, fill_model)
#
# Chosen to disagree with each other. A tight step with a small target
# harvests constantly and shows a high win rate with modest return; a
# wide target holds inventory and looks better on CAGR while carrying
# stuck capital. Both are real, and a reader should see the trade rather
# than be handed a winner.
PLAN: list[tuple[str, list[str], list[float], list[float], str, str]] = [
    ("fixed, tight grid", ["TQQQ"], [0.0025, 0.005], [0.003, 0.005], "fixed", "close"),
    ("fixed, wide targets", ["TQQQ"], [0.005, 0.01], [0.01, 0.02], "fixed", "close"),
    ("fixed, intrabar fills", ["TQQQ"], [0.005], [0.003, 0.005], "fixed", "intrabar"),
    ("champion sizing", ["TQQQ"], [0.00075], [0.003, 0.005], "hf_local_reference", "close"),
    ("rsi momentum", ["TQQQ"], [0.005], [0.005, 0.01], "rsi", "close"),
    ("bell curve", ["TQQQ"], [0.005], [0.005, 0.01], "bell_curve", "close"),
    # One profit target only: this model estimates P(reaching ONE
    # target_return), so the engine refuses to sweep several against it.
    ("bayesian dual scale", ["TQQQ"], [0.005], [0.005], "bayesian_dual_scale", "close"),
    ("unleveraged, same grid", ["QQQ"], [0.0025, 0.005], [0.003, 0.005], "fixed", "close"),
    ("equal weight", ["RSP"], [0.0025, 0.005], [0.003, 0.005], "fixed", "close"),
    ("3x semis", ["SOXL"], [0.005, 0.01], [0.005, 0.01], "fixed", "close"),
]


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--limit",
        type=int,
        default=200_000,
        help="Bars per configuration. Lower is faster and coarser.",
    )
    parser.add_argument("--start", default=None, help="ISO date, inclusive.")
    parser.add_argument("--end", default=None, help="ISO date, inclusive.")
    parser.add_argument(
        "--only",
        default=None,
        help="Substring filter on the label, to re-run one entry.",
    )
    args = parser.parse_args(argv)

    print(f"Seeding run history into {history.directory()}\n")
    started = time.time()
    seeded = failed = 0

    for label, tickers, steps, targets, model, fill in PLAN:
        if args.only and args.only.lower() not in label.lower():
            continue
        request = {
            "tickers": tickers,
            "grid_steps": steps,
            "profit_targets": targets,
            "sizing_model": model,
            "strategy_params": STRATEGY_DEFAULTS.get(model, {}),
            "fill_model": fill,
            "limit": args.limit,
        }
        if args.start:
            request["start"] = args.start
        if args.end:
            request["end"] = args.end

        run_id = f"seed-{model}-{fill}-{'-'.join(tickers)}-{abs(hash(label)) % 10000:04d}"
        cells = len(steps) * len(targets)
        print(f"  {label:<24} {','.join(tickers):<6} {cells} cells ... ", end="", flush=True)

        began = time.time()
        try:
            report = run_backtest(request, lambda fraction, note: None)
        except Exception as exc:
            # One bad entry must not abandon the rest -- a missing data
            # file for one instrument is the common case and says
            # nothing about the others.
            failed += 1
            print(f"FAILED {type(exc).__name__}: {exc}"[:120])
            continue

        report["run_id"] = run_id
        history.save(
            run_id,
            {
                "run_id": run_id,
                "status": "complete",
                "progress": 1.0,
                "message": f"seeded: {label}",
                "report": report,
                "error": None,
            },
        )
        seeded += 1
        fund = next(iter(report["funds"].values()))
        metrics = fund["metrics"]
        print(
            f"{time.time() - began:5.1f}s  CAGR {metrics['cagr_pct']:7.2f}%  "
            f"DD {metrics['max_drawdown_pct']:6.2f}%  trades {metrics['total_trades']}"
        )

    print(f"\n{seeded} seeded, {failed} failed, {(time.time() - started) / 60:.1f} min")
    return 0 if seeded else 1


if __name__ == "__main__":
    sys.exit(main())
