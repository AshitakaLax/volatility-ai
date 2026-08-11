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
            # Dynamically instantiate the target sizing engine with the current dictionary of parameters
            sizing_engine = strategy_class(**params)
            oms = OrderManagementSystem(mode="SIMULATION")
            
            start_price = self.data['close'].iloc[0]
            state = BacktestState(initial_cash=100000.0, start_price=start_price)
            
            for timestamp, row in self.data.iterrows():
                current_price = row['close']

                # Every bar, unconditionally -- B4. Strategies maintaining
                # an internal rolling window (RSI, Bayesian posteriors)
                # need continuous ticks even on bars with no trigger.
                # Interim form (price only), per architecture_overview.md
                # Section 5.2 -- Task 4.1 migrates this to record_tick(context).
                sizing_engine.record_tick(current_price)

                # Track peaks and drawdowns every bar (not only on trigger
                # bars) -- B3. A stale/sparse drawdown value here would
                # also feed sizing strategies once threaded through.
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
                    if exec_res.get("status") != OrderStatus.FILLED:
                        # NEW/ACCEPTED/PENDING/PARTIALLY_FILLED/CANCELED/
                        # REJECTED/EXPIRED are all non-complete-fill states
                        # -- lot stays open, nothing credited. (Real
                        # partial-fill accounting -- crediting the filled
                        # portion, reducing shares, leaving the rest open
                        # -- needs ledger support this repo doesn't have
                        # yet; see AssetLotLedger.close_lot and Task 7.2.)
                        logger.warning(
                            f"Sell not filled for lot {lot.order_id}: status={exec_res.get('status')}"
                        )
                        continue

                    filled_qty = exec_res["filled_qty"]
                    filled_price = exec_res["filled_avg_price"]
                    net_sell_proceeds = filled_qty * filled_price
                    allocated_cost_basis = lot.buy_price * filled_qty
                    if net_sell_proceeds < allocated_cost_basis:
                        logger.warning(
                            f"Sell for lot {lot.order_id} rejected: net proceeds "
                            f"{net_sell_proceeds:.2f} would be below cost basis "
                            f"{allocated_cost_basis:.2f} (no-loss invariant)."
                        )
                        continue

                    state.cash += net_sell_proceeds
                    ledger.close_lot(lot)
                
                # 2. Step purchase checks
                if current_price <= state.last_buy_price * (1.0 - step):
                    # total_equity/current_dd already computed above for every bar.

                    # Query the sizing engine (RSI/Drawdown internal states process the tick here)
                    trade_value = sizing_engine.calculate_trade_value(
                        total_equity, current_price, current_dd=current_dd
                    )
                    
                    if state.cash >= trade_value and trade_value > 0:
                        order = oms.execute_buy("TQQQ", trade_value, current_price)
                        if order.get("status") != OrderStatus.FILLED:
                            logger.warning(f"Buy not filled: status={order.get('status')}")
                        else:
                            filled_qty = order["filled_qty"]
                            filled_price = order["filled_avg_price"]
                            ledger.register_buy(order["id"], "TQQQ", filled_price, filled_qty, target)
                            state.cash -= (filled_qty * filled_price)
                            state.last_buy_price = current_price
            
            final_price = self.data['close'].iloc[-1]
            open_assets_val = sum(lot.shares * final_price for lot in ledger.open_lots)
            final_portfolio_value = state.cash + open_assets_val
            
            metrics = PerformanceAnalyzer.calculate_metrics(ledger, final_portfolio_value, 100000.0)
            metrics["Max Drawdown %"] = state.max_drawdown * 100.0
            
            # Merge the strategy parameter dictionary directly into the results table for clean output
            result_row = {
                "Grid Step": step,
                "Profit Target": target,
                **params, 
                **metrics
            }
            results.append(result_row)
            
        logger.info("Hyperparameter sweeping logic execution complete.")
        return pd.DataFrame(results).sort_values(by="Capital Velocity Index", ascending=False)
