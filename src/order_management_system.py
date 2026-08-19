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
    call site keeps working unmodified whether callers pass the enum or
    the string.

    PAPER (Task 7.7) is a first-class third mode, deliberately NOT a
    boolean flag on LIVE: paper trading is the mandatory gate between
    backtest and real capital, and making it a distinct mode means
    reaching LIVE is an explicit, auditable step rather than flipping
    one config value.
    """

    SIMULATION = "SIMULATION"
    PAPER = "PAPER"
    LIVE = "LIVE"


# Modes that never touch real capital.
NON_CAPITAL_MODES = (Mode.SIMULATION, Mode.PAPER)


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
    def __init__(self, mode: str = "SIMULATION", live_capital_promotion=None):
        """Task 7.7: constructing a LIVE (real-capital) OMS requires an
        explicit, passing PromotionEvaluation. There is deliberately no
        boolean "enable_live=True" shortcut -- the caller must hold
        actual evidence that a paper-trading stage was completed and
        met the recorded criteria, which is the whole point of the gate.

        SIMULATION and PAPER need no such evidence; neither touches
        real capital.
        """
        if mode not in ("SIMULATION", "PAPER", "LIVE"):
            raise ConfigurationError(f"mode must be 'SIMULATION', 'PAPER', or 'LIVE', got {mode!r}")
        if mode == "LIVE":
            if live_capital_promotion is None:
                raise ConfigurationError(
                    "Refusing to construct a LIVE (real-capital) OrderManagementSystem without a "
                    "passing paper-trading PromotionEvaluation (Task 7.7). Use mode='PAPER' to "
                    "trade risk-free, or supply the promotion evidence to enable live capital."
                )
            if not getattr(live_capital_promotion, "passed", False):
                raise ConfigurationError(
                    "Refusing to enable live capital: the supplied promotion evaluation did not "
                    f"pass. Unmet criteria: {list(getattr(live_capital_promotion, 'failures', ()))}"
                )
        self.mode = mode
        self.live_capital_promotion = live_capital_promotion
        self._order_seq = 0

    def _next_order_id(self) -> str:
        self._order_seq += 1
        return f"SIM-{self._order_seq:06d}"

    def execute_buy(self, symbol: str, trade_value: float, price: float, client_order_id: str = None) -> dict:
        """Buy trade_value dollars of symbol at price. Returns qty as
        trade_value / price (fractional shares -- optimization_controller.py
        does not round this).

        client_order_id (Task 7.4) is the caller's stable decision_id,
        passed through to the broker for server-side deduplication in
        LIVE mode. Defaults to None so every existing call site is
        unaffected; in SIMULATION mode it is echoed back on the result
        when supplied, and the generated "id" is used otherwise."""
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
            "client_order_id": client_order_id,
            "symbol": symbol,
            "qty": qty,
            "filled_qty": qty,
            "filled_avg_price": price,
            "status": OrderStatus.FILLED,
        }

    def execute_sell(self, symbol: str, qty: float, price: float, client_order_id: str = None) -> dict:
        """Sell qty shares of symbol at price. Fills completely.

        client_order_id: see execute_buy."""
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
            "client_order_id": client_order_id,
            "symbol": symbol,
            "qty": qty,
            "filled_qty": qty,
            "filled_avg_price": price,
            "status": OrderStatus.FILLED,
        }
