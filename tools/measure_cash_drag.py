#!/usr/bin/env python
"""
How much is this project's 0% cash assumption costing the measurement?

--------------------------------------------------------------------
WHY THIS MATTERS MORE HERE THAN IT WOULD ELSEWHERE

Every backtest in this repo values idle cash at zero. For a strategy
that is fully invested that assumption is nearly free. For these
strategies it is not: the deep-dip book is roughly 90% cash by design,
and the regime book stands aside for whole stretches. A strategy whose
edge is patience is being scored as though patience earns nothing.

It also is not hypothetical. The target account is a Fidelity
Traditional IRA, where uninvested cash sweeps to SPAXX automatically --
so the yield is not something that would have to be arranged, it is
something the account already earns and the model already ignores.

--------------------------------------------------------------------
THE PRIMARY RESULT NEEDS NO INTEREST-RATE DATA

The authoritative rate series is not obtainable here -- bls.gov and
fred.stlouisfed.org both refuse programmatic access (recorded in
src/high_frequency_sizing.py). So the headline measures the thing that
requires no rate at all: the CASH FRACTION of the book, bar by bar, and
the uplift per 1 percentage point of annual yield. Multiply by whatever
rate you think defensible.

A rounded APPROX_YIELDS table is then used for one secondary figure.
That is a deliberate exception to "do not hand-enter data", made
because the alternative was worse: a flat 4-5% illustration is wrong
for six of eleven years here, and without per-year rates the tool
cannot show whether the cash-heavy years are the high-rate ones. It
drives nothing in src/ and the per-1pp number stands without it.

Worth knowing what that comparison found, since the intuition points
the other way: the correlation is mildly UNFAVOURABLE for the regime
book. It is most in cash in 2016 (90%) and 2022 (94%), and those years
paid 0.3% and ~1.7%; the 4.2-5.2% years, 2023-2025, were only ~55%
cash. Correlation-aware comes in at +1.42pp against a naive +1.49pp.
Small, but in the opposite direction to "it holds cash when cash pays".

The cash fraction is read from MarketContext.cash / MarketContext.equity
on every bar through an ordinary record_tick override -- the same
values the sizing strategies themselves see, not a reconstruction.

--------------------------------------------------------------------
WHAT THE UPLIFT NUMBER IS, AND WHAT IT IS NOT

  uplift_per_1pct = mean(cash_fraction) x 1%

It is a first-order approximation and it is stated as one. It ignores
compounding of the interest itself and it ignores that a higher cash
balance early compounds for longer than the same balance late. Both
push the true figure UP, so this understates rather than flatters.

What it is emphatically not is a claim that adding cash yield makes a
losing strategy good. It shifts every strategy in the same direction
and shifts the cash-heavy ones most, which changes RANKINGS -- and that
is the reason to know the size of it before ranking anything else.

Usage:
    python tools/measure_cash_drag.py
"""

from __future__ import annotations

import argparse
import os as _os
import sys as _sys

_REPO_ROOT = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
if _REPO_ROOT not in _sys.path:
    _sys.path.insert(0, _REPO_ROOT)

import logging

import pandas as pd

from optimization_controller import OptimizationController
from src.config import BacktestConfig
from src.high_frequency_sizing import HighFrequencyLocalReferenceSizing
from src.risk_manager import RiskManager
from tools.probe_regime_integrated import RegimeSwitched

TQQQ = "data/TQQQ_1Min_sip_all_2016-01-01_2026-08-21.csv"

# APPROXIMATE annual average money-market/sweep yields, percent.
#
# Hand-entered and rounded, and labelled approximate everywhere it is
# used, because the authoritative series is not obtainable here --
# src/high_frequency_sizing.py records that bls.gov and
# fred.stlouisfed.org both refuse programmatic access.
#
# Included despite that, for one specific reason: WITHOUT per-year rates
# this tool cannot show the interaction that matters, and its flat 4%/5%
# illustrations actively invite the wrong conclusion, since 2016-2021
# yields were near zero. A rounded series that makes the shape visible
# beats a flat number that is wrong for six of eleven years.
#
# These drive NOTHING in src/ and no strategy reads them. They scale one
# reported figure, and the parameter-free "per 1pp" number remains the
# primary result precisely so this table can be disagreed with without
# invalidating the measurement.
APPROX_YIELDS = {
    2016: 0.3,
    2017: 0.8,
    2018: 1.8,
    2019: 2.2,
    2020: 0.4,
    2021: 0.05,
    2022: 1.7,
    2023: 4.9,
    2024: 5.2,
    2025: 4.2,
    2026: 4.0,
}

# Written to by the mixin below. Module-level because run_sweep
# constructs the strategy itself, so a caller has no handle on the
# instance that actually ran -- the same reason tests/unit/
# test_signal_exit.py collects its observations this way.
SAMPLES: list[tuple[pd.Timestamp, float]] = []


class _RecordsCashFraction:
    """Records cash/equity every bar. Mixed into a real strategy so the
    figures come from a real run rather than a simplified stand-in."""

    def record_tick(self, context) -> None:
        super().record_tick(context)
        equity = context.equity
        if equity > 0:
            SAMPLES.append((context.timestamp, context.cash / equity))


class RegimeCash(_RecordsCashFraction, RegimeSwitched):
    pass


class DipCash(_RecordsCashFraction, HighFrequencyLocalReferenceSizing):
    """The deep-dip escalating book, whose own header calls it ~90% cash."""

    def __init__(self, *args, max_mult: float = 400.0, dd_ref: float = 0.75, **kwargs):
        super().__init__(*args, **kwargs)
        self.max_mult, self.dd_ref = max_mult, dd_ref
        self._price_peak: float | None = None

    def record_tick(self, context) -> None:
        super().record_tick(context)
        if context.price > 0:
            self._price_peak = (
                context.price if self._price_peak is None else max(self._price_peak, context.price)
            )

    def calculate_trade_value(self, context) -> float:
        base = super().calculate_trade_value(context)
        if not self._price_peak:
            return base
        drawdown = 1.0 - context.price / self._price_peak
        if drawdown <= 0:
            return base
        return base * min(self.max_mult, self.max_mult ** (drawdown / self.dd_ref))


def measure(controller, cfg, label, strategy_class, params, *, cap, step, target, signal_exits):
    SAMPLES.clear()
    summary, _ = controller.run_sweep(
        grid_steps=[step],
        profit_targets=[target],
        strategy_class=strategy_class,
        strategy_params_grid=[params],
        cost_model=cfg.costs.build(),
        risk_manager=RiskManager(max_concurrent_lots=6000, max_total_exposure_pct=cap),
        fill_model="intrabar",
        intrabar_priority="sell_first",
        enforce_no_loss=True,
        allow_signal_exit=signal_exits,
        on_flat_reentry="stale_reference",
        return_full_results=True,
    )
    frame = pd.DataFrame(SAMPLES, columns=["timestamp", "cash_frac"]).set_index("timestamp")
    mean_frac = float(frame["cash_frac"].mean())
    cagr = float(summary.iloc[0]["CAGR %"])
    print(f"\n{label}")
    print(f"  measured CAGR at 0% cash yield : {cagr:6.2f}%")
    print(f"  mean cash fraction             : {mean_frac:6.1%}")
    print(f"  median cash fraction           : {frame['cash_frac'].median():6.1%}")
    print(f"  bars at >90% cash              : {(frame['cash_frac'] > 0.90).mean():6.1%}")
    print(f"  UPLIFT PER 1pp OF CASH YIELD   : +{mean_frac:.2f}pp of CAGR")
    print("  by year (mean cash fraction):")
    yearly = frame["cash_frac"].groupby(frame.index.year).mean()
    print("    " + "  ".join(f"{yr}:{v:.0%}" for yr, v in yearly.items()))
    print("  a FLAT yield, which is counterfactual -- see below:")
    for rate in (2.0, 4.0, 5.0):
        print(
            f"    {rate:.0f}% flat  ->  CAGR {cagr:.2f}% + {mean_frac * rate:.2f}pp "
            f"= {cagr + mean_frac * rate:.2f}%"
        )

    # A flat rate is the wrong shape for this period and OVERSTATES
    # badly: 2016-2021 money-market yields were near zero. But applying
    # the period average instead UNDERSTATES, because this strategy's
    # cash fraction is correlated with the rate -- it sits in cash during
    # bad years, and the bad years here happen to be the high-rate ones.
    # Only a year-by-year weighting gets both right.
    weighted = sum(yearly.get(yr, 0.0) * rate for yr, rate in APPROX_YIELDS.items())
    years = len(APPROX_YIELDS)
    flat_avg = sum(APPROX_YIELDS.values()) / years
    print("  year-by-year, using the approximate yields listed at the end:")
    print(f"    period-average yield           : {flat_avg:.2f}%")
    print(f"    naive (avg yield x avg cash)   : +{mean_frac * flat_avg:.2f}pp")
    print(
        f"    correlation-aware (per year)   : +{weighted / years:.2f}pp"
        f"  -> CAGR {cagr + weighted / years:.2f}%"
    )
    return mean_frac


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Value of the ignored cash yield.")
    parser.add_argument("--quiet", action="store_true", default=True)
    args = parser.parse_args(argv)
    if args.quiet:
        logging.disable(logging.WARNING)

    cfg = BacktestConfig.from_yaml("config/probe_dipbuy_full.yaml")
    frame = pd.read_csv(TQQQ, parse_dates=["timestamp"]).set_index("timestamp")
    controller = OptimizationController(historical_data=frame)

    print("Every backtest here values idle cash at 0%. These strategies hold a lot")
    print("of it, and the target account sweeps cash to SPAXX automatically.")

    regime = dict(cfg.strategy.strategy_params)
    regime.update(
        per_lot_pct=0.02,
        bull_step=0.005,
        bear_step=0.10,
        max_mult=400.0,
        dd_ref=0.75,
        regime_days=200,
        daily_signal=True,
        stand_aside_until_warm=True,
    )
    measure(
        controller,
        cfg,
        "regime + signal exits (0.005 / cap 0.50) -- 13.79% CAGR row",
        RegimeCash,
        regime,
        cap=0.50,
        step=0.10,
        target=0.04,
        signal_exits=True,
    )

    dip = dict(cfg.strategy.strategy_params)
    dip.update(per_lot_pct=0.02, max_mult=400.0, dd_ref=0.75)
    measure(
        controller,
        cfg,
        "deep-dip escalating (cap 0.50) -- the ~90%-cash book",
        DipCash,
        dip,
        cap=0.50,
        step=0.10,
        target=0.04,
        signal_exits=False,
    )

    print("\napproximate yields used above (percent, hand-entered and rounded):")
    print("  " + "  ".join(f"{yr}:{r}" for yr, r in APPROX_YIELDS.items()))
    print("  The authoritative series is not obtainable here. The per-1pp number")
    print("  needs none of this and stands on its own.")
    print("\nFirst-order: uplift ignores compounding of the interest itself and")
    print("ignores that early cash compounds longer. Both push the true figure UP,")
    print("so these understate. Cash yield lifts every strategy but lifts the")
    print("cash-heavy ones most, which is why it can reorder a ranking.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
