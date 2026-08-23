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

import concurrent.futures
import dataclasses
import logging

import pandas as pd

from src import data_validation, decision_cycle, intraday_validation
from src.cost_models import TransactionCostModel, ZeroCostModel
from src.earnings_calendar import EARNINGS_REACTION_DATES
from src.exceptions import ConfigurationError
from src.fomc_calendar import EASTERN_TZ as _EASTERN_TZ
from src.fomc_calendar import FOMC_DECISION_DATES
from src.idempotency import ProcessedEventStore
from src.intraday_profile import SESSION_MINUTES as _SESSION_MINUTES
from src.intraday_profile import SESSION_OPEN_MINUTE as _SESSION_OPEN_MINUTE
from src.ledger import AssetLotLedger
from src.market_context import MarketContext, SimulationResult
from src.no_loss_guard import NoLossViolation, compute_sell_economics, validate_sell
from src.order_management_system import OrderManagementSystem, OrderStatus
from src.performance_analyzer import PerformanceAnalyzer
from src.risk_manager import RiskManager
from src.search_strategies import BayesianSearch, GridSearch, SearchStrategy
from src.size_calculators import SizingStrategy
from src.validation import validate_run_sweep_config

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
    search_strategy,
    grid_steps,
    profit_targets,
    strategy_params_grid,
    rank_by,
    search_seed,
    search_direction="maximize",
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
            grid_steps,
            profit_targets,
            strategy_params_grid,
            rank_by=rank_by,
            direction=search_direction,
            seed=search_seed,
        )
    if isinstance(search_strategy, SearchStrategy):
        return search_strategy
    raise ConfigurationError(
        f"search_strategy must be None, 'grid', 'bayesian', or a SearchStrategy instance, got {search_strategy!r}"
    )


def _validate_fill_model(fill_model: str, intrabar_priority: str) -> None:
    """Range-check the fill-model pair. Module-level so run_sweep can
    front-load it (before any combination runs) and _simulate_single
    can enforce it for direct callers, without two copies of the
    rules."""
    if fill_model not in ("close", "intrabar"):
        raise ConfigurationError(f"fill_model must be 'close' or 'intrabar', got {fill_model!r}")
    if intrabar_priority not in ("sell_first", "buy_first"):
        raise ConfigurationError(
            f"intrabar_priority must be 'sell_first' or 'buy_first', got {intrabar_priority!r}"
        )
    if fill_model == "intrabar" and intrabar_priority == "buy_first":
        # Raised rather than silently ignored. _simulate_single evaluates
        # harvest-before-buy in fixed source order (the canonical
        # execution sequence), so honoring "buy_first" would mean
        # reordering the two phases -- a real change to a loop the whole
        # suite pins, not a flag read. Accepting the value and then not
        # applying it would be the worse failure: a config that says one
        # thing and does another.
        # OptimizationController.validate_finalists_intraday ->
        # intraday_validation.simulate_single_intraday does support
        # buy_first today, for the finalist replay pass.
        raise ConfigurationError(
            "fill_model='intrabar' currently supports intrabar_priority='sell_first' only "
            "(got 'buy_first'). Use validate_finalists_intraday for a buy_first replay."
        )


def _strategy_name(strategy_class) -> str:
    """Human-readable name for whatever run_sweep was handed.

    Deliberately not `strategy_class.__name__`. Despite the parameter
    name, run_sweep's contract is "a callable that constructs a
    strategy", and tests legitimately pass factory OBJECTS -- which
    have no __name__. Falling back to the callable's type keeps those
    call sites working and still yields something identifiable.
    """
    return getattr(strategy_class, "__name__", None) or type(strategy_class).__name__


def _run_one_combination(
    controller: "OptimizationController",
    step: float,
    target: float,
    strategy_class: type[SizingStrategy],
    params: dict,
    symbol: str,
    initial_cash: float,
    cost_model: TransactionCostModel,
    risk_manager: RiskManager,
    on_flat_reentry: str,
    fill_model: str = "close",
    intrabar_priority: str = "sell_first",
    enforce_no_loss: bool = True,
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
            fill_model=fill_model,
            enforce_no_loss=enforce_no_loss,
            intrabar_priority=intrabar_priority,
        )
        # Strategy is identified by name rather than by the config's
        # strategy_id, because run_sweep takes a callable and never
        # sees the id -- and a row naming something the reader can go
        # look at beats one naming a registry key. It matters at all
        # only now that more than one sizing strategy exists: results
        # from different strategies were previously indistinguishable
        # once combined.
        identity = {"Strategy": _strategy_name(strategy_class)}
        result_row = {
            "Grid Step": step,
            "Profit Target": target,
            **identity,
            **params,
            **result.metrics,
        }
        return result_row, result
    except Exception as e:
        logger.error(f"Combination failed: step={step} target={target} params={params}: {e}")
        return {
            "Grid Step": step,
            "Profit Target": target,
            "Strategy": _strategy_name(strategy_class),
            **params,
            "error": str(e),
        }, None


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
        # Computed lazily, once per controller, and reused by every
        # combination in a sweep -- see _fomc_flags. Doing the Eastern
        # conversion per bar per combination meant 1.03M timezone
        # conversions x however many combinations the sweep runs.
        self._fomc_flags_cache = None
        self._earnings_flags_cache = None
        self._eastern_dates_cache = None
        self._eastern_index_cache = None
        self._minutes_since_open_cache = None
        logger.info(
            f"OptimizationController initialized with historical dataset length: {len(historical_data)}"
        )

    @property
    def _fomc_flags(self):
        """Per-bar FOMC-decision-day flags for this controller's data.

        Vectorized and cached rather than calling
        fomc_calendar.is_fomc_day_at() per bar: the dataset is
        immutable for the controller's lifetime, so the Eastern-date
        conversion is done once for the whole index and every
        combination in a sweep reuses it. Profiled at ~0.55s per
        combination before caching -- trivial once, meaningful when
        multiplied by a sweep's combination count.

        Uses the same conversion the scalar helper documents (naive
        index treated as UTC, matched on the Eastern calendar date), so
        the two cannot disagree; tests/unit/test_fomc_calendar.py pins
        the scalar semantics and an integration test pins that this
        path agrees with it.
        """
        if self._fomc_flags_cache is None:
            self._fomc_flags_cache = [d in FOMC_DECISION_DATES for d in self._eastern_dates]
        return self._fomc_flags_cache

    @property
    def _eastern_index(self):
        """This controller's index converted to Eastern, once.

        Everything time-derived hangs off this: the two calendars need
        the DATE, the intraday profile needs the MINUTE. Converting
        separately for each would repeat the ~0.55s-per-combination cost
        _fomc_flags documents, three times over, for identical results.
        """
        if self._eastern_index_cache is None:
            index = self.data.index
            if getattr(index, "tz", None) is None:
                index = index.tz_localize("UTC")
            self._eastern_index_cache = index.tz_convert(_EASTERN_TZ)
        return self._eastern_index_cache

    @property
    def _eastern_dates(self):
        """Per-bar Eastern calendar dates for this controller's data.

        Factored out of _fomc_flags once a SECOND calendar
        (earnings_calendar) needed the same conversion. Now derived from
        the shared _eastern_index rather than converting again.
        """
        if self._eastern_dates_cache is None:
            self._eastern_dates_cache = self._eastern_index.date
        return self._eastern_dates_cache

    @property
    def _minutes_since_open(self):
        """Per-bar minutes since 09:30 Eastern, -1 outside the session.

        Vectorized rather than calling intraday_profile.minutes_since_open
        per bar, for the same reason the calendar flags are: this is
        1.03M lookups per combination otherwise. Uses the same Eastern
        conversion and the same 0-389 window as the scalar helper, so
        backtest and live cannot disagree about which minute a bar is.
        """
        if self._minutes_since_open_cache is None:
            eastern = self._eastern_index
            offset = eastern.hour * 60 + eastern.minute - _SESSION_OPEN_MINUTE
            self._minutes_since_open_cache = [
                int(m) if 0 <= m < _SESSION_MINUTES else -1 for m in offset
            ]
        return self._minutes_since_open_cache

    @property
    def _earnings_flags(self):
        """Per-bar mega-cap-earnings-reaction-day flags, cached exactly
        as _fomc_flags is and matching src/earnings_calendar.py's scalar
        semantics.

        Note these flags mark the session that TRADES the reaction, not
        the announcement date -- see that module's docstring for the
        measurement behind that distinction.
        """
        if self._earnings_flags_cache is None:
            self._earnings_flags_cache = [
                d in EARNINGS_REACTION_DATES for d in self._eastern_dates
            ]
        return self._earnings_flags_cache

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
        fill_model: str = "close",
        intrabar_priority: str = "sell_first",
        enforce_no_loss: bool = True,
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

        --------------------------------------------------------------
        fill_model: "close" (default) or "intrabar".

        "close" is the original, unchanged behavior: a sell needs the
        bar's CLOSE at or above the lot's target, a buy needs the CLOSE
        at or below the trigger level, and a buy fills at the close.
        Every pre-existing caller and config gets exactly this, which is
        what tests/fixtures/regression_baseline.py pins.

        "intrabar" models the resting LIMIT orders a grid strategy
        actually works by: a level that the bar TOUCHED (high >= sell
        target, or low <= buy trigger) fills, and it fills AT that
        level, not at the close. Measured on this repo's 10-year TQQQ
        minute data, the close-only model sees roughly HALF the fills
        the touch model does -- 1.83x-1.91x fewer, consistently across
        every threshold from 3bps to 50bps -- because median intrabar
        range (14.5bps) is more than double median close-to-close
        movement (6.8bps). For a strategy harvesting bps-scale moves
        that difference is not a refinement, it is most of the
        behavior.

        This mirrors the fill convention src/intraday_validation.py
        established for its opt-in replay pass (fill at the touched
        level, not at high/low/close), so the two agree. Unlike that
        module, this path routes through decision_cycle and the real
        RiskManager, and asks the strategy for its own trigger LEVEL
        (SizingStrategy._grid_trigger_level) rather than assuming the
        default last_buy_price*(1-step) formula -- which that module
        hardcodes and which is wrong for any strategy that overrides
        the trigger.

        intrabar_priority ("sell_first" default / "buy_first") decides
        the order on bars where BOTH a sell target and a buy trigger
        were touched and OHLC alone cannot establish which came first
        -- 14.5% of bars on this dataset at representative thresholds,
        so not a rare tie-break. Ignored entirely when
        fill_model="close" (a close is a single price; no ambiguity
        exists). Same contract and default as intraday_validation's.
        """
        _validate_fill_model(fill_model, intrabar_priority)
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

        start_price = self.data["close"].iloc[0]
        state = BacktestState(initial_cash=initial_cash, start_price=start_price)

        # Task 7.5: the previous bar's close, fed to the cost model so
        # volatility-aware slippage can scale by this bar's move. None
        # on the first bar (no previous close exists) --
        # DynamicSlippageModel falls back to base_bps in that case.
        prev_close = None
        fomc_flags = self._fomc_flags
        earnings_flags = self._earnings_flags
        minute_flags = self._minutes_since_open

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
                is_macro_event_day=fomc_flags[bar_index],
                is_earnings_reaction_day=earnings_flags[bar_index],
                time_of_day_flag=minute_flags[bar_index],
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

            # 1. Harvest target checks. Under "intrabar", a resting
            # limit sell fills if the bar's HIGH touched the target,
            # not only if the close finished above it; the fill price
            # is the target either way (oms.execute_sell below), so
            # only the trigger price differs between the two models.
            harvest_probe = context.price if fill_model == "close" else row.high
            marketable = ledger.get_marketable_lots(harvest_probe)
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
                        lot,
                        filled_qty,
                        filled_price,
                        cost_model,
                        context=context,
                        prev_close=prev_close,
                    )
                except NoLossViolation:
                    if enforce_no_loss:
                        continue  # already logged by the guard
                    # Guard disabled via execution.enforce_no_loss=false.
                    # The sell proceeds, so the economics have to be
                    # recomputed without the raise. compute_sell_economics
                    # is the very formula validate_sell wraps -- it is
                    # exposed separately for exactly this case -- so the
                    # permitted path cannot drift from the guarded one.
                    economics = compute_sell_economics(
                        lot,
                        filled_qty,
                        filled_price,
                        cost_model,
                        context=context,
                        prev_close=prev_close,
                    )
                net_sell_proceeds = economics.net_sell_proceeds

                def _apply_sell_fill(
                    lot=lot,
                    context=context,
                    net_sell_proceeds=net_sell_proceeds,
                    filled_price=filled_price,
                    filled_qty=filled_qty,
                ):
                    """Side effects of one confirmed sell, applied at most once.

                    Wrapped as a closure so ProcessedEventStore.apply_once
                    (Task 4.10) can guard it by order id -- a duplicated
                    fill event must not credit cash or close a lot twice.

                    Per-iteration values are bound as DEFAULT ARGUMENTS
                    rather than captured by reference. apply_once happens
                    to invoke this immediately, so late binding is not a
                    bug today -- but if it ever deferred or batched, a
                    free-variable capture would silently apply the wrong
                    lot's economics. Binding removes that failure mode
                    outright instead of relying on the caller's timing.
                    """
                    state.cash += net_sell_proceeds
                    ledger.close_lot(lot)
                    blotter_records.append(
                        {
                            "timestamp": context.timestamp,
                            "side": "sell",
                            "price": filled_price,
                            "qty": filled_qty,
                            "equity": context.equity,
                        }
                    )
                    if len(ledger.open_lots) == 0 and on_flat_reentry == "reset_to_market":
                        state.last_buy_price = context.price

                event_store.apply_once(exec_res["id"], _apply_sell_fill, event_kind="sell_fill")

            # 2. Step purchase checks -- delegated to the shared canonical
            # decision cycle (Task 7.1), which live_execution.py also
            # calls, so the trigger/sizing/clamp sequence exists in
            # exactly one place. state.cash (not context.cash) is passed
            # deliberately: it reflects this same bar's harvest proceeds,
            # which have already landed by the time a buy is sized.
            #
            # Under "intrabar" the trigger is a TOUCH of the level by
            # the bar's low, and both sizing and the fill happen at
            # that level rather than at the close -- so the level is
            # asked of the strategy itself (_grid_trigger_level) and
            # passed through a context whose price is overridden to it.
            # dataclasses.replace because MarketContext is frozen.
            if fill_model == "close":
                buy_fill_price = context.price
                decision = decision_cycle.evaluate_grid_decision(
                    strategy_instance, risk_manager, context, state.last_buy_price, step, state.cash
                )
            else:
                trigger_level = strategy_instance._grid_trigger_level(
                    context, state.last_buy_price, step
                )
                buy_fill_price = trigger_level
                fill_context = dataclasses.replace(
                    context, close=trigger_level, low=min(row.low, trigger_level)
                )
                decision = decision_cycle.evaluate_grid_decision(
                    strategy_instance,
                    risk_manager,
                    context,
                    state.last_buy_price,
                    step,
                    state.cash,
                    triggered=row.low <= trigger_level,
                    sizing_context=fill_context,
                )
            if decision.triggered:
                trade_value = decision.clamped_trade_value

                if state.cash >= trade_value and trade_value > 0:
                    order = oms.execute_buy(symbol, trade_value, buy_fill_price)
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

                        def _apply_buy_fill(
                            order=order,
                            context=context,
                            per_share_cost_basis=per_share_cost_basis,
                            total_buy_outlay=total_buy_outlay,
                            filled_price=filled_price,
                            filled_qty=filled_qty,
                            buy_fill_price=buy_fill_price,
                        ):
                            """Side effects of one confirmed buy, applied at most once.

                            Closure for the same reason as _apply_sell_fill:
                            idempotency is enforced by order id, so a
                            replayed fill cannot open a second lot or debit
                            cash twice. Per-iteration values are likewise
                            bound as default arguments so the closure is
                            correct regardless of when it is invoked.
                            """
                            ledger.register_buy(
                                order["id"], symbol, per_share_cost_basis, filled_qty, target
                            )
                            state.cash -= total_buy_outlay
                            # The grid reference advances to where this buy
                            # ACTUALLY filled -- the close under "close",
                            # the touched limit level under "intrabar".
                            # Using the close in the intrabar case would
                            # ratchet the ladder from a price no order
                            # transacted at, letting the next rung trigger
                            # from the wrong reference.
                            state.last_buy_price = buy_fill_price
                            blotter_records.append(
                                {
                                    "timestamp": context.timestamp,
                                    "side": "buy",
                                    "price": filled_price,
                                    "qty": filled_qty,
                                    "equity": context.equity,
                                }
                            )

                        event_store.apply_once(order["id"], _apply_buy_fill, event_kind="buy_fill")

            # End of bar: this bar's close becomes the next bar's
            # prev_close. At the loop's own indentation so it advances
            # every bar, not only on triggering ones (Task 7.5).
            prev_close = current_price

        final_price = self.data["close"].iloc[-1]
        open_assets_val = sum(lot.shares * final_price for lot in ledger.open_lots)
        final_portfolio_value = state.cash + open_assets_val

        metrics = PerformanceAnalyzer.calculate_metrics(ledger, final_portfolio_value, initial_cash)
        metrics["Max Drawdown %"] = state.max_drawdown * 100.0
        # Assigned here rather than in PerformanceAnalyzer for the same
        # reason "Max Drawdown %" is: it is derived from the drawdown
        # this loop tracks per bar, and computing it in two places would
        # risk two figures under one key.
        #
        # Exists so a search can rank on something that PRICES the
        # drawdown it takes on. Ranking by "Total Return %" alone is
        # measured to walk straight into the corner of the space where
        # drawdown saturates near 80% on this dataset, because return
        # alone has no term pulling the other way.
        #
        # A zero-drawdown run is not penalized by a NaN (which
        # na_position="last" would sink to the bottom of a ranking,
        # exactly backwards): a positive return with no drawdown is the
        # best possible outcome and sorts as +inf, while a run that
        # neither gained nor drew down is a flat 0.0.
        drawdown_pct = metrics["Max Drawdown %"]
        total_return_pct = metrics["Total Return %"]
        if drawdown_pct > 0.0:
            metrics["Return/Drawdown"] = total_return_pct / drawdown_pct
        elif total_return_pct > 0.0:
            metrics["Return/Drawdown"] = float("inf")
        else:
            metrics["Return/Drawdown"] = 0.0

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
            "fill_model": fill_model,
            "enforce_no_loss": enforce_no_loss,
            # Underscore-prefixed attributes are excluded deliberately.
            # The intent above is "the strategy's own constructor-derived
            # attributes"; a stateful strategy's rolling indicator state
            # is not that. Without the filter, a strategy holding a
            # bounded price deque or posterior object would attach it to
            # every SimulationResult, which is both misleading as a
            # "what configured this run" record and a real memory cost
            # across a sweep held in return_full_results.
            **{k: v for k, v in vars(strategy_instance).items() if not k.startswith("_")},
        }

        return SimulationResult(
            metrics=metrics,
            trade_blotter=pd.DataFrame(blotter_records),
            equity_curve=pd.Series(
                data=equity_curve_values, index=pd.Index(equity_curve_timestamps, name="timestamp")
            ),
            params=params,
        )

    def run_sweep(
        self,
        grid_steps: list,
        profit_targets: list,
        strategy_class: type[SizingStrategy],
        strategy_params_grid: list[dict],
        cost_model: TransactionCostModel = None,
        risk_manager: RiskManager = None,
        on_flat_reentry: str = "stale_reference",
        fill_model: str = "close",
        intrabar_priority: str = "sell_first",
        enforce_no_loss: bool = True,
        symbol: str = "TQQQ",
        initial_cash: float = 100_000.0,
        n_jobs: int = 1,
        return_full_results: bool = False,
        rank_by: str = "Capital Velocity Index",
        tie_break_by: str | None = None,
        search_strategy=None,
        search_seed: int | None = None,
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
        :param fill_model: "close" (default, exactly today's behavior) fills a sell only
            when the bar's CLOSE reaches the lot's target and a buy only when the CLOSE
            reaches the trigger, filling the buy at that close. "intrabar" models resting
            LIMIT orders instead: a level TOUCHED during the bar (high >= sell target,
            low <= buy trigger) fills, at that level. On this repo's 10-year TQQQ minute
            data the close-only model sees ~1.85x fewer fills on both sides -- see
            _simulate_single's docstring for the measurements and the rationale.
        :param intrabar_priority: Only meaningful with fill_model="intrabar"; "sell_first"
            (default) is the only value currently supported there (see _simulate_single).
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
        # Front-loaded for the same reason as everything above it: these
        # are CONFIG errors, and _simulate_single runs inside
        # _run_one_combination's per-combination try/except (Task 4.4),
        # which would turn one bad value into an {"error": ...} row for
        # every combination in the sweep instead of one clear failure
        # before any work starts. _simulate_single validates them too,
        # for callers that reach it directly.
        _validate_fill_model(fill_model, intrabar_priority)
        cost_model = cost_model if cost_model is not None else ZeroCostModel()
        risk_manager = risk_manager if risk_manager is not None else RiskManager()
        results = []
        full_results = []

        resolved_search_strategy = _resolve_search_strategy(
            search_strategy,
            grid_steps,
            profit_targets,
            strategy_params_grid,
            rank_by,
            search_seed,
            search_direction,
        )
        total_combinations = len(grid_steps) * len(profit_targets) * len(strategy_params_grid)
        logger.info(
            f"Starting parameter sweep. Evaluating up to {total_combinations} total variations."
        )

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
                    self,
                    suggestion["grid_step"],
                    suggestion["profit_target"],
                    strategy_class,
                    suggestion["strategy_params"],
                    symbol,
                    initial_cash,
                    cost_model,
                    risk_manager,
                    on_flat_reentry,
                    fill_model,
                    intrabar_priority,
                    enforce_no_loss,
                )
                resolved_search_strategy.report(suggestion, sim_result)
                results.append(row)
                # Retained ONLY when the caller asked for them. Each
                # SimulationResult carries a per-bar equity curve (one
                # entry per bar -- ~1.03M on this repo's 10-year minute
                # dataset) and a full trade blotter (~540k rows for a
                # high-frequency combination), i.e. tens of MB EACH.
                # Appending unconditionally meant a sweep's peak memory
                # grew with combination count even when the caller only
                # ever reads summary_df -- which is what exhausted RAM
                # on a 1,260-combination run here. The search strategy's
                # report() above consumes sim_result transiently and
                # does not retain it, so dropping it here is safe.
                if return_full_results:
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
                            _run_one_combination,
                            self,
                            s["grid_step"],
                            s["profit_target"],
                            strategy_class,
                            s["strategy_params"],
                            symbol,
                            initial_cash,
                            cost_model,
                            risk_manager,
                            on_flat_reentry,
                            fill_model,
                            intrabar_priority,
                            enforce_no_loss,
                        ): s
                        for s in batch
                    }
                    for future in concurrent.futures.as_completed(future_to_suggestion):
                        suggestion = future_to_suggestion[future]
                        row, sim_result = future.result()
                        resolved_search_strategy.report(suggestion, sim_result)
                        results.append(row)
                        if return_full_results:  # see the sequential branch
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
        # Only populated when return_full_results is set (see above), so
        # the reorder is guarded to match -- an empty list must stay
        # empty rather than being indexed by the sorted row positions.
        if return_full_results:
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

            rows.append(
                {
                    "Grid Step": grid_step,
                    "Profit Target": profit_target,
                    **strategy_params,
                    "Daily Closed Trades": daily_result["Closed Trade Count"],
                    "Intraday Closed Trades": intraday_metrics["Closed Trade Count"],
                    "Daily Final Equity": daily_result["Final Equity"],
                    "Intraday Final Equity": intraday_metrics["Final Equity"],
                    "Diverges": daily_result["Closed Trade Count"]
                    != intraday_metrics["Closed Trade Count"],
                }
            )

        return pd.DataFrame(rows)
