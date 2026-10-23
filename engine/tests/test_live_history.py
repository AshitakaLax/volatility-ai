"""engine/trading/live_history.py -- what a live loop is handed to replay
before its first tick: the right sessions, from the loop's own feed,
regular hours only, adjusted like the warehouse."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pandas as pd

from engine.trading.live_history import EASTERN, AlpacaSessionHistory, last_sessions


def _bars(days, times=("09:30", "12:00", "15:59")) -> pd.DataFrame:
    index = pd.DatetimeIndex(
        [pd.Timestamp(f"{day} {t}", tz=EASTERN) for day in days for t in times], name="timestamp"
    ).tz_convert("UTC")
    return pd.DataFrame(
        dict.fromkeys(("open", "high", "low", "close"), 100.0) | {"volume": 1}, index=index
    )


def _eastern_dates(frame) -> list:
    return sorted(set(frame.index.tz_convert(EASTERN).date))


def test_the_last_sessions_before_today_and_today_so_far():
    days = ["2026-10-12", "2026-10-13", "2026-10-14", "2026-10-15", "2026-10-16", "2026-10-19"]
    kept = last_sessions(_bars(days), 3, today=pd.Timestamp("2026-10-19").date())
    assert [str(d) for d in _eastern_dates(kept)] == [
        "2026-10-14",
        "2026-10-15",
        "2026-10-16",
        "2026-10-19",
    ]
    assert len(kept) == 4 * 3, "every bar of each kept session"


def test_sessions_are_eastern_dates_not_utc_ones():
    """A 19:30 ET bar is past midnight UTC in winter; it still belongs to
    the Eastern session it traded in."""
    frame = _bars(["2026-01-14", "2026-01-15"], times=("09:30", "19:30"))
    kept = last_sessions(frame, 1, today=pd.Timestamp("2026-01-16").date())
    assert [str(d) for d in _eastern_dates(kept)] == ["2026-01-15"]
    assert len(kept) == 2


class _Fetcher:
    def __init__(self, frame):
        self.frame = frame
        self.specs = []

    def fetch_bars(self, spec):
        self.specs.append(spec)
        return self.frame, 0, 0


NOW = datetime(2026, 10, 19, 14, 0, tzinfo=UTC)  # 10:00 ET


def test_fetches_the_loops_own_feed_adjusted_regular_hours_minutes():
    fetcher = _Fetcher(_bars(["2026-10-16", "2026-10-19"]))
    history = AlpacaSessionHistory(fetcher, feed="iex", now=lambda: NOW)
    frame = history("TQQQ", 20)
    (spec,) = fetcher.specs
    assert spec.symbol == "TQQQ"
    assert spec.feed == "iex"
    assert spec.adjustment == "all", "as the warehouse's bars are"
    assert spec.regular_hours_only is True
    assert spec.timeframe == "1Min"
    assert spec.end == NOW, "IEX history runs to now"
    assert (spec.end - spec.start) >= timedelta(days=30), "room for 20 sessions"
    assert len(frame) == 6


def test_sip_history_ends_outside_the_free_subscription_delay():
    fetcher = _Fetcher(_bars(["2026-10-16"]))
    AlpacaSessionHistory(fetcher, feed="sip", now=lambda: NOW)("TQQQ", 5)
    assert NOW - fetcher.specs[0].end >= timedelta(minutes=15)
