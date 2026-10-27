"""fidelity_gateway/quotes.py: Fidelity's quote, read-only, as a second source."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

import fidelity_gateway.quotes as quotes
from fidelity_gateway.broker import QUOTE_PATH
from fidelity_gateway.session import READ_ONLY_ENDPOINTS
from fidelity_gateway.tests.test_fidelity_broker import FakeSession

REPLY = {"QUOTE_DATA": {"BID_PRICE": "216.90", "ASK_PRICE": "217.10", "LAST_PRICE": "217.00"}}


def test_the_prices_are_read_and_the_endpoint_is_read_only():
    session = FakeSession({QUOTE_PATH: REPLY})
    quote = quotes.FidelityQuotes(session).quote("RSP")
    assert (quote.bid, quote.ask, quote.last) == (216.9, 217.1, 217.0)
    assert quote.source == "fidelity" and quote.spread == pytest.approx(0.2 / 217.0)
    assert session.calls == [(QUOTE_PATH, {"symbols": "RSP"})]
    assert QUOTE_PATH in READ_ONLY_ENDPOINTS


def test_until_its_time_fields_are_known_no_quote_says_when_it_is_from():
    """And so the feed uses none: before the open, LAST may be yesterday's."""
    assert quotes.TIME_FIELDS == () and quotes.LAST_TIME_FIELDS == ()
    quote = quotes.FidelityQuotes(FakeSession({QUOTE_PATH: REPLY})).quote("RSP")
    assert quote.at is None and quote.last_at is None


def test_a_known_time_field_dates_the_quote(monkeypatch):
    monkeypatch.setattr(quotes, "TIME_FIELDS", (("QUOTE_TIME", "epoch_ms"),))
    reply = {"QUOTE_DATA": {**REPLY["QUOTE_DATA"], "QUOTE_TIME": "1793192400000"}}
    quote = quotes.FidelityQuotes(FakeSession({QUOTE_PATH: reply})).quote("RSP")
    assert quote.at == datetime.fromtimestamp(1793192400, UTC)
    assert quote.last_at is None  # the bid and ask's time never dates the last trade


def test_a_known_last_time_field_dates_the_last_trade(monkeypatch):
    monkeypatch.setattr(quotes, "LAST_TIME_FIELDS", (("LAST_TIME", "epoch_ms"),))
    reply = {"QUOTE_DATA": {**REPLY["QUOTE_DATA"], "LAST_TIME": "1793131800000"}}
    quote = quotes.FidelityQuotes(FakeSession({QUOTE_PATH: reply})).quote("RSP")
    assert quote.last_at == datetime.fromtimestamp(1793131800, UTC) and quote.at is None


def test_a_missing_price_is_none_not_zero():
    reply = {"QUOTE_DATA": {"LAST_PRICE": "217.00", "BID_PRICE": "0"}}
    quote = quotes.FidelityQuotes(FakeSession({QUOTE_PATH: reply})).quote("RSP")
    assert quote.bid is None and quote.ask is None and quote.last == 217.0
