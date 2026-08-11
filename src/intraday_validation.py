"""Optional intraday replay validation for daily-sweep finalists."""

from __future__ import annotations

import itertools
from typing import Literal

import pandas as pd

from src.ledger import AssetLotLedger
from src.order_management_system import OrderManagementSystem, OrderStatus
from src.performance_analyzer import PerformanceAnalyzer


class IntradayValidationError(ValueError):
    pass


class IntradayValidator:
    """Replay finalist parameter combinations using OHLC intrabar touches.

    The normal daily-close sweep is intentionally untouched. This validator is
    an opt-in diagnostic pass: buys use the bar close, while open sell targets
    are considered touched when the bar high reaches the target. If a bar also
    reaches a grid-buy level, ``sell_first`` is the conservative/default
    ordering because the canonical decision sequence evaluates exits before
    new entries.
    """

    def __init__(self, *, intrabar_priority: Literal["sell_first", "buy_first"] = "sell_first") -> None:
        if intrabar_priority not in {"sell_first", "buy_first"}:
            raise ValueError("intrabar_priority must be 'sell_first' or 'buy_first'")
        self.intrabar_priority = intrabar_priority

    def validate_finalists_intraday(
        self,
        finalist_params: list[dict],
        intraday_data: pd.DataFrame,
        *,
        strategy_class,
        strategy_params_grid: list[dict],
        initial_cash: float = 100000.0,
    ) -> pd.DataFrame:
        if intraday_data.empty:
            raise IntradayValidationError("intraday_data is empty")
        required = {"open", "high", "low", "close"}
        missing = required - set(intraday_data.columns)
        if missing:
            raise IntradayValidationError(f"intraday_data missing required columns: {missing}")
        if not intraday_data.index.is_monotonic_increasing or intraday_data.index.duplicated().any():
            raise IntradayValidationError("intraday_data must have a sorted, unique index")
        if not finalist_params:
            return pd.DataFrame()

        rows = []
        for finalist in finalist_params:
            step = float(finalist["Grid Step"])
            target = float(finalist["Profit Target"])
            strategy_params = self._strategy_params(finalist, strategy_params_grid)
            metrics = self._replay(
                intraday_data,
                step=step,
                target=target,
                strategy_class=strategy_class,
                strategy_params=strategy_params,
                initial_cash=initial_cash,
            )
            rows.append({
                **finalist,
                "Intraday Final Portfolio Value": metrics["Final Portfolio Value"],
                "Intraday Trade Count": metrics["Trade Count"],
                "Intraday Total Return %": metrics["Total Return %"],
                "Intraday Capital Velocity Index": metrics["Capital Velocity Index"],
                "Intraday Max Drawdown %": metrics["Max Drawdown %"],
            })
        return pd.DataFrame(rows)

    @staticmethod
    def _strategy_params(finalist: dict, strategy_params_grid: list[dict]) -> dict:
        if not strategy_params_grid:
            return {}
        keys = strategy_params_grid[0].keys()
        return {key: finalist[key] for key in keys if key in finalist}

    def _replay(self, data, *, step, target, strategy_class, strategy_params, initial_cash):
        ledger = AssetLotLedger()
        sizing = strategy_class(**strategy_params)
        oms = OrderManagementSystem(mode="SIMULATION")
        cash = float(initial_cash)
        last_buy_price = float(data["close"].iloc[0])
        peak_equity = cash
        max_drawdown = 0.0

        for _, row in data.iterrows():
            price = float(row["close"])
            sizing.record_tick(price)
            equity = cash + sum(lot.shares * price for lot in ledger.open_lots)
            peak_equity = max(peak_equity, equity)
            max_drawdown = max(max_drawdown, (peak_equity - equity) / peak_equity)

            def harvest() -> None:
                nonlocal cash
                for lot in ledger.get_marketable_lots(price, market_high=float(row["high"])):
                    order = oms.execute_sell(lot.symbol, lot.shares, lot.target_sell_price)
                    if order.get("status") == OrderStatus.FILLED.value:
                        qty = float(order.get("filled_qty", order.get("qty", 0.0)))
                        fill_price = float(order["filled_avg_price"])
                        cash += qty * fill_price
                        ledger.close_lot(lot)

            def buy() -> None:
                nonlocal cash, last_buy_price
                if price <= last_buy_price * (1.0 - step):
                    equity_now = cash + sum(lot.shares * price for lot in ledger.open_lots)
                    dd = max(0.0, (peak_equity - equity_now) / peak_equity)
                    value = sizing.calculate_trade_value(equity_now, price, dd)
                    if cash >= value and value > 0:
                        order = oms.execute_buy("TQQQ", value, price)
                        if order.get("status") == OrderStatus.FILLED.value:
                            qty = float(order.get("filled_qty", order.get("qty", 0.0)))
                            fill_price = float(order["filled_avg_price"])
                            cash -= qty * fill_price
                            ledger.register_buy(order["id"], "TQQQ", fill_price, qty, target)
                            last_buy_price = price

            if self.intrabar_priority == "sell_first":
                harvest()
                buy()
            else:
                buy()
                harvest()

        final_price = float(data["close"].iloc[-1])
        final_value = cash + sum(lot.shares * final_price for lot in ledger.open_lots)
        metrics = PerformanceAnalyzer.calculate_metrics(ledger, final_value, initial_cash)
        metrics["Max Drawdown %"] = max_drawdown * 100.0
        return metrics
