"""
apply_risk_report and clear_risk_report, as the trader applies them.

The Live page previews a report (server/live_control.py, which writes
nothing) and queues `apply_risk_report` for each deployment chosen. The
TRADER -- the running loop between ticks, or the market-hours supervisor
between sessions (engine/trading/operator_control.py) -- claims it and calls
the handler here, which parses and maps the report AGAIN, never trusting the
server's parse, and writes risk_reports/<session>.json
(research/risk_overlay/archive.py).

--------------------------------------------------------------------
THE RULES (docs/daily_risk_report_plan.md, "Getting a report in")

  one session       a report is for exactly one session: the one after its
                    as_of's evening (engine/core/risk_report.target_session)
  before it opens   a newer report replaces the old one
  after it opens    one that tightens applies at the next tick; one that
                    would loosen is archived and not applied. "Opens" is the
                    deployment's first traded window: 07:00 ET for a
                    Fidelity deployment that trades the pre-market
  never resumes     a report never touches the circuit breaker: an operator
                    pause or a halt wins whatever the report says
  real money        takes one report a session
  clearing          only before the session opens: afterwards it would loosen

In advisory mode the overlay is archived and shown, and nothing trades
differently; the handler says so in its result.
"""

from __future__ import annotations

import time
from collections.abc import Callable
from datetime import UTC, date, datetime
from typing import Any

from engine.core.config import BacktestConfig
from engine.core.risk_overlay import NEUTRAL, SessionOverlay, neutral_for
from engine.core.risk_report import RiskReport, parse_report, regular_bounds
from engine.core.venue_sessions import VENUES, VenueCalendar
from research.risk_overlay.archive import ReportArchive
from research.risk_overlay.mapping import Mapped, MappingInputs, map_report

InputsFor = Callable[[RiskReport, date, datetime], tuple[MappingInputs, list[str]]]


def first_window(config: BacktestConfig, session: date) -> datetime:
    """When `session` opens for this deployment: its first traded window."""
    venue = config.live.broker if config.live.broker in VENUES else "alpaca"
    span = VenueCalendar(venue, config.live.traded_sessions).day_span(session)
    return span[0].astimezone(UTC) if span else regular_bounds(session)[0]


def _receipt(
    command, report: RiskReport, mapped: Mapped, at: datetime, outcome: str, detail: str
) -> dict:
    return {
        "sha256": report.sha256,
        "received_at": at.isoformat(),
        "session": report.session.isoformat(),
        "operator": command.operator,
        "client": command.client,
        "command_id": command.id,
        "outcome": outcome,
        "detail": detail,
        "tier": mapped.tier,
        "abstained": mapped.abstained,
        "weekly_ceiling": mapped.weekly_ceiling,
    }


def risk_report_handlers(
    config: BacktestConfig,
    *,
    archive: ReportArchive,
    inputs_for: InputsFor,
    clock: Callable[[], float] = time.time,
    on_change: Callable[[date], None] | None = None,
) -> dict[str, Callable[[Any], str]]:
    """The two commands, for the trader's ControlApplier. `inputs_for(report,
    session, received_at)` gives the mapping's inputs (inputs.build_inputs
    with the trader's own closes); `on_change(session)` tells a running loop
    to read its session's overlay again."""
    from engine.trading.operator_control import CommandRejected

    settings = config.risk.overlay
    paper = bool(config.live.paper_trading)
    symbol = config.backtest.symbol.upper()

    def apply(command) -> str:
        if settings is None:
            raise CommandRejected(f"its config has no risk.overlay: {symbol} takes no reports")
        audit = parse_report(command.args.get("report"))
        if not audit.ok:
            listed = "; ".join(f"{f.where}: {f.message}" for f in audit.errors[:6])
            more = len(audit.errors) - 6
            raise CommandRejected(
                f"the report does not pass the audit ({len(audit.errors)} problem(s)): {listed}"
                + (f"; and {more} more" if more > 0 else "")
            )
        report = audit.require()
        session = report.session
        now = datetime.fromtimestamp(clock(), UTC)
        if now >= regular_bounds(session)[1]:
            raise CommandRejected(f"the {session} session it is for has already ended")
        inputs, notes = inputs_for(report, session, now)
        mapped = map_report(report, inputs, settings)
        existing = archive.current(session)
        receipts = list((existing or {}).get("receipts") or [])
        if existing is not None and existing.get("sha256") == report.sha256:
            return f"{session}: this report is already the one in force"
        if not paper and existing is not None:
            raise CommandRejected(
                f"real money takes one report a session, and {session} has one (received "
                f"{existing.get('received_at')} from {existing.get('operator')})"
            )
        opened = now >= first_window(config, session)
        in_force = (
            SessionOverlay.from_dict(existing["overlay"])
            if existing is not None and existing.get("overlay")
            else None
        )
        overlay = mapped.overlay
        outcome = "applied"
        if opened:
            base = in_force or NEUTRAL
            tightened = base.tightest(overlay)
            if tightened.no_looser_than(base) and base.no_looser_than(tightened):
                detail = (
                    f"{session} is already trading and this report would not tighten it: "
                    "archived, not applied"
                )
                if existing is not None:
                    receipts.append(_receipt(command, report, mapped, now, "not_applied", detail))
                    archive.update(session, receipts=receipts)
                else:
                    receipt = _receipt(command, report, mapped, now, "not_applied", detail)
                    archive.write(
                        session,
                        _entry(
                            command,
                            report,
                            mapped,
                            audit,
                            notes,
                            inputs,
                            now,
                            neutral_for(session, mode=settings.mode),
                            "not_applied",
                            [receipt],
                            settings,
                        ),
                    )
                return detail
            overlay, outcome = tightened, "tightened"
        words = overlay.describe()
        mode = (
            "advisory: shown and logged, trading as configured"
            if settings.mode == "advisory"
            else "enforced"
        )
        detail = f"{words} ({mode})"
        if mapped.abstained:
            detail = f"{session}: the mapping abstains -- {'; '.join(mapped.reasons)} ({mode})"
        receipts.append(_receipt(command, report, mapped, now, outcome, detail))
        archive.write(
            session,
            _entry(
                command,
                report,
                mapped,
                audit,
                notes,
                inputs,
                now,
                overlay,
                outcome,
                receipts,
                settings,
            ),
        )
        if on_change is not None:
            on_change(session)
        return detail

    def clear(command) -> str:
        if settings is None:
            raise CommandRejected(f"its config has no risk.overlay: {symbol} takes no reports")
        try:
            session = date.fromisoformat(str(command.args.get("session")))
        except ValueError as exc:
            raise CommandRejected("name the session to clear (YYYY-MM-DD)") from exc
        now = datetime.fromtimestamp(clock(), UTC)
        if archive.current(session) is None:
            return f"{session} has no report to clear"
        if now >= first_window(config, session):
            raise CommandRejected(
                f"{session} is already trading: clearing its report would loosen it, and a "
                "session's report may only tighten once it opens"
            )
        archive.clear(session, by=command.operator, reason=command.reason, at=now)
        if on_change is not None:
            on_change(session)
        return f"{session}'s report is withdrawn: it trades as configured"

    return {"apply_risk_report": apply, "clear_risk_report": clear}


def _entry(
    command,
    report: RiskReport,
    mapped: Mapped,
    audit,
    notes: list[str],
    inputs: MappingInputs,
    now: datetime,
    overlay: SessionOverlay,
    outcome: str,
    receipts: list[dict],
    settings,
) -> dict:
    return {
        "session": report.session.isoformat(),
        "source": "llm",
        "received_at": now.isoformat(),
        "operator": command.operator,
        "client": command.client,
        "command_id": command.id,
        "reason": command.reason,
        "schema_version": report.schema_version,
        "prompt_version": report.prompt_version,
        "model": report.model,
        "as_of": report.as_of.isoformat(),
        "sha256": report.sha256,
        "report": dict(report.raw),
        "mapping_id": mapped.mapping_id,
        "mode": settings.mode,
        "mapped": mapped.to_dict(),
        "overlay": overlay.to_dict(),
        "summary": overlay.describe(),
        "outcome": outcome,
        "findings": [f.to_dict() for f in audit.findings],
        "notes": list(notes),
        # What the mapping read besides the report: the scorecard's naive
        # baseline is the implied move (tools/score_risk_reports.py).
        "inputs": {
            "implied_move_pct": inputs.implied_move_pct,
            "implied_source": inputs.implied_source,
            "proxy_move_pct": inputs.proxy_move_pct,
            "last_close": inputs.last_close,
            "baseline_move_pct": inputs.baseline.move_pct if inputs.baseline else None,
            "calendar": [c.to_dict() for c in inputs.calendar],
        },
        "receipts": receipts,
    }


__all__ = ["first_window", "risk_report_handlers"]
