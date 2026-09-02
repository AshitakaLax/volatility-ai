"""
The Fidelity adapter. No network, no browser, no account.

Weighted heavily toward the negative cases. This is the module that
would spend real money if it were wrong, and the two things it must
never do -- place an order, or act on the wrong account -- are each
pinned from more than one direction, because a single mechanism is a
single point of failure.

Payload shapes here are TRANSCRIBED FROM REAL CAPTURES (2026-09-02),
not invented. A fixture shaped to my assumption rather than to the
venue is how 49 green tests once missed a broken import path in this
same subsystem.
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

from src import fidelity_broker
from src.exceptions import ConfigurationError, ExecutionError
from src.fidelity_broker import (
    PREVIEW_PATH,
    FidelityBroker,
    FidelityOrder,
    derive_order_state,
)
from src.fidelity_session import PLACE_ENDPOINTS, FidelitySession
from src.order_lifecycle import OrderState

ACCOUNT = "231930409"
OTHER = "999999999"

# --- real captured order records --------------------------------------

FILLED = {
    "orderNum": "2C50H6WV", "acctNum": ACCOUNT, "symbol": "TQQQ", "action": "Sell",
    "quantity": "1 Share", "status": "Filled at $69.35", "cancelableInd": False,
    "orderType": "stock/etf", "tifCode": "D",
    "amountDetail": {"avgExecPrice": 69.35, "commission": 0, "gross": 69.35,
                     "net": 69.35, "qty": 1, "qtyExec": 1, "qtyRemaining": 0,
                     "totalPriceImprovement": 0.01},
}
WORKING = {
    "orderNum": "2C50H81C", "acctNum": ACCOUNT, "symbol": "TQQQ", "action": "Buy",
    "quantity": "1 Share", "status": "Open", "cancelableInd": True,
    "amountDetail": {"qty": 1, "qtyExec": 0, "qtyRemaining": 1, "avgExecPrice": 0},
}
CANCELED = {
    "orderNum": "2C50JKCQ", "acctNum": ACCOUNT, "symbol": "TQQQ", "action": "Buy",
    "quantity": "1 Share", "status": "Verified Canceled", "cancelableInd": False,
    "amountDetail": {"qty": 1, "qtyExec": 0, "qtyRemaining": 1, "avgExecPrice": 0},
}
PARTIAL = {
    "orderNum": "2C50PART", "acctNum": ACCOUNT, "symbol": "TQQQ", "action": "Buy",
    "quantity": "10 Shares", "status": "Filled at $69.10", "cancelableInd": True,
    "amountDetail": {"qty": 10, "qtyExec": 4, "qtyRemaining": 6, "avgExecPrice": 69.10},
}


class FakeSession:
    """Records what was asked for and replays canned JSON."""

    def __init__(self, responses=None, refuse=()):
        self.responses = responses or {}
        self.refuse = set(refuse)
        self.calls = []

    def post_json(self, path, payload):
        self.calls.append((path, payload))
        if path in self.refuse:
            raise ConfigurationError(f"{path} refused by the transport gate")
        value = self.responses.get(path, {})
        return value(payload) if callable(value) else value

    def assert_authenticated(self):
        return None


def _broker(session=None, account=ACCOUNT, allowed=(ACCOUNT,)):
    return FidelityBroker(session or FakeSession(), account, allowed)


def _pending(orders):
    return {"data": {"orders": list(orders)}}


# ======================================================================
# It cannot place an order
# ======================================================================


def test_no_string_constant_in_the_module_names_a_place_endpoint():
    """Structural: the capability must be ABSENT, not defaulted off.

    Mirrors test_no_source_path_can_set_dry_false for fidelity_recon.py,
    but via the AST rather than a line grep. A grep matched this module's
    own DOCSTRING, which explains at length why it does not place orders
    -- so the first version of this test failed on the prose describing
    the very property it was checking. Docstrings are excluded and every
    other string constant is inspected, which is what "no code path can
    reach placeOrder" actually means.
    """
    tree = ast.parse(Path("src/fidelity_broker.py").read_text(encoding="utf-8"))
    docstrings = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef)):
            doc = ast.get_docstring(node, clean=False)
            if doc is not None:
                docstrings.add(doc)
    offenders = [
        node.value for node in ast.walk(tree)
        if isinstance(node, ast.Constant) and isinstance(node.value, str)
        and node.value not in docstrings
        and ("placeOrder" in node.value or "cancelPlaceOrder" in node.value)
    ]
    assert offenders == [], f"a place endpoint is reachable as a literal: {offenders}"


def test_no_endpoint_constant_resolves_to_a_place_endpoint():
    """The same guarantee from the other direction: whatever paths this
    module can POST to, none of them place an order."""
    paths = {
        v for k, v in vars(fidelity_broker).items()
        if k.endswith("_PATH") and isinstance(v, str)
    }
    assert paths and not (paths & PLACE_ENDPOINTS)


@pytest.mark.parametrize("path", sorted(PLACE_ENDPOINTS))
def test_the_transport_refuses_placing_even_if_this_module_tried(path):
    """The guarantee does not rest on the adapter behaving.

    A preview-only FidelitySession refuses the place endpoints outright,
    so even a bug here cannot submit.
    """
    session = FidelitySession(object(), allow_preview_endpoints=True)
    with pytest.raises(ConfigurationError, match="PLACES OR CANCELS A REAL ORDER"):
        session.post_json(path, {})


def test_a_previewed_order_is_never_reported_as_submitted():
    """Third layer. A caller that ignored everything above still cannot
    mistake a preview for a live order."""
    session = FakeSession({
        "/ftgw/digital/trade-equity/getquote": {"lastPrice": 69.50},
        PREVIEW_PATH: {"preview": {"orderConfirmDetail": {"confNum": "2C50QMK4"}}},
    })
    order = _broker(session).submit_buy("TQQQ", 200.0, client_order_id="dec-1")
    assert order.state is OrderState.CREATED
    assert order.state is not OrderState.SUBMITTED
    assert order.status == "CREATED"


def test_a_preview_without_a_confnum_is_a_failure_not_a_success():
    """The confNum is the only handle by which the order could later be
    found or cancelled. Accepting a preview without one would recreate
    the ambiguity window reconnaissance closed."""
    session = FakeSession({
        "/ftgw/digital/trade-equity/getquote": {"lastPrice": 69.50},
        PREVIEW_PATH: {"preview": {"ok": True}},
    })
    with pytest.raises(ExecutionError, match="no confNum"):
        _broker(session).submit_buy("TQQQ", 200.0)


# ======================================================================
# It cannot act on the wrong account
# ======================================================================


def test_an_account_outside_the_allowlist_is_refused_before_any_request():
    session = FakeSession()
    with pytest.raises(ConfigurationError, match="allowed_accounts"):
        FidelityBroker(session, OTHER, (ACCOUNT,))
    assert session.calls == [], "refused before touching the network"


def test_an_empty_allowlist_permits_nothing():
    """Empty means 'nothing is permitted', never 'everything is'."""
    with pytest.raises(ConfigurationError, match="empty"):
        FidelityBroker(FakeSession(), ACCOUNT, ())


def test_a_substring_of_an_allowed_account_is_not_enough():
    """The library this replaces matched accounts by case-insensitive
    SUBSTRING against a dropdown. Only exact equality is accepted."""
    for candidate in ("2319304", "31930409", "231930409X", "231930409 "):
        with pytest.raises(ConfigurationError):
            FidelityBroker(FakeSession(), candidate, (ACCOUNT,))


def test_an_account_echoed_back_differently_aborts_the_order():
    """The request naming the right account is not proof the venue
    applied it."""
    session = FakeSession({
        "/ftgw/digital/trade-equity/getquote": {"lastPrice": 69.50},
        PREVIEW_PATH: {"preview": {"orderConfirmDetail": {
            "confNum": "2C50QMK4", "acctNum": OTHER}}},
    })
    with pytest.raises(ExecutionError, match="DIFFERENT account"):
        _broker(session).submit_buy("TQQQ", 200.0)


def test_orders_belonging_to_another_account_are_dropped_from_the_snapshot():
    stray = dict(FILLED, orderNum="2C5OTHER", acctNum=OTHER)
    session = FakeSession({
        "/ftgw/digital/activityapi/api/v1/transactions/pending": _pending([FILLED, stray]),
        "/ftgw/digital/traderplus-api/api/positions/v1": {},
        "/ftgw/digital/trade-equity/balance": {"cashDetail": {"settledAmt": 1000.0}},
    })
    snap = _broker(session).snapshot()
    assert set(snap.orders) == {"2C50H6WV"}


# ======================================================================
# The status trap
# ======================================================================


@pytest.mark.parametrize(
    "record,expected",
    [
        (WORKING, OrderState.ACCEPTED),
        (FILLED, OrderState.FILLED),
        (CANCELED, OrderState.CANCELED),
        (PARTIAL, OrderState.PARTIALLY_FILLED),
    ],
)
def test_state_comes_from_the_structured_fields(record, expected):
    assert derive_order_state(record) is expected


def test_the_prose_status_is_never_what_decides():
    """The headline finding. Fidelity interpolates the fill price into
    `status` ("Filled at $69.335"), so no exact-match table can cover it.
    An order with a status string this code has never seen still resolves
    correctly, because amountDetail carries the truth."""
    weird = dict(FILLED, status="Executed — see confirmation for details")
    assert derive_order_state(weird) is OrderState.FILLED

    blank = dict(WORKING, status="")
    assert derive_order_state(blank) is OrderState.ACCEPTED


def test_a_partially_filled_order_that_is_cancelled_keeps_its_fill():
    """Reporting it CANCELED would lose shares that really executed."""
    record = dict(PARTIAL, cancelableInd=False, status="Verified Canceled")
    assert derive_order_state(record) is OrderState.PARTIALLY_FILLED


def test_an_unrecognisable_terminal_order_is_unknown_not_guessed():
    record = {"orderNum": "X", "status": "Something New", "cancelableInd": False,
              "amountDetail": {"qty": 1, "qtyExec": 0, "qtyRemaining": 1}}
    assert derive_order_state(record) is OrderState.UNKNOWN


def test_cancelableind_as_the_string_False_is_not_truthy():
    """This API returns cancelableInd as a real bool in one place and the
    STRING 'False' in another, and bool('False') is True."""
    # The string "True" must read as cancelable...
    assert derive_order_state(dict(WORKING, cancelableInd="True")) is OrderState.ACCEPTED
    # ...and the string "False" must not, which the built-in would get wrong.
    assert derive_order_state(dict(CANCELED, cancelableInd="False")) is OrderState.CANCELED


def test_an_order_claiming_Open_while_not_cancelable_is_unknown():
    """Not a contrived case -- it is what a stale or partial payload looks
    like, and the two fields genuinely contradict each other. UNKNOWN
    forces reconciliation instead of picking whichever field to believe.
    """
    contradictory = dict(WORKING, cancelableInd=False, status="Open")
    assert derive_order_state(contradictory) is OrderState.UNKNOWN


# ======================================================================
# Notional -> shares
# ======================================================================


def test_share_conversion_rounds_down_so_it_cannot_overspend():
    session = FakeSession({
        "/ftgw/digital/trade-equity/getquote": {"lastPrice": 69.50},
        PREVIEW_PATH: {"preview": {"orderConfirmDetail": {"confNum": "C1"}}},
    })
    _broker(session).submit_buy("TQQQ", 209.0)  # 209/69.50 = 3.007
    ticket = session.calls[-1][1]["orderDetails"]
    assert ticket["qty"] == 3
    assert ticket["qty"] * 69.50 <= 209.0


def test_a_trade_value_under_one_share_refuses_rather_than_rounding_to_zero():
    session = FakeSession({
        "/ftgw/digital/trade-equity/getquote": {"lastPrice": 69.50},
    })
    with pytest.raises(ExecutionError, match="one whole share"):
        _broker(session).submit_buy("TQQQ", 40.0)


def test_a_quote_this_code_had_to_guess_at_is_refused():
    session = FakeSession({"/ftgw/digital/trade-equity/getquote": {"unrelated": 1}})
    with pytest.raises(ExecutionError, match="No usable price"):
        _broker(session).submit_buy("TQQQ", 200.0)


def test_every_ticket_carries_an_explicit_limit_price():
    """Extended hours cannot be disabled at this venue, which forces the
    limit branch -- and a market order in a thin session is the one thing
    a grid strategy must never emit."""
    session = FakeSession({
        "/ftgw/digital/trade-equity/getquote": {"lastPrice": 69.50},
        PREVIEW_PATH: {"preview": {"orderConfirmDetail": {"confNum": "C1"}}},
    })
    broker = _broker(session)
    broker.submit_buy("TQQQ", 200.0)
    broker.submit_sell("TQQQ", 2, 71.25)
    for path, payload in session.calls:
        if path != PREVIEW_PATH:
            continue
        assert payload["orderDetails"]["priceTypeCode"] == "L"
        assert payload["orderDetails"]["limitPrice"] > 0


# ======================================================================
# Reconciliation surface
# ======================================================================


def test_snapshot_feeds_the_reconciler_without_adaptation():
    session = FakeSession({
        "/ftgw/digital/activityapi/api/v1/transactions/pending":
            _pending([FILLED, WORKING, PARTIAL]),
        "/ftgw/digital/traderplus-api/api/positions/v1":
            {"positions": [{"symbol": "TQQQ", "quantity": 12.0, "acctNum": ACCOUNT}]},
        "/ftgw/digital/trade-equity/balance": {"cashDetail": {"settledAmt": 4321.55}},
    })
    snap = _broker(session).snapshot()
    assert snap.positions == {"TQQQ": 12.0}
    assert snap.cash == 4321.55
    assert snap.orders["2C50H6WV"]["state"] is OrderState.FILLED
    assert snap.orders["2C50H6WV"]["avg_fill_price"] == 69.35
    assert snap.orders["2C50PART"]["filled_qty"] == 4


def test_cash_prefers_settled_because_this_is_a_cash_account():
    """Proceeds settle T+1 here, so unsettled cash is visible in the
    account and is NOT tradeable without a good-faith violation."""
    session = FakeSession({
        "/ftgw/digital/activityapi/api/v1/transactions/pending": _pending([]),
        "/ftgw/digital/traderplus-api/api/positions/v1": {},
        "/ftgw/digital/trade-equity/balance": {
            "cash": 9999.99, "cashDetail": {"settledAmt": 100.00}},
    })
    assert _broker(session).snapshot().cash == 100.00


def test_an_order_is_findable_by_our_decision_id_after_preview():
    """Fidelity has no client-reference field, so the decision_id ->
    confNum map is written at PREVIEW time -- before anything could be
    committed, so it is never a guess made after the fact."""
    session = FakeSession({
        "/ftgw/digital/trade-equity/getquote": {"lastPrice": 69.50},
        PREVIEW_PATH: {"preview": {"orderConfirmDetail": {"confNum": "2C50H6WV"}}},
        "/ftgw/digital/activityapi/api/v1/transactions/pending": _pending([FILLED]),
    })
    broker = _broker(session)
    assert broker.get_order_by_client_id("dec-9") is None
    broker.submit_buy("TQQQ", 200.0, client_order_id="dec-9")
    found = broker.get_order_by_client_id("dec-9")
    assert isinstance(found, FidelityOrder)
    assert found.id == "2C50H6WV"
    assert found.state is OrderState.FILLED
    assert found.filled_avg_price == 69.35


def test_an_order_placed_by_hand_still_appears_in_the_snapshot():
    """Keyed by confNum rather than dropped. Reconciliation should SEE an
    unrecognised order, not have it silently hidden."""
    session = FakeSession({
        "/ftgw/digital/activityapi/api/v1/transactions/pending": _pending([WORKING]),
        "/ftgw/digital/traderplus-api/api/positions/v1": {},
        "/ftgw/digital/trade-equity/balance": {},
    })
    snap = _broker(session).snapshot()
    assert "2C50H81C" in snap.orders


def test_a_missing_balance_is_none_rather_than_zero():
    """Zero cash and unknown cash are completely different facts to
    reconcile against."""
    session = FakeSession({
        "/ftgw/digital/activityapi/api/v1/transactions/pending": _pending([]),
        "/ftgw/digital/traderplus-api/api/positions/v1": {},
        "/ftgw/digital/trade-equity/balance": {},
    })
    assert _broker(session).snapshot().cash is None
