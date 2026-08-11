import pandas as pd
import pytest

from optimization_controller import OptimizationController
from src.size_calculators import FixedPortfolioPercentage


def _fixture():
    index = pd.date_range("2024-01-01", periods=40, freq="D")
    close = [100.0 - (i % 7) * 0.5 + i * 0.02 for i in range(40)]
    return pd.DataFrame({"open": close, "high": [p + 1 for p in close], "low": [p - 1 for p in close], "close": close, "volume": [1000] * 40}, index=index)


def _canonical(df):
    return df.sort_values(["Grid Step", "Profit Target", "percentage"], na_position="last").reset_index(drop=True)


def test_default_sequential_behavior_and_parallel_results_are_equivalent():
    controller = OptimizationController(_fixture())
    kwargs = dict(
        grid_steps=[0.01, 0.02],
        profit_targets=[0.01, 0.02],
        strategy_class=FixedPortfolioPercentage,
        strategy_params_grid=[{"percentage": 0.01}, {"percentage": 0.02}],
    )
    sequential = _canonical(controller.run_sweep(**kwargs, n_jobs=1))
    parallel = _canonical(controller.run_sweep(**kwargs, n_jobs=2))
    pd.testing.assert_frame_equal(sequential, parallel, check_dtype=False)


def test_n_jobs_rejects_non_positive_values():
    controller = OptimizationController(_fixture())
    kwargs = dict(grid_steps=[0.01], profit_targets=[0.01], strategy_class=FixedPortfolioPercentage, strategy_params_grid=[{"percentage": 0.01}])
    with pytest.raises(ValueError):
        controller.run_sweep(**kwargs, n_jobs=0)
    with pytest.raises(ValueError):
        controller.run_sweep(**kwargs, n_jobs=-1)


def test_parallel_worker_failure_isolated_to_one_row():
    class FailingStrategy(FixedPortfolioPercentage):
        def __init__(self, percentage=0.01, fail=False):
            if fail:
                raise ZeroDivisionError("parallel deliberate failure")
            super().__init__(percentage=percentage)

    controller = OptimizationController(_fixture())
    result = controller.run_sweep(
        grid_steps=[0.01],
        profit_targets=[0.01],
        strategy_class=FailingStrategy,
        strategy_params_grid=[{"percentage": 0.01, "fail": False}, {"percentage": 0.01, "fail": True}],
        n_jobs=2,
    )
    assert len(result) == 2
    assert result["error"].notna().sum() == 1
    assert result["Final Portfolio Value"].notna().sum() == 1
