from pathlib import Path

import pandas as pd
import pytest

from optimization_controller import OptimizationController
from src.risk_manager import RiskManager
from src.size_calculators import FixedPortfolioPercentage
from tests.fixtures.regression_baseline import BASELINE

FIXTURE_PATH = Path(__file__).resolve().parents[1] / "fixtures" / "regression_ohlcv.csv"


def _load_fixture() -> pd.DataFrame:
    df = pd.read_csv(FIXTURE_PATH, parse_dates=["timestamp"])
    df.set_index("timestamp", inplace=True)
    return df


def _run(df, risk_manager=None):
    kwargs = {}
    if risk_manager is not None:
        kwargs["risk_manager"] = risk_manager
    return OptimizationController(historical_data=df).run_sweep(
        grid_steps=[BASELINE["Grid Step"]],
        profit_targets=[BASELINE["Profit Target"]],
        strategy_class=FixedPortfolioPercentage,
        strategy_params_grid=[{"allocation_pct": BASELINE["allocation_pct"]}],
        **kwargs,
    ).iloc[0]


def test_risk_manager_omitted_matches_baseline():
    row = _run(_load_fixture())
    for key, expected in BASELINE.items():
        assert row[key] == expected


def test_explicit_unlimited_risk_manager_matches_baseline():
    row = _run(_load_fixture(), risk_manager=RiskManager())
    for key, expected in BASELINE.items():
        assert row[key] == expected


def test_max_concurrent_lots_caps_trade_count():
    # Baseline fixture opens 4 lots with no cap (verified in Task 0.1);
    # verified numerically before writing this test that no harvests
    # interleave before all 4 would otherwise fire, so a cap of 2
    # cleanly caps the trade count at 2, not some other interaction.
    df = _load_fixture()
    row = _run(df, risk_manager=RiskManager(max_concurrent_lots=2))
    assert row["Trade Count"] == 2
    assert row["Final Equity"] < BASELINE["Final Equity"], "Fewer trades harvested -> less total profit"


def test_max_concurrent_lots_never_blocks_below_the_cap():
    df = _load_fixture()
    row = _run(df, risk_manager=RiskManager(max_concurrent_lots=10))  # above the natural 4
    assert row["Trade Count"] == BASELINE["Trade Count"]
