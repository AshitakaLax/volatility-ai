import pandas as pd

from optimization_controller import OptimizationController
from src.risk_manager import RiskManager
from src.size_calculators import FixedPortfolioPercentage


def _data():
    return pd.DataFrame(
        {"close": [100.0, 99.0, 98.0, 97.0]},
        index=pd.date_range("2024-01-01", periods=4, freq="D"),
    )


def _run(risk_manager):
    return OptimizationController(_data()).run_sweep(
        grid_steps=[0.01],
        profit_targets=[0.01],
        strategy_class=FixedPortfolioPercentage,
        strategy_params_grid=[{"percentage": 0.10}],
        risk_manager=risk_manager,
    ).iloc[0]


def test_risk_manager_is_applied_before_buy_submission():
    unrestricted = _run(RiskManager())
    one_lot = _run(RiskManager(max_concurrent_lots=1))

    assert one_lot["Trade Count"] < unrestricted["Trade Count"]


def test_risk_manager_none_preserves_unlimited_behavior():
    default = _run(None)
    explicit = _run(RiskManager())
    assert default["Final Portfolio Value"] == explicit["Final Portfolio Value"]
    assert default["Trade Count"] == explicit["Trade Count"]


def test_exposure_limit_reduces_trade_value_without_changing_strategy():
    unrestricted = _run(RiskManager())
    constrained = _run(RiskManager(max_total_exposure=0.05))
    assert constrained["Final Portfolio Value"] != unrestricted["Final Portfolio Value"]
