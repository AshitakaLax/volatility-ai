"""engine/core/exit_policy.py and its use in engine/trading/decision_cycle.py:
the quantity half of a sell decision (Phase 1 of
docs/research/buy-sell-composition.md)."""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from engine.core import exit_policy
from engine.core.exit_policy import ExitOrder, floor_shares, sellable_quantity
from engine.core.ledger import AssetLotLedger
from engine.core.persistence import LedgerStore
from engine.trading import decision_cycle
from engine.trading.no_loss_guard import SellReason


def test_the_reasons_are_the_guards_own():
    """core/ cannot import SellReason, so it carries its values; they must
    stay the same strings or a partial exit would be booked under the wrong
    reason."""
    assert SellReason.PROFIT_TARGET.value == exit_policy.PROFIT_TARGET
    assert SellReason.SIGNAL_EXIT.value == exit_policy.SIGNAL_EXIT
    assert {SellReason(r) for r in exit_policy.REASONS} == set(SellReason)


@pytest.mark.parametrize(
    ("requested", "shares", "whole", "expected"),
    [
        (10.0, 10.0, False, 10.0),  # the whole lot, exactly
        (12.0, 10.0, False, 10.0),  # never more than it holds
        (5.0, 10.0, False, 5.0),
        (1 / 3, 1.0, False, 0.333333333),  # floored to nine decimals
        (2.7, 10.0, True, 2.0),  # whole-share venue: floored to shares
        (0.6, 10.0, True, 0.0),  # floors to nothing: wait, do not sell it all
        (9.9999999999, 10.0, False, 10.0),  # within epsilon of the lot is the lot
        (0.0, 10.0, False, 0.0),
        (-1.0, 10.0, False, 0.0),
        (float("nan"), 10.0, False, 0.0),
        (5.0, 0.0, False, 0.0),
    ],
)
def test_sellable_quantity(requested, shares, whole, expected):
    assert sellable_quantity(requested, shares, whole_shares=whole) == pytest.approx(expected)


def test_a_whole_lot_request_returns_the_lots_own_shares_object_value():
    """So a caller comparing with lot.shares takes the whole-lot path."""
    shares = 0.123456789123
    assert sellable_quantity(shares, shares) == shares


def test_floor_shares_never_rounds_up():
    assert floor_shares(1.9999999999) == 1.999999999
    assert floor_shares(2.0) == 2.0


def test_exit_order_validates_itself():
    lot = SimpleNamespace(shares=4.0)
    with pytest.raises(ValueError):
        ExitOrder(lot, 0.0)
    with pytest.raises(ValueError):
        ExitOrder(lot, float("inf"))
    with pytest.raises(ValueError):
        ExitOrder(lot, 1.0, "stop_loss")
    assert ExitOrder(lot, 4.0).whole and not ExitOrder(lot, 1.0).whole
    a, b = ExitOrder(lot, 1.0), ExitOrder(lot, 1.0)
    assert a != b, "identity equality: two orders are two orders"


# --- decision_cycle ------------------------------------------------------


def _book(*sizes):
    ledger = AssetLotLedger()
    lots = [ledger.register_buy(f"L{i}", "TQQQ", 100.0, s, 0.01) for i, s in enumerate(sizes)]
    return ledger, lots


class _Exits:
    def __init__(self, make):
        self.make = make

    def lots_to_liquidate(self, open_lots, context):
        return self.make(open_lots)


def test_partial_and_whole_liquidations_become_signal_exit_orders():
    ledger, (a, b, _c) = _book(10.0, 4.0, 3.0)
    strategy = _Exits(lambda lots: [ExitOrder(lots[0], 2.5), lots[1], ExitOrder(lots[0], 9.0)])
    orders = decision_cycle.collect_liquidations(
        strategy, ledger, None, allow_signal_exit=True, as_orders=True
    )
    assert [(o.lot, o.quantity, o.reason) for o in orders] == [
        (a, 2.5, exit_policy.SIGNAL_EXIT),  # the first entry for a lot wins
        (b, 4.0, exit_policy.SIGNAL_EXIT),
    ]
    assert decision_cycle.collect_liquidations(strategy, ledger, None, allow_signal_exit=True) == [
        a,
        b,
    ], "without as_orders: the condemned lots, as it always was"


def test_partial_liquidations_still_need_the_flag():
    ledger, _ = _book(10.0)
    strategy = _Exits(lambda lots: [ExitOrder(lots[0], 1.0)])
    assert (
        decision_cycle.collect_liquidations(
            strategy, ledger, None, allow_signal_exit=False, as_orders=True
        )
        == []
    )


def test_a_whole_share_venue_drops_a_tranche_smaller_than_a_share():
    ledger, (_a, b) = _book(10.0, 10.0)
    strategy = _Exits(lambda lots: [ExitOrder(lots[0], 0.4), ExitOrder(lots[1], 3.6)])
    orders = decision_cycle.collect_liquidations(
        strategy, ledger, None, allow_signal_exit=True, as_orders=True, whole_shares=True
    )
    assert [(o.lot, o.quantity) for o in orders] == [(b, 3.0)]


def test_a_stale_exit_order_is_ignored():
    ledger, _ = _book(10.0)
    ghost = AssetLotLedger().register_buy("ghost", "TQQQ", 1.0, 1.0, 0.01)
    strategy = _Exits(lambda lots: [ExitOrder(ghost, 1.0)])
    assert (
        decision_cycle.collect_liquidations(
            strategy, ledger, None, allow_signal_exit=True, as_orders=True
        )
        == []
    )


class _Halves:
    def harvest_quantity(self, lot, context):
        return lot.shares / 2


def test_harvest_orders_default_to_the_whole_lot():
    _, lots = _book(10.0, 3.0)
    orders = decision_cycle.harvest_orders(object(), lots, None)
    assert [(o.lot, o.quantity, o.reason) for o in orders] == [
        (lots[0], 10.0, exit_policy.PROFIT_TARGET),
        (lots[1], 3.0, exit_policy.PROFIT_TARGET),
    ]
    assert all(o.whole for o in orders)


def test_harvest_orders_ask_the_strategy_how_much():
    _, lots = _book(10.0, 3.0)
    orders = decision_cycle.harvest_orders(_Halves(), lots, None)
    assert [o.quantity for o in orders] == [5.0, 1.5]


def test_legacy_lots_always_sell_whole():
    _, lots = _book(10.0, 3.0)
    orders = decision_cycle.harvest_orders(_Halves(), lots, None, skip_order_ids={"L1"})
    assert [o.quantity for o in orders] == [5.0, 3.0]


def test_a_tranche_that_shapes_to_nothing_is_not_sold_this_bar():
    _, lots = _book(1.0, 10.0)
    orders = decision_cycle.harvest_orders(_Halves(), lots, None, whole_shares=True)
    assert [(o.lot, o.quantity) for o in orders] == [(lots[1], 5.0)]


def test_lot_tag_is_optional_and_typed():
    assert decision_cycle.lot_tag(object()) is None
    assert decision_cycle.lot_tag(SimpleNamespace(next_lot_tag=lambda: "reversal")) == "reversal"
    with pytest.raises(TypeError):
        decision_cycle.lot_tag(SimpleNamespace(next_lot_tag=lambda: 3))


# --- the ledger and its store ---------------------------------------------


def test_a_lot_remembers_its_opening_size_and_tag():
    ledger = AssetLotLedger()
    lot = ledger.register_buy("L", "TQQQ", 100.0, 8.0, 0.01, entry_tag="reversal")
    assert (lot.original_shares, lot.entry_tag, lot.sold_fraction) == (8.0, "reversal", 0.0)
    ledger.close_lot(lot, sell_qty=2.0, execution_price=101.0)
    assert (lot.shares, lot.original_shares, lot.sold_fraction) == (6.0, 8.0, 0.25)
    assert (lot.partial_sold_shares, lot.partial_sold_value) == (2.0, 202.0)


def test_a_half_sold_tagged_lot_survives_a_restart(tmp_path):
    path = str(tmp_path / "ledger.db")
    store = LedgerStore(path)
    ledger = AssetLotLedger()
    lot = ledger.register_buy("L", "TQQQ", 100.0, 8.0, 0.01, entry_tag="reversal")
    store.record_open_lot(lot)
    ledger.close_lot(lot, sell_qty=4.0, execution_price=101.0)
    store.sync_lot(ledger, lot)
    lot.retarget(0.03)  # the ladder's next rung
    store.record_open_lot(lot)  # what the live loop does after a retarget
    store.close()

    (restored,) = LedgerStore(path).load_ledger().open_lots
    assert (restored.shares, restored.original_shares, restored.entry_tag) == (4.0, 8.0, "reversal")
    assert restored.sold_fraction == 0.5
    assert restored.profit_target == 0.03


def test_a_lot_recorded_before_details_existed_loads_as_unsold(tmp_path):
    path = str(tmp_path / "ledger.db")
    store = LedgerStore(path)
    store.record_open_lot(AssetLotLedger().register_buy("L", "TQQQ", 100.0, 8.0, 0.01))
    store._conn.execute("DELETE FROM ledger_lot_details")
    store._conn.commit()
    (lot,) = store.load_ledger().open_lots
    assert (lot.shares, lot.original_shares, lot.entry_tag) == (8.0, 8.0, None)
