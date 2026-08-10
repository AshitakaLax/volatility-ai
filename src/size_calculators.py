"""Position-sizing strategies used by the backtest controller."""

from __future__ import annotations

from abc import ABC, abstractmethod


class SizingStrategy(ABC):
    """Base contract for sizing engines used by the current controller.

    Phase 1/4 will extend this contract with per-bar drawdown/context methods;
    the current controller only requires ``calculate_trade_value``.
    """

    def _check_grid_trigger(self, current_price: float, last_buy_price: float, step: float) -> bool:
        return float(current_price) <= float(last_buy_price) * (1.0 - float(step))

    def record_tick(self, current_price: float) -> None:
        """Hook for stateful strategies; no-op for the fixed strategy."""

    @abstractmethod
    def calculate_trade_value(
        self,
        total_equity: float,
        current_price: float,
        current_dd: float = 0.0,
    ) -> float:
        raise NotImplementedError


class FixedPortfolioPercentage(SizingStrategy):
    """Deploy a fixed percentage of current portfolio equity per grid buy."""

    def __init__(self, percentage: float | None = None, allocation_pct: float | None = None) -> None:
        if percentage is None and allocation_pct is None:
            raise TypeError("percentage is required")
        if percentage is not None and allocation_pct is not None and percentage != allocation_pct:
            raise ValueError("percentage and allocation_pct disagree")
        value = percentage if percentage is not None else allocation_pct
        assert value is not None
        if not 0.0 < float(value) <= 1.0:
            raise ValueError("percentage must be in the interval (0, 1]")
        self.percentage = float(value)

    def calculate_trade_value(
        self,
        total_equity: float,
        current_price: float,
        current_dd: float = 0.0,
    ) -> float:
        _ = current_price, current_dd
        return max(0.0, float(total_equity) * self.percentage)
