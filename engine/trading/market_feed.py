"""
The trading loop's market data: Alpaca's bars first, a venue's quote second.

--------------------------------------------------------------------
WHY A SECOND SOURCE, AND WHY ONLY SECOND

Alpaca's API is the easy one to depend on, and its bars are what every
backtest here ran on. But the free IEX feed has almost no bars outside the
regular session (RSP: none in ten days of pre-market; SPY and TQQQ under
5% of minutes; docs/research/fidelity-extended-hours.md), so there the loop
would have no price at all -- in exactly the hours a deployment on its
venue's windows (live.sessions) was started early for.
Fidelity's Trader+ page has a real-time quote for those hours, and a
Fidelity deployment can read it through the browser extension
(fidelity_gateway/quotes.py, live.secondary_feed).

So it is used three ways, each narrow:

  * PRICING. Its bid and ask are where a limit order is placed
    (engine/execution/limit_pricing.py). That is what a quote is for.
  * CROSS-CHECK. When both have a price and they differ by more than
    live.secondary_feed.max_divergence, the tick is refused (FeedsDisagree):
    one of them is wrong, and trading on either is the mistake.
  * GAP FILL, and only inside a traded window outside the regular session:
    with no fresh Alpaca bar, the minute is a bar at the quote's last trade
    (open = high = low = close, volume 0), marked source="fidelity". Never in
    the regular session, where Alpaca is not missing minutes and the backtest
    parity of its bars matters more.

A quote is used only when it is fresh (live.secondary_feed.max_age_seconds)
AND says when it is from. A quote with no time is not believed. Its last
trade is used -- to cross-check, or to fill a gap -- only when the venue
dates that trade too, and it is as fresh: before the open, Fidelity's bid
and ask are this morning's while its "last" is yesterday's close
(engine/core/quotes.Quote.last_at).

Every quote read is handed to `quote_listener` (the control directory's
quotes journal), for measuring how often IEX misses a minute and how far
the two sources disagree.
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime

from engine.core.exceptions import BrokerUnavailableError, DataValidationError
from engine.core.quotes import Quote, QuoteSource
from engine.core.venue_sessions import REGULAR

logger = logging.getLogger("Optimizer")

# An Alpaca bar older than this is not "the minute's bar".
DEFAULT_BAR_MAX_AGE_SECONDS = 120.0


class FeedsDisagree(DataValidationError):
    """The primary bar and the second source's quote are too far apart."""


@dataclass(frozen=True)
class FeedBar:
    """A bar as the loop reads one (LiveBar's fields), and where it came from."""

    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float = 0.0
    source: str = "alpaca"


class MarketFeed:
    """Stands in for the loop's market data (AlpacaMarketData's surface:
    latest_bar, is_open, is_open_extended), adding quote().

    `calendar` (engine/core/venue_sessions.VenueCalendar) says where a gap
    may be filled. Without a `secondary`, every call is the primary's.
    """

    def __init__(
        self,
        primary,
        *,
        secondary: QuoteSource | None = None,
        calendar=None,
        max_age_seconds: float = 90.0,
        max_divergence: float = 0.01,
        bar_max_age_seconds: float = DEFAULT_BAR_MAX_AGE_SECONDS,
        now: Callable[[], datetime] = lambda: datetime.now(UTC),
        quote_listener: Callable[[dict], None] | None = None,
    ) -> None:
        self.primary = primary
        self.secondary = secondary
        self.calendar = calendar
        self.max_age_seconds = float(max_age_seconds)
        self.max_divergence = float(max_divergence)
        self.bar_max_age_seconds = float(bar_max_age_seconds)
        self._now = now
        self._quote_listener = quote_listener
        self._quote: Quote | None = None
        self._quote_read_at: datetime | None = None
        self._said_untimed = False
        # Why the second source was not used on the last read, for the status.
        self.secondary_note: str | None = None

    # -- the primary's surface --------------------------------------------

    def is_open(self) -> bool:
        return self.primary.is_open()

    def is_open_extended(self) -> bool:
        return self.primary.is_open_extended()

    def __getattr__(self, name):
        # trading_client and anything else the loop or cli reads off the
        # primary. Only reached for names this class does not define.
        if name == "primary" or name.startswith("__"):
            raise AttributeError(name)
        return getattr(self.primary, name)

    # -- bars --------------------------------------------------------------

    def latest_bar(self, symbol: str):
        now = self._now()
        quote = self._read_quote(symbol, now)
        try:
            bar = self.primary.latest_bar(symbol)
        except DataValidationError:
            bar = None
        fresh = bar is not None and _age(bar.timestamp, now) <= self.bar_max_age_seconds
        last = self._fresh_last(quote, now)
        if fresh:
            if last is not None:
                apart = abs(float(bar.close) - last) / last
                if apart > self.max_divergence:
                    raise FeedsDisagree(
                        f"Alpaca's {symbol} bar closed at {bar.close} and {quote.source}'s last "
                        f"trade is {last} ({apart:.2%} apart, over "
                        f"{self.max_divergence:.2%}); not trading on either this minute"
                    )
            return bar
        if last is not None and self._may_fill_gap(now):
            minute = quote.last_at.astimezone(UTC).replace(second=0, microsecond=0)
            return FeedBar(
                timestamp=minute,
                open=last,
                high=last,
                low=last,
                close=last,
                volume=0.0,
                source=quote.source,
            )
        if bar is not None:
            return bar  # stale: the loop records it and does not trade on it
        raise DataValidationError(f"No bar returned for {symbol}, and no quote to stand in")

    def _fresh_last(self, quote: Quote | None, now: datetime) -> float | None:
        """The quote's last trade, when the venue dates it and it is recent."""
        if quote is None or not quote.last or quote.last_at is None:
            return None
        return quote.last if _age(quote.last_at, now) <= self.max_age_seconds else None

    def _may_fill_gap(self, now: datetime) -> bool:
        if self.calendar is None:
            return False
        window = self.calendar.window_at(now)
        return window is not None and window.session != REGULAR

    # -- quotes ------------------------------------------------------------

    def quote(self, symbol: str) -> Quote | None:
        """This minute's quote from the second source, or None (none
        configured, unreachable, stale, or untimed). Read once per tick:
        latest_bar() already read it."""
        now = self._now()
        if self._quote_read_at is not None and _age(self._quote_read_at, now) < 5.0:
            return self._quote
        return self._read_quote(symbol, now)

    def _read_quote(self, symbol: str, now: datetime) -> Quote | None:
        self._quote, self._quote_read_at = None, now
        if self.secondary is None:
            return None
        try:
            quote = self.secondary.quote(symbol)
        except BrokerUnavailableError as exc:
            self.secondary_note = f"{self.secondary.source} unreachable: {exc}"
            return None
        except Exception as exc:  # a second source never stops a tick
            self.secondary_note = f"{self.secondary.source} quote failed: {exc}"
            logger.warning(f"Second-source quote failed (ignored): {type(exc).__name__}: {exc}")
            return None
        self._report(quote, now)
        if quote.at is None:
            self.secondary_note = f"{quote.source}'s quote says not when it is from; not used"
            if not self._said_untimed:
                logger.warning(f"{self.secondary_note} (said once)")
                self._said_untimed = True
            return None
        age = _age(quote.at, now)
        if age > self.max_age_seconds:
            self.secondary_note = f"{quote.source}'s quote is {age:.0f}s old; not used"
            return None
        self.secondary_note = None
        self._quote = quote
        return quote

    def _report(self, quote: Quote, now: datetime) -> None:
        if self._quote_listener is None:
            return
        try:
            self._quote_listener({"t": now.timestamp(), **quote.to_dict()})
        except Exception as exc:
            logger.warning(f"Quote listener failed (ignored): {type(exc).__name__}: {exc}")


def _age(moment: datetime, now: datetime) -> float:
    if moment.tzinfo is None:
        moment = moment.replace(tzinfo=UTC)
    return (now - moment).total_seconds()
