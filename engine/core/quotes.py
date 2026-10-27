"""
A venue's real-time quote, and the port a second data source fills.

Alpaca's bars are the engine's market data. A Fidelity deployment can also
read Fidelity's own real-time quote through the browser extension
(fidelity_gateway/quotes.py) -- a SECOND source: it prices limit orders
(bid and ask), cross-checks Alpaca's price, and stands in for a minute
Alpaca has no bar for, outside the regular session
(engine/trading/market_feed.py). The engine never imports fidelity_gateway;
it is handed anything with this shape.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Protocol


@dataclass(frozen=True)
class Quote:
    """One quote. Any price may be None when the venue did not give it.

    Two times, because they are not the same moment: `at` is when the bid
    and ask are from, `last_at` when the last trade was. Before the open a
    venue's bid and ask move while its "last" is still yesterday's close
    (Fidelity's, captured 2026-10-27). Either is None when the venue did not
    say."""

    symbol: str
    bid: float | None
    ask: float | None
    last: float | None
    at: datetime | None
    source: str
    last_at: datetime | None = None

    @property
    def mid(self) -> float | None:
        if self.bid and self.ask and self.ask >= self.bid:
            return (self.bid + self.ask) / 2.0
        return None

    @property
    def spread(self) -> float | None:
        """The spread as a fraction of the midpoint, or None."""
        mid = self.mid
        return (self.ask - self.bid) / mid if mid else None

    def to_dict(self) -> dict:
        return {
            "symbol": self.symbol,
            "bid": self.bid,
            "ask": self.ask,
            "last": self.last,
            "at": self.at.isoformat() if self.at else None,
            "last_at": self.last_at.isoformat() if self.last_at else None,
            "source": self.source,
        }


class QuoteSource(Protocol):
    """What engine/trading/market_feed.py reads a second source through."""

    source: str

    def quote(self, symbol: str) -> Quote:
        """The current quote. Raises when there is none to be had -- a
        BrokerUnavailableError when the venue cannot be reached for now."""
        ...
