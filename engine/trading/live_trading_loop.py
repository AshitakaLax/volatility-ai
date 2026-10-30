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
--------------------------------------------------------------------
HISTORY BEFORE THE FIRST TICK. A backtest's strategy has watched every
bar since the run began; a live process starts each session cold. A
strategy that declares live_history_sessions() is handed that many
sessions of bars (history_provider; engine/trading/live_history.py says
why each choice there) through record_tick before the first tick, then
resume(open_lots) with the durable book -- the state a restart loses that
no bar can rebuild. A strategy that wants history and gets no source is
refused rather than started blind.
--------------------------------------------------------------------
A DECISION THE BROKER COULD NOT TAKE. A BrokerUnavailableError skips the
rest of the tick: nothing was sent (an order that MAY have been is
AmbiguousSubmissionError, which halts). Most strategies decide again on
every bar, so the next tick covers it. One that decides once -- ultimate_rsp
rebalances at one minute of the session -- would lose the whole session's
decision (10-26: the extension did not answer the rebalance's preview, and
nothing was bought until the next day). If the failure came after the bar
reached record_tick, a strategy that declares decision_not_sent() is told,
and decides again on the next bar. Never called in a backtest, which has
no broker to fail.
--------------------------------------------------------------------
ON THE VENUE'S OWN WINDOWS (live.sessions, a `calendar` here). The loop is
up before the first window it trades and through the gaps between them, and
three things change:

  * WHEN IT TRADES. Bars are watched whenever the venue has any (its whole
    day, 04:00-20:00 ET); orders are placed only inside a traded window, and
    not in its last live.orders.session_close_margin_seconds. A strategy
    built on regular-session bars (`regular_session_only`) sees and trades
    the regular session's alone, however early the engine started.
  * EVERY ORDER IS A LIMIT AND IS WATCHED. Each carries its window. A buy
    left resting for live.orders.ttl_seconds outside the regular session is
    cancelled, and every order of a window is cancelled before it ends and
    confirmed gone -- a pre-market order Fidelity expires at 09:28 is not
    assumed gone. A resting buy holds back its cash. Each order's life goes
    to `order_listener` (the orders journal): the proof it filled or not.
  * EACH WINDOW IS AUDITED when it ends: every order it placed must be
    terminal at the venue and, once nothing is open, the venue's position
    must equal the ledger's -- or new buys halt for reconciliation, naming
    what disagrees. `last_window` says how the window went.

Without a calendar none of this runs and every tick is what it always was.
--------------------------------------------------------------------
WHAT IT SAYS ABOUT ITSELF, for whoever watches it (the Live page, through
the trader's status file -- engine/trading/operator_control.py):

  decision      after every tick: the price a buy triggers at (None when
                the strategy will buy at no price right now), the reference
                it measures from, what blocks a buy, and the strategy's own
                diagnostics() -- Ultimate's regime among them.
  shadow        the CONFIG FILE's algorithm while an override trades in its
                place: fed the same bars, trading nothing, so a reader can
                see what switching back would do now (which lots its exit
                would sell) before doing it.
  recent_bars   the last sessions of the replayed history; last_bar each
                tick's bar -- the feed the loop actually traded on.
  fills         every fill as it is booked, to fill_listener: the ledger
                keeps lots, never what a sale fetched.

None of it feeds back into a decision, and none of it may stop a tick: a
report that fails is dropped.
"""

from __future__ import annotations

import json
import logging
import math
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from decimal import ROUND_FLOOR, Decimal

from engine.core.config import BacktestConfig
from engine.core.exceptions import BrokerUnavailableError, ConfigurationError, PersistenceError
from engine.core.idempotency import compute_decision_id
from engine.core.ledger import EXIT_AT_COST_TARGET, SHARE_EPSILON
from engine.core.market_context import MarketContext
from engine.core.retry_policy import AmbiguousSubmissionError
from engine.core.venue_sessions import AFTER_HOURS, PRE_MARKET, REGULAR
from engine.data.earnings_calendar import is_earnings_reaction_day_at
from engine.data.fomc_calendar import is_fomc_day_at
from engine.data.implied_vol_signal import change_at
from engine.data.intraday_profile import minutes_since_open
from engine.data.tick_validation import TickValidator
from engine.execution import limit_pricing
from engine.execution.cost_models import ZeroCostModel
from engine.execution.fill_accounting import FillTracker, extract_alpaca_fill
from engine.execution.order_lifecycle import TERMINAL_STATES, OrderState, map_broker_status
from engine.trading import decision_cycle
from engine.trading.duplicate_order_guard import DuplicateOrderGuard
from engine.trading.live_history import EASTERN, last_sessions
from engine.trading.no_loss_guard import NoLossViolation, SellReason, validate_sell
from engine.trading.risk_manager import CircuitBreaker, RiskManager

logger = logging.getLogger("Optimizer")

# Completed sessions of the replayed history kept for a reader's chart.
RECENT_SESSIONS = 5
# On the venue's windows: a bar older than this is recorded, never traded on.
TRADABLE_BAR_AGE_SECONDS = 120.0
# How long after a window ends its orders must all be terminal at the venue.
WINDOW_AUDIT_GRACE_SECONDS = 180.0
# During shutdown, how often the venue is asked about orders still settling.
SETTLE_POLL_SECONDS = 5.0
EXTENDED_SESSIONS = (PRE_MARKET, AFTER_HOURS)


# The order events that end an order's life.
_FINAL_EVENTS = ("filled", "cancelled", "expired", "rejected")
_FINAL_EVENT = {
    OrderState.FILLED: "filled",
    OrderState.CANCELED: "cancelled",
    OrderState.EXPIRED: "expired",
    OrderState.REJECTED: "rejected",
}


def _seconds(value: float):
    from datetime import timedelta

    return timedelta(seconds=float(value))


def _floor_shares(qty: float) -> float:
    """Down to the nine decimals a fractional order may carry, never up:
    an order for more shares than the lots hold would sell what we do not
    own."""
    return float(Decimal(str(qty)).quantize(Decimal("0.000000001"), rounding=ROUND_FLOOR))


# Durable keys for the scalars that are not lots. Namespaced so they
# cannot collide with Task 7.8's halt keys in the same meta table.
_META_CASH = "live.cash"
# Unsettled proceeds and their maturity sessions, as JSON. Persisted
# because a restart that forgot them would treat unsettled money as
# spendable and trade MORE aggressively than the backtest modelled --
# in a cash account, that is extra good-faith violations.
_META_UNSETTLED = "live.unsettled"
_META_PEAK_EQUITY = "live.peak_equity"
# The last observed price and the moment it was observed. A real
# heartbeat, unlike the store's file mtime, which cannot tell a
# stopped loop from a closed market.
_META_LAST_TICK = "live.last_tick"
_META_OPEN_ORDERS = "live.open_orders"
_META_PARAMETERS = "live.parameters"
# The algorithm switch whose "what to do with the lots held" has been applied
# (its changedAt stamp), so a restart does not apply it twice.
_META_TRANSITION = "live.transition"
# The owner of lots an earlier algorithm bought and a switch left to exit at
# their own targets (persistence: ledger_lot_owners).
LEGACY_OWNER = "legacy"


def seed_fresh_ledger(store, cash: float) -> None:
    """A new ledger's starting book: the broker's cash, and drawdown measured
    from the first tick (the Live page's "fresh paper ledger" --
    engine/trading/operator_control.py). Without the cash the loop would
    start from the config's initial_cash, which a reset paper account need
    not hold."""
    store.set_meta(_META_CASH, str(float(cash)))
    reset_drawdown_baseline(store)


def reset_drawdown_baseline(store) -> None:
    """Make the next run measure drawdown from its first tick's equity
    (LiveTradingLoop.reset_drawdown_baseline, for a store no loop holds --
    the supervisor applying an operator's resume between sessions)."""
    store.set_meta(_META_PEAK_EQUITY, "0.0")


def _history_sessions(strategy) -> int:
    wanted = getattr(strategy, "live_history_sessions", None)
    return int(wanted()) if callable(wanted) else 0


def _diagnostics(strategy) -> dict | None:
    """A strategy's own diagnostics(), as plain JSON values; None when it
    offers none or they fail. Outside the SizingStrategy contract (as in
    regime_scaled_sizing.py), so asked for, never required."""
    report = getattr(strategy, "diagnostics", None)
    if not callable(report):
        return None
    try:
        raw = dict(report() or {})
    except Exception as exc:
        logger.warning(f"{type(strategy).__name__}.diagnostics() failed: {exc}")
        return None
    plain = {}
    for key, value in raw.items():
        value = value.item() if hasattr(value, "item") else value  # numpy scalars
        if isinstance(value, float) and not math.isfinite(value):
            value = None
        if value is None or isinstance(value, bool | int | float | str):
            plain[str(key)] = value
    return plain


def _buy_level(strategy, context: MarketContext, last_buy_price, step: float) -> float | None:
    """The price at or below which `strategy` buys on this bar -- its own
    _grid_trigger_level, the one definition the buy decision uses -- or None
    when it would buy at no price (NO_BUY_LEVEL) or cannot say."""
    if last_buy_price is None:
        return None
    try:
        level = float(strategy._grid_trigger_level(context, last_buy_price, step))
    except Exception:
        return None
    return level if math.isfinite(level) and level > 0 else None


def _bar_rows(frame) -> list[dict]:
    """Minute bars as the trader's bar journal keeps them."""
    if frame is None or len(frame) == 0:
        return []
    columns = [frame[name].to_numpy(float) for name in ("open", "high", "low", "close")]
    volume = frame["volume"].to_numpy(float) if "volume" in frame.columns else [0.0] * len(frame)
    return [
        {
            "t": int(ts.timestamp()),
            "o": float(columns[0][i]),
            "h": float(columns[1][i]),
            "l": float(columns[2][i]),
            "c": float(columns[3][i]),
            "v": float(volume[i]),
        }
        for i, ts in enumerate(frame.index)
    ]


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
    # A SIGNAL EXIT sells many lots in ONE order (_submit_exit): their ids,
    # in the order fills are allocated to them. Empty for every other order.
    exit_lot_ids: tuple[str, ...] = ()
    # The bar it was submitted on, and whether a cancel has been asked: an
    # exit still resting on a later bar is cancelled and re-offered.
    submitted_bar: str | None = None
    cancel_requested: bool = False
    # On the venue's windows (module docstring): the window it was placed in,
    # when, its limit and size, when it must be gone by, the dollars a resting
    # buy holds back from buying power, and why a cancel was asked.
    session: str | None = None
    submitted_at: str | None = None
    expires_at: str | None = None
    limit_price: float | None = None
    qty: float | None = None
    reserve: float = 0.0
    cancel_reason: str | None = None

    @property
    def lot_ids(self) -> tuple[str, ...]:
        """Every lot this order sells."""
        if self.exit_lot_ids:
            return self.exit_lot_ids
        return (self.lot_order_id,) if self.lot_order_id is not None else ()

    def to_dict(self) -> dict:
        """Durable form, INCLUDING the tracker's cumulative counters.

        The counters are the whole point. A restart that rebuilt this
        table with fresh FillTrackers would read the broker's CUMULATIVE
        figures against a zero baseline and book the entire fill again
        as a new increment -- double-counting an execution that was
        already applied. That is worse than the state it replaces, so
        cumulative_qty and cumulative_notional travel with the order.
        """
        return {
            "client_order_id": self.client_order_id,
            "kind": self.kind,
            "lot_order_id": self.lot_order_id,
            "trigger_price": self.trigger_price,
            "profit_target": self.profit_target,
            "sell_reason": str(self.sell_reason),
            "exit_lot_ids": list(self.exit_lot_ids),
            "submitted_bar": self.submitted_bar,
            "cancel_requested": self.cancel_requested,
            "session": self.session,
            "submitted_at": self.submitted_at,
            "expires_at": self.expires_at,
            "limit_price": self.limit_price,
            "qty": self.qty,
            "reserve": self.reserve,
            "cancel_reason": self.cancel_reason,
            "cumulative_qty": self.tracker.cumulative_qty,
            "cumulative_notional": self.tracker.cumulative_notional,
        }

    @classmethod
    def from_dict(cls, raw: dict) -> _TrackedOrder:
        """Rebuild one tracked order, restoring the tracker's baseline."""
        tracker = FillTracker(raw["client_order_id"])
        tracker.restore(float(raw["cumulative_qty"]), float(raw["cumulative_notional"]))
        return cls(
            client_order_id=raw["client_order_id"],
            kind=raw["kind"],
            tracker=tracker,
            lot_order_id=raw.get("lot_order_id"),
            trigger_price=float(raw.get("trigger_price", 0.0)),
            profit_target=float(raw.get("profit_target", 0.0)),
            sell_reason=SellReason(raw.get("sell_reason", SellReason.PROFIT_TARGET)),
            exit_lot_ids=tuple(raw.get("exit_lot_ids") or ()),
            submitted_bar=raw.get("submitted_bar"),
            cancel_requested=bool(raw.get("cancel_requested", False)),
            session=raw.get("session"),
            submitted_at=raw.get("submitted_at"),
            expires_at=raw.get("expires_at"),
            limit_price=raw.get("limit_price"),
            qty=raw.get("qty"),
            reserve=float(raw.get("reserve") or 0.0),
            cancel_reason=raw.get("cancel_reason"),
        )


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

    # The most recent accepted tick. Written every tick so a reader has
    # a mark to value the book at without being told one by hand.
    last_tick_price: float | None = None
    last_tick_at: str | None = None

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
        tick_listener: Callable[[dict], None] | None = None,
        history_provider: Callable[[str, int], object] | None = None,
        shadow=None,
        fill_listener: Callable[[dict], None] | None = None,
        calendar=None,
        order_listener: Callable[[dict], None] | None = None,
        now: Callable[[], datetime] | None = None,
        transition: dict | None = None,
    ) -> None:
        """Assemble the loop and load durable state.

        transition is the algorithm override in force (the Live page's switch):
        its `legacy_lots` says what to do with the lots held at the switch,
        applied once (`_apply_transition`).

        tick_listener, if given, is told what each tick of run_forever
        did -- {"at", "reason", ...} -- so whatever supervises the loop
        can show that it is alive and why it is or is not trading. Its
        failures are logged and never reach the loop.

        fill_listener, likewise, is told every fill as it is booked --
        {"t", "side", "lot", "qty", "price", ...}. shadow is a second
        strategy fed every bar and asked what it would do, trading nothing
        (module docstring, WHAT IT SAYS ABOUT ITSELF).

        calendar (engine/core/venue_sessions.VenueCalendar) puts the loop on
        its venue's own windows (module docstring, ON THE VENUE'S OWN
        WINDOWS); order_listener is told each moment of an order's life;
        `now` is the wall clock those windows are read against. `broker` may
        be None to build the loop -- and replay its history -- before the
        broker is connected (attach_broker).

        history_provider(symbol, sessions) returns that many sessions of
        regular-hours minute bars (a DataFrame: UTC index, open/high/low/
        close/volume), replayed through the strategy before the first tick
        when the strategy asks for any -- see the module docstring.

        Refuses to construct on a config that does not name a single
        live step and profit_target. Those are validated here rather
        than in BacktestConfig.validate() because this loop is the only
        thing that needs them -- and it needs them absolutely, since
        they ARE the strategy that real capital will trade.
        """
        config.validate()
        self.extended_hours = bool(getattr(config.live, "extended_hours", False))
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
            from engine.core.exceptions import DataValidationError as _DataValidationError
            from engine.data.event_calendar import EarningsEventTable

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
                from engine.data.implied_vol_signal import load_implied_vol_change

                self._implied_vol_series = load_implied_vol_change(implied_vol_path)
            except (FileNotFoundError, _DataValidationError) as e:
                logger.warning(
                    f"No implied-vol series loaded from {implied_vol_path} ({e}); "
                    "implied_vol_change stays 0.0."
                )
        self._sleep = sleep
        self._tick_listener = tick_listener
        self._fill_listener = fill_listener
        self._order_listener = order_listener
        self.calendar = calendar
        self._now = now or (lambda: datetime.now(UTC))
        # On the venue's windows: the traded window this tick is in, the last
        # bar fed to the strategy, the windows already audited, and how the
        # last one went (for the status).
        self.window = None
        self._last_bar_at: datetime | None = None
        self._audited: set[tuple[str, str]] = set()
        self.last_window: dict | None = None
        self._last_settle_poll: float | None = None
        self._orders_seen: dict[str, dict] = {}
        # Why this bar's buy was not placed (limit_pricing's answer), once.
        self._buy_note: str | None = None
        self.shadow = shadow
        # What the loop says about itself after each tick (module docstring).
        self.decision: dict | None = None
        self.shadow_state: dict | None = None
        self.last_bar: dict | None = None
        self.recent_bars: list[dict] = []
        self._stop_requested = False
        # Why the broker could not be reached, while it cannot; None when
        # it can. Readable by whatever supervises the loop.
        self.broker_unavailable: str | None = None
        self._unavailable_ticks = 0
        # Whether this tick's bar reached the strategy's record_tick: a
        # broker that fails after that has cost the strategy its decision.
        self._decided = False

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
        self._restore_open_orders(store.get_meta(_META_OPEN_ORDERS))
        self._legacy: set[str] = {
            order_id for order_id, owner in store.lot_owners().items() if owner == LEGACY_OWNER
        }
        self._apply_transition(transition)
        self.replayed_bars = self._prepare_strategy(history_provider)
        logger.info(
            f"LiveTradingLoop ready: symbol={self.symbol} step={self.step} "
            f"profit_target={self.profit_target} cash={self.state.cash:.2f} "
            f"open_lots={len(self.ledger.open_lots)} history_bars={self.replayed_bars}"
        )

    def _apply_transition(self, override: dict | None) -> None:
        """What a switch does with the lots held when it was made, once.

        "keep" (the default for a switch): they are the legacy book. They
        stay and exit at their own targets, but the new algorithm neither
        sees nor retargets nor liquidates them, and its grid starts from the
        price now rather than the old algorithm's last buy. "exit_at_cost"
        does the same and moves their targets to the smallest gain that
        clears cost. Anything else (a switch made when flat, a revert) is a
        no-op.
        """
        if override is None and self._legacy:
            # Reverted to the config file's algorithm: the lots it left
            # selling are its own again.
            self.store.clear_lot_owners()
            logger.info(f"Reverted: {len(self._legacy)} legacy lot(s) are the algorithm's again")
            self._legacy.clear()
            self.store.set_meta(_META_TRANSITION, None)
            return
        mode = (override or {}).get("legacy_lots")
        stamp = (override or {}).get("changedAt")
        if mode not in ("keep", "exit_at_cost") or not stamp:
            return
        if self.store.get_meta(_META_TRANSITION) == stamp:
            return
        held = [lot for lot in self.ledger.open_lots if lot.order_id not in self._legacy]
        if mode == "exit_at_cost":
            for lot in held:
                if lot.profit_target > EXIT_AT_COST_TARGET:
                    lot.retarget(EXIT_AT_COST_TARGET)
                    self.store.record_open_lot(lot)
        if held:
            self.store.set_lot_owners([lot.order_id for lot in held], LEGACY_OWNER)
            self._legacy.update(lot.order_id for lot in held)
            self.state.last_buy_price = None
            self.store.set_meta("last_buy_price", None)
            logger.info(
                f"Algorithm switch ({mode}): {len(held)} lot(s) kept as the legacy book, "
                "exiting at their own targets; the new grid starts from the price now"
            )
        self.store.set_meta(_META_TRANSITION, str(stamp))

    @property
    def legacy_lots(self) -> list:
        """The open lots an earlier algorithm bought (see `_apply_transition`)."""
        return [lot for lot in self.ledger.open_lots if lot.order_id in self._legacy]

    def _own_lots(self) -> list:
        """The open lots the algorithm now trading may see: not the legacy book."""
        return [lot for lot in self.ledger.open_lots if lot.order_id not in self._legacy]

    def _prepare_strategy(self, history_provider) -> int:
        """Replay the history the strategy asks for, then hand it the
        durable book. Returns the number of bars replayed.

        The shadow, if any, gets the same treatment from the same fetch --
        the larger of the two asks -- each replaying only the sessions it
        wants. A shadow that cannot be prepared is dropped, never a reason
        not to trade."""
        sessions = _history_sessions(self.strategy)
        shadow_sessions = _history_sessions(self.shadow) if self.shadow is not None else 0
        if sessions > 0 and history_provider is None:
            raise ConfigurationError(
                f"{type(self.strategy).__name__} needs {sessions} sessions of history "
                "before its first live tick, and no history source was given. Without "
                "it the strategy starts each session cold -- not the strategy that was "
                "backtested."
            )
        replayed = 0
        fetch = max(sessions, shadow_sessions) if history_provider is not None else 0
        if fetch > 0:
            bars = history_provider(self.symbol, fetch)
            today = datetime.now(UTC).astimezone(EASTERN).date()

            def tail(wanted: int):
                # The provider returned the larger ask; the smaller takes its
                # own last sessions of it (all of it, if they cannot be told).
                if wanted >= fetch:
                    return bars
                try:
                    return last_sessions(bars, wanted, today)
                except (AttributeError, TypeError):
                    return bars

            if sessions > 0:
                replayed = self.replay_history(tail(sessions))
            if shadow_sessions > 0:
                try:
                    self.replay_history(tail(shadow_sessions), strategy=self.shadow)
                except Exception as exc:
                    self._drop_shadow(exc)
            try:
                self.recent_bars = _bar_rows(last_sessions(bars, RECENT_SESSIONS, today))
            except Exception as exc:  # for a reader's chart only
                logger.warning(f"No recent bars kept for the chart: {exc}")
        for strategy in (self.strategy, self.shadow):
            resume = getattr(strategy, "resume", None)
            if callable(resume):
                try:
                    resume(self._own_lots())
                except Exception as exc:
                    if strategy is self.strategy:
                        raise
                    self._drop_shadow(exc)
        return replayed

    def _drop_shadow(self, exc: Exception) -> None:
        if self.shadow is not None:
            logger.warning(
                f"Dropped the shadow {type(self.shadow).__name__} ({type(exc).__name__}: {exc}); "
                "trading is unaffected."
            )
        self.shadow = None
        self.shadow_state = None

    def replay_history(self, bars, strategy=None) -> int:
        """Feed past bars to the strategy's record_tick (or `strategy`'s),
        oldest first.

        Each context carries the bar's own market fields and a NEUTRAL
        portfolio -- no cash, no equity, no drawdown -- with the book's
        current open-lot count, so the replay moves only market state:
        nothing a strategy captures from equity (the champion's lot
        baseline) is taken from it, and no bar looks like a buy. Nothing
        is traded and nothing is persisted.
        """
        if bars is None or len(bars) == 0:
            return 0
        if not bars.index.is_monotonic_increasing:
            raise ConfigurationError("history bars must be in ascending time order")
        open_lot_count = len(self.ledger.open_lots)
        columns = [bars[name].to_numpy(float) for name in ("open", "high", "low", "close")]
        volume = bars["volume"].to_numpy(float) if "volume" in bars.columns else [0.0] * len(bars)
        for i, ts in enumerate(bars.index):
            timestamp = ts.to_pydatetime() if hasattr(ts, "to_pydatetime") else ts
            context = self._market_context(
                timestamp,
                columns[0][i],
                columns[1][i],
                columns[2][i],
                columns[3][i],
                volume[i],
                cash=0.0,
                equity=0.0,
                peak_equity=0.0,
                drawdown=0.0,
                open_lot_count=open_lot_count,
            )
            decision_cycle.record_tick(strategy or self.strategy, context)
        return len(bars)

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
            self.state.session = int(saved["session"])
            self.state.unsettled = float(saved["unsettled"])
            self.state.pending = [[int(d), float(a)] for d, a in saved["pending"]]
        except (TypeError, ValueError, KeyError) as exc:
            self.state.unsettled = self.state.cash
            self.state.pending = []
            logger.warning(
                f"Settlement state unreadable ({exc}); treating the whole "
                f"${self.state.cash:.2f} balance as unsettled until the next "
                "session. This under-trades deliberately -- the alternative "
                "is spending money that may not have settled."
            )

    def _restore_open_orders(self, raw: str | None) -> None:
        """Reload the in-flight order table, or refuse to start.

        WHY THIS EXISTS. open_orders and sells_in_flight used to be
        memory-only. Any restart that was not a clean shutdown -- a
        crash, an OOM kill, a redeploy, the scheduled task firing --
        forgot every resting order. Three things followed, none of them
        detectable at the time:

          * the fill was never applied, so cash and the ledger silently
            missed an execution that really happened;
          * sells_in_flight came back empty, so a lot with a live
            resting sell was eligible for a SECOND sell, and the
            duplicate guard could not stop it (its decision_id is
            derived from the bar timestamp, which differs);
          * startup reconciliation could not catch either, because a
            RESTING order leaves positions agreeing.

        CORRUPT STATE RAISES rather than defaulting to empty. Empty is
        precisely the broken behaviour this method replaces, and
        "in-flight orders unknown" is not a state in which it is safe to
        harvest -- a second sell against shares already sold is the
        outcome. Failing to start leaves the position visible, the
        durable submission records intact, and a human to clear it.

        ABSENT state is a different fact: nothing was ever written, so
        there is nothing in flight. That is the fresh-deployment case
        and the same distinction _restore_settlement draws.
        """
        if raw is None:
            return
        try:
            restored = {
                entry["client_order_id"]: _TrackedOrder.from_dict(entry)
                for entry in json.loads(raw)
            }
        except (TypeError, ValueError, KeyError) as exc:
            raise PersistenceError(
                f"In-flight order state is unreadable ({exc}). Refusing to start: an unknown "
                "set of resting orders cannot be harvested against without risking a second "
                f"sell of shares already sold. Inspect {_META_OPEN_ORDERS!r} in the store, "
                "reconcile against the broker, and clear it once the truth is known."
            ) from exc

        self.state.open_orders = restored
        # DERIVED, never stored separately. The two are maintained in
        # lockstep at every mutation site, so persisting both would
        # create a second source of truth that could disagree with the
        # first -- and the failure mode of disagreement is the double
        # sell this whole method exists to prevent.
        self.state.sells_in_flight = {
            lot_id
            for order in restored.values()
            if order.kind == "sell"
            for lot_id in order.lot_ids
        }
        if restored:
            logger.warning(
                f"Restored {len(restored)} in-flight order(s) from durable state: "
                f"{sorted(restored)}. Their fills will be applied on the next poll."
            )

    def _persist_open_orders(self) -> None:
        """Write the in-flight order table through.

        Called at every mutation of the table rather than once per tick,
        matching how lots are handled: a crash between submitting an
        order and the durable write is exactly the window that made this
        state unreliable, and _harvest can submit up to
        max_sells_per_tick orders inside one tick.
        """
        self.store.set_meta(
            _META_OPEN_ORDERS,
            json.dumps([order.to_dict() for order in self.state.open_orders.values()]),
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

    def reset_drawdown_baseline(self) -> None:
        """Measure drawdown from the next tick's equity again, not from the
        old peak -- an operator resuming buys after a drawdown halt, who
        would otherwise see it trip again on the next tick. Zero is enough:
        _build_context raises the peak to the tick's equity before it
        measures. Strategies that size on drawdown see it reset too."""
        self.state.peak_equity = 0.0
        reset_drawdown_baseline(self.store)

    def is_flat(self) -> bool:
        """No open lots and nothing awaiting a fill."""
        return not self.ledger.open_lots and self.in_flight_settled()

    # --- the tick ---

    def _session_is_open(self) -> bool:
        """Whether the loop should tick, per the session it trades.

        Alpaca's clock reports the REGULAR session only, so gating on it
        meant the loop never woke outside 09:30-16:00 ET. With
        extended_hours enabled that made the whole feature inert: the
        broker could build a pre-market limit order perfectly well, and
        nothing ever asked it to, because run_once had already returned
        "market_closed" an hour before the pre-market session began.

        Refuses rather than falling back when the data source cannot
        answer the extended question. Silently using the regular clock
        would reproduce exactly the inertness above, and it would look
        like the flag was on and working.
        """
        if not self.extended_hours:
            return self.market_data.is_open()
        extended = getattr(self.market_data, "is_open_extended", None)
        if extended is None:
            raise ConfigurationError(
                f"live.extended_hours is enabled but {type(self.market_data).__name__} "
                "has no is_open_extended(). Falling back to the regular-session clock "
                "would leave the loop asleep during exactly the hours the flag was "
                "turned on for."
            )
        return bool(extended())

    def run_once(self) -> TickOutcome:
        """One full cycle. Returns what it did, including why it skipped.

        Fills are applied FIRST, before anything reads cash or lots, so
        the tick's sizing decisions see confirmed reality rather than
        state that is one fill stale.
        """
        self._decided = False
        if self.calendar is not None:
            return self._run_once_on_windows()
        if not self._session_is_open():
            return TickOutcome(acted=False, reason="market_closed")

        from engine.core.exceptions import DataValidationError

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
        self.state.last_tick_price = float(price)
        self.state.last_tick_at = bar.timestamp.isoformat()
        self.last_bar = {
            "t": int(bar.timestamp.timestamp()),
            "o": float(bar.open),
            "h": float(bar.high),
            "l": float(bar.low),
            "c": float(bar.close),
            "v": float(getattr(bar, "volume", 0.0) or 0.0),
        }

        # Phase 1, unconditionally and before any harvest.
        decision_cycle.record_tick(self.strategy, context)
        self._decided = True
        if self.shadow is not None:
            try:
                decision_cycle.record_tick(self.shadow, context)
            except Exception as exc:
                self._drop_shadow(exc)

        sells = self._harvest(context)

        # Task 7.8: the drawdown halt blocks NEW BUYS only. record_tick
        # above already ran and the harvest above already ran, so a
        # halted loop still tracks the market and still exits open lots.
        self.circuit_breaker.evaluate(
            context.drawdown, self.risk_manager.halt_new_buys_if_drawdown_exceeds
        )
        buys = self._maybe_buy(context) if self.circuit_breaker.allows_new_buys else 0
        self._describe(context)

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

    # --- on the venue's own windows (module docstring) ---

    def set_listeners(self, *, tick=None, fill=None, order=None) -> None:
        """Who hears the ticks, fills and order events of a loop built before
        its trading process was (cli.py's engine-first start)."""
        self._tick_listener, self._fill_listener, self._order_listener = tick, fill, order

    def attach_broker(self, broker) -> None:
        """The broker, once it is connected: a loop built before it (cli.py's
        engine-first start) has replayed its history and watched the market
        without one."""
        self.broker = broker

    def watch_once(self) -> TickOutcome:
        """A tick without the broker: the bar reaches the strategy, and
        nothing else happens -- no fill is read and no order placed. What an
        engine that is ready does while it waits for its broker, so its
        strategy misses no bar meanwhile."""
        self._decided = False
        now = self._now()
        if self.calendar is not None and not self.calendar.observing(now):
            return TickOutcome(acted=False, reason="market_closed")
        bar, price, skipped = self._next_bar(now)
        if skipped is not None:
            return skipped
        context = self._build_context(bar, price)
        self._record(context)
        self._decision_not_sent()  # whatever it decided, nothing was sent
        self._describe(context)
        self.state.prev_close = price
        return TickOutcome(acted=False, reason="watching", price=price)

    def _run_once_on_windows(self) -> TickOutcome:
        """run_once on the venue's windows: orders kept and audited every
        tick, bars watched across the venue's day, orders placed only inside
        a traded window."""
        now = self._now()
        self._buy_note = None
        if not self.calendar.observing(now):
            self.window = None
            return TickOutcome(acted=False, reason="market_closed")
        self.window = self.calendar.window_at(now)
        if self.settlement_days > 0:
            # The EASTERN date: after 19:00 ET in winter a bar's UTC date is
            # already tomorrow's, and T+1 cash must not settle a session early.
            day = now.astimezone(EASTERN).date().toordinal()
            if day != self.state.session:
                self.state.advance_session(day)

        broker_error = None
        fills = 0
        try:
            fills = self._poll_open_orders()
            self._expire_orders(now)
            self._audit_windows(now)
        except BrokerUnavailableError as exc:
            broker_error = exc

        bar, price, skipped = self._next_bar(now)
        if skipped is not None:
            if broker_error is not None:
                raise broker_error
            skipped.fills_applied = fills
            self.persist_state()
            return skipped

        context = self._build_context(bar, price)
        sees = self._record(context)
        if broker_error is not None:
            # The bar reached the strategy; nothing more without the broker.
            # run_forever persists and tells the strategy its decision was
            # not sent.
            raise broker_error

        why_not = self._why_not_trading(now, bar, sees)
        sells = buys = 0
        if why_not is None:
            sells = self._harvest(context)
        self.circuit_breaker.evaluate(
            context.drawdown, self.risk_manager.halt_new_buys_if_drawdown_exceeds
        )
        if why_not is None and self.circuit_breaker.allows_new_buys:
            buys = self._maybe_buy(context)
        if why_not is not None:
            self._decision_not_sent()
        self._describe(context)
        if why_not is not None and self.decision is not None:
            self.decision["blocked"] = why_not
        self.state.prev_close = price
        self.persist_state()
        return TickOutcome(
            acted=True,
            reason="ok" if why_not is None else "not_trading",
            price=price,
            fills_applied=fills,
            sells_submitted=sells,
            buys_submitted=buys,
        )

    def _next_bar(self, now: datetime):
        """(bar, price, None), or (None, None, the TickOutcome of a tick with
        no new bar to act on)."""
        from engine.core.exceptions import DataValidationError

        try:
            bar = self.market_data.latest_bar(self.symbol)
        except DataValidationError as e:
            reason = "feeds_disagree" if type(e).__name__ == "FeedsDisagree" else "no_data"
            logger.warning(f"No bar this tick: {e}")
            return None, None, TickOutcome(acted=False, reason=reason)
        stamp = bar.timestamp if bar.timestamp.tzinfo else bar.timestamp.replace(tzinfo=UTC)
        # Outside the regular session a minute often has no trade: the same
        # bar again is not a new one to the strategy.
        if (
            self.calendar is not None
            and self._last_bar_at is not None
            and stamp <= self._last_bar_at
        ):
            return None, None, TickOutcome(acted=False, reason="no_new_bar", price=bar.close)
        check = self.tick_validator.validate(bar.close)
        if not check.accepted:
            logger.warning(f"Tick rejected by validation: {bar.close}")
            return None, None, TickOutcome(acted=False, reason="tick_rejected", price=bar.close)
        self._last_bar_at = stamp
        price = check.price
        self.state.last_tick_price = float(price)
        self.state.last_tick_at = bar.timestamp.isoformat()
        self.last_bar = {
            "t": int(bar.timestamp.timestamp()),
            "o": float(bar.open),
            "h": float(bar.high),
            "l": float(bar.low),
            "c": float(bar.close),
            "v": float(getattr(bar, "volume", 0.0) or 0.0),
        }
        source = getattr(bar, "source", None)
        if source and source != "alpaca":
            self.last_bar["source"] = source
        return bar, price, None

    def _sees(self, strategy, timestamp: datetime) -> bool:
        """Whether `strategy` is fed this bar: one built on regular-session
        bars sees the regular session's alone."""
        if self.calendar is None or not getattr(strategy, "regular_session_only", False):
            return True
        return self.calendar.session_at(timestamp) == REGULAR

    def _record(self, context: MarketContext) -> bool:
        """record_tick for the strategy (and the shadow) that see this bar.
        Returns whether the strategy did."""
        sees = self._sees(self.strategy, context.timestamp)
        if sees:
            decision_cycle.record_tick(self.strategy, context)
            self._decided = True
        if self.shadow is not None and self._sees(self.shadow, context.timestamp):
            try:
                decision_cycle.record_tick(self.shadow, context)
            except Exception as exc:
                self._drop_shadow(exc)
        return sees

    def _why_not_trading(self, now: datetime, bar, sees: bool) -> str | None:
        """None when this tick may place orders; else why not, for the
        status."""
        window = self.window
        if window is None:
            upcoming = self.calendar.next_window(now)
            when = f"; the next opens {upcoming.start:%H:%M} ET" if upcoming is not None else ""
            return f"between trading windows{when}"
        if not sees or (
            getattr(self.strategy, "regular_session_only", False) and window.session != REGULAR
        ):
            return f"{type(self.strategy).__name__} trades the regular session only"
        orders = self.config.live.orders
        closing = window.end - _seconds(
            orders.session_close_margin_seconds + float(self.config.live.poll_interval_seconds)
        )
        if now >= closing:
            return f"the {window.session} window closes at {window.end:%H:%M} ET"
        stamp = bar.timestamp if bar.timestamp.tzinfo else bar.timestamp.replace(tzinfo=UTC)
        age = (now - stamp).total_seconds()
        if age > TRADABLE_BAR_AGE_SECONDS:
            return f"the last bar is {age:.0f}s old"
        unsupported = self._session_unsupported(window.session)
        if unsupported:
            return unsupported
        return None

    def _session_unsupported(self, session: str) -> str | None:
        """Why the broker cannot place an order in `session`, or None."""
        ask = getattr(self.broker, "session_support", None)
        if callable(ask):
            return ask(session)
        if session in EXTENDED_SESSIONS and not getattr(self.broker, "extended_hours", False):
            return f"{type(self.broker).__name__} places no {session} orders"
        return None

    def _order_kwargs(self) -> dict:
        """The window an order is placed in, for a broker on the venue's
        windows; nothing otherwise, so every other call is unchanged."""
        return {"session": self.window.session} if self.window is not None else {}

    def _window_fields(self, *, limit: float | None, qty: float | None, reserve: float) -> dict:
        if self.window is None:
            return {}
        now = self._now()
        margin = _seconds(self.config.live.orders.session_close_margin_seconds)
        return {
            "session": self.window.session,
            "submitted_at": now.isoformat(),
            "expires_at": (self.window.end - margin).isoformat(),
            "limit_price": float(limit) if limit is not None else None,
            "qty": float(qty) if qty is not None else None,
            "reserve": float(reserve),
        }

    def _quote(self):
        """This tick's quote from a second source, or None."""
        read = getattr(self.market_data, "quote", None)
        if not callable(read):
            return None
        try:
            return read(self.symbol)
        except Exception as exc:
            logger.warning(f"No quote this tick: {type(exc).__name__}: {exc}")
            return None

    def reserved(self) -> float:
        """Dollars held back by buys still resting: their limit x size, less
        what has filled (which cash already reflects)."""
        held = 0.0
        for tracked in self.state.open_orders.values():
            if tracked.kind == "buy" and tracked.reserve > 0:
                held += max(0.0, tracked.reserve - tracked.tracker.cumulative_notional)
        return held

    def _spendable(self) -> float:
        """Settled buying power, less what resting buys hold back on the
        venue's windows (where a buy can rest)."""
        power = self.state.buying_power
        if self.calendar is not None:
            power = max(0.0, power - self.reserved())
        return power

    def _expire_orders(self, now: datetime) -> None:
        """Cancel what must not rest any longer: every order a tick before
        its window's end (less the margin), and a buy outside the regular
        session once it has rested live.orders.ttl_seconds. Done when the
        venue reports it terminal (_poll_open_orders); a part that filled is
        booked as any fill is."""
        cancel = getattr(self.broker, "cancel_order", None)
        poll = _seconds(float(self.config.live.poll_interval_seconds))
        ttl = float(self.config.live.orders.ttl_seconds)
        changed = False
        for tracked in list(self.state.open_orders.values()):
            if tracked.cancel_requested:
                continue
            why = None
            if tracked.expires_at and now >= datetime.fromisoformat(tracked.expires_at) - poll:
                why = "session_end"
            elif (
                tracked.kind == "buy"
                and tracked.session in EXTENDED_SESSIONS
                and tracked.submitted_at
                and (now - datetime.fromisoformat(tracked.submitted_at)).total_seconds() >= ttl
            ):
                why = "ttl"
            if why is None:
                continue
            if not callable(cancel):
                logger.warning(
                    f"{tracked.client_order_id!r} should be cancelled ({why}) but "
                    f"{type(self.broker).__name__} cannot cancel; it rests until the venue "
                    "expires it."
                )
                continue
            try:
                cancel(tracked.client_order_id)
            except BrokerUnavailableError:
                raise
            except Exception as exc:
                logger.warning(
                    f"Could not cancel {tracked.client_order_id!r} ({why}; "
                    f"{type(exc).__name__}: {exc}); trying again next tick."
                )
                continue
            tracked.cancel_requested, tracked.cancel_reason = True, why
            changed = True
            logger.warning(
                f"{tracked.kind.upper()} {tracked.client_order_id!r} cancel requested ({why}); "
                "done when the venue reports it gone."
            )
            self._order_event(tracked, "cancel_requested", why=why)
        if changed:
            self._persist_open_orders()

    def _audit_windows(self, now: datetime) -> None:
        """Audit each traded window of today once it has ended (and
        WINDOW_AUDIT_GRACE_SECONDS passed): its orders all terminal at the
        venue and, with nothing open, the venue's position the ledger's."""
        today = now.astimezone(EASTERN).date()
        for window in self.calendar.traded(today):
            key = (today.isoformat(), window.session)
            if key in self._audited or now < window.end + _seconds(WINDOW_AUDIT_GRACE_SECONDS):
                continue
            # Marked done only once it ran: a venue unreachable mid-audit
            # (BrokerUnavailableError) leaves it for the next tick.
            self._audit(window, now)
            self._audited.add(key)

    def _audit(self, window, now: datetime) -> None:
        summary = {
            "day": window.start.date().isoformat(),
            "session": window.session,
            "start": window.start.isoformat(),
            "end": window.end.isoformat(),
            "at": now.isoformat(),
            **self._window_tally(window),
        }
        stuck = [
            tracked.client_order_id
            for tracked in self.state.open_orders.values()
            if tracked.expires_at and datetime.fromisoformat(tracked.expires_at) <= window.end
        ]
        problem = None
        if stuck:
            problem = (
                f"after the {window.session} window ({window.start:%H:%M}-{window.end:%H:%M} ET) "
                f"order(s) {stuck} are still open at the venue, though cancelled before it "
                "ended. Check Activity & Orders and reconcile before buying again."
            )
        elif self.state.open_orders:
            summary["position"] = "not checked: orders of a later window are open"
        else:
            held = float(self.broker.snapshot().positions.get(self.symbol, 0.0) or 0.0)
            booked = float(sum(lot.shares for lot in self.ledger.open_lots))
            summary["position"] = {"venue": held, "ledger": booked}
            if abs(held - booked) > SHARE_EPSILON:
                problem = (
                    f"after the {window.session} window the venue holds {held:g} {self.symbol} "
                    f"and the ledger {booked:g}. Reconcile before buying again."
                )
        if problem is not None:
            summary["problem"] = problem
            logger.error(f"WINDOW AUDIT: {problem}")
            self.circuit_breaker.halt_for_reconciliation(problem)
        else:
            logger.warning(f"WINDOW AUDIT {window.session}: {summary}")
        self.last_window = summary

    def _window_tally(self, window) -> dict:
        """The orders this process placed in `window`: how many, what filled
        and at what price, and how the rest ended."""
        mine = [
            entry
            for entry in self._orders_seen.values()
            if entry["session"] == window.session
            and entry["day"] == window.start.date().isoformat()
        ]
        filled = sum(entry["filled_qty"] for entry in mine)
        notional = sum(entry["filled_notional"] for entry in mine)
        ended: dict[str, int] = {}
        for entry in mine:
            if entry["final"]:
                ended[entry["final"]] = ended.get(entry["final"], 0) + 1
        return {
            "orders": len(mine),
            "filled_qty": filled,
            "avg_price": (notional / filled) if filled > 0 else None,
            "ended": ended,
        }

    def _order_event(self, tracked: _TrackedOrder, event: str, **fields) -> None:
        """One moment of an order's life, to the order listener and the
        window's tally. Never raises."""
        try:
            entry = self._orders_seen.setdefault(
                tracked.client_order_id,
                {
                    "session": tracked.session,
                    "day": (
                        datetime.fromisoformat(tracked.submitted_at)
                        .astimezone(EASTERN)
                        .date()
                        .isoformat()
                        if tracked.submitted_at
                        else None
                    ),
                    "filled_qty": 0.0,
                    "filled_notional": 0.0,
                    "final": None,
                },
            )
            entry["filled_qty"] = float(tracked.tracker.cumulative_qty)
            entry["filled_notional"] = float(tracked.tracker.cumulative_notional)
            if event in _FINAL_EVENTS:
                entry["final"] = event
        except Exception as exc:
            logger.warning(f"Order tally failed (ignored): {type(exc).__name__}: {exc}")
        if self._order_listener is None:
            return
        try:
            filled = float(tracked.tracker.cumulative_qty)
            self._order_listener(
                {
                    "t": self._now().timestamp(),
                    "order": tracked.client_order_id,
                    "kind": tracked.kind,
                    "event": event,
                    "session": tracked.session,
                    "limit": tracked.limit_price,
                    "qty": tracked.qty,
                    "filled_qty": filled,
                    "avg_price": (
                        float(tracked.tracker.cumulative_notional) / filled if filled > 0 else None
                    ),
                    "reason": str(tracked.sell_reason) if tracked.kind == "sell" else None,
                    **fields,
                }
            )
        except Exception as exc:
            logger.warning(f"Order listener failed (ignored): {type(exc).__name__}: {exc}")

    def settle_in_flight(self) -> bool:
        """in_flight_settled for a shutdown on the venue's windows: orders the
        last tick cancelled are asked about (at most every
        SETTLE_POLL_SECONDS), so a cancel the venue confirms during the
        shutdown's window counts as settled rather than as an order left in
        flight."""
        if not self.state.open_orders:
            return True
        if self.calendar is None or self.broker is None:
            return False
        moment = time.monotonic()
        if self._last_settle_poll is None or moment - self._last_settle_poll >= SETTLE_POLL_SECONDS:
            self._last_settle_poll = moment
            try:
                self._poll_open_orders()
            except Exception as exc:
                logger.warning(f"Could not ask about orders settling: {type(exc).__name__}: {exc}")
        return not self.state.open_orders

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
                    self._note_broker_available()
                    logger.info(
                        f"tick price={outcome.price} fills={outcome.fills_applied} "
                        f"sells={outcome.sells_submitted} buys={outcome.buys_submitted} "
                        f"cash={self.state.cash:.2f} open_lots={len(self.ledger.open_lots)}"
                    )
                self._report_tick(outcome.reason, acted=outcome.acted, price=outcome.price)
            except BrokerUnavailableError as exc:
                # NOTHING WAS SENT: the broker could not take the request
                # -- its session signed out, its connection dropped, or
                # trading was switched off on its side. Not a reason to
                # stop: skip the rest of this tick and try again on the
                # next. Whatever the tick already applied (a confirmed
                # fill, say) is persisted now rather than at the tick's
                # end, which it did not reach.
                self.persist_state()
                self._decision_not_sent()
                self._note_broker_unavailable(exc)
                self._report_tick("broker_unavailable", acted=False, detail=str(exc))
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

    def _describe(self, context: MarketContext) -> None:
        """This tick's `decision` and `shadow_state` (module docstring, WHAT
        IT SAYS ABOUT ITSELF). Never raises: a report is not a reason to stop
        a tick."""
        try:
            level = _buy_level(self.strategy, context, self.state.last_buy_price, self.step)
            cap = getattr(self.risk_manager, "max_concurrent_lots", None)
            if not self.circuit_breaker.allows_new_buys:
                blocked = f"buys paused: {self.circuit_breaker.reason}"
            elif level is None:
                blocked = "the strategy buys at no price right now"
            elif self._spendable() <= 0:
                blocked = "no buying power left"
            elif cap is not None and len(self.ledger.open_lots) >= cap:
                blocked = f"at its limit of {cap} open lots"
            else:
                blocked = None
            if blocked is None and self._buy_note:
                blocked = self._buy_note
            self.decision = {
                "price": float(context.price),
                "buy_level": level,
                "reference": self.state.last_buy_price,
                "blocked": blocked,
                "strategy": _diagnostics(self.strategy),
            }
            if self.calendar is not None:
                upcoming = self.calendar.next_window(self._now())
                self.decision["window"] = self.window.to_dict() if self.window else None
                self.decision["next_window"] = upcoming.to_dict() if upcoming else None
                self.decision["reserved"] = round(self.reserved(), 2)
                note = getattr(self.market_data, "secondary_note", None)
                if note:
                    self.decision["secondary_feed"] = note
        except Exception as exc:
            logger.warning(f"No decision report this tick: {type(exc).__name__}: {exc}")
            self.decision = None
        if self.shadow is None:
            self.shadow_state = None
            return
        try:
            # What switching back would do to the book now: the lots the
            # shadow's own exit would sell on this bar.
            lots = self._own_lots()
            liquidate = getattr(self.shadow, "lots_to_liquidate", None)
            selling = list(liquidate(lots, context)) if callable(liquidate) else []
            self.shadow_state = {
                "strategy": _diagnostics(self.shadow),
                "would_sell": len(selling),
                "would_sell_cost": round(sum(lot.buy_price * lot.shares for lot in selling), 2),
            }
        except Exception as exc:
            self._drop_shadow(exc)

    def _report_fill(self, **fields) -> None:
        """Tell the fill listener about a booked fill. A listener that fails
        is logged, never allowed to stop the loop."""
        if self._fill_listener is None:
            return
        try:
            self._fill_listener({"t": datetime.now(UTC).timestamp(), **fields})
        except Exception as exc:
            logger.warning(f"Fill listener failed (ignored): {type(exc).__name__}: {exc}")

    def _report_tick(self, reason: str, **fields) -> None:
        """Tell the tick listener what this tick did. A listener that
        fails is logged, never allowed to stop the loop."""
        if self._tick_listener is None:
            return
        try:
            self._tick_listener({"at": datetime.now(UTC).isoformat(), "reason": reason, **fields})
        except Exception as exc:
            logger.warning(f"Tick listener failed (ignored): {type(exc).__name__}: {exc}")

    def _decision_not_sent(self) -> None:
        """The broker could not take this tick's orders AFTER the strategy
        decided on its bar (module docstring, A DECISION THE BROKER COULD
        NOT TAKE). A strategy that declares decision_not_sent() is told, so
        it can decide again on the next bar. Never raises."""
        if not self._decided:
            return
        self._decided = False
        hook = getattr(self.strategy, "decision_not_sent", None)
        if not callable(hook):
            return
        try:
            hook()
        except Exception as exc:
            logger.warning(f"decision_not_sent failed (ignored): {type(exc).__name__}: {exc}")

    def _note_broker_unavailable(self, exc: BrokerUnavailableError) -> None:
        """Log an unreachable broker without flooding the log: when it
        starts, when the reason changes, and every 30 ticks while it
        lasts."""
        detail = str(exc)
        self._unavailable_ticks += 1
        if detail != self.broker_unavailable or self._unavailable_ticks % 30 == 0:
            logger.warning(
                f"Broker unavailable ({self._unavailable_ticks} tick(s) in a row) -- skipping "
                f"and trying again next tick: {detail}"
            )
        self.broker_unavailable = detail

    def _note_broker_available(self) -> None:
        if self.broker_unavailable is None:
            return
        logger.warning(
            f"Broker available again after {self._unavailable_ticks} skipped tick(s); "
            "trading resumes."
        )
        self.broker_unavailable = None
        self._unavailable_ticks = 0

    # --- fills ---

    def _poll_open_orders(self) -> int:
        """Apply every newly confirmed fill increment. Returns how many.

        Iterates a snapshot of the tracked orders because applying a
        fill can untrack the order it came from.
        """
        applied = removed = 0
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

            state = map_broker_status(order.status)
            if state in TERMINAL_STATES:
                self.state.open_orders.pop(client_order_id, None)
                self.state.sells_in_flight.difference_update(tracked.lot_ids)
                removed += 1
                self._order_event(tracked, _FINAL_EVENT.get(state, str(state).lower()))
            elif not delta.is_empty:
                self._order_event(tracked, "partially_filled")
        if removed or applied:
            self._persist_open_orders()
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
        self._report_fill(
            side="buy",
            lot=lot_order_id,
            qty=float(delta.qty),
            price=float(delta.avg_price),
            value=float(delta.notional),
            target=float(tracked.profit_target),
        )

    def _apply_exit_fill(self, tracked: _TrackedOrder, delta) -> None:
        """Allocate one signal-exit fill increment across the lots it sold,
        oldest first: each closes as fully as the increment reaches, through
        the no-loss guard like any sale (which lets a signal exit realize a
        loss). Shares filled beyond the lots' own are reported, never
        invented into the ledger."""
        remaining = delta.qty
        for lot_id in tracked.exit_lot_ids:
            if remaining <= SHARE_EPSILON:
                break
            lot = next((lot for lot in self.ledger.open_lots if lot.order_id == lot_id), None)
            if lot is None:
                continue  # closed by an earlier increment
            qty = min(lot.shares, remaining)
            try:
                economics = validate_sell(
                    lot,
                    qty,
                    delta.avg_price,
                    self.cost_model,
                    prev_close=self.state.prev_close,
                    reason=tracked.sell_reason,
                )
            except NoLossViolation:
                continue  # logged by the guard; left visible for reconciliation
            cost = lot.buy_price * qty
            self.state.credit_sale(economics.net_sell_proceeds, self.settlement_days)
            self.ledger.close_lot(lot, sell_qty=qty, execution_price=delta.avg_price)
            self.store.sync_lot(self.ledger, lot)
            remaining -= qty
            self._report_sale(tracked, lot_id, qty, delta.avg_price, economics, cost)
        logger.info(
            f"EXIT filled: {delta.qty} @ {delta.avg_price} across "
            f"{len(tracked.exit_lot_ids)} lot(s); cash={self.state.cash:.2f}"
        )
        if remaining > 1e-6:
            logger.error(
                f"Exit {tracked.client_order_id!r} filled {remaining} shares more than its "
                "open lots held. Not applied -- reconcile."
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
        if tracked.exit_lot_ids:
            self._apply_exit_fill(tracked, delta)
            return
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

        cost = lot.buy_price * delta.qty
        self.state.credit_sale(economics.net_sell_proceeds, self.settlement_days)
        self.ledger.close_lot(lot, sell_qty=delta.qty, execution_price=delta.avg_price)
        self.store.sync_lot(self.ledger, lot)
        logger.info(
            f"SELL filled: {delta.qty} @ {delta.avg_price} "
            f"(net ${economics.net_sell_proceeds:.2f}); cash={self.state.cash:.2f}"
        )
        self._report_sale(tracked, lot.order_id, delta.qty, delta.avg_price, economics, cost)

    def _report_sale(self, tracked, lot_id, qty, price, economics, cost) -> None:
        """A booked sale, with what it fetched against what the lot cost --
        the figure the ledger cannot give (it stores no sale price)."""
        proceeds = float(economics.net_sell_proceeds)
        self._report_fill(
            side="sell",
            reason=str(tracked.sell_reason),
            lot=lot_id,
            qty=float(qty),
            price=float(price),
            proceeds=proceeds,
            cost=float(cost),
            pnl=proceeds - float(cost),
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

        return self._market_context(
            bar.timestamp,
            bar.open,
            bar.high,
            bar.low,
            price,
            float(getattr(bar, "volume", 0.0) or 0.0),
            cash=self.state.cash,
            equity=equity,
            peak_equity=self.state.peak_equity,
            drawdown=drawdown,
            open_lot_count=len(self.ledger.open_lots),
        )

    def _market_context(
        self,
        timestamp,
        open_,
        high,
        low,
        close,
        volume,
        *,
        cash,
        equity,
        peak_equity,
        drawdown,
        open_lot_count,
    ) -> MarketContext:
        """One bar's MarketContext, the market half derived the same way
        for a live tick and a replayed history bar."""
        if timestamp.tzinfo is None:
            timestamp = timestamp.replace(tzinfo=UTC)

        if self._event_table is not None:
            event_intensity, minutes_to_event = self._event_table.scalar(timestamp)
        else:
            event_intensity, minutes_to_event = 0.0, -1.0

        return MarketContext(
            timestamp=timestamp,
            open=open_,
            high=high,
            low=low,
            close=close,
            cash=cash,
            equity=equity,
            peak_equity=peak_equity,
            drawdown=drawdown,
            open_lot_count=open_lot_count,
            bar_index=0,
            is_macro_event_day=is_fomc_day_at(timestamp),
            is_earnings_reaction_day=is_earnings_reaction_day_at(timestamp),
            time_of_day_flag=minutes_since_open(timestamp),
            volume=volume,
            event_intensity=event_intensity,
            minutes_to_event=minutes_to_event,
            implied_vol_change=change_at(self._implied_vol_series, timestamp),
        )

    # --- order submission ---

    def _harvest(self, context: MarketContext) -> int:
        """Submit limit sells for every lot that has reached its target, and
        one order for every lot the strategy wants out of (_submit_exit).

        A lot with a sell already in flight is skipped: re-offering it
        would put two sell orders against one position and could sell
        shares that no longer exist. Harvests are bounded per tick so one
        very large harvest cannot overrun the poll interval; the remainder
        is picked up next tick.
        """
        self._cancel_stale_exits(context)
        submitted = 0
        # Trailing exits, through the shared helper the backtest paths
        # also call. Lots with a sell in flight are excluded: that order
        # is resting at the lot's current target, so moving the target
        # would leave our ledger and the broker's live order disagreeing
        # about one lot's price.
        retargeted = decision_cycle.adjust_open_lot_targets(
            self.strategy,
            self.ledger,
            context,
            skip_order_ids=self.state.sells_in_flight | self._legacy,
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
        liquidations = decision_cycle.collect_liquidations(
            self.strategy,
            self.ledger,
            context,
            allow_signal_exit=self.config.execution.allow_signal_exit,
            skip_order_ids=self.state.sells_in_flight | self._legacy,
        )
        if liquidations:
            condemned = {lot.order_id for lot in liquidations}
            marketable = [lot for lot in marketable if lot.order_id not in condemned]
            submitted += self._submit_exit(liquidations, context)

        for lot in marketable[: max(0, self.config.live.max_sells_per_tick - submitted)]:
            if lot.order_id in self.state.sells_in_flight:
                continue
            decision_id = self._decision_id("SELL", context.timestamp, lot.order_id)
            outcome = self.guard.submit_once(
                decision_id,
                lambda cid, lot=lot: str(
                    self.broker.submit_sell(
                        self.symbol,
                        lot.shares,
                        lot.target_sell_price,
                        client_order_id=cid,
                        **self._order_kwargs(),
                    ).id
                ),
                event_kind="sell_submission",
            )
            if not outcome.submitted_now:
                continue
            self.state.open_orders[decision_id] = _TrackedOrder(
                client_order_id=decision_id,
                kind="sell",
                tracker=FillTracker(decision_id),
                lot_order_id=lot.order_id,
                sell_reason=SellReason.PROFIT_TARGET,
                **self._window_fields(limit=lot.target_sell_price, qty=lot.shares, reserve=0.0),
            )
            self.state.sells_in_flight.add(lot.order_id)
            self._persist_open_orders()
            self._order_event(self.state.open_orders[decision_id], "placed")
            submitted += 1
        return submitted

    def _submit_exit(self, lots: list, context: MarketContext) -> int:
        """ONE limit order for every lot the strategy wants out of.

        A signal exit used to send an order per lot, at most
        max_sells_per_tick a tick: a calm book of 3,000 lots took about an
        hour to leave where the backtest sells it on one bar, and every
        order was one more request against the venue's rate limit. One
        order for their summed shares leaves in one fill; the fill is
        allocated back to the lots, oldest first (_apply_exit_fill).

        Priced exit_limit_buffer through the bar's price: a limit AT the
        last trade often rests below a bid a tick lower, and a resting exit
        is the one outcome it must not have. Still a limit, so a thin book
        cannot fill it arbitrarily far away; the fill is the market's price.
        One still resting on a later bar is cancelled and the rest offered
        again at the new price (_cancel_stale_exits).
        """
        lots = [lot for lot in lots if lot.order_id not in self.state.sells_in_flight]
        qty = _floor_shares(sum(lot.shares for lot in lots))
        if not lots or qty <= 0:
            return 0
        price = context.price * (1.0 - self.config.live.exit_limit_buffer)
        if self.calendar is not None:
            # Through the quote's bid when there is one (limit_pricing).
            price = limit_pricing.marketable_sell(
                context.price,
                self._quote(),
                max_premium=self.config.live.orders.max_premium,
                buffer=self.config.live.exit_limit_buffer,
            ).price
        decision_id = self._decision_id("SELL", context.timestamp, "exit")
        outcome = self.guard.submit_once(
            decision_id,
            lambda cid: str(
                self.broker.submit_sell(
                    self.symbol, qty, price, client_order_id=cid, **self._order_kwargs()
                ).id
            ),
            event_kind="sell_submission",
        )
        if not outcome.submitted_now:
            return 0
        logger.warning(
            f"SIGNAL EXIT submitted: {len(lots)} lot(s), {qty} shares, limit {price:.4f} "
            f"({self.config.live.exit_limit_buffer:.2%} through {context.price}). These "
            "sales are permitted to realize a loss."
        )
        self.state.open_orders[decision_id] = _TrackedOrder(
            client_order_id=decision_id,
            kind="sell",
            tracker=FillTracker(decision_id),
            sell_reason=SellReason.SIGNAL_EXIT,
            exit_lot_ids=tuple(lot.order_id for lot in lots),
            submitted_bar=context.timestamp.isoformat(),
            **self._window_fields(limit=price, qty=qty, reserve=0.0),
        )
        self.state.sells_in_flight.update(lot.order_id for lot in lots)
        self._persist_open_orders()
        self._order_event(self.state.open_orders[decision_id], "placed")
        return 1

    def _cancel_stale_exits(self, context: MarketContext) -> None:
        """Cancel a signal exit still resting on a later bar: the market
        moved through its limit. Once the venue reports it done -- with any
        part that filled applied as usual -- its lots are free again and
        the strategy, still wanting out, has them re-offered at the new
        price. A broker without cancel_order leaves it resting until the
        session ends, as every exit did before."""
        cancel = getattr(self.broker, "cancel_order", None)
        if not callable(cancel):
            return
        bar = context.timestamp.isoformat()
        changed = False
        for tracked in list(self.state.open_orders.values()):
            if not tracked.exit_lot_ids or tracked.cancel_requested:
                continue
            if tracked.submitted_bar == bar:
                continue
            try:
                cancel(tracked.client_order_id)
            except BrokerUnavailableError:
                raise
            except Exception as exc:
                logger.warning(
                    f"Could not cancel resting exit {tracked.client_order_id!r} "
                    f"({type(exc).__name__}: {exc}); trying again next tick."
                )
                continue
            tracked.cancel_requested = True
            changed = True
            logger.warning(
                f"Signal exit {tracked.client_order_id!r} was still resting a bar later; "
                "cancel requested so what is left is offered again at the market."
            )
        if changed:
            self._persist_open_orders()

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
        if trade_value <= 0 or self._spendable() < trade_value:
            return 0

        # context.price IS the target buy price -- the grid trigger fired at
        # it. On the venue's windows a buy is placed by what it is for
        # (engine/execution/limit_pricing.py): a grid buy at that price, a
        # rebalance through the quote.
        limit_price = context.price
        if self.calendar is not None:
            limit = self._buy_limit(context)
            if limit.price is None:
                logger.warning(f"No buy this bar: {limit.why}")
                self._buy_note = limit.why
                return 0
            limit_price = limit.price
        # A whole-share venue (Fidelity) cannot place a buy worth less than
        # one share. Raised from submit_buy it aborted the loop (10-30, a $16
        # lot of RSP at $219) after submit_once had claimed the decision, so
        # it is settled HERE, before the claim: such a lot buys ONE share,
        # if that share passes the same risk clamp and fits the cash; else
        # this bar buys nothing and the status says why.
        if getattr(self.broker, "whole_shares", False) and trade_value < limit_price:
            why = self._whole_share_refusal(context, limit_price)
            if why is not None:
                logger.warning(f"No buy this bar: {why}")
                self._buy_note = why
                return 0
            logger.info(
                f"Lot of ${trade_value:.2f} rounded up to one whole share at ${limit_price:.2f}"
            )
            trade_value = limit_price
        placed = {}

        def submit(cid):
            # Passed unconditionally: a regular-hours notional market buy
            # ignores it, and an extended-hours buy cannot be placed without
            # it, so the loop stays out of the business of knowing which
            # shape the venue will take.
            placed["order"] = self.broker.submit_buy(
                self.symbol,
                trade_value,
                client_order_id=cid,
                limit_price=limit_price,
                **self._order_kwargs(),
            )
            return str(placed["order"].id)

        decision_id = self._decision_id("BUY", context.timestamp)
        outcome = self.guard.submit_once(decision_id, submit, event_kind="buy_submission")
        if not outcome.submitted_now:
            return 0

        qty = getattr(placed.get("order"), "qty", None) or None
        self.state.open_orders[decision_id] = _TrackedOrder(
            client_order_id=decision_id,
            kind="buy",
            tracker=FillTracker(decision_id),
            trigger_price=context.price,
            profit_target=self.profit_target,
            **self._window_fields(limit=limit_price, qty=qty, reserve=trade_value),
        )
        self._persist_open_orders()
        self._order_event(self.state.open_orders[decision_id], "placed")
        return 1

    def _whole_share_refusal(self, context: MarketContext, price: float) -> str | None:
        """Why one whole share at `price` may not be bought, or None."""
        venue = type(self.broker).__name__
        clamped = self.risk_manager.clamp_trade_value(
            price,
            context.equity,
            self.state.buying_power,
            context.open_lot_count,
            context.drawdown,
        )
        if clamped < price:
            return f"one whole share (${price:.2f}) is over the risk limit; {venue} buys whole shares only"
        if self._spendable() < price:
            return f"one whole share (${price:.2f}) is more than the cash to spend; {venue} buys whole shares only"
        return None

    def _buy_limit(self, context: MarketContext):
        """Where a buy goes on the venue's windows: through the quote for a
        strategy whose buys must fill (a rebalance: `marketable_orders`), at
        the trigger otherwise."""
        quote = self._quote()
        orders = self.config.live.orders
        if getattr(self.strategy, "marketable_orders", False):
            return limit_pricing.marketable_buy(
                context.price,
                quote,
                max_premium=orders.max_premium,
                buffer=self.config.live.exit_limit_buffer,
            )
        return limit_pricing.grid_buy(context.price, quote, max_spread=orders.max_spread)

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
            json.dumps(
                {
                    "session": self.state.session,
                    "unsettled": self.state.unsettled,
                    "pending": self.state.pending,
                }
            ),
        )
        self.store.set_meta(_META_CASH, str(self.state.cash))
        # THE PARAMETERS THIS LOOP IS ACTUALLY TRADING. The store held
        # cash, lots and a halt, but nothing about the configuration
        # that produced them -- so a reader could see 94 lots sitting at
        # a 30% target without being able to tell whether that was the
        # intent or a misplaced decimal. It was a misplaced decimal, and
        # it took a config file and a ledger side by side to find.
        #
        # Written every tick with the other scalars rather than once at
        # startup, so a restart under a changed config cannot leave the
        # store describing the previous one.
        self.store.set_meta(
            _META_PARAMETERS,
            json.dumps(
                {
                    "symbol": self.symbol,
                    "step": self.step,
                    "profit_target": self.profit_target,
                    "strategy_id": self.config.strategy.strategy_id,
                    "paper": bool(self.config.live.paper_trading),
                    "poll_interval_seconds": float(self.config.live.poll_interval_seconds),
                    "extended_hours": bool(self.config.live.extended_hours),
                    **(
                        {"sessions": list(self.config.live.traded_sessions)}
                        if self.calendar is not None
                        else {}
                    ),
                }
            ),
        )
        self.store.set_meta(_META_PEAK_EQUITY, str(self.state.peak_equity))
        # The price this tick saw, and when. The loop already knows both
        # and was discarding them, which left every reader downstream
        # with no mark to value the book at and no way to tell a running
        # deployment from a stopped one except the store's file mtime --
        # a proxy that cannot distinguish "stopped" from "market closed".
        if self.state.last_tick_price is not None:
            self.store.set_meta(
                _META_LAST_TICK,
                json.dumps(
                    {
                        "price": self.state.last_tick_price,
                        "at": self.state.last_tick_at,
                        "symbol": self.symbol,
                    }
                ),
            )

    def in_flight_settled(self) -> bool:
        """Whether nothing is awaiting a fill.

        Wired to RuntimeLifecycle.shutdown's bounded settle window: an
        in-flight order that lands mid-shutdown must still be accounted
        for, or the next startup reconciles against state that never
        recorded it.
        """
        return not self.state.open_orders
