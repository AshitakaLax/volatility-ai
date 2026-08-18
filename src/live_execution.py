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
from src import decision_cycle
from src.exceptions import ConfigurationError
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


class LiveExecutionLoop:
    """Drive live ticks through the canonical strategy-facing contract."""

    def __init__(
        self,
        config: BacktestConfig,
        strategy: SizingStrategy,
        risk_manager: RiskManager | None = None,
        *,
        broker_factory: Callable[[LiveCredentials], LiveBroker] | None = None,
        oms: OrderManagementSystem | None = None,
    ) -> None:
        config.validate()
        if not config.live.enabled:
            raise ConfigurationError("live.enabled=False: live execution is disabled")
        self.config = config
        self.strategy = strategy
        self.risk_manager = risk_manager or RiskManager(
            max_concurrent_lots=config.risk.max_concurrent_lots,
            max_total_exposure=config.risk.max_total_exposure,
        )
        self._broker_factory = broker_factory
        self.oms = oms or OrderManagementSystem(mode=Mode.LIVE)
        self.broker: LiveBroker | None = None
        self.last_buy_price = None
        self._started = False

    def start(self) -> None:
        """Validate credentials before attempting any broker/WebSocket work."""
        credentials = load_live_credentials()
        if self._broker_factory is not None:
            self.broker = self._broker_factory(credentials)
        self._started = True

    def build_context(
        self,
        *,
        timestamp: datetime,
        open: float,
        high: float,
        low: float,
        close: float,
        cash: float,
        equity: float,
        peak_equity: float,
        drawdown: float,
        open_lot_count: int,
        bar_index: int,
        time_of_day_flag: int = 0,
        is_macro_event_day: bool = False,
        macro_surprise_factor: float = 0.0,
    ) -> MarketContext:
        if timestamp.tzinfo is None:
            timestamp = timestamp.replace(tzinfo=timezone.utc)
        return MarketContext(
            timestamp=timestamp,
            open=float(open), high=float(high), low=float(low), close=float(close),
            cash=float(cash), equity=float(equity), peak_equity=float(peak_equity),
            drawdown=float(drawdown), open_lot_count=int(open_lot_count),
            bar_index=int(bar_index), time_of_day_flag=int(time_of_day_flag),
            is_macro_event_day=bool(is_macro_event_day),
            macro_surprise_factor=float(macro_surprise_factor),
        )

    def decision_cycle(
        self, context: MarketContext, *, step: float, last_buy_price: float, cash: float | None = None
    ) -> LiveDecision:
        """Canonical live strategy sequence; no broker/network side effects.

        Delegates to src/decision_cycle.py -- the same functions
        optimization_controller._simulate_single calls -- so live and
        backtest provably run one implementation of the sequence rather
        than two copies (Task 7.1's shared decision-cycle contract).

        cash defaults to context.cash, preserving this method's
        pre-Task-7.1 behavior for existing callers. Pass it explicitly
        when current cash has moved since the context was built (e.g.
        fills confirmed mid-tick) -- the backtest path passes its
        post-harvest cash for exactly that reason.
        """
        if not self._started:
            raise RuntimeError("live execution has not been started")
        decision_cycle.record_tick(self.strategy, context)
        decision = decision_cycle.evaluate_grid_decision(
            self.strategy,
            self.risk_manager,
            context,
            last_buy_price,
            step,
            context.cash if cash is None else cash,
        )
        return LiveDecision(
            context=decision.context,
            triggered=decision.triggered,
            proposed_trade_value=decision.proposed_trade_value,
            clamped_trade_value=decision.clamped_trade_value,
        )

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
