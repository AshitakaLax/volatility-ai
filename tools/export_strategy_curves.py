#!/usr/bin/env python
"""
Export every strategy measured in this project to one JSON blob, so a
report can plot them against each other instead of against a table of
numbers copied by hand from separate runs.

Each strategy is run ONCE over the full dataset through the ordinary
engine -- same cost model, same enforce_no_loss, same fill model -- and
its per-bar equity curve is resampled to daily. Nothing here re-derives
a return from a summary statistic: the curves are the simulations'.

The one exception is SMA200-else-cash, which is not a grid strategy and
has no ledger. It is computed the way it always has been in this
project (daily TQQQ return when the prior close is above its own
200-session average, zero otherwise, less a switching cost), and it is
labelled a benchmark rather than a strategy everywhere it appears.

Usage:
    python tools/export_strategy_curves.py [--out PATH]
"""

from __future__ import annotations

import argparse
import json
import os as _os
import sys as _sys

_REPO_ROOT = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
if _REPO_ROOT not in _sys.path:
    _sys.path.insert(0, _REPO_ROOT)

import logging

import numpy as np
import pandas as pd

from optimization_controller import OptimizationController
from src.config import BacktestConfig
from src.performance_analyzer import annual_returns
from src.risk_manager import RiskManager
from tools.probe_bull_capture import RegimeHold
from tools.probe_downturn_tactics import Escalating
from tools.probe_regime_integrated import RegimeSwitched
from tools.probe_vol_filtered_regime import VolFilteredRegime, build_signal

DATA = "data/TQQQ_1Min_sip_all_2016-01-01_2026-08-21.csv"
SWITCH_COST = 0.0015


def _curve(equity: pd.Series) -> dict:
    daily = equity.resample("D").last().dropna()
    peak = daily.cummax()
    return {
        "dates": [d.strftime("%Y-%m-%d") for d in daily.index],
        "equity": [round(float(v), 2) for v in daily.values],
        "drawdown": [round(float(v), 4) for v in ((peak - daily) / peak * 100.0).values],
    }


def _stats(equity: pd.Series) -> dict:
    yearly = annual_returns(equity)
    complete = yearly[[ts.year < 2026 for ts in yearly.index]]
    years = (equity.index[-1] - equity.index[0]).days / 365.25
    peak = equity.cummax()
    return {
        "cagr": round(float((equity.iloc[-1] / equity.iloc[0]) ** (1 / years) - 1) * 100, 2),
        "total": round(float(equity.iloc[-1] / equity.iloc[0] - 1) * 100, 1),
        "maxdd": round(float(((peak - equity) / peak).max() * 100), 1),
        "annual": {str(ts.year): round(float(v), 1) for ts, v in yearly.items()},
        "worst_complete": round(float(complete.min()), 1),
        "neg_complete": int((complete < 0).sum()),
        "n_complete": len(complete),
    }


def run(controller, cfg, strategy_class, params, *, step, target, cap, signal_exits):
    summary, full = controller.run_sweep(
        grid_steps=[step],
        profit_targets=[target],
        strategy_class=strategy_class,
        strategy_params_grid=[params],
        cost_model=cfg.costs.build(),
        risk_manager=RiskManager(max_concurrent_lots=6000, max_total_exposure_pct=cap),
        fill_model="intrabar",
        intrabar_priority="sell_first",
        enforce_no_loss=True,
        allow_signal_exit=signal_exits,
        on_flat_reentry="stale_reference",
        return_full_results=True,
    )
    return full[0].equity_curve, int(summary.iloc[0]["Signal Exit Count"])


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Export strategy equity curves as JSON.")
    parser.add_argument("--out", default="strategy_curves.json")
    parser.add_argument("--quiet", action="store_true", default=True)
    args = parser.parse_args(argv)
    if args.quiet:
        logging.disable(logging.WARNING)

    cfg = BacktestConfig.from_yaml("config/probe_dipbuy_full.yaml")
    frame = pd.read_csv(DATA, parse_dates=["timestamp"]).set_index("timestamp")
    controller = OptimizationController(historical_data=frame)
    base = dict(cfg.strategy.strategy_params)

    out: dict = {"strategies": {}}

    # --- TQQQ itself, and the SMA200-else-cash benchmark ---
    price = frame["close"].resample("D").last().dropna()
    hold = price / price.iloc[0] * 100_000.0
    out["strategies"]["TQQQ buy & hold"] = {
        "kind": "reference",
        "note": "the instrument itself",
        **_stats(hold),
        "curve": _curve(hold),
    }

    ret = price.pct_change().fillna(0.0)
    bull = (price > price.rolling(200).mean()).shift(1).fillna(False)
    switch = (bull != bull.shift(1)).fillna(False)
    bench_ret = np.where(bull, ret, 0.0) - switch * SWITCH_COST
    bench = pd.Series((1 + bench_ret).cumprod() * 100_000.0, index=price.index)
    out["strategies"]["SMA200-else-cash"] = {
        "kind": "benchmark",
        "note": "hold TQQQ above the 200-day average, else cash",
        **_stats(bench),
        "curve": _curve(bench),
    }

    # --- the grid strategies, each one full engine run ---
    specs = [
        (
            "Regime, harvest bull",
            RegimeSwitched,
            dict(
                base,
                per_lot_pct=0.02,
                bull_step=0.005,
                bear_step=0.10,
                max_mult=400.0,
                dd_ref=0.75,
                regime_days=200,
                daily_signal=True,
                stand_aside_until_warm=True,
            ),
            0.10,
            0.04,
            0.50,
            True,
            "signal exits on; every complete year positive",
        ),
        (
            "Regime, hold bull (cap 0.50)",
            RegimeHold,
            dict(
                base,
                per_lot_pct=0.02,
                bull_lot_scale=5.0,
                bull_step=0.002,
                bear_step=0.05,
                bear_target=0.04,
                max_mult=400.0,
                dd_ref=0.75,
                regime_days=200,
                hold_in_bull=True,
            ),
            0.05,
            0.04,
            0.50,
            True,
            "holds the trend instead of harvesting it",
        ),
        (
            "Regime, hold bull (cap 1.00)",
            RegimeHold,
            dict(
                base,
                per_lot_pct=0.02,
                bull_lot_scale=2.0,
                bull_step=0.005,
                bear_step=0.05,
                bear_target=0.04,
                max_mult=400.0,
                dd_ref=0.75,
                regime_days=200,
                hold_in_bull=True,
            ),
            0.05,
            0.04,
            1.00,
            True,
            "full exposure; matches the benchmark's CAGR",
        ),
        (
            "Deep-dip escalating .10/.04",
            Escalating,
            dict(base, per_lot_pct=0.02, max_mult=400.0, dd_ref=0.75),
            0.10,
            0.04,
            0.50,
            False,
            "~98% cash; only trades deep drawdowns",
        ),
        (
            "Dip escalating .05/.04",
            Escalating,
            dict(base, per_lot_pct=0.02, max_mult=400.0, dd_ref=0.75),
            0.05,
            0.04,
            0.50,
            False,
            "the downturn winner, run over the whole period",
        ),
        (
            "Vol-filtered, hold bull",
            VolFilteredRegime,
            dict(
                base,
                per_lot_pct=0.02,
                signal=None,
                bull_step=0.005,
                bear_step=0.05,
                bear_target=0.04,
                bull_lot_scale=2.0,
                max_mult=400.0,
                dd_ref=0.75,
                hold_in_bull=True,
                use_dip_in_bear=False,
            ),
            0.05,
            0.04,
            1.00,
            True,
            "SMA200 AND calm volatility; holds the trend, cash otherwise",
        ),
    ]
    signal = build_signal(price, trend=200, vol_win=20, lookback=250, q=0.75)
    for label, cls, params, step, target, cap, exits, note in specs:
        if "signal" in params:
            params = dict(params, signal=signal)
        print(f"running {label} ...", flush=True)
        equity, n_exits = run(
            controller, cfg, cls, params, step=step, target=target, cap=cap, signal_exits=exits
        )
        out["strategies"][label] = {
            "kind": "strategy",
            "note": note,
            "signal_exits": n_exits,
            **_stats(equity),
            "curve": _curve(equity),
        }

    with open(args.out, "w", encoding="utf-8") as fh:
        json.dump(out, fh, separators=(",", ":"))
    size = _os.path.getsize(args.out) / 1e6
    print(f"\nwrote {args.out} ({size:.1f} MB), {len(out['strategies'])} series")
    for name, s in out["strategies"].items():
        print(
            f"  {name:34s} CAGR {s['cagr']:7.2f}%  maxDD {s['maxdd']:5.1f}%  "
            f"worst {s['worst_complete']:+7.1f}%  neg {s['neg_complete']}/{s['n_complete']}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
