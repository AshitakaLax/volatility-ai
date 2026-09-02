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


def adjust_open_lot_targets(
    strategy,
    ledger,
    context: MarketContext,
    skip_order_ids=frozenset(),
) -> list:
    """Phase 1b: let the strategy move open lots' exit targets, before
    this bar's marketable check. Returns the lots actually changed.

    Placed BETWEEN record_tick and the harvest deliberately. After
    record_tick, so a trailing policy reading the strategy's own rolling
    state sees this bar included; before the marketable check, so a
    target lowered on this bar can be harvested on this bar rather than
    waiting for the next one -- which on a 60s live poll would be a
    real, and silent, delay.

    Lives here for the same reason record_tick does: the backtest, the
    intrabar replay, and the live loop must apply this at the identical
    point in the sequence. Three copies of "loop the open lots and
    retarget" would be three chances to disagree about ordering, which
    is exactly the divergence this module exists to prevent.

    skip_order_ids lets the live loop exclude lots with a sell already
    in flight -- their resting order was submitted at the current
    target, so moving it would leave the ledger and the broker
    disagreeing about one lot's price. Backtests pass nothing.

    Returns the changed lots (not a count) because the live caller has
    to re-persist exactly those rows, and rediscovering which ones
    changed would mean either re-running the policy or writing every
    open lot every tick.
    """
    # getattr rather than a direct call: SizingStrategy supplies a
    # default, but strategy_class is only duck-typed at the
    # _simulate_single boundary -- test doubles and any externally
    # supplied strategy need not subclass it. Treating the hook as
    # optional keeps those working, the same way diagnostics() is
    # deliberately outside the contract.
    hook = getattr(strategy, "adjust_profit_target", None)
    if hook is None:
        return []

    # EARLY-OUT WHEN RETARGETING IS INERT. Profiled on a 120,000-bar
    # slice, this function was 63% of total runtime: 62.6 MILLION calls
    # to adjust_profit_target, ~522 open lots re-examined on every bar,
    # plus a list copy and 62.6M set.add calls to build open_ids.
    #
    # In the default configuration all of it does nothing. trail_pct
    # defaults to None, so adjust_profit_target returns None immediately
    # and retain_lots is a no-op -- the champion config and most sweeps
    # pay the full cost for zero effect.
    #
    # Duck-typed and defaulting to True, so a strategy that does not
    # implement it (a test double, an externally supplied strategy)
    # keeps today's behavior exactly. A strategy answering False is
    # promising that BOTH adjust_profit_target and retain_lots are
    # inert, since this skips both.
    wants = getattr(strategy, "wants_lot_retargeting", None)
    if wants is not None and not wants():
        return []

    changed = []
    open_ids = set()
    # list() because retarget mutates lots while we iterate, and a
    # caller is free to close lots in the harvest that follows.
    for lot in list(ledger.open_lots):
        open_ids.add(lot.order_id)
        if lot.order_id in skip_order_ids:
            continue
        proposed = hook(lot, context)
        if proposed is None:
            continue
        if proposed == lot.profit_target:
            continue
        lot.retarget(proposed)
        changed.append(lot)

    # Let a strategy holding per-lot state release what has closed. A
    # trailing policy keeps one peak per lot it has ever seen, and a
    # live daemon closes lots indefinitely -- without this the map is a
    # slow leak for exactly the deployment that runs longest. Collected
    # from the loop above rather than a second pass, so this costs a set
    # insert per open lot and changes no asymptotics.
    retain = getattr(strategy, "retain_lots", None)
    if retain is not None:
        retain(open_ids)

    # Tell the ledger a target moved DOWN. get_marketable_lots keeps a
    # lower bound on every open target so it can skip scanning the book
    # on a price that cannot possibly trigger a sale; a bound that never
    # heard about a ratcheted-down target would sit ABOVE a target that
    # is now reachable and silently skip a real sale. Trailing only
    # ratchets down, but the ledger takes a min, so reporting a raised
    # target is harmless.
    #
    # Duck-typed like the hooks above: a ledger double in a test need not
    # implement it.
    if changed:
        note = getattr(ledger, "note_target_lowered", None)
        if note is not None:
            note(min(lot.target_sell_price for lot in changed))

    return changed


def collect_liquidations(
    strategy,
    ledger,
    context: MarketContext,
    *,
    allow_signal_exit: bool,
    skip_order_ids=frozenset(),
) -> list:
    """Phase 1c: the open lots a strategy wants closed on signal, not price.

    Returns lots the caller must sell at this bar's price REGARDLESS of
    whether they are profitable. Every other exit in this system happens
    because price reached a target; this is the only one that does not,
    and closing an underwater lot is a normal outcome of it rather than
    an error -- see src/no_loss_guard.SellReason.SIGNAL_EXIT.

    TWO INDEPENDENT CONDITIONS, both checked here. `allow_signal_exit`
    comes from config; the hook comes from the strategy. Either one
    missing returns empty, so neither a config flag flipped without a
    strategy that uses it, nor a strategy dropped into a default config,
    can realize a single loss. Both are cheap and both are checked every
    bar rather than cached, because a cached authorization is one
    refactor away from being the only authorization.

    Ordering: after adjust_open_lot_targets, before the marketable
    check. After, so a strategy that both retargets and liquidates sees
    a consistent book. Before, so a lot that is BOTH marketable and
    condemned exits once -- the caller drops it from the harvest -- and
    the exit that actually fires is the profitable one, since the caller
    processes liquidations first and get_marketable_lots then no longer
    sees the lot. A lot cannot be sold twice in a bar.

    Lives here rather than in the three sell sites for the reason the
    whole module exists: backtest, intrabar replay, and live must make
    the identical decision, and "loop the open lots and ask" copied
    three times is three chances to disagree.

    skip_order_ids mirrors adjust_open_lot_targets: the live loop
    excludes lots with a sell already in flight, since condemning a lot
    whose order is resting would submit a second one.
    """
    if not allow_signal_exit:
        return []

    # Duck-typed and optional for the same reason adjust_profit_target
    # is: strategy_class is only duck-typed at the _simulate_single
    # boundary, so test doubles and externally supplied strategies need
    # not subclass SizingStrategy.
    hook = getattr(strategy, "lots_to_liquidate", None)
    if hook is None:
        return []

    open_lots = list(ledger.open_lots)
    if not open_lots:
        return []

    requested = hook(open_lots, context)
    if not requested:
        return []

    # Filter against the book we just read rather than trusting the
    # returned list. A strategy holding a stale reference to an
    # already-closed lot would otherwise sell shares that are gone --
    # silently, since the ledger would happily record a second close.
    # Identity, not order_id: two lots can share neither, but a lot
    # object not in this bar's open book is not sellable this bar.
    live = {id(lot) for lot in open_lots if lot.order_id not in skip_order_ids}
    condemned = [lot for lot in requested if id(lot) in live]

    # Deduplicate while preserving the strategy's order -- a hook that
    # returns the same lot twice must not produce two sells.
    seen = set()
    unique = []
    for lot in condemned:
        if id(lot) not in seen:
            seen.add(id(lot))
            unique.append(lot)
    return unique


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
    clamped = risk_manager.clamp_trade_value(
        proposed, context.equity, cash, context.open_lot_count, context.drawdown
    )
    return GridDecision(
        context=context,
        triggered=True,
        proposed_trade_value=float(proposed),
        clamped_trade_value=float(clamped),
    )
