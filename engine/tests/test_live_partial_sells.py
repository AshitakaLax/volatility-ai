"""Partial-lot selling in the live loop (Phase 1 of
docs/research/buy-sell-composition.md): a ladder's tranches, a partial
signal exit's per-lot quantities, a whole-share venue, and a buy's entry tag
-- each surviving the asynchrony of real fills and a restart."""

from __future__ import annotations

from datetime import timedelta

import pytest

from engine.core.exit_policy import ExitOrder
from engine.tests.test_live_trading_loop import (
    BASE_TS,
    BOOK,
    FakeBroker,
    FakeMarketData,
    _book,
    make_config,
    make_loop,
    store,  # noqa: F401 -- the fixture
)
from research.strategies.size_calculators import FixedPortfolioPercentage

RUNG_TOLERANCE = 1e-6


class _Ladder(FixedPortfolioPercentage):
    """Half at the base target, the rest at 3%."""

    def wants_lot_retargeting(self) -> bool:
        return True

    def adjust_profit_target(self, lot, context):
        return 0.03 if lot.sold_fraction >= 0.5 - RUNG_TOLERANCE else None

    def harvest_quantity(self, lot, context):
        if lot.sold_fraction < 0.5 - RUNG_TOLERANCE:
            return lot.original_shares * 0.5
        return lot.shares


class _Tagged(FixedPortfolioPercentage):
    def next_lot_tag(self):
        return "reversal"


class _TrimsBelow(FixedPortfolioPercentage):
    def lots_to_liquidate(self, open_lots, context):
        return [ExitOrder(lot, lot.shares / 2) for lot in open_lots] if context.price < 95 else []


def _open_lot(ledger_store, broker, market, strategy, qty=10.0, buy_price=98.0, config=None):
    market.push(100.0)
    loop = make_loop(ledger_store, broker, market, strategy=strategy, config=config)
    loop.run_once()
    market.push(buy_price, ts=BASE_TS + timedelta(minutes=1))
    loop.run_once()
    _, _, cid = broker.buys[0]
    broker.fill(cid, qty=qty, price=buy_price)
    market.push(buy_price, ts=BASE_TS + timedelta(minutes=2))
    loop.run_once()
    return loop


def test_a_ladder_sells_half_then_the_rest_at_its_next_rung(store):  # noqa: F811
    broker, market = FakeBroker(), FakeMarketData()
    loop = _open_lot(store, broker, market, _Ladder(allocation_pct=0.05))
    (lot,) = loop.ledger.open_lots
    first_target = lot.target_sell_price

    market.push(first_target + 0.5, ts=BASE_TS + timedelta(minutes=3))
    loop.run_once()
    _, qty, price, cid = broker.sells[0]
    assert (qty, price) == (5.0, first_target), "half the lot, at its own target"
    broker.fill(cid, qty=qty, price=price)

    market.push(first_target + 0.5, ts=BASE_TS + timedelta(minutes=4))
    loop.run_once()
    (lot,) = loop.ledger.open_lots
    assert (lot.shares, lot.original_shares) == (5.0, 10.0)
    assert lot.profit_target == 0.03, "moved to the next rung once half had sold"
    assert len(broker.sells) == 1, "below the next rung, nothing more is offered"

    market.push(98.0 * 1.03 + 0.5, ts=BASE_TS + timedelta(minutes=5))
    loop.run_once()
    _, qty, price, cid = broker.sells[1]
    assert (qty, price) == (5.0, pytest.approx(98.0 * 1.03))
    broker.fill(cid, qty=qty, price=price)
    market.push(98.0 * 1.03 + 0.5, ts=BASE_TS + timedelta(minutes=6))
    loop.run_once()
    assert loop.ledger.open_lots == []


def test_a_half_sold_lot_resumes_on_its_rung_after_a_restart(store):  # noqa: F811
    broker, market = FakeBroker(), FakeMarketData()
    loop = _open_lot(store, broker, market, _Ladder(allocation_pct=0.05))
    target = loop.ledger.open_lots[0].target_sell_price
    market.push(target + 0.5, ts=BASE_TS + timedelta(minutes=3))
    loop.run_once()
    _, qty, price, cid = broker.sells[0]
    broker.fill(cid, qty=qty, price=price)
    market.push(target + 0.5, ts=BASE_TS + timedelta(minutes=4))
    loop.run_once()

    restarted = make_loop(store, broker, market, strategy=_Ladder(allocation_pct=0.05))
    (lot,) = restarted.ledger.open_lots
    assert (lot.shares, lot.original_shares, lot.profit_target) == (5.0, 10.0, 0.03)


def test_a_whole_share_venue_floors_a_tranche(store):  # noqa: F811
    broker, market = FakeBroker(), FakeMarketData()
    broker.whole_shares = True
    loop = _open_lot(store, broker, market, _Ladder(allocation_pct=0.05), qty=3.0)
    target = loop.ledger.open_lots[0].target_sell_price
    market.push(target + 0.5, ts=BASE_TS + timedelta(minutes=3))
    loop.run_once()
    assert broker.sells[0][1] == 1.0, "half of three, floored to a whole share"


def test_a_buys_entry_tag_reaches_its_lot_and_survives_a_restart(store):  # noqa: F811
    broker, market = FakeBroker(), FakeMarketData()
    loop = _open_lot(store, broker, market, _Tagged(allocation_pct=0.05))
    assert loop.ledger.open_lots[0].entry_tag == "reversal"
    restarted = make_loop(store, broker, market, strategy=_Tagged(allocation_pct=0.05))
    assert restarted.ledger.open_lots[0].entry_tag == "reversal"


def _trim_loop(ledger_store, broker, market):
    _book(ledger_store, *BOOK)
    config = make_config()
    object.__setattr__(config.execution, "allow_signal_exit", True)
    return make_loop(
        ledger_store, broker, market, config=config, strategy=_TrimsBelow(allocation_pct=0.05)
    )


def test_a_partial_exit_asks_for_half_of_every_lot_in_one_order(store):  # noqa: F811
    broker, market = FakeBroker(), FakeMarketData()
    loop = _trim_loop(store, broker, market)
    market.push(90.0)
    loop.run_once()
    (_, qty, _, cid) = broker.sells[0]
    halves = [1.25 / 2, 2.5 / 2, 0.333333333 / 2]
    assert qty == pytest.approx(sum(halves), abs=1e-8)
    assert loop.state.open_orders[cid].exit_lot_qtys == pytest.approx(halves)

    broker.fill(cid, qty=qty, price=89.9)
    market.push(96.0, ts=BASE_TS + timedelta(seconds=30))
    loop.run_once()
    shares = {lot.order_id: lot.shares for lot in loop.ledger.open_lots}
    assert shares == pytest.approx({"a": 0.625, "b": 1.25, "c": 0.333333333 / 2}, abs=1e-8), (
        "each lot gave up only the half asked of it, oldest first or not"
    )


def test_a_partial_exit_fill_never_takes_more_than_a_lot_was_asked_for(store):  # noqa: F811
    """An increment larger than the first lot's half moves on to the next
    lot rather than selling the first one whole."""
    broker, market = FakeBroker(), FakeMarketData()
    loop = _trim_loop(store, broker, market)
    market.push(90.0)
    loop.run_once()
    (_, _qty, _, cid) = broker.sells[0]
    broker.fill(cid, qty=1.0, price=89.9, status="partially_filled")
    market.push(90.0, ts=BASE_TS + timedelta(seconds=30))
    loop.run_once()
    shares = {lot.order_id: lot.shares for lot in loop.ledger.open_lots}
    assert shares["a"] == pytest.approx(0.625)  # its half, no more
    assert shares["b"] == pytest.approx(2.5 - 0.375)  # the rest of the increment


def test_a_partial_exit_in_flight_keeps_its_quantities_across_a_restart(store):  # noqa: F811
    broker, market = FakeBroker(), FakeMarketData()
    loop = _trim_loop(store, broker, market)
    market.push(90.0)
    loop.run_once()
    cid = broker.sells[0][3]
    restarted = make_loop(store, broker, market, config=loop.config, strategy=loop.strategy)
    assert restarted.state.open_orders[cid].exit_lot_qtys == pytest.approx(
        [1.25 / 2, 2.5 / 2, 0.333333333 / 2]
    )


def test_every_sell_site_asks_the_shared_helper_how_much():
    """The quantity decision is made in one place, like the liquidation one
    (engine/tests/test_signal_exit.py)."""
    import inspect

    from engine.trading import live_trading_loop
    from research.optimization import intraday_validation, optimization_controller

    for name, source in {
        "_simulate_single": inspect.getsource(
            optimization_controller.OptimizationController._simulate_single
        ),
        "simulate_single_intraday": inspect.getsource(intraday_validation.simulate_single_intraday),
        "LiveTradingLoop._harvest": inspect.getsource(live_trading_loop.LiveTradingLoop._harvest),
    }.items():
        assert "decision_cycle.harvest_orders(" in source, name
        assert "as_orders=True" in source, name
        assert "harvest_quantity(" not in source, f"{name} calls the hook directly"


class _SessionBroker(FakeBroker):
    """Fidelity's shape: fractional in the regular session, whole outside it."""

    def whole_shares_in(self, session):
        return session != "regular"


def test_a_per_session_broker_is_asked_about_this_ticks_window(store):  # noqa: F811
    from types import SimpleNamespace

    loop = make_loop(store, broker=_SessionBroker())
    loop.window = SimpleNamespace(session="pre_market")
    assert loop._whole_shares() is True
    loop.window = SimpleNamespace(session="regular")
    assert loop._whole_shares() is False


def test_fidelity_still_sends_whole_shares_in_every_session():
    """Until a captured fractional ticket confirms its quantity type
    (docs/research/buy-sell-composition.md, Phase 1b)."""
    from fidelity_gateway.broker import FidelityBroker

    for session in (None, "pre_market", "regular", "after_hours"):
        assert FidelityBroker.whole_shares_in(object(), session) is True
