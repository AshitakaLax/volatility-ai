"""
Transaction cost models, per architecture_overview.md Section 5.3
(implemented here for Task 2.2, including the context/prev_close
forward-compatible parameters that section documents adding for
Task 7.5 -- included from the start so no signature change is needed
later).
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional


class TransactionCostModel(ABC):
    @abstractmethod
    def apply_buy(
        self, price: float, qty: float, context: Optional["MarketContext"] = None, prev_close: Optional[float] = None
    ) -> tuple[float, float]:
        """Returns (effective_fill_price, cost). Pure calculation --
        does not mutate portfolio, ledger, or order state. context/
        prev_close are optional forward-compatible hooks for
        volatility-aware models (Section 5.5); static models ignore them."""

    @abstractmethod
    def apply_sell(
        self, price: float, qty: float, context: Optional["MarketContext"] = None, prev_close: Optional[float] = None
    ) -> tuple[float, float]:
        """Returns (effective_fill_price, cost)."""


class ZeroCostModel(TransactionCostModel):
    """Matches current (pre-Task-2.2) behavior exactly -- the default."""

    def apply_buy(self, price, qty, context=None, prev_close=None):
        return price, 0.0

    def apply_sell(self, price, qty, context=None, prev_close=None):
        return price, 0.0


class SlippageCommissionModel(TransactionCostModel):
    def __init__(self, commission_per_trade: float = 0.0, slippage_bps: float = 0.0):
        self.commission_per_trade = commission_per_trade
        self.slippage_bps = slippage_bps

    def apply_buy(self, price, qty, context=None, prev_close=None):
        # Slippage increases the effective buy price -- you pay more.
        return price * (1 + self.slippage_bps / 10_000), self.commission_per_trade

    def apply_sell(self, price, qty, context=None, prev_close=None):
        # Slippage decreases the effective sell price -- you receive less.
        return price * (1 - self.slippage_bps / 10_000), self.commission_per_trade
