"""
Fidelity's real-time quote, as a second data source behind Alpaca.

engine/trading/market_feed.py reads it through engine/core/quotes.QuoteSource
when live.secondary_feed is enabled on a Fidelity deployment: its bid and ask
price limit orders, its last trade cross-checks Alpaca's bar and -- in a
traded window outside the regular session -- stands in for a minute Alpaca
has no bar for.

Read-only: one POST to trade-equity/getquote, an endpoint in
session.READ_ONLY_ENDPOINTS and the extension's own allowlist, through the
trader's own FidelitySession. Nothing here can preview or place.

--------------------------------------------------------------------
WHAT IS KNOWN, AND WHAT IS NOT YET

The price fields are Fidelity's, from captured traffic and already relied on
by FidelityBroker.get_quote: QUOTE_DATA.BID_PRICE / ASK_PRICE / LAST_PRICE,
UPPER_SNAKE and string-valued.

Not known yet: which getquote fields say WHEN the bid and ask are from and
when the last trade was. A pre-market capture of Trader+'s own quote
(traderplus-api quotes/v1, 2026-10-27; docs/research/fidelity-extended-hours.md)
shows why those are two questions: its bid and ask carried this morning's
times while its last price was yesterday's close, dated yesterday, even after
pre-market trades. getquote itself is still to be captured. Until it is,
TIME_FIELDS and LAST_TIME_FIELDS are empty, every quote's `at` and `last_at`
are None, and the feed uses none of them -- a quote that cannot say when it
is from is not believed.
"""

from __future__ import annotations

from datetime import UTC, datetime

from engine.core.quotes import Quote
from fidelity_gateway.broker import QUOTE_PATH, _as_float, _find_first

SOURCE = "fidelity"

#: The reply's field(s) giving the bid and ask's time, in the order to try,
#: and how each is written. EMPTY until a pre-market capture names them
#: (module docstring).
TIME_FIELDS: tuple[tuple[str, str], ...] = ()

#: The same for the last trade's time -- never the bid and ask's: before the
#: open that would date yesterday's close to this morning.
LAST_TIME_FIELDS: tuple[tuple[str, str], ...] = ()


class FidelityQuotes:
    """engine/core/quotes.QuoteSource over a FidelitySession."""

    source = SOURCE

    def __init__(self, session) -> None:
        self._session = session

    def quote(self, symbol: str) -> Quote:
        reply = self._session.post_json(QUOTE_PATH, {"symbols": symbol})

        def price(key: str) -> float | None:
            value = _as_float(_find_first(reply, key))
            return value if value > 0 else None

        return Quote(
            symbol=symbol,
            bid=price("BID_PRICE"),
            ask=price("ASK_PRICE"),
            last=price("LAST_PRICE"),
            at=_quote_time(reply, TIME_FIELDS),
            last_at=_quote_time(reply, LAST_TIME_FIELDS),
            source=SOURCE,
        )


def _quote_time(reply, fields: tuple[tuple[str, str], ...]) -> datetime | None:
    for key, form in fields:
        raw = _find_first(reply, key)
        if raw in (None, ""):
            continue
        try:
            if form == "epoch_ms":
                return datetime.fromtimestamp(float(raw) / 1000.0, UTC)
            if form == "epoch":
                return datetime.fromtimestamp(float(raw), UTC)
            moment = datetime.fromisoformat(str(raw))
            return moment if moment.tzinfo else None
        except (TypeError, ValueError, OverflowError):
            continue
    return None
