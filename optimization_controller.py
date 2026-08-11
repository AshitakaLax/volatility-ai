import itertools
import logging
import pandas as pd
from src.ledger import AssetLotLedger
from src.size_calculators import FixedPortfolioPercentage
from src.order_management_system import OrderManagementSystem, OrderStatus
from src.performance_analyzer import PerformanceAnalyzer
from src import data_validation
from src.cost_models import TransactionCostModel, ZeroCostModel
from src import intraday_validation
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
        cost_model: TransactionCostModel = None,
        risk_manager: RiskManager = None,
        on_flat_reentry: str = "stale_reference",
    ) -> pd.DataFrame:
        """
        Creates a parametric multi-dimensional sweep.
        :param strategy_class: The uninstantiated class of the strategy (e.g., RsiMomentumSizing).
        :param strategy_params_grid: A list of keyword-argument dictionaries to instantiate the strategy.
        :param cost_model: Commission/slippage model applied to every fill. Defaults to
            ZeroCostModel() (zero commission, zero slippage) -- exactly today's behavior.
        :param risk_manager: Clamps proposed new-buy value. Defaults to RiskManager() with
            both limits unset (unlimited) -- exactly today's behavior.
        :param on_flat_reentry: "stale_reference" (default, exactly today's behavior) keeps
            last_buy_price as-is when the portfolio goes fully flat (no open lots) --
            the next grid trigger compares against that stale reference. "reset_to_market"
            resets last_buy_price to the current bar's price the moment the portfolio goes
            flat, so the next trigger is measured from the price level at which it went flat.
        """
        if on_flat_reentry not in ("stale_reference", "reset_to_market"):
            raise ValueError(
                f"on_flat_reentry must be 'stale_reference' or 'reset_to_market', got {on_flat_reentry!r}"
            )
        cost_model = cost_model if cost_model is not None else ZeroCostModel()
        risk_manager = risk_manager if risk_manager is not None else RiskManager()
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

                    # Cost model runs on the confirmed fill, after the
                    # status check -- effective_price/sell_cost feed the
                    # no-loss check below so it reflects actual realized
                    # economics, not just the quoted price (Task 2.2).
                    effective_price, sell_cost = cost_model.apply_sell(filled_price, filled_qty)
                    net_sell_proceeds = (effective_price * filled_qty) - sell_cost
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

                    if len(ledger.open_lots) == 0 and on_flat_reentry == "reset_to_market":
                        state.last_buy_price = current_price
                
                # 2. Step purchase checks
                if current_price <= state.last_buy_price * (1.0 - step):
                    # total_equity/current_dd already computed above for every bar.

                    # Query the sizing engine (RSI/Drawdown internal states process the tick here)
                    trade_value = sizing_engine.calculate_trade_value(
                        total_equity, current_price, current_dd=current_dd
                    )
                    trade_value = risk_manager.clamp_trade_value(
                        trade_value, total_equity, state.cash, len(ledger.open_lots)
                    )
                    
                    if state.cash >= trade_value and trade_value > 0:
                        order = oms.execute_buy("TQQQ", trade_value, current_price)
                        if order.get("status") != OrderStatus.FILLED:
                            logger.warning(f"Buy not filled: status={order.get('status')}")
                        else:
                            filled_qty = order["filled_qty"]
                            filled_price = order["filled_avg_price"]

                            # Cost model runs on the confirmed fill, after
                            # the status check, before decrementing cash
                            # (Task 2.2). buy_cost is folded into a
                            # per-share cost basis (rather than tracked
                            # separately) so the sell-side no-loss check's
                            # existing lot.buy_price * filled_qty formula
                            # stays correct unchanged -- it already
                            # includes the buy-side commission this way.
                            effective_price, buy_cost = cost_model.apply_buy(filled_price, filled_qty)
                            total_buy_outlay = (effective_price * filled_qty) + buy_cost
                            per_share_cost_basis = total_buy_outlay / filled_qty

                            ledger.register_buy(order["id"], "TQQQ", per_share_cost_basis, filled_qty, target)
                            state.cash -= total_buy_outlay
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

    def validate_finalists_intraday(
        self,
        finalist_params: list,
        intraday_data: pd.DataFrame,
        strategy_class,
        cost_model: TransactionCostModel = None,
        intrabar_priority: str = "sell_first",
    ) -> pd.DataFrame:
        """
        Task 2.3 (F2). Re-runs each finalist combination -- typically a
        short list picked from a prior daily-close run_sweep() -- against
        minute-bar intraday_data, using high/low to catch any intrabar
        sell-target or grid-trigger touch the daily pass would have
        missed. Strictly additive: run_sweep()'s own behavior is
        unaffected by this method existing or being called.

        :param finalist_params: list of {"grid_step": float, "profit_target": float,
            "strategy_params": dict} -- one entry per finalist combination to re-check.
        :param intraday_data: minute-bar OHLC data (needs open/high/low/close),
            same index conventions as run_sweep's historical_data.
        :param cost_model: applied identically to both the daily comparison run
            and the intraday replay, so the comparison isolates the intrabar
            effect rather than mixing it with a cost-model difference.
        """
        intraday_validation.validate_intraday_schema(intraday_data)

        rows = []
        for finalist in finalist_params:
            grid_step = finalist["grid_step"]
            profit_target = finalist["profit_target"]
            strategy_params = finalist.get("strategy_params", {})

            daily_result = self.run_sweep(
                grid_steps=[grid_step],
                profit_targets=[profit_target],
                strategy_class=strategy_class,
                strategy_params_grid=[strategy_params],
                cost_model=cost_model,
            ).iloc[0]

            intraday_metrics = intraday_validation.simulate_single_intraday(
                intraday_data=intraday_data,
                grid_step=grid_step,
                profit_target=profit_target,
                strategy_class=strategy_class,
                strategy_params=strategy_params,
                cost_model=cost_model,
                intrabar_priority=intrabar_priority,
            )

            rows.append({
                "Grid Step": grid_step,
                "Profit Target": profit_target,
                **strategy_params,
                "Daily Closed Trades": daily_result["Closed Trade Count"],
                "Intraday Closed Trades": intraday_metrics["Closed Trade Count"],
                "Daily Final Equity": daily_result["Final Equity"],
                "Intraday Final Equity": intraday_metrics["Final Equity"],
                "Diverges": daily_result["Closed Trade Count"] != intraday_metrics["Closed Trade Count"],
            })

        return pd.DataFrame(rows)
