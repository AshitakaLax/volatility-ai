"""Tests for EarningsEventTable.

The property that matters most: scalar() (the live path) and
vectorized() (the backtest path) must agree on every bar, or the two
execution paths would trade on different information for the same
timestamp -- exactly the divergence src/decision_cycle.py exists to
prevent for the rest of the sequence.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from src.event_calendar import (
    DEFAULT_EARNINGS_CSV,
    DEFAULT_LEAD_MINUTES,
    NO_EVENT_MINUTES,
    EarningsEventTable,
)
from src.exceptions import ConfigurationError, DataValidationError
from src.index_weights import weight_pct


def events(*rows: tuple[str, str]) -> pd.DataFrame:
    """rows of (symbol, 'YYYY-MM-DD HH:MM' UTC)."""
    return pd.DataFrame(
        {
            "symbol": [r[0] for r in rows],
            "release_utc": pd.to_datetime([r[1] for r in rows], utc=True),
        }
    )


def minute_index(start: str, n: int) -> pd.DatetimeIndex:
    return pd.date_range(start, periods=n, freq="1min", tz="UTC")


# --- basic window shape ---


def test_zero_before_the_lead_window_opens():
    t = EarningsEventTable(events(("NVDA", "2024-06-03 21:00")))  # NVDA 8.50%
    intensity, minutes = t.scalar(pd.Timestamp("2024-06-03 20:44", tz="UTC"))
    assert intensity == 0.0
    assert minutes == NO_EVENT_MINUTES


def test_weighted_at_the_instant_the_lead_window_opens():
    t = EarningsEventTable(events(("NVDA", "2024-06-03 21:00")), lead_minutes=15.0)
    intensity, minutes = t.scalar(pd.Timestamp("2024-06-03 20:45", tz="UTC"))
    assert intensity == pytest.approx(weight_pct("NVDA"))
    assert minutes == pytest.approx(15.0)


def test_countdown_decreases_toward_the_release():
    t = EarningsEventTable(events(("NVDA", "2024-06-03 21:00")), lead_minutes=15.0)
    _, minutes = t.scalar(pd.Timestamp("2024-06-03 20:59", tz="UTC"))
    assert minutes == pytest.approx(1.0)


def test_minutes_to_event_is_the_sentinel_once_released():
    """Awareness is a countdown to something that has not happened;
    once it has, intensity carries the signal, not a frozen countdown."""
    t = EarningsEventTable(events(("NVDA", "2024-06-03 21:00")), reaction_minutes=30.0)
    intensity, minutes = t.scalar(pd.Timestamp("2024-06-03 21:00", tz="UTC"))
    assert intensity == pytest.approx(weight_pct("NVDA"))
    assert minutes == NO_EVENT_MINUTES


def test_intensity_stays_weighted_through_the_reaction_window():
    t = EarningsEventTable(events(("NVDA", "2024-06-03 21:00")), reaction_minutes=30.0)
    intensity, _ = t.scalar(pd.Timestamp("2024-06-03 21:29", tz="UTC"))
    assert intensity == pytest.approx(weight_pct("NVDA"))


def test_zero_after_the_reaction_window_closes():
    t = EarningsEventTable(events(("NVDA", "2024-06-03 21:00")), reaction_minutes=30.0)
    intensity, minutes = t.scalar(pd.Timestamp("2024-06-03 21:30", tz="UTC"))
    assert intensity == 0.0
    assert minutes == NO_EVENT_MINUTES


# --- overlapping events sum, not max ---


def test_two_overlapping_releases_sum_their_weights():
    """Different companies reporting in the same window are independent
    exposure, unlike the day-level event flags' max() (see module
    docstring)."""
    t = EarningsEventTable(
        events(("NVDA", "2024-06-03 21:00"), ("AAPL", "2024-06-03 21:05")),
        lead_minutes=15.0,
        reaction_minutes=30.0,
    )
    intensity, _ = t.scalar(pd.Timestamp("2024-06-03 21:05", tz="UTC"))
    assert intensity == pytest.approx(weight_pct("NVDA") + weight_pct("AAPL"))


def test_the_nearer_of_two_pending_events_sets_the_countdown():
    t = EarningsEventTable(
        events(("NVDA", "2024-06-03 21:30"), ("AAPL", "2024-06-03 21:10")),
        lead_minutes=60.0,
    )
    _, minutes = t.scalar(pd.Timestamp("2024-06-03 21:00", tz="UTC"))
    assert minutes == pytest.approx(10.0)  # AAPL is 10 min out, NVDA 30


# --- an untracked symbol contributes zero weight, not an error ---


def test_an_untracked_symbol_has_zero_weight_but_still_an_event():
    t = EarningsEventTable(events(("ZZZZ", "2024-06-03 21:00")), lead_minutes=15.0)
    intensity, minutes = t.scalar(pd.Timestamp("2024-06-03 20:50", tz="UTC"))
    assert intensity == 0.0
    assert minutes == pytest.approx(10.0)


# --- scalar/vectorized agreement -- the property that matters most ---


def test_scalar_and_vectorized_agree_on_every_bar():
    t = EarningsEventTable(
        events(("NVDA", "2024-06-03 21:20"), ("AAPL", "2024-06-03 21:35")),
        lead_minutes=15.0,
        reaction_minutes=30.0,
    )
    idx = minute_index("2024-06-03 20:55", 90)

    vec_intensity, vec_minutes = t.vectorized(idx)
    for i, ts in enumerate(idx):
        s_intensity, s_minutes = t.scalar(ts)
        assert vec_intensity[i] == pytest.approx(s_intensity), f"intensity mismatch at {ts}"
        assert vec_minutes[i] == pytest.approx(s_minutes), f"minutes mismatch at {ts}"


def test_vectorized_output_length_matches_the_index():
    t = EarningsEventTable(events(("NVDA", "2024-06-03 21:00")))
    idx = minute_index("2024-06-03 20:00", 200)
    intensity, minutes = t.vectorized(idx)
    assert len(intensity) == len(idx) == len(minutes)


def test_vectorized_requires_a_tz_aware_index():
    t = EarningsEventTable(events(("NVDA", "2024-06-03 21:00")))
    naive = pd.date_range("2024-06-03 20:00", periods=10, freq="1min")
    with pytest.raises(DataValidationError, match="tz-aware"):
        t.vectorized(naive)


# --- construction validation ---


def test_empty_events_is_rejected():
    with pytest.raises(DataValidationError, match="empty"):
        EarningsEventTable(pd.DataFrame(columns=["symbol", "release_utc"]))


def test_naive_release_timestamps_are_rejected():
    df = pd.DataFrame({"symbol": ["NVDA"], "release_utc": pd.to_datetime(["2024-06-03 21:00"])})
    with pytest.raises(DataValidationError, match="tz-aware"):
        EarningsEventTable(df)


@pytest.mark.parametrize("kw", [{"lead_minutes": 0.0}, {"lead_minutes": -5.0}])
def test_non_positive_lead_minutes_is_rejected(kw):
    with pytest.raises(ConfigurationError, match="lead_minutes"):
        EarningsEventTable(events(("NVDA", "2024-06-03 21:00")), **kw)


@pytest.mark.parametrize("kw", [{"reaction_minutes": 0.0}, {"reaction_minutes": -1.0}])
def test_non_positive_reaction_minutes_is_rejected(kw):
    with pytest.raises(ConfigurationError, match="reaction_minutes"):
        EarningsEventTable(events(("NVDA", "2024-06-03 21:00")), **kw)


# --- the real derived dataset ---


@pytest.mark.skipif(
    not DEFAULT_EARNINGS_CSV.exists(),
    reason=(
        f"{DEFAULT_EARNINGS_CSV} is a GENERATED artifact and is gitignored. "
        "Build it with `python tools/build_earnings_calendar.py`."
    ),
)
def test_loads_and_is_internally_consistent_against_the_real_dataset():
    """Skipped when the derived CSV is absent, which is the documented
    contract rather than a convenience.

    src/event_calendar.py's own docstring calls this file "a generated
    artifact, not a committed one", and BOTH production callers --
    optimization_controller._load_event_table and LiveTradingLoop --
    catch FileNotFoundError and fall back to no events, because the
    consuming multiplier defaults to 1.0 so its absence is an exact
    no-op. The code was right and this test was not: it called from_csv
    unguarded, so it passed only on a machine that happened to have run
    the generator, and failed on every clean checkout -- which is every
    CI run.
    """
    t = EarningsEventTable.from_csv()
    assert t.event_count >= 400  # 676 at time of writing across 16 tickers

    idx = pd.date_range("2024-01-01", "2024-03-01", freq="1min", tz="UTC")
    intensity, minutes = t.vectorized(idx)
    assert (intensity >= 0).all()
    assert np.isfinite(intensity).all()
    # Every non-sentinel countdown must be within the lead window.
    pending = minutes != NO_EVENT_MINUTES
    assert (minutes[pending] >= 0).all()
    assert (minutes[pending] <= DEFAULT_LEAD_MINUTES).all()


def test_scalar_accepts_a_plain_datetime_not_only_pd_timestamp():
    """live_trading_loop.py passes datetime.datetime, not pd.Timestamp --
    they are not interchangeable (no .tz_convert on the former)."""
    import datetime as dt

    t = EarningsEventTable(events(("NVDA", "2024-06-03 21:00")), lead_minutes=15.0)
    plain = dt.datetime(2024, 6, 3, 20, 50, tzinfo=dt.UTC)
    intensity, minutes = t.scalar(plain)
    assert intensity == pytest.approx(weight_pct("NVDA"))
    assert minutes == pytest.approx(10.0)
