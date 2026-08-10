"""Focused regression tests for Task 1.2: drawdown is sampled every bar."""

import pandas as pd
import pytest

from optimization_controller import OptimizationController
from src.size_calculators import FixedPortfolioPercentage


def test_max_drawdown_includes_non_trigger_bar():
    """The deepest drawdown can occur on a bar that does not trigger a buy."""
    index = pd.date_range("2026-01-01", periods=5, freq="D")
    data = pd.DataFrame(
        {
            "open": [100.0, 99.0, 98.5, 99.5, 100.0],
            "high": [100.0, 99.0, 98.5, 99.5, 100.0],
            "low": [100.0, 99.0, 98.5, 99.5, 100.0],
            "close": [100.0, 99.0, 98.5, 99.5, 100.0],
            "volume": [1_000] * 5,
        },
        index=index,
    )

    result = OptimizationController(data).run_sweep(
        grid_steps=[0.01],
        profit_targets=[0.5],
        strategy_class=FixedPortfolioPercentage,
        strategy_params_grid=[{"percentage": 0.05}],
    ).iloc[0]

    # The buy occurs at 99. The next bar at 98.5 is only a 0.505% decline
    # from the last buy, so it is not a 1% grid trigger. Nevertheless the
    # open position loses value and must contribute to max drawdown.
    expected = ((100_000.0 - 5_000.0 + (5_000.0 / 99.0) * 98.5) / 100_000.0)
    expected *= 100.0

    assert result["Max Drawdown %"] == pytest.approx(expected)
    assert result["Max Drawdown %"] > 0.0
