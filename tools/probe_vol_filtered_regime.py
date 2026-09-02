#!/usr/bin/env python
"""
Hold the trend when trend AND volatility agree; harvest dips when they
do not. The synthesis of every measurement in this project so far.

--------------------------------------------------------------------
WHERE EACH PIECE CAME FROM

tools/probe_regime_signals.py compared nineteen regime indicators
through an identical shell (long TQQQ when bull, cash when bear). Two
findings drive this file:

  1. FASTER IS WORSE. Every attempt to fix SMA200's latency by using a
     quicker signal made 2022 worse, not better -- EMA20 -65.0%, SMA50
     -51.5%, RSI(14) -65.7% against SMA200's -19.8%. 2022 was full of
     violent bear-market rallies, and a fast signal buys every one of
     them. Latency was the wrong diagnosis.

  2. A VOLATILITY FILTER IS WHAT WORKS. Requiring 20-day realised vol
     to sit below its own trailing 250-day 75th percentile, ON TOP of
     SMA200, beat the incumbent on every axis at once: 38.98% CAGR vs
     34.57%, worst year -1.0% vs -19.8%, max drawdown 35.6% vs 50.2%.
     Robust across percentiles 0.40-0.75 and vol windows 20-30, and it
     collapses only when the lookback is stretched to 500 days.

--------------------------------------------------------------------
THE THING THAT NUMBER IS NOT

The filtered signal returns exactly +0.0% in 2022, and that is not a
profit. It is CASH: the filter holds the book out of the market for
0 of 251 trading days that year. Every percentile from 0.40 to 0.75
prints the identical +0.0% for exactly that reason, which is the tell.

Avoiding a bear market and earning through one are different claims,
and the request was the second. So this file spends those 251 days on
the tactic that was actually measured to work inside drawdowns -- the
5% step / 4% target escalating dip book from
tools/probe_downturn_tactics.py, positive in 14 of 14 episodes.

--------------------------------------------------------------------
STRUCTURE

  bull   SMA200 AND vol20 below its trailing 75th percentile.
         Accumulate toward full exposure and HOLD -- open lots are
         retargeted out of reach so nothing harvests, which is worth
         ~20pp of CAGR over harvesting the same trend.
  bear   anything else. Run the escalating dip book.
  flip   liquidate the whole book in both directions, which requires
         SellReason.SIGNAL_EXIT -- a rotation must close lots
         regardless of P&L.

The signal is computed on DAILY closes and shifted one day, so the
position held on day t+1 is decided by information that closed on day
t. It is precomputed into a date -> bool map rather than recomputed
bar-by-bar inside the strategy: same values, and the shift lives in one
place where it can be checked.

Usage:
    python tools/probe_vol_filtered_regime.py
"""

from __future__ import annotations

import argparse
import os as _os
import sys as _sys

_REPO_ROOT = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
if _REPO_ROOT not in _sys.path:
    _sys.path.insert(0, _REPO_ROOT)

import logging  # noqa: E402

import pandas as pd  # noqa: E402

from optimization_controller import OptimizationController  # noqa: E402
from src.config import BacktestConfig  # noqa: E402
from src.high_frequency_sizing import HighFrequencyLocalReferenceSizing  # noqa: E402
from src.performance_analyzer import annual_returns  # noqa: E402
from src.risk_manager import RiskManager  # noqa: E402

DATA = "data/TQQQ_1Min_sip_all_2016-01-01_2026-08-21.csv"
HOLD_TARGET = 50.0  # finite but unreachable, so persistence's derivation check still holds


def build_signal(px: pd.Series, *, trend: int, vol_win: int, lookback: int, q: float) -> dict:
    """date -> is_bull, already shifted so day t+1 uses day t's close."""
    vol = px.pct_change().rolling(vol_win).std()
    bull = (px > px.rolling(trend).mean()) & (vol < vol.rolling(lookback).quantile(q))
    bull = bull.shift(1).fillna(False)
    return {ts.date(): bool(v) for ts, v in bull.items()}


class VolFilteredRegime(HighFrequencyLocalReferenceSizing):
    """Hold when trend and calm agree; harvest dips otherwise."""

    def __init__(self, *args, signal=None, bull_step=0.005, bear_step=0.05,
                 bear_target=0.04, bull_lot_scale=2.0, max_mult=400.0, dd_ref=0.75,
                 hold_in_bull=True, use_dip_in_bear=True, **kwargs):
        super().__init__(*args, **kwargs)
        self.signal = signal or {}
        self.bull_step, self.bear_step = bull_step, bear_step
        self.bear_target, self.bull_lot_scale = bear_target, bull_lot_scale
        self.max_mult, self.dd_ref = max_mult, dd_ref
        self.hold_in_bull, self.use_dip_in_bear = hold_in_bull, use_dip_in_bear
        self._is_bull = False
        self._flipped = False
        self._price_peak = None
        self._seen = False

    def wants_lot_retargeting(self) -> bool:
        # Must be True or decision_cycle early-outs and adjust_profit_target
        # never runs -- silently, with identical results either way.
        return True

    def record_tick(self, context) -> None:
        super().record_tick(context)
        if context.price <= 0:
            return
        was = self._is_bull
        self._is_bull = self.signal.get(context.timestamp.date(), False)
        self._flipped = self._seen and (was != self._is_bull)
        self._seen = True
        self._price_peak = (context.price if self._price_peak is None
                            else max(self._price_peak, context.price))

    def _grid_trigger_level(self, context, last_buy_price: float, step: float) -> float:
        high = self._rolling_high.value
        ref = last_buy_price if high is None else max(last_buy_price, high)
        return ref * (1.0 - (self.bull_step if self._is_bull else self.bear_step))

    def calculate_trade_value(self, context) -> float:
        base = super().calculate_trade_value(context)
        if self._is_bull:
            return base * self.bull_lot_scale
        if not self.use_dip_in_bear:
            return 0.0  # the control: sit in cash, like the daily-level study
        if not self._price_peak:
            return base
        dd = 1.0 - context.price / self._price_peak
        if dd <= 0:
            return base
        return base * min(self.max_mult, self.max_mult ** (dd / self.dd_ref))

    def adjust_profit_target(self, lot, context):
        if not self.hold_in_bull:
            return None
        want = HOLD_TARGET if self._is_bull else self.bear_target
        return want if lot.profit_target != want else None

    def lots_to_liquidate(self, open_lots, context) -> list:
        return list(open_lots) if self._flipped else []


def run(controller, cfg, signal, *, cap, dip_in_bear, hold_in_bull, bull_scale):
    params = dict(cfg.strategy.strategy_params)
    params.update(per_lot_pct=0.02, signal=signal, bull_step=0.005, bear_step=0.05,
                  bear_target=0.04, bull_lot_scale=bull_scale, max_mult=400.0,
                  dd_ref=0.75, hold_in_bull=hold_in_bull, use_dip_in_bear=dip_in_bear)
    summary, full = controller.run_sweep(
        grid_steps=[0.05], profit_targets=[0.04],
        strategy_class=VolFilteredRegime, strategy_params_grid=[params],
        cost_model=cfg.costs.build(),
        risk_manager=RiskManager(max_concurrent_lots=6000, max_total_exposure_pct=cap),
        fill_model="intrabar", intrabar_priority="sell_first",
        enforce_no_loss=True, allow_signal_exit=True,
        on_flat_reentry="stale_reference", return_full_results=True,
    )
    return summary.iloc[0], annual_returns(full[0].equity_curve)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Vol-filtered regime, dip book in bear.")
    parser.add_argument("--quiet", action="store_true", default=True)
    args = parser.parse_args(argv)
    if args.quiet:
        logging.disable(logging.WARNING)

    cfg = BacktestConfig.from_yaml("config/probe_dipbuy_full.yaml")
    frame = pd.read_csv(DATA, parse_dates=["timestamp"]).set_index("timestamp")
    controller = OptimizationController(historical_data=frame)
    px = frame["close"].resample("D").last().dropna()
    signal = build_signal(px, trend=200, vol_win=20, lookback=250, q=0.75)

    print("bull = SMA200 AND vol20 below its trailing 75th percentile")
    print("Reference points, all measured earlier in this project:")
    print("  SMA200-else-cash            34.57% CAGR   2022 -19.8%   maxDD 50.2%")
    print("  vol-filtered, else CASH     38.98% CAGR   2022  +0.0%   maxDD 35.6%  (0/251 days invested)")
    print("  regime harvest bull         13.79% CAGR   2022  +3.6%   maxDD 44.3%\n")

    print(f"{'bear leg':>10}{'hold':>6}{'cap':>6}{'bullx':>7}{'CAGR':>9}{'maxDD':>8}"
          f"{'worst':>8}{'neg':>7}{'2022':>8}{'exits':>8}")
    for dip_in_bear in (True, False):
        for cap, scale in ((1.00, 2.0), (0.50, 5.0)):
            for hold in (True, False) if dip_in_bear else (True,):
                row, yearly = run(controller, cfg, signal, cap=cap, dip_in_bear=dip_in_bear,
                                  hold_in_bull=hold, bull_scale=scale)
                complete = yearly[[t.year < 2026 for t in yearly.index]]
                y22 = yearly[[t.year == 2022 for t in yearly.index]].iloc[0]
                print(f"{'dip' if dip_in_bear else 'cash':>10}{str(hold):>6}{cap:6.2f}"
                      f"{scale:6.1f}x{row['CAGR %']:8.2f}%{row['Max Drawdown %']:7.1f}%"
                      f"{complete.min():+7.1f}%{int((complete < 0).sum()):5d}/10"
                      f"{y22:+7.1f}%{int(row['Signal Exit Count']):8d}")
                print("          " + "  ".join(f"{t.year}:{v:+.0f}%" for t, v in yearly.items()))

    print("\n'worst'/'neg' are COMPLETE years only; 2026 is a Jan-Aug stub.")
    print("hold=False is the control -- identical but bull lots harvest at 4%.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
