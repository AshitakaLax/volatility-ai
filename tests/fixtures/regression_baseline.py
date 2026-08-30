"""
Task 0.1 -- regression baseline fixture for OptimizationController.run_sweep.

Phase 1 intentionally changes runtime behavior (drawdown will start
reaching sizing strategies, record_tick will start firing every bar,
etc. -- see architecture_overview.md Findings B2-B4). Before any of
that lands, this module pins what run_sweep() currently outputs on a
small, fixed synthetic dataset, so Phase 1's changes can be diffed
against a known "before" state instead of discovered by surprise.

This module is the single source of truth for:
  1. Loading the fixed synthetic OHLCV dataset (regression_ohlcv.csv).
  2. Running the exact one-combination sweep Task 0.1 specifies.
  3. Holding the frozen "current behavior" baseline that
     tests/test_regression_baseline.py asserts against.

--------------------------------------------------------------------
src/size_calculators.py now exists (written fresh -- see the chat
this fixture was produced in, since no prior implementation was
available to read). FixedPortfolioPercentage's constructor keyword is
`allocation_pct`, per implementation_task_specs.md Task 1.1's own
proposed reading of Run_Instructions' example. STRATEGY_PARAMS below
has been updated to match.
--------------------------------------------------------------------

Usage (one-time, in an environment with the real src/ package on disk):

    python -m tests.fixtures.regression_baseline

    This prints the freshly computed baseline as a Python dict
    literal. Paste it in as the value of BASELINE below to freeze it.
    From then on, `pytest tests/test_regression_baseline.py` asserts
    every subsequent run still matches.
"""

from __future__ import annotations

import os
import sys

import pandas as pd

# Make the repository root importable regardless of the CWD pytest/python
# is invoked from (repo root is optimization_controller.py's directory,
# two levels up from this file: tests/fixtures/ -> tests/ -> repo root).
_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
_REPO_ROOT = os.path.abspath(os.path.join(_THIS_DIR, "..", ".."))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

from optimization_controller import OptimizationController  # noqa: E402
from src.size_calculators import FixedPortfolioPercentage  # noqa: E402

OHLCV_FIXTURE_PATH = os.path.join(_THIS_DIR, "regression_ohlcv.csv")

# Single combination -> exactly one result row, per Task 0.1 step 3
# ("one grid_step, one profit_target, FixedPortfolioPercentage, one
# params dict"). Values chosen so the fixture data (decline ~5.8% off
# a $50 start, then recovery to ~+14.7%) exercises a few grid buys and
# at least one profit-target harvest -- see regression_ohlcv.csv.
GRID_STEP = 0.01
PROFIT_TARGET = 0.005
STRATEGY_PARAMS = {"allocation_pct": 0.05}


def load_fixture_data() -> pd.DataFrame:
    """Load the fixed synthetic OHLCV dataset the same way Run_Instructions
    documents loading real historical data, so this fixture exercises the
    identical ingestion path production data would."""
    df = pd.read_csv(OHLCV_FIXTURE_PATH, parse_dates=["timestamp"])
    df.set_index("timestamp", inplace=True)
    return df


def run_baseline_sweep() -> dict:
    """Run the exact single-combination sweep Task 0.1 specifies and return
    the resulting one-row DataFrame as a plain dict (column -> value)."""
    data = load_fixture_data()
    controller = OptimizationController(historical_data=data)
    result_df = controller.run_sweep(
        grid_steps=[GRID_STEP],
        profit_targets=[PROFIT_TARGET],
        strategy_class=FixedPortfolioPercentage,
        strategy_params_grid=[STRATEGY_PARAMS],
    )
    if len(result_df) != 1:
        raise AssertionError(
            "Expected exactly one result row from a single-combination sweep, "
            f"got {len(result_df)}. Check GRID_STEP/PROFIT_TARGET/STRATEGY_PARAMS "
            "are each still single-value lists of length 1."
        )
    return result_df.iloc[0].to_dict()


# ----------------------------------------------------------------------
# Frozen baseline. None until captured once against the real src/
# package (see "Usage" in the module docstring above).
# tests/test_regression_baseline.py fails loudly -- rather than
# silently passing -- while this is None, since Task 0.1's acceptance
# criteria is that the test passes against real, current behavior,
# not a placeholder.
# ----------------------------------------------------------------------
# DELIBERATE SCHEMA UPDATE: "Strategy" was added when the sizing
# strategies stopped being a set of one. Before it, rows from a
# FixedPortfolioPercentage sweep and a BayesianDualScaleSizing sweep
# were indistinguishable once combined into a single results table.
#
# The update was reviewed rather than regenerated on faith: every
# previously pinned value was confirmed byte-identical first, so this
# revision adds a column and changes no behavior. If a future edit here
# also moves a number, that is a regression, not a schema change.
BASELINE: dict | None = {
    "Grid Step": 0.01,
    "Profit Target": 0.005,
    "Strategy": "FixedPortfolioPercentage",
    "allocation_pct": 0.05,
    "Final Equity": 100099.81489816227,
    "Total Return %": 0.09981489816226485,
    "Realized PnL": 99.81489816224163,
    "Trade Count": 4.0,
    "Closed Trade Count": 4.0,
    "Open Trade Count": 0.0,
    "Capital Velocity Index": 1.0,
    "Max Drawdown %": 0.4430668810465577,
    # Added when run_sweep began reporting a drawdown-aware ranking
    # metric. Every other value above is UNCHANGED by that addition and
    # by the is_earnings_reaction_day wiring alongside it -- both were
    # re-derived and compared against the previous baseline before this
    # key was appended, so this file still pins the same behavior it
    # did before, plus one new column.
    "Return/Drawdown": 0.2252817857351343,
    # Added alongside the drawdown-aware metric. Annualizing is a
    # monotonic transform of Total Return %, so this changes no ranking
    # and no other pinned value -- all twelve above were re-derived and
    # compared before it was appended.
    "CAGR %": 1.0775051531105362,
    # Added when run_sweep began reporting calendar-year return spread
    # (Average/Best/Worst) alongside the single whole-period CAGR. This
    # fixture's data spans under one calendar year, so there is exactly
    # one annual_returns() bucket -- meaning all three of these are
    # necessarily identical to each other AND to Total Return % itself
    # (see test_a_single_year_is_simultaneously_average_best_and_worst
    # in test_performance_analyzer.py for why that is correct, not a
    # degenerate baseline). All fourteen values above were re-derived
    # and confirmed byte-identical before these three were appended.
    "Average Annual Return %": 0.09981489816226485,
    "Best Year Return %": 0.09981489816226485,
    "Worst Year Return %": 0.09981489816226485,
}


if __name__ == "__main__":
    baseline = run_baseline_sweep()
    print("Captured baseline -- paste this in as BASELINE in this file:\n")
    print("BASELINE = {")
    for k, v in baseline.items():
        print(f"    {k!r}: {v!r},")
    print("}")
