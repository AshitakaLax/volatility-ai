"""tools/probe_risk_overlay.py, without the warehouse: every stage's plan is
JSON and uniquely named, every kind of schedule builds over a small proxy
archive, a shift moves overlays in time, and the report reads its rows."""

from __future__ import annotations

import json
from datetime import date

import numpy as np
import pandas as pd
import pytest

from engine.core.trading_calendar import sessions_between
from research.risk_overlay import baselines as baselines_module
from research.risk_overlay.archive import ReportArchive
from research.risk_overlay.baselines import Baseline
from research.risk_overlay.proxy import build_archive
from tools import probe_risk_overlay as P

SESSIONS = sessions_between(date(2023, 1, 1), date(2025, 6, 30))


@pytest.fixture(scope="module")
def proxy_dir(tmp_path_factory):
    rng = np.random.default_rng(3)
    closes = pd.Series(
        50 * np.exp(np.cumsum(rng.normal(0, 0.03, len(SESSIONS)))), index=pd.DatetimeIndex(SESSIONS)
    )

    def series(level, spread):
        stamps = pd.DatetimeIndex(
            [pd.Timestamp(d).tz_localize("UTC") + pd.Timedelta(hours=21) for d in SESSIONS]
        )
        return pd.Series(
            level * np.exp(np.cumsum(rng.normal(0, spread, len(SESSIONS)))), index=stamps
        )

    outside = {
        "cboe_VXN": series(22, 0.06),
        "cboe_VIX": series(17, 0.06),
        "cboe_VIX9D": series(16, 0.07),
        "cboe_VIX3M": series(19, 0.03),
        "cboe_VIX6M": series(21, 0.02),
        "cboe_SKEW": series(135, 0.01),
        "yahoo_QQQ": series(400, 0.012),
    }
    root = tmp_path_factory.mktemp("proxy")
    archive = ReportArchive(root)
    for entry in build_archive("TQQQ", closes, outside, SESSIONS[260:]):
        archive.write(date.fromisoformat(entry["session"]), entry)
    return str(root)


@pytest.fixture(autouse=True)
def frozen_baseline(monkeypatch):
    monkeypatch.setattr(
        baselines_module,
        "baseline_for",
        lambda symbol, path=None: Baseline(
            symbol, 4.0, {"next_month": -30.0, "next_quarter": -45.0}
        ),
    )
    P.proxy_state.cache_clear()
    P.truth_state.cache_clear()


def _attribution_rows(out, sessions):
    rows = {
        d.isoformat(): {
            "lots": 3,
            "within_5": (i % 7) / 7,
            "within_21": (i % 5) / 5,
            "open_at_end": 0,
        }
        for i, d in enumerate(sessions)
    }
    for book in P.BOOKS:
        line = {
            "stage": "attribution",
            "name": f"attribution {book} none",
            "meta": {"book": book},
            "metrics": {"x": 1},
            "attribution": rows,
        }
        with (out / "results.jsonl").open("a") as sink:
            sink.write(json.dumps(line) + "\n")


@pytest.mark.parametrize(
    "stage",
    [
        "tiers",
        "attribution",
        "oracle",
        "matrix",
        "proxy",
        "spacing",
        "weekly",
        "null",
        "robust",
        "stress",
        "perturb",
        "catalysts",
        "priority",
        "advisory",
        "accuracy",
    ],
)
def test_every_stage_plans_json_with_unique_names(stage, proxy_dir, tmp_path):
    _attribution_rows(tmp_path, SESSIONS[260:])
    specs = P.plan(stage, "grid", proxy_dir, tmp_path)
    assert specs, stage
    names = [s["name"] for s in specs]
    assert len(names) == len(set(names)), "a repeated name would be skipped as done"
    json.dumps(specs)
    if stage == "accuracy":
        assert len(specs) == 1 + 4 * 21 * P.SEEDS + len(P.KNOBS) * len(P.KNOB_ACCURACIES) * P.SEEDS
    if stage == "null":
        assert sum(1 for s in specs if isinstance(s["meta"].get("shift"), int)) == 3 * P.NULL_SHIFTS


@pytest.mark.parametrize(
    "schedule",
    [
        {"kind": "constant", "response": "x0.5"},
        {"kind": "random", "share": 0.13, "seed": 1, "response": "pause"},
        {"kind": "dates", "dates": ["2024-03-04", "2024-03-05"], "response": "pause"},
        {"kind": "proxy", "form": "graded", "settings": P.LEVERS["all"]},
        {"kind": "proxy", "form": "binary", "settings": P.LEVERS["tiers"]},
        {"kind": "proxy", "form": "continuous", "settings": P.LEVERS["tiers"]},
        {
            "kind": "proxy",
            "form": "ceiling",
            "settings": P.LEVERS["tiers"],
            "thresholds_delta": 0.05,
        },
        {"kind": "proxy", "settings": P.LEVERS["tiers"], "drop": "gap", "shift": 30},
        {"kind": "matrix", "row": 3, "response": "pause"},
        {"kind": "perturb", "how": "inverted"},
        {"kind": "advisory", "follow": 0.8, "delay": 30, "seed": 2},
    ],
)
def test_every_kind_of_schedule_builds_and_is_enforced(schedule, proxy_dir):
    built = P.build_schedule({"schedule": {**schedule, "proxy": proxy_dir}}, SESSIONS)
    assert built is not None
    assert all(o.mode == "enforce" for _d, o in built.items())


def test_none_is_no_schedule():
    assert P.build_schedule({"schedule": {"kind": "none"}}, SESSIONS) is None


def test_a_shift_moves_every_overlay(proxy_dir):
    base = P.build_schedule(
        {"schedule": {"kind": "proxy", "settings": P.LEVERS["tiers"], "proxy": proxy_dir}}, SESSIONS
    )
    moved = P.shifted(base, SESSIONS, 10)
    assert len(moved) == len(base)
    position = {d: i for i, d in enumerate(SESSIONS)}
    first, overlay = base.items()[0]
    target = SESSIONS[(position[first] + 10) % len(SESSIONS)]
    assert moved.get(target).tier == overlay.tier


def test_the_auc_check_and_the_report(proxy_dir, tmp_path):
    _attribution_rows(tmp_path, SESSIONS[260:])
    table = P.auc_table(proxy_dir, tmp_path, "grid")
    assert table and all(v is None or 0 <= v <= 1 for v in table.values())

    def row(name, form, cagr, dd):
        metrics = {"cagr": cagr, "max_dd": dd, "calmar": cagr / dd}
        return {
            "stage": "tiers",
            "name": name,
            "meta": {"book": "grid", "form": form},
            "metrics": metrics,
            "halves": {"2017-21": metrics, "2022 on": metrics},
        }

    with (tmp_path / "results.jsonl").open("a") as sink:
        sink.write(json.dumps(row("tiers grid none", "none", 40.0, 50.0)) + "\n")
        sink.write(json.dumps(row("tiers grid x0.5", "x0.5", 30.0, 30.0)) + "\n")
    text = P.report(tmp_path)
    assert "## grid" in text and "tiers grid x0.5" in text and "+0.20" in text


def test_a_run_through_the_engine_enforces_its_schedule(monkeypatch):
    """One spec end to end through probe_daily_ultimate.run_one: a pause
    every session buys nothing, and the run says what its overlay did."""
    from datetime import UTC, datetime, timedelta

    from engine.warehouse import bars as bars_module
    from tools import probe_daily_ultimate as du

    days = sessions_between(date(2023, 12, 1), date(2025, 2, 28))
    stamps, closes = [], []
    rng = np.random.default_rng(0)
    price = 50.0
    for day in days:
        opens = datetime.combine(day, datetime.min.time(), tzinfo=UTC) + timedelta(
            hours=14, minutes=30
        )
        for minute in range(0, 390, 30):
            price *= float(np.exp(rng.normal(0, 0.004)))
            stamps.append(opens + timedelta(minutes=minute))
            closes.append(price)
    frame = pd.DataFrame(
        {"open": closes, "high": closes, "low": closes, "close": closes, "volume": 1000.0},
        index=pd.DatetimeIndex(stamps, name="timestamp"),
    )
    monkeypatch.setattr(bars_module, "load_frame", lambda symbol: frame)
    # A target the path reaches: a book that never sells has no sale columns
    # for probe_daily_ultimate.trading_metrics to read.
    config = du._config("TQQQ", "fixed", {"allocation_pct": 0.05}, 0.01, 0.02)

    def spec(schedule):
        return {
            "stage": "t",
            "name": f"t {schedule['kind']}",
            "fund": "TQQQ",
            "config": config,
            "schedule": schedule,
            "meta": {"book": "test"},
        }

    plain = P.run(spec({"kind": "none"}))
    paused = P.run(spec({"kind": "constant", "response": "pause"}))
    # Over the whole run (the scored window is its last few months).
    assert plain["engine"]["Trade Count"] > 0
    assert paused["engine"]["Trade Count"] == 0
    assert paused["overlay"]["Overlay Paused Sessions"] > 200
    assert "Overlay Sessions" not in plain["overlay"]
    assert set(paused["halves"]) == {"2017-21", "2022 on"}
