"""
ONE contract, run against BOTH broker adapters.

Step 6 of the Fidelity plan. Until now nothing asserted that the two
venues present the same surface -- the closest test instantiated
AlpacaBroker directly, so it could only ever describe Alpaca. Every
divergence between the adapters was therefore invisible until
live_trading_loop hit it against real money.

WHY THIS IS NOT THE `LiveBroker` PROTOCOL
src/live_execution.LiveBroker names two methods, submit_buy and
submit_sell. The live loop and the reconciler actually depend on five,
and the Protocol is not runtime_checkable, so it cannot even be asserted
against. It documents an interface narrower than the one that exists.
This file pins the REAL contract -- what live_trading_loop.py,
reconciliation.py, fill_accounting.py and duplicate_order_guard.py
genuinely read -- rather than the declared one.

Both adapters run every test below against injected fakes. No network,
no browser, no credentials, no account.

The Fidelity adapter is PREVIEW-ONLY by construction, so where the
contract concerns submission the assertion is on the returned object's
shape, never on the venue having accepted anything. That difference is
itself pinned, at the bottom, so it stays a deliberate property rather
than becoming an unnoticed divergence.
"""

from __future__ import annotations

import pytest

from src.alpaca_broker import AlpacaBroker
from src.fidelity_broker import PREVIEW_PATH, FidelityBroker
from src.order_lifecycle import OrderState
from src.reconciliation import BrokerSnapshot, Reconciler
from src.retry_policy import RetryConfig
from src.secrets import LiveCredentials
from tests.unit.test_alpaca_broker import FakeAccount, FakeClient, FakeOrder, FakePosition
from tests.unit.test_fidelity_broker import ACCOUNT, FILLED, FakeSession

FAST_RETRY = RetryConfig(base_delay=0.001, max_attempts=2)


# --- builders: each returns (broker, notes) for one venue --------------


def _alpaca(orders=(), positions=(), cash="1000.00"):
    client = FakeClient(
        orders=list(orders), positions=list(positions), account=FakeAccount(cash=cash)
    )
    broker = AlpacaBroker(
        LiveCredentials(api_key_id="PKTEST", api_secret_key="secret"),
        client=client,
        retry_config=FAST_RETRY,
    )
    return broker


def _fidelity(orders=(), positions=(), cash=1000.00):
    session = FakeSession(
        {
            "/ftgw/digital/trade-equity/getquote": {
                "QUOTE_DATA": {"ASK_PRICE": "100.00", "LAST_PRICE": "100.00"}
            },
            PREVIEW_PATH: {"preview": {"orderConfirmDetail": {"confNum": "2C50H6WV"}}},
            "/ftgw/digital/activityapi/api/v1/transactions/pending": {
                "data": {"orders": list(orders)}
            },
            "/ftgw/digital/trade-equity/positions": list(positions),
            "/ftgw/digital/trade-equity/balance": {"cashDetail": {"settledAmt": cash}},
        }
    )
    return FidelityBroker(session, ACCOUNT, (ACCOUNT,))


def _empty_alpaca():
    return _alpaca()


def _empty_fidelity():
    return _fidelity()


BUILDERS = [pytest.param(_empty_alpaca, id="alpaca"), pytest.param(_empty_fidelity, id="fidelity")]


# --- the surface -------------------------------------------------------


@pytest.mark.parametrize("build", BUILDERS)
@pytest.mark.parametrize(
    "method", ["submit_buy", "submit_sell", "get_order_by_client_id", "snapshot", "ping"]
)
def test_every_adapter_exposes_the_five_methods_the_loop_actually_uses(build, method):
    """Not the two the Protocol declares. See the module docstring."""
    assert callable(getattr(build(), method, None)), (
        f"{method} missing -- live_trading_loop or reconciliation calls it"
    )


@pytest.mark.parametrize("build", BUILDERS)
def test_ping_succeeds_against_a_healthy_connection(build):
    build().ping()


# --- submission returns something the loop can read --------------------


@pytest.mark.parametrize("build", BUILDERS)
def test_a_buy_returns_an_object_carrying_the_ids_the_loop_reads(build):
    """live_trading_loop does str(broker.submit_*(...).id) and stores the
    client_order_id. Both must be present and non-empty."""
    order = build().submit_buy("TQQQ", 500.0, client_order_id="dec-1")
    assert str(order.id)
    assert order.client_order_id == "dec-1"
    assert order.status is not None


@pytest.mark.parametrize("build", BUILDERS)
def test_a_sell_returns_an_object_carrying_the_ids_the_loop_reads(build):
    order = build().submit_sell("TQQQ", 3, 105.25, client_order_id="dec-2")
    assert str(order.id)
    assert order.client_order_id == "dec-2"


@pytest.mark.parametrize("build", BUILDERS)
def test_a_notional_buy_never_rounds_up(build):
    """Both venues size a dollar amount into shares. Rounding UP would
    overspend the amount risk actually cleared, so both must floor."""
    order = build().submit_buy("TQQQ", 250.0, client_order_id="dec-3")
    qty = float(getattr(order, "qty", 0) or 0)
    if qty:  # Alpaca submits notional and may not echo a share count
        assert qty * 100.0 <= 250.0 + 1e-9


@pytest.mark.parametrize("build", BUILDERS)
@pytest.mark.parametrize("bad", [0.0, -1.0])
def test_a_non_positive_trade_value_is_refused_by_both(build, bad):
    """SAME exception type from both, not merely "some error".

    The first run of this file caught the adapters disagreeing here --
    Alpaca raised ValueError, Fidelity ExecutionError. Two venues
    rejecting identical bad input with different types is exactly the
    divergence this file exists to find, and a caller that catches one
    would sail past the other. ValueError is the convention: a bad
    ARGUMENT, as against ExecutionError for a bad VENUE RESPONSE.
    """
    with pytest.raises(ValueError):
        build().submit_buy("TQQQ", bad)


@pytest.mark.parametrize("build", BUILDERS)
@pytest.mark.parametrize("bad", [0.0, -3.0])
def test_a_non_positive_sell_quantity_is_refused_by_both(build, bad):
    with pytest.raises(ValueError):
        build().submit_sell("TQQQ", bad, 105.25)


# --- lookup ------------------------------------------------------------


@pytest.mark.parametrize("build", BUILDERS)
def test_an_absent_order_is_none_not_an_exception(build):
    """Not-found is an ANSWER. It is what tells the duplicate-order guard
    the order never landed; raising would look like a transport failure
    and send it down the ambiguous-submission path instead."""
    assert build().get_order_by_client_id("never-submitted") is None


# --- the snapshot the reconciler consumes ------------------------------


@pytest.mark.parametrize(
    "build",
    [
        pytest.param(
            lambda: _alpaca(
                orders=[
                    FakeOrder(client_order_id="dec-1", status="filled", filled_qty="2", avg="69.35")
                ],
                positions=[FakePosition(symbol="TQQQ", qty="2")],
            ),
            id="alpaca",
        ),
        pytest.param(
            lambda: _fidelity(
                orders=[FILLED],
                positions=[{"symbol": "TQQQ", "quantity": 2.0}],
            ),
            id="fidelity",
        ),
    ],
)
class TestSnapshotContract:
    """Grouped because every one of these reads the same populated
    snapshot, and building it per test would hide which field broke."""

    def test_it_is_a_real_broker_snapshot(self, build):
        assert isinstance(build().snapshot(), BrokerSnapshot)

    def test_positions_map_symbol_to_a_float_share_count(self, build):
        positions = build().snapshot().positions
        assert positions == {"TQQQ": pytest.approx(2.0)}
        assert all(isinstance(v, float) for v in positions.values())

    def test_every_order_row_has_the_four_keys_reconciliation_reads(self, build):
        for key, row in build().snapshot().orders.items():
            assert isinstance(key, str) and key
            assert set(row) >= {"state", "filled_qty", "avg_fill_price", "symbol"}

    def test_state_is_a_canonical_orderstate_not_a_venue_string(self, build):
        """The whole point of an adapter. A venue string reaching
        reconciliation is the bug this contract exists to catch -- and
        Fidelity's own status field is prose with the fill price inside
        it ("Filled at $69.35"), which would map to UNKNOWN and halt."""
        for row in build().snapshot().orders.values():
            assert isinstance(row["state"], OrderState)
            assert row["state"] is not OrderState.UNKNOWN

    def test_fill_figures_are_numbers_not_strings(self, build):
        """Alpaca returns these as strings over the wire. Reconciliation
        does arithmetic on them."""
        for row in build().snapshot().orders.values():
            assert isinstance(row["filled_qty"], float)
            assert isinstance(row["avg_fill_price"], float)

    def test_the_real_reconciler_accepts_it_without_adaptation(self, build):
        class Store:
            def has_processed(self, _):
                return False

            def compare_with_broker(self, positions):
                class R:
                    agrees = True

                return R()

        report = Reconciler(Store()).reconcile(build().snapshot())
        assert report is not None


@pytest.mark.parametrize("build", BUILDERS)
def test_an_empty_account_snapshots_cleanly_rather_than_raising(build):
    snap = build().snapshot()
    assert snap.positions == {}
    assert snap.orders == {}


# --- where the two venues deliberately differ --------------------------


def test_only_the_fidelity_adapter_is_preview_only():
    """Pinned so the difference stays DELIBERATE.

    Alpaca submits; Fidelity previews and stops. If Fidelity ever starts
    returning SUBMITTED this fails, which is the notification that
    something granted it a capability it is not supposed to have.
    """
    assert _fidelity().submit_buy("TQQQ", 500.0).state is OrderState.CREATED

    alpaca_order = _alpaca().submit_buy("TQQQ", 500.0)
    assert alpaca_order.status is not None
    assert str(getattr(alpaca_order.status, "value", alpaca_order.status)) != "CREATED"
