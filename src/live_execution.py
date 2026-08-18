"""Live execution adapter using the same strategy decision-cycle as backtests."""

from __future__ import annotations

import dataclasses
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
import logging
from typing import Any, Callable, Protocol

from src.audit import (
    AuditEvent,
    MarketContextPayload,
    StrategyDecisionPayload,
    RiskDecisionPayload,
    OrderIntentPayload,
    OrderStatusPayload,
    FillPayload,
    LedgerMutationPayload,
    ReconciliationPayload,
    RiskHaltPayload,
    StartupShutdownPayload,
    canonical_event_id,
    generate_event_id,
)
from src.config import BacktestConfig
from src.cost_models import TransactionCostModel, ZeroCostModel
from src.exceptions import ConfigurationError, ReconciliationError, SellEconomicsError
from src.ledger import AssetLotLedger, InventoryLot, validate_sell
from src.market_context import MarketContext
from src.order_management_system import Mode, OrderManagementSystem
from src.persistence import SQLiteStateStore
from src.promotion_gate import PromotionGate
from src.risk_manager import RiskManager
from src.secrets import LiveCredentials, load_live_credentials
from src.size_calculators import SizingStrategy
from src.live_circuit_breaker import LiveCircuitBreaker, SQLiteCircuitBreakerStore
from src.fill_cursor import FillCursor

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
    decision_id: str | None = None


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
        self._fill_state: dict[str, FillCursor] = {}
        self.reconciliation_required = False
        self._last_known_good_price: float | None = None
        self._last_market_event_id: str | None = None
        self.rejected_tick_count = 0
        self.no_loss_guard_violations: int = 0

    def _record_audit(self, event_type: str, payload_obj: Any, event_id: str | None = None) -> AuditEvent | None:
        if self.state_store is None:
            return None
        event = AuditEvent(event_id=event_id or generate_event_id(), timestamp=datetime.now(timezone.utc).isoformat(), event_type=event_type, schema_version=1, deployment_id=getattr(self.config, "deployment_id", "unknown"), payload=dataclasses.asdict(payload_obj) if dataclasses.is_dataclass(payload_obj) else payload_obj)
        self.state_store.record_audit(event)
        return event

    def _record_canonical_audit(self, event_type: str, payload_factory: Callable[[str], Any], *, strategy_id: str, symbol: str, market_event_id: str | int, decision_type: str) -> AuditEvent | None:
        if self.state_store is None:
            return None
        deployment_id = getattr(self.config, "deployment_id", "unknown")
        timestamp = datetime.now(timezone.utc).isoformat()
        def builder(sequence: int) -> AuditEvent:
            event_id = canonical_event_id(deployment_id=deployment_id, strategy_id=strategy_id, symbol=symbol, market_event_id=market_event_id, decision_type=decision_type, sequence_number=sequence)
            payload = payload_factory(event_id)
            return AuditEvent(event_id=event_id, timestamp=timestamp, event_type=event_type, schema_version=1, deployment_id=deployment_id, payload=dataclasses.asdict(payload) if dataclasses.is_dataclass(payload) else payload, sequence=sequence)
        event, _ = self.state_store.record_audit_builder(builder)
        return event

    def _record_order_intent(self, *, decision_id: str, symbol: str, side: str, quantity: float, limit_price: float | None, market_event_id: str | int) -> AuditEvent | None:
        return self._record_canonical_audit("ORDER_INTENT", lambda event_id: OrderIntentPayload(intent_id=event_id, decision_id=decision_id, symbol=symbol, side=side, quantity=float(quantity), limit_price=limit_price), strategy_id=self.config.strategy.strategy_id, symbol=symbol, market_event_id=market_event_id, decision_type="ORDER_INTENT")

    def _transition(self, state: RuntimeState) -> None:
        self.runtime_state = state
        logger.info("Live runtime state transition: %s", state.value)
        self._record_audit("STARTUP_SHUTDOWN", StartupShutdownPayload(deployment_id=getattr(self.config, "deployment_id", "unknown"), runtime_state=state.value, reconciliation_result=None), event_id=f"runtime:{datetime.now(timezone.utc).isoformat()}")

    def start(self) -> None:
        self._transition(RuntimeState.STARTING)
        self._transition(RuntimeState.LOAD_CONFIG)
        credentials = load_live_credentials()
        self._transition(RuntimeState.LOAD_STATE)
        if self.circuit_store is not None:
            self.circuit_breaker.state = self.circuit_store.load()
        if self.state_store is not None:
            self.ledger = self.state_store.load_open_lots()
            self._fill_state = {order_id: FillCursor(qty, notional) for order_id, (qty, notional) in self.state_store.load_fill_cursors().items()}
            if self.ledger.open_lots:
                self.last_buy_price = self.ledger.open_lots[-1].buy_price
        self._transition(RuntimeState.CONNECT_BROKER)
        if self._broker_factory is not None:
            self.broker = self._broker_factory(credentials)
        self._transition(RuntimeState.RECONCILE)
        if self.state_store is not None and self._broker_position_qty is not None:
            b_qty = float(self._broker_position_qty(self.config.backtest.symbol))
            l_qty = float(self.ledger.open_share_count)
            matched = abs(b_qty - l_qty) <= 1e-9
            self._record_audit("RECONCILIATION", ReconciliationPayload(correlation_id="startup-reconcile", local_state_summary={"position_qty": l_qty}, broker_state_summary={"position_qty": b_qty}, resolution="matched" if matched else "mismatch"))
            self.state_store.reconcile_position(self.ledger, b_qty)
        self._transition(RuntimeState.VALIDATE_DATA_CLOCK)
        self._started = True
        self.reconciliation_required = False
        self._transition(RuntimeState.READY)

    def persist_state(self) -> None:
        if self.state_store is not None:
            self.state_store.persist_ledger(self.ledger)
            for order_id, cursor in self._fill_state.items():
                cursor.persist(self.state_store, order_id)

    def apply_sell_fill(self, order: Any, lot: InventoryLot, ledger: AssetLotLedger | None = None, cash: float = 0.0, *, execution_cost: float = 0.0, cost_model: TransactionCostModel | None = None) -> tuple[float, float]:
        cost_model = cost_model or ZeroCostModel()
        ledger = ledger or self.ledger
        order_id = str(order.id)
        cursor = self._fill_state.setdefault(order_id, FillCursor())
        current_qty = float(order.filled_qty or 0.0)
        current_avg = float(order.filled_avg_price or 0.0)
        current_notional = current_qty * current_avg
        new_qty, new_notional = cursor.delta(current_qty, current_notional)
        if new_qty <= 0.0:
            return float(cash), 0.0
        if new_qty > lot.shares + 1e-12:
            raise ReconciliationError(f"fill qty {new_qty} exceeds remaining lot shares {lot.shares}")
        event_id = f"fill:{order_id}:{current_qty:.12g}"
        if self.state_store is not None and not self.state_store.mark_processed(event_id)[0]:
            return float(cash), 0.0
        try:
            econ = validate_sell(lot, new_qty, new_notional / new_qty, cost_model)
            net_proceeds = econ.net_sell_proceeds
        except SellEconomicsError as exc:
            logger.warning("No-loss guard violation at fill boundary (fill already executed): %s", exc)
            self.no_loss_guard_violations += 1
            net_proceeds = new_notional - float(execution_cost)
        applied, _ = self.oms.process_event_once(event_id, lambda: ledger.close_lot(lot, sell_qty=new_qty, execution_price=new_notional / new_qty, completed=False))
        if not applied:
            return float(cash), 0.0
        cursor.advance(current_qty, current_notional)
        if self.state_store is not None:
            cursor.persist(self.state_store, order_id)
        self._record_audit("ORDER_STATUS", OrderStatusPayload(intent_id=order_id, broker_order_id=order_id, status="FILLED" if current_qty >= lot.shares - 1e-9 else "PARTIALLY_FILLED", cumulative_filled_qty=current_qty), event_id=f"{event_id}:status")
        self._record_audit("FILL", FillPayload(fill_id=event_id, order_id=order_id, incremental_fill_qty=new_qty, cumulative_filled_qty=current_qty, price=new_notional / new_qty, fees=execution_cost, timestamp=datetime.now(timezone.utc).isoformat()), event_id=event_id)
        self._record_audit("LEDGER_MUTATION", LedgerMutationPayload(event_id=event_id, lot_id=lot.order_id, mutation_type="close_lot", quantity_delta=-new_qty, cash_delta=net_proceeds), event_id=f"{event_id}:ledger")
        if self.state_store is not None:
            self.state_store.persist_ledger(ledger)
        return float(cash) + net_proceeds, net_proceeds

    def apply_buy_fill(self, order: Any, symbol: str, profit_target: float, ledger: AssetLotLedger | None = None, cash: float = 0.0, *, execution_cost: float = 0.0) -> tuple[float, InventoryLot | None]:
        ledger = ledger or self.ledger
        order_id = str(order.id)
        cursor = self._fill_state.setdefault(order_id, FillCursor())
        current_qty = float(order.filled_qty or 0.0)
        current_avg = float(order.filled_avg_price or 0.0)
        current_notional = current_qty * current_avg
        new_qty, new_notional = cursor.delta(current_qty, current_notional)
        if new_qty <= 0.0:
            return float(cash), None
        event_id = f"fill:{order_id}:{current_qty:.12g}"
        if self.state_store is not None and not self.state_store.mark_processed(event_id)[0]:
            return float(cash), None
        applied, lot = self.oms.process_event_once(event_id, lambda: ledger.register_buy(order_id, symbol, new_notional / new_qty, new_qty, profit_target))
        if not applied:
            return float(cash), None
        cursor.advance(current_qty, current_notional)
        if self.state_store is not None:
            cursor.persist(self.state_store, order_id)
        self._record_audit("ORDER_STATUS", OrderStatusPayload(intent_id=order_id, broker_order_id=order_id, status="FILLED" if current_qty > 0 else "PARTIALLY_FILLED", cumulative_filled_qty=current_qty), event_id=f"{event_id}:status")
        self._record_audit("FILL", FillPayload(fill_id=event_id, order_id=order_id, incremental_fill_qty=new_qty, cumulative_filled_qty=current_qty, price=new_notional / new_qty, fees=execution_cost, timestamp=datetime.now(timezone.utc).isoformat()), event_id=event_id)
        self._record_audit("LEDGER_MUTATION", LedgerMutationPayload(event_id=event_id, lot_id=order_id, mutation_type="register_buy", quantity_delta=new_qty, cash_delta=-(new_notional + execution_cost)), event_id=f"{event_id}:ledger")
        if self.state_store is not None:
            self.state_store.persist_ledger(ledger)
        return float(cash) - new_notional - float(execution_cost), lot
