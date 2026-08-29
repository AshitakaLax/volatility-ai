"""Integration tests for the strategy registry, sweepable strategy
params, and running the new strategies through a real sweep.

The unit tests prove the mathematics. These prove the strategies are
actually reachable from a config file and survive the full
OptimizationController path -- which is where a sizing strategy that
works in isolation tends to fall over.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from optimization_controller import OptimizationController
from src.bayesian_sizing_calculators import BayesianDualScaleSizing
from src.config import BacktestConfig, expand_strategy_params
from src.exceptions import ConfigurationError
from src.size_calculators import (
    BellCurveProbabilitySizing,
    FixedPortfolioPercentage,
    RsiMomentumSizing,
)
from src.strategy_registry import STRATEGIES, resolve_strategy


@pytest.fixture
def price_data():
    """A volatile random walk -- flat data would let the grid trigger
    almost never and make a passing sweep meaningless."""
    rng = np.random.default_rng(11)
    n = 1200
    price = 70.0
    rows = []
    ts = pd.Timestamp("2026-01-02 14:30", tz="UTC")
    for _ in range(n):
        price *= 1.0 + rng.normal(0, 0.0015)
        rows.append(
            {
                "timestamp": ts,
                "open": price,
                "high": price * 1.0004,
                "low": price * 0.9996,
                "close": price,
                "volume": 10_000,
            }
        )
        ts += pd.Timedelta(minutes=1)
    return pd.DataFrame(rows).set_index("timestamp")


# --- registry ---


def test_every_registered_id_resolves_to_its_class():
    assert resolve_strategy("fixed") is FixedPortfolioPercentage
    assert resolve_strategy("bell_curve") is BellCurveProbabilitySizing
    assert resolve_strategy("rsi") is RsiMomentumSizing
    assert resolve_strategy("bayesian_dual_scale") is BayesianDualScaleSizing


def test_an_unknown_id_fails_listing_the_valid_ones():
    """A bare KeyError names only what is missing, not what works."""
    with pytest.raises(ConfigurationError, match="bayesian_dual_scale"):
        resolve_strategy("no_such_strategy")


def test_the_cli_registry_is_the_same_table():
    """Two hand-maintained copies of this mapping is the drift the
    registry exists to prevent."""
    import cli

    cli.STRATEGY_REGISTRY.clear()
    assert cli._load_strategy_registry() == STRATEGIES


# --- sweepable strategy params ---


def test_scalar_params_still_produce_exactly_one_combination():
    """Existing configs must be bit-identical to before."""
    assert expand_strategy_params({"allocation_pct": 0.05}) == [{"allocation_pct": 0.05}]


def test_list_params_expand_into_a_cartesian_grid():
    combos = expand_strategy_params({"mu": [0.1, 0.2], "sigma": [0.05, 0.1], "fixed": 3})
    assert len(combos) == 4
    assert all(c["fixed"] == 3 for c in combos)
    assert {(c["mu"], c["sigma"]) for c in combos} == {
        (0.1, 0.05),
        (0.1, 0.1),
        (0.2, 0.05),
        (0.2, 0.1),
    }


def test_an_empty_list_is_rejected_rather_than_sweeping_nothing():
    with pytest.raises(ConfigurationError, match="empty list"):
        expand_strategy_params({"mu": []})


def test_a_config_can_now_drive_a_multi_combination_strategy_sweep():
    """The gap this closes: strategy tunables were reachable from the
    Python API but not from a config file, which is where sweeps are
    actually written."""
    config = BacktestConfig.from_dict(
        {
            "strategy": {
                "strategy_id": "bell_curve",
                "strategy_params": {
                    "max_trade_pct": 0.05,
                    "lookback_days": 5.0,
                    "bars_per_day": 100,
                    "mu": [0.05, 0.10],
                    "sigma": [0.05, 0.10],
                },
            },
            "grid": {"steps": [0.01], "profit_targets": [0.005]},
        }
    )
    kwargs = config.to_run_sweep_kwargs(BellCurveProbabilitySizing)
    assert len(kwargs["strategy_params_grid"]) == 4


# --- the strategies through a real sweep ---


@pytest.mark.parametrize(
    "strategy_class,params",
    [
        (FixedPortfolioPercentage, {"allocation_pct": 0.05}),
        (
            BellCurveProbabilitySizing,
            {"max_trade_pct": 0.05, "lookback_days": 2.0, "bars_per_day": 100, "mu": 0.02},
        ),
        (RsiMomentumSizing, {"max_trade_pct": 0.05, "period": 14}),
        (
            BayesianDualScaleSizing,
            {
                "max_trade_pct": 0.05,
                "target_return": 0.005,
                "horizon_days": 1.0,
                "bars_per_day": 100,
                "fast_half_life_days": 1.0,
                "slow_half_life_days": 5.0,
            },
        ),
    ],
)
def test_each_strategy_completes_a_real_sweep(price_data, strategy_class, params):
    controller = OptimizationController(historical_data=price_data)
    results = controller.run_sweep(
        grid_steps=[0.003],
        profit_targets=[0.005],
        strategy_class=strategy_class,
        strategy_params_grid=[params],
    )
    assert len(results) == 1
    assert "error" not in results.columns, results.to_dict("records")
    assert results["Strategy"].iloc[0] == strategy_class.__name__


# --- the target_return / profit_target cross-check ---


def test_a_target_return_mismatch_fails_that_combination_with_a_clear_error(price_data):
    """BayesianDualScaleSizing's target_return (0.02) does not match
    the swept profit_target (0.005) -- previously silent (nothing
    anywhere checked this), now caught before any simulation runs.

    A second, matching params entry rides along so the sweep has at
    least one successful row to rank -- run_sweep legitimately raises
    when EVERY combination fails (nothing to rank_by), which is a
    separate, correct behavior this test is not exercising.
    """
    controller = OptimizationController(historical_data=price_data)
    base = {
        "max_trade_pct": 0.05,
        "horizon_days": 1.0,
        "bars_per_day": 100,
        "fast_half_life_days": 1.0,
        "slow_half_life_days": 5.0,
    }
    results = controller.run_sweep(
        grid_steps=[0.003],
        profit_targets=[0.005],
        strategy_class=BayesianDualScaleSizing,
        strategy_params_grid=[
            {**base, "target_return": 0.02},  # mismatched -- must fail
            {**base, "target_return": 0.005},  # matches -- must succeed
        ],
    )
    assert len(results) == 2
    assert "error" in results.columns
    failed = results[results["target_return"] == 0.02]
    succeeded = results[results["target_return"] == 0.005]
    assert len(failed) == 1 and len(succeeded) == 1
    assert "target_return" in failed["error"].iloc[0]
    assert "0.02" in failed["error"].iloc[0]
    assert "0.005" in failed["error"].iloc[0]
    assert pd.isna(succeeded["error"].iloc[0])


def test_a_matching_target_return_runs_cleanly(price_data):
    """Direct contrast: identical setup, target_return now matches --
    no error, matching test_each_strategy_completes_a_real_sweep."""
    controller = OptimizationController(historical_data=price_data)
    results = controller.run_sweep(
        grid_steps=[0.003],
        profit_targets=[0.005],
        strategy_class=BayesianDualScaleSizing,
        strategy_params_grid=[
            {
                "max_trade_pct": 0.05,
                "target_return": 0.005,
                "horizon_days": 1.0,
                "bars_per_day": 100,
                "fast_half_life_days": 1.0,
                "slow_half_life_days": 5.0,
            }
        ],
    )
    assert "error" not in results.columns, results.to_dict("records")


def test_allow_target_return_mismatch_is_the_deliberate_escape_hatch(price_data):
    """The module docstring calls a deliberate mismatch legitimate --
    this is how a config actually asserts that, rather than a mismatch
    always failing regardless of intent."""
    controller = OptimizationController(historical_data=price_data)
    results = controller.run_sweep(
        grid_steps=[0.003],
        profit_targets=[0.005],
        strategy_class=BayesianDualScaleSizing,
        strategy_params_grid=[
            {
                "max_trade_pct": 0.05,
                "target_return": 0.02,
                "horizon_days": 1.0,
                "bars_per_day": 100,
                "fast_half_life_days": 1.0,
                "slow_half_life_days": 5.0,
                "allow_target_return_mismatch": True,
            }
        ],
    )
    assert "error" not in results.columns, results.to_dict("records")


def test_the_cross_check_does_not_fire_for_strategies_without_target_return(price_data):
    """getattr-based, not an isinstance check -- must not misfire for
    every OTHER strategy, which has no target_return attribute at all."""
    controller = OptimizationController(historical_data=price_data)
    results = controller.run_sweep(
        grid_steps=[0.003],
        profit_targets=[0.005],
        strategy_class=FixedPortfolioPercentage,
        strategy_params_grid=[{"allocation_pct": 0.05}],
    )
    assert "error" not in results.columns, results.to_dict("records")


def test_results_from_different_strategies_are_distinguishable_when_combined(price_data):
    """The reason Strategy was added to result rows: two sweeps that
    happened to share grid parameters were previously identical rows."""
    controller = OptimizationController(historical_data=price_data)
    common = {"grid_steps": [0.003], "profit_targets": [0.005]}
    fixed = controller.run_sweep(
        strategy_class=FixedPortfolioPercentage,
        strategy_params_grid=[{"allocation_pct": 0.05}],
        **common,
    )
    rsi = controller.run_sweep(
        strategy_class=RsiMomentumSizing,
        strategy_params_grid=[{"max_trade_pct": 0.05}],
        **common,
    )
    combined = pd.concat([fixed, rsi], ignore_index=True)
    assert set(combined["Strategy"]) == {"FixedPortfolioPercentage", "RsiMomentumSizing"}


def test_a_stateful_strategy_does_not_attach_its_state_to_results(price_data):
    """Task 4.6's params capture merges the strategy's public
    attributes. An unbounded rolling history there would be both
    misleading and a real memory cost across a sweep."""
    controller = OptimizationController(historical_data=price_data)
    _, full = controller.run_sweep(
        grid_steps=[0.003],
        profit_targets=[0.005],
        strategy_class=BayesianDualScaleSizing,
        strategy_params_grid=[
            {
                "max_trade_pct": 0.05,
                "target_return": 0.005,
                "horizon_days": 1.0,
                "bars_per_day": 100,
            }
        ],
        return_full_results=True,
    )
    for value in full[0].params.values():
        assert not isinstance(value, (list, dict, set)), (
            f"internal state leaked into SimulationResult.params: {value!r}"
        )


def test_sweep_combinations_are_isolated_from_each_other(price_data):
    """A stateful strategy reused across combinations would let one
    combination's posterior contaminate the next. run_sweep constructs
    a fresh instance per combination; this pins that."""
    controller = OptimizationController(historical_data=price_data)
    params = {
        "max_trade_pct": 0.05,
        "target_return": 0.005,
        "horizon_days": 1.0,
        "bars_per_day": 100,
    }
    first = controller.run_sweep(
        grid_steps=[0.003],
        profit_targets=[0.005],
        strategy_class=BayesianDualScaleSizing,
        strategy_params_grid=[params],
    )
    twice = controller.run_sweep(
        grid_steps=[0.003, 0.004],
        profit_targets=[0.005],
        strategy_class=BayesianDualScaleSizing,
        strategy_params_grid=[params],
    )
    same = twice[twice["Grid Step"] == 0.003].iloc[0]
    assert same["Final Equity"] == pytest.approx(first["Final Equity"].iloc[0])
