"""Order-management abstraction with deterministic simulation fills."""

from __future__ import annotations

from enum import Enum
from itertools import count
from typing import Callable, TypeVar


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


T = TypeVar("T")


class OrderManagementSystem:
    """Submit orders through a simulation adapter and process events once."""

    def __init__(self, mode: str | Mode = Mode.SIMULATION) -> None:
        self.mode = Mode(mode)
        self._ids = count(1)
        self.orders: list[dict] = []
        self._processed_event_ids: set[str] = set()
        self._acted_decision_ids: set[str] = set()

    def _simulation_order(self, side: str, symbol: str, qty: float, price: float, notional: float, decision_id: str | None = None) -> dict:
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
        if decision_id is not None:
            order["decision_id"] = str(decision_id)
            self._acted_decision_ids.add(str(decision_id))
        self.orders.append(order)
        return order

    def process_event_once(self, event_id: str, handler: Callable[[], T]) -> tuple[bool, T | None]:
        key = str(event_id)
        if not key:
            raise ValueError("event_id must be non-empty")
        if key in self._processed_event_ids:
            return False, None
        self._processed_event_ids.add(key)
        try:
            return True, handler()
        except Exception:
            self._processed_event_ids.remove(key)
            raise

    def is_event_processed(self, event_id: str) -> bool:
        return str(event_id) in self._processed_event_ids

    def has_acted_on_decision(self, decision_id: str) -> bool:
        return str(decision_id) in self._acted_decision_ids

    def record_acted_decision(self, decision_id: str) -> None:
        if not str(decision_id):
            raise ValueError("decision_id must be non-empty")
        self._acted_decision_ids.add(str(decision_id))

    def execute_buy(self, symbol: str, trade_value: float, current_price: float, decision_id: str | None = None) -> dict:
        if self.mode is not Mode.SIMULATION:
            raise NotImplementedError("LIVE execution is implemented by Phase 7")
        qty = float(trade_value) / float(current_price)
        return self._simulation_order("BUY", symbol, qty, current_price, trade_value, decision_id)

    def execute_sell(self, symbol: str, qty: float, target_price: float, decision_id: str | None = None) -> dict:
        if self.mode is not Mode.SIMULATION:
            raise NotImplementedError("LIVE execution is implemented by Phase 7")
        notional = float(qty) * float(target_price)
        return self._simulation_order("SELL", symbol, qty, target_price, notional, decision_id)
