#!/usr/bin/env python
"""
The risk governor's measurement (docs/research/risk-governor.md): do outside
series -- implied volatility, credit, the leading sector, the index trend,
the OFR stress index -- improve the Daily Ultimate reserve, and in what form?

    python tools/probe_risk_governor.py --stage forms    --out DIR [--jobs N]
    python tools/probe_risk_governor.py --stage frontier --out DIR
    python tools/probe_risk_governor.py --stage robust   --out DIR
    python tools/probe_risk_governor.py --stage null     --out DIR
    python tools/probe_risk_governor.py --stage stress   --out DIR
    python tools/probe_risk_governor.py --stage daily    --out DIR
    python tools/probe_risk_governor.py --stage daily-null   --out DIR
    python tools/probe_risk_governor.py --stage daily-stress --out DIR
    python tools/probe_risk_governor.py --report DIR

Every run is the reserve configuration (tools/probe_daily_reserve.CHOSEN) on
TQQQ, measured exactly as tools/probe_daily_ultimate.py measures one: causal
intrabar fills, dynamic slippage, no cash yield, from 2016-01-04, scored from
2017-01-03. `--external DIR` names the outside series (default: the
governor's own directory, data/external/, written by
tools/refresh_external.py). A run already in DIR/results.jsonl is skipped.

--------------------------------------------------------------------
THE STAGES

  forms     the same warnings used three ways: ANDed into the regime as a
            veto, ORed in as an override ("stay in while the outside reads
            benign"), and as a pause on new buying. Only the pause helps.
  frontier  the pause (CORE_SIGNALS, CORE_MIN_VOTES) against no governor at
            four lot sizes: is the gain a lot-size artefact?
  robust    one change at a time: the vote threshold, a wider signal set,
            each core signal left out, each signal alone.
  null      the core pause map moved in time by NULL_SHIFTS random offsets:
            the same number of paused sessions in the same runs, at the
            wrong dates. Where the real map sits among them is the evidence
            that the dates matter.
  stress    with and without the governor under tools/stress_paths.py's
            paths. The fund's bars are the stressed ones; the outside series
            are history's (and `twice` moves the fund's dates after its
            second bear), so this shows the pause does no harm on a worse
            path, not what the outside series would have read there.

The `daily*` stages repeat the measurement on DAILY ULTIMATE itself
(config/daily_ultimate_tqqq.yaml: fixed 0.8% lots, reversal lots while
turbulent), the book the paper trial runs, in two forms: `plain`, as it was
researched, and `throttle`, with the drawdown throttle paper-ultimate's own
risk section applies to whatever it trades.
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from concurrent.futures import ProcessPoolExecutor, as_completed
from datetime import date
from pathlib import Path
from typing import Any

_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from research.strategies.risk_governor import (
    CORE_MIN_VOTES,
    CORE_SIGNALS,
    SIGNALS,
    RiskGovernor,
    external_directory,
)
from tools import probe_daily_reserve as dr
from tools import probe_daily_ultimate as du
from tools import stress_paths

FUND = dr.FUND
LOTS = (0.0025, 0.003, 0.0035, 0.0045)
WIDE_SIGNALS = (*CORE_SIGNALS, "dxy_up", "move_hi", "nfci_tight")
NULL_SHIFTS = 40
NULL_SEED = 20261110
STRESSES = (*stress_paths.SCENARIOS, "top")
HALVES = (("2017-21", None, du.SPLIT), ("2022 on", du.SPLIT, None))


# --------------------------------------------------------------- the plan


def governed(
    external: Path,
    signals=CORE_SIGNALS,
    min_votes: int = CORE_MIN_VOTES,
    lot: float | None = None,
    **over,
) -> dict:
    """The reserve configuration with the governor reading `external`."""
    return reserve(
        lot,
        params={
            "caution_min_votes": min_votes,
            "caution_signals": ",".join(signals),
            "caution_dir": str(external),
            **over.pop("params", {}),
        },
        **over,
    )


def reserve(lot: float | None = None, **over) -> dict:
    cell = list(dr.CHOSEN)
    if lot is not None:
        cell[0] = lot
    return dr.reserve(*cell, **over)


def _spec(stage: str, name: str, config: dict, **meta) -> dict:
    return du._spec(stage, du._name(stage, "|", name), FUND, config, **meta)


def plan_frontier(external: Path) -> list[dict]:
    out = []
    for lot in LOTS:
        out.append(_spec("frontier", f"lot{lot} off", reserve(lot), lot=lot, governor="off"))
        out.append(
            _spec(
                "frontier", f"lot{lot} core", governed(external, lot=lot), lot=lot, governor="core"
            )
        )
    return out


def plan_robust(external: Path) -> list[dict]:
    out = [_spec("robust", "off", reserve(), change="no governor")]

    def add(name: str, signals, votes: int) -> None:
        out.append(
            _spec("robust", name, governed(external, signals, votes), change=name, votes=votes)
        )

    for votes in range(2, len(CORE_SIGNALS) + 1):
        add(f"core votes>={votes}", CORE_SIGNALS, votes)
    for votes in (4, 5, 6):
        add(f"wide votes>={votes}", WIDE_SIGNALS, votes)
    for left_out in CORE_SIGNALS:
        rest = tuple(s for s in CORE_SIGNALS if s != left_out)
        add(f"without {left_out} votes>=3", rest, 3)
        add(f"without {left_out} votes>=4", rest, 4)
    for name in SIGNALS:
        add(f"alone {name}", (name,), 1)
    return out


def shifted_maps(paused: list[bool], days: list[date], n: int, seed: int) -> list[dict]:
    """`n` copies of a paused series moved round its own calendar by a
    random number of sessions (at least a year from where it was): the
    same paused sessions in the same runs, on other dates."""
    rng = random.Random(seed)
    size = len(paused)
    if size < 3 * 252:
        raise SystemExit("too short a history for the null stage")
    maps = []
    for _ in range(n):
        shift = rng.randrange(252, size - 252)
        maps.append({days[i]: True for i in range(size) if paused[(i - shift) % size]})
    return maps


def plan_null(external: Path) -> list[dict]:
    table = RiskGovernor.from_directory(external).table()
    table = table[table.index >= du.START]
    days = [ts.date() for ts in table.index]
    paused = [bool(v) for v in table["paused"]]
    out = [
        _spec("null", "real", governed(external), shift="real"),
        _spec("null", "off", reserve(), shift="off"),
    ]
    for i, mapping in enumerate(shifted_maps(paused, days, NULL_SHIFTS, NULL_SEED)):
        config = reserve(params={"caution_by_date": mapping})
        out.append(_spec("null", f"shift {i:02d}", config, shift=i))
    return out


def plan_stress(external: Path) -> list[dict]:
    out = []
    for lot in (LOTS[0], LOTS[2]):
        for label, config in (("off", reserve(lot)), ("core", governed(external, lot=lot))):
            for stress in STRESSES:
                spec = _spec(
                    "stress", f"lot{lot} {label} {stress}", config, lot=lot, governor=label
                )
                spec["meta"]["stress"] = stress
                out.append(dr._under(spec, stress))
    return out


# -- Daily Ultimate: the pinned configuration, plain and under the throttle

BOOKS = ("plain", "throttle")
DAILY_VOTES = (3, CORE_MIN_VOTES)


def daily(book: str, **params) -> dict:
    """config/daily_ultimate_tqqq.yaml, `params` added to its strategy's;
    `throttle` adds the reserve's drawdown throttle, as paper-ultimate does."""
    if book not in BOOKS:
        raise ValueError(f"book must be one of {BOOKS}, got {book!r}")
    config = dr._pinned_config()
    config["strategy"]["strategy_params"] = {**config["strategy"]["strategy_params"], **params}
    if book == "throttle":
        config["risk"] = {**config.get("risk", {}), **dr.THROTTLE}
    return config


def daily_governed(book: str, external: Path, min_votes: int = CORE_MIN_VOTES) -> dict:
    return daily(
        book,
        caution_min_votes=min_votes,
        caution_signals=",".join(CORE_SIGNALS),
        caution_dir=str(external),
    )


def plan_daily(external: Path) -> list[dict]:
    out = []
    for book in BOOKS:
        out.append(_spec("daily", f"{book} off", daily(book), book=book, governor="off"))
        for votes in DAILY_VOTES:
            out.append(
                _spec(
                    "daily",
                    f"{book} core>={votes}",
                    daily_governed(book, external, votes),
                    book=book,
                    governor=f"core>={votes}",
                )
            )
    return out


def plan_daily_null(external: Path) -> list[dict]:
    table = RiskGovernor.from_directory(external).table()
    table = table[table.index >= du.START]
    days = [ts.date() for ts in table.index]
    paused = [bool(v) for v in table["paused"]]
    maps = shifted_maps(paused, days, NULL_SHIFTS, NULL_SEED)
    out = []
    for book in BOOKS:
        real = daily_governed(book, external)
        out.append(_spec("daily-null", f"{book} real", real, book=book, shift="real"))
        out.append(_spec("daily-null", f"{book} off", daily(book), book=book, shift="off"))
        for i, mapping in enumerate(maps):
            config = daily(book, caution_by_date=mapping)
            out.append(_spec("daily-null", f"{book} shift {i:02d}", config, book=book, shift=i))
    return out


def plan_daily_stress(external: Path) -> list[dict]:
    out = []
    for book in BOOKS:
        for label, config in (("off", daily(book)), ("core", daily_governed(book, external))):
            for stress in STRESSES:
                spec = _spec(
                    "daily-stress", f"{book} {label} {stress}", config, book=book, governor=label
                )
                spec["meta"]["stress"] = stress
                out.append(dr._under(spec, stress))
    return out


# -- forms: the warnings as a veto and as an override of the NATR regime


def governed_regime(daily, veto: dict | None = None, allow: dict | None = None) -> dict:
    """The reserve's own regime -- NATR(14) against its 100-session median,
    the 50% / 250-session bear filter, a 5-session hold -- with an outside
    flag forced into the raw reading before the hold: `veto` sessions read
    turbulent, `allow` sessions calm (a veto wins). {date: calm}."""
    from research.strategies.natr_regime import IncrementalNatrRegime

    veto, allow = veto or {}, allow or {}

    class Governed(IncrementalNatrRegime):
        def _open_session(self, day):
            if self._pending is not None:
                if allow.get(day, False):
                    self._pending = True
                if veto.get(day, False):
                    self._pending = False
            super()._open_session(day)

    buy = du.BUY
    regime = Governed(
        period=buy["natr_period"],
        lookback=buy["natr_lookback"],
        min_hold=buy["regime_min_hold"],
        bear_dd=buy["bear_dd"],
        bear_window=buy["bear_window"],
    )
    out = {}
    for ts, high, low, close in zip(
        daily.index, daily["high"], daily["low"], daily["close"], strict=True
    ):
        regime.observe(ts, float(high), float(low), float(close))
        if regime.calm is not None:
            out[ts.date()] = bool(regime.calm)
    return out


def _session_bars():
    import pandas as pd

    from engine.warehouse.bars import load_frame
    from research.strategies.natr_regime import daily_bars

    bars = load_frame(FUND)
    bars = bars[bars.index >= pd.Timestamp(du.START, tz="UTC")]
    ny = bars.index.tz_convert(du.TZ)
    minutes = ny.hour * 60 + ny.minute
    return daily_bars(bars[(minutes >= 570) & (minutes < 960)])


def plan_forms(external: Path) -> list[dict]:
    names = (*CORE_SIGNALS, "term_flat")
    table = RiskGovernor.from_directory(external, signals=names, min_votes=1).table()
    daily = _session_bars()

    def flags(column) -> dict:
        return {ts.date(): True for ts, v in column.items() if v}

    core_votes = table[list(CORE_SIGNALS)].sum(axis=1)
    raised = {name: flags(table[name] == 1.0) for name in names}
    raised["core>=4"] = flags(core_votes >= CORE_MIN_VOTES)
    # "Benign": the index above its trend, and none of the named warnings.
    benign = {
        "trend": flags(table["trend100"] == 0.0),
        "trend+term": flags((table["trend100"] == 0.0) & (table["term_flat"] == 0.0)),
        "trend+vxn": flags((table["trend100"] == 0.0) & (table["vxn_hi"] == 0.0)),
        "no core warning": flags((core_votes == 0) & (table["known"] >= len(CORE_SIGNALS))),
    }
    out = [_spec("forms", "off", reserve(), form="off")]
    for name, mapping in raised.items():
        veto = reserve(params={"regime_by_date": governed_regime(daily, veto=mapping)})
        out.append(_spec("forms", f"veto {name}", veto, form="veto", signal=name))
        pause = reserve(params={"caution_by_date": mapping})
        out.append(_spec("forms", f"pause {name}", pause, form="pause", signal=name))
    for name, mapping in benign.items():
        allow = reserve(params={"regime_by_date": governed_regime(daily, allow=mapping)})
        out.append(_spec("forms", f"allow {name}", allow, form="allow", signal=name))
    return out


# --------------------------------------------------------------- running


def run(spec: dict) -> dict:
    """du.run_one, with the injected maps left out of what is written: a
    {date: flag} map is neither small nor JSON."""
    row = du.run_one(spec)
    for key in ("caution_by_date", "regime_by_date"):
        if key in row.get("params", {}):
            row["params"] = {**row["params"], key: f"<{len(row['params'][key])} sessions>"}
    return row


# --------------------------------------------------------------- the report


def line(row: dict) -> str:
    m, e = row["metrics"], row.get("exposure") or {}
    halves = "  ".join(
        f"{label} {w['geo_daily']:.3f}%/d DD {w['max_dd']:4.1f}%"
        for label, start, end in HALVES
        for w in (du.window_metrics(row, start, end),)
    )
    return (
        f"{m['geo_daily']:.3f}%/d  CAGR {m['cagr']:4.1f}%  DD {m['max_dd']:4.1f}%  "
        f"Sharpe {m['sharpe']:.2f}  {halves}  in {FUND} {e.get('avg_exposure', float('nan')):.0f}%"
    )


def null_rank(
    rows: list[dict], stage: str = "null", book: str | None = None
) -> dict[str, Any] | None:
    """Where the real pause map sits among its time-shifted copies, in
    `stage` (and for one `book` of a daily stage)."""
    by = {
        r["meta"]["shift"]: r["metrics"]
        for r in rows
        if r["stage"] == stage and (book is None or r["meta"].get("book") == book)
    }
    shifted = [m for k, m in by.items() if k not in ("real", "off")]
    if "real" not in by or "off" not in by or not shifted:
        return None
    real, off = by["real"], by["off"]

    def calmar(m: dict) -> float:
        return m["cagr"] / m["max_dd"]

    return {
        "n": len(shifted),
        "real": real,
        "off": off,
        "geo_beaten_by": sum(m["geo_daily"] >= real["geo_daily"] for m in shifted),
        "dd_beaten_by": sum(m["max_dd"] <= real["max_dd"] for m in shifted),
        "calmar_beaten_by": sum(calmar(m) >= calmar(real) for m in shifted),
        "shifted_geo_median": sorted(m["geo_daily"] for m in shifted)[len(shifted) // 2],
        "shifted_dd_median": sorted(m["max_dd"] for m in shifted)[len(shifted) // 2],
    }


def report(out_dir: Path) -> str:
    rows = [r for r in du.load_results(out_dir) if du._ok(r)]
    lines = [f"# Risk governor probe -- {out_dir.name}", ""]
    for stage in ("forms", "frontier", "robust", "stress", "daily", "daily-stress"):
        staged = [r for r in rows if r["stage"] == stage]
        if not staged:
            continue
        lines += [f"## {stage}", "", "```"]
        width = max(len(r["name"]) for r in staged) - len(stage) - 3
        for r in staged:
            lines.append(f"{r['name'].split('| ', 1)[1]:<{width}}  {line(r)}")
        lines += ["```", ""]
    ranks = [("null", null_rank(rows))]
    ranks += [(f"daily-null, {book}", null_rank(rows, "daily-null", book)) for book in BOOKS]
    for title, rank in ranks:
        if not rank:
            continue
        real, off = rank["real"], rank["off"]
        lines += [
            f"## {title}",
            "",
            f"real map: {real['geo_daily']:.3f}%/d, DD {real['max_dd']:.1f}%; "
            f"no governor: {off['geo_daily']:.3f}%/d, DD {off['max_dd']:.1f}%; "
            f"{rank['n']} shifted maps: median {rank['shifted_geo_median']:.3f}%/d, "
            f"DD {rank['shifted_dd_median']:.1f}%.",
            "",
            f"Shifted maps at least as good as the real one: return "
            f"{rank['geo_beaten_by']}/{rank['n']}, drawdown {rank['dd_beaten_by']}/{rank['n']}, "
            f"return over drawdown {rank['calmar_beaten_by']}/{rank['n']}.",
            "",
        ]
    text = "\n".join(lines)
    (out_dir / "report.md").write_text(text)
    return text


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.strip().splitlines()[0])
    parser.add_argument(
        "--stage",
        choices=(
            "forms",
            "frontier",
            "robust",
            "null",
            "stress",
            "daily",
            "daily-null",
            "daily-stress",
        ),
    )
    parser.add_argument("--out", type=Path)
    parser.add_argument("--external", type=Path, help="the outside series (default: data/external)")
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
    external = external_directory(args.external).resolve()
    plans = {
        "forms": plan_forms,
        "frontier": plan_frontier,
        "robust": plan_robust,
        "null": plan_null,
        "stress": plan_stress,
        "daily": plan_daily,
        "daily-null": plan_daily_null,
        "daily-stress": plan_daily_stress,
    }
    specs = plans[args.stage](external)
    done = {r["name"] for r in du.load_results(args.out)}
    todo = [s for s in specs if s["name"] not in done]
    print(f"{args.stage}: {len(specs)} runs, {len(specs) - len(todo)} done, {len(todo)} to run")
    if args.dry_run or not todo:
        return 0
    with (
        ProcessPoolExecutor(max_workers=args.jobs) as pool,
        (args.out / "results.jsonl").open("a") as sink,
    ):
        futures = {pool.submit(run, spec): spec for spec in todo}
        for n, future in enumerate(as_completed(futures), 1):
            spec = futures[future]
            try:
                result = future.result()
            except Exception as exc:  # one failed configuration never stops the stage
                result = {k: spec[k] for k in ("stage", "name", "fund", "meta")}
                result["error"] = repr(exc)[:2000]
            sink.write(json.dumps(result, default=str) + "\n")
            sink.flush()
            m = result.get("metrics") or {}
            status = result.get("error", "")[:160] or (
                f"{m.get('geo_daily', float('nan')):.3f}%/d DD {m.get('max_dd', float('nan')):.1f}%"
            )
            print(f"[{n}/{len(todo)}] {spec['name']}: {status}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
