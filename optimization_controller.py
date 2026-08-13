import itertools
import logging
from concurrent.futures import ProcessPoolExecutor, as_completed
from typing import Type

import pandas as pd

from src import data_validation
from src.cost_models import TransactionCostModel, ZeroCostModel
from src.ledger import AssetLotLedger
from src.market_context import MarketContext, SimulationResult
from src.order_management_system import Mode, OrderManagementSystem, OrderStatus
from src.performance_analyzer import PerformanceAnalyzer
from src.risk_manager import RiskManager
from src.search_strategies import BayesianSearch, GridSearch, SearchStrategy
from src.size_calculators import SizingStrategy
from src.validation import validate_sweep_config

logger = logging.getLogger("Optimizer")


class BacktestState:
    def __init__(self, initial_cash: float, start_price: float):
        self.cash = initial_cash
        self.last_buy_price = start_price
        self.peak_equity = initial_cash
        self.max_drawdown = 0.0


def _run_single_combination(controller, idx, total, step, target, strategy_class, params, symbol, initial_cash, cost_model, risk_manager, return_full_results=False):
    try:
        strategy_instance = strategy_class(**params)
        simulation = controller._simulate_single(step, target, strategy_instance, symbol, initial_cash, cost_model, risk_manager)
        return {"Grid Step": step, "Profit Target": target, **params, **simulation.metrics}, simulation if return_full_results else None
    except Exception as exc:
        logger.error(f"Combination failed [{idx + 1}/{total}] step={step} target={target} params={params}: {exc}")
        return {"Grid Step": step, "Profit Target": target, **params, "error": str(exc)}, None


def _rank_results(results: pd.DataFrame, rank_by: str = "Capital Velocity Index", direction: str = "maximize") -> pd.DataFrame:
    if results.empty:
        return results
    if direction not in {"maximize", "minimize"}:
        raise ValueError("direction must be 'maximize' or 'minimize'")
    ranked = results.copy()
    fallback = float("-inf") if direction == "maximize" else float("inf")
    if rank_by not in ranked.columns:
        ranked[rank_by] = fallback
    ranked["_ranking_metric"] = pd.to_numeric(ranked[rank_by], errors="coerce")
    ranked["_ranking_metric"] = ranked["_ranking_metric"].where(ranked["_ranking_metric"].notna(), fallback)
    ranked["_ranking_metric"] = ranked["_ranking_metric"].where(ranked["_ranking_metric"] != float("inf"), fallback)
    ranked["_ranking_metric"] = ranked["_ranking_metric"].where(ranked["_ranking_metric"] != float("-inf"), fallback)
    ranked["_result_order"] = range(len(ranked))
    ranked = ranked.sort_values(by=["_ranking_metric", "_result_order"], ascending=[direction == "minimize", True], kind="mergesort")
    return ranked.drop(columns=["_ranking_metric", "_result_order"])


class OptimizationController:
    def __init__(self, historical_data: pd.DataFrame):
        data_validation.validate(historical_data)
        self.data = historical_data
        self._on_flat_reentry = "stale_reference"
        logger.info(f"OptimizationController initialized with historical dataset length: {len(historical_data)}")

    def _simulate_single(self, step: float, target: float, strategy_instance: SizingStrategy, symbol: str, initial_cash: float, cost_model: TransactionCostModel, risk_manager: RiskManager) -> SimulationResult:
        ledger = AssetLotLedger()
        oms = OrderManagementSystem(mode=Mode.SIMULATION)
        state = BacktestState(initial_cash, float(self.data["close"].iloc[0]))
        trade_blotter, equity_points = [], []
        previous_close = None
        for bar_index, row in enumerate(self.data.itertuples()):
            timestamp, current_price = row.Index, float(row.close)
            equity = state.cash + sum(lot.shares * current_price for lot in ledger.open_lots)
            if equity > state.peak_equity:
                state.peak_equity = equity
            drawdown = (state.peak_equity - equity) / state.peak_equity if state.peak_equity else 0.0
            state.max_drawdown = max(state.max_drawdown, drawdown)
            context = MarketContext(timestamp=timestamp.to_pydatetime() if hasattr(timestamp, "to_pydatetime") else timestamp, open=float(getattr(row, "open", current_price)), high=float(getattr(row, "high", current_price)), low=float(getattr(row, "low", current_price)), close=current_price, cash=float(state.cash), equity=float(equity), peak_equity=float(state.peak_equity), drawdown=float(drawdown), open_lot_count=len(ledger.open_lots), bar_index=bar_index)
            strategy_instance.record_tick(context)
            for lot in ledger.get_marketable_lots(current_price):
                result = oms.execute_sell(lot.symbol, lot.shares, lot.target_sell_price)
                applied, _ = oms.process_event_once(f"fill:{result['id']}", lambda: None)
                if applied and result.get("status") == OrderStatus.FILLED.value:
                    qty, price = float(result.get("filled_qty", result.get("qty", 0.0))), result.get("filled_avg_price")
                    if qty > 0 and price is not None:
                        effective_price, cost = cost_model.apply_sell(float(price), qty, context=context, prev_close=previous_close)
                        state.cash += qty * effective_price - cost
                        ledger.close_lot(lot)
                        trade_blotter.append({"timestamp": context.timestamp, "side": "SELL", "price": float(effective_price), "qty": qty, "equity": float(context.equity)})
                        if not ledger.open_lots and self._on_flat_reentry == "reset_to_market":
                            state.last_buy_price = current_price
            if strategy_instance._check_grid_trigger(context, state.last_buy_price, step):
                post_sell_equity = state.cash + sum(lot.shares * current_price for lot in ledger.open_lots)
                if post_sell_equity > state.peak_equity:
                    state.peak_equity = post_sell_equity
                post_sell_dd = (state.peak_equity - post_sell_equity) / state.peak_equity if state.peak_equity else 0.0
                state.max_drawdown = max(state.max_drawdown, post_sell_dd)
                if post_sell_equity != context.equity or post_sell_dd != context.drawdown:
                    context = MarketContext(timestamp=context.timestamp, open=context.open, high=context.high, low=context.low, close=context.close, cash=float(state.cash), equity=float(post_sell_equity), peak_equity=float(state.peak_equity), drawdown=float(post_sell_dd), open_lot_count=len(ledger.open_lots), bar_index=bar_index)
                proposed = strategy_instance.calculate_trade_value(context)
                trade_value = risk_manager.clamp_trade_value(proposed, context.equity, state.cash, len(ledger.open_lots))
                if state.cash >= trade_value and trade_value > 0:
                    result = oms.execute_buy(symbol, trade_value, current_price)
                    if result.get("status") == OrderStatus.FILLED.value:
                        qty, price = float(result.get("filled_qty", result.get("qty", 0.0))), result.get("filled_avg_price")
                        if qty > 0 and price is not None:
                            effective_price, cost = cost_model.apply_buy(float(price), qty, context=context, prev_close=previous_close)
                            actual_notional = qty * effective_price + cost
                            if state.cash >= actual_notional:
                                state.cash -= actual_notional
                                ledger.register_buy(result["id"], symbol, effective_price, qty, target)
                                trade_blotter.append({"timestamp": context.timestamp, "side": "BUY", "price": float(effective_price), "qty": qty, "equity": float(context.equity)})
            equity_points.append((context.timestamp, float(context.equity)))
            previous_close = current_price
        final_price = float(self.data["close"].iloc[-1])
        final_value = state.cash + sum(lot.shares * final_price for lot in ledger.open_lots)
        metrics = PerformanceAnalyzer.calculate_metrics(ledger, final_value, initial_cash)
        metrics["Max Drawdown %"] = state.max_drawdown * 100.0
        blotter = pd.DataFrame(trade_blotter, columns=["timestamp", "side", "price", "qty", "equity"])
        if not blotter.empty:
            blotter["timestamp"] = pd.to_datetime(blotter["timestamp"])
        equity_curve = pd.Series({timestamp: equity for timestamp, equity in equity_points}, dtype=float)
        return SimulationResult(metrics=metrics, trade_blotter=blotter, equity_curve=equity_curve, params={"Grid Step": step, "Profit Target": target})

    def run_sweep(self, grid_steps: list, profit_targets: list, strategy_class: Type[SizingStrategy], strategy_params_grid: list[dict], cost_model: TransactionCostModel | None = None, risk_manager: RiskManager | None = None, on_flat_reentry: str = "stale_reference", symbol: str = "TQQQ", initial_cash: float = 100_000.0, n_jobs: int = 1, return_full_results: bool = False, search_strategy: str | SearchStrategy = "grid", rank_by: str = "Capital Velocity Index", rank_direction: str = "maximize", search_seed: int = 0, search_n_trials: int | None = None):
        validate_sweep_config(grid_steps=grid_steps, profit_targets=profit_targets, n_jobs=n_jobs, initial_cash=initial_cash, max_concurrent_lots=getattr(risk_manager, "max_concurrent_lots", None) if risk_manager is not None else None, max_total_exposure=getattr(risk_manager, "max_total_exposure", None) if risk_manager is not None else None)
        if on_flat_reentry not in {"stale_reference", "reset_to_market"}:
            raise ValueError("on_flat_reentry must be 'stale_reference' or 'reset_to_market'")
        if rank_direction not in {"maximize", "minimize"}:
            raise ValueError("rank_direction must be 'maximize' or 'minimize'")
        cost_model = ZeroCostModel() if cost_model is None else cost_model
        risk_manager = RiskManager() if risk_manager is None else risk_manager
        self._on_flat_reentry = on_flat_reentry
        combinations = [{"Grid Step": step, "Profit Target": target, **params} for step, target, params in itertools.product(grid_steps, profit_targets, strategy_params_grid)]
        if search_strategy == "grid":
            search: SearchStrategy = GridSearch(combinations)
        elif search_strategy == "bayesian":
            if n_jobs != 1:
                raise ValueError("Bayesian search requires n_jobs=1 because suggestions depend on prior reports")
            trial_count = search_n_trials if search_n_trials is not None else max(1, int(len(combinations) * 0.75))
            search = BayesianSearch(combinations, rank_by=rank_by, direction=rank_direction, seed=search_seed, n_trials=trial_count)
        elif isinstance(search_strategy, SearchStrategy):
            search = search_strategy
        else:
            raise ValueError("search_strategy must be 'grid', 'bayesian', or a SearchStrategy instance')
        results, full_results = [], []
        if isinstance(search, BayesianSearch):
            while True:
                try:
                    candidate = search.suggest()
                except StopIteration:
                    break
                step, target = candidate.pop("Grid Step"), candidate.pop("Profit Target")
                result_row, simulation = _run_single_combination(self, len(results), search.n_trials, step, target, strategy_class, candidate, symbol, initial_cash, cost_model, risk_manager, return_full_results)
                results.append(result_row)
                if simulation is not None:
                    full_results.append(simulation)
                search.report({"Grid Step": step, "Profit Target": target, **candidate}, simulation or SimulationResult(metrics={}))
        elif n_jobs == 1:
            while True:
                try:
                    candidate = search.suggest()
                except StopIteration:
                    break
                step, target = candidate.pop("Grid Step"), candidate.pop("Profit Target")
                result_row, simulation = _run_single_combination(self, len(results), len(combinations), step, target, strategy_class, candidate, symbol, initial_cash, cost_model, risk_manager, return_full_results)
                results.append(result_row)
                if simulation is not None:
                    full_results.append(simulation)
                search.report({"Grid Step": step, "Profit Target": target, **candidate}, simulation or SimulationResult(metrics={}))
        else:
            ordered = []
            while True:
                try:
                    ordered.append(search.suggest())
                except StopIteration:
                    break
            with ProcessPoolExecutor(max_workers=n_jobs) as executor:
                futures = {}
                for idx, candidate in enumerate(ordered):
                    step, target = candidate.pop("Grid Step"), candidate.pop("Profit Target")
                    futures[executor.submit(_run_single_combination, self, idx, len(ordered), step, target, strategy_class, candidate, symbol, initial_cash, cost_model, risk_manager, return_full_results)] = (idx, step, target, candidate)
                completed = {}
                for future in as_completed(futures):
                    idx, step, target, params = futures[future]
                    try:
                        result_row, simulation = future.result()
                    except Exception as exc:
                        result_row, simulation = {"Grid Step": step, "Profit Target": target, **params, "error": str(exc)}, None
                    results.append(result_row)
                    if simulation is not None:
                        completed[idx] = simulation
                full_results = [completed[idx] for idx in sorted(completed)]
                for idx in sorted(completed):
                    _, step, target, params = futures[next(f for f in futures if futures[f][0] == idx)]
                    search.report({"Grid Step": step, "Profit Target": target, **params}, completed[idx])
        summary = _rank_results(pd.DataFrame(results), rank_by=rank_by, direction=rank_direction)
        return (summary, full_results) if return_full_results else summary

    def validate_finalists_intraday(self, finalist_params, intraday_data, *, strategy_class, strategy_params_grid, intrabar_priority="sell_first") -> pd.DataFrame:
        from src.intraday_validation import IntradayValidator
        return IntradayValidator(intrabar_priority=intrabar_priority).validate_finalists_intraday(finalist_params, intraday_data, strategy_class=strategy_class, strategy_params_grid=strategy_params_grid)
