"""Position-sizing strategies used by the backtest controller."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections import deque

from src.market_context import MarketContext


class SizingStrategy(ABC):
    """Canonical context-based sizing strategy contract."""

    def _check_grid_trigger(self, context: MarketContext, last_buy_price: float, step: float) -> bool:
        return context.price <= float(last_buy_price) * (1.0 - float(step))

    @abstractmethod
    def record_tick(self, context: MarketContext) -> None:
        raise NotImplementedError

    @abstractmethod
    def calculate_trade_value(self, context: MarketContext) -> float:
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

    def record_tick(self, context: MarketContext) -> None:
        _ = context

    def calculate_trade_value(self, context: MarketContext) -> float:
        return max(0.0, float(context.equity) * self.percentage)


class RsiMomentumSizing(SizingStrategy):
    """RSI-aware position sizing using the canonical MarketContext contract."""

    def __init__(
        self,
        rsi_period: int = 14,
        base_percentage: float = 0.10,
        allocation_pct: float | None = None,
    ) -> None:
        if int(rsi_period) < 2:
            raise ValueError("rsi_period must be at least 2")
        percentage = base_percentage if allocation_pct is None else allocation_pct
        if not 0.0 < float(percentage) <= 1.0:
            raise ValueError("base_percentage must be in the interval (0, 1]")
        self.rsi_period = int(rsi_period)
        self.base_percentage = float(percentage)
        self._prices: deque[float] = deque(maxlen=self.rsi_period + 1)
        self._rsi: float | None = None

    @property
    def rsi(self) -> float | None:
        return self._rsi

    def record_tick(self, context: MarketContext) -> None:
        price = float(context.price)
        if price <= 0.0:
            raise ValueError("context.price must be positive")
        self._prices.append(price)
        if len(self._prices) < self.rsi_period + 1:
            self._rsi = None
            return

        gains = 0.0
        losses = 0.0
        prices = list(self._prices)
        for previous, current in zip(prices, prices[1:]):
            change = current - previous
            if change > 0.0:
                gains += change
            elif change < 0.0:
                losses -= change

        avg_gain = gains / self.rsi_period
        avg_loss = losses / self.rsi_period
        if avg_loss == 0.0:
            self._rsi = 100.0 if avg_gain > 0.0 else 50.0
        else:
            self._rsi = 100.0 - (100.0 / (1.0 + (avg_gain / avg_loss)))

    def calculate_trade_value(self, context: MarketContext) -> float:
        if self._rsi is None:
            return 0.0
        multiplier = 1.0 if self._rsi <= 50.0 else max(0.0, (70.0 - self._rsi) / 20.0)
        return max(0.0, float(context.equity) * self.base_percentage * multiplier)
