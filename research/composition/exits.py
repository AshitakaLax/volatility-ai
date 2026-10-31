"""
Sell policies: when to sell an open lot and how much of it, apart from how it
was bought. One of these is the `sell` half of a ComposedStrategy
(composed_strategy.py); the `buy` half is any registered buy algorithm.

An ExitPolicy answers exactly the sell-side questions the SizingStrategy
port asks (engine/core/sizing.py), with the same meaning and the same
defaults, so a policy that overrides nothing sells exactly as the grid has
always sold: each lot whole, at the target it was bought with.

  adjust_profit_target(lot, context)  -> new target, or None      (no loss possible)
  harvest_quantity(lot, context)      -> shares to sell at target (no loss possible)
  lots_to_liquidate(open_lots, ctx)   -> lots / ExitOrders to close now (MAY lose;
                                         only behind execution.allow_signal_exit)
  wants_lot_retargeting(), retain_lots(open_ids), record_tick(context)

`can_realize_loss` says which TRACK a policy is on (docs/research/
buy-sell-composition.md, Design §5): False for a policy whose every sale is a
target harvest the no-loss guard checks, True for one that emits signal
exits. The web marks the second kind "may sell below cost", and a live
deployment refuses it without allow_signal_exit in its own file.

Nothing here reimplements the no-loss comparison: every sale a policy asks
for still reaches engine/trading/no_loss_guard.py.
"""

from __future__ import annotations

from engine.core.exceptions import ConfigurationError
from engine.core.market_context import MarketContext
from research.optimization.trailing_target import TrailingTargetPolicy

# A tranche is floored to nine decimals (exit_policy.sellable_quantity), so
# the fraction of a lot sold lands a hair under the rung it reached. A rung
# check compares with this tolerance, far above that step.
RUNG_TOLERANCE = 1e-6


class ExitPolicy:
    """Sell every lot whole at its own target: the grid's behaviour since the
    start, and the base every policy refines."""

    exit_id = "fixed_target"
    label = "Fixed target"
    can_realize_loss = False

    def record_tick(self, context: MarketContext) -> None:
        """Every bar, after the buy side's record_tick."""

    def wants_lot_retargeting(self) -> bool:
        """False promises adjust_profit_target and retain_lots are inert, so
        the engine may skip walking the open book (decision_cycle)."""
        return False

    def adjust_profit_target(self, lot, context: MarketContext) -> float | None:
        return None

    def retain_lots(self, open_order_ids) -> None:
        """Forget per-lot state for lots no longer open."""

    def harvest_quantity(self, lot, context: MarketContext) -> float:
        return lot.shares

    def lots_to_liquidate(self, open_lots, context: MarketContext) -> list:
        return []

    def diagnostics(self) -> dict:
        return {}


class FixedTarget(ExitPolicy):
    """Each lot whole, at the target it was bought with (grid.profit_targets)."""


class Trailing(ExitPolicy):
    """A target that trails the best price each lot has reached, ratcheting
    down only (research/optimization/trailing_target.py). The same policy
    the HF family builds from trail_pct, so composed with the champion it
    is the champion with trail_pct set."""

    exit_id = "trailing"
    label = "Trailing target"

    def __init__(self, trail_pct: float, min_profit_target: float = 0.001) -> None:
        self.trail_pct = trail_pct
        self.min_profit_target = min_profit_target
        self._trailing = TrailingTargetPolicy(trail_pct, min_profit_target=min_profit_target)

    def wants_lot_retargeting(self) -> bool:
        return True

    def adjust_profit_target(self, lot, context: MarketContext) -> float | None:
        return self._trailing.propose(lot, context.price)

    def retain_lots(self, open_order_ids) -> None:
        self._trailing.retain_lots(open_order_ids)


EXITS: dict[str, type[ExitPolicy]] = {
    "fixed_target": FixedTarget,
    "trailing": Trailing,
}

# What a sell policy's parameters are seeded to on the web form, as
# research/strategies/param_schema.STRATEGY_DEFAULTS is for strategies.
EXIT_DEFAULTS: dict[str, dict] = {
    "fixed_target": {},
    "trailing": {"trail_pct": 0.01, "min_profit_target": 0.001},
}


def register(cls: type[ExitPolicy], defaults: dict | None = None) -> type[ExitPolicy]:
    """Add a sell policy to the registry (used by the policy library)."""
    if not cls.exit_id or (cls.exit_id in EXITS and EXITS[cls.exit_id] is not cls):
        raise ConfigurationError(f"exit id {cls.exit_id!r} is empty or already taken")
    EXITS[cls.exit_id] = cls
    EXIT_DEFAULTS[cls.exit_id] = dict(defaults or {})
    return cls


def resolve_exit(exit_id: str) -> type[ExitPolicy]:
    try:
        return EXITS[exit_id]
    except KeyError:
        known = ", ".join(sorted(EXITS))
        raise ConfigurationError(f"Unknown sell policy {exit_id!r}. Known: {known}") from None


def build_exit(exit_id: str, params: dict) -> ExitPolicy:
    cls = resolve_exit(exit_id)
    try:
        return cls(**params)
    except TypeError as exc:
        raise ConfigurationError(f"sell policy {exit_id} refused these parameters: {exc}") from exc
