"""research/composition/ (Phase 2 of docs/research/buy-sell-composition.md):
a composed strategy is its parts exactly -- identical blotters, not "close"
-- and the plumbing around it (nested sweeps, the loss gate, live checks,
session bars, parallel runs) treats it like any other strategy."""

from __future__ import annotations

import pickle

import pytest

from engine.core.config import BacktestConfig, expand_strategy_params
from engine.core.exceptions import ConfigurationError
from research.composition import entries, exits
from research.composition.composed_strategy import ComposedStrategy
from research.optimization import intraday_validation
from research.optimization.optimization_controller import OptimizationController
from research.strategies.live_algorithm import build_strategy
from research.strategies.param_schema import STRATEGY_DEFAULTS
from research.strategies.strategy_registry import (
    STRATEGIES,
    may_realize_loss,
    regular_session_only,
    session_bars,
)
from tests.fixtures import composition_baseline as fixture

HF = dict(fixture.HF)
FILLS = {
    "close": {"fill_model": "close"},
    "intrabar-causal": {"fill_model": "intrabar", "intrabar_fill": "causal"},
    "intrabar-level": {"fill_model": "intrabar"},
}
OUTCOMES = (
    "Final Equity",
    "Realized PnL",
    "Trade Count",
    "Closed Trade Count",
    "Open Trade Count",
    "Max Drawdown %",
    "Signal Exit Count",
    "Sharpe",
)


@pytest.fixture(scope="module")
def ohlcv():
    return fixture.load_ohlcv()


def _run(df, cls, params, target=0.01, **sweep):
    summary, full = OptimizationController(historical_data=df).run_sweep(
        grid_steps=[0.002],
        profit_targets=[target],
        strategy_class=cls,
        strategy_params_grid=[params],
        return_full_results=True,
        **sweep,
    )
    assert full[0] is not None, summary.to_dict("records")
    return summary.iloc[0], full[0].trade_blotter


def _same(df, original, original_params, buy, sell, **sweep):
    row_a, blot_a = _run(df, original, original_params, **sweep)
    row_b, blot_b = _run(df, ComposedStrategy, {"buy": buy, "sell": sell}, **sweep)
    assert fixture.blotter_digest(blot_a) == fixture.blotter_digest(blot_b)
    assert blot_a.equals(blot_b)
    for column in OUTCOMES:
        assert row_a[column] == row_b[column], column
    return blot_a


# --- pinned identities -------------------------------------------------------


@pytest.mark.parametrize("fill", FILLS, ids=list(FILLS))
def test_the_champion_with_a_fixed_target_is_the_champion(ohlcv, fill):
    blotter = _same(
        ohlcv,
        STRATEGIES["hf_local_reference"],
        HF,
        {"id": "hf_local_reference", "params": HF},
        {"id": "fixed_target"},
        **FILLS[fill],
    )
    assert (blotter["side"] == "sell").sum() > 100, "the identity must cover real trading"


@pytest.mark.parametrize("fill", ["close", "intrabar-causal"])
def test_the_champion_with_a_trailing_sell_is_the_champion_with_trail_pct(ohlcv, fill):
    _same(
        ohlcv,
        STRATEGIES["hf_local_reference"],
        {**HF, "trail_pct": 0.003, "trail_min_profit_target": 0.002},
        {"id": "hf_local_reference", "params": HF},
        {"id": "trailing", "params": {"trail_pct": 0.003, "min_profit_target": 0.002}},
        **FILLS[fill],
    )


def test_a_gated_buyer_with_a_fixed_target_is_itself(ohlcv):
    params = {**HF, "momentum_gate": "early_negative"}
    _same(
        ohlcv,
        STRATEGIES["hf_entry_gated"],
        params,
        {"id": "hf_entry_gated", "params": params},
        {"id": "fixed_target"},
        **FILLS["intrabar-causal"],
    )


@pytest.mark.parametrize("strategy_id", ["rk62_ma_cross", "rk147_zscore", "rk44_supertrend"])
def test_a_library_buyer_with_a_fixed_target_is_itself(ohlcv, strategy_id):
    params = {**STRATEGY_DEFAULTS[strategy_id], **HF}
    _same(
        ohlcv,
        STRATEGIES[strategy_id],
        params,
        {"id": strategy_id, "params": params},
        {"id": "fixed_target"},
        **FILLS["intrabar-causal"],
    )


def test_the_simple_buyers_with_a_fixed_target_are_themselves(ohlcv):
    for strategy_id in ("fixed", "rsi", "bell_curve"):
        params = dict(STRATEGY_DEFAULTS[strategy_id])
        if "bars_per_day" in params:
            params["bars_per_day"] = fixture.BARS_PER_DAY
        _same(
            ohlcv,
            STRATEGIES[strategy_id],
            params,
            {"id": strategy_id, "params": params},
            {"id": "fixed_target"},
        )


def test_the_intraday_replay_sees_the_same_strategy(ohlcv):
    plain = intraday_validation.simulate_single_intraday(
        ohlcv, 0.002, 0.01, STRATEGIES["hf_local_reference"], HF
    )
    composed = intraday_validation.simulate_single_intraday(
        ohlcv,
        0.002,
        0.01,
        ComposedStrategy,
        {"buy": {"id": "hf_local_reference", "params": HF}, "sell": {"id": "fixed_target"}},
    )
    assert plain == composed


# --- what a composition refuses ----------------------------------------------


def test_selling_parameters_are_refused_on_the_buy_side():
    with pytest.raises(ConfigurationError, match="configure selling"):
        ComposedStrategy(
            buy={"id": "hf_local_reference", "params": {**HF, "trail_pct": 0.01}},
            sell={"id": "fixed_target"},
        )


@pytest.mark.parametrize(
    ("buy", "match"),
    [
        ({"id": "composed", "params": {}}, "cannot be a buy policy"),
        ({"id": "nope", "params": {}}, "Unknown buy policy"),
        ({"params": {}}, "must be"),
        ({"id": "fixed", "extra": 1}, "unknown keys"),
    ],
)
def test_a_bad_buy_policy_is_refused_with_its_reason(buy, match):
    with pytest.raises(ConfigurationError, match=match):
        ComposedStrategy(buy=buy, sell={"id": "fixed_target"})


def test_a_bad_sell_policy_is_refused_with_its_reason():
    with pytest.raises(ConfigurationError, match="Unknown sell policy"):
        ComposedStrategy(buy={"id": "fixed", "params": {"allocation_pct": 0.05}}, sell={"id": "x"})
    with pytest.raises(ConfigurationError, match="refused these parameters"):
        ComposedStrategy(
            buy={"id": "fixed", "params": {"allocation_pct": 0.05}},
            sell={"id": "fixed_target", "params": {"bogus": 1}},
        )


# --- the plumbing --------------------------------------------------------------


def test_a_buy_by_sell_sweep_expands_to_every_cell(ohlcv):
    grid = expand_strategy_params(
        {
            "buy": [
                {"id": "hf_local_reference", "params": HF},
                {"id": "hf_entry_gated", "params": {**HF, "momentum_gate": "early_negative"}},
            ],
            "sell": [
                {"id": "fixed_target"},
                {"id": "trailing", "params": {"trail_pct": [0.003, 0.006]}},
            ],
        }
    )
    assert len(grid) == 6
    summary = OptimizationController(historical_data=ohlcv.iloc[:2000]).run_sweep(
        grid_steps=[0.002],
        profit_targets=[0.01],
        strategy_class=ComposedStrategy,
        strategy_params_grid=grid,
    )
    assert len(summary) == 6 and "error" not in summary.columns


def test_a_composed_config_runs_from_yaml_shaped_data():
    config = BacktestConfig.from_dict(
        {
            "strategy": {
                "strategy_id": "composed",
                "strategy_params": {
                    "buy": {"id": "fixed", "params": {"allocation_pct": 0.05}},
                    "sell": {"id": "trailing", "params": {"trail_pct": [0.01, 0.02]}},
                },
            },
            "grid": {"steps": [0.01], "profit_targets": [0.02]},
        }
    )
    kwargs = config.to_run_sweep_kwargs(ComposedStrategy)
    assert [p["sell"]["params"]["trail_pct"] for p in kwargs["strategy_params_grid"]] == [
        0.01,
        0.02,
    ]


def test_parallel_runs_pickle_a_composition(ohlcv):
    strategy = ComposedStrategy(
        buy={"id": "hf_local_reference", "params": HF},
        sell={"id": "trailing", "params": {"trail_pct": 0.01}},
    )
    pickle.loads(pickle.dumps(strategy))
    grid = [
        {"buy": {"id": "hf_local_reference", "params": HF}, "sell": {"id": "fixed_target"}},
        {
            "buy": {"id": "fixed", "params": {"allocation_pct": 0.05}},
            "sell": {"id": "fixed_target"},
        },
    ]
    controller = OptimizationController(historical_data=ohlcv.iloc[:1500])
    kwargs = {"grid_steps": [0.002], "profit_targets": [0.01], "strategy_class": ComposedStrategy}
    one = controller.run_sweep(strategy_params_grid=grid, **kwargs)
    two = controller.run_sweep(strategy_params_grid=grid, n_jobs=2, **kwargs)
    key = ["Final Equity", "Trade Count"]
    assert sorted(map(tuple, one[key].to_numpy())) == sorted(map(tuple, two[key].to_numpy()))


def test_no_phase_2_sell_policy_may_realize_a_loss():
    for exit_id, cls in exits.EXITS.items():
        if exit_id in ("fixed_target", "trailing"):
            assert cls.can_realize_loss is False
    assert not may_realize_loss("composed", STRATEGY_DEFAULTS["composed"])
    assert may_realize_loss("ultimate")


def test_a_composition_passes_the_live_checks():
    config = BacktestConfig.from_dict(
        {
            "strategy": {
                "strategy_id": "composed",
                "strategy_params": STRATEGY_DEFAULTS["composed"],
            },
            "grid": {"steps": [0.001], "profit_targets": [0.01]},
            "backtest": {"symbol": "TQQQ"},
            "live": {"enabled": True, "paper_trading": True, "step": 0.001, "profit_target": 0.01},
        }
    )
    strategy = build_strategy(config, STRATEGIES)
    assert isinstance(strategy, ComposedStrategy)
    assert strategy.live_history_sessions() > 0, "the champion's windows still need history"


def test_session_bars_ask_the_composition(ohlcv):
    params = STRATEGY_DEFAULTS["composed"]
    assert regular_session_only(ComposedStrategy, params) is False
    assert session_bars(ComposedStrategy, ohlcv, params) is ohlcv


def test_every_listed_buy_policy_constructs_from_its_defaults():
    for entry_id in entries.entry_ids():
        ComposedStrategy(
            buy={"id": entry_id, "params": entries.entry_defaults(entry_id)},
            sell={"id": "fixed_target"},
        )


def test_the_composed_defaults_are_the_champion():
    defaults = STRATEGY_DEFAULTS["composed"]
    assert defaults["buy"] == {
        "id": "hf_local_reference",
        "params": STRATEGY_DEFAULTS["hf_local_reference"],
    }
    assert defaults["sell"]["id"] == "fixed_target"
