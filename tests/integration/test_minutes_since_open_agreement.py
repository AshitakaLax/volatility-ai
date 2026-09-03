"""time_of_day_flag: the vectorized and scalar implementations must agree.

WHY THIS FILE EXISTS. `minutes_since_open` is written twice, by hand:

    scalar      src/intraday_profile.py         (live, replay paths)
    vectorized  optimization_controller.py      (backtest)

The vectorized one's docstring asserts the property outright --

    "Uses the same Eastern conversion and the same 0-389 window as the
     scalar helper, so backtest and live cannot disagree about which
     minute a bar is."

-- and until this file, nothing checked it. The identical invariant for
the FOMC flags IS pinned, in
tests/integration/test_fomc_event_day_boost.py::test_the_vectorized_flag_cache_agrees_with_the_scalar_helper,
whose docstring gives the reason: "Two implementations of the same rule
can drift, so this pins that they agree bar-for-bar."

The stakes are higher here than for the calendars. time_of_day_flag
feeds src/intraday_profile.py's range profile, the largest effect
measured anywhere in this project (the open runs 2.56x the session
average). A one-minute drift between paths would silently mis-scale
every bar of a backtest relative to what live would have done, and
nothing else in the suite would notice.

DST is the case that would actually break: both implementations do
naive `hour * 60 + minute` arithmetic on an Eastern-converted timestamp,
so they agree only as long as they convert identically. The fixtures
below straddle both transitions on purpose.
"""

from __future__ import annotations

import pandas as pd
import pytest

from optimization_controller import OptimizationController
from src.intraday_profile import SESSION_MINUTES, minutes_since_open

# Both 2026 US DST transitions, plus an ordinary winter and summer day.
# 2026-03-08 is the spring-forward Sunday and 2026-11-01 the fall-back
# Sunday; the sessions either side are what a bar index actually holds.
DST_SPRING = ("2026-03-06", "2026-03-09")
DST_FALL = ("2026-10-30", "2026-11-02")
ORDINARY = ("2026-01-15", "2026-07-15")


def _session_bars(day: str) -> pd.DatetimeIndex:
    """A full 04:00-20:00 Eastern span at one-minute resolution, so the
    index covers pre-market, the regular session, and after-hours --
    the -1 sentinel outside 0-389 is as much a part of the contract as
    the in-session values."""
    return pd.date_range(
        f"{day} 04:00", f"{day} 19:59", freq="1min", tz="America/New_York"
    ).tz_convert("UTC")


def _frame(days) -> pd.DataFrame:
    index = pd.DatetimeIndex([]).append([_session_bars(d) for d in days]).sort_values()
    return pd.DataFrame(
        {"open": 50.0, "high": 50.5, "low": 49.5, "close": 50.0, "volume": 1000.0},
        index=index,
    )


@pytest.mark.parametrize(
    ("label", "days"),
    [("spring-forward", DST_SPRING), ("fall-back", DST_FALL), ("ordinary", ORDINARY)],
)
def test_the_vectorized_minute_cache_agrees_with_the_scalar_helper(label, days):
    frame = _frame(days)
    controller = OptimizationController(historical_data=frame)
    vectorized = controller._minutes_since_open

    assert len(vectorized) == len(frame)
    expected = [minutes_since_open(ts) for ts in frame.index]
    assert vectorized == expected, f"vectorized/scalar drift across {label}"


def test_the_fixture_actually_spans_in_session_and_out():
    """A fixture that never leaves the session, or never enters it, would
    pass the agreement test while checking almost nothing."""
    frame = _frame(ORDINARY)
    values = OptimizationController(historical_data=frame)._minutes_since_open

    assert any(v == -1 for v in values), "no out-of-session bars in the fixture"
    assert any(0 <= v < SESSION_MINUTES for v in values), "no in-session bars"
    assert min(values) == -1
    assert max(values) == SESSION_MINUTES - 1, "the last regular minute (15:59) is missing"


def test_the_session_boundary_lands_on_the_documented_minutes():
    """Pins the two edges by hand, so a drift that happened to be
    identical in BOTH implementations still fails here."""
    frame = _frame(("2026-01-15",))
    values = OptimizationController(historical_data=frame)._minutes_since_open
    index = frame.index.tz_convert("America/New_York")

    by_clock = {f"{ts.hour:02d}:{ts.minute:02d}": v for ts, v in zip(index, values, strict=False)}
    assert by_clock["09:29"] == -1, "09:29 is pre-market"
    assert by_clock["09:30"] == 0, "09:30 is minute zero"
    assert by_clock["15:59"] == SESSION_MINUTES - 1, "15:59 is the last regular minute"
    assert by_clock["16:00"] == -1, "16:00 is after the close"
