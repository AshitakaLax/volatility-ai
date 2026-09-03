"""
The adapter that can spend real money.

Every gate is tested from the refusing side first. The affirmative cases
exist to prove the thing works at all; the refusals are the reason the
module is safe to have in the tree.

CWH is the symbol throughout because it is what the first live test will
use -- a ~$20 share, so a one-share order risks about twenty dollars.
"""

from __future__ import annotations

import json

import pytest

from src.exceptions import ConfigurationError
from src.fidelity_broker import FidelityBroker
from src.fidelity_placing_broker import (
    CANCEL_PLACE_PATH,
    CANCEL_PREVIEW_PATH,
    PLACE_PATH,
    FidelityPlacingBroker,
    FileConfNumJournal,
    unresolved_orders,
)
from src.fidelity_session import PREVIEW_ENDPOINTS, FidelitySession
from src.order_lifecycle import OrderState
from src.retry_policy import AmbiguousSubmissionError
from tests.unit.test_fidelity_broker import ACCOUNT, FakeSession

SYMBOL = "CWH"
PRICE = 20.00
PREVIEW = "/ftgw/digital/trade-equity/previewSrvc"


class SpyJournal:
    def __init__(self, explode=False):
        self.records = []
        self.explode = explode

    def record(self, decision_id, conf_num, detail):
        if self.explode:
            raise OSError("disk full")
        self.records.append((decision_id, conf_num, detail))

    def read_all(self):
        return [{"decision_id": d, "conf_num": c, **x} for d, c, x in self.records]


def _session(conf="2C50CWH1", place_conf=None, place_raises=None):
    return FakeSession(
        {
            "/ftgw/digital/trade-equity/getquote": {
                "QUOTE_DATA": {"ASK_PRICE": str(PRICE), "LAST_PRICE": str(PRICE)}
            },
            PREVIEW: {"preview": {"orderConfirmDetail": {"confNum": conf}}},
            PLACE_PATH: (
                _raise(place_raises)
                if place_raises
                else {"place": {"orderConfirmDetail": {"confNum": place_conf or conf}}}
            ),
            "/ftgw/digital/activityapi/api/v1/transactions/pending": {"data": {"orders": []}},
        }
    )


def _raise(exc):
    def _boom(_payload):
        raise exc

    return _boom


_UNSET = object()


def _broker(session=None, journal=_UNSET, **kw):
    """Sentinel, not None, for the journal default.

    The first version used `journal=None` as the default and swapped in a
    SpyJournal when it saw one -- which made an explicit journal=None
    indistinguishable from "not supplied", so
    test_no_journal_means_no_placing silently tested nothing and passed
    for the wrong reason. A helper that cannot express the case a test
    needs is a helper that disables the test.
    """
    options = dict(
        confirm_live_orders=True,
        allowed_symbols=(SYMBOL,),
        max_order_value=100.0,
        journal=SpyJournal() if journal is _UNSET else journal,
    )
    options.update(kw)
    return FidelityPlacingBroker(session or _session(), ACCOUNT, (ACCOUNT,), **options)


# ======================================================================
# Construction refuses anything permissive by default
# ======================================================================


def test_it_will_not_construct_without_an_explicit_acknowledgement():
    with pytest.raises(ConfigurationError, match="REAL ORDERS WITH REAL MONEY"):
        FidelityPlacingBroker(
            _session(),
            ACCOUNT,
            (ACCOUNT,),
            allowed_symbols=(SYMBOL,),
            max_order_value=100.0,
            journal=SpyJournal(),
        )


def test_an_empty_symbol_allowlist_permits_nothing():
    with pytest.raises(ConfigurationError, match="allowed_symbols is empty"):
        _broker(allowed_symbols=())


@pytest.mark.parametrize("ceiling", [0.0, -1.0])
def test_a_missing_or_nonsensical_value_ceiling_is_refused(ceiling):
    with pytest.raises(ConfigurationError, match="max_order_value"):
        _broker(max_order_value=ceiling)


def test_no_journal_means_no_placing():
    """The gate that looks like bookkeeping and is not: without a durable
    confNum, a placeOrder timeout is unknowable rather than recoverable."""
    with pytest.raises(ConfigurationError, match="ConfNumJournal is required"):
        _broker(journal=None)


def test_the_preview_only_adapter_is_still_preview_only():
    """Placing lives in a subclass precisely so this stays true."""
    plain = FidelityBroker(_session(), ACCOUNT, (ACCOUNT,))
    assert not hasattr(plain, "place")


# ======================================================================
# Per-order gates
# ======================================================================


def test_a_symbol_outside_the_allowlist_is_refused():
    with pytest.raises(ConfigurationError, match="not in allowed_symbols"):
        _broker().place("TQQQ", "buy", 1, 69.0, "dec-1")


def test_the_symbol_check_is_case_insensitive_but_still_exact():
    broker = _broker()
    broker.place("cwh", "buy", 1, PRICE, "dec-1")  # same ticker, different case
    with pytest.raises(ConfigurationError):
        broker.place("CWHX", "buy", 1, PRICE, "dec-2")


def test_an_order_over_the_value_ceiling_is_refused_not_trimmed():
    """A size this code did not expect is a bug to surface, not a number
    to quietly adjust."""
    with pytest.raises(ConfigurationError, match="exceeds the max_order_value"):
        _broker().place(SYMBOL, "buy", 10, 20.0, "dec-1")  # $200 > $100


def test_placing_requires_a_decision_id():
    """It is the key the journal and reconciliation both use."""
    with pytest.raises(ValueError, match="client_order_id is required"):
        _broker().submit_buy(SYMBOL, 40.0)


@pytest.mark.parametrize("side", ["short", "BUY", ""])
def test_an_unknown_side_is_refused(side):
    with pytest.raises(ValueError, match="side must be"):
        _broker().place(SYMBOL, side, 1, PRICE, "dec-1")


# ======================================================================
# The sequence: preview -> journal -> commit
# ======================================================================


def test_the_confnum_is_journalled_before_the_order_is_committed():
    """THE CENTRAL SAFETY PROPERTY. If this ordering ever inverts, a
    timeout stops being recoverable."""
    journal = SpyJournal()
    session = _session()
    _broker(session, journal).place(SYMBOL, "buy", 1, PRICE, "dec-1")

    paths = [path for path, _ in session.calls]
    assert paths.index(PREVIEW) < paths.index(PLACE_PATH)
    assert journal.records, "nothing journalled"
    assert journal.records[0][1] == "2C50CWH1"
    # and the journal write happened between them
    assert len(journal.records) == 1


def test_a_journal_failure_stops_the_order_before_it_is_placed():
    session = _session()
    with pytest.raises(OSError):
        _broker(session, SpyJournal(explode=True)).place(SYMBOL, "buy", 1, PRICE, "dec-1")
    assert PLACE_PATH not in [p for p, _ in session.calls], (
        "an unjournalled order must never be committed"
    )


def test_the_place_ticket_is_the_preview_ticket_plus_the_confnum():
    session = _session()
    _broker(session).place(SYMBOL, "buy", 1, PRICE, "dec-1")
    preview = next(p for path, p in session.calls if path == PREVIEW)["orderDetails"]
    placed = next(p for path, p in session.calls if path == PLACE_PATH)["orderDetails"]
    assert placed == dict(preview, confNum="2C50CWH1")


def test_a_placed_order_reports_submitted():
    order = _broker().place(SYMBOL, "buy", 1, PRICE, "dec-1")
    assert order.state is OrderState.SUBMITTED
    assert order.id == "2C50CWH1"
    assert order.client_order_id == "dec-1"


def test_every_ticket_is_a_limit_order():
    """A market order in a thin session is the one thing never to emit."""
    session = _session()
    _broker(session).place(SYMBOL, "buy", 1, PRICE, "dec-1")
    ticket = next(p for path, p in session.calls if path == PLACE_PATH)["orderDetails"]
    assert ticket["priceTypeCode"] == "L"
    assert ticket["limitPrice"] == PRICE
    assert ticket["stopPrice"] is None


# ======================================================================
# When it goes wrong
# ======================================================================


def test_a_transport_failure_is_ambiguous_never_retryable():
    session = _session(place_raises=TimeoutError("gateway timeout"))
    with pytest.raises(AmbiguousSubmissionError) as caught:
        _broker(session).place(SYMBOL, "buy", 1, PRICE, "dec-1")
    message = str(caught.value)
    assert "2C50CWH1" in message, "the confNum must be in the error, for recovery"
    assert "MAY BE LIVE" in message
    assert "Do not" in message and "resubmit" in message


def test_a_mismatched_confnum_is_ambiguous_rather_than_assumed():
    session = _session(conf="2C50CWH1", place_conf="2C50OTHER")
    with pytest.raises(AmbiguousSubmissionError, match="echoed confNum"):
        _broker(session).place(SYMBOL, "buy", 1, PRICE, "dec-1")


def test_the_transport_is_the_last_line_and_it_holds():
    """Even correctly configured, a session without place permission
    cannot be talked into it."""
    preview_only = FidelitySession(object(), allow_preview_endpoints=True)
    with pytest.raises(ConfigurationError, match="PLACES OR CANCELS A REAL ORDER"):
        preview_only.post_json(PLACE_PATH, {})
    for path in PREVIEW_ENDPOINTS:
        assert path not in (PLACE_PATH,)


# ======================================================================
# Recovery
# ======================================================================


def test_the_journal_survives_being_written_one_line_at_a_time(tmp_path):
    path = tmp_path / "orders.jsonl"
    journal = FileConfNumJournal(str(path))
    journal.record("dec-1", "2C50CWH1", {"symbol": SYMBOL, "qty": 1.0})
    journal.record("dec-2", "2C50CWH2", {"symbol": SYMBOL, "qty": 2.0})

    lines = [json.loads(x) for x in path.read_text(encoding="utf-8").splitlines()]
    assert [x["conf_num"] for x in lines] == ["2C50CWH1", "2C50CWH2"]
    assert journal.read_all() == lines


def test_a_missing_journal_file_reads_as_empty_not_an_error(tmp_path):
    assert FileConfNumJournal(str(tmp_path / "absent.jsonl")).read_all() == []


def test_unresolved_orders_names_what_the_venue_never_received(tmp_path):
    """After an ambiguous submit, this is the question that matters."""
    path = tmp_path / "orders.jsonl"
    journal = FileConfNumJournal(str(path))
    journal.record("dec-1", "2C50LANDED", {"symbol": SYMBOL})
    journal.record("dec-2", "2C50LOST", {"symbol": SYMBOL})

    session = FakeSession(
        {
            "/ftgw/digital/activityapi/api/v1/transactions/pending": {
                "data": {
                    "orders": [
                        {
                            "orderNum": "2C50LANDED",
                            "acctNum": ACCOUNT,
                            "symbol": SYMBOL,
                            "status": "Open",
                            "cancelableInd": True,
                        }
                    ]
                }
            }
        }
    )
    missing = unresolved_orders(journal, FidelityBroker(session, ACCOUNT, (ACCOUNT,)))
    assert [x["decision_id"] for x in missing] == ["dec-2"]


# ======================================================================
# Regressions: gates that protected the wrong thing
# ======================================================================


def test_the_spend_ceiling_does_not_block_an_exit():
    """A ceiling applied to sells traps capital it was meant to protect.

    Being unable to LEAVE a position you already hold is strictly worse
    than being unable to enter one -- a book built one $20 share at a
    time could not be sold in a single order under a $50 ceiling.
    """
    session = _session()
    order = _broker(session, max_order_value=50.0).place(
        SYMBOL,
        "sell",
        10,
        20.0,
        "exit-1",  # $200, four times the ceiling
    )
    assert order.state is OrderState.SUBMITTED


def test_the_spend_ceiling_still_blocks_an_entry():
    with pytest.raises(ConfigurationError, match="exceeds the max_order_value"):
        _broker(max_order_value=50.0).place(SYMBOL, "buy", 10, 20.0, "entry-1")


def test_a_transport_refusal_is_not_reported_as_a_possible_live_order():
    """The endpoint gate fires BEFORE any network call, so nothing was
    sent. Calling that ambiguous would send an operator hunting for an
    order that never existed -- and teach them to distrust the warning
    that does matter."""
    session = _session()
    session.refuse = {PLACE_PATH}
    with pytest.raises(ConfigurationError):
        _broker(session).place(SYMBOL, "buy", 1, PRICE, "dec-1")


def test_a_real_transport_failure_is_still_ambiguous():
    """The distinction must not swallow the case it was carved out of."""
    session = _session(place_raises=TimeoutError("gateway timeout"))
    with pytest.raises(AmbiguousSubmissionError):
        _broker(session).place(SYMBOL, "buy", 1, PRICE, "dec-1")


# --- cancelling -------------------------------------------------------
#
# Cancelling reaches the same endpoint family as placing, so it is gated
# the same way. The asymmetries below are deliberate and each has a
# reason: a cancel only ever REDUCES exposure, so the checks that exist
# to stop this deployment entering the wrong position do not apply to
# leaving one.


def _cancel_session(cancel_raises=None, echo_account=None):
    responses = {
        CANCEL_PREVIEW_PATH: {"preview": {"orderConfirmDetail": {"confNum": "2C50CWH1"}}},
        CANCEL_PLACE_PATH: (
            _raise(cancel_raises)
            if cancel_raises
            else {"place": {"orderConfirmDetail": {"acctNum": echo_account or ACCOUNT}}}
        ),
        "/ftgw/digital/activityapi/api/v1/transactions/pending": {"data": {"orders": []}},
    }
    return FakeSession(responses)


def test_a_cancel_previews_then_commits_in_that_order():
    """Same two-step shape as placing, and the order is the point: the
    preview half is inert, so a failure there costs nothing."""
    session = _cancel_session()
    _broker(session).cancel("2C50CWH1")
    assert [path for path, _ in session.calls] == [CANCEL_PREVIEW_PATH, CANCEL_PLACE_PATH]


def test_both_cancel_steps_carry_the_captured_envelope():
    """Transcribed from a captured request, not designed -- a shape this
    fiddly is worth pinning against drift."""
    session = _cancel_session()
    _broker(session).cancel("2C50CWH1")
    for _path, payload in session.calls:
        assert payload == {"cancelOrderDetails": {"acctNum": ACCOUNT, "confNum": "2C50CWH1"}}


def test_a_preview_only_transport_refuses_to_cancel():
    """The transport is the gate, not this class. cancelPlaceOrder sits in
    PLACE_ENDPOINTS precisely so a dry-run deployment cannot reach it."""
    preview_only = FidelitySession(object(), allow_preview_endpoints=True)
    with pytest.raises(ConfigurationError):
        preview_only.post_json(CANCEL_PLACE_PATH, {})


def test_cancelling_re_checks_the_account():
    """An allowlist consulted once at construction is decorative. A
    cancel is still an instruction aimed at one account."""
    broker = _broker(_cancel_session())
    broker._account = "999999999"
    with pytest.raises(ConfigurationError, match="allowed_accounts"):
        broker.cancel("2C50CWH1")


def test_a_cancel_is_not_gated_on_the_symbol_allowlist():
    """THE DELIBERATE ASYMMETRY. allowed_symbols stops this deployment
    ENTERING instruments it was not configured for. Refusing to cancel an
    order because its symbol drifted out of a config file would strand a
    live order in the market to satisfy a check that was never about
    that -- the same reasoning that keeps max_order_value on buys only.
    """
    broker = _broker(_cancel_session(), allowed_symbols=("SOMETHINGELSE",))
    broker.cancel("2C50CWH1")  # must not raise


def test_a_failed_cancel_is_ambiguous_and_never_retried():
    """The unknown outcome of a failed cancel is that the order is still
    working -- which is the state it was already in. Still ambiguous, and
    still never a retry."""
    session = _cancel_session(cancel_raises=RuntimeError("gateway timeout"))
    with pytest.raises(AmbiguousSubmissionError, match="may still be WORKING"):
        _broker(session).cancel("2C50CWH1")


def test_a_transport_refusal_while_cancelling_is_not_reported_as_ambiguous():
    """The endpoint gate fires BEFORE any network call, so nothing was
    sent and nothing can be live. Calling that ambiguous would send an
    operator hunting for an order that never existed."""
    session = FakeSession({CANCEL_PREVIEW_PATH: {"preview": {}}}, refuse={CANCEL_PLACE_PATH})
    with pytest.raises(ConfigurationError):
        _broker(session).cancel("2C50CWH1")


def test_cancelling_reads_the_account_back_out_of_the_reply():
    """The request naming the right account is not proof the venue
    applied it."""
    from src.exceptions import ExecutionError

    session = _cancel_session(echo_account="111111111")
    with pytest.raises(ExecutionError, match="DIFFERENT account"):
        _broker(session).cancel("2C50CWH1")


@pytest.mark.parametrize("blank", ["", "   "])
def test_an_empty_confnum_is_refused_before_anything_is_sent(blank):
    session = _cancel_session()
    with pytest.raises(ValueError, match="conf_num is required"):
        _broker(session).cancel(blank)
    assert session.calls == []
