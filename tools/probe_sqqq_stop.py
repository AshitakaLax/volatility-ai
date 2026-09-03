#!/usr/bin/env python
"""
Does a STOPPABLE SQQQ book work, now that a loss can be realized?

--------------------------------------------------------------------
WHY THIS IS A DIFFERENT QUESTION FROM measure_hedge_conditions.py

That tool asked "when can SQQQ be bought and later sold at a profit?"
and answered it fairly: the entry conditions do not separate at any
profit target big enough to matter. At +10% the best condition scores
54.7% against a 53.4% baseline. That is null, and no amount of
searching entry rules fixes it.

But that tool was measuring a game with one rule that no longer holds.
Its own header states the objection:

    "On SQQQ [enforce_no_loss] is a permanent bag-holding rule: a lot
    bought above a level the price never revisits is never sellable,
    and the capital is gone for the life of the run."

SQQQ fell 99.97% over 2016-2026. Under a no-loss-only engine, every lot
bought above a level the fund never sees again is dead capital forever.
src/no_loss_guard.SellReason.SIGNAL_EXIT removes that constraint: a lot
can now be cut. So the question worth re-asking is not "which entries
are good" -- it is "does a stop convert this from uninvestable to
merely bad, or is it bad either way".

--------------------------------------------------------------------
WHAT IS ACTUALLY MEASURED, AND ONE METRIC THAT HAD TO BE THROWN OUT

CAGR alone would flatter the no-stop run: a book frozen in
never-sellable lots can post a tolerable return on the sliver still
working while being uninvestable, because the frozen capital is not
available and not compounding. So the report also asks how many
positions never got out at all.

`unsold%` is Open Trade Count / Trade Count -- the share of every lot
ever opened that never found an exit by the end of the run. Both come
straight from the engine's own metrics.

**A first version of this column measured something else and looked
meaningful.** It reported the mark-to-market of open lots as a share of
final equity, and printed 50.4% on four runs whose open-lot counts
ranged from 8 to 1,415. Identical numbers across wildly different books
is not a finding, it is a tell. It was reporting the EXPOSURE CAP: the
book runs pinned against max_total_exposure_pct, so open-value over
equity just recovers that setting. Re-running at cap=0.25 printed
25.33% and confirmed it. The column answered "how much is deployed",
which the config already states, rather than "how much can never be
sold", which is the question.

--------------------------------------------------------------------
WHAT THIS IS NOT

Not a hedge test. A hedge is a claim about two books held together, and
this engine simulates one instrument per run -- combining two separately
simulated equity curves is exactly the splice that produced a fictional
43.50% CAGR and was falsified by tools/probe_regime_integrated.py. The
leg is tested on its own first because if a stoppable SQQQ book loses
money standing alone, no combination question arises.

Usage:
    python tools/probe_sqqq_stop.py
    python tools/probe_sqqq_stop.py --stops 0.05 0.10 0.20
"""

from __future__ import annotations

import argparse
import os as _os
import sys as _sys

_REPO_ROOT = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
if _REPO_ROOT not in _sys.path:
    _sys.path.insert(0, _REPO_ROOT)

import logging

import pandas as pd

from optimization_controller import OptimizationController
from src.config import BacktestConfig
from src.high_frequency_sizing import HighFrequencyLocalReferenceSizing
from src.performance_analyzer import annual_returns
from src.risk_manager import RiskManager

DATA = "data/SQQQ_rth_full.csv"


class Stopped(HighFrequencyLocalReferenceSizing):
    """Cuts any lot down more than `stop_pct` from its buy price.

    The crudest possible stop, deliberately. If the answer depends on a
    clever stop rule then the answer is a description of this dataset,
    and the point here is to find out whether the CATEGORY of change
    helps at all.

    stop_pct=None disables it entirely, which reproduces today's
    engine -- the lot is held until the price comes back, forever if it
    does not.
    """

    def __init__(self, *args, stop_pct: float | None = None, **kwargs):
        super().__init__(*args, **kwargs)
        self.stop_pct = stop_pct

    def lots_to_liquidate(self, open_lots, context) -> list:
        if self.stop_pct is None:
            return []
        floor = 1.0 - self.stop_pct
        price = context.price
        return [lot for lot in open_lots if price <= lot.buy_price * floor]


def run(controller, cfg, *, stop_pct, cap, per_lot, step, target):
    params = dict(cfg.strategy.strategy_params)
    params.update(per_lot_pct=per_lot, stop_pct=stop_pct)
    summary, full = controller.run_sweep(
        grid_steps=[step],
        profit_targets=[target],
        strategy_class=Stopped,
        strategy_params_grid=[params],
        cost_model=cfg.costs.build(),
        risk_manager=RiskManager(max_concurrent_lots=6000, max_total_exposure_pct=cap),
        fill_model="intrabar",
        intrabar_priority="sell_first",
        enforce_no_loss=True,
        # Harmless when stop_pct is None -- the hook returns nothing, so
        # the flag authorizes an empty list. That is the two-condition
        # gate doing its job, and it means the no-stop row really is
        # today's engine rather than a differently-configured one.
        allow_signal_exit=True,
        on_flat_reentry="stale_reference",
        return_full_results=True,
    )
    return summary.iloc[0], full[0]


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Stoppable SQQQ book.")
    parser.add_argument("--stops", type=float, nargs="*", default=[0.05, 0.10, 0.20, 0.40])
    parser.add_argument("--cap", type=float, default=0.50)
    parser.add_argument("--step", type=float, default=0.02)
    parser.add_argument("--target", type=float, default=0.04)
    parser.add_argument("--per-lot", type=float, default=0.02)
    parser.add_argument("--quiet", action="store_true", default=True)
    args = parser.parse_args(argv)
    if args.quiet:
        logging.disable(logging.WARNING)

    cfg = BacktestConfig.from_yaml("config/probe_dipbuy_full.yaml")
    frame = pd.read_csv(DATA, parse_dates=["timestamp"]).set_index("timestamp")
    controller = OptimizationController(historical_data=frame)

    price = frame["close"]
    print(
        f"SQQQ {price.iloc[0]:.2f} -> {price.iloc[-1]:.4f} "
        f"({(price.iloc[-1] / price.iloc[0] - 1) * 100:.2f}% over the period)"
    )
    print(
        f"grid step {args.step:.0%}, target {args.target:.0%}, "
        f"per-lot {args.per_lot:.0%}, exposure cap {args.cap:.0%}\n"
    )
    print(
        f"{'stop':>8} {'CAGR':>8} {'maxDD':>7} {'worst':>8} {'2022':>8} "
        f"{'openLots':>9} {'unsold':>8} {'exits':>7}"
    )

    for stop_pct in [None, *args.stops]:
        row, result = run(
            controller,
            cfg,
            stop_pct=stop_pct,
            cap=args.cap,
            per_lot=args.per_lot,
            step=args.step,
            target=args.target,
        )
        equity = result.equity_curve
        yearly = annual_returns(equity)
        y2022 = yearly[[i.year == 2022 for i in yearly.index]].iloc[0]

        opened = float(row["Trade Count"])
        still_open = float(row["Open Trade Count"])
        unsold = 100.0 * still_open / opened if opened else float("nan")
        label = "none" if stop_pct is None else f"{stop_pct:.0%}"
        print(
            f"{label:>8} {row['CAGR %']:7.2f}% {row['Max Drawdown %']:6.1f}% "
            f"{yearly.min():+7.2f}% {y2022:+7.2f}% {still_open:9.0f} "
            f"{unsold:7.1f}% {int(row['Signal Exit Count']):7d}"
        )
        print("         " + "  ".join(f"{ts.year}:{v:+.1f}%" for ts, v in yearly.items()))

    print("\nunsold = share of all lots ever opened that never found an exit.")
    print("A stop drives it to ~0 by construction -- it forces the exit -- so read")
    print("it against CAGR, not on its own: getting out of everything is only good")
    print("news if the getting out was not itself the loss.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
