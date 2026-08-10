"""
Sizing strategies for the grid-harvesting strategy.

Original, from-scratch implementation (no existing src/size_calculators.py
was available to read -- see the chat this was produced in).

SizingStrategy implements the *interim* form of the shared contract from
architecture_overview.md Section 5.2, not the MarketContext-based target
form:

    record_tick(current_price)
    calculate_trade_value(total_equity, current_price, current_dd=0.0)

Section 5.2's own sequencing note says this interim form is what Phase 1
(Tasks 1.3/1.4) fixes bugs B2/B4 against, and that Task 4.1 migrates
every strategy to the MarketContext form later. optimization_controller.py
currently calls only calculate_trade_value(total_equity, current_price) --
never record_tick, and never with a current_dd argument -- which is
exactly documented bugs B4 and B2. That means current_dd defaults to
0.0 here and record_tick is defined but never invoked, matching current
(unfixed) behavior rather than working around it.

Only FixedPortfolioPercentage is implemented. BellCurveProbabilitySizing,
RsiMomentumSizing (also named for this file in the module layout,
architecture_overview.md Section 6) and BayesianDualScaleSizing (a
separate file, src/bayesian_sizing_calculators.py) are not included --
Task 0.1's regression fixture only exercises FixedPortfolioPercentage,
and none of the three have a documented sizing formula to implement
against, unlike FixedPortfolioPercentage's straightforward
equity-times-percentage rule.
"""

from __future__ import annotations

from abc import ABC, abstractmethod


class SizingStrategy(ABC):
    """Interim-form sizing-strategy contract (architecture_overview.md
    Section 5.2's pre-Task-4.1 form)."""

    def _check_grid_trigger(self, current_price: float, last_buy_price: float, step: float) -> bool:
        """Default: identical to optimization_controller.py's current inline
        check. Not currently called by the controller (it has its own
        inline check) -- provided for interface completeness and so a
        future strategy can override trigger logic without the controller
        needing to change first."""
        return current_price <= last_buy_price * (1.0 - step)

    @abstractmethod
    def record_tick(self, current_price: float) -> None:
        """Called once per bar in the target execution sequence
        (implementation_task_specs.md "Canonical execution sequence").
        Not currently called by optimization_controller.py (documented
        bug B4) -- implementations should not assume it fires."""
        ...

    @abstractmethod
    def calculate_trade_value(
        self, total_equity: float, current_price: float, current_dd: float = 0.0
    ) -> float:
        """Dollar value to buy at a confirmed grid trigger. current_dd is
        the current drawdown fraction; optimization_controller.py never
        passes it (documented bug B2), so it defaults to 0.0."""
        ...


class FixedPortfolioPercentage(SizingStrategy):
    """Allocates a fixed percentage of total equity to each triggered buy.

    Stateless: ignores ticks and drawdown entirely. This matches Task
    1.6's acceptance criteria for this specific strategy ("doesn't use
    drawdown or ticks in its sizing" -- output should be unchanged
    versus the pre-Phase-1 baseline once B2/B4 are fixed elsewhere).

    Constructor keyword is `allocation_pct`, per
    implementation_task_specs.md Task 1.1's own proposed reading of
    Run_Instructions' (buggy) `allocations` example parameter --
    flagged there as an unconfirmed guess in the absence of real
    source; adopted here as the concrete name since this is now the
    real source.
    """

    def __init__(self, allocation_pct: float):
        if not 0.0 < allocation_pct <= 1.0:
            raise ValueError(f"allocation_pct must be in (0, 1], got {allocation_pct}")
        self.allocation_pct = allocation_pct

    def record_tick(self, current_price: float) -> None:
        pass  # stateless -- nothing to track

    def calculate_trade_value(
        self, total_equity: float, current_price: float, current_dd: float = 0.0
    ) -> float:
        return total_equity * self.allocation_pct
