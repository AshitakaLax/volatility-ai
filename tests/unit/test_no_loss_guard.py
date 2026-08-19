"""
Task 7.15 acceptance tests.

Acceptance criteria:
1. A sell at the nominal target passes only when net proceeds cover
   allocated cost basis.
2. A sell whose nominal target is profitable but becomes a loss after
   modeled commission/slippage is rejected.
3. A partial fill that remains profitable closes only the filled portion.
4. No live circuit-breaker, shutdown, or reconciliation path can create
   an intentional loss-making sell.
5. Only ONE implementation of the no-loss comparison exists; Tasks 1.5
   and 7.2 call it rather than duplicating it.
"""

import re
from pathlib import Path

import pytest

from src.cost_models import SlippageCommissionModel, ZeroCostModel
from src.exceptions import ExecutionError
from src.ledger import AssetLotLedger
from src.no_loss_guard import (
    MONEY_EPSILON,
    NoLossViolation,
    SellEconomics,
    compute_sell_economics,
    validate_sell,
)

REPO_ROOT = Path(__file__).resolve().parents[2]


def _lot(buy_price=100.0, shares=10.0, profit_target=0.01):
    ledger = AssetLotLedger()
    return ledger, ledger.register_buy("lot-1", "TQQQ", buy_price, shares, profit_target)


def test_profitable_sell_at_the_nominal_target_is_permitted():
    _, lot = _lot(buy_price=100.0, shares=10.0, profit_target=0.01)
    economics = validate_sell(lot, 10.0, lot.target_sell_price, ZeroCostModel())
    assert economics.permitted
    assert economics.realized_pnl > 0
    assert economics.allocated_cost_basis == pytest.approx(1000.0)
    assert economics.net_sell_proceeds == pytest.approx(1010.0)


def test_sell_below_cost_basis_is_rejected():
    _, lot = _lot(buy_price=100.0, shares=10.0)
    with pytest.raises(NoLossViolation, match="REJECTED"):
        validate_sell(lot, 10.0, 99.0, ZeroCostModel())


def test_break_even_sell_is_permitted():
    # sell_permitted iff net_sell_proceeds >= allocated_cost_basis --
    # exactly equal must pass, not fail.
    _, lot = _lot(buy_price=100.0, shares=10.0)
    economics = validate_sell(lot, 10.0, 100.0, ZeroCostModel())
    assert economics.permitted
    assert economics.realized_pnl == pytest.approx(0.0)


def test_a_loss_smaller_than_money_epsilon_is_tolerated():
    # The contract rejects only below (basis - MONEY_EPSILON).
    _, lot = _lot(buy_price=100.0, shares=1.0)
    economics = validate_sell(lot, 1.0, 100.0 - MONEY_EPSILON / 2, ZeroCostModel())
    assert economics.permitted


def test_a_loss_larger_than_money_epsilon_is_rejected():
    _, lot = _lot(buy_price=100.0, shares=1.0)
    with pytest.raises(NoLossViolation):
        validate_sell(lot, 1.0, 100.0 - 1e-4, ZeroCostModel())


def test_nominally_profitable_sell_rejected_once_costs_are_modeled():
    """The criterion that makes this guard necessary at all."""
    _, lot = _lot(buy_price=100.0, shares=10.0, profit_target=0.01)  # target 101.0

    # Zero cost: comfortably profitable.
    assert validate_sell(lot, 10.0, lot.target_sell_price, ZeroCostModel()).permitted

    # A $50 commission wipes out the $10 nominal gain.
    costly = SlippageCommissionModel(commission_per_trade=50.0, slippage_bps=0)
    with pytest.raises(NoLossViolation) as exc_info:
        validate_sell(lot, 10.0, lot.target_sell_price, costly)
    assert "sell costs" in str(exc_info.value)


def test_slippage_alone_can_turn_a_nominal_profit_into_a_rejection():
    _, lot = _lot(buy_price=100.0, shares=10.0, profit_target=0.01)  # target 101.0
    # 200bps of slippage against a 100bps nominal gain.
    slippery = SlippageCommissionModel(commission_per_trade=0.0, slippage_bps=200)
    with pytest.raises(NoLossViolation):
        validate_sell(lot, 10.0, lot.target_sell_price, slippery)


def test_costs_are_included_in_the_reported_economics():
    _, lot = _lot(buy_price=100.0, shares=10.0)
    economics = compute_sell_economics(
        lot, 10.0, 120.0, SlippageCommissionModel(commission_per_trade=5.0, slippage_bps=0)
    )
    assert economics.sell_costs == 5.0
    assert economics.net_sell_proceeds == pytest.approx(10.0 * 120.0 - 5.0)
    assert economics.realized_pnl == pytest.approx(1195.0 - 1000.0)


def test_partial_fill_allocates_cost_basis_proportionally():
    _, lot = _lot(buy_price=100.0, shares=10.0)
    economics = validate_sell(lot, 4.0, 110.0, ZeroCostModel())
    assert economics.quantity == 4.0
    assert economics.allocated_cost_basis == pytest.approx(400.0), "4 of 10 shares -> 40% of basis"
    assert economics.net_sell_proceeds == pytest.approx(440.0)
    assert economics.realized_pnl == pytest.approx(40.0)


def test_partial_fill_closes_only_the_filled_portion_and_never_marks_the_rest_realized():
    ledger, lot = _lot(buy_price=100.0, shares=10.0)
    economics = validate_sell(lot, 4.0, 110.0, ZeroCostModel())
    ledger.close_lot(lot, sell_qty=economics.quantity, execution_price=110.0)

    assert lot in ledger.open_lots, "The unsold remainder must stay open"
    assert lot.shares == pytest.approx(6.0)
    assert lot.buy_price == 100.0, "Remaining shares keep their original cost basis"
    # And the remainder's basis is exactly what was NOT realized.
    remaining = compute_sell_economics(lot, lot.shares, 110.0, ZeroCostModel())
    assert remaining.allocated_cost_basis == pytest.approx(600.0)
    assert economics.allocated_cost_basis + remaining.allocated_cost_basis == pytest.approx(1000.0)


def test_a_partial_fill_that_would_realize_a_loss_is_rejected():
    _, lot = _lot(buy_price=100.0, shares=10.0)
    with pytest.raises(NoLossViolation):
        validate_sell(lot, 4.0, 95.0, ZeroCostModel())


def test_selling_the_full_quantity_uses_the_whole_basis():
    _, lot = _lot(buy_price=100.0, shares=10.0)
    economics = compute_sell_economics(lot, 10.0, 110.0, ZeroCostModel())
    assert economics.allocated_cost_basis == pytest.approx(1000.0)


def test_only_one_no_loss_comparison_exists_in_the_codebase():
    """Scans src/ and the controller for a second copy of the formula.

    Two independent inline implementations existed before this task
    (optimization_controller._simulate_single and
    intraday_validation.simulate_single_intraday); both were folded
    into validate_sell. This test fails if one is ever reintroduced.
    """
    comparison = re.compile(r"net_sell_proceeds\s*<\s*allocated_cost_basis")
    offenders = []
    for path in list((REPO_ROOT / "src").glob("*.py")) + [REPO_ROOT / "optimization_controller.py"]:
        if path.name == "no_loss_guard.py":
            continue  # the one legitimate home
        if comparison.search(path.read_text()):
            offenders.append(path.name)
    assert offenders == [], f"Duplicate no-loss comparison found in: {offenders}"


def test_both_former_inline_sites_now_call_the_guard():
    for filename in ("optimization_controller.py", "src/intraday_validation.py"):
        source = (REPO_ROOT / filename).read_text()
        assert "validate_sell(" in source, f"{filename} no longer calls the canonical guard"


def test_the_guard_uses_the_canonical_formulas():
    # net_sell_proceeds = qty * effective_price - sell_costs
    # allocated_cost_basis = buy_price * qty (proportional)
    _, lot = _lot(buy_price=100.0, shares=10.0)
    model = SlippageCommissionModel(commission_per_trade=3.0, slippage_bps=100)
    economics = compute_sell_economics(lot, 5.0, 200.0, model)

    effective_price, sell_costs = model.apply_sell(200.0, 5.0)
    assert economics.net_sell_proceeds == pytest.approx(5.0 * effective_price - sell_costs)
    assert economics.allocated_cost_basis == pytest.approx(100.0 * 5.0)
    assert economics.realized_pnl == pytest.approx(
        economics.net_sell_proceeds - economics.allocated_cost_basis
    )


def test_guard_is_pure_and_mutates_nothing():
    """Purity is what lets every exit path share one guard safely."""
    ledger, lot = _lot(buy_price=100.0, shares=10.0)
    before = (lot.shares, lot.buy_price, lot.target_sell_price, len(ledger.open_lots))

    compute_sell_economics(lot, 4.0, 110.0, ZeroCostModel())
    with pytest.raises(NoLossViolation):
        validate_sell(lot, 4.0, 50.0, ZeroCostModel())

    assert (lot.shares, lot.buy_price, lot.target_sell_price, len(ledger.open_lots)) == before


def test_a_rejected_sell_leaves_the_lot_fully_intact():
    ledger, lot = _lot(buy_price=100.0, shares=10.0)
    with pytest.raises(NoLossViolation):
        validate_sell(lot, 10.0, 50.0, ZeroCostModel())
    assert lot in ledger.open_lots
    assert lot.shares == 10.0


def test_no_operational_module_can_force_a_loss_making_sell():
    """Circuit breaker, shutdown, and reconciliation each expose no
    liquidation path at all -- so there is nothing that could bypass
    this guard even if it wanted to."""
    from src.reconciliation import Reconciler
    from src.risk_manager import CircuitBreaker
    from src.runtime_lifecycle import RuntimeLifecycle

    forbidden = ("liquidate", "close_all", "emergency_sell", "flatten", "force_exit", "force_sell")
    for obj in (CircuitBreaker(), RuntimeLifecycle(), Reconciler(store=None)):
        for name in forbidden:
            assert not hasattr(obj, name), (
                f"{type(obj).__name__} exposes {name!r} -- an operational path must never be able "
                "to create an intentional loss-making sell"
            )


def test_no_loss_violation_is_distinguishable_from_execution_failure():
    # Callers handle "this exit is forbidden" very differently from
    # "the broker failed".
    assert issubclass(NoLossViolation, ExecutionError)
    assert NoLossViolation is not ExecutionError


@pytest.mark.parametrize("quantity", [0.0, -1.0])
def test_non_positive_quantity_rejected(quantity):
    _, lot = _lot()
    with pytest.raises(ValueError):
        validate_sell(lot, quantity, 110.0, ZeroCostModel())


@pytest.mark.parametrize("price", [0.0, -1.0])
def test_non_positive_price_rejected(price):
    _, lot = _lot()
    with pytest.raises(ValueError):
        validate_sell(lot, 1.0, price, ZeroCostModel())


def test_sell_economics_is_immutable():
    import dataclasses

    _, lot = _lot()
    economics = compute_sell_economics(lot, 1.0, 110.0, ZeroCostModel())
    assert isinstance(economics, SellEconomics)
    with pytest.raises(dataclasses.FrozenInstanceError):
        economics.realized_pnl = 999.0


def test_volatility_aware_cost_model_is_supported_at_the_guard():
    from datetime import datetime, timezone

    from src.cost_models import DynamicSlippageModel
    from src.market_context import MarketContext

    _, lot = _lot(buy_price=100.0, shares=10.0)
    context = MarketContext(
        timestamp=datetime(2024, 1, 1, tzinfo=timezone.utc),
        open=105.0, high=105.0, low=105.0, close=105.0,
        cash=0.0, equity=0.0, peak_equity=0.0, drawdown=0.0,
        open_lot_count=1, bar_index=0,
    )
    model = DynamicSlippageModel(base_bps=5.0, vol_multiplier=1.0)

    calm = compute_sell_economics(lot, 10.0, 110.0, model, context=context, prev_close=104.9)
    volatile = compute_sell_economics(lot, 10.0, 110.0, model, context=context, prev_close=100.0)
    assert volatile.net_sell_proceeds < calm.net_sell_proceeds, (
        "A volatile bar must reduce net proceeds through the guard, not bypass the cost model"
    )
