#!/usr/bin/env python
"""
The regime strategy as ONE simulation, not two spliced return streams.

WHY THIS EXISTS. tools/probe_regime_combo.py measured "TQQQ while above
the 200-day average, deep-dip escalation while below" by simulating each
leg separately and switching between their daily returns. That reported
43.50% CAGR with zero negative years -- but it assumed a clean handoff at
every regime flip, which is precisely the thing that cannot be assumed.

A real implementation has ONE ledger. Lots opened in a bear regime are
still open when the regime turns bull, and enforce_no_loss forbids
closing them at a loss. The splice quietly deleted that inventory at
each transition. This runs both legs through a single simulation so the
carried inventory is real, and the gap between the two numbers is the
size of the error the approximation was making.

--------------------------------------------------------------------
WHAT THE FIRST VERSION OF THIS SCRIPT PROVED, AND WHY IT NEEDED A
FEATURE AFTER ALL

The original header here claimed "no engine changes were needed, and
that is the point" -- both legs were expressible through
_grid_trigger_level and calculate_trade_value. That was true of the
BUYING, and it measured 32.25% CAGR with -79.07% in 2022, against the
splice's fictional 43.50% / +11.5%.

The gap was entirely the selling. Trend-following is DEFINED by exiting
on a signal regardless of P&L, and the engine had no way to express
that: the only sell path was a lot reaching its target_sell_price. So
the bull leg's TQQQ inventory sat through the whole bear market, which
is exactly the -79%. No parameter bridges that.

src/no_loss_guard.SellReason and decision_cycle.collect_liquidations
close it. This script now overrides lots_to_liquidate as well, and the
run below is the first honest measurement of the strategy as designed.

  _grid_trigger_level  -- bull uses a tight threshold (stay invested
                          through ordinary chop), bear demands a deep
                          spike.
  calculate_trade_value -- bear scales the lot log-linearly with the
                          UNDERLYING's drawdown from its trailing peak.
  lots_to_liquidate     -- on a bull->bear flip, close the book. This
                          MAY realize losses, which is the point of a
                          trend exit and the reason it needs the flag.

--------------------------------------------------------------------
THE REGIME SIGNAL

A 200-session simple moving average, maintained on minute bars
(200 x bars_per_day). Before it is warm the regime reads BEAR, matching
what the daily study did -- pandas produced NaN there, and `NaN >` is
False, so that run was in cash for its first 200 sessions too. Keeping
the same convention is what makes the two comparable.

The regime is read from the CURRENT bar's own price against the average
of the bars before it, so there is no lookahead: the average never
includes a price the strategy has not already seen.
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
from src.sizing_indicators import RollingMean  # noqa: E402

DATA = "data/TQQQ_1Min_sip_all_2016-01-01_2026-08-21.csv"


class RegimeSwitched(HighFrequencyLocalReferenceSizing):
    """Trend-follow above the moving average, deep-dip escalate below."""

    def __init__(
        self,
        *args,
        regime_days: int = 200,
        daily_signal: bool = False,
        bull_step: float = 0.01,
        bear_step: float = 0.10,
        max_mult: float = 400.0,
        dd_ref: float = 0.75,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        self.bull_step, self.bear_step = bull_step, bear_step
        self.max_mult, self.dd_ref = max_mult, dd_ref
        # daily_signal=True evaluates the regime ONCE PER SESSION, from
        # the prior session's close, which is what the 34.55% benchmark
        # actually is. On minute bars the same 200-session average is
        # crossed back and forth by intraday noise, and with liquidation
        # wired up every one of those crossings dumps the book -- 7,334
        # signal exits over the period, each one a realized loss. That is
        # whipsaw, not a regime call, and comparing it to a daily
        # benchmark compares two different strategies.
        self.daily_signal = daily_signal
        self._regime_mean = RollingMean(
            max(2, regime_days if daily_signal else regime_days * self.bars_per_day)
        )
        self._session: object | None = None
        self._prior_close: float | None = None
        self._price_peak: float | None = None
        self._is_bull = False  # cold start reads bear, as the daily study did
        self._flipped_to_bear = False

    def record_tick(self, context) -> None:
        super().record_tick(context)
        price = context.price
        if price <= 0:
            return
        was_bull = self._is_bull
        if self.daily_signal:
            # One decision per session, taken at the first bar of a new
            # day from the PREVIOUS day's last price against an average
            # of days before it. No lookahead: nothing in the average or
            # the compared price has not already closed.
            session = (context.timestamp.year, context.timestamp.month, context.timestamp.day)
            if self._session is None:
                self._session = session
            elif session != self._session:
                self._session = session
                if self._prior_close is not None:
                    average = self._regime_mean.value
                    self._is_bull = average is not None and self._prior_close > average
                    self._regime_mean.update(self._prior_close)
            self._prior_close = price
        else:
            # Read the regime BEFORE folding this bar in, so the average
            # is strictly of prior bars and cannot contain the price it
            # judges.
            average = self._regime_mean.value
            self._is_bull = average is not None and price > average
            self._regime_mean.update(price)
        # Latch the EDGE, not the level. Liquidating on every bear bar
        # would re-condemn each lot the deep-dip leg opens on the way
        # down -- which is the opposite of what the bear leg is for.
        # Only the transition closes the book.
        self._flipped_to_bear = was_bull and not self._is_bull
        self._price_peak = price if self._price_peak is None else max(self._price_peak, price)

    def _grid_trigger_level(self, context, last_buy_price: float, step: float) -> float:
        """Regime decides how far price must fall before a buy fires.

        `step` from the config is deliberately ignored: this strategy owns
        the threshold on both sides, and honouring a third value would
        make the config look like it controlled something it does not.
        """
        rolling_high = self._rolling_high.value
        reference = last_buy_price if rolling_high is None else max(last_buy_price, rolling_high)
        return reference * (1.0 - (self.bull_step if self._is_bull else self.bear_step))

    def lots_to_liquidate(self, open_lots, context) -> list:
        """Close everything on the bull->bear flip.

        Inventory opened while trend-following is precisely what must
        not be carried into a bear market, and it is underwater by
        definition at the moment the trend breaks -- the average was
        crossed downward. Every one of these sells is a loss the
        PROFIT_TARGET path would refuse.
        """
        return list(open_lots) if self._flipped_to_bear else []

    def calculate_trade_value(self, context) -> float:
        base = super().calculate_trade_value(context)
        if self._is_bull or not self._price_peak:
            return base
        drawdown = 1.0 - context.price / self._price_peak
        if drawdown <= 0:
            return base
        return base * min(self.max_mult, self.max_mult ** (drawdown / self.dd_ref))


def run(
    controller, cfg, *, cap, bull_step, bear_step, per_lot, max_mult, target, daily_signal=False
):
    params = dict(cfg.strategy.strategy_params)
    params.update(
        per_lot_pct=per_lot,
        bull_step=bull_step,
        bear_step=bear_step,
        max_mult=max_mult,
        dd_ref=0.75,
        regime_days=200,
        daily_signal=daily_signal,
    )
    summary, full = controller.run_sweep(
        grid_steps=[bear_step],  # ignored by the override; kept for the results row
        profit_targets=[target],
        strategy_class=RegimeSwitched,
        strategy_params_grid=[params],
        cost_model=cfg.costs.build(),
        risk_manager=RiskManager(max_concurrent_lots=6000, max_total_exposure_pct=cap),
        fill_model="intrabar",
        intrabar_priority="sell_first",
        enforce_no_loss=True,
        allow_signal_exit=True,
        on_flat_reentry="stale_reference",
        return_full_results=True,
    )
    row = summary.iloc[0]
    yearly = annual_returns(full[0].equity_curve)
    return row, yearly


def _print_row(controller, cfg, bull_step, cap, daily_signal):
    row, yearly = run(
        controller,
        cfg,
        cap=cap,
        bull_step=bull_step,
        bear_step=0.10,
        per_lot=0.02,
        max_mult=400.0,
        target=0.04,
        daily_signal=daily_signal,
    )
    y2022 = yearly[[i.year == 2022 for i in yearly.index]].iloc[0]
    print(
        f"{bull_step:6.3f} {0.10:6.2f} {cap:5.2f} {row['CAGR %']:7.2f}% "
        f"{row['Max Drawdown %']:6.1f}% {yearly.min():+7.2f}% "
        f"{int((yearly < 0).sum()):3d}/11 {y2022:+7.2f}% "
        f"{int(row['Signal Exit Count']):7d}"
    )
    print("       " + "  ".join(f"{ts.year}:{v:+.1f}%" for ts, v in yearly.items()))


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Integrated regime-switched backtest.")
    parser.add_argument("--quiet", action="store_true", default=True)
    args = parser.parse_args(argv)
    if args.quiet:
        logging.disable(logging.WARNING)

    cfg = BacktestConfig.from_yaml("config/probe_dipbuy_full.yaml")
    frame = pd.read_csv(DATA, parse_dates=["timestamp"]).set_index("timestamp")
    controller = OptimizationController(historical_data=frame)

    print("ONE ledger. Signal exits ON: the book is closed at every bull->bear flip.")
    print("Benchmark to beat: 34.55% CAGR / -19.8% worst year (SMA200-else-cash).")
    for daily_signal in (False, True):
        cadence = "once per session" if daily_signal else "every minute"
        print(f"\n--- regime evaluated {cadence} ---")
        print(
            f"{'bull':>6} {'bear':>6} {'cap':>5} {'CAGR':>8} {'maxDD':>7} {'worst':>8} "
            f"{'neg':>6} {'2022':>8} {'exits':>7}"
        )
        for bull_step in (0.005, 0.02):
            for cap in (0.50, 1.00):
                _print_row(controller, cfg, bull_step, cap, daily_signal)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
