"""strategy_registry.session_bars: a regular-session strategy backtested on a
fund kept with extended hours sees only the regular session's bars."""

from __future__ import annotations

import pandas as pd

from research.strategies.strategy_registry import STRATEGIES, session_bars


def _day_with_extended_hours() -> pd.DataFrame:
    index = (
        pd.date_range("2026-10-21 04:00", "2026-10-21 19:59", freq="1min", tz="America/New_York")
        .tz_convert("UTC")
        .rename("timestamp")
    )
    return pd.DataFrame(
        {"open": 1.0, "high": 1.0, "low": 1.0, "close": 1.0, "volume": 1}, index=index
    )


def test_the_ultimate_family_sees_only_the_regular_session():
    bars = _day_with_extended_hours()
    for strategy_id in ("ultimate", "ultimate_rsp", "ultimate_ursp"):
        kept = session_bars(STRATEGIES[strategy_id], bars)
        local = kept.index.tz_convert("America/New_York")
        assert len(kept) == 390, strategy_id
        assert (local[0].strftime("%H:%M"), local[-1].strftime("%H:%M")) == ("09:30", "15:59")


def test_every_other_strategy_sees_every_bar():
    bars = _day_with_extended_hours()
    for strategy_id in ("fixed", "hf_local_reference", "rsi", "bell_curve"):
        assert session_bars(STRATEGIES[strategy_id], bars) is bars
