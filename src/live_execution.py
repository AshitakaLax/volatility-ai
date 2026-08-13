"""Live execution adapter using the same strategy decision-cycle as backtests."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
import logging
from typing import Any, Callable, Protocol

from src.config import BacktestConfig
from src.exceptions import ConfigurationError, ReconciliationError
from src.ledger import AssetLotLedger, InventoryLot
from src.market_context import MarketContext
from src.order_management_system import Mode, OrderManagementSystem
from src.persistence import SQLiteStateStore
from src.promotion_gate import PromotionGate
from src.risk_manager import RiskManager
from src.secrets import LiveCredentials, load_live_credentials
from src.size_calculators import SizingStrategy
from src.live_circuit_breaker import LiveCircuitBreaker, SQLiteCircuitBreakerStore

logger = logging.getLogger("LiveExecution")


class LiveBroker(Protocol):
    def submit_buy(self, symbol: str, trade_value: float) -> Any: ...
    def submit_sell(self, symbol: str, qty: float, target_price: float) -> Any: ...


class RuntimeState(str, Enum):
    STARTING = "STARTING"
    LOAD_CONFIG = "LOAD_CONFIG"
    LOAD_STATE = "LOAD_STATE"
    CONNECT_BROKER = "CONNECT_BROKER"
    RECONCILE = "RECONCILE"
    VALIDATE_DATA_CLOCK = "VALIDATE_DATA/CLOCK"
    READY = "READY"
    SHUTTING_DOWN = "SHUTTING_DOWN"
    RECONCILIATION_REQUIRED = "RECONCILIATION_REQUIRED"
    STOPPED = "STOPPED"


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
    current_qty = float(order.filled_qty or 0.0)
    current_avg = float(order.filled_avg_price or 0.0)
    current_notional = current_qty * current_avg
    new_qty = current_qty - previous.qty
    new_notional = current_notional - previous.notional
    if new_qty < -1e-12 or new_notional < -1e-9:
        raise ReconciliationError(f"cumulative fill decreased: previous_qty={previous.qty}, current_qty={current_qty}, previous_notional={previous.notional}, current_notional={current_notional}")
    if new_qty <= 1e-12:
        return 0.0, 0.0, 0.0
    return new_qty, new_notional, new_notional / new_qty


class LiveExecutionLoop:
    LIVE_TICK_MAX_MOVE_PCT = 0.15

    def __init__(self, config: BacktestConfig, strategy: SizingStrategy, risk_manager: RiskManager | None = None, *, broker_factory: Callable[[LiveCredentials], LiveBroker] | None = None, oms: OrderManagementSystem | None = None, state_store: SQLiteStateStore | None = None, state_path: str | None = None, broker_position_qty: Callable[[str], float] | None = None, promotion_gate: PromotionGate | None = None, circuit_breaker: LiveCircuitBreaker | None = None, circuit_store: SQLiteCircuitBreakerStore | None = None) -> None:
        config.validate()
        if not config.live.enabled:
            raise ConfigurationError("live.enabled=False: live execution is disabled")
        if not config.live.paper_trading:
            if promotion_gate is None:
                raise ConfigurationError("live capital requires a passed paper-trading promotion gate")
            promotion_gate.require_live_promotion()
        self.config = config
        self.strategy = strategy
        self.circuit_store = circuit_store
        self.circuit_breaker = circuit_breaker or LiveCircuitBreaker()
        self.risk_manager = risk_manager or RiskManager(max_concurrent_lots=config.risk.max_concurrent_lots, max_total_exposure=config.risk.max_total_exposure, circuit_breaker=self.circuit_breaker)
        self._broker_factory = broker_factory
        self.oms = oms or OrderManagementSystem(mode=Mode.LIVE)
        self.broker: LiveBroker | None = None
        self.state_store = state_store or (SQLiteStateStore(state_path) if state_path else None)
        self._broker_position_qty = broker_position_qty
        self.ledger = AssetLotLedger()
        self.last_buy_price = None
        self._started = False
        self.runtime_state = RuntimeState.STARTING
        self._fill_state: dict[str, _CumulativeFill] = {}
        self.reconciliation_required = False
        self._last_known_good_price: float | None = None
        self.rejected_tick_count = 0

    def _transition(self, state: RuntimeState) -> None:
        self.runtime_state = state
        logger.info("Live runtime state transition: %s", state.value)
        if self.state_store is not None:
            self.state_store.record_audit(
                f"runtime:{datetime.now(timezone.utc).isoformat()}",
                "STARTUP_SHUTDOWN",
                {"deployment_id": getattr(self.config, "deployment_id", "unknown"), "runtime_state": state.value},
            )

    def start(self) -> None:
        self._transition(RuntimeState.STARTING)
        self._transition(RuntimeState.LOAD_CONFIG)
        credentials = load_live_credentials()
        self._transition(RuntimeState.LOAD_STATE)
        if self.circuit_store is not None:
            self.circuit_breaker.state = self.circuit_store.load()
        if self.state_store is not None:
            self.ledger = self.state_store.load_open_lots()
            if self.ledger.open_lots:
                self.last_buy_price = self.ledger.open_lots[-1].buy_price
        self._transition(RuntimeState.CONNECT_BROKER)
        if self._broker_factory is not None:
            self.broker = self._broker_factory(credentials)
        self._transition(RuntimeState.RECONCILE)
        if self.state_store is not None:
            if self._broker_position_qty is not None:
                self.state_store.reconcile_position(self.ledger, self._broker_position_qty(self.config.backtest.symbol))
            elif self.ledger.open_lots and self.broker is not None:
                self.reconciliation_required = True
                self._transition(RuntimeState.RECONCILIATION_REQUIRED)
                raise ReconciliationError("durable ledger has open lots but no broker position reconciliation callback was supplied")
        self._transition(RuntimeState.VALIDATE_DATA_CLOCK)
        self._started = True
        self.reconciliation_required = False
        self._transition(RuntimeState.READY)

    def shutdown(self, *, settle: Callable[[], bool] | None = None, max_wait_seconds: float = 30.0) -> RuntimeState:
        if self.runtime_state in {RuntimeState.STOPPED, RuntimeState.RECONCILIATION_REQUIRED}:
            return self.runtime_state
        if max_wait_seconds < 0:
            raise ValueError("max_wait_seconds must be non-negative")
        self._transition(RuntimeState.SHUTTING_DOWN)
        self._started = False
        settled = True if settle is None else bool(settle())
        self.persist_state()
        if self.state_store is not None:
            self.state_store.record_audit(
                f"shutdown:{datetime.now(timezone.utc).isoformat()}",
                "STARTUP_SHUTDOWN",
                {"deployment_id": getattr(self.config, "deployment_id", "unknown"), "runtime_state": RuntimeState.SHUTTING_DOWN.value, "settled": settled, "max_wait_seconds": float(max_wait_seconds)},
            )
        if not settled:
            self.reconciliation_required = True
            self._transition(RuntimeState.RECONCILIATION_REQUIRED)
            return self.runtime_state
        self._transition(RuntimeState.STOPPED)
        if self.state_store is not None:
            self.state_store.close()
        return self.runtime_state

    def evaluate_circuit_breaker(self, drawdown: float) -> bool:
        halted = self.circuit_breaker.evaluate(float(drawdown))
        if halted and self.circuit_store is not None:
            self.circuit_store.save(self.circuit_breaker.state)
        return halted

    def reset_circuit_breaker(self) -> None:
        self.circuit_breaker.reset()
        if self.circuit_store is not None:
            self.circuit_store.save(self.circuit_breaker.state)

    def persist_state(self) -> None:
        if self.state_store is not None:
            self.state_store.persist_ledger(self.ledger)

    def build_context(self, *, timestamp: datetime, open: float, high: float, low: float, close: float, cash: float, equity: float, peak_equity: float, drawdown: float, open_lot_count: int, bar_index: int, time_of_day_flag: int = 0, is_macro_event_day: bool = False, macro_surprise_factor: float = 0.0) -> MarketContext:
        if timestamp.tzinfo is None:
            timestamp = timestamp.replace(tzinfo=timezone.utc)
        return MarketContext(timestamp=timestamp, open=float(open), high=float(high), low=float(low), close=float(close), cash=float(cash), equity=float(equity), peak_equity=float(peak_equity), drawdown=float(drawdown), open_lot_count=int(open_lot_count), bar_index=int(bar_index), time_of_day_flag=int(time_of_day_flag), is_macro_event_day=bool(is_macro_event_day), macro_surprise_factor=float(macro_surprise_factor))

    def validate_tick(self, price: float) -> bool:
        price = float(price)
        if price <= 0.0:
            self.rejected_tick_count += 1
            logger.warning("Rejected live tick: non-positive price price=%s", price)
            return False
        previous = self._last_known_good_price
        if previous is not None:
            move = abs(price / previous - 1.0)
            if move > self.LIVE_TICK_MAX_MOVE_PCT:
                self.rejected_tick_count += 1
                logger.warning("Rejected live tick: implausible price move previous=%s price=%s move_pct=%.4f threshold=%.4f", previous, price, move, self.LIVE_TICK_MAX_MOVE_PCT)
                return False
        self._last_known_good_price = price
        return True

    def process_tick(self, context: MarketContext, *, step: float, last_buy_price: float) -> LiveDecision | None:
        if not self.validate_tick(context.close):
            return None
        return self.decision_cycle(context, step=step, last_buy_price=last_buy_price)

    def decision_cycle(self, context: MarketContext, *, step: float, last_buy_price: float) -> LiveDecision:
        if not self._started or self.runtime_state is not RuntimeState.READY:
            raise RuntimeError("live execution is not READY")
        if self.reconciliation_required:
            raise ReconciliationError("live execution is halted pending reconciliation")
        self.strategy.record_tick(context)
        triggered = self.strategy._check_grid_trigger(context, last_buy_price, step)
        if not triggered:
            return LiveDecision(context=context, triggered=False)
        proposed = self.strategy.calculate_trade_value(context)
        self.evaluate_circuit_breaker(context.drawdown)
        clamped = self.risk_manager.clamp_trade_value(proposed, context.equity, context.cash, context.open_lot_count)
        return LiveDecision(context=context, triggered=True, proposed_trade_value=float(proposed), clamped_trade_value=float(clamped))

    def apply_sell_fill(self, order: Any, lot: InventoryLot, ledger: AssetLotLedger | None = None, cash: float = 0.0, *, execution_cost: float = 0.0) -> tuple[float, float]:
        ledger = ledger or self.ledger
        order_id = str(order.id)
        state = self._fill_state.setdefault(order_id, _CumulativeFill())
        new_qty, new_notional, new_avg = _cumulative_fill_delta(order, state)
        if new_qty <= 0.0:
            return float(cash), 0.0
        if new_qty > lot.shares + 1e-12:
            raise ReconciliationError(f"fill qty {new_qty} exceeds remaining lot shares {lot.shares}")
        event_id = f"fill:{order_id}:{float(order.filled_qty):.12g}"
        if self.state_store is not None:
            claimed, _ = self.state_store.mark_processed(event_id)
            if not claimed:
                return float(cash), 0.0
        applied, _ = self.oms.process_event_once(event_id, lambda: ledger.close_lot(lot, sell_qty=new_qty, execution_price=new_avg, completed=False))
        if not applied:
            return float(cash), 0.0
        state.qty = float(order.filled_qty)
        state.notional = float(order.filled_qty) * float(order.filled_avg_price or 0.0)
        if self.state_store is not None:
            self.state_store.persist_ledger(ledger)
            self.state_store.record_audit(event_id, "fill", {"order_id": order_id, "side": "sell", "qty": new_qty, "notional": new_notional})
        return float(cash) + new_notional - float(execution_cost), new_notional

    def apply_buy_fill(self, order: Any, symbol: str, profit_target: float, ledger: AssetLotLedger | None = None, cash: float = 0.0, *, execution_cost: float = 0.0) -> tuple[float, InventoryLot | None]:
        ledger = ledger or self.ledger
        order_id = str(order.id)
        state = self._fill_state.setdefault(order_id, _CumulativeFill())
        new_qty, new_notional, new_avg = _cumulative_fill_delta(order, state)
        if new_qty <= 0.0:
            return float(cash), None
        event_id = f"fill:{order_id}:{float(order.filled_qty):.12g}"
        if self.state_store is not None:
            claimed, _ = self.state_store.mark_processed(event_id)
            if not claimed:
                return float(cash), None
        applied, lot = self.oms.process_event_once(event_id, lambda: ledger.register_buy(order_id, symbol, new_avg, new_qty, profit_target))
        if not applied:
            return float(cash), None
        state.qty = float(order.filled_qty)
        state.notional = float(order.filled_qty) * float(order.filled_avg_price or 0.0)
        if self.state_store is not None:
            self.state_store.persist_ledger(ledger)
            self.state_store.record_audit(event_id, "fill", {"order_id": order_id, "side": "buy", "qty": new_qty, "notional": new_notional})
        return float(cash) - new_notional - float(execution_cost), lot

    def submit_buy(self, decision: LiveDecision) -> Any:
        if self.broker is None:
            raise RuntimeError("live broker is not connected")
        if self.runtime_state is not RuntimeState.READY:
            return None
        if self.circuit_breaker.halted or decision.clamped_trade_value <= 0:
            return None
        return self.broker.submit_buy(self.config.backtest.symbol, decision.clamped_trade_value)

    def submit_sell(self, qty: float, target_price: float) -> Any:
        if self.broker is None:
            raise RuntimeError("live broker is not connected")
        return self.broker.submit_sell(self.config.backtest.symbol, float(qty), float(target_price))
