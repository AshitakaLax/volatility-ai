#!/usr/bin/env python
"""
The risk report overlay's measurement (docs/daily_risk_report_plan.md,
Phase 2; written up in docs/research/risk-overlay.md).

    python tools/build_proxy_reports.py --symbol TQQQ --out PROXY --baselines
    python tools/probe_risk_overlay.py --stage auc --proxy PROXY --out DIR
    python tools/probe_risk_overlay.py --stage tiers --book grid --proxy PROXY --out DIR [--jobs N]
    ...                               --stage attribution | oracle | matrix | proxy | spacing |
                                      weekly | null | robust | stress | perturb | catalysts |
                                      priority | advisory | accuracy | all
    python tools/probe_risk_overlay.py --report DIR

Every run is one of the three books the deployments trade -- `grid` (the
champion grid, config/paper_aggressive.yaml's algorithm), `ultimate`
(config/ultimate_paper.yaml's, its drawdown throttle included) and `daily`
(Daily Ultimate, config/daily_ultimate_tqqq.yaml) -- on TQQQ, measured as the
risk governor was: causal intrabar fills, dynamic slippage, no cash yield,
from 2016-01-04, scored from 2017-01-03, with the halves 2017-21 and 2022 on
(tools/probe_daily_ultimate.py's run_one). Each run hands the RiskManager an
ENFORCED schedule built in the worker from the spec -- an archive of proxy
reports, a synthetic history at a chosen accuracy, or a constant, random,
shifted or perturbed one -- so no schedule file is written per run. A run
already in DIR/results.jsonl is skipped.

--------------------------------------------------------------------
THE STAGES (the plan's table; `walk` and the gates are read from the others)

  auc          before any engine run: does the proxy's score S rank the
               sessions that were bad to buy on (the attribution label)?
  tiers        every session at x1, x0.75, x0.5, x0.25; a 50% ceiling; a
               pause on a random 13%: what each level of risk costs and buys
  attribution  the tier-0 run's lots by the session that bought them: the
               share at target within 5 and 21 sessions, still open at the end
  oracle       pause (or tier 2) the worst 5, 10, 20% of sessions by it
  matrix       the proxy's tier (rows) x a response (columns) on those
               sessions only: the dose-response for each kind of day
  proxy        mapping v1 on the proxy: a binary pause, the graded tiers, a
               continuous x(1 - S), the ceiling alone
  spacing      lever B alone and with the tiers
  weekly       lever G alone and with the others
  null         40 copies of each lever's schedule moved in time
  robust       thresholds +-0.05, each component left out, reversals not exempt
  stress       tools/stress_paths.py's paths, with and without the overlay
  perturb      10/25/50% of tiers randomised; inverted; always 3; always 0
  catalysts    the blackout at 10, 15 and 30 minutes
  priority     superseding both levers, the governor alone, or neither
  advisory     an operator who follows a tier-3 pause with probability
               0.5/0.8/1, 0/30/90 minutes after the open; 20 seeds
  accuracy     each lever on the mixture and noisy families at 8 accuracies
               and proxy+ at 5, 20 seeds each; then the knobs on noisy
"""

from __future__ import annotations

import argparse
import copy
import json
import math
import random
import statistics
import sys
from concurrent.futures import ProcessPoolExecutor, as_completed
from dataclasses import replace
from datetime import date, datetime, time, timedelta
from functools import lru_cache
from pathlib import Path
from typing import Any

_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from tools import probe_daily_ultimate as du

FUND = "TQQQ"
BOOKS = {
    "grid": "config/paper_aggressive.yaml",
    "ultimate": "config/ultimate_paper.yaml",
    "daily": "config/daily_ultimate_tqqq.yaml",
}
HALVES = (("2017-21", None, du.SPLIT), ("2022 on", du.SPLIT, None))
NULL_SHIFTS = 40
NULL_SEED = 20261120
SEEDS = 20
ACCURACIES = (0.0, 0.1, 0.2, 0.3, 0.5, 0.7, 0.9, 1.0)
LAMBDAS = (0.0, 0.1, 0.2, 0.3, 0.5)
KNOB_ACCURACIES = (0.2, 0.5, 0.9)
KNOBS = {
    "persistence": {"persistence": 0.8},
    "shared": {"shared": 0.7},
    # Named by their beta. Runs named "complacent" and "alarmist" were made
    # while the bias changed nothing (research/risk_overlay/synthetic.py, the
    # bias), and the report leaves them out.
    "bias -0.5": {"bias": -0.5},
    "bias +0.5": {"bias": 0.5},
    "missing": {"missing": 0.1},
    "catalyst_miss": {"catalyst_miss": 0.3},
}
# The levers each schedule is measured for.
LEVERS = {
    "tiers": {"daily": True, "spacing": {"enabled": False}, "weekly": {"enabled": False}},
    "spacing": {"daily": False, "spacing": {"enabled": True}, "weekly": {"enabled": False}},
    "weekly": {"daily": False, "spacing": {"enabled": False}, "weekly": {"enabled": True}},
    "all": {"daily": True, "spacing": {"enabled": True}, "weekly": {"enabled": True}},
}
OVERLAY_KEYS = (
    "Overlay Sessions",
    "Overlay Paused Sessions",
    "Overlay Mean Step Multiplier",
    "Overlay Buys Withheld",
    "Overlay Dollars Withheld",
)


# --------------------------------------------------------------- the books


def book_config(book: str) -> dict:
    """The book as a backtest: its algorithm, step and target as deployed,
    its risk section without an overlay, measured the governor's way."""
    import yaml

    data = yaml.safe_load((_REPO_ROOT / BOOKS[book]).read_text(encoding="utf-8"))
    live = data.pop("live", None) or {}
    risk = {k: v for k, v in (data.get("risk") or {}).items() if k != "overlay"}
    strategy = data["strategy"]
    step = live.get("step") or data["grid"]["steps"][0]
    target = live.get("profit_target") or data["grid"]["profit_targets"][0]
    config = du._config(
        FUND,
        strategy["strategy_id"],
        dict(strategy.get("strategy_params") or {}),
        step,
        target,
        risk=risk,
    )
    return config


def settings(**over) -> Any:
    """A risk.overlay section in enforce mode, with `over` laid on the plan's defaults."""
    from engine.core.config import _parse_overlay

    data: dict = {"mode": "enforce"}
    for key, value in over.items():
        if isinstance(value, dict):
            data[key] = {**data.get(key, {}), **value}
        else:
            data[key] = value
    return _parse_overlay(data)


# --------------------------------------------------------------- per worker


@lru_cache(maxsize=2)
def proxy_state(proxy_dir: str) -> dict:
    """The proxy archive, parsed once a process."""
    from engine.core.risk_report import parse_report
    from research.risk_overlay.archive import ReportArchive
    from research.risk_overlay.baselines import baseline_for
    from research.risk_overlay.schedules import entry_inputs

    baseline = baseline_for(FUND)
    if baseline is None:
        raise SystemExit(
            f"no frozen baseline for {FUND}: run tools/build_proxy_reports.py --baselines"
        )
    entries = ReportArchive(proxy_dir).entries()
    reports, inputs, received = [], [], []
    for entry in entries:
        report = parse_report(entry["report"]).require()
        reports.append(report)
        inputs.append(entry_inputs(entry, report, FUND, baseline))
        received.append(entry["received_at"])
    return {"reports": reports, "inputs": inputs, "received": received, "baseline": baseline}


@lru_cache(maxsize=1)
def truth_state(proxy_dir: str):
    """What each proxy session's report should have said (synthetic.truths)."""
    import pandas as pd

    from engine.warehouse.bars import load_frame
    from research.risk_overlay.synthetic import truths

    state = proxy_state(proxy_dir)
    bars = load_frame(FUND)
    ny = bars.index.tz_convert(du.TZ)
    minutes = ny.hour * 60 + ny.minute
    regular = bars[(minutes >= 570) & (minutes < 960)]
    days = pd.DatetimeIndex(regular.index.tz_convert(du.TZ).date)
    grouped = regular.groupby(days)
    opens = {d.date(): float(v) for d, v in grouped["open"].first().items()}
    closes = {d.date(): float(v) for d, v in grouped["close"].last().items()}
    lows = {d.date(): float(v) for d, v in grouped["low"].min().items()}
    return truths([r.session for r in state["reports"]], opens, closes, lows)


def proxy_mapped(proxy_dir: str, over: dict, variant: dict | None = None):
    from research.risk_overlay.mapping import map_report

    state = proxy_state(proxy_dir)
    config = settings(**over)
    return [
        map_report(r, x, config, variant=variant)
        for r, x in zip(state["reports"], state["inputs"], strict=True)
    ], config


def _tier_overlay(session: date, tier: int, config, **fields):
    from engine.core.risk_overlay import SessionOverlay
    from research.risk_overlay.mapping import TIERS

    t = TIERS[tier]
    return SessionOverlay(
        session=session,
        pause=t.pause,
        buy_multiplier=t.buy_multiplier,
        exposure_ceiling=(
            max(t.exposure_ceiling, float(config.exposure_floor)) if t.exposure_ceiling else None
        ),
        supersedes=frozenset(config.supersedes),
        mode="enforce",
        tier=tier,
        mapping_id="probe",
        exempt=tuple(config.exempt),
        **fields,
    )


def _response(session: date, response: str, config, tier: int | None = None):
    """One response applied to a session: x0.75, x0.5, x0.25, a pause or a 50% ceiling."""
    from engine.core.risk_overlay import SessionOverlay

    fields: dict[str, Any] = {}
    if response == "pause":
        fields["pause"] = True
    elif response == "ceiling50":
        fields["exposure_ceiling"] = 0.5
    else:
        fields["buy_multiplier"] = float(response.lstrip("x"))
    return SessionOverlay(
        session=session,
        supersedes=frozenset(config.supersedes),
        mode="enforce",
        tier=tier,
        mapping_id="probe",
        exempt=tuple(config.exempt),
        **fields,
    )


def build_schedule(spec: dict, sessions: list[date]):
    """The OverlaySchedule `spec["schedule"]` describes, over `sessions`."""
    from engine.core.risk_overlay import OverlaySchedule
    from research.risk_overlay.archive import schedule_from_entries

    how = spec.get("schedule") or {"kind": "none"}
    kind = how["kind"]
    if kind == "none":
        return None
    proxy_dir = how.get("proxy")
    config = settings(**how.get("settings", {}))
    if kind == "constant":
        return OverlaySchedule([_response(d, how["response"], config) for d in sessions])
    if kind == "random":
        rng = random.Random(how["seed"])
        chosen = [d for d in sessions if rng.random() < how["share"]]
        return OverlaySchedule([_response(d, how["response"], config) for d in chosen])
    if kind == "dates":
        return OverlaySchedule(
            [_response(date.fromisoformat(d), how["response"], config) for d in how["dates"]]
        )
    if kind == "proxy":
        variant = {k: how[k] for k in ("thresholds_delta", "drop") if how.get(k)}
        mapped, config = proxy_mapped(proxy_dir, how.get("settings", {}), variant or None)
        state = proxy_state(proxy_dir)
        form = how.get("form", "graded")
        entries = []
        for m, received in zip(mapped, state["received"], strict=True):
            if m.abstained:
                continue
            overlay = m.overlay
            if form == "binary":
                overlay = replace(
                    overlay, pause=m.tier == 3, buy_multiplier=1.0, exposure_ceiling=None
                )
            elif form == "continuous":
                overlay = replace(
                    overlay,
                    pause=False,
                    exposure_ceiling=None,
                    buy_multiplier=round(max(0.0, 1.0 - (m.score or 0.0)), 4),
                )
            elif form == "ceiling":
                ceiling = {0: None, 1: 0.75, 2: 0.5, 3: 0.25}[m.tier or 0]
                overlay = replace(
                    overlay, pause=False, buy_multiplier=1.0, exposure_ceiling=ceiling
                )
            entries.append(
                {
                    "session": overlay.session.isoformat(),
                    "overlay": overlay.to_dict(),
                    "receipts": [{"received_at": received, "weekly_ceiling": m.weekly_ceiling}],
                }
            )
        schedule = schedule_from_entries(entries, sessions, config)
        if how.get("shift"):
            schedule = shifted(schedule, sessions, int(how["shift"]))
        return schedule
    if kind == "matrix":
        mapped, config = proxy_mapped(proxy_dir, {})
        return OverlaySchedule(
            [
                _response(m.overlay.session, how["response"], config, tier=m.tier)
                for m in mapped
                if not m.abstained and m.tier == how["row"]
            ]
        )
    if kind == "perturb":
        mapped, config = proxy_mapped(proxy_dir, LEVERS["tiers"])
        rng = random.Random(how.get("seed", 0))
        out = []
        for m in mapped:
            if m.abstained:
                continue
            tier = m.tier or 0
            if how["how"] == "random" and rng.random() < how["share"]:
                tier = rng.randrange(4)
            elif how["how"] == "inverted":
                tier = 3 - tier
            elif how["how"] in ("always3", "always0"):
                tier = int(how["how"][-1])
            out.append(_tier_overlay(m.overlay.session, tier, config))
        return OverlaySchedule(out)
    if kind == "advisory":
        mapped, config = proxy_mapped(proxy_dir, LEVERS["tiers"])
        rng = random.Random(how["seed"])
        out = []
        from engine.core.risk_overlay import SessionOverlay
        from engine.core.risk_report import regular_bounds

        for m in mapped:
            if m.abstained or m.tier != 3 or rng.random() >= how["follow"]:
                continue
            opens, closes = regular_bounds(m.overlay.session)
            delay = timedelta(minutes=how["delay"])
            if not how["delay"]:
                out.append(_tier_overlay(m.overlay.session, 3, config))
            else:
                window = (opens + delay, closes + timedelta(hours=4))
                out.append(
                    SessionOverlay(
                        session=m.overlay.session,
                        blackouts=(window,),
                        supersedes=frozenset(config.supersedes),
                        mode="enforce",
                        tier=3,
                        mapping_id="probe",
                        exempt=tuple(config.exempt),
                    )
                )
        return OverlaySchedule(out)
    if kind == "synthetic":
        from research.risk_overlay.synthetic import Knobs, synthetic_schedule

        state = proxy_state(proxy_dir)
        knobs = Knobs(**how["knobs"])
        return synthetic_schedule(
            state["reports"],
            state["inputs"],
            state["received"],
            truth_state(proxy_dir),
            knobs,
            config,
        )
    raise ValueError(f"unknown schedule kind {kind!r}")


def shifted(schedule, sessions: list[date], offset: int):
    """`schedule`'s overlays moved `offset` sessions along `sessions`, wrapping."""
    from engine.core.risk_overlay import OverlaySchedule

    position = {d: i for i, d in enumerate(sessions)}
    out = []
    for session, overlay in schedule.items():
        if session not in position:
            continue
        target = sessions[(position[session] + offset) % len(sessions)]
        moved = replace(
            overlay,
            session=target,
            blackouts=tuple(
                (
                    s + (datetime.combine(target, time()) - datetime.combine(session, time())),
                    e + (datetime.combine(target, time()) - datetime.combine(session, time())),
                )
                for s, e in overlay.blackouts
            ),
        )
        out.append(moved)
    return OverlaySchedule(out)


# --------------------------------------------------------------- running


def _attribution(sim_result, frame) -> dict:
    """Per session: the lots it bought, the share sold within 5 and 21
    sessions, and how many were still open at the end."""
    import pandas as pd

    blotter = sim_result.trade_blotter
    if blotter is None or blotter.empty or "lot_id" not in blotter:
        return {}
    day = pd.to_datetime(blotter["timestamp"], utc=True).dt.tz_convert(du.TZ).dt.date
    sessions = sorted(set(pd.DatetimeIndex(frame.index).tz_convert(du.TZ).date))
    position = {d: i for i, d in enumerate(sessions)}
    buys = blotter[blotter["side"] == "buy"].assign(day=day)
    sells = blotter[blotter["side"] != "buy"].assign(day=day)
    sold_at = sells.groupby("lot_id")["day"].min().to_dict()
    out: dict[str, dict] = {}
    for session, group in buys.groupby("day"):
        lots = list(group["lot_id"])
        spans = [
            position[sold_at[lot]] - position[session] if lot in sold_at else None for lot in lots
        ]
        out[str(session)] = {
            "lots": len(lots),
            "within_5": sum(1 for s in spans if s is not None and s <= 5) / len(lots),
            "within_21": sum(1 for s in spans if s is not None and s <= 21) / len(lots),
            "open_at_end": sum(1 for s in spans if s is None),
        }
    return out


def run(spec: dict) -> dict:
    import pandas as pd

    def prepare(kwargs: dict, frame) -> None:
        sessions = sorted(set(pd.DatetimeIndex(frame.index).tz_convert(du.TZ).date))
        schedule = build_schedule(spec, sessions)
        if schedule is not None:
            manager = copy.copy(kwargs["risk_manager"])
            manager.set_overlay(schedule)
            kwargs["risk_manager"] = manager

    def on_result(sim_result, row, frame, out) -> None:
        out["overlay"] = {k: row.get(k) for k in OVERLAY_KEYS if k in row}
        if spec.get("attribution"):
            out["attribution"] = _attribution(sim_result, frame)

    row = du.run_one(spec, prepare=prepare, on_result=on_result)
    if du._ok(row):
        row["halves"] = {label: du.window_metrics(row, start, end) for label, start, end in HALVES}
        for half in row["halves"].values():
            half.pop("years", None)
        if not spec.get("keep_equity"):
            row.pop("equity", None)
    return row


# --------------------------------------------------------------- the plan


def _spec(stage: str, book: str, name: str, schedule: dict | None, **meta) -> dict:
    return {
        "stage": stage,
        "name": du._name(stage, book, name),
        "fund": FUND,
        "config": book_config(book),
        "schedule": schedule or {"kind": "none"},
        "meta": {"book": book, **meta},
    }


def plan(stage: str, book: str, proxy: str, out_dir: Path) -> list[dict]:
    p = {"proxy": proxy}
    specs: list[dict] = [_spec(stage, book, "none", None, form="none", keep_equity=True)]
    specs[0]["keep_equity"] = True
    if stage == "tiers":
        for response in ("x1.0", "x0.75", "x0.5", "x0.25", "ceiling50"):
            specs.append(
                _spec(
                    stage,
                    book,
                    response,
                    {"kind": "constant", "response": response},
                    response=response,
                )
            )
        specs.append(
            _spec(
                stage,
                book,
                "pause random 13%",
                {"kind": "random", "share": 0.13, "seed": 1, "response": "pause"},
                response="pause13",
            )
        )
    elif stage == "attribution":
        specs = [_spec(stage, book, "none", None)]
        specs[0]["attribution"] = True
    elif stage == "oracle":
        labels = load_attribution(out_dir, book)
        ranked = sorted(labels, key=lambda d: (labels[d]["within_21"], -labels[d]["lots"]))
        for share in (0.05, 0.10, 0.20):
            worst = ranked[: max(1, int(len(ranked) * share))]
            for response in ("pause", "x0.5"):
                specs.append(
                    _spec(
                        stage,
                        book,
                        f"worst {share:.0%} {response}",
                        {"kind": "dates", "dates": worst, "response": response},
                        share=share,
                        response=response,
                    )
                )
    elif stage == "matrix":
        for row in (0, 1, 2, 3):
            for response in ("x0.75", "x0.5", "x0.25", "pause"):
                specs.append(
                    _spec(
                        stage,
                        book,
                        f"tier{row} {response}",
                        {"kind": "matrix", "row": row, "response": response, **p},
                        row=row,
                        response=response,
                    )
                )
    elif stage == "proxy":
        for form in ("binary", "graded", "continuous", "ceiling"):
            specs.append(
                _spec(
                    stage,
                    book,
                    form,
                    {"kind": "proxy", "form": form, "settings": LEVERS["tiers"], **p},
                    form=form,
                )
            )
    elif stage == "spacing":
        for exponent in (0.5, 1.0):
            for top in (2.0, 4.0):
                for follows in (False, True):
                    sp = {
                        "enabled": True,
                        "exponent": exponent,
                        "max_multiplier": top,
                        "target_follows": follows,
                    }
                    specs.append(
                        _spec(
                            stage,
                            book,
                            f"B e{exponent} max{top} follow={follows}",
                            {
                                "kind": "proxy",
                                "settings": {**LEVERS["spacing"], "spacing": sp},
                                **p,
                            },
                            exponent=exponent,
                            top=top,
                            follows=follows,
                        )
                    )
        specs.append(
            _spec(
                stage,
                book,
                "B + tiers",
                {"kind": "proxy", "settings": {"daily": True, "weekly": {"enabled": False}}, **p},
                combo=True,
            )
        )
    elif stage == "weekly":
        for horizon in ("next_month", "next_quarter", "max"):
            for slope in (0.25, 0.5, 1.0):
                wk = {"enabled": True, "horizon": horizon, "slope": slope}
                specs.append(
                    _spec(
                        stage,
                        book,
                        f"G {horizon} slope {slope}",
                        {"kind": "proxy", "settings": {**LEVERS["weekly"], "weekly": wk}, **p},
                        horizon=horizon,
                        slope=slope,
                    )
                )
        specs.append(
            _spec(
                stage,
                book,
                "G every five sessions",
                {
                    "kind": "proxy",
                    "settings": {
                        **LEVERS["weekly"],
                        "weekly": {"enabled": True, "reset": "five_sessions"},
                    },
                    **p,
                },
                reset="five_sessions",
            )
        )
        specs.append(
            _spec(
                stage,
                book,
                "all levers",
                {"kind": "proxy", "settings": LEVERS["all"], **p},
                combo=True,
            )
        )
    elif stage == "null":
        rng = random.Random(NULL_SEED)
        offsets = [rng.randrange(60, 2400) for _ in range(NULL_SHIFTS)]
        for lever in ("tiers", "spacing", "weekly"):
            base = {"kind": "proxy", "settings": LEVERS[lever], **p}
            specs.append(_spec(stage, book, f"{lever} real", base, lever=lever, shift="real"))
            for i, offset in enumerate(offsets):
                specs.append(
                    _spec(
                        stage,
                        book,
                        f"{lever} shift {i:02d}",
                        {**base, "shift": offset},
                        lever=lever,
                        shift=i,
                    )
                )
    elif stage == "robust":
        from research.risk_overlay import mapping

        for delta in (-0.05, 0.05):
            specs.append(
                _spec(
                    stage,
                    book,
                    f"thresholds {delta:+.2f}",
                    {"kind": "proxy", "settings": LEVERS["tiers"], "thresholds_delta": delta, **p},
                    delta=delta,
                )
            )
        for component in mapping.WEIGHTS:
            specs.append(
                _spec(
                    stage,
                    book,
                    f"without {component}",
                    {"kind": "proxy", "settings": LEVERS["tiers"], "drop": component, **p},
                    drop=component,
                )
            )
        specs.append(
            _spec(
                stage,
                book,
                "reversals not exempt",
                {"kind": "proxy", "settings": {**LEVERS["tiers"], "exempt": []}, **p},
                exempt=False,
            )
        )
    elif stage == "stress":
        from tools import stress_paths

        for scenario in (*stress_paths.SCENARIOS, "top"):
            for label, schedule in (
                ("none", None),
                ("tiers", {"kind": "proxy", "settings": LEVERS["tiers"], **p}),
            ):
                spec = _spec(
                    stage, book, f"{scenario} {label}", schedule, stress=scenario, form=label
                )
                spec["stress"] = scenario
                specs.append(spec)
    elif stage == "perturb":
        for share in (0.10, 0.25, 0.50):
            specs.append(
                _spec(
                    stage,
                    book,
                    f"random {share:.0%}",
                    {"kind": "perturb", "how": "random", "share": share, "seed": 3, **p},
                    how="random",
                    share=share,
                )
            )
        for how in ("inverted", "always3", "always0"):
            specs.append(_spec(stage, book, how, {"kind": "perturb", "how": how, **p}, how=how))
    elif stage == "catalysts":
        for minutes in (10, 15, 30):
            specs.append(
                _spec(
                    stage,
                    book,
                    f"blackout {minutes}m",
                    {
                        "kind": "proxy",
                        "settings": {
                            "daily": False,
                            "spacing": {"enabled": False},
                            "weekly": {"enabled": False},
                            "blackout_minutes": minutes,
                        },
                        **p,
                    },
                    minutes=minutes,
                )
            )
    elif stage == "priority":
        for label, supersedes in (
            ("both", ["governor", "event_boosts"]),
            ("governor", ["governor"]),
            ("neither", []),
        ):
            specs.append(
                _spec(
                    stage,
                    book,
                    f"supersedes {label}",
                    {
                        "kind": "proxy",
                        "settings": {**LEVERS["tiers"], "supersedes": supersedes},
                        **p,
                    },
                    supersedes=label,
                )
            )
    elif stage == "advisory":
        for follow in (0.5, 0.8, 1.0):
            for delay in (0, 30, 90):
                for seed in range(SEEDS):
                    specs.append(
                        _spec(
                            stage,
                            book,
                            f"follow {follow} after {delay}m seed {seed}",
                            {
                                "kind": "advisory",
                                "follow": follow,
                                "delay": delay,
                                "seed": seed,
                                **p,
                            },
                            follow=follow,
                            delay=delay,
                            seed=seed,
                        )
                    )
    elif stage == "accuracy":
        lever_settings = {**LEVERS, "advisory": LEVERS["tiers"]}
        for lever in ("tiers", "spacing", "weekly", "all"):
            for family, values in (
                ("mixture", ACCURACIES),
                ("noisy", ACCURACIES),
                ("proxy+", LAMBDAS),
            ):
                for accuracy in values:
                    for seed in range(SEEDS):
                        knobs = {"family": family, "accuracy": accuracy, "seed": seed}
                        specs.append(
                            _spec(
                                stage,
                                book,
                                f"{lever} {family} {accuracy} seed {seed}",
                                {
                                    "kind": "synthetic",
                                    "knobs": knobs,
                                    "settings": lever_settings[lever],
                                    **p,
                                },
                                lever=lever,
                                family=family,
                                accuracy=accuracy,
                                seed=seed,
                            )
                        )
        for name, knob in KNOBS.items():
            for accuracy in KNOB_ACCURACIES:
                for seed in range(SEEDS):
                    knobs = {"family": "noisy", "accuracy": accuracy, "seed": seed, **knob}
                    specs.append(
                        _spec(
                            stage,
                            book,
                            f"all {name} {accuracy} seed {seed}",
                            {"kind": "synthetic", "knobs": knobs, "settings": LEVERS["all"], **p},
                            lever="all",
                            knob=name,
                            family="noisy",
                            accuracy=accuracy,
                            seed=seed,
                        )
                    )
    else:
        raise SystemExit(f"unknown stage {stage!r}")
    return specs


def load_attribution(out_dir: Path, book: str) -> dict:
    for row in du.load_results(out_dir):
        if (
            row.get("stage") == "attribution"
            and row["meta"].get("book") == book
            and row.get("attribution")
        ):
            return row["attribution"]
    raise SystemExit(f"no attribution for {book} in {out_dir}: run --stage attribution first")


# --------------------------------------------------------------- the AUC check


def auc(scores: list[float], bad: list[bool]) -> float | None:
    """P(a bad session scores above a good one), ties half."""
    pos = [s for s, b in zip(scores, bad, strict=True) if b]
    neg = [s for s, b in zip(scores, bad, strict=True) if not b]
    if not pos or not neg:
        return None
    from scipy import stats

    ranks = stats.rankdata(pos + neg)
    return float((sum(ranks[: len(pos)]) - len(pos) * (len(pos) + 1) / 2) / (len(pos) * len(neg)))


def auc_table(proxy: str, out_dir: Path, book: str) -> dict:
    mapped, _config = proxy_mapped(proxy, {})
    labels = load_attribution(out_dir, book)
    median = statistics.median(v["within_21"] for v in labels.values()) if labels else 0.0
    by_year: dict[str, tuple[list, list]] = {}
    for m in mapped:
        label = labels.get(m.overlay.session.isoformat()) if m.overlay.session else None
        if label is None or m.score is None:
            continue
        year = str(m.overlay.session.year)
        scores, bad = by_year.setdefault(year, ([], []))
        scores.append(m.score)
        bad.append(label["within_21"] < median)
    return {year: auc(*pair) for year, pair in sorted(by_year.items())}


# --------------------------------------------------------------- the report


def _calmar(m: dict) -> float:
    value = m.get("calmar")
    return float(value) if value is not None and math.isfinite(value) else float("nan")


def _delta(row: dict, base: dict) -> dict:
    m, b = row["metrics"], base["metrics"]
    return {
        "return": m["cagr"] - b["cagr"],
        "dd": m["max_dd"] - b["max_dd"],
        "calmar": _calmar(m) - _calmar(b),
        "halves": {
            label: _calmar(row["halves"][label]) - _calmar(base["halves"][label])
            for label in row.get("halves", {})
            if label in base.get("halves", {})
        },
    }


TABLE_ROWS = 60


def _base(rows: list[dict], stage: str, book: str) -> dict | None:
    """The stage's run with no overlay on the real path ("<stage> <book>
    none"), else any run with none. Results arrive in the order they
    finish, so the first `none` of the stress stage can be a stress path's."""
    named = f"{stage} {book} none" if stage else None
    return next((r for r in rows if named and r.get("name") == named), None) or next(
        (r for r in rows if r["meta"].get("form") == "none" and not r["meta"].get("stress")), None
    )


def advisory_summary(rows: list[dict], base: dict) -> list[str]:
    """The operator model by follow-through and delay: each setting's seeds
    averaged against no overlay (the table above lists runs, not settings)."""
    groups: dict[tuple, list[dict]] = {}
    for r in rows:
        meta = r["meta"]
        if "follow" in meta:
            groups.setdefault((meta["follow"], meta.get("delay", 0)), []).append(r)
    if not groups:
        return []
    b = base["metrics"]
    out = [
        "| follows | after | seeds | d return | d max DD | d Calmar | seeds better |",
        "|---|---|---|---|---|---|---|",
    ]
    for (follow, delay), runs in sorted(groups.items()):
        d_return = statistics.mean(r["metrics"]["cagr"] - b["cagr"] for r in runs)
        d_dd = statistics.mean(r["metrics"]["max_dd"] - b["max_dd"] for r in runs)
        d_calmar = [_calmar(r["metrics"]) - _calmar(b) for r in runs]
        better = sum(1 for d in d_calmar if d > 0)
        out.append(
            f"| {follow:.0%} | {delay} min | {len(runs)} | {d_return:+.2f} pts | {d_dd:+.2f} pts "
            f"| {statistics.mean(d_calmar):+.3f} | {better} of {len(runs)} |"
        )
    return out


def report(out_dir: Path) -> str:
    rows = [r for r in du.load_results(out_dir) if du._ok(r)]
    lines = ["# Risk overlay measurement", ""]
    for book in BOOKS:
        mine = [r for r in rows if r["meta"].get("book") == book]
        if not mine:
            continue
        lines += [f"## {book}", ""]
        for stage in dict.fromkeys(r["stage"] for r in mine):
            if stage == "attribution":
                continue  # its labels feed the oracle and the AUC check
            stage_rows = [r for r in mine if r["stage"] == stage and "cagr" in r["metrics"]]
            if stage == "accuracy":  # results.jsonl keeps runs of retired knobs too
                stage_rows = [r for r in stage_rows if r["meta"].get("knob") in (None, *KNOBS)]
            base = _base(stage_rows, stage, book) or _base(mine, "", book)
            if base is None:
                continue
            lines += [
                f"### {stage}",
                "",
                "| run | CAGR | max DD | Calmar | d Calmar | 2017-21 | 2022 on |",
                "|---|---|---|---|---|---|---|",
            ]
            for r in stage_rows[:TABLE_ROWS]:
                d = _delta(r, base)
                m = r["metrics"]
                halves = " | ".join(
                    f"{d['halves'].get(label, float('nan')):+.2f}" for label, *_ in HALVES
                )
                lines.append(
                    f"| {r['name']} | {m['cagr']:.1f}% | {m['max_dd']:.1f}% | {_calmar(m):.2f} | {d['calmar']:+.2f} | {halves} |"
                )
            if len(stage_rows) > TABLE_ROWS:
                lines.append(
                    f"\n*The first {TABLE_ROWS} of {len(stage_rows)} runs; every run is in "
                    "results.jsonl, and the lines below count them all.*"
                )
            if stage == "advisory":
                lines += ["", *advisory_summary(stage_rows, base)]
            if stage == "stress":
                for r in stage_rows:
                    if r["meta"].get("form") != "tiers":
                        continue
                    pair = next(
                        (
                            x
                            for x in stage_rows
                            if x["meta"].get("form") == "none"
                            and x["meta"].get("stress") == r["meta"].get("stress")
                        ),
                        None,
                    )
                    if pair:
                        lines.append(
                            f"\n{r['meta']['stress']}: the tiers move max DD by {r['metrics']['max_dd'] - pair['metrics']['max_dd']:+.1f} points."
                        )
            if stage == "null":
                for lever in ("tiers", "spacing", "weekly"):
                    real = next(
                        (
                            r
                            for r in stage_rows
                            if r["meta"].get("lever") == lever and r["meta"].get("shift") == "real"
                        ),
                        None,
                    )
                    nulls = [
                        r
                        for r in stage_rows
                        if r["meta"].get("lever") == lever
                        and isinstance(r["meta"].get("shift"), int)
                    ]
                    if real and nulls:
                        beaten = sum(
                            1 for n in nulls if _calmar(real["metrics"]) > _calmar(n["metrics"])
                        )
                        lines.append(
                            f"\n{lever}: the real schedule beats {beaten} of {len(nulls)} shifted copies on Calmar."
                        )
            if stage == "accuracy":
                lines += ["", *accuracy_curves(stage_rows, base), "", *knob_table(stage_rows, base)]
            lines.append("")
    return "\n".join(lines)


def _quantile(sorted_values: list[float], p: float) -> float:
    return sorted_values[min(len(sorted_values) - 1, int(p * len(sorted_values)))]


def accuracy_curves(rows: list[dict], base: dict) -> list[str]:
    """Median d Calmar (10th-90th percentile) by lever, family and accuracy,
    and each lever's break-even accuracy rho* and rho*90 on the noisy family."""
    out = [
        "| lever | family | accuracy | median d Calmar | p10 | p90 |",
        "|---|---|---|---|---|---|",
    ]
    groups: dict[tuple, list[float]] = {}
    for r in rows:
        meta = r["meta"]
        if meta.get("knob"):
            continue
        key = (meta.get("lever"), meta.get("family"), meta.get("accuracy"))
        groups.setdefault(key, []).append(_delta(r, base)["calmar"])
    breakeven: dict[str, tuple[float | None, float | None]] = {}
    for key in sorted(groups, key=lambda k: (str(k[0]), str(k[1]), float(k[2] or 0))):
        values = sorted(groups[key])
        out.append(
            f"| {key[0]} | {key[1]} | {key[2]} | {statistics.median(values):+.3f} | {_quantile(values, 0.1):+.3f} | {_quantile(values, 0.9):+.3f} |"
        )
        lever, family, accuracy = key
        if family == "noisy":
            star, star90 = breakeven.get(lever, (None, None))
            if star is None and statistics.median(values) > 0:
                star = accuracy
            if star90 is None and _quantile(values, 0.1) > 0:
                star90 = accuracy
            breakeven[lever] = (star, star90)
    out.append("")
    for lever, (star, star90) in breakeven.items():
        out.append(f"{lever}: rho* = {star}, rho*90 = {star90}")
    return out


def knob_table(rows: list[dict], base: dict) -> list[str]:
    """The error knobs (all three levers, the noisy family): each knob's
    median d Calmar beside plain noise at the same accuracy."""

    def median_of(select) -> str:
        values = [_delta(r, base)["calmar"] for r in rows if select(r["meta"])]
        return f"{statistics.median(values):+.3f}" if values else "-"

    knobs = [k for k in KNOBS if any(r["meta"].get("knob") == k for r in rows)]
    if not knobs:
        return []
    out = [
        "| knob | " + " | ".join(f"rho {a}" for a in KNOB_ACCURACIES) + " |",
        "|---|" + "---|" * len(KNOB_ACCURACIES),
    ]
    plain = [
        median_of(
            lambda m, a=a: (
                m.get("lever") == "all"
                and m.get("family") == "noisy"
                and m.get("accuracy") == a
                and not m.get("knob")
            )
        )
        for a in KNOB_ACCURACIES
    ]
    out.append("| none | " + " | ".join(plain) + " |")
    for knob in knobs:
        cells = [
            median_of(lambda m, a=a, k=knob: m.get("knob") == k and m.get("accuracy") == a)
            for a in KNOB_ACCURACIES
        ]
        out.append(f"| {knob} | " + " | ".join(cells) + " |")
    return out


# --------------------------------------------------------------- main


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--stage")
    parser.add_argument("--book", choices=sorted(BOOKS), action="append")
    parser.add_argument(
        "--proxy", type=Path, help="the proxy archive (tools/build_proxy_reports.py --out)"
    )
    parser.add_argument("--out", type=Path)
    parser.add_argument("--jobs", type=int, default=8)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--report", type=Path)
    args = parser.parse_args(argv)
    if args.report:
        print(report(args.report))
        return 0
    if not (args.stage and args.out and args.proxy):
        parser.error("--stage, --proxy and --out are required (or --report DIR)")
    args.out.mkdir(parents=True, exist_ok=True)
    books = args.book or list(BOOKS)
    if args.stage == "auc":
        for book in books:
            print(book, json.dumps(auc_table(str(args.proxy), args.out, book)))
        return 0
    stages = (
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
        ]
        if args.stage == "all"
        else [args.stage]
    )
    for stage in stages:
        specs = [s for book in books for s in plan(stage, book, str(args.proxy), args.out)]
        done = {r["name"] for r in du.load_results(args.out)}
        todo = [s for s in specs if s["name"] not in done]
        print(f"{stage}: {len(specs)} runs, {len(todo)} to do", flush=True)
        if args.dry_run or not todo:
            continue
        with (
            ProcessPoolExecutor(max_workers=args.jobs) as pool,
            (args.out / "results.jsonl").open("a") as sink,
        ):
            futures = {pool.submit(run, spec): spec for spec in todo}
            for i, future in enumerate(as_completed(futures), 1):
                spec = futures[future]
                try:
                    row = future.result()
                except Exception as exc:  # one failed run is a row, not a stopped probe
                    row = {
                        **{k: spec[k] for k in ("stage", "name", "fund", "meta")},
                        "error": f"{type(exc).__name__}: {exc}",
                    }
                sink.write(json.dumps(row, default=str) + "\n")
                sink.flush()
                if i % 20 == 0 or i == len(todo):
                    print(f"  {stage}: {i}/{len(todo)}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
