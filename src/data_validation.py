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
from dataclasses import dataclass

import numpy as np
import pandas as pd

from src.exceptions import DataValidationError

REQUIRED_COLUMNS = {
    "close"
}  # extend to {"open","high","low","close","volume"} if/when OHLC is adopted (Task 2.3)


@dataclass(frozen=True)
class ValidationReport:
    """What validate() found but did not reject.

    Exists because the >15% single-bar check is the last line of defence
    against the worst failure mode in this system, and until now its
    only output was a log line. src/historical_data.py's own docstring
    says why that is not enough:

        "A grid strategy reads that as a catastrophic dip and fires
         every rung at once, at a price that never existed, producing a
         backtest that looks like a spectacular win. The only thing
         standing between that and a shipped parameter set is
         validate()'s >15% move warning -- a logging.warning that
         scrolls past unread in a sweep printing hundreds of lines."

    A caller could not previously ask "did anything look unadjusted?",
    count the bars, record them, or refuse to proceed. Returning the
    finding rather than only logging it makes all four possible, without
    changing what validate() rejects: a large move can be a genuine
    event, so it is still never fatal on its own.

    suspect_bars carries the actual timestamps and magnitudes, because
    "3 bars moved >15%" is not actionable and "these three bars, on
    2020-03-09, 03-13 and 03-16, moved +16.5%, -18.1%, +22.8%" is --
    that is a COVID-crash signature, not an unadjusted split, and
    telling them apart requires the values.
    """

    suspect_bars: tuple[tuple[pd.Timestamp, float], ...] = ()

    @property
    def has_suspect_bars(self) -> bool:
        return bool(self.suspect_bars)

    def describe(self, limit: int = 5) -> str:
        """One line per suspect bar, truncated -- for a sidecar or an
        operator prompt."""
        shown = [
            f"{ts.isoformat()} {change * 100:+.1f}%"
            for ts, change in self.suspect_bars[:limit]
        ]
        extra = len(self.suspect_bars) - limit
        return "; ".join(shown) + (f" (+{extra} more)" if extra > 0 else "")


def _format_bad_indices(df: pd.DataFrame, mask: pd.Series, limit: int = 5) -> str:
    """Render the offending timestamps for an error message.

    Truncates to `limit` with a "+N more" suffix, so a systematically
    broken dataset produces a readable error rather than thousands of
    lines of index dump.
    """
    bad = df.index[mask]
    shown = list(bad[:limit])
    suffix = f" (+{len(bad) - limit} more)" if len(bad) > limit else ""
    return f"{shown}{suffix}"


def validate(df: pd.DataFrame, *, warn_on_gap_pct: float = 0.15) -> ValidationReport:
    """Validate a historical dataset before any simulation runs.

    RAISES DataValidationError for conditions that make results
    meaningless: empty frame, missing columns, NaN/inf, non-positive
    prices, unsorted index, duplicate timestamps.

    WARNS but does not raise for a large single-bar move, since that is
    usually an unadjusted split but can be a genuine event -- and
    rejecting real data outright would be worse than flagging it.

    RETURNS a ValidationReport carrying those flagged bars. Previously
    this returned None and the finding existed only as a log line, so no
    caller could act on it -- see ValidationReport's docstring. Returning
    a value changes nothing about what is rejected; every existing caller
    that ignores the return behaves exactly as before.
    """
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

    # Signed, not absolute: the direction is diagnostic. A split shows as
    # a single large NEGATIVE step; a crash or a squeeze goes either way
    # and clusters. Discarding the sign threw away the cheapest signal
    # for telling those apart.
    pct_change = close.pct_change()
    big_jumps = pct_change[pct_change.abs() > warn_on_gap_pct]
    report = ValidationReport(
        suspect_bars=tuple(zip(big_jumps.index, big_jumps.to_numpy()))
    )
    if report.has_suspect_bars:
        logging.getLogger("Optimizer").warning(
            f"{len(big_jumps)} bar(s) show a >{warn_on_gap_pct:.0%} single-bar move in 'close' "
            f"- verify data is split/dividend adjusted: {report.describe()}"
        )
    return report
