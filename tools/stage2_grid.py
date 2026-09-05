#!/usr/bin/env python
"""Stage 2, redone: are the grid-native leaders ridges or single cells?

--------------------------------------------------------------------
WHY THIS EXISTS

Stage 1-grid found ten configurations that beat buy-and-hold on
return/drawdown, led by NATR-below -- the only signal to lead on BOTH
instruments and BOTH exit policies. Every one of them was scored at ONE
parameter setting: the indicator's TA-Lib default period, and a 250-bar
threshold lookback picked as a generic rule.

That is exactly the position Stage 1 was in before Stage 2 ran, and
Stage 2's answer was brutal. TQQQ LINEARREG looked like the strongest
result in the sweep and turned out to live in one lookback column of an
eighteen-cell surface -- 250 was the only column that worked, and it had
been chosen by convention rather than by evidence. Reporting the best
cell of a surface nobody had looked at is how that happened.

So the same test, in the engine this time: sweep each leader's periods
across a 6x range and its threshold lookback across 100/250/500, and ask
how the NEIGHBOURS did. A real parameter effect is a ridge. A maximum
surrounded by mediocrity is a noisy sample's argmax and will not survive
new data.

--------------------------------------------------------------------
WHICH POLICY EACH CANDIDATE RUNS UNDER

Stage 1-grid measured 147 paired runs and found liquidate-on-flip worse
for return in 146 of them, so the policy question is settled and does not
need re-answering per parameter cell. Each candidate is swept under the
policy it actually survived under -- `liquidate` for nine of ten -- which
halves the cost against sweeping both.

NATR is the exception and gets both, because it survived under both and
is the candidate this stage exists to test.

--------------------------------------------------------------------
BOTH METRICS ARE REPORTED, BECAUSE THE BAR IS NOT SETTLED

Nothing in Stage 1-grid cleared the return floor, and the ten survivors
survived on return/drawdown. Which bar applies is the user's call, so
the ridge test runs on both surfaces rather than silently adopting the
one that flatters the candidate.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
import warnings
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
warnings.filterwarnings("ignore")

from optimization_controller import OptimizationController
from src.config import BacktestConfig
from src.indicator_library import available, compute, load_bars, signals, warmup_bars
from src.risk_manager import RiskManager
from tools.indicator_sweep import (
    INSTRUMENTS,
    RETURN_FLOOR,
    Journal,
    config_id,
    param_grid,
    ridge_scores,
)
from tools.probe_regime_integrated import annual_returns
from tools.probe_stage3_engine import IndicatorRegime

LOOKBACKS = (100, 250, 500)


def leaders(path: str) -> list[dict]:
    """The Stage 1-grid rows that beat buy-and-hold on return/drawdown.

    Read from the journal rather than hard-coded, so this stage cannot
    quietly disagree with the stage that selected its input.
    """
    with open(path, encoding="utf-8") as fh:
        rows = [json.loads(line) for line in fh if line.strip()]
    frame = pd.DataFrame([r for r in rows if "error" not in r])
    frame["ret_dd"] = frame.cagr / frame.max_dd.abs()
    bar = frame.instrument.map({k: v["bh_ret_dd"] for k, v in INSTRUMENTS.items()})
    frame = frame[frame.ret_dd > bar]

    out: dict[tuple, dict] = {}
    for row in frame.itertuples():
        key = (row.instrument, row.indicator, row.output, row.variant)
        entry = out.setdefault(key, {"policies": set(), "stage1_ret_dd": 0.0})
        entry["policies"].add(row.policy)
        entry["stage1_ret_dd"] = max(entry["stage1_ret_dd"], round(row.ret_dd, 3))
    return [
        {
            "instrument": k[0],
            "indicator": k[1],
            "output": k[2],
            "variant": k[3],
            "policies": sorted(v["policies"]),
            "stage1_ret_dd": v["stage1_ret_dd"],
        }
        for k, v in out.items()
    ]


def daily_regime(symbol, ind, output, variant, params, lookback):
    """The bull/bear flag per session date, from DAILY bars.

    Daily, not per-minute, for the reason probe_stage3_engine records: a
    21-period indicator on minute bars is a 21-MINUTE signal, a different
    claim about the market than anything these stages measured.
    """
    bars = load_bars(INSTRUMENTS[symbol]["path"])
    values = compute(ind, bars, **params)[output]
    flags = signals(values, ind, lookback=lookback)[variant]
    skip = max(warmup_bars(ind, **params), lookback)
    flags = flags.iloc[skip:]
    regime = {ts.date(): bool(v) for ts, v in flags.items()}
    numeric = flags.astype(float)
    flips = int((numeric.diff().abs() > 0).sum())
    return regime, flips, round(float(numeric.mean()) * 100, 2)


def score(regime, liquidate, cfg, frame, target) -> dict:
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
        regime_by_date=regime,
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
    cagr = round(float(row["CAGR %"]), 3)
    dd = round(float(row["Max Drawdown %"]), 3)
    return {
        "cagr": cagr,
        "max_dd": dd,
        "ret_dd": round(cagr / abs(dd), 4) if dd else 0.0,
        "worst_year": round(float(yearly.min()), 3),
        "neg_years": int((yearly < 0).sum()),
        "trades": int(row["Trade Count"]),
        "signal_exits": int(row.get("Signal Exit Count", 0)),
    }


def build_plan(source: str) -> list[tuple]:
    inventory = {i.name: i for i in available()}
    plan = []
    for cand in leaders(source):
        ind = inventory[cand["indicator"]]
        for params in param_grid(ind):
            for lookback in LOOKBACKS:
                for policy in cand["policies"]:
                    plan.append((cand, ind, params, lookback, policy))
    return plan


def report(path: str) -> None:
    """Ridge scores per signal, on BOTH surfaces."""
    with open(path, encoding="utf-8") as fh:
        rows = [json.loads(line) for line in fh if line.strip()]
    frame = pd.DataFrame([r for r in rows if "error" not in r])
    if frame.empty:
        return
    for keys, group in frame.groupby(["instrument", "indicator", "output", "variant", "policy"]):
        symbol = keys[0]
        print(f"\n=== {' '.join(map(str, keys))}  ({len(group)} settings) ===")
        for metric, metric_bar in (
            ("ret_dd", INSTRUMENTS[symbol]["bh_ret_dd"]),
            ("cagr", RETURN_FLOOR[symbol]),
        ):
            scored = ridge_scores(group, metric)
            best = scored.loc[scored[metric].idxmax()]
            verdict = "RIDGE" if abs(best["ridge"]) < abs(best[metric]) * 0.25 else "spike"
            print(
                f"  {metric:<7} best {best[metric]:8.3f} at {best['params']} "
                f"lb={best['lookback']} | neighbours {best['neighbour_mean']:8.3f} "
                f"({verdict}) | {int((scored[metric] >= metric_bar).sum())}/{len(scored)} "
                f"clear {metric_bar}"
            )


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--config", default="config/paper_aggressive.yaml")
    p.add_argument("--source", default="output/stage1_grid.jsonl")
    p.add_argument("--out", default="output/stage2_grid.jsonl")
    p.add_argument("--target", type=float, default=0.04)
    p.add_argument("--report-only", action="store_true")
    p.add_argument("--no-resume", dest="resume", action="store_false")
    p.set_defaults(resume=True)
    args = p.parse_args(argv)

    if args.report_only:
        report(args.out)
        return 0

    journal = Journal(args.out)
    done = journal.done_ids() if args.resume else set()
    cfg = BacktestConfig.from_yaml(args.config)
    plan = build_plan(args.source)
    total = len(plan)
    print(f"[grid2] {total} engine runs (~23s each, ~{total * 23 / 3600:.1f}h)")
    if done:
        print(f"[grid2] resuming: {len(done)} already complete")

    frames: dict[str, pd.DataFrame] = {}
    started = time.time()
    ran = failed = 0

    for i, (cand, ind, params, lookback, policy) in enumerate(plan, 1):
        symbol = cand["instrument"]
        cid = config_id(
            symbol,
            ind.name,
            cand["output"],
            cand["variant"],
            json.dumps(params, sort_keys=True),
            str(lookback),
            policy,
            "grid2",
        )
        if cid in done:
            continue
        if symbol not in frames:
            frames[symbol] = pd.read_csv(
                INSTRUMENTS[symbol]["path"], parse_dates=["timestamp"]
            ).set_index("timestamp")
        try:
            regime, flips, in_market = daily_regime(
                symbol, ind, cand["output"], cand["variant"], params, lookback
            )
            m = score(regime, policy == "liquidate", cfg, frames[symbol], args.target)
            row = {
                "config_id": cid,
                "instrument": symbol,
                "indicator": ind.name,
                "output": cand["output"],
                "variant": cand["variant"],
                "policy": policy,
                "params": json.dumps(params, sort_keys=True),
                "lookback": lookback,
                "flips": flips,
                "in_market_pct": in_market,
                "stage1_ret_dd": cand["stage1_ret_dd"],
                **m,
            }
            journal.write(row)
            ran += 1
            rate = (time.time() - started) / max(ran, 1)
            print(
                f"[{i:>4}/{total}] {symbol:<5} {ind.name:<10} {cand['variant']:<6} "
                f"{policy:<9} {params!s:<38} lb={lookback:<4} "
                f"CAGR {m['cagr']:7.2f}%  DD {m['max_dd']:6.2f}%  "
                f"ret/dd {m['ret_dd']:6.3f}  ({rate:.0f}s, eta {rate * (total - i) / 3600:.1f}h)",
                flush=True,
            )
        except Exception as exc:
            failed += 1
            journal.write({"config_id": cid, "error": f"{type(exc).__name__}: {exc}"[:200]})
            print(f"[{i:>4}/{total}] FAILED {type(exc).__name__}: {exc}"[:160], flush=True)

    print(f"\n[grid2] {ran} run, {failed} failed, {(time.time() - started) / 60:.1f} min")
    report(args.out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
