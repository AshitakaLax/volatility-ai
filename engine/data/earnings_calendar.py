"""
Static mega-cap earnings REACTION-day calendar.

--------------------------------------------------------------------
WHY STATIC, NOT AN INGESTION PIPELINE

Same rationale as src/fomc_calendar.py, which this module deliberately
mirrors: the consumer is a sizing multiplier, the dates are already
history, and a hand-verified list is the complete implementation
rather than a placeholder for a "real" one. Unlike FOMC dates these
are not published a year ahead, but every date below is in the PAST
relative to this repo's data cutoff, so there is nothing to forecast.

That is also why a static list cannot be the whole of it for a LIVE loop:
a reaction session is known only the evening before, and the list ended
2026-07-31 while seven more went by unflagged. See LIVE, below.

--------------------------------------------------------------------
WHAT COUNTS AS AN "EARNINGS REACTION DAY" HERE, AND WHY

The date flagged is the SESSION THAT TRADES THE REACTION, not the
announcement date. 381 of 385 events in this window were released
after the close (>=16:00 Eastern), so the announcement date itself is
an ordinary session and the move lands the following morning.

That is measured, not assumed. Mean absolute overnight gap in each
constituent's own SIP daily bars, announcement date vs the next
session:

    AAPL   0.71%  ->  3.52%
    META   1.38%  ->  8.20%
    NVDA   0.82%  ->  5.53%

Announcement-day gaps sit at or below the ~1% baseline; the next
session carries a 3.5-8.2% mean gap. For the 4 events released
before or during market hours the announcement date IS the reaction
date, and those are mapped accordingly.

--------------------------------------------------------------------
WHICH COMPANIES, AND WHY THESE

    AAPL, AMZN, AVGO, GOOGL, META, MSFT, NFLX, NVDA, TSLA

Chosen by INDEX WEIGHT, not by the "FANG" acronym. TQQQ is 3x QQQ, so
what matters is what moves the Nasdaq-100; these names carry roughly
half its weight between them. GOOG is omitted because it reports the
same day as GOOGL and would only duplicate dates.

385 announcements collapse to 296 unique sessions (11.1% of the
2672 in this repo's TQQQ dataset) because mega-caps cluster their
reporting into the same few weeks each quarter. 14 of those
sessions are also FOMC decision days. (As generated, through
2026-07-31. Seven sessions were added on 2026-11-12, making 303; none
is an FOMC decision day.)

--------------------------------------------------------------------
MEASURED EFFECT

Realized intraday volatility (std of 1-minute log returns, annualized
over a 390-bar session) on this repo's 10-year TQQQ SIP dataset:

    earnings reaction days   3.79%  vs  3.40%   -> +11.4%, Welch t=2.89
    FOMC decision days       4.58%  vs  3.41%   -> +34.1%, Welch t=2.11

Smaller per-day effect than FOMC but a stronger statistic, because it
covers 4x as many sessions. Recorded here so a future reader does not
have to re-derive whether this calendar was worth building.

--------------------------------------------------------------------
PROVENANCE

Announcement dates and times: Yahoo Finance via yfinance 1.6.0,
queried 2026-08-22 for 2016-01-01 through 2026-08-21. yfinance is NOT a
dependency of this project -- it was used once, in a throwaway
environment, to generate the literal list below. Nothing at runtime
touches it.

The announcement-to-reaction mapping was verified independently
against Alpaca SIP daily bars (the gap table above), so the dates here
do not rest on Yahoo's timestamps alone.

The seven sessions from 2026-08-27 to 2026-11-03 are from SEC EDGAR
instead: each company's 8-K under Item 2.02, stamped the second the
filing was accepted, mapped to its reaction session the same way
(tools/refresh_external.py). Over the list as generated, EDGAR's
reaction sessions for these nine companies are 98.9% in it.

--------------------------------------------------------------------
LIVE: THE LIST, AND WHAT CAME AFTER IT

A backtest reads EARNINGS_REACTION_DATES alone: the same flags on every
machine that runs it, a sweep shard included.

A live loop also reads data/external/earnings_reaction_days.csv
(VAI_EXTERNAL_DIR), which tools/refresh_external.py -- the compose
market-inputs service -- rewrites from EDGAR every evening and again at
07:30 Eastern: `date,symbols`, one row a reaction session. Only rows
dated AFTER the last entry below are taken, and only for the companies
above, so the file can add to the list and never alter it. A loop starts
each session cold and reads it then. Without the file the list stands
alone, as before.

When the file runs ahead of the list, tools/refresh_external.py names
the sessions the list lacks on every run and tools/preflight.py warns:
adding them below keeps backtests of those sessions in step with what
traded.

--------------------------------------------------------------------
JOIN SEMANTICS

Identical to fomc_calendar's: exact-match set lookup on US/Eastern
calendar dates. EASTERN_TZ and the UTC-to-Eastern conversion are
imported from fomc_calendar rather than redefined, so the two
calendars cannot drift apart on timezone handling.
"""

import os
from datetime import UTC, date, datetime
from functools import lru_cache
from pathlib import Path

# Imported, not redefined: fomc_calendar already owns the Eastern zone,
# and two copies of that could disagree.
from engine.data.fomc_calendar import EASTERN_TZ

#: Where the live loop's later sessions come from (module docstring, LIVE).
EXTERNAL_DIR_ENV = "VAI_EXTERNAL_DIR"
REACTION_FILE = "earnings_reaction_days.csv"

MEGA_CAP_SYMBOLS: tuple[str, ...] = (
    "AAPL",
    "AMZN",
    "AVGO",
    "GOOGL",
    "META",
    "MSFT",
    "NFLX",
    "NVDA",
    "TSLA",
)

EARNINGS_REACTION_DATES: frozenset[date] = frozenset(
    date(y, m, d)
    for y, m, d in [
        # 2016 (32 sessions)
        (2016, 1, 20),
        (2016, 1, 27),
        (2016, 1, 28),
        (2016, 1, 29),
        (2016, 2, 2),
        (2016, 2, 11),
        (2016, 2, 18),
        (2016, 3, 4),
        (2016, 4, 19),
        (2016, 4, 22),
        (2016, 4, 27),
        (2016, 4, 28),
        (2016, 4, 29),
        (2016, 5, 5),
        (2016, 5, 13),
        (2016, 6, 3),
        (2016, 7, 19),
        (2016, 7, 20),
        (2016, 7, 27),
        (2016, 7, 28),
        (2016, 7, 29),
        (2016, 8, 4),
        (2016, 8, 12),
        (2016, 9, 2),
        (2016, 10, 18),
        (2016, 10, 21),
        (2016, 10, 26),
        (2016, 10, 27),
        (2016, 10, 28),
        (2016, 11, 3),
        (2016, 11, 11),
        (2016, 12, 9),
        # 2017 (29 sessions)
        (2017, 1, 19),
        (2017, 1, 27),
        (2017, 2, 1),
        (2017, 2, 2),
        (2017, 2, 3),
        (2017, 2, 10),
        (2017, 2, 23),
        (2017, 3, 2),
        (2017, 4, 18),
        (2017, 4, 28),
        (2017, 5, 3),
        (2017, 5, 4),
        (2017, 5, 10),
        (2017, 6, 2),
        (2017, 7, 18),
        (2017, 7, 21),
        (2017, 7, 25),
        (2017, 7, 27),
        (2017, 7, 28),
        (2017, 8, 2),
        (2017, 8, 3),
        (2017, 8, 11),
        (2017, 8, 25),
        (2017, 10, 17),
        (2017, 10, 27),
        (2017, 11, 2),
        (2017, 11, 3),
        (2017, 11, 10),
        (2017, 12, 7),
        # 2018 (29 sessions)
        (2018, 1, 23),
        (2018, 2, 1),
        (2018, 2, 2),
        (2018, 2, 8),
        (2018, 2, 9),
        (2018, 3, 16),
        (2018, 4, 17),
        (2018, 4, 24),
        (2018, 4, 26),
        (2018, 4, 27),
        (2018, 5, 4),
        (2018, 5, 11),
        (2018, 6, 8),
        (2018, 7, 17),
        (2018, 7, 20),
        (2018, 7, 24),
        (2018, 7, 26),
        (2018, 7, 27),
        (2018, 8, 1),
        (2018, 8, 2),
        (2018, 8, 17),
        (2018, 9, 7),
        (2018, 10, 17),
        (2018, 10, 25),
        (2018, 10, 26),
        (2018, 10, 31),
        (2018, 11, 2),
        (2018, 11, 16),
        (2018, 12, 7),
        # 2019 (28 sessions)
        (2019, 1, 18),
        (2019, 1, 30),
        (2019, 1, 31),
        (2019, 2, 1),
        (2019, 2, 5),
        (2019, 2, 15),
        (2019, 3, 15),
        (2019, 4, 17),
        (2019, 4, 25),
        (2019, 4, 26),
        (2019, 4, 30),
        (2019, 5, 1),
        (2019, 5, 17),
        (2019, 6, 14),
        (2019, 7, 18),
        (2019, 7, 19),
        (2019, 7, 25),
        (2019, 7, 26),
        (2019, 7, 31),
        (2019, 8, 16),
        (2019, 9, 13),
        (2019, 10, 17),
        (2019, 10, 24),
        (2019, 10, 25),
        (2019, 10, 29),
        (2019, 10, 31),
        (2019, 11, 15),
        (2019, 12, 13),
        # 2020 (24 sessions)
        (2020, 1, 22),
        (2020, 1, 29),
        (2020, 1, 30),
        (2020, 1, 31),
        (2020, 2, 4),
        (2020, 2, 14),
        (2020, 3, 13),
        (2020, 4, 22),
        (2020, 4, 29),
        (2020, 4, 30),
        (2020, 5, 1),
        (2020, 5, 22),
        (2020, 6, 5),
        (2020, 7, 17),
        (2020, 7, 23),
        (2020, 7, 31),
        (2020, 8, 20),
        (2020, 9, 4),
        (2020, 10, 21),
        (2020, 10, 22),
        (2020, 10, 28),
        (2020, 10, 30),
        (2020, 11, 19),
        (2020, 12, 11),
        # 2021 (26 sessions)
        (2021, 1, 20),
        (2021, 1, 27),
        (2021, 1, 28),
        (2021, 2, 3),
        (2021, 2, 25),
        (2021, 3, 5),
        (2021, 4, 21),
        (2021, 4, 27),
        (2021, 4, 28),
        (2021, 4, 29),
        (2021, 4, 30),
        (2021, 5, 27),
        (2021, 6, 4),
        (2021, 7, 21),
        (2021, 7, 27),
        (2021, 7, 28),
        (2021, 7, 29),
        (2021, 7, 30),
        (2021, 8, 19),
        (2021, 9, 3),
        (2021, 10, 20),
        (2021, 10, 26),
        (2021, 10, 27),
        (2021, 10, 29),
        (2021, 11, 18),
        (2021, 12, 10),
        # 2022 (29 sessions)
        (2022, 1, 21),
        (2022, 1, 26),
        (2022, 1, 27),
        (2022, 1, 28),
        (2022, 2, 2),
        (2022, 2, 3),
        (2022, 2, 4),
        (2022, 2, 17),
        (2022, 3, 4),
        (2022, 4, 20),
        (2022, 4, 21),
        (2022, 4, 27),
        (2022, 4, 28),
        (2022, 4, 29),
        (2022, 5, 26),
        (2022, 7, 20),
        (2022, 7, 21),
        (2022, 7, 27),
        (2022, 7, 28),
        (2022, 7, 29),
        (2022, 8, 25),
        (2022, 9, 2),
        (2022, 10, 19),
        (2022, 10, 20),
        (2022, 10, 26),
        (2022, 10, 27),
        (2022, 10, 28),
        (2022, 11, 17),
        (2022, 12, 9),
        # 2023 (28 sessions)
        (2023, 1, 20),
        (2023, 1, 25),
        (2023, 1, 26),
        (2023, 2, 2),
        (2023, 2, 3),
        (2023, 2, 23),
        (2023, 3, 3),
        (2023, 4, 19),
        (2023, 4, 20),
        (2023, 4, 26),
        (2023, 4, 27),
        (2023, 4, 28),
        (2023, 5, 5),
        (2023, 5, 25),
        (2023, 6, 2),
        (2023, 7, 20),
        (2023, 7, 26),
        (2023, 7, 27),
        (2023, 8, 4),
        (2023, 8, 24),
        (2023, 9, 1),
        (2023, 10, 19),
        (2023, 10, 25),
        (2023, 10, 26),
        (2023, 10, 27),
        (2023, 11, 3),
        (2023, 11, 22),
        (2023, 12, 8),
        # 2024 (28 sessions)
        (2024, 1, 24),
        (2024, 1, 25),
        (2024, 1, 31),
        (2024, 2, 2),
        (2024, 2, 22),
        (2024, 3, 8),
        (2024, 4, 19),
        (2024, 4, 24),
        (2024, 4, 25),
        (2024, 4, 26),
        (2024, 5, 1),
        (2024, 5, 3),
        (2024, 5, 23),
        (2024, 6, 13),
        (2024, 7, 19),
        (2024, 7, 24),
        (2024, 7, 31),
        (2024, 8, 1),
        (2024, 8, 2),
        (2024, 8, 29),
        (2024, 9, 6),
        (2024, 10, 18),
        (2024, 10, 24),
        (2024, 10, 30),
        (2024, 10, 31),
        (2024, 11, 1),
        (2024, 11, 21),
        (2024, 12, 13),
        # 2025 (26 sessions)
        (2025, 1, 22),
        (2025, 1, 30),
        (2025, 1, 31),
        (2025, 2, 5),
        (2025, 2, 7),
        (2025, 2, 27),
        (2025, 3, 7),
        (2025, 4, 21),
        (2025, 4, 23),
        (2025, 4, 25),
        (2025, 5, 1),
        (2025, 5, 2),
        (2025, 5, 29),
        (2025, 6, 6),
        (2025, 7, 18),
        (2025, 7, 24),
        (2025, 7, 31),
        (2025, 8, 1),
        (2025, 8, 28),
        (2025, 9, 5),
        (2025, 10, 22),
        (2025, 10, 23),
        (2025, 10, 30),
        (2025, 10, 31),
        (2025, 11, 20),
        (2025, 12, 12),
        # 2026 (17 sessions)
        (2026, 1, 21),
        (2026, 1, 29),
        (2026, 1, 30),
        (2026, 2, 5),
        (2026, 2, 6),
        (2026, 2, 26),
        (2026, 3, 5),
        (2026, 4, 17),
        (2026, 4, 23),
        (2026, 4, 30),
        (2026, 5, 1),
        (2026, 5, 21),
        (2026, 6, 4),
        (2026, 7, 17),
        (2026, 7, 23),
        (2026, 7, 30),
        (2026, 7, 31),
        # 2026, from SEC EDGAR (module docstring, PROVENANCE): 7 sessions
        (2026, 8, 27),  # NVDA
        (2026, 9, 3),  # AVGO
        (2026, 10, 21),  # NFLX
        (2026, 10, 22),  # META, TSLA
        (2026, 10, 29),  # GOOGL, MSFT
        (2026, 10, 30),  # AMZN
        (2026, 11, 3),  # AAPL
    ]
)


def is_earnings_reaction_day(d: date) -> bool:
    """True if `d` (an Eastern-time calendar date) is a session that
    traded a mega-cap earnings reaction. See module docstring for what
    that means and why it is not the announcement date."""
    return d in EARNINGS_REACTION_DATES


def is_earnings_reaction_day_at(timestamp: datetime) -> bool:
    """True if `timestamp` falls on an earnings reaction day, converting
    to the Eastern calendar date first (see fomc_calendar's Join
    Semantics for why that conversion, and why naive input is treated
    as UTC)."""
    if timestamp.tzinfo is None:
        timestamp = timestamp.replace(tzinfo=UTC)
    return is_earnings_reaction_day(timestamp.astimezone(EASTERN_TZ).date())


def read_later_reaction_dates(path: Path | str) -> frozenset[date]:
    """The reaction sessions in `path` (`date,symbols` rows) dated after
    the list's last entry, for the companies in MEGA_CAP_SYMBOLS. A file
    that is missing or unreadable, and a row that is not a date, give
    nothing: the list then stands alone."""
    last = max(EARNINGS_REACTION_DATES)
    found = set()
    try:
        lines = Path(path).read_text(encoding="utf-8").splitlines()
    except OSError:
        return frozenset()
    for line in lines[1:]:
        day_text, _, symbols = line.partition(",")
        try:
            day = date.fromisoformat(day_text.strip())
        except ValueError:
            continue
        if day > last and day.weekday() < 5 and set(symbols.split()) & set(MEGA_CAP_SYMBOLS):
            found.add(day)
    return frozenset(found)


def reaction_file() -> Path:
    """data/external/earnings_reaction_days.csv, or VAI_EXTERNAL_DIR's."""
    named = os.environ.get(EXTERNAL_DIR_ENV)
    root = Path(named) if named else Path(__file__).resolve().parents[2] / "data" / "external"
    return root / REACTION_FILE


@lru_cache(maxsize=1)
def later_reaction_dates() -> frozenset[date]:
    """read_later_reaction_dates(reaction_file()), read once a process: a
    live loop is one session, started cold."""
    return read_later_reaction_dates(reaction_file())


def is_live_earnings_reaction_day_at(
    timestamp: datetime, later: frozenset[date] | None = None
) -> bool:
    """is_earnings_reaction_day_at for a LIVE loop: the list, or a session
    after it in `later` (default: later_reaction_dates()). See the module
    docstring, LIVE."""
    if timestamp.tzinfo is None:
        timestamp = timestamp.replace(tzinfo=UTC)
    day = timestamp.astimezone(EASTERN_TZ).date()
    if is_earnings_reaction_day(day):
        return True
    return day in (later_reaction_dates() if later is None else later)
