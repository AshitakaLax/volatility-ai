import importlib.util

import pandas as pd
import pytest

from optimization_controller import OptimizationController
from src.market_context import SimulationResult
from src.search_strategies import GridSearch
from src.size_calculators import FixedPortfolioPercentage


def test_grid_search_preserves_cartesian_order():
    combinations = [
        {"Grid Step": 0.01, "Profit Target": 0.02, "percentage": 0.1},
        {"Grid Step": 0.01, "Profit Target": 0.03, "percentage": 0.1},
        {"Grid Step": 0.02, "Profit Target": 0.02, "percentage": 0.1},
    ]
    search = GridSearch(combinations)
    assert [search.suggest() for _ in combinations] == combinations
    with pytest.raises(StopIteration):
        search.suggest()


def test_default_grid_sweep_evaluates_every_combination():
    data = pd.DataFrame({"close": [100.0, 99.0, 98.0]}, index=pd.date_range("2024-01-01", periods=3))
    result = OptimizationController(data).run_sweep(
        grid_steps=[0.01, 0.02],
        profit_targets=[0.01, 0.02],
        strategy_class=FixedPortfolioPercentage,
        strategy_params_grid=[{"percentage": 0.01}],
    )
    assert len(result) == 4


def test_bayesian_requires_optuna_dependency():
    if importlib.util.find_spec("optuna") is not None:
        pytest.skip("Optuna installed; dependency-error path is not applicable")
    data = pd.DataFrame({"close": [100.0, 99.0, 98.0]}, index=pd.date_range("2024-01-01", periods=3))
    with pytest.raises(Exception, match="Optuna"):
        OptimizationController(data).run_sweep(
            grid_steps=[0.01],
            profit_targets=[0.01],
            strategy_class=FixedPortfolioPercentage,
            strategy_params_grid=[{"percentage": 0.01}],
            search_strategy="bayesian",
        )


@pytest.mark.skipif(importlib.util.find_spec("optuna") is None, reason="Optuna is an explicit runtime dependency for Bayesian search")
def test_bayesian_seed_is_reproducible_and_uses_at_most_75_percent_of_grid():
    from src.search_strategies import BayesianSearch

    combinations = [
        {"Grid Step": step, "Profit Target": target, "percentage": percentage}
        for step in [0.01, 0.02]
        for target in [0.01, 0.02]
        for percentage in [0.01, 0.02]
    ]
    first = BayesianSearch(combinations, rank_by="score", seed=7, n_trials=4)
    second = BayesianSearch(combinations, rank_by="score", seed=7, n_trials=4)
    first_suggestions = []
    second_suggestions = []
    for _ in range(4):
        p1 = first.suggest()
        p2 = second.suggest()
        first_suggestions.append(p1)
        second_suggestions.append(p2)
        result = SimulationResult(metrics={"score": float(p1["Grid Step"])})
        first.report(p1, result)
        second.report(p2, result)
    assert first_suggestions == second_suggestions
    assert first.completed_trials == 4
    assert first.completed_trials <= int(len(combinations) * 0.75)
