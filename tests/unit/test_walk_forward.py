"""
Task 5.1 acceptance tests (M1).

Fold boundaries verified numerically (train_window=15, test_window=5,
step=5 on the 35-bar regression fixture -> 4 folds, each
train=[start:start+15), test=[start+15:start+20)) before writing
these tests.
"""

from pathlib import Path

import pandas as pd
import pytest

from optimization_controller import OptimizationController
from src.exceptions import ConfigurationError
from src.size_calculators import FixedPortfolioPercentage
from src.walk_forward import WalkForwardRunner

FIXTURE_PATH = Path(__file__).resolve().parents[1] / "fixtures" / "regression_ohlcv.csv"


def _load_fixture() -> pd.DataFrame:
    df = pd.read_csv(FIXTURE_PATH, parse_dates=["timestamp"])
    df.set_index("timestamp", inplace=True)
    return df


def _controller_factory(df_slice):
    return OptimizationController(historical_data=df_slice)


def test_produces_the_expected_number_of_folds():
    runner = WalkForwardRunner(_controller_factory, train_window=15, test_window=5, step=5)
    result = runner.run(
        _load_fixture(),
        grid_steps=[0.01],
        profit_targets=[0.005],
        strategy_class=FixedPortfolioPercentage,
        strategy_params_grid=[{"allocation_pct": 0.05}],
    )
    assert len(result) == 4


def test_no_test_slice_overlaps_its_own_train_slice():
    runner = WalkForwardRunner(_controller_factory, train_window=15, test_window=5, step=5)
    result = runner.run(
        _load_fixture(),
        grid_steps=[0.01],
        profit_targets=[0.005],
        strategy_class=FixedPortfolioPercentage,
        strategy_params_grid=[{"allocation_pct": 0.05}],
    )
    for _, row in result.iterrows():
        assert row["test_start"] > row["train_end"], (
            "Test slice must strictly follow its own train slice"
        )


def test_fold_boundaries_are_utc():
    runner = WalkForwardRunner(_controller_factory, train_window=15, test_window=5, step=5)
    result = runner.run(
        _load_fixture(),
        grid_steps=[0.01],
        profit_targets=[0.005],
        strategy_class=FixedPortfolioPercentage,
        strategy_params_grid=[{"allocation_pct": 0.05}],
    )
    for col in ("train_start", "train_end", "test_start", "test_end"):
        for ts in result[col]:
            assert ts.tzinfo is not None


def test_rolling_window_train_start_advances_each_fold():
    runner = WalkForwardRunner(
        _controller_factory, train_window=15, test_window=5, step=5, anchored=False
    )
    result = runner.run(
        _load_fixture(),
        grid_steps=[0.01],
        profit_targets=[0.005],
        strategy_class=FixedPortfolioPercentage,
        strategy_params_grid=[{"allocation_pct": 0.05}],
    )
    train_starts = result["train_start"].tolist()
    assert train_starts == sorted(train_starts) and len(set(train_starts)) == len(train_starts)


def test_anchored_window_train_start_is_always_the_beginning():
    runner = WalkForwardRunner(
        _controller_factory, train_window=15, test_window=5, step=5, anchored=True
    )
    result = runner.run(
        _load_fixture(),
        grid_steps=[0.01],
        profit_targets=[0.005],
        strategy_class=FixedPortfolioPercentage,
        strategy_params_grid=[{"allocation_pct": 0.05}],
    )
    df = _load_fixture()
    assert (result["train_start"] == df.index[0]).all()


@pytest.mark.parametrize(
    "kwargs",
    [
        dict(train_window=0),
        dict(train_window=-1),
        dict(test_window=0),
        dict(test_window=-1),
        dict(step=0),
        dict(step=-1),
    ],
)
def test_non_positive_window_values_rejected(kwargs):
    base = dict(train_window=15, test_window=5, step=5)
    base.update(kwargs)
    with pytest.raises(ConfigurationError):
        WalkForwardRunner(_controller_factory, **base)


def test_winner_params_correctly_reconstructed_for_the_test_rerun():
    # The test-slice re-run must use the SAME allocation_pct the
    # training window selected as the winner, not a default/wrong one.
    runner = WalkForwardRunner(_controller_factory, train_window=15, test_window=5, step=5)
    result = runner.run(
        _load_fixture(),
        grid_steps=[0.01],
        profit_targets=[0.005],
        strategy_class=FixedPortfolioPercentage,
        strategy_params_grid=[{"allocation_pct": 0.03}, {"allocation_pct": 0.08}],
    )
    for _, row in result.iterrows():
        assert row["train_allocation_pct"] == row["test_allocation_pct"]
