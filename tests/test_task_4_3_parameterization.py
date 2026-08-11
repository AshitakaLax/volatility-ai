import pandas as pd

from optimization_controller import OptimizationController
from src.size_calculators import FixedPortfolioPercentage


def _fixture():
    return pd.DataFrame(
        {
            "open": [100.0, 99.0, 98.0],
            "high": [100.0, 99.0, 98.0],
            "low": [100.0, 99.0, 98.0],
            "close": [100.0, 99.0, 98.0],
            "volume": [1_000, 1_000, 1_000],
        },
        index=pd.date_range("2024-01-01", periods=3, freq="D"),
    )


def test_default_symbol_and_cash_preserve_execution():
    result = OptimizationController(_fixture()).run_sweep(
        [0.01], [0.01], FixedPortfolioPercentage, [{"percentage": 0.01}]
    )
    assert len(result) == 1
    assert result.iloc[0]["Final Portfolio Value"] > 0


def test_custom_symbol_and_initial_cash_are_threaded_to_simulation(monkeypatch):
    controller = OptimizationController(_fixture())
    seen = []

    original = controller._simulate_single

    def wrapped(step, target, strategy, symbol, initial_cash, cost_model, risk_manager):
        seen.append((symbol, initial_cash))
        return original(step, target, strategy, symbol, initial_cash, cost_model, risk_manager)

    monkeypatch.setattr(controller, "_simulate_single", wrapped)
    controller.run_sweep(
        [0.01], [0.01], FixedPortfolioPercentage, [{"percentage": 0.01}],
        symbol="SPXL", initial_cash=50_000.0,
    )
    assert seen == [("SPXL", 50_000.0)]
