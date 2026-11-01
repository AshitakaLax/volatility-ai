#!/usr/bin/env python
"""
The buy x sell sweep of the composed model, as web-UI runs on the server's
queue (so every configuration lands in sim_results.duckdb and Run History).

    python tools/sweep_composed.py --dry-run                 # the plan and its cost
    python tools/sweep_composed.py                           # every fund, every sell
    python tools/sweep_composed.py --fund RSP --loss-only    # the first sweep's slice
    python tools/sweep_composed.py --buy rk62_ma_cross --sell regime_exit
    python tools/sweep_composed.py --local-only              # keep it off the shards

ONE TO ONE: every run is one buy policy with one sell policy (`composed`,
params {buy: [one], sell: [one]}), each at its committed defaults. By default
every buy in the catalog is paired with every sell and run on every fund in
the warehouse; --loss-only keeps the sells that may sell below cost (owner,
Oct 31: `loss: true` in research/composition/catalog.py). A loss-capable pair
sets allow_signal_exit, as build_config does for any such composition.

Left out, and said so: a buy whose signal reads data the warehouse does not hold
(SKIP_BUYS: the run fails on every configuration), and any pair /validate
refuses (an ML policy on a fund it was not trained on). Both are listed.

INTRABAR fills, the whole history, the cost model of tools/sweep_brute_force.py.
The grid is small (2 steps x 2 targets, scaled by the fund's leverage), to cover
every pair; widen it on the winners. Re-running skips names already in Run
History or the queue.
"""

from __future__ import annotations

import argparse
import sys
import urllib.error
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

_TOOLS = Path(__file__).resolve().parent
for path in (_TOOLS, _TOOLS.parent):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from sweep_brute_force import FILL, RANK_BY, WORKERS, _get, _post, already_handled

CAMPAIGN = "composed 2026-11"
STEPS = [0.005, 0.01]
TARGETS = [0.01, 0.02]
SECONDS_PER_CONFIG = 35.0  # measured for a plain strategy on this machine

# How far a fund moves relative to RSP; the grid is RSP's times this.
SCALE = {
    "TQQQ": 3.0,
    "SQQQ": 3.0,
    "SOXL": 3.0,
    "URSP": 2.0,
    "URSP_SIM": 2.0,
    "QQQ": 1.3,
    "IWM": 1.2,
    "XBI": 1.5,
}

# These signals read files the warehouse does not hold (measured Nov 1: every
# configuration of every run errors with "reads data the warehouse does not hold").
SKIP_BUYS = frozenset(
    {
        "rk168_vix_term",
        "rk204_lead_lag",
        "rk212_breadth_thrust",
        "rk217_causal_impact",
        "rk221_transfer_entropy",
        "rk293_sentiment",
        "rk311_event_sentiment",
    }
)

# A buy that checks its own target against the sweep's: one run per target,
# with the buy's own parameter set to it (else every configuration errors).
TARGET_PARAM = {"bayesian_dual_scale": "target_return"}


def policies(loss_only: bool) -> tuple[list[str], list[str]]:
    """(buy ids, sell ids), from the catalog the web serves."""
    from research.composition import catalog

    cat = catalog.catalog()
    sells = [k for k, v in sorted(cat["sells"].items()) if v.get("loss") or not loss_only]
    return sorted(cat["buys"]), sells


def warehouse_funds(api: str) -> list[str]:
    return sorted(f["ticker"] for f in _get(api, "/api/backtest/funds")["funds"] if f.get("ok"))


def _grid(fund: str) -> tuple[list[float], list[float]]:
    scale = SCALE.get(fund, 1.0)
    return [round(s * scale, 6) for s in STEPS], [round(t * scale, 6) for t in TARGETS]


def plan(
    funds: list[str], buys: list[str], sells: list[str], local_only: bool = False
) -> list[dict]:
    out = []
    for fund in funds:
        steps, targets_all = _grid(fund)
        for buy in buys:
            for sell in sells:
                for targets in [[t] for t in targets_all] if buy in TARGET_PARAM else [targets_all]:
                    params = {"id": buy}
                    tag = ""
                    if buy in TARGET_PARAM:
                        from research.composition.catalog import defaults_for

                        # Named parameters replace the defaults wholesale.
                        params["params"] = {
                            **defaults_for("buy", buy),
                            TARGET_PARAM[buy]: targets[0],
                        }
                        tag = f" pt={targets[0]:g}"
                    out.append(
                        {
                            "name": f"{fund} {CAMPAIGN} -- {buy} x {sell}{tag}",
                            "tickers": [fund],
                            "grid_steps": steps,
                            "targets": targets,
                            "model": "composed",
                            "params": {"buy": [params], "sell": [{"id": sell}]},
                            "fill": FILL,
                            "rank_by": RANK_BY,
                            "local_only": local_only,
                        }
                    )
    return out


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.strip().splitlines()[0])
    parser.add_argument("--api", default="http://127.0.0.1:8000")
    parser.add_argument("--fund", nargs="+", help="only these funds (default: every fund)")
    parser.add_argument("--buy", nargs="+", help="only these buy policies")
    parser.add_argument("--sell", nargs="+", help="only these sell policies")
    parser.add_argument(
        "--loss-only", action="store_true", help="only sells that may sell below cost"
    )
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--local-only", action="store_true")
    parser.add_argument("--resubmit", action="store_true")
    args = parser.parse_args(argv)

    try:
        funds = [f for f in warehouse_funds(args.api) if not args.fund or f in args.fund]
    except urllib.error.URLError as exc:
        print(f"UNREACHABLE {args.api}: {getattr(exc, 'reason', exc)}", file=sys.stderr)
        return 1
    buys, sells = policies(args.loss_only)
    buys = [b for b in buys if (not args.buy or b in args.buy) and b not in SKIP_BUYS]
    sells = [s for s in sells if not args.sell or s in args.sell]
    bodies = plan(funds, buys, sells, local_only=args.local_only)

    def check(body: dict) -> list:
        return _post(args.api, "/api/backtest/validate", body).get("errors") or []

    with ThreadPoolExecutor(max_workers=12) as pool:
        verdicts = list(pool.map(check, bodies))
    valid = [b for b, e in zip(bodies, verdicts, strict=True) if not e]
    refused = [(b, e) for b, e in zip(bodies, verdicts, strict=True) if e]
    n = sum(len(b["grid_steps"]) * len(b["targets"]) for b in valid)
    hours = n * SECONDS_PER_CONFIG / WORKERS / 3600
    print(f"{len(funds)} funds x {len(buys)} buys x {len(sells)} sells ({', '.join(sells)})")
    print(f"left out, needing data the warehouse lacks: {', '.join(sorted(SKIP_BUYS))}")
    print(f"{len(valid)} valid runs, {len(refused)} refused; {n:,} configurations,")
    print(
        f"about {hours:.0f} h on this machine's {WORKERS} workers alone ({FILL} fills, full history)"
    )
    reasons: dict[str, int] = {}
    for _, errors in refused:
        key = str(errors[0])[:90]
        reasons[key] = reasons.get(key, 0) + 1
    for key, count in sorted(reasons.items(), key=lambda kv: -kv[1])[:8]:
        print(f"  refused x{count}: {key}")
    if args.dry_run:
        print("--dry-run: nothing queued.")
        return 0

    skip = set() if args.resubmit else already_handled(args.api)
    queued = 0
    for body in valid:
        if body["name"] in skip:
            continue
        try:
            _post(args.api, "/api/backtest/runs", body)
        except urllib.error.HTTPError as exc:
            print(
                f"REJECTED {body['name']}: {exc.code} {exc.read().decode()[:300]}", file=sys.stderr
            )
            return 1
        queued += 1
    print(
        f"{queued} run(s) queued ({len(valid) - queued} already handled). The server owns them now."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
