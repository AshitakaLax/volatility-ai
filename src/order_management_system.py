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
    """Submit orders through a simulation adapter and process events once.

    The simulation adapter owns an in-process processed-event set. Live-mode
    persistence is intentionally deferred to the persistence layer specified
    by the later live/reconnect tasks; this set is sufficient for a simulation
    run whose lifetime bounds duplicate-event delivery.
    """

    def __init__(self, mode: str | Mode = Mode.SIMULATION) -> None:
        self.mode = Mode(mode)
        self._ids = count(1)
        self.orders: list[dict] = []
        self._processed_event_ids: set[str] = set()

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

    def process_event_once(self, event_id: str, handler: Callable[[], T]) -> tuple[bool, T | None]:
        """Apply an externally sourced event at most once.

        Returns ``(True, result)`` for the first delivery and
        ``(False, None)`` for a duplicate. Event IDs are broker/order IDs for
        broker-sourced events; simulation order IDs are stable for the run.
        """
        key = str(event_id)
        if not key:
            raise ValueError("event_id must be non-empty")
        if key in self._processed_event_ids:
            return False, None
        self._processed_event_ids.add(key)
        try:
            return True, handler()
        except Exception:
            # Failed handlers did not successfully apply the event; allow a
            # later delivery to retry rather than permanently swallowing it.
            self._processed_event_ids.remove(key)
            raise

    def is_event_processed(self, event_id: str) -> bool:
        return str(event_id) in self._processed_event_ids

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
