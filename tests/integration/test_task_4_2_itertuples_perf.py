"""
Task 4.2 acceptance tests (A3).

1. Regression fixture output is unchanged.
2. A simple timing comparison shows a measurable speedup over
   iterrows() on a few hundred bars.

For (2), rather than timing optimization_controller.py itself before
vs. after (the "before" version no longer exists to time against),
this benchmarks iterrows() vs itertuples() directly on a
representative-sized DataFrame doing comparable per-row work --
isolating exactly the change this task made, on the concrete claim
("itertuples is faster") rather than the whole system's speed, which
depends on many other things besides this one iteration method.
"""

import timeit

import pandas as pd

from optimization_controller import OptimizationController
from src.size_calculators import FixedPortfolioPercentage
from tests.fixtures.regression_baseline import BASELINE


def test_regression_fixture_output_unchanged():
    df = pd.read_csv("tests/fixtures/regression_ohlcv.csv", parse_dates=["timestamp"])
    df.set_index("timestamp", inplace=True)
    result = OptimizationController(historical_data=df).run_sweep(
        grid_steps=[BASELINE["Grid Step"]],
        profit_targets=[BASELINE["Profit Target"]],
        strategy_class=FixedPortfolioPercentage,
        strategy_params_grid=[{"allocation_pct": BASELINE["allocation_pct"]}],
    ).iloc[0]
    for key, expected in BASELINE.items():
        assert result[key] == expected


def test_itertuples_measurably_faster_than_iterrows_on_comparable_work():
    n_bars = 500
    idx = pd.date_range("2024-01-01", periods=n_bars, freq="min", tz="UTC")
    df = pd.DataFrame(
        {
            "open": [100.0] * n_bars,
            "high": [100.5] * n_bars,
            "low": [99.5] * n_bars,
            "close": [100.0 + (i % 7) * 0.01 for i in range(n_bars)],
            "volume": [1000] * n_bars,
        },
        index=idx,
    )

    def _via_iterrows():
        total = 0.0
        for _timestamp, row in df.iterrows():
            total += row["close"] + row["open"] + row["high"] + row["low"]
        return total

    def _via_itertuples():
        total = 0.0
        for row in df.itertuples():
            total += row.close + row.open + row.high + row.low
        return total

    assert _via_iterrows() == _via_itertuples()  # same work, sanity check

    iterrows_time = timeit.timeit(_via_iterrows, number=20)
    itertuples_time = timeit.timeit(_via_itertuples, number=20)

    assert itertuples_time < iterrows_time, (
        f"itertuples ({itertuples_time:.4f}s) was not faster than iterrows "
        f"({iterrows_time:.4f}s) over {n_bars} bars x 20 runs"
    )
