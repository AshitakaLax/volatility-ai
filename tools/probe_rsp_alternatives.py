#!/usr/bin/env python
"""
RSP: is there anything that beats simply holding it?

--------------------------------------------------------------------
WHY THIS EXISTS

The grid strategy does not work on RSP, and the sweep that established
that was monotonic enough to be worth stating plainly
(output/probe_rsp_tight.csv plus the earlier probe_rsp_scaled.csv):

    profit target   CAGR     max DD
    0.5%            9.13%    39.99%
    1%             10.69%    40.04%
    2%             11.35%    40.04%
    4%             11.89%    40.04%
    5%             12.27%    40.04%
    40%            12.44%    40.04%
    buy and hold   12.52%    39.11%

The less it harvested, the better it did, converging on buy-and-hold
from below with drawdown pinned near 40% throughout. The mechanism is
not subtle: RSP rose 251% over the window, and every sale swaps an
uncapped position for one capped at +X%. enforce_no_loss means the book
can only ever cap winners. Tuning that is tuning the wrong thing.

So this asks a different question. Buy-and-hold is the bar; what
MECHANISM, not what parameter, could beat it?

--------------------------------------------------------------------
WHAT IS TESTED, AND WHY EACH ONE IS HERE

Every variant is evaluated on DAILY bars. Minute-cadence regime
flipping has already produced one wrong answer in this project -- a
regime probe that flipped on minute bars logged 7,334 signal exits and
was being compared against a daily benchmark, which is two different
strategies rather than one comparison.

  hold            The bar. 100% invested from the first bar.
  sma200          Hold above the 200-day average, cash below. The
                  variant that measured best on TQQQ.
  sma200_rising   The same, but also requiring the average itself to be
                  rising -- refuses to buy a bounce inside a downtrend.
  vol_filter      Out when trailing realized vol is in its own top
                  decile. Targets the drawdown rather than the trend.
  dip_ladder      Holds cash and deploys it in tranches as drawdown
                  from the high deepens. The one variant that can beat
                  buy-and-hold on ENTRY PRICE rather than on timing.

--------------------------------------------------------------------
TWO THINGS THAT WOULD MAKE THIS DISHONEST, AND ARE HANDLED

LOOKAHEAD. Every signal is computed from data up to and including day
t, and the position it implies is held over day t+1. The shift is
explicit, not implied, because a regime filter that acts on the same
day's close is reading the future and will look extraordinary.

CASH IS NOT FREE, AND IT IS NOT ZERO EITHER. A filter that sits out
earns something -- the target account sweeps to a money-market fund --
and this project has already measured that ignoring it understates
cash-heavy strategies by roughly 1 percentage point of CAGR per point
of yield. Reporting only the 0% case would flatter buy-and-hold; only
the 4% case would flatter the filters. Both are printed.

Switching costs are charged on every regime change, so a filter that
flips weekly pays for it.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

TRADING_DAYS = 252


def load_daily(path: str) -> pd.Series:
    """Daily closes from a 1-minute file."""
    df = pd.read_csv(path, usecols=["timestamp", "close"], parse_dates=["timestamp"])
    return df.set_index("timestamp")["close"].resample("1D").last().dropna()


def metrics(equity: pd.Series, label: str, switches: int = 0) -> dict:
    years = (equity.index[-1] - equity.index[0]).days / 365.25
    total = equity.iloc[-1] / equity.iloc[0] - 1
    cagr = (equity.iloc[-1] / equity.iloc[0]) ** (1 / years) - 1
    dd = (equity / equity.cummax() - 1).min()
    annual = equity.resample("YE").last().pct_change().dropna()
    return {
        "variant": label,
        "CAGR %": cagr * 100,
        "Total %": total * 100,
        "MaxDD %": dd * 100,
        "Return/DD": (cagr * 100) / abs(dd * 100) if dd else float("nan"),
        "Worst yr %": annual.min() * 100,
        "Neg yrs": int((annual < 0).sum()),
        "Switches": switches,
    }


def run_weighted(
    close: pd.Series, weight: pd.Series, cash_yield: float, cost_pct: float
) -> tuple[pd.Series, int]:
    """Equity for a series of target weights, held over the NEXT day.

    weight is shifted by one bar before it is applied. That single line
    is the difference between a measurement and a look at the answer.
    """
    weight = weight.shift(1).fillna(0.0).clip(0.0, 1.0)
    asset = close.pct_change().fillna(0.0)
    daily_cash = (1 + cash_yield) ** (1 / TRADING_DAYS) - 1
    gross = weight * asset + (1 - weight) * daily_cash
    turnover = weight.diff().abs().fillna(0.0)
    net = gross - turnover * cost_pct
    return (1 + net).cumprod(), int((turnover > 1e-9).sum())


def variants(close: pd.Series) -> dict[str, pd.Series]:
    """Target weight per day, from information available that day."""
    sma200 = close.rolling(200).mean()
    # Stand aside until the window is FULL. rolling(...).mean() yields a
    # value from the first bar unless min_periods is respected, and a
    # partial mean is a different signal wearing the same name -- that
    # exact mistake made a previous probe's worst year an artifact.
    warm = close.rolling(200).count() >= 200

    ret = close.pct_change()
    vol = ret.rolling(20).std() * np.sqrt(TRADING_DAYS)
    vol_warm = ret.rolling(20).count() >= 20
    # Expanding quantile, so the threshold uses only past data. A single
    # quantile over the whole sample would know the future.
    vol_cut = vol.expanding(min_periods=250).quantile(0.90)

    drawdown = close / close.cummax() - 1

    out = {
        "hold": pd.Series(1.0, index=close.index),
        "sma200": ((close > sma200) & warm).astype(float),
        "sma200_rising": ((close > sma200) & (sma200.diff() > 0) & warm).astype(float),
        "vol_filter": (~((vol > vol_cut) & vol_warm.astype(bool))).astype(float),
    }

    # Dip ladder: cash on the sidelines, deployed as the drawdown
    # deepens, never sold back. Beats buy-and-hold only if entry price
    # beats t=0 -- the one mechanism here that is about WHERE you buy
    # rather than WHEN you are out.
    ladder = pd.Series(0.25, index=close.index)
    ladder[drawdown <= -0.05] = 0.50
    ladder[drawdown <= -0.10] = 0.75
    ladder[drawdown <= -0.20] = 1.00
    out["dip_ladder"] = ladder.cummax()  # ratchets up, never back down
    return out


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    parser.add_argument(
        "--data", default="data/RSP_1Min_sip_all_rthuniform_2016-01-01_2026-08-30.csv"
    )
    parser.add_argument(
        "--cost-pct",
        type=float,
        default=0.0005,
        help="Charged on each unit of weight changed (default 5bps).",
    )
    parser.add_argument(
        "--cash-yields",
        type=float,
        nargs="+",
        default=[0.0, 0.04],
        help="Yields to report. Both ends are printed on purpose -- see the "
        "module docstring on why either alone flatters one side.",
    )
    args = parser.parse_args(argv)

    close = load_daily(args.data)
    print(
        f"RSP daily, {close.index[0]:%Y-%m-%d} to {close.index[-1]:%Y-%m-%d} "
        f"({len(close)} sessions)\n"
    )

    for cash_yield in args.cash_yields:
        rows = []
        for label, weight in variants(close).items():
            equity, switches = run_weighted(close, weight, cash_yield, args.cost_pct)
            rows.append(metrics(equity, label, switches))
        table = pd.DataFrame(rows).sort_values("CAGR %", ascending=False)
        print(f"=== idle cash earns {cash_yield * 100:.1f}% ===")
        print(table.to_string(index=False, float_format=lambda v: f"{v:8.2f}"))
        print()

    print(
        "Read the drawdown column, not just CAGR: a variant that trails on\n"
        "return while halving the drawdown is a different instrument, not a\n"
        "worse one, and which you want is a question this script cannot answer."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
