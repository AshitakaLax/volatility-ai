import pandas as pd
import pytest

from optimization_controller import OptimizationController
from src.size_calculators import FixedPortfolioPercentage
from src.intraday_validation import IntradayValidator


def _intraday_fixture():
    return pd.DataFrame(
        {
            "open": [100.0, 99.0, 99.0],
            "high": [100.0, 99.5, 101.5],
            "low": [100.0, 98.5, 98.5],
            "close": [100.0, 99.0, 99.0],
            "volume": [1000, 1000, 1000],
        },
        index=pd.date_range("2024-01-01", periods=3, freq="min", tz="UTC"),
    )


def test_intraday_replay_detects_sell_target_touched_above_close():
    data = _intraday_fixture()
    finalists = [{"Grid Step": 0.01, "Profit Target": 0.01, "percentage": 0.01}]

    daily = OptimizationController(data[["close"]]).run_sweep(
        [0.01], [0.01], FixedPortfolioPercentage, [{"percentage": 0.01}]
    ).iloc[0]
    assert daily["Trade Count"] == 0

    result = IntradayValidator().validate_finalists_intraday(
        finalists,
        data,
        strategy_class=FixedPortfolioPercentage,
        strategy_params_grid=[{"percentage": 0.01}],
    ).iloc[0]

    assert result["Intraday Trade Count"] == 1
    assert result["Intraday Final Portfolio Value"] > 100000.0


def test_intraday_priority_is_configurable_and_validated():
    assert IntradayValidator(intrabar_priority="buy_first").intrabar_priority == "buy_first"
    with pytest.raises(ValueError):
        IntradayValidator(intrabar_priority="unknown")


def test_controller_exposes_intraday_validation_pass():
    controller = OptimizationController(_intraday_fixture())
    result = controller.validate_finalists_intraday(
        [{"Grid Step": 0.01, "Profit Target": 0.01, "percentage": 0.01}],
        _intraday_fixture(),
        strategy_class=FixedPortfolioPercentage,
        strategy_params_grid=[{"percentage": 0.01}],
    )
    assert result.loc[0, "Intraday Trade Count"] == 1
