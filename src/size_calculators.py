"""
Sizing strategies for the grid-harvesting strategy.

SizingStrategy now implements the *target* form of the shared contract
from architecture_overview.md Section 5.2, as of Task 4.1:

    record_tick(context: MarketContext) -> None
    calculate_trade_value(context: MarketContext) -> float

Migrated from the interim (loose-parameter) form Phases 0-3 used --
see git history for that version. optimization_controller.py's
_simulate_single (Task 4.1) constructs one MarketContext per bar and
passes it to record_tick, _check_grid_trigger, and
calculate_trade_value uniformly.

Only FixedPortfolioPercentage is implemented. BellCurveProbabilitySizing,
RsiMomentumSizing (also named for this file in the module layout,
architecture_overview.md Section 6) and BayesianDualScaleSizing (a
separate file, src/bayesian_sizing_calculators.py) are not included --
none of the three have a documented sizing formula to implement
against, unlike FixedPortfolioPercentage's straightforward
equity-times-percentage rule.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from src.market_context import MarketContext
from src.exceptions import ConfigurationError


class SizingStrategy(ABC):
    """Target-form sizing-strategy contract (architecture_overview.md
    Section 5.2), as of Task 4.1."""

    def _check_grid_trigger(self, context: MarketContext, last_buy_price: float, step: float) -> bool:
        """Default: identical to the pre-Task-4.1 inline check
        (current_price <= last_buy_price * (1 - step)), now expressed
        against context.price. last_buy_price/step aren't part of
        MarketContext (they're grid/backtest state, not market state),
        so they stay as explicit parameters. Overridable per-strategy."""
        return context.price <= last_buy_price * (1.0 - step)

    @abstractmethod
    def record_tick(self, context: MarketContext) -> None:
        """Called once per bar in the target execution sequence
        (implementation_task_specs.md "Canonical execution sequence")."""
        ...

    @abstractmethod
    def calculate_trade_value(self, context: MarketContext) -> float:
        """Dollar value to buy at a confirmed grid trigger."""
        ...


class FixedPortfolioPercentage(SizingStrategy):
    """Allocates a fixed percentage of total equity to each triggered buy.

    Stateless: ignores ticks and drawdown entirely. This matches Task
    1.6's acceptance criteria for this specific strategy ("doesn't use
    drawdown or ticks in its sizing").

    Constructor keyword is `allocation_pct`, per
    implementation_task_specs.md Task 1.1's own proposed reading of
    Run_Instructions' (buggy) `allocations` example parameter.
    """

    def __init__(self, allocation_pct: float):
        if not 0.0 < allocation_pct <= 1.0:
            raise ConfigurationError(f"allocation_pct must be in (0, 1], got {allocation_pct}")
        self.allocation_pct = allocation_pct

    def record_tick(self, context: MarketContext) -> None:
        pass  # stateless -- nothing to track

    def calculate_trade_value(self, context: MarketContext) -> float:
        return context.equity * self.allocation_pct
