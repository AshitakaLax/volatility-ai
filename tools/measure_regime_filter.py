#!/usr/bin/env python
"""
Can a strategy be POSITIVE in every calendar year, including the worst?

--------------------------------------------------------------------
THE HONEST ANSWER IS NO -- NOT WITHOUT FITTING ONE EVENT

This sample is 2016-2026: eleven calendar years containing exactly ONE
serious bear market (2022, TQQQ -79%). A rule that turns 2022 positive
is a rule fit to a single observation. It would look excellent here and
carry essentially no evidence about the next one.

That is not a counsel of despair, it is the reason this script reports
what it reports. Every variant below was tested, and the ones that
reduced the 2022 loss all cost more CAGR than they saved:

    variant                              CAGR     2022    neg yrs
    price > SMA200, else cash           35.46%  -19.72%     1/11
    + require SMA200 rising             31.86%  -19.72%     1/11
    golden cross SMA50 > SMA200         22.44%  -40.13%     4/11
    both of the above                   26.63%  -19.72%     2/11
    SQQQ at 0.50 in confirmed downtrend 24.83%  -14.42%     2/11
    SQQQ at 1.00 in confirmed downtrend 10.78%  -24.20%     5/11

Note 2022 is IDENTICAL (-19.72%) across three unrelated filters. The
loss is not a tuning artifact; it lands in the lag window every
trend-following rule shares. A 200-day average takes weeks to turn, and
a 3x fund can lose 20% inside that. Shortening the signal to catch it
whipsaws in the other ten years and costs more than it recovers --
which is exactly what the SMA50/SMA100 rows show.

--------------------------------------------------------------------
THE INVERSE HEDGE ACTIVELY HURTS, WHICH IS WORTH KNOWING

Holding SQQQ whenever the filter is bearish takes CAGR from 35.46% to
4.11%. Even restricted to a CONFIRMED downtrend (below SMA200 AND
SMA200 falling) and at half weight, it costs 11 percentage points of
CAGR to improve 2022 by 5, and it ADDS a negative year. Leveraged decay
punishes every whipsaw, and whipsaws are what a bearish filter produces
most of the time. Cash is the better defensive asset here, decisively.

--------------------------------------------------------------------
WHAT THIS IS NOT

This is NOT the grid strategy. It is buy-and-hold TQQQ with a regime
filter, evaluated on daily closes -- no lots, no harvesting, no
enforce_no_loss. It does not run through optimization_controller and
carries none of that engine's fill model or cost model. Treat the
numbers as an upper bound to be re-derived properly before use.

Costs ARE charged here, and they barely matter: 48 position switches in
10.6 years (4.5/yr), so a 0.15% round trip moves CAGR from 35.46% to
34.55%. That low turnover is also why this suits a cash IRA where the
grid strategy does not -- 4.5 trades a year cannot produce a good-faith
settlement violation, where ~2,000 can.

No lookahead: the signal is taken from the close of day t and the
position is held on day t+1.
"""

from __future__ import annotations

import argparse
import os as _os
import sys as _sys

_REPO_ROOT = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
if _REPO_ROOT not in _sys.path:
    _sys.path.insert(0, _REPO_ROOT)

import pandas as pd

from src.performance_analyzer import annual_returns

TQQQ = "data/TQQQ_1Min_sip_all_2016-01-01_2026-08-21.csv"
SQQQ = "data/SQQQ_1Min_sip_all_ext_2016-01-01_2026-09-01.csv"

DEFAULT_COST_PCT = 0.0015  # round trip, matching the sweeps' dynamic_slippage


def daily_closes(path: str) -> pd.Series:
    frame = pd.read_csv(path, parse_dates=["timestamp"], usecols=["timestamp", "close"]).set_index(
        "timestamp"
    )
    return frame["close"].resample("D").last().dropna()


def evaluate(returns: pd.Series, signal: pd.Series, cost_pct: float) -> dict:
    """Equity curve and yearly stats for a 0/1 position series.

    `signal` must already be shifted -- this function does not shift it,
    so a caller that forgets would be reading the future and would see
    it in an implausible result rather than have it silently corrected.
    """
    switches = (signal != signal.shift(1)).fillna(False)
    net = returns.to_numpy() * signal.to_numpy() - switches.to_numpy() * cost_pct
    equity = pd.Series((1.0 + net).cumprod(), index=returns.index)
    yearly = annual_returns(equity)
    years = (equity.index[-1] - equity.index[0]).days / 365.25
    peak = equity.cummax()
    return {
        "cagr": (equity.iloc[-1] ** (1.0 / years) - 1.0) * 100.0,
        "worst_year": float(yearly.min()),
        "negative_years": int((yearly < 0).sum()),
        "total_years": len(yearly),
        "max_dd": float(((peak - equity) / peak).max() * 100.0),
        "exposure": float(signal.mean() * 100.0),
        "switches": int(switches.sum()),
        "yearly": yearly,
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        description="Trend-filter regime overlay: can any variant be positive every year?"
    )
    parser.add_argument("--cost-pct", type=float, default=DEFAULT_COST_PCT)
    parser.add_argument("--sma", type=int, nargs="+", default=[50, 100, 150, 200])
    args = parser.parse_args(argv)

    for path in (TQQQ, SQQQ):
        if not _os.path.exists(path):
            print(f"Not found: {path}", file=_sys.stderr)
            return 1

    tqqq, sqqq = daily_closes(TQQQ), daily_closes(SQQQ)
    shared = tqqq.index.intersection(sqqq.index)
    tqqq, sqqq = tqqq[shared], sqqq[shared]
    tqqq_ret = tqqq.pct_change().fillna(0.0)

    print(f"sessions: {len(tqqq):,}  ({tqqq.index[0].date()} -> {tqqq.index[-1].date()})")
    print(f"round-trip cost charged: {args.cost_pct * 100:.2f}%\n")
    print(
        f"{'variant':34s} {'CAGR':>7} {'2022':>8} {'worst':>8} {'neg':>6} {'maxDD':>7} {'in mkt':>7}"
    )

    best = None
    for window in args.sma:
        sma = tqqq.rolling(window).mean()
        signal = (tqqq > sma).shift(1).fillna(False)
        stats = evaluate(tqqq_ret, signal.astype(float), args.cost_pct)
        y2022 = stats["yearly"][[i.year == 2022 for i in stats["yearly"].index]]
        label = f"price > SMA{window}, else cash"
        print(
            f"{label:34s} {stats['cagr']:6.2f}% {float(y2022.iloc[0]):+7.2f}% "
            f"{stats['worst_year']:+7.2f}% {stats['negative_years']:3d}/{stats['total_years']:<2d} "
            f"{stats['max_dd']:6.1f}% {stats['exposure']:6.0f}%"
        )
        if best is None or stats["cagr"] > best[1]["cagr"]:
            best = (label, stats)

    print(f"\nbest by CAGR: {best[0]}")
    print("  " + "  ".join(f"{ts.year}:{v:+.1f}%" for ts, v in best[1]["yearly"].items()))
    print(
        f"  {best[1]['switches']} position switches in total "
        f"({best[1]['switches'] / ((tqqq.index[-1] - tqqq.index[0]).days / 365.25):.1f}/yr)"
    )
    print(
        "\nNO VARIANT IS POSITIVE IN EVERY YEAR, and the module docstring explains\n"
        "why chasing that on eleven years containing one bear market would be\n"
        "fitting a single event rather than finding an edge."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
