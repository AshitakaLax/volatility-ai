import itertools
import logging
from typing import Type

import pandas as pd

from src import data_validation
from src.cost_models import TransactionCostModel, ZeroCostModel
from src.ledger import AssetLotLedger
from src.market_context import MarketContext, SimulationResult
from src.order_management_system import OrderManagementSystem, OrderStatus
from src.performance_analyzer import PerformanceAnalyzer
from src.risk_manager import RiskManager
from src.size_calculators import SizingStrategy

logger = logging.getLogger("Optimizer")


class BacktestState:
    def __init__(self, initial_cash: float, start_price: float):
        self.cash = initial_cash
        self.last_buy_price = start_price
        self.peak_equity = initial_cash
        self.max_drawdown = 0.0


class OptimizationController:
    def __init__(self, historical_data: pd.DataFrame):
        data_validation.validate(historical_data)
        self.data = historical_data
        logger.info(f"OptimizationController initialized with historical dataset length: {len(historical_data)}")

    def _simulate_single(
        self,
        step: float,
        target: float,
        strategy_instance: SizingStrategy,
        symbol: str,
        initial_cash: float,
        cost_model: TransactionCostModel,
        risk_manager: RiskManager,
    ) -> SimulationResult:
        ledger = AssetLotLedger()
        oms = OrderManagementSystem(mode="SIMULATION")
        state = BacktestState(initial_cash, float(self.data["close"].iloc[0]))

        for bar_index, (timestamp, row) in enumerate(self.data.iterrows()):
            current_price = float(row["close"])
            equity = state.cash + sum(lot.shares * current_price for lot in ledger.open_lots)
            if equity > state.peak_equity:
                state.peak_equity = equity
            drawdown = (state.peak_equity - equity) / state.peak_equity if state.peak_equity else 0.0
            state.max_drawdown = max(state.max_drawdown, drawdown)

            context = MarketContext(
                timestamp=timestamp.to_pydatetime() if hasattr(timestamp, "to_pydatetime") else timestamp,
                open=float(row["open"]) if "open" in row else current_price,
                high=float(row["high"]) if "high" in row else current_price,
                low=float(row["low"]) if "low" in row else current_price,
                close=current_price,
                cash=float(state.cash),
                equity=float(equity),
                peak_equity=float(state.peak_equity),
                drawdown=float(drawdown),
                open_lot_count=len(ledger.open_lots),
                bar_index=bar_index,
            )
            strategy_instance.record_tick(context)

            for lot in ledger.get_marketable_lots(current_price):
                result = oms.execute_sell(lot.symbol, lot.shares, lot.target_sell_price)
                if result.get("status") == OrderStatus.FILLED.value:
                    qty = float(result.get("filled_qty", result.get("qty", 0.0)))
                    price = result.get("filled_avg_price")
                    if qty > 0 and price is not None:
                        effective_price, cost = cost_model.apply_sell(float(price), qty, context=context)
                        state.cash += qty * effective_price - cost
                        ledger.close_lot(lot)
                else:
                    logger.warning(f"Sell not filled for lot {lot.symbol}: status={result.get('status')}")

            if strategy_instance._check_grid_trigger(context, state.last_buy_price, step):
                post_sell_equity = state.cash + sum(lot.shares * current_price for lot in ledger.open_lots)
                if post_sell_equity > state.peak_equity:
                    state.peak_equity = post_sell_equity
                post_sell_dd = (state.peak_equity - post_sell_equity) / state.peak_equity if state.peak_equity else 0.0
                state.max_drawdown = max(state.max_drawdown, post_sell_dd)
                if post_sell_equity != context.equity or post_sell_dd != context.drawdown:
                    context = MarketContext(
                        timestamp=context.timestamp, open=context.open, high=context.high, low=context.low,
                        close=context.close, cash=float(state.cash), equity=float(post_sell_equity),
                        peak_equity=float(state.peak_equity), drawdown=float(post_sell_dd),
                        open_lot_count=len(ledger.open_lots), bar_index=bar_index,
                    )
                proposed = strategy_instance.calculate_trade_value(context)
                trade_value = risk_manager.clamp_trade_value(proposed, context.equity, state.cash, len(ledger.open_lots))
                if state.cash >= trade_value and trade_value > 0:
                    result = oms.execute_buy(symbol, trade_value, current_price)
                    if result.get("status") == OrderStatus.FILLED.value:
                        qty = float(result.get("filled_qty", result.get("qty", 0.0)))
                        price = result.get("filled_avg_price")
                        if qty > 0 and price is not None:
                            effective_price, cost = cost_model.apply_buy(float(price), qty, context=context)
                            actual_notional = qty * effective_price + cost
                            if state.cash >= actual_notional:
                                state.cash -= actual_notional
                                ledger.register_buy(result["id"], symbol, effective_price, qty, target)
                    else:
                        logger.warning(f"Buy not filled for {symbol}: status={result.get('status')}")

        final_price = float(self.data["close"].iloc[-1])
        final_value = state.cash + sum(lot.shares * final_price for lot in ledger.open_lots)
        metrics = PerformanceAnalyzer.calculate_metrics(ledger, final_value, initial_cash)
        metrics["Max Drawdown %"] = state.max_drawdown * 100.0
        return SimulationResult(metrics=metrics)

    def run_sweep(
        self,
        grid_steps: list,
        profit_targets: list,
        strategy_class: Type[SizingStrategy],
        strategy_params_grid: list[dict],
        cost_model: TransactionCostModel | None = None,
        risk_manager: RiskManager | None = None,
        on_flat_reentry: str = "stale_reference",
    ) -> pd.DataFrame:
        if on_flat_reentry not in {"stale_reference", "reset_to_market"}:
            raise ValueError("on_flat_reentry must be 'stale_reference' or 'reset_to_market'")
        cost_model = ZeroCostModel() if cost_model is None else cost_model
        risk_manager = RiskManager() if risk_manager is None else risk_manager
        results = []
        for step, target, params in itertools.product(grid_steps, profit_targets, strategy_params_grid):
            simulation = self._simulate_single(
                step, target, strategy_class(**params), "TQQQ", 100_000.0, cost_model, risk_manager
            )
            results.append({"Grid Step": step, "Profit Target": target, **params, **simulation.metrics})
        return pd.DataFrame(results).sort_values(by="Capital Velocity Index", ascending=False)

    def validate_finalists_intraday(self, finalist_params, intraday_data, *, strategy_class, strategy_params_grid, intrabar_priority="sell_first") -> pd.DataFrame:
        from src.intraday_validation import IntradayValidator
        validator = IntradayValidator(intrabar_priority=intrabar_priority)
        return validator.validate_finalists_intraday(finalist_params, intraday_data, strategy_class=strategy_class, strategy_params_grid=strategy_params_grid)
