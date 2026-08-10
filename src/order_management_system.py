"""Order-management abstraction with deterministic simulation fills."""

from __future__ import annotations

from enum import Enum
from itertools import count


class OrderStatus(str, Enum):
    CREATED = "CREATED"
    SUBMITTED = "SUBMITTED"
    FILLED = "FILLED"
    PARTIALLY_FILLED = "PARTIALLY_FILLED"
    CANCELED = "CANCELED"
    REJECTED = "REJECTED"
    UNKNOWN = "UNKNOWN"


class Mode(str, Enum):
    SIMULATION = "SIMULATION"
    LIVE = "LIVE"


class OrderManagementSystem:
    """Submit orders through a simulation adapter.

    Live broker integration belongs to the later live-execution tasks.  The
    simulation mode is intentionally deterministic: every accepted order is
    completely filled at the requested price.
    """

    def __init__(self, mode: str | Mode = Mode.SIMULATION) -> None:
        self.mode = Mode(mode)
        self._ids = count(1)
        self.orders: list[dict] = []

    def _simulation_order(self, side: str, symbol: str, qty: float, price: float, notional: float) -> dict:
        if qty <= 0 or price <= 0:
            raise ValueError("quantity and price must be positive")
        order = {
            "id": f"sim-{next(self._ids)}",
            "symbol": symbol,
            "side": side,
            "qty": float(qty),
            "filled_qty": float(qty),
            "filled_avg_price": float(price),
            "notional": float(notional),
            "status": OrderStatus.FILLED.value,
        }
        self.orders.append(order)
        return order

    def execute_buy(self, symbol: str, trade_value: float, current_price: float) -> dict:
        if self.mode is not Mode.SIMULATION:
            raise NotImplementedError("LIVE execution is implemented by Phase 7")
        qty = float(trade_value) / float(current_price)
        return self._simulation_order("BUY", symbol, qty, current_price, trade_value)

    def execute_sell(self, symbol: str, qty: float, target_price: float) -> dict:
        if self.mode is not Mode.SIMULATION:
            raise NotImplementedError("LIVE execution is implemented by Phase 7")
        notional = float(qty) * float(target_price)
        return self._simulation_order("SELL", symbol, qty, target_price, notional)
