#!/usr/bin/env python
"""
Which instruments suit a volatility-harvesting grid? Daily bars, minutes.

--------------------------------------------------------------------
WHY A DAILY SCREEN AT ALL, WHEN THE STRATEGY TRADES MINUTES

tools/screen_instruments.py answers a similar question on 1-minute
data and needs roughly a million bars per candidate to do it. It has
been attempted twice and failed both times on the download
(output/instrument_screen_*.log, "No candidates succeeded"), which is
its own argument: an hours-long fetch that must complete for ANY
result is a bad shape for a question whose whole purpose is to narrow
a list.

Daily bars settle the ranking. The properties that decide whether this
strategy can work -- how much the thing moves, whether it oscillates
or trends, and whether it survives its own leverage -- are all visible
at daily resolution and none of them change character at one minute.
Use this to pick one or two candidates, then spend the minute-bar
download on those.

--------------------------------------------------------------------
WHAT IS MEASURED, AND WHY EACH ONE DECIDES SOMETHING

The frontier sweep's regime breakdown is the premise: this strategy
wins in down and crash months (100% win rate at crash < -15%) and
loses in rallies (6% win rate at rally > +15%). So the instrument it
wants is volatile and RANGE-BOUND, and the instrument it fights is one
with a strong secular trend -- which is exactly what TQQQ is, and what
the strategy has been fighting the whole time.

  vol         Annualised daily volatility. The harvestable amplitude.
              RSP's 14.2% is the reason the grid could not work there:
              there is simply not much to harvest.

  efficiency  |net displacement| / sum|daily moves|. LOW is good. It
              is the fraction of all the travelling that ended up
              going somewhere -- a one-way mover scores high and gives
              a harvester nothing but capped upside.

  VR(5)       Variance ratio. Var(5-day return) / (5 x Var(1-day)).
              BELOW 1 is mean-reverting, above 1 trending. This is the
              direct test, where efficiency is the indirect one.

  B&H CAGR    Survivability, and the bar. A candidate that decayed to
              nothing under its own leverage is unusable no matter how
              well it scores elsewhere, and a candidate whose
              buy-and-hold already beats what a strategy could realise
              is one where the strategy has nothing to add.

NO COMPOSITE SCORE IS PRINTED, deliberately. Weighting volatility
against mean-reversion against survivability is the judgement being
asked for, and folding it into one number would hide the trade-off
rather than inform it.
"""

from __future__ import annotations

import argparse
import os
import sys
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

TRADING_DAYS = 252

# Leveraged/volatile candidates, plus controls. TQQQ is the known-good
# reference and RSP the known-bad one, so the table has both ends of the
# answer already in it and a new candidate can be read against them
# rather than against an abstract threshold.
DEFAULT_SYMBOLS = [
    "TQQQ",  # 3x Nasdaq-100 -- the incumbent, strongly trending
    "RSP",  # 1x equal-weight S&P -- measured, grid does not work
    "SPY",  # 1x S&P -- plain control
    "TNA",  # 3x Russell 2000 -- small caps, more range-bound
    "SOXL",  # 3x semiconductors -- cyclical
    "FAS",  # 3x financials -- cyclical
    "SPXL",  # 3x S&P -- large-cap control at leverage
    "LABU",  # 3x biotech -- high vol, range-bound
    "YINN",  # 3x China -- high vol, no secular trend this window
    "ERX",  # 2x energy -- cyclical
    "TMF",  # 3x long treasuries -- different asset class
    "SQQQ",  # -3x Nasdaq -- structurally decaying, included as a warning
]


def fetch_daily(symbols: list[str], start: str, end: str) -> dict[str, pd.Series]:
    from alpaca.data.historical import StockHistoricalDataClient
    from alpaca.data.requests import StockBarsRequest
    from alpaca.data.timeframe import TimeFrame

    from src.secrets import load_live_credentials

    creds = load_live_credentials()
    client = StockHistoricalDataClient(creds.api_key_id, creds.api_secret_key)
    out: dict[str, pd.Series] = {}
    for sym in symbols:
        try:
            bars = client.get_stock_bars(
                StockBarsRequest(
                    symbol_or_symbols=sym,
                    timeframe=TimeFrame.Day,
                    start=datetime.fromisoformat(start),
                    end=datetime.fromisoformat(end),
                    adjustment="all",
                )
            ).df
            if bars.empty:
                print(f"  {sym}: no data", file=sys.stderr)
                continue
            s = (
                bars.xs(sym, level="symbol")["close"]
                if "symbol" in bars.index.names
                else bars["close"]
            )
            out[sym] = s.dropna()
            print(f"  {sym}: {len(out[sym])} daily bars", file=sys.stderr)
        except Exception as exc:
            print(f"  {sym}: FAILED {type(exc).__name__}: {exc}", file=sys.stderr)
    return out


def variance_ratio(returns: pd.Series, k: int) -> float:
    """Var(k-period) / (k * Var(1-period)). Below 1 = mean-reverting."""
    r1 = returns.dropna()
    if len(r1) < k * 10:
        return float("nan")
    rk = r1.rolling(k).sum().dropna()
    v1, vk = r1.var(), rk.var()
    return vk / (k * v1) if v1 > 0 else float("nan")


def profile(close: pd.Series, symbol: str) -> dict:
    r = close.pct_change().dropna()
    logr = np.log(close).diff().dropna()
    years = (close.index[-1] - close.index[0]).days / 365.25
    cagr = (close.iloc[-1] / close.iloc[0]) ** (1 / years) - 1
    dd = (close / close.cummax() - 1).min()
    gross = logr.abs().sum()
    net = abs(np.log(close.iloc[-1] / close.iloc[0]))
    return {
        "symbol": symbol,
        "vol %": r.std() * np.sqrt(TRADING_DAYS) * 100,
        "effic %": (net / gross * 100) if gross else float("nan"),
        "VR(5)": variance_ratio(r, 5),
        "B&H CAGR %": cagr * 100,
        "B&H DD %": dd * 100,
        "years": years,
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    parser.add_argument("--symbols", nargs="+", default=DEFAULT_SYMBOLS)
    parser.add_argument("--start", default="2016-01-01")
    parser.add_argument("--end", default=datetime.now().strftime("%Y-%m-%d"))
    args = parser.parse_args(argv)

    if not os.environ.get("APCA_API_KEY_ID"):
        print("APCA_API_KEY_ID is not set -- source .env first.", file=sys.stderr)
        return 2

    print(f"Fetching daily bars {args.start} to {args.end} ...", file=sys.stderr)
    series = fetch_daily(args.symbols, args.start, args.end)
    if not series:
        print("No candidates returned data.", file=sys.stderr)
        return 1

    table = pd.DataFrame([profile(s, sym) for sym, s in series.items()])
    table = table.sort_values("vol %", ascending=False)
    print()
    print(table.to_string(index=False, float_format=lambda v: f"{v:9.2f}"))
    print()
    print("  vol      higher = more to harvest")
    print("  effic    LOWER is better: fraction of travel that went somewhere")
    print("  VR(5)    BELOW 1 = mean-reverting, above 1 = trending")
    print()
    print("  Read TQQQ and RSP as the calibration points: the grid works on the")
    print("  first and was measured not to work on the second.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
