"""
Task 5.2 acceptance tests (M2).

1. With a fixed seed, two runs produce identical resampled paths and
   identical output.
2. Percentile spread is visibly narrower for a lower-volatility
   fixture than a higher-volatility one.
Plus: block_size exceeding available data fails clearly (Monte Carlo
contract), and run() over a modest n_paths returns clean percentile
summaries without raising, via the real OptimizationController/
PerformanceAnalyzer pipeline.

All numbers here were verified directly in the chat this test was
produced in before being written (seed determinism confirmed via
array equality; volatility spread confirmed ~20x wider for the
high-vol fixture, comfortably past any reasonable "visibly narrower"
threshold).
"""

import numpy as np
import pandas as pd
import pytest

from optimization_controller import OptimizationController
from src.exceptions import ConfigurationError
from src.monte_carlo import MonteCarloRunner, generate_synthetic_path
from src.size_calculators import FixedPortfolioPercentage


def _fixture(vol: float, seed: int, n: int = 80) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    closes = 100 * np.cumprod(1 + rng.normal(0.0, vol, n))
    idx = pd.date_range("2020-01-01", periods=n, freq="D", tz="UTC")
    df = pd.DataFrame(
        {"open": np.roll(closes, 1), "high": closes * 1.005, "low": closes * 0.995, "close": closes, "volume": 1_000_000},
        index=idx,
    )
    df.iloc[0, df.columns.get_loc("open")] = closes[0]
    return df


def _factory(path_df):
    return OptimizationController(historical_data=path_df)


def test_same_seed_produces_identical_paths():
    df = _fixture(vol=0.01, seed=1)
    runner = MonteCarloRunner()
    paths1 = runner.generate_paths(df, n_paths=5, block_size=5, seed=42)
    paths2 = runner.generate_paths(df, n_paths=5, block_size=5, seed=42)
    for p1, p2 in zip(paths1, paths2):
        pd.testing.assert_series_equal(p1["close"], p2["close"])


def test_different_seed_produces_different_paths():
    df = _fixture(vol=0.01, seed=1)
    runner = MonteCarloRunner()
    paths_a = runner.generate_paths(df, n_paths=1, block_size=5, seed=42)
    paths_b = runner.generate_paths(df, n_paths=1, block_size=5, seed=99)
    assert not paths_a[0]["close"].equals(paths_b[0]["close"])


def test_paths_within_one_call_are_independent_not_identical():
    df = _fixture(vol=0.01, seed=1)
    runner = MonteCarloRunner()
    paths = runner.generate_paths(df, n_paths=5, block_size=5, seed=42)
    closes = [tuple(p["close"]) for p in paths]
    assert len(set(closes)) == 5, "All 5 paths within one call must be distinct"


def test_same_seed_produces_identical_run_output():
    df = _fixture(vol=0.01, seed=1)
    runner = MonteCarloRunner()
    kwargs = dict(
        controller_factory=_factory, n_paths=10, block_size=5, step=0.01, target=0.005,
        strategy_class=FixedPortfolioPercentage, strategy_params={"allocation_pct": 0.05},
        historical_data=df, seed=42,
    )
    result1 = runner.run(**kwargs)
    result2 = runner.run(**kwargs)
    pd.testing.assert_frame_equal(result1, result2)


def test_block_size_exceeding_available_data_fails_clearly():
    df = _fixture(vol=0.01, seed=1, n=20)
    runner = MonteCarloRunner()
    with pytest.raises(ConfigurationError, match="block_size"):
        runner.generate_paths(df, n_paths=1, block_size=100, seed=1)


def test_run_over_modest_n_paths_returns_clean_percentile_summary():
    df = _fixture(vol=0.01, seed=1)
    runner = MonteCarloRunner()
    result = runner.run(
        controller_factory=_factory, n_paths=20, block_size=5, step=0.01, target=0.005,
        strategy_class=FixedPortfolioPercentage, strategy_params={"allocation_pct": 0.05},
        historical_data=df, seed=42,
    )
    assert list(result.index) == [5, 25, 50, 75, 95]
    assert list(result.columns) == ["CAGR", "Max Drawdown %", "Final Equity"]
    assert result.notna().all().all()
    assert result["Final Equity"].is_monotonic_increasing


def test_percentile_spread_visibly_narrower_for_lower_volatility():
    low_vol = _fixture(vol=0.003, seed=1)
    high_vol = _fixture(vol=0.03, seed=1)
    runner = MonteCarloRunner()
    common = dict(
        controller_factory=_factory, n_paths=30, block_size=5, step=0.01, target=0.005,
        strategy_class=FixedPortfolioPercentage, strategy_params={"allocation_pct": 0.05}, seed=42,
    )
    low_result = runner.run(historical_data=low_vol, **common)
    high_result = runner.run(historical_data=high_vol, **common)

    low_spread = low_result.loc[95, "Final Equity"] - low_result.loc[5, "Final Equity"]
    high_spread = high_result.loc[95, "Final Equity"] - high_result.loc[5, "Final Equity"]
    assert high_spread > low_spread * 1.5, (
        f"Expected high-volatility spread ({high_spread:.2f}) to be visibly wider than "
        f"low-volatility spread ({low_spread:.2f})"
    )


def test_generate_synthetic_path_preserves_length_and_start_price():
    df = _fixture(vol=0.01, seed=1)
    rng = np.random.default_rng(1)
    path = generate_synthetic_path(df, block_size=5, rng=rng)
    assert len(path) == len(df)
    assert path["close"].iloc[0] == df["close"].iloc[0]
    assert list(path.index) == list(df.index)


@pytest.mark.parametrize("kwargs", [dict(n_paths=0), dict(n_paths=-1), dict(block_size=0), dict(block_size=-1)])
def test_non_positive_config_rejected(kwargs):
    df = _fixture(vol=0.01, seed=1)
    runner = MonteCarloRunner()
    base = dict(n_paths=5, block_size=5, seed=1)
    base.update(kwargs)
    with pytest.raises(ConfigurationError):
        runner.generate_paths(df, **base)
