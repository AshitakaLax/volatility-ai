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
        self._last_market_event_id: str | None = None
        self.rejected_tick_count = 0
        self.no_loss_guard_violations: int = 0

    def _record_audit(self, event_type: str, payload_obj: Any, event_id: str | None = None) -> AuditEvent | None:
        if self.state_store is None:
            return None
        event = AuditEvent(
            event_id=event_id or generate_event_id(),
            timestamp=datetime.now(timezone.utc).isoformat(),
            event_type=event_type,
            schema_version=1,
            deployment_id=getattr(self.config, "deployment_id", "unknown"),
            payload=dataclasses.asdict(payload_obj) if dataclasses.is_dataclass(payload_obj) else payload_obj,
        )
        self.state_store.record_audit(event)
        return event

    def _record_canonical_audit(self, event_type: str, payload_factory: Callable[[str], Any], *, strategy_id: str, symbol: str, market_event_id: str | int, decision_type: str) -> AuditEvent | None:
        """Persist one canonical v6.1 event using the transaction-owned sequence."""
        if self.state_store is None:
            return None
        deployment_id = getattr(self.config, "deployment_id", "unknown")
        timestamp = datetime.now(timezone.utc).isoformat()

        def builder(sequence: int) -> AuditEvent:
            event_id = canonical_event_id(
                deployment_id=deployment_id,
                strategy_id=strategy_id,
                symbol=symbol,
                market_event_id=market_event_id,
                decision_type=decision_type,
                sequence_number=sequence,
            )
            payload = payload_factory(event_id)
            return AuditEvent(
                event_id=event_id,
                timestamp=timestamp,
                event_type=event_type,
                schema_version=1,
                deployment_id=deployment_id,
                payload=dataclasses.asdict(payload) if dataclasses.is_dataclass(payload) else payload,
                sequence=sequence,
            )

        event, _ = self.state_store.record_audit_builder(builder)
        return event

    def _record_order_intent(self, *, decision_id: str, symbol: str, side: str, quantity: float, limit_price: float | None, market_event_id: str | int) -> AuditEvent | None:
        """Persist an ORDER_INTENT using the same canonical ID scheme as 4.10/7.14."""
        return self._record_canonical_audit(
            "ORDER_INTENT",
            lambda event_id: OrderIntentPayload(
                intent_id=event_id,
                decision_id=decision_id,
                symbol=symbol,
                side=side,
                quantity=float(quantity),
                limit_price=limit_price,
            ),
            strategy_id=self.config.strategy.strategy_id,
            symbol=symbol,
            market_event_id=market_event_id,
            decision_type="ORDER_INTENT",
        )

    def _transition(self, state: RuntimeState) -> None:
        self.runtime_state = state
        logger.info("Live runtime state transition: %s", state.value)
        self._record_audit(
            "STARTUP_SHUTDOWN",
            StartupShutdownPayload(
                deployment_id=getattr(self.config, "deployment_id", "unknown"),
                runtime_state=state.value,
                reconciliation_result=None
            ),
            event_id=f"runtime:{datetime.now(timezone.utc).isoformat()}"
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
                b_qty = float(self._broker_position_qty(self.config.backtest.symbol))
                l_qty = float(self.ledger.open_share_count)
                matched = abs(b_qty - l_qty) <= 1e-9
                self._record_audit(
                    "RECONCILIATION",
                    ReconciliationPayload(
                        correlation_id="startup-reconcile",
                        local_state_summary={"position_qty": l_qty},
                        broker_state_summary={"position_qty": b_qty},
                        resolution="matched" if matched else "mismatch"
                    )
                )
                self.state_store.reconcile_position(self.ledger, b_qty)
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
        self._record_audit(
            "STARTUP_SHUTDOWN",
            StartupShutdownPayload(
                deployment_id=getattr(self.config, "deployment_id", "unknown"),
                runtime_state=RuntimeState.SHUTTING_DOWN.value,
                reconciliation_result=f"settled={settled}"
            ),
            event_id=f"shutdown:{datetime.now(timezone.utc).isoformat()}"
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
        was_halted = self.circuit_breaker.halted
        halted = self.circuit_breaker.evaluate(float(drawdown))
        if halted != was_halted:
            self._record_audit("RISK_HALT", RiskHaltPayload(
                halt_reason="drawdown_exceeded" if halted else "reset",
                previous_state="halted" if was_halted else "active",
                new_state="halted" if halted else "active"
            ))
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

        symbol = self.config.backtest.symbol
        strategy_id = self.config.strategy.strategy_id
        market_event_id = str(context.bar_index)
        self._last_market_event_id = market_event_id
        market_event = self._record_canonical_audit(
            "MARKET_CONTEXT",
            lambda _event_id: MarketContextPayload(
                timestamp=context.timestamp.isoformat(),
                symbol=symbol,
                OHLCV={"open": context.open, "high": context.high, "low": context.low, "close": context.close, "volume": 0.0},
                bar_event_id=market_event_id,
            ),
            strategy_id=strategy_id,
            symbol=symbol,
            market_event_id=market_event_id,
            decision_type="MARKET_CONTEXT",
        )

        self.strategy.record_tick(context)
        triggered = self.strategy._check_grid_trigger(context, last_buy_price, step)
        proposed = float(self.strategy.calculate_trade_value(context)) if triggered else 0.0

        strategy_event = self._record_canonical_audit(
            "STRATEGY_DECISION",
            lambda event_id: StrategyDecisionPayload(
                decision_id=event_id,
                strategy_id=strategy_id,
                proposed_action="BUY" if triggered else "NONE",
                parameters={"proposed_trade_value": proposed, "step": step},
            ),
            strategy_id=strategy_id,
            symbol=symbol,
            market_event_id=market_event_id,
            decision_type="STRATEGY_DECISION",
        )
        if strategy_event is not None:
            decision_id = strategy_event.event_id
        elif market_event is not None:
            decision_id = market_event.event_id
        else:
            decision_id = f"decision:{market_event_id}"

        if not triggered:
            return LiveDecision(context=context, triggered=False, decision_id=decision_id)

        self.evaluate_circuit_breaker(context.drawdown)
        clamped = float(self.risk_manager.clamp_trade_value(proposed, context.equity, context.cash, context.open_lot_count))
        self._record_canonical_audit(
            "RISK_DECISION",
            lambda event_id: RiskDecisionPayload(
                decision_id=decision_id,
                allowed=(clamped > 0),
                reason="clamped" if clamped < proposed else ("halted" if self.circuit_breaker.halted else "allowed"),
                relevant_limits={"max_concurrent_lots": getattr(self.risk_manager, "max_concurrent_lots", None), "max_total_exposure": getattr(self.risk_manager, "max_total_exposure", None)},
            ),
            strategy_id=strategy_id,
            symbol=symbol,
            market_event_id=market_event_id,
            decision_type="RISK_DECISION",
        )
        return LiveDecision(context=context, triggered=True, proposed_trade_value=proposed, clamped_trade_value=clamped, decision_id=decision_id)

    def apply_sell_fill(self, order: Any, lot: InventoryLot, ledger: AssetLotLedger | None = None, cash: float = 0.0, *, execution_cost: float = 0.0, cost_model: TransactionCostModel | None = None) -> tuple[float, float]:
        cost_model = cost_model or ZeroCostModel()
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

        fill_violation = False
        try:
            econ = validate_sell(lot, new_qty, new_avg, cost_model)
            net_proceeds = econ.net_sell_proceeds
        except SellEconomicsError as exc:
            logger.warning("No-loss guard violation at fill boundary (fill already executed): %s", exc)
            self.no_loss_guard_violations += 1
            fill_violation = True
            net_proceeds = new_notional - float(execution_cost)

        applied, _ = self.oms.process_event_once(event_id, lambda: ledger.close_lot(lot, sell_qty=new_qty, execution_price=new_avg, completed=False))
        if not applied:
            return float(cash), 0.0
        state.qty = float(order.filled_qty)
        state.notional = float(order.filled_qty) * float(order.filled_avg_price or 0.0)

        self._record_audit("ORDER_STATUS", OrderStatusPayload(intent_id=order_id, broker_order_id=order_id, status="FILLED" if state.qty >= lot.shares - 1e-9 else "PARTIALLY_FILLED", cumulative_filled_qty=state.qty), event_id=f"{event_id}:status")
        self._record_audit("FILL", FillPayload(fill_id=event_id, order_id=order_id, incremental_fill_qty=new_qty, cumulative_filled_qty=state.qty, price=new_avg, fees=execution_cost, timestamp=datetime.now(timezone.utc).isoformat()), event_id=event_id)
        self._record_audit("LEDGER_MUTATION", LedgerMutationPayload(event_id=event_id, lot_id=lot.order_id, mutation_type="close_lot" + ("_violation" if fill_violation else ""), quantity_delta=-new_qty, cash_delta=net_proceeds), event_id=f"{event_id}:ledger")
        if self.state_store is not None:
            self.state_store.persist_ledger(ledger)
        return float(cash) + net_proceeds, net_proceeds

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
        self._record_audit("ORDER_STATUS", OrderStatusPayload(intent_id=order_id, broker_order_id=order_id, status="FILLED" if state.qty > 0 else "PARTIALLY_FILLED", cumulative_filled_qty=state.qty), event_id=f"{event_id}:status")
        self._record_audit("FILL", FillPayload(fill_id=event_id, order_id=order_id, incremental_fill_qty=new_qty, cumulative_filled_qty=state.qty, price=new_avg, fees=execution_cost, timestamp=datetime.now(timezone.utc).isoformat()), event_id=event_id)
        self._record_audit("LEDGER_MUTATION", LedgerMutationPayload(event_id=event_id, lot_id=order_id, mutation_type="register_buy", quantity_delta=new_qty, cash_delta=-(new_notional + execution_cost)), event_id=f"{event_id}:ledger")
        if self.state_store is not None:
            self.state_store.persist_ledger(ledger)
        return float(cash) - new_notional - float(execution_cost), lot

    def submit_buy(self, decision: LiveDecision) -> Any:
        if self.broker is None:
            raise RuntimeError("live broker is not connected")
        if self.runtime_state is not RuntimeState.READY:
            return None
        if self.circuit_breaker.halted or decision.clamped_trade_value <= 0:
            return None

        symbol = self.config.backtest.symbol
        market_event_id = str(decision.context.bar_index)
        intent_event = self._record_order_intent(
            decision_id=decision.decision_id or "",
            symbol=symbol,
            side="BUY",
            quantity=decision.clamped_trade_value,
            limit_price=None,
            market_event_id=market_event_id,
        )
        if intent_event is not None:
            intent_id = intent_event.event_id
        else:
            intent_id = generate_event_id()
            self._record_audit("ORDER_INTENT", OrderIntentPayload(intent_id=intent_id, decision_id=decision.decision_id or "", symbol=symbol, side="BUY", quantity=decision.clamped_trade_value, limit_price=None), event_id=intent_id)
        result = self.broker.submit_buy(symbol, decision.clamped_trade_value)
        broker_order_id = str(getattr(result, "id", "")) if result is not None else ""
        status = str(getattr(result, "status", "SUBMITTED"))
        self._record_audit("ORDER_STATUS", OrderStatusPayload(intent_id=intent_id, broker_order_id=broker_order_id or intent_id, status=status, cumulative_filled_qty=float(getattr(result, "filled_qty", 0.0) or 0.0)), event_id=f"{intent_id}:status")
        return result

    def submit_sell(self, qty: float, target_price: float, decision_id: str = "", *, lot: InventoryLot | None = None, cost_model: TransactionCostModel | None = None, market_event_id: str | int | None = None) -> Any:
        """Submit a sell intent only when an authoritative lot proves Rule One."""
        if self.broker is None:
            raise RuntimeError("live broker is not connected")
        if lot is None:
            raise SellEconomicsError("submit_sell requires the authoritative InventoryLot for the Rule One no-loss guard")
        cost_model = cost_model or ZeroCostModel()
        try:
            validate_sell(lot, float(qty), float(target_price), cost_model)
        except SellEconomicsError as exc:
            logger.warning("submit_sell rejected by no-loss guard — order not submitted: %s", exc)
            self.no_loss_guard_violations += 1
            return None

        symbol = self.config.backtest.symbol
        resolved_market_event_id = str(market_event_id if market_event_id is not None else (self._last_market_event_id or decision_id))
        intent_event = self._record_order_intent(
            decision_id=decision_id,
            symbol=symbol,
            side="SELL",
            quantity=qty,
            limit_price=target_price,
            market_event_id=resolved_market_event_id,
        )
        if intent_event is not None:
            intent_id = intent_event.event_id
        else:
            intent_id = generate_event_id()
            self._record_audit("ORDER_INTENT", OrderIntentPayload(intent_id=intent_id, decision_id=decision_id, symbol=symbol, side="SELL", quantity=qty, limit_price=target_price), event_id=intent_id)
        result = self.broker.submit_sell(symbol, float(qty), float(target_price))
        broker_order_id = str(getattr(result, "id", "")) if result is not None else ""
        status = str(getattr(result, "status", "SUBMITTED"))
        self._record_audit("ORDER_STATUS", OrderStatusPayload(intent_id=intent_id, broker_order_id=broker_order_id or intent_id, status=status, cumulative_filled_qty=float(getattr(result, "filled_qty", 0.0) or 0.0)), event_id=f"{intent_id}:status")
        return result
