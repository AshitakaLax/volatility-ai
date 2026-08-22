"""
The canonical strategy decision cycle. Task 7.1 (L1, L3).

Shared decision-cycle contract (implementation_task_specs.md Task
7.1): "The live loop must invoke the same canonical decision-cycle
implementation/path used by backtest after MarketContext
construction. Do not maintain separate copies of sell/buy decision
ordering." Its acceptance criterion is explicit that this must be
provable "via a shared helper function both call, not two
independently-written copies."

Before this module existed, optimization_controller._simulate_single
and live_execution.LiveExecutionLoop.decision_cycle each had their
own hand-written copy of the sequence. They had already diverged on
one argument -- verified directly, not hypothesised: the backtest
passed state.cash (live-updated by that same bar's harvest sells)
to clamp_trade_value, while the live loop passed context.cash (the
pre-harvest snapshot taken when MarketContext was constructed). Both
now call the functions here instead.

Why TWO functions rather than one covering the whole sequence:
record_tick fires at the very top of a bar/tick, but the grid
trigger is evaluated only AFTER that bar's harvest sells (the
canonical execution sequence's sell-before-buy ordering -- see
_simulate_single). A single function doing all four calls back to
back would have to move record_tick after the harvest, silently
changing when stateful strategies observe the market. Splitting at
the real seam keeps both call sites honest about the phase boundary
instead of hiding it.

`cash` is an explicit parameter rather than being read off
context.cash because the two call sites legitimately hold different
current-cash values at this point in the cycle -- see above. The
contract this module enforces is that the sequence, the methods, and
the argument SHAPES are identical; the values each caller supplies
are its own to determine correctly.
"""

from __future__ import annotations

from dataclasses import dataclass

from src.market_context import MarketContext


@dataclass(frozen=True)
class GridDecision:
    """Outcome of one grid-trigger evaluation. triggered=False means no
    buy is proposed and both trade values are 0.0."""

    context: MarketContext
    triggered: bool
    proposed_trade_value: float = 0.0
    clamped_trade_value: float = 0.0


def record_tick(strategy, context: MarketContext) -> None:
    """Phase 1: fires once per bar/tick, unconditionally, before any
    harvest or trigger evaluation (bug B4's fix, Task 1.3)."""
    strategy.record_tick(context)


def evaluate_grid_decision(
    strategy,
    risk_manager,
    context: MarketContext,
    last_buy_price: float,
    step: float,
    cash: float,
    triggered: bool | None = None,
    sizing_context: MarketContext | None = None,
) -> GridDecision:
    """Phases 2-4: grid-trigger check, then (only if triggered) sizing
    and the risk clamp. Pure with respect to portfolio state -- it
    proposes a value; it does not submit orders, move cash, or touch
    the ledger. Callers own those effects.

    triggered/sizing_context exist for the intrabar fill model and
    default to None, which preserves the original behavior exactly
    (evaluate the trigger against context.price, size against the same
    context). The intrabar caller has already determined the trigger
    from the bar's LOW rather than its close, and must size against the
    touched limit level rather than the close -- so it passes both in
    rather than having this function re-derive them from a close it
    isn't using. Keeping the clamp and the call sequence here, rather
    than letting that caller inline its own copy, is the whole point of
    this module (see docstring)."""
    if triggered is None:
        triggered = strategy._check_grid_trigger(context, last_buy_price, step)
    if not triggered:
        return GridDecision(context=context, triggered=False)

    proposed = strategy.calculate_trade_value(
        context if sizing_context is None else sizing_context
    )
    clamped = risk_manager.clamp_trade_value(proposed, context.equity, cash, context.open_lot_count)
    return GridDecision(
        context=context,
        triggered=True,
        proposed_trade_value=float(proposed),
        clamped_trade_value=float(clamped),
    )
