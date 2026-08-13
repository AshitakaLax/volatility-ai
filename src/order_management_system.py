"""
Order management system.

Original, from-scratch implementation (no existing
src/order_management_system.py was available to read -- see the chat
this was produced in).

Targets exactly optimization_controller.py's current calling convention:

    oms = OrderManagementSystem(mode="SIMULATION")
    order = oms.execute_buy("TQQQ", trade_value, current_price)
    exec_res = oms.execute_sell(lot.symbol, lot.shares, lot.target_sell_price)

SIMULATION mode fills completely, at the requested price, with no
slippage or transaction-cost modeling -- those are separately specced
(TransactionCostModel/DynamicSlippageModel, architecture_overview.md
Sections 5.3/5.5, Phase 2/7 tasks) and are not implemented here.

Every returned dict includes a "status" field using OrderStatus below,
matching implementation_task_specs.md Task 1.5's "exact fill contract"
(only FILLED may mutate cash/ledger; NEW/ACCEPTED/PENDING/
PARTIALLY_FILLED/CANCELED/REJECTED/EXPIRED must not be). This mirrors
the *names* Task 1.5 references from Alpaca's real OrderStatus enum
without taking a hard alpaca-py dependency here -- optimization_controller.py
doesn't check this field yet (that check is Task 1.5's job), so
including it now is forward-compatible and a no-op for current behavior.

LIVE mode is not implemented: real broker execution needs Phase 7's
broker adapter and real Alpaca credentials, well outside this file's
scope. Calling execute_buy/execute_sell in LIVE mode raises
NotImplementedError rather than silently behaving like SIMULATION.
"""

from __future__ import annotations

from enum import Enum

from src.exceptions import ConfigurationError


class Mode(str, Enum):
    """Subclasses str so Mode.SIMULATION == "SIMULATION" and
    Mode.LIVE == "LIVE" -- every existing bare-string mode="SIMULATION"
    call site (and the `mode not in ("SIMULATION", "LIVE")` /
    `self.mode == "LIVE"` checks below) keeps working unmodified
    whether callers pass the enum or the string. Added to unblock
    src/live_execution.py, pushed directly to main mid-session with
    `from src.order_management_system import Mode` -- see the chat
    this was produced in."""

    SIMULATION = "SIMULATION"
    LIVE = "LIVE"


class OrderStatus:
    """String constants mirroring the Alpaca OrderStatus values named in
    implementation_task_specs.md Task 1.5's fill contract. Not the real
    alpaca-py enum -- see module docstring."""

    NEW = "NEW"
    ACCEPTED = "ACCEPTED"
    PENDING = "PENDING"
    PARTIALLY_FILLED = "PARTIALLY_FILLED"
    FILLED = "FILLED"
    CANCELED = "CANCELED"
    REJECTED = "REJECTED"
    EXPIRED = "EXPIRED"


class OrderManagementSystem:
    def __init__(self, mode: str = "SIMULATION"):
        if mode not in ("SIMULATION", "LIVE"):
            raise ConfigurationError(f"mode must be 'SIMULATION' or 'LIVE', got {mode!r}")
        self.mode = mode
        self._order_seq = 0

    def _next_order_id(self) -> str:
        self._order_seq += 1
        return f"SIM-{self._order_seq:06d}"

    def execute_buy(self, symbol: str, trade_value: float, price: float) -> dict:
        """Buy trade_value dollars of symbol at price. Returns qty as
        trade_value / price (fractional shares -- optimization_controller.py
        does not round this)."""
        if self.mode == "LIVE":
            raise NotImplementedError(
                "LIVE mode needs a real Alpaca broker adapter (Phase 7) -- not implemented here."
            )
        if trade_value <= 0:
            raise ValueError(f"trade_value must be positive, got {trade_value}")
        if price <= 0:
            raise ValueError(f"price must be positive, got {price}")

        qty = trade_value / price
        return {
            "id": self._next_order_id(),
            "symbol": symbol,
            "qty": qty,
            "filled_qty": qty,
            "filled_avg_price": price,
            "status": OrderStatus.FILLED,
        }

    def execute_sell(self, symbol: str, qty: float, price: float) -> dict:
        """Sell qty shares of symbol at price. Fills completely."""
        if self.mode == "LIVE":
            raise NotImplementedError(
                "LIVE mode needs a real Alpaca broker adapter (Phase 7) -- not implemented here."
            )
        if qty <= 0:
            raise ValueError(f"qty must be positive, got {qty}")
        if price <= 0:
            raise ValueError(f"price must be positive, got {price}")

        return {
            "id": self._next_order_id(),
            "symbol": symbol,
            "qty": qty,
            "filled_qty": qty,
            "filled_avg_price": price,
            "status": OrderStatus.FILLED,
        }
