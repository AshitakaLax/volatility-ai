"""
Shared session aggregation for the analysis tools in tools/.

--------------------------------------------------------------------
WHY THIS EXISTS

Three tools written in quick succession -- measure_event_effects.py,
measure_vol_signal.py and measure_hedge_conditions.py -- each grew its
own copy of "read a minute CSV, keep regular hours, aggregate to one row
per session", each with the minute boundaries written out as bare
numbers (570, 630, 960).

Meanwhile src/intraday_profile.py already owns those boundaries as
SESSION_OPEN_MINUTE and SESSION_MINUTES, and optimization_controller.py
imports them rather than hardcoding. So the production engine shares one
definition of "which minute of the session is this" and the tools
measuring that engine each invented their own.

That is worse than ordinary duplication. These tools produce the
evidence that decides what gets built -- the event-calendar rejections,
the implied-vol wiring, the SQQQ hedge answer. A tool that disagreed
with the engine about which bars are in-session would silently be
measuring a different market than the one being traded, and the
disagreement would never surface as an error.

960 is not a constant at all: it is SESSION_OPEN_MINUTE +
SESSION_MINUTES, i.e. 16:00. Writing it as a literal is how a session
length change becomes a silent inconsistency.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from src.fomc_calendar import EASTERN_TZ
from src.intraday_profile import SESSION_MINUTES, SESSION_OPEN_MINUTE

# Derived, never written as literals -- see the module docstring.
SESSION_OPEN = SESSION_OPEN_MINUTE  # 09:30 Eastern
SESSION_CLOSE = SESSION_OPEN_MINUTE + SESSION_MINUTES  # 16:00 Eastern
OPEN_WINDOW_END = SESSION_OPEN_MINUTE + 60  # 10:30 Eastern


def minute_of_day(index: pd.DatetimeIndex) -> np.ndarray:
    """Minutes since midnight Eastern for each bar.

    Uses the same conversion src/intraday_profile.minutes_since_open and
    optimization_controller._minutes_since_open use, so a tool cannot
    disagree with the engine about which minute a bar falls in.
    """
    eastern = index.tz_convert(EASTERN_TZ)
    return eastern.hour * 60 + eastern.minute


def session_dates(index: pd.DatetimeIndex) -> np.ndarray:
    """Exchange-local calendar date per bar -- the session grouping key."""
    return np.array(index.tz_convert(EASTERN_TZ).date)


def load_minute_bars(
    path: str, columns=("high", "low", "close"), *, regular_hours_only: bool = True
) -> pd.DataFrame:
    """Read a minute CSV, optionally restricted to the regular session."""
    frame = pd.read_csv(
        path, parse_dates=["timestamp"], usecols=["timestamp", *columns]
    ).set_index("timestamp")
    if frame.index.tz is None:
        raise ValueError(
            f"{path} has timezone-naive timestamps; the session boundary would be "
            "undefined. Every file cli.py fetch-data writes is UTC-aware."
        )
    if regular_hours_only:
        minutes = minute_of_day(frame.index)
        frame = frame[(minutes >= SESSION_OPEN) & (minutes < SESSION_CLOSE)]
    return frame


def to_sessions(bars: pd.DataFrame) -> pd.DataFrame:
    """Aggregate minute bars to one row per session: high, low, close."""
    dates = session_dates(bars.index)
    out = pd.DataFrame(
        {
            "high": bars["high"].groupby(dates).max(),
            "low": bars["low"].groupby(dates).min(),
            "close": bars["close"].groupby(dates).last(),
        }
    )
    out.index.name = "session"
    return out


def session_bars(path: str) -> pd.DataFrame:
    """Regular-hours minute CSV -> one OHLC row per session."""
    return to_sessions(load_minute_bars(path))
