#!/usr/bin/env python
"""
Does a forward-looking implied-vol series beat the backward-looking
realized vol this project already uses?

WHY THIS QUESTION. `vol_scale_exponent` is the single most valuable
signal measured in this project (+13.05pp, against ~1-2pp for each event
calendar). It scales size by realized volatility --
`clamp((fast_vol / slow_vol) ** exponent, min, max)` -- computed from the
instrument's own past bars. src/high_frequency_sizing.py states its
structural weakness plainly:

    "That scaler is backward-looking and structurally lags the open:
     even its shortest window (0.25 days = 97 bars) is still mostly
     describing yesterday afternoon at 09:30, so it cannot react to the
     open's volatility until most of the open is already gone."

An implied-vol index is the market's own FORWARD estimate and is known
before the session starts. src/external_index_series.py was built for
exactly this and has never had a consumer. The question is whether it
carries information the incumbent does not.

--------------------------------------------------------------------
THE TEST IS AIMED AT WHERE THE INCUMBENT IS BLIND

Two targets, and the second is the one that matters:

  1. next session's FULL-DAY realized volatility
  2. next session's OPENING volatility (09:30-10:30)

On (1) a trailing realized-vol measure should do well -- volatility
clusters, so yesterday's vol predicts today's. That is the incumbent's
home ground and beating it there is hard and not very interesting.

On (2) the incumbent is structurally handicapped by its own admission,
while an implied-vol close from the prior session is fully known in
advance. If the candidate adds anything, it should show up here.

--------------------------------------------------------------------
INCREMENTAL, NOT ABSOLUTE

A raw correlation between implied vol and future realized vol will be
high simply because both measure "the market is turbulent lately". That
is not news and not a reason to add a knob. What matters is whether the
candidate says anything AFTER the incumbent has spoken, so this reports
the PARTIAL correlation -- the candidate against the target, holding the
incumbent fixed.

--------------------------------------------------------------------
A CAVEAT THIS PROJECT HAS ALREADY PAID FOR

config/search_hf_volume_sweep.yaml records, from experience:

    "rank correlation against forward troughs is a WEAK predictor of
     backtest value, and should not be used to pre-filter candidates on
     its own again"

So a positive result here is a licence to SWEEP the signal, not
evidence that it works. A negative result is the stronger conclusion,
because it means there is nothing to sweep.

--------------------------------------------------------------------
VIXY IS A PROXY, AND THE MISMATCH IS REAL

The right series is VXN -- Nasdaq-100 implied volatility, the index
TQQQ tracks 3x. It comes from hfmarketdata.io, which was unreachable
when this was written (HTTP 000 after 25s while control hosts answered
in 1.5s -- the outage mode src/hf_market_data.py's docstring already
documents). VIXY is reachable via Alpaca and is used instead, with two
substitutions stated rather than buried:

  * VIX (S&P 500), not VXN (Nasdaq-100). Highly correlated, not the
    same index.
  * VIX FUTURES via an ETF wrapper, not spot VIX. It carries roll decay,
    a persistent downward drift unrelated to implied vol. Levels are
    therefore not comparable across years; CHANGES and short/long RATIOS
    largely difference it out, which is why those are reported alongside
    the level.

Re-run against real VXN when the provider returns before trusting any
of this too far.

Usage:
    python tools/measure_vol_signal.py
    python tools/measure_vol_signal.py --primary data/TQQQ_...csv --signal data/VIXY_...csv
"""

from __future__ import annotations

import argparse
import os as _os
import sys as _sys

_REPO_ROOT = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
if _REPO_ROOT not in _sys.path:
    _sys.path.insert(0, _REPO_ROOT)

import numpy as np
import pandas as pd

from tools.session_bars import (
    OPEN_WINDOW_END,
    SESSION_CLOSE,
    SESSION_OPEN,
    minute_of_day,
    session_dates,
)

DEFAULT_PRIMARY = "data/TQQQ_1Min_sip_all_2016-01-01_2026-08-21.csv"
DEFAULT_SIGNAL = "data/VIXY_1Min_sip_all_ext_2016-01-01_2026-09-01.csv"

SESSION_MINUTES = 390


# ------------------------------------------------------------ measures


def session_frame(path: str, *, regular_hours_only: bool = True) -> pd.DataFrame:
    """Per-session realized volatility and close for one instrument."""
    df = pd.read_csv(
        path, parse_dates=["timestamp"], usecols=["timestamp", "close"]
    ).set_index("timestamp")
    minutes = minute_of_day(df.index)
    if regular_hours_only:
        keep = (minutes >= SESSION_OPEN) & (minutes < SESSION_CLOSE)
        df, minutes = df[keep], minutes[keep]

    dates = session_dates(df.index)
    log_ret = np.log(df["close"] / df["close"].shift(1))
    # Cross-session returns are the overnight gap, not a traded minute.
    # Dropped here deliberately: tools/measure_event_effects.py showed the
    # gap-inclusive convention conflates "the open moved" with "the
    # session was volatile", which is exactly the confusion this script
    # exists to resolve.
    same = dates == np.roll(dates, 1)
    same[0] = False
    intraday = log_ret.where(same)
    scale = np.sqrt(SESSION_MINUTES) * 100.0

    in_open = same & (minutes >= SESSION_OPEN) & (minutes < OPEN_WINDOW_END)
    out = pd.DataFrame(
        {
            "vol": intraday.groupby(dates).std() * scale,
            "open_vol": log_ret.where(in_open).groupby(dates).std() * scale,
            "close": df["close"].groupby(dates).last(),
        }
    )
    out.index.name = "session"
    return out


def spearman(a: pd.Series, b: pd.Series) -> float:
    """Rank correlation. Implemented via ranks + Pearson rather than
    scipy, which is not a dependency and must not become one here."""
    joined = pd.concat([a, b], axis=1).dropna()
    if len(joined) < 3:
        return float("nan")
    ra = joined.iloc[:, 0].rank()
    rb = joined.iloc[:, 1].rank()
    return float(np.corrcoef(ra, rb)[0, 1])


def partial_spearman(
    target: pd.Series, candidate: pd.Series, control: pd.Series
) -> float:
    """Rank correlation of candidate with target, holding control fixed.

    The number that decides this question. A raw correlation is inflated
    by both series measuring "the market is turbulent lately"; this asks
    what the candidate adds once the incumbent has already spoken.
    """
    r_tc = spearman(target, candidate)
    r_ta = spearman(target, control)
    r_ca = spearman(candidate, control)
    denom = np.sqrt((1 - r_ta**2) * (1 - r_ca**2))
    # A TOLERANCE, not `== 0`. When the control explains the target (or
    # the candidate) almost perfectly, the denominator is ~1e-9 rather
    # than exactly zero, and an exact-equality guard sails past it and
    # divides by it -- turning a genuinely undefined partial correlation
    # into a large, confident-looking, meaningless number. The partial
    # correlation is not defined when either relationship is degenerate,
    # so say so.
    if not np.isfinite(denom) or denom < 1e-6:
        return float("nan")
    return float((r_tc - r_ta * r_ca) / denom)


def build(primary: pd.DataFrame, signal: pd.DataFrame) -> pd.DataFrame:
    """Align both instruments and construct predictors and targets.

    Every predictor is dated at the END of session d and every target at
    session d+1, so nothing is knowable only in hindsight.
    """
    frame = pd.DataFrame(index=primary.index.intersection(signal.index)).sort_index()
    frame["vol"] = primary["vol"]
    frame["open_vol"] = primary["open_vol"]

    # Incumbent: trailing realized vol, and the fast/slow RATIO that
    # vol_scale_exponent actually uses. 5/60 sessions mirrors the shape of
    # the 0.25/10.0-day intraday windows at session granularity.
    frame["rv_fast"] = frame["vol"].rolling(5).mean()
    frame["rv_slow"] = frame["vol"].rolling(60).mean()
    frame["rv_ratio"] = frame["rv_fast"] / frame["rv_slow"]

    # Candidate: implied-vol level, its change, and its own fast/slow
    # ratio. The ratio is the one to watch -- it differences out the roll
    # decay the level carries.
    sig = signal["close"]
    frame["iv_level"] = sig
    frame["iv_chg"] = sig.pct_change() * 100.0
    frame["iv_ratio"] = sig.rolling(5).mean() / sig.rolling(60).mean()

    # Targets: strictly the NEXT session.
    frame["target_vol"] = frame["vol"].shift(-1)
    frame["target_open_vol"] = frame["open_vol"].shift(-1)
    return frame


def report(frame: pd.DataFrame) -> None:
    candidates = [
        ("iv_level", "implied level"),
        ("iv_chg", "implied 1d change"),
        ("iv_ratio", "implied 5/60 ratio"),
    ]
    controls = [("rv_fast", "trailing realized vol"), ("rv_ratio", "realized 5/60 ratio")]

    for target, label in (
        ("target_vol", "NEXT SESSION full-day volatility"),
        ("target_open_vol", "NEXT SESSION opening volatility (09:30-10:30)"),
    ):
        print(f"\n=== target: {label} ===")
        usable = frame[[target]].dropna()
        print(f"  sessions: {len(usable):,}\n")

        print("  incumbent (what the strategy already has):")
        for col, name in controls:
            print(f"    {name:26s} rho = {spearman(frame[target], frame[col]):+.3f}")

        print("\n  candidate, raw:")
        for col, name in candidates:
            print(f"    {name:26s} rho = {spearman(frame[target], frame[col]):+.3f}")

        # BOTH controls, always. Reporting only the first is actively
        # misleading and nearly produced the wrong recommendation:
        # the implied 5/60 ratio scores +0.31 against the realized RATIO
        # and exactly +0.00 against trailing realized VOL. It looked
        # additive only because the ratio is the weaker predictor
        # (rho +0.39 vs +0.78). A candidate must clear the STRONGER
        # control to have said anything new.
        print("\n  candidate, PARTIAL | realized 5/60 ratio (the weaker control):")
        for col, name in candidates:
            pr = partial_spearman(frame[target], frame[col], frame["rv_ratio"])
            print(f"    {name:26s} rho = {pr:+.3f}")

        print("\n  candidate, PARTIAL | trailing realized vol (THE DECIDING ONE):")
        for col, name in candidates:
            pr = partial_spearman(frame[target], frame[col], frame["rv_fast"])
            print(f"    {name:26s} rho = {pr:+.3f}")

    print(
        "\nReading this: the LAST table decides it.\n"
        "A raw correlation is inflated by both series measuring 'the market is\n"
        "turbulent lately'. Controlling for the realized 5/60 ratio is not enough\n"
        "either -- that ratio is a much weaker predictor than the trailing vol\n"
        "level, so a candidate can beat it while adding nothing. Only a candidate\n"
        "that survives 'PARTIAL | trailing realized vol' has said something the\n"
        "strategy does not already know.\n"
        "\n"
        "And per config/search_hf_volume_sweep.yaml, a positive result licenses a\n"
        "SWEEP, not a conclusion -- rank correlation is a weak predictor of\n"
        "backtest value here. A negative result is the stronger finding."
    )


def parse_args(argv=None):
    p = argparse.ArgumentParser(
        description="Does forward-looking implied vol beat backward-looking realized vol?"
    )
    p.add_argument("--primary", default=DEFAULT_PRIMARY, help="Traded instrument minute CSV")
    p.add_argument("--signal", default=DEFAULT_SIGNAL, help="Implied-vol proxy minute CSV")
    return p.parse_args(argv)


def main(argv=None) -> int:
    args = parse_args(argv)
    for path in (args.primary, args.signal):
        if not _os.path.exists(path):
            print(f"Not found: {path}", file=_sys.stderr)
            return 1

    print(f"primary: {args.primary}")
    print(f"signal : {args.signal}")
    primary = session_frame(args.primary)
    signal = session_frame(args.signal)
    frame = build(primary, signal)
    print(f"overlapping sessions: {len(frame):,}")
    report(frame)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
