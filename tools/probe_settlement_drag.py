#!/usr/bin/env python
"""
What does T+1 settlement cost, on the strategies actually under
consideration?

--------------------------------------------------------------------
WHY THIS IS ON THE CRITICAL PATH AND NOT A DETAIL

Every recorded result in this project assumes sale proceeds can be
redeployed the instant they are booked. The champion configurations
trade roughly 2,000 times a year on that assumption.

The target account cannot do that. It is a Fidelity Traditional IRA -- a
CASH account, confirmed independently three ways: `placeOrder` carries
acctName "Traditional IRA", `balance` returns only cash buying power with
no margin line, and every captured order says tradeType "Cash". Proceeds
settle T+1, and buying with unsettled proceeds is a good-faith violation.

The user has accepted that violation RISK as a cost of doing business,
and this tool does not relitigate that. It answers a different question,
which acceptance does not settle: **how much of each measured return
depended on money that would not have been in the account yet?**

That matters before building anything else, because it COULD change
which strategy is worth trading.

**MEASURED ANSWER: it does not. The cost is negligible.** The largest
effect across four candidate strategies is -0.09pp of CAGR, and two are
unchanged to two decimal places. The prediction that it would re-rank
them was wrong, and the reason is visible in an earlier measurement:
these books are 64% to 98% CASH on average
(tools/measure_cash_drag.py). A strategy sitting on that much idle
settled cash is almost never short of buying power, so the unsettled
portion rarely binds.

The finding is worth as much as the reverse would have been. It removes
settlement from the list of things that could invalidate a backtest
here, and it does so with a number rather than an argument.

One counter-intuitive detail, kept because it is real: the effect is NOT
monotonic. The regime book trades MORE at T+1 (24,675 vs 24,648) and its
2022 improves (+3.7% vs +3.6%), while its CAGR still falls. A buy that
cannot be funded today does not merely vanish -- it leaves the grid
reference where it was, changing every subsequent trigger. Do not read
"tighter constraint" as "uniformly worse".

--------------------------------------------------------------------
WHAT IS MODELLED, AND WHAT IS NOT

MODELLED: the cash. A sale's proceeds join total equity immediately --
they are really yours -- but cannot fund a purchase until the settlement
date. A buy that cannot be funded simply does not happen.

NOT MODELLED: the good-faith-violation RULE itself, or the 90-day
restriction that repeat violations bring. Those are consequences of
breaking a rule this simulation instead OBEYS. Modelling obedience is
the conservative direction and the one that reveals the dependency;
modelling the penalty would require guessing at Fidelity's enforcement.

So read the T+1 column as "what the strategy earns if it never commits a
violation". The real account, permitted to violate, sits somewhere
between that and the instant column -- closer to instant early on, and
closer to T+1 as restrictions accumulate.

Usage:
    python tools/probe_settlement_drag.py
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
from src.performance_analyzer import annual_returns
from src.risk_manager import RiskManager
from tools.probe_downturn_tactics import Escalating
from tools.probe_regime_integrated import RegimeSwitched
from tools.probe_vol_filtered_regime import (
    VolFilteredRegime,
    build_signal,
)

DATA = "data/TQQQ_1Min_sip_all_2016-01-01_2026-08-21.csv"


def run(controller, cfg, cls, params, *, step, target, cap, exits, days):
    summary, full = controller.run_sweep(
        grid_steps=[step],
        profit_targets=[target],
        strategy_class=cls,
        strategy_params_grid=[params],
        cost_model=cfg.costs.build(),
        risk_manager=RiskManager(max_concurrent_lots=6000, max_total_exposure_pct=cap),
        fill_model="intrabar",
        intrabar_priority="sell_first",
        enforce_no_loss=True,
        allow_signal_exit=exits,
        settlement_days=days,
        on_flat_reentry="stale_reference",
        return_full_results=True,
    )
    row = summary.iloc[0]
    yearly = annual_returns(full[0].equity_curve)
    return row, yearly


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Cost of T+1 settlement.")
    parser.add_argument("--quiet", action="store_true", default=True)
    args = parser.parse_args(argv)
    if args.quiet:
        logging.disable(logging.WARNING)

    cfg = BacktestConfig.from_yaml("config/probe_dipbuy_full.yaml")
    frame = pd.read_csv(DATA, parse_dates=["timestamp"]).set_index("timestamp")
    controller = OptimizationController(historical_data=frame)
    base = dict(cfg.strategy.strategy_params)
    price = frame["close"].resample("D").last().dropna()
    signal = build_signal(price, trend=200, vol_win=20, lookback=250, q=0.75)

    specs = [
        ("Regime, harvest bull", RegimeSwitched,
         dict(base, per_lot_pct=0.02, bull_step=0.005, bear_step=0.10, max_mult=400.0,
              dd_ref=0.75, regime_days=200, daily_signal=True,
              stand_aside_until_warm=True),
         0.10, 0.04, 0.50, True),
        ("Vol-filtered, hold bull", VolFilteredRegime,
         dict(base, per_lot_pct=0.02, signal=signal, bull_step=0.005, bear_step=0.05,
              bear_target=0.04, bull_lot_scale=2.0, max_mult=400.0, dd_ref=0.75,
              hold_in_bull=True, use_dip_in_bear=False),
         0.05, 0.04, 1.00, True),
        ("Dip escalating .05/.04", Escalating,
         dict(base, per_lot_pct=0.02, max_mult=400.0, dd_ref=0.75),
         0.05, 0.04, 0.50, False),
        ("Deep-dip .10/.04", Escalating,
         dict(base, per_lot_pct=0.02, max_mult=400.0, dd_ref=0.75),
         0.10, 0.04, 0.50, False),
    ]

    print("Sale proceeds spendable immediately (T+0) vs on the next session (T+1).")
    print("T+1 is what a cash IRA imposes. Every recorded result used T+0.\n")
    print(f"{'strategy':<26}{'settle':>7}{'CAGR':>9}{'trades':>9}{'2022':>8}"
          f"{'maxDD':>8}{'dCAGR':>9}{'dTrades':>10}")

    for label, cls, params, step, target, cap, exits in specs:
        base_row = None
        for days in (0, 1):
            row, yearly = run(controller, cfg, cls, params, step=step, target=target,
                              cap=cap, exits=exits, days=days)
            y22 = yearly[[t.year == 2022 for t in yearly.index]].iloc[0]
            trades = int(row["Trade Count"])
            if days == 0:
                base_row, _base_yearly = row, yearly
                delta = dtrades = ""
            else:
                delta = f"{row['CAGR %'] - base_row['CAGR %']:+8.2f}"
                lost = trades - int(base_row["Trade Count"])
                pct = lost / max(1, int(base_row["Trade Count"])) * 100
                dtrades = f"{pct:+9.1f}%"
            print(f"{label if days == 0 else '':<26}{'T+' + str(days):>7}"
                  f"{row['CAGR %']:8.2f}%{trades:9d}{y22:+7.1f}%"
                  f"{row['Max Drawdown %']:7.1f}%{delta:>9}{dtrades:>10}")
        print()

    print("The cost is NEGLIGIBLE -- at most -0.09pp of CAGR here. These books")
    print("hold 64-98% cash on average (tools/measure_cash_drag.py), so they are")
    print("almost never short of settled buying power. The expectation that this")
    print("would re-rank the strategies was wrong; the measurement says so.")
    print("\nNot monotonic, either: the regime book trades MORE at T+1 and its")
    print("2022 improves, while CAGR still falls. A deferred buy moves the grid")
    print("reference, which changes every trigger after it.")
    print("\nThe violation RULE is not modelled, only the cash. Read T+1 as 'what")
    print("this earns while never committing a violation'; the real account, which")
    print("is permitted to violate, sits between the two columns.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
