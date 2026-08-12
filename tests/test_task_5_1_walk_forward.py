import pandas as pd
import pytest

from src.exceptions import ConfigurationError
from src.walk_forward import WalkForwardRunner
from optimization_controller import OptimizationController
from src.size_calculators import FixedPortfolioPercentage


def _controller_factory(data):
    return OptimizationController(data)


def _data(n=18):
    return pd.DataFrame(
        {"close": [100.0 + ((i % 6) - 2) for i in range(n)]},
        index=pd.date_range("2024-01-01", periods=n, freq="D"),
    )


def test_walk_forward_returns_train_and_test_rows_for_three_folds():
    runner = WalkForwardRunner(_controller_factory, train_window=6, test_window=3, step=3)
    result = runner.run(
        _data(),
        [0.01, 0.02],
        [0.01],
        FixedPortfolioPercentage,
        [{"percentage": 0.01}, {"percentage": 0.02}],
    )

    assert len(result) == 4
    assert {"fold", "train_start", "train_end", "test_start", "test_end"}.issubset(result.columns)
    assert "train_Capital Velocity Index" in result.columns
    assert "test_Capital Velocity Index" in result.columns


def test_walk_forward_uses_only_training_window_to_select_winner():
    seen = []

    class RecordingController(OptimizationController):
        def run_sweep(self, *args, **kwargs):
            seen.append(self.data.index.copy())
            return super().run_sweep(*args, **kwargs)

    runner = WalkForwardRunner(lambda data: RecordingController(data), 6, 3, 3)
    runner.run(_data(), [0.01], [0.01], FixedPortfolioPercentage, [{"percentage": 0.01}])

    # Each fold invokes training first, followed by a test slice that starts
    # immediately after the training slice.
    assert seen[0][-1] < seen[1][0]
    assert len(seen[0]) == 6
    assert len(seen[1]) == 3


def test_walk_forward_rejects_invalid_window_configuration():
    with pytest.raises(ConfigurationError):
        WalkForwardRunner(_controller_factory, 0, 3, 1)
    with pytest.raises(ConfigurationError):
        WalkForwardRunner(_controller_factory, 3, -1, 1)
    with pytest.raises(ConfigurationError):
        WalkForwardRunner(_controller_factory, 3, 2, 0)


def test_walk_forward_requires_enough_data():
    runner = WalkForwardRunner(_controller_factory, 10, 5, 1)
    with pytest.raises(ConfigurationError):
        runner.run(_data(14), [0.01], [0.01], FixedPortfolioPercentage, [{"percentage": 0.01}])
