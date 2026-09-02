#!/usr/bin/env python
"""
The regime book captures ~1/3 of the benchmark in EVERY bull year.
That, not the downturn, is where its CAGR goes.

--------------------------------------------------------------------
THE MEASUREMENT THAT MOTIVATES THIS

Comparing the regime strategy (13.79% CAGR) against SMA200-else-cash
(34.55%) year by year, the shortfall is not spread around -- it is
entirely in the up years, and it is almost constant:

    2017  34% of benchmark      2021  37%
    2019  31%                   2023  36%
    2020  39%                   2024  15%

The regime book beats the benchmark in exactly two years, 2018 and
2022, and both are downturns. Mean gap across the nine losing years:
-32.8pp. A deficit that stable across six independent bull markets is
structural, not luck.

The cause is visible in the configuration rather than the data. During
a BULL regime the book runs a grid: 2% lots, a 50% exposure cap, and a
4% profit target. So it is never more than half invested, and it sells
its winners into a rising market and buys them back higher. The
benchmark simply holds. In a trend, holding wins, and the ~1/3 capture
ratio is what "half invested, and harvesting" looks like against it.

--------------------------------------------------------------------
WHAT THIS CHANGES, AND WHY IT COULD NOT BE DONE BEFORE

  bull   accumulate toward FULL exposure and do not harvest. Expressed
         by raising each open lot's profit target while the regime is
         bull, so nothing becomes marketable -- adjust_profit_target is
         a sanctioned mutation (src/ledger.Lot.retarget) and moving a
         target can never permit a losing sell, since the no-loss guard
         evaluates cost basis independently of it.

  flip   liquidate the whole book, in BOTH directions. Bull->bear
         because carrying trend inventory into a bear market is the
         -79% that started all of this; bear->bull because the dip
         book's lots carry a 4% target that a bull leg would then
         freeze at a huge one, stranding them.

  bear   the 5% step / 4% target escalating dip book that came out of
         tools/probe_downturn_tactics.py -- 14/14 drawdown episodes
         positive, median +6.0%.

The liquidation is what was impossible before src/no_loss_guard.
SellReason.SIGNAL_EXIT: a rotation has to close lots regardless of
P&L, and until this month the engine could only sell at a profit.

--------------------------------------------------------------------
RESULT: CONFIRMED, AND IT COSTS EXACTLY WHAT IT BUYS

Holding closes the capture gap completely. Against the same benchmark
years, cap 1.00 / bull 2x:

    2017 100%   2019 174%   2020 132%   2021 100%   2023 251%

against 34% / 31% / 39% / 37% / 36% before. CAGR goes from 13.79% to
33.28%, level with the 34.55% benchmark. The hold=False control -- the
identical strategy in every respect except that bull lots harvest at 4%
instead of being held -- gets 10.19%. So roughly 20pp of CAGR is the
price of harvesting a trend, and it is not a modelling artifact.

AND IT GIVES BACK THE THING THAT MADE THE STRATEGY INTERESTING.
2022 goes from +3.6% to -67%, and max drawdown from 44% to 73%. This is
a straight move along a frontier, not a free improvement:

    hold  cap   CAGR    2022    maxDD
    no    0.50  13.79%   +3.6%   44.3%     every complete year positive
    yes   0.50  19.82%  -50.8%   56.4%
    yes   1.00  33.28%  -67.1%   72.6%     level with the benchmark

Which end is right is a preference, not a measurement, and the stated
preference here has been "the worst year positive, drawdown very small
in comparison" -- which the top row satisfies and the others do not.

--------------------------------------------------------------------
WHY 2022 IS -67% HERE BUT ONLY -19.8% FOR THE BENCHMARK

Worth being precise about, because it is not the bull leg. Both flip on
the same late SMA200 signal and eat the same initial loss. The
benchmark then sits in CASH for the rest of the year. This rotates into
the dip book, which BUYS INTO the continuing decline.

That also exposes a real limitation of tools/probe_downturn_tactics.py,
which reported that same dip book positive in 14 of 14 episodes. It
measures PEAK-TO-RECOVERY return and says nothing about the path. The
2021-11 episode returned +13.8% end to end -- earned largely in the
2023-24 recovery -- while being deeply underwater through 2022. A
tactic can be 14/14 on episode return and still have enormous
intra-episode drawdowns, and that study does not measure them.

Usage:
    python tools/probe_bull_capture.py
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

# SMA200-else-cash, measured earlier in this project. The number to beat.
BENCHMARK = {
    2016: 3.7, 2017: 118.3, 2018: 8.4, 2019: 40.5, 2020: 68.4, 2021: 83.0,
    2022: -19.8, 2023: 65.2, 2024: 36.4, 2025: 18.0, 2026: 3.5,
}
BENCHMARK_CAGR = 34.55

# Effectively unreachable, so a bull lot never becomes marketable and
# the position is HELD. Not infinity: target_sell_price stays a real
# finite number that persistence's buy_price*(1+target) derivation
# check can still verify.
HOLD_TARGET = 50.0


class RegimeHold(HighFrequencyLocalReferenceSizing):
    """Hold the trend in bull, harvest deep dips in bear, rotate on flip."""

    def __init__(
        self,
        *args,
        regime_days: int = 200,
        bull_step: float = 0.002,
        bear_step: float = 0.05,
        bear_target: float = 0.04,
        bull_lot_scale: float = 5.0,
        max_mult: float = 400.0,
        dd_ref: float = 0.75,
        hold_in_bull: bool = True,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        self.bull_step, self.bear_step = bull_step, bear_step
        self.bear_target = bear_target
        # per_lot_pct IS the bear leg's size and stays at the value the
        # 14-episode study validated (0.02). The bull leg scales off it.
        # Keeping them separate is not tidiness: the first run of this
        # probe raised per_lot to 0.10 for the bull leg and thereby made
        # the BEAR leg five times more aggressive than anything measured,
        # which is most of why it printed -80% in 2022. One change at a
        # time, or the result is uninterpretable.
        self.bull_lot_scale = bull_lot_scale
        self.max_mult, self.dd_ref = max_mult, dd_ref
        self.hold_in_bull = hold_in_bull
        self._regime_mean = RollingMean(max(2, regime_days))
        self._session = None
        self._prior_close: float | None = None
        self._price_peak: float | None = None
        self._is_bull = False
        self._flipped = False

    # --- regime, evaluated once per session from the prior close ---

    @property
    def _warm(self) -> bool:
        return self._regime_mean.count >= self._regime_mean.window

    def wants_lot_retargeting(self) -> bool:
        """MUST be overridden here, and the first version of this probe
        forgot to.

        HighFrequencyLocalReferenceSizing answers False whenever
        trail_pct is unset -- a real 63%-of-runtime optimisation whose
        docstring states plainly that False "promises adjust_profit_target
        AND retain_lots are both inert". Overriding adjust_profit_target
        without lifting that promise means decision_cycle early-outs and
        the override never runs. It fails SILENTLY: hold_in_bull=True and
        hold_in_bull=False printed byte-identical results, which is the
        only reason it was caught.
        """
        return True

    def record_tick(self, context) -> None:
        super().record_tick(context)
        price = context.price
        if price <= 0:
            return
        was_bull = self._is_bull
        session = (context.timestamp.year, context.timestamp.month, context.timestamp.day)
        if self._session is None:
            self._session = session
        elif session != self._session:
            self._session = session
            if self._prior_close is not None:
                average = self._regime_mean.value
                self._is_bull = (
                    self._warm and average is not None and self._prior_close > average
                )
                self._regime_mean.update(self._prior_close)
        self._prior_close = price
        # Flip in EITHER direction rotates the book.
        self._flipped = was_bull != self._is_bull
        self._price_peak = price if self._price_peak is None else max(self._price_peak, price)

    # --- entries ---

    def _grid_trigger_level(self, context, last_buy_price: float, step: float) -> float:
        if not self._warm:
            return 0.0  # unreachable: no signal, no position
        rolling_high = self._rolling_high.value
        reference = last_buy_price if rolling_high is None else max(last_buy_price, rolling_high)
        return reference * (1.0 - (self.bull_step if self._is_bull else self.bear_step))

    def calculate_trade_value(self, context) -> float:
        if not self._warm:
            return 0.0
        base = super().calculate_trade_value(context)
        if self._is_bull:
            return base * self.bull_lot_scale
        if not self._price_peak:
            return base
        drawdown = 1.0 - context.price / self._price_peak
        if drawdown <= 0:
            return base
        return base * min(self.max_mult, self.max_mult ** (drawdown / self.dd_ref))

    # --- exits ---

    def adjust_profit_target(self, lot, context):
        """Freeze bull lots; leave bear lots on their normal target.

        Returning a target rather than suppressing the sale keeps the
        exit decision where the engine already makes it. The no-loss
        guard is unaffected either way -- it evaluates cost basis, not
        targets (src/ledger.Lot.retarget documents exactly this).
        """
        if not self.hold_in_bull:
            return None
        want = HOLD_TARGET if self._is_bull else self.bear_target
        return want if lot.profit_target != want else None

    def lots_to_liquidate(self, open_lots, context) -> list:
        return list(open_lots) if self._flipped else []


def run(controller, cfg, *, hold_in_bull, cap, per_lot, bull_step):
    params = dict(cfg.strategy.strategy_params)
    params.update(
        per_lot_pct=0.02,  # the bear leg, held at the validated value
        bull_lot_scale=per_lot,
        bull_step=bull_step,
        bear_step=0.05,
        bear_target=0.04,
        max_mult=400.0,
        dd_ref=0.75,
        regime_days=200,
        hold_in_bull=hold_in_bull,
    )
    summary, full = controller.run_sweep(
        grid_steps=[0.05],
        profit_targets=[0.04],
        strategy_class=RegimeHold,
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
    return summary.iloc[0], annual_returns(full[0].equity_curve)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Does holding the bull regime close the gap?")
    parser.add_argument("--quiet", action="store_true", default=True)
    args = parser.parse_args(argv)
    if args.quiet:
        logging.disable(logging.WARNING)

    cfg = BacktestConfig.from_yaml("config/probe_dipbuy_full.yaml")
    frame = pd.read_csv(DATA, parse_dates=["timestamp"]).set_index("timestamp")
    controller = OptimizationController(historical_data=frame)

    print("bull = hold the trend, bear = 5%/4% escalating dips, flip = rotate the book")
    print(f"benchmark SMA200-else-cash: {BENCHMARK_CAGR:.2f}% CAGR, worst year -19.8%\n")
    print(f"{'hold':>5} {'cap':>5} {'bullx':>6} {'bull':>6} {'CAGR':>8} {'maxDD':>7} "
          f"{'worst':>8} {'neg':>6} {'2022':>8} {'exits':>7}")

    for hold_in_bull in (True, False):
        for cap, per_lot, bull_step in ((1.00, 5.0, 0.002), (1.00, 2.0, 0.005),
                                        (0.50, 5.0, 0.002)):
            row, yearly = run(controller, cfg, hold_in_bull=hold_in_bull, cap=cap,
                              per_lot=per_lot, bull_step=bull_step)
            y2022 = yearly[[i.year == 2022 for i in yearly.index]].iloc[0]
            complete = yearly[[ts.year < 2026 for ts in yearly.index]]
            print(
                f"{str(hold_in_bull):>5} {cap:5.2f} {per_lot:5.1f}x {bull_step:6.3f} "
                f"{row['CAGR %']:7.2f}% {row['Max Drawdown %']:6.1f}% "
                f"{complete.min():+7.2f}% {int((complete < 0).sum()):3d}/10 "
                f"{y2022:+7.2f}% {int(row['Signal Exit Count']):7d}"
            )
            print("      " + "  ".join(f"{ts.year}:{v:+.0f}%" for ts, v in yearly.items()))
            caps = [yearly[[t.year == y for t in yearly.index]].iloc[0] / BENCHMARK[y]
                    for y in (2017, 2019, 2020, 2021, 2023) if BENCHMARK[y]]
            print(f"      bull-year capture vs benchmark: "
                  + "  ".join(f"{y}:{c:.0%}" for y, c in
                              zip((2017, 2019, 2020, 2021, 2023), caps)))

    print("\n'worst' and 'neg' cover COMPLETE years only -- 2026 is a Jan-Aug stub.")
    print("hold=False is the control: identical in every respect except that bull")
    print("lots harvest at 4% instead of being held.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
