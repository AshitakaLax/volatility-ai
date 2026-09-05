#!/usr/bin/env python
"""Stage 4: does the NATR effect track LEVERAGE? A prediction, then a test.

--------------------------------------------------------------------
THE MECHANISM, AND WHY IT IS FALSIFIABLE

Stage 3-grid established that TQQQ `NATR below` under liquidate-on-flip
is not the exit policy in disguise -- a matched random regime scores
-0.017 against the signal's 1.448, twelve standard deviations away, and
the policy applied to noise is actively destructive. So the signal
carries information. What it does NOT establish is WHY, and a
correlation across 18 cells with no mechanism is still a data-mining
survivor until it predicts something it was not fitted to.

There is an obvious candidate mechanism, and it is arithmetic rather
than a market opinion. A daily-rebalanced L-times fund tracking an index
with variance sigma^2 loses approximately

    (L^2 - L) / 2 * sigma^2

per unit time relative to L times the index return. For L = 3 that is
3*sigma^2. For L = 1 it is EXACTLY ZERO -- an unleveraged fund has no
volatility drag at all.

So the mechanism makes a sharp prediction: avoiding high-volatility
regimes should pay a 3x fund handsomely and an unleveraged fund almost
nothing.

--------------------------------------------------------------------
THE PREDICTION, RECORDED BEFORE THE RUN

QQQ is the controlled comparison. It tracks the SAME index as TQQQ, so
leverage is the only variable that changes -- unlike SOXL or RSP, which
change the underlying as well.

  TQQQ  (3x Nasdaq-100)   18 of 18 settings clear its bar   [MEASURED]
  RSP   (1x equal-weight)  7 of 18                          [MEASURED]
  QQQ   (1x Nasdaq-100)   PREDICTED: near RSP, not near TQQQ, and its
                          ratio to buy-and-hold near 1.0 if drag is the
                          whole story.

If QQQ instead clears 15+ of 18, the drag mechanism is WRONG. The effect
would then be something that survives without leverage, which is a
different and larger claim needing a different explanation -- and one
this project should not assume just because it is the flattering
outcome.

--------------------------------------------------------------------
THE CONFOUND THIS HAS TO CONTROL FOR, OR THE NULL IS UNINTERPRETABLE

The grid parameters -- a 4% profit target on a 0.075% bull step -- were
tuned on TQQQ, whose daily volatility is roughly three times QQQ's. Run
unchanged on QQQ they may simply produce too few round trips to measure
anything, and a null result would then be evidence about the PARAMETERS,
not about leverage.

So QQQ runs twice: once at TQQQ's target, and once at a target scaled by
the ratio of realised daily volatilities, MEASURED from the two price
series rather than assumed to be 3. Only if both come back weak is the
prediction confirmed.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
warnings.filterwarnings("ignore")

from src.config import BacktestConfig
from src.indicator_library import available
from tools.indicator_sweep import Journal, config_id, param_grid
from tools.stage2_grid import LOOKBACKS, daily_regime, score
from tools.stage3_grid import matched_random_regime, realised

INDICATOR = "NATR"
OUTPUT = "real"
VARIANT = "below"
BEST = {"timeperiod": 10}
BEST_LOOKBACK = 100

# Measured, not assumed. bh_* are filled in from the price series so a
# new instrument needs no hand-entered benchmark that could go stale.
CANDIDATES = {
    "QQQ": "data/QQQ_1Min_sip_all_2016-01-01_2026-09-05.csv",
    "SOXL": "data/SOXL_1Min_sip_all_rth_2016-01-01_2026-09-03.csv",
}
REFERENCE = "data/TQQQ_1Min_sip_all_2016-01-01_2026-08-21.csv"


def buy_and_hold(frame: pd.DataFrame) -> dict:
    close = frame["close"]
    years = (frame.index[-1] - frame.index[0]).days / 365.25
    cagr = ((close.iloc[-1] / close.iloc[0]) ** (1 / years) - 1) * 100
    dd = abs((close / close.cummax() - 1).min()) * 100
    return {
        "bh_cagr": round(float(cagr), 3),
        "bh_dd": round(float(dd), 3),
        "bh_ret_dd": round(float(cagr / dd), 4),
    }


def daily_vol(frame: pd.DataFrame) -> float:
    """Annualised daily volatility, from session closes."""
    daily = frame["close"].resample("1D").last().dropna()
    return float(daily.pct_change().dropna().std() * np.sqrt(252))


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--config", default="config/paper_aggressive.yaml")
    p.add_argument("--out", default="output/stage4_leverage.jsonl")
    p.add_argument("--target", type=float, default=0.04)
    p.add_argument("--seeds", type=int, default=30)
    p.add_argument("--instruments", nargs="+", default=list(CANDIDATES))
    p.add_argument("--no-resume", dest="resume", action="store_false")
    p.set_defaults(resume=True)
    args = p.parse_args(argv)

    journal = Journal(args.out)
    done = journal.done_ids() if args.resume else set()
    cfg = BacktestConfig.from_yaml(args.config)
    ind = {i.name: i for i in available()}[INDICATOR]

    print("PREDICTION, recorded before the run: an unleveraged fund has ZERO")
    print("volatility drag, so QQQ should land near RSP's 7 of 18, not near")
    print("TQQQ's 18 of 18. 15+ of 18 on QQQ falsifies the drag mechanism.\n")

    ref = pd.read_csv(REFERENCE, parse_dates=["timestamp"]).set_index("timestamp")
    ref_vol = daily_vol(ref)
    print(f"[grid4] TQQQ annualised daily vol {ref_vol:.3f}, target {args.target}")

    plan: list[tuple] = []
    frames: dict[str, pd.DataFrame] = {}
    benchmarks: dict[str, dict] = {}

    for symbol in args.instruments:
        path = CANDIDATES[symbol]
        if not Path(path).exists():
            print(f"[grid4] SKIP {symbol}: {path} not found")
            continue
        frame = pd.read_csv(path, parse_dates=["timestamp"]).set_index("timestamp")
        frames[symbol] = frame
        benchmarks[symbol] = buy_and_hold(frame)
        vol = daily_vol(frame)
        scaled = round(args.target * vol / ref_vol, 5)
        print(
            f"[grid4] {symbol}: vol {vol:.3f} ({vol / ref_vol:.2f}x TQQQ), "
            f"scaled target {scaled}, buy-and-hold {benchmarks[symbol]}"
        )
        # The full 18-cell surface at TQQQ's target, so the "clears the
        # bar" count is comparable to Stage 2-grid's cell for cell.
        for params in param_grid(ind):
            for lookback in LOOKBACKS:
                plan.append((symbol, "surface", params, lookback, args.target, None))
        # The same surface at the volatility-scaled target, so a null
        # cannot be blamed on parameters tuned for a 3x fund.
        for params in param_grid(ind):
            for lookback in LOOKBACKS:
                plan.append((symbol, "surface_scaled", params, lookback, scaled, None))
        # And the matched-random control at the best cell, on each
        # target, so each instrument carries its own null rather than
        # borrowing TQQQ's.
        regime, flips, in_market = daily_regime(
            symbol, ind, OUTPUT, VARIANT, BEST, BEST_LOOKBACK, path=path
        )
        for seed in range(args.seeds):
            control = matched_random_regime(list(regime), in_market / 100, flips, seed)
            plan.append((symbol, f"control{seed}", {}, BEST_LOOKBACK, args.target, control))

    total = len(plan)
    print(f"\n[grid4] {total} engine runs (~23s each, ~{total * 23 / 3600:.1f}h)")

    started = time.time()
    ran = failed = 0
    for i, (symbol, kind, params, lookback, target, control) in enumerate(plan, 1):
        cid = config_id(
            symbol,
            kind,
            json.dumps(params, sort_keys=True),
            str(lookback),
            str(target),
            "grid4",
        )
        if cid in done:
            continue
        try:
            if control is None:
                regime, flips, in_market = daily_regime(
                    symbol, ind, OUTPUT, VARIANT, params, lookback, path=CANDIDATES[symbol]
                )
            else:
                regime = control
                in_market, flips = realised(control)
            m = score(regime, True, cfg, frames[symbol], target)
            bh = benchmarks[symbol]
            row = {
                "config_id": cid,
                "instrument": symbol,
                "kind": kind,
                "is_control": kind.startswith("control"),
                "params": json.dumps(params, sort_keys=True),
                "lookback": lookback,
                "target": target,
                "in_market_pct": in_market,
                "flips": flips,
                **bh,
                **m,
                "ratio_to_bh": round(m["ret_dd"] / bh["bh_ret_dd"], 3) if bh["bh_ret_dd"] else 0.0,
            }
            journal.write(row)
            ran += 1
            rate = (time.time() - started) / max(ran, 1)
            print(
                f"[{i:>4}/{total}] {symbol:<5} {kind:<16} {params!s:<22} lb={lookback:<4} "
                f"tgt={target:<8} CAGR {m['cagr']:7.2f}% (bh {bh['bh_cagr']:6.2f}) "
                f"ret/dd {m['ret_dd']:6.3f} (bh {bh['bh_ret_dd']:.3f}) "
                f"{row['ratio_to_bh']:5.2f}x  (eta {rate * (total - i) / 3600:.1f}h)",
                flush=True,
            )
        except Exception as exc:
            failed += 1
            journal.write({"config_id": cid, "error": f"{type(exc).__name__}: {exc}"[:200]})
            print(f"[{i:>4}/{total}] FAILED {type(exc).__name__}: {exc}"[:160], flush=True)

    print(f"\n[grid4] {ran} run, {failed} failed, {(time.time() - started) / 60:.1f} min")
    return 0


if __name__ == "__main__":
    sys.exit(main())
