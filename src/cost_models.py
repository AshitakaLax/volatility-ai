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


class DynamicSlippageModel(TransactionCostModel):
    """Volatility-aware slippage. Task 7.5 (L6), implemented exactly per
    architecture_overview.md Section 5.5.

    Scales slippage by the current bar's absolute percentage move
    versus the previous bar's close, so a fast-moving bar costs more to
    trade than a calm one -- a flat slippage_bps understates cost
    exactly when it matters most.

    Falls back to base_bps when context or prev_close is unavailable
    (the first bar of a run has no previous close), so it degrades to
    static behavior rather than raising or silently assuming zero
    volatility. Note the falsy check inherited from the canonical
    implementation also covers prev_close == 0, which would otherwise
    divide by zero.

    Swapping the single-bar-move proxy for a proper ATR is Section
    5.5's own stated "reasonable refinement, not required for Task
    7.5" -- deliberately not done here.
    """

    def __init__(self, base_bps: float = 0.0, vol_multiplier: float = 1.0, commission_per_trade: float = 0.0):
        self.base_bps = base_bps
        self.vol_multiplier = vol_multiplier
        self.commission_per_trade = commission_per_trade

    def _dynamic_bps(self, context, prev_close) -> float:
        if not context or not prev_close:
            return self.base_bps
        bar_move_pct = abs(context.close - prev_close) / prev_close
        return self.base_bps + (bar_move_pct * 10_000 * self.vol_multiplier)

    def apply_buy(self, price, qty, context=None, prev_close=None):
        bps = self._dynamic_bps(context, prev_close)
        return price * (1 + bps / 10_000), self.commission_per_trade

    def apply_sell(self, price, qty, context=None, prev_close=None):
        bps = self._dynamic_bps(context, prev_close)
        return price * (1 - bps / 10_000), self.commission_per_trade
