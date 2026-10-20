"""
Recent session history for a live strategy, fetched before its first tick.

--------------------------------------------------------------------
WHY A LIVE LOOP NEEDS HISTORY AT ALL

A backtest carries every strategy's state from one bar to the next for
years. A live deployment does not: the market-hours supervisor starts a
fresh process for every session, so each morning began with every
in-memory window empty --

  * the champion's volatility and volume windows (10 sessions) sized
    every lot as if the session had just begun, which is the one moment
    the backtest sizes DOWN hardest;
  * the Ultimate algorithm's volatility regime carries no flag for its
    first ~250 sessions, so it bought nothing at all;
  * and even with the regime seeded, Ultimate started each session with
    no mode, so a flip to turbulent -- the trigger for its regime exit --
    could never be seen, and its reversal signal had no previous close.

LiveTradingLoop replays what this module returns through the strategy's
record_tick before the first live tick, so the process starts in the state
a continuous run would have reached.

--------------------------------------------------------------------
WHAT IS FETCHED, AND WHY EACH CHOICE

  * Regular-session minute bars: every backtest this project ran saw
    nothing else, and the session-based state (daily ranges, the previous
    close) is defined on them.
  * The live loop's OWN feed. Mixing feeds would skew every fast/slow
    ratio: IEX volume is a small fraction of the consolidated tape's, so
    SIP history followed by IEX ticks reads as volume collapsing.
  * Adjusted for splits and dividends ("all"), as the warehouse bars every
    sweep ran on are: a split inside the window would otherwise read as a
    crash to a range-based regime. Adjustment rescales only bars before
    each event, so the latest history meets the live price on one basis.
  * The last `sessions` completed sessions plus today's bars so far. A
    process restarted mid-session resumes with the morning already seen,
    including a regime exit that was due at minute 60.
"""

from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from zoneinfo import ZoneInfo

import pandas as pd

EASTERN = ZoneInfo("America/New_York")

# Calendar days requested per session wanted: 252 sessions fall in 365 days,
# so 1.5 leaves room for holidays; the floor covers a long weekend.
_CALENDAR_DAYS_PER_SESSION = 1.5
_MIN_CALENDAR_DAYS = 10
# Alpaca refuses SIP bars from the last 15 minutes on a free subscription.
_SIP_DELAY = timedelta(minutes=16)


def last_sessions(bars: pd.DataFrame, sessions: int, today) -> pd.DataFrame:
    """The bars of the last `sessions` sessions before `today` (an Eastern
    date), plus every bar of `today` itself. Sessions are Eastern dates."""
    if bars.empty:
        return bars
    dates = bars.index.tz_convert(EASTERN).date
    earlier = sorted({day for day in dates if day < today})[-sessions:] if sessions > 0 else []
    keep = set(earlier) | {today}
    return bars[[day in keep for day in dates]]


class AlpacaSessionHistory:
    """LiveTradingLoop's history_provider, over Alpaca's historical bars.

    `fetcher` is an engine.data.historical_data.AlpacaHistoricalData (any
    object with its fetch_bars(spec) -> (frame, ...) contract).
    """

    def __init__(
        self,
        fetcher,
        *,
        feed: str,
        now: Callable[[], datetime] = lambda: datetime.now(UTC),
    ) -> None:
        self._fetcher = fetcher
        self._feed = feed
        self._now = now

    def __call__(self, symbol: str, sessions: int) -> pd.DataFrame:
        from engine.data.historical_data import FetchSpec

        now = self._now()
        end = now - _SIP_DELAY if self._feed == "sip" else now
        days = max(_MIN_CALENDAR_DAYS, int(sessions * _CALENDAR_DAYS_PER_SESSION) + 7)
        spec = FetchSpec(
            symbol=symbol,
            start=end - timedelta(days=days),
            end=end,
            timeframe="1Min",
            feed=self._feed,
            adjustment="all",
            regular_hours_only=True,
        )
        frame, _, _ = self._fetcher.fetch_bars(spec)
        return last_sessions(frame, sessions, today=now.astimezone(EASTERN).date())


__all__ = ["EASTERN", "AlpacaSessionHistory", "last_sessions"]
