import itertools
import logging
import pandas as pd
from src.ledger import AssetLotLedger
from src.size_calculators import FixedPortfolioPercentage, SizingStrategy
from src.order_management_system import OrderManagementSystem, OrderStatus
from src.performance_analyzer import PerformanceAnalyzer
from src import data_validation
from src.cost_models import TransactionCostModel, ZeroCostModel
from src import intraday_validation
from src.risk_manager import RiskManager
from src.market_context import MarketContext, SimulationResult

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

    def _simulate_single(
        self,
        step: float,
        target: float,
        strategy_instance: SizingStrategy,
        symbol: str,
        initial_cash: float,
        cost_model: TransactionCostModel,
        risk_manager: RiskManager,
        on_flat_reentry: str = "stale_reference",
    ) -> SimulationResult:
        """
        Task 4.1. One isolated combination: fresh AssetLotLedger and
        OrderManagementSystem every call, no state leaks between calls.
        strategy_instance is already-constructed (run_sweep instantiates
        it per combination, same as before extraction).

        on_flat_reentry isn't in Task 4.1's illustrative signature but is
        pre-existing behavior (Task 3.3) this extraction must preserve
        unchanged, per this task's own Non-goals ("this task extracts
        and unifies existing behavior -- it does not change ... logic").
        Threaded through as an extra parameter rather than dropped.
        """
        ledger = AssetLotLedger()
        oms = OrderManagementSystem(mode="SIMULATION")

        start_price = self.data['close'].iloc[0]
        state = BacktestState(initial_cash=initial_cash, start_price=start_price)

        for bar_index, (timestamp, row) in enumerate(self.data.iterrows()):
            current_price = row['close']

            # Peaks/drawdown every bar (B3), before constructing context,
            # since MarketContext.equity/peak_equity/drawdown need this
            # bar's values.
            open_assets_val = sum(lot.shares * current_price for lot in ledger.open_lots)
            total_equity = state.cash + open_assets_val
            if total_equity > state.peak_equity:
                state.peak_equity = total_equity
            current_dd = (state.peak_equity - total_equity) / state.peak_equity
            if current_dd > state.max_drawdown:
                state.max_drawdown = current_dd

            context = MarketContext(
                timestamp=timestamp,
                open=row['open'],
                high=row['high'],
                low=row['low'],
                close=current_price,
                cash=state.cash,
                equity=total_equity,
                peak_equity=state.peak_equity,
                drawdown=current_dd,
                open_lot_count=len(ledger.open_lots),
                bar_index=bar_index,
            )

            # Every bar, unconditionally -- B4.
            strategy_instance.record_tick(context)

            # 1. Harvest target checks
            marketable = ledger.get_marketable_lots(context.price)
            for lot in marketable:
                exec_res = oms.execute_sell(lot.symbol, lot.shares, lot.target_sell_price)
                if exec_res.get("status") != OrderStatus.FILLED:
                    logger.warning(
                        f"Sell not filled for lot {lot.order_id}: status={exec_res.get('status')}"
                    )
                    continue

                filled_qty = exec_res["filled_qty"]
                filled_price = exec_res["filled_avg_price"]

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
                    state.last_buy_price = context.price

            # 2. Step purchase checks -- now delegated to the strategy's
            # _check_grid_trigger (default implementation is identical to
            # the pre-Task-4.1 inline check), not a hardcoded inline check.
            if strategy_instance._check_grid_trigger(context, state.last_buy_price, step):
                trade_value = strategy_instance.calculate_trade_value(context)
                trade_value = risk_manager.clamp_trade_value(
                    trade_value, context.equity, state.cash, context.open_lot_count
                )

                if state.cash >= trade_value and trade_value > 0:
                    order = oms.execute_buy(symbol, trade_value, context.price)
                    if order.get("status") != OrderStatus.FILLED:
                        logger.warning(f"Buy not filled: status={order.get('status')}")
                    else:
                        filled_qty = order["filled_qty"]
                        filled_price = order["filled_avg_price"]

                        effective_price, buy_cost = cost_model.apply_buy(filled_price, filled_qty)
                        total_buy_outlay = (effective_price * filled_qty) + buy_cost
                        per_share_cost_basis = total_buy_outlay / filled_qty

                        ledger.register_buy(order["id"], symbol, per_share_cost_basis, filled_qty, target)
                        state.cash -= total_buy_outlay
                        state.last_buy_price = context.price

        final_price = self.data['close'].iloc[-1]
        open_assets_val = sum(lot.shares * final_price for lot in ledger.open_lots)
        final_portfolio_value = state.cash + open_assets_val

        metrics = PerformanceAnalyzer.calculate_metrics(ledger, final_portfolio_value, initial_cash)
        metrics["Max Drawdown %"] = state.max_drawdown * 100.0

        return SimulationResult(metrics=metrics)

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

            # Dynamically instantiate the target sizing engine with the current dictionary of parameters
            sizing_engine = strategy_class(**params)

            result = self._simulate_single(
                step=step,
                target=target,
                strategy_instance=sizing_engine,
                symbol="TQQQ",
                initial_cash=100_000.0,
                cost_model=cost_model,
                risk_manager=risk_manager,
                on_flat_reentry=on_flat_reentry,
            )

            # Merge the strategy parameter dictionary directly into the results table for clean output
            result_row = {
                "Grid Step": step,
                "Profit Target": target,
                **params,
                **result.metrics
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
