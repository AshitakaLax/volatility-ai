"""The live loop on its venue's own windows (live.sessions): when it trades,
how its limit orders are aged and audited, and the engine watching the market
without its broker.

The same fakes as test_live_trading_loop.py, with a wall clock the test moves
and a broker that takes an order's window.
"""

from __future__ import annotations

from datetime import UTC, date, datetime, time
from types import SimpleNamespace

import pytest

from engine.core.exceptions import BrokerUnavailableError
from engine.core.persistence import LedgerStore
from engine.core.trading_calendar import EASTERN
from engine.core.venue_sessions import VenueCalendar
from engine.data.alpaca_market_data import LiveBar
from engine.tests.test_live_trading_loop import FakeBroker, FakeMarketData, make_config
from engine.trading.live_trading_loop import LiveTradingLoop
from engine.trading.risk_manager import CircuitBreakerState
from research.strategies.size_calculators import FixedPortfolioPercentage

DAY = date(2026, 10, 27)
ALL = ("pre_market", "regular", "after_hours")


@pytest.fixture
def store(tmp_path):
    s = LedgerStore(str(tmp_path / "ledger.db"))
    yield s
    s.close()


def et(hour, minute=0, second=0):
    return datetime.combine(DAY, time(hour, minute, second), EASTERN).astimezone(UTC)


class Clock:
    def __init__(self, moment):
        self.now = moment

    def __call__(self):
        return self.now


class WindowBroker(FakeBroker):
    """FakeBroker that takes the window an order is for, and answers a
    snapshot of its position."""

    def __init__(self, unsupported=None):
        super().__init__()
        self.sessions = []
        self.held = 0.0
        self.unsupported = unsupported or {}

    def submit_buy(self, symbol, trade_value, client_order_id=None, limit_price=None, session=None):
        self.sessions.append(session)
        order = super().submit_buy(symbol, trade_value, client_order_id, limit_price)
        order.qty = int(trade_value // limit_price)
        return order

    def submit_sell(self, symbol, qty, target_price, client_order_id=None, session=None):
        self.sessions.append(session)
        return super().submit_sell(symbol, qty, target_price, client_order_id)

    def session_support(self, session):
        return self.unsupported.get(session)

    def snapshot(self):
        return SimpleNamespace(positions={"TQQQ": self.held}, orders={}, cash=None)


class RegularOnly(FixedPortfolioPercentage):
    """A strategy built on regular-session bars (the Ultimate family's flag)."""

    regular_session_only = True

    def __init__(self):
        super().__init__(allocation_pct=0.05)
        self.seen = []

    def record_tick(self, context):
        self.seen.append(context.timestamp)


class Market(FakeMarketData):
    def bar(self, close, at):
        self.push(close, ts=at)


def _loop(store, *, sessions=ALL, start=None, strategy=None, broker=None, listener=None, **live):
    clock = Clock(start or et(7, 5))
    config = make_config(sessions=list(sessions), **live)
    calendar = VenueCalendar("fidelity", sessions)
    market = Market()
    broker = broker or WindowBroker()
    heard = [] if listener is None else listener
    loop = LiveTradingLoop(
        config=config,
        strategy=strategy or FixedPortfolioPercentage(allocation_pct=0.05),
        broker=broker,
        market_data=market,
        store=store,
        sleep=lambda _: None,
        calendar=calendar,
        order_listener=heard.append,
        now=clock,
    )
    return loop, clock, market, broker, heard


def _buy_in_premarket(loop, clock, market):
    """A reference bar, then one 1% under it: the grid's buy."""
    market.bar(100.0, et(7, 5))
    clock.now = et(7, 5, 30)
    loop.run_once()
    market.bar(99.0, et(7, 6))
    clock.now = et(7, 6, 30)
    return loop.run_once()


def test_a_pre_market_dip_is_bought_with_a_limit_for_that_window(store):
    loop, clock, market, broker, heard = _loop(store)
    outcome = _buy_in_premarket(loop, clock, market)
    assert outcome.buys_submitted == 1 and broker.sessions == ["pre_market"]
    assert broker.buy_limits == [99.0], "a grid buy rests at its trigger"
    tracked = next(iter(loop.state.open_orders.values()))
    assert tracked.session == "pre_market"
    assert datetime.fromisoformat(tracked.expires_at) == et(9, 26), "09:28 less the margin"
    assert [e["event"] for e in heard] == ["placed"] and heard[0]["session"] == "pre_market"


def test_an_unfilled_pre_market_buy_is_cancelled_after_its_time_to_live(store):
    loop, clock, market, broker, heard = _loop(store)
    _buy_in_premarket(loop, clock, market)
    cid = next(iter(loop.state.open_orders))
    clock.now = et(7, 10)
    loop.run_once()
    assert broker.cancels == [], "four minutes: still resting"
    clock.now = et(7, 11, 31)
    loop.run_once()
    assert broker.cancels == [cid]
    assert loop.state.open_orders[cid].cancel_reason == "ttl"
    broker.fill(cid, 0.0, 0.0, status="canceled")
    clock.now = et(7, 12, 30)
    loop.run_once()
    assert cid not in loop.state.open_orders, "done when the venue says it is gone"
    assert [e["event"] for e in heard] == ["placed", "cancel_requested", "cancelled"]


def test_a_resting_buy_holds_back_its_cash(store):
    loop, clock, market, _broker, _ = _loop(store)
    _buy_in_premarket(loop, clock, market)
    assert loop.reserved() == pytest.approx(5_000.0)
    loop.state.cash = 5_000.0  # all of it is held by the resting buy
    market.bar(98.0, et(7, 7))
    clock.now = et(7, 7, 30)
    assert loop.run_once().buys_submitted == 0
    assert loop.decision["blocked"] == "no buying power left"


def test_no_order_in_the_two_minutes_before_the_open_or_a_windows_last_minutes(store):
    loop, clock, market, broker, _ = _loop(store)
    market.bar(100.0, et(9, 20))
    clock.now = et(9, 20, 30)
    loop.run_once()
    market.bar(98.0, et(9, 26))
    clock.now = et(9, 26, 10)
    outcome = loop.run_once()
    assert outcome.reason == "not_trading" and broker.buys == []
    assert "closes at 09:28" in loop.decision["blocked"]
    market.bar(97.0, et(9, 28))
    clock.now = et(9, 29)
    loop.run_once()
    assert broker.buys == [] and loop.decision["blocked"].startswith("between trading windows")


def test_every_order_of_a_window_is_cancelled_before_it_ends_and_the_window_audited(store):
    loop, clock, market, broker, _heard = _loop(store)
    _buy_in_premarket(loop, clock, market)
    cid = next(iter(loop.state.open_orders))
    broker.fill(cid, 10.0, 99.0, status="partially_filled")
    clock.now = et(7, 7)
    loop.run_once()
    assert loop.reserved() == pytest.approx(5_000.0 - 990.0), "what filled is cash now"
    # Placed (as far as the TTL knows) just now, so the cancel is the window's.
    loop.state.open_orders[cid].submitted_at = et(9, 24).isoformat()
    clock.now = et(9, 26)
    loop.run_once()
    assert broker.cancels == [cid] and loop.state.open_orders[cid].cancel_reason == "session_end"
    broker.fill(cid, 10.0, 99.0, status="canceled")
    broker.held = 10.0
    clock.now = et(9, 31, 1)
    market.bar(99.0, et(9, 31))
    loop.run_once()
    summary = loop.last_window
    assert summary["session"] == "pre_market" and "problem" not in summary
    assert summary["orders"] == 1 and summary["filled_qty"] == 10.0
    assert summary["ended"] == {"cancelled": 1}
    assert summary["position"] == {"venue": 10.0, "ledger": 10.0}
    assert loop.circuit_breaker.state is not CircuitBreakerState.HALTED_NEW_BUYS


def test_an_order_still_open_after_its_window_halts_buys_and_names_it(store):
    loop, clock, market, broker, _ = _loop(store)
    _buy_in_premarket(loop, clock, market)
    cid = next(iter(loop.state.open_orders))
    broker.cancel_order = lambda _cid: True  # the venue takes the cancel and never acts
    loop.state.open_orders[cid].submitted_at = et(9, 24).isoformat()
    clock.now = et(9, 26)
    loop.run_once()
    clock.now = et(9, 31, 1)
    loop.run_once()
    assert cid in loop.last_window["problem"]
    assert loop.circuit_breaker.state is CircuitBreakerState.HALTED_NEW_BUYS


def test_a_position_the_ledger_does_not_have_halts_buys(store):
    loop, clock, market, broker, _ = _loop(store)
    broker.held = 3.0  # shares bought by hand in the pre-market
    clock.now = et(9, 31, 1)
    market.bar(99.0, et(9, 31))
    loop.run_once()
    assert "holds 3 TQQQ and the ledger 0" in loop.last_window["problem"]
    assert loop.circuit_breaker.state is CircuitBreakerState.HALTED_NEW_BUYS


def test_a_regular_session_strategy_sees_and_trades_only_the_regular_session(store):
    strategy = RegularOnly()
    loop, clock, market, _broker, _ = _loop(
        store, sessions=("pre_market", "regular"), strategy=strategy
    )
    market.bar(100.0, et(8, 30))
    clock.now = et(8, 30, 30)
    loop.run_once()
    assert strategy.seen == [] and "regular session only" in loop.decision["blocked"]
    market.bar(100.0, et(9, 31))
    clock.now = et(9, 31, 30)
    loop.run_once()
    assert strategy.seen == [et(9, 31)]


def test_the_same_bar_twice_is_not_a_new_bar(store):
    loop, clock, market, _broker, _ = _loop(store)
    market.bar(100.0, et(7, 5))
    clock.now = et(7, 5, 30)
    assert loop.run_once().reason == "ok"
    clock.now = et(7, 6, 30)
    assert loop.run_once().reason == "no_new_bar", "no pre-market trade this minute"


def test_a_stale_bar_is_recorded_and_not_traded_on(store):
    loop, clock, market, _broker, _ = _loop(store)
    market.bar(100.0, et(7, 0))
    clock.now = et(7, 0, 30)
    loop.run_once()
    market.bar(98.0, et(7, 1))
    clock.now = et(7, 9)
    outcome = loop.run_once()
    assert outcome.buys_submitted == 0 and "old" in loop.decision["blocked"]


def test_a_window_the_broker_cannot_trade_yet_says_so(store):
    broker = WindowBroker(unsupported={"pre_market": "Fidelity's pre-market ticket is not known"})
    loop, clock, market, broker, _ = _loop(store, broker=broker)
    _buy_in_premarket(loop, clock, market)
    assert broker.buys == [] and "ticket is not known" in loop.decision["blocked"]


def test_the_broker_down_mid_window_still_feeds_the_strategy(store):
    strategy = RegularOnly()
    loop, clock, market, broker, _ = _loop(store, strategy=strategy)

    def down(_cid):
        raise BrokerUnavailableError("Fidelity signed you out")

    market.bar(100.0, et(10, 0))
    clock.now = et(10, 0, 30)
    broker.get_order_by_client_id = down
    loop.state.open_orders["x"] = _tracked("x")  # an order to ask about
    with pytest.raises(BrokerUnavailableError):
        loop.run_once()
    assert strategy.seen == [et(10, 0)], "the bar reached the strategy first"


def _tracked(cid):
    from engine.execution.fill_accounting import FillTracker
    from engine.trading.live_trading_loop import _TrackedOrder

    return _TrackedOrder(client_order_id=cid, kind="buy", tracker=FillTracker(cid))


def test_an_engine_waiting_for_its_broker_watches_without_it(store):
    strategy = RegularOnly()
    loop, clock, market, _, _ = _loop(store, strategy=strategy)
    loop.attach_broker(None)
    market.bar(100.0, et(9, 45))
    clock.now = et(9, 45, 30)
    outcome = loop.watch_once()
    assert outcome.reason == "watching" and strategy.seen == [et(9, 45)]


def test_a_shutdown_asks_the_venue_about_orders_still_settling(store, monkeypatch):
    loop, clock, market, broker, _ = _loop(store)
    _buy_in_premarket(loop, clock, market)
    cid = next(iter(loop.state.open_orders))
    assert loop.settle_in_flight() is False
    broker.fill(cid, 0.0, 0.0, status="canceled")
    import engine.trading.live_trading_loop as module

    later = module.time.monotonic() + 10
    monkeypatch.setattr(module.time, "monotonic", lambda: later)
    assert loop.settle_in_flight() is True


def test_after_hours_settles_on_the_eastern_date(store):
    """19:30 ET in winter is already tomorrow in UTC."""
    winter = date(2026, 12, 15)
    clock = Clock(datetime.combine(winter, time(19, 30), EASTERN).astimezone(UTC))
    assert clock.now.date() != winter
    config = make_config(sessions=list(ALL))
    from dataclasses import replace

    config = replace(config, execution=replace(config.execution, settlement_days=1))
    market = Market()
    market.push(100.0, ts=clock.now)
    loop = LiveTradingLoop(
        config=config,
        strategy=FixedPortfolioPercentage(allocation_pct=0.05),
        broker=WindowBroker(),
        market_data=market,
        store=store,
        sleep=lambda _: None,
        calendar=VenueCalendar("fidelity", ALL),
        now=clock,
    )
    loop.run_once()
    assert loop.state.session == winter.toordinal()


def test_bars_report_where_they_came_from(store):
    loop, clock, market, _, _ = _loop(store)
    from engine.trading.market_feed import FeedBar

    market._bars.append(FeedBar(et(7, 5), 100.0, 100.0, 100.0, 100.0, 0.0, source="fidelity"))
    clock.now = et(7, 5, 30)
    loop.run_once()
    assert loop.last_bar["source"] == "fidelity"
    market._bars.append(LiveBar(timestamp=et(7, 6), open=1, high=1, low=1, close=100.0))
    clock.now = et(7, 6, 30)
    loop.run_once()
    assert "source" not in loop.last_bar


def test_an_audit_the_venue_could_not_answer_is_tried_again(store):
    loop, clock, market, broker, _ = _loop(store)
    calls = {"n": 0}

    def snapshot():
        calls["n"] += 1
        if calls["n"] == 1:
            raise BrokerUnavailableError("Fidelity signed you out")
        return SimpleNamespace(positions={"TQQQ": 0.0}, orders={}, cash=None)

    broker.snapshot = snapshot
    market.bar(99.0, et(9, 31))
    clock.now = et(9, 31, 1)
    with pytest.raises(BrokerUnavailableError):
        loop.run_once()
    assert loop.last_window is None
    market.bar(99.0, et(9, 32))
    clock.now = et(9, 32, 1)
    loop.run_once()
    assert loop.last_window["session"] == "pre_market" and "problem" not in loop.last_window
