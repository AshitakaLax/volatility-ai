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
FINDINGS, AND THE ONE THAT REVERSED ON INSPECTION

VOLATILITY TARGETING IS CRASH INSURANCE WITH A PRICE, NOT A FREE
IMPROVEMENT. Over the full sample it looks like a clean win -- Sharpe
0.76-0.78 across every target from 10% to 26%, against 0.73 for holding,
and an improvement that flat across a parameter usually means a real
effect rather than a fitted one. It is not:

    Sharpe                     full sample   COVID removed
    hold                          0.73           0.88
    voltarget_22                  0.77           0.85
    voltarget_12                  0.78           0.79

Excluding February-June 2020 reverses it completely and holding wins on
every risk-adjusted measure. Without that crash, hold's own worst
drawdown is only -21.4%, and voltarget_22 gives up a point of CAGR to
improve it to -20.8%. So the honest description is not "better
risk-adjusted returns" -- it is a hedge against a COVID-shaped event,
costing roughly 1.4 points of CAGR a year at target 22% and 3.8 at 12%.
Whether that is worth buying is a real question; pretending it is free
is not.

The drawdown reduction itself IS robust, because it is mechanical: less
exposure is less drawdown, in every subsample. It is only the claim of a
BETTER RETURN PER UNIT OF RISK that rests on one event.

LEVERAGE MAKES IT WORSE, which was not the expected answer. voltarget_12
earns a better Sharpe than holding while averaging 81% invested, so
levering it back up should convert that into return. It does not: at
1.5x and 2.0x the CAGR FALLS (8.12% and 8.16% against 8.70% unlevered)
and drawdown worsens, because borrowing costs more than idle cash earns
and turnover roughly doubles. Priced at a borrow rate 1.5% over the cash
rate.

THE DIP-LADDER COMBINATION WAS THE SAME BET TWICE. It posted the best
headline Sharpe of anything here, 0.84. The ladder ratchets to full
exposure on 2018-12-24 and from that day differs from plain
voltarget_12 on ZERO days; restricted to the post-ramp sample the two
are identical to two decimals. Its edge was holding less during
2016-2018 -- one path through one sample.

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


def metrics(equity: pd.Series, label: str, switches: int = 0, exposure=None) -> dict:
    years = (equity.index[-1] - equity.index[0]).days / 365.25
    cagr = (equity.iloc[-1] / equity.iloc[0]) ** (1 / years) - 1
    dd = (equity / equity.cummax() - 1).min()
    annual = equity.resample("YE").last().pct_change().dropna()
    daily = equity.pct_change().dropna()
    sharpe = (daily.mean() / daily.std()) * np.sqrt(TRADING_DAYS) if daily.std() else float("nan")
    # Ulcer index: RMS of the drawdown path, not its single worst point.
    # A strategy that spends years 20% under water and one that touches
    # -39% for a fortnight can share a max drawdown; only this separates
    # them, and for a risk question that difference is the whole point.
    underwater = equity / equity.cummax() - 1
    ulcer = np.sqrt((underwater**2).mean()) * 100
    return {
        "variant": label,
        "CAGR %": cagr * 100,
        "MaxDD %": dd * 100,
        "Ulcer %": ulcer,
        "Sharpe": sharpe,
        "Return/DD": (cagr * 100) / abs(dd * 100) if dd else float("nan"),
        "Worst yr %": annual.min() * 100,
        "Neg yrs": int((annual < 0).sum()),
        "InMkt %": float(exposure.mean() * 100) if exposure is not None else 100.0,
        "Switches": switches,
    }


def run_weighted(
    close: pd.Series, weight: pd.Series, cash_yield: float, cost_pct: float
) -> tuple[pd.Series, int]:
    """Equity for a series of target weights, held over the NEXT day.

    weight is shifted by one bar before it is applied. That single line
    is the difference between a measurement and a look at the answer.
    """
    # Upper bound is the variant's own; clipping to 1.0 here would
    # silently neuter the leveraged rows and report them as if they
    # had been run.
    weight = weight.shift(1).fillna(0.0).clip(lower=0.0)
    asset = close.pct_change().fillna(0.0)
    daily_cash = (1 + cash_yield) ** (1 / TRADING_DAYS) - 1
    # Weight above 1.0 is BORROWED, and borrowed money costs more than
    # idle cash earns. Charging the same rate both ways would make
    # leverage look free, which is the whole trap in these rows.
    borrow_rate = cash_yield + 0.015
    daily_borrow = (1 + borrow_rate) ** (1 / TRADING_DAYS) - 1
    idle = (1 - weight).clip(lower=0.0)
    borrowed = (weight - 1).clip(lower=0.0)
    gross = weight * asset + idle * daily_cash - borrowed * daily_borrow
    turnover = weight.diff().abs().fillna(0.0)
    net = gross - turnover * cost_pct
    return (1 + net).cumprod(), int((turnover > 1e-9).sum()), weight


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

    # VOLATILITY TARGETING -- the technique built for this exact
    # question, and the one the first pass of this probe missed.
    #
    # The trend filters here are BINARY: fully in or fully out, so every
    # false signal costs a whole position and RSP's 67 SMA200 crossings
    # cost 5.7 points of CAGR to buy 14 points of drawdown. Volatility
    # targeting is continuous instead -- exposure is target/realised, so
    # a rise in volatility trims the position rather than closing it,
    # and there is no threshold to whipsaw across.
    #
    # It also aims at the right thing. A trend filter is a bet on
    # direction, which is hard. This is a bet that volatility is
    # PERSISTENT, which is among the most durable facts in the data:
    # today's realised vol predicts tomorrow's far better than today's
    # return predicts tomorrow's.
    #
    # The blend of fast and slow windows is deliberate. A 20-day
    # estimate alone reacts fast and trades constantly; a 60-day alone
    # is calm and late. Averaging them keeps most of the response for
    # much less turnover.
    vol_fast = ret.rolling(20).std() * np.sqrt(TRADING_DAYS)
    vol_slow = ret.rolling(60).std() * np.sqrt(TRADING_DAYS)
    vol_est = ((vol_fast + vol_slow) / 2).where(ret.rolling(60).count() >= 60)

    for target in (0.10, 0.12, 0.15, 0.18, 0.22, 0.26):
        # Capped at 1.0: the target account is a CASH account, so
        # leverage is not available and reporting an uncapped result
        # would be reporting a strategy that cannot be run.
        w = (target / vol_est).clip(0.0, 1.0)
        # Rounded to 5% steps so a one-day vol wobble does not generate a
        # trade. Turnover is the cost that kills continuous sizing.
        out[f"voltarget_{int(target * 100)}"] = (w * 20).round() / 20

    # Volatility targeting with the trend filter on top -- does the
    # direction bet still add anything once size is already being
    # managed, or is it redundant?
    w12 = ((0.12 / vol_est).clip(0.0, 1.0) * 20).round() / 20
    out["voltarget_12_sma200"] = w12.where((close > sma200) & warm, 0.0)

    # LEVERAGED VOL TARGETING, to price what the cap is costing.
    #
    # voltarget_12 earns a better Sharpe than buy-and-hold while
    # averaging ~81% invested, which is the standard shape of this
    # result: the risk-adjusted return improved and the absolute one
    # fell because the position got smaller. Leverage is what converts
    # the first into the second, and these rows say how much is on the
    # table rather than leaving it as a claim.
    #
    # THESE ARE NOT RUNNABLE IN THE TARGET ACCOUNT AS WRITTEN. It is a
    # cash IRA: no margin. They are priced here because the exposure is
    # reachable another way -- an equal-weight core plus a small
    # leveraged S&P sleeve approximates it -- and because a cap chosen
    # without knowing its cost is a guess.
    for cap in (1.5, 2.0):
        w = (0.12 / vol_est).clip(0.0, cap)
        out[f"voltarget_12_lev{cap:g}"] = (w * 20).round() / 20

    # Vol targeting layered on the dip ladder. MEASURED TO BE THE SAME
    # BET TWICE: the ladder ratchets to full exposure on 2018-12-24 and
    # from then on this differs from plain voltarget_12 on ZERO days.
    # Its better headline Sharpe comes entirely from holding less during
    # 2016-2018, which is one path through one sample, not a mechanism.
    # Kept so the finding stays visible rather than being quietly
    # deleted along with the row that produced it.
    ladder_w = out["dip_ladder"]
    out["voltarget_12_ladder"] = pd.concat([w12, ladder_w], axis=1).min(axis=1)
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
            equity, switches, held = run_weighted(close, weight, cash_yield, args.cost_pct)
            rows.append(metrics(equity, label, switches, held))
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
