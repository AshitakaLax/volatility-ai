"""Canonical transaction-cost models for backtest execution."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from src.market_context import MarketContext


class TransactionCostModel(ABC):
    @abstractmethod
    def apply_buy(self, price: float, qty: float, context: Optional["MarketContext"] = None, prev_close: Optional[float] = None) -> tuple[float, float]:
        raise NotImplementedError

    @abstractmethod
    def apply_sell(self, price: float, qty: float, context: Optional["MarketContext"] = None, prev_close: Optional[float] = None) -> tuple[float, float]:
        raise NotImplementedError


class ZeroCostModel(TransactionCostModel):
    def apply_buy(self, price, qty, context=None, prev_close=None):
        return float(price), 0.0

    def apply_sell(self, price, qty, context=None, prev_close=None):
        return float(price), 0.0


class SlippageCommissionModel(TransactionCostModel):
    def __init__(self, commission_per_trade: float = 0.0, slippage_bps: float = 0.0):
        if commission_per_trade < 0.0 or slippage_bps < 0.0:
            raise ValueError("commission_per_trade and slippage_bps cannot be negative")
        self.commission_per_trade = float(commission_per_trade)
        self.slippage_bps = float(slippage_bps)

    def apply_buy(self, price, qty, context=None, prev_close=None):
        _ = qty, context, prev_close
        return float(price) * (1.0 + self.slippage_bps / 10_000.0), self.commission_per_trade

    def apply_sell(self, price, qty, context=None, prev_close=None):
        _ = qty, context, prev_close
        return float(price) * (1.0 - self.slippage_bps / 10_000.0), self.commission_per_trade


class DynamicSlippageModel(TransactionCostModel):
    """Scale base slippage with the absolute move from the previous close.

    The multiplier is ``1 + abs(price / prev_close - 1)``. When no previous
    close is supplied (or it is non-positive), the base slippage is used.
    """

    def __init__(self, commission_per_trade: float = 0.0, slippage_bps: float = 0.0):
        if commission_per_trade < 0.0 or slippage_bps < 0.0:
            raise ValueError("commission_per_trade and slippage_bps cannot be negative")
        self.commission_per_trade = float(commission_per_trade)
        self.slippage_bps = float(slippage_bps)

    def _effective_bps(self, price: float, prev_close: Optional[float]) -> float:
        if prev_close is None or float(prev_close) <= 0.0:
            return self.slippage_bps
        move = abs(float(price) / float(prev_close) - 1.0)
        return self.slippage_bps * (1.0 + move)

    def apply_buy(self, price, qty, context=None, prev_close=None):
        _ = qty, context
        bps = self._effective_bps(price, prev_close)
        return float(price) * (1.0 + bps / 10_000.0), self.commission_per_trade

    def apply_sell(self, price, qty, context=None, prev_close=None):
        _ = qty, context
        bps = self._effective_bps(price, prev_close)
        return float(price) * (1.0 - bps / 10_000.0), self.commission_per_trade
