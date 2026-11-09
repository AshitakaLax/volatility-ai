"""tools/probe_daily_reserve.py: how much of the account is in the fund, the
rule that chooses the reserve configuration, and plans that build
configurations the engine accepts."""

from __future__ import annotations

import json

import pandas as pd
import pytest

from engine.core.config import BacktestConfig
from research.strategies.strategy_registry import resolve_strategy
from tools import probe_daily_reserve as probe
from tools import probe_daily_ultimate as du


def test_exposure_is_shares_held_at_each_close_over_equity():
    index = pd.DatetimeIndex(
        [
            pd.Timestamp(f"2024-01-0{d} {hm}", tz=du.TZ).tz_convert("UTC")
            for d in (2, 3)
            for hm in ("09:30", "15:59")
        ]
    )
    equity = pd.Series([1000.0, 1000.0, 1010.0, 1020.0], index=index)
    close = [10.0, 10.0, 11.0, 12.0]
    blotter = pd.DataFrame(
        {"side": ["buy", "buy", "sell"], "qty": [20.0, 10.0, 30.0], "bar_index": [0, 1, 3]}
    )
    e = du.exposure_metrics(blotter, close, equity, "2024-01-02")
    # 20 x 10 / 1000, 30 x 10 / 1000, 30 x 11 / 1010, then sold out.
    held = [0.2, 0.3, 330 / 1010, 0.0]
    assert e["avg_exposure"] == pytest.approx(sum(held) / 4 * 100)
    assert e["max_exposure"] == pytest.approx(33 / 1.01)
    assert e["pct_sessions_closing_in_cash"] == pytest.approx(50.0)  # the 3rd closes flat
    later = du.exposure_metrics(blotter, close, equity, "2024-01-03")
    assert later["avg_exposure"] == pytest.approx(330 / 1010 / 2 * 100)


def _row(name, geo, dd, avg=10.0, stage="reserve", **meta):
    return {
        "stage": stage,
        "name": name,
        "meta": meta,
        "metrics": {"geo_daily": geo, "max_dd": dd},
        "exposure": {"avg_exposure": avg, "max_exposure": avg * 3},
    }


def _book(label, geo, dds: dict, avg=10.0):
    rows = [_row(f"reserve {label}", geo, dds.get("history", 10.0), avg)]
    for stress in probe.STRESSES:
        rows.append(
            _row(
                f"stress {stress} | {label}",
                geo,
                dds.get(stress, 10.0),
                stage="stress",
                base=label,
                stress=stress,
            )
        )
    return rows


def test_a_configuration_is_judged_by_its_worst_drawdown_over_history_and_stress():
    rows = _book("a", 0.12, {"history": 8.0, "twice": 31.0})
    book = probe.books(rows)["a"]
    s = probe.summary(book)
    assert s["worst_dd"] == 31.0 and s["worst_stress"] == "twice"
    del book["grind"]
    assert probe.summary(book) is None  # incomplete until every stress has run


def test_the_choice_is_the_shallowest_worst_drawdown_at_the_goal_ties_to_less_exposure():
    rows = (
        _book("deep", 0.15, {"twice": 40.0}, avg=5.0)
        + _book("short", 0.09, {"twice": 5.0}, avg=1.0)  # misses the goal
        + _book("shallow", 0.11, {"twice": 20.0}, avg=30.0)
        + _book("tied", 0.10, {"twice": 20.0 + probe.TIE_DD}, avg=12.0)
    )
    summaries = [probe.summary(b) for b in probe.books(rows).values()]
    assert probe.choose(summaries)["row"]["name"] == "reserve tied"
    assert probe.choose([s for s in summaries if s["geo_daily"] < 0.1]) is None


def test_candidates_are_the_shallowest_history_drawdowns_at_the_goal():
    rows = [_row("a", 0.2, 30.0), _row("b", 0.05, 1.0), _row("c", 0.1, 12.0), _row("d", 0.11, 9.0)]
    assert [r["name"] for r in probe.candidates(rows, 2)] == ["d", "c"]


def test_every_lever_group_sends_its_best_at_the_goal_to_the_stress_paths(monkeypatch):
    monkeypatch.setattr(probe, "STRESS_CANDIDATES", 1)

    def row(name, geo, dd, cap):
        return {**_row(name, geo, dd), "meta": {"turbulent": "cash", "cap": cap, "protect": "none"}}

    rows = [row("a", 0.1, 5.0, None), row("b", 0.1, 9.0, 0.3), row("c", 0.1, 7.0, 0.3)]
    rows.append(row("d", 0.05, 1.0, 0.2))  # its group never reaches the goal
    names = [r["name"] for r in probe.stress_candidates(rows)]
    assert names == ["a", "c"]


def test_reserve_puts_each_lever_where_the_engine_reads_it():
    plain = probe.reserve(0.004, 0.08, 0.002, None)
    assert plain["risk"] == {}
    assert plain["strategy"]["strategy_params"]["compound_lots"] is True
    assert plain["strategy"]["strategy_params"]["goal_pause_buys"] is True
    assert plain["strategy"]["strategy_params"]["turbulent_mode"] == "cash"
    capped = probe.reserve(0.004, 0.08, 0.002, 0.3, protect="throttle")
    assert capped["risk"] == {"max_total_exposure": 0.3, **probe.THROTTLE}
    bear = probe.reserve(0.004, 0.08, 0.004, 0.2, turbulent="rev5", protect="bear30")
    params = bear["strategy"]["strategy_params"]
    assert params["bear_dd"] == 0.3 and params["reversal_lot_pct"] == 0.05
    assert bear["grid"] == {"steps": [0.004], "profit_targets": [0.08]}
    assert bear["execution"]["allow_signal_exit"] is True


def test_the_reserve_plan_builds_configurations_the_engine_accepts():
    specs = probe.plan_reserve()
    assert len(specs) == len({s["name"] for s in specs}) == 864
    for spec in specs[::37]:
        config = BacktestConfig.from_dict(spec["config"])
        config.to_run_sweep_kwargs(resolve_strategy(config.strategy.strategy_id))
        config.risk.build()


def test_stressed_specs_name_their_scenario_and_the_top_start(monkeypatch):
    monkeypatch.setattr(probe, "_top_start", lambda: "2020-11-19")
    specs = probe._stressed("stress", "x", {"c": 1}, {"lot": 0.004}, history=True)
    assert [s["meta"]["stress"] for s in specs] == ["history", *probe.STRESSES]
    assert [s.get("stress") for s in specs] == [None, "deeper", "grind", "twice", "fast", None]
    assert specs[-1]["start"] == "2020-11-19" and "start" not in specs[0]
    assert all(s["meta"]["base"] == "x" and s["meta"]["lot"] == 0.004 for s in specs)


def test_later_stages_end_where_the_reserve_stage_did(tmp_path):
    with pytest.raises(SystemExit):
        probe.reserve_end(tmp_path)
    rows = [_row("reserve a", 0.1, 5.0), _row("reserve b", 0.1, 5.0), _row("stress x", 0.1, 5.0)]
    for row, end in zip(rows, ("2026-11-03", "2026-11-04", "2026-11-06"), strict=True):
        row["metrics"]["end"] = end
    rows[-1]["stage"] = "stress"
    (tmp_path / "results.jsonl").write_text("".join(json.dumps(r) + "\n" for r in rows))
    assert probe.reserve_end(tmp_path) == "2026-11-04"


def test_the_committed_reserve_config_is_the_choice():
    import yaml

    assert yaml.safe_load(probe.CHOSEN_CONFIG.read_text()) == probe.reserve(*probe.CHOSEN)
    config = BacktestConfig.from_yaml(probe.CHOSEN_CONFIG)
    config.validate()
    kwargs = config.to_run_sweep_kwargs(resolve_strategy(config.strategy.strategy_id))
    assert kwargs["allow_signal_exit"] is True and kwargs["intrabar_fill"] == "causal"
    assert config.risk.max_total_exposure is None and config.risk.dd_exposure_start == 0.05


def test_paper_ultimate_trades_the_choice_with_its_throttle(tmp_path):
    """The live profile is the committed config's algorithm, and paper-ultimate,
    which holds the risk limits a profile cannot, has the config's throttle and
    takes the profile."""
    from research.strategies import live_profiles
    from research.strategies.live_algorithm import AlgorithmControl
    from research.strategies.strategy_registry import STRATEGIES

    chosen = BacktestConfig.from_yaml(probe.CHOSEN_CONFIG)
    profile = live_profiles.get("daily-ultimate-reserve-tqqq")
    assert profile.change() == {
        "strategy_id": chosen.strategy.strategy_id,
        "strategy_params": chosen.strategy.strategy_params,
        "step": chosen.grid.steps[0],
        "profit_target": chosen.grid.profit_targets[0],
    }
    paper = BacktestConfig.from_yaml(probe.CHOSEN_CONFIG.parent / "ultimate_paper.yaml")
    throttle = ("dd_exposure_start", "dd_exposure_full", "dd_exposure_floor_pct")
    assert [getattr(paper.risk, f) for f in throttle] == [getattr(chosen.risk, f) for f in throttle]
    assert paper.risk.max_total_exposure == chosen.risk.max_total_exposure
    control = AlgorithmControl(
        paper, state_db=tmp_path / "ledger.db", registry=STRATEGIES, allowed=False, web_allowed=True
    )
    _, trades = control.check(profile.change())
    assert trades.strategy.strategy_id == "daily_ultimate" and trades.risk == paper.risk


def test_both_stresses_only_configurations_at_the_goal_in_both_halves(tmp_path, monkeypatch):
    monkeypatch.setattr(probe, "_top_start", lambda: "2020-11-19")
    days = pd.bdate_range("2021-11-01", "2022-02-28")
    split = days.searchsorted(pd.Timestamp(du.SPLIT))

    def row(name, before, after):
        growth = [1 + before] * split + [1 + after] * (len(days) - split)
        equity = pd.Series(growth, index=days).cumprod() * 1000.0
        meta = dict(zip(probe.CELL, (0.004, 0.08, 0.002, None, "cash", False, "none"), strict=True))
        return {
            **_row(f"reserve {name}", 0.1, 30.0),
            "meta": meta,
            "equity": {str(d.date()): v for d, v in equity.items()},
        }

    rows = [row("a", 0.0012, 0.0011), row("b", 0.0015, 0.0005), row("c", 0.0005, 0.0015)]
    assert [r["name"] for r in probe.at_goal_in_both_halves(rows)] == ["reserve a"]
    (tmp_path / "results.jsonl").write_text("".join(json.dumps(r) + "\n" for r in rows))
    specs = probe.plan_both(tmp_path)
    assert [s["name"] for s in specs] == [f"both {s} | a" for s in probe.STRESSES]
    assert all(s["meta"]["base"] == "a" for s in specs)
