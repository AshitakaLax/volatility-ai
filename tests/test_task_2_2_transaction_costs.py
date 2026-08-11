import pandas as pd
import pytest

from optimization_controller import OptimizationController
from src.cost_models import SlippageCommissionModel, ZeroCostModel
from src.size_calculators import FixedPortfolioPercentage


def fixture_data():
    return pd.DataFrame(
        {"close": [100.0, 99.0, 98.0, 99.5, 100.0, 101.0]},
        index=pd.date_range("2024-01-01", periods=6, freq="D", tz="UTC"),
    )


def run(model):
    return OptimizationController(fixture_data()).run_sweep(
        grid_steps=[0.01],
        profit_targets=[0.01],
        strategy_class=FixedPortfolioPercentage,
        strategy_params_grid=[{"percentage": 0.10}],
        cost_model=model,
    ).iloc[0]


def test_zero_cost_model_preserves_default_economics():
    default = run(None)
    explicit = run(ZeroCostModel())
    for metric in ["Final Portfolio Value", "Trade Count", "Total Return %", "Capital Velocity Index", "Max Drawdown %"]:
        assert default[metric] == pytest.approx(explicit[metric])


def test_slippage_and_commission_reduce_final_equity():
    zero = run(ZeroCostModel())
    costs = run(SlippageCommissionModel(commission_per_trade=1.0, slippage_bps=5.0))
    assert costs["Final Portfolio Value"] < zero["Final Portfolio Value"]


def test_cost_model_buy_sell_directionality():
    model = SlippageCommissionModel(commission_per_trade=1.0, slippage_bps=5.0)
    buy_price, buy_cost = model.apply_buy(100.0, 10.0)
    sell_price, sell_cost = model.apply_sell(100.0, 10.0)
    assert buy_price > 100.0
    assert sell_price < 100.0
    assert buy_cost == sell_cost == 1.0
