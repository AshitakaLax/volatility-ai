import pandas as pd
from optimization_controller import OptimizationController
from src.market_context import SimulationResult
from src.size_calculators import FixedPortfolioPercentage


def test_task_4_6_full_results():
    data = pd.DataFrame({"open": [100, 99, 98], "high": [101, 100, 99], "low": [99, 98, 97], "close": [100, 99, 98], "volume": [1000, 1000, 1000]}, index=pd.date_range("2024-01-01", periods=3))
    summary, full = OptimizationController(data).run_sweep([0.01], [0.01], FixedPortfolioPercentage, [{"percentage": 0.01}], return_full_results=True)
    assert isinstance(summary, pd.DataFrame)
    assert len(full) == 1
    assert isinstance(full[0], SimulationResult)
    assert len(full[0].equity_curve) == len(data)
    assert list(full[0].trade_blotter.columns) == ["timestamp", "side", "price", "qty", "equity"]
    assert "Capital Velocity Index" in full[0].metrics
