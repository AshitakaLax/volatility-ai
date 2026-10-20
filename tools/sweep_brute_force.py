#!/usr/bin/env python
"""
Brute-force every strategy that can trade a fund, as a series of web-UI runs
on this machine.

    python tools/sweep_brute_force.py --dry-run            # the plan and its cost
    python tools/sweep_brute_force.py                      # queue it (RSP, URSP_SIM)
    python tools/sweep_brute_force.py --fund RSP --only ultimate_rsp fixed

The generalisation of tools/sweep_rsp_all.py (one fund, the seven strategies
that existed in September), and it keeps that tool's two rules: INTRABAR fills
only, and the WHOLE history. RSP's parameter spaces are that tool's, measured
choices centred on each strategy's committed defaults.

--------------------------------------------------------------------
WHAT THE SERVER DOES WITH IT

Each submission is one strategy (or one slice of one: see SPACES) on one fund,
as a RunRequest. The server splits anything over its per-run ceiling into a
batch of runs itself (server/backtest.py bisect_request), runs them on its
durable queue, and:

  local_only   keeps every run on this server's own worker -- a remote
               `cli.py shard` never claims one (server/jobs.py);
  warehouse    records every configuration in sim_results.duckdb, one
               sweep per run (`server-<run id>-<fund>`), with the best
               configuration's trade log (server/backtest._warehouse_writer);
  Run History  archives every run with all its configurations, which the
               UI filters, sorts and pages across runs per fund.

Killing this script does not stop anything: the server owns the runs. A run
whose name is already in Run History or the queue is skipped, so re-running
this resumes a series rather than duplicating it.

--------------------------------------------------------------------
THE FUNDS

  RSP       1x equal-weight S&P 500, 2016-01-04 on: real SIP minute bars.
  URSP_SIM  2x RSP (tools/simulate_ursp.py): simulated before the real fund's
            2025-08-27 launch, the fund itself after. Run from 2016-01-04, the
            window RSP covers -- before that its minutes are borrowed from
            similar RSP days -- with the 2003-2015 sessions as the warm-up of
            the strategies that take one. Its grid steps and targets are RSP's
            doubled, because its daily moves are.

--------------------------------------------------------------------
WHICH STRATEGIES

Every registered strategy that can trade the fund. The ML ones are bound to
one fund each by the model they load (data/ml/models/<fund>_*; trained with
tools/train_qlib_regime.py --use-qlib and tools/train_ml_model.py), so they
run only there, and their regime thresholds are read from that model's own
output quantiles at plan time. ultimate_rsp and ultimate_ursp run on BOTH
funds: they were designed for one each, but neither checks its ticker, and
brute force asks what each does on the other.

Cost per configuration was measured on this machine (one full-history RSP
configuration each, a single process): 25-35 s, Ultimate 58 s. The server
uses every core but one.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

CAMPAIGN = "brute force 2026-10"
RANK_BY = "Total Return %"
FILL = "intrabar"
WORKERS = max(1, (os.cpu_count() or 2) - 1)

# Seconds per full-history configuration on this machine, measured.
COST_SECONDS: dict[str, float] = {
    "fixed": 25.1,
    "rsi": 25.6,
    "bell_curve": 29.2,
    "bayesian_dual_scale": 30.5,
    "ultimate_rsp": 31.7,
    "ultimate_ursp": 30.6,
    "hf_local_reference": 34.4,
    "hf_entry_gated": 34.2,
    "ultimate": 57.9,
    # Measured on 2024-2026 and scaled to the full history.
    "ml_regime_rsp": 60.0,
    "ml_regime_ursp": 60.0,
    "ml_reachability_rsp": 1200.0,
}

FUNDS: dict[str, dict[str, Any]] = {
    "RSP": {
        "start": None,
        "steps": [0.0025, 0.005, 0.0075, 0.01, 0.015, 0.02],
        "targets": [0.005, 0.01, 0.02, 0.03],
        "scale": 1.0,
    },
    "URSP_SIM": {
        "start": "2016-01-04",
        "steps": [0.005, 0.01, 0.015, 0.02, 0.03, 0.04],
        "targets": [0.01, 0.02, 0.04, 0.06],
        "scale": 2.0,
    },
}

# Queue order: the researched designs first, then from cheap to dear, so the
# results worth reading arrive first.
ORDER = [
    "ultimate_rsp",
    "ultimate_ursp",
    "ultimate",
    "fixed",
    "hf_local_reference",
    "hf_entry_gated",
    "rsi",
    "bell_curve",
    "bayesian_dual_scale",
    "ml_regime_rsp",
    "ml_regime_ursp",
    "ml_reachability_rsp",
]

# Strategies bound to one fund by the model they load.
ONLY_ON = {
    "ml_regime_rsp": {"RSP"},
    "ml_regime_ursp": {"URSP_SIM"},
    "ml_reachability_rsp": {"RSP"},
}
MODELS = _REPO_ROOT / "data" / "ml" / "models"

# BayesianDualScaleSizing estimates the probability of reaching ONE target, so
# the server refuses a submission with several: one per target instead.
ONE_TARGET_PER_RUN = {"bayesian_dual_scale"}


def _scaled(values: list[float], scale: float) -> list[float]:
    return [round(v * scale, 6) for v in values]


def spaces(strategy: str, fund: str) -> list[dict[str, Any]]:
    """The parameter space(s) of `strategy` on `fund`, over the strategy's
    committed defaults (param_schema.STRATEGY_DEFAULTS: the values its
    research chose), so an axis not swept keeps the researched value rather
    than a bare constructor default. A list, because some strategies have
    parameters that only mean something in one mode, and one cartesian
    product would run the same configuration many times."""
    from research.strategies.param_schema import STRATEGY_DEFAULTS

    defaults = STRATEGY_DEFAULTS.get(strategy, {})
    return [{**defaults, **space} for space in _spaces(strategy, fund)]


def _spaces(strategy: str, fund: str) -> list[dict[str, Any]]:
    scale = FUNDS[fund]["scale"]
    if strategy == "fixed":
        return [{"allocation_pct": [0.01, 0.02, 0.03, 0.05, 0.08, 0.12, 0.20, 0.30]}]
    if strategy == "hf_local_reference":
        return [
            {
                "bars_per_day": [387],
                "per_lot_pct": [0.0002, 0.0005, 0.001, 0.002],
                "lookback_days": [0.02, 0.1, 0.5, 1.0, 3.0],
                "vol_scale_exponent": [0.0, -0.75, -1.5],
                "vol_fast_days": [0.25, 0.5],
                "vol_slow_days": [10.0, 20.0],
                "volume_scale_exponent": [0.0, -1.0],
                "dd_throttle_start": [None, 0.15],
            }
        ]
    if strategy == "hf_entry_gated":
        # Every combination of the five entry gates, on the champion's sizing.
        return [
            {
                "bars_per_day": [387],
                "per_lot_pct": [0.0005, 0.001],
                "lookback_days": [0.1, 0.5],
                "breakdown_gate": ["off", "dual_thrust", "opening_range", "prior_low"],
                "pattern_gate": ["off", "shooting_star"],
                "momentum_gate": ["off", "early_negative"],
                "bounce_gate": ["off", "w_bottom"],
                "rsi_gate": ["off", "head_shoulders"],
            }
        ]
    if strategy == "rsi":
        return [
            {
                "max_trade_pct": [0.02, 0.05, 0.08, 0.15],
                "period": [7, 14, 21, 30],
                "oversold_threshold": [20.0, 30.0, 40.0],
                "baseline_multiplier": [0.0, 0.1, 0.25],
                "aggression_factor": [0.5, 0.9],
                "exponent": [1.0, 2.0],
            }
        ]
    if strategy == "bell_curve":
        return [
            {
                "max_trade_pct": [0.02, 0.05, 0.08, 0.15],
                "lookback_days": [5, 10, 20, 40, 60],
                "bars_per_day": [387],
                "mu": [0.1, 0.2, 0.3],
                "sigma": [0.05, 0.1, 0.2],
                "inverse_scale_kappa": [0.0, 1.0],
            }
        ]
    if strategy == "bayesian_dual_scale":
        # target_return is the grid's own profit target (the server aligns it).
        return [
            {
                "max_trade_pct": [0.02, 0.05, 0.08],
                "horizon_days": [1.0, 3.0],
                "bars_per_day": [387],
                "fast_half_life_days": [2.0, 5.0, 10.0],
                "slow_half_life_days": [60.0, 120.0],
                "confidence_k": [1.0, 2.0, 3.0],
                "vol_scale_exponent": [0.0, -1.0],
                "reference_probability": [0.4, 0.5, 0.6],
            }
        ]
    if strategy == "ultimate":
        # The regime and its two turbulent modes; capitulation thresholds and
        # targets scale with the fund (TQQQ's -9% / 6% is a 3x fund's).
        common = {
            "bars_per_day": [387],
            "natr_period": [10, 14],
            "bear_dd": [None, 0.25, 0.5],
            "per_lot_pct": [0.0002, 0.001],
        }
        return [
            {
                **common,
                "turbulent_mode": ["reversal"],
                "reversal_threshold": _scaled([-0.02, -0.03, -0.05], scale),
                "reversal_target": _scaled([0.02, 0.04], scale),
            },
            {**common, "turbulent_mode": ["cash"]},
        ]
    if strategy == "ultimate_rsp":
        return [
            {
                "pd_weight": [0.0, 0.25, 0.5, 0.75, 1.0],
                "execute_minute": [30, 60, 120],
                "rebalance_band": [0.02, 0.05, 0.1, 0.2],
                "pd_periods": ["14,21,42", "10,14,21", "21,42,63"],
                "pd_lookbacks": ["100,250", "50,100"],
                "ad_params": ["3/10,5/20,10/40", "5/20"],
            }
        ]
    if strategy in ("ml_regime_rsp", "ml_regime_ursp"):
        return [_regime_space(fund)]
    if strategy == "ml_reachability_rsp":
        return [
            {
                "max_trade_pct": [0.02, 0.05, 0.08, 0.15],
                "confidence_floor": [0.0, 0.25, 0.5, 0.75],
                "inverse_scale_kappa": [0.0, 1.0],
            }
        ]
    if strategy == "ultimate_ursp":
        return [
            {
                "pd_weight": [0.25, 0.5, 0.75],
                "rebalance_band": [0.1, 0.2, 0.3],
                "bear_window": [125, 250],
                "bear_dd_start": [0.15, 0.25, 0.35],
                "bear_dd_full": [0.45, 0.55, 0.7],
            }
        ]
    raise KeyError(strategy)


def _quantiles(fund: str, head: str) -> dict[str, float]:
    import json

    sidecar = MODELS / f"{fund}_regime_{head}.json"
    return json.loads(sidecar.read_text(encoding="utf-8"))["score_quantiles"]


def _regime_space(fund: str) -> dict[str, Any]:
    """MLRegimeScaledSizing's thresholds come from ITS model's own output:
    a calibrated classifier on a ~18% base rate never emits a high number,
    and a threshold above its p99 never fires (and is refused). Entry at the
    model's distinct upper levels, exit at its median."""
    crash, fwdvol = _quantiles(fund, "crash"), _quantiles(fund, "fwdvol")
    exit_at = round(crash["p50"], 4)
    enter = sorted({round(crash[q], 4) for q in ("p75", "p90", "p99")} - {exit_at})
    return {
        "ticker": [fund],
        "max_trade_pct": [0.02, 0.05, 0.08],
        "crash_step_multiplier": [1.0, 2.0, 4.0],
        "regime_enter_threshold": [level for level in enter if level > exit_at],
        "regime_exit_threshold": [exit_at],
        "regime_floor": [0.10, 0.25, 0.50],
        "vol_reference": sorted({round(fwdvol["p50"], 4), round(fwdvol["p75"], 4)}),
    }


def grid(strategy: str, fund: str) -> tuple[list[float], list[float]]:
    """(grid steps, profit targets) for `strategy` on `fund`."""
    scale = FUNDS[fund]["scale"]
    if strategy in ("ultimate_rsp", "ultimate_ursp"):
        # Daily exposure targets, exited by signal: no grid to search. The
        # configs these were researched with use exactly this.
        return [0.001], [10.0]
    if strategy == "ultimate":
        # Its calm sleeve is the champion: small steps, wide targets.
        return _scaled([0.0005, 0.001, 0.0025, 0.005], scale), _scaled([0.01, 0.03, 0.1], scale)
    if strategy == "ml_reachability_rsp":
        # Scoring every bar with a model costs ~20x a plain strategy, so a
        # coarser grid: every other step, the two middle targets.
        steps, targets = FUNDS[fund]["steps"], FUNDS[fund]["targets"]
        return steps[::2], targets[1:3]
    return FUNDS[fund]["steps"], FUNDS[fund]["targets"]


def combos(space: dict[str, Any]) -> int:
    n = 1
    for value in space.values():
        n *= len(value) if isinstance(value, list) else 1
    return n


def plan(funds: list[str], strategies: list[str]) -> list[dict[str, Any]]:
    """Every submission, in queue order: strategy by strategy, each fund in turn."""
    out = []
    for strategy in strategies:
        for fund in funds:
            if strategy in ONLY_ON and fund not in ONLY_ON[strategy]:
                continue
            steps, targets = grid(strategy, fund)
            subspaces = spaces(strategy, fund)
            target_groups = [[t] for t in targets] if strategy in ONE_TARGET_PER_RUN else [targets]
            total = len(subspaces) * len(target_groups)
            i = 0
            for space in subspaces:
                for group in target_groups:
                    i += 1
                    suffix = f" [{i}/{total}]" if total > 1 else ""
                    tag = f" pt={group[0]:.3g}" if strategy in ONE_TARGET_PER_RUN else ""
                    body = {
                        "name": f"{fund} {CAMPAIGN} -- {strategy}{suffix}{tag}",
                        "tickers": [fund],
                        "grid_steps": steps,
                        "targets": group,
                        "model": strategy,
                        "params": space,
                        "fill": FILL,
                        "rank_by": RANK_BY,
                        "local_only": True,
                    }
                    if FUNDS[fund]["start"]:
                        body["start"] = FUNDS[fund]["start"]
                    configurations = combos(space) * len(steps) * len(group)
                    out.append({"body": body, "strategy": strategy, "n": configurations})
    return out


def _get(api: str, path: str) -> Any:
    with urllib.request.urlopen(f"{api}{path}", timeout=60) as resp:
        return json.loads(resp.read())


def _post(api: str, path: str, body: dict[str, Any]) -> Any:
    request = urllib.request.Request(
        f"{api}{path}",
        data=json.dumps(body).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=120) as resp:
        return json.loads(resp.read())


def already_handled(api: str) -> set[str]:
    """Names in Run History, or queued, running or paused."""
    done = {run.get("name") for run in _get(api, "/api/backtest/history/runs")["runs"].values()}
    pending = {
        (run.get("req") or {}).get("name")
        for run in _get(api, "/api/backtest/runs").get("runs", [])
        if run.get("status") in ("queued", "running", "pausing", "paused")
    }
    return {name for name in done | pending if name}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.strip().splitlines()[0])
    parser.add_argument("--api", default="http://127.0.0.1:8000")
    parser.add_argument("--fund", nargs="+", choices=list(FUNDS), default=list(FUNDS))
    parser.add_argument("--only", nargs="+", metavar="STRATEGY", choices=ORDER)
    parser.add_argument("--dry-run", action="store_true", help="print the plan; queue nothing")
    parser.add_argument(
        "--resubmit", action="store_true", help="queue runs already in history or the queue"
    )
    args = parser.parse_args(argv)

    submissions = plan(args.fund, args.only or ORDER)
    total = sum(s["n"] for s in submissions)
    hours = sum(s["n"] * COST_SECONDS[s["strategy"]] for s in submissions) / WORKERS / 3600
    print(f"{len(submissions)} submissions, {total:,} configurations, about {hours:.1f} h ")
    print(f"on {WORKERS} workers ({FILL} fills, full history, this machine only)\n")
    for s in submissions:
        each = s["n"] * COST_SECONDS[s["strategy"]] / WORKERS / 3600
        print(f"  {s['n']:>6,} cfg  ~{each:>5.2f} h  {s['body']['name']}")

    try:
        for s in submissions:
            problems = _post(args.api, "/api/backtest/validate", s["body"]).get("errors") or []
            if problems:
                print(f"\nINVALID {s['body']['name']}: {problems}", file=sys.stderr)
                return 2
    except urllib.error.URLError as exc:
        print(f"\nUNREACHABLE {args.api}: {getattr(exc, 'reason', exc)}", file=sys.stderr)
        return 1
    print("\nEvery submission validates.")
    if args.dry_run:
        print("--dry-run: nothing queued.")
        return 0

    skip = set() if args.resubmit else already_handled(args.api)
    queued = 0
    for s in submissions:
        name = s["body"]["name"]
        if name in skip:
            print(f"  skip (already handled) {name}")
            continue
        try:
            answer = _post(args.api, "/api/backtest/runs", s["body"])
        except urllib.error.HTTPError as exc:
            print(f"  REJECTED {name}: {exc.code} {exc.read().decode()[:300]}", file=sys.stderr)
            return 1
        runs = answer.get("runs") or [answer]
        print(f"  queued {len(runs)} run(s)  {name}", flush=True)
        queued += 1
    print(f"\n{queued} submission(s) queued. The server owns them now.")
    print(f"Watch: {args.api}  (Backtesting -> Active runs, Run History)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
