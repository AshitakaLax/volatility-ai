"""A paper trial's PaperTradingRecord, read from what the trader journaled.

Pure: the caller (server/algorithms.py) reads the journals and passes the
rows. Only what the trader actually records is counted, and only inside the
trial's WINDOW: from the moment its switch was applied to the moment another
algorithm took the deployment (None while it still trades). A deployment's
journals hold every algorithm it has run; without the window a trial would
be credited with another's fills.

The incident counters the promotion gate names (accounting discrepancies,
duplicate-order incidents, no-loss violations, unhandled exceptions) come
from the trader's incidents journal (engine/trading/control_inbox.py). A
zero nobody measured would pass a gate it should not, so they count as
MEASURED only when every session the trial traded carries the journal's
"watching" row -- the trader that ran it journaled incidents. A session
without one (a build from before the journal) leaves them `unmeasured`, and
the verdict fails closed on them (`evaluate`). A reconciliation halt is
measured: the trader's status says it.
"""

from __future__ import annotations

from dataclasses import asdict, replace
from datetime import UTC, date, datetime

from engine.core.trading_calendar import EASTERN
from engine.promotion import PaperTradingRecord, PromotionCriteria, evaluate_promotion
from engine.trading.control_inbox import INCIDENT_KINDS, WATCHING

# Counters with no journal behind them unless the trader shows it watched,
# by the record field they would fill.
UNMEASURED = INCIDENT_KINDS


def _within(rows: list[dict], started_at: float, ended_at: float | None) -> list[dict]:
    return [
        row
        for row in rows
        if float(row.get("t", 0)) >= started_at
        and (ended_at is None or float(row.get("t", 0)) < ended_at)
    ]


def _session(row: dict) -> date:
    return datetime.fromtimestamp(float(row["t"]), UTC).astimezone(EASTERN).date()


def build_record(
    deployment_id: str,
    *,
    started_at: float,
    bars: list[dict],
    fills: list[dict],
    orders: list[dict],
    halted_for_reconciliation: bool,
    ended_at: float | None = None,
    incidents: list[dict] | None = None,
) -> PaperTradingRecord:
    """The trial's record from the rows journaled in its window (epoch
    seconds, ended_at exclusive). A day is a session with a bar; a decision
    is an order placed; an incident is a row of its kind."""
    sessions = {_session(row) for row in _within(bars, started_at, ended_at)}
    counted = dict.fromkeys(INCIDENT_KINDS, 0)
    for row in _within(incidents or [], started_at, ended_at):
        if row.get("kind") in counted:
            counted[row["kind"]] += 1
    return PaperTradingRecord(
        deployment_id=deployment_id,
        paper_trading_days=float(len(sessions)),
        decision_count=sum(
            1 for row in _within(orders, started_at, ended_at) if row.get("event") == "placed"
        ),
        fill_count=len(_within(fills, started_at, ended_at)),
        unresolved_reconciliations=1 if halted_for_reconciliation else 0,
        **counted,
    )


def unmeasured(
    *,
    started_at: float,
    bars: list[dict],
    incidents: list[dict] | None,
    ended_at: float | None = None,
) -> tuple[str, ...]:
    """The incident counters this window cannot vouch for: all of them unless
    every session it traded (a session with a bar) has a watching row, and
    none for a window with no session yet -- nothing traded, nothing to miss
    (the minimums fail that trial anyway)."""
    traded = {_session(row) for row in _within(bars, started_at, ended_at)}
    watched = {
        _session(row)
        for row in (incidents or [])
        if row.get("kind") == WATCHING and (ended_at is None or float(row["t"]) < ended_at)
    }
    return () if traded <= watched else UNMEASURED


def evaluate(
    record: PaperTradingRecord,
    criteria: PromotionCriteria | None = None,
    *,
    unmeasured: tuple[str, ...] = UNMEASURED,
) -> dict:
    """The gate's verdict as a plain dict (the `passed` key is what
    research/strategies/live_profiles.py reads). Counters nobody measured are
    listed and fail the trial: their zeros are not evidence."""
    shown = replace(record, **dict.fromkeys(unmeasured, 0))
    evaluation = evaluate_promotion(shown, criteria)
    failures = list(evaluation.failures) + [
        f"{name}: not measured (the trader did not journal it for every session of the trial)"
        for name in unmeasured
    ]
    return {
        "passed": evaluation.passed and not unmeasured,
        "failures": failures,
        "criteria": evaluation.criteria,
        "record": asdict(shown),
        "unmeasured": list(unmeasured),
        "manual": False,
    }
