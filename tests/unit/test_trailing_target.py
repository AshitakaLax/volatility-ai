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
from src.ledger import AssetLotLedger, Lot
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
    policy = TrailingTargetPolicy(trail_pct=0.30)
    _, lot = a_lot(buy_price=100.0, profit_target=0.75)

    policy.observe(lot, 160.0)
    lot.retarget(policy.propose(lot, 100.0))  # peak 160, trail 30% -> 112, above cost
    lowered = lot.target_sell_price

    # A much higher peak would trail to 350, far above the lowered
    # target -- it must be refused rather than applied.
    assert policy.propose(lot, 500.0) is None
    assert lot.target_sell_price == pytest.approx(lowered)


def test_the_floor_is_a_bound_not_a_destination():
    """A trailed price below the floor produces NO proposal -- the lot
    keeps its original target rather than being dragged down to the
    floor.

    This previously asserted the opposite (clamp to the floor), which is
    what made the floor an attractor: see
    test_the_floor_does_not_swallow_the_difference_between_trail_pcts
    for the failure that behavior caused."""
    policy = TrailingTargetPolicy(trail_pct=0.50, min_profit_target=0.01)
    _, lot = a_lot(buy_price=100.0, profit_target=0.75)

    # Peak 201 trailed by 50% is 100.5 -- above cost, but below the
    # 1% floor at 101. Nothing to propose.
    assert policy.propose(lot, 201.0) is None
    assert lot.target_sell_price == pytest.approx(175.0)


def test_no_proposal_ever_lands_below_the_floor():
    """The floor's actual job, stated as an invariant over a wide sweep
    of peaks rather than a single case."""
    policy = TrailingTargetPolicy(trail_pct=0.20, min_profit_target=0.10)
    for peak in range(101, 400):
        _, lot = a_lot(buy_price=100.0, profit_target=3.0)
        proposed = policy.propose(lot, float(peak))
        if proposed is not None:
            assert proposed >= 0.10


def test_the_floor_does_not_swallow_the_difference_between_trail_pcts():
    """THE REGRESSION THIS FILE EXISTS FOR, second occurrence.

    With `new_target = max(trailed_price, floor_price)` and a guard that
    only required trailed_price > buy_price, the guard released while
    trailed_price was still far below the floor -- so max() returned the
    floor, and ratchet-down-only locked the lot there. Every trail_pct
    produced an IDENTICAL target, differing only in when it snapped.

    Caught from sweep output twice, a month apart: first with a fixed
    0.10 floor across profit_targets 0.30-1.00 (all four byte-identical),
    then again after scaling the floor per-target, where trail_pct 0.05
    and 0.10 still returned identical results -- 2621.31% return, 91,608
    trades, to the digit. Scaling an attractor just moves it.

    A tighter trail must give up on the original target EARLIER and land
    HIGHER than a looser one. If these ever coincide, the floor is
    swallowing the parameter again and every sweep over trail_pct is
    measuring nothing."""
    targets = {}
    for trail_pct in (0.05, 0.10, 0.20):
        policy = TrailingTargetPolicy(trail_pct=trail_pct, min_profit_target=0.15)
        _, lot = a_lot(buy_price=100.0, profit_target=0.30)
        # Walk the price up one dollar at a time, applying whatever the
        # policy proposes -- exactly what adjust_open_lot_targets does.
        for price in range(100, 130):
            proposed = policy.propose(lot, float(price))
            if proposed is not None:
                lot.retarget(proposed)
        targets[trail_pct] = lot.target_sell_price

    assert len(set(targets.values())) == 3, (
        f"trail_pct made no difference to the final target: {targets}"
    )
    # Among the trails that engaged, a tighter one lands higher.
    assert targets[0.05] > targets[0.10]
    # 0.20 never engages here, and that is correct rather than a gap: a
    # 20% trail cannot clear a 15% floor until the peak reaches 143.75,
    # by which point the lot has long since passed its own 30% target at
    # 130 and sold. A trail wider than the distance between the floor and
    # the target is inert by construction -- worth pinning, because a
    # sweep row showing "trailing did nothing" is a real finding about
    # the parameterisation and not a bug to go hunting for.
    assert targets[0.20] == pytest.approx(130.0)
    # None of them is the floor itself -- that is the attractor signature.
    assert all(t != pytest.approx(115.0) for t in targets.values())


def test_trailing_does_not_activate_from_a_degenerate_peak():
    """The regression this exists to pin: observe() seeds a fresh lot's
    peak from buy_price, so on the FIRST call, before price has moved
    at all, trailed_price = buy_price * (1 - trail_pct) is already
    BELOW cost for any trail_pct > 0. Without the guard,
    max(trailed_price, floor_price) picks floor_price unconditionally
    on that first call -- collapsing profit_target=0.30 straight to
    whatever the floor is, regardless of trail_pct, regardless of
    whether price ever moved, and the ratchet-down-only rule then locks
    it there permanently. Verified directly before this fix existed:
    propose(lot, 100.0) with buy_price=100.0 proposed 0.10 immediately."""
    for trail_pct in (0.05, 0.10, 0.20):
        policy = TrailingTargetPolicy(trail_pct=trail_pct, min_profit_target=0.10)
        _, lot = a_lot(buy_price=100.0, profit_target=0.30)
        assert policy.propose(lot, 100.0) is None, (
            f"trail_pct={trail_pct} activated on the very first tick, price unchanged"
        )
        assert lot.profit_target == pytest.approx(0.30)


def test_trailing_activates_once_the_peak_shows_a_real_gain():
    """The other half of the same fix: it must still activate once
    there IS something to trail from."""
    policy = TrailingTargetPolicy(trail_pct=0.05, min_profit_target=0.10)
    _, lot = a_lot(buy_price=100.0, profit_target=0.30)
    policy.observe(lot, 100.0)  # no gain yet

    proposed = policy.propose(lot, 116.0)  # 16% gain -- trail(5%) clears cost
    assert proposed is not None
    assert proposed < 0.30


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


@pytest.mark.parametrize("kw", [{"trail_pct": 0.0}, {"trail_pct": 1.0}, {"trail_pct": -0.1}])
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


# --- the inert-retargeting early-out (a performance guard) ---


class _CountingLedger:
    def __init__(self, lots):
        self.open_lots = lots


class _Recorder:
    """A strategy double that counts how often it is asked to retarget."""

    def __init__(self, wants: bool | None):
        self.calls = 0
        self.retained = 0
        if wants is not None:
            self.wants_lot_retargeting = lambda: wants

    def adjust_profit_target(self, lot, context):
        self.calls += 1
        return None

    def retain_lots(self, open_order_ids):
        self.retained += 1


def _lots(n):
    return [
        Lot(order_id=f"L{i}", symbol="TQQQ", buy_price=100.0, shares=1.0, profit_target=0.10)
        for i in range(n)
    ]


def test_a_strategy_declaring_inert_retargeting_is_not_walked():
    """The performance fix. Profiled at 63% of runtime under cProfile
    and a measured 2.4x wall-clock speedup: with trail_pct unset, this
    walked every open lot on every bar to call a hook that returns None
    immediately."""
    strategy = _Recorder(wants=False)
    ledger = _CountingLedger(_lots(500))

    changed = decision_cycle.adjust_open_lot_targets(strategy, ledger, ctx(100.0))

    assert changed == []
    assert strategy.calls == 0, "the hook was called despite being declared inert"
    assert strategy.retained == 0, "retain_lots ran despite being declared inert"


def test_a_strategy_declaring_it_wants_retargeting_is_still_walked():
    strategy = _Recorder(wants=True)
    ledger = _CountingLedger(_lots(7))

    decision_cycle.adjust_open_lot_targets(strategy, ledger, ctx(100.0))

    assert strategy.calls == 7
    assert strategy.retained == 1


def test_a_strategy_without_the_method_keeps_the_old_behavior():
    """Duck-typed and defaulting to walked. A test double or an
    externally supplied strategy that never heard of this optimisation
    must behave exactly as before."""
    strategy = _Recorder(wants=None)
    assert not hasattr(strategy, "wants_lot_retargeting")
    ledger = _CountingLedger(_lots(4))

    decision_cycle.adjust_open_lot_targets(strategy, ledger, ctx(100.0))

    assert strategy.calls == 4
    assert strategy.retained == 1


def test_the_real_strategy_reports_inert_exactly_when_trailing_is_off():
    """The declaration must track the actual condition, or the early-out
    would skip work that matters."""
    from src.high_frequency_sizing import HighFrequencyLocalReferenceSizing

    common = dict(per_lot_pct=0.001, lookback_days=0.02, bars_per_day=390)
    assert HighFrequencyLocalReferenceSizing(**common).wants_lot_retargeting() is False
    with_trail = HighFrequencyLocalReferenceSizing(
        trail_pct=0.05, trail_min_profit_target=0.10, **common
    )
    assert with_trail.wants_lot_retargeting() is True


def test_trailing_still_retargets_through_the_real_helper():
    """End-to-end guard: the early-out must not disable trailing for a
    strategy that genuinely uses it."""
    from src.high_frequency_sizing import HighFrequencyLocalReferenceSizing

    strategy = HighFrequencyLocalReferenceSizing(
        per_lot_pct=0.001,
        lookback_days=0.02,
        bars_per_day=390,
        trail_pct=0.05,
        trail_min_profit_target=0.10,
    )
    lot = Lot(order_id="L1", symbol="TQQQ", buy_price=100.0, shares=1.0, profit_target=1.00)
    ledger = _CountingLedger([lot])
    # Drive the peak well above the floor so a lower target is proposed.
    for price in (100.0, 150.0, 200.0, 190.0):
        decision_cycle.adjust_open_lot_targets(strategy, ledger, ctx(price))

    assert lot.profit_target < 1.00, "trailing did not retarget through the helper"
