"""The sizing-strategy PORT: the contract the engine calls, with no
knowledge of any concrete strategy.

--------------------------------------------------------------------
WHY IT LIVES IN core/ AND NOT WITH THE STRATEGIES

This ABC used to sit in research/strategies/size_calculators.py alongside
the concrete strategies that implement it. That meant the two engine
modules which merely CALL a strategy --
engine/execution/live_execution.py and engine/trading/decision_cycle.py --
had to import research.strategies to name the type, so the engine imported
the algorithm library, which imports the engine back. That edge was
part of what kept 10 of src/'s 12 subpackages in a single
strongly-connected component.

The contract is not an algorithm. Engine depends on the port; the
strategies in research/strategies/ and research/ml/ are the adapters that
implement it, and nothing in the engine needs to know they exist --
research/strategies/strategy_registry.py is the one place that does.

size_calculators.py re-exports this name, so the ~28 modules and tests
that do `from research.strategies.size_calculators import SizingStrategy`
keep working unchanged; only the engine imports it from here.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from engine.core.market_context import MarketContext

__all__ = ["SizingStrategy"]


class SizingStrategy(ABC):
    """Target-form sizing-strategy contract (architecture_overview.md
    Section 5.2), as of Task 4.1."""

    def _grid_trigger_level(
        self, context: MarketContext, last_buy_price: float, step: float
    ) -> float:
        """The price AT OR BELOW WHICH a buy triggers.

        Split out from _check_grid_trigger so the level is a value the
        caller can inspect, not just a boolean it can evaluate. The
        intrabar fill model needs exactly that: it compares the level
        against the bar's LOW (did a resting limit order get touched?)
        and fills AT the level, which is impossible to do from a
        boolean alone.

        Before this existed, src/intraday_validation.py recomputed
        `last_buy_price * (1 - grid_step)` inline -- which silently
        hardcoded the DEFAULT formula and would have been wrong for any
        strategy overriding the trigger (HighFrequencyLocalReferenceSizing
        measures its pullback from max(last_buy_price, rolling_high),
        not from last_buy_price). Overriding THIS method, rather than
        _check_grid_trigger, is what keeps the close-only and intrabar
        paths agreeing on one definition per strategy.
        """
        return last_buy_price * (1.0 - step)

    def _check_grid_trigger(
        self, context: MarketContext, last_buy_price: float, step: float
    ) -> bool:
        """Default: identical to the pre-Task-4.1 inline check
        (current_price <= last_buy_price * (1 - step)), now expressed
        against context.price and routed through _grid_trigger_level so
        there is one definition of the level per strategy.
        last_buy_price/step aren't part of MarketContext (they're
        grid/backtest state, not market state), so they stay as explicit
        parameters. Overridable per-strategy, though overriding
        _grid_trigger_level is usually the better seam -- see there."""
        return context.price <= self._grid_trigger_level(context, last_buy_price, step)

    def adjust_profit_target(self, lot, context: MarketContext) -> float | None:
        """The profit_target `lot` should now carry, or None to leave it.

        Default: None for every lot, so a strategy that does not
        override this keeps the original fixed-at-entry behavior
        exactly -- no existing strategy, config, or recorded sweep
        result changes because this hook exists.

        Called once per open lot per bar, BEFORE that bar's marketable
        check, by decision_cycle.adjust_open_lot_targets -- which is
        what keeps backtest and live applying it at the same point in
        the sequence rather than in two places that could drift.

        Overriding this cannot make a losing sell possible.
        src/no_loss_guard.py evaluates against buy_price and rejects
        independently of any target; see src/ledger.Lot.retarget.
        Compose src/trailing_target.TrailingTargetPolicy here rather
        than writing peak-tracking by hand.
        """
        return None

    def lots_to_liquidate(self, open_lots, context: MarketContext) -> list:
        """Open lots to close NOW for a reason unrelated to their price.

        Default: empty for every strategy, so this hook existing changes
        nothing. A strategy that overrides it is asking for a signal
        exit -- a trend break, a regime flip -- and such an exit MAY
        realize a loss, which is the whole reason the hook is separate
        from adjust_profit_target (which explicitly cannot).

        That makes this the only hook in the sizing interface capable of
        losing money on purpose, so it is deliberately half a gate:
        `execution.allow_signal_exit` must ALSO be True. A strategy
        overriding this against a default config liquidates nothing --
        see decision_cycle.collect_liquidations, which is where the two
        conditions meet, and src/no_loss_guard.SellReason for why the
        guard still runs on every one of these sells.

        Called once per bar, after adjust_open_lot_targets and before
        the marketable check, by decision_cycle.collect_liquidations --
        the same single-implementation discipline that keeps backtest,
        intrabar replay, and live from drifting apart.

        `open_lots` is a snapshot list, safe to filter. Return a subset
        of it; lots not in the ledger are ignored rather than trusted.
        """
        return []

    @abstractmethod
    def record_tick(self, context: MarketContext) -> None:
        """Called once per bar in the target execution sequence
        (implementation_task_specs.md "Canonical execution sequence")."""
        ...

    @abstractmethod
    def calculate_trade_value(self, context: MarketContext) -> float:
        """Dollar value to buy at a confirmed grid trigger."""
        ...
