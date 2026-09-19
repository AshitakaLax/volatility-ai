"""
Nasdaq-100 constituent weights, for weighting event signals.

--------------------------------------------------------------------
WHAT A "WEIGHT IN TQQQ" ACTUALLY IS

TQQQ holds no company stock. It is a 3x daily-return swap-based ETF on
the Nasdaq-100, so its book is swaps and futures against a cash
collateral basket. "AAPL's weight in TQQQ" is therefore not a holding
-- it is AAPL's weight in the INDEX, which is what the swaps reference
and what moves the price this project trades. These are QQQ's published
holdings, which track NDX directly.

The 3x leverage does not change the weights. It scales the return, so a
1% index move from a constituent becomes ~3% here; the relative
importance of one constituent against another is unchanged.

--------------------------------------------------------------------
THIS IS A SINGLE CURRENT SNAPSHOT, AND THAT IS LOOKAHEAD BIAS

Every weight below is as of 2026-08-13 and is applied to all history,
because that is what is available today. Used against a 2016 backtest
it is wrong in a specific and predictable direction: it over-weights
whatever has won since (NVDA at 8.50% was nothing like that in 2016)
and under-weights what has since faded (INTC, CSCO were far larger).

Concretely: MU is the 4th largest holding here at 4.61%, and was not a
top-ten Nasdaq-100 name for most of the backtest window. Any result
that depends on MU's weight in 2017 is reading 2026 into 2017.

This is a deliberate, temporary simplification -- quarterly snapshots
are the agreed next step, and WEIGHTS_AS_OF exists so that a caller (or
a reader of a sweep result) can tell which regime produced it. Do not
promote a result that hinges on these weights without re-running
against point-in-time weights first.

--------------------------------------------------------------------
GOOG AND GOOGL ARE BOTH HERE, ON PURPOSE. They are one company with one
earnings release and two separately-weighted share classes. Summing the
weights of everything reporting at a given instant gives 6.06% for an
Alphabet release, which is the real index exposure to that event;
keeping only GOOGL would understate it by nearly half.
"""

from __future__ import annotations

from datetime import date

# Provenance: QQQ published holdings via stockanalysis.com/etf/qqq/holdings.
WEIGHTS_AS_OF = date(2026, 8, 13)

# symbol -> percent of the index (NOT a fraction; 8.50 means 8.50%).
INDEX_WEIGHTS_PCT: dict[str, float] = {
    "NVDA": 8.50,
    "AAPL": 6.99,
    "MSFT": 5.75,
    "MU": 4.61,
    "AMZN": 4.44,
    "AMD": 3.39,
    "GOOGL": 3.14,
    "AVGO": 3.09,
    "GOOG": 2.92,
    "META": 2.75,
    "TSLA": 2.65,
    "WMT": 2.43,
    "INTC": 2.26,
    "CSCO": 1.92,
    "COST": 1.84,
}


def weight_pct(symbol: str, as_of: date | None = None) -> float:
    """This symbol's index weight in percent, or 0.0 if it is not a
    tracked constituent.

    as_of is accepted and currently ignored -- it is the seam quarterly
    snapshots will use, and taking it now means callers do not have to
    change when point-in-time weights land. A caller that passes a date
    is asking the right question; it just gets the same answer for every
    date until the snapshots exist.
    """
    return INDEX_WEIGHTS_PCT.get(symbol.upper(), 0.0)


def total_tracked_weight_pct() -> float:
    """How much of the index these constituents account for.

    Worth checking rather than assuming: an event signal weighted by
    these numbers can only ever speak for this fraction of the index,
    and the remainder is invisible to it.
    """
    return sum(INDEX_WEIGHTS_PCT.values())
