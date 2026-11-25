"""
Pre-market inputs observable at ~4:20am ET from free sources -- the pure
calculations, ported from the pre-market forecast generator
(chronos_service/market_inputs.py) so both compute the same values.

  overnight futures change   the latest 1-minute index-futures close against
                             the futures price at the last completed
                             session's 16:00 ET cash close (the 15:59 bar,
                             the end of CME's settlement window). Yahoo's
                             futures quotes are about 10 minutes delayed.
  overnight VIX              Cboe disseminates VIX from 03:15 ET; Yahoo's
                             1-minute bars with pre/post carry those prints
                             about 15 minutes late.
  Cboe daily index closes    VIX9D, VIX3M, VXN, RVX..., posted ~17:30 ET the
                             same day. CLOSE only: VIX's OPEN is the 03:15
                             overnight print and intraday LOWs carry bad
                             prints.

These are snapshot and display values. They must NOT become model
covariates: no history exists at the same 4:20am clock time (Yahoo keeps
about seven days of 1-minute bars), so training on them would read the
future (research/CLAUDE.md, the causal-transform rule).

Nothing here touches the network; research/forecast_generator/market_data.py
fetches.
"""

from __future__ import annotations

from datetime import date, datetime, timedelta
from datetime import time as clock_time
from typing import Any

import pandas as pd

from engine.core.trading_calendar import EASTERN, SESSION_CLOSE

OVERNIGHT_VIX_START = clock_time(3, 15)
REGULAR_OPEN = clock_time(9, 30)

# Cboe symbol for each volatility index, with the Yahoo daily ticker to fall
# back on. ^RVX is no longer served by Yahoo ("symbol may be delisted"), so
# RVX has no fallback.
CBOE_INDEX_SOURCES: dict[str, dict[str, str | None]] = {
    "^VIX": {"cboe": "VIX", "yahoo_fallback": "^VIX"},
    "^VXN": {"cboe": "VXN", "yahoo_fallback": "^VXN"},
    "^RVX": {"cboe": "RVX", "yahoo_fallback": None},
    "^VIX9D": {"cboe": "VIX9D", "yahoo_fallback": "^VIX9D"},
    "^VIX3M": {"cboe": "VIX3M", "yahoo_fallback": "^VIX3M"},
}


def overnight_futures_change(
    closes: pd.Series,
    session_date: date,
    now_et: datetime,
    close_time: clock_time = SESSION_CLOSE,
    max_stale_minutes: float = 60.0,
) -> dict[str, Any]:
    """True overnight futures change (percent) against the cash close on
    `session_date`.

    The reference is the last bar in the ten minutes before `close_time`.
    With no bar there -- an early close, when futures halt at 13:15 ET and
    the calendar here does not model it -- the change is reported as
    unavailable rather than measured from the wrong time."""
    result: dict[str, Any] = {"change_pct": None, "latest": None, "reference": None, "reason": None}
    if closes.empty:
        result["reason"] = "no futures bars"
        return result
    close_at = datetime.combine(session_date, close_time, tzinfo=EASTERN)
    window = closes[(closes.index >= close_at - timedelta(minutes=10)) & (closes.index < close_at)]
    if window.empty:
        result["reason"] = (
            f"no futures bar in the ten minutes before {close_time:%H:%M} ET on {session_date}"
        )
        return result
    result["reference"] = (window.index[-1], float(window.iloc[-1]))
    after = closes[(closes.index >= close_at) & (closes.index <= now_et)]
    if after.empty:
        result["reason"] = "no futures bar after the reference close"
        return result
    latest_ts = after.index[-1]
    result["latest"] = (latest_ts, float(after.iloc[-1]))
    age_minutes = (now_et - latest_ts.to_pydatetime()).total_seconds() / 60.0
    if age_minutes > max_stale_minutes:
        result["reason"] = (
            f"latest futures bar is {age_minutes:.0f} minutes old (limit {max_stale_minutes:.0f})"
        )
        return result
    result["change_pct"] = (float(after.iloc[-1]) / float(window.iloc[-1]) - 1.0) * 100.0
    return result


def overnight_vix_window_open(now_et: datetime) -> bool:
    """From 03:30 ET (the first 03:15 print plus Yahoo's ~15-minute delay)
    to the 09:30 open on weekdays."""
    return now_et.weekday() < 5 and clock_time(3, 30) <= now_et.time() < REGULAR_OPEN


def latest_overnight_vix(
    closes: pd.Series, today_et: date, base_session_date: date, now_et: datetime | None = None
) -> tuple[pd.Timestamp, float] | None:
    """The last VIX print on `today_et` between 03:15 and 09:29 ET, when
    `today_et` is after the base session."""
    if closes.empty or today_et <= base_session_date:
        return None
    start = datetime.combine(today_et, OVERNIGHT_VIX_START, tzinfo=EASTERN)
    end = datetime.combine(today_et, REGULAR_OPEN, tzinfo=EASTERN)
    window = closes[(closes.index >= start) & (closes.index < end)]
    if now_et is not None:
        window = window[window.index <= now_et]
    if window.empty:
        return None
    return window.index[-1], float(window.iloc[-1])


def closes_through(series: pd.Series, as_of: date) -> pd.Series:
    return series[[index <= as_of for index in series.index]]


def iv_rank_pct(series: pd.Series, as_of: date, window: int = 252) -> float | None:
    """(last - min) / (max - min) x 100 over the trailing `window` closes
    ending on or before `as_of`."""
    tail = closes_through(series, as_of).tail(window)
    if len(tail) < window:
        return None
    lo, hi = float(tail.min()), float(tail.max())
    if not hi > lo:
        return None
    return (float(tail.iloc[-1]) - lo) / (hi - lo) * 100.0


def choose_daily_series(candidates: list[dict[str, Any]], as_of: date) -> dict[str, Any] | None:
    """The candidate whose latest close on or before `as_of` is newest;
    earlier candidates win ties."""
    best: dict[str, Any] | None = None
    for candidate in candidates:
        series = candidate.get("series")
        if series is None or len(series) == 0:
            continue
        through = closes_through(series, as_of)
        if through.empty:
            continue
        latest_date = through.index[-1]
        if best is None or latest_date > best["latest_date"]:
            best = {
                "source": candidate["source"],
                "ticker": candidate["ticker"],
                "series": through,
                "latest_date": latest_date,
                "latest": float(through.iloc[-1]),
            }
    return best


def iso_utc(timestamp: pd.Timestamp | datetime) -> str:
    return pd.Timestamp(timestamp).tz_convert("UTC").strftime("%Y-%m-%dT%H:%M:%SZ")


def daily_observation(field: str, source: str, ticker: str, session_date: date) -> dict[str, Any]:
    """Where a daily-close input came from: the session it closed."""
    return {
        "field": field,
        "source": source,
        "ticker": ticker,
        "kind": "daily_close",
        "observed_at": None,
        "session_date": session_date.isoformat(),
        "reference_observed_at": None,
    }


def intraday_observation(
    field: str,
    ticker: str,
    timestamp: pd.Timestamp,
    reference_timestamp: pd.Timestamp | None = None,
) -> dict[str, Any]:
    """Where an intraday input came from: the bar it was read at (and the
    bar it is measured against, for a change)."""
    return {
        "field": field,
        "source": "yahoo_chart_1m",
        "ticker": ticker,
        "kind": "intraday_bar",
        "observed_at": iso_utc(timestamp),
        "session_date": pd.Timestamp(timestamp).tz_convert(EASTERN).date().isoformat(),
        "reference_observed_at": (
            iso_utc(reference_timestamp) if reference_timestamp is not None else None
        ),
    }


__all__ = [
    "CBOE_INDEX_SOURCES",
    "OVERNIGHT_VIX_START",
    "REGULAR_OPEN",
    "choose_daily_series",
    "closes_through",
    "daily_observation",
    "intraday_observation",
    "iso_utc",
    "iv_rank_pct",
    "latest_overnight_vix",
    "overnight_futures_change",
    "overnight_vix_window_open",
]
