"""
Historical-data validation for OptimizationController.

Task 2.1 (F4). The base checks below are implementation_task_specs.md
Task 2.1's own code sample, extended to also cover two cases that
sample doesn't check but the same task's "Validation severity
contract" explicitly requires as ERROR/reject conditions:
non-finite (inf) prices, and non-positive (<=0) prices. Both are also
in that task's own "Boundary fixtures" list, so the sample and the
contract were reconciled in favor of the contract (the stricter,
more complete requirement) rather than picking one arbitrarily.
"""

from __future__ import annotations

import logging

import numpy as np
import pandas as pd

from src.exceptions import DataValidationError

REQUIRED_COLUMNS = {"close"}  # extend to {"open","high","low","close","volume"} if/when OHLC is adopted (Task 2.3)


def _format_bad_indices(df: pd.DataFrame, mask: pd.Series, limit: int = 5) -> str:
    bad = df.index[mask]
    shown = list(bad[:limit])
    suffix = f" (+{len(bad) - limit} more)" if len(bad) > limit else ""
    return f"{shown}{suffix}"


def validate(df: pd.DataFrame, *, warn_on_gap_pct: float = 0.15) -> None:
    if df.empty:
        raise DataValidationError("historical_data is empty.")

    missing = REQUIRED_COLUMNS - set(df.columns)
    if missing:
        raise DataValidationError(f"historical_data missing required columns: {missing}")

    close = df["close"]

    non_finite = ~np.isfinite(close.astype(float))
    if non_finite.any():
        raise DataValidationError(
            f"historical_data contains NaN/inf values in 'close' at: {_format_bad_indices(df, non_finite)}"
        )

    non_positive = close <= 0
    if non_positive.any():
        raise DataValidationError(
            f"historical_data contains non-positive 'close' prices at: {_format_bad_indices(df, non_positive)}"
        )

    if not df.index.is_monotonic_increasing:
        raise DataValidationError("historical_data index is not sorted ascending.")

    dup_mask = df.index.duplicated()
    if dup_mask.any():
        raise DataValidationError(
            f"historical_data contains duplicate timestamps at: {_format_bad_indices(df, dup_mask)}"
        )

    pct_change = close.pct_change().abs()
    big_jumps = pct_change[pct_change > warn_on_gap_pct]
    if not big_jumps.empty:
        logging.getLogger("Optimizer").warning(
            f"{len(big_jumps)} bar(s) show a >{warn_on_gap_pct:.0%} single-bar move in 'close' "
            "- verify data is split/dividend adjusted."
        )
