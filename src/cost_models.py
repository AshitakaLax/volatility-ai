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
    """Interface for modeling the real cost of a fill.

    Implementations are PURE: they compute an effective price and a cost
    and return them. They never move cash, touch a lot, or submit an
    order -- callers apply the result. That purity is what lets the
    backtest loop, the intraday replay, and the no-loss guard all call
    the same model without coordinating side effects.

    Both methods return (effective_fill_price, cost) as a 2-tuple, where
    cost is an absolute currency amount (commission/fees) and slippage is
    already folded into effective_fill_price.
    """

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
        """Returns (effective_fill_price, cost) for a sell.

        Slippage on a sell moves the effective price DOWN (you receive
        less), the mirror of apply_buy. Same purity contract.
        """


class ZeroCostModel(TransactionCostModel):
    """Matches current (pre-Task-2.2) behavior exactly -- the default."""

    def apply_buy(self, price, qty, context=None, prev_close=None):
        """Fill at exactly the quoted price with no cost."""
        return price, 0.0

    def apply_sell(self, price, qty, context=None, prev_close=None):
        """Fill at exactly the quoted price with no cost."""
        return price, 0.0


class SlippageCommissionModel(TransactionCostModel):
    """Flat per-trade commission plus a fixed slippage rate.

    Slippage is constant regardless of market conditions. For a model
    that widens with volatility, see DynamicSlippageModel below.
    """

    def __init__(self, commission_per_trade: float = 0.0, slippage_bps: float = 0.0):
        """commission_per_trade is an absolute currency amount charged
        once per fill. slippage_bps is in basis points (100 bps = 1%),
        applied against the quoted price and always in the direction
        that costs the trader."""
        self.commission_per_trade = commission_per_trade
        self.slippage_bps = slippage_bps

    def apply_buy(self, price, qty, context=None, prev_close=None):
        """Effective buy price, worsened by a fixed slippage rate."""
        # Slippage increases the effective buy price -- you pay more.
        return price * (1 + self.slippage_bps / 10_000), self.commission_per_trade

    def apply_sell(self, price, qty, context=None, prev_close=None):
        """Effective sell price, worsened by a fixed slippage rate."""
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
        """base_bps is the floor charged even on a flat bar.
        vol_multiplier scales the volatility component: the bar's
        absolute percentage move is converted to bps and multiplied by
        this before being added to base_bps. Defaults make this a
        complete no-op, so it is safe to construct without configuring.
        """
        self.base_bps = base_bps
        self.vol_multiplier = vol_multiplier
        self.commission_per_trade = commission_per_trade

    def _dynamic_bps(self, context, prev_close) -> float:
        """Total slippage in bps for this bar: base plus a
        volatility component proportional to |close - prev_close| /
        prev_close.

        Falls back to base_bps alone when context or prev_close is
        missing -- the first bar of a run has no previous close. The
        falsy check also covers prev_close == 0, which would otherwise
        divide by zero.
        """
        if not context or not prev_close:
            return self.base_bps
        bar_move_pct = abs(context.close - prev_close) / prev_close
        return self.base_bps + (bar_move_pct * 10_000 * self.vol_multiplier)

    def apply_buy(self, price, qty, context=None, prev_close=None):
        """Effective buy price, worsened in proportion to this bar's move."""
        bps = self._dynamic_bps(context, prev_close)
        return price * (1 + bps / 10_000), self.commission_per_trade

    def apply_sell(self, price, qty, context=None, prev_close=None):
        """Effective sell price, worsened in proportion to this bar's move."""
        bps = self._dynamic_bps(context, prev_close)
        return price * (1 - bps / 10_000), self.commission_per_trade
