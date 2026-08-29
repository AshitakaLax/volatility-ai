"""
ExternalIndexSeries -- an as-of join for a level series sourced
independently of the primary instrument's own bars.

--------------------------------------------------------------------
WHY THIS EXISTS

Every vol signal this project has today (vol_scale_exponent in both
HighFrequencyLocalReferenceSizing and BayesianDualScaleSizing) measures
REALIZED volatility from TQQQ's own price history -- necessarily
backward-looking. The market's own forward estimate (VXN, the
Nasdaq-100 volatility index -- the same index TQQQ tracks 3x) is
available from the same provider used for the extended-hours pull
(src/hf_market_data.py), at 1-min granularity for the index asset
class. This module is the join layer for bringing a series like that
onto TQQQ's own bar index, generically enough that it is not
VXN-specific.

--------------------------------------------------------------------
WHY AN AS-OF JOIN, NOT AN EXACT-TIMESTAMP ONE

An external series is not guaranteed to print on the same minute grid
as the primary bars -- a quiet index minute, a different session
calendar, or (if daily data were used instead) an entirely different
frequency. The right semantics for "what did VXN say at this instant"
is "the most recent known value at or before this instant," the same
as how a real trader would have read a quote feed: never a future
value, and never fabricated between real prints (see
src/historical_data.py's own "will not fill gaps" stance).

--------------------------------------------------------------------
STATE OWNERSHIP

Holds the sorted external series and nothing else -- read-only after
construction. vectorized() and scalar() share the identical as-of
definition (backward merge / searchsorted), the same
scalar/vectorized-must-agree discipline src/event_calendar.py
establishes, and are pinned equal by test.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from src.exceptions import DataValidationError


class ExternalIndexSeries:
    """A sorted (timestamp, value) series with as-of lookups."""

    def __init__(self, series: pd.DataFrame, *, value_column: str = "close") -> None:
        """series must have a tz-aware timestamp index (or 'timestamp'
        column) and value_column. Sorted here rather than trusted, so a
        caller's CSV does not have to guarantee ordering itself."""
        if series.empty:
            raise DataValidationError("ExternalIndexSeries given an empty series.")
        if "timestamp" in series.columns:
            series = series.set_index("timestamp")
        index = pd.DatetimeIndex(series.index)
        if index.tz is None:
            raise DataValidationError("ExternalIndexSeries requires a tz-aware timestamp index.")
        if value_column not in series.columns:
            raise DataValidationError(
                f"ExternalIndexSeries: column {value_column!r} not found in {list(series.columns)}"
            )

        order = np.argsort(index.values)
        self._timestamps = index.tz_convert("UTC")[order]
        self._values = series[value_column].to_numpy(dtype=float)[order]

    @classmethod
    def from_csv(cls, path: Path | str, *, value_column: str = "close") -> "ExternalIndexSeries":
        df = pd.read_csv(path)
        if "timestamp" not in df.columns:
            raise DataValidationError(f"{path}: expected a 'timestamp' column.")
        df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True)
        return cls(df.set_index("timestamp"), value_column=value_column)

    @property
    def first_timestamp(self) -> pd.Timestamp:
        return self._timestamps[0]

    @property
    def last_timestamp(self) -> pd.Timestamp:
        return self._timestamps[-1]

    def scalar(self, timestamp) -> float | None:
        """The most recent known value at or before timestamp, or None
        if timestamp is before the series' first print.

        None (not 0.0) for "no data yet" -- 0.0 would be a fabricated
        reading for e.g. an implied-vol level, where zero is never a
        real quote and a consumer must be able to tell the difference.
        """
        ts = pd.Timestamp(timestamp)
        ts = ts.tz_localize("UTC") if ts.tzinfo is None else ts.tz_convert("UTC")
        ts64 = ts.to_datetime64()

        i = np.searchsorted(self._timestamps.values, ts64, side="right") - 1
        if i < 0:
            return None
        return float(self._values[i])

    def vectorized(self, index: pd.DatetimeIndex) -> np.ndarray:
        """As-of values for a full bar index, NaN before the series'
        first print -- matching scalar()'s None, in a form a numeric
        array can carry. index must be tz-aware and sorted ascending,
        the same convention every other vectorized join in this project
        (src/event_calendar.py, optimization_controller.py's _fomc_flags)
        assumes of the bars it runs against.
        """
        if index.tz is None:
            raise DataValidationError("ExternalIndexSeries.vectorized requires a tz-aware index.")
        idx_utc = index.tz_convert("UTC").values

        positions = np.searchsorted(self._timestamps.values, idx_utc, side="right") - 1
        out = np.full(len(idx_utc), np.nan, dtype=float)
        valid = positions >= 0
        out[valid] = self._values[positions[valid]]
        return out
