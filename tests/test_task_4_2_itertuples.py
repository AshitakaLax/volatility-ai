import inspect

import pandas as pd

from optimization_controller import OptimizationController
from src.size_calculators import FixedPortfolioPercentage


def test_simulation_loop_uses_itertuples_and_preserves_result_shape():
    data = pd.DataFrame(
        {
            "open": [100.0, 99.0, 98.0, 101.0],
            "high": [101.0, 100.0, 99.0, 102.0],
            "low": [99.0, 98.0, 97.0, 100.0],
            "close": [100.0, 99.0, 98.0, 101.0],
            "volume": [1000, 1000, 1000, 1000],
        },
        index=pd.date_range("2024-01-01", periods=4, freq="D"),
    )
    controller = OptimizationController(data)
    source = inspect.getsource(OptimizationController._simulate_single)
    assert ".itertuples(" in source
    assert ".iterrows(" not in source

    result = controller.run_sweep(
        grid_steps=[0.01],
        profit_targets=[0.01],
        strategy_class=FixedPortfolioPercentage,
        strategy_params_grid=[{"percentage": 0.01}],
    )
    assert len(result) == 1
    assert "Final Portfolio Value" in result.columns
    assert "Capital Velocity Index" in result.columns
