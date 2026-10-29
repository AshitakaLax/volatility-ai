"""A paper trial's PaperTradingRecord, read from what the trader journaled.

Pure: the caller (server/algorithms.py) reads the journals and passes the
rows. Only what the trader actually records is counted. The incident
counters the promotion gate names (accounting discrepancies, duplicate-order
incidents, no-loss violations, unhandled exceptions) are not journaled
anywhere yet, and a zero nobody measured would pass a gate it should not, so
they are reported as `unmeasured` and the verdict fails closed on them
(`evaluate`). A reconciliation halt is measured: the trader's status says it.
"""

from __future__ import annotations

from dataclasses import asdict
from datetime import UTC, datetime

from engine.core.trading_calendar import EASTERN
from engine.promotion import PaperTradingRecord, PromotionCriteria, evaluate_promotion

# Counters with no journal behind them, by the record field they would fill.
UNMEASURED = (
    "accounting_discrepancies",
    "duplicate_order_incidents",
    "no_loss_violations",
    "unhandled_exceptions",
)


def _since(rows: list[dict], started_at: float) -> list[dict]:
    return [row for row in rows if float(row.get("t", 0)) >= started_at]


def build_record(
    deployment_id: str,
    *,
    started_at: float,
    bars: list[dict],
    fills: list[dict],
    orders: list[dict],
    halted_for_reconciliation: bool,
) -> PaperTradingRecord:
    """The trial's record from the rows journaled since it started (epoch
    seconds). A day is a session with a bar; a decision is an order placed."""
    sessions = {
        datetime.fromtimestamp(float(row["t"]), UTC).astimezone(EASTERN).date()
        for row in _since(bars, started_at)
    }
    return PaperTradingRecord(
        deployment_id=deployment_id,
        paper_trading_days=float(len(sessions)),
        decision_count=sum(1 for row in _since(orders, started_at) if row.get("event") == "placed"),
        fill_count=len(_since(fills, started_at)),
        unresolved_reconciliations=1 if halted_for_reconciliation else 0,
    )


def evaluate(record: PaperTradingRecord, criteria: PromotionCriteria | None = None) -> dict:
    """The gate's verdict as a plain dict (the `passed` key is what
    research/strategies/live_profiles.py reads). Counters nobody measures are
    listed and fail the trial: until the trader journals them, a paper trial
    cannot pass and a promotion needs the owner's explicit sign-off."""
    evaluation = evaluate_promotion(record, criteria)
    failures = list(evaluation.failures) + [
        f"{name}: not measured (the trader does not journal it yet)" for name in UNMEASURED
    ]
    return {
        "passed": evaluation.passed and not UNMEASURED,
        "failures": failures,
        "criteria": evaluation.criteria,
        "record": asdict(record),
        "unmeasured": list(UNMEASURED),
        "manual": False,
    }
