"""
Task 7.10 acceptance tests.

Acceptance criteria:
1. Every broker status used by the implementation maps to one
   canonical internal state.
2. Invalid transitions are rejected without mutating accounting.
3. Partial-fill transitions preserve remaining quantity.
4. The transition table is ENFORCED, not just described in a comment.
"""

import pytest

from src.exceptions import ExecutionError
from src.order_lifecycle import (
    ALLOWED_TRANSITIONS,
    TERMINAL_STATES,
    OrderRecord,
    OrderState,
    map_broker_status,
)


def _order(**overrides) -> OrderRecord:
    base = dict(client_order_id="cid-1", requested_qty=10.0, symbol="TQQQ")
    base.update(overrides)
    return OrderRecord(**base)


def _accepted_order(**overrides) -> OrderRecord:
    order = _order(**overrides)
    order.transition_to(OrderState.SUBMITTED)
    order.transition_to(OrderState.ACCEPTED)
    return order


def test_every_real_alpaca_status_maps_to_a_canonical_state():
    """Enumerates the installed SDK's actual enum -- so a future
    alpaca-py adding a status makes this fail loudly rather than
    silently falling through to UNKNOWN in production."""
    from alpaca.trading.enums import OrderStatus

    unmapped = []
    for status in OrderStatus:
        if map_broker_status(status) is OrderState.UNKNOWN:
            unmapped.append(status.value)
    assert unmapped == [], f"Broker statuses with no canonical mapping: {unmapped}"


def test_all_eighteen_alpaca_statuses_are_covered():
    from alpaca.trading.enums import OrderStatus

    assert len(list(OrderStatus)) == 18, "SDK status count changed -- re-verify the mapping table"
    for status in OrderStatus:
        assert isinstance(map_broker_status(status), OrderState)


@pytest.mark.parametrize(
    "broker_status,expected",
    [
        ("pending_new", OrderState.SUBMITTED),
        ("new", OrderState.ACCEPTED),
        ("accepted", OrderState.ACCEPTED),
        ("partially_filled", OrderState.PARTIALLY_FILLED),
        ("filled", OrderState.FILLED),
        ("canceled", OrderState.CANCELED),
        ("expired", OrderState.EXPIRED),
        ("rejected", OrderState.REJECTED),
        ("replaced", OrderState.CANCELED),
    ],
)
def test_representative_status_mappings(broker_status, expected):
    assert map_broker_status(broker_status) is expected


def test_ambiguous_statuses_map_to_non_terminal_states():
    # Safety principle: a wrongly-terminal mapping loses track of live
    # exposure; a wrongly-working one only costs a redundant query.
    for ambiguous in (
        "held",
        "stopped",
        "suspended",
        "calculated",
        "done_for_day",
        "pending_cancel",
    ):
        assert map_broker_status(ambiguous) not in TERMINAL_STATES


def test_unrecognized_status_maps_to_unknown_not_a_guess():
    assert map_broker_status("some_future_status") is OrderState.UNKNOWN


def test_status_mapping_is_case_insensitive_and_accepts_enums():
    from alpaca.trading.enums import OrderStatus

    assert map_broker_status("FILLED") is OrderState.FILLED
    assert map_broker_status(OrderStatus.FILLED) is OrderState.FILLED


def test_the_specified_transition_table_is_implemented_exactly():
    assert ALLOWED_TRANSITIONS[OrderState.CREATED] == {OrderState.SUBMITTED}
    assert ALLOWED_TRANSITIONS[OrderState.SUBMITTED] == {
        OrderState.ACCEPTED,
        OrderState.REJECTED,
        OrderState.UNKNOWN,
    }
    assert ALLOWED_TRANSITIONS[OrderState.ACCEPTED] == {
        OrderState.PARTIALLY_FILLED,
        OrderState.FILLED,
        OrderState.CANCELED,
        OrderState.EXPIRED,
    }
    assert ALLOWED_TRANSITIONS[OrderState.PARTIALLY_FILLED] == {
        OrderState.PARTIALLY_FILLED,
        OrderState.FILLED,
        OrderState.CANCELED,
    }


def test_every_terminal_state_has_no_outgoing_transitions():
    for state in TERMINAL_STATES:
        assert ALLOWED_TRANSITIONS[state] == frozenset()


def test_the_happy_path_walks_the_table():
    order = _order()
    assert order.state is OrderState.CREATED
    order.transition_to(OrderState.SUBMITTED)
    order.transition_to(OrderState.ACCEPTED)
    order.transition_to(OrderState.PARTIALLY_FILLED)
    order.transition_to(OrderState.FILLED)
    assert order.is_terminal


@pytest.mark.parametrize(
    "from_state,to_state",
    [
        (OrderState.CREATED, OrderState.ACCEPTED),  # skips SUBMITTED
        (OrderState.CREATED, OrderState.FILLED),  # skips everything
        (OrderState.SUBMITTED, OrderState.FILLED),  # skips ACCEPTED
        (OrderState.SUBMITTED, OrderState.PARTIALLY_FILLED),
        (OrderState.ACCEPTED, OrderState.SUBMITTED),  # backwards
        (OrderState.ACCEPTED, OrderState.REJECTED),  # not in the table
        (OrderState.PARTIALLY_FILLED, OrderState.ACCEPTED),  # backwards
        (OrderState.PARTIALLY_FILLED, OrderState.EXPIRED),  # not in the table
    ],
)
def test_transitions_absent_from_the_table_are_rejected(from_state, to_state):
    order = _order()
    order.state = from_state
    with pytest.raises(ExecutionError, match="Invalid order transition"):
        order.transition_to(to_state)


@pytest.mark.parametrize("terminal", sorted(TERMINAL_STATES, key=lambda s: s.value))
def test_terminal_states_reject_every_further_transition(terminal):
    for target in OrderState:
        order = _order()
        order.state = terminal
        with pytest.raises(ExecutionError):
            order.transition_to(target)


def test_invalid_transition_leaves_all_accounting_untouched():
    order = _accepted_order()
    order.apply_broker_update("partially_filled", filled_qty=4.0, avg_fill_price=150.0)

    snapshot = (
        order.state,
        order.filled_qty,
        order.avg_fill_price,
        order.remaining_qty,
        order.requested_qty,
        order.broker_order_id,
    )

    with pytest.raises(ExecutionError):
        order.transition_to(OrderState.EXPIRED)  # not allowed from PARTIALLY_FILLED

    assert (
        order.state,
        order.filled_qty,
        order.avg_fill_price,
        order.remaining_qty,
        order.requested_qty,
        order.broker_order_id,
    ) == snapshot


def test_invalid_broker_update_does_not_record_its_quantities():
    order = _accepted_order()
    order.apply_broker_update("partially_filled", filled_qty=4.0, avg_fill_price=150.0)

    with pytest.raises(ExecutionError):
        # expired is not reachable from PARTIALLY_FILLED
        order.apply_broker_update("expired", filled_qty=99.0, avg_fill_price=999.0)

    assert order.filled_qty == 4.0, "A rejected update must not write its quantities"
    assert order.avg_fill_price == 150.0


def test_partial_fill_preserves_remaining_quantity():
    order = _accepted_order(requested_qty=10.0)
    order.apply_broker_update("partially_filled", filled_qty=4.0, avg_fill_price=150.0)
    assert order.filled_qty == 4.0
    assert order.remaining_qty == 6.0
    assert order.requested_qty == 10.0, "Requested quantity is never rewritten by a fill"


def test_successive_partial_fills_track_remaining_quantity():
    order = _accepted_order(requested_qty=10.0)
    for cumulative, expected_remaining in ((4.0, 6.0), (7.0, 3.0), (9.0, 1.0)):
        order.apply_broker_update("partially_filled", filled_qty=cumulative)
        assert order.state is OrderState.PARTIALLY_FILLED
        assert order.remaining_qty == expected_remaining


def test_full_fill_leaves_zero_remaining():
    order = _accepted_order(requested_qty=10.0)
    order.apply_broker_update("partially_filled", filled_qty=4.0)
    order.apply_broker_update("filled", filled_qty=10.0, avg_fill_price=151.0)
    assert order.state is OrderState.FILLED
    assert order.remaining_qty == 0.0


def test_remaining_quantity_never_goes_negative():
    # An over-reporting broker is a reconciliation problem, not a
    # reason to hand downstream sizing a negative remainder.
    order = _accepted_order(requested_qty=10.0)
    order.apply_broker_update("partially_filled", filled_qty=12.0)
    assert order.remaining_qty == 0.0


def test_cancel_after_partial_fill_keeps_the_filled_quantity():
    order = _accepted_order(requested_qty=10.0)
    order.apply_broker_update("partially_filled", filled_qty=4.0, avg_fill_price=150.0)
    order.apply_broker_update("canceled")
    assert order.state is OrderState.CANCELED
    assert order.filled_qty == 4.0, "A cancel must not erase quantity already filled"


def test_unknown_cannot_be_escaped_by_an_ordinary_transition():
    order = _order()
    order.transition_to(OrderState.SUBMITTED)
    order.transition_to(OrderState.UNKNOWN)
    for target in OrderState:
        with pytest.raises(ExecutionError):
            order.transition_to(target)


def test_unknown_resolves_only_with_an_explicit_resolution_source():
    order = _order()
    order.transition_to(OrderState.SUBMITTED)
    order.transition_to(OrderState.UNKNOWN)

    for bad in ("", "   ", None):
        with pytest.raises(ExecutionError, match="resolution_source"):
            order.resolve_from_unknown(OrderState.FILLED, resolution_source=bad)
    assert order.state is OrderState.UNKNOWN

    order.resolve_from_unknown(OrderState.FILLED, resolution_source="broker get_order_by_client_id")
    assert order.state is OrderState.FILLED


def test_resolve_from_unknown_is_rejected_from_any_other_state():
    order = _accepted_order()
    with pytest.raises(ExecutionError, match="only valid from UNKNOWN"):
        order.resolve_from_unknown(OrderState.FILLED, resolution_source="query")


def test_duplicate_broker_update_is_idempotent_not_an_error():
    order = _accepted_order()
    order.apply_broker_update("filled", filled_qty=10.0, avg_fill_price=150.0)
    order.apply_broker_update("filled", filled_qty=10.0, avg_fill_price=150.0)  # replay
    assert order.state is OrderState.FILLED
    assert order.filled_qty == 10.0


def test_all_step_four_fields_are_separate():
    order = _order(requested_qty=10.0)
    order.transition_to(OrderState.SUBMITTED)
    order.transition_to(OrderState.ACCEPTED)
    order.apply_broker_update(
        "partially_filled", filled_qty=4.0, avg_fill_price=150.0, broker_order_id="brk-99"
    )
    assert order.requested_qty == 10.0
    assert order.filled_qty == 4.0
    assert order.remaining_qty == 6.0
    assert order.avg_fill_price == 150.0
    assert order.client_order_id == "cid-1"
    assert order.broker_order_id == "brk-99"
    assert order.created_at is not None
    assert order.submitted_at is not None
    assert order.last_update_at is not None


def test_timestamps_are_utc_aware():
    order = _order()
    order.transition_to(OrderState.SUBMITTED)
    assert order.created_at.tzinfo is not None
    assert order.submitted_at.tzinfo is not None


def test_submitted_at_is_recorded_once_not_overwritten():
    order = _order()
    order.transition_to(OrderState.SUBMITTED)
    first = order.submitted_at
    order.transition_to(OrderState.ACCEPTED)
    assert order.submitted_at == first


# --- idempotence on canonical states ---
#
# An adapter that already speaks canonical states hands this function a
# value it produced. src/fidelity_broker.FidelityOrder.status does,
# because Fidelity's own status field is prose with the fill price
# interpolated into it ("Filled at $69.335").


@pytest.mark.parametrize("state", list(OrderState))
def test_every_canonical_state_round_trips(state):
    """Six of nine used to survive by coincidence -- Alpaca's vocabulary
    happens to overlap the enum names -- while CREATED, SUBMITTED and
    UNKNOWN did not. A live Fidelity order in CREATED or SUBMITTED
    mapped to UNKNOWN, which is not terminal, so the loop polled it
    forever and warned on every tick."""
    assert map_broker_status(str(state)) is state
    assert map_broker_status(state) is state


@pytest.mark.parametrize("state", list(OrderState))
def test_mapping_is_stable_under_repetition(state):
    """f(f(x)) == f(x). Anything else means a value can degrade each
    time it passes through a layer."""
    once = map_broker_status(str(state))
    assert map_broker_status(once) is once


def test_the_alpaca_vocabulary_still_maps():
    """The canonical shortcut must not shadow real venue strings."""
    assert map_broker_status("pending_new") is OrderState.SUBMITTED
    assert map_broker_status("done_for_day") is OrderState.ACCEPTED
    assert map_broker_status("replaced") is OrderState.CANCELED


def test_a_genuinely_unrecognised_status_is_still_unknown():
    """Fidelity's raw prose must NOT be quietly accepted -- it carries
    the fill price and no exact-match table can cover it."""
    assert map_broker_status("Filled at $69.35") is OrderState.UNKNOWN
    assert map_broker_status("Verified Canceled") is OrderState.UNKNOWN
