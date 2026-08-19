"""
Backtest orchestration: parameter sweeps over the grid-harvesting strategy.

OptimizationController owns one historical dataset and evaluates many
parameter combinations against it. _simulate_single runs exactly one
combination in isolation; run_sweep drives the search across many.

This module is the backtest half of the system. Its live counterpart is
src/live_execution.py, and the two deliberately share their strategy
call sequence through src/decision_cycle.py (Task 7.1) and their
exit-boundary loss check through src/no_loss_guard.py (Task 7.15)
rather than keeping parallel copies that could drift apart.
"""

import logging
from typing import Type, Optional
import concurrent.futures
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
from src.exceptions import ConfigurationError
from src.validation import validate_run_sweep_config
from src.idempotency import ProcessedEventStore
from src.search_strategies import SearchStrategy, GridSearch, BayesianSearch
from src import decision_cycle
from src.no_loss_guard import NoLossViolation, validate_sell

logger = logging.getLogger("Optimizer")

class BacktestState:
    """Enforces isolated state management for simulation iterations."""

    def __init__(self, initial_cash: float, start_price: float):
        """Fresh mutable state for one combination.

        A new instance per combination is what keeps sweeps independent:
        cash, the grid reference price, and the running peak/drawdown all
        start clean, so one combination's trades cannot influence
        another's. start_price seeds last_buy_price so the first grid
        trigger is measured from the dataset's opening price.
        """
        self.cash = initial_cash
        self.last_buy_price = start_price
        self.peak_equity = initial_cash
        self.max_drawdown = 0.0


def _resolve_search_strategy(
    search_strategy, grid_steps, profit_targets, strategy_params_grid, rank_by, search_seed, search_direction="maximize"
) -> SearchStrategy:
    """Task 5.3. None/"grid" -> GridSearch (today's exact exhaustive
    behavior). "bayesian" -> BayesianSearch over the same discrete
    space. An already-constructed SearchStrategy is used as-is,
    letting a caller configure e.g. BayesianSearch's own n_trials
    directly rather than being forced into the default (full
    combination count) budget."""
    if search_strategy is None or search_strategy == "grid":
        return GridSearch(grid_steps, profit_targets, strategy_params_grid)
    if search_strategy == "bayesian":
        return BayesianSearch(
            grid_steps, profit_targets, strategy_params_grid,
            rank_by=rank_by, direction=search_direction, seed=search_seed,
        )
    if isinstance(search_strategy, SearchStrategy):
        return search_strategy
    raise ConfigurationError(
        f"search_strategy must be None, 'grid', 'bayesian', or a SearchStrategy instance, got {search_strategy!r}"
    )


def _run_one_combination(
    controller: "OptimizationController",
    step: float,
    target: float,
    strategy_class: Type[SizingStrategy],
    params: dict,
    symbol: str,
    initial_cash: float,
    cost_model: TransactionCostModel,
    risk_manager: RiskManager,
    on_flat_reentry: str,
):
    """
    Task 4.5. Module-level (not a method) so it, and everything passed
    to it, is picklable for ProcessPoolExecutor when n_jobs > 1 --
    controller (wraps only self.data, a DataFrame), strategy_class,
    and params must all be picklable for that path to work at all.

    Same per-combination try/except isolation (Task 4.4) whether
    called from the sequential loop or a worker process, so behavior
    can't drift between the two paths. Does NOT log the per-iteration
    "Evaluating..." debug line itself -- that stays in run_sweep, in
    the main process only, so subprocess logging setup/noise (an
    explicit concern this task raises) is never a question: worker
    processes only ever log on failure (logger.error below), and even
    that's best-effort, since a freshly spawned process doesn't
    inherit the parent's logging handlers without extra setup this
    task doesn't ask for -- the functional guarantee (an isolated
    failure becomes a returned {"error": ...} row) holds either way,
    independent of whether that log line is actually visible anywhere.

    Returns (result_row, simulation_result) -- simulation_result is
    None on failure (Task 4.6's return_full_results needs the full
    SimulationResult, not just the flattened row, and re-running to
    get it separately would double the work and risk it disagreeing
    with the row that was already reported).
    """
    try:
        sizing_engine = strategy_class(**params)
        result = controller._simulate_single(
            step=step,
            target=target,
            strategy_instance=sizing_engine,
            symbol=symbol,
            initial_cash=initial_cash,
            cost_model=cost_model,
            risk_manager=risk_manager,
            on_flat_reentry=on_flat_reentry,
        )
        result_row = {"Grid Step": step, "Profit Target": target, **params, **result.metrics}
        return result_row, result
    except Exception as e:
        logger.error(f"Combination failed: step={step} target={target} params={params}: {e}")
        return {"Grid Step": step, "Profit Target": target, **params, "error": str(e)}, None

class OptimizationController:
    """Runs parameter sweeps of the grid strategy over one historical dataset.

    The dataset is validated once at construction and then held immutable
    for the controller's lifetime, so every combination in a sweep is
    scored against identical data.
    """

    def __init__(self, historical_data: pd.DataFrame):
        """Validate and retain the historical dataset.

        Validation happens here rather than at sweep time so malformed
        data fails immediately, before any combination runs. Raises
        DataValidationError (Task 2.1) on empty, non-finite,
        non-positive, unsorted, or duplicate-timestamped input.
        """
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
        # mode="SIMULATION" stays a bare string here (Task 4.3): a Mode
        # enum would live in src/order_management_system.py, which isn't
        # in this task's Files touched -- noted as a follow-up dependent
        # on that file, per Task 4.3's own alternative wording, rather
        # than extended here.
        oms = OrderManagementSystem(mode="SIMULATION")

        # Task 4.10: one store per combination run -- in-process is
        # sufficient for SIMULATION mode per that task's own wording
        # ("bounded by the run's lifetime, no restart to survive").
        # See src/idempotency.py's docstring for the full ID-scheme
        # contract (shared with Tasks 7.4/7.14).
        event_store = ProcessedEventStore()

        # Task 4.6: opt-in trade blotter / equity curve capture.
        blotter_records = []
        equity_curve_timestamps = []
        equity_curve_values = []

        start_price = self.data['close'].iloc[0]
        state = BacktestState(initial_cash=initial_cash, start_price=start_price)

        # Task 7.5: the previous bar's close, fed to the cost model so
        # volatility-aware slippage can scale by this bar's move. None
        # on the first bar (no previous close exists) --
        # DynamicSlippageModel falls back to base_bps in that case.
        prev_close = None

        for bar_index, row in enumerate(self.data.itertuples()):
            timestamp = row.Index
            current_price = row.close

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
                open=row.open,
                high=row.high,
                low=row.low,
                close=current_price,
                cash=state.cash,
                equity=total_equity,
                peak_equity=state.peak_equity,
                drawdown=current_dd,
                open_lot_count=len(ledger.open_lots),
                bar_index=bar_index,
            )

            # Every bar, unconditionally -- B4. Routed through the shared
            # canonical decision cycle (Task 7.1) so live and backtest
            # provably call the same code, not two copies.
            decision_cycle.record_tick(strategy_instance, context)

            # Task 4.6: one equity-curve entry per bar, regardless of
            # trade activity, using the bar's start-of-bar equity
            # (matches context.equity's existing convention).
            equity_curve_timestamps.append(context.timestamp)
            equity_curve_values.append(context.equity)

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

                # Task 7.15: the ONE no-loss guard. This block used to
                # carry its own copy of the net_sell_proceeds /
                # allocated_cost_basis comparison; it now calls the
                # canonical implementation so the two cannot drift.
                try:
                    economics = validate_sell(
                        lot, filled_qty, filled_price, cost_model,
                        context=context, prev_close=prev_close,
                    )
                except NoLossViolation:
                    continue  # already logged by the guard
                net_sell_proceeds = economics.net_sell_proceeds

                def _apply_sell_fill():
                    """Side effects of one confirmed sell, applied at most once.

                    Wrapped as a closure so ProcessedEventStore.apply_once
                    (Task 4.10) can guard it by order id -- a duplicated
                    fill event must not credit cash or close a lot twice.
                    """
                    state.cash += net_sell_proceeds
                    ledger.close_lot(lot)
                    blotter_records.append({
                        "timestamp": context.timestamp,
                        "side": "sell",
                        "price": filled_price,
                        "qty": filled_qty,
                        "equity": context.equity,
                    })
                    if len(ledger.open_lots) == 0 and on_flat_reentry == "reset_to_market":
                        state.last_buy_price = context.price

                event_store.apply_once(exec_res["id"], _apply_sell_fill, event_kind="sell_fill")

            # 2. Step purchase checks -- delegated to the shared canonical
            # decision cycle (Task 7.1), which live_execution.py also
            # calls, so the trigger/sizing/clamp sequence exists in
            # exactly one place. state.cash (not context.cash) is passed
            # deliberately: it reflects this same bar's harvest proceeds,
            # which have already landed by the time a buy is sized.
            decision = decision_cycle.evaluate_grid_decision(
                strategy_instance, risk_manager, context, state.last_buy_price, step, state.cash
            )
            if decision.triggered:
                trade_value = decision.clamped_trade_value

                if state.cash >= trade_value and trade_value > 0:
                    order = oms.execute_buy(symbol, trade_value, context.price)
                    if order.get("status") != OrderStatus.FILLED:
                        logger.warning(f"Buy not filled: status={order.get('status')}")
                    else:
                        filled_qty = order["filled_qty"]
                        filled_price = order["filled_avg_price"]

                        effective_price, buy_cost = cost_model.apply_buy(
                            filled_price, filled_qty, context=context, prev_close=prev_close
                        )
                        total_buy_outlay = (effective_price * filled_qty) + buy_cost
                        per_share_cost_basis = total_buy_outlay / filled_qty

                        def _apply_buy_fill():
                            """Side effects of one confirmed buy, applied at most once.

                            Closure for the same reason as _apply_sell_fill:
                            idempotency is enforced by order id, so a
                            replayed fill cannot open a second lot or debit
                            cash twice.
                            """
                            ledger.register_buy(order["id"], symbol, per_share_cost_basis, filled_qty, target)
                            state.cash -= total_buy_outlay
                            state.last_buy_price = context.price
                            blotter_records.append({
                                "timestamp": context.timestamp,
                                "side": "buy",
                                "price": filled_price,
                                "qty": filled_qty,
                                "equity": context.equity,
                            })

                        event_store.apply_once(order["id"], _apply_buy_fill, event_kind="buy_fill")

            # End of bar: this bar's close becomes the next bar's
            # prev_close. At the loop's own indentation so it advances
            # every bar, not only on triggering ones (Task 7.5).
            prev_close = current_price

        final_price = self.data['close'].iloc[-1]
        open_assets_val = sum(lot.shares * final_price for lot in ledger.open_lots)
        final_portfolio_value = state.cash + open_assets_val

        metrics = PerformanceAnalyzer.calculate_metrics(ledger, final_portfolio_value, initial_cash)
        metrics["Max Drawdown %"] = state.max_drawdown * 100.0

        # Task 4.6. params captures every input _simulate_single itself
        # actually received -- the strategy's own constructor-derived
        # attributes (e.g. allocation_pct) are merged in via vars(),
        # since a "what configured this run" record that omitted the
        # strategy's own settings would be missing exactly the thing
        # someone re-inspecting a specific combination's blotter would
        # want to know. This isn't literally specified (the task only
        # says "set params"), documented here as a deliberate choice.
        params = {
            "step": step,
            "target": target,
            "symbol": symbol,
            "initial_cash": initial_cash,
            "on_flat_reentry": on_flat_reentry,
            **vars(strategy_instance),
        }

        return SimulationResult(
            metrics=metrics,
            trade_blotter=pd.DataFrame(blotter_records),
            equity_curve=pd.Series(data=equity_curve_values, index=pd.Index(equity_curve_timestamps, name="timestamp")),
            params=params,
        )

    def run_sweep(
        self,
        grid_steps: list,
        profit_targets: list,
        strategy_class: Type[SizingStrategy],
        strategy_params_grid: list[dict],
        cost_model: TransactionCostModel = None,
        risk_manager: RiskManager = None,
        on_flat_reentry: str = "stale_reference",
        symbol: str = "TQQQ",
        initial_cash: float = 100_000.0,
        n_jobs: int = 1,
        return_full_results: bool = False,
        rank_by: str = "Capital Velocity Index",
        tie_break_by: Optional[str] = None,
        search_strategy=None,
        search_seed: Optional[int] = None,
        search_direction: str = "maximize",
    ) -> pd.DataFrame:
        """
        Creates a parametric multi-dimensional sweep.
        :param strategy_class: The uninstantiated SizingStrategy subclass (e.g., RsiMomentumSizing).
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
        :param symbol: Ticker traded. Defaults to "TQQQ" -- exactly today's behavior.
        :param initial_cash: Starting cash for every combination. Defaults to 100_000.0 --
            exactly today's behavior.
        :param n_jobs: 1 (default) runs combinations sequentially in this process --
            exactly today's behavior. >1 runs combinations across a
            ProcessPoolExecutor with that many workers. Row order may differ
            from n_jobs=1 (workers complete in whatever order they finish),
            but the *set* of rows is identical -- worker completion order
            never affects ranking or any metric value (Determinism contract,
            architecture_overview.md Section 5.5-adjacent). self.data,
            strategy_class, and every params dict must all be picklable
            for n_jobs > 1 to work.
        :param return_full_results: False (default) returns a single summary
            DataFrame, exactly today's behavior -- return type unchanged.
            True additionally returns the list of per-combination
            SimulationResult objects (trade_blotter, equity_curve, params) as
            (summary_df, full_results); a failed combination contributes None
            to that list rather than a SimulationResult.
        :param rank_by: Column results are sorted by, descending. Defaults to
            "Capital Velocity Index" -- exactly today's behavior. Raises a
            clear error (naming available columns) if the column doesn't
            exist, rather than a raw pandas KeyError.
        :param tie_break_by: Optional secondary sort column for rows tied on
            rank_by, also descending. None (default) -- exactly today's
            behavior (ties broken arbitrarily by pandas' stable sort).
        :param search_strategy: None or "grid" (default) uses GridSearch --
            exactly today's exhaustive itertools.product behavior, same
            combinations, same order. "bayesian" uses Optuna-backed
            BayesianSearch over the same discrete space, with search_seed
            for reproducibility and a trial budget defaulting to the full
            combination count (pass a pre-configured BayesianSearch
            instance instead of the string for a smaller budget). A
            SearchStrategy instance can be passed directly instead of a
            string for advanced/custom configurations.
        :param search_seed: Seed for search_strategy="bayesian"'s sampler.
            Ignored for grid search (nothing stochastic to seed).
        :param search_direction: "maximize" (default) or "minimize" -- only
            affects search_strategy="bayesian" (passed to Optuna). Grid
            search always enumerates exhaustively regardless of direction;
            ranking/sorting is controlled separately by rank_by/ascending.
        """
        # Task 4.9: validate everything up front, before building
        # combinations or running anything -- a bad config fails
        # immediately rather than partway through a potentially
        # expensive sweep. Replaces the two inline checks this
        # previously did itself.
        validate_run_sweep_config(
            grid_steps=grid_steps,
            profit_targets=profit_targets,
            n_jobs=n_jobs,
            on_flat_reentry=on_flat_reentry,
            initial_cash=initial_cash,
        )
        cost_model = cost_model if cost_model is not None else ZeroCostModel()
        risk_manager = risk_manager if risk_manager is not None else RiskManager()
        results = []
        full_results = []

        resolved_search_strategy = _resolve_search_strategy(
            search_strategy, grid_steps, profit_targets, strategy_params_grid, rank_by, search_seed, search_direction
        )
        total_combinations = len(grid_steps) * len(profit_targets) * len(strategy_params_grid)
        logger.info(f"Starting parameter sweep. Evaluating up to {total_combinations} total variations.")

        idx = 0
        if n_jobs == 1:
            while True:
                suggestion = resolved_search_strategy.suggest()
                if suggestion is None:
                    break
                idx += 1
                logger.debug(
                    f"Evaluating iteration [{idx}]: Step={suggestion['grid_step']}, "
                    f"Target={suggestion['profit_target']}, Params={suggestion['strategy_params']}"
                )
                row, sim_result = _run_one_combination(
                    self, suggestion["grid_step"], suggestion["profit_target"], strategy_class,
                    suggestion["strategy_params"], symbol, initial_cash, cost_model, risk_manager, on_flat_reentry,
                )
                resolved_search_strategy.report(suggestion, sim_result)
                results.append(row)
                full_results.append(sim_result)
        else:
            # One executor reused across every batch (rather than one per
            # batch) -- avoids repeated pool spin-up/teardown overhead.
            with concurrent.futures.ProcessPoolExecutor(max_workers=n_jobs) as executor:
                while True:
                    batch = []
                    for _ in range(n_jobs):
                        suggestion = resolved_search_strategy.suggest()
                        if suggestion is None:
                            break
                        batch.append(suggestion)
                    if not batch:
                        break

                    future_to_suggestion = {
                        executor.submit(
                            _run_one_combination, self, s["grid_step"], s["profit_target"], strategy_class,
                            s["strategy_params"], symbol, initial_cash, cost_model, risk_manager, on_flat_reentry,
                        ): s
                        for s in batch
                    }
                    for future in concurrent.futures.as_completed(future_to_suggestion):
                        suggestion = future_to_suggestion[future]
                        row, sim_result = future.result()
                        resolved_search_strategy.report(suggestion, sim_result)
                        results.append(row)
                        full_results.append(sim_result)

        logger.info("Hyperparameter sweeping logic execution complete.")

        summary_df = pd.DataFrame(results)

        if rank_by not in summary_df.columns:
            available = sorted(summary_df.columns.tolist())
            raise ConfigurationError(
                f"rank_by column {rank_by!r} not found in results. Available columns: {available}"
            )
        if tie_break_by is not None and tie_break_by not in summary_df.columns:
            available = sorted(summary_df.columns.tolist())
            raise ConfigurationError(
                f"tie_break_by column {tie_break_by!r} not found in results. Available columns: {available}"
            )

        missing_rank_count = summary_df[rank_by].isna().sum()
        if missing_rank_count > 0:
            logger.warning(
                f"{missing_rank_count} row(s) have no {rank_by!r} value (error rows or NaN/inf metrics) "
                f"and were excluded from ranking -- sunk to the bottom regardless of sort direction."
            )

        sort_columns = [rank_by] if tie_break_by is None else [rank_by, tie_break_by]
        # Sort via the DataFrame's own resulting index (not a plain
        # sort_values-and-done) so full_results -- a separate,
        # same-order-as-results list -- can be reordered identically and
        # stay paired with the right row after sorting (Task 4.6's
        # return_full_results needs summary_df.iloc[i] and
        # full_results[i] to correspond). na_position="last" is
        # pandas' own default, made explicit here since sinking
        # rank_by-missing rows to the bottom is now a stated contract,
        # not an implicit side effect.
        sorted_df = summary_df.sort_values(by=sort_columns, ascending=False, na_position="last")
        sort_order = sorted_df.index
        summary_df = sorted_df.reset_index(drop=True)
        full_results = [full_results[i] for i in sort_order]

        if return_full_results:
            return summary_df, full_results
        return summary_df

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
