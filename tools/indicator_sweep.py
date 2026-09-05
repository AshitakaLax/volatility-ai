#!/usr/bin/env python
"""Brute-force every TA-Lib indicator against two instruments. See plan.md.

TQQQ and RSP are INDEPENDENT OBJECTIVES and are never ranked together.
TQQQ is held for return and its strategy already beats buy-and-hold by
2.9 points, so its question is how much more. RSP is held for the
diversification of 500 equal-weighted names and nothing has beaten owning
it, so its question is whether anything makes owning it safer at an
acceptable price. A combined leaderboard would be dominated by TQQQ's
larger numbers and would answer the RSP question with the TQQQ answer.

--------------------------------------------------------------------
THE LOG IS THE POINT

These runs are long, this box has had a memory incident from overlapping
sweeps, and a run that loses hours to a crash gets abandoned rather than
restarted. So every completed configuration is appended to a JSONL file
and fsynced before the next one starts -- the same discipline as
FileConfNumJournal in src/fidelity_placing_broker.py, and for the same
reason: a buffered handle is exactly how a journal loses its last entry.

--resume is the DEFAULT. The key is a hash of (instrument, role,
indicator, output, variant), never a row index -- an index changes the
moment the inventory grows, which would silently re-run everything or,
worse, skip the wrong things.

--------------------------------------------------------------------
WHAT IS AND IS NOT DEFENDED AGAINST

Lookahead: every signal is computed from data through day t and applied
to day t+1. Thresholds are TRAILING medians, never full-sample
quantiles.

Warmup: the first warmup_bars are dropped by our own rule, because three
well-known libraries emit confident wrong values through their first
hundred bars rather than NaN. See src/indicator_library.

Multiple comparisons: NOT defended against here, and cannot be. Running
~900 configurations against a fixed bar WILL produce winners by chance --
roughly 45 at a 5% threshold. That is why every row carries both
chronological halves and why --report prints the distribution rather than
the leaderboard. Reading only the top row of this output is the one
mistake that makes the whole exercise worse than useless.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import time
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
warnings.filterwarnings("ignore")

from src.indicator_library import (
    available,
    compute,
    exposure,
    load_bars,
    signals,
    warmup_bars,
)

TRADING_DAYS = 252

# The bar per instrument, computed once from these exact files at DAILY
# resolution, and written down rather than recomputed per experiment.
# plan.md carries the minute-resolution figures, which differ -- 39.29%
# against 39.15% on TQQQ -- and Stage 1 is judged against these.
INSTRUMENTS = {
    "TQQQ": {
        "path": "data/TQQQ_1Min_sip_all_2016-01-01_2026-08-21.csv",
        "bh_cagr": 39.15,
        "bh_dd": -81.68,
        "bh_ret_dd": 0.479,
        "objective": "return",
    },
    "RSP": {
        "path": "data/RSP_1Min_sip_all_rthuniform_2016-01-01_2026-08-30.csv",
        "bh_cagr": 12.46,
        "bh_dd": -39.11,
        "bh_ret_dd": 0.319,
        "objective": "risk",
    },
}


def config_id(*parts: str) -> str:
    return hashlib.sha256("|".join(parts).encode()).hexdigest()[:16]


def metrics(equity: pd.Series) -> dict:
    """Everything a row needs, including both chronological halves."""
    years = (equity.index[-1] - equity.index[0]).days / 365.25
    if years <= 0 or equity.iloc[0] <= 0:
        return {}
    cagr = (equity.iloc[-1] / equity.iloc[0]) ** (1 / years) - 1
    underwater = equity / equity.cummax() - 1
    dd = underwater.min()
    daily = equity.pct_change().dropna()
    sharpe = float(daily.mean() / daily.std() * np.sqrt(TRADING_DAYS)) if daily.std() else np.nan
    annual = equity.resample("YE").last().pct_change().dropna()

    # The halves are not decoration. An indicator whose halves disagree in
    # sign is describing one regime, not stating a rule, and with ~900
    # configurations that distinction is the main defence against noise.
    mid = equity.index[len(equity) // 2]
    halves = []
    for seg in (equity[:mid], equity[mid:]):
        y = (seg.index[-1] - seg.index[0]).days / 365.25
        halves.append(float((seg.iloc[-1] / seg.iloc[0]) ** (1 / y) - 1) * 100 if y > 0 else np.nan)

    return {
        "cagr": round(float(cagr) * 100, 4),
        "max_dd": round(float(dd) * 100, 4),
        "ulcer": round(float(np.sqrt((underwater**2).mean()) * 100), 4),
        "sharpe": round(sharpe, 4),
        "ret_dd": round(float(cagr) * 100 / abs(float(dd) * 100), 4) if dd else None,
        "worst_year": round(float(annual.min()) * 100, 4) if len(annual) else None,
        "neg_years": int((annual < 0).sum()) if len(annual) else None,
        "first_half_cagr": round(halves[0], 4),
        "second_half_cagr": round(halves[1], 4),
        "halves_agree": bool(halves[0] > 0) == bool(halves[1] > 0),
    }


def run_weights(
    close: pd.Series, weight: pd.Series, cash_yield: float, cost_pct: float
) -> pd.Series:
    """Equity for a weight series, held over the NEXT day.

    The shift is the difference between a measurement and a look at the
    answer, and it is one line, so it is written explicitly here rather
    than assumed to have happened upstream.
    """
    weight = weight.reindex(close.index).shift(1).fillna(0.0).clip(0.0, 1.0)
    asset = close.pct_change().fillna(0.0)
    daily_cash = (1 + cash_yield) ** (1 / TRADING_DAYS) - 1
    gross = weight * asset + (1 - weight) * daily_cash
    turnover = weight.diff().abs().fillna(0.0)
    return (1 + gross - turnover * cost_pct).cumprod()


def configurations(include_patterns: bool = True):
    """Every (instrument, indicator, output, role, variant) to evaluate."""
    inventory = available(include_patterns=include_patterns)
    for symbol in INSTRUMENTS:
        for ind in inventory:
            for out in ind.outputs:
                yield symbol, ind, out, "regime", "above" if not ind.is_pattern else "bull"
                yield symbol, ind, out, "regime", "below" if not ind.is_pattern else "bear"
                if not ind.is_pattern:
                    yield symbol, ind, out, "sizing", "rank"


class Journal:
    """Append-only, fsynced per row. Survives the process dying."""

    def __init__(self, path: str) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def done_ids(self) -> set[str]:
        if not self.path.exists():
            return set()
        out = set()
        with open(self.path, encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                try:
                    out.add(json.loads(line)["config_id"])
                except (json.JSONDecodeError, KeyError):
                    continue  # a torn final line from a hard kill
        return out

    def write(self, row: dict) -> None:
        with open(self.path, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(row, sort_keys=True) + "\n")
            fh.flush()
            os.fsync(fh.fileno())


def stage1(args) -> int:
    journal = Journal(args.out)
    done = journal.done_ids() if args.resume else set()
    todo = list(configurations(not args.no_patterns))
    total = len(todo)

    cache: dict[str, pd.DataFrame] = {}
    values_cache: dict[tuple[str, str], pd.DataFrame] = {}

    print(f"[sweep] {total} configurations across {len(INSTRUMENTS)} instruments")
    if done:
        print(f"[sweep] resuming: {len(done)} already complete, skipping them")
    started = time.time()
    ran = skipped = failed = 0
    best: dict[str, tuple[float, str]] = {}

    for i, (symbol, ind, out, role, variant) in enumerate(todo, 1):
        cid = config_id(symbol, ind.name, out, role, variant)
        if cid in done:
            skipped += 1
            continue

        spec = INSTRUMENTS[symbol]
        try:
            if symbol not in cache:
                cache[symbol] = load_bars(spec["path"])
            bars = cache[symbol]

            key = (symbol, ind.name)
            if key not in values_cache:
                values_cache[key] = compute(ind, bars)
            values = values_cache[key][out]

            skip = warmup_bars(ind)
            if role == "regime":
                sig = signals(values, ind)[variant]
                weight = sig.astype(float)
            else:
                weight = exposure(values)

            close = bars["close"].iloc[skip:]
            weight = weight.iloc[skip:]
            if len(close) < TRADING_DAYS * 2 or not np.isfinite(weight).any():
                raise ValueError("insufficient usable history after warmup")

            equity = run_weights(close, weight, args.cash_yield, args.cost_pct)
            m = metrics(equity)
            if not m:
                raise ValueError("degenerate equity curve")

            row = {
                "config_id": cid,
                "instrument": symbol,
                "objective": spec["objective"],
                "indicator": ind.name,
                "group": ind.group,
                "output": out,
                "role": role,
                "variant": variant,
                "warmup_bars": skip,
                "in_market_pct": round(float(weight.mean()) * 100, 2),
                "switches": int((weight.diff().abs() > 1e-9).sum()),
                "bh_cagr": spec["bh_cagr"],
                "bh_ret_dd": spec["bh_ret_dd"],
                "beats_bar": (
                    m["cagr"] > spec["bh_cagr"]
                    if spec["objective"] == "return"
                    else (m["ret_dd"] or 0) > spec["bh_ret_dd"]
                ),
                **m,
            }
            journal.write(row)
            ran += 1

            score = m["cagr"] if spec["objective"] == "return" else (m["ret_dd"] or 0)
            if symbol not in best or score > best[symbol][0]:
                best[symbol] = (score, f"{ind.name}.{out} {role}/{variant}")

            elapsed = time.time() - started
            rate = elapsed / max(ran, 1)
            eta = rate * (total - i) / 3600
            print(
                f"[{i:>4}/{total}] {symbol:<5} {ind.name:<14} {out:<12} {role}/{variant:<6} "
                f"CAGR {m['cagr']:7.2f}%  DD {m['max_dd']:7.2f}%  "
                f"Sh {m['sharpe']:5.2f}  ({rate:.2f}s, eta {eta:.2f}h)",
                flush=True,
            )
        except Exception as exc:
            # One indicator failing on a degenerate window must not end a
            # long run. The row records it and the sweep continues; a
            # stage that ends with a handful of failures is a result,
            # one that dies partway through is nothing.
            failed += 1
            journal.write(
                {
                    "config_id": cid,
                    "instrument": symbol,
                    "indicator": ind.name,
                    "output": out,
                    "role": role,
                    "variant": variant,
                    "error": f"{type(exc).__name__}: {exc}"[:200],
                }
            )

        if ran and ran % 30 == 0:
            mins = (time.time() - started) / 60
            leaders = "  ".join(f"{k}:{v[1]} ({v[0]:.2f})" for k, v in best.items())
            print(
                f"[sweep] {ran} run, {failed} failed, {mins:.1f} min | best {leaders}", flush=True
            )

    print(
        f"\n[sweep] complete: {ran} run, {skipped} skipped, {failed} failed, "
        f"{(time.time() - started) / 60:.1f} min -> {args.out}"
    )
    return 0


# Stage 2's return floor per instrument. Stage 1 showed 96 of 392 RSP
# configurations "beating the bar" against 5 of 392 on TQQQ -- not
# because RSP is easier, but because a return/drawdown of 0.319 is
# trivially beaten by de-risking, and a book that sits in cash beats it
# without doing anything useful. The floor makes the objective say what
# it always meant: cut the drawdown WITHOUT surrendering the return.
# It collapses 96 survivors to 3.
RETURN_FLOOR = {"TQQQ": 39.15, "RSP": 11.0}


def survivors(path: str, min_market: float = 20.0) -> pd.DataFrame:
    """Stage 1 rows that earned a parameter sweep."""
    with open(path, encoding="utf-8") as fh:
        rows = [json.loads(line) for line in fh if line.strip()]
    d = pd.DataFrame([r for r in rows if "error" not in r])
    d = d[d.in_market_pct >= min_market]
    keep = d.beats_bar & d.halves_agree
    floor = d.instrument.map(RETURN_FLOOR).fillna(0)
    return d[keep & (d.cagr >= floor)]


def param_grid(ind) -> list[dict]:
    """Parameter settings to try for one indicator.

    Periods scale multiplicatively rather than by fixed steps, because
    the question is whether an effect holds across a RANGE, and 12 to 16
    on a 14-period default proves far less than 7 to 42 does.

    Non-period parameters (matype, nbdev) stay at their defaults. Stage 4
    is where axes get combined, and sweeping them here would multiply the
    space for exactly the reason plan.md refuses to elsewhere.
    """
    periods = {k: v for k, v in ind.params.items() if "period" in k.lower()}
    if not periods:
        return [{}]
    out: list[dict] = []
    for scale in (0.5, 0.75, 1.0, 1.5, 2.0, 3.0):
        setting = {k: max(2, round(v * scale)) for k, v in periods.items()}
        # A fast/slow pair that crosses is not a slower indicator, it is
        # an undefined one.
        if (
            "fastperiod" in setting
            and "slowperiod" in setting
            and setting["fastperiod"] >= setting["slowperiod"]
        ):
            continue
        if setting not in out:
            out.append(setting)
    return out


def ridge_scores(frame: pd.DataFrame, metric: str) -> pd.DataFrame:
    """How each setting's ADJACENT neighbours did.

    plan.md: "a real parameter effect is a ridge, not a point". A setting
    whose neighbours in parameter space also perform is describing
    something about the market; one surrounded by mediocrity is the
    maximum of a noisy sample and will not survive new data.

    THE FIRST VERSION OF THIS COMPARED AGAINST THE MEAN OF EVERY OTHER
    SETTING, which is not a neighbourhood -- it is "better than the
    average of a grid that spans periods 7 to 42 and lookbacks 100 to
    500". It reported LINEARREG at +20 CAGR points of "ridge" and
    PLUS_DM at +0.4, which made the fragile result look stronger than
    the robust one. Adjacency in BOTH axes is what the plan meant:
    neighbours are the settings one step away in period at the same
    lookback, and one step away in lookback at the same period.
    """
    frame = frame.copy()
    frame["grid_period"] = frame["params"].apply(
        lambda p: next(iter(json.loads(p).values())) if json.loads(p) else 0
    )
    periods = sorted(frame["grid_period"].unique())
    lookbacks = sorted(frame["lookback"].unique())
    lookup = {(r.grid_period, r.lookback): getattr(r, metric) for r in frame.itertuples()}

    means, counts = [], []
    for row in frame.itertuples():
        pi, li = periods.index(row.grid_period), lookbacks.index(row.lookback)
        vals = []
        for dp, dl in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            p, lb = pi + dp, li + dl
            if 0 <= p < len(periods) and 0 <= lb < len(lookbacks):
                v = lookup.get((periods[p], lookbacks[lb]))
                if v is not None:
                    vals.append(v)
        means.append(round(sum(vals) / len(vals), 4) if vals else float("nan"))
        counts.append(len(vals))

    frame["neighbour_mean"] = means
    frame["neighbours"] = counts
    frame["ridge"] = (frame[metric] - frame["neighbour_mean"]).round(4)
    return frame.drop(columns=["grid_period"])


def surface(frame: pd.DataFrame, metric: str, bar: float) -> str:
    """One line summarising the whole parameter surface.

    The fraction of settings that clear the bar is the honest headline.
    A result present in 1 of 18 cells and one present in 18 of 18 are
    different findings however similar their best rows look, and the
    best row alone cannot tell them apart.
    """
    n = len(frame)
    over = int((frame[metric] >= bar).sum())
    return f"{over}/{n} settings clear the bar"


def stage2(args) -> int:
    """Full parameter grid over every Stage 1 survivor."""
    surv = survivors(args.from_path or args.out, args.min_market)
    if surv.empty:
        print("No Stage 1 survivors to sweep. Run --stage 1 first.", file=sys.stderr)
        return 1

    inventory = {i.name: i for i in available()}
    seen = surv[["instrument", "indicator", "output", "role", "variant"]].drop_duplicates()
    print(f"[stage2] {len(seen)} surviving signals from Stage 1")
    for inst, grp in seen.groupby("instrument"):
        print(f"[stage2]   {inst}: {', '.join(sorted(set(grp.indicator)))}")

    journal = Journal(args.out2)
    done = journal.done_ids() if args.resume else set()
    cache: dict[str, pd.DataFrame] = {}
    written = 0

    for _, row in seen.iterrows():
        ind = inventory.get(row.indicator)
        if ind is None:
            continue
        spec = INSTRUMENTS[row.instrument]
        if row.instrument not in cache:
            cache[row.instrument] = load_bars(spec["path"])
        bars = cache[row.instrument]

        collected = []
        for setting in param_grid(ind):
            for lookback in args.lookbacks:
                cid = config_id(
                    row.instrument,
                    ind.name,
                    row.output,
                    row.role,
                    row.variant,
                    json.dumps(setting, sort_keys=True),
                    str(lookback),
                )
                if cid in done:
                    continue
                try:
                    values = compute(ind, bars, **setting)[row.output]
                    skip = max(warmup_bars(ind, **setting), lookback)
                    if row.role == "regime":
                        weight = signals(values, ind, lookback=lookback)[row.variant].astype(float)
                    else:
                        weight = exposure(values, lookback=lookback)
                    close = bars["close"].iloc[skip:]
                    weight = weight.iloc[skip:]
                    if len(close) < TRADING_DAYS * 2:
                        raise ValueError("insufficient history after warmup")
                    m = metrics(run_weights(close, weight, args.cash_yield, args.cost_pct))
                    if not m:
                        raise ValueError("degenerate curve")
                    base = next(iter(setting.values())) if setting else 0
                    default = next(iter(ind.params.values())) if ind.params else 0
                    out_row = {
                        "config_id": cid,
                        "instrument": row.instrument,
                        "indicator": ind.name,
                        "output": row.output,
                        "role": row.role,
                        "variant": row.variant,
                        "params": json.dumps(setting, sort_keys=True),
                        "lookback": lookback,
                        "scale": round(base / default, 3) if default else 1.0,
                        "in_market_pct": round(float(weight.mean()) * 100, 2),
                        **m,
                    }
                    journal.write(out_row)
                    collected.append(out_row)
                    written += 1
                except Exception as exc:
                    journal.write({"config_id": cid, "error": f"{type(exc).__name__}: {exc}"[:200]})

        if collected:
            metric = "cagr" if spec["objective"] == "return" else "ret_dd"
            f = ridge_scores(pd.DataFrame(collected), metric)
            best = f.loc[f[metric].idxmax()]
            bar = spec["bh_cagr"] if spec["objective"] == "return" else spec["bh_ret_dd"]
            verdict = "RIDGE" if abs(best["ridge"]) < abs(best[metric]) * 0.25 else "spike"
            print(
                f"[stage2] {row.instrument:<5} {ind.name:<16} {row.role}/{row.variant:<6} "
                f"best {metric} {best[metric]:7.3f} at {best['params']} lb={best['lookback']} | "
                f"neighbours {best['neighbour_mean']:7.3f} ({verdict}) | "
                f"{surface(f, metric, bar)}",
                flush=True,
            )

    print(f"\n[stage2] {written} rows -> {args.out2}")
    return 0


def report(path: str, min_market: float = 20.0) -> int:
    with open(path, encoding="utf-8") as fh:
        rows = [json.loads(line) for line in fh if line.strip()]
    ok = pd.DataFrame([r for r in rows if "error" not in r])
    errs = [r for r in rows if "error" in r]
    if ok.empty:
        print("No successful rows.")
        return 1

    # A CONFIGURATION THAT IS NEVER INVESTED IS NOT A STRATEGY.
    #
    # The first run of this report was topped, on RSP, by twelve
    # candlestick patterns showing return/drawdown near 118 -- which was
    # 4.07% CAGR over a 0.03% drawdown. Both numbers are artifacts of
    # sitting in cash: 4.07% IS the cash yield, and a book that is never
    # in the market cannot draw down. Ranking by return/drawdown rewards
    # that perfectly, so the metric is DEGENERATE at low exposure rather
    # than merely noisy.
    #
    # Patterns fire on a handful of bars a year so almost all of them
    # land here, but the floor applies to every role equally rather than
    # excluding a family by name -- the problem is the exposure, not the
    # indicator, and a continuous signal that collapses to 3% invested
    # deserves the same treatment.
    live = ok[ok.get("in_market_pct", 0) >= min_market]
    dropped = len(ok) - len(live)
    print(f"{len(ok)} results, {len(errs)} failures")
    print(
        f"{dropped} dropped for being invested under {min_market:.0f}% of the time "
        "(cash in disguise -- see the note in report())" + chr(10)
    )
    ok = live
    for symbol, spec in INSTRUMENTS.items():
        sub = ok[ok.instrument == symbol]
        if sub.empty:
            continue
        metric = "cagr" if spec["objective"] == "return" else "ret_dd"
        bar = spec["bh_cagr"] if spec["objective"] == "return" else spec["bh_ret_dd"]

        print(f"=== {symbol} -- objective: {spec['objective']} -- bar: {bar} ({metric}) ===")
        # THE DISTRIBUTION FIRST. With ~450 configurations per instrument
        # the top row is the maximum of 450 draws and is biased upward by
        # construction; the shape of the whole set is what says whether
        # anything real is present.
        d = sub[metric].describe(percentiles=[0.5, 0.9, 0.99])
        print(
            f"  distribution: median {d['50%']:.3f}  p90 {d['90%']:.3f}  "
            f"p99 {d['99%']:.3f}  max {d['max']:.3f}"
        )
        beat = sub[sub.beats_bar]
        print(f"  beat the bar: {len(beat)} of {len(sub)} ({len(beat) / len(sub) * 100:.1f}%)")
        agree = beat[beat.halves_agree]
        print(f"  ...and both halves agree in sign: {len(agree)}")
        print()
        cols = [
            "indicator",
            "output",
            "role",
            "variant",
            "cagr",
            "max_dd",
            "sharpe",
            "ret_dd",
            "first_half_cagr",
            "second_half_cagr",
        ]
        top = agree.nlargest(12, metric) if len(agree) else sub.nlargest(12, metric)
        print(top[cols].to_string(index=False, float_format=lambda v: f"{v:8.2f}"))
        print()
    return 0


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description="Brute-force indicator sweep. See plan.md.")
    p.add_argument("--stage", type=int, default=1)
    p.add_argument("--from", dest="from_path", help="Stage 1 JSONL to take survivors from.")
    p.add_argument("--out2", default="output/indicator_stage2.jsonl")
    p.add_argument("--lookbacks", type=int, nargs="+", default=[100, 250, 500])
    p.add_argument("--out", default="output/indicator_sweep.jsonl")
    p.add_argument("--report", metavar="JSONL")
    p.add_argument("--cost-pct", type=float, default=0.0005)
    p.add_argument("--cash-yield", type=float, default=0.04)
    p.add_argument("--no-patterns", action="store_true", help="Skip the 61 candlestick patterns.")
    p.add_argument(
        "--min-market",
        type=float,
        default=20.0,
        help="Drop configurations invested less than this percent of the time. They "
        "score brilliantly on return/drawdown by never being exposed.",
    )
    p.add_argument("--no-resume", dest="resume", action="store_false")
    p.set_defaults(resume=True)
    args = p.parse_args(argv)

    if args.report:
        return report(args.report, args.min_market)
    if args.stage == 1:
        return stage1(args)
    if args.stage == 2:
        return stage2(args)
    print(f"Stage {args.stage} is not implemented yet; see plan.md.", file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main())
