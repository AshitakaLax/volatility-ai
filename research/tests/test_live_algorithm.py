"""research/strategies/live_algorithm.py -- the live algorithm, as the
Fidelity Bridge extension sees and changes it.

What is pinned: only the strategy, its parameters, live.step and
live.profit_target can change, and only when the deployment's file
allows it; every change is validated the way a start-up would be before
anything is written; the override is the one place a change lives, and
an unreadable one is an error rather than silently ignored.
"""

from __future__ import annotations

import json

import pytest

from engine.core.config import BacktestConfig
from engine.core.exceptions import ConfigurationError
from research.strategies.live_algorithm import (
    OVERRIDE_FILENAME,
    AlgorithmControl,
    build_strategy,
    check_target_return,
    override_path,
)
from research.strategies.strategy_registry import STRATEGIES


def _base(**strategy) -> BacktestConfig:
    return BacktestConfig.from_dict(
        {
            "strategy": strategy
            or {"strategy_id": "fixed", "strategy_params": {"allocation_pct": 0.05}},
            "grid": {"steps": [0.01], "profit_targets": [0.005]},
            "backtest": {"symbol": "TQQQ", "initial_cash": 10_000.0},
            "live": {"enabled": True, "step": 0.01, "profit_target": 0.005},
        }
    )


def _control(tmp_path, *, allowed=True, base=None, **kwargs) -> AlgorithmControl:
    lines: list[str] = []
    control = AlgorithmControl(
        base or _base(),
        state_db=tmp_path / "state" / "ledger.db",
        registry=STRATEGIES,
        allowed=allowed,
        config_path="config/fidelity_live.yaml",
        log=lines.append,
        now=lambda: 1_791_300_000.0,
        **kwargs,
    )
    control.lines = lines
    return control


def _change(**overrides) -> dict:
    change = {
        "strategy_id": "fixed",
        "strategy_params": {"allocation_pct": 0.08},
        "step": 0.02,
        "profit_target": 0.01,
    }
    change.update(overrides)
    return change


# -- what is in force ----------------------------------------------------------


def test_without_an_override_the_config_files_algorithm_is_traded(tmp_path):
    config = _control(tmp_path).effective_config()
    assert config.strategy.strategy_id == "fixed"
    assert config.live.step == 0.01 and config.live.profit_target == 0.005


def test_an_accepted_change_is_what_is_traded_from_then_on(tmp_path):
    control = _control(tmp_path)
    control.set(_change())
    config = control.effective_config()
    assert config.strategy.strategy_params == {"allocation_pct": 0.08}
    assert (config.live.step, config.live.profit_target) == (0.02, 0.01)
    # Everything else is still the file's.
    assert config.backtest.symbol == "TQQQ" and config.backtest.initial_cash == 10_000.0
    # And a restart reads it back the same way.
    again = _control(tmp_path).effective_config()
    assert again.strategy.strategy_params == {"allocation_pct": 0.08}


def test_an_override_a_deployment_does_not_allow_is_ignored_and_said_so(tmp_path):
    _control(tmp_path).set(_change())
    closed = _control(tmp_path, allowed=False)
    assert closed.effective_config().live.step == 0.01, (
        "the file wins when it does not allow changes"
    )
    assert closed.ignored_override() is True


def test_an_unreadable_override_stops_the_engine_rather_than_being_skipped(tmp_path):
    control = _control(tmp_path)
    control.path.parent.mkdir(parents=True)
    control.path.write_text("{ half written", encoding="utf-8")
    with pytest.raises(ConfigurationError, match="not readable JSON"):
        control.effective_config()
    control.path.write_text("[1, 2]", encoding="utf-8")
    with pytest.raises(ConfigurationError, match="JSON object"):
        control.effective_config()


def test_the_override_lives_beside_the_state_database(tmp_path):
    assert override_path(tmp_path / "state" / "ledger.db") == tmp_path / "state" / OVERRIDE_FILENAME


# -- describe --------------------------------------------------------------------


def test_describe_shows_what_is_traded_and_what_may_be_picked(tmp_path):
    described = _control(tmp_path).describe()
    assert described["editable"] is True and described["reason"] is None
    assert described["symbol"] == "TQQQ"
    assert described["current"] == {
        "strategy_id": "fixed",
        "strategy_params": {"allocation_pct": 0.05},
        "step": 0.01,
        "profit_target": 0.005,
    }
    assert described["source"] == "config" and described["changedAt"] is None
    ids = [entry["id"] for entry in described["strategies"]]
    assert ids == sorted(STRATEGIES)
    fixed = next(entry for entry in described["strategies"] if entry["id"] == "fixed")
    allocation = next(spec for spec in fixed["params"] if spec["name"] == "allocation_pct")
    assert allocation["required"] is True and allocation["suggested"] == 0.05
    json.dumps(described)  # it goes over the wire


def test_describe_after_a_change_names_its_source_and_the_files_algorithm(tmp_path):
    control = _control(tmp_path)
    control.set(_change())
    described = control.describe()
    assert described["source"] == "extension"
    assert described["changedAt"].startswith("2026-")
    assert described["current"]["step"] == 0.02
    assert described["configFile"]["step"] == 0.01


def test_a_deployment_that_does_not_allow_changes_says_how_to_allow_them(tmp_path):
    described = _control(tmp_path, allowed=False).describe()
    assert described["editable"] is False
    assert "allow_algorithm_changes: true" in described["reason"]
    assert "config/fidelity_live.yaml" in described["reason"]


# -- set ------------------------------------------------------------------------------


def test_a_change_is_refused_when_the_deployment_does_not_allow_it(tmp_path):
    control = _control(tmp_path, allowed=False)
    with pytest.raises(PermissionError, match="allow_algorithm_changes"):
        control.set(_change())
    with pytest.raises(PermissionError):
        control.reset()
    assert not control.path.exists()


@pytest.mark.parametrize(
    "change,match",
    [
        ({"strategy_id": "nope"}, "Unknown strategy"),
        ({"strategy_id": 7}, "Unknown strategy"),
        ({"step": 0}, "between 0 and 1"),
        ({"step": 1}, "between 0 and 1"),
        ({"step": 5}, "between 0 and 1"),
        ({"profit_target": -0.01}, "between 0 and 1"),
        ({"profit_target": "0.01"}, "must be a number"),
        ({"profit_target": float("nan")}, "must be a number"),
        ({"step": True}, "must be a number"),
        ({"strategy_params": {"allocation_pct": 0.05, "no_such": 1}}, "no parameter 'no_such'"),
        ({"strategy_params": {"allocation_pct": 0.05, "percentage": 0.05}}, "not set here"),
        ({"strategy_params": {"allocation_pct": "lots"}}, "must be a number"),
        ({"strategy_params": {"allocation_pct": None}}, "is required"),
        ({"strategy_params": "everything"}, "strategy_params must be an object"),
    ],
)
def test_a_bad_change_is_refused_and_nothing_is_written(tmp_path, change, match):
    control = _control(tmp_path)
    with pytest.raises(ConfigurationError, match=match):
        control.set(_change(**change))
    assert not control.path.exists()


def test_parameter_types_come_from_the_constructor(tmp_path):
    control = _control(tmp_path)
    params = {"per_lot_pct": 0.0002, "lookback_days": 0.02, "bars_per_day": 387.5}
    with pytest.raises(ConfigurationError, match="whole number"):
        control.set(_change(strategy_id="hf_local_reference", strategy_params=params))
    params["bars_per_day"] = 387.0
    control.set(_change(strategy_id="hf_local_reference", strategy_params=params))
    stored = json.loads(control.path.read_text(encoding="utf-8"))
    assert stored["strategy_params"]["bars_per_day"] == 387
    assert isinstance(stored["strategy_params"]["bars_per_day"], int)


def test_a_choice_must_be_one_of_the_choices(tmp_path):
    control = _control(tmp_path)
    params = {
        "per_lot_pct": 0.0002,
        "lookback_days": 0.02,
        "bars_per_day": 387,
        "vol_measure": "vibes",
    }
    with pytest.raises(ConfigurationError, match="one of stdev, range"):
        control.set(_change(strategy_id="hf_local_reference", strategy_params=params))


def test_a_blank_optional_parameter_keeps_the_constructors_default(tmp_path):
    control = _control(tmp_path)
    params = {
        "per_lot_pct": 0.0002,
        "lookback_days": 0.02,
        "bars_per_day": 387,
        "event_day_boost_multiplier": None,
    }
    control.set(_change(strategy_id="hf_local_reference", strategy_params=params))
    stored = json.loads(control.path.read_text(encoding="utf-8"))
    assert "event_day_boost_multiplier" not in stored["strategy_params"]


def test_a_target_return_follows_the_profit_target(tmp_path):
    """bayesian_dual_scale's posterior must estimate the target actually
    traded; the form cannot set it, the profit target does."""
    control = _control(tmp_path)
    control.set(
        _change(
            strategy_id="bayesian_dual_scale",
            strategy_params={"max_trade_pct": 0.05, "horizon_days": 1.0, "bars_per_day": 387},
            profit_target=0.012,
        )
    )
    config = control.effective_config()
    assert config.strategy.strategy_params["target_return"] == 0.012


def test_wiring_the_config_file_supplies_is_kept_for_the_same_strategy(tmp_path):
    base = _base(
        strategy_id="ultimate_rsp",
        strategy_params={"exposure_by_date": None, **_ultimate_rsp_params()},
    )
    control = _control(tmp_path, base=base)
    control.set(_change(strategy_id="ultimate_rsp", strategy_params=_ultimate_rsp_params()))
    stored = json.loads(control.path.read_text(encoding="utf-8"))
    assert "exposure_by_date" in stored["strategy_params"]


def _ultimate_rsp_params() -> dict:
    from research.strategies.param_schema import STRATEGY_DEFAULTS

    return dict(STRATEGY_DEFAULTS["ultimate_rsp"])


def test_a_strategy_that_refuses_its_parameters_refuses_the_change(tmp_path):
    control = _control(tmp_path)
    with pytest.raises(ConfigurationError, match=r"refused these parameters|allocation"):
        control.set(_change(strategy_params={"allocation_pct": 5.0}))
    assert not control.path.exists()


def test_an_accepted_change_is_written_logged_and_announced(tmp_path):
    control = _control(tmp_path)
    told = []
    control.on_apply = lambda: told.append(True)
    result = control.set(_change())
    assert result["applied"] is True and result["source"] == "extension"
    assert result["current"]["strategy_params"] == {"allocation_pct": 0.08}
    stored = json.loads(control.path.read_text(encoding="utf-8"))
    assert stored["changedAt"] == "2026-10-06T15:20:00+00:00"
    assert told == [True]
    assert any("changed from the extension: fixed" in line for line in control.lines)
    assert not list(control.path.parent.glob("*.tmp")), "written atomically"


def test_pending_until_the_loop_trades_it(tmp_path):
    control = _control(tmp_path)
    assert control.pending() is False, "nothing is live yet to compare with"
    control.mark_live(control.effective_config())
    assert control.pending() is False
    control.set(_change())
    assert control.pending() is True
    assert control.describe()["pending"] is True
    control.mark_live(control.effective_config())
    assert control.pending() is False


# -- reset ------------------------------------------------------------------------------


def test_reset_goes_back_to_the_config_files_algorithm(tmp_path):
    control = _control(tmp_path)
    control.set(_change())
    told = []
    control.on_apply = lambda: told.append(True)
    result = control.reset()
    assert result == {
        "applied": True,
        "current": {
            "strategy_id": "fixed",
            "strategy_params": {"allocation_pct": 0.05},
            "step": 0.01,
            "profit_target": 0.005,
        },
        "source": "config",
    }
    assert not control.path.exists()
    assert told == [True]
    assert control.effective_config().live.step == 0.01


def test_reset_with_nothing_to_reset_changes_nothing(tmp_path):
    control = _control(tmp_path)
    told = []
    control.on_apply = lambda: told.append(True)
    assert control.reset()["applied"] is False
    assert told == []


# -- the shared checks ------------------------------------------------------------------


def test_build_strategy_names_the_known_strategies_for_an_unknown_one():
    config = BacktestConfig.from_dict(
        {**_base().to_dict(), "strategy": {"strategy_id": "nope", "strategy_params": {}}}
    )
    with pytest.raises(ConfigurationError, match=r"Known: .*fixed"):
        build_strategy(config, STRATEGIES)


def test_the_target_return_cross_check():
    class Strategy:
        target_return = 0.0075

    config = _base()  # live.profit_target 0.005
    with pytest.raises(ConfigurationError, match="does not match"):
        check_target_return(config, Strategy())
    Strategy.allow_target_return_mismatch = True
    check_target_return(config, Strategy())
    Strategy.target_return = None
    check_target_return(config, Strategy())


def test_a_hand_edited_override_is_held_to_the_same_rules(tmp_path):
    control = _control(tmp_path)
    control.set(_change())
    stored = json.loads(control.path.read_text(encoding="utf-8"))
    for broken, match in (
        ({**stored, "step": 7}, "between 0 and 1"),
        ({**stored, "strategy_id": "nope"}, "Unknown strategy"),
        ({**stored, "strategy_params": {"allocation_pct": "lots"}}, "must be a number"),
    ):
        control.path.write_text(json.dumps(broken), encoding="utf-8")
        with pytest.raises(ConfigurationError, match=match) as caught:
            control.effective_config()
        assert str(control.path) in str(caught.value)
