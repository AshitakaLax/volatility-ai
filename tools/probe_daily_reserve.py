#!/usr/bin/env python
"""
Daily Ultimate RESERVE (docs/research/daily-ultimate-reserve.md): the owner's
+0.1% of equity a session at the least drawdown, with as much of the account
in cash as possible -- and still standing if the next bear is worse than
2022's.

    python tools/probe_daily_reserve.py --stage reserve --out DIR [--jobs N]
    python tools/probe_daily_reserve.py --stage stress  --out DIR
    python tools/probe_daily_reserve.py --stage trim    --out DIR
    python tools/probe_daily_reserve.py --stage robust  --out DIR
    python tools/probe_daily_reserve.py --stage both    --out DIR
    python tools/probe_daily_reserve.py --report DIR

Stages run in that order, each reading the last from DIR; a run already in
DIR/results.jsonl is skipped. Every later stage ends on the reserve stage's
last session, so bars added to the warehouse since do not move its history.
Every run is measured as
tools/probe_daily_ultimate.py measures one (causal fills, dynamic slippage,
no cash yield, TQQQ from 2016-01-04, scored from 2017-01-03), plus how much
of the account is in the fund, bar by bar.

--------------------------------------------------------------------
WHY THE LOTS ARE COMPOUNDED

config/daily_ultimate_tqqq.yaml's lots are a share of STARTING equity. From
2016 they shrink to a sliver of an account that has grown fourfold by 2022,
which is most of why its drawdown reads 29.9%: the same configuration opened
at the 2021 peak falls 57.6%, with 59% of the account in TQQQ on average.
Here every lot is a share of the session's opening equity, so a drawdown is
the same whenever the account starts and whatever it has grown to.

--------------------------------------------------------------------
THE AXES (reserve)

  turbulent  cash, or Ultimate's reversal lots at 5% of equity (four at most)
  cap        risk.max_total_exposure: none, 50%, 30%, 20% of equity in TQQQ
  lot        0.2%, 0.4%, 0.8% of equity at each step
  step       0.2%, 0.4%
  target     +4%, +8%, +12%
  pause      buy nothing more in a calm session once it is up 0.1%
  protect    none; a drawdown throttle (the exposure cap ramps from its value
             at a 5% drawdown to 10% of equity at 20%); or a tighter bear
             filter (no calm buying 30% below the 250-session high, not 50%)

Everything else is the pinned daily_ultimate's: NATR(14) against its
100-session median, held 5 sessions, regime exit an hour into the first
turbulent session, reversal after a -8% session sold at +8%.

--------------------------------------------------------------------
THE STRESS (stress)

The STRESS_CANDIDATES configurations at the goal with the shallowest drawdown
over history, the shallowest at the goal for each turbulent sleeve x cap x
protection, and the pinned config for reference, each under
tools/stress_paths.py's four falls worse than 2022's (deeper -92%, grind
-95%, twice -96.5%, and fast: 2020's crash taken to -83.5% in a month) and
opened at the 2021 peak ("top").

--------------------------------------------------------------------
THE CHOICE

At the goal -- at least GOAL a session over the whole history -- the
shallowest WORST drawdown, the deepest of history's and the five stress
runs'. Drawdowns within TIE_DD points tie, and the tie goes to the lower
average exposure: the cash the owner asked to keep.

trim then spends whatever return the choice makes above the goal: its lot and
cap stepped down, every step stressed, the same rule choosing again. robust
changes one thing at a time and runs each on history and on the choice's
worst stress path.

The walk-forward check in the report applies the rule to 2017-2021 alone
(history, at the goal there, shallowest drawdown there) and scores what it
picks on 2022 onward. both stresses every configuration at the goal in BOTH
halves, 2017-2021 and 2022 on, which the choice need not be: the price of a
goal that holds after 2022 too. It does not change the choice.
"""

from __future__ import annotations

import argparse
import functools
import json
import sys
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path
from typing import Any

_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from tools import probe_daily_ultimate as du
from tools import stress_paths

FUND = "TQQQ"
GOAL = du.GOAL
TIE_DD = 1.0  # drawdowns within a point tie; the tie goes to the lower exposure
STRESS_CANDIDATES = 30
STRESSES = (*stress_paths.SCENARIOS, "top")
PINNED = _REPO_ROOT / "config" / "daily_ultimate_tqqq.yaml"
# What the stages chose (docs/research/daily-ultimate-reserve.md), as a CELL,
# committed as config/daily_ultimate_reserve_tqqq.yaml.
CHOSEN = (0.0025, 0.12, 0.004, None, "cash", True, "throttle")
CHOSEN_CONFIG = _REPO_ROOT / "config" / "daily_ultimate_reserve_tqqq.yaml"

TURBULENT = ("cash", "rev5")
CAPS = (None, 0.5, 0.3, 0.2)
LOTS = (0.002, 0.004, 0.008)
STEPS = (0.002, 0.004)
TARGETS = (0.04, 0.08, 0.12)
THROTTLE = {"dd_exposure_start": 0.05, "dd_exposure_full": 0.20, "dd_exposure_floor_pct": 0.10}
PROTECT = ("none", "throttle", "bear30")
CELL = ("lot", "target", "step", "cap", "turbulent", "pause", "protect")


# --------------------------------------------------------------- the plan


def reserve(
    lot: float,
    target: float,
    step: float,
    cap: float | None,
    turbulent: str = "cash",
    pause: bool = True,
    protect: str = "none",
    **over,
) -> dict:
    """The engine config of one reserve configuration."""
    params, _, tgt = du.daily_ultimate(
        FUND, 1.0, target, lot, "hold", pause, True, turbulent=turbulent
    )
    if protect == "bear30":
        params["bear_dd"] = 0.3
    params.update(over.pop("params", {}))
    risk: dict[str, Any] = {} if cap is None else {"max_total_exposure": cap}
    if protect == "throttle":
        risk.update(THROTTLE)
    risk.update(over.pop("risk", {}))
    return du._config(FUND, "daily_ultimate", params, step, tgt, risk=risk, **over)


def _label(lot, target, step, cap, turbulent, pause, protect) -> str:
    return du._name(
        f"lot{lot}",
        f"t{target}",
        f"s{step}",
        f"cap{cap}" if cap is not None else "nocap",
        turbulent,
        "pause" if pause else "",
        "" if protect == "none" else protect,
    )


def plan_reserve() -> list[dict]:
    out = []
    for turbulent in TURBULENT:
        for cap in CAPS:
            for lot in LOTS:
                for step in STEPS:
                    for target in TARGETS:
                        for pause in (False, True):
                            for protect in PROTECT:
                                cell = (lot, target, step, cap, turbulent, pause, protect)
                                out.append(
                                    du._spec(
                                        "reserve",
                                        du._name("reserve", _label(*cell)),
                                        FUND,
                                        reserve(*cell),
                                        lot=lot,
                                        target=target,
                                        step=step,
                                        cap=cap,
                                        turbulent=turbulent,
                                        pause=pause,
                                        protect=protect,
                                    )
                                )
    return out


def _pinned_config() -> dict:
    import yaml

    return yaml.safe_load(PINNED.read_text())


@functools.cache
def _top_start() -> str:
    from engine.warehouse.bars import load_frame

    return stress_paths.top_start(load_frame(FUND))


def _under(spec: dict, stress: str | None) -> dict:
    """`spec` run under `stress`: a stress path, "top" (opened at the 2021
    peak), or None for history."""
    if stress == "top":
        spec["start"] = _top_start()
    elif stress is not None:
        spec["stress"] = stress
    return spec


def _stressed(stage: str, label: str, config: dict, meta: dict, history: bool) -> list[dict]:
    """`config` under every stress (and on history, if asked): specs named
    "<stage> <stress> | <label>"."""
    out = []
    for stress in ((None,) if history else ()) + STRESSES:
        spec = du._spec(stage, du._name(stage, stress or "history", "|", label), FUND, config)
        spec["meta"] = {**meta, "base": label, "stress": stress or "history"}
        out.append(_under(spec, stress))
    return out


def candidates(rows: list[dict], n: int | None = None) -> list[dict]:
    """The `n` (STRESS_CANDIDATES) history rows at the goal with the
    shallowest drawdown."""
    hit = [r for r in rows if r["metrics"]["geo_daily"] >= GOAL * 100]
    return sorted(hit, key=lambda r: r["metrics"]["max_dd"])[: n or STRESS_CANDIDATES]


def stress_candidates(rows: list[dict]) -> list[dict]:
    """candidates(), plus the shallowest at the goal for every turbulent
    sleeve x cap x protection, so each lever meets the stress paths."""
    out = {r["name"]: r for r in candidates(rows)}
    groups: dict[tuple, list[dict]] = {}
    for r in rows:
        m = r["meta"]
        groups.setdefault((m["turbulent"], m["cap"], m["protect"]), []).append(r)
    for group in groups.values():
        for r in candidates(group, 1):
            out.setdefault(r["name"], r)
    return list(out.values())


def plan_stress(out_dir: Path) -> list[dict]:
    rows = [r for r in du.load_results(out_dir) if r["stage"] == "reserve" and du._ok(r)]
    if not rows:
        raise SystemExit(f"no reserve results in {out_dir}: run --stage reserve first")
    out = _stressed("stress", "pinned daily_ultimate_tqqq", _pinned_config(), {}, history=True)
    for row in stress_candidates(rows):
        label = row["name"].removeprefix("reserve ")
        out += _stressed("stress", label, _config_of(row), row["meta"], history=False)
    return out


def reserve_end(out_dir: Path) -> str:
    """The last session the reserve stage loaded: every later stage ends
    there too."""
    ends = {
        r["metrics"]["end"]
        for r in du.load_results(out_dir)
        if r["stage"] == "reserve" and du._ok(r)
    }
    if not ends:
        raise SystemExit(f"no reserve results in {out_dir}: run --stage reserve first")
    return max(ends)


def _config_of(row: dict) -> dict:
    return reserve(**{k: row["meta"][k] for k in CELL})


# --------------------------------------------------------------- the books


def books(rows: list[dict]) -> dict[str, dict]:
    """Every configuration's runs keyed by its label: {"history": row,
    "<stress>": row, ...}. A reserve row is its configuration's history."""
    out: dict[str, dict] = {}
    for r in rows:
        if r["stage"] == "reserve":
            out.setdefault(r["name"].removeprefix("reserve "), {})["history"] = r
        elif "base" in r["meta"]:
            out.setdefault(r["meta"]["base"], {})[r["meta"]["stress"]] = r
    return out


def summary(book: dict) -> dict | None:
    """One configuration over history and every stress, or None until all
    of them have run."""
    if "history" not in book or any(s not in book for s in STRESSES):
        return None
    h = book["history"]
    dds = {s: book[s]["metrics"]["max_dd"] for s in ("history", *STRESSES)}
    exposure = h.get("exposure") or {}
    return {
        "row": h,
        "geo_daily": h["metrics"]["geo_daily"],
        "dd": dds,
        "worst_dd": max(dds.values()),
        "worst_stress": max(dds, key=dds.get),
        "avg_exposure": exposure.get("avg_exposure", float("nan")),
        "max_exposure": exposure.get("max_exposure", float("nan")),
    }


def choose(summaries: list[dict]) -> dict | None:
    """THE CHOICE (module docstring)."""
    hit = [s for s in summaries if s["geo_daily"] >= GOAL * 100]
    if not hit:
        return None
    floor = min(s["worst_dd"] for s in hit)
    tied = [s for s in hit if s["worst_dd"] <= floor + TIE_DD]
    return min(tied, key=lambda s: (s["avg_exposure"], s["worst_dd"], -s["geo_daily"]))


def chosen(out_dir: Path, stages=("stress", "reserve")) -> dict:
    rows = [r for r in du.load_results(out_dir) if du._ok(r)]
    rows = [r for r in rows if r["stage"] in stages]
    done = [s for s in map(summary, books(rows).values()) if s]
    best = choose(done)
    if best is None:
        raise SystemExit(f"no stressed configuration at the goal in {out_dir}")
    return best


def plan_trim(out_dir: Path) -> list[dict]:
    """The choice's lot and cap stepped down (module docstring)."""
    best = chosen(out_dir)
    m = best["row"]["meta"]
    rows = [r for r in du.load_results(out_dir) if du._ok(r)]
    complete = {label for label, book in books(rows).items() if summary(book)}
    out = []
    for lot_x in (0.5, 0.625, 0.75, 0.875, 1.0):
        for cap_x in (0.5, 0.75, 1.0):
            if lot_x == cap_x == 1.0:
                continue
            lot = round(m["lot"] * lot_x, 6)
            cap = None if m["cap"] is None else round(m["cap"] * cap_x, 4)
            if m["cap"] is None and cap_x != 1.0:
                continue
            cell = (lot, m["target"], m["step"], cap, m["turbulent"], m["pause"], m["protect"])
            label = _label(*cell)
            if label in complete:  # already stressed as a candidate
                continue
            meta = dict(zip(CELL, cell, strict=True))
            out += _stressed("trim", label, reserve(*cell), meta, history=True)
    return out


def plan_robust(out_dir: Path) -> list[dict]:
    """The final choice with one thing changed, on history and on its worst
    stress path."""
    best = chosen(out_dir, stages=("stress", "reserve", "trim"))
    m, worst = best["row"]["meta"], best["worst_stress"]
    cap = m["cap"]
    variants: list[tuple[str, dict]] = [
        ("slippage x4", {"costs": {**du.SLIPPAGE, "base_bps": 2.0}}),
        ("slippage x10", {"costs": {**du.SLIPPAGE, "base_bps": 5.0}}),
        ("target x0.75", {"target": round(m["target"] * 0.75, 6)}),
        ("target x1.5", {"target": round(m["target"] * 1.5, 6)}),
        ("step x0.5", {"step": round(m["step"] / 2, 6)}),
        ("step x2", {"step": round(m["step"] * 2, 6)}),
        ("bear_dd 0.4", {"params": {"bear_dd": 0.4}}),
        ("bear_dd 0.6", {"params": {"bear_dd": 0.6}}),
        ("bear_window 125", {"params": {"bear_window": 125}}),
        ("bear_window 500", {"params": {"bear_window": 500}}),
        ("natr_period 10", {"params": {"natr_period": 10}}),
        ("natr_period 20", {"params": {"natr_period": 20}}),
        ("regime_min_hold 1", {"params": {"regime_min_hold": 1}}),
        ("regime_min_hold 10", {"params": {"regime_min_hold": 10}}),
        ("liquidate_minute 1", {"params": {"liquidate_minute": 1}}),
        ("liquidate_minute 180", {"params": {"liquidate_minute": 180}}),
        ("goal 0.05%", {"params": {"daily_goal": 0.0005}}),
        ("goal 0.2%", {"params": {"daily_goal": 0.002}}),
        # Idle cash earning a money-market rate: a flat 2% a year, about
        # EFFR's 2017-2026 average (the smart EFFR default needs data/external).
        ("cash yield 2%", {"cash_yield_pct": 0.02}),
    ]
    if cap is not None:
        variants += [
            ("cap x1.5", {"cap": min(1.0, round(cap * 1.5, 4))}),
            ("no cap", {"cap": None}),
        ]
    stresses = (None,) if worst == "history" else (None, worst)
    out = []
    for label, change in variants:
        cell = {k: change.get(k, m[k]) for k in CELL}
        over = {k: change[k] for k in ("params", "costs") if k in change}
        config = reserve(**cell, **over)
        if "cash_yield_pct" in change:
            config["execution"]["cash_yield_pct"] = change["cash_yield_pct"]
        for stress in stresses:
            spec = du._spec(
                "robust", du._name("robust", stress or "history", "|", label), FUND, config
            )
            spec["meta"] = {"variant": label, "stress": stress or "history"}
            out.append(_under(spec, stress))
    return out


def at_goal_in_both_halves(rows: list[dict]) -> list[dict]:
    """The rows at the goal over 2017-2021 and again from 2022 on."""
    return [
        r
        for r in rows
        if min(
            du.window_metrics(r, None, du.SPLIT).get("geo_daily", float("-inf")),
            du.window_metrics(r, du.SPLIT, None).get("geo_daily", float("-inf")),
        )
        >= GOAL * 100
    ]


def plan_both(out_dir: Path) -> list[dict]:
    """Every reserve configuration at the goal in both halves, stressed."""
    rows = [r for r in du.load_results(out_dir) if r["stage"] == "reserve" and du._ok(r)]
    out = []
    for row in at_goal_in_both_halves(rows):
        label = row["name"].removeprefix("reserve ")
        out += _stressed("both", label, _config_of(row), row["meta"], history=False)
    return out


# --------------------------------------------------------------- the report


def buy_and_hold(out_dir: Path) -> dict[str, dict]:
    """TQQQ held over history and each stress path (scored from the same
    session the books are), cached."""
    import pandas as pd

    from engine.warehouse.bars import load_frame

    cache = out_dir / "buy_and_hold_stress.json"
    if cache.exists():
        return json.loads(cache.read_text())
    bars = load_frame(FUND)
    bars = bars[bars.index >= pd.Timestamp(du.START, tz="UTC")]
    out = {}
    for stress in (None, *stress_paths.SCENARIOS, "top"):
        frame = bars
        if stress == "top":
            frame = bars[bars.index >= pd.Timestamp(stress_paths.top_start(bars), tz="UTC")]
        elif stress is not None:
            frame = stress_paths.stressed(bars, stress)
        idx = frame.index.tz_convert(du.TZ).tz_localize(None)
        closes = pd.Series(frame["close"].to_numpy(float), index=idx).groupby(idx.normalize())
        closes = closes.last()
        scored = closes[closes.index >= pd.Timestamp(du.score_start(closes.index))]
        out[stress or "history"] = du.daily_metrics(scored)
    cache.write_text(json.dumps(out, indent=1))
    return out


def _line(s: dict) -> str:
    dd = s["dd"]
    m = s["row"]["metrics"]
    stresses = "  ".join(f"{k} {dd[k]:4.1f}" for k in STRESSES)
    return (
        f"{s['geo_daily']:6.3f}%/d CAGR {m['cagr']:5.1f}%  DD {dd['history']:4.1f}%  "
        f"[{stresses}]  worst {s['worst_dd']:4.1f}%  "
        f"in TQQQ avg {s['avg_exposure']:4.1f}% max {s['max_exposure']:5.1f}%"
    )


def report(out_dir: Path) -> str:
    rows = [r for r in du.load_results(out_dir) if du._ok(r)]
    failed = [r for r in du.load_results(out_dir) if r.get("error")]
    bh = buy_and_hold(out_dir)
    lines = [f"# daily-ultimate reserve sweep: {len(rows)} runs ({len(failed)} failed)", ""]
    lines.append("TQQQ buy-and-hold:")
    for k, m in bh.items():
        lines.append(
            f"- {k:8s} {m['start']}..{m['end']}: {m['geo_daily']:.3f}%/d CAGR {m['cagr']:.1f}% "
            f"DD {m['max_dd']:.1f}%"
        )

    history = [r for r in rows if r["stage"] == "reserve"]
    if history:
        hit = [r for r in history if r["metrics"]["geo_daily"] >= GOAL * 100]
        lines += [
            "",
            f"## reserve: {len(history)} configurations, {len(hit)} at the goal over history",
            "",
            "The shallowest drawdowns at the goal (history only):",
        ]
        for r in candidates(history, 25):
            e, m = r.get("exposure", {}), r["metrics"]
            lines.append(
                f"  {r['name'].removeprefix('reserve '):52s} {m['geo_daily']:6.3f}%/d "
                f"CAGR {m['cagr']:5.1f}% DD {m['max_dd']:4.1f}% 2022 {m['years'].get('2022'):6.1f}% "
                f"in TQQQ avg {e.get('avg_exposure', float('nan')):4.1f}% "
                f"max {e.get('max_exposure', float('nan')):5.1f}%"
            )
        by_axis = {}
        for axis in ("turbulent", "cap", "protect", "pause", "step"):
            for value in sorted({str(r["meta"][axis]) for r in history}):
                sub = [r for r in history if str(r["meta"][axis]) == value]
                at = [r for r in sub if r["metrics"]["geo_daily"] >= GOAL * 100]
                best = min((r["metrics"]["max_dd"] for r in at), default=float("nan"))
                by_axis[(axis, value)] = (len(at), len(sub), best)
        lines += ["", "Each axis: configurations at the goal, and the shallowest drawdown there:"]
        for (axis, value), (n, total, best) in by_axis.items():
            lines.append(f"  {axis:9s} {value:8s} {n:3d} of {total:3d}   DD {best:5.1f}%")

    stressed_rows = [r for r in rows if r["stage"] in ("reserve", "stress", "trim")]
    every = {label: s for label, book in books(stressed_rows).items() if (s := summary(book))}
    picked = None
    for stage in ("stress", "trim"):
        shown = {
            label: s
            for label, s in every.items()
            if any(r["stage"] == stage for r in books(stressed_rows)[label].values()) or s is picked
        }
        if not shown:
            continue
        picked = choose([*shown.values()]) if stage == "stress" else choose([*every.values()])
        lines += ["", f"## {stage}", ""]
        for label, s in sorted(shown.items(), key=lambda kv: kv[1]["worst_dd"]):
            mark = "**" if s is picked else "  "
            lines.append(f"{mark}{label:52s} {_line(s)}")
        if picked:
            lines += ["", f"Chosen: {picked['row']['name']} (worst on {picked['worst_stress']})"]

    robust = [r for r in rows if r["stage"] == "robust"]
    if robust:
        lines += ["", "## robust", ""]
        for r in sorted(robust, key=lambda r: (r["meta"]["stress"], r["meta"]["variant"])):
            m, e = r["metrics"], r.get("exposure", {})
            lines.append(
                f"  {r['meta']['stress']:8s} {r['meta']['variant']:22s} {m['geo_daily']:6.3f}%/d "
                f"CAGR {m['cagr']:5.1f}% DD {m['max_dd']:4.1f}% "
                f"in TQQQ avg {e.get('avg_exposure', float('nan')):4.1f}%"
            )

    if history:
        for r in history:
            r["in"] = du.window_metrics(r, None, du.SPLIT)
            r["out"] = du.window_metrics(r, du.SPLIT, None)
        hit_in = [r for r in history if r["in"]["geo_daily"] >= GOAL * 100]
        lines += ["", "## walk-forward (the rule on 2017-2021 history alone, scored 2022 on)", ""]
        if hit_in:
            pick = min(hit_in, key=lambda r: r["in"]["max_dd"])
            ranked = sorted(history, key=lambda r: -r["out"]["geo_daily"])
            i, o = pick["in"], pick["out"]
            lines += [
                f"  picked {pick['name']}",
                f"    2017-2021 {i['geo_daily']:.3f}%/d DD {i['max_dd']:.1f}%",
                f"    2022 on   {o['geo_daily']:.3f}%/d DD {o['max_dd']:.1f}%, "
                f"rank {ranked.index(pick) + 1} of {len(ranked)}",
            ]
        both = [
            r for r in history if min(r["in"]["geo_daily"], r["out"]["geo_daily"]) >= GOAL * 100
        ]
        lines.append(f"  at the goal in BOTH halves: {len(both)} of {len(history)}")

    both_rows = [r for r in rows if r["stage"] in ("reserve", "both")]
    shown = {
        label: s
        for label, book in books(both_rows).items()
        if any(r["stage"] == "both" for r in book.values()) and (s := summary(book))
    }
    if shown:
        lines += ["", "## both (at the goal in both halves, stressed)", ""]
        for label, s in sorted(shown.items(), key=lambda kv: kv[1]["worst_dd"]):
            out = s["row"].get("out") or du.window_metrics(s["row"], du.SPLIT, None)
            lines.append(f"  {label:52s} {_line(s)}  2022 on {out['geo_daily']:.3f}%/d")
    text = "\n".join(lines) + "\n"
    (out_dir / "report.md").write_text(text)
    return text


# --------------------------------------------------------------- main


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.strip().splitlines()[0])
    parser.add_argument("--stage", choices=("reserve", "stress", "trim", "robust", "both"))
    parser.add_argument("--out", type=Path)
    parser.add_argument("--report", type=Path, help="print and write DIR/report.md")
    parser.add_argument("--jobs", type=int, default=16)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)
    if args.report:
        print(report(args.report))
        return 0
    if not args.stage or not args.out:
        parser.error("--stage and --out are required (or --report DIR)")
    args.out.mkdir(parents=True, exist_ok=True)
    plans = {
        "reserve": lambda: plan_reserve(),
        "stress": lambda: plan_stress(args.out),
        "trim": lambda: plan_trim(args.out),
        "robust": lambda: plan_robust(args.out),
        "both": lambda: plan_both(args.out),
    }
    specs = plans[args.stage]()
    if args.stage != "reserve":
        end = reserve_end(args.out)
        for spec in specs:
            spec["end"] = end
    done = {r["name"] for r in du.load_results(args.out)}
    todo = [s for s in specs if s["name"] not in done]
    print(f"{args.stage}: {len(specs)} runs, {len(specs) - len(todo)} done, {len(todo)} to run")
    if args.dry_run or not todo:
        return 0
    with (
        ProcessPoolExecutor(max_workers=args.jobs) as pool,
        (args.out / "results.jsonl").open("a") as sink,
    ):
        futures = {pool.submit(du.run_one, spec): spec for spec in todo}
        for n, future in enumerate(as_completed(futures), 1):
            spec = futures[future]
            try:
                result = future.result()
            except Exception as exc:  # one failed configuration never stops the stage
                result = {k: spec[k] for k in ("stage", "name", "fund", "meta")}
                result["error"] = repr(exc)[:2000]
            sink.write(json.dumps(result, default=str) + "\n")
            sink.flush()
            m, e = result.get("metrics") or {}, result.get("exposure") or {}
            status = result.get("error", "")[:120] or (
                f"{m.get('geo_daily', float('nan')):.3f}%/d DD {m.get('max_dd', float('nan')):.1f}% "
                f"in TQQQ avg {e.get('avg_exposure', float('nan')):.1f}%"
            )
            print(f"[{n}/{len(todo)}] {spec['name']}: {status}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
