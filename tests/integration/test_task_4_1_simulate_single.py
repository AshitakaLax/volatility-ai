"""
Task 4.1 acceptance tests (A1).

1. Calling _simulate_single directly with a single parameter
   combination executes without raising and returns a valid
   SimulationResult.
2. run_sweep's output matrix is mathematically identical value-for-
   value to the pre-Task-4.1 regression baseline.

Plus: MarketContext is genuinely frozen, and no ledger/OMS/strategy
state leaks between combinations within one run_sweep call.
"""

import dataclasses
from pathlib import Path

import pandas as pd
import pytest

from optimization_controller import OptimizationController
from src.cost_models import ZeroCostModel
from src.market_context import MarketContext, SimulationResult
from src.risk_manager import RiskManager
from src.size_calculators import FixedPortfolioPercentage
from tests.fixtures.regression_baseline import BASELINE

FIXTURE_PATH = Path(__file__).resolve().parents[1] / "fixtures" / "regression_ohlcv.csv"


def _load_fixture() -> pd.DataFrame:
    df = pd.read_csv(FIXTURE_PATH, parse_dates=["timestamp"])
    df.set_index("timestamp", inplace=True)
    return df


def test_simulate_single_callable_directly_returns_valid_simulation_result():
    df = _load_fixture()
    controller = OptimizationController(historical_data=df)
    strategy = FixedPortfolioPercentage(allocation_pct=0.05)

    result = controller._simulate_single(
        step=0.01,
        target=0.005,
        strategy_instance=strategy,
        symbol="TQQQ",
        initial_cash=100_000.0,
        cost_model=ZeroCostModel(),
        risk_manager=RiskManager(),
    )

    assert isinstance(result, SimulationResult)
    assert isinstance(result.metrics, dict)
    assert "Final Equity" in result.metrics
    assert "Max Drawdown %" in result.metrics
    # Task 4.6 landed after this test was first written -- trade_blotter/
    # equity_curve/params are populated now, not at their empty defaults.
    # See tests/integration/test_task_4_6_blotter_equity_curve.py for the
    # dedicated tests on their actual content.
    assert not result.trade_blotter.empty
    assert not result.equity_curve.empty
    assert result.params != {}


def test_run_sweep_output_matches_pre_task_4_1_baseline_exactly():
    df = _load_fixture()
    result = OptimizationController(historical_data=df).run_sweep(
        grid_steps=[BASELINE["Grid Step"]],
        profit_targets=[BASELINE["Profit Target"]],
        strategy_class=FixedPortfolioPercentage,
        strategy_params_grid=[{"allocation_pct": BASELINE["allocation_pct"]}],
    ).iloc[0]
    for key, expected in BASELINE.items():
        assert result[key] == expected, f"{key}: {result[key]!r} != baseline {expected!r} post-Task-4.1"


def test_market_context_is_genuinely_frozen():
    context = MarketContext(
        timestamp=None, open=1.0, high=1.0, low=1.0, close=1.0,
        cash=1.0, equity=1.0, peak_equity=1.0, drawdown=0.0,
        open_lot_count=0, bar_index=0,
    )
    with pytest.raises(dataclasses.FrozenInstanceError):
        context.close = 2.0


def test_market_context_price_property_returns_close():
    context = MarketContext(
        timestamp=None, open=1.0, high=1.0, low=1.0, close=42.0,
        cash=1.0, equity=1.0, peak_equity=1.0, drawdown=0.0,
        open_lot_count=0, bar_index=0,
    )
    assert context.price == 42.0


def test_no_state_leaks_between_combinations():
    # Two combinations with very different grid steps in the same
    # run_sweep call must produce independent trade counts -- if
    # ledger/OMS state leaked between combinations, the second
    # combination's count would be contaminated by the first's.
    df = _load_fixture()
    result = OptimizationController(historical_data=df).run_sweep(
        grid_steps=[0.005, 0.05],  # one much more sensitive than the other
        profit_targets=[0.005],
        strategy_class=FixedPortfolioPercentage,
        strategy_params_grid=[{"allocation_pct": 0.05}],
    )
    assert len(result) == 2
    tight_step_row = result[result["Grid Step"] == 0.005].iloc[0]
    wide_step_row = result[result["Grid Step"] == 0.05].iloc[0]
    assert tight_step_row["Trade Count"] != wide_step_row["Trade Count"]
