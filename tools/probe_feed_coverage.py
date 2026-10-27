#!/usr/bin/env python
"""
How often does Alpaca's feed have a bar in Fidelity's extended windows?

    python tools/probe_feed_coverage.py --symbol RSP --sessions 10 [--feed iex] [--compare sip]

--------------------------------------------------------------------
WHY THIS EXISTS

A deployment on Fidelity's windows (live.sessions) trades 07:00-09:28 and
16:00-20:00 ET as well as the regular session. The loop decides on Alpaca's
minute bars, and on the free IEX feed a pre-market minute often has no trade
at all -- a minute with no bar is a minute the strategy cannot act on. The
second source (Fidelity's quote, live.secondary_feed) is there to fill those
gaps; this says how many there are to fill, per window, before relying on it.

With --compare sip the same minutes are counted on the consolidated feed
(free for history older than 15 minutes), which is what the warehouse's bars
and so every backtest are: how far the live feed is from the researched one.

Read-only: fetches bars and prints counts. Needs APCA_API_KEY_ID /
APCA_API_SECRET_KEY in the environment (any paper key).
"""

from __future__ import annotations

import argparse
import sys
from datetime import UTC, date, datetime, timedelta
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from engine.core.trading_calendar import EASTERN
from engine.core.venue_sessions import SESSIONS, VenueCalendar


def coverage(stamps, calendar: VenueCalendar) -> dict:
    """{(day, session): (minutes with a bar, minutes in the window)} for the
    windows `stamps` (UTC minute-bar timestamps) fall in, and every window of
    their days."""
    days = sorted({stamp.astimezone(EASTERN).date() for stamp in stamps})
    seen: dict = {}
    for stamp in stamps:
        session = calendar.session_at(stamp)
        if session in SESSIONS:
            key = (stamp.astimezone(EASTERN).date(), session)
            seen[key] = seen.get(key, 0) + 1
    table = {}
    for day in days:
        for window in calendar.windows(day):
            minutes = int((window.end - window.start).total_seconds() // 60)
            table[(day, window.session)] = (seen.get((day, window.session), 0), minutes)
    return table


def _fetch(symbol: str, sessions: int, feed: str):
    from engine.core.secrets import load_live_credentials
    from engine.data.historical_data import AlpacaHistoricalData, FetchSpec

    end = datetime.now(UTC) - timedelta(minutes=16)
    spec = FetchSpec(
        symbol=symbol,
        start=end - timedelta(days=int(sessions * 1.5) + 7),
        end=end,
        timeframe="1Min",
        feed=feed,
        adjustment="all",
        regular_hours_only=False,
    )
    frame, _, _ = AlpacaHistoricalData(credentials=load_live_credentials()).fetch_bars(spec)
    return [ts.to_pydatetime() for ts in frame.index]


def last_days(stamps, sessions: int, today: date) -> set[date]:
    """The last `sessions` finished days with a bar; today is not finished yet."""
    days = sorted({s.astimezone(EASTERN).date() for s in stamps} - {today})
    return set(days[-sessions:])


def on_days(stamps, days: set[date]) -> list:
    return [s for s in stamps if s.astimezone(EASTERN).date() in days]


def _report(name: str, table: dict, other: dict | None) -> None:
    print(f"\n{name}: minutes with a bar / minutes in the window")
    print(f"{'session':12} " + " ".join(f"{s:>16}" for s in SESSIONS))
    for day in sorted({day for day, _ in table}):
        cells = []
        for session in SESSIONS:
            have, of = table.get((day, session), (0, 0))
            cell = f"{have}/{of}"
            if other is not None:
                cell += f" ({other.get((day, session), (0, 0))[0]})"
            cells.append(f"{cell:>16}")
        print(f"{day.isoformat():12} " + " ".join(cells))
    for session in SESSIONS:
        have = sum(v[0] for (_, s), v in table.items() if s == session)
        of = sum(v[1] for (_, s), v in table.items() if s == session)
        print(f"  {session:12} {have / of:6.1%} of minutes have a bar" if of else "")


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__.split("\n\n")[1])
    p.add_argument("--symbol", default="RSP")
    p.add_argument("--sessions", type=int, default=10)
    p.add_argument("--feed", default="iex")
    p.add_argument("--compare", default=None, help="another feed to count beside it, e.g. sip")
    p.add_argument("--venue", default="fidelity", choices=("fidelity", "alpaca"))
    args = p.parse_args(argv)

    calendar = VenueCalendar(args.venue, SESSIONS)
    stamps = _fetch(args.symbol, args.sessions, args.feed)
    # Both feeds are counted on the same days, so a column is a like-for-like comparison.
    days = last_days(stamps, args.sessions, datetime.now(EASTERN).date())
    table = coverage(on_days(stamps, days), calendar)
    other = None
    if args.compare:
        other = coverage(on_days(_fetch(args.symbol, args.sessions, args.compare), days), calendar)
    label = f"{args.symbol} on {args.feed}" + (f" ({args.compare} in brackets)" if other else "")
    _report(label, table, other)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
