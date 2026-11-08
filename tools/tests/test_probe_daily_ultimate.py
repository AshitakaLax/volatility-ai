"""tools/probe_daily_ultimate.py: the per-session metrics the daily goal is
judged by, the rule that chooses among configurations, and plans that
build configurations the engine accepts."""

from __future__ import annotations

import pandas as pd
import pytest

from engine.core.config import BacktestConfig
from research.strategies.strategy_registry import resolve_strategy
from tools import probe_daily_ultimate as probe


def _equity(returns, start="2024-01-02"):
    days = pd.bdate_range(start, periods=len(returns) + 1)
    values = [100.0]
    for r in returns:
        values.append(values[-1] * (1 + r))
    return pd.Series(values, index=days)


def test_daily_metrics_count_goal_flat_and_down_sessions():
    m = probe.daily_metrics(_equity([0.002, 0.0, -0.001, 0.0005, 0.001]))
    assert m["pct_goal_days"] == pytest.approx(40.0)  # +0.2% and +0.1%
    assert m["pct_flat_days"] == pytest.approx(20.0)  # a cash day is not an up day
    assert m["pct_up_days"] == pytest.approx(60.0)
    assert m["pct_down_days"] == pytest.approx(20.0)
    assert m["worst_day"] == pytest.approx(-0.1)


def test_the_geometric_daily_return_is_the_compounded_rate():
    m = probe.daily_metrics(_equity([probe.GOAL] * 252))
    assert m["geo_daily"] == pytest.approx(probe.GOAL * 100)
    assert m["max_dd"] == pytest.approx(0.0)


def _row(name, geo, dd, goal_days=10.0):
    return {"name": name, "metrics": {"geo_daily": geo, "max_dd": dd, "pct_goal_days": goal_days}}


def test_the_choice_is_the_shallowest_drawdown_that_makes_the_goal():
    rows = [_row("fast", 0.2, 60.0), _row("steady", 0.11, 25.0), _row("short", 0.09, 5.0)]
    assert probe.choose(rows)["name"] == "steady"
    tie = [_row("a", 0.12, 25.0, 30.0), _row("b", 0.15, 25.0, 40.0)]
    assert probe.choose(tie)["name"] == "b"


def test_without_a_configuration_at_the_goal_the_best_rate_is_reported():
    assert probe.choose([_row("x", 0.05, 5.0), _row("y", 0.08, 30.0)])["name"] == "y"
    assert probe.choose([]) is None


def test_the_score_starts_after_a_year_of_warm_up():
    late = pd.bdate_range("2016-12-19", periods=600)  # COWZ's history starts here
    assert probe.score_start(late) == str(late[252].date())
    assert probe.score_start(pd.bdate_range("2016-01-04", periods=3000)) == probe.SCORE_FROM


def _builds(spec):
    config = BacktestConfig.from_dict(spec["config"])
    config.validate()
    cls = resolve_strategy(config.strategy.strategy_id)
    for params in config.to_run_sweep_kwargs(cls)["strategy_params_grid"]:
        cls(**params)
    return config


@pytest.mark.parametrize("stage", ["funds", "grid"])
def test_every_planned_configuration_builds(stage):
    scales = dict.fromkeys(probe.FUNDS, 1.0)
    specs = probe.plan_funds(scales) if stage == "funds" else probe.plan_grid("TQQQ", 1.0)
    assert len({s["name"] for s in specs}) == len(specs), "names are the resume key"
    for spec in specs[:: max(1, len(specs) // 25)]:
        config = _builds(spec)
        assert config.execution.intrabar_fill == "causal"
        assert config.execution.cash_yield_pct == 0.0
        assert config.execution.allow_signal_exit, "Ultimate's regime exit is the design"


def test_the_pairs_and_robust_stages_build_from_a_chosen_configuration():
    spec = probe.plan_grid("TQQQ", 1.0)[5]
    base = {
        "params": spec["config"]["strategy"]["strategy_params"],
        "step": spec["config"]["grid"]["steps"][0],
        "target": spec["config"]["grid"]["profit_targets"][0],
    }
    pairs = probe.plan_pairs("TQQQ", base)
    assert {s["meta"]["buy"].split()[0] for s in pairs} == {
        "daily_ultimate",
        "ultimate",
        "hf_local_reference",
    }
    for spec in pairs + probe.plan_robust("TQQQ", base):
        _builds(spec)
