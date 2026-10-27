"""engine/trading/market_feed.py: Alpaca first, the venue's quote second."""

from __future__ import annotations

from datetime import UTC, date, datetime, time, timedelta
from types import SimpleNamespace

import pytest

from engine.core.exceptions import BrokerUnavailableError, DataValidationError
from engine.core.quotes import Quote
from engine.core.trading_calendar import EASTERN
from engine.core.venue_sessions import VenueCalendar
from engine.trading.market_feed import FeedsDisagree, MarketFeed

DAY = date(2026, 10, 27)


def _et(hour, minute=0, second=0):
    return datetime.combine(DAY, time(hour, minute, second), EASTERN).astimezone(UTC)


class Primary:
    def __init__(self, bar=None):
        self.bar = bar

    def latest_bar(self, symbol):
        if self.bar is None:
            raise DataValidationError("No bar returned")
        return self.bar

    trading_client = "the clock"


class Secondary:
    source = "fidelity"

    def __init__(self, quote=None, error=None):
        self.q, self.error, self.calls = quote, error, 0

    def quote(self, symbol):
        self.calls += 1
        if self.error:
            raise self.error
        return self.q


def _bar(at, close=217.0):
    return SimpleNamespace(timestamp=at, open=close, high=close, low=close, close=close, volume=10)


def _quote(at, last=217.0, bid=216.9, ask=217.1, last_at="same"):
    last_at = at if last_at == "same" else last_at
    return Quote("RSP", bid=bid, ask=ask, last=last, at=at, source="fidelity", last_at=last_at)


def _feed(primary, secondary=None, now=None, **kw):
    calendar = VenueCalendar("fidelity", ("pre_market", "regular", "after_hours"))
    heard = []
    feed = MarketFeed(
        primary,
        secondary=secondary,
        calendar=calendar,
        now=lambda: now,
        quote_listener=heard.append,
        **kw,
    )
    return feed, heard


def test_a_fresh_alpaca_bar_is_the_bar():
    now = _et(8, 31, 10)
    bar = _bar(_et(8, 30))
    feed, _ = _feed(Primary(bar), Secondary(_quote(now)), now)
    assert feed.latest_bar("RSP") is bar
    assert feed.quote("RSP").ask == 217.1


def test_a_pre_market_minute_with_no_alpaca_bar_is_filled_from_the_quote():
    now = _et(8, 31, 10)
    feed, heard = _feed(Primary(None), Secondary(_quote(now - timedelta(seconds=5), 217.4)), now)
    bar = feed.latest_bar("RSP")
    assert bar.source == "fidelity" and bar.close == bar.low == 217.4 and bar.volume == 0
    assert bar.timestamp == _et(8, 31)
    assert heard and heard[0]["last"] == 217.4, "every quote read is journaled"


def test_a_stale_alpaca_bar_gives_way_to_the_quote_outside_the_regular_session():
    now = _et(17, 5)
    feed, _ = _feed(Primary(_bar(_et(16, 40))), Secondary(_quote(now)), now)
    assert feed.latest_bar("RSP").source == "fidelity"


def test_the_regular_session_is_never_gap_filled():
    now = _et(11, 0, 30)
    stale = _bar(_et(10, 50))
    feed, _ = _feed(Primary(stale), Secondary(_quote(now)), now)
    assert feed.latest_bar("RSP") is stale, "returned stale for the loop to record, not trade"
    empty, _ = _feed(Primary(None), Secondary(_quote(now)), now)
    with pytest.raises(DataValidationError):
        empty.latest_bar("RSP")


def test_feeds_that_disagree_refuse_the_tick():
    now = _et(8, 31, 10)
    feed, _ = _feed(Primary(_bar(_et(8, 31), 217.0)), Secondary(_quote(now, last=225.0)), now)
    with pytest.raises(FeedsDisagree, match="apart"):
        feed.latest_bar("RSP")


def test_an_old_untimed_or_unreachable_quote_is_not_used():
    now = _et(8, 31, 10)
    old, _ = _feed(Primary(None), Secondary(_quote(now - timedelta(minutes=5))), now)
    with pytest.raises(DataValidationError):
        old.latest_bar("RSP")
    assert "old" in old.secondary_note

    untimed, _ = _feed(Primary(None), Secondary(_quote(None)), now)
    with pytest.raises(DataValidationError):
        untimed.latest_bar("RSP")
    assert "says not when" in untimed.secondary_note, "before the open, 'last' can be yesterday's"

    gone, _ = _feed(Primary(None), Secondary(error=BrokerUnavailableError("signed out")), now)
    with pytest.raises(DataValidationError):
        gone.latest_bar("RSP")
    assert gone.quote("RSP") is None and "unreachable" in gone.secondary_note


def test_without_a_second_source_it_is_the_primary():
    now = _et(8, 31, 10)
    bar = _bar(_et(8, 31))
    feed, _ = _feed(Primary(bar), None, now)
    assert feed.latest_bar("RSP") is bar and feed.quote("RSP") is None
    assert feed.trading_client == "the clock", "the primary's attributes show through"


def test_one_quote_read_serves_the_tick():
    now = _et(8, 31, 10)
    secondary = Secondary(_quote(now))
    feed, _ = _feed(Primary(_bar(_et(8, 31))), secondary, now)
    feed.latest_bar("RSP")
    feed.quote("RSP")
    assert secondary.calls == 1


def test_a_last_trade_from_yesterday_neither_fills_a_gap_nor_cross_checks():
    """Fidelity before the open: the bid and ask are this morning's, the last
    price is yesterday's close and dated so (captured 2026-10-27)."""
    now = _et(8, 31, 10)
    yesterday = _et(16, 10) - timedelta(days=1)
    quote = _quote(now - timedelta(seconds=5), last=210.0, last_at=yesterday)
    feed, _ = _feed(Primary(None), Secondary(quote), now)
    with pytest.raises(DataValidationError, match="no quote to stand in"):
        feed.latest_bar("RSP")
    bar = _bar(_et(8, 31), close=217.0)  # 3% from that "last": no disagreement
    feed, _ = _feed(Primary(bar), Secondary(quote), now)
    assert feed.latest_bar("RSP") is bar
    assert feed.quote("RSP").bid == 216.9  # the bid and ask still price an order


def test_an_undated_last_trade_is_not_used():
    now = _et(8, 31, 10)
    feed, _ = _feed(Primary(None), Secondary(_quote(now, last_at=None)), now)
    with pytest.raises(DataValidationError):
        feed.latest_bar("RSP")
