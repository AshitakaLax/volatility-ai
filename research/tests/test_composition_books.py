"""Phase 4 of docs/research/buy-sell-composition.md: the strategies whose
buying and selling were one design, split into a buy policy and a sell
policy -- each pair pinned identical to the original, blotter for blotter,
on the same cases Phase 0 pinned. Then the split halves pair with others."""

from __future__ import annotations

import pytest

from engine.core.exceptions import ConfigurationError
from research.composition import entries
from research.composition.composed_strategy import ComposedStrategy
from research.composition.entries import UltimateEntry
from research.optimization.optimization_controller import OptimizationController
from research.strategies.param_schema import STRATEGY_DEFAULTS
from research.strategies.strategy_registry import STRATEGIES
from research.strategies.ultimate_sizing import CALM, TURBULENT
from tests.fixtures import composition_baseline as fixture

HF = dict(fixture.HF)
SIGNAL = {"fill_model": "intrabar", "intrabar_fill": "causal", "allow_signal_exit": True}


@pytest.fixture(scope="module")
def ohlcv():
    return fixture.load_ohlcv()


def _run(df, cls, params, target, **sweep):
    summary, full = OptimizationController(historical_data=df).run_sweep(
        grid_steps=[0.002 if target < 1 else 0.001],
        profit_targets=[target],
        strategy_class=cls,
        strategy_params_grid=[params],
        return_full_results=True,
        **sweep,
    )
    assert full[0] is not None, summary.to_dict("records")
    return summary.iloc[0], full[0].trade_blotter


def _identical(df, original, original_params, buy, sell, target, **sweep):
    row_a, blot_a = _run(df, original, original_params, target, **sweep)
    row_b, blot_b = _run(df, ComposedStrategy, {"buy": buy, "sell": sell}, target, **sweep)
    assert fixture.blotter_digest(blot_a) == fixture.blotter_digest(blot_b)
    for column in ("Final Equity", "Trade Count", "Closed Trade Count", "Signal Exit Count"):
        assert row_a[column] == row_b[column], column
    return blot_a


def _case(name):
    return next(case for case in fixture.CASES if case.name == name)


def test_the_harvest_sleeves_target_decay_is_age_decay(ohlcv):
    case = _case("harvest-decay")
    params = case.params(ohlcv)
    buy = {k: v for k, v in params.items() if not k.startswith("target_decay")}
    blotter = _identical(
        ohlcv,
        case.strategy(),
        params,
        {"id": "harvest_sleeve", "params": buy},
        {"id": "age_decay", "params": {"after_bars": 200, "span_bars": 400}},
        case.target,
        **case.sweep,
    )
    assert len(blotter) > 100


def test_the_calm_sleeves_regime_exit_is_regime_exit(ohlcv):
    case = _case("harvest-calm-sleeve-full-exit")
    params = case.params(ohlcv)
    _identical(
        ohlcv,
        case.strategy(),
        params,
        {"id": "harvest_sleeve", "params": params},
        {"id": "regime_exit", "params": {"regime_by_date": params["regime_by_date"]}},
        case.target,
        **case.sweep,
    )


def _ultimate_split(params):
    sell_keys = {"regime_by_date", "reversal_target", "liquidate_minute"}
    buy = {k: v for k, v in params.items() if k not in {"reversal_target"}}
    sell = {k: v for k, v in params.items() if k in sell_keys}
    return {"id": "ultimate", "params": buy}, {"id": "ultimate_exit", "params": sell}


def test_ultimate_is_its_buying_and_its_regime_exit(ohlcv):
    case = _case("ultimate")
    params = case.params(ohlcv)
    buy, sell = _ultimate_split(params)
    blotter = _identical(ohlcv, case.strategy(), params, buy, sell, case.target, **case.sweep)
    sells = blotter[blotter["side"] == "sell"]
    assert sells["sell_reason"].str.contains("signal_exit").any()
    assert sells["sell_reason"].str.contains("profit_target").any()


def test_ultimate_with_its_reversal_lots_sold_on_the_calm_flip(ohlcv):
    case = _case("ultimate")
    params = {**case.params(ohlcv), "liquidate_reversal_on_calm": True, "liquidate_minute": 15}
    buy, sell = _ultimate_split(params)
    buy["params"].pop("liquidate_reversal_on_calm")
    buy["params"].pop("liquidate_minute")
    sell["params"]["liquidate_reversal_on_calm"] = True
    _identical(ohlcv, case.strategy(), params, buy, sell, case.target, **case.sweep)


@pytest.mark.parametrize(
    ("name", "sell"),
    [("ultimate-rsp", "rsp_rebalance"), ("catalog-exposure-sma", "catalog_rebalance")],
)
def test_an_exposure_book_is_its_buying_and_its_rebalance(ohlcv, name, sell):
    case = _case(name)
    params = case.params(ohlcv)
    entry_id = "ultimate_rsp" if name == "ultimate-rsp" else "catalog_exposure"
    blotter = _identical(
        ohlcv,
        case.strategy(),
        params,
        {"id": entry_id, "params": params},
        {"id": sell, "params": params},
        case.target,
        **case.sweep,
    )
    assert (blotter["side"] == "sell").any()


def test_ursp_constructs_both_halves():
    params = dict(STRATEGY_DEFAULTS["ultimate_ursp"])
    ComposedStrategy(
        buy={"id": "ultimate_ursp", "params": params},
        sell={"id": "ursp_rebalance", "params": params},
    )


def test_bayesian_buying_pairs_with_a_target_keeping_sell_only():
    params = dict(STRATEGY_DEFAULTS["bayesian_dual_scale"])
    ComposedStrategy(
        buy={"id": "bayesian_dual_scale", "params": params},
        sell={"id": "trailing", "params": {"trail_pct": 0.01}},
    )
    with pytest.raises(ConfigurationError, match="target_return"):
        ComposedStrategy(
            buy={"id": "bayesian_dual_scale", "params": params}, sell={"id": "scale_out"}
        )


def test_bayesian_with_a_fixed_target_is_itself(ohlcv):
    params = {**STRATEGY_DEFAULTS["bayesian_dual_scale"], "bars_per_day": fixture.BARS_PER_DAY}
    target = params["target_return"]
    _identical(
        ohlcv.iloc[:3000],
        STRATEGIES["bayesian_dual_scale"],
        params,
        {"id": "bayesian_dual_scale", "params": params},
        {"id": "fixed_target"},
        target,
    )


def test_every_buy_policy_constructs_from_its_defaults():
    for entry_id in entries.entry_ids():
        ComposedStrategy(
            buy={"id": entry_id, "params": entries.entry_defaults(entry_id)},
            sell={"id": "fixed_target"},
        )


@pytest.mark.parametrize(
    ("entry_id", "param", "value"),
    [
        ("ultimate", "liquidate_minute", 10),
        ("ultimate", "reversal_target", 0.03),
        ("harvest_sleeve", "target_decay_after_bars", 100),
        ("harvest_sleeve", "liquidate_fraction", 0.5),
        ("ml_regime_tqqq", "trail_pct", 0.01),
    ],
)
def test_a_selling_parameter_on_a_split_buyer_is_refused(entry_id, param, value):
    params = {**entries.entry_defaults(entry_id), param: value}
    with pytest.raises(ConfigurationError, match="configure selling"):
        ComposedStrategy(buy={"id": entry_id, "params": params}, sell={"id": "fixed_target"})


def test_a_selling_parameter_left_at_its_default_is_accepted():
    params = {**entries.entry_defaults("harvest_sleeve"), **HF, "liquidate_fraction": 1.0}
    ComposedStrategy(buy={"id": "harvest_sleeve", "params": params}, sell={"id": "fixed_target"})


def test_ultimate_tags_what_it_buys_in_turbulence():
    entry = UltimateEntry(**HF)
    entry.mode = TURBULENT
    assert entry.next_lot_tag() == "reversal"
    entry.mode = CALM
    assert entry.next_lot_tag() is None


def test_ultimates_exit_pairs_with_another_buyer(ohlcv):
    """The point of splitting it: the regime exit on the champion's lots."""
    params = _case("ultimate").params(ohlcv)
    row, _ = _run(
        ohlcv,
        ComposedStrategy,
        {
            "buy": {"id": "hf_local_reference", "params": HF},
            "sell": {"id": "ultimate_exit", "params": {"regime_by_date": params["regime_by_date"]}},
        },
        0.01,
        **SIGNAL,
    )
    assert row["Signal Exit Count"] > 0


def test_an_exposure_rebalance_caps_a_grid_buyer(ohlcv):
    row, _ = _run(
        ohlcv,
        ComposedStrategy,
        {
            "buy": {"id": "hf_local_reference", "params": HF},
            "sell": {"id": "rsp_rebalance", "params": dict(fixture.EXPOSURE)},
        },
        0.01,
        **SIGNAL,
    )
    assert row["Signal Exit Count"] > 0


def test_the_split_sells_are_loss_capable_and_regular_session():
    from research.composition.exits import EXITS

    for exit_id in ("ultimate_exit", "rsp_rebalance", "ursp_rebalance", "catalog_rebalance"):
        assert EXITS[exit_id].can_realize_loss
    assert ComposedStrategy.regular_session_only_for(
        {"buy": {"id": "hf_local_reference"}, "sell": {"id": "ultimate_exit"}}
    )
    assert ComposedStrategy.regular_session_only_for(
        {"buy": {"id": "ultimate"}, "sell": {"id": "fixed_target"}}
    )
