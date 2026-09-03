"""
The long-running live trading loop.

Everything before this module could decide what to do; nothing drove
it on a schedule. This is the daemon `cli.py live` runs: it ticks,
applies confirmed fills, harvests, buys, persists, and shuts down
gracefully -- and it composes existing pieces rather than reproducing
them.

--------------------------------------------------------------------
PARITY WITH THE BACKTEST is the constraint that shapes the tick.

The per-tick order below is _simulate_single's per-bar order, and the
two phases that make a strategy stateful go through the SAME shared
functions in src/decision_cycle.py that the backtest calls, per Task
7.1's requirement that this be provable "via a shared helper function
both call, not two independently-written copies":

    record_tick  ->  harvest sells  ->  grid trigger/size/clamp  ->  buy

The ordering is not cosmetic. record_tick fires at the very top of the
tick, before any harvest, because a stateful strategy's view of the
market must not depend on whether a lot happened to be sold. The grid
trigger is then evaluated with POST-harvest cash, which is why `cash`
is passed explicitly rather than read from the context snapshot --
src/decision_cycle.py's own docstring documents this seam, and the two
call sites having disagreed about exactly this argument is why that
module exists.

This loop calls decision_cycle directly rather than going through
LiveExecutionLoop.decision_cycle, which bundles record_tick and the
grid evaluation into one call. That bundling leaves no seam for the
harvest to sit in, so using it here would force record_tick to run
after the harvest -- the precise reordering decision_cycle.py warns
against. LiveExecutionLoop remains the right tool for a caller driving
single decisions; it is not the right shape for the full cycle.
--------------------------------------------------------------------
FILLS ARE ASYNCHRONOUS, and that is the deepest difference from the
backtest.

In a backtest an order fills instantly and completely, so the same
statement that submits it can move cash. Live, submission and fill are
separate events, and a limit sell at a profit target may never fill at
all -- that is what a limit order IS. So this loop separates the two:

  - Submitting records an order and mutates nothing.
  - A later tick polls the broker, converts the broker's CUMULATIVE
    figures into an increment via Task 7.2's FillTracker, and only
    that increment is allowed to move cash, lots, or the ledger.

The consequence worth stating plainly: cash and lots reflect CONFIRMED
fills only. An order in flight is deliberately invisible to sizing,
which is the conservative direction -- the strategy under-counts what
it may already own rather than spending money twice.

Unfilled DAY orders expire at the close. The next poll sees a terminal
status, stops tracking, and leaves the lot open and unsold. That is
correct and needs no special case: the lot is simply re-offered on a
later tick if it is still marketable.
--------------------------------------------------------------------
THE COST MODEL IS NOT APPLIED TO REAL BUY FILLS.

A backtest applies TransactionCostModel to model slippage it cannot
observe. A live fill price already contains the real slippage, so
applying the model on top would count it twice and overstate every
lot's cost basis. The confirmed fill price IS the cost basis here.

The sell side does still run the configured cost model, through
no_loss_guard.validate_sell. That direction is safe: modeled costs
reduce net proceeds, which can only make the no-loss guard stricter,
never looser.
--------------------------------------------------------------------
NO FORCED LIQUIDATION, EVER. There is no code path in this module that
sells a lot for any reason other than its profit target being met and
the no-loss guard permitting it. Shutdown does not liquidate, a
drawdown halt does not liquidate, and a reconciliation failure does not
liquidate -- consistent with Task 7.8's no-loss shutdown invariant.
"""

from __future__ import annotations

import json
import logging
import time
from dataclasses import dataclass, field
from datetime import UTC, datetime

from src import decision_cycle
from src.config import BacktestConfig
from src.cost_models import ZeroCostModel
from src.duplicate_order_guard import DuplicateOrderGuard
from src.earnings_calendar import is_earnings_reaction_day_at
from src.exceptions import ConfigurationError
from src.fill_accounting import FillTracker, extract_alpaca_fill
from src.fomc_calendar import is_fomc_day_at
from src.idempotency import compute_decision_id
from src.implied_vol_signal import change_at
from src.intraday_profile import minutes_since_open
from src.market_context import MarketContext
from src.no_loss_guard import NoLossViolation, SellReason, validate_sell
from src.order_lifecycle import TERMINAL_STATES, map_broker_status
from src.retry_policy import AmbiguousSubmissionError
from src.risk_manager import CircuitBreaker, RiskManager
from src.tick_validation import TickValidator

logger = logging.getLogger("Optimizer")

# Durable keys for the scalars that are not lots. Namespaced so they
# cannot collide with Task 7.8's halt keys in the same meta table.
_META_CASH = "live.cash"
# Unsettled proceeds and their maturity sessions, as JSON. Persisted
# because a restart that forgot them would treat unsettled money as
# spendable and trade MORE aggressively than the backtest modelled --
# in a cash account, that is extra good-faith violations.
_META_UNSETTLED = "live.unsettled"
_META_PEAK_EQUITY = "live.peak_equity"


@dataclass
class TickOutcome:
    """What one tick did.

    `acted` distinguishes a tick that ran the full cycle from one that
    deliberately did nothing (market closed, bad print, no data). The
    reason is carried rather than logged-and-forgotten so the caller --
    and the tests -- can assert on WHY a tick was skipped instead of
    inferring it from an absence of orders.
    """

    acted: bool
    reason: str
    price: float | None = None
    fills_applied: int = 0
    sells_submitted: int = 0
    buys_submitted: int = 0


@dataclass
class _TrackedOrder:
    """One in-flight order and its cumulative-fill state.

    Holds a FillTracker rather than a running total: the broker reports
    cumulative figures, and converting them to increments is Task 7.2's
    job, not something to re-derive here.
    """

    client_order_id: str
    kind: str  # "buy" or "sell"
    tracker: FillTracker
    lot_order_id: str | None = None
    trigger_price: float = 0.0
    profit_target: float = 0.0
    # WHY the sell was submitted, carried from submission to fill.
    # Unlike the backtest, live splits those into two ticks: the guard
    # runs in _apply_sell_fill, long after _maybe_sell decided. Without
    # this field the fill handler cannot tell a harvest from a signal
    # exit, would refuse to book the loss, and would leave a position
    # the broker has already sold still open in our ledger -- the exact
    # divergence reconciliation exists to catch, manufactured by us.
    sell_reason: SellReason = SellReason.PROFIT_TARGET


@dataclass
class _LoopState:
    """The scalars that survive a restart, alongside the persisted lots."""

    cash: float
    peak_equity: float
    last_buy_price: float | None = None
    prev_close: float | None = None
    max_drawdown: float = 0.0
    open_orders: dict = field(default_factory=dict)
    sells_in_flight: set = field(default_factory=set)

    # T+N settlement, mirroring optimization_controller.BacktestState.
    # `cash` remains TOTAL cash so equity is unaffected; only what can
    # be SPENT is reduced.
    unsettled: float = 0.0
    pending: list = field(default_factory=list)
    session: int = 0

    @property
    def buying_power(self) -> float:
        """Cash that can actually be spent right now.

        Floored at zero: a buy debits total cash while unsettled is
        unchanged, so cash can legitimately fall below unsettled. That
        means "nothing spendable", not "negative spendable".
        """
        return max(0.0, self.cash - self.unsettled)

    def credit_sale(self, amount: float, settlement_days: int) -> None:
        """Book sale proceeds, settling `settlement_days` sessions later."""
        self.cash += amount
        if settlement_days <= 0:
            return
        self.unsettled += amount
        self.pending.append([self.session + settlement_days, amount])

    def advance_session(self, session: int) -> None:
        """Move to a new session and settle what has matured."""
        self.session = session
        if not self.pending:
            return
        still = []
        for settles_on, amount in self.pending:
            if settles_on <= session:
                self.unsettled -= amount
            else:
                still.append([settles_on, amount])
        self.pending = still
        if not self.pending:
            self.unsettled = 0.0


class LiveTradingLoop:
    """Drives live trading tick by tick.

    State ownership: this object owns the in-flight order table and the
    cash/peak-equity scalars, and writes both through to the
    LedgerStore. It does NOT own lots (AssetLotLedger does), the halt
    (CircuitBreaker), fill arithmetic (FillTracker), or the exit
    decision (no_loss_guard) -- each of those is delegated to the module
    that already implements it.
    """

    def __init__(
        self,
        config: BacktestConfig,
        strategy,
        broker,
        market_data,
        store,
        *,
        risk_manager: RiskManager | None = None,
        circuit_breaker=None,
        cost_model=None,
        tick_validator: TickValidator | None = None,
        deployment_id: str = "default",
        sleep=time.sleep,
    ) -> None:
        """Assemble the loop and load durable state.

        Refuses to construct on a config that does not name a single
        live step and profit_target. Those are validated here rather
        than in BacktestConfig.validate() because this loop is the only
        thing that needs them -- and it needs them absolutely, since
        they ARE the strategy that real capital will trade.
        """
        config.validate()
        if not config.live.enabled:
            raise ConfigurationError("live.enabled=False: live trading is disabled")
        if config.live.step is None or config.live.profit_target is None:
            raise ConfigurationError(
                "live.step and live.profit_target are both required to run the live trading "
                "loop. They are deliberately not taken from grid.steps/grid.profit_targets: "
                "those are sweep lists, and trading real capital on their first element would "
                "make the running parameters an implicit side effect of sweep ordering."
            )

        self.config = config
        self.strategy = strategy
        self.broker = broker
        self.market_data = market_data
        self.store = store
        self.symbol = config.backtest.symbol
        self.step = float(config.live.step)
        self.profit_target = float(config.live.profit_target)
        self.deployment_id = deployment_id
        # Loaded once at startup, not per tick -- src/event_calendar.py's
        # from_csv parses ~700 rows, cheap once but wasteful at a
        # 60s poll interval over a multi-day deployment. Falls back to
        # None (no events) if the generated CSV is absent, matching
        # optimization_controller.py's and intraday_validation.py's
        # same fallback -- see EarningsEventTable._load_event_table's
        # docstring pattern.
        try:
            from src.event_calendar import EarningsEventTable
            from src.exceptions import DataValidationError as _DataValidationError

            self._event_table = EarningsEventTable.from_csv()
        except (FileNotFoundError, _DataValidationError) as e:
            logger.warning(f"No earnings event table loaded ({e}); event_intensity stays 0.0.")
            self._event_table = None
        # Implied-vol change series -- same optional-artifact fallback as
        # the event table above, and for the same reason: the consuming
        # exponent defaults to 0.0, so its absence is an exact no-op
        # rather than something worth refusing to start over.
        self._implied_vol_series = None
        implied_vol_path = getattr(getattr(config, "live", None), "implied_vol_path", None)
        if implied_vol_path:
            try:
                from src.implied_vol_signal import load_implied_vol_change

                self._implied_vol_series = load_implied_vol_change(implied_vol_path)
            except (FileNotFoundError, _DataValidationError) as e:
                logger.warning(
                    f"No implied-vol series loaded from {implied_vol_path} ({e}); "
                    "implied_vol_change stays 0.0."
                )
        self._sleep = sleep
        self._stop_requested = False

        self.risk_manager = risk_manager or RiskManager(
            max_concurrent_lots=config.risk.max_concurrent_lots,
            max_total_exposure=config.risk.max_total_exposure,
        )
        self.circuit_breaker = circuit_breaker or CircuitBreaker(store=store)
        # Zero by default: a real fill price already contains real
        # slippage (see module docstring). A configured model still
        # applies to the sell-side guard, where extra cost is the safe
        # direction.
        self.cost_model = cost_model or ZeroCostModel()
        self.tick_validator = tick_validator or TickValidator()
        self.guard = DuplicateOrderGuard(store)

        self.ledger = store.load_ledger()
        cash = store.get_meta(_META_CASH)
        peak = store.get_meta(_META_PEAK_EQUITY)
        initial_cash = float(config.backtest.initial_cash)
        self.settlement_days = int(config.execution.settlement_days)
        self.state = _LoopState(
            cash=float(cash) if cash is not None else initial_cash,
            peak_equity=float(peak) if peak is not None else initial_cash,
            last_buy_price=store.load_last_buy_price(),
        )
        self._restore_settlement(store.get_meta(_META_UNSETTLED))
        logger.info(
            f"LiveTradingLoop ready: symbol={self.symbol} step={self.step} "
            f"profit_target={self.profit_target} cash={self.state.cash:.2f} "
            f"open_lots={len(self.ledger.open_lots)}"
        )

    def _restore_settlement(self, raw: str | None) -> None:
        """Reload unsettled proceeds, or fail SAFE if they are unreadable.

        A restart that silently forgot unsettled money would treat it as
        spendable -- trading more aggressively than the backtest
        modelled, which in a cash account means good-faith violations
        that were never simulated. So CORRUPT state does not default to
        zero: it treats all cash as unsettled until the next session,
        which under-trades for at most one session and cannot over-trade.

        ABSENT state is a different fact and is handled differently. A
        fresh deployment has written nothing yet, and its opening balance
        is settled cash already sitting in the account. Conflating the
        two froze buying power at zero on every first run.
        """
        if self.settlement_days <= 0:
            return
        if raw is None:
            # NEVER WRITTEN, not corrupt. A fresh deployment's opening
            # balance is settled cash sitting in the account -- there is
            # nothing outstanding to wait for. Treating absence as the
            # failure case froze buying power at zero on the first run and
            # the loop could never open a position.
            return
        try:
            saved = json.loads(raw)
            self.state.session = int(saved['session'])
            self.state.unsettled = float(saved['unsettled'])
            self.state.pending = [[int(d), float(a)] for d, a in saved['pending']]
        except (TypeError, ValueError, KeyError) as exc:
            self.state.unsettled = self.state.cash
            self.state.pending = []
            logger.warning(
                f"Settlement state unreadable ({exc}); treating the whole "
                f"${self.state.cash:.2f} balance as unsettled until the next "
                "session. This under-trades deliberately -- the alternative "
                "is spending money that may not have settled."
            )

    # --- control ---

    def request_stop(self) -> None:
        """Ask the loop to stop after the current tick completes.

        Cooperative rather than immediate: a tick that is midway through
        applying a confirmed fill must finish writing it, or the next
        startup reconciles against state that never recorded a fill the
        broker already executed.
        """
        logger.info("Stop requested -- will exit after the current tick.")
        self._stop_requested = True

    @property
    def stop_requested(self) -> bool:
        """Whether a stop has been requested."""
        return self._stop_requested

    # --- the tick ---

    def run_once(self) -> TickOutcome:
        """One full cycle. Returns what it did, including why it skipped.

        Fills are applied FIRST, before anything reads cash or lots, so
        the tick's sizing decisions see confirmed reality rather than
        state that is one fill stale.
        """
        if not self.market_data.is_open():
            return TickOutcome(acted=False, reason="market_closed")

        from src.exceptions import DataValidationError

        try:
            bar = self.market_data.latest_bar(self.symbol)
        except DataValidationError as e:
            # A missing bar is routine on IEX in a quiet interval. Skip
            # the tick; never synthesize a price.
            logger.warning(f"No bar this tick: {e}")
            return TickOutcome(acted=False, reason="no_data")

        check = self.tick_validator.validate(bar.close)
        if not check.accepted:
            # Task 7.6: a rejected print never reaches strategy
            # evaluation and never advances last_good_price.
            logger.warning(f"Tick rejected by validation: {bar.close}")
            return TickOutcome(acted=False, reason="tick_rejected", price=bar.close)

        price = check.price

        # SESSION BOUNDARY, before fills are applied, so proceeds credited
        # this tick are not settled by this tick's own advance. Mirrors
        # _simulate_single, which advances at the top of each bar for the
        # same reason. Guarded on the flag so the default path pays one
        # integer comparison per tick.
        if self.settlement_days > 0:
            day = bar.timestamp.toordinal()
            if day != self.state.session:
                self.state.advance_session(day)

        fills = self._poll_open_orders()

        context = self._build_context(bar, price)

        # Phase 1, unconditionally and before any harvest.
        decision_cycle.record_tick(self.strategy, context)

        sells = self._harvest(context)

        # Task 7.8: the drawdown halt blocks NEW BUYS only. record_tick
        # above already ran and the harvest above already ran, so a
        # halted loop still tracks the market and still exits open lots.
        self.circuit_breaker.evaluate(
            context.drawdown, self.risk_manager.halt_new_buys_if_drawdown_exceeds
        )
        buys = self._maybe_buy(context) if self.circuit_breaker.allows_new_buys else 0

        self.state.prev_close = price
        self.persist_state()
        return TickOutcome(
            acted=True,
            reason="ok",
            price=price,
            fills_applied=fills,
            sells_submitted=sells,
            buys_submitted=buys,
        )

    def run_forever(self, max_ticks: int | None = None) -> int:
        """Tick until stopped. Returns the number of ticks executed.

        max_ticks bounds the loop for tests and for a bounded operator
        run; None is the daemon case. Sleeps between ticks regardless of
        whether the market was open, so a closed market costs one clock
        call per interval instead of a spin.
        """
        interval = float(self.config.live.poll_interval_seconds)
        ticks = 0
        while not self._stop_requested and (max_ticks is None or ticks < max_ticks):
            try:
                outcome = self.run_once()
                if outcome.acted:
                    logger.info(
                        f"tick price={outcome.price} fills={outcome.fills_applied} "
                        f"sells={outcome.sells_submitted} buys={outcome.buys_submitted} "
                        f"cash={self.state.cash:.2f} open_lots={len(self.ledger.open_lots)}"
                    )
            except AmbiguousSubmissionError:
                # It is unknown whether an order reached the broker.
                # Halting and stopping is the only safe response --
                # continuing to trade could double an existing position.
                # Re-raised after halting so the process exits into a
                # state a human must clear.
                self.circuit_breaker.halt_for_reconciliation(
                    "Ambiguous order submission -- unknown whether the broker received an "
                    "order. Reconcile by client order ID before resuming."
                )
                raise
            ticks += 1
            if self._stop_requested or (max_ticks is not None and ticks >= max_ticks):
                break
            self._sleep(interval)
        return ticks

    # --- fills ---

    def _poll_open_orders(self) -> int:
        """Apply every newly confirmed fill increment. Returns how many.

        Iterates a snapshot of the tracked orders because applying a
        fill can untrack the order it came from.
        """
        applied = 0
        for client_order_id, tracked in list(self.state.open_orders.items()):
            order = self.broker.get_order_by_client_id(client_order_id)
            if order is None:
                # Claimed locally but absent at the broker. Not resolved
                # by guessing -- reconciliation owns this, and until it
                # runs the order stays tracked rather than being dropped
                # (dropping it would lose a real position).
                logger.warning(
                    f"Order {client_order_id!r} is tracked locally but the broker has no "
                    "record of it; leaving it tracked for reconciliation."
                )
                continue

            filled_qty, filled_avg_price = extract_alpaca_fill(order)
            delta = tracked.tracker.apply_update(filled_qty, filled_avg_price)
            if not delta.is_empty:
                if tracked.kind == "buy":
                    self._apply_buy_fill(tracked, delta)
                else:
                    self._apply_sell_fill(tracked, delta)
                applied += 1

            if map_broker_status(order.status) in TERMINAL_STATES:
                self.state.open_orders.pop(client_order_id, None)
                if tracked.lot_order_id is not None:
                    self.state.sells_in_flight.discard(tracked.lot_order_id)
        return applied

    def _apply_buy_fill(self, tracked: _TrackedOrder, delta) -> None:
        """Open (or add to) a lot from a confirmed buy increment.

        The fill's own average price is the per-share cost basis --
        unmodified, because it already contains real slippage. Each
        increment of a partially-filled order opens its own lot, keyed
        by a suffixed order id: the increments genuinely executed at
        different prices, and merging them would invent a blended basis
        no single execution ever had.
        """
        lot_order_id = tracked.client_order_id
        if any(lot.order_id == lot_order_id for lot in self.ledger.open_lots):
            lot_order_id = f"{tracked.client_order_id}#{len(self.ledger.open_lots)}"

        lot = self.ledger.register_buy(
            lot_order_id,
            self.symbol,
            delta.avg_price,
            delta.qty,
            tracked.profit_target,
        )
        self.state.cash -= delta.notional
        self.state.last_buy_price = tracked.trigger_price or delta.avg_price
        self.store.record_open_lot(lot)
        self.store.save_last_buy_price(self.state.last_buy_price)
        logger.info(
            f"BUY filled: {delta.qty} @ {delta.avg_price} (${delta.notional:.2f}) -> lot "
            f"{lot_order_id!r}; cash={self.state.cash:.2f}"
        )

    def _apply_sell_fill(self, tracked: _TrackedOrder, delta) -> None:
        """Close (or reduce) a lot from a confirmed sell increment.

        The no-loss guard runs against the ACTUAL fill price, not the
        target that was quoted at submission. A limit sell can only fill
        at or above its limit, so this should always pass -- which is
        exactly why it is checked: a failure here means a real
        assumption broke, and the guard refusing to book the sale is
        preferable to silently recording a loss.
        """
        lot = next(
            (lot for lot in self.ledger.open_lots if lot.order_id == tracked.lot_order_id), None
        )
        if lot is None:
            logger.error(
                f"Sell fill for {tracked.client_order_id!r} references lot "
                f"{tracked.lot_order_id!r}, which is not open. Not applying -- reconcile."
            )
            return

        try:
            economics = validate_sell(
                lot,
                delta.qty,
                delta.avg_price,
                self.cost_model,
                prev_close=self.state.prev_close,
                reason=tracked.sell_reason,
            )
        except NoLossViolation:
            # Already logged by the guard. Deliberately not applied:
            # refusing to book it leaves the position visible and
            # reconcilable rather than quietly realizing a loss.
            return

        self.state.credit_sale(economics.net_sell_proceeds, self.settlement_days)
        self.ledger.close_lot(lot, sell_qty=delta.qty, execution_price=delta.avg_price)
        self.store.sync_lot(self.ledger, lot)
        logger.info(
            f"SELL filled: {delta.qty} @ {delta.avg_price} "
            f"(net ${economics.net_sell_proceeds:.2f}); cash={self.state.cash:.2f}"
        )

    # --- context ---

    def _build_context(self, bar, price: float) -> MarketContext:
        """Build this tick's MarketContext.

        Peak equity and drawdown are updated every tick, not only on
        triggering ones -- bug B3's fix, and the same ordering
        _simulate_single uses: the peak must already include this tick
        before drawdown is measured against it.
        """
        open_assets = sum(lot.shares * price for lot in self.ledger.open_lots)
        equity = self.state.cash + open_assets
        if equity > self.state.peak_equity:
            self.state.peak_equity = equity
        drawdown = (
            (self.state.peak_equity - equity) / self.state.peak_equity
            if self.state.peak_equity > 0
            else 0.0
        )
        self.state.max_drawdown = max(self.state.max_drawdown, drawdown)

        if self.state.last_buy_price is None:
            # First tick of a fresh deployment: the grid needs a
            # reference price and there is no prior buy. The current
            # price is the honest starting reference -- the same thing
            # BacktestState does with the first bar's close.
            self.state.last_buy_price = price

        timestamp = bar.timestamp
        if timestamp.tzinfo is None:
            timestamp = timestamp.replace(tzinfo=UTC)

        if self._event_table is not None:
            event_intensity, minutes_to_event = self._event_table.scalar(timestamp)
        else:
            event_intensity, minutes_to_event = 0.0, -1.0

        return MarketContext(
            timestamp=timestamp,
            open=bar.open,
            high=bar.high,
            low=bar.low,
            close=price,
            cash=self.state.cash,
            equity=equity,
            peak_equity=self.state.peak_equity,
            drawdown=drawdown,
            open_lot_count=len(self.ledger.open_lots),
            bar_index=0,
            is_macro_event_day=is_fomc_day_at(timestamp),
            is_earnings_reaction_day=is_earnings_reaction_day_at(timestamp),
            time_of_day_flag=minutes_since_open(timestamp),
            volume=float(getattr(bar, "volume", 0.0) or 0.0),
            event_intensity=event_intensity,
            minutes_to_event=minutes_to_event,
            implied_vol_change=change_at(self._implied_vol_series, timestamp),
        )

    # --- order submission ---

    def _harvest(self, context: MarketContext) -> int:
        """Submit limit sells for every lot that has reached its target.

        A lot with a sell already in flight is skipped: re-offering it
        would put two sell orders against one position and could sell
        shares that no longer exist. Bounded per tick so one very large
        harvest cannot overrun the poll interval; the remainder is
        picked up next tick.
        """
        submitted = 0
        # Trailing exits, through the shared helper the backtest paths
        # also call. Lots with a sell in flight are excluded: that order
        # is resting at the lot's current target, so moving the target
        # would leave our ledger and the broker's live order disagreeing
        # about one lot's price.
        retargeted = decision_cycle.adjust_open_lot_targets(
            self.strategy, self.ledger, context, skip_order_ids=self.state.sells_in_flight
        )
        # Persist immediately, before any sell is submitted off the new
        # target. A crash between retargeting and the durable write would
        # otherwise restart with the OLD target while the broker may
        # already hold an order placed against the new one -- and
        # load_ledger's derivation check cannot catch that, since both
        # fields moved together and stay self-consistent.
        for lot in retargeted:
            self.store.record_open_lot(lot)
        marketable = self.ledger.get_marketable_lots(context.price)

        # Signal exits, through the shared helper the backtest paths call,
        # with the same in-flight exclusion retargeting uses: a lot whose
        # sell is already resting must not get a second order.
        #
        # Priced at context.price rather than at the lot's target. A
        # signal exit that rested above the market would simply not fill,
        # which is the one outcome it must not have -- the strategy asked
        # to be OUT. It stays a limit order (never a market order) so a
        # thin book cannot fill it arbitrarily far away; it is marketable
        # at submission, and an unfilled remainder is re-offered next
        # tick at the new price rather than chased.
        liquidations = decision_cycle.collect_liquidations(
            self.strategy,
            self.ledger,
            context,
            allow_signal_exit=self.config.execution.allow_signal_exit,
            skip_order_ids=self.state.sells_in_flight,
        )
        exits = [(lot, context.price, SellReason.SIGNAL_EXIT) for lot in liquidations]
        if liquidations:
            condemned = {lot.order_id for lot in liquidations}
            marketable = [lot for lot in marketable if lot.order_id not in condemned]
        exits.extend((lot, lot.target_sell_price, SellReason.PROFIT_TARGET) for lot in marketable)

        # The per-tick bound applies to the COMBINED list, not to each
        # kind separately, because it exists to keep one tick inside the
        # poll interval and the broker does not care why an order was
        # sent. Signal exits are ordered first, so a harvest large enough
        # to fill the budget defers other harvests rather than the exit a
        # strategy asked for.
        for lot, sell_price, sell_reason in exits[: self.config.live.max_sells_per_tick]:
            if lot.order_id in self.state.sells_in_flight:
                continue
            decision_id = self._decision_id("SELL", context.timestamp, lot.order_id)
            outcome = self.guard.submit_once(
                decision_id,
                lambda cid, lot=lot, sell_price=sell_price: str(
                    self.broker.submit_sell(
                        self.symbol, lot.shares, sell_price, client_order_id=cid
                    ).id
                ),
                event_kind="sell_submission",
            )
            if not outcome.submitted_now:
                continue
            if sell_reason is SellReason.SIGNAL_EXIT:
                logger.warning(
                    f"SIGNAL EXIT submitted for lot {lot.order_id} "
                    f"({lot.shares} @ {sell_price}, bought at {lot.buy_price}): "
                    "this sell is permitted to realize a loss."
                )
            self.state.open_orders[decision_id] = _TrackedOrder(
                client_order_id=decision_id,
                kind="sell",
                tracker=FillTracker(decision_id),
                lot_order_id=lot.order_id,
                sell_reason=sell_reason,
            )
            self.state.sells_in_flight.add(lot.order_id)
            submitted += 1
        return submitted

    def _maybe_buy(self, context: MarketContext) -> int:
        """Evaluate the grid trigger and submit a buy if one is due.

        Passes self.state.buying_power -- post-harvest, confirmed,
        SETTLED cash -- rather than context.cash, matching what
        _simulate_single passes and what decision_cycle.py's docstring
        requires.

        This said `self.state.cash` and claimed parity with
        _simulate_single after that function had switched to settled
        buying power. The claim was false and the divergence was real:
        with execution.settlement_days set, the backtest honoured T+1
        and live spent unsettled proceeds -- trading more aggressively
        than anything that had been simulated, in the one account type
        where that is a rule violation rather than a preference.
        """
        decision = decision_cycle.evaluate_grid_decision(
            self.strategy,
            self.risk_manager,
            context,
            self.state.last_buy_price,
            self.step,
            self.state.buying_power,
        )
        if not decision.triggered:
            return 0

        trade_value = decision.clamped_trade_value
        if trade_value <= 0 or self.state.buying_power < trade_value:
            return 0

        decision_id = self._decision_id("BUY", context.timestamp)
        outcome = self.guard.submit_once(
            decision_id,
            lambda cid: str(
                self.broker.submit_buy(self.symbol, trade_value, client_order_id=cid).id
            ),
            event_kind="buy_submission",
        )
        if not outcome.submitted_now:
            return 0

        self.state.open_orders[decision_id] = _TrackedOrder(
            client_order_id=decision_id,
            kind="buy",
            tracker=FillTracker(decision_id),
            trigger_price=context.price,
            profit_target=self.profit_target,
        )
        return 1

    def _decision_id(self, decision_type: str, timestamp: datetime, suffix: str = "") -> str:
        """The stable id used as both the audit key and the Alpaca
        client_order_id.

        Derived from the bar's own timestamp, so a tick that re-reads
        the same bar -- which happens whenever the poll interval is
        shorter than the bar interval -- recomputes the SAME id. The
        duplicate-order guard then refuses the second submission. That
        is not incidental: it is what stops a fast poll loop from
        buying the same signal repeatedly, and it falls out of the
        identity scheme rather than needing a separate throttle.
        """
        market_event_id = timestamp.isoformat()
        if suffix:
            market_event_id = f"{market_event_id}#{suffix}"
        return compute_decision_id(
            deployment_id=self.deployment_id,
            strategy_id=self.config.strategy.strategy_id,
            symbol=self.symbol,
            market_event_id=market_event_id,
            decision_type=decision_type,
            sequence_number=0,
        )

    # --- persistence ---

    def persist_state(self) -> None:
        """Write through the non-lot state.

        Lots are persisted as they change (record_open_lot/sync_lot);
        these two scalars have no natural event to hang off, so they are
        written at the end of every tick. Cheap, and it means a crash
        loses at most one tick of drift rather than a session's.
        """
        self.store.set_meta(
            _META_UNSETTLED,
            json.dumps({
                "session": self.state.session,
                "unsettled": self.state.unsettled,
                "pending": self.state.pending,
            }),
        )
        self.store.set_meta(_META_CASH, str(self.state.cash))
        self.store.set_meta(_META_PEAK_EQUITY, str(self.state.peak_equity))

    def in_flight_settled(self) -> bool:
        """Whether nothing is awaiting a fill.

        Wired to RuntimeLifecycle.shutdown's bounded settle window: an
        in-flight order that lands mid-shutdown must still be accounted
        for, or the next startup reconciles against state that never
        recorded it.
        """
        return not self.state.open_orders
