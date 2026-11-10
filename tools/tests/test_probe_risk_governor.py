"""tools/probe_risk_governor.py: what each stage plans, the null stage's
shifted maps, the veto and override regimes, and the pinned configuration.
No engine run and no network."""

from __future__ import annotations

from datetime import date, timedelta
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
import yaml

from engine.core.config import BacktestConfig
from engine.core.trading_calendar import sessions_between
from research.strategies.natr_regime import IncrementalNatrRegime
from research.strategies.risk_governor import CORE_MIN_VOTES, CORE_SIGNALS, SIGNALS
from tools import probe_daily_reserve as dr
from tools import probe_risk_governor as probe

ROOT = Path(__file__).resolve().parents[2]
EXTERNAL = Path("/somewhere/external")


def test_the_governed_configuration_is_the_reserve_plus_the_switch():
    plain, governed = probe.reserve(), probe.governed(EXTERNAL)
    extra = {
        k: v
        for k, v in governed["strategy"]["strategy_params"].items()
        if k not in plain["strategy"]["strategy_params"]
    }
    assert extra == {
        "caution_min_votes": CORE_MIN_VOTES,
        "caution_signals": ",".join(CORE_SIGNALS),
        "caution_dir": str(EXTERNAL),
    }
    without = {k: v for k, v in governed["strategy"]["strategy_params"].items() if k not in extra}
    assert without == plain["strategy"]["strategy_params"]
    assert {k: governed[k] for k in governed if k != "strategy"} == {
        k: plain[k] for k in plain if k != "strategy"
    }
    assert plain == dr.reserve(*dr.CHOSEN)


def test_the_pinned_config_is_the_measured_one():
    pinned = yaml.safe_load((ROOT / "config" / "daily_ultimate_governed_tqqq.yaml").read_text())
    governed = probe.governed(EXTERNAL)
    governed["strategy"]["strategy_params"].pop("caution_dir")  # the default directory
    assert pinned == governed
    config = BacktestConfig.from_dict(pinned)
    assert config.strategy.strategy_id == "daily_ultimate"
    assert config.execution.allow_signal_exit


def test_every_stage_names_its_runs_once():
    frontier = probe.plan_frontier(EXTERNAL)
    assert len(frontier) == 2 * len(probe.LOTS)
    assert {s["meta"]["governor"] for s in frontier} == {"off", "core"}
    robust = probe.plan_robust(EXTERNAL)
    names = [s["name"] for s in [*frontier, *robust]]
    assert len(set(names)) == len(names)
    alone = [s for s in robust if s["meta"]["change"].startswith("alone ")]
    assert len(alone) == len(SIGNALS)
    for spec in robust[1:]:
        params = spec["config"]["strategy"]["strategy_params"]
        signals = params["caution_signals"].split(",")
        assert 1 <= params["caution_min_votes"] <= len(signals)


def test_shifted_maps_keep_the_pauses_and_move_the_dates():
    days = sessions_between(date(2016, 1, 3), date(2021, 12, 31))
    rng = np.random.default_rng(3)
    paused = [bool(v) for v in rng.random(len(days)) < 0.13]
    real = {day: True for day, flag in zip(days, paused, strict=True) if flag}
    maps = probe.shifted_maps(paused, days, 12, seed=7)
    assert len(maps) == 12 and maps == probe.shifted_maps(paused, days, 12, seed=7)
    for mapping in maps:
        assert len(mapping) == len(real) and mapping != real
        assert set(mapping) <= set(days)
    with pytest.raises(SystemExit):
        probe.shifted_maps(paused[:300], days[:300], 3, seed=7)


def _daily(n: int = 420) -> pd.DataFrame:
    """Sessions whose range narrows and widens, so the NATR flag flips."""
    days = sessions_between(date(2020, 1, 1), date(2020, 1, 1) + timedelta(days=2 * n))[:n]
    close = 100.0 + np.cumsum(np.sin(np.arange(n) / 9.0))
    width = 1.0 + np.abs(np.sin(np.arange(n) / 37.0)) * 4.0
    index = pd.DatetimeIndex(pd.to_datetime(days)).tz_localize("UTC")
    return pd.DataFrame({"high": close + width, "low": close - width, "close": close}, index=index)


def test_the_veto_and_the_override_force_the_regime_and_nothing_else_changes_it():
    daily = _daily()
    buy = probe.du.BUY
    plain = IncrementalNatrRegime(
        period=buy["natr_period"],
        lookback=buy["natr_lookback"],
        min_hold=buy["regime_min_hold"],
        bear_dd=buy["bear_dd"],
        bear_window=buy["bear_window"],
    )
    expected = {}
    for ts, row in daily.iterrows():
        plain.observe(ts, row["high"], row["low"], row["close"])
        if plain.calm is not None:
            expected[ts.date()] = plain.calm
    assert probe.governed_regime(daily) == expected
    assert len(set(expected.values())) == 2  # the fixture really has both regimes
    every = dict.fromkeys(expected, True)
    assert not any(probe.governed_regime(daily, veto=every).values())
    assert all(probe.governed_regime(daily, allow=every).values())
    assert not any(probe.governed_regime(daily, veto=every, allow=every).values())


def _row(shift, geo, dd) -> dict:
    return {
        "stage": "null",
        "meta": {"shift": shift},
        "metrics": {"geo_daily": geo, "max_dd": dd, "cagr": geo * 280},
    }


def test_the_null_rank_counts_the_shifted_maps_that_match_the_real_one():
    rows = [_row("real", 0.100, 18.5), _row("off", 0.098, 20.6)]
    rows += [_row(0, 0.090, 20.6), _row(1, 0.101, 21.0), _row(2, 0.095, 18.0)]
    rank = probe.null_rank(rows)
    assert rank["n"] == 3
    assert (rank["geo_beaten_by"], rank["dd_beaten_by"], rank["calmar_beaten_by"]) == (1, 1, 0)
    assert probe.null_rank(rows[:2]) is None


# -- Daily Ultimate ----------------------------------------------------------------


def test_the_daily_stages_are_daily_ultimate_plain_and_under_the_throttle(monkeypatch):
    monkeypatch.setattr(dr, "_top_start", lambda: "2020-11-19")  # no warehouse here
    pinned = yaml.safe_load((ROOT / "config" / "daily_ultimate_tqqq.yaml").read_text())
    assert probe.daily("plain") == pinned
    throttled = probe.daily("throttle")
    assert throttled["risk"] == dr.THROTTLE
    assert throttled["strategy"] == pinned["strategy"]
    with pytest.raises(ValueError):
        probe.daily("other")
    specs = probe.plan_daily(EXTERNAL)
    assert len(specs) == len(probe.BOOKS) * (1 + len(probe.DAILY_VOTES))
    stress = probe.plan_daily_stress(EXTERNAL)
    assert len(stress) == len(probe.BOOKS) * 2 * len(probe.STRESSES)
    assert len({s["name"] for s in [*specs, *stress]}) == len(specs) + len(stress)


def test_the_null_rank_is_taken_one_book_at_a_time():
    def row(book, shift, geo, dd):
        base = _row(shift, geo, dd)
        return {**base, "stage": "daily-null", "meta": {"shift": shift, "book": book}}

    rows = [row("plain", "real", 0.16, 30.0), row("plain", "off", 0.158, 29.9)]
    rows += [row("plain", 0, 0.15, 30.0), row("throttle", 0, 0.2, 10.0)]
    rank = probe.null_rank(rows, "daily-null", "plain")
    assert rank["n"] == 1 and rank["geo_beaten_by"] == 0 and rank["dd_beaten_by"] == 1
    assert probe.null_rank(rows, "daily-null", "throttle") is None
    assert probe.null_rank(rows) is None  # nothing in the reserve's null stage


def test_paper_ultimate_takes_the_governed_daily_ultimate_profile(tmp_path):
    """The live profile is Daily Ultimate's committed algorithm plus the
    governor's switch, and paper-ultimate passes it through the trader's
    validation (which builds the strategy, and so its governor)."""
    from research.strategies import live_profiles
    from research.strategies.live_algorithm import AlgorithmControl
    from research.strategies.strategy_registry import STRATEGIES

    governed = probe.daily_governed("plain", EXTERNAL)
    params = governed["strategy"]["strategy_params"]
    params.pop("caution_dir")  # the profile reads the default directory
    profile = live_profiles.get("daily-ultimate-governed-tqqq")
    assert profile.change() == {
        "strategy_id": "daily_ultimate",
        "strategy_params": params,
        "step": governed["grid"]["steps"][0],
        "profit_target": governed["grid"]["profit_targets"][0],
    }
    assert profile.fits("TQQQ") and not profile.promoted()
    paper = BacktestConfig.from_yaml(ROOT / "config" / "ultimate_paper.yaml")
    control = AlgorithmControl(
        paper, state_db=tmp_path / "ledger.db", registry=STRATEGIES, allowed=False, web_allowed=True
    )
    _, trades = control.check(profile.change())
    assert trades.strategy.strategy_params["caution_min_votes"] == CORE_MIN_VOTES
    assert trades.risk == paper.risk
