"""Restart-safe cumulative broker fill cursor for Task 7.14."""

from __future__ import annotations

from dataclasses import dataclass

from src.exceptions import ReconciliationError
from src.persistence import SQLiteStateStore


@dataclass
class FillCursor:
    """Last durably observed cumulative broker quantity/notional for one order."""

    cumulative_qty: float = 0.0
    cumulative_notional: float = 0.0

    def delta(self, cumulative_qty: float, cumulative_notional: float) -> tuple[float, float]:
        qty = float(cumulative_qty)
        notional = float(cumulative_notional)
        if qty < self.cumulative_qty - 1e-12 or notional < self.cumulative_notional - 1e-9:
            raise ReconciliationError(
                "broker cumulative fill regressed: "
                f"previous_qty={self.cumulative_qty}, current_qty={qty}, "
                f"previous_notional={self.cumulative_notional}, current_notional={notional}"
            )
        delta_qty = qty - self.cumulative_qty
        delta_notional = notional - self.cumulative_notional
        if delta_qty <= 1e-12:
            return 0.0, 0.0
        if delta_notional < -1e-9:
            raise ReconciliationError(
                f"broker cumulative fill notional regressed: previous={self.cumulative_notional}, current={notional}"
            )
        return delta_qty, delta_notional

    def advance(self, cumulative_qty: float, cumulative_notional: float) -> None:
        qty = float(cumulative_qty)
        notional = float(cumulative_notional)
        if qty < self.cumulative_qty - 1e-12 or notional < self.cumulative_notional - 1e-9:
            raise ReconciliationError("cannot advance fill cursor backwards")
        self.cumulative_qty = qty
        self.cumulative_notional = notional

    def persist(self, store: SQLiteStateStore, order_id: str) -> int:
        return store.save_fill_cursor(order_id, self.cumulative_qty, self.cumulative_notional)

    @classmethod
    def load(cls, store: SQLiteStateStore, order_id: str) -> "FillCursor":
        value = store.load_fill_cursor(order_id)
        if value is None:
            return cls()
        return cls(cumulative_qty=value[0], cumulative_notional=value[1])
