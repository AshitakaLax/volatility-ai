"""Transaction-cost models used by the backtest execution path."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(frozen=True)
class TransactionCosts:
    """Cost breakdown for one executed order."""

    commission: float = 0.0
    slippage: float = 0.0

    @property
    def total(self) -> float:
        return self.commission + self.slippage


class TransactionCostModel(ABC):
    """Interface for deterministic transaction-cost calculation."""

    @abstractmethod
    def calculate(self, quantity: float, price: float, side: str) -> TransactionCosts:
        raise NotImplementedError


class ZeroCostModel(TransactionCostModel):
    """Preserve the historical zero-cost simulation baseline."""

    def calculate(self, quantity: float, price: float, side: str) -> TransactionCosts:
        _ = quantity, price, side
        return TransactionCosts()


class SlippageCommissionModel(TransactionCostModel):
    """Apply percentage slippage and commission to an execution notional.

    ``slippage_pct`` changes the effective execution price: buys pay more and
    sells receive less. ``commission_pct`` is an additional cash cost charged
    on the executed notional.
    """

    def __init__(self, slippage_pct: float = 0.0, commission_pct: float = 0.0) -> None:
        if slippage_pct < 0.0 or commission_pct < 0.0:
            raise ValueError("cost percentages cannot be negative")
        self.slippage_pct = float(slippage_pct)
        self.commission_pct = float(commission_pct)

    def calculate(self, quantity: float, price: float, side: str) -> TransactionCosts:
        quantity = float(quantity)
        price = float(price)
        if quantity <= 0.0 or price <= 0.0:
            raise ValueError("quantity and price must be positive")
        normalized_side = str(side).upper()
        if normalized_side not in {"BUY", "SELL"}:
            raise ValueError("side must be BUY or SELL")
        notional = quantity * price
        slippage = notional * self.slippage_pct
        commission = notional * self.commission_pct
        return TransactionCosts(commission=commission, slippage=slippage)
