#!/usr/bin/env python
"""Score each night's risk report against what the session did, and whether
its suggestion was followed (docs/daily_risk_report_plan.md, "Scoring the
forecasts every night").

    python tools/score_risk_reports.py --all            # every deployment's scored sessions
    python tools/score_risk_reports.py --deployment paper-ultimate
    python tools/score_risk_reports.py --forecasts      # the forecast database's nightly step, now
    python tools/score_risk_reports.py --import tests/fixtures/risk_reports/*.json

A few months of reports give a P&L test no power; the forecast itself can be
scored every day. tools/track_live.py calls score_session() and followed()
for each tracked session that had a report and stores the result in the
session's row (`risk`); this tool summarises those rows. It reads the
tracking service's record and writes nothing.

--------------------------------------------------------------------
WHAT A SESSION'S SCORE SAYS

  coverage    whether the close-to-close return fell inside [p05, p95] (90%
              of sessions should) and [p25, p75] (50%)
  pit         where it fell in the report's distribution, interpolated
              between its quantiles: uniform when the report is calibrated
  pinball     the mean quantile (pinball) loss over the six quantiles, about
              the CRPS; and the same for a naive normal at the options
              index's implied move -- skill = 1 - loss / its loss
  move_ratio  |return| / expected_1d_move_pct
  week        the 5-day horizon against the close five sessions later, once
              that close exists

The summary adds, across sessions: the coverage rates, the mean skill with a
block-bootstrap interval, and ACCURACY on the scale the synthetic reports use
-- the rank correlation of expected_1d_move_pct with the realised |return|
(docs/daily_risk_report_plan.md, "Placing the real sources on the curve").

--------------------------------------------------------------------
WHETHER A SUGGESTION WAS FOLLOWED

Advisory mode trades the YAML; the owner acts with Pause buys. For a session
whose suggestion was a pause: `followed` when buying was paused by the first
window or within FOLLOW_MINUTES of it, `late` when a pause came later in the
session, `not_followed` when none did. Size, spacing and the weekly cap have
no button: `not_actionable`. In enforce mode: `enforced`.

--------------------------------------------------------------------
THE FORECAST DATABASE (research/risk_overlay/forecasts.py)

Every report the Live page checked, apart from any deployment. Its nightly
step -- run by tools/track_live.py after the warehouse refresh, or now with
--forecasts -- copies in each report a trader archived, records the closes
of each finished session that has a report (the warehouse's regular-hours
minute bars, the last bar at 15:45 Eastern or later, or a later session's
bars there: a close is written once, so a refresh cut off mid-day must not
leave a wrong one), and scores every report against its session. The
tracking rows above score against the trader's own bar journal; the
database scores against the warehouse, the same closes for every
deployment. --import stores report files by hand.
"""

from __future__ import annotations

import argparse
import json
import math
import random
import statistics
import sys
from collections.abc import Iterable, Mapping, Sequence
from datetime import UTC, date, datetime, timedelta
from datetime import time as clock_time
from itertools import pairwise
from pathlib import Path
from typing import Any

_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from engine.core.risk_report import QUANTILES, RiskReport, regular_bounds

FOLLOW_MINUTES = 30
LEVELS = {"p01": 0.01, "p05": 0.05, "p25": 0.25, "p75": 0.75, "p95": 0.95, "p99": 0.99}
# Standard normal quantiles at the six levels.
_Z = {"p01": -2.3263, "p05": -1.6449, "p25": -0.6745, "p75": 0.6745, "p95": 1.6449, "p99": 2.3263}
DEFAULT_OUT = _REPO_ROOT / "output" / "tracking"


def pinball(quantiles: Mapping[str, float], realised: float) -> float:
    """The mean pinball loss of `quantiles` (percent returns by level key)."""
    losses = []
    for key in QUANTILES:
        tau, q = LEVELS[key], float(quantiles[key])
        losses.append(max(tau * (realised - q), (tau - 1.0) * (realised - q)))
    return sum(losses) / len(losses)


def pit(quantiles: Mapping[str, float], realised: float) -> float:
    """Where `realised` falls in the distribution, interpolated linearly
    between the quantiles; the tails beyond p01/p99 are squeezed into
    [0, 0.01] and [0.99, 1]."""
    points = [(float(quantiles[k]), LEVELS[k]) for k in QUANTILES]
    if realised <= points[0][0]:
        return 0.0 if realised < points[0][0] else points[0][1]
    if realised >= points[-1][0]:
        return 1.0 if realised > points[-1][0] else points[-1][1]
    for (x0, p0), (x1, p1) in pairwise(points):
        if x0 <= realised <= x1:
            return p0 + (p1 - p0) * ((realised - x0) / (x1 - x0) if x1 > x0 else 0.0)
    return 0.5


def naive_quantiles(move_pct: float) -> dict[str, float]:
    """A normal centred on zero with the implied move as its sigma."""
    return {key: _Z[key] * move_pct for key in QUANTILES}


def score_session(
    report: RiskReport,
    *,
    prior_close: float | None,
    close: float | None,
    week_close: float | None = None,
    implied_move_pct: float | None = None,
) -> dict[str, Any] | None:
    """One session's score (module docstring), or None without its closes."""
    if not prior_close or not close:
        return None
    realised = 100.0 * (close / prior_close - 1.0)
    tomorrow = report.horizon("tomorrow")
    q = tomorrow.quantiles
    row: dict[str, Any] = {
        "return_pct": round(realised, 4),
        "in_90": q["p05"] <= realised <= q["p95"],
        "in_50": q["p25"] <= realised <= q["p75"],
        "pit": round(pit(q, realised), 4),
        "pinball": round(pinball(q, realised), 4),
        "expected_move_pct": report.expected_move_pct,
        "move_ratio": round(abs(realised) / report.expected_move_pct, 4),
    }
    if implied_move_pct:
        naive = pinball(naive_quantiles(implied_move_pct), realised)
        row["naive_pinball"] = round(naive, 4)
        row["skill"] = round(1.0 - row["pinball"] / naive, 4) if naive > 0 else None
    if week_close:
        week = 100.0 * (week_close / prior_close - 1.0)
        wq = report.horizon("next_week").quantiles
        row["week"] = {
            "return_pct": round(week, 4),
            "in_90": wq["p05"] <= week <= wq["p95"],
            "pinball": round(pinball(wq, week), 4),
        }
    return row


def followed(
    overlay: Mapping[str, Any] | None,
    commands: Iterable[Mapping[str, Any]],
    *,
    session: date,
    opens: datetime,
    mode: str = "advisory",
) -> dict[str, Any] | None:
    """Whether the session's suggestion was followed (module docstring).
    `commands` are the deployment's command rows (ControlInbox.history);
    `opens` its first traded window."""
    if not overlay:
        return None
    if mode == "enforce":
        return {"status": "enforced"}
    if not overlay.get("pause"):
        return {"status": "not_actionable"} if overlay.get("tier") else None
    ends = regular_bounds(session)[1]
    state_at_open = None
    paused_at = None
    for row in sorted(commands, key=lambda r: r.get("seq") or 0):
        if row.get("status") != "applied" or row.get("type") not in ("pause_buys", "resume_buys"):
            continue
        try:
            when = datetime.fromisoformat(str(row.get("finished_at")))
        except ValueError:
            continue
        if when.tzinfo is None:
            when = when.replace(tzinfo=UTC)
        if when < opens:
            state_at_open = row["type"]
        elif when < ends and row["type"] == "pause_buys" and paused_at is None:
            paused_at = when
    if state_at_open == "pause_buys":
        return {"status": "followed", "minutes": 0}
    if paused_at is not None:
        minutes = round((paused_at - opens).total_seconds() / 60.0, 1)
        return {"status": "followed" if minutes <= FOLLOW_MINUTES else "late", "minutes": minutes}
    return {"status": "not_followed"}


# --------------------------------------------------------------------
# Across sessions
# --------------------------------------------------------------------


def _ranks(values: Sequence[float]) -> list[float]:
    order = sorted(range(len(values)), key=lambda i: values[i])
    ranks = [0.0] * len(values)
    i = 0
    while i < len(order):
        j = i
        while j + 1 < len(order) and values[order[j + 1]] == values[order[i]]:
            j += 1
        for k in range(i, j + 1):
            ranks[order[k]] = (i + j) / 2.0
        i = j + 1
    return ranks


def spearman(x: Sequence[float], y: Sequence[float]) -> float | None:
    if len(x) < 3 or len(x) != len(y):
        return None
    rx, ry = _ranks(x), _ranks(y)
    try:
        return statistics.correlation(rx, ry)
    except statistics.StatisticsError:
        return None


def block_bootstrap(
    values: Sequence[float], *, block: int = 5, draws: int = 2000, seed: int = 0
) -> tuple[float, float] | None:
    """A 90% interval for the mean of `values` by the moving-block bootstrap."""
    n = len(values)
    if n < 2 * block:
        return None
    rng = random.Random(seed)
    means = []
    for _ in range(draws):
        sample: list[float] = []
        while len(sample) < n:
            start = rng.randrange(0, n - block + 1)
            sample.extend(values[start : start + block])
        means.append(sum(sample[:n]) / n)
    means.sort()
    return means[int(0.05 * draws)], means[int(0.95 * draws) - 1]


def summarize(scores: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    """Across scored sessions (module docstring)."""
    rows = [s for s in scores if s]
    if not rows:
        return {"sessions": 0}
    skills = [s["skill"] for s in rows if s.get("skill") is not None]
    accuracy = spearman(
        [s["expected_move_pct"] for s in rows], [abs(s["return_pct"]) for s in rows]
    )
    half_width = 1.645 / math.sqrt(len(rows)) if len(rows) > 3 else None
    return {
        "sessions": len(rows),
        "coverage_90": round(sum(1 for s in rows if s["in_90"]) / len(rows), 4),
        "coverage_50": round(sum(1 for s in rows if s["in_50"]) / len(rows), 4),
        "mean_pinball": round(statistics.fmean(s["pinball"] for s in rows), 4),
        "mean_skill": round(statistics.fmean(skills), 4) if skills else None,
        "skill_interval": block_bootstrap(skills),
        "accuracy_move": round(accuracy, 4) if accuracy is not None else None,
        "accuracy_interval_half_width": round(half_width, 3) if half_width else None,
        "mean_move_ratio": round(statistics.fmean(s["move_ratio"] for s in rows), 4),
    }


def load_scores(out: Path, deployment: str) -> list[dict]:
    path = out / deployment / "sessions.jsonl"
    scores = []
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError:
        return []
    for line in lines:
        try:
            row = json.loads(line)
        except ValueError:
            continue
        score = ((row.get("risk") or {}).get("score")) if isinstance(row, dict) else None
        if score:
            scores.append({"session": row.get("session"), **score})
    return scores


# --------------------------------------------------------------------
# The forecast database
# --------------------------------------------------------------------

REGULAR_OPEN = clock_time(9, 30)
REGULAR_CLOSE = clock_time(16, 0)
LATE_BAR = clock_time(15, 45)
NY = "America/New_York"


def session_closes(frame: Any) -> dict[date, float]:
    """Each finished session's regular-hours close from minute bars (a
    frame on a UTC index with a `close` column), by Eastern date. Finished:
    the last regular bar is at LATE_BAR or later, or a later session has
    bars (an early close)."""
    if frame is None or len(frame) == 0:
        return {}
    last: dict[date, tuple[Any, float]] = {}
    for moment, close in zip(frame.index.tz_convert(NY), frame["close"], strict=True):
        if not REGULAR_OPEN <= moment.time() < REGULAR_CLOSE:
            continue
        day = moment.date()
        if day not in last or moment >= last[day][0]:
            last[day] = (moment, float(close))
    days = sorted(last)
    return {
        day: last[day][1]
        for i, day in enumerate(days)
        if last[day][0].time() >= LATE_BAR or i < len(days) - 1
    }


def score_forecasts(store, now: datetime, *, load=None) -> dict[str, int]:
    """Record the closes of every finished session with a report, then
    score each report whose session has them. `load(symbol, since=...)`
    gives minute bars (default: engine.warehouse.bars.load_frame)."""
    import pandas as pd

    from engine.core.trading_calendar import previous_session

    if load is None:
        from engine.warehouse.bars import load_frame as load
    counts = {"closes": 0, "scored": 0, "waiting": 0}
    wanted: dict[str, list[date]] = {}
    for symbol, session in store.unclosed(now):
        wanted.setdefault(symbol, []).append(session)
    for symbol, sessions in wanted.items():
        start = previous_session(min(sessions)) - timedelta(days=7)
        closes = session_closes(load(symbol, since=pd.Timestamp(start.isoformat(), tz=NY)))
        for session in sessions:
            prior = previous_session(session)
            if session not in closes or prior not in closes:
                counts["waiting"] += 1
                continue
            store.record_close(
                symbol,
                session,
                close=closes[session],
                prior_session=prior,
                prior_close=closes[prior],
                source="warehouse",
                at=now,
            )
            counts["closes"] += 1
    for report, close in store.unscored():
        score = score_session(report, prior_close=close["prior_close"], close=close["close"])
        if score is not None:
            store.record_score(report.sha256, score, at=now)
            counts["scored"] += 1
    return counts


def collect_archives(store, deployments: Iterable[Any]) -> int:
    """Copy into the database every report a deployment's trader archived
    (each session's entry and those superseded), so an Apply the page did
    not record is not lost. Returns how many were new; one already there
    adds nothing, as its receipt is keyed by when the trader received it."""
    from research.risk_overlay.archive import ReportArchive
    from research.risk_overlay.forecasts import ForecastRefused

    added = 0
    for deployment in deployments:
        inbox = deployment.inbox()
        if inbox is None:
            continue
        archive = ReportArchive.in_control_dir(inbox.root)
        for entry in [*archive.entries(), *archive.superseded()]:
            raw = entry.get("report")
            if not isinstance(raw, Mapping):
                continue
            at = _moment(entry.get("received_at")) or _moment(entry.get("as_of"))
            if at is None:
                continue
            try:
                stored = store.record(
                    raw, via=f"archive:{deployment.id}", operator=entry.get("operator"), at=at
                )
            except ForecastRefused:
                continue
            added += int(stored["new"])
    return added


def _moment(text: Any) -> datetime | None:
    try:
        moment = datetime.fromisoformat(str(text))
    except ValueError:
        return None
    return moment if moment.tzinfo else moment.replace(tzinfo=UTC)


def import_reports(store, paths: Iterable[Path], *, operator: str) -> list[dict[str, Any]]:
    """Store report files by hand; a file that does not pass the audit is
    reported, not stored."""
    from research.risk_overlay.forecasts import ForecastRefused

    results = []
    for path in paths:
        try:
            stored = store.record(path.read_text(encoding="utf-8"), via="import", operator=operator)
        except ForecastRefused as exc:
            results.append({"file": str(path), "error": str(exc)})
            continue
        results.append({"file": str(path), **stored})
    return results


def describe_forecasts(store, limit: int = 20) -> list[str]:
    """The database's sessions, one line each, by symbol."""
    lines = []
    for symbol in store.symbols():
        for row in store.sessions(symbol, limit):
            q = row["quantiles"]
            band = f"90% {q['p05']:+.2f}%..{q['p95']:+.2f}%"
            actual = row["actual"]
            score = row["score"]
            if actual is None:
                said = "waiting for its close"
            else:
                where = (
                    "inside its middle 50%"
                    if score and score["in_50"]
                    else "inside its 90%"
                    if score and score["in_90"]
                    else "outside its 90%"
                )
                said = f"actual {actual['return_pct']:+.2f}%: {where}"
            lines.append(
                f"{symbol} {row['session']}  {band}  move {row['expected_move_pct']:.2f}%  {said}"
                f"  ({row['reports']} report(s), {row['sha256'][:12]})"
            )
    return lines


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    which = parser.add_mutually_exclusive_group(required=True)
    which.add_argument("--all", action="store_true")
    which.add_argument("--deployment")
    which.add_argument(
        "--forecasts",
        action="store_true",
        help="the forecast database's nightly step now (archived reports, closes, scores)",
    )
    which.add_argument(
        "--import",
        dest="import_files",
        nargs="+",
        type=Path,
        metavar="REPORT",
        help="store these report files in the forecast database",
    )
    parser.add_argument(
        "--out", type=Path, default=DEFAULT_OUT, help="the tracking service's --out"
    )
    parser.add_argument(
        "--db",
        type=Path,
        help="the forecast database (default: VAI_FORECAST_DB, else "
        "warehouse/forecasts/risk_reports.db)",
    )
    parser.add_argument("--operator", default="import", help="who --import records")
    args = parser.parse_args(argv)
    if args.forecasts or args.import_files:
        from research.risk_overlay.forecasts import ForecastStore

        store = ForecastStore(args.db)
        if args.import_files:
            failed = False
            for result in import_reports(store, args.import_files, operator=args.operator):
                if "error" in result:
                    failed = True
                    print(f"{result['file']}: NOT stored: {result['error']}")
                else:
                    print(
                        f"{result['file']}: {result['symbol']} {result['session']} "
                        f"{'stored' if result['new'] else 'already stored'} ({result['sha256'][:12]})"
                    )
            if failed:
                return 1
        else:
            from server import live_registry

            copied = collect_archives(store, live_registry.registry().values())
            counts = score_forecasts(store, datetime.now(UTC))
            print(
                f"{copied} archived report(s) copied in; {counts['closes']} close(s) recorded, "
                f"{counts['scored']} report(s) scored, {counts['waiting']} session(s) waiting"
            )
        print(f"{store.path}:")
        for line in describe_forecasts(store):
            print(f"  {line}")
        return 0
    if args.all:
        from server import live_registry

        names = list(live_registry.registry())
    else:
        names = [args.deployment]
    for name in names:
        summary = summarize(load_scores(args.out, name))
        print(f"{name}: {json.dumps(summary)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
