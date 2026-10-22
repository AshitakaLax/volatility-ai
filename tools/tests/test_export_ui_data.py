"""tools/export_ui_data.py's fund_metrics: a missing figure reads as zero."""

from __future__ import annotations

import math

from tools.export_ui_data import fund_metrics


def test_a_missing_count_reads_as_zero_rather_than_raising():
    """A summary frame holds NaN where a row lacks a column, and int(NaN)
    raises: on 2026-10-21 that failed two whole runs at their last step,
    after every configuration had finished."""
    metrics = fund_metrics(
        {
            "Total Return %": 1.5,
            "Max Consecutive Losses": math.nan,
            "Trade Count": None,
            "Closed Trade Count": 7.0,
            "Open Trade Count": math.inf,
        }
    )
    assert metrics["max_consecutive_losses"] == 0
    assert metrics["total_trades"] == 0
    assert metrics["closed_trades"] == 7
    assert metrics["open_trades"] == 0
    assert metrics["signal_exits"] == 0, "absent altogether, as before"
