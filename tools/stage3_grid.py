#!/usr/bin/env python
"""Stage 3, redone: is the NATR result about the SIGNAL or about the POLICY?

--------------------------------------------------------------------
THE QUESTION NOTHING SO FAR HAS ASKED

Stage 2-grid found TQQQ `NATR below` under liquidate-on-flip clearing
buy-and-hold's return/drawdown at 18 of 18 parameter settings, peaking at
38.64% CAGR against a 26.68% drawdown where buy-and-hold takes 81.68%.

Every stage that produced that number would have produced it just the
same if NATR carried no information at all. The signal is in the market
54% of the time and flips 138 times; liquidate-on-flip then forces sales
that `enforce_no_loss` has already shaped, and periodically flattens a
book on a leveraged ETF. That is a POLICY effect, and it would be scored
identically to a SIGNAL effect by Stages 1, 2 and 3 alike.

So the first thing here is a control, and it is the whole point:

  RANDOM REGIMES MATCHED ON IN-MARKET FRACTION AND FLIP COUNT.

A two-state Markov chain reproduces both moments exactly in expectation.
For P(bull->bear) = p and P(bear->bull) = q, the stationary in-market
fraction is q/(p+q) and the per-step flip probability is 2*f*p, so a
target (f, flips/N) inverts to p = flips / (2*f*N) and q = p*f/(1-f).

If a matched random regime reaches ret/dd near 1.4, the finding is about
liquidate-on-flip and NATR is decoration. If the random distribution sits
well below it, the indicator is carrying information. Either answer is
worth more than another parameter sweep.

--------------------------------------------------------------------
AND THREE ROBUSTNESS CHECKS THE CANDIDATE HAS NOT FACED

  halves      first and second chronological half, separately. The
              existing sweep had a `halves_agree` column; the engine
              stages never carried one.
  ex-COVID    March 2020 removed. This project has already found one
              RSP result that reversed entirely when COVID came out, so
              a drawdown claim that survives only because of one month
              is a known failure mode here, not a hypothetical.
  lb < 100    Stage 2-grid's optimum sits on the SMALLEST lookback it
              tested, so the true optimum may be outside the grid. A
              boundary optimum is weaker evidence than an interior one,
              and extending the axis is how that gets settled.
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
from tools.indicator_sweep import INSTRUMENTS, Journal, config_id
from tools.stage2_grid import daily_regime, score

SYMBOL = "TQQQ"
INDICATOR = "NATR"
OUTPUT = "real"
VARIANT = "below"

# The Stage 2-grid argmax. Reported alongside a mid-surface cell, since
# the argmax is a spike on a robust plateau and the plateau is the part
# worth deploying.
BEST = {"timeperiod": 10}
BEST_LOOKBACK = 100
MID = {"timeperiod": 21}
MID_LOOKBACK = 250

COVID = ("2020-02-01", "2020-05-01")


def segments(frame: pd.DataFrame) -> dict[str, pd.DataFrame]:
    """Full sample, both chronological halves, and COVID removed."""
    mid = frame.index[len(frame) // 2]
    covid = (frame.index >= COVID[0]) & (frame.index < COVID[1])
    return {
        "full": frame,
        "first_half": frame[frame.index < mid],
        "second_half": frame[frame.index >= mid],
        "ex_covid": frame[~covid],
    }


def matched_random_regime(dates, in_market: float, flips: int, seed: int) -> dict:
    """A random bull/bear series matching in-market fraction and flips.

    Two-state Markov chain, so the run-length structure is geometric
    rather than the independent coin flips a naive shuffle would give.
    That matters: a Bernoulli series with the right MEAN has wildly the
    wrong flip count, and flip count is exactly what liquidate-on-flip
    responds to. Both moments have to be matched or the control does not
    control for anything.
    """
    n = len(dates)
    f = min(max(in_market, 0.01), 0.99)
    p = min(flips / (2 * f * n), 0.99)
    q = min(p * f / (1 - f), 0.99)
    rng = np.random.default_rng(seed)
    draws = rng.random(n)
    state = rng.random() < f
    out = {}
    for i, date in enumerate(dates):
        out[date] = bool(state)
        state = (draws[i] >= p) if state else (draws[i] < q)
    return out


def realised(regime: dict) -> tuple[float, int]:
    """What a regime ACTUALLY delivered, not what it was asked for.

    A Markov chain matches its targets in expectation; one draw does not.
    Recording the realised moments is what makes the control auditable --
    a draw that came out at 30% in-market is not a match for a 54% signal
    however it was parameterised.
    """
    values = np.array(list(regime.values()), dtype=float)
    return round(float(values.mean()) * 100, 2), int((np.diff(values) != 0).sum())


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--config", default="config/paper_aggressive.yaml")
    p.add_argument("--out", default="output/stage3_grid.jsonl")
    p.add_argument("--target", type=float, default=0.04)
    p.add_argument("--seeds", type=int, default=30)
    p.add_argument("--no-resume", dest="resume", action="store_false")
    p.set_defaults(resume=True)
    args = p.parse_args(argv)

    journal = Journal(args.out)
    done = journal.done_ids() if args.resume else set()
    cfg = BacktestConfig.from_yaml(args.config)
    ind = {i.name: i for i in available()}[INDICATOR]
    frame = pd.read_csv(INSTRUMENTS[SYMBOL]["path"], parse_dates=["timestamp"]).set_index(
        "timestamp"
    )
    parts = segments(frame)

    real, flips, in_market = daily_regime(SYMBOL, ind, OUTPUT, VARIANT, BEST, BEST_LOOKBACK)
    mid_regime, _, _ = daily_regime(SYMBOL, ind, OUTPUT, VARIANT, MID, MID_LOOKBACK)
    dates = list(real)
    print(f"[grid3] NATR below {BEST} lb={BEST_LOOKBACK}: {in_market}% in market, {flips} flips")

    plan: list[tuple] = []
    # The candidate and its mid-surface neighbour, over every segment.
    for label, params, lookback, regime in (
        ("best", BEST, BEST_LOOKBACK, real),
        ("mid_surface", MID, MID_LOOKBACK, mid_regime),
    ):
        for seg in parts:
            for policy in ("liquidate", "hold"):
                plan.append((f"natr_{label}", seg, policy, regime, params, lookback))
    # Lookbacks below the swept range, full sample only.
    for lookback in (25, 50, 75):
        for period in (7, 10, 14):
            reg, _, _ = daily_regime(SYMBOL, ind, OUTPUT, VARIANT, {"timeperiod": period}, lookback)
            plan.append(
                ("natr_short_lb", "full", "liquidate", reg, {"timeperiod": period}, lookback)
            )
    # The control.
    for seed in range(args.seeds):
        reg = matched_random_regime(dates, in_market / 100, flips, seed)
        for policy in ("liquidate", "hold"):
            plan.append((f"control_seed{seed}", "full", policy, reg, {}, BEST_LOOKBACK))

    total = len(plan)
    print(f"[grid3] {total} engine runs (~23s each, ~{total * 23 / 3600:.1f}h)")

    started = time.time()
    ran = failed = 0
    for i, (kind, seg, policy, regime, params, lookback) in enumerate(plan, 1):
        cid = config_id(
            SYMBOL, kind, seg, policy, json.dumps(params, sort_keys=True), str(lookback), "grid3"
        )
        if cid in done:
            continue
        try:
            got_market, got_flips = realised(regime)
            m = score(regime, policy == "liquidate", cfg, parts[seg], args.target)
            row = {
                "config_id": cid,
                "kind": kind,
                "is_control": kind.startswith("control"),
                "segment": seg,
                "policy": policy,
                "params": json.dumps(params, sort_keys=True),
                "lookback": lookback,
                "in_market_pct": got_market,
                "flips": got_flips,
                **m,
            }
            journal.write(row)
            ran += 1
            rate = (time.time() - started) / max(ran, 1)
            print(
                f"[{i:>4}/{total}] {kind:<16} {seg:<12} {policy:<9} "
                f"lb={lookback:<4} mkt {got_market:5.1f}% flips {got_flips:>4}  "
                f"CAGR {m['cagr']:7.2f}%  DD {m['max_dd']:6.2f}%  ret/dd {m['ret_dd']:6.3f}  "
                f"(eta {rate * (total - i) / 3600:.1f}h)",
                flush=True,
            )
        except Exception as exc:
            failed += 1
            journal.write({"config_id": cid, "error": f"{type(exc).__name__}: {exc}"[:200]})
            print(f"[{i:>4}/{total}] FAILED {type(exc).__name__}: {exc}"[:160], flush=True)

    print(f"\n[grid3] {ran} run, {failed} failed, {(time.time() - started) / 60:.1f} min")
    return 0


if __name__ == "__main__":
    sys.exit(main())
