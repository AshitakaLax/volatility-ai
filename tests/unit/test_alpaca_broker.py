"""Tests for the Alpaca broker adapter.

Two kinds of test live here, deliberately:

  - Translation tests against an injected fake client. These assert
    what this adapter actually decides -- order type, side, rounding
    direction, retry classification -- without a network.
  - SDK-contract tests against the really-installed alpaca-py, in the
    same spirit as tests/unit/test_duplicate_order_guard.py's own
    SDK checks. They fail loudly if an SDK upgrade moves a field this
    adapter depends on, rather than letting that surface as a runtime
    error against real money.
"""

from __future__ import annotations

import pytest

from src.alpaca_broker import (
    MINIMUM_NOTIONAL,
    AlpacaBroker,
    _ceil_to_tick,
    _floor_to_cent,
    alpaca_broker_factory,
)
from src.exceptions import ConfigurationError, ExecutionError
from src.order_lifecycle import OrderState
from src.retry_policy import AmbiguousSubmissionError, RetryConfig
from src.secrets import LiveCredentials

CREDS = LiveCredentials(api_key_id="PKTEST", api_secret_key="secret")

# No real backoff in tests -- the retry policy's own timing is
# tests/unit/test_retry_policy.py's subject, not this module's.
FAST_RETRY = RetryConfig(base_delay=0.001, max_attempts=3)


class FakeOrder:
    def __init__(
        self, client_order_id="cid", status="filled", filled_qty="0", avg="0", symbol="TQQQ"
    ):
        self.client_order_id = client_order_id
        self.id = "broker-id"
        self.status = status
        self.filled_qty = filled_qty
        self.filled_avg_price = avg
        self.symbol = symbol


class FakeAccount:
    def __init__(self, cash="1000.50", status="ACTIVE"):
        self.cash = cash
        self.status = status


class FakePosition:
    def __init__(self, symbol="TQQQ", qty="3.5"):
        self.symbol = symbol
        self.qty = qty


class FakeClient:
    """Records what the adapter asked for, so tests assert on the real
    request object the adapter built rather than on a mock of itself."""

    def __init__(self, orders=None, positions=None, account=None, submit_raises=None):
        self.submitted = []
        self.lookups = []
        self._orders = orders if orders is not None else []
        self._positions = positions if positions is not None else []
        self._account = account if account is not None else FakeAccount()
        self._submit_raises = submit_raises

    def submit_order(self, order_data):
        self.submitted.append(order_data)
        if self._submit_raises is not None:
            raise self._submit_raises
        return FakeOrder(client_order_id=order_data.client_order_id or "cid")

    def get_account(self):
        return self._account

    def get_all_positions(self):
        return self._positions

    def get_orders(self, filter=None):
        self.order_filter = filter
        return self._orders

    def get_order_by_client_id(self, client_order_id):
        self.lookups.append(client_order_id)
        for order in self._orders:
            if order.client_order_id == client_order_id:
                return order
        raise api_error(404, "order not found")


def api_error(status_code, message):
    """Build an APIError the way the real SDK does.

    alpaca-py raises APIError(body, http_error) with the HTTPError
    attached (verified in alpaca.common.rest.RESTClient), and
    APIError.status_code reads through to http_error.response.status_code
    -- returning None when no HTTP context was attached. Constructing it
    faithfully matters: a bare APIError('...') has status_code None, so a
    fake that skipped the http_error would test a code path that cannot
    occur against the real broker.
    """
    import requests
    from alpaca.common.exceptions import APIError

    response = requests.Response()
    response.status_code = status_code
    return APIError(f'{{"message": "{message}"}}', requests.HTTPError(response=response))


def broker(client=None, **kwargs):
    kwargs.setdefault("retry_config", FAST_RETRY)
    return AlpacaBroker(CREDS, client=client or FakeClient(), **kwargs)


# --- rounding: direction is the whole point ---


def test_buy_notional_rounds_down_never_up():
    """The incoming trade_value is RiskManager's approved ceiling, so
    rounding up would submit an order larger than risk authorized."""
    assert _floor_to_cent(100.999) == 100.99
    assert _floor_to_cent(100.991) == 100.99
    assert _floor_to_cent(100.99) == 100.99


def test_sell_limit_price_rounds_up_never_down():
    """A no-loss-validated price rounded DOWN could land below cost
    basis, realizing exactly the loss the guard prevents."""
    assert _ceil_to_tick(100.001) == 100.01
    assert _ceil_to_tick(100.009) == 100.01
    assert _ceil_to_tick(100.01) == 100.01


def test_sub_dollar_limit_price_uses_four_decimals():
    """Alpaca's tick rule: four decimals below $1.00, two at or above."""
    assert _ceil_to_tick(0.12341) == 0.1235
    assert _ceil_to_tick(0.1234) == 0.1234


def test_rounding_does_not_inherit_float_representation_error():
    """0.07 * 3 is 0.21000000000000002 in float; Decimal-based rounding
    must not turn that into an extra cent."""
    assert _floor_to_cent(0.07 * 3) == 0.21


# --- buy: notional market order ---


def test_buy_submits_a_notional_market_day_order():
    client = FakeClient()
    broker(client).submit_buy("TQQQ", 500.257, client_order_id="decision-1")
    (request,) = client.submitted
    assert request.notional == 500.25, "notional must floor, not round to nearest"
    assert request.qty is None, "notional and qty are mutually exclusive at Alpaca"
    assert request.symbol == "TQQQ"
    assert request.side.value == "buy"
    assert request.type.value == "market"
    assert request.time_in_force.value == "day"
    assert request.client_order_id == "decision-1"


def test_buy_rejects_non_positive_value():
    for bad in (0, -1.0):
        with pytest.raises(ValueError):
            broker().submit_buy("TQQQ", bad)


def test_buy_below_alpaca_minimum_notional_is_rejected_locally():
    """Rejected here rather than spending a round trip on a 4xx, and
    the message names the actual amount."""
    with pytest.raises(ValueError, match="minimum notional"):
        broker().submit_buy("TQQQ", 0.5)
    assert MINIMUM_NOTIONAL == 1.0


# --- sell: limit order preserving the no-loss guarantee ---


def test_sell_submits_a_limit_order_not_a_market_order():
    """The critical safety property: a market sell would discard the
    no-loss guard's validated price at the venue."""
    client = FakeClient()
    broker(client).submit_sell("TQQQ", 3.5, 101.004, client_order_id="decision-2")
    (request,) = client.submitted
    assert request.type.value == "limit", "a market sell can fill below cost basis"
    assert request.limit_price == 101.01, "limit price must ceil, protecting no-loss"
    assert request.qty == 3.5, "fractional quantities must survive intact"
    assert request.side.value == "sell"
    assert request.time_in_force.value == "day"


def test_sell_rejects_non_positive_inputs():
    with pytest.raises(ValueError):
        broker().submit_sell("TQQQ", 0, 100.0)
    with pytest.raises(ValueError):
        broker().submit_sell("TQQQ", 1.0, 0)


# --- paper/live routing ---


def test_paper_defaults_to_true_so_live_must_be_typed_out():
    assert broker().paper is True


def test_from_mode_maps_paper_and_live():
    assert AlpacaBroker.from_mode("PAPER", CREDS, client=FakeClient()).paper is True
    assert AlpacaBroker.from_mode("LIVE", CREDS, client=FakeClient()).paper is False


def test_from_mode_refuses_simulation():
    """A simulation must not be able to reach the network at all."""
    with pytest.raises(ConfigurationError, match="SIMULATION"):
        AlpacaBroker.from_mode("SIMULATION", CREDS, client=FakeClient())


def test_from_mode_accepts_the_real_mode_enum():
    from src.order_management_system import Mode

    assert AlpacaBroker.from_mode(Mode.PAPER, CREDS, client=FakeClient()).paper is True
    assert AlpacaBroker.from_mode(Mode.LIVE, CREDS, client=FakeClient()).paper is False


def test_factory_matches_the_broker_factory_signature_live_execution_expects():
    factory = alpaca_broker_factory(paper=True, client=FakeClient(), retry_config=FAST_RETRY)
    built = factory(CREDS)
    assert isinstance(built, AlpacaBroker)
    assert built.paper is True


# --- credentials must not be retrievable off the instance ---


def test_credentials_are_not_stored_on_the_broker():
    """Keeping them off the instance means no repr or traceback frame
    of this object can surface them."""
    b = broker()
    leaked = [
        name
        for name, value in vars(b).items()
        if isinstance(value, str) and value in (CREDS.api_key_id, CREDS.api_secret_key)
    ]
    assert leaked == [], f"credentials reachable via instance attributes: {leaked}"
    assert "secret" not in repr(b)


# --- retry / ambiguity routing ---


def test_a_timeout_after_submission_is_ambiguous_and_is_not_retried():
    """The duplicate-exposure case: it is unknown whether the order
    landed, so this must reconcile rather than retry."""
    import requests.exceptions as rex

    client = FakeClient(submit_raises=rex.ConnectTimeout("timed out"))
    with pytest.raises(AmbiguousSubmissionError):
        broker(client).submit_buy("TQQQ", 100.0)
    assert len(client.submitted) == 1, "an ambiguous submission must never be retried"


def test_a_rate_limit_is_retried_because_the_broker_answered():
    from alpaca.common.exceptions import APIError

    class Rate(APIError):
        status_code = 429

    client = FakeClient(submit_raises=Rate('{"message": "rate limited"}'))
    with pytest.raises(ExecutionError):
        broker(client).submit_buy("TQQQ", 100.0)
    assert len(client.submitted) > 1, "a 429 means the broker answered; retrying is safe"


# --- reconciliation snapshot ---


def test_snapshot_is_shaped_for_the_reconciler():
    client = FakeClient(
        orders=[FakeOrder(client_order_id="cid-1", status="filled", filled_qty="2", avg="50.5")],
        positions=[FakePosition("TQQQ", "3.5")],
        account=FakeAccount(cash="1234.56"),
    )
    snap = broker(client).snapshot()

    assert snap.positions == {"TQQQ": 3.5}
    assert snap.cash == 1234.56
    assert snap.orders["cid-1"]["state"] is OrderState.FILLED
    assert snap.orders["cid-1"]["filled_qty"] == 2.0
    assert snap.orders["cid-1"]["avg_fill_price"] == 50.5


def test_snapshot_requests_all_orders_not_just_open_ones():
    """Open-only would omit filled orders, and the Reconciler reads a
    locally-live order missing from the snapshot as absent at the
    broker -- turning every ordinary fill into a spurious halt."""
    client = FakeClient()
    broker(client).snapshot()
    assert client.order_filter.status.value == "all"


def test_snapshot_feeds_the_real_reconciler_without_adaptation():
    """End-to-end shape check: the Reconciler must accept this object
    as-is, or the adapter's contract is only theoretically correct."""
    from src.reconciliation import Reconciler

    class Store:
        def has_processed(self, _):
            return False

        def compare_with_broker(self, positions):
            class R:
                agrees = True

            return R()

    client = FakeClient(orders=[], positions=[], account=FakeAccount(cash="100.00"))
    report = Reconciler(Store()).reconcile(broker(client).snapshot())
    assert report.ready


# --- lookup by client order id (duplicate-order resolution) ---


def test_lookup_returns_the_order_when_the_broker_has_it():
    client = FakeClient(orders=[FakeOrder(client_order_id="cid-1")])
    assert broker(client).get_order_by_client_id("cid-1").client_order_id == "cid-1"


def test_lookup_returns_none_when_genuinely_absent():
    """Not-found is an answer, not a failure -- it is what tells the
    duplicate-order guard the order never landed."""
    assert broker(FakeClient(orders=[])).get_order_by_client_id("cid-missing") is None


def test_lookup_does_not_swallow_a_non_404_as_not_found():
    """The dangerous direction. Reporting an auth or server error as
    "no such order" would tell the duplicate-order guard that a real
    position does not exist -- so only a literal 404 may become None.
    """

    from alpaca.common.exceptions import APIError

    class Forbidden(FakeClient):
        def get_order_by_client_id(self, client_order_id):
            raise api_error(403, "forbidden")

    with pytest.raises(APIError):
        broker(Forbidden()).get_order_by_client_id("cid-1")


def test_lookup_does_not_swallow_an_error_carrying_no_http_status():
    """APIError.status_code is None when no HTTP context was attached
    (documented in retry_policy.py). An unclassifiable error must
    propagate rather than be guessed as not-found."""
    from alpaca.common.exceptions import APIError

    class NoStatus(FakeClient):
        def get_order_by_client_id(self, client_order_id):
            raise APIError('{"message": "mystery"}')

    with pytest.raises(APIError):
        broker(NoStatus()).get_order_by_client_id("cid-1")


def test_lookup_resolves_an_ambiguous_submission_through_the_real_guard():
    from src.duplicate_order_guard import DuplicateOrderGuard

    class Store:
        def __init__(self):
            self.refs = {}
            self.processed = {"cid-1": "order_submission"}

        def has_processed(self, decision_id):
            return decision_id in self.processed

        def get_event_result_ref(self, decision_id):
            return self.refs.get(decision_id)

        def set_event_result_ref(self, decision_id, ref):
            self.refs[decision_id] = ref

    b = broker(FakeClient(orders=[FakeOrder(client_order_id="cid-1")]))
    guard = DuplicateOrderGuard(Store())
    resolved = guard.resolve_ambiguous_submission("cid-1", b.get_order_by_client_id)
    assert resolved == "cid-1", "a found order is adopted, never re-submitted"


# --- connection check ---


def test_ping_hits_an_authenticated_endpoint():
    """TradingClient's constructor performs no I/O, so a typo'd key
    would otherwise pass CONNECT_BROKER and fail at the first order."""
    client = FakeClient()
    broker(client).ping()  # must not raise


def test_ping_failure_surfaces_as_an_execution_error():
    from src.exceptions import ExecutionError

    class Dead(FakeClient):
        def get_account(self):
            raise ConnectionError("no route to host")

    with pytest.raises(ExecutionError, match="connection check failed"):
        broker(Dead()).ping()


# --- SDK contract: verified against the really-installed alpaca-py ---


def test_alpaca_sdk_still_supports_notional_market_orders():
    from alpaca.trading.enums import OrderSide, TimeInForce
    from alpaca.trading.requests import MarketOrderRequest

    request = MarketOrderRequest(
        symbol="TQQQ",
        notional=100.0,
        side=OrderSide.BUY,
        time_in_force=TimeInForce.DAY,
    )
    assert request.notional == 100.0


def test_alpaca_sdk_still_accepts_a_fractional_limit_sell():
    """The single assumption this adapter's safety argument rests on.

    Alpaca's documentation supports fractional limit orders with
    time_in_force=Day; the installed SDK's OrderRequest docstring
    still claims fractional works only with market orders. If that
    stale line ever becomes true again, this test is where it must be
    caught -- a market sell cannot carry the no-loss guarantee.
    """
    from alpaca.trading.enums import OrderSide, TimeInForce
    from alpaca.trading.requests import LimitOrderRequest

    request = LimitOrderRequest(
        symbol="TQQQ",
        qty=3.5,
        side=OrderSide.SELL,
        time_in_force=TimeInForce.DAY,
        limit_price=101.01,
    )
    assert request.qty == 3.5
    assert request.limit_price == 101.01


def test_trading_client_still_routes_paper_by_constructor_flag():
    import inspect

    from alpaca.trading.client import TradingClient

    assert "paper" in inspect.signature(TradingClient.__init__).parameters


def test_alpaca_order_still_exposes_every_field_the_snapshot_reads():
    from alpaca.trading.models import Order, Position, TradeAccount

    for field in ("client_order_id", "status", "filled_qty", "filled_avg_price", "symbol"):
        assert field in Order.model_fields, f"snapshot() reads Order.{field}"
    for field in ("symbol", "qty"):
        assert field in Position.model_fields, f"snapshot() reads Position.{field}"
    assert "cash" in TradeAccount.model_fields


# --- extended hours: the buy changes SHAPE, not just a flag -----------
#
# Alpaca will not execute a market order outside regular hours, and its
# own OrderRequest docstring says notional "only works with MarketOrders"
# and "does not work with qty". Those two facts together mean an
# extended-hours buy cannot be notional AND cannot be a market order --
# so enabling extended hours has to change the order the adapter builds,
# not merely set a flag on the one it already built.
#
# The previous code set extended_hours on the SELL only and documented
# the buy as impossible. The observation was right; the conclusion was
# not.


def _ext(**kw):
    return broker(extended_hours=True, **kw)


def test_a_regular_hours_buy_is_still_a_notional_market_order():
    """The default path must not move. limit_price is accepted and
    ignored, so callers pass it unconditionally."""
    client = FakeClient()
    broker(client).submit_buy("TQQQ", 100.0, client_order_id="cid", limit_price=50.0)
    request = client.submitted[0]
    assert request.notional == 100.0
    assert getattr(request, "limit_price", None) is None
    assert getattr(request, "qty", None) is None


def test_an_extended_hours_buy_is_a_share_sized_limit_order():
    client = FakeClient()
    _ext(client=client).submit_buy("TQQQ", 100.0, client_order_id="cid", limit_price=20.0)
    request = client.submitted[0]
    assert request.qty == 5
    assert float(request.limit_price) == 20.0
    assert request.notional is None, "notional does not work with qty"
    assert request.extended_hours is True
    assert request.time_in_force.value == "day", "Alpaca requires DAY with extended_hours"


def test_an_extended_hours_buy_without_a_limit_price_is_refused():
    """THE IMPORTANT REFUSAL. Falling back to a market order would build
    an order the venue rejects at 4:30pm, and the deployment would look
    like it was trading extended hours while placing nothing."""
    client = FakeClient()
    with pytest.raises(ConfigurationError, match="no limit_price"):
        _ext(client=client).submit_buy("TQQQ", 100.0, client_order_id="cid")
    assert client.submitted == [], "nothing may reach the venue"


def test_the_buy_limit_floors_so_the_cost_basis_never_rises():
    """Mirror of the sell limit's ceiling, for the same invariant. A buy
    fill BECOMES the cost basis every later sell is validated against,
    so rounding a buy limit up would raise the bar the lot must clear."""
    client = FakeClient()
    _ext(client=client).submit_buy("TQQQ", 100.0, client_order_id="cid", limit_price=20.999)
    assert float(client.submitted[0].limit_price) == 20.99


def test_the_share_count_floors_so_cost_stays_inside_the_budget():
    """trade_value is RiskManager's approved ceiling; the order may cost
    less than it, never more."""
    client = FakeClient()
    _ext(client=client).submit_buy("TQQQ", 100.0, client_order_id="cid", limit_price=30.0)
    request = client.submitted[0]
    assert request.qty == 3
    assert request.qty * float(request.limit_price) <= 100.0


def test_an_extended_hours_buy_is_whole_shares_never_fractional():
    """Fractional trading is a regular-hours facility at Alpaca. Sizing
    to whole shares here beats discovering it as a venue rejection."""
    client = FakeClient()
    _ext(client=client).submit_buy("TQQQ", 100.0, client_order_id="cid", limit_price=30.0)
    assert float(client.submitted[0].qty).is_integer()


def test_a_budget_too_small_for_one_share_says_so_rather_than_rounding_to_zero():
    client = FakeClient()
    with pytest.raises(ValueError, match="one whole share"):
        _ext(client=client).submit_buy("TQQQ", 10.0, client_order_id="cid", limit_price=20.0)
    assert client.submitted == []


def test_extended_hours_still_reaches_the_sell_side():
    """The flag's original job has not been lost in the rework."""
    client = FakeClient()
    _ext(client=client).submit_sell("TQQQ", 2.0, 25.0, client_order_id="cid")
    assert client.submitted[0].extended_hours is True


@pytest.mark.parametrize("bad", [0.0, -1.0])
def test_a_non_positive_limit_price_is_refused(bad):
    client = FakeClient()
    with pytest.raises(ValueError, match="limit_price must be positive"):
        _ext(client=client).submit_buy("TQQQ", 100.0, client_order_id="cid", limit_price=bad)
    assert client.submitted == []


def test_extended_hours_comes_from_the_deployment_config_not_a_caller_kwarg():
    """It changes the SHAPE of every buy, so the file that describes the
    deployment must be what decides it."""
    from types import SimpleNamespace

    from src.broker_selection import build_broker

    config = SimpleNamespace(
        live=SimpleNamespace(
            broker="alpaca", paper_trading=True, extended_hours=True, fidelity=None
        )
    )
    built = build_broker(config, credentials=CREDS, client=FakeClient())
    assert built.extended_hours is True
