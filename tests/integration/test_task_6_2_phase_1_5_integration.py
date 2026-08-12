import pandas as pd
import pytest

from optimization_controller import OptimizationController
from src.risk_manager import RiskManager
from src.size_calculators import FixedPortfolioPercentage, SizingStrategy
from src.walk_forward import WalkForwardRunner


def make_data(values):
    index = pd.date_range("2024-01-01", periods=len(values), freq="D")
    return pd.DataFrame({"open": values, "high": [v + 1 for v in values], "low": [v - 1 for v in values], "close": values, "volume": [1000] * len(values)}, index=index)


class RecordingStrategy(FixedPortfolioPercentage):
    ticks = []

    def record_tick(self, context):
        type(self).ticks.append(context.bar_index)
        super().record_tick(context)


class DrawdownAwareStrategy(FixedPortfolioPercentage):
    observed_drawdowns = []

    def calculate_trade_value(self, context):
        type(self).observed_drawdowns.append(context.drawdown)
        return super().calculate_trade_value(context)


class LargeAllocationStrategy(FixedPortfolioPercentage):
    def calculate_trade_value(self, context):
        return context.equity


class FailingStrategy(FixedPortfolioPercentage):
    def __init__(self, fail=False, percentage=0.1):
        if fail:
            raise RuntimeError("intentional integration failure")
        super().__init__(percentage=percentage)


def test_record_tick_called_once_per_bar():
    RecordingStrategy.ticks = []
    controller = OptimizationController(make_data([100, 99, 98, 97]))
    controller.run_sweep([0.01], [0.01], RecordingStrategy, [{"percentage": 0.1}])
    assert RecordingStrategy.ticks == [0, 1, 2, 3]


def test_nonzero_drawdown_reaches_sizing_strategy():
    DrawdownAwareStrategy.observed_drawdowns = []
    controller = OptimizationController(make_data([100, 90, 80, 70]))
    controller.run_sweep([0.01], [0.01], DrawdownAwareStrategy, [{"percentage": 0.1}])
    assert any(value > 0 for value in DrawdownAwareStrategy.observed_drawdowns)


def test_risk_manager_clamps_allocation():
    controller = OptimizationController(make_data([100, 99, 98]))
    result = controller.run_sweep(
        [0.01], [0.01], LargeAllocationStrategy, [{}],
        risk_manager=RiskManager(max_total_exposure=0.25),
        return_full_results=True,
    )
    _, full_results = result
    blotter = full_results[0].trade_blotter
    assert not blotter.empty
    assert blotter.iloc[0]["price"] * blotter.iloc[0]["qty"] <= 25_000.0 + 1e-9


def test_failed_combination_does_not_abort_sweep():
    controller = OptimizationController(make_data([100, 99, 98]))
    result = controller.run_sweep(
        [0.01], [0.01], FailingStrategy,
        [{"fail": False, "percentage": 0.1}, {"fail": True, "percentage": 0.1}],
    )
    assert len(result) == 2
    assert result["error"].notna().sum() == 1


def test_parallel_sweep_matches_sequential_sweep():
    data = make_data([100, 99, 101, 98, 102])
    kwargs = dict(
        grid_steps=[0.01, 0.02],
        profit_targets=[0.01],
        strategy_class=FixedPortfolioPercentage,
        strategy_params_grid=[{"percentage": 0.05}, {"percentage": 0.1}],
    )
    sequential = OptimizationController(data).run_sweep(**kwargs, n_jobs=1)
    parallel = OptimizationController(data).run_sweep(**kwargs, n_jobs=2)
    pd.testing.assert_frame_equal(
        sequential.reset_index(drop=True),
        parallel.reset_index(drop=True),
        check_dtype=False,
    )


def test_walk_forward_test_metrics_use_unseen_test_window():
    data = make_data([100, 101, 102, 103, 104, 105, 106, 107])
    runner = WalkForwardRunner(OptimizationController, train_window=4, test_window=2, step=2)
    result = runner.run(
        data,
        grid_steps=[0.01],
        profit_targets=[0.01],
        strategy_class=FixedPortfolioPercentage,
        strategy_params_grid=[{"percentage": 0.1}],
    )
    assert len(result) == 2
    for _, row in result.iterrows():
        assert row["train_end"] < row["test_start"]
        assert row["test_start"] <= row["test_end"]
        assert pd.notna(row["test_Final Portfolio Value"])
