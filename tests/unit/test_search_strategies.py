"""
Task 5.3 acceptance tests (M3).

1. search_strategy="grid" (default) reproduces the existing regression
   baseline exactly, including evaluating every combination.
2. search_strategy="bayesian" on a fixture with a known optimum finds
   a combination within 5% of it using no more than 75% of the
   evaluations the equivalent full grid would need.

Known-optimum fixture and all figures below were determined
empirically (running the real exhaustive grid once) and verified
directly in the chat this test was produced in before being written,
including a 5-seed robustness check with an even smaller (30-trial,
~47%) budget than the 40 used here -- 40/64 = 62.5%, comfortably under
the 75% ceiling. "Total Return %" is used as rank_by rather than the
system default "Capital Velocity Index" specifically because every
combination on this fixture harvests every lot (Capital Velocity Index
== 1.0 for all 64 -- verified, not assumed), which would make "within
5%" trivially true for any answer; Total Return % has real spread
(0.08 to 3.97) and only 1 of 64 combinations lands within 5% of the
true optimum, so finding it is a genuine test of convergence.
"""

import pandas as pd
import pytest

from optimization_controller import OptimizationController
from src.exceptions import ConfigurationError
from src.search_strategies import BayesianSearch, GridSearch, SearchStrategy
from src.size_calculators import FixedPortfolioPercentage
from tests.fixtures.regression_baseline import BASELINE

GRID_STEPS = [0.01, 0.02, 0.03, 0.04]
PROFIT_TARGETS = [0.01, 0.02, 0.03, 0.04]
ALLOCATIONS = [0.02, 0.04, 0.06, 0.08]
STRATEGY_PARAMS_GRID = [{"allocation_pct": a} for a in ALLOCATIONS]
TRUE_OPTIMUM_TOTAL_RETURN_PCT = 3.967736885090578  # Grid Step=0.01, Profit Target=0.04, allocation_pct=0.06


def _known_optimum_fixture() -> pd.DataFrame:
    closes = [100.0]
    for _ in range(20):
        closes.append(closes[-1] * 0.99)  # decline ~18%
    for _ in range(40):
        closes.append(closes[-1] * 1.02)  # strong recovery
    idx = pd.date_range("2024-01-01", periods=len(closes), freq="D", tz="UTC")
    return pd.DataFrame(
        {
            "open": [closes[0]] + closes[:-1],
            "high": [c * 1.002 for c in closes],
            "low": [c * 0.998 for c in closes],
            "close": closes,
            "volume": 1_000_000,
        },
        index=idx,
    )


def _regression_fixture() -> pd.DataFrame:
    df = pd.read_csv("tests/fixtures/regression_ohlcv.csv", parse_dates=["timestamp"])
    df.set_index("timestamp", inplace=True)
    return df


def test_grid_search_matches_itertools_product_exactly():
    import itertools

    expected = list(itertools.product(GRID_STEPS, PROFIT_TARGETS, STRATEGY_PARAMS_GRID))
    gs = GridSearch(GRID_STEPS, PROFIT_TARGETS, STRATEGY_PARAMS_GRID)
    actual = []
    while True:
        s = gs.suggest()
        if s is None:
            break
        actual.append((s["grid_step"], s["profit_target"], s["strategy_params"]))
    assert actual == expected


def test_search_strategy_default_reproduces_task_0_1_baseline():
    df = _regression_fixture()
    row = OptimizationController(historical_data=df).run_sweep(
        grid_steps=[BASELINE["Grid Step"]],
        profit_targets=[BASELINE["Profit Target"]],
        strategy_class=FixedPortfolioPercentage,
        strategy_params_grid=[{"allocation_pct": BASELINE["allocation_pct"]}],
    ).iloc[0]
    for key, expected in BASELINE.items():
        assert row[key] == expected


def test_search_strategy_grid_string_reproduces_baseline():
    df = _regression_fixture()
    row = OptimizationController(historical_data=df).run_sweep(
        grid_steps=[BASELINE["Grid Step"]],
        profit_targets=[BASELINE["Profit Target"]],
        strategy_class=FixedPortfolioPercentage,
        strategy_params_grid=[{"allocation_pct": BASELINE["allocation_pct"]}],
        search_strategy="grid",
    ).iloc[0]
    for key, expected in BASELINE.items():
        assert row[key] == expected


def test_search_strategy_grid_evaluates_every_combination():
    df = _regression_fixture()
    result = OptimizationController(historical_data=df).run_sweep(
        grid_steps=[0.005, 0.01, 0.015],
        profit_targets=[0.003, 0.005],
        strategy_class=FixedPortfolioPercentage,
        strategy_params_grid=[{"allocation_pct": a} for a in [0.02, 0.05]],
        search_strategy="grid",
    )
    assert len(result) == 3 * 2 * 2


def test_bayesian_search_finds_near_optimum_with_62_percent_of_evaluations():
    df = _known_optimum_fixture()
    controller = OptimizationController(historical_data=df)
    full_grid_size = len(GRID_STEPS) * len(PROFIT_TARGETS) * len(STRATEGY_PARAMS_GRID)
    n_trials = 40
    assert n_trials / full_grid_size <= 0.75

    search = BayesianSearch(
        GRID_STEPS, PROFIT_TARGETS, STRATEGY_PARAMS_GRID, rank_by="Total Return %", n_trials=n_trials, seed=42
    )
    result = controller.run_sweep(
        grid_steps=GRID_STEPS, profit_targets=PROFIT_TARGETS,
        strategy_class=FixedPortfolioPercentage, strategy_params_grid=STRATEGY_PARAMS_GRID,
        search_strategy=search,
    )
    assert len(result) == n_trials
    best_found = result["Total Return %"].max()
    assert best_found >= TRUE_OPTIMUM_TOTAL_RETURN_PCT * 0.95


def test_bayesian_search_reproducible_with_same_seed():
    df = _known_optimum_fixture()
    controller = OptimizationController(historical_data=df)

    def _run(seed):
        search = BayesianSearch(GRID_STEPS, PROFIT_TARGETS, STRATEGY_PARAMS_GRID, n_trials=15, seed=seed)
        return controller.run_sweep(
            grid_steps=GRID_STEPS, profit_targets=PROFIT_TARGETS,
            strategy_class=FixedPortfolioPercentage, strategy_params_grid=STRATEGY_PARAMS_GRID,
            search_strategy=search,
        )

    result1 = _run(42)
    result2 = _run(42)
    pd.testing.assert_frame_equal(
        result1.sort_values(by=list(result1.columns)).reset_index(drop=True),
        result2.sort_values(by=list(result2.columns)).reset_index(drop=True),
    )


def test_search_strategy_bayesian_string_uses_search_seed():
    df = _known_optimum_fixture()
    controller = OptimizationController(historical_data=df)
    result1 = controller.run_sweep(
        grid_steps=GRID_STEPS, profit_targets=PROFIT_TARGETS,
        strategy_class=FixedPortfolioPercentage, strategy_params_grid=STRATEGY_PARAMS_GRID,
        search_strategy="bayesian", search_seed=7,
    )
    result2 = controller.run_sweep(
        grid_steps=GRID_STEPS, profit_targets=PROFIT_TARGETS,
        strategy_class=FixedPortfolioPercentage, strategy_params_grid=STRATEGY_PARAMS_GRID,
        search_strategy="bayesian", search_seed=7,
    )
    pd.testing.assert_frame_equal(
        result1.sort_values(by=list(result1.columns)).reset_index(drop=True),
        result2.sort_values(by=list(result2.columns)).reset_index(drop=True),
    )


def test_failed_evaluation_reported_to_bayesian_search_without_crashing():
    from src.market_context import MarketContext
    from src.size_calculators import SizingStrategy

    class _ExplodingStrategy(SizingStrategy):
        def __init__(self, divisor: float):
            self.divisor = divisor

        def record_tick(self, context: MarketContext) -> None:
            pass

        def calculate_trade_value(self, context: MarketContext) -> float:
            return context.equity * 0.05 / self.divisor

    df = _regression_fixture()
    controller = OptimizationController(historical_data=df)
    search = BayesianSearch(
        [0.01], [0.005], [{"divisor": 1.0}, {"divisor": 0.0}, {"divisor": 2.0}], n_trials=3, seed=1
    )
    result = controller.run_sweep(
        grid_steps=[0.01], profit_targets=[0.005],
        strategy_class=_ExplodingStrategy,
        strategy_params_grid=[{"divisor": 1.0}, {"divisor": 0.0}, {"divisor": 2.0}],
        search_strategy=search,
    )
    assert len(result) == 3
    assert result["error"].notna().sum() == 1


def test_search_strategy_instance_used_directly():
    df = _regression_fixture()
    custom = GridSearch([0.01], [0.005], [{"allocation_pct": 0.05}])
    # grid_steps/profit_targets/strategy_params_grid here are still
    # validated by validate_run_sweep_config (Task 4.9) even though
    # they're functionally unused for enumeration once a pre-built
    # SearchStrategy is supplied -- valid dummy values, not the
    # actual search space, since GridSearch(custom) already owns that.
    result = OptimizationController(historical_data=df).run_sweep(
        grid_steps=[0.99], profit_targets=[0.99],
        strategy_class=FixedPortfolioPercentage, strategy_params_grid=[{"allocation_pct": 0.5}],
        search_strategy=custom,
    )
    assert len(result) == 1
    assert result.iloc[0]["Grid Step"] == 0.01


def test_invalid_search_strategy_value_rejected():
    df = _regression_fixture()
    with pytest.raises(ConfigurationError, match="search_strategy"):
        OptimizationController(historical_data=df).run_sweep(
            grid_steps=[0.01], profit_targets=[0.005],
            strategy_class=FixedPortfolioPercentage, strategy_params_grid=[{"allocation_pct": 0.05}],
            search_strategy="genetic_algorithm",
        )


def test_bayesian_search_missing_optuna_raises_configuration_error(monkeypatch):
    import builtins

    real_import = builtins.__import__

    def fake_import(name, *args, **kwargs):
        if name == "optuna":
            raise ImportError("simulated: optuna not installed")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", fake_import)
    with pytest.raises(ConfigurationError, match="optuna"):
        BayesianSearch([0.01], [0.005], [{"allocation_pct": 0.05}])


def test_grid_search_is_a_search_strategy():
    gs = GridSearch([0.01], [0.005], [{"allocation_pct": 0.05}])
    assert isinstance(gs, SearchStrategy)
