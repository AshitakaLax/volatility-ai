"""
Static FOMC decision-day calendar.

--------------------------------------------------------------------
WHY STATIC, NOT AN INGESTION PIPELINE

Task 7.9 (see tests/unit/test_task_7_9_macro_signals_discovery.py)
deliberately deferred building any macro/seasonality ingestion because
no consumer existed. HighFrequencyLocalReferenceSizing's
event_day_boost_multiplier is now that consumer -- but FOMC meeting
dates are exactly the case that discovery gate's own step 4 already
anticipated needing no live dependency for: the Federal Reserve
publishes its meeting calendar more than a year in advance. There is
no NLP, sentiment, or live macro feed here, and none is needed -- a
hand-verified, sourced list of dates is the complete, correct
implementation, not a placeholder for a "real" one.

--------------------------------------------------------------------
WHAT COUNTS AS A "FOMC DAY" HERE, AND WHY

The date flagged is the DECISION/PRESS-CONFERENCE day -- the second
day of a two-day meeting, when the policy statement and (starting
2019) the press conference actually move markets -- not the first day
of the meeting, which is not itself a market-moving event.

2016-2018: only the March/June/September/December meetings (the ones
with a Summary of Economic Projections) had a press conference; the
other four meetings/year did not. 2019 onward: every regularly
scheduled meeting has had one, following the policy change announced
in November 2018.

2020 also includes two unscheduled COVID-era emergency actions:
2020-03-03 (an emergency 50bp cut announced Tuesday during market
hours) and 2020-03-16 (the market's first trading session after the
Fed's Sunday March 15 announcement of an emergency cut to zero plus
QE -- the announcement itself fell on a non-trading day, so the
market-relevant date is the next session, not the announcement date).
The regularly scheduled March 17-18, 2020 meeting was superseded by
these actions and is not separately listed.

Dates were verified against the Federal Reserve's own historical
meeting-calendar pages (federalreserve.gov/monetarypolicy/
fomchistorical<year>.htm) and, for the 2020 emergency actions, contemporaneous
reporting (CNN/CNBC, March 2020) -- not recalled from memory alone.
Every date below was cross-checked to land on an actual NYSE trading
day present in this repo's TQQQ SIP dataset before being accepted.

--------------------------------------------------------------------
JOIN SEMANTICS

is_fomc_day(d) takes a date (not a datetime) and does an exact-match
set lookup against calendar dates in US/Eastern local terms -- FOMC
meetings are scheduled and reported in Eastern time, so a caller must
pass the EASTERN calendar date of the bar being evaluated, not a raw
UTC date that may have already rolled to the next day.

is_fomc_day_at(timestamp) is the shared UTC-timestamp-to-Eastern-date
conversion, used identically by optimization_controller.py (backtest)
and live_trading_loop.py (live) -- one implementation, not two copies
that could drift, matching src/sizing_indicators.py's own stated
reason for existing. A naive (tzinfo=None) timestamp is treated as
already being UTC, matching every real data source in this codebase
(Alpaca bars, this repo's own fixtures) rather than silently assuming
the host machine's local timezone, which would make the result depend
on where the code happens to run.

--------------------------------------------------------------------
MAINTENANCE

This list runs through 2026-07-29 (the last FOMC date on or before
this repo's data cutoff at the time it was written). Dates beyond
that are FUTURE meetings per the Fed's published schedule and are
included where already confirmed; extending this list for later years
is a data-entry task against the same federalreserve.gov source, not a
design change.
"""

from __future__ import annotations

from datetime import UTC, date, datetime
from zoneinfo import ZoneInfo

_EASTERN = ZoneInfo("America/New_York")

FOMC_DECISION_DATES: frozenset[date] = frozenset(
    date(y, m, d)
    for y, m, d in [
        # 2016 (quarterly press conferences only: Mar/Jun/Sep/Dec)
        (2016, 3, 16), (2016, 6, 15), (2016, 9, 21), (2016, 12, 14),
        # 2017
        (2017, 3, 15), (2017, 6, 14), (2017, 9, 20), (2017, 12, 13),
        # 2018
        (2018, 3, 21), (2018, 6, 13), (2018, 9, 26), (2018, 12, 19),
        # 2019 (press conference after every meeting, policy effective Jan 2019)
        (2019, 1, 30), (2019, 3, 20), (2019, 5, 1), (2019, 6, 19),
        (2019, 7, 31), (2019, 9, 18), (2019, 10, 30), (2019, 12, 11),
        # 2020 (incl. 2 unscheduled COVID emergency actions; see module docstring)
        (2020, 1, 29), (2020, 3, 3), (2020, 3, 16), (2020, 4, 29),
        (2020, 6, 10), (2020, 7, 29), (2020, 9, 16), (2020, 11, 5), (2020, 12, 16),
        # 2021
        (2021, 1, 27), (2021, 3, 17), (2021, 4, 28), (2021, 6, 16),
        (2021, 7, 28), (2021, 9, 22), (2021, 11, 3), (2021, 12, 15),
        # 2022
        (2022, 1, 26), (2022, 3, 16), (2022, 5, 4), (2022, 6, 15),
        (2022, 7, 27), (2022, 9, 21), (2022, 11, 2), (2022, 12, 14),
        # 2023
        (2023, 2, 1), (2023, 3, 22), (2023, 5, 3), (2023, 6, 14),
        (2023, 7, 26), (2023, 9, 20), (2023, 11, 1), (2023, 12, 13),
        # 2024
        (2024, 1, 31), (2024, 3, 20), (2024, 5, 1), (2024, 6, 12),
        (2024, 7, 31), (2024, 9, 18), (2024, 11, 7), (2024, 12, 18),
        # 2025
        (2025, 1, 29), (2025, 3, 19), (2025, 5, 7), (2025, 6, 18),
        (2025, 7, 30), (2025, 9, 17), (2025, 10, 29), (2025, 12, 10),
        # 2026 (through this repo's data cutoff of 2026-08-21)
        (2026, 1, 28), (2026, 3, 18), (2026, 4, 29), (2026, 6, 17), (2026, 7, 29),
    ]
)


def is_fomc_day(d: date) -> bool:
    """True if `d` (an Eastern-time calendar date) is an FOMC decision
    day per FOMC_DECISION_DATES. See module docstring for exactly what
    that means and why the list stops where it does."""
    return d in FOMC_DECISION_DATES


def is_fomc_day_at(timestamp: datetime) -> bool:
    """True if `timestamp` falls on an FOMC decision day, converting to
    the Eastern calendar date first (see module docstring's Join
    Semantics section for why that conversion, and why naive input is
    treated as UTC rather than local time)."""
    if timestamp.tzinfo is None:
        timestamp = timestamp.replace(tzinfo=UTC)
    return is_fomc_day(timestamp.astimezone(_EASTERN).date())
