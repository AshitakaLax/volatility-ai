import itertools
import logging
import pandas as pd
from src import data_validation
from src.ledger import AssetLotLedger
from src.size_calculators import FixedPortfolioPercentage
from src.order_management_system import OrderManagementSystem, OrderStatus
from src.performance_analyzer import PerformanceAnalyzer
from src.cost_models import TransactionCostModel, ZeroCostModel
from src.risk_manager import RiskManager

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
        data_validation.validate(historical_data)
        self.data = historical_data
        logger.info(f"OptimizationController initialized with historical dataset length: {len(historical_data)}")

    def run_sweep(
        self,
        grid_steps: list,
        profit_targets: list,
        strategy_class,
        strategy_params_grid: list[dict],
        cost_model: TransactionCostModel | None = None,
        risk_manager: RiskManager | None = None,
    ) -> pd.DataFrame:
        """Creates a parametric multi-dimensional sweep."""
        results = []
        cost_model = ZeroCostModel() if cost_model is None else cost_model
        risk_manager = RiskManager() if risk_manager is None else risk_manager
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
                current_price = float(row['close'])
                sizing_engine.record_tick(current_price)
                open_assets_val = sum(lot.shares * current_price for lot in ledger.open_lots)
                total_equity = state.cash + open_assets_val
                if total_equity > state.peak_equity:
                    state.peak_equity = total_equity
                current_dd = (state.peak_equity - total_equity) / state.peak_equity
                if current_dd > state.max_drawdown:
                    state.max_drawdown = current_dd

                marketable = ledger.get_marketable_lots(current_price)
                for lot in marketable:
                    exec_res = oms.execute_sell(lot.symbol, lot.shares, lot.target_sell_price)
                    if exec_res.get("status") == OrderStatus.FILLED.value:
                        filled_qty = float(exec_res.get("filled_qty", exec_res.get("qty", 0.0)))
                        filled_price = exec_res.get("filled_avg_price")
                        if filled_qty > 0 and filled_price is not None:
                            effective_price, sell_cost = cost_model.apply_sell(float(filled_price), filled_qty)
                            state.cash += filled_qty * effective_price - sell_cost
                            ledger.close_lot(lot)
                    else:
                        logger.warning(f"Sell not filled for lot {lot.symbol}: status={exec_res.get('status')}")

                if current_price <= state.last_buy_price * (1.0 - step):
                    open_assets_val = sum(lot.shares * current_price for lot in ledger.open_lots)
                    total_equity = state.cash + open_assets_val
                    if total_equity > state.peak_equity:
                        state.peak_equity = total_equity
                    current_dd = (state.peak_equity - total_equity) / state.peak_equity
                    if current_dd > state.max_drawdown:
                        state.max_drawdown = current_dd
                    proposed_trade_value = sizing_engine.calculate_trade_value(total_equity, current_price, current_dd)
                    trade_value = risk_manager.clamp_trade_value(
                        proposed_trade_value,
                        total_equity,
                        state.cash,
                        len(ledger.open_lots),
                    )
                    if state.cash >= trade_value and trade_value > 0:
                        order = oms.execute_buy("TQQQ", trade_value, current_price)
                        if order.get("status") == OrderStatus.FILLED.value:
                            filled_qty = float(order.get("filled_qty", order.get("qty", 0.0)))
                            filled_price = order.get("filled_avg_price")
                            if filled_qty > 0 and filled_price is not None:
                                effective_price, buy_cost = cost_model.apply_buy(float(filled_price), filled_qty)
                                actual_notional = filled_qty * effective_price + buy_cost
                                if state.cash >= actual_notional:
                                    state.cash -= actual_notional
                                    ledger.register_buy(order["id"], "TQQQ", effective_price, filled_qty, target)
                        else:
                            logger.warning(f"Buy not filled for TQQQ: status={order.get('status')}")

            final_price = float(self.data['close'].iloc[-1])
            open_assets_val = sum(lot.shares * final_price for lot in ledger.open_lots)
            final_portfolio_value = state.cash + open_assets_val
            metrics = PerformanceAnalyzer.calculate_metrics(ledger, final_portfolio_value, 100000.0)
            metrics["Max Drawdown %"] = state.max_drawdown * 100.0
            results.append({"Grid Step": step, "Profit Target": target, **params, **metrics})

        logger.info("Hyperparameter sweeping logic execution complete.")
        return pd.DataFrame(results).sort_values(by="Capital Velocity Index", ascending=False)

    def validate_finalists_intraday(
        self,
        finalist_params: list[dict],
        intraday_data: pd.DataFrame,
        *,
        strategy_class,
        strategy_params_grid: list[dict],
        intrabar_priority: str = "sell_first",
    ) -> pd.DataFrame:
        """Run the opt-in OHLC intraday validation pass for daily finalists."""
        from src.intraday_validation import IntradayValidator
        validator = IntradayValidator(intrabar_priority=intrabar_priority)
        return validator.validate_finalists_intraday(
            finalist_params,
            intraday_data,
            strategy_class=strategy_class,
            strategy_params_grid=strategy_params_grid,
        )
