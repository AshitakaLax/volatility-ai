#!/usr/bin/env python
"""
Measure whether a candidate event class actually moves volatility.

WHY THIS EXISTS. A long list of candidate market inputs was proposed
(macro releases, options expiration, corporate and geopolitical events).
This project has already measured what calendar signals are worth, and
the answer argues against adding many of them:

    FOMC day boost          +1.66pp on a 166% return
    earnings day boost      +1.06 to +1.68pp
    vol_scale_exponent      +13.05pp        (continuous, every bar)

src/high_frequency_sizing.py's own conclusion: "Identifying volatile days
is not the constraint -- a multiplier that fires on a twentieth of the
calendar simply cannot move a 10-year result much." And adding a sweep
axis has a measured cost: two axes worth ~3pp once took coverage from
3.2% to 0.30% and caused a sweep to miss a configuration a smaller run
had already found.

So this produces EVIDENCE, not knobs. It touches no strategy code, no
MarketContext field, and no config. A candidate earns a knob only by
clearing the bar the existing signals cleared, and this is what measures
that.

--------------------------------------------------------------------
THE METHODOLOGY IS REPRODUCED, NOT REINVENTED

src/earnings_calendar.py records the numbers that established the two
existing signals:

    earnings reaction days   3.79%  vs  3.40%   -> +11.4%, Welch t=2.89
    FOMC decision days       4.58%  vs  3.41%   -> +34.1%, Welch t=2.11

`--validate` re-derives all four from the raw data and asserts they come
back. A harness that cannot reproduce the established figures has no
business being believed about a new one, so that check runs first.

Reproducing them pinned down a detail the prose does not state, and it
matters more than it sounds: **the recorded measure INCLUDES the
overnight gap.** Session volatility is the standard deviation of
one-minute log returns times sqrt(390), where the first "return" of each
session is actually the close-to-open gap. Excluding it gives 3.86% vs
2.75% (+40.1%) -- different numbers and a different effect size.

That is a real limitation for the candidates being measured here.
Most macro releases land at 08:30 ET, BEFORE the open, so a
gap-inclusive measure partly scores "the release moved the open" as
though it were intraday volatility -- which is precisely the confound to
avoid when the strategy already models the open at 2.56x via
time_of_day_flag. This therefore reports BOTH conventions, and the
difference between them is itself the finding.

--------------------------------------------------------------------
WHAT IT MEASURES, AND WHY MORE THAN ONE THING

  session_vol_gap   std of 1-min log returns x sqrt(390), gap included
                    -- comparable to the recorded FOMC/earnings numbers
  session_vol       the same, cross-session returns dropped
                    -- the honest intraday measure
  open_vol          gap-excluded, restricted to 09:30-10:30
  rest_vol          gap-excluded, 10:30 onward
                    -- together these separate "this is just the open
                       again" from a genuinely separate effect
  mean_range_bps    mean intrabar (high-low)/close
  volume            session total

Range and volume are not decoration. Options expiration is a
liquidity and pinning phenomenon; if it shows up anywhere it may well be
in volume or intrabar range rather than in close-to-close volatility,
and a harness that only looked at the latter would report a false
negative.

--------------------------------------------------------------------
CALENDARS DERIVED HERE ARE DELIBERATELY LOCAL

The nth-weekday helpers below live in this file, not in src/. Phase 1
produces evidence and changes no production behaviour; if a candidate
clears the bar, Phase 2 promotes its calendar into src/ as a proper
module with the scalar/vectorized pair and agreement test the existing
calendars have. Writing it into src/ first would be building the thing
this measurement is supposed to justify.

Every derived date is checked against sessions actually present in the
data before use -- an nth-weekday rule silently generates market
holidays (Good Friday lands on a third Friday), and
src/fomc_calendar.py set the precedent: "Every date below was
cross-checked to land on an actual NYSE trading day present in this
repo's TQQQ SIP dataset before being accepted."

Usage:
    python tools/measure_event_effects.py --validate
    python tools/measure_event_effects.py
    python tools/measure_event_effects.py --data data/RSP_1Min_sip_all_ext_...csv
"""

from __future__ import annotations

import argparse
import os as _os
import sys as _sys
from datetime import date, timedelta

_REPO_ROOT = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
if _REPO_ROOT not in _sys.path:
    _sys.path.insert(0, _REPO_ROOT)

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from src.earnings_calendar import EARNINGS_REACTION_DATES  # noqa: E402
from src.fomc_calendar import EASTERN_TZ, FOMC_DECISION_DATES  # noqa: E402
from tools.session_bars import (  # noqa: E402
    OPEN_WINDOW_END,
    SESSION_OPEN,
    minute_of_day,
    session_dates,
)

DEFAULT_DATA = "data/TQQQ_1Min_sip_all_2016-01-01_2026-08-21.csv"

# 390 minutes in a regular session. The scale factor turns a per-minute
# standard deviation into a per-session one; it is NOT annualisation.
SESSION_MINUTES = 390

# The recorded figures this harness must reproduce before it is trusted.
# From src/earnings_calendar.py's MEASURED EFFECT section.
KNOWN_RESULTS = {
    "FOMC": {"flagged": 4.58, "baseline": 3.41, "pct": 34.1, "t": 2.11, "n": 74},
    "earnings": {"flagged": 3.79, "baseline": 3.40, "pct": 11.4, "t": 2.89, "n": 296},
}


# ---------------------------------------------------------------- dates


def nth_weekday(year: int, month: int, weekday: int, n: int) -> date:
    """The nth `weekday` of a month. weekday: Monday=0 .. Sunday=6.

    The repo has no nth-weekday helper anywhere -- no relativedelta, no
    calendar.monthrange, no bdate_range -- so this is written here rather
    than reached for.
    """
    first = date(year, month, 1)
    offset = (weekday - first.weekday()) % 7
    return first + timedelta(days=offset + 7 * (n - 1))


def third_friday(year: int, month: int) -> date:
    """Standard monthly options expiration."""
    return nth_weekday(year, month, weekday=4, n=3)


def opex_dates(years) -> set[date]:
    """Monthly equity-options expiration, all twelve months."""
    return {third_friday(y, m) for y in years for m in range(1, 13)}


def witching_dates(years) -> set[date]:
    """Triple/quadruple witching -- the QUARTERLY subset, when index
    futures and index options expire alongside equity options.

    Measured separately from ordinary monthly expiration because it is a
    different-magnitude claim, not the same one four times a year.
    """
    return {third_friday(y, m) for y in years for m in (3, 6, 9, 12)}


def month_end_sessions(sessions: pd.Index) -> set[date]:
    """The LAST ACTUAL SESSION of each month, not the calendar last day.

    Derived from the sessions present in the data rather than from the
    calendar, because month-end rebalancing flows land on the last day
    the market is open, which is frequently not the 30th or 31st.
    """
    frame = pd.DataFrame({"d": list(sessions)})
    frame["ym"] = [(d.year, d.month) for d in frame["d"]]
    return set(frame.groupby("ym")["d"].max())


def quarter_end_sessions(sessions: pd.Index) -> set[date]:
    frame = pd.DataFrame({"d": list(sessions)})
    frame["yq"] = [(d.year, (d.month - 1) // 3) for d in frame["d"]]
    return set(frame.groupby("yq")["d"].max())


# ------------------------------------------------------------ measures


def load_session_metrics(path: str) -> pd.DataFrame:
    """One row per session, carrying every metric this harness compares."""
    df = pd.read_csv(
        path,
        parse_dates=["timestamp"],
        usecols=["timestamp", "high", "low", "close", "volume"],
    ).set_index("timestamp")
    if df.index.tz is None:
        raise SystemExit(f"{path} has timezone-naive timestamps; refusing to guess.")

    dates = session_dates(df.index)
    minutes = minute_of_day(df.index)

    log_ret = np.log(df["close"] / df["close"].shift(1))
    # A return spanning two sessions is the overnight gap, not a minute
    # of trading. `same_session` marks the ones that are genuinely
    # intraday; the recorded convention keeps the gap, so both are built.
    same_session = dates == np.roll(dates, 1)
    same_session[0] = False
    intraday = log_ret.where(same_session)

    scale = np.sqrt(SESSION_MINUTES) * 100.0
    in_open = same_session & (minutes >= SESSION_OPEN) & (minutes < OPEN_WINDOW_END)
    in_rest = same_session & (minutes >= OPEN_WINDOW_END)

    metrics = pd.DataFrame(
        {
            "session_vol_gap": log_ret.groupby(dates).std() * scale,
            "session_vol": intraday.groupby(dates).std() * scale,
            "open_vol": log_ret.where(in_open).groupby(dates).std() * scale,
            "rest_vol": log_ret.where(in_rest).groupby(dates).std() * scale,
            "mean_range_bps": (
                ((df["high"] - df["low"]) / df["close"]).groupby(dates).mean() * 1e4
            ),
            "volume": df["volume"].groupby(dates).sum(),
        }
    )
    metrics.index.name = "session"
    return metrics.dropna(subset=["session_vol_gap"])


def welch_t(a: np.ndarray, b: np.ndarray) -> float:
    """Welch's t (unequal variances). Implemented directly rather than
    via scipy, which is not a dependency of this project and must not
    become one for a measurement script."""
    if len(a) < 2 or len(b) < 2:
        return float("nan")
    v1, v2 = np.var(a, ddof=1), np.var(b, ddof=1)
    denom = np.sqrt(v1 / len(a) + v2 / len(b))
    if denom == 0:
        return float("nan")
    return float((np.mean(a) - np.mean(b)) / denom)


def compare(metrics: pd.DataFrame, flagged: set[date], column: str) -> dict:
    mask = pd.Series([d in flagged for d in metrics.index], index=metrics.index)
    series = metrics[column].dropna()
    mask = mask.reindex(series.index).fillna(False)
    a, b = series[mask].to_numpy(), series[~mask].to_numpy()
    if len(a) == 0 or len(b) == 0:
        return {"n": len(a), "flagged": float("nan"), "baseline": float("nan"),
                "pct": float("nan"), "t": float("nan")}
    return {
        "n": len(a),
        "flagged": float(np.mean(a)),
        "baseline": float(np.mean(b)),
        "pct": float((np.mean(a) / np.mean(b) - 1.0) * 100.0),
        "t": welch_t(a, b),
    }


# ------------------------------------------------------------- reports


def validate(metrics: pd.DataFrame) -> bool:
    """Re-derive the two recorded results. Runs before anything else."""
    print("=== VALIDATION: reproducing the recorded figures ===")
    print("(src/earnings_calendar.py MEASURED EFFECT; gap-inclusive convention)\n")
    ok = True
    for label, calendar in (("FOMC", FOMC_DECISION_DATES),
                            ("earnings", EARNINGS_REACTION_DATES)):
        got = compare(metrics, calendar, "session_vol_gap")
        want = KNOWN_RESULTS[label]
        checks = [
            abs(got["flagged"] - want["flagged"]) < 0.02,
            abs(got["baseline"] - want["baseline"]) < 0.02,
            abs(got["pct"] - want["pct"]) < 0.3,
            abs(got["t"] - want["t"]) < 0.03,
            got["n"] == want["n"],
        ]
        passed = all(checks)
        ok &= passed
        mark = "OK " if passed else "MISMATCH"
        print(
            f"  [{mark}] {label:9s} n={got['n']:4d} (want {want['n']})  "
            f"{got['flagged']:.2f}% vs {got['baseline']:.2f}% -> {got['pct']:+.1f}%, "
            f"t={got['t']:.2f}"
        )
        if not passed:
            print(
                f"            wanted {want['flagged']:.2f}% vs {want['baseline']:.2f}% "
                f"-> {want['pct']:+.1f}%, t={want['t']:.2f}"
            )
    print()
    if not ok:
        print("  VALIDATION FAILED -- do not trust any result below.\n")
    return ok


def _row(name: str, r: dict) -> str:
    return (
        f"  {name:22s} n={r['n']:5d}  {r['flagged']:7.3f} vs {r['baseline']:7.3f}  "
        f"{r['pct']:+7.1f}%  t={r['t']:+6.2f}"
    )


def report(metrics: pd.DataFrame, candidates: dict[str, set[date]]) -> None:
    sessions = set(metrics.index)
    print("=== CANDIDATES ===")
    print(f"sessions in dataset: {len(sessions):,}  "
          f"({min(sessions)} -> {max(sessions)})\n")

    for name, dates_all in candidates.items():
        present = dates_all & sessions
        missing = len(dates_all) - len(present)
        print(f"--- {name} ---")
        print(f"  derived dates: {len(dates_all)}, present as sessions: {len(present)}"
              f"{f', ABSENT (holiday/weekend): {missing}' if missing else ''}")
        if not present:
            print("  no overlap with this dataset -- skipping\n")
            continue
        for column, label in (
            ("session_vol_gap", "session vol (gap)"),
            ("session_vol", "session vol (intraday)"),
            ("open_vol", "09:30-10:30 vol"),
            ("rest_vol", "10:30-close vol"),
            ("mean_range_bps", "mean range (bps)"),
            ("volume", "volume"),
        ):
            print(_row(label, compare(metrics, present, column)))
        print()

    print("Reference bar: earnings cleared at +11.4%, t=2.89 (n=296).")
    print("A candidate whose effect lives ONLY in '09:30-10:30 vol' is probably")
    print("restating time_of_day_flag, which already prices the open at 2.56x.")


def parse_args(argv=None):
    p = argparse.ArgumentParser(
        description="Measure whether candidate event classes move volatility."
    )
    p.add_argument("--data", default=DEFAULT_DATA, help=f"Minute CSV (default: {DEFAULT_DATA})")
    p.add_argument("--validate", action="store_true",
                   help="Only re-derive the recorded FOMC/earnings figures and exit.")
    return p.parse_args(argv)


def main(argv=None) -> int:
    args = parse_args(argv)
    if not _os.path.exists(args.data):
        print(f"Data file not found: {args.data}", file=_sys.stderr)
        return 1

    print(f"Loading {args.data} ...\n")
    metrics = load_session_metrics(args.data)

    ok = validate(metrics)
    if args.validate:
        return 0 if ok else 1

    sessions = metrics.index
    years = sorted({d.year for d in sessions})
    candidates = {
        "OpEx (3rd Friday, monthly)": opex_dates(years),
        "Triple witching (quarterly)": witching_dates(years),
        "Month-end session": month_end_sessions(sessions),
        "Quarter-end session": quarter_end_sessions(sessions),
        "FOMC (control)": set(FOMC_DECISION_DATES),
        "Earnings (control)": set(EARNINGS_REACTION_DATES),
    }
    report(metrics, candidates)
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
