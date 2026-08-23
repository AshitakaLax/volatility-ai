import pytest

from src.config import BacktestConfig, GridConfig, StrategyConfig
from src.exceptions import ConfigurationError


def _valid_dict():
    return {
        "strategy": {"strategy_id": "fixed", "strategy_params": {"percentage": 0.1}},
        "backtest": {"symbol": "TQQQ", "initial_cash": 100_000.0},
        "grid": {"steps": [0.01], "profit_targets": [0.02]},
        "live": {"enabled": True, "paper_trading": True},
    }


def test_from_dict_matches_live_execution_tests_exact_usage():
    config = BacktestConfig.from_dict(_valid_dict())
    assert isinstance(config.strategy, StrategyConfig)
    assert isinstance(config.grid, GridConfig)
    assert config.strategy.strategy_id == "fixed"
    assert config.strategy.strategy_params == {"percentage": 0.1}
    assert config.backtest.symbol == "TQQQ"
    assert config.backtest.initial_cash == 100_000.0
    assert config.grid.steps == (0.01,)  # tuple, not list
    assert config.grid.profit_targets == (0.02,)
    assert config.live.enabled is True
    assert config.live.paper_trading is True


def test_from_dict_defaults_risk_section_when_omitted():
    config = BacktestConfig.from_dict(_valid_dict())  # no "risk" key at all
    assert config.risk.max_concurrent_lots is None
    assert config.risk.max_total_exposure is None


def test_from_dict_accepts_explicit_risk_section():
    data = _valid_dict()
    data["risk"] = {"max_concurrent_lots": 3, "max_total_exposure": 0.6}
    config = BacktestConfig.from_dict(data)
    assert config.risk.max_concurrent_lots == 3
    assert config.risk.max_total_exposure == 0.6


def test_from_dict_missing_strategy_id_raises_clear_error():
    data = _valid_dict()
    del data["strategy"]["strategy_id"]
    with pytest.raises(ConfigurationError, match="strategy_id"):
        BacktestConfig.from_dict(data)


def test_from_dict_missing_grid_raises_clear_error():
    data = _valid_dict()
    del data["grid"]
    with pytest.raises(ConfigurationError, match="grid"):
        BacktestConfig.from_dict(data)


def test_validate_accepts_the_valid_config():
    config = BacktestConfig.from_dict(_valid_dict())
    config.validate()  # does not raise


def test_validate_rejects_non_positive_initial_cash():
    data = _valid_dict()
    data["backtest"]["initial_cash"] = 0.0
    config = BacktestConfig.from_dict(data)
    with pytest.raises(ConfigurationError):
        config.validate()


def test_validate_rejects_empty_grid_steps():
    data = _valid_dict()
    data["grid"]["steps"] = []
    config = BacktestConfig.from_dict(data)
    with pytest.raises(ConfigurationError):
        config.validate()


def test_validate_rejects_grid_step_at_or_above_1():
    data = _valid_dict()
    data["grid"]["steps"] = [1.0]
    config = BacktestConfig.from_dict(data)
    with pytest.raises(ConfigurationError):
        config.validate()


def test_validate_rejects_out_of_range_risk_values():
    data = _valid_dict()
    data["risk"] = {"max_concurrent_lots": -1}
    config = BacktestConfig.from_dict(data)
    with pytest.raises(ConfigurationError):
        config.validate()

    data = _valid_dict()
    data["risk"] = {"max_total_exposure": 1.5}
    config = BacktestConfig.from_dict(data)
    with pytest.raises(ConfigurationError):
        config.validate()


def test_enforce_no_loss_defaults_to_true_and_round_trips():
    """The guard stays ON unless a config explicitly turns it off, so
    every pre-existing config keeps today's behavior."""
    from src.config import BacktestConfig

    base = {
        "strategy": {"strategy_id": "fixed", "strategy_params": {"allocation_pct": 0.05}},
        "grid": {"steps": [0.01], "profit_targets": [0.005]},
    }
    assert BacktestConfig.from_dict(base).execution.enforce_no_loss is True

    off = dict(base, execution={"enforce_no_loss": False})
    cfg = BacktestConfig.from_dict(off)
    assert cfg.execution.enforce_no_loss is False
    assert cfg.to_run_sweep_kwargs(strategy_class=object)["enforce_no_loss"] is False
