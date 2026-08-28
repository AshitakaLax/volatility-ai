"""Tests for trailing exit targets.

The headline properties here are the two that make this safe to bolt
onto a system whose lots were previously immutable after creation:

  1. A target only ever ratchets DOWN, so nothing can strand a lot that
     was already sellable.
  2. Retargeting preserves target_sell_price == buy_price *
     (1 + profit_target), which src/persistence.py asserts on every
     reload -- break it and every restart raises PersistenceError.
"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from src import decision_cycle
from src.exceptions import ConfigurationError
from src.ledger import AssetLotLedger
from src.market_context import MarketContext
from src.size_calculators import FixedPortfolioPercentage
from src.trailing_target import TrailingTargetPolicy

EQUITY = 100_000.0


def ctx(price: float) -> MarketContext:
    return MarketContext(
        timestamp=datetime(2026, 3, 2, 15, 0, tzinfo=UTC),
        open=price,
        high=price,
        low=price,
        close=price,
        cash=EQUITY,
        equity=EQUITY,
        peak_equity=EQUITY,
        drawdown=0.0,
        open_lot_count=0,
        bar_index=0,
    )


def a_lot(buy_price: float = 100.0, profit_target: float = 0.75):
    ledger = AssetLotLedger()
    lot = ledger.register_buy("ord-1", "TQQQ", buy_price, 10.0, profit_target)
    return ledger, lot


# --- Lot.retarget ---


def test_retarget_moves_both_fields_together():
    """The derivation persistence.load_ledger asserts on must survive."""
    _, lot = a_lot(buy_price=100.0, profit_target=0.75)
    assert lot.target_sell_price == pytest.approx(175.0)

    lot.retarget(0.20)

    assert lot.profit_target == pytest.approx(0.20)
    assert lot.target_sell_price == pytest.approx(120.0)
    # The exact invariant src/persistence.py:322 checks on reload.
    assert lot.target_sell_price == pytest.approx(lot.buy_price * (1.0 + lot.profit_target))


def test_retarget_never_touches_cost_basis_or_shares():
    """buy_price is what the no-loss guard evaluates against."""
    _, lot = a_lot(buy_price=100.0)
    lot.retarget(0.05)
    assert lot.buy_price == pytest.approx(100.0)
    assert lot.shares == pytest.approx(10.0)


@pytest.mark.parametrize("bad", [0.0, -0.01])
def test_retarget_rejects_a_non_positive_target(bad):
    _, lot = a_lot()
    with pytest.raises(ValueError, match="new_profit_target"):
        lot.retarget(bad)


def test_a_retargeted_lot_becomes_marketable_at_the_new_price():
    ledger, lot = a_lot(buy_price=100.0, profit_target=0.75)
    assert ledger.get_marketable_lots(120.0) == []
    lot.retarget(0.20)
    assert ledger.get_marketable_lots(120.0) == [lot]


# --- TrailingTargetPolicy ---


def test_target_trails_the_peak_down_once_price_retreats():
    policy = TrailingTargetPolicy(trail_pct=0.10)
    _, lot = a_lot(buy_price=100.0, profit_target=0.75)

    # Rises to 160 -- still short of the 175 fixed target, so a fixed
    # target would leave this lot unsellable.
    policy.observe(lot, 160.0)
    proposed = policy.propose(lot, 150.0)

    assert proposed is not None
    # peak 160 trailed by 10% -> 144 -> profit_target 0.44
    assert proposed == pytest.approx(0.44)


def test_the_target_only_ratchets_down_never_back_up():
    policy = TrailingTargetPolicy(trail_pct=0.10)
    _, lot = a_lot(buy_price=100.0, profit_target=0.75)

    policy.observe(lot, 160.0)
    lot.retarget(policy.propose(lot, 150.0))
    lowered = lot.target_sell_price

    # Price falls further: the peak is unchanged, so the trailed price
    # is unchanged, and there is nothing to move.
    assert policy.propose(lot, 120.0) is None
    assert lot.target_sell_price == pytest.approx(lowered)


def test_a_new_peak_does_not_raise_an_already_lowered_target():
    """The ratchet holds even when the peak legitimately rises."""
    policy = TrailingTargetPolicy(trail_pct=0.50)
    _, lot = a_lot(buy_price=100.0, profit_target=0.75)

    policy.observe(lot, 160.0)
    lot.retarget(policy.propose(lot, 100.0))  # peak 160, trail 50% -> 80 -> floored
    lowered = lot.target_sell_price

    # A much higher peak would trail to 250, far above the lowered
    # target -- it must be refused rather than applied.
    assert policy.propose(lot, 500.0) is None
    assert lot.target_sell_price == pytest.approx(lowered)


def test_the_floor_stops_the_target_falling_to_the_cost_basis():
    policy = TrailingTargetPolicy(trail_pct=0.90, min_profit_target=0.01)
    _, lot = a_lot(buy_price=100.0, profit_target=0.75)

    # Peak 100 (the buy price) trailed by 90% would be 10 -- far below
    # cost. The floor must win.
    proposed = policy.propose(lot, 100.0)
    assert proposed == pytest.approx(0.01)
    lot.retarget(proposed)
    assert lot.target_sell_price == pytest.approx(101.0)
    assert lot.target_sell_price > lot.buy_price


def test_the_peak_is_seeded_from_buy_price_not_the_first_observation():
    """A lot that only ever falls trails from what it cost."""
    policy = TrailingTargetPolicy(trail_pct=0.10)
    _, lot = a_lot(buy_price=100.0, profit_target=0.75)
    assert policy.observe(lot, 50.0) == pytest.approx(100.0)


def test_forget_drops_a_closed_lots_peak():
    policy = TrailingTargetPolicy(trail_pct=0.10)
    _, lot = a_lot()
    policy.observe(lot, 150.0)
    assert lot.order_id in policy._peaks
    policy.forget(lot.order_id)
    assert lot.order_id not in policy._peaks


@pytest.mark.parametrize(
    "kw", [{"trail_pct": 0.0}, {"trail_pct": 1.0}, {"trail_pct": -0.1}]
)
def test_invalid_trail_pct_is_rejected(kw):
    with pytest.raises(ConfigurationError, match="trail_pct"):
        TrailingTargetPolicy(**kw)


def test_invalid_min_profit_target_is_rejected():
    with pytest.raises(ConfigurationError, match="min_profit_target"):
        TrailingTargetPolicy(trail_pct=0.1, min_profit_target=0.0)


# --- the decision-cycle hook ---


def test_strategies_do_not_retarget_by_default():
    """Every existing strategy must behave exactly as before."""
    ledger, lot = a_lot(buy_price=100.0, profit_target=0.75)
    strategy = FixedPortfolioPercentage(allocation_pct=0.05)
    before = lot.target_sell_price

    changed = decision_cycle.adjust_open_lot_targets(strategy, ledger, ctx(150.0))

    assert changed == []
    assert lot.target_sell_price == pytest.approx(before)


def test_adjust_open_lot_targets_applies_and_reports_changes():
    class Trailing(FixedPortfolioPercentage):
        def __init__(self):
            super().__init__(allocation_pct=0.05)
            self.policy = TrailingTargetPolicy(trail_pct=0.10)

        def adjust_profit_target(self, lot, context):
            return self.policy.propose(lot, context.price)

    ledger, lot = a_lot(buy_price=100.0, profit_target=0.75)
    strategy = Trailing()
    strategy.policy.observe(lot, 160.0)

    changed = decision_cycle.adjust_open_lot_targets(strategy, ledger, ctx(150.0))

    assert changed == [lot]
    assert lot.target_sell_price == pytest.approx(144.0)


def test_skip_order_ids_leaves_those_lots_untouched():
    """The live loop's in-flight-sell exclusion."""

    class AlwaysHalve(FixedPortfolioPercentage):
        def __init__(self):
            super().__init__(allocation_pct=0.05)

        def adjust_profit_target(self, lot, context):
            return lot.profit_target / 2.0

    ledger = AssetLotLedger()
    kept = ledger.register_buy("in-flight", "TQQQ", 100.0, 10.0, 0.75)
    moved = ledger.register_buy("free", "TQQQ", 100.0, 10.0, 0.75)

    changed = decision_cycle.adjust_open_lot_targets(
        AlwaysHalve(), ledger, ctx(150.0), skip_order_ids={"in-flight"}
    )

    assert changed == [moved]
    assert kept.profit_target == pytest.approx(0.75)
    assert moved.profit_target == pytest.approx(0.375)


def test_a_hook_returning_the_current_target_is_not_a_change():
    """No mutation and no durable write for a coincidental no-op."""

    class Unchanged(FixedPortfolioPercentage):
        def __init__(self):
            super().__init__(allocation_pct=0.05)

        def adjust_profit_target(self, lot, context):
            return lot.profit_target

    ledger, _ = a_lot()
    assert decision_cycle.adjust_open_lot_targets(Unchanged(), ledger, ctx(150.0)) == []
