"""
Task 1.6 acceptance test: re-confirms, explicitly and directly (not
just incidentally via the Task 0.1 regression test staying green
through Tasks 1.2-1.5), the two things Task 1.6 requires:

1. FixedPortfolioPercentage's output is value-for-value identical to
   the pre-Phase-1 baseline captured in Task 0.1.
2. No naming collision between optimization_controller.py's own
   "Max Drawdown %" assignment and anything PerformanceAnalyzer.
   calculate_metrics produces independently.
"""

from pathlib import Path

import pandas as pd

from optimization_controller import OptimizationController
from src.size_calculators import FixedPortfolioPercentage
from tests.fixtures.regression_baseline import BASELINE

FIXTURE_PATH = Path(__file__).resolve().parents[1] / "fixtures" / "regression_ohlcv.csv"


def test_fixed_portfolio_percentage_baseline_value_for_value_identical_post_phase_1():
    assert BASELINE is not None, "Task 0.1's baseline must be captured for this comparison to mean anything"

    df = pd.read_csv(FIXTURE_PATH, parse_dates=["timestamp"])
    df.set_index("timestamp", inplace=True)
    controller = OptimizationController(historical_data=df)
    result = controller.run_sweep(
        grid_steps=[BASELINE["Grid Step"]],
        profit_targets=[BASELINE["Profit Target"]],
        strategy_class=FixedPortfolioPercentage,
        strategy_params_grid=[{"allocation_pct": BASELINE["allocation_pct"]}],
    )
    fresh = result.iloc[0].to_dict()

    for key, expected in BASELINE.items():
        assert fresh[key] == expected, (
            f"Post-Phase-1 {key!r} = {fresh[key]!r} differs from the pre-Phase-1 "
            f"baseline {expected!r} -- FixedPortfolioPercentage doesn't use "
            f"drawdown or record_tick, so Tasks 1.2-1.5 should not have moved this at all."
        )


def test_no_collision_between_controller_and_analyzer_drawdown_figures():
    df = pd.read_csv(FIXTURE_PATH, parse_dates=["timestamp"])
    df.set_index("timestamp", inplace=True)
    controller = OptimizationController(historical_data=df)
    result = controller.run_sweep(
        grid_steps=[0.01],
        profit_targets=[0.005],
        strategy_class=FixedPortfolioPercentage,
        strategy_params_grid=[{"allocation_pct": 0.05}],
    )
    row = result.iloc[0]
    # PerformanceAnalyzer.calculate_metrics never produces this key by
    # design (see src/performance_analyzer.py docstring) -- the value
    # present in the final row must be exactly the controller's own
    # state.max_drawdown * 100.0, with nothing else able to have
    # silently written or overwritten it in between.
    assert "Max Drawdown %" in row
    assert row["Max Drawdown %"] == 0.4430668810465577  # matches Task 0.1's captured baseline exactly
