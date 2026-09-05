#!/usr/bin/env python
"""Stage 1, redone: every indicator scored INSIDE the grid engine.

--------------------------------------------------------------------
WHY THIS EXISTS

The first Stage 1 scored 784 configurations in a long/cash shell on
daily bars, and Stage 3 showed that shell answers a different question
than this project asks. In a long/cash book "exit" means selling the
index and holding cash, costing the spread. In the grid it means closing
every open lot, and a signal exit is the ONE path permitted to realise a
loss -- so a signal that flips often crystallises the losing half of the
book at every flip. PLUS_DM measured 12.37% CAGR at -13.37% drawdown in
the shell and -0.19% in the engine, on 37,407 signal exits.

So the indicators were never the problem and the ranking was never
wrong; it was a ranking for a strategy nobody runs. This scores them
where the strategy actually lives: OptimizationController, 1-minute
bars, real costs, intrabar fills, one lot ledger, the no-loss guard.

--------------------------------------------------------------------
THE FLIP CAP, WHICH IS DERIVED AND NOT ARBITRARY

Stage 3 established the mechanism: liquidate-on-flip costs the losing
half of the book each time it fires. SMA200 flips ~27 times over the
sample and works; PLUS_DM flips ~277 and does not. The median indicator
here flips 362 times.

So flips are counted FIRST, on daily bars in milliseconds, and only
signals under the cap reach the engine. This is a filter with a
mechanism behind it rather than a budget cut -- though it is also a
budget cut, and both are true. Raise it with --max-flips if you want the
whole space; at ~30s a run the full 507 is about four hours.

--------------------------------------------------------------------
BOTH EXIT POLICIES, BECAUSE STAGE 3 SHOWED THEY ARE DIFFERENT STRATEGIES

  liquidate   close the book on a bull->bear flip. Protects against the
              drawdown, pays for it in realised losses.
  hold        stop BUYING in bear, keep the book. Costs nothing at the
              flip and provides no protection -- PLUS_DM's drawdown went
              straight back to buy-and-hold's -40.04% under this policy.

Neither dominates and the choice interacts with flip rate, so both are
run and both are reported.
"""

from __future__ import annotations

import argparse
import sys
import time
import warnings
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
warnings.filterwarnings("ignore")

from optimization_controller import OptimizationController
from src.config import BacktestConfig
from src.indicator_library import (
    available,
    compute,
    load_bars,
    signals,
    warmup_bars,
)
from src.risk_manager import RiskManager
from tools.indicator_sweep import INSTRUMENTS, Journal, config_id
from tools.probe_regime_integrated import annual_returns
from tools.probe_stage3_engine import IndicatorRegime


def candidates(symbol: str, max_flips: int, include_patterns: bool):
    """Signals whose flip count is low enough to survive the engine.

    Counted on daily bars, which costs milliseconds, so the expensive
    step only ever sees signals that can plausibly work.
    """
    bars = load_bars(INSTRUMENTS[symbol]["path"])
    out = []
    for ind in available(include_patterns=include_patterns):
        try:
            values = compute(ind, bars)
        except Exception:
            continue
        skip = warmup_bars(ind)
        for output in ind.outputs:
            try:
                states = signals(values[output], ind)
            except Exception:
                continue
            for variant, mask in states.items():
                flags = mask.iloc[skip:].fillna(False).astype(float)
                if len(flags) < 500:
                    continue
                flips = int((flags.diff().abs() > 0).sum())
                in_market = float(flags.mean()) * 100
                if flips > max_flips or in_market < 20 or in_market > 99.5:
                    continue
                out.append(
                    {
                        "indicator": ind.name,
                        "output": output,
                        "variant": variant,
                        "flips": flips,
                        "in_market_pct": round(in_market, 2),
                        "regime": {ts.date(): bool(v) for ts, v in mask.iloc[skip:].items()},
                    }
                )
    return out


def score(symbol: str, cand: dict, liquidate: bool, cfg, frame, target: float) -> dict:
    controller = OptimizationController(historical_data=frame)
    params = dict(cfg.strategy.strategy_params)
    params.update(
        per_lot_pct=0.002,
        bull_step=0.00075,
        bear_step=0.10,
        max_mult=400.0,
        dd_ref=0.75,
        regime_days=200,
        daily_signal=True,
        stand_aside_until_warm=True,
        regime_by_date=cand["regime"],
    )
    summary, full = controller.run_sweep(
        grid_steps=[0.10],
        profit_targets=[target],
        strategy_class=IndicatorRegime,
        strategy_params_grid=[params],
        cost_model=cfg.costs.build(),
        risk_manager=RiskManager(max_concurrent_lots=6000, max_total_exposure_pct=1.0),
        fill_model="intrabar",
        intrabar_priority="sell_first",
        enforce_no_loss=True,
        allow_signal_exit=liquidate,
        on_flat_reentry="stale_reference",
        return_full_results=True,
    )
    row = summary.iloc[0]
    yearly = annual_returns(full[0].equity_curve)
    return {
        "cagr": round(float(row["CAGR %"]), 3),
        "max_dd": round(float(row["Max Drawdown %"]), 3),
        "worst_year": round(float(yearly.min()), 3),
        "neg_years": int((yearly < 0).sum()),
        "trades": int(row["Trade Count"]),
        "signal_exits": int(row.get("Signal Exit Count", 0)),
    }


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--config", default="config/paper_aggressive.yaml")
    p.add_argument("--out", default="output/stage1_grid.jsonl")
    p.add_argument("--max-flips", type=int, default=120)
    p.add_argument("--target", type=float, default=0.04)
    p.add_argument("--no-patterns", action="store_true")
    p.add_argument("--instruments", nargs="+", default=list(INSTRUMENTS))
    p.add_argument("--no-resume", dest="resume", action="store_false")
    p.set_defaults(resume=True)
    args = p.parse_args(argv)

    journal = Journal(args.out)
    done = journal.done_ids() if args.resume else set()
    cfg = BacktestConfig.from_yaml(args.config)

    plan = []
    for symbol in args.instruments:
        cands = candidates(symbol, args.max_flips, not args.no_patterns)
        print(f"[grid1] {symbol}: {len(cands)} signals under {args.max_flips} flips")
        for c in cands:
            for liquidate in (True, False):
                plan.append((symbol, c, liquidate))

    total = len(plan)
    print(f"[grid1] {total} engine runs (~30s each, ~{total * 30 / 3600:.1f}h)")
    if done:
        print(f"[grid1] resuming: {len(done)} already complete")

    frames: dict[str, pd.DataFrame] = {}
    started = time.time()
    ran = failed = 0

    for i, (symbol, cand, liquidate) in enumerate(plan, 1):
        cid = config_id(
            symbol, cand["indicator"], cand["output"], cand["variant"], str(liquidate), "grid"
        )
        if cid in done:
            continue
        if symbol not in frames:
            frames[symbol] = pd.read_csv(
                INSTRUMENTS[symbol]["path"], parse_dates=["timestamp"]
            ).set_index("timestamp")
        try:
            m = score(symbol, cand, liquidate, cfg, frames[symbol], args.target)
            bh = INSTRUMENTS[symbol]["bh_cagr"]
            row = {
                "config_id": cid,
                "instrument": symbol,
                "indicator": cand["indicator"],
                "output": cand["output"],
                "variant": cand["variant"],
                "policy": "liquidate" if liquidate else "hold",
                "flips": cand["flips"],
                "in_market_pct": cand["in_market_pct"],
                "bh_cagr": bh,
                "beats_bh": m["cagr"] > bh,
                **m,
            }
            journal.write(row)
            ran += 1
            rate = (time.time() - started) / max(ran, 1)
            print(
                f"[{i:>4}/{total}] {symbol:<5} {cand['indicator']:<14} {cand['variant']:<6} "
                f"{row['policy']:<9} flips {cand['flips']:>4}  CAGR {m['cagr']:7.2f}% "
                f"(bh {bh:.2f})  DD {m['max_dd']:6.2f}%  exits {m['signal_exits']:>6}  "
                f"({rate:.0f}s, eta {rate * (total - i) / 3600:.1f}h)",
                flush=True,
            )
        except Exception as exc:
            failed += 1
            journal.write({"config_id": cid, "error": f"{type(exc).__name__}: {exc}"[:200]})

    print(f"\n[grid1] {ran} run, {failed} failed, {(time.time() - started) / 60:.1f} min")
    return 0


if __name__ == "__main__":
    sys.exit(main())
