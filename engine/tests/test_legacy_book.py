"""An algorithm switch's `legacy_lots`: the lots held at the switch keep
exiting at their own targets, and the algorithm now trading neither sees nor
retargets nor liquidates them (live_trading_loop._apply_transition)."""

from __future__ import annotations

import pytest

from engine.core.ledger import EXIT_AT_COST_TARGET
from engine.core.persistence import LedgerStore
from engine.tests.test_live_trading_loop import FakeBroker, FakeMarketData, make_config
from engine.trading.live_trading_loop import LEGACY_OWNER, LiveTradingLoop
from research.strategies.size_calculators import FixedPortfolioPercentage

STAMP = "2026-10-28T14:00:00+00:00"


class Resuming(FixedPortfolioPercentage):
    """Records the lots it was handed to resume."""

    resumed: list | None = None

    def resume(self, open_lots):
        self.resumed = [lot.order_id for lot in open_lots]


@pytest.fixture
def store(tmp_path):
    s = LedgerStore(str(tmp_path / "ledger.db"))
    for order_id, price in (("old-1", 100.0), ("old-2", 90.0)):
        ledger = s.load_ledger()
        lot = ledger.register_buy(order_id, "TQQQ", price, 10.0, 0.05)
        s.record_open_lot(lot)
    s.save_last_buy_price(90.0)
    yield s
    s.close()


def loop(store, strategy=None, transition=None):
    return LiveTradingLoop(
        config=make_config(),
        strategy=strategy or Resuming(allocation_pct=0.05),
        broker=FakeBroker(),
        market_data=FakeMarketData(),
        store=store,
        sleep=lambda _: None,
        transition=transition,
    )


def test_a_switch_that_keeps_the_lots_hides_them_from_the_new_strategy(store):
    strategy = Resuming(allocation_pct=0.05)
    built = loop(store, strategy, {"legacy_lots": "keep", "changedAt": STAMP})
    assert {lot.order_id for lot in built.legacy_lots} == {"old-1", "old-2"}
    assert strategy.resumed == []
    assert store.lot_owners() == {"old-1": LEGACY_OWNER, "old-2": LEGACY_OWNER}
    # Their targets are untouched: they exit as they were bought to.
    assert [lot.profit_target for lot in built.ledger.open_lots] == [0.05, 0.05]


def test_the_new_grid_starts_from_the_price_now_not_the_old_last_buy(store):
    built = loop(store, transition={"legacy_lots": "keep", "changedAt": STAMP})
    assert built.state.last_buy_price is None
    assert store.load_last_buy_price() is None


def test_exit_at_cost_moves_the_legacy_targets_and_persists_them(store):
    loop(store, transition={"legacy_lots": "exit_at_cost", "changedAt": STAMP})
    assert [lot.profit_target for lot in store.load_ledger().open_lots] == [EXIT_AT_COST_TARGET] * 2


def test_a_switch_is_applied_once_across_restarts(store):
    override = {"legacy_lots": "keep", "changedAt": STAMP}
    loop(store, transition=override)
    # A lot the new algorithm bought, then a restart under the same override.
    ledger = store.load_ledger()
    store.record_open_lot(ledger.register_buy("new-1", "TQQQ", 80.0, 10.0, 0.01))
    strategy = Resuming(allocation_pct=0.05)
    again = loop(store, strategy, override)
    assert strategy.resumed == ["new-1"]
    assert {lot.order_id for lot in again.legacy_lots} == {"old-1", "old-2"}


def test_a_later_switch_makes_the_lots_then_held_legacy_too(store):
    loop(store, transition={"legacy_lots": "keep", "changedAt": STAMP})
    ledger = store.load_ledger()
    store.record_open_lot(ledger.register_buy("new-1", "TQQQ", 80.0, 10.0, 0.01))
    second = loop(store, transition={"legacy_lots": "keep", "changedAt": STAMP + "x"})
    assert {lot.order_id for lot in second.legacy_lots} == {"old-1", "old-2", "new-1"}


def test_a_switch_made_when_flat_or_without_a_mode_changes_nothing(store):
    for override in ({"legacy_lots": "wait", "changedAt": STAMP}, {"changedAt": STAMP}, None):
        built = loop(store, transition=override)
        assert built.legacy_lots == []
    assert store.lot_owners() == {}


def test_a_revert_gives_the_legacy_lots_back(store):
    loop(store, transition={"legacy_lots": "keep", "changedAt": STAMP})
    strategy = Resuming(allocation_pct=0.05)
    built = loop(store, strategy, transition=None)
    assert built.legacy_lots == []
    assert strategy.resumed == ["old-1", "old-2"]
    assert store.lot_owners() == {}


def test_the_legacy_lots_still_sell_at_their_targets(store):
    market = FakeMarketData()
    broker = FakeBroker()
    built = LiveTradingLoop(
        config=make_config(),
        strategy=Resuming(allocation_pct=0.05),
        broker=broker,
        market_data=market,
        store=store,
        sleep=lambda _: None,
        transition={"legacy_lots": "keep", "changedAt": STAMP},
    )
    market.push(106.0)  # old-1 bought at 100 targets 105; old-2 at 90 targets 94.5
    built.run_once()
    assert len(broker.sells) == 2
