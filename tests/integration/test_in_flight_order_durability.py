"""In-flight orders must survive a restart that was not a clean shutdown.

open_orders and sells_in_flight were memory-only. Any restart that did
not drain them -- a crash, an OOM kill, a redeploy, a scheduled task
firing -- forgot every resting order, and three things followed, none
detectable at the time:

  * the fill was never applied, so cash and the ledger silently missed
    an execution that really happened;
  * sells_in_flight came back empty, so a lot with a live resting sell
    was eligible for a SECOND sell, and DuplicateOrderGuard cannot stop
    it -- its decision_id is derived from the bar timestamp, which
    differs on the next tick;
  * startup reconciliation caught neither, because a RESTING order
    leaves broker and local POSITIONS agreeing.

The double sell is the one that costs money: in the cash IRA this
system targets, it is a sale of shares the account does not hold.

`test_a_lot_with_a_sell_in_flight_is_not_offered_again` in
test_live_trading_loop.py is the same assertion within one process.
These are its across-a-restart counterparts, and a restart is modelled
the way the process actually experiences it -- a second LiveTradingLoop
constructed over the same LedgerStore, with nothing carried across in
memory.
"""

from __future__ import annotations

import json
from datetime import timedelta

import pytest

from src.exceptions import PersistenceError
from src.fill_accounting import FillTracker
from src.live_trading_loop import _META_OPEN_ORDERS, _TrackedOrder
from src.no_loss_guard import SellReason
from tests.integration.test_live_trading_loop import (
    BASE_TS,
    FakeBroker,
    FakeMarketData,
    _loop_with_an_open_lot,
    make_loop,
    store,  # noqa: F401  -- the LedgerStore fixture, reused deliberately
)

# --- the serialised form ---


def test_round_trip_preserves_every_field():
    tracker = FillTracker("sell-1")
    tracker.apply_update(4.0, 25.0)
    original = _TrackedOrder(
        client_order_id="sell-1",
        kind="sell",
        tracker=tracker,
        lot_order_id="lot-7",
        trigger_price=24.0,
        profit_target=0.03,
        sell_reason=SellReason.SIGNAL_EXIT,
    )

    restored = _TrackedOrder.from_dict(json.loads(json.dumps(original.to_dict())))

    assert restored.client_order_id == "sell-1"
    assert restored.kind == "sell"
    assert restored.lot_order_id == "lot-7"
    assert restored.trigger_price == pytest.approx(24.0)
    assert restored.profit_target == pytest.approx(0.03)
    assert restored.sell_reason is SellReason.SIGNAL_EXIT


def test_the_cumulative_baseline_survives_so_a_fill_is_not_booked_twice():
    """The single most important assertion in this file.

    A tracker rebuilt at zero reads the broker's CUMULATIVE figures as
    one enormous first increment. Restoring 10 already-applied shares
    and then seeing the broker still report 10 must yield an EMPTY
    delta, not a second 10-share fill.
    """
    tracker = FillTracker("buy-1")
    tracker.apply_update(10.0, 50.0)
    order = _TrackedOrder(client_order_id="buy-1", kind="buy", tracker=tracker)

    restored = _TrackedOrder.from_dict(order.to_dict())

    assert restored.tracker.apply_update(10.0, 50.0).is_empty, (
        "a restart re-applied a fill that had already been booked"
    )
    # A fill that landed WHILE the process was down is still picked up,
    # as the increment only.
    assert restored.tracker.apply_update(15.0, 50.0).qty == pytest.approx(5.0)


def test_sell_reason_survives_so_a_restored_signal_exit_is_not_refused():
    """Losing the reason would default the fill to PROFIT_TARGET, the
    no-loss guard would refuse it, and the lot would stay open in our
    ledger after the broker had already sold it."""
    order = _TrackedOrder(
        client_order_id="sell-2",
        kind="sell",
        tracker=FillTracker("sell-2"),
        lot_order_id="lot-1",
        sell_reason=SellReason.SIGNAL_EXIT,
    )
    assert _TrackedOrder.from_dict(order.to_dict()).sell_reason is SellReason.SIGNAL_EXIT


# --- across a real restart ---


def test_a_resting_sell_is_not_reoffered_after_a_restart(store):  # noqa: F811
    """THE BUG. Two sell orders against one position, one per process."""
    broker = FakeBroker()
    market = FakeMarketData()
    loop = _loop_with_an_open_lot(store, broker, market)
    lot = loop.ledger.open_lots[0]

    market.push(lot.target_sell_price + 1.0, ts=BASE_TS + timedelta(minutes=3))
    loop.run_once()
    assert len(broker.sells) == 1

    # The process dies here. Nothing is drained, nothing is closed.
    restarted = make_loop(store, broker, market)

    assert restarted.state.sells_in_flight == {lot.order_id}
    assert set(restarted.state.open_orders) == set(loop.state.open_orders)

    for i in range(4, 7):
        market.push(lot.target_sell_price + 1.0, ts=BASE_TS + timedelta(minutes=i))
        restarted.run_once()

    assert len(broker.sells) == 1, "the restarted loop sold shares that were already sold"


def test_a_fill_that_lands_while_the_process_is_down_is_applied_exactly_once(store):  # noqa: F811
    """The other half: the restart must not LOSE the execution either."""
    broker = FakeBroker()
    market = FakeMarketData()
    loop = _loop_with_an_open_lot(store, broker, market)
    lot = loop.ledger.open_lots[0]
    cash_before = loop.state.cash

    market.push(lot.target_sell_price + 1.0, ts=BASE_TS + timedelta(minutes=3))
    loop.run_once()
    _, qty, target, sell_cid = broker.sells[0]

    # Filled while nothing was watching.
    broker.fill(sell_cid, qty=qty, price=target)
    restarted = make_loop(store, broker, market)

    market.push(lot.target_sell_price + 1.0, ts=BASE_TS + timedelta(minutes=4))
    restarted.run_once()

    assert restarted.ledger.open_lots == []
    assert len(restarted.ledger.closed_lots) == 1
    assert restarted.state.cash == pytest.approx(cash_before + qty * target)

    # And a further tick does not book it a second time.
    market.push(lot.target_sell_price + 1.0, ts=BASE_TS + timedelta(minutes=5))
    restarted.run_once()
    assert restarted.state.cash == pytest.approx(cash_before + qty * target)


def test_a_resting_buy_survives_and_still_opens_its_lot(store):  # noqa: F811
    """Buys are tracked in the same table and were lost the same way."""
    broker = FakeBroker()
    market = FakeMarketData()
    market.push(100.0)
    loop = make_loop(store, broker, market)
    loop.run_once()
    market.push(98.0, ts=BASE_TS + timedelta(minutes=1))
    loop.run_once()
    _, _, buy_cid = broker.buys[0]

    restarted = make_loop(store, broker, market)
    assert buy_cid in restarted.state.open_orders

    broker.fill(buy_cid, qty=10.0, price=98.0)
    market.push(98.0, ts=BASE_TS + timedelta(minutes=2))
    restarted.run_once()

    assert len(restarted.ledger.open_lots) == 1
    assert restarted.ledger.open_lots[0].shares == pytest.approx(10.0)


def test_a_terminal_order_is_dropped_durably_and_does_not_come_back(store):  # noqa: F811
    """The removal side has to be written through too, or a settled
    order returns on every restart and blocks its lot forever."""
    broker = FakeBroker()
    market = FakeMarketData()
    loop = _loop_with_an_open_lot(store, broker, market)
    lot = loop.ledger.open_lots[0]

    market.push(lot.target_sell_price + 1.0, ts=BASE_TS + timedelta(minutes=3))
    loop.run_once()
    _, qty, target, sell_cid = broker.sells[0]
    broker.fill(sell_cid, qty=qty, price=target)
    market.push(lot.target_sell_price + 1.0, ts=BASE_TS + timedelta(minutes=4))
    loop.run_once()
    assert loop.state.open_orders == {}

    restarted = make_loop(store, broker, market)
    assert restarted.state.open_orders == {}
    assert restarted.state.sells_in_flight == set()


# --- unreadable state ---


def test_corrupt_state_refuses_to_start_rather_than_defaulting_to_empty(store):  # noqa: F811
    """Empty is exactly the broken behaviour being replaced.

    "In-flight orders unknown" is not a state in which it is safe to
    harvest, so this fails closed instead of quietly resuming.
    """
    make_loop(store, FakeBroker(), FakeMarketData())
    store.set_meta(_META_OPEN_ORDERS, "{not json")

    with pytest.raises(PersistenceError, match="unreadable"):
        make_loop(store, FakeBroker(), FakeMarketData())


def test_a_malformed_entry_refuses_to_start(store):  # noqa: F811
    make_loop(store, FakeBroker(), FakeMarketData())
    store.set_meta(_META_OPEN_ORDERS, json.dumps([{"kind": "sell"}]))

    with pytest.raises(PersistenceError):
        make_loop(store, FakeBroker(), FakeMarketData())


def test_absent_state_is_a_fresh_deployment_not_a_failure(store):  # noqa: F811
    """Absent and corrupt are different facts -- the same distinction
    _restore_settlement draws, for the same reason."""
    loop = make_loop(store, FakeBroker(), FakeMarketData())
    assert loop.state.open_orders == {}
    assert loop.state.sells_in_flight == set()
