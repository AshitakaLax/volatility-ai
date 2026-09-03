"""Combine the two: trend-follow in bull regimes, deep-dip escalate in bear.

They are complementary in TIME, not competing for capital. The SMA200
book is in TQQQ 72% of the time and idle cash the other 28%. The
deep-dip book is ~90% cash and only works during deep drawdowns, which
is exactly when SMA200 is flat. So route the capital by regime.

No lookahead: the regime signal is taken from the close of day t and
applied to day t+1's return, and the dip-buyer's own daily returns come
from its independently simulated equity curve.
"""

import sys

sys.path.insert(0, r"C:/workspace/volatility-ai")
import logging

import numpy as np
import pandas as pd

logging.disable(logging.WARNING)
from optimization_controller import OptimizationController
from src.config import BacktestConfig
from src.high_frequency_sizing import HighFrequencyLocalReferenceSizing
from src.performance_analyzer import annual_returns
from src.risk_manager import RiskManager


class Escalating(HighFrequencyLocalReferenceSizing):
    def __init__(self, *a, max_mult=400.0, dd_ref=0.75, **kw):
        super().__init__(*a, **kw)
        self.max_mult, self.dd_ref = max_mult, dd_ref
        self._price_peak = None

    def record_tick(self, context):
        super().record_tick(context)
        if context.price > 0:
            self._price_peak = (
                context.price if self._price_peak is None
                else max(self._price_peak, context.price)
            )

    def calculate_trade_value(self, context):
        base = super().calculate_trade_value(context)
        if not self._price_peak:
            return base
        dd = 1.0 - context.price / self._price_peak
        return base if dd <= 0 else base * min(
            self.max_mult, self.max_mult ** (dd / self.dd_ref)
        )


def main() -> int:
    """Everything below used to run at IMPORT time.

    That made these modules unimportable as libraries: reusing the
    Escalating class from here fired a full multi-minute sweep as a side
    effect of the import statement. Every other tool in this directory
    already had this guard; these two were the exception, and nothing
    noticed because nobody had imported them until now.
    """
    cfg = BacktestConfig.from_yaml("config/probe_dipbuy_full.yaml")
    df = pd.read_csv(
        "data/TQQQ_1Min_sip_all_2016-01-01_2026-08-21.csv", parse_dates=["timestamp"]
    ).set_index("timestamp")
    controller = OptimizationController(historical_data=df)

    # The dip-buyer, simulated independently, at two risk caps.
    dip_daily = {}
    for cap in (0.50, 1.00):
        p = dict(cfg.strategy.strategy_params)
        p["per_lot_pct"], p["max_mult"], p["dd_ref"] = 0.02, 400.0, 0.75
        _, full = controller.run_sweep(
            grid_steps=[0.10], profit_targets=[0.04], strategy_class=Escalating,
            strategy_params_grid=[p], cost_model=cfg.costs.build(),
            risk_manager=RiskManager(max_concurrent_lots=6000, max_total_exposure_pct=cap),
            fill_model="intrabar", intrabar_priority="sell_first", enforce_no_loss=True,
            on_flat_reentry="stale_reference", return_full_results=True,
        )
        eq = full[0].equity_curve.resample("D").last().dropna()
        dip_daily[cap] = eq.pct_change().fillna(0.0)

    price = df["close"].resample("D").last().dropna()
    tqqq_ret = price.pct_change().fillna(0.0)
    bull = (price > price.rolling(200).mean()).shift(1).fillna(False)

    COST = 0.0015


    def report(label, returns):
        eq = pd.Series((1 + returns).cumprod(), index=returns.index)
        ar = annual_returns(eq)
        yrs = (eq.index[-1] - eq.index[0]).days / 365.25
        dd = ((eq.cummax() - eq) / eq.cummax()).max() * 100
        y22 = ar[[i.year == 2022 for i in ar.index]].iloc[0]
        print(f"{label:38s} CAGR {(eq.iloc[-1] ** (1 / yrs) - 1) * 100:6.2f}%  "
              f"maxDD {dd:5.1f}%  worst {ar.min():+7.2f}%  neg {int((ar < 0).sum())}/11  2022 {y22:+7.2f}%")
        return ar


    switch = (bull != bull.shift(1)).fillna(False)
    report("TQQQ > SMA200, else cash", np.where(bull, tqqq_ret, 0.0) - switch * COST)
    for cap, dip in dip_daily.items():
        aligned = dip.reindex(price.index).fillna(0.0)
        combo = np.where(bull, tqqq_ret, aligned) - switch * COST
        ar = report(f"SMA200 bull -> TQQQ, bear -> dip cap {cap}", pd.Series(combo, index=price.index))
        print("     " + "  ".join(f"{ts.year}:{v:+.1f}%" for ts, v in ar.items()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
