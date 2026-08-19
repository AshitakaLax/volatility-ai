"""
Intraday-replay validation pass. Task 2.3 (F2).

Re-runs a short list of finalist parameter combinations against
minute-bar OHLC data, using high/low to detect any intrabar touch of
a sell target (or grid-buy trigger) that a daily close-only pass would
miss. Strictly additive/opt-in -- run_sweep()'s default daily-close
behavior is unchanged by this module existing.

Implemented as its own simulation loop, deliberately duplicating (not
sharing) optimization_controller.py's per-bar logic, per Task 2.3's
own explicit allowance: "can be implemented against the current
inline loop (with some duplicated logic) or deferred until after 4.1
for a cleaner implementation that reuses _simulate_single directly."
Updated for Task 4.1's MarketContext-based SizingStrategy interface,
but still its own loop, not a call into _simulate_single -- Task 2.3
sanctioned duplication, not a promise to unify later, and unifying
these two genuinely different fill models (limit-at-touched-level vs.
fill-at-close) is a bigger change than this pass warrants right now.

Intrabar ambiguity contract: when a bar's high/low show that both a
sell target and a buy trigger were touched and the true order can't
be established from OHLC alone, this module does not assume the
favorable order. intrabar_priority controls which check runs first,
applied uniformly every bar (not conditionally only on ambiguous bars
-- for a bar where only one condition is true, order doesn't matter,
so uniform ordering produces the documented rule's intended result on
both ambiguous and unambiguous bars alike). Default "sell_first" is
consistent with the Canonical execution sequence's existing sell-
before-buy ordering (optimization_controller.py already evaluates
harvest checks before grid-trigger checks every bar).

Fill convention: a touched level fills AT that level (the limit
price), not at the bar's high/low/close -- a sell target fills at
lot.target_sell_price when high touches or exceeds it; a buy trigger
fills at last_buy_price * (1 - grid_step) when low touches or
crosses it. This differs from the daily pass, which fills buys at
that bar's close (there's no theoretical trigger level to fill at on
a daily bar) -- an intentional difference from daily behavior, not an
oversight, since intraday data makes the actual touched limit price
knowable. Because of this, calculate_trade_value is given a
*fill_context* with close/price overridden to the touched trigger
level (via dataclasses.replace on the bar's real MarketContext, since
it's frozen) rather than the bar's real context -- matching the
pre-Task-4.1 behavior, which sized against trigger_level, not the
bar's close.
"""

from __future__ import annotations

import dataclasses
import logging
from typing import Literal

import pandas as pd

from src.cost_models import TransactionCostModel, ZeroCostModel
from src.ledger import AssetLotLedger
from src.market_context import MarketContext
from src.no_loss_guard import NoLossViolation, validate_sell
from src.order_management_system import OrderManagementSystem, OrderStatus
from src.performance_analyzer import PerformanceAnalyzer

logger = logging.getLogger("Optimizer")

REQUIRED_INTRADAY_COLUMNS = {"open", "high", "low", "close"}


class IntradayValidationError(ValueError):
    """Raised when intraday data is unusable for a replay pass."""

    pass


def validate_intraday_schema(df: pd.DataFrame) -> None:
    """Require the OHLC columns an intrabar replay depends on.

    Stricter than the daily validator, which needs only `close`: high
    and low are what make intrabar touch detection possible at all.
    """
    if df.empty:
        raise IntradayValidationError("intraday_data is empty.")
    missing = REQUIRED_INTRADAY_COLUMNS - set(df.columns)
    if missing:
        raise IntradayValidationError(f"intraday_data missing required columns: {missing}")


def simulate_single_intraday(
    intraday_data: pd.DataFrame,
    grid_step: float,
    profit_target: float,
    strategy_class,
    strategy_params: dict,
    cost_model: TransactionCostModel = None,
    intrabar_priority: Literal["sell_first", "buy_first"] = "sell_first",
    initial_cash: float = 100_000.0,
) -> dict:
    """One finalist combination, re-simulated bar-by-bar against
    minute data. Fill-status validation (Task 1.5), the no-loss
    invariant, and cost-model application (Task 2.2) all apply
    identically to the daily path."""
    if intrabar_priority not in ("sell_first", "buy_first"):
        raise ValueError(
            f"intrabar_priority must be 'sell_first' or 'buy_first', got {intrabar_priority!r}"
        )
    cost_model = cost_model if cost_model is not None else ZeroCostModel()

    ledger = AssetLotLedger()
    sizing_engine = strategy_class(**strategy_params)
    oms = OrderManagementSystem(mode="SIMULATION")

    start_price = intraday_data["close"].iloc[0]
    cash = initial_cash
    last_buy_price = start_price
    peak_equity = initial_cash
    max_drawdown = 0.0

    def _harvest_check(context: MarketContext) -> None:
        """Sell any lot whose target the bar's HIGH reached.

        Uses high rather than close, which is the whole point of the
        intraday pass: a target touched and then reversed within the bar
        is a real fill that a close-only backtest never sees.
        """
        nonlocal cash
        marketable = [lot for lot in ledger.open_lots if context.high >= lot.target_sell_price]
        for lot in marketable:
            exec_res = oms.execute_sell(lot.symbol, lot.shares, lot.target_sell_price)
            if exec_res.get("status") != OrderStatus.FILLED:
                logger.warning(
                    f"[intraday] Sell not filled for lot {lot.order_id}: status={exec_res.get('status')}"
                )
                continue
            filled_qty = exec_res["filled_qty"]
            filled_price = exec_res["filled_avg_price"]
            # Task 7.15: same canonical guard the daily path calls --
            # this block previously carried its own duplicate copy of
            # the comparison.
            try:
                economics = validate_sell(
                    lot, filled_qty, filled_price, cost_model, context=context
                )
            except NoLossViolation:
                continue  # already logged by the guard
            cash += economics.net_sell_proceeds
            ledger.close_lot(lot)

    def _trigger_check(context: MarketContext) -> None:
        """Buy if the bar's LOW reached the grid trigger level.

        Fills at the trigger level itself, not the bar's close, since
        intraday data makes the actual touched limit price knowable.
        Sizes against that same level for the same reason.
        """
        nonlocal cash, last_buy_price
        trigger_level = last_buy_price * (1.0 - grid_step)
        if context.low > trigger_level:
            return
        # Fill happens at the touched limit price, not the bar's close --
        # size against that level (matches pre-Task-4.1 behavior). frozen
        # dataclass, so a modified copy rather than mutation.
        fill_context = dataclasses.replace(context, close=trigger_level)
        trade_value = sizing_engine.calculate_trade_value(fill_context)
        if not (cash >= trade_value and trade_value > 0):
            return
        order = oms.execute_buy("TQQQ", trade_value, trigger_level)
        if order.get("status") != OrderStatus.FILLED:
            logger.warning(f"[intraday] Buy not filled: status={order.get('status')}")
            return
        filled_qty = order["filled_qty"]
        filled_price = order["filled_avg_price"]
        effective_price, buy_cost = cost_model.apply_buy(filled_price, filled_qty)
        total_buy_outlay = (effective_price * filled_qty) + buy_cost
        per_share_cost_basis = total_buy_outlay / filled_qty
        ledger.register_buy(order["id"], "TQQQ", per_share_cost_basis, filled_qty, profit_target)
        cash -= total_buy_outlay
        last_buy_price = trigger_level

    for bar_index, (timestamp, row) in enumerate(intraday_data.iterrows()):
        bar_close = row["close"]

        open_assets_val = sum(lot.shares * bar_close for lot in ledger.open_lots)
        total_equity = cash + open_assets_val
        if total_equity > peak_equity:
            peak_equity = total_equity
        current_dd = (peak_equity - total_equity) / peak_equity
        if current_dd > max_drawdown:
            max_drawdown = current_dd

        context = MarketContext(
            timestamp=timestamp,
            open=row["open"],
            high=row["high"],
            low=row["low"],
            close=bar_close,
            cash=cash,
            equity=total_equity,
            peak_equity=peak_equity,
            drawdown=current_dd,
            open_lot_count=len(ledger.open_lots),
            bar_index=bar_index,
        )

        sizing_engine.record_tick(context)

        if intrabar_priority == "sell_first":
            _harvest_check(context)
            _trigger_check(context)
        else:
            _trigger_check(context)
            _harvest_check(context)

    final_price = intraday_data["close"].iloc[-1]
    open_assets_val = sum(lot.shares * final_price for lot in ledger.open_lots)
    final_portfolio_value = cash + open_assets_val

    metrics = PerformanceAnalyzer.calculate_metrics(ledger, final_portfolio_value, initial_cash)
    metrics["Max Drawdown %"] = max_drawdown * 100.0
    return metrics
