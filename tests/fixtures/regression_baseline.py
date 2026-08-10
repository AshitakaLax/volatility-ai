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
REPOSITORY-ADAPTIVE -- CONFIRM BEFORE CAPTURING (see
architecture_overview.md Appendix 8, "Sizing constructors --
repository-adaptive"):

    STRATEGY_PARAMS below assumes FixedPortfolioPercentage's
    constructor takes a `percentage` keyword. This has NOT been
    confirmed against the real src/size_calculators.py (that file
    was not available at implementation time -- see the chat this
    fixture was produced in). If the real keyword name differs,
    update STRATEGY_PARAMS to match. Do not rename the class's
    public constructor to match this fixture.
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
STRATEGY_PARAMS = {"percentage": 0.05}  # TODO: confirm kwarg name -- see module docstring


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
BASELINE: dict | None = None


if __name__ == "__main__":
    baseline = run_baseline_sweep()
    print("Captured baseline -- paste this in as BASELINE in this file:\n")
    print("BASELINE = {")
    for k, v in baseline.items():
        print(f"    {k!r}: {v!r},")
    print("}")
