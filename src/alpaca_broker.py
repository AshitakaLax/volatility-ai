"""
Alpaca broker adapter -- the concrete LiveBroker implementation.

This is the class whose absence every other Phase 7 module was written
around: src/order_management_system.py raises NotImplementedError for
Mode.LIVE, cli.py's `live` command stops at RECOVERY_REQUIRED, and
src/reconciliation.py's BrokerSnapshot docstring explicitly defers
"this module does not talk to Alpaca itself (that's the broker
adapter's job)". This module is that job, and nothing more -- it
reimplements no accounting, no retry classification, no reconciliation
logic, and no lifecycle sequencing. It translates between this
codebase's contracts and alpaca-py, and that is all.

Implements src.live_execution.LiveBroker structurally (submit_buy /
submit_sell), so LiveExecutionLoop accepts it via broker_factory
without either module importing the other.

--------------------------------------------------------------------
PAPER vs LIVE is a constructor argument, not a runtime branch.

alpaca-py routes by base URL: TradingClient(paper=True) talks to
paper-api.alpaca.markets, paper=False to the real one. There is no
in-flight check that could catch a mistake here, so `paper` defaults
to True (the safe direction) and from_mode() derives it from the
already-audited Mode enum rather than letting a caller pass a loose
boolean. Mode.SIMULATION is refused outright: a simulation must not
hold a broker connection at all.
--------------------------------------------------------------------
ORDER-TYPE CHOICES, and why each is forced rather than configurable:

BUY is a NOTIONAL MARKET order. The LiveBroker contract hands this
method dollars (`trade_value`), not shares, and notional is how Alpaca
accepts dollars directly -- no local price lookup, so no window in
which our price and theirs disagree. Alpaca supports notional only for
market orders (confirmed in the installed SDK's own OrderRequest
docstring), so the type is not a choice.

SELL is a LIMIT order at the target price, and this one is a safety
requirement rather than a preference. The system's primary invariant
is that it never intentionally sells at a loss; src/no_loss_guard.py
validates `target_price` against the lot's cost basis before this
method is ever called. A MARKET sell would discard that guarantee at
the venue -- it fills at whatever the book offers, which can be below
the validated price, realizing exactly the loss the guard exists to
prevent. A limit order is the only order type that carries the guard's
decision through to execution. An unfilled sell is recoverable; a
sell below cost basis is not.

Fractional quantities are supported for limit orders with
time_in_force=DAY. Verified against Alpaca's current documentation
rather than the installed SDK, whose OrderRequest docstring still says
"fractional qty for stocks only with market orders" -- that line is
stale, and believing it would have forced the unsafe market-sell
design above. TimeInForce.DAY is therefore fixed for both sides: it is
the only value Alpaca accepts for fractional or notional orders.
--------------------------------------------------------------------
ROUNDING is directional, never nearest.

Both roundings below are deliberately biased toward safety, because
"round to nearest" is wrong in both places:

  - Buy notional floors to the cent. `trade_value` arriving here is
    RiskManager's clamped, risk-approved ceiling; rounding it up would
    submit an order fractionally larger than risk authorized.
  - Sell limit price ceils to the tick. Rounding a validated no-loss
    price DOWN could push it below cost basis and realize a loss --
    the one outcome this system must never produce. Rounding up can
    only leave an order unfilled, which is recoverable.

Decimal, not float, does the rounding: float already cannot represent
most cent values exactly, and money rounding is precisely where that
bites.
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from decimal import ROUND_CEILING, ROUND_FLOOR, Decimal
from typing import Any

from src.exceptions import ConfigurationError, ExecutionError
from src.fill_accounting import extract_alpaca_fill
from src.order_lifecycle import map_broker_status
from src.reconciliation import BrokerSnapshot
from src.retry_policy import RetryConfig, retry_call
from src.secrets import LiveCredentials

logger = logging.getLogger("Optimizer")

# Alpaca's price increment rule: two decimals at or above $1.00, four
# below it. Applied to the sell limit price so a rounded price is one
# the venue will actually accept.
_SUB_DOLLAR_TICK = Decimal("0.0001")
_TICK = Decimal("0.01")

# Alpaca rejects a notional order below $1.00. Enforced locally so the
# rejection is a clear local error naming the amount, rather than a
# 4xx that has already consumed a round trip.
MINIMUM_NOTIONAL = 1.0

# How many recent orders snapshot() pulls for reconciliation. Alpaca's
# own default page size is 50; 500 is chosen so a busy session's
# already-filled orders stay inside the window, because an order that
# ages out of it looks "absent at broker" to the Reconciler.
DEFAULT_SNAPSHOT_ORDER_LIMIT = 500


def _floor_to_cent(value: float) -> float:
    """Round a dollar amount DOWN to the cent.

    Down, never nearest: the caller's value is a risk-approved ceiling
    (see module docstring), so rounding up would breach it.
    """
    return float(Decimal(str(value)).quantize(_TICK, rounding=ROUND_FLOOR))


def _ceil_to_tick(price: float) -> float:
    """Round a limit price UP to a tick Alpaca accepts.

    Up, never nearest: this price has already cleared the no-loss guard,
    and rounding it down could put it below the lot's cost basis.
    """
    quantum = _SUB_DOLLAR_TICK if price < 1 else _TICK
    return float(Decimal(str(price)).quantize(quantum, rounding=ROUND_CEILING))


def _floor_to_tick(price: float) -> float:
    """Round a BUY limit price DOWN to a tick Alpaca accepts.

    Down, never nearest, and the direction is the mirror of
    _ceil_to_tick's for the same reason. A buy's fill price BECOMES the
    lot's cost basis, and every later sell is validated against it by
    no_loss_guard. Rounding a buy limit UP raises the cost basis by up
    to a tick, which raises the price the lot must reach to clear the
    guard -- paying more now to make the exit harder later.

    Rounding down can only leave a buy unfilled, and an unfilled buy is
    recoverable: the grid trigger fires again on the next bar that
    qualifies.
    """
    quantum = _SUB_DOLLAR_TICK if price < 1 else _TICK
    return float(Decimal(str(price)).quantize(quantum, rounding=ROUND_FLOOR))


def _floor_shares(qty: float, whole_only: bool) -> float:
    """Round a share count DOWN, so cost never exceeds the budget.

    whole_only exists because fractional shares and extended hours do
    not mix at Alpaca: fractional trading is a regular-hours facility.
    Rather than discover that as a venue rejection at 4:30pm, an
    extended-hours order is sized in whole shares here.

    Fractional quantities are floored to six places. Alpaca accepts
    more, but the precision is not the point -- the FLOOR is, so that
    qty * limit_price stays at or under the risk-approved value.
    """
    if whole_only:
        return float(Decimal(str(qty)).quantize(Decimal("1"), rounding=ROUND_FLOOR))
    return float(Decimal(str(qty)).quantize(Decimal("0.000001"), rounding=ROUND_FLOOR))


def _require_alpaca():
    """Import alpaca-py, or raise a ConfigurationError explaining how to
    get it.

    Imported lazily rather than at module scope because alpaca-py is an
    optional dependency (see requirements.txt): backtesting must not
    require the live-trading SDK, and importing this module must not
    fail for someone who only runs sweeps. Mirrors how
    src/retry_policy.py imports the SDK inside classify_error.
    """
    try:
        from alpaca.common.exceptions import APIError
        from alpaca.trading.client import TradingClient
        from alpaca.trading.enums import OrderSide, TimeInForce
        from alpaca.trading.requests import LimitOrderRequest, MarketOrderRequest
    except ImportError as e:  # pragma: no cover - exercised only without the SDK
        raise ConfigurationError(
            "alpaca-py is required for live/paper trading but is not installed. "
            "Install it with `pip install alpaca-py` (it is listed in requirements.txt "
            "as an optional live-trading dependency)."
        ) from e
    return (
        APIError,
        TradingClient,
        OrderSide,
        TimeInForce,
        LimitOrderRequest,
        MarketOrderRequest,
    )


class AlpacaBroker:
    """Submits orders to Alpaca, implementing the LiveBroker protocol.

    State ownership: this object owns the TradingClient connection and
    nothing else. It holds no cash, no lots, no order history, and no
    fill state -- LedgerStore, OrderRecord, and FillTracker own those.
    Every method here is a translation, so there is no local state that
    could drift from the broker's.
    """

    def __init__(
        self,
        credentials: LiveCredentials,
        *,
        paper: bool = True,
        client: Any = None,
        retry_config: RetryConfig | None = None,
        extended_hours: bool = False,
        snapshot_limit: int = DEFAULT_SNAPSHOT_ORDER_LIMIT,
    ) -> None:
        """Connect to Alpaca for one account.

        paper defaults to True so the unsafe direction is always the
        one a caller has to type out. Prefer from_mode(), which derives
        it from the Mode enum that already carries the promotion gate.

        client is injectable so tests exercise this adapter's real
        translation logic against a double, rather than mocking the
        adapter itself and testing nothing. When supplied, credentials
        are not used to build a connection.

        extended_hours makes BOTH sides eligible outside regular hours,
        and changes the shape of a buy to get there. It used to apply to
        the sell only, on the true observation that a notional market
        buy cannot run outside regular hours -- but the conclusion drawn
        from it was wrong. The fix is not to leave buys behind; it is to
        stop making them notional market orders when the flag is on. See
        submit_buy.

        The asymmetry that remains is real: an extended-hours buy is
        sized in WHOLE shares, because fractional trading is a
        regular-hours facility. A deployment whose lots are usually
        fractional will therefore trade a coarser grid outside regular
        hours.

        snapshot_limit bounds how many recent orders snapshot() pulls
        for reconciliation. It has to be large enough to cover every
        order that could still be unsettled locally; raise it for a
        high-frequency deployment rather than lowering it to save a
        round trip, since an order that falls off the end of this
        window reads to the Reconciler as absent at the broker.
        """
        if credentials is None and client is None:
            raise ConfigurationError(
                "AlpacaBroker requires either LiveCredentials or an injected client."
            )
        self.paper = bool(paper)
        self.extended_hours = bool(extended_hours)
        self.snapshot_limit = int(snapshot_limit)
        self._retry_config = retry_config or RetryConfig()

        if client is not None:
            self._client = client
        else:
            _, TradingClient, *_ = _require_alpaca()
            # Credentials are read here and never stored on self: keeping
            # them off the instance means no repr, log line, or traceback
            # frame of this object can surface them, complementing
            # LiveCredentials' own redaction.
            self._client = TradingClient(
                api_key=credentials.api_key_id,
                secret_key=credentials.api_secret_key,
                paper=self.paper,
            )
        logger.info(
            f"AlpacaBroker connected to the {'PAPER' if self.paper else 'LIVE (real capital)'} "
            "trading endpoint."
        )

    @property
    def trading_client(self):
        """The underlying TradingClient.

        Exposed so AlpacaMarketData can read the market clock (a
        trading-API endpoint) through the connection this object
        already holds, rather than opening and authenticating a second
        one that could drift from it.
        """
        return self._client

    # --- construction ---

    @classmethod
    def from_mode(cls, mode, credentials: LiveCredentials, **kwargs) -> AlpacaBroker:
        """Build a broker for a Mode, deriving the paper/live routing.

        Mode.SIMULATION is refused rather than quietly mapped to paper:
        a simulation has no business holding a broker connection, and
        silently giving it one would make a backtest capable of
        reaching the network.

        Reaching Mode.LIVE is already gated on a passing
        PromotionEvaluation by OrderManagementSystem (Task 7.7); this
        method deliberately does not re-implement that check, so there
        remains exactly one place that decides whether live capital is
        permitted.
        """
        mode_value = getattr(mode, "value", mode)
        if mode_value == "SIMULATION":
            raise ConfigurationError(
                "Refusing to build an AlpacaBroker for Mode.SIMULATION -- a simulation must not "
                "hold a broker connection. Use Mode.PAPER to trade against Alpaca risk-free."
            )
        if mode_value not in ("PAPER", "LIVE"):
            raise ConfigurationError(f"mode must be 'PAPER' or 'LIVE', got {mode_value!r}")
        return cls(credentials, paper=(mode_value == "PAPER"), **kwargs)

    # --- LiveBroker protocol ---

    def submit_buy(
        self,
        symbol: str,
        trade_value: float,
        client_order_id: str | None = None,
        limit_price: float | None = None,
    ) -> Any:
        """Buy trade_value dollars of symbol.

        TWO ORDER SHAPES, and which one is used is decided by
        extended_hours, not by the caller:

        * REGULAR HOURS (extended_hours=False) -- a NOTIONAL MARKET
          order, exactly as before. Alpaca takes dollars directly, so
          there is no local price lookup and no window in which our
          price and theirs disagree.

        * EXTENDED HOURS (extended_hours=True) -- a LIMIT order at
          limit_price, sized in whole shares. This is not a preference.
          Alpaca will not execute a market order outside regular hours,
          and `notional` "only works with MarketOrders" and "does not
          work with qty" (the SDK's own OrderRequest docstring). So an
          extended-hours buy CANNOT be notional and CANNOT be a market
          order; a share-sized limit order is the only shape the venue
          accepts, and the local price lookup notional was avoiding
          becomes unavoidable.

        limit_price is the strategy's TARGET BUY PRICE -- the price at
        which the grid trigger fired. It is accepted in both modes and
        ignored in the first, so the caller passes it unconditionally
        rather than branching on a venue detail it should not know
        about.

        client_order_id should be Task 7.4's decision_id, which Alpaca
        stores and dedupes on server-side -- pass it and a replayed
        decision cannot become a second position even if the local
        guard is bypassed. It is optional only so the bare LiveBroker
        protocol signature still type-checks.

        Submission is retried with after_submission=True, which is the
        important half: a 429 or 5xx (the broker answered) is retried,
        but a timeout or dropped connection (unknown whether the order
        landed) raises AmbiguousSubmissionError with no retry at all,
        routing to reconciliation instead of risking a duplicate.
        """
        if trade_value <= 0:
            raise ValueError(f"trade_value must be positive, got {trade_value}")

        if self.extended_hours:
            return self._submit_extended_hours_buy(
                symbol, trade_value, client_order_id, limit_price
            )

        notional = _floor_to_cent(trade_value)
        if notional < MINIMUM_NOTIONAL:
            raise ValueError(
                f"trade_value {trade_value} floors to ${notional:.2f}, below Alpaca's "
                f"${MINIMUM_NOTIONAL:.2f} minimum notional order size."
            )

        _, _, OrderSide, TimeInForce, _, MarketOrderRequest = _require_alpaca()
        request = MarketOrderRequest(
            symbol=symbol,
            notional=notional,
            side=OrderSide.BUY,
            # DAY is the only time_in_force Alpaca accepts for notional
            # orders -- not a default, a constraint.
            time_in_force=TimeInForce.DAY,
            client_order_id=client_order_id,
        )
        logger.info(
            f"Submitting BUY {symbol} notional=${notional:.2f} "
            f"client_order_id={client_order_id!r} (paper={self.paper})"
        )
        return self._submit(request)

    def _submit_extended_hours_buy(
        self,
        symbol: str,
        trade_value: float,
        client_order_id: str | None,
        limit_price: float | None,
    ) -> Any:
        """A share-sized limit buy, eligible outside regular hours.

        Refuses rather than falling back to a market order when no
        limit_price is available. A silent fallback would submit an
        order the venue rejects at 4:30pm -- and the deployment would
        look like it was trading extended hours while placing nothing.
        """
        if limit_price is None:
            raise ConfigurationError(
                "extended_hours is enabled but no limit_price was supplied for a "
                f"BUY of {symbol}. Alpaca does not execute market orders outside "
                "regular hours, and notional sizing is market-only, so an "
                "extended-hours buy must be a share-sized LIMIT order. Pass the "
                "strategy's target buy price."
            )
        if limit_price <= 0:
            raise ValueError(f"limit_price must be positive, got {limit_price}")

        price = _floor_to_tick(limit_price)
        if price <= 0:
            raise ValueError(
                f"limit_price {limit_price} floors to {price}, which is not a submittable price."
            )
        # Whole shares: fractional trading is a regular-hours facility at
        # Alpaca, so an extended-hours order is sized to whole shares here
        # rather than rejected at the venue.
        qty = _floor_shares(trade_value / price, whole_only=True)
        if qty < 1:
            raise ValueError(
                f"${trade_value:.2f} does not buy one whole share of {symbol} at "
                f"${price:.2f}. Extended-hours orders cannot be fractional, so this "
                "trade cannot be expressed outside regular hours."
            )

        _, _, OrderSide, TimeInForce, LimitOrderRequest, _ = _require_alpaca()
        request = LimitOrderRequest(
            symbol=symbol,
            qty=qty,
            side=OrderSide.BUY,
            # DAY is required alongside extended_hours -- Alpaca rejects
            # any other time_in_force on an extended-hours order.
            time_in_force=TimeInForce.DAY,
            limit_price=price,
            client_order_id=client_order_id,
            extended_hours=True,
        )
        logger.info(
            f"Submitting BUY {symbol} qty={qty} limit=${price} EXTENDED-HOURS "
            f"(budget ${trade_value:.2f}, cost ${qty * price:.2f}) "
            f"client_order_id={client_order_id!r} (paper={self.paper})"
        )
        return self._submit(request)

    def submit_sell(
        self,
        symbol: str,
        qty: float,
        target_price: float,
        client_order_id: str | None = None,
    ) -> Any:
        """Sell qty shares of symbol as a limit order at target_price.

        Callers must have cleared this quantity and price through
        src/no_loss_guard.validate_sell first; this method does not
        re-check, matching LiveExecutionLoop.submit_sell's own contract
        that the guard lives in exactly one place. What this method
        does guarantee is that the validated price survives to the
        venue -- see the module docstring on why this is a limit order
        and why its rounding goes up.
        """
        if qty <= 0:
            raise ValueError(f"qty must be positive, got {qty}")
        if target_price <= 0:
            raise ValueError(f"target_price must be positive, got {target_price}")

        limit_price = _ceil_to_tick(target_price)

        # A fractional lot cannot trade outside regular hours, so the
        # EXTENDED-HOURS FLAG is dropped -- never the order. Refusing
        # would block an exit, and being unable to leave a position is
        # the one failure this system must not manufacture; the same
        # reasoning that keeps the Fidelity value ceiling on buys only.
        #
        # The order is still submitted as a DAY limit at the validated
        # price. Outside regular hours Alpaca queues it for the session
        # open rather than rejecting it, so the exit is placed and
        # merely waits -- which is what it would have done anyway if the
        # flag had never been set.
        eligible = self.extended_hours and float(qty).is_integer()
        if self.extended_hours and not eligible:
            logger.info(
                f"SELL {symbol} qty={qty} is fractional, so it is not eligible for "
                "extended hours; submitting it as a regular-hours DAY limit rather "
                "than refusing the exit."
            )
        _, _, OrderSide, TimeInForce, LimitOrderRequest, _ = _require_alpaca()
        request = LimitOrderRequest(
            symbol=symbol,
            qty=qty,
            side=OrderSide.SELL,
            # DAY is required for fractional quantities, and every lot
            # this system opens is fractional (buys are notional).
            time_in_force=TimeInForce.DAY,
            limit_price=limit_price,
            client_order_id=client_order_id,
            extended_hours=eligible or None,
        )
        logger.info(
            f"Submitting SELL {symbol} qty={qty} limit=${limit_price} "
            f"extended_hours={eligible} "
            f"client_order_id={client_order_id!r} (paper={self.paper})"
        )
        return self._submit(request)

    def _submit(self, request) -> Any:
        """Send one order request under the canonical retry policy.

        after_submission=True is the whole point of routing through
        retry_policy rather than calling the SDK directly: it makes an
        ambiguous outcome raise AmbiguousSubmissionError instead of
        being retried into a possible duplicate position.
        """
        return retry_call(
            lambda: self._client.submit_order(order_data=request),
            self._retry_config,
            after_submission=True,
        )

    # --- queries (read-only; safe to retry normally) ---

    def get_order_by_client_id(self, client_order_id: str):
        """Look up an order by our client_order_id, or None if absent.

        This is the resolver DuplicateOrderGuard.resolve_ambiguous_submission
        expects: it answers "did the order we may have submitted
        actually land?" using the same decision_id we submitted under.

        A 404 returns None -- genuinely not found is an answer, not a
        failure. Any other APIError propagates, because treating an
        auth or rate-limit error as "no such order" would tell the
        guard to declare a real position nonexistent.
        """
        APIError, *_ = _require_alpaca()

        def _lookup():
            try:
                return self._client.get_order_by_client_id(client_order_id)
            except APIError as e:
                status = getattr(e, "status_code", None)
                if status == 404:
                    return None
                raise

        return retry_call(_lookup, self._retry_config, after_submission=False)

    def snapshot(self) -> BrokerSnapshot:
        """Current broker truth, shaped for src/reconciliation.Reconciler.

        Fills the BrokerSnapshot that reconciliation.py's docstring
        says the adapter is responsible for supplying. Statuses are
        translated through order_lifecycle.map_broker_status so the
        adapter and the reconciler cannot disagree about what an Alpaca
        status means -- there is one mapping table, not two.

        Orders are keyed by client_order_id (our decision_id), not by
        Alpaca's order id, because that is the key the Reconciler
        matches local orders on and the only one that identifies a
        decision this system actually made.

        The order query asks for status=ALL deliberately. get_orders()
        with no filter returns OPEN orders only, which would omit every
        order that has already filled -- and the Reconciler reads a
        locally-live order missing from the snapshot as
        ORDER_ABSENT_AT_BROKER and halts. Filtering to open orders would
        therefore turn each ordinary fill into a spurious halt.
        """
        _require_alpaca()  # raises a clear ConfigurationError if the SDK is absent
        from alpaca.trading.enums import QueryOrderStatus
        from alpaca.trading.requests import GetOrdersRequest

        order_filter = GetOrdersRequest(status=QueryOrderStatus.ALL, limit=self.snapshot_limit)

        def _fetch():
            account = self._client.get_account()
            positions = self._client.get_all_positions()
            orders = self._client.get_orders(filter=order_filter)
            return account, positions, orders

        account, positions, orders = retry_call(_fetch, self._retry_config, after_submission=False)

        position_map = {p.symbol: float(p.qty) for p in positions or ()}
        order_map = {}
        for order in orders or ():
            filled_qty, filled_avg_price = extract_alpaca_fill(order)
            order_map[str(order.client_order_id)] = {
                "state": map_broker_status(order.status),
                "filled_qty": filled_qty,
                "avg_fill_price": filled_avg_price,
                "symbol": order.symbol,
            }

        cash = float(account.cash) if account is not None and account.cash is not None else None
        return BrokerSnapshot(positions=position_map, orders=order_map, cash=cash)

    def ping(self) -> None:
        """Prove the connection and credentials actually work.

        Used as RuntimeLifecycle's connect_broker step. Deliberately
        hits an authenticated endpoint rather than merely constructing
        a client: TradingClient's constructor performs no I/O, so a
        typo'd key would otherwise sail through CONNECT_BROKER and only
        fail at the first order.
        """
        try:
            account = retry_call(
                self._client.get_account, self._retry_config, after_submission=False
            )
        except Exception as e:
            raise ExecutionError(
                f"Alpaca connection check failed against the "
                f"{'paper' if self.paper else 'live'} endpoint: {type(e).__name__}: {e}"
            ) from e
        logger.info(
            f"Alpaca connection verified (paper={self.paper}); account status="
            f"{getattr(account, 'status', 'unknown')}."
        )


def alpaca_broker_factory(
    *, paper: bool = True, **kwargs
) -> Callable[[LiveCredentials], AlpacaBroker]:
    """Build the broker_factory LiveExecutionLoop expects.

    LiveExecutionLoop.start() loads credentials itself and then calls
    broker_factory(credentials) -- this adapts AlpacaBroker's keyword
    arguments to that one-argument shape without making the loop know
    anything about Alpaca.
    """

    def _factory(credentials: LiveCredentials) -> AlpacaBroker:
        return AlpacaBroker(credentials, paper=paper, **kwargs)

    return _factory
