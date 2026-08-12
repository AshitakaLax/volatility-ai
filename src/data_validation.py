"""Validation helpers for historical backtest data."""

from __future__ import annotations

import logging

import pandas as pd

from src.exceptions import DataValidationError

REQUIRED_COLUMNS = {"close"}


def validate(df: pd.DataFrame, *, warn_on_gap_pct: float = 0.15) -> None:
    """Validate the minimum historical-data contract used by the current engine.

    The Phase 2 contract requires a non-empty frame with a close column,
    non-null close values, monotonically increasing timestamps, and no duplicate
    timestamps. Large single-bar moves are warnings rather than hard failures.
    """
    if not isinstance(df, pd.DataFrame):
        raise DataValidationError("historical_data must be a pandas DataFrame.")
    if df.empty:
        raise DataValidationError("historical_data is empty.")

    missing = REQUIRED_COLUMNS - set(df.columns)
    if missing:
        raise DataValidationError(
            f"historical_data missing required columns: {sorted(missing)}"
        )

    if df["close"].isna().any():
        raise DataValidationError("historical_data contains NaN values in 'close'.")

    if not df.index.is_monotonic_increasing:
        raise DataValidationError("historical_data index is not sorted ascending.")

    if df.index.duplicated().any():
        raise DataValidationError("historical_data contains duplicate timestamps.")

    pct_change = df["close"].pct_change().abs()
    big_jumps = pct_change[pct_change > warn_on_gap_pct]
    if not big_jumps.empty:
        logging.getLogger("Optimizer").warning(
            f"{len(big_jumps)} bar(s) show a >{warn_on_gap_pct:.0%} single-bar move in 'close' "
            "- verify data is split/dividend adjusted."
        )
