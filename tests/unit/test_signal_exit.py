"""
Signal exits: the only sell path in this system permitted to realize a
loss (src/no_loss_guard.SellReason.SIGNAL_EXIT).

The tests here are weighted toward the NEGATIVE cases -- the ones that
prove the feature stays off -- because that is where the risk is. A
signal exit that fails to fire costs a backtest result. A signal exit
that fires when nobody asked for one sells real inventory at a real
loss, and the two-condition gate is the only thing standing in front of
that.

The strategy-level assertions run through the real OptimizationController
on the regression fixture rather than against a hand-built ledger, so
they exercise the actual sell block, the actual guard call, and the
actual metrics row -- not a reimplementation of them.
"""

from __future__ import annotations

import pytest

from optimization_controller import OptimizationController
from src import decision_cycle
from src.cost_models import ZeroCostModel
from src.ledger import AssetLotLedger
from src.no_loss_guard import NoLossViolation, SellReason, validate_sell
from src.size_calculators import FixedPortfolioPercentage
from tests.fixtures.regression_baseline import (
    GRID_STEP,
    PROFIT_TARGET,
    STRATEGY_PARAMS,
    load_fixture_data,
)


class _LiquidateEverything(FixedPortfolioPercentage):
    """Dumps the whole book on the bar its trip price is first crossed.

    Deliberately a crude signal. The point under test is the plumbing --
    that a request reaches the sell block and closes lots regardless of
    P&L -- not whether the signal is any good.
    """

    def __init__(self, *args, trip_below: float = 0.0, **kwargs):
        super().__init__(*args, **kwargs)
        self.trip_below = trip_below
        self.liquidation_calls = 0

    def lots_to_liquidate(self, open_lots, context):
        self.liquidation_calls += 1
        if context.price >= self.trip_below:
            return []
        return list(open_lots)


def _sweep(strategy_class, params, **kwargs) -> dict:
    controller = OptimizationController(historical_data=load_fixture_data())
    result = controller.run_sweep(
        grid_steps=[GRID_STEP],
        profit_targets=[PROFIT_TARGET],
        strategy_class=strategy_class,
        strategy_params_grid=[params],
        **kwargs,
    )
    return result.iloc[0].to_dict()


# --- the two-condition gate -------------------------------------------


def test_hook_without_the_flag_liquidates_nothing():
    """Half the gate is not the gate.

    A strategy that asks to liquidate on every bar, dropped into a
    default config, must sell nothing on signal. This is the case that
    protects a user who pip-installs someone else's strategy.
    """
    params = dict(STRATEGY_PARAMS, trip_below=1e9)  # always wants out
    row = _sweep(_LiquidateEverything, params)
    assert row["Signal Exit Count"] == 0


def test_flag_without_the_hook_liquidates_nothing():
    """The other half. A config with the flag on, running a strategy that
    never implements the hook, behaves exactly as it does with the flag
    off -- every number, not just the exit count."""
    on = _sweep(FixedPortfolioPercentage, dict(STRATEGY_PARAMS), allow_signal_exit=True)
    off = _sweep(FixedPortfolioPercentage, dict(STRATEGY_PARAMS), allow_signal_exit=False)
    assert on["Signal Exit Count"] == 0
    assert on == pytest.approx(
        {k: v for k, v in off.items() if isinstance(v, (int, float))}, rel=0, abs=1e-12
    ) or all(on[k] == off[k] for k in off if not isinstance(off[k], (int, float)))
    for key, value in off.items():
        assert on[key] == value, f"{key} moved when the flag was enabled with no hook"


def test_collect_liquidations_checks_both_conditions_every_call():
    """Not cached, not resolved once at construction.

    An authorization computed once is one refactor away from being the
    only authorization; this pins that the flag is consulted on the call
    itself, so flipping it mid-run takes effect.
    """
    ledger = AssetLotLedger()
    lot = ledger.register_buy("a", "TQQQ", 100.0, 10.0, PROFIT_TARGET)
    strategy = _LiquidateEverything(allocation_pct=0.05, trip_below=1e9)

    class _Ctx:
        price = 100.0

    assert (
        decision_cycle.collect_liquidations(strategy, ledger, _Ctx(), allow_signal_exit=False) == []
    )
    assert decision_cycle.collect_liquidations(
        strategy, ledger, _Ctx(), allow_signal_exit=True
    ) == [lot]


# --- the feature actually working -------------------------------------


# Written to by _LiquidateUnderwater below. A module-level list because
# run_sweep constructs the strategy itself, so the test has no handle on
# the instance that actually ran.
UNDERWATER_EXITS: list[tuple[float, float]] = []


class _LiquidateUnderwater(FixedPortfolioPercentage):
    """Condemns only lots that are CURRENTLY AT A LOSS.

    Sharper than _LiquidateEverything for the affirmative case: every
    exit it requests is one the no-loss guard would refuse under
    PROFIT_TARGET, so any of them completing is direct evidence that
    SIGNAL_EXIT changed the outcome rather than merely reordering it.
    """

    def lots_to_liquidate(self, open_lots, context):
        losing = [lot for lot in open_lots if context.price < lot.buy_price]
        UNDERWATER_EXITS.extend((lot.buy_price, context.price) for lot in losing)
        return losing


def test_both_conditions_close_lots_at_a_loss():
    """The affirmative case, asserted on the property under test.

    NOT on final equity: dumping inventory on a decline frees cash that
    re-enters lower, and on this fixture the flag-on run actually ends
    slightly AHEAD. That is a real effect, not a bug, and it is exactly
    why "did equity fall?" is the wrong question -- an aggregate that a
    second effect can swamp proves nothing either way.

    The claim being tested is narrower and checkable: sells completed at
    prices below their lots' buy prices. Under PROFIT_TARGET every one
    of them would have raised NoLossViolation and been skipped.
    """
    UNDERWATER_EXITS.clear()
    on = _sweep(_LiquidateUnderwater, dict(STRATEGY_PARAMS), allow_signal_exit=True)
    requested_with_flag = len(UNDERWATER_EXITS)

    UNDERWATER_EXITS.clear()
    off = _sweep(_LiquidateUnderwater, dict(STRATEGY_PARAMS), allow_signal_exit=False)
    requested_without_flag = len(UNDERWATER_EXITS)

    assert requested_with_flag > 0, (
        "The fixture never put a lot underwater, so this test is not "
        "measuring anything. Check regression_ohlcv.csv still declines."
    )
    # With the flag off the hook is NOT CALLED AT ALL -- collect_liquidations
    # returns before touching strategy code. Pinned deliberately, for two
    # reasons. Cost: this runs once per bar over ~1M bars, and the
    # wants_lot_retargeting early-out exists because exactly this shape of
    # per-bar hook was 63% of runtime. Safety: a strategy whose hook has
    # side effects cannot have them when the feature is disabled.
    assert requested_without_flag == 0

    # THE PROOF, and it rests on where the counter lives. Signal Exit
    # Count is incremented inside _apply_sell_fill -- after the guard
    # returned, after close_lot, after the cash moved. A nonzero count
    # therefore means lots CLOSED, not merely that exits were requested.
    # And _LiquidateUnderwater only ever condemns lots trading below
    # their buy price, so every one of those closes was a booked loss
    # that PROFIT_TARGET would have refused.
    assert on["Signal Exit Count"] > 0
    assert off["Signal Exit Count"] == 0

    # Deliberately NOT asserted on Closed Trade Count: it comes out equal
    # (4 and 4) on this fixture, because a signal exit substitutes for a
    # harvest that would have happened later and the freed cash re-enters.
    # An aggregate two effects push in opposite directions is not evidence
    # of either one. The run must still DIFFER somewhere, though -- if
    # every number matched, the exits would have been undone.
    assert any(on[k] != off[k] for k in off), "signal exits changed nothing measurable"


def test_signal_exit_count_appears_even_when_the_feature_is_off():
    """A column that appears conditionally is one an analysis script
    silently reads as absent-means-zero."""
    row = _sweep(FixedPortfolioPercentage, dict(STRATEGY_PARAMS))
    assert row["Signal Exit Count"] == 0


# --- the guard itself --------------------------------------------------


class _Lot:
    order_id = "x"
    symbol = "TQQQ"
    shares = 10.0
    buy_price = 100.0
    target_sell_price = 100.5
    profit_target = 0.005


def test_profit_target_still_raises_on_a_losing_sell():
    """The default reason must keep rejecting losses. If this ever stops
    being true, the feature has widened from 'signal exits may lose' to
    'sells may lose', which is a different system."""
    with pytest.raises(NoLossViolation):
        validate_sell(_Lot(), 10.0, 90.0, ZeroCostModel())

    with pytest.raises(NoLossViolation):
        validate_sell(_Lot(), 10.0, 90.0, ZeroCostModel(), reason=SellReason.PROFIT_TARGET)


def test_signal_exit_returns_the_same_economics_it_would_have_raised_on():
    """A signal exit is not a bypass: it runs the identical computation
    and returns it. The loss it reports must be the loss the guard
    would have refused, to the cent."""
    losing = validate_sell(_Lot(), 10.0, 90.0, ZeroCostModel(), reason=SellReason.SIGNAL_EXIT)
    assert losing.net_sell_proceeds < losing.allocated_cost_basis
    assert losing.net_sell_proceeds == pytest.approx(900.0)

    # And a PROFITABLE signal exit is unremarkable -- same numbers as a
    # harvest, since only the decision to raise differs.
    won = validate_sell(_Lot(), 10.0, 110.0, ZeroCostModel(), reason=SellReason.SIGNAL_EXIT)
    harvested = validate_sell(_Lot(), 10.0, 110.0, ZeroCostModel())
    assert won == harvested


# --- interactions ------------------------------------------------------


def test_a_condemned_lot_is_not_also_harvested():
    """A lot both marketable and condemned must sell ONCE.

    Selling it twice would credit cash for shares that no longer exist,
    which the ledger would happily record.
    """
    ledger = AssetLotLedger()
    lot = ledger.register_buy("a", "TQQQ", 100.0, 10.0, PROFIT_TARGET)
    strategy = _LiquidateEverything(allocation_pct=0.05, trip_below=1e9)

    class _Ctx:
        price = 200.0  # far above the target, so it is marketable too

    condemned = decision_cycle.collect_liquidations(
        strategy, ledger, _Ctx(), allow_signal_exit=True
    )
    marketable = ledger.get_marketable_lots(_Ctx.price)
    assert lot in condemned and lot in marketable

    remaining = [x for x in marketable if x.order_id not in {c.order_id for c in condemned}]
    assert remaining == [], "the de-duplication the sell sites perform must remove it"


def test_a_stale_lot_reference_is_ignored_rather_than_sold():
    """A strategy holding a lot that has already closed must not be able
    to sell it again. Filtered against the live book, not trusted."""
    ledger = AssetLotLedger()
    lot = ledger.register_buy("a", "TQQQ", 100.0, 10.0, PROFIT_TARGET)
    kept = ledger.register_buy("b", "TQQQ", 100.0, 10.0, PROFIT_TARGET)
    ledger.close_lot(lot)

    class _Stale(FixedPortfolioPercentage):
        def lots_to_liquidate(self, open_lots, context):
            return [lot, kept, kept]  # closed lot, plus a duplicate

    class _Ctx:
        price = 100.0

    got = decision_cycle.collect_liquidations(
        _Stale(allocation_pct=0.05), ledger, _Ctx(), allow_signal_exit=True
    )
    assert got == [kept], "closed lot dropped, duplicate collapsed"


def test_in_flight_lots_are_excluded():
    """The live loop's exclusion: a lot with a sell already resting must
    not receive a second order."""
    ledger = AssetLotLedger()
    a = ledger.register_buy("a", "TQQQ", 100.0, 10.0, PROFIT_TARGET)
    b = ledger.register_buy("b", "TQQQ", 100.0, 10.0, PROFIT_TARGET)
    strategy = _LiquidateEverything(allocation_pct=0.05, trip_below=1e9)

    class _Ctx:
        price = 100.0

    got = decision_cycle.collect_liquidations(
        strategy, ledger, _Ctx(), allow_signal_exit=True, skip_order_ids={a.order_id}
    )
    assert got == [b]


# --- all three sell sites, or none ------------------------------------


def test_every_sell_site_routes_through_the_shared_helper():
    """Requirement 4 of the scope, enforced at the source level.

    Divergence between backtest and live is the exact failure
    src/decision_cycle.py exists to prevent. The liquidation decision is
    made in ONE place; a sell site that grew its own copy would be
    invisible to every behavioral test here, because both copies would
    agree on the day they were written and drift afterward.

    Mirrors test_both_paths_route_through_the_shared_decision_cycle_module,
    which pins the same discipline for record_tick and the grid trigger.
    """
    import inspect

    import optimization_controller
    import src.intraday_validation
    import src.live_trading_loop

    sites = {
        "_simulate_single": inspect.getsource(
            optimization_controller.OptimizationController._simulate_single
        ),
        "simulate_single_intraday": inspect.getsource(
            src.intraday_validation.simulate_single_intraday
        ),
        "LiveTradingLoop._harvest": inspect.getsource(
            src.live_trading_loop.LiveTradingLoop._harvest
        ),
    }
    for name, source in sites.items():
        assert "decision_cycle.collect_liquidations(" in source, (
            f"{name} does not route signal exits through the shared module. "
            "Either wire it up or remove the feature -- three sell sites "
            "that disagree about when to liquidate is worse than none."
        )
        assert "lots_to_liquidate(" not in source, (
            f"{name} calls the strategy hook directly, bypassing the "
            "allow_signal_exit gate that lives in collect_liquidations."
        )


def test_every_sell_site_names_the_reason_it_is_selling():
    """No sell site may call validate_sell without saying why.

    An omitted `reason` defaults to PROFIT_TARGET, which is the safe
    direction -- but a signal exit silently defaulting to PROFIT_TARGET
    would be refused by the guard and leave the position open while the
    strategy believed it had exited. Live, that means holding inventory
    a regime signal said to drop.
    """
    import inspect
    import re

    import optimization_controller
    import src.intraday_validation
    import src.live_trading_loop

    for name, source in (
        (
            "_simulate_single",
            inspect.getsource(optimization_controller.OptimizationController._simulate_single),
        ),
        (
            "simulate_single_intraday",
            inspect.getsource(src.intraday_validation.simulate_single_intraday),
        ),
        (
            "LiveTradingLoop._apply_sell_fill",
            inspect.getsource(src.live_trading_loop.LiveTradingLoop._apply_sell_fill),
        ),
    ):
        calls = re.findall(r"validate_sell\((.*?)\n\s*\)", source, re.DOTALL)
        assert calls, f"{name} no longer calls validate_sell at all"
        for call in calls:
            assert "reason=" in call, f"{name} calls validate_sell without a reason"


# --- T+N settlement ----------------------------------------------------
#
# Lives here rather than in its own file because it shares _sweep and the
# same "default is byte-identical" discipline. The measurement of what it
# costs is tools/probe_settlement_drag.py.


def test_settlement_defaults_to_instant_and_changes_nothing():
    on = _sweep(FixedPortfolioPercentage, dict(STRATEGY_PARAMS), settlement_days=0)
    off = _sweep(FixedPortfolioPercentage, dict(STRATEGY_PARAMS))
    assert on == off


def test_settlement_is_not_monotonic_and_this_is_expected():
    """DELIBERATELY asserts no ordering, because none holds.

    The first version of this test asserted that T+1 can only reduce
    trade count and equity -- "a tighter constraint cannot help". It
    passed on this fixture and is FALSE on the real dataset: the regime
    book goes from 24,648 trades at T+0 to 24,675 at T+1, and its 2022
    improves from +3.6% to +3.7%.

    The reason is path dependence. A buy that cannot be funded today
    does not merely vanish -- it leaves last_buy_price and the rolling
    grid reference where they were, which changes every subsequent
    trigger. Removing one trade early can produce more trades later.

    So the invariant worth pinning is that the constraint is APPLIED,
    not that the outcome moves in a particular direction. That is
    covered by the buying-power tests below, which check the mechanism
    directly rather than inferring it from an aggregate.
    """
    instant = _sweep(FixedPortfolioPercentage, dict(STRATEGY_PARAMS), settlement_days=0)
    delayed = _sweep(FixedPortfolioPercentage, dict(STRATEGY_PARAMS), settlement_days=1)
    assert set(instant) == set(delayed), "same columns either way"
    assert delayed["Final Equity"] > 0, "a T+1 run still completes"


def test_a_buy_cannot_be_funded_from_unsettled_proceeds():
    """The mechanism, checked directly.

    This is what "settlement is applied" actually means, and it is
    asserted here rather than inferred from a sweep aggregate -- see
    test_settlement_is_not_monotonic_and_this_is_expected for why an
    aggregate cannot carry that claim.
    """
    from optimization_controller import BacktestState

    state = BacktestState(0.0, 50.0)
    state.advance_session(1000)
    state.credit_sale(1_000.0, settlement_days=1)
    assert state.cash == 1_000.0
    assert state.buying_power == 0.0, "nothing spendable on the sale day"
    state.advance_session(1001)
    assert state.buying_power == 1_000.0, "spendable on the next session"


def test_unsettled_proceeds_still_count_as_equity():
    """They are really yours -- they just cannot be SPENT yet. Excluding
    them from equity would understate the account and corrupt drawdown."""
    from optimization_controller import BacktestState

    state = BacktestState(1_000.0, 50.0)
    state.credit_sale(500.0, settlement_days=1)
    assert state.cash == 1_500.0, "equity uses total cash"
    assert state.buying_power == 1_000.0, "only settled cash is spendable"


def test_buying_power_floors_at_zero_rather_than_going_negative():
    """A buy debits total cash while unsettled is unchanged, so cash can
    legitimately fall below unsettled. That means nothing spendable, and
    a negative would silently invert the comparison at the buy gate."""
    from optimization_controller import BacktestState

    state = BacktestState(100.0, 50.0)
    state.credit_sale(900.0, settlement_days=1)
    state.cash -= 150.0
    assert state.buying_power == 0.0


def test_proceeds_settle_on_a_later_session_not_a_later_bar():
    """T+1 means the next TRADING DAY, not the next minute."""
    from optimization_controller import BacktestState

    state = BacktestState(0.0, 50.0)
    state.advance_session(1000)
    state.credit_sale(500.0, settlement_days=1)
    assert state.buying_power == 0.0
    state.advance_session(1000)  # same session again
    assert state.buying_power == 0.0
    state.advance_session(1001)
    assert state.buying_power == 500.0
