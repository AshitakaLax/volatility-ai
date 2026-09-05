#!/usr/bin/env python
"""Stage 3: the surviving signals through the REAL engine, minute bars.

Stages 1 and 2 measured indicators in a long/cash shell on daily bars.
That shell is not the strategy this project runs. This puts the
survivors through `OptimizationController` on 1-minute data with costs,
the no-loss guard, intrabar fills and one ledger -- the same machinery
the live loop uses.

--------------------------------------------------------------------
WHY THE SIGNAL STAYS DAILY

The indicator is computed on DAILY bars and looked up by session date,
not recomputed per minute. That is not a shortcut, it is the thing that
was measured: a 21-period PLUS_DM on minute bars is a 21-MINUTE signal,
a different statement about the market that Stages 1 and 2 never tested.

It is also the mistake this project has already made once. A regime
probe flipped on minute bars, logged 7,334 signal exits -- each a
realised loss -- and was being compared against a daily benchmark. Two
different strategies. Evaluating once per session moved it from 7.38% to
12.97% CAGR.

So: daily signal, minute execution. What changes between Stage 2 and
here is not the signal but everything around it -- real fills, real
costs, a real lot ledger that carries inventory across regime flips, and
the no-loss guard refusing to close what is under water.

--------------------------------------------------------------------
WHAT THIS IS EXPECTED TO SHOW

Stage 2's prior, written down before running: the TQQQ trend-line family
should NOT survive. Its entire effect lived in one lookback column of an
eighteen-cell surface. PLUS_DM and ADOSC on RSP cleared their bar in 17
of 18 cells and are the ones with a real chance.

Recording that here so the result is read against a prediction rather
than after the fact.
"""

from __future__ import annotations

import argparse
import sys
import warnings
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
warnings.filterwarnings("ignore")

from optimization_controller import OptimizationController
from src.config import BacktestConfig
from src.indicator_library import available, compute, load_bars, signals, warmup_bars
from src.risk_manager import RiskManager
from tools.indicator_sweep import INSTRUMENTS
from tools.probe_regime_integrated import RegimeSwitched, annual_returns

# (instrument, indicator, output, variant, params, lookback) for the
# signals Stage 2 left standing, with the parameters it chose.
CANDIDATES = [
    ("RSP", "PLUS_DM", "real", "below", {"timeperiod": 21}, 100),
    ("RSP", "ADOSC", "real", "below", {"fastperiod": 9, "slowperiod": 30}, 500),
    ("TQQQ", "LINEARREG", "real", "above", {"timeperiod": 14}, 250),
    ("TQQQ", "TSF", "real", "above", {"timeperiod": 14}, 250),
]


def daily_regime(symbol: str, name: str, output: str, variant: str, params: dict, lookback: int):
    """The bull/bear flag per session date, from daily bars."""
    inventory = {i.name: i for i in available()}
    ind = inventory[name]
    bars = load_bars(INSTRUMENTS[symbol]["path"])
    values = compute(ind, bars, **params)[output]
    flags = signals(values, ind, lookback=lookback)[variant]
    skip = max(warmup_bars(ind, **params), lookback)
    flags = flags.iloc[skip:]
    return {ts.date(): bool(v) for ts, v in flags.items()}


class IndicatorRegime(RegimeSwitched):
    """RegimeSwitched with its SMA replaced by a precomputed signal.

    Only `_read_regime` changes. Everything else -- the asymmetric grid
    trigger, the liquidate-on-flip hook, the warmup gate -- is inherited,
    so any difference in the result attributes to the SIGNAL and not to a
    second implementation of the surrounding strategy.
    """

    def __init__(self, *args, regime_by_date=None, **kwargs):
        super().__init__(*args, **kwargs)
        self._regime_by_date = regime_by_date or {}
        self._last_seen = False

    def _read_regime(self, price: float) -> bool:
        # Falls back to the LAST KNOWN value on a date the signal does
        # not cover, rather than to False. Returning bear on an unknown
        # date would liquidate the book at every gap in the daily series,
        # which is a data artifact masquerading as a trading decision.
        ts = getattr(self, "_current_timestamp", None)
        if ts is None:
            return self._last_seen
        self._last_seen = self._regime_by_date.get(ts.date(), self._last_seen)
        return self._last_seen

    def record_tick(self, context):
        self._current_timestamp = context.timestamp
        return super().record_tick(context)


def run_one(symbol, name, output, variant, params, lookback, args) -> dict:
    cfg = BacktestConfig.from_yaml(args.config)
    frame = pd.read_csv(INSTRUMENTS[symbol]["path"], parse_dates=["timestamp"]).set_index(
        "timestamp"
    )
    controller = OptimizationController(historical_data=frame)
    regime = daily_regime(symbol, name, output, variant, params, lookback)

    strategy_params = dict(cfg.strategy.strategy_params)
    strategy_params.update(
        per_lot_pct=0.002,
        bull_step=0.00075,
        bear_step=0.10,
        max_mult=400.0,
        dd_ref=0.75,
        regime_days=200,
        daily_signal=True,
        stand_aside_until_warm=True,
        regime_by_date=regime,
    )
    summary, full = controller.run_sweep(
        grid_steps=[0.10],
        profit_targets=[args.target],
        strategy_class=IndicatorRegime,
        strategy_params_grid=[strategy_params],
        cost_model=cfg.costs.build(),
        risk_manager=RiskManager(max_concurrent_lots=6000, max_total_exposure_pct=1.0),
        fill_model="intrabar",
        intrabar_priority="sell_first",
        enforce_no_loss=True,
        # A HIGH-FLIP SIGNAL CANNOT AFFORD LIQUIDATE-ON-FLIP. In the
        # long/cash shell of Stages 1-2, "exit" means selling the index
        # and going to cash, which costs nothing beyond the spread. In
        # the grid it means closing every open lot, and enforce_no_loss
        # notwithstanding, a SIGNAL exit is the one path permitted to
        # realise a loss -- so each flip crystallises the losing half of
        # the book. PLUS_DM flips 277 times against SMA200's 27.
        allow_signal_exit=args.signal_exits,
        on_flat_reentry="stale_reference",
        return_full_results=True,
    )
    row = summary.iloc[0]
    yearly = annual_returns(full[0].equity_curve)
    return {
        "instrument": symbol,
        "signal": f"{name}.{output} {variant}",
        "cagr": round(float(row["CAGR %"]), 2),
        "max_dd": round(float(row["Max Drawdown %"]), 2),
        "worst_year": round(float(yearly.min()), 2),
        "neg_years": int((yearly < 0).sum()),
        "trades": int(row["Trade Count"]),
        "signal_exits": int(row.get("Signal Exit Count", 0)),
        "liquidate_on_flip": bool(args.signal_exits),
        "bh_cagr": INSTRUMENTS[symbol]["bh_cagr"],
    }


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--config", default="config/paper_aggressive.yaml")
    p.add_argument("--target", type=float, default=0.04)
    p.add_argument("--only", help="Substring filter on the indicator name.")
    p.add_argument("--out", default="output/stage3_engine.csv")
    p.add_argument(
        "--no-signal-exits",
        dest="signal_exits",
        action="store_false",
        help="Stop buying in bear but keep the book, instead of liquidating on flip.",
    )
    p.set_defaults(signal_exits=True)
    args = p.parse_args(argv)

    print("Stage 3: daily signal, MINUTE execution, real engine.")
    print("Prior from Stage 2, recorded before running: the TQQQ trend-line family")
    print("should NOT survive (3 of 18 settings); PLUS_DM and ADOSC should (17 of 18).\n")

    rows = []
    for symbol, name, output, variant, params, lookback in CANDIDATES:
        if args.only and args.only.upper() not in name.upper():
            continue
        print(f"[stage3] {symbol} {name} {variant} {params} lb={lookback} ...", flush=True)
        try:
            r = run_one(symbol, name, output, variant, params, lookback, args)
            rows.append(r)
            print(
                f"[stage3]   CAGR {r['cagr']:7.2f}% (buy-and-hold {r['bh_cagr']:.2f}%)  "
                f"DD {r['max_dd']:6.2f}%  worst yr {r['worst_year']:+7.2f}%  "
                f"trades {r['trades']}  signal exits {r['signal_exits']}",
                flush=True,
            )
        except Exception as exc:
            print(f"[stage3]   FAILED {type(exc).__name__}: {exc}", flush=True)

    if rows:
        frame = pd.DataFrame(rows)
        Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        frame.to_csv(args.out, index=False)
        print(f"\n{frame.to_string(index=False)}\n-> {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
