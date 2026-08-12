import pytest

from src.config import BacktestConfig
from src.exceptions import ConfigurationError


def valid_config():
    return {
        "strategy": {"strategy_id": "fixed_portfolio_percentage", "strategy_params": {"percentage": 0.01}},
        "backtest": {"symbol": "TQQQ", "initial_cash": 100000.0},
        "grid": {"steps": [0.005, 0.01], "profit_targets": [0.003, 0.005]},
    }


def test_config_round_trips_to_canonical_dict():
    config = BacktestConfig.from_dict(valid_config())
    data = config.to_dict()
    assert data["strategy"]["strategy_id"] == "fixed_portfolio_percentage"
    assert data["backtest"]["symbol"] == "TQQQ"
    assert data["search"]["strategy"] == "grid"
    assert data["output"]["return_full_results"] is False


def test_invalid_search_strategy_is_rejected_before_use():
    data = valid_config()
    data["search"] = {"strategy": "random"}
    with pytest.raises(ConfigurationError, match="search.strategy"):
        BacktestConfig.from_dict(data)


def test_invalid_initial_cash_is_rejected():
    data = valid_config()
    data["backtest"]["initial_cash"] = 0
    with pytest.raises(ConfigurationError, match="initial_cash"):
        BacktestConfig.from_dict(data)


def test_secrets_are_not_part_of_canonical_config_fields():
    config = BacktestConfig.from_dict(valid_config())
    assert "api_key" not in config.to_dict()
    assert "secret_key" not in config.to_dict()
