"""Broker/local-state reconciliation performed before live trading resumes."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Mapping, Any

from src.exceptions import ReconciliationError
from src.ledger import AssetLotLedger


@dataclass(frozen=True)
class ReconciliationResult:
    symbol: str
    local_position_qty: float
    broker_position_qty: float
    local_open_orders: int
    broker_open_orders: int
    matched: bool
    reason: str


class BrokerReconciler:
    """Compare durable local state with broker state without mutating either."""

    def __init__(
        self,
        *,
        position_reader: Callable[[str], float],
        open_orders_reader: Callable[[str], int] | None = None,
        quantity_epsilon: float = 1e-9,
    ) -> None:
        if quantity_epsilon < 0:
            raise ValueError("quantity_epsilon must be non-negative")
        self.position_reader = position_reader
        self.open_orders_reader = open_orders_reader
        self.quantity_epsilon = float(quantity_epsilon)

    def reconcile(
        self,
        symbol: str,
        ledger: AssetLotLedger,
        *,
        local_open_orders: int = 0,
    ) -> ReconciliationResult:
        broker_qty = float(self.position_reader(symbol))
        local_qty = float(ledger.open_share_count)
        broker_open_orders = int(self.open_orders_reader(symbol)) if self.open_orders_reader else 0
        matched = abs(broker_qty - local_qty) <= self.quantity_epsilon and broker_open_orders == int(local_open_orders)
        result = ReconciliationResult(
            symbol=str(symbol),
            local_position_qty=local_qty,
            broker_position_qty=broker_qty,
            local_open_orders=int(local_open_orders),
            broker_open_orders=broker_open_orders,
            matched=matched,
            reason="matched" if matched else "broker/local state mismatch",
        )
        if not matched:
            raise ReconciliationError(
                f"reconciliation failed for {symbol}: local_qty={local_qty}, "
                f"broker_qty={broker_qty}, local_open_orders={int(local_open_orders)}, "
                f"broker_open_orders={broker_open_orders}"
            )
        return result
