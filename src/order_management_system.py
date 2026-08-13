"""Order-management abstraction and canonical order lifecycle state machine."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from itertools import count
from typing import Callable, TypeVar


class OrderStatus(str, Enum):
    CREATED = "CREATED"
    SUBMITTED = "SUBMITTED"
    ACCEPTED = "ACCEPTED"
    PARTIALLY_FILLED = "PARTIALLY_FILLED"
    FILLED = "FILLED"
    CANCELED = "CANCELED"
    REJECTED = "REJECTED"
    EXPIRED = "EXPIRED"
    UNKNOWN = "UNKNOWN"


class Mode(str, Enum):
    SIMULATION = "SIMULATION"
    LIVE = "LIVE"


_ALLOWED_TRANSITIONS: dict[OrderStatus, frozenset[OrderStatus]] = {
    OrderStatus.CREATED: frozenset({OrderStatus.SUBMITTED}),
    OrderStatus.SUBMITTED: frozenset({OrderStatus.ACCEPTED, OrderStatus.REJECTED, OrderStatus.UNKNOWN}),
    OrderStatus.ACCEPTED: frozenset({OrderStatus.PARTIALLY_FILLED, OrderStatus.FILLED, OrderStatus.CANCELED, OrderStatus.EXPIRED}),
    OrderStatus.PARTIALLY_FILLED: frozenset({OrderStatus.PARTIALLY_FILLED, OrderStatus.FILLED, OrderStatus.CANCELED}),
    OrderStatus.FILLED: frozenset(),
    OrderStatus.CANCELED: frozenset(),
    OrderStatus.REJECTED: frozenset(),
    OrderStatus.EXPIRED: frozenset(),
    OrderStatus.UNKNOWN: frozenset(),
}

_BROKER_STATUS_MAP = {
    "new": OrderStatus.ACCEPTED,
    "accepted": OrderStatus.ACCEPTED,
    "pending_new": OrderStatus.SUBMITTED,
    "partially_filled": OrderStatus.PARTIALLY_FILLED,
    "filled": OrderStatus.FILLED,
    "canceled": OrderStatus.CANCELED,
    "cancelled": OrderStatus.CANCELED,
    "rejected": OrderStatus.REJECTED,
    "expired": OrderStatus.EXPIRED,
    "done_for_day": OrderStatus.EXPIRED,
    "stopped": OrderStatus.CANCELED,
    "suspended": OrderStatus.UNKNOWN,
}

T = TypeVar("T")


@dataclass
class OrderRecord:
    """Mutable execution state; accounting is owned by the ledger, not here."""

    order_id: str
    symbol: str
    side: str
    requested_qty: float
    filled_qty: float = 0.0
    remaining_qty: float = 0.0
    average_fill_price: float | None = None
    client_order_id: str | None = None
    broker_order_id: str | None = None
    status: OrderStatus = OrderStatus.CREATED
    created_at: object | None = None
    submitted_at: object | None = None
    updated_at: object | None = None


class InvalidOrderTransition(ValueError):
    """Raised when an order lifecycle transition is not permitted."""


class OrderManagementSystem:
    """Order lifecycle state machine with deterministic simulation fills."""

    def __init__(self, mode: str | Mode = Mode.SIMULATION) -> None:
        self.mode = Mode(mode)
        self._ids = count(1)
        self.orders: list[dict] = []
        self.order_states: dict[str, OrderRecord] = {}
        self._processed_event_ids: set[str] = set()
        self._acted_decision_ids: set[str] = set()

    @staticmethod
    def map_broker_status(status: object) -> OrderStatus:
        key = getattr(status, "value", status)
        return _BROKER_STATUS_MAP.get(str(key).lower(), OrderStatus.UNKNOWN)

    def transition(self, order_id: str, new_status: OrderStatus | str) -> OrderRecord:
        record = self.order_states[order_id]
        target = OrderStatus(new_status)
        if target not in _ALLOWED_TRANSITIONS[record.status]:
            raise InvalidOrderTransition(f"invalid order transition {record.status.value} -> {target.value} for {order_id}")
        record.status = target
        return record

    def update_fill(self, order_id: str, cumulative_filled_qty: float, average_fill_price: float | None = None) -> OrderRecord:
        record = self.order_states[order_id]
        cumulative = float(cumulative_filled_qty)
        if cumulative < record.filled_qty or cumulative > record.requested_qty:
            raise ValueError("cumulative filled quantity must be monotonic and <= requested quantity")
        record.filled_qty = cumulative
        record.remaining_qty = record.requested_qty - cumulative
        if average_fill_price is not None:
            record.average_fill_price = float(average_fill_price)
        target = OrderStatus.FILLED if cumulative == record.requested_qty else OrderStatus.PARTIALLY_FILLED
        if target != record.status:
            self.transition(order_id, target)
        return record

    def _simulation_order(self, side: str, symbol: str, qty: float, price: float, notional: float, decision_id: str | None = None) -> dict:
        if qty <= 0 or price <= 0:
            raise ValueError("quantity and price must be positive")
        order_id = f"sim-{next(self._ids)}"
        record = OrderRecord(order_id=order_id, symbol=symbol, side=side, requested_qty=float(qty), remaining_qty=float(qty))
        self.order_states[order_id] = record
        self.transition(order_id, OrderStatus.SUBMITTED)
        self.transition(order_id, OrderStatus.ACCEPTED)
        self.update_fill(order_id, float(qty), float(price))
        order = {
            "id": order_id, "symbol": symbol, "side": side, "qty": float(qty),
            "filled_qty": float(qty), "filled_avg_price": float(price), "notional": float(notional),
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
