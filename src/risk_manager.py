"""Risk constraints applied between strategy sizing and order execution."""

from __future__ import annotations

from enum import Enum
from typing import Any


class CircuitState(str, Enum):
    ACTIVE = "ACTIVE"
    HALTED_NEW_BUYS = "HALTED_NEW_BUYS"
    MANUAL_RESET_REQUIRED = "MANUAL_RESET_REQUIRED"


class RiskManager:
    """Clamp proposed trade values to configured portfolio risk limits."""

    def __init__(self, *, max_concurrent_lots: int | None = None, max_total_exposure: float | None = None, circuit_breaker: Any | None = None) -> None:
        if max_concurrent_lots is not None and max_concurrent_lots < 0:
            raise ValueError("max_concurrent_lots must be non-negative or None")
        if max_total_exposure is not None and not 0.0 <= float(max_total_exposure) <= 1.0:
            raise ValueError("max_total_exposure must be between 0 and 1 or None")
        self.max_concurrent_lots = max_concurrent_lots
        self.max_total_exposure = None if max_total_exposure is None else float(max_total_exposure)
        self.circuit_breaker = circuit_breaker

    def clamp_trade_value(self, proposed_value: float, equity: float, cash: float, open_lot_count: int) -> float:
        proposed = max(0.0, float(proposed_value))
        equity = max(0.0, float(equity))
        cash = max(0.0, float(cash))
        lots = max(0, int(open_lot_count))
        if self.circuit_breaker is not None and self.circuit_breaker.state != CircuitState.ACTIVE:
            return 0.0
        if self.max_concurrent_lots is not None and lots >= self.max_concurrent_lots:
            return 0.0
        allowed = cash
        if self.max_total_exposure is not None:
            current_exposure = max(0.0, equity - cash)
            exposure_cap = equity * self.max_total_exposure
            allowed = min(allowed, max(0.0, exposure_cap - current_exposure))
        return min(proposed, allowed)
