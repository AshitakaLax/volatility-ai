"""
Session-over-session change in an implied-volatility series, as an
as-of-joinable signal.

--------------------------------------------------------------------
WHAT THIS IS, AND WHAT IT IS NOT

Every volatility signal this project has measures REALIZED volatility
from the traded instrument's own past bars. `vol_scale_exponent` is the
most valuable thing measured anywhere here (+13.05pp, against ~1-2pp for
each event calendar), and it is backward-looking by construction.
src/high_frequency_sizing.py states the consequence:

    "That scaler is backward-looking and structurally lags the open:
     even its shortest window (0.25 days = 97 bars) is still mostly
     describing yesterday afternoon at 09:30, so it cannot react to the
     open's volatility until most of the open is already gone."

This carries the market's own forward estimate instead. It is NOT a
second realized-vol measure wearing a different hat, and that was
established by measurement rather than assumed -- see below.

--------------------------------------------------------------------
IT IS THE CHANGE, NOT THE LEVEL AND NOT THE RATIO

tools/measure_vol_signal.py measured all three against next-session
volatility on 2,671 sessions, and the answer was not the obvious one:

                        raw    partial|rv_ratio   partial|rv_fast
    implied level     -0.180        -0.188            -0.085
    implied 1d change +0.119        +0.136            +0.257
    implied 5/60 ratio+0.429        +0.277            -0.039

  * The RATIO looks like the winner against the realized 5/60 ratio
    (+0.277) and collapses to -0.039 against trailing realized vol. The
    first control is much the weaker predictor (rho +0.41 vs +0.79), so
    the ratio was only re-encoding volatility persistence the incumbent
    already had. Rejected.
  * The LEVEL is negatively correlated, which is roll decay, not signal:
    a VIX-futures ETF drifts down for structural reasons while
    volatility does not trend, so levels are not comparable across
    years. Unusable.
  * The 1-DAY CHANGE strengthens under the harder control (+0.136 ->
    +0.257) on both full-day and opening-volatility targets. That is the
    shape of genuine new information: a jump in implied vol today is
    news about tomorrow that yesterday's realized vol cannot contain.

So this module carries exactly one quantity, the change, because that is
the only one that survived.

--------------------------------------------------------------------
NO LOOKAHEAD, BY CONSTRUCTION

The change across session d is fully known only at d's close, so it is
published to the as-of series at **midnight Eastern on the day AFTER d**.
Every bar of the next session -- pre-market included -- therefore reads a
value that was already history when that session opened.

Publishing at "the next session's open" was rejected: it requires
knowing the next session date, which means a market calendar this
project deliberately does not keep (src/alpaca_market_data.py: "a
hand-rolled schedule gets wrong a handful of days a year -- exactly the
days an unattended 24/7 process would be trading against a closed
book"). Midnight-after-d needs no calendar and is never later than the
next session, so a Friday close is read by Monday's bars with nothing
in between to read it early.

--------------------------------------------------------------------
THE JOIN IS NOT REIMPLEMENTED

src/external_index_series.py already provides the as-of lookup, with
matching scalar()/vectorized() pinned equal by test. This module only
BUILDS the series; ExternalIndexSeries joins it. Writing a second
searchsorted here would be a second thing to keep correct.

--------------------------------------------------------------------
THE SERIES IS A PROXY UNTIL VXN IS REACHABLE

The right input is VXN -- Nasdaq-100 implied volatility, the index TQQQ
tracks 3x -- from hfmarketdata.io. That provider was unreachable when
this was written (HTTP 000 after 25s while control hosts answered in
1.5s; src/hf_market_data.py documents the same outage mode). VIXY was
used instead: VIX (S&P 500) rather than VXN, and VIX FUTURES via an ETF
wrapper rather than spot. Nothing here is VIXY-specific -- point it at a
VXN file when the provider returns and re-run the measurement before
trusting the tuned parameters.
"""

from __future__ import annotations

from datetime import timedelta

import numpy as np
import pandas as pd

from src.exceptions import DataValidationError
from src.external_index_series import ExternalIndexSeries
from src.fomc_calendar import EASTERN_TZ

# The column ExternalIndexSeries is told to read. Named for what it
# holds rather than left as "close", which it emphatically is not.
CHANGE_COLUMN = "iv_change_pct"

# What a bar sees when no prior session change is known yet -- the first
# session of the series, or any bar before it. 0.0 means "no change",
# which is the correct no-op: the consumer's multiplier is 1.0 there.
NO_SIGNAL = 0.0


def build_session_change_series(bars: pd.DataFrame, *, value_column: str = "close") -> pd.DataFrame:
    """Turn implied-vol bars into an as-of-joinable change series.

    Returns a frame indexed by the UTC instant at which each change
    BECAME KNOWN, carrying CHANGE_COLUMN as a percentage.
    """
    if bars.empty:
        raise DataValidationError("build_session_change_series given no bars.")
    if value_column not in bars.columns:
        raise DataValidationError(
            f"build_session_change_series: column {value_column!r} not found in "
            f"{list(bars.columns)}"
        )
    index = pd.DatetimeIndex(bars.index)
    if index.tz is None:
        raise DataValidationError(
            "build_session_change_series requires a tz-aware index; a naive one leaves "
            "the session boundary undefined."
        )

    eastern = index.tz_convert(EASTERN_TZ)
    session_dates = np.array(eastern.date)
    closes = bars[value_column].groupby(session_dates).last().sort_index()
    if len(closes) < 2:
        raise DataValidationError(
            f"Need at least two sessions to compute a change, got {len(closes)}."
        )

    change_pct = (closes / closes.shift(1) - 1.0) * 100.0

    # Published at midnight Eastern the day AFTER the session whose close
    # produced it -- see the module docstring on why not "the next
    # session's open".
    available_at = pd.DatetimeIndex(
        [pd.Timestamp(d + timedelta(days=1), tz=EASTERN_TZ) for d in change_pct.index]
    ).tz_convert("UTC")

    frame = pd.DataFrame({CHANGE_COLUMN: change_pct.to_numpy()}, index=available_at)
    frame.index.name = "timestamp"
    return frame.dropna()


def load_implied_vol_change(path, *, value_column: str = "close") -> ExternalIndexSeries:
    """Read an implied-vol minute CSV and return the joinable change series."""
    bars = pd.read_csv(path, parse_dates=["timestamp"]).set_index("timestamp")
    if bars.index.tz is None:
        bars.index = bars.index.tz_localize("UTC")
    return ExternalIndexSeries(
        build_session_change_series(bars, value_column=value_column),
        value_column=CHANGE_COLUMN,
    )


def changes_for_index(series: ExternalIndexSeries | None, index: pd.DatetimeIndex) -> np.ndarray:
    """Vectorized per-bar changes, NO_SIGNAL where nothing is known yet.

    NaN is converted here rather than left to the caller: every
    construction site would otherwise repeat the same fillna, and one of
    them would eventually forget and feed NaN into a multiplier.
    """
    if series is None:
        return np.full(len(index), NO_SIGNAL, dtype=float)
    return np.nan_to_num(series.vectorized(index), nan=NO_SIGNAL)


def change_at(series: ExternalIndexSeries | None, timestamp) -> float:
    """Scalar twin of changes_for_index, for the live and replay paths."""
    if series is None:
        return NO_SIGNAL
    value = series.scalar(timestamp)
    return NO_SIGNAL if value is None else float(value)
