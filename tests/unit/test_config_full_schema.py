"""
Task 6.1 acceptance tests.

Acceptance criteria:
1. Constructing BacktestConfig programmatically and via YAML with
   equivalent values produces equal configs.
2. Every parameter mentioned in Run_Instructions actually exists on
   run_sweep (or BacktestConfig) at doc-writing time -- covered here
   for the config side; Run_Instructions itself is checked by actually
   running it (see test_task_1_1_run_instructions.py's pattern, reused
   for the Task 6.1 rewrite).
3. A minimal config (only required fields) still runs end to end using
   documented defaults for everything else.
"""

import pandas as pd
import pytest

from optimization_controller import OptimizationController
from src.config import BacktestConfig
from src.cost_models import DynamicSlippageModel, SlippageCommissionModel, ZeroCostModel
from src.exceptions import ConfigurationError
from src.risk_manager import RiskManager
from src.size_calculators import FixedPortfolioPercentage


def _load_fixture() -> pd.DataFrame:
    df = pd.read_csv("tests/fixtures/regression_ohlcv.csv", parse_dates=["timestamp"])
    df.set_index("timestamp", inplace=True)
    return df


FULL_DICT = {
    "strategy": {"strategy_id": "fixed", "strategy_params": {"allocation_pct": 0.05}},
    "grid": {"steps": [0.01], "profit_targets": [0.005]},
    "backtest": {"symbol": "TQQQ", "initial_cash": 100_000.0},
    "costs": {"model_type": "slippage_commission", "commission_per_trade": 1.0, "slippage_bps": 5},
    "risk": {"max_concurrent_lots": 3, "max_total_exposure": 0.6},
    "search": {
        "strategy": "grid",
        "rank_by": "Capital Velocity Index",
        "direction": "maximize",
        "seed": 42,
    },
    "execution": {"on_flat_reentry": "stale_reference", "intrabar_priority": "sell_first"},
    "output": {"return_full_results": False},
    "live": {"enabled": False, "paper_trading": True},
}

FULL_YAML = """
strategy:
  strategy_id: fixed
  strategy_params:
    allocation_pct: 0.05
grid:
  steps: [0.01]
  profit_targets: [0.005]
backtest:
  symbol: TQQQ
  initial_cash: 100000.0
costs:
  model_type: slippage_commission
  commission_per_trade: 1.0
  slippage_bps: 5
risk:
  max_concurrent_lots: 3
  max_total_exposure: 0.6
search:
  strategy: grid
  rank_by: Capital Velocity Index
  direction: maximize
  seed: 42
execution:
  on_flat_reentry: stale_reference
  intrabar_priority: sell_first
output:
  return_full_results: false
live:
  enabled: false
  paper_trading: true
"""


def test_dict_and_yaml_construction_produce_equal_configs():
    from_dict_config = BacktestConfig.from_dict(FULL_DICT)
    from_yaml_config = BacktestConfig.from_yaml(FULL_YAML, is_path=False)
    assert from_dict_config == from_yaml_config


def test_full_config_validates_and_builds_real_objects():
    config = BacktestConfig.from_dict(FULL_DICT)
    config.validate()
    assert isinstance(config.costs.build(), SlippageCommissionModel)
    assert isinstance(config.risk.build(), RiskManager)
    assert config.risk.build().max_concurrent_lots == 3


def test_minimal_config_runs_end_to_end_with_documented_defaults():
    minimal = {
        "strategy": {"strategy_id": "fixed", "strategy_params": {"allocation_pct": 0.05}},
        "grid": {"steps": [0.01], "profit_targets": [0.005]},
    }
    config = BacktestConfig.from_dict(minimal)
    config.validate()

    assert isinstance(config.costs.build(), ZeroCostModel)
    assert config.risk.build().max_concurrent_lots is None
    assert config.execution.on_flat_reentry == "stale_reference"

    kwargs = config.to_run_sweep_kwargs(FixedPortfolioPercentage)
    result = OptimizationController(historical_data=_load_fixture()).run_sweep(**kwargs)
    assert len(result) == 1


def test_to_run_sweep_kwargs_actually_drives_a_real_run():
    config = BacktestConfig.from_dict(FULL_DICT)
    kwargs = config.to_run_sweep_kwargs(FixedPortfolioPercentage)
    result = OptimizationController(historical_data=_load_fixture()).run_sweep(**kwargs)
    assert len(result) == 1
    from tests.fixtures.regression_baseline import BASELINE

    assert result.iloc[0]["Final Equity"] != BASELINE["Final Equity"]


def test_yaml_from_actual_file(tmp_path):
    yaml_path = tmp_path / "config.yaml"
    yaml_path.write_text(FULL_YAML)
    config = BacktestConfig.from_yaml(str(yaml_path), is_path=True)
    assert config.strategy.strategy_id == "fixed"
    assert config.grid.steps == (0.01,)


def test_dynamic_slippage_cost_config_builds_the_real_model():
    data = dict(FULL_DICT)
    data["costs"] = {"model_type": "dynamic_slippage", "base_bps": 0.5, "vol_multiplier": 0.3}
    config = BacktestConfig.from_dict(data)
    config.validate()
    model = config.costs.build()
    assert isinstance(model, DynamicSlippageModel)
    assert model.base_bps == 0.5
    assert model.vol_multiplier == 0.3


def test_existing_costs_configs_round_trip_unchanged_with_new_fields_defaulted():
    """base_bps/vol_multiplier are additive -- every pre-existing config
    (this repo's own committed YAMLs included) must still round-trip
    identically now that the dataclass has two new fields."""
    config = BacktestConfig.from_dict(FULL_DICT)
    assert config.costs.base_bps == 0.0
    assert config.costs.vol_multiplier == 1.0
    assert BacktestConfig.from_dict(config.to_dict()) == config


def test_dynamic_slippage_actually_reaches_simulation_and_widens_spread_on_a_volatile_bar():
    """Mirrors test_task_2_2_transaction_costs.py's pattern for
    slippage_commission: prove the config-built model isn't just
    constructed correctly in isolation, but actually changes fills when
    driven through a real OptimizationController.run_sweep."""
    df = _load_fixture()
    data = dict(FULL_DICT)
    data["costs"] = {"model_type": "dynamic_slippage", "base_bps": 1.0, "vol_multiplier": 2.0}
    config = BacktestConfig.from_dict(data)
    config.validate()
    kwargs = config.to_run_sweep_kwargs(FixedPortfolioPercentage)

    flat_row = OptimizationController(historical_data=_load_fixture()).run_sweep(
        **{**kwargs, "cost_model": ZeroCostModel()}
    ).iloc[0]
    dynamic_row = OptimizationController(historical_data=df).run_sweep(**kwargs).iloc[0]

    assert dynamic_row["Final Equity"] != flat_row["Final Equity"]
    assert dynamic_row["Trade Count"] == flat_row["Trade Count"], (
        "the cost model must not change which/how many trades fire"
    )


def test_invalid_costs_model_type_rejected_by_validate():
    data = dict(FULL_DICT)
    data["costs"] = {"model_type": "bogus"}
    config = BacktestConfig.from_dict(data)
    with pytest.raises(ConfigurationError):
        config.validate()


def test_invalid_search_direction_rejected_by_validate():
    data = dict(FULL_DICT)
    data["search"] = {"direction": "sideways"}
    config = BacktestConfig.from_dict(data)
    with pytest.raises(ConfigurationError):
        config.validate()


def test_invalid_yaml_non_mapping_rejected():
    with pytest.raises(ConfigurationError):
        BacktestConfig.from_yaml("- just\n- a\n- list\n", is_path=False)


def test_search_direction_threaded_through_bayesian_construction():
    from src.search_strategies import BayesianSearch

    search = BayesianSearch([0.01], [0.005], [{"allocation_pct": 0.05}], direction="minimize")
    assert search._study.direction.name.lower() == "minimize"
