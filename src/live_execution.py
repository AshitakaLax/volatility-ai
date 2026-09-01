"""Live execution adapter using the same strategy decision-cycle as backtests.

Broker I/O is deliberately injected so importing this module never opens a
network connection. Credentials are loaded before a broker adapter can be
constructed.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, Protocol

from src import decision_cycle
from src.config import BacktestConfig
from src.exceptions import ConfigurationError
from src.market_context import MarketContext
from src.order_management_system import Mode, OrderManagementSystem
from src.risk_manager import CircuitBreaker, RiskManager
from src.secrets import LiveCredentials, load_live_credentials
from src.size_calculators import SizingStrategy
from src.tick_validation import TickCheck, TickValidator


class LiveBroker(Protocol):
    """Minimal broker interface the live loop depends on.

    A Protocol rather than a base class so any object with these two
    methods works -- real Alpaca client, paper client, or test double --
    without inheriting from anything here.
    """

    def submit_buy(self, symbol: str, trade_value: float) -> Any:
        """Buy trade_value worth of symbol. Returns the broker's order object."""
        ...

    def submit_sell(self, symbol: str, qty: float, target_price: float) -> Any:
        """Sell qty of symbol at target_price. Returns the broker's order object."""
        ...


@dataclass(frozen=True)
class LiveDecision:
    """One tick's outcome: what the strategy proposed and what risk allowed.

    triggered=False means no buy is proposed -- either the grid did not
    trigger, or a halt suppressed it. clamped_trade_value is the amount
    actually permitted after the risk clamp, and is the only figure a
    caller should act on.
    """

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
        tick_validator: TickValidator | None = None,
        live_capital_promotion=None,
        circuit_breaker=None,
    ) -> None:
        """Assemble the live loop from its collaborators.

        Every collaborator is injectable and defaults to a safe
        instance, so a caller opts in to risk rather than out of it:
        an unconfigured RiskManager is unlimited but the OMS still
        defaults to PAPER mode, and reaching LIVE additionally requires
        live_capital_promotion (Task 7.7).

        Raises ConfigurationError if config.live.enabled is False --
        constructing a live loop from a config that does not ask for
        live execution is a mistake worth failing on, not defaulting.
        """
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
        # Task 7.7: honor config.live.paper_trading. This previously
        # constructed Mode.LIVE unconditionally, ignoring the flag
        # entirely -- so a paper-trading config still built a
        # real-capital OMS. Reaching LIVE now additionally requires a
        # passing promotion evaluation (enforced in the OMS itself).
        self.oms = oms or OrderManagementSystem(
            mode=Mode.PAPER if config.live.paper_trading else Mode.LIVE,
            live_capital_promotion=live_capital_promotion,
        )
        self.broker: LiveBroker | None = None
        self.last_buy_price = None
        self._started = False
        # Task 7.6: per-tick sanity check. Owns last_good_price; a
        # rejected tick never advances it.
        # Task 7.8: live-only hard stop on new buys. Defaults to a
        # fresh in-memory breaker; pass one backed by a LedgerStore to
        # make the halt survive a restart.
        self.circuit_breaker = circuit_breaker or CircuitBreaker()
        self.tick_validator = tick_validator or TickValidator()

    def validate_tick(self, price: float) -> TickCheck:
        """Task 7.6 entry point: check an incoming tick BEFORE building
        a MarketContext or evaluating strategy. Returns the check;
        callers must not proceed to decision_cycle on a rejected tick.
        See process_tick for the guarded path that enforces that."""
        return self.tick_validator.validate(price)

    def process_tick(
        self, price: float, context_builder, *, step: float, last_buy_price: float
    ) -> LiveDecision | None:
        """Guarded per-tick path: sanity-check first, and only build a
        context and run the decision cycle if the tick passed.

        Returns None for a rejected tick -- strategy is never
        evaluated, no order is proposed, and last_good_price is
        unchanged. context_builder is called only for accepted ticks,
        so a bad print can't even reach MarketContext construction.
        """
        check = self.validate_tick(price)
        if not check.accepted:
            return None
        context = context_builder(check.price)
        return self.decision_cycle(context, step=step, last_buy_price=last_buy_price)

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
        is_earnings_reaction_day: bool = False,
        volume: float = 0.0,
        event_intensity: float = 0.0,
        minutes_to_event: float = -1.0,
        implied_vol_change: float = 0.0,
    ) -> MarketContext:
        """Build the per-tick MarketContext the strategy sees.

        Naive timestamps are coerced to UTC rather than rejected, since
        a broker feed supplying local-naive times is common and silently
        mixing zones is the worse failure.

        The event/macro fields are accepted and forwarded, and default to
        the safe values from overview 5.1. Two of them are now live
        inputs rather than the inert ones Task 7.9's discovery outcome
        recorded in CHANGELOG.md: HighFrequencyLocalReferenceSizing
        consumes is_macro_event_day and is_earnings_reaction_day to
        scale its per-lot size. macro_surprise_factor remains unconsumed
        and is still never populated by the backtest path.

        event_intensity, minutes_to_event and implied_vol_change are
        accepted here too. They were previously ABSENT from this
        signature while the three other MarketContext construction sites
        (optimization_controller, live_trading_loop, intraday_validation)
        all populated them -- so a caller of this shim silently built a
        context blinder than the one every other path produces. That
        asymmetry is the bug this signature existed to avoid, so a new
        field goes in all four places or none.
        """
        if timestamp.tzinfo is None:
            timestamp = timestamp.replace(tzinfo=UTC)
        return MarketContext(
            timestamp=timestamp,
            open=float(open),
            high=float(high),
            low=float(low),
            close=float(close),
            cash=float(cash),
            equity=float(equity),
            peak_equity=float(peak_equity),
            drawdown=float(drawdown),
            open_lot_count=int(open_lot_count),
            bar_index=int(bar_index),
            time_of_day_flag=int(time_of_day_flag),
            is_macro_event_day=bool(is_macro_event_day),
            macro_surprise_factor=float(macro_surprise_factor),
            is_earnings_reaction_day=bool(is_earnings_reaction_day),
            volume=float(volume),
            event_intensity=float(event_intensity),
            minutes_to_event=float(minutes_to_event),
            implied_vol_change=float(implied_vol_change),
        )

    def decision_cycle(
        self,
        context: MarketContext,
        *,
        step: float,
        last_buy_price: float,
        cash: float | None = None,
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

        # Task 7.8: the circuit breaker is checked at the same point as
        # the sizing clamp but is deliberately DISTINCT from it -- the
        # clamp reduces size, this blocks new entry outright. Only the
        # BUY side is affected: record_tick above already ran (strategy
        # rolling state keeps updating), and harvest/sell evaluation is
        # untouched, so open lots stay fully exitable. This never forces
        # liquidation (no-loss shutdown invariant).
        self.circuit_breaker.evaluate(
            context.drawdown, self.risk_manager.halt_new_buys_if_drawdown_exceeds
        )
        if decision.triggered and not self.circuit_breaker.allows_new_buys:
            return LiveDecision(
                context=decision.context,
                triggered=False,
                proposed_trade_value=decision.proposed_trade_value,
                clamped_trade_value=0.0,
            )

        return LiveDecision(
            context=decision.context,
            triggered=decision.triggered,
            proposed_trade_value=decision.proposed_trade_value,
            clamped_trade_value=decision.clamped_trade_value,
        )

    def submit_buy(self, decision: LiveDecision) -> Any:
        """Submit the buy a decision authorized, if any.

        Submits clamped_trade_value -- the risk-approved amount -- never
        the strategy's raw proposal. Returns None without contacting the
        broker when the clamped value is zero, which is how a suppressed
        or fully-clamped decision ends quietly rather than as an error.
        """
        if self.broker is None:
            raise RuntimeError("live broker is not connected")
        if decision.clamped_trade_value <= 0:
            return None
        return self.broker.submit_buy(self.config.backtest.symbol, decision.clamped_trade_value)

    def submit_sell(self, qty: float, target_price: float) -> Any:
        """Submit a harvest sell for an open lot.

        Callers must have already cleared this quantity and price
        through src/no_loss_guard.validate_sell (Task 7.15); this method
        does not re-check, because the guard exists in exactly one place.
        """
        if self.broker is None:
            raise RuntimeError("live broker is not connected")
        return self.broker.submit_sell(self.config.backtest.symbol, float(qty), float(target_price))
