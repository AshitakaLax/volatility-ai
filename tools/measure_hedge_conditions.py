#!/usr/bin/env python
"""
Under what conditions can an SQQQ hedge leg be bought and later sold at
a profit?

--------------------------------------------------------------------
WHY THE QUESTION IS HARDER THAN IT LOOKS

SQQQ is -3x the Nasdaq-100 and fell 99.97% over 2016-2026, with one
positive calendar year in eleven (2022, +81.71%). Leveraged decay means
its price has no tendency to return to a prior level -- unlike TQQQ,
where a decade-long uptrend eventually bails out almost any lot.

That distinction is what makes `enforce_no_loss` behave completely
differently on the two instruments. On TQQQ it is a patience rule. On
SQQQ it is a permanent bag-holding rule: a lot bought above a level the
price never revisits is never sellable, and the capital is gone for the
life of the run.

So "buy and sell at a profit 100% of the time" is not a tuning target
here, it is a claim that needs testing against an instrument built to
decay. Measured unconditionally, from every session entry, with a
profitable exit defined as the forward HIGH exceeding entry x (1+cost):

    horizon      profitable exit available
      5 sessions       85.9%
     20 sessions       91.2%
     60 sessions       93.9%
    250 sessions       95.5%

It rises monotonically with the horizon: given long enough, SQQQ's
volatility almost always offers SOME exit above a given entry, even
while the price falls 99.97% overall. Decay does not prevent that,
because a -3x fund's daily swings are enormous relative to its drift.

An earlier version of this table read 91.8% at H=60 and 86.6% at H=250
and concluded that waiting past a quarter "starts actively hurting --
the drift outruns the volatility". That was wrong, and wrong in an
instructive way: the fall was entirely right-censoring (see
profitable_exit_available), and it survived review because leveraged
decay is real and made the artifact sound like a mechanism. The trap
is that a plausible story makes a measurement error harder to see,
not easier.

What decay DOES cost is not the hit rate but the price paid to get it:
the exit is available at some point, but the entry may sit deeply
underwater for months first, and the profit when it comes is measured
against an entry that keeps getting cheaper. Hit rate is not edge --
see the caveats below.

--------------------------------------------------------------------
WHAT THIS MEASURES

For every session entry, whether a profitable exit EXISTED within each
horizon, bucketed by conditions known at entry time. Conditions are all
backward-looking; the outcome is strictly forward. No entry can see its
own result.

The conditions are about TQQQ, VIXY and SQQQ's own stretch, because
buying an inverse fund is a bet the index falls -- so the useful
question is "when is the index most likely to drop", not "when does
SQQQ look cheap".

--------------------------------------------------------------------
HOW TO READ A HIGH NUMBER, AND HOW NOT TO

A 100% bucket in a 2,680-session sample is not a guarantee. It is most
often a small bucket, and this project has already paid for confusing
an in-sample correlation with a tradable edge -- see
config/search_hf_volume_sweep.yaml: "rank correlation against forward
troughs is a WEAK predictor of backtest value, and should not be used
to pre-filter candidates on its own again."

So the report prints, for every bucket: the sample size, the hit rate,
AND the per-year breakdown. A condition that only works in 2022 is a
description of 2022, not a hedge rule. Buckets below MIN_BUCKET are
flagged rather than trusted.

Costs are charged. A "profit" that does not clear the round trip is not
a profit; DEFAULT_COST_PCT mirrors config's dynamic_slippage settings
(base_bps 0.5 each way, plus slippage headroom).

Usage:
    python tools/measure_hedge_conditions.py
    python tools/measure_hedge_conditions.py --horizons 5 20 60
"""

from __future__ import annotations

import argparse
import os as _os
import sys as _sys

_REPO_ROOT = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
if _REPO_ROOT not in _sys.path:
    _sys.path.insert(0, _REPO_ROOT)

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from src.fomc_calendar import EASTERN_TZ  # noqa: E402

SQQQ = "data/SQQQ_1Min_sip_all_ext_2016-01-01_2026-09-01.csv"
TQQQ = "data/TQQQ_1Min_sip_all_2016-01-01_2026-08-21.csv"
VIXY = "data/VIXY_1Min_sip_all_ext_2016-01-01_2026-09-01.csv"

# Round-trip cost. base_bps 0.5 each way plus slippage headroom, matching
# the dynamic_slippage model the sweeps use.
DEFAULT_COST_PCT = 0.0015

# Below this a bucket's hit rate is noise dressed as a finding.
MIN_BUCKET = 60


def session_bars(path: str) -> pd.DataFrame:
    """Regular-hours OHLC aggregated to one row per session."""
    df = pd.read_csv(
        path, parse_dates=["timestamp"], usecols=["timestamp", "high", "low", "close"]
    ).set_index("timestamp")
    eastern = df.index.tz_convert(EASTERN_TZ)
    minute = eastern.hour * 60 + eastern.minute
    keep = (minute >= 570) & (minute < 960)
    df = df[keep]
    dates = np.array(df.index.tz_convert(EASTERN_TZ).date)
    out = pd.DataFrame(
        {
            "high": df["high"].groupby(dates).max(),
            "low": df["low"].groupby(dates).min(),
            "close": df["close"].groupby(dates).last(),
        }
    )
    out.index.name = "session"
    return out


def rsi(series: pd.Series, period: int = 14) -> pd.Series:
    """Wilder's RSI. Written here rather than imported because this
    project has no TA dependency and adding one for an exploratory
    measurement would be exactly the "ingestion dependency added on
    spec" the Task 7.9 gate exists to prevent."""
    delta = series.diff()
    gain = delta.clip(lower=0.0)
    loss = (-delta).clip(lower=0.0)
    avg_gain = gain.ewm(alpha=1 / period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1 / period, adjust=False).mean()
    rs = avg_gain / avg_loss.replace(0.0, np.nan)
    out = 100.0 - 100.0 / (1.0 + rs)
    # avg_loss == 0 makes rs undefined, and a blanket fillna(50) sent the
    # MOST overbought case -- a window with no down-bars at all -- to
    # NEUTRAL. That is backwards, and on a tool whose whole purpose is
    # bucketing by how stretched the index is, it would have quietly
    # filed the strongest uptrends into the middle bucket. Zero losses
    # with gains is 100; zero of both is a flat series, which really is
    # neutral.
    no_loss = avg_loss == 0.0
    out = out.mask(no_loss & (avg_gain > 0.0), 100.0)
    out = out.mask(no_loss & (avg_gain == 0.0), 50.0)
    return out.fillna(50.0)


def profitable_exit_available(
    bars: pd.DataFrame, horizon: int, cost_pct: float
) -> pd.Series:
    """Did the forward HIGH, strictly AFTER entry, clear entry x (1+cost)
    within `horizon` sessions?

    Returns True / False / NaN, where NaN means "not yet knowable" --
    the entry is close enough to the end of the data that its full
    forward window does not exist. Those entries are EXCLUDED from every
    rate below, not counted as failures.

    THAT DISTINCTION IS NOT PEDANTRY; getting it wrong produced a
    confident false conclusion in the first version of this script.
    `NaN > x` is False in pandas, so a truncated window silently scored
    as "no profitable exit". At H=250 that forces the last ~250 of 2,680
    entries (9%) to False, which manufactured an apparent decline in the
    hit rate at long horizons -- and it was read as leveraged decay,
    which is a real phenomenon and made the artifact sound plausible. It
    also made 2026 look like a regime collapse (58% against 90-98% for
    every other year) when it was only the last two months of a sample
    that had not finished happening yet.

    Uses the high rather than the close because a limit order resting at
    the target fills on a touch -- the same intrabar reasoning the fill
    model already uses. Shifted by one so an entry can never be exited on
    its own bar.
    """
    forward_high = (
        bars["high"].shift(-1).rolling(horizon, min_periods=1).max().shift(-(horizon - 1))
    )
    hit = forward_high > bars["close"] * (1.0 + cost_pct)
    # Where the window is incomplete the answer is unknown, not "no".
    return hit.astype(float).where(forward_high.notna())


def build(cost_pct: float) -> pd.DataFrame:
    sqqq, tqqq, vixy = session_bars(SQQQ), session_bars(TQQQ), session_bars(VIXY)
    idx = sqqq.index.intersection(tqqq.index).intersection(vixy.index)
    frame = pd.DataFrame(index=idx).sort_index()

    frame["sqqq_close"] = sqqq["close"]
    frame["sqqq_high"] = sqqq["high"]
    t = tqqq["close"]

    # --- conditions, all backward-looking ---
    frame["tqqq_rsi14"] = rsi(t)
    frame["tqqq_above_sma20"] = (t / t.rolling(20).mean() - 1.0) * 100.0
    frame["tqqq_above_sma50"] = (t / t.rolling(50).mean() - 1.0) * 100.0
    # How far TQQQ sits below its own trailing peak. Near 0 = at highs,
    # which is where an inverse hedge has the most room to work.
    frame["tqqq_drawdown"] = (1.0 - t / t.rolling(250, min_periods=20).max()) * 100.0
    frame["vixy_close"] = vixy["close"]
    frame["vixy_chg5"] = (vixy["close"] / vixy["close"].shift(5) - 1.0) * 100.0
    # VIXY level is not comparable across years (roll decay), so rank it
    # within a trailing window instead of using the raw number.
    frame["vixy_pctile"] = (
        vixy["close"].rolling(250, min_periods=60).rank(pct=True) * 100.0
    )
    return frame


def summarize(frame: pd.DataFrame, horizons, cost_pct: float) -> None:
    sq = frame[["sqqq_close", "sqqq_high"]].rename(
        columns={"sqqq_close": "close", "sqqq_high": "high"}
    )
    outcomes = {h: profitable_exit_available(sq, h, cost_pct) for h in horizons}

    print(f"sessions: {len(frame):,}  ({frame.index[0]} -> {frame.index[-1]})")
    print(f"round-trip cost charged: {cost_pct * 100:.2f}%\n")

    print("=== UNCONDITIONAL ===")
    for h in horizons:
        o = outcomes[h].dropna()
        print(
            f"  H={h:3d}  profitable exit available {o.mean() * 100:5.1f}%  "
            f"(n={len(o):,}; {int(outcomes[h].isna().sum())} entries excluded as not-yet-knowable)"
        )

    conditions = [
        ("tqqq_rsi14", "TQQQ RSI(14)"),
        ("tqqq_above_sma20", "TQQQ % above SMA20"),
        ("tqqq_above_sma50", "TQQQ % above SMA50"),
        ("tqqq_drawdown", "TQQQ drawdown from 250d peak %"),
        ("vixy_pctile", "VIXY 250d percentile"),
        ("vixy_chg5", "VIXY 5-session change %"),
    ]

    for column, label in conditions:
        print(f"\n=== {label} ===")
        series = frame[column]
        try:
            buckets = pd.qcut(series, 5, labels=False, duplicates="drop")
        except ValueError:
            print("  (not enough distinct values to bucket)")
            continue
        for b in sorted(pd.Series(buckets).dropna().unique()):
            mask = buckets == b
            lo, hi = series[mask].min(), series[mask].max()
            n = int(mask.sum())
            rates = " ".join(
                f"H{h}={outcomes[h][mask].dropna().mean() * 100:5.1f}%" for h in horizons
            )
            usable = int(outcomes[max(horizons)][mask].notna().sum())
            flag = "  <-- SMALL" if usable < MIN_BUCKET else ""
            print(f"  q{int(b) + 1} [{lo:8.2f}, {hi:8.2f}]  n={usable:5d}  {rates}{flag}")


def per_year(frame: pd.DataFrame, horizon: int, cost_pct: float) -> None:
    """A condition that only works in one regime is a description of that
    regime, not a rule. This is the check that catches it."""
    sq = frame[["sqqq_close", "sqqq_high"]].rename(
        columns={"sqqq_close": "close", "sqqq_high": "high"}
    )
    ok = profitable_exit_available(sq, horizon, cost_pct)
    years = pd.Series([d.year for d in frame.index], index=frame.index)
    print(f"\n=== PER YEAR, H={horizon} (regime check) ===")
    for year, group in ok.groupby(years):
        usable = group.dropna()
        if usable.empty:
            print(f"  {year}  n=   0  (entire year still inside the forward window)")
            continue
        excluded = len(group) - len(usable)
        note = f"  ({excluded} not yet knowable)" if excluded else ""
        print(f"  {year}  n={len(usable):4d}  {usable.mean() * 100:5.1f}%{note}")


def by_target(frame: pd.DataFrame, horizon: int) -> None:
    """Hit rate at HEDGE-SIZED targets -- the view that decides it.

    The default cost-sized bar (0.15%) is nearly free on a -3x fund that
    swings ~5% a day, so almost any entry clears it and almost any
    condition looks predictive. Measured that way the median winner
    exits in ONE session having never gone more than 0.2% underwater,
    which is a description of SQQQ's volatility, not of an edge.

    A hedge has to earn enough to offset a loss on the primary position,
    so the honest question is asked at +10% and +20%, not +0.15%.
    """
    sq = frame[["sqqq_close", "sqqq_high"]].rename(
        columns={"sqqq_close": "close", "sqqq_high": "high"}
    )
    conditions = [
        ("ALL entries (baseline)", pd.Series(True, index=frame.index)),
        ("TQQQ >15.2% over SMA50", frame["tqqq_above_sma50"] > 15.2),
        ("TQQQ RSI(14) > 66", frame["tqqq_rsi14"] > 66.31),
        ("TQQQ within 1.4% of peak", frame["tqqq_drawdown"] <= 1.44),
    ]
    targets = (0.02, 0.05, 0.10, 0.20)

    print(f"\n=== HIT RATE BY PROFIT TARGET, H={horizon} ===")
    header = "  ".join(f"+{t * 100:.0f}%".rjust(6) for t in targets)
    print(f"  {'condition':28s} {header}      n")
    for label, mask in conditions:
        cells = []
        for target in targets:
            hit = profitable_exit_available(sq, horizon, target)[mask].dropna()
            cells.append(f"{hit.mean() * 100:5.1f}%".rjust(6))
        n = len(profitable_exit_available(sq, horizon, targets[0])[mask].dropna())
        print(f"  {label:28s} {'  '.join(cells)}  {n:5d}")
    print(
        "\n  Read the +10% and +20% columns. Whatever separation the conditions\n"
        "  show at small targets is gone by the time the target is large enough\n"
        "  to offset a real TQQQ loss -- the 'best' condition is no better than\n"
        "  the baseline there, and sometimes worse."
    )


def parse_args(argv=None):
    p = argparse.ArgumentParser(
        description="When can an SQQQ hedge leg be exited at a profit?"
    )
    p.add_argument("--horizons", type=int, nargs="+", default=[5, 20, 60])
    p.add_argument("--cost-pct", type=float, default=DEFAULT_COST_PCT)
    return p.parse_args(argv)


def main(argv=None) -> int:
    args = parse_args(argv)
    for path in (SQQQ, TQQQ, VIXY):
        if not _os.path.exists(path):
            print(f"Not found: {path}", file=_sys.stderr)
            return 1
    frame = build(args.cost_pct).dropna()
    summarize(frame, args.horizons, args.cost_pct)
    per_year(frame, max(args.horizons), args.cost_pct)
    by_target(frame, max(args.horizons))
    print(
        "\nA 100% bucket is not a guarantee -- check n, and check the per-year row.\n"
        "SQQQ decays, so an entry that never recovers is capital gone for the life\n"
        "of the run, which is what enforce_no_loss would turn it into."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
