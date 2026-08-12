"""Live execution adapter using the same strategy decision-cycle as backtests.

Broker I/O is deliberately injected so importing this module never opens a
network connection. Credentials are loaded before a broker adapter can be
constructed.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Callable, Protocol

from src.config import BacktestConfig
from src.exceptions import ConfigurationError, ReconciliationError
from src.ledger import AssetLotLedger, InventoryLot
from src.market_context import MarketContext
from src.order_management_system import Mode, OrderManagementSystem
from src.risk_manager import RiskManager
from src.secrets import LiveCredentials, load_live_credentials
from src.size_calculators import SizingStrategy


class LiveBroker(Protocol):
    def submit_buy(self, symbol: str, trade_value: float) -> Any: ...
    def submit_sell(self, symbol: str, qty: float, target_price: float) -> Any: ...


@dataclass(frozen=True)
class LiveDecision:
    context: MarketContext
    triggered: bool
    proposed_trade_value: float = 0.0
    clamped_trade_value: float = 0.0


@dataclass
class _CumulativeFill:
    qty: float = 0.0
    notional: float = 0.0


def _cumulative_fill_delta(order: Any, previous: _CumulativeFill) -> tuple[float, float, float]:
    """Calculate an incremental fill from broker-reported cumulative totals."""
    current_qty = float(order.filled_qty or 0.0)
    current_avg = float(order.filled_avg_price or 0.0)
    current_notional = current_qty * current_avg
    new_qty = current_qty - previous.qty
    new_notional = current_notional - previous.notional
    if new_qty < -1e-12 or new_notional < -1e-9:
        raise ReconciliationError(
            f"cumulative fill decreased: previous_qty={previous.qty}, current_qty={current_qty}, "
            f"previous_notional={previous.notional}, current_notional={current_notional}"
        )
    if new_qty <= 1e-12:
        return 0.0, 0.0, 0.0
    if new_notional < -1e-9:
        raise ReconciliationError("cumulative fill notional decreased")
    return new_qty, new_notional, new_notional / new_qty


class LiveExecutionLoop:
    """Drive live ticks through the canonical strategy-facing contract."""

    def __init__(self, config: BacktestConfig, strategy: SizingStrategy, risk_manager: RiskManager | None = None, *, broker_factory: Callable[[LiveCredentials], LiveBroker] | None = None, oms: OrderManagementSystem | None = None) -> None:
        config.validate()
        if not config.live.enabled:
            raise ConfigurationError("live.enabled=False: live execution is disabled")
        self.config = config
        self.strategy = strategy
        self.risk_manager = risk_manager or RiskManager(max_concurrent_lots=config.risk.max_concurrent_lots, max_total_exposure=config.risk.max_total_exposure)
        self._broker_factory = broker_factory
        self.oms = oms or OrderManagementSystem(mode=Mode.LIVE)
        self.broker: LiveBroker | None = None
        self.last_buy_price = None
        self._started = False
        self._fill_state: dict[str, _CumulativeFill] = {}

    def start(self) -> None:
        """Validate credentials before attempting any broker/WebSocket work."""
        credentials = load_live_credentials()
        if self._broker_factory is not None:
            self.broker = self._broker_factory(credentials)
        self._started = True

    def build_context(self, *, timestamp: datetime, open: float, high: float, low: float, close: float, cash: float, equity: float, peak_equity: float, drawdown: float, open_lot_count: int, bar_index: int, time_of_day_flag: int = 0, is_macro_event_day: bool = False, macro_surprise_factor: float = 0.0) -> MarketContext:
        if timestamp.tzinfo is None:
            timestamp = timestamp.replace(tzinfo=timezone.utc)
        return MarketContext(timestamp=timestamp, open=float(open), high=float(high), low=float(low), close=float(close), cash=float(cash), equity=float(equity), peak_equity=float(peak_equity), drawdown=float(drawdown), open_lot_count=int(open_lot_count), bar_index=int(bar_index), time_of_day_flag=int(time_of_day_flag), is_macro_event_day=bool(is_macro_event_day), macro_surprise_factor=float(macro_surprise_factor))

    def decision_cycle(self, context: MarketContext, *, step: float, last_buy_price: float) -> LiveDecision:
        if not self._started:
            raise RuntimeError("live execution has not been started")
        self.strategy.record_tick(context)
        triggered = self.strategy._check_grid_trigger(context, last_buy_price, step)
        if not triggered:
            return LiveDecision(context=context, triggered=False)
        proposed = self.strategy.calculate_trade_value(context)
        clamped = self.risk_manager.clamp_trade_value(proposed, context.equity, context.cash, context.open_lot_count)
        return LiveDecision(context=context, triggered=True, proposed_trade_value=float(proposed), clamped_trade_value=float(clamped))

    def apply_sell_fill(self, order: Any, lot: InventoryLot, ledger: AssetLotLedger, cash: float, *, execution_cost: float = 0.0) -> tuple[float, float]:
        """Apply only the newly confirmed cumulative sell fill to cash/ledger."""
        order_id = str(order.id)
        state = self._fill_state.setdefault(order_id, _CumulativeFill())
        new_qty, new_notional, new_avg = _cumulative_fill_delta(order, state)
        if new_qty <= 0.0:
            return float(cash), 0.0
        if new_qty > lot.shares + 1e-12:
            raise ReconciliationError(f"fill qty {new_qty} exceeds remaining lot shares {lot.shares}")
        applied, _ = self.oms.process_event_once(f"fill:{order_id}:{float(order.filled_qty):.12g}", lambda: ledger.close_lot(lot, sell_qty=new_qty, execution_price=new_avg, completed=False))
        if not applied:
            return float(cash), 0.0
        state.qty = float(order.filled_qty)
        state.notional = float(order.filled_qty) * float(order.filled_avg_price or 0.0)
        return float(cash) + new_notional - float(execution_cost), new_notional

    def apply_buy_fill(self, order: Any, symbol: str, profit_target: float, ledger: AssetLotLedger, cash: float, *, execution_cost: float = 0.0) -> tuple[float, InventoryLot | None]:
        """Register only the newly confirmed cumulative buy fill."""
        order_id = str(order.id)
        state = self._fill_state.setdefault(order_id, _CumulativeFill())
        new_qty, new_notional, new_avg = _cumulative_fill_delta(order, state)
        if new_qty <= 0.0:
            return float(cash), None
        applied, lot = self.oms.process_event_once(f"fill:{order_id}:{float(order.filled_qty):.12g}", lambda: ledger.register_buy(order_id, symbol, new_avg, new_qty, profit_target))
        if not applied:
            return float(cash), None
        state.qty = float(order.filled_qty)
        state.notional = float(order.filled_qty) * float(order.filled_avg_price or 0.0)
        return float(cash) - new_notional - float(execution_cost), lot

    def submit_buy(self, decision: LiveDecision) -> Any:
        if self.broker is None:
            raise RuntimeError("live broker is not connected")
        if decision.clamped_trade_value <= 0:
            return None
        return self.broker.submit_buy(self.config.backtest.symbol, decision.clamped_trade_value)

    def submit_sell(self, qty: float, target_price: float) -> Any:
        if self.broker is None:
            raise RuntimeError("live broker is not connected")
        return self.broker.submit_sell(self.config.backtest.symbol, float(qty), float(target_price))
