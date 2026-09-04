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
    PENDING_PATH,
    PREVIEW_PATH,
    FidelityBroker,
    FidelityOrder,
    derive_order_state,
)
from src.fidelity_session import PLACE_ENDPOINTS, FidelitySession
from src.order_lifecycle import OrderState

# A DELIBERATELY FAKE account number. This was the operator's real
# Fidelity account until it was noticed that this repository is public,
# which put it in every clone and in GitHub's search index. An account
# number cannot move money on its own -- Fidelity needs an authenticated
# session for that -- but it is precisely the field an attacker would
# use to redirect an order or to sound legitimate to a support desk, and
# a test fixture never needed a real one.
ACCOUNT = "999888777"
OTHER = "999999999"

# --- real captured order records --------------------------------------

FILLED = {
    "orderNum": "2C50H6WV",
    "acctNum": ACCOUNT,
    "symbol": "TQQQ",
    "action": "Sell",
    "quantity": "1 Share",
    "status": "Filled at $69.35",
    "cancelableInd": False,
    "orderType": "stock/etf",
    "tifCode": "D",
    "amountDetail": {
        "avgExecPrice": 69.35,
        "commission": 0,
        "gross": 69.35,
        "net": 69.35,
        "qty": 1,
        "qtyExec": 1,
        "qtyRemaining": 0,
        "totalPriceImprovement": 0.01,
    },
}
WORKING = {
    "orderNum": "2C50H81C",
    "acctNum": ACCOUNT,
    "symbol": "TQQQ",
    "action": "Buy",
    "quantity": "1 Share",
    "status": "Open",
    "cancelableInd": True,
    "amountDetail": {"qty": 1, "qtyExec": 0, "qtyRemaining": 1, "avgExecPrice": 0},
}
CANCELED = {
    "orderNum": "2C50JKCQ",
    "acctNum": ACCOUNT,
    "symbol": "TQQQ",
    "action": "Buy",
    "quantity": "1 Share",
    "status": "Verified Canceled",
    "cancelableInd": False,
    "amountDetail": {"qty": 1, "qtyExec": 0, "qtyRemaining": 1, "avgExecPrice": 0},
}
PARTIAL = {
    "orderNum": "2C50PART",
    "acctNum": ACCOUNT,
    "symbol": "TQQQ",
    "action": "Buy",
    "quantity": "10 Shares",
    "status": "Filled at $69.10",
    "cancelableInd": True,
    "amountDetail": {"qty": 10, "qtyExec": 4, "qtyRemaining": 6, "avgExecPrice": 69.10},
}


# Fidelity's real quote payload: UPPER_SNAKE keys, STRING values,
# nested under QUOTE_DATA. Transcribed from a capture. The previous
# fixture used {"lastPrice": 69.50}, a shape that appears nowhere in
# Fidelity's responses -- so it agreed with the adapter's wrong guess
# and the pair of them hid a get_quote that could never work.
QUOTE = {
    "QUOTE_DATA": {
        "ASK_PRICE": "69.54",
        "BID_PRICE": "69.53",
        "LAST_PRICE": "69.5376",
        "OPEN_PRICE": "68.969",
    }
}

# trade-equity/positions returns a FLAT LIST already scoped to the
# requested account. SPAXX is the core money-market sweep and is CASH,
# not a holding -- it is in every real response and must not be counted.
SPAXX_ROW = {
    "symbol": "SPAXX",
    "securityType": "Core",
    "quantity": 27336.03,
    "securityDescription": "FIDELITY GOVERNMENT MONEY MARKET",
    "securityDetail": {"brokerageHoldingType": "Cash", "isCash": True},
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
        node.value
        for node in ast.walk(tree)
        if isinstance(node, ast.Constant)
        and isinstance(node.value, str)
        and node.value not in docstrings
        and ("placeOrder" in node.value or "cancelPlaceOrder" in node.value)
    ]
    assert offenders == [], f"a place endpoint is reachable as a literal: {offenders}"


def test_no_endpoint_constant_resolves_to_a_place_endpoint():
    """The same guarantee from the other direction: whatever paths this
    module can POST to, none of them place an order."""
    paths = {
        v for k, v in vars(fidelity_broker).items() if k.endswith("_PATH") and isinstance(v, str)
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
    session = FakeSession(
        {
            "/ftgw/digital/trade-equity/getquote": QUOTE,
            PREVIEW_PATH: {"preview": {"orderConfirmDetail": {"confNum": "2C50QMK4"}}},
        }
    )
    order = _broker(session).submit_buy("TQQQ", 200.0, client_order_id="dec-1")
    assert order.state is OrderState.CREATED
    assert order.state is not OrderState.SUBMITTED
    assert order.status == "CREATED"


def test_a_preview_without_a_confnum_is_a_failure_not_a_success():
    """The confNum is the only handle by which the order could later be
    found or cancelled. Accepting a preview without one would recreate
    the ambiguity window reconnaissance closed."""
    session = FakeSession(
        {
            "/ftgw/digital/trade-equity/getquote": QUOTE,
            PREVIEW_PATH: {"preview": {"ok": True}},
        }
    )
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
    for candidate in ("9998887", "99888777", "999888777X", "999888777 "):
        with pytest.raises(ConfigurationError):
            FidelityBroker(FakeSession(), candidate, (ACCOUNT,))


def test_an_account_echoed_back_differently_aborts_the_order():
    """The request naming the right account is not proof the venue
    applied it."""
    session = FakeSession(
        {
            "/ftgw/digital/trade-equity/getquote": QUOTE,
            PREVIEW_PATH: {
                "preview": {"orderConfirmDetail": {"confNum": "2C50QMK4", "acctNum": OTHER}}
            },
        }
    )
    with pytest.raises(ExecutionError, match="DIFFERENT account"):
        _broker(session).submit_buy("TQQQ", 200.0)


def test_orders_belonging_to_another_account_are_dropped_from_the_snapshot():
    stray = dict(FILLED, orderNum="2C5OTHER", acctNum=OTHER)
    session = FakeSession(
        {
            "/ftgw/digital/activityapi/api/v1/transactions/pending": _pending([FILLED, stray]),
            "/ftgw/digital/trade-equity/positions": [],
            "/ftgw/digital/trade-equity/balance": {"cashDetail": {"settledAmt": 1000.0}},
        }
    )
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
    record = {
        "orderNum": "X",
        "status": "Something New",
        "cancelableInd": False,
        "amountDetail": {"qty": 1, "qtyExec": 0, "qtyRemaining": 1},
    }
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
    session = FakeSession(
        {
            "/ftgw/digital/trade-equity/getquote": QUOTE,
            PREVIEW_PATH: {"preview": {"orderConfirmDetail": {"confNum": "C1"}}},
        }
    )
    _broker(session).submit_buy("TQQQ", 209.0)  # 209 / 69.54 (ASK) = 3.005
    ticket = session.calls[-1][1]["orderDetails"]
    assert ticket["qty"] == 3
    assert ticket["qty"] * 69.54 <= 209.0


def test_a_trade_value_under_one_share_refuses_rather_than_rounding_to_zero():
    session = FakeSession(
        {
            "/ftgw/digital/trade-equity/getquote": QUOTE,
        }
    )
    with pytest.raises(ValueError, match="one whole share"):
        _broker(session).submit_buy("TQQQ", 40.0)


def test_a_quote_this_code_had_to_guess_at_is_refused():
    session = FakeSession({"/ftgw/digital/trade-equity/getquote": {"unrelated": 1}})
    with pytest.raises(ExecutionError, match="No usable price"):
        _broker(session).submit_buy("TQQQ", 200.0)


def test_every_ticket_carries_an_explicit_limit_price():
    """Extended hours cannot be disabled at this venue, which forces the
    limit branch -- and a market order in a thin session is the one thing
    a grid strategy must never emit."""
    session = FakeSession(
        {
            "/ftgw/digital/trade-equity/getquote": QUOTE,
            PREVIEW_PATH: {"preview": {"orderConfirmDetail": {"confNum": "C1"}}},
        }
    )
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
    session = FakeSession(
        {
            "/ftgw/digital/activityapi/api/v1/transactions/pending": _pending(
                [FILLED, WORKING, PARTIAL]
            ),
            "/ftgw/digital/trade-equity/positions": [
                SPAXX_ROW,
                {"symbol": "TQQQ", "quantity": 12.0},
            ],
            "/ftgw/digital/trade-equity/balance": {"cashDetail": {"settledAmt": 4321.55}},
        }
    )
    snap = _broker(session).snapshot()
    assert snap.positions == {"TQQQ": 12.0}
    assert snap.cash == 4321.55
    assert snap.orders["2C50H6WV"]["state"] is OrderState.FILLED
    assert snap.orders["2C50H6WV"]["avg_fill_price"] == 69.35
    assert snap.orders["2C50PART"]["filled_qty"] == 4


def test_cash_prefers_settled_because_this_is_a_cash_account():
    """Proceeds settle T+1 here, so unsettled cash is visible in the
    account and is NOT tradeable without a good-faith violation."""
    session = FakeSession(
        {
            "/ftgw/digital/activityapi/api/v1/transactions/pending": _pending([]),
            "/ftgw/digital/trade-equity/positions": [],
            "/ftgw/digital/trade-equity/balance": {
                "cash": 9999.99,
                "cashDetail": {"settledAmt": 100.00},
            },
        }
    )
    assert _broker(session).snapshot().cash == 100.00


def test_an_order_is_findable_by_our_decision_id_after_preview():
    """Fidelity has no client-reference field, so the decision_id ->
    confNum map is written at PREVIEW time -- before anything could be
    committed, so it is never a guess made after the fact."""
    session = FakeSession(
        {
            "/ftgw/digital/trade-equity/getquote": QUOTE,
            PREVIEW_PATH: {"preview": {"orderConfirmDetail": {"confNum": "2C50H6WV"}}},
            "/ftgw/digital/activityapi/api/v1/transactions/pending": _pending([FILLED]),
        }
    )
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
    session = FakeSession(
        {
            "/ftgw/digital/activityapi/api/v1/transactions/pending": _pending([WORKING]),
            "/ftgw/digital/trade-equity/positions": [],
            "/ftgw/digital/trade-equity/balance": {},
        }
    )
    snap = _broker(session).snapshot()
    assert "2C50H81C" in snap.orders


def test_a_missing_balance_is_none_rather_than_zero():
    """Zero cash and unknown cash are completely different facts to
    reconcile against."""
    session = FakeSession(
        {
            "/ftgw/digital/activityapi/api/v1/transactions/pending": _pending([]),
            "/ftgw/digital/trade-equity/positions": [],
            "/ftgw/digital/trade-equity/balance": {},
        }
    )
    assert _broker(session).snapshot().cash is None


# ======================================================================
# Regressions found by reading captured traffic, not by these tests
# ======================================================================
#
# Every bug below was invisible because the FIXTURES encoded the same
# wrong beliefs as the code. They agreed with each other and were both
# wrong about Fidelity. The fixtures above are now transcriptions of
# real payloads, and these assert the specific things that were broken.


def test_the_core_money_market_sweep_is_not_a_position():
    """SPAXX appears in every real positions response with a quantity in
    the tens of thousands. Counted, it tells reconciliation the account
    holds 27,336 shares of something the strategy has never traded."""
    session = FakeSession(
        {
            "/ftgw/digital/activityapi/api/v1/transactions/pending": _pending([]),
            "/ftgw/digital/trade-equity/positions": [
                SPAXX_ROW,
                {"symbol": "TQQQ", "quantity": 5.0},
            ],
            "/ftgw/digital/trade-equity/balance": {},
        }
    )
    assert _broker(session).snapshot().positions == {"TQQQ": 5.0}


@pytest.mark.parametrize(
    "row",
    [
        {"symbol": "X", "quantity": 1.0, "securityDetail": {"isCash": True}},
        {"symbol": "X", "quantity": 1.0, "securityType": "Core"},
        {"symbol": "X", "quantity": 1.0, "securityDetail": {"brokerageHoldingType": "Cash"}},
    ],
)
def test_cash_is_excluded_on_any_of_its_three_markers(row):
    """Any one marker could be renamed; cash misreported as a position is
    the failure that matters, so this errs toward excluding."""
    session = FakeSession(
        {
            "/ftgw/digital/activityapi/api/v1/transactions/pending": _pending([]),
            "/ftgw/digital/trade-equity/positions": [row],
            "/ftgw/digital/trade-equity/balance": {},
        }
    )
    assert _broker(session).snapshot().positions == {}


def test_the_quote_reads_fidelitys_own_field_names():
    """get_quote previously looked for lastPrice/last/askPrice/bidPrice --
    camelCase names that appear NOWHERE in a Fidelity quote. It could
    never have returned a price, and every order would have died at
    'No usable price'. The real shape is QUOTE_DATA.ASK_PRICE, upper
    snake case, string-valued."""
    assert (
        _broker(FakeSession({"/ftgw/digital/trade-equity/getquote": QUOTE})).get_quote("TQQQ")
        == 69.54
    )


def test_the_quote_prefers_the_ask_because_a_buy_pays_it():
    """Sizing a dollar amount against a lower last price would buy more
    shares than the cash covers."""
    session = FakeSession(
        {
            "/ftgw/digital/trade-equity/getquote": {
                "QUOTE_DATA": {"ASK_PRICE": "70.00", "LAST_PRICE": "69.00", "BID_PRICE": "68.00"}
            }
        }
    )
    assert _broker(session).get_quote("TQQQ") == 70.00


def test_the_adapter_never_calls_the_multi_account_positions_endpoint():
    """traderplus-api/api/positions/v1 nests TWELVE accounts and its rows
    carry no acctNum, so a key-search over it sums every account the user
    owns. No row-level predicate can recover an account the row does not
    name -- the only fix was to stop calling it."""
    import ast

    source = Path("src/fidelity_broker.py").read_text(encoding="utf-8")
    tree = ast.parse(source)
    docs = {
        ast.get_docstring(n, clean=False)
        for n in ast.walk(tree)
        if isinstance(n, (ast.Module, ast.ClassDef, ast.FunctionDef))
    }
    literals = [
        n.value
        for n in ast.walk(tree)
        if isinstance(n, ast.Constant)
        and isinstance(n.value, str)
        and n.value not in docs
        and "traderplus-api" in n.value
    ]
    assert literals == [], f"multi-account endpoint reachable: {literals}"


@pytest.mark.parametrize(
    "method,path,check",
    [
        (
            "_orders",
            "/ftgw/digital/activityapi/api/v1/transactions/pending",
            lambda payload: "filter" in payload and "accounts" in payload["filter"],
        ),
        (
            "_positions",
            "/ftgw/digital/trade-equity/positions",
            lambda payload: payload.get("acctNum") == ACCOUNT,
        ),
        (
            "_cash",
            "/ftgw/digital/trade-equity/balance",
            lambda payload: isinstance(payload, list) and payload[0]["acctNum"] == ACCOUNT,
        ),
    ],
)
def test_each_read_endpoint_is_sent_the_body_fidelity_actually_expects(method, path, check):
    """Every one of these was wrong. Request shapes were never captured
    from real traffic -- only responses were -- so all three were
    invented, and the adapter would have failed on its first real call."""
    session = FakeSession(
        {
            "/ftgw/digital/activityapi/api/v1/transactions/pending": _pending([]),
            "/ftgw/digital/trade-equity/positions": [],
            "/ftgw/digital/trade-equity/balance": {},
        }
    )
    getattr(_broker(session), method)()
    sent = next(p for called, p in session.calls if called == path)
    assert check(sent), f"{path} was sent {sent!r}"


# --- the pending-orders filter ----------------------------------------
#
# Every field below is REQUIRED by the venue, and each was learned by
# being refused. The first live readback sent only acctNum and got:
#
#   400 "filter.accounts.0.acctType should not be empty"
#
# then, once acctType was added:
#
#   400 "filter.accounts.0.acctName should not be empty"
#
# That happened AFTER the order it was reading back had been placed
# successfully, which is the worst moment to discover a payload is
# incomplete -- the money had moved and the tool could not see it.


def _account_filter(session):
    """The account entry actually sent to transactions/pending."""
    path, payload = next((p, q) for p, q in session.calls if p.endswith("transactions/pending"))
    assert path
    return payload["filter"]["accounts"][0]


def test_the_pending_filter_carries_every_field_the_venue_demands():
    session = FakeSession({PENDING_PATH: _pending([])})
    FidelityBroker(session, ACCOUNT, (ACCOUNT,), account_name="Traditional IRA")._orders()
    entry = _account_filter(session)
    assert entry == {
        "acctNum": ACCOUNT,
        "acctType": "Brokerage",
        "acctSubType": "Brokerage",
        "acctName": "Traditional IRA",
    }


def test_the_account_type_describes_the_account_and_is_not_a_constant():
    """A different account type sends something else, so these are
    constructor arguments rather than module constants."""
    session = FakeSession({PENDING_PATH: _pending([])})
    FidelityBroker(
        session,
        ACCOUNT,
        (ACCOUNT,),
        account_name="Some Cash Account",
        account_type="Cash",
        account_sub_type="CashManagement",
    )._orders()
    entry = _account_filter(session)
    assert entry["acctType"] == "Cash"
    assert entry["acctSubType"] == "CashManagement"


def test_a_bare_account_number_is_not_what_this_endpoint_takes():
    """Pins the shape against a well-meaning simplification back to
    {"acctNum": ...}, which reads cleaner and is rejected."""
    session = FakeSession({PENDING_PATH: _pending([])})
    FidelityBroker(session, ACCOUNT, (ACCOUNT,), account_name="Traditional IRA")._orders()
    assert set(_account_filter(session)) > {"acctNum"}
