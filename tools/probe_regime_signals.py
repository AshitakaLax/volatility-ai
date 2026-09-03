#!/usr/bin/env python
"""
Which regime indicator actually gets you out of 2022 -- and what does it
cost in the other ten years?

--------------------------------------------------------------------
THE PROBLEM WITH SMA200, STATED PRECISELY

SMA200-else-cash returns 34.57% CAGR and -19.8% in 2022. The -19.8% is
not the indicator being wrong, it is the indicator being LATE: a
200-session average has to be crossed before it says anything, and by
the time TQQQ crossed it in early 2022 the fund had already fallen
hard. Holding the trend instead of harvesting it makes that worse
(-67%), because there is more inventory to be caught with.

So the question is whether a faster or differently-constructed signal
buys back some of that without giving away the eleven years around it.

--------------------------------------------------------------------
THE OVERFITTING PROBLEM, WHICH IS SEVERE HERE

Searching indicators for one that "works in 2022" is close to the
definition of curve-fitting: there is exactly ONE full bear market in
this dataset, so a signal tuned to it has a sample size of one. Every
guard available is applied, and none of them make it safe:

  * Every year is reported, not just 2022. An indicator that rescues
    2022 and loses 2017 has not helped.
  * A chronological split (2016-2020 / 2021-2026) is printed for every
    indicator. 2022 sits in the second half, so a signal that only
    works there shows up as a split that disagrees.
  * FLIPS PER YEAR is reported. Latency and whipsaw are the same dial
    turned in opposite directions -- any indicator that beats SMA200 in
    2022 by being faster will pay for it in false exits, and this is
    where that cost becomes visible.
  * Switching costs are charged on every regime change.

Read the results as "how does the latency/whipsaw trade-off look", not
as "here is the indicator that would have saved 2022".

--------------------------------------------------------------------
THE SHELL IS DELIBERATELY THE SIMPLEST ONE

Every indicator is run through the SAME shell as the benchmark: fully
long TQQQ when the signal says bull, fully in cash when it says bear.
No grid, no escalation, no lot sizing. That isolates the signal, which
is the only thing under test -- putting the dip book underneath would
mean two changes at once and the result would not attribute.

NO LOOKAHEAD: every indicator is computed on daily closes up to and
including day t, then shifted one day before it is applied, so the
position held on day t+1 is decided by information that closed on day
t. The shift is applied in one place (`_apply`) rather than in each
indicator, so it cannot be forgotten for one of them.

Usage:
    python tools/probe_regime_signals.py
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

from src.performance_analyzer import annual_returns

TQQQ = "data/TQQQ_1Min_sip_all_2016-01-01_2026-08-21.csv"
VIXY = "data/VIXY_1Min_sip_all_ext_2016-01-01_2026-09-01.csv"
SWITCH_COST = 0.0015


def daily(path: str) -> pd.Series:
    frame = pd.read_csv(path, parse_dates=["timestamp"], usecols=["timestamp", "close"])
    return frame.set_index("timestamp")["close"].resample("D").last().dropna()


def ema(series: pd.Series, span: int) -> pd.Series:
    return series.ewm(span=span, adjust=False).mean()


def rsi(series: pd.Series, period: int = 14) -> pd.Series:
    """Wilder's RSI. avg_loss==0 yields NaN rather than a fabricated 100 --
    filling it would report the most overbought bar in the sample as
    neutral, which is a bug this project has already shipped once."""
    delta = series.diff()
    gain = delta.clip(lower=0.0)
    loss = (-delta).clip(lower=0.0)
    ag = gain.ewm(alpha=1 / period, adjust=False).mean()
    al = loss.ewm(alpha=1 / period, adjust=False).mean()
    return 100.0 - 100.0 / (1.0 + ag / al.replace(0.0, np.nan))


def asymmetric(px: pd.Series, exit_sig: pd.Series, entry_sig: pd.Series) -> pd.Series:
    """Exit on one condition, re-enter on a different, slower one.

    The single most promising structure the plain-indicator table cannot
    express. Latency and whipsaw are the same dial there -- a signal
    fast enough to leave early is noisy enough to leave constantly -- but
    they are only the same dial if ONE rule controls both directions.
    Splitting them lets the exit be fast and the re-entry slow, so a
    false exit costs missed upside rather than a churn of round trips.

    Written as an explicit state machine rather than boolean algebra
    because the position is genuinely stateful: whether today is bull
    depends on yesterday's position, not only on today's indicators.
    """
    e_out = exit_sig.reindex(px.index).fillna(False).to_numpy(dtype=bool)
    e_in = entry_sig.reindex(px.index).fillna(False).to_numpy(dtype=bool)
    held = False
    armed = True
    out = np.zeros(len(px), dtype=bool)
    for i in range(len(px)):
        if held and not e_out[i]:
            held = False
            # RE-ARM GATE. Without this the entry condition is still true
            # the instant the exit fires -- price below its 20-day EMA is
            # routinely still far above its 200-day average -- so every
            # exit was reversed the next day. That produced 58.7 flips a
            # year and made the asymmetric rows measure churn rather than
            # the idea. Re-entry now requires the entry signal to go
            # FALSE and come back, i.e. a genuine re-cross.
            armed = False
        elif not held and armed and e_in[i]:
            held = True
        if not armed and not e_in[i]:
            armed = True
        out[i] = held
    return pd.Series(out, index=px.index)


def signals(px: pd.Series, vix: pd.Series) -> dict:
    """Every indicator as a boolean 'bull' series on daily closes.

    NaN during warmup is fine and is handled uniformly by _apply: a
    NaN comparison is False, i.e. bear, i.e. flat -- which is what
    "no signal yet" should mean for a long-only book.
    """
    ret = px.pct_change()
    peak = px.cummax()
    vol20 = ret.rolling(20).std()
    macd = ema(px, 12) - ema(px, 26)

    return {
        # --- the incumbent and its faster relatives ---
        "SMA200 (incumbent)": px > px.rolling(200).mean(),
        "SMA100": px > px.rolling(100).mean(),
        "SMA50": px > px.rolling(50).mean(),
        "EMA50": px > ema(px, 50),
        "EMA20": px > ema(px, 20),
        "SMA20 > SMA100": px.rolling(20).mean() > px.rolling(100).mean(),

        # --- price-structure signals ---
        "Donchian: > 50d low x1.10": px > px.rolling(50).min() * 1.10,
        "Drawdown < 15% off 250d peak": (px / px.rolling(250).max()) > 0.85,
        "Trailing peak: < 20% off high": (px / peak) > 0.80,

        # --- oscillators and volatility ---
        "MACD > 0": macd > 0,
        "MACD > signal": macd > ema(macd, 9),
        "RSI(14) > 45": rsi(px) > 45,
        "Vol20 below its 250d median": vol20 < vol20.rolling(250).median(),

        # --- implied volatility, from VIXY ---
        "VIXY below 250d median": vix < vix.rolling(250).median(),
        "VIXY 10d change < +10%": vix.pct_change(10) < 0.10,

        # --- combinations: trend AND a risk filter ---
        "SMA200 and vol20 < median": (px > px.rolling(200).mean())
                                     & (vol20 < vol20.rolling(250).median()),
        "SMA200 or EMA20 (either)": (px > px.rolling(200).mean()) | (px > ema(px, 20)),
        "SMA200 and EMA20 (both)": (px > px.rolling(200).mean()) & (px > ema(px, 20)),
        "SMA100 and MACD > 0": (px > px.rolling(100).mean()) & (macd > 0),

        # --- variants of the one filter that reached 2022 breakeven ---
        "SMA200 and vol20 < 1.25x med": (px > px.rolling(200).mean())
                                        & (vol20 < vol20.rolling(250).median() * 1.25),
        "SMA200 and vol20 < 75th pct": (px > px.rolling(200).mean())
                                       & (vol20 < vol20.rolling(250).quantile(0.75)),
        "SMA100 and vol20 < median": (px > px.rolling(100).mean())
                                     & (vol20 < vol20.rolling(250).median()),
        "SMA200 and vol60 < median": (px > px.rolling(200).mean())
                                     & (ret.rolling(60).std()
                                        < ret.rolling(60).std().rolling(250).median()),

        # --- asymmetric: leave fast, come back slow ---
        "exit EMA20 / enter SMA200": asymmetric(
            px, px > ema(px, 20), px > px.rolling(200).mean()),
        "exit SMA50 / enter SMA200": asymmetric(
            px, px > px.rolling(50).mean(), px > px.rolling(200).mean()),
        "exit EMA20 / enter SMA100": asymmetric(
            px, px > ema(px, 20), px > px.rolling(100).mean()),
        "exit -12% off peak / SMA200": asymmetric(
            px, (px / px.rolling(250).max()) > 0.88, px > px.rolling(200).mean()),
        "exit volspike / enter SMA200": asymmetric(
            px, vol20 < vol20.rolling(250).median() * 1.5,
            px > px.rolling(200).mean()),
    }


def _apply(px: pd.Series, bull_raw: pd.Series) -> tuple[pd.Series, float]:
    """Equity curve for 'long TQQQ when bull, else cash', and flips/year.

    THE SHIFT LIVES HERE, once. bull_raw is computed from closes up to
    and including day t; shifting it makes day t+1's position depend on
    day t's information. Doing this per-indicator would be nineteen
    chances to forget it.
    """
    bull = bull_raw.reindex(px.index).shift(1).fillna(False).astype(bool)
    switch = (bull != bull.shift(1)).fillna(False)
    ret = px.pct_change().fillna(0.0)
    strat = np.where(bull, ret, 0.0) - switch * SWITCH_COST
    equity = pd.Series((1.0 + strat).cumprod() * 100_000.0, index=px.index)
    years = (px.index[-1] - px.index[0]).days / 365.25
    return equity, float(switch.sum()) / years


def report(name: str, equity: pd.Series, flips: float) -> dict:
    yearly = annual_returns(equity)
    complete = yearly[[ts.year < 2026 for ts in yearly.index]]
    years = (equity.index[-1] - equity.index[0]).days / 365.25
    peak = equity.cummax()
    first = complete[[ts.year <= 2020 for ts in complete.index]]
    second = complete[[ts.year >= 2021 for ts in complete.index]]

    def cagr(sub):
        return (np.prod([1 + v / 100 for v in sub]) ** (1 / max(1, len(sub))) - 1) * 100

    return {
        "name": name,
        "cagr": float((equity.iloc[-1] / equity.iloc[0]) ** (1 / years) - 1) * 100,
        "y2022": float(yearly[[i.year == 2022 for i in yearly.index]].iloc[0]),
        "worst": float(complete.min()),
        "neg": int((complete < 0).sum()),
        "maxdd": float(((peak - equity) / peak).max() * 100),
        "flips": flips,
        "first": cagr(first),
        "second": cagr(second),
        "annual": yearly,
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Regime indicators, isolated.")
    parser.add_argument("--sort", default="y2022",
                        choices=["y2022", "cagr", "worst", "maxdd"])
    args = parser.parse_args(argv)

    px = daily(TQQQ)
    vix = daily(VIXY).reindex(px.index).ffill()

    rows = [report(name, *_apply(px, sig)) for name, sig in signals(px, vix).items()]
    rows.append(report("TQQQ buy & hold", *_apply(px, pd.Series(True, index=px.index))))
    rows.sort(key=lambda r: -r[args.sort] if args.sort != "maxdd" else r[args.sort])

    print("Long TQQQ when the signal says bull, cash when it says bear. Nothing else.")
    print("Switching costs charged. Signal from day t's close, applied to day t+1.\n")
    print(f"{'indicator':<32}{'CAGR':>8}{'2022':>9}{'worst':>9}{'neg':>6}"
          f"{'maxDD':>8}{'flips/yr':>10}{'16-20':>8}{'21-26':>8}")
    print("-" * 98)
    for r in rows:
        mark = " *" if r["y2022"] > 0 else "  "
        print(f"{r['name']:<32}{r['cagr']:7.2f}%{r['y2022']:+8.1f}%{r['worst']:+8.1f}%"
              f"{r['neg']:4d}/10{r['maxdd']:7.1f}%{r['flips']:9.1f}"
              f"{r['first']:7.1f}%{r['second']:7.1f}%{mark}")

    print("\n* = positive in 2022.  16-20 / 21-26 are per-year mean CAGRs for each half;")
    print("an indicator whose two halves disagree is describing one regime, not a rule.")
    print("\nflips/yr is the whipsaw cost. Any signal that beats SMA200's -19.8% by being")
    print("faster pays for it here, and 'faster' and 'noisier' are the same property.")

    best = sorted(rows, key=lambda r: -r["cagr"])[:5]
    print("\ntop five by CAGR, year by year:")
    for r in best:
        print(f"  {r['name']:<32}" +
              "  ".join(f"{ts.year}:{v:+.0f}%" for ts, v in r["annual"].items()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
