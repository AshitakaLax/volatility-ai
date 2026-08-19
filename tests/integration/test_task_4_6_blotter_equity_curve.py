"""
Task 4.6 acceptance tests (A6).

1. return_full_results=False (default) reproduces the existing
   regression baseline exactly, including return type (single DataFrame).
2. return_full_results=True additionally returns one SimulationResult
   per combination, whose trade_blotter row count matches the
   combination's actual buys+sells and whose equity_curve has one
   entry per bar in the input data.
3. SimulationResult.metrics contains every key
   PerformanceAnalyzer.calculate_metrics originally returned, unmodified.
"""

import pandas as pd

from optimization_controller import OptimizationController
from src.cost_models import ZeroCostModel
from src.ledger import AssetLotLedger
from src.market_context import SimulationResult
from src.performance_analyzer import PerformanceAnalyzer
from src.risk_manager import RiskManager
from src.size_calculators import FixedPortfolioPercentage
from tests.fixtures.regression_baseline import BASELINE


def _load_fixture() -> pd.DataFrame:
    df = pd.read_csv("tests/fixtures/regression_ohlcv.csv", parse_dates=["timestamp"])
    df.set_index("timestamp", inplace=True)
    return df


def test_return_full_results_false_default_unchanged_return_type_and_baseline():
    df = _load_fixture()
    result = OptimizationController(historical_data=df).run_sweep(
        grid_steps=[BASELINE["Grid Step"]],
        profit_targets=[BASELINE["Profit Target"]],
        strategy_class=FixedPortfolioPercentage,
        strategy_params_grid=[{"allocation_pct": BASELINE["allocation_pct"]}],
        # return_full_results omitted -> default False.
    )
    assert isinstance(result, pd.DataFrame)  # not a tuple
    row = result.iloc[0]
    for key, expected in BASELINE.items():
        assert row[key] == expected


def test_return_full_results_true_returns_tuple_with_matching_blotter_and_curve():
    df = _load_fixture()
    n_bars = len(df)
    summary_df, full_results = OptimizationController(historical_data=df).run_sweep(
        grid_steps=[BASELINE["Grid Step"]],
        profit_targets=[BASELINE["Profit Target"]],
        strategy_class=FixedPortfolioPercentage,
        strategy_params_grid=[{"allocation_pct": BASELINE["allocation_pct"]}],
        return_full_results=True,
    )
    assert isinstance(summary_df, pd.DataFrame)
    assert isinstance(full_results, list)
    assert len(full_results) == 1
    assert isinstance(full_results[0], SimulationResult)

    sim_result = full_results[0]
    summary_row = summary_df.iloc[0]

    # Blotter row count matches actual buys+sells for this combination:
    # each closed lot is 1 buy + 1 sell, each still-open lot is 1 buy only.
    expected_tickets = summary_row["Closed Trade Count"] * 2 + summary_row["Open Trade Count"]
    assert len(sim_result.trade_blotter) == expected_tickets
    assert set(sim_result.trade_blotter["side"]) <= {"buy", "sell"}

    # Equity curve has exactly one entry per bar in the input data.
    assert len(sim_result.equity_curve) == n_bars


def test_summary_df_and_full_results_stay_paired_after_sorting():
    # Multiple combinations, sorted by Capital Velocity Index -- verify
    # summary_df.iloc[i] and full_results[i] describe the SAME
    # combination after the sort reorders both.
    df = _load_fixture()
    summary_df, full_results = OptimizationController(historical_data=df).run_sweep(
        grid_steps=[0.01],
        profit_targets=[0.003, 0.005, 0.01],
        strategy_class=FixedPortfolioPercentage,
        strategy_params_grid=[{"allocation_pct": 0.05}],
        return_full_results=True,
    )
    assert len(summary_df) == len(full_results) == 3
    for i in range(len(summary_df)):
        row = summary_df.iloc[i]
        sim_result = full_results[i]
        assert sim_result is not None
        assert row["Final Equity"] == sim_result.metrics["Final Equity"]
        assert row["Profit Target"] == sim_result.params["target"]


def test_failed_combination_contributes_none_to_full_results():
    from src.market_context import MarketContext
    from src.size_calculators import SizingStrategy

    class _ExplodingStrategy(SizingStrategy):
        def __init__(self, divisor: float):
            self.divisor = divisor

        def record_tick(self, context: MarketContext) -> None:
            pass

        def calculate_trade_value(self, context: MarketContext) -> float:
            return context.equity * 0.05 / self.divisor

    df = _load_fixture()
    summary_df, full_results = OptimizationController(historical_data=df).run_sweep(
        grid_steps=[0.01],
        profit_targets=[0.005],
        strategy_class=_ExplodingStrategy,
        strategy_params_grid=[{"divisor": 1.0}, {"divisor": 0.0}],
        return_full_results=True,
    )
    assert len(full_results) == 2
    none_count = sum(1 for r in full_results if r is None)
    assert none_count == 1
    for i, sim_result in enumerate(full_results):
        if sim_result is None:
            assert pd.notna(summary_df.iloc[i].get("error"))
        else:
            assert "error" not in summary_df.columns or pd.isna(summary_df.iloc[i].get("error"))


def test_simulation_result_metrics_passes_through_every_performance_analyzer_key():
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

    # Independently call PerformanceAnalyzer to get its real key set
    # rather than assuming it.
    probe_metrics = PerformanceAnalyzer.calculate_metrics(AssetLotLedger(), 100_000.0, 100_000.0)

    for key in probe_metrics:
        assert key in result.metrics, (
            f"PerformanceAnalyzer key {key!r} was dropped from SimulationResult.metrics"
        )
