#!/usr/bin/env python
"""Build the proxy risk reports for a fund, freeze its baselines, and
calibrate the daily tiers (docs/daily_risk_report_plan.md, Phase 2).

    python tools/build_proxy_reports.py --symbol TQQQ --out DIR
    python tools/build_proxy_reports.py --symbol TQQQ --out DIR --baselines
    python tools/build_proxy_reports.py --symbol TQQQ --out DIR --calibrate

--out DIR receives one JSON per session in research/risk_overlay/archive.py's
format (source: proxy), from --from (2011-01-03, VIX9D's first year) to the
latest session the data reaches -- the archive a backtest's
`risk.overlay: {source: proxy, path: DIR}` reads. Written fresh each run.

--baselines then writes research/risk_overlay/baselines.json's entry for the
fund: the median expected move and the median 21- and 63-session expected
shortfall over the research window (2016-01-04 on), the scale every mapping
measures against. --calibrate prints the tier thresholds set by FREQUENCY on
the proxy over 2011-2018 -- tier 3 on the riskiest 10% of sessions, tier 2 on
the next 15%, tier 1 on the next 25% -- for freezing in mapping.py.

The fund's closes are the warehouse's (engine/warehouse/bars.py). Before the
warehouse's first session (TQQQ: 2016-01-04) they are spliced from QQQ's
daily closes at the fund's leverage, so the realised-volatility half of the
expected move exists from 2011; the splice is the proxy's input only, never
a backtest's bars. The outside series are research/ml/sources.py's files
(VAI_EXTERNAL_DIR), read point in time.
"""

from __future__ import annotations

import argparse
import json
import shutil
import statistics
import sys
from bisect import bisect_left
from datetime import date
from itertools import pairwise
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

FROM = date(2011, 1, 3)
RESEARCH_FROM = date(2016, 1, 4)
CALIBRATE = (date(2011, 1, 3), date(2018, 12, 31))
# Shares of sessions in tiers 3, 2 and 1 (the plan's frequencies).
TIER_SHARES = (0.10, 0.15, 0.25)


def load_inputs(symbol: str):
    """(the fund's daily closes, spliced; the outside series)."""
    import pandas as pd

    from engine.warehouse.bars import load_frame
    from research.risk_overlay.inputs import IMPLIED_INDEX
    from research.risk_overlay.proxy import SERIES, daily_closes
    from research.strategies.risk_governor import external_directory, read_series

    root = external_directory()
    series = {}
    for key in SERIES:
        path = root / f"{key}.csv"
        series[key] = read_series(path) if path.exists() else None
    closes = daily_closes(load_frame(symbol))
    leverage = IMPLIED_INDEX.get(symbol.upper(), ("", 1.0))[1]
    qqq = series.get("yahoo_QQQ")
    if qqq is not None and len(closes):
        first = closes.index[0]
        # Each QQQ reading is stamped when it could first be read; its
        # session is the Eastern date of the close it records.
        q = qqq.copy()
        q.index = pd.DatetimeIndex(q.index.tz_convert("America/New_York").date)
        q = q.groupby(level=0).last()
        # The fund's first close walked backwards by QQQ's returns at the
        # fund's leverage: synthetic[t] = first close / prod (1 + r) over (t, first].
        r = (q.pct_change() * leverage).fillna(0.0)
        r = r[r.index <= first]
        growth = (1.0 + r)[::-1].cumprod()[::-1].shift(-1)
        synthetic = (closes.iloc[0] / growth)[lambda x: x.index < first].dropna()
        closes = pd.concat([synthetic, closes])
    return closes, series


def build(symbol: str, out: Path, start: date) -> list[dict]:
    from engine.core.trading_calendar import sessions_between
    from research.risk_overlay.archive import ReportArchive
    from research.risk_overlay.proxy import build_archive

    closes, series = load_inputs(symbol)
    last = closes.index[-1].date() if hasattr(closes.index[-1], "date") else closes.index[-1]
    sessions = sessions_between(start, last)
    entries = build_archive(symbol, closes, series, sessions)
    if out.exists():
        shutil.rmtree(out)
    archive = ReportArchive(out)
    for entry in entries:
        archive.write(date.fromisoformat(entry["session"]), entry)
    (out / "meta.json").write_text(
        json.dumps(
            {
                "symbol": symbol,
                "sessions": len(entries),
                "first": entries[0]["session"] if entries else None,
                "last": entries[-1]["session"] if entries else None,
                "series": {
                    k: (str(s.index[0].date()) if s is not None else None)
                    for k, s in series.items()
                },
            },
            indent=2,
        )
    )
    return entries


def baselines(symbol: str, entries: list[dict]) -> dict:
    from research.risk_overlay.baselines import Baseline, read_baselines, write_baselines

    window = [e for e in entries if e["session"] >= RESEARCH_FROM.isoformat()]
    moves = [e["report"]["execution_signals"]["expected_1d_move_pct"] for e in window]
    es5 = {
        horizon: statistics.median(
            e["report"]["horizons"][horizon]["summary"]["expected_shortfall_5pct"] for e in window
        )
        for horizon in ("next_month", "next_quarter")
    }
    known = read_baselines()
    known[symbol.upper()] = Baseline(
        symbol=symbol.upper(),
        move_pct=round(statistics.median(moves), 4),
        es5_pct={k: round(v, 4) for k, v in es5.items()},
        window=(window[0]["session"], window[-1]["session"]),
        source="proxy-v1 median over the research window (tools/build_proxy_reports.py)",
        computed_at=date.today().isoformat(),
    )
    write_baselines(known)
    return known[symbol.upper()].to_dict()


def calibrate(symbol: str, entries: list[dict]) -> dict:
    """The thresholds that put TIER_SHARES of 2011-2018's sessions in tiers
    3, 2 and 1, from the score S the provisional mapping gives each."""
    from engine.core.config import RiskOverlayConfig
    from engine.core.risk_report import parse_report
    from research.risk_overlay.baselines import baseline_for
    from research.risk_overlay.mapping import map_report
    from research.risk_overlay.schedules import entry_inputs

    settings = RiskOverlayConfig(mode="enforce")
    baseline = baseline_for(symbol)
    if baseline is None:
        raise SystemExit(f"no baseline for {symbol}: run --baselines first")
    scores = []
    low, high = (d.isoformat() for d in CALIBRATE)
    for entry in entries:
        if not low <= entry["session"] <= high:
            continue
        report = parse_report(entry["report"]).require()
        mapped = map_report(report, entry_inputs(entry, report, symbol, baseline), settings)
        if mapped.score is not None:
            scores.append(mapped.score)
    thresholds = thresholds_for(scores, TIER_SHARES)
    return {
        "sessions": len(scores),
        "thresholds": list(thresholds),
        "shares": tier_shares(scores, thresholds),
        "window": [low, high],
    }


def threshold_at(scores: list[float], share: float) -> float:
    """The threshold that puts the share of `scores` at or above it closest
    to `share`.

    S takes few values on the proxy (four of its five components are
    categorical, and the volatility one is 0 on every calm session), so a
    quantile lands on a tie, and `S >= quantile` would take the whole tie into
    the higher tier: 2011-2018's 0.10 alone is 15% of its sessions. A tie
    falls wholly on one side of a threshold, so the candidates are the
    midpoints between neighbouring values (no score sits on one) and the
    lowest value; the nearest share wins, the higher threshold on a draw."""
    values = sorted(set(scores))
    if not values:
        raise ValueError("no scores to calibrate on")
    ordered = sorted(scores)
    n = len(ordered)
    candidates = [values[0], *((a + b) / 2 for a, b in pairwise(values))]

    def miss(threshold: float) -> tuple[float, float]:
        at_or_above = n - bisect_left(ordered, threshold)
        return abs(at_or_above / n - share), -threshold

    return round(min(candidates, key=miss), 6)


def thresholds_for(
    scores: list[float], shares: tuple[float, float, float]
) -> tuple[float, float, float]:
    """(tier 1, tier 2, tier 3) thresholds for `shares` of sessions in tiers
    3, 2 and 1 (TIER_SHARES)."""
    t3 = threshold_at(scores, shares[0])
    t2 = threshold_at(scores, shares[0] + shares[1])
    t1 = threshold_at(scores, sum(shares))
    return t1, t2, t3


def tier_shares(scores: list[float], thresholds: tuple[float, float, float]) -> list[float]:
    """The share of `scores` in tiers 0-3 under `thresholds`."""
    counts = [0, 0, 0, 0]
    for score in scores:
        counts[sum(1 for t in thresholds if score >= t)] += 1
    return [round(c / len(scores), 4) for c in counts] if scores else counts


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--symbol", default="TQQQ")
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--from", dest="start", type=date.fromisoformat, default=FROM)
    parser.add_argument("--baselines", action="store_true", help="freeze the fund's baselines")
    parser.add_argument("--calibrate", action="store_true", help="print frequency-set thresholds")
    args = parser.parse_args(argv)
    entries = build(args.symbol, args.out, args.start)
    print(
        f"{args.symbol}: {len(entries)} proxy reports, {entries[0]['session']} to {entries[-1]['session']}"
    )
    if args.baselines:
        print("baseline:", json.dumps(baselines(args.symbol, entries)))
    if args.calibrate:
        print("calibration:", json.dumps(calibrate(args.symbol, entries)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
