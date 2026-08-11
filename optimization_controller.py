import itertools
import logging
import pandas as pd
from src.ledger import AssetLotLedger
from src.size_calculators import FixedPortfolioPercentage
from src.order_management_system import OrderManagementSystem, OrderStatus
from src.performance_analyzer import PerformanceAnalyzer

logger = logging.getLogger("Optimizer")

class BacktestState:
    """Enforces isolated state management for simulation iterations."""
    def __init__(self, initial_cash: float, start_price: float):
        self.cash = initial_cash
        self.last_buy_price = start_price
        self.peak_equity = initial_cash
        self.max_drawdown = 0.0

class OptimizationController:
    def __init__(self, historical_data: pd.DataFrame):
        self.data = historical_data
        logger.info(f"OptimizationController initialized with historical dataset length: {len(historical_data)}")

    def run_sweep(self, grid_steps: list, profit_targets: list, strategy_class, strategy_params_grid: list[dict]) -> pd.DataFrame:
        """
        Creates a parametric multi-dimensional sweep.
        :param strategy_class: The uninstantiated class of the strategy (e.g., RsiMomentumSizing).
        :param strategy_params_grid: A list of keyword-argument dictionaries to instantiate the strategy.
        """
        results = []
        combinations = list(itertools.product(grid_steps, profit_targets, strategy_params_grid))
        logger.info(f"Starting parameter sweep. Evaluating {len(combinations)} total variations.")
        
        for idx, (step, target, params) in enumerate(combinations):
            logger.debug(f"Evaluating iteration [{idx + 1}/{len(combinations)}]: Step={step}, Target={target}, Params={params}")
            
            ledger = AssetLotLedger()
            sizing_engine = strategy_class(**params)
            oms = OrderManagementSystem(mode="SIMULATION")
            
            start_price = self.data['close'].iloc[0]
            state = BacktestState(initial_cash=100000.0, start_price=start_price)
            
            for timestamp, row in self.data.iterrows():
                current_price = row['close']

                # Every sizing strategy receives exactly one tick for every bar,
                # before any bar-level trading decisions are evaluated.
                sizing_engine.record_tick(current_price)

                # Track portfolio equity, peak equity, and drawdown on every bar,
                # not only on bars that happen to trigger a grid purchase.
                open_assets_val = sum(lot.shares * current_price for lot in ledger.open_lots)
                total_equity = state.cash + open_assets_val
                if total_equity > state.peak_equity:
                    state.peak_equity = total_equity
                current_dd = (state.peak_equity - total_equity) / state.peak_equity
                if current_dd > state.max_drawdown:
                    state.max_drawdown = current_dd
                
                # 1. Harvest target checks
                marketable = ledger.get_marketable_lots(current_price)
                for lot in marketable:
                    exec_res = oms.execute_sell(lot.symbol, lot.shares, lot.target_sell_price)
                    if exec_res.get("status") == OrderStatus.FILLED.value:
                        filled_qty = exec_res.get("filled_qty", exec_res.get("qty", 0.0))
                        filled_price = exec_res.get("filled_avg_price")
                        if filled_qty > 0 and filled_price is not None:
                            state.cash += float(filled_qty) * float(filled_price)
                            ledger.close_lot(lot)
                    else:
                        logger.warning(
                            f"Sell not filled for lot {lot.symbol}: status={exec_res.get('status')}"
                        )
                
                # 2. Step purchase checks
                if current_price <= state.last_buy_price * (1.0 - step):
                    # Recalculate equity after any same-bar harvest before sizing the buy.
                    open_assets_val = sum(lot.shares * current_price for lot in ledger.open_lots)
                    total_equity = state.cash + open_assets_val
                    
                    # Track peaks and drawdowns for the post-harvest account state as well.
                    if total_equity > state.peak_equity:
                        state.peak_equity = total_equity
                    current_dd = (state.peak_equity - total_equity) / state.peak_equity
                    if current_dd > state.max_drawdown:
                        state.max_drawdown = current_dd

                    trade_value = sizing_engine.calculate_trade_value(total_equity, current_price, current_dd)
                    
                    if state.cash >= trade_value and trade_value > 0:
                        order = oms.execute_buy("TQQQ", trade_value, current_price)
                        if order.get("status") == OrderStatus.FILLED.value:
                            filled_qty = order.get("filled_qty", order.get("qty", 0.0))
                            filled_price = order.get("filled_avg_price")
                            if filled_qty > 0 and filled_price is not None:
                                filled_notional = float(filled_qty) * float(filled_price)
                                state.cash -= filled_notional
                                ledger.register_buy(
                                    order["id"], "TQQQ", float(filled_price), float(filled_qty), target
                                )
                        else:
                            logger.warning(
                                f"Buy not filled for TQQQ: status={order.get('status')}"
                            )
            
            final_price = self.data['close'].iloc[-1]
            open_assets_val = sum(lot.shares * final_price for lot in ledger.open_lots)
            final_portfolio_value = state.cash + open_assets_val
            
            metrics = PerformanceAnalyzer.calculate_metrics(ledger, final_portfolio_value, 100000.0)
            metrics["Max Drawdown %"] = state.max_drawdown * 100.0
            
            result_row = {
                "Grid Step": step,
                "Profit Target": target,
                **params, 
                **metrics
            }
            results.append(result_row)
            
        logger.info("Hyperparameter sweeping logic execution complete.")
        return pd.DataFrame(results).sort_values(by="Capital Velocity Index", ascending=False)