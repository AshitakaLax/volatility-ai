"""Task 0.1 frozen regression baseline for OptimizationController.run_sweep."""

from __future__ import annotations

import os
import sys

import pandas as pd

_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
_REPO_ROOT = os.path.abspath(os.path.join(_THIS_DIR, "..", ".."))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

from optimization_controller import OptimizationController  # noqa: E402
from src.size_calculators import FixedPortfolioPercentage  # noqa: E402

OHLCV_FIXTURE_PATH = os.path.join(_THIS_DIR, "regression_ohlcv.csv")
GRID_STEP = 0.01
PROFIT_TARGET = 0.005
STRATEGY_PARAMS = {"percentage": 0.05}


def load_fixture_data() -> pd.DataFrame:
    df = pd.read_csv(OHLCV_FIXTURE_PATH, parse_dates=["timestamp"])
    df.set_index("timestamp", inplace=True)
    return df


def run_baseline_sweep() -> dict:
    data = load_fixture_data()
    controller = OptimizationController(historical_data=data)
    result_df = controller.run_sweep(
        grid_steps=[GRID_STEP],
        profit_targets=[PROFIT_TARGET],
        strategy_class=FixedPortfolioPercentage,
        strategy_params_grid=[STRATEGY_PARAMS],
    )
    if len(result_df) != 1:
        raise AssertionError(f"Expected exactly one result row, got {len(result_df)}")
    return result_df.iloc[0].to_dict()


# Captured from the current pre-Phase-1 implementation after restoring the
# missing src/ dependencies. This is intentionally a behavior baseline, not
# a claim that the current behavior is ideal; Phase 1 is expected to change
# some of these values.
BASELINE: dict = {
    "Grid Step": 0.01,
    "Profit Target": 0.005,
    "percentage": 0.05,
    "Final Portfolio Value": 100099.81489816227,
    "Trade Count": 4,
    "Total Return %": 0.09981489816226531,
    "Capital Velocity Index": 0.000998148981622653,
    "Max Drawdown %": 0.0,
}


if __name__ == "__main__":
    print("BASELINE = {")
    for key, value in run_baseline_sweep().items():
        print(f"    {key!r}: {value!r},")
    print("}")
