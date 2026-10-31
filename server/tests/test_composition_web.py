"""Phase 7 of docs/research/buy-sell-composition.md, the server half: the web
can describe, validate, keep, trial and switch to a composed algorithm
through the same approval pipeline a single strategy uses -- and a sell
policy that may sell below cost is marked everywhere and gated where it
matters (a deployment's own allow_signal_exit)."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from engine.core.config import BacktestConfig
from engine.core.exceptions import ConfigurationError
from research.strategies.live_algorithm import AlgorithmControl
from research.strategies.strategy_registry import STRATEGIES
from server.app import app
from server.tests.test_algorithms import client  # noqa: F401  (a fixture)
from server.tests.test_history_api import cell, save_run
from server.tests.test_live_control_api import deployments  # noqa: F401  (a fixture)

HF = {"per_lot_pct": 0.0002, "lookback_days": 0.02, "bars_per_day": 387}


@pytest.fixture
def api():
    return TestClient(app)


# --- the catalogue -------------------------------------------------------------


def test_the_funds_catalogue_describes_every_buy_and_sell_policy(api):
    composition = api.get("/api/backtest/funds").json()["composition"]
    assert "hf_local_reference" in composition["buys"]
    assert "ultimate" in composition["buys"]
    sells = composition["sells"]
    assert {"fixed_target", "trailing", "scale_out", "regime_exit"} <= set(sells)
    assert sells["regime_exit"]["loss"] is True and "loss" not in sells["scale_out"]
    assert sells["scale_out"]["partial"] is True
    buy_params = {p["name"] for p in composition["buys"]["hf_local_reference"]["params"]}
    assert "per_lot_pct" in buy_params and "trail_pct" not in buy_params, (
        "selling params are the sell side's"
    )


# --- validating a run ----------------------------------------------------------


def _request(buy, sell):
    return {
        "tickers": ["TQQQ"],
        "grid_steps": [0.001],
        "targets": [0.01],
        "model": "composed",
        "fill": "intrabar",
        "params": {"buy": buy, "sell": sell},
    }


def test_a_matrix_request_validates_with_unnamed_params_taken_from_the_defaults(api):
    body = api.post(
        "/api/backtest/validate",
        json=_request(
            [{"id": "hf_local_reference"}, {"id": "rk62_ma_cross"}],
            [{"id": "fixed_target"}, {"id": "regime_exit"}],
        ),
    ).json()
    assert body["errors"] == []
    buys = body["resolved"]["buy"]
    assert buys[1]["params"]["signal"] == "ma_cross"


def test_a_component_given_params_is_used_as_given(api):
    body = api.post(
        "/api/backtest/validate",
        json=_request(
            {"id": "hf_local_reference", "params": {"per_lot_pct": 0.001}}, {"id": "fixed_target"}
        ),
    ).json()
    assert body["errors"], "the champion's required params were not given: no silent merge"


def test_a_selling_param_on_the_buy_side_is_refused_by_name(api):
    body = api.post(
        "/api/backtest/validate",
        json=_request(
            {"id": "hf_local_reference", "params": {**HF, "trail_pct": 0.01}},
            {"id": "fixed_target"},
        ),
    ).json()
    assert any("configure selling" in error["msg"] for error in body["errors"])


def test_a_loss_capable_sell_runs_with_signal_exits_on():
    from server.backtest import RunRequest, build_config

    config = build_config(
        RunRequest(**_request({"id": "hf_local_reference", "params": HF}, {"id": "regime_exit"}))
    )
    assert config.execution.allow_signal_exit is True
    config = build_config(
        RunRequest(**_request({"id": "hf_local_reference", "params": HF}, {"id": "scale_out"}))
    )
    assert config.execution.allow_signal_exit is False


# --- the live switch: the trader's own check ----------------------------------


def _control(tmp_path, allow_signal_exit=False):
    config = BacktestConfig.from_dict(
        {
            "strategy": {"strategy_id": "fixed", "strategy_params": {"allocation_pct": 0.05}},
            "grid": {"steps": [0.01], "profit_targets": [0.005]},
            "backtest": {"symbol": "TQQQ"},
            "execution": {"allow_signal_exit": allow_signal_exit},
            "live": {"enabled": True, "paper_trading": True, "step": 0.01, "profit_target": 0.005},
        }
    )
    return AlgorithmControl(
        config, state_db=tmp_path / "l.db", registry=STRATEGIES, allowed=False, web_allowed=True
    )


def _change(buy, sell):
    return {
        "strategy_id": "composed",
        "strategy_params": {"buy": buy, "sell": sell},
        "step": 0.01,
        "profit_target": 0.01,
    }


def test_the_trader_takes_a_composed_change(tmp_path):
    change, _ = _control(tmp_path).check(
        _change(
            {"id": "hf_local_reference", "params": HF},
            {"id": "trailing", "params": {"trail_pct": 0.01}},
        )
    )
    assert change["strategy_params"]["sell"] == {"id": "trailing", "params": {"trail_pct": 0.01}}


@pytest.mark.parametrize(
    ("buy", "sell", "match"),
    [
        (
            {"id": "hf_local_reference", "params": {**HF, "per_lot_pct": "lots"}},
            {"id": "fixed_target"},
            r"buy\.params\.per_lot_pct",
        ),
        (
            {"id": "hf_local_reference", "params": {**HF, "nope": 1}},
            {"id": "fixed_target"},
            "no parameter 'nope'",
        ),
        ({"id": "nonesuch"}, {"id": "fixed_target"}, "Unknown buy policy"),
        ({"id": "hf_local_reference", "params": HF}, {"id": "nonesuch"}, "Unknown sell policy"),
    ],
)
def test_a_bad_composed_change_is_refused_by_name(tmp_path, buy, sell, match):
    with pytest.raises(ConfigurationError, match=match):
        _control(tmp_path).check(_change(buy, sell))


def test_a_loss_capable_sell_needs_the_deployments_own_flag(tmp_path):
    change = _change({"id": "hf_local_reference", "params": HF}, {"id": "regime_exit"})
    with pytest.raises(ConfigurationError, match="allow_signal_exit"):
        _control(tmp_path).check(change)
    _control(tmp_path / "x", allow_signal_exit=True).check(change)


def test_the_live_describe_carries_the_catalogue(tmp_path):
    assert "regime_exit" in _control(tmp_path).describe()["composition"]["sells"]


# --- the approval pipeline -------------------------------------------------------


def _composed_cell(sell="fixed_target"):
    return cell(
        0.001,
        0.01,
        {"buy": {"id": "hf_local_reference", "params": HF}, "sell": {"id": sell, "params": {}}},
        net_yield_pct=9.0,
        cagr_pct=2.0,
    )


def _keep(client, run, sell):  # noqa: F811
    save_run(run, ticker="TQQQ", model="composed", cells=[_composed_cell(sell)])
    return client.post(
        "/api/algorithms/candidates",
        json={"run": run, "ticker": "TQQQ", "cell": 0, "operator": "tester"},
    )


def test_a_composed_cell_becomes_a_candidate_named_for_its_halves(client, deployments):  # noqa: F811
    body = _keep(client, "aaa111bbb222", "fixed_target").json()
    assert body["id"].startswith("hf-local-reference-x-fixed-target-tqqq")
    assert body["label"].startswith("hf_local_reference buying, fixed_target selling, on TQQQ")
    assert body["composition"] == {
        "buy": "hf_local_reference",
        "sell": "fixed_target",
        "loss": False,
    }
    assert "paper" in body["paper_deployments"], "the trader on the paper deployment would take it"


def test_a_loss_capable_candidate_is_marked_and_refused_where_the_flag_is_off(client, deployments):  # noqa: F811
    body = _keep(client, "ccc333ddd444", "regime_exit").json()
    assert body["composition"]["loss"] is True
    refused = {entry["deployment"]: entry["reason"] for entry in body.get("paper_refused", [])}
    assert "paper" not in body["paper_deployments"]
    assert "allow_signal_exit" in refused["paper"]


def test_a_composed_trial_queues_the_composed_switch(client, deployments):  # noqa: F811
    candidate_id = _keep(client, "eee555fff666", "fixed_target").json()["id"]
    started = client.post(
        f"/api/algorithms/{candidate_id}/trial", json={"deployment": "paper", "operator": "tester"}
    )
    assert started.status_code == 200, started.text
    commands = client.get("/api/live/deployments/paper").json()["commands"]
    (command,) = [c for c in commands if c["type"] == "switch_algorithm"]
    assert command["args"]["strategy_id"] == "composed"
    assert command["args"]["strategy_params"]["sell"]["id"] == "fixed_target"
