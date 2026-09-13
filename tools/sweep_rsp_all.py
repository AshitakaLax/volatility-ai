#!/usr/bin/env python
"""
Brute-force every strategy and parameter against RSP, as a series of
web-UI runs.

--------------------------------------------------------------------
WHY THIS SUBMITS TO THE SERVER INSTEAD OF CALLING THE ENGINE

Every other probe in tools/ imports run_backtest and calls it in
process. That is the right shape for a question you answer once and
paste into a commit message, and the wrong shape here: an in-process
call never touches server/jobs.py or server/history.py, so it leaves no
run_id, no progress, and nothing in Run History. A sweep that takes
hours and cannot be watched is a sweep nobody watches.

So this posts RunRequests to /api/backtest/runs and prints the ids. The
server's queue is a single-worker FIFO, which is exactly what is wanted:
submit the whole series at once, let it drain in order, and watch it in
the browser. Killing this script does not kill the sweeps -- they are
the server's jobs now, not this process's.

--------------------------------------------------------------------
THE TWO CONSTRAINTS THAT DRIVE EVERY SIZE DECISION HERE

  intrabar fills only.  A level TOUCHED inside the bar fills, at that
      level. This is the honest model for a resting limit order and the
      only one this sweep uses -- no "close" runs, not even for the
      cheap strategies.

  the full file, always.  No start/end, and limit=None so RunRequest's
      200,000-bar default cap does NOT apply. That is 1,044,810 bars,
      2016-01-04 to 2026-08-28.

Cost per configuration, measured on this machine at n_jobs=1, one
configuration each:

    rsi                  29.3s      bayesian_dual_scale   31.9s
    fixed                30.3s      hf_local_reference    34.7s
    bell_curve           30.3s      ml_regime_rsp         52.5s
                                    ml_reachability_rsp  623.1s

Five of the seven sit within 20% of each other because the per-bar loop
dominates, not the fill count -- hf_local_reference does 4,116 fills
against fixed's 22 and costs 14% more.

ml_reachability_rsp IS THE OUTLIER AND IT IS NOT A ROUNDING ERROR: 623s
is twenty times the median, so its 768 configurations cost more wall
time than bell_curve's 8,640. Estimating the whole plan off one shared
constant understated it by roughly two days, which is why COST_SECONDS
below is per strategy rather than a single number. If that strategy's
share is unacceptable, drop it with --only rather than trimming
everything else.

--------------------------------------------------------------------
WHY A SERIES RATHER THAN ONE ENORMOUS RUN

server/backtest.py caps one submission at MAX_SWEEP_COMBINATIONS (2000)
because build_config expands the whole combination space synchronously
in the request handler. Rather than raise that ceiling, a strategy whose
full grid exceeds it is SPLIT along one axis into consecutive runs, each
under the cap by RECURSIVE BISECTION of its widest axis. The whole space
still gets enumerated; it arrives as several rows in Run History instead
of one, each a coherent slice ("per_lot_pct = 0.0002 and 0.0005,
everything else") rather than an arbitrary cut.

Bisecting repeatedly, rather than splitting one axis once, is load
bearing: halving only the widest axis leaves chunks still over the cap
whenever the REST of the space exceeds it alone. The first version did
that and produced chunks 5x too large, which the server would have
rejected one at a time.

--------------------------------------------------------------------
WHICH STRATEGIES, AND WHY NOT THE OTHERS

STRATEGIES (src/trading/strategy_registry.py) lists sixteen ids, but
nine of them are MLRegimeScaledSizing / MLReachabilitySizing bound to a
specific ticker's trained model -- ml_regime_tqqq loads
data/ml/models/TQQQ_regime_crash.txt. Pointing those at RSP bars would
score RSP with a model trained on a different instrument and report the
result as if it meant something. Only the two RSP-specific ones are
included, and both models were confirmed present.

Read the numbers against RSP buy-and-hold, not against each other:
12.46% CAGR at a -39.11% max drawdown over this window. The RSP work
already recorded in tools/probe_rsp_alternatives.py's own output found
nothing that beat holding, and the ordering there was monotone -- the
less a configuration harvested, the better it did. This sweep is the
exhaustive version of that question, and the prior is that it confirms
it.
"""

from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.request
from typing import Any

# ---------------------------------------------------------------
# The window and fill model. Not parameters -- the point of the run.
# ---------------------------------------------------------------
TICKER = "RSP"
FILL_MODEL = "intrabar"
LIMIT = None  # the whole file; RunRequest's default would cap at 200k
BARS = 1_044_810  # for the estimate only
WORKERS = 11  # server/backtest.py DEFAULT_JOBS on a 12-core box

# Seconds per configuration, per strategy, measured (see docstring).
# Per strategy rather than one constant because the spread is 21x.
COST_SECONDS: dict[str, float] = {
    "fixed": 30.3,
    "hf_local_reference": 34.7,
    "rsi": 29.3,
    "bell_curve": 30.3,
    "bayesian_dual_scale": 31.9,
    "ml_reachability_rsp": 623.1,
    "ml_regime_rsp": 52.5,
}
DEFAULT_COST = 35.0

MAX_COMBOS = 2000  # server/backtest.py MAX_SWEEP_COMBINATIONS

# The two grid axes every strategy shares. RunRequest caps each at 12.
GRID_STEPS = [0.0025, 0.005, 0.0075, 0.01, 0.015, 0.02]
PROFIT_TARGETS = [0.005, 0.01, 0.02, 0.03]

# ---------------------------------------------------------------
# The parameter space, per strategy.
#
# Values are centred on each strategy's committed default (the
# STRATEGY_DEFAULTS entry, itself lifted from a config this project
# actually selected) and widened outward, rather than invented around a
# round number. Where a default is the edge of the sensible range the
# span is one-sided.
# ---------------------------------------------------------------
SPACES: dict[str, dict[str, list[Any]]] = {
    # allocation_pct is the whole strategy. Swept wide because it is the
    # only thing there is to sweep, and because the RSP question is
    # specifically whether LESS harvesting does better.
    "fixed": {
        "allocation_pct": [0.01, 0.02, 0.03, 0.05, 0.08, 0.12, 0.20, 0.30],
    },
    # The champion strategy elsewhere, and the one with real surface.
    # lookback_days is the trigger reference window; vol_scale_exponent
    # negative means size DOWN when short-horizon vol runs hot.
    # trail_pct is excluded: it is evaluated per open lot per bar and
    # measured 31x slower on a book this size, for an effect that came
    # to 16 fills in 35,430 on the comparable XBI test.
    "hf_local_reference": {
        "bars_per_day": [387],
        "per_lot_pct": [0.0002, 0.0005, 0.001, 0.002],
        "lookback_days": [0.02, 0.1, 0.5, 1.0, 3.0],
        "vol_scale_exponent": [0.0, -0.75, -1.5],
        "vol_fast_days": [0.25, 0.5],
        "vol_slow_days": [10.0, 20.0],
        "volume_scale_exponent": [0.0, -1.0],
        "dd_throttle_start": [None, 0.15],
    },
    "rsi": {
        "max_trade_pct": [0.02, 0.05, 0.08, 0.15],
        "period": [7, 14, 21, 30],
        "oversold_threshold": [20.0, 30.0, 40.0],
        "baseline_multiplier": [0.0, 0.1, 0.25],
        "aggression_factor": [0.5, 0.9],
        "exponent": [1.0, 2.0],
    },
    "bell_curve": {
        "max_trade_pct": [0.02, 0.05, 0.08, 0.15],
        "lookback_days": [5, 10, 20, 40, 60],
        "bars_per_day": [387],
        "mu": [0.1, 0.2, 0.3],
        "sigma": [0.05, 0.1, 0.2],
        "inverse_scale_kappa": [0.0, 1.0],
    },
    # target_return is DELIBERATELY ABSENT, and cannot be added: this
    # strategy estimates the probability of reaching exactly one target,
    # so the server aligns target_return to each combination's own grid
    # profit target and rejects the request outright if it is also swept
    # ("cannot be swept independently" -- /api/backtest/validate catches
    # it). PROFIT_TARGETS above is therefore already sweeping it, four
    # values deep; listing it here would be the same axis twice and a
    # 400.
    "bayesian_dual_scale": {
        "max_trade_pct": [0.02, 0.05, 0.08],
        "horizon_days": [1.0, 3.0],
        "bars_per_day": [387],
        "fast_half_life_days": [2.0, 5.0, 10.0],
        "slow_half_life_days": [60.0, 120.0],
        "confidence_k": [1.0, 2.0, 3.0],
        "vol_scale_exponent": [0.0, -1.0],
        "reference_probability": [0.4, 0.5, 0.6],
    },
    # RSP-specific trained models, both confirmed present in
    # data/ml/models/. confidence_floor is the only real knob.
    "ml_reachability_rsp": {
        "max_trade_pct": [0.02, 0.05, 0.08, 0.15],
        "ticker": ["RSP"],
        "confidence_floor": [0.0, 0.25, 0.5, 0.75],
        "inverse_scale_kappa": [0.0, 1.0],
    },
    # Thresholds read off RSP_regime_crash.json's OWN score_quantiles
    # (p50=0.229, p75=0.347, p90=0.418, p95=0.453, p99=0.520), because a
    # calibrated classifier on a low base rate never emits a high
    # number and _check_threshold_is_reachable rejects anything above
    # p99. Every exit candidate sits below every enter candidate.
    "ml_regime_rsp": {
        "max_trade_pct": [0.02, 0.05, 0.08],
        "ticker": ["RSP"],
        "crash_step_multiplier": [1.0, 2.0, 4.0, 6.0],
        "regime_enter_threshold": [0.347, 0.418, 0.453],
        "regime_exit_threshold": [0.229, 0.30],
        "regime_floor": [0.10, 0.25, 0.50],
        "drawdown_response": [0.0, -1.5, 1.5],
        "vol_reference": [0.15, 0.172, 0.20],
    },
}


# STRATEGIES THAT REFUSE MORE THAN ONE PROFIT TARGET PER SUBMISSION.
#
# BayesianDualScaleSizing estimates the probability of reaching ONE
# target_return, and the server aligns target_return to the grid's
# profit target -- so a submission carrying four of them is ambiguous
# and is rejected outright ("cannot sweep 4 profit targets at once").
# The axis is not dropped; it becomes one run per target instead, which
# is what --dry-run's [1/4]-style labels show.
ONE_TARGET_PER_RUN = {"bayesian_dual_scale"}


def targets_for(strategy: str) -> list[float]:
    """The profit targets one submission of `strategy` may carry."""
    return [PROFIT_TARGETS[0]] if strategy in ONE_TARGET_PER_RUN else PROFIT_TARGETS


def combos(space: dict[str, list[Any]]) -> int:
    n = 1
    for v in space.values():
        n *= len(v)
    return n


def split_axis(space: dict[str, list[Any]]) -> str | None:
    """The parameter to chunk along: the one with the most values.

    Picked by width rather than by name so the chunks stay balanced and
    each remains a readable slice of the space.
    """
    multi = {k: v for k, v in space.items() if len(v) > 1}
    return max(multi, key=lambda k: len(multi[k])) if multi else None


def plan(strategy: str, space: dict[str, list[Any]]) -> list[dict[str, list[Any]]]:
    """Split one strategy's space into chunks that each fit the cap.

    RECURSIVE BISECTION, not a single split, and the difference matters:
    halving only the widest axis cannot get under the cap when the rest
    of the space is already over it on its own -- the first version of
    this did exactly that and emitted chunks still 5x too large, which
    the server would have rejected one by one.

    Bisecting repeatedly works because a cartesian product cut along an
    axis yields two smaller cartesian products, so every chunk is still
    something the server can expand normally. Halving the WIDEST axis
    each time keeps the tree balanced and the chunks readable.
    """
    grid_axes = len(GRID_STEPS) * len(targets_for(strategy))

    def divide(sub: dict[str, list[Any]]) -> list[dict[str, list[Any]]]:
        if combos(sub) * grid_axes <= MAX_COMBOS:
            return [sub]
        axis = split_axis(sub)
        if axis is None:
            # Every axis is a single value and it is STILL over cap, so
            # the grid axes alone exceed it. Nothing left to split.
            return [sub]
        values = sub[axis]
        mid = len(values) // 2
        left, right = dict(sub), dict(sub)
        left[axis], right[axis] = values[:mid], values[mid:]
        return divide(left) + divide(right)

    return divide(space)


def request_for(
    strategy: str,
    space: dict[str, list[Any]],
    label: str,
    targets: list[float] | None = None,
) -> dict[str, Any]:
    return {
        "name": label,
        "tickers": [TICKER],
        "grid_steps": GRID_STEPS,
        "profit_targets": targets if targets is not None else targets_for(strategy),
        "sizing_model": strategy,
        "strategy_params": space,
        "fill_model": FILL_MODEL,
        "limit": LIMIT,
        # No start/end: the whole file.
        "rank_by": "Capital Velocity Index",
        "search_direction": "maximize",
    }


def submit(api: str, body: dict[str, Any]) -> dict[str, Any]:
    req = urllib.request.Request(
        f"{api}/api/backtest/runs",
        data=json.dumps(body).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        return json.loads(resp.read())


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    ap.add_argument("--api", default="http://127.0.0.1:8000")
    ap.add_argument("--only", nargs="+", metavar="STRATEGY", help="Submit only these strategy ids.")
    ap.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the plan and the time estimate. Submits nothing.",
    )
    args = ap.parse_args(argv)

    selected = args.only or list(SPACES)
    unknown = [s for s in selected if s not in SPACES]
    if unknown:
        print(f"Unknown strategy id(s): {unknown}. Known: {list(SPACES)}", file=sys.stderr)
        return 2

    batches: list[tuple[str, str, dict[str, list[Any]], list[float], int]] = []
    for strategy in selected:
        space = SPACES[strategy]
        chunks = plan(strategy, space)
        # A strategy in ONE_TARGET_PER_RUN fans out over the targets
        # instead of carrying them in one submission; every other one
        # gets the whole list at once.
        target_groups = (
            [[t] for t in PROFIT_TARGETS] if strategy in ONE_TARGET_PER_RUN else [PROFIT_TARGETS]
        )
        total_runs = len(chunks) * len(target_groups)
        i = 0
        for targets in target_groups:
            for chunk in chunks:
                i += 1
                n = combos(chunk) * len(GRID_STEPS) * len(targets)
                suffix = f" [{i}/{total_runs}]" if total_runs > 1 else ""
                tag = f" pt={targets[0]:.3g}" if strategy in ONE_TARGET_PER_RUN else ""
                label = f"RSP brute force -- {strategy}{suffix}{tag} (intrabar, full history)"
                batches.append((strategy, label, chunk, targets, n))

    total_cfgs = sum(b[-1] for b in batches)
    est_h = sum(b[-1] * COST_SECONDS.get(b[0], DEFAULT_COST) for b in batches) / WORKERS / 3600

    print(f"{TICKER}: {BARS:,} bars, {FILL_MODEL} fills, full history")
    print(
        f"{len(batches)} runs, {total_cfgs:,} configurations, "
        f"~{est_h:.1f}h ({est_h / 24:.1f} days) across {WORKERS} workers\n"
    )
    for strategy, label, _chunk, _targets, n in batches:
        hrs = n * COST_SECONDS.get(strategy, DEFAULT_COST) / WORKERS / 3600
        over = "  OVER CAP" if n > MAX_COMBOS else ""
        print(f"  {n:>5,} cfg  ~{hrs:>5.1f}h  {label}{over}")

    if args.dry_run:
        print("\n--dry-run: nothing submitted.")
        return 0

    print()
    ok = 0
    for strategy, label, chunk, targets, n in batches:
        try:
            job = submit(args.api, request_for(strategy, chunk, label, targets))
            print(f"  queued {job['run_id']}  {n:>5,} cfg  {label}", flush=True)
            ok += 1
        except urllib.error.HTTPError as exc:
            print(f"  REJECTED {label}\n    {exc.code}: {exc.read().decode()[:300]}")
        except urllib.error.URLError as exc:
            print(f"  UNREACHABLE {args.api}: {exc.reason}")
            print("  Start it with: uvicorn server.app:app --host 127.0.0.1 --port 8000")
            return 1

    print(
        f"\n{ok}/{len(batches)} queued. The server owns them now -- closing this "
        f"process does not stop them."
    )
    print(f"Watch: {args.api}  (Backtesting -> Run History)")
    return 0 if ok == len(batches) else 1


if __name__ == "__main__":
    raise SystemExit(main())
