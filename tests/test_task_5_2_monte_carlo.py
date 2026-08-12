import numpy as np
import pandas as pd
import pytest

from optimization_controller import OptimizationController
from src.monte_carlo import MonteCarloRunner
from src.size_calculators import FixedPortfolioPercentage


def fixture_data(volatility: float, n: int = 80) -> pd.DataFrame:
    rng = np.random.default_rng(1234)
    returns = rng.normal(0.0005, volatility, n - 1)
    prices = 100.0 * np.cumprod(np.r_[1.0, 1.0 + returns])
    return pd.DataFrame({"close": prices}, index=pd.date_range("2024-01-01", periods=n))


def test_fixed_seed_produces_identical_output_and_percentiles():
    data = fixture_data(0.01)
    factory = OptimizationController
    a = MonteCarloRunner(factory)
    b = MonteCarloRunner(factory)
    kwargs = dict(
        full_data=data,
        n_paths=8,
        block_size=5,
        step=0.01,
        target=0.01,
        strategy_class=FixedPortfolioPercentage,
        strategy_params={"percentage": 0.01},
        seed=42,
    )
    left = a.run(**kwargs)
    right = b.run(**kwargs)
    pd.testing.assert_frame_equal(left, right)
    pd.testing.assert_frame_equal(a.last_percentiles, b.last_percentiles)


def test_iteration_order_is_deterministic():
    data = fixture_data(0.01)
    runner = MonteCarloRunner(OptimizationController)
    result = runner.run(data, 5, 4, 0.01, 0.01, FixedPortfolioPercentage, {"percentage": 0.01}, seed=7)
    assert result["iteration"].tolist() == list(range(5))


def test_insufficient_block_size_is_rejected():
    data = fixture_data(0.01, n=5)
    runner = MonteCarloRunner(OptimizationController)
    with pytest.raises(ValueError, match="insufficient observations"):
        runner.run(data, 2, 5, 0.01, 0.01, FixedPortfolioPercentage, {"percentage": 0.01}, seed=1)


def test_higher_volatility_produces_wider_final_equity_spread():
    low = fixture_data(0.002)
    high = fixture_data(0.03)
    low_runner = MonteCarloRunner(OptimizationController)
    high_runner = MonteCarloRunner(OptimizationController)
    low_result = low_runner.run(low, 30, 5, 0.01, 0.01, FixedPortfolioPercentage, {"percentage": 0.01}, seed=9)
    high_result = high_runner.run(high, 30, 5, 0.01, 0.01, FixedPortfolioPercentage, {"percentage": 0.01}, seed=9)
    low_spread = low_runner.last_percentiles.loc["Final Portfolio Value", "p95"] - low_runner.last_percentiles.loc["Final Portfolio Value", "p05"]
    high_spread = high_runner.last_percentiles.loc["Final Portfolio Value", "p95"] - high_runner.last_percentiles.loc["Final Portfolio Value", "p05"]
    assert high_spread > low_spread
