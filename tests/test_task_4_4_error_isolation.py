import pandas as pd

from optimization_controller import OptimizationController
from src.size_calculators import FixedPortfolioPercentage


class FailingStrategy(FixedPortfolioPercentage):
    def __init__(self, percentage=0.01, fail=False):
        if fail:
            raise ZeroDivisionError("deliberate combination failure")
        super().__init__(percentage=percentage)


def test_one_bad_combination_does_not_abort_the_sweep():
    data = pd.DataFrame({"close": [100.0, 99.0, 98.0]}, index=pd.date_range("2024-01-01", periods=3))
    controller = OptimizationController(data)

    result = controller.run_sweep(
        grid_steps=[0.01],
        profit_targets=[0.01],
        strategy_class=FailingStrategy,
        strategy_params_grid=[{"fail": False}, {"fail": True}, {"fail": False}],
    )

    assert len(result) == 3
    assert result["error"].notna().sum() == 1
    assert result["Final Portfolio Value"].notna().sum() == 2
    assert "deliberate combination failure" in result.loc[result["error"].notna(), "error"].iloc[0]


def test_successful_combinations_keep_normal_metrics():
    data = pd.DataFrame({"close": [100.0, 99.0, 98.0]}, index=pd.date_range("2024-01-01", periods=3))
    controller = OptimizationController(data)
    result = controller.run_sweep(
        grid_steps=[0.01],
        profit_targets=[0.01],
        strategy_class=FixedPortfolioPercentage,
        strategy_params_grid=[{"percentage": 0.01}],
    )
    assert result.iloc[0]["error"] != result.iloc[0]["error"]  # NaN
    assert pd.notna(result.iloc[0]["Final Portfolio Value"])
