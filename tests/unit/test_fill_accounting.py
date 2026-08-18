"""
Task 7.2 tests (L4): cumulative-to-incremental fill accounting.

Includes the task's REQUIRED "Cumulative-fill arithmetic fixture", and
documents the contradiction between it and the "Cumulative-fill
invariant" section, which states different numbers for the same input.
See src/fill_accounting.py's module docstring for the full resolution.
"""

import uuid
from datetime import datetime, timezone

import pytest

from src.exceptions import ReconciliationError
from src.fill_accounting import FillTracker, extract_alpaca_fill
from src.ledger import AssetLotLedger


def test_required_cumulative_fill_arithmetic_fixture():
    """The task's own 'Cumulative-fill arithmetic fixture'. The exact
    delta notionals 600 / 457 / 463 must be asserted."""
    tracker = FillTracker("order-1")

    d1 = tracker.apply_update(filled_qty=4, filled_avg_price=150)
    assert d1.qty == pytest.approx(4.0)
    assert d1.notional == pytest.approx(600.0)

    d2 = tracker.apply_update(filled_qty=7, filled_avg_price=151)
    assert d2.qty == pytest.approx(3.0)
    assert d2.notional == pytest.approx(457.0)

    d3 = tracker.apply_update(filled_qty=10, filled_avg_price=152)
    assert d3.qty == pytest.approx(3.0)
    assert d3.notional == pytest.approx(463.0)


def test_deltas_sum_to_the_final_cumulative_notional():
    """Independent correctness check, and the decisive evidence for
    which of the spec's two conflicting number sets is right.

    The task's 'Cumulative-fill invariant' section states the notionals
    as 600 / 453 / 456 for this same sequence. Those are exactly
    delta_qty * CUMULATIVE avg price (3*151, 3*152) -- the calculation
    the very next sentence of that same paragraph explicitly forbids --
    and they sum to 1509, losing $11 of a $1520 order. The fixture's
    600 / 457 / 463 sum correctly and match the spec's own stated
    formula. This test pins the correct behavior.
    """
    tracker = FillTracker("order-1")
    deltas = [
        tracker.apply_update(4, 150),
        tracker.apply_update(7, 151),
        tracker.apply_update(10, 152),
    ]
    total_notional = sum(d.notional for d in deltas)
    total_qty = sum(d.qty for d in deltas)

    assert total_qty == pytest.approx(10.0)
    assert total_notional == pytest.approx(10 * 152.0)  # 1520, the true cumulative
    assert total_notional != pytest.approx(1509.0)  # the invariant section's incorrect sum


def test_never_uses_delta_qty_times_cumulative_average():
    # The explicitly forbidden calculation would give 453 here.
    tracker = FillTracker("order-1")
    tracker.apply_update(4, 150)
    d2 = tracker.apply_update(7, 151)
    assert d2.notional != pytest.approx(3 * 151)
    assert d2.notional == pytest.approx(457.0)


def test_delta_avg_price_is_the_incremental_not_cumulative_price():
    tracker = FillTracker("order-1")
    tracker.apply_update(4, 150)
    d2 = tracker.apply_update(7, 151)
    # 457/3 = 152.33..., NOT the cumulative 151.
    assert d2.avg_price == pytest.approx(457.0 / 3.0)
    assert d2.avg_price != pytest.approx(151.0)


def test_repeated_identical_update_yields_an_empty_delta():
    # A duplicate broker message must not double-count.
    tracker = FillTracker("order-1")
    tracker.apply_update(4, 150)
    duplicate = tracker.apply_update(4, 150)
    assert duplicate.qty == 0.0
    assert duplicate.notional == 0.0
    assert duplicate.is_empty


def test_decreasing_cumulative_quantity_raises_reconciliation_error():
    tracker = FillTracker("order-1")
    tracker.apply_update(7, 151)
    with pytest.raises(ReconciliationError, match="decreased"):
        tracker.apply_update(4, 150)


def test_decreasing_cumulative_notional_raises_reconciliation_error():
    tracker = FillTracker("order-1")
    tracker.apply_update(10, 152)
    with pytest.raises(ReconciliationError, match="decreased"):
        tracker.apply_update(10, 100)  # same qty, lower avg -> notional dropped


def test_unfilled_order_yields_empty_delta():
    tracker = FillTracker("order-1")
    delta = tracker.apply_update(0, 0)
    assert delta.is_empty


def test_tracker_exposes_running_cumulative_state():
    tracker = FillTracker("order-1")
    tracker.apply_update(4, 150)
    assert tracker.cumulative_qty == pytest.approx(4.0)
    assert tracker.cumulative_notional == pytest.approx(600.0)


def _alpaca_order(filled_qty: str, filled_avg_price, status, qty: str = "10.0"):
    """Working equivalent of the task's specified mock.

    The task's literal blueprint --
      Order(id="test-123", status=..., qty="10.0", filled_qty="4.0",
            filled_avg_price="150.00", side=OrderSide.SELL)
    -- does NOT construct against the real alpaca-py SDK: verified
    directly, it raises 7 pydantic ValidationErrors (id must be a UUID,
    plus 6 required fields absent: client_order_id, created_at,
    updated_at, submitted_at, time_in_force, extended_hours). This
    preserves the blueprint's intent exactly (a PARTIALLY_FILLED sell,
    qty 10, filled 4 @ 150.00, id carried as client_order_id) while
    actually satisfying the SDK.
    """
    from alpaca.trading.enums import OrderSide, TimeInForce
    from alpaca.trading.models import Order

    now = datetime(2024, 1, 1, tzinfo=timezone.utc)
    return Order(
        id=str(uuid.UUID(int=123)),
        client_order_id="test-123",
        created_at=now, updated_at=now, submitted_at=now,
        status=status,
        qty=qty, filled_qty=filled_qty, filled_avg_price=filled_avg_price,
        side=OrderSide.SELL,
        time_in_force=TimeInForce.DAY,
        extended_hours=False,
    )


def test_extract_alpaca_fill_parses_string_fields_to_floats():
    from alpaca.trading.enums import OrderStatus

    order = _alpaca_order(filled_qty="4.0", filled_avg_price="150.00", status=OrderStatus.PARTIALLY_FILLED)
    filled_qty, filled_avg_price = extract_alpaca_fill(order)
    assert filled_qty == pytest.approx(4.0)
    assert filled_avg_price == pytest.approx(150.0)


def test_extract_alpaca_fill_handles_none_avg_price_before_first_fill():
    from alpaca.trading.enums import OrderStatus

    order = _alpaca_order(filled_qty="0", filled_avg_price=None, status=OrderStatus.NEW)
    filled_qty, filled_avg_price = extract_alpaca_fill(order)
    assert filled_qty == 0.0
    assert filled_avg_price == 0.0


def test_partial_sell_credits_cash_for_exactly_four_shares_and_leaves_six_open():
    """Task 7.2's stated acceptance criteria, using the specified
    4-of-10 partial fill."""
    from alpaca.trading.enums import OrderStatus

    ledger = AssetLotLedger()
    lot = ledger.register_buy("buy-1", "TQQQ", buy_price=100.0, shares=10.0, profit_target=0.5)

    order = _alpaca_order(filled_qty="4.0", filled_avg_price="150.00", status=OrderStatus.PARTIALLY_FILLED)
    filled_qty, filled_avg_price = extract_alpaca_fill(order)

    tracker = FillTracker("sell-1")
    delta = tracker.apply_update(filled_qty, filled_avg_price)

    cash = 0.0
    cash += delta.notional  # credit strictly by incremental fill notional
    ledger.close_lot(lot, sell_qty=delta.qty, execution_price=delta.avg_price)

    assert cash == pytest.approx(4 * 150.0), "Cash must be credited for exactly the 4 filled shares"
    assert lot in ledger.open_lots, "The lot must remain open"
    assert lot.shares == pytest.approx(6.0), "Remaining share count must be 6"


def test_simulation_full_close_call_site_still_works_unmodified():
    # Acceptance criterion 3: the original ledger.close_lot(lot) call
    # site must be unchanged and unbroken.
    ledger = AssetLotLedger()
    lot = ledger.register_buy("ord-1", "TQQQ", buy_price=40.0, shares=10.0, profit_target=0.01)
    ledger.close_lot(lot)
    assert lot not in ledger.open_lots
    assert lot in ledger.closed_lots
