"""Tests for the live trading loop.

Everything runs against fakes with no network, but against the REAL
LedgerStore, AssetLotLedger, DuplicateOrderGuard, FillTracker,
CircuitBreaker and no-loss guard -- the loop's whole job is composing
those correctly, so substituting them would test nothing.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from src.alpaca_market_data import LiveBar
from src.config import BacktestConfig
from src.exceptions import ConfigurationError, DataValidationError
from src.live_trading_loop import LiveTradingLoop
from src.persistence import LedgerStore
from src.size_calculators import FixedPortfolioPercentage

BASE_TS = datetime(2026, 3, 2, 15, 0, tzinfo=UTC)


class FakeBrokerOrder:
    def __init__(self, order_id, client_order_id, status="new", filled_qty=0.0, avg=0.0):
        self.id = order_id
        self.client_order_id = client_order_id
        self.status = status
        self.filled_qty = filled_qty
        self.filled_avg_price = avg


class FakeBroker:
    """Records submissions and lets a test drive fills explicitly.

    Orders do NOT fill on their own: the asynchrony is the point, and a
    fake that filled instantly would hide every bug this design exists
    to prevent.
    """

    def __init__(self):
        self.buys = []
        self.buy_limits = []
        self.sells = []
        self.orders = {}
        self._seq = 0

    def submit_buy(self, symbol, trade_value, client_order_id=None, limit_price=None):
        self._seq += 1
        self.buys.append((symbol, trade_value, client_order_id))
        self.buy_limits.append(limit_price)
        order = FakeBrokerOrder(f"b{self._seq}", client_order_id)
        self.orders[client_order_id] = order
        return order

    def submit_sell(self, symbol, qty, target_price, client_order_id=None):
        self._seq += 1
        self.sells.append((symbol, qty, target_price, client_order_id))
        order = FakeBrokerOrder(f"s{self._seq}", client_order_id)
        self.orders[client_order_id] = order
        return order

    def get_order_by_client_id(self, client_order_id):
        return self.orders.get(client_order_id)

    def fill(self, client_order_id, qty, price, status="filled"):
        """Drive a cumulative fill update, the way Alpaca reports them."""
        order = self.orders[client_order_id]
        order.filled_qty = qty
        order.filled_avg_price = price
        order.status = status


class FakeMarketData:
    def __init__(self, bars=None, is_open=True):
        self._bars = list(bars or [])
        self._open = is_open
        self.raise_no_data = False

    def is_open(self):
        return self._open

    def set_open(self, value):
        self._open = value

    def push(self, close, ts=None, **kw):
        self._bars.append(
            LiveBar(
                timestamp=ts or BASE_TS,
                open=kw.get("open", close),
                high=kw.get("high", close),
                low=kw.get("low", close),
                close=close,
                volume=kw.get("volume", 0.0),
            )
        )

    def latest_bar(self, symbol):
        """The most recently pushed bar -- "latest" means latest, so a
        tick that runs twice without a new push legitimately sees the
        same bar again (which is what the poll-faster-than-bars case
        looks like in production)."""
        if self.raise_no_data or not self._bars:
            raise DataValidationError("no bar")
        return self._bars[-1]


def make_config(**live_overrides):
    live = {
        "enabled": True,
        "paper_trading": True,
        "step": 0.01,
        "profit_target": 0.005,
        "poll_interval_seconds": 1.0,
    }
    live.update(live_overrides)
    return BacktestConfig.from_dict(
        {
            "strategy": {"strategy_id": "fixed", "strategy_params": {"allocation_pct": 0.05}},
            "grid": {"steps": [0.01], "profit_targets": [0.005]},
            "backtest": {"symbol": "TQQQ", "initial_cash": 100_000.0},
            "live": live,
        }
    )


@pytest.fixture
def store(tmp_path):
    s = LedgerStore(str(tmp_path / "ledger.db"))
    yield s
    s.close()


def make_loop(store, broker=None, market=None, config=None, strategy=None, **kw):
    return LiveTradingLoop(
        config=config or make_config(),
        strategy=strategy or FixedPortfolioPercentage(allocation_pct=0.05),
        broker=broker or FakeBroker(),
        market_data=market or FakeMarketData(),
        store=store,
        sleep=lambda _: None,
        **kw,
    )


# --- construction / config ---


def test_requires_a_single_live_step_and_profit_target(store):
    """The parameters real capital trades must be explicit."""
    config = make_config()
    object.__setattr__(config.live, "step", None)
    with pytest.raises(ConfigurationError, match=r"live\.step"):
        make_loop(store, config=config)


def test_refuses_to_run_when_live_is_disabled(store):
    with pytest.raises(ConfigurationError, match=r"live\.enabled"):
        make_loop(store, config=make_config(enabled=False))


def test_starts_from_configured_cash_on_a_fresh_deployment(store):
    assert make_loop(store).state.cash == 100_000.0


# --- ticks that deliberately do nothing ---


def test_closed_market_does_not_trade(store):
    broker = FakeBroker()
    market = FakeMarketData(is_open=False)
    market.push(100.0)
    outcome = make_loop(store, broker, market).run_once()
    assert outcome.acted is False
    assert outcome.reason == "market_closed"
    assert broker.buys == [] and broker.sells == []


def test_a_missing_bar_skips_the_tick_rather_than_inventing_a_price(store):
    """Routine on IEX in a quiet interval -- must never be filled in."""
    broker = FakeBroker()
    market = FakeMarketData()
    market.raise_no_data = True
    outcome = make_loop(store, broker, market).run_once()
    assert outcome.acted is False
    assert outcome.reason == "no_data"
    assert broker.buys == []


def test_a_rejected_tick_never_reaches_the_strategy(store):
    broker = FakeBroker()
    market = FakeMarketData()
    market.push(100.0)
    loop = make_loop(store, broker, market)
    loop.run_once()  # establishes last_good_price

    market.push(-5.0)  # an impossible print
    outcome = loop.run_once()
    assert outcome.acted is False
    assert outcome.reason == "tick_rejected"
    assert broker.buys == []


# --- the buy path ---


def test_a_grid_trigger_submits_exactly_one_buy(store):
    broker = FakeBroker()
    market = FakeMarketData()
    market.push(100.0)
    loop = make_loop(store, broker, market)
    loop.run_once()  # sets last_buy_price = 100

    market.push(98.0, ts=BASE_TS + timedelta(minutes=1))  # a 2% drop trips a 1% step
    outcome = loop.run_once()

    assert outcome.buys_submitted == 1
    assert len(broker.buys) == 1
    symbol, trade_value, cid = broker.buys[0]
    assert symbol == "TQQQ"
    assert trade_value > 0
    assert cid, "a client_order_id must be supplied for broker-side dedup"


def test_bar_volume_reaches_the_strategy_as_context_volume(store):
    """End-to-end regression for the LiveBar volume fix: a real volume
    figure on the source bar must reach the strategy's context, not the
    always-0.0 default that shipped for the whole life of this loop
    until src/alpaca_market_data.py's LiveBar gained a volume field."""
    seen = []

    class RecordingStrategy(FixedPortfolioPercentage):
        def record_tick(self, context):
            seen.append(context.volume)
            super().record_tick(context)

    market = FakeMarketData()
    market.push(100.0, volume=54321.0)
    loop = make_loop(store, market=market, strategy=RecordingStrategy(allocation_pct=0.05))
    loop.run_once()

    assert seen == [54321.0]


def test_submitting_a_buy_does_not_move_cash_until_it_fills(store):
    """Cash reflects confirmed fills only -- an in-flight order is
    deliberately invisible to sizing."""
    broker = FakeBroker()
    market = FakeMarketData()
    market.push(100.0)
    loop = make_loop(store, broker, market)
    loop.run_once()
    market.push(98.0, ts=BASE_TS + timedelta(minutes=1))
    loop.run_once()

    assert broker.buys, "precondition: a buy was submitted"
    assert loop.state.cash == 100_000.0, "cash must not move on submission"
    assert loop.ledger.open_lots == []


def test_a_confirmed_buy_fill_opens_a_lot_and_debits_cash(store):
    broker = FakeBroker()
    market = FakeMarketData()
    market.push(100.0)
    loop = make_loop(store, broker, market)
    loop.run_once()
    market.push(98.0, ts=BASE_TS + timedelta(minutes=1))
    loop.run_once()

    _, _trade_value, cid = broker.buys[0]
    broker.fill(cid, qty=10.0, price=98.0)

    market.push(98.0, ts=BASE_TS + timedelta(minutes=2))
    outcome = loop.run_once()

    assert outcome.fills_applied == 1
    assert len(loop.ledger.open_lots) == 1
    lot = loop.ledger.open_lots[0]
    assert lot.buy_price == 98.0, "the real fill price is the cost basis, unmodified"
    assert lot.shares == 10.0
    assert loop.state.cash == pytest.approx(100_000.0 - 980.0)


def test_the_same_bar_cannot_be_bought_twice(store):
    """A poll interval shorter than the bar interval re-reads the same
    bar. The decision id is derived from the bar timestamp, so the
    duplicate-order guard refuses the second submission -- this is what
    stops a fast loop from buying one signal repeatedly."""
    broker = FakeBroker()
    market = FakeMarketData()
    market.push(100.0)
    loop = make_loop(store, broker, market)
    loop.run_once()

    repeated = LiveBar(
        timestamp=BASE_TS + timedelta(minutes=1),
        open=98.0,
        high=98.0,
        low=98.0,
        close=98.0,
    )
    market._bars = [repeated]
    loop.run_once()
    loop.run_once()
    loop.run_once()

    assert len(broker.buys) == 1, "one bar must produce at most one buy"


# --- the harvest path ---


def _loop_with_an_open_lot(store, broker, market, buy_price=98.0, qty=10.0):
    market.push(100.0)
    loop = make_loop(store, broker, market)
    loop.run_once()
    market.push(buy_price, ts=BASE_TS + timedelta(minutes=1))
    loop.run_once()
    _, _, cid = broker.buys[0]
    broker.fill(cid, qty=qty, price=buy_price)
    market.push(buy_price, ts=BASE_TS + timedelta(minutes=2))
    loop.run_once()
    return loop


def test_a_lot_reaching_its_target_is_offered_as_a_limit_sell(store):
    broker = FakeBroker()
    market = FakeMarketData()
    loop = _loop_with_an_open_lot(store, broker, market)
    lot = loop.ledger.open_lots[0]

    market.push(lot.target_sell_price + 1.0, ts=BASE_TS + timedelta(minutes=3))
    outcome = loop.run_once()

    assert outcome.sells_submitted == 1
    symbol, qty, target, _cid = broker.sells[0]
    assert symbol == "TQQQ"
    assert qty == lot.shares
    assert target == lot.target_sell_price, "the sell is offered at the lot's own target"


def test_a_lot_with_a_sell_in_flight_is_not_offered_again(store):
    """Two sell orders against one position could sell shares that no
    longer exist."""
    broker = FakeBroker()
    market = FakeMarketData()
    loop = _loop_with_an_open_lot(store, broker, market)
    lot = loop.ledger.open_lots[0]

    for i in range(3, 6):
        market.push(lot.target_sell_price + 1.0, ts=BASE_TS + timedelta(minutes=i))
        loop.run_once()

    assert len(broker.sells) == 1


def test_a_confirmed_sell_fill_closes_the_lot_and_credits_cash(store):
    broker = FakeBroker()
    market = FakeMarketData()
    loop = _loop_with_an_open_lot(store, broker, market)
    lot = loop.ledger.open_lots[0]
    cash_before = loop.state.cash

    market.push(lot.target_sell_price + 1.0, ts=BASE_TS + timedelta(minutes=3))
    loop.run_once()
    _, qty, target, sell_cid = broker.sells[0]
    broker.fill(sell_cid, qty=qty, price=target)

    market.push(lot.target_sell_price + 1.0, ts=BASE_TS + timedelta(minutes=4))
    loop.run_once()

    assert loop.ledger.open_lots == []
    assert len(loop.ledger.closed_lots) == 1
    assert loop.state.cash == pytest.approx(cash_before + qty * target)


def test_a_sell_that_never_fills_leaves_the_lot_open(store):
    """A limit order that does not fill is the normal case, not an
    error -- the position must survive intact."""
    broker = FakeBroker()
    market = FakeMarketData()
    loop = _loop_with_an_open_lot(store, broker, market)
    lot = loop.ledger.open_lots[0]
    cash_before = loop.state.cash

    market.push(lot.target_sell_price + 1.0, ts=BASE_TS + timedelta(minutes=3))
    loop.run_once()
    _, _, _, sell_cid = broker.sells[0]
    broker.fill(sell_cid, qty=0.0, price=0.0, status="expired")

    market.push(lot.target_sell_price + 1.0, ts=BASE_TS + timedelta(minutes=4))
    loop.run_once()

    assert len(loop.ledger.open_lots) == 1, "an unfilled sell must not close the lot"
    assert loop.state.cash == pytest.approx(cash_before), "no proceeds without a fill"


def test_an_expired_sell_is_reoffered_on_a_later_tick(store):
    """DAY orders expire at the close; the lot is simply re-offered."""
    broker = FakeBroker()
    market = FakeMarketData()
    loop = _loop_with_an_open_lot(store, broker, market)
    lot = loop.ledger.open_lots[0]

    market.push(lot.target_sell_price + 1.0, ts=BASE_TS + timedelta(minutes=3))
    loop.run_once()
    _, _, _, sell_cid = broker.sells[0]
    broker.fill(sell_cid, qty=0.0, price=0.0, status="expired")

    market.push(lot.target_sell_price + 1.0, ts=BASE_TS + timedelta(minutes=4))
    loop.run_once()  # untracks the expired order
    market.push(lot.target_sell_price + 1.0, ts=BASE_TS + timedelta(minutes=5))
    loop.run_once()

    assert len(broker.sells) == 2, "the lot must be offered again after expiry"


# --- the no-loss invariant ---


def test_a_sell_below_cost_basis_is_never_booked(store):
    """The primary invariant. If a fill somehow lands below the lot's
    basis, refusing to book it keeps the position visible and
    reconcilable rather than quietly realizing a loss."""
    broker = FakeBroker()
    market = FakeMarketData()
    loop = _loop_with_an_open_lot(store, broker, market, buy_price=98.0, qty=10.0)
    lot = loop.ledger.open_lots[0]
    cash_before = loop.state.cash

    market.push(lot.target_sell_price + 1.0, ts=BASE_TS + timedelta(minutes=3))
    loop.run_once()
    _, qty, _, sell_cid = broker.sells[0]
    broker.fill(sell_cid, qty=qty, price=50.0)  # far below basis

    market.push(lot.target_sell_price + 1.0, ts=BASE_TS + timedelta(minutes=4))
    loop.run_once()

    assert loop.state.cash == cash_before, "a loss-making sell must not credit cash"
    assert len(loop.ledger.open_lots) == 1, "the lot must stay open"


def test_a_halt_never_liquidates(store):
    """A halt stops trading; it does not unwind the book.

    Renamed from test_nothing_in_this_module_can_force_a_liquidation.
    That name outlived its truth: signal exits mean a STRATEGY can now
    force one (see the signal-exit tests below). What this actually
    asserted, and still asserts, is narrower and unaffected -- the
    circuit breaker is not a liquidation trigger.
    """
    broker = FakeBroker()
    market = FakeMarketData()
    loop = _loop_with_an_open_lot(store, broker, market)
    loop.circuit_breaker.halt_for_reconciliation("test halt")

    market.push(98.0, ts=BASE_TS + timedelta(minutes=3))
    loop.run_once()

    assert broker.sells == [], "a halt must never liquidate"
    assert len(loop.ledger.open_lots) == 1


# --- the circuit breaker ---


def test_a_halt_blocks_new_buys_but_still_records_ticks(store):
    broker = FakeBroker()
    market = FakeMarketData()
    market.push(100.0)
    loop = make_loop(store, broker, market)
    loop.run_once()
    loop.circuit_breaker.halt_for_reconciliation("test halt")

    market.push(98.0, ts=BASE_TS + timedelta(minutes=1))
    outcome = loop.run_once()

    assert outcome.acted is True, "the tick still runs"
    assert outcome.buys_submitted == 0
    assert broker.buys == []


def test_a_halted_loop_still_harvests_so_lots_stay_exitable(store):
    broker = FakeBroker()
    market = FakeMarketData()
    loop = _loop_with_an_open_lot(store, broker, market)
    lot = loop.ledger.open_lots[0]
    loop.circuit_breaker.halt_for_reconciliation("test halt")

    market.push(lot.target_sell_price + 1.0, ts=BASE_TS + timedelta(minutes=3))
    outcome = loop.run_once()

    assert outcome.sells_submitted == 1, "a halt blocks entry, not exit"


# --- durability ---


def test_state_survives_a_restart(store, tmp_path):
    """The whole point of the persistent volume: a container restart
    must not lose cash, lots, or the grid reference price."""
    broker = FakeBroker()
    market = FakeMarketData()
    loop = _loop_with_an_open_lot(store, broker, market)
    cash = loop.state.cash
    lot_id = loop.ledger.open_lots[0].order_id
    store.close()

    reopened = LedgerStore(str(tmp_path / "ledger.db"))
    try:
        revived = make_loop(reopened, FakeBroker(), FakeMarketData())
        assert revived.state.cash == pytest.approx(cash)
        assert [lot.order_id for lot in revived.ledger.open_lots] == [lot_id]
        assert revived.state.last_buy_price is not None
    finally:
        reopened.close()


# --- the runner ---


def test_run_forever_stops_when_asked(store):
    market = FakeMarketData()
    market.push(100.0)
    loop = make_loop(store, market=market)
    loop.request_stop()
    assert loop.run_forever(max_ticks=10) == 0


def test_run_forever_honors_max_ticks(store):
    market = FakeMarketData()
    market.push(100.0)
    assert make_loop(store, market=market).run_forever(max_ticks=3) == 3


def test_in_flight_settled_reports_outstanding_orders(store):
    broker = FakeBroker()
    market = FakeMarketData()
    market.push(100.0)
    loop = make_loop(store, broker, market)
    loop.run_once()
    assert loop.in_flight_settled() is True

    market.push(98.0, ts=BASE_TS + timedelta(minutes=1))
    loop.run_once()
    assert loop.in_flight_settled() is False, "a submitted order is still in flight"


# --- signal exits, end to end through the live loop ---
#
# The backtest decides and fills within one bar; live splits that across
# ticks, so the REASON a sell was submitted has to survive the gap on
# _TrackedOrder. These exercise the whole path -- _harvest submits, the
# broker fills later, _apply_sell_fill books it -- rather than asserting
# that the source contains the right function names, which is all
# tests/unit/test_signal_exit.py can do for this module.
#
# This is the path that spends real money, so the negative cases come
# first.


class _LiquidatesBelow(FixedPortfolioPercentage):
    """Asks to close every open lot once price drops under `trip`.

    A trip price rather than "always", so the setup ticks that OPEN the
    lot do not also condemn it. The first version of this had no trip
    and fired during setup, which made three tests below pass while
    measuring a bar other than the one they named.
    """

    def __init__(self, *args, trip=95.0, **kwargs):
        super().__init__(*args, **kwargs)
        self.trip = trip

    def lots_to_liquidate(self, open_lots, context):
        return list(open_lots) if context.price < self.trip else []


def _liquidating_loop(store, broker, market, *, allow, buy_price=98.0, qty=10.0):
    """An open lot, held by a strategy that wants out below 95, under a
    config that either permits signal exits or does not.

    Returns with the lot open, nothing condemned, and no sell in flight
    -- every setup tick runs at buy_price (98), above the trip.
    """
    config = make_config()
    object.__setattr__(config.execution, "allow_signal_exit", allow)
    market.push(100.0)
    loop = make_loop(
        store, broker, market, config=config, strategy=_LiquidatesBelow(allocation_pct=0.05)
    )
    loop.run_once()
    market.push(buy_price, ts=BASE_TS + timedelta(minutes=1))
    loop.run_once()
    _, _, cid = broker.buys[0]
    broker.fill(cid, qty=qty, price=buy_price)
    market.push(buy_price, ts=BASE_TS + timedelta(minutes=2))
    loop.run_once()
    assert broker.sells == [], "setup must not have condemned anything yet"
    return loop


def test_a_strategy_wanting_out_sells_nothing_without_the_config_flag(store):
    """The gate, in the place where it costs money to be wrong."""
    broker = FakeBroker()
    market = FakeMarketData()
    loop = _liquidating_loop(store, broker, market, allow=False)

    market.push(90.0, ts=BASE_TS + timedelta(minutes=3))  # well below basis
    outcome = loop.run_once()

    assert broker.sells == [], "no config flag, no signal exit"
    assert outcome.sells_submitted == 0
    assert len(loop.ledger.open_lots) == 1


def test_a_signal_exit_is_submitted_at_the_market_not_the_lot_target(store):
    """An exit resting above the market would not fill, which is the one
    outcome a 'get me out' instruction must not have."""
    broker = FakeBroker()
    market = FakeMarketData()
    loop = _liquidating_loop(store, broker, market, allow=True)
    lot = loop.ledger.open_lots[0]

    market.push(90.0, ts=BASE_TS + timedelta(minutes=3))
    outcome = loop.run_once()

    assert outcome.sells_submitted == 1
    symbol, qty, price, _cid = broker.sells[0]
    assert symbol == "TQQQ"
    assert qty == lot.shares
    assert price == 90.0, "priced at the current bar, not the lot's target"
    assert price < lot.target_sell_price


def test_a_signal_exit_books_the_loss_that_a_harvest_would_refuse(store):
    """The end-to-end claim. The identical fill is refused as a harvest
    (test_a_sell_below_cost_basis_is_never_booked, 50.0 against a 98.0
    basis) and accepted as a signal exit -- so this pins the REASON as
    the thing that decides, not the price."""
    broker = FakeBroker()
    market = FakeMarketData()
    loop = _liquidating_loop(store, broker, market, allow=True)
    cash_before = loop.state.cash

    market.push(90.0, ts=BASE_TS + timedelta(minutes=3))
    loop.run_once()
    _, qty, _, sell_cid = broker.sells[0]
    broker.fill(sell_cid, qty=qty, price=90.0)  # 8.00/share below basis

    market.push(90.0, ts=BASE_TS + timedelta(minutes=4))
    loop.run_once()

    assert loop.ledger.open_lots == [], "the lot must actually close"
    assert loop.state.cash == pytest.approx(cash_before + qty * 90.0), (
        "proceeds credited at the real fill price, loss and all"
    )


def test_a_lot_with_a_sell_in_flight_is_not_condemned_twice(store):
    """A resting order plus a signal exit would be two sells against one
    position."""
    broker = FakeBroker()
    market = FakeMarketData()
    loop = _liquidating_loop(store, broker, market, allow=True)

    market.push(90.0, ts=BASE_TS + timedelta(minutes=3))
    loop.run_once()
    assert len(broker.sells) == 1

    market.push(89.0, ts=BASE_TS + timedelta(minutes=4))
    loop.run_once()
    assert len(broker.sells) == 1, "the in-flight lot must not be re-offered"


# --- T+N settlement, and backtest/live parity on it ---
#
# The live loop gated buys on state.cash while _simulate_single had
# switched to settled buying_power. With execution.settlement_days set,
# the backtest honoured T+1 and live spent unsettled proceeds -- trading
# more aggressively than anything simulated, in the one account type
# where that is a rule violation rather than a preference.


def _settling_loop(store, broker, market, *, days=1, buy_price=98.0, qty=10.0):
    config = make_config()
    object.__setattr__(config.execution, "settlement_days", days)
    market.push(100.0)
    loop = make_loop(store, broker, market, config=config)
    loop.run_once()
    market.push(buy_price, ts=BASE_TS + timedelta(minutes=1))
    loop.run_once()
    _, _, cid = broker.buys[0]
    broker.fill(cid, qty=qty, price=buy_price)
    market.push(buy_price, ts=BASE_TS + timedelta(minutes=2))
    loop.run_once()
    return loop


def test_sale_proceeds_are_not_spendable_on_the_day_they_land(store):
    broker = FakeBroker()
    market = FakeMarketData()
    loop = _settling_loop(store, broker, market)
    lot = loop.ledger.open_lots[0]
    before = loop.state.buying_power

    market.push(lot.target_sell_price + 1.0, ts=BASE_TS + timedelta(minutes=3))
    loop.run_once()
    _, qty, _, sell_cid = broker.sells[0]
    broker.fill(sell_cid, qty=qty, price=lot.target_sell_price)
    market.push(lot.target_sell_price + 1.0, ts=BASE_TS + timedelta(minutes=4))
    loop.run_once()

    assert loop.state.cash > before, "proceeds are equity immediately"
    assert loop.state.buying_power == pytest.approx(before), "but not spendable until they settle"


def test_proceeds_settle_on_the_next_session(store):
    broker = FakeBroker()
    market = FakeMarketData()
    loop = _settling_loop(store, broker, market)
    lot = loop.ledger.open_lots[0]

    market.push(lot.target_sell_price + 1.0, ts=BASE_TS + timedelta(minutes=3))
    loop.run_once()
    _, qty, _, sell_cid = broker.sells[0]
    broker.fill(sell_cid, qty=qty, price=lot.target_sell_price)
    market.push(lot.target_sell_price + 1.0, ts=BASE_TS + timedelta(minutes=4))
    loop.run_once()
    held = loop.state.unsettled
    assert held > 0

    market.push(lot.target_sell_price, ts=BASE_TS + timedelta(days=1))
    loop.run_once()
    assert loop.state.unsettled == 0.0
    assert loop.state.buying_power == pytest.approx(loop.state.cash)


def test_settlement_defaults_off_and_buying_power_is_just_cash(store):
    broker = FakeBroker()
    market = FakeMarketData()
    loop = _settling_loop(store, broker, market, days=0)
    assert loop.settlement_days == 0
    assert loop.state.buying_power == pytest.approx(loop.state.cash)


def test_unsettled_funds_survive_a_restart(store, tmp_path):
    """A restart that forgot them would treat unsettled money as
    spendable -- which is exactly the over-trading this models away."""
    broker = FakeBroker()
    market = FakeMarketData()
    loop = _settling_loop(store, broker, market)
    lot = loop.ledger.open_lots[0]

    market.push(lot.target_sell_price + 1.0, ts=BASE_TS + timedelta(minutes=3))
    loop.run_once()
    _, qty, _, sell_cid = broker.sells[0]
    broker.fill(sell_cid, qty=qty, price=lot.target_sell_price)
    market.push(lot.target_sell_price + 1.0, ts=BASE_TS + timedelta(minutes=4))
    loop.run_once()
    unsettled = loop.state.unsettled
    assert unsettled > 0

    config = make_config()
    object.__setattr__(config.execution, "settlement_days", 1)
    revived = make_loop(store, FakeBroker(), FakeMarketData(), config=config)
    assert revived.state.unsettled == pytest.approx(unsettled)
    assert revived.state.pending, "the maturity schedule survives too"


def test_unreadable_settlement_state_fails_safe_rather_than_to_zero(store):
    """Corrupt state must UNDER-trade, never over-trade: treat the whole
    balance as unsettled until the next session."""
    config = make_config()
    object.__setattr__(config.execution, "settlement_days", 1)
    store.set_meta("live.unsettled", "{not json")
    loop = make_loop(store, FakeBroker(), FakeMarketData(), config=config)
    assert loop.state.unsettled == pytest.approx(loop.state.cash)
    assert loop.state.buying_power == 0.0


def test_the_live_buy_gate_reads_the_same_quantity_the_backtest_does(store):
    """Source-level parity check. Both must gate on settled buying power;
    the divergence this catches was invisible because the live docstring
    still CLAIMED parity after _simulate_single had moved on."""
    import inspect

    import optimization_controller

    backtest = inspect.getsource(optimization_controller.OptimizationController._simulate_single)
    live = inspect.getsource(LiveTradingLoop._maybe_buy)
    assert "state.buying_power >= trade_value" in backtest
    assert "self.state.buying_power < trade_value" in live
    assert "self.state.cash < trade_value" not in live


def test_the_buy_carries_the_target_price_the_grid_triggered_at(store):
    """The loop must hand the broker a limit price it can use outside
    regular hours, without knowing which shape the venue will take.

    A regular-hours notional market buy ignores it; an extended-hours
    buy cannot be placed without it. Passing it unconditionally keeps
    that venue detail out of the loop.
    """
    broker = FakeBroker()
    market = FakeMarketData()
    market.push(100.0)
    loop = make_loop(store, broker, market)
    loop.run_once()

    market.push(98.0, ts=BASE_TS + timedelta(minutes=1))
    loop.run_once()

    assert len(broker.buys) == 1, "no buy submitted; the assertion below would be vacuous"
    assert broker.buy_limits[0] == 98.0, "the limit must be the price the trigger fired at"
