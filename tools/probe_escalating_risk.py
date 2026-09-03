"""
Escalating deep-dip sizing: lot size scales with the UNDERLYING's drawdown.

WHY. The fixed-size deep-dip strategy was sitting on $102,119 of cash --
93.9% of the account -- on 2022-06-13, the first day TQQQ was down 75%
from its peak. It was maximally conservative at the moment the
opportunity was greatest. Cash on hand at each TQQQ drawdown level:

    TQQQ -60% (2020-03-12)   cash $62,805   71.2% of equity
    TQQQ -75% (2022-06-13)   cash $102,119  93.9% of equity
    TQQQ -80% (2022-10-10)   cash $79,558   72.2% of equity

THE FIX, AND THE ONE DESIGN POINT THAT MATTERS. The escalation keys off
the UNDERLYING's drawdown from its own trailing peak, NOT the portfolio's.
context.drawdown was ~1% at TQQQ -75%, because the book was mostly cash --
scaling on it would never have fired at all. That distinction is the
whole reason this works.

    multiplier = min(max_mult, max_mult ** (price_drawdown / dd_ref))

Log-linear: the log of the multiplier is linear in the drawdown.

RESULT, full period, step 0.10 / target 0.04 / per-lot 0.02:

    cap 0.50:  CAGR 3.62%  maxDD 35.4%  2022 +15.4%  0 negative years
    cap 1.00:  CAGR 6.07%  maxDD 54.6%  2022 +39.2%  0 negative years

against 0.47% CAGR and +1.0% in 2022 with no escalation. Seven times the
CAGR and a far better worst year, with zero negative years preserved.

THE INTERACTION THAT DECIDES IT: escalation only works PAIRED WITH a deep
entry requirement. At step 0.05 the same escalation drives 2022 to -61%
to -71%, because it deploys the escalated size into shallow dips early in
the decline and is then fully invested for the rest of it. Deep entry
without escalation is safe but earns nothing; escalation without deep
entry is ruinous. Both together are the result above.

CAVEAT. The escalation curve is fitted against two deep drawdowns in the
sample (2020 and 2022). n=2. mult=400 is also far past the point where the
exposure cap binds -- at TQQQ -50% the multiplier is already 54x, so the
cap, not the multiplier, is what actually sets risk beyond that. Read
mult as "deploy whatever the cap allows once the drop is deep" rather
than as a tuned constant.

This is a PROBE, not a shipped strategy: it subclasses the real strategy
rather than modifying it, so nothing in src/ changes.
"""
import sys

sys.path.insert(0, r"C:/workspace/volatility-ai")
import logging

import pandas as pd

logging.disable(logging.WARNING)
from optimization_controller import OptimizationController
from src.config import BacktestConfig
from src.performance_analyzer import annual_returns
from src.risk_manager import RiskManager
from tools.harness import Escalating


# Escalating now lives in tools/harness.py -- ONE definition. Three
# independent copies of it lived in this directory, verified equivalent
# but each a chance to diverge silently, which would have made two
# probes' results look comparable while not being so.
def main() -> int:
    """Everything below used to run at IMPORT time.

    That made these modules unimportable as libraries: reusing the
    Escalating class from here fired a full multi-minute sweep as a side
    effect of the import statement. Every other tool in this directory
    already had this guard; these two were the exception, and nothing
    noticed because nobody had imported them until now.
    """
    cfg = BacktestConfig.from_yaml("config/probe_dipbuy_full.yaml")
    cost = cfg.costs.build()
    df = pd.read_csv(
        "data/TQQQ_1Min_sip_all_2016-01-01_2026-08-21.csv", parse_dates=["timestamp"]
    ).set_index("timestamp")
    controller = OptimizationController(historical_data=df)

    for cap in (0.50, 1.00):
        p = dict(cfg.strategy.strategy_params)
        p["per_lot_pct"], p["max_mult"], p["dd_ref"] = 0.02, 400.0, 0.75
        rm = RiskManager(max_concurrent_lots=6000, max_total_exposure_pct=cap)
        summary, full = controller.run_sweep(
            grid_steps=[0.10], profit_targets=[0.04], strategy_class=Escalating,
            strategy_params_grid=[p], cost_model=cost, risk_manager=rm,
            fill_model="intrabar", intrabar_priority="sell_first",
            enforce_no_loss=True, on_flat_reentry="stale_reference",
            return_full_results=True,
        )
        ar = annual_returns(full[0].equity_curve)
        r = summary.iloc[0]
        print(f"--- step 0.10 / mult 400 / cap {cap:.2f} ---")
        print("  " + "  ".join(f"{ts.year}:{v:+.1f}%" for ts, v in ar.items()))
        print(f"  CAGR {r['CAGR %']:.2f}%   maxDD {r['Max Drawdown %']:.1f}%   "
              f"total {r['Total Return %']:.0f}%   trades {int(r['Trade Count'])}")

    print("\nlot-size multiplier at each TQQQ drawdown (mult=400, dd_ref=0.75):")
    for dd in (0.10, 0.25, 0.50, 0.60, 0.75, 0.80):
        print(f"  TQQQ -{dd * 100:2.0f}%  ->  x{min(400, 400 ** (dd / 0.75)):7.1f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
