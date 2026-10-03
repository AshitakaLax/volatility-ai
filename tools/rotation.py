"""Rotation books: one account that moves between long-only instruments.

    python -m tools.rotation --mode defensive            # ledger X2 + X9
    python -m tools.rotation --mode relative_strength    # ledger X3
    python -m tools.rotation --mode hrp                  # ledger A5 / Q13

defensive
    The lead (TQQQ) while the regime is risk-on -- any regime
    tools/leverage_stepdown.py offers (--regime natr | turbulence | macd
    | awesome | psar | heikin_ashi | lppls, --min-hold, --lag). When it
    is off, the --defensive ETF (default XLP XLU USMV GLD) with the best
    trailing --rs-days return among those whose OWN NATR regime is calm
    -- a defensive that is itself crashing is not a refuge, which is what
    March 2020 did to utilities and low-volatility funds. None calm:
    cash, which earns the configured cash yield.

relative_strength
    Dual momentum over --universe (default QQQ RSP XLP USMV): the best
    trailing --rs-days return; cash when even the best is negative.
    Quant-trading's pair-trading spread logic, used to CHOOSE a leg
    rather than to trade one against the other (no short leg).

hrp
    Every --universe instrument at once, each sleeve's lot size scaled
    by hierarchical-risk-parity weights fitted on the first --warmup
    sessions only; results are measured from the session after.

Each held instrument runs as a regime sleeve through the real engine,
active only on the sessions assigned to it (research/strategies/
regime_sleeve_sizing.py; liquidated on the session it is rotated out of,
which needs and sets allow_signal_exit). Grid step and target are scaled
by each instrument's median daily range relative to the lead's, over the
warm-up, so a lot asks for a comparable move everywhere. P&L is added
into one account exactly as in leverage_stepdown.py: right for the
champion's fixed-dollar lots, approximate where a sleeve's standalone run
was cash-constrained. In hrp mode the sleeves run CONCURRENTLY, which
stretches that approximation further: total deployed capital can exceed
what one account would allow.

Every assignment uses closes through the PREVIOUS session; every regime
map is lagged one session. Nothing here has been run on real data.
"""

from __future__ import annotations

import argparse
import sys
from datetime import date
from itertools import pairwise
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from engine.core.config import BacktestConfig
from research.strategies.hrp import hrp_weights
from research.strategies.natr_regime import calm_by_date, daily_bars
from tools.leverage_stepdown import (
    FOCUS_YEARS,
    SleeveFactory,
    add_regime_args,
    build_regime,
    run_book,
    stitch,
    summarize,
)

CASH = "CASH"


def aligned_closes(frames: dict[str, pd.DataFrame], names: list[str]) -> pd.DataFrame:
    """Daily closes on the sessions every named instrument traded. Unlike
    turbulence_regime.basket_closes, one instrument is fine here: a
    single defensive candidate, or absolute momentum on one ETF."""
    return pd.DataFrame({n: daily_bars(frames[n])["close"] for n in names}).dropna(how="any")


def trailing_returns(closes: pd.DataFrame, days: int) -> pd.DataFrame:
    """Return over `days` sessions ending at the PREVIOUS session -- the
    value knowable at each session's open."""
    if days < 1:
        raise SystemExit(f"--rs-days must be >= 1, got {days}")
    return (closes / closes.shift(days) - 1.0).shift(1)


def assign_defensive(
    risk_on: dict[date, bool],
    lead: str,
    closes: pd.DataFrame,
    calm: dict[str, dict[date, bool]],
    days: int,
) -> dict[date, str]:
    rs = trailing_returns(closes, days)
    by_date = {ts.date(): row for ts, row in rs.iterrows()}
    out: dict[date, str] = {}
    for d in sorted(risk_on):
        if risk_on[d]:
            out[d] = lead
            continue
        best, best_ret = CASH, None
        row = by_date.get(d)
        if row is not None:
            for name in closes.columns:
                r = row[name]
                if pd.isna(r) or not calm.get(name, {}).get(d, False):
                    continue
                if best_ret is None or r > best_ret:
                    best, best_ret = name, r
        out[d] = best
    return out


def assign_relative_strength(closes: pd.DataFrame, days: int) -> dict[date, str]:
    rs = trailing_returns(closes, days).dropna(how="any")
    out: dict[date, str] = {}
    for ts, row in rs.iterrows():
        best = row.idxmax()
        out[ts.date()] = best if row[best] > 0 else CASH
    return out


def grid_scales(frames: dict[str, pd.DataFrame], lead: str, warmup: int) -> dict[str, float]:
    """Median daily (high-low)/close over the first `warmup` sessions,
    relative to the lead's -- in-sample only, so it is fixed before the
    measured window starts."""

    def median_range(frame: pd.DataFrame) -> float:
        d = daily_bars(frame).iloc[:warmup]
        return float(((d["high"] - d["low"]) / d["close"]).median())

    base = median_range(frames[lead])
    return {name: median_range(frame) / base for name, frame in frames.items()}


def count_switches(assignment: dict[date, str]) -> int:
    values = [assignment[d] for d in sorted(assignment)]
    return sum(1 for a, b in pairwise(values) if a != b)


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--mode", choices=("defensive", "relative_strength", "hrp"), default="defensive")
    p.add_argument("--config", default="config/best_known_2026-08-24.yaml")
    p.add_argument("--tqqq", default="TQQQ", help="the lead instrument (risk-on, and the champion)")
    p.add_argument("--qqq", default="QQQ", help="regime source when --regime-from qqq")
    p.add_argument("--defensive", nargs="+", default=["XLP", "XLU", "USMV", "GLD"])
    p.add_argument("--universe", nargs="+", default=["QQQ", "RSP", "XLP", "USMV"])
    p.add_argument("--rs-days", type=int, default=63)
    p.add_argument("--warmup", type=int, default=250)
    p.add_argument("--cash-yield", type=float, default=None)
    p.add_argument("--fill-model", choices=("close", "intrabar"), default="intrabar")
    p.add_argument(
        "--intrabar-fill", choices=("level", "open_or_level", "causal"), default="causal"
    )
    p.add_argument("--out", default="output/rotation")
    add_regime_args(p)
    args = p.parse_args(argv)

    from engine.warehouse.bars import load_frame

    cfg = BacktestConfig.from_yaml(args.config)
    if cfg.strategy.strategy_id != "hf_local_reference":
        raise SystemExit(f"{args.config} is not an hf_local_reference config")
    params = dict(cfg.strategy.strategy_params)
    step, target = cfg.grid.steps[0], cfg.grid.profit_targets[0]
    initial = cfg.backtest.initial_cash
    lead = args.tqqq

    names = [lead, *args.defensive] if args.mode == "defensive" else [lead, *args.universe]
    frames: dict[str, pd.DataFrame] = {}

    def load(name: str) -> pd.DataFrame:
        if name not in frames:
            frames[name] = load_frame(name)
            if frames[name].empty:
                raise SystemExit(f"No warehouse data for {name!r}; ingest it first.")
        return frames[name]

    for name in dict.fromkeys(names):
        load(name)
    scales = grid_scales(frames, lead, args.warmup)

    weights = None
    if args.mode == "defensive":
        source = load(lead if args.regime_from == "tqqq" else args.qqq)
        regime, desc = build_regime(args, source, load)
        calm = {name: calm_by_date(daily_bars(frames[name])) for name in args.defensive}
        closes = aligned_closes(frames, args.defensive)
        assignment = assign_defensive(regime, lead, closes, calm, args.rs_days)
        desc = f"defensive rotation; risk-on regime: {desc}"
    elif args.mode == "relative_strength":
        closes = aligned_closes(frames, args.universe)
        assignment = assign_relative_strength(closes, args.rs_days)
        desc = f"dual momentum over {'+'.join(args.universe)}, {args.rs_days}-session returns"
    else:
        closes = aligned_closes(frames, args.universe)
        fit = closes.iloc[: args.warmup + 1]
        weights = hrp_weights((fit / fit.shift(1) - 1.0).dropna())
        assignment = {ts.date(): "ALL" for ts in closes.index[args.warmup + 1 :]}
        desc = "HRP weights " + ", ".join(f"{n} {w:.2f}" for n, w in weights.items())
    if not assignment:
        raise SystemExit("no sessions to evaluate -- not enough data")
    start = pd.Timestamp(min(assignment), tz=frames[lead].index.tz)
    print(f"Rotation: {desc}")
    print(f"  {len(assignment)} sessions from {start.date()}")

    fill = (args.cash_yield, args.fill_model, args.intrabar_fill)
    curves = {}
    if weights is None:
        held = sorted({a for a in assignment.values() if a != CASH})
        shares = pd.Series(list(assignment.values())).value_counts(normalize=True) * 100
        print("  share of sessions: " + ", ".join(f"{k} {v:.1f}%" for k, v in shares.items()))
        print(
            f"  {count_switches(assignment)} switches (each one liquidates the outgoing sleeve)\n"
        )
        for name in held:
            active = {d: a == name for d, a in assignment.items()}
            s = scales[name]
            print(
                f"[{name}] active {sum(active.values())} sessions, grid scale {s:.3f}", flush=True
            )
            curves[name], _ = run_book(
                frames[name],
                cfg,
                SleeveFactory("calm", active),
                name,
                step * s,
                target * s,
                params,
                *fill,
            )
    else:
        n = len(weights)
        print()
        for name, w in weights.items():
            s = scales[name]
            sized = {**params, "per_lot_pct": params["per_lot_pct"] * w * n}
            print(f"[{name}] weight {w:.3f}, grid scale {s:.3f}", flush=True)
            curves[name], _ = run_book(
                frames[name],
                cfg,
                SleeveFactory("always", {}),
                name,
                step * s,
                target * s,
                sized,
                *fill,
            )
    print(f"[champion] {lead}", flush=True)
    champion, _ = run_book(
        frames[lead], cfg, SleeveFactory("always", {}), lead, step, target, params, *fill
    )

    books = {
        "champion": champion,
        "rotation": stitch(initial, list(curves.values())) if curves else None,
    }
    if books["rotation"] is None:
        raise SystemExit("the rotation never held an instrument")
    for name in dict.fromkeys(names):
        books[f"{name} b&h"] = frames[name]["close"].astype(float)
    stats = {name: summarize(curve, start) for name, curve in books.items()}

    print(
        f"\n{'=' * 78}\n{'book':<12} {'CAGR':>8} {'maxDD':>8} {'CAGR/DD':>8} {'worst yr':>9} {'total':>10}"
    )
    for name, st in stats.items():
        print(
            f"{name:<12} {st['cagr_pct']:>7.2f}% {st['max_dd_pct']:>7.2f}% "
            f"{st['cagr_over_dd']:>8.3f} {st['worst_year_pct']:>8.2f}% {st['total_return_pct']:>9.1f}%"
        )
    annual = pd.DataFrame({name: st["annual"] for name, st in stats.items()})
    print(f"\n{'=' * 78}\nCalendar-year returns (%), from {start.date()}:")
    print(annual.round(2).to_string())
    focus = [y for y in FOCUS_YEARS if y in annual.index]
    if focus:
        diff = annual.loc[focus, "rotation"] - annual.loc[focus, "champion"]
        print(
            "\nrotation minus champion in the correction years: "
            + ", ".join(f"{y} {d:+.2f}pp" for y, d in diff.items())
        )

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    tag = f"{args.mode}_{args.regime if args.mode == 'defensive' else 'na'}_rs{args.rs_days}"
    pd.DataFrame(
        {name: {k: v for k, v in st.items() if k != "annual"} for name, st in stats.items()}
    ).T.to_csv(out / f"summary_{tag}.csv")
    annual.to_csv(out / f"annual_{tag}.csv")
    pd.Series(assignment).sort_index().to_csv(out / f"assignment_{tag}.csv", header=["holding"])
    print(f"Wrote {out}/summary_{tag}.csv, annual_{tag}.csv, assignment_{tag}.csv")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
