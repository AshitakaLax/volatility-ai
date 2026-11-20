"""
The trader's side of the risk report: the session's overlay, kept current.

cli.py builds one SessionRisk for a deployment whose config has a
risk.overlay. At the session's start it reads the session's report from
risk_reports/ and maps it AGAIN with the freshest outside data (the 07:30 ET
refresh may have moved VXN since the evening), composes the week's cap, and
records what it found in the archive entry (`start`). Each tick its status()
goes into status.json as `risk_overlay`: in force (enforce mode) or
suggested (advisory), the words, the report it came from -- or "no report:
trading as configured". A report applied mid-session (one that tightens)
refreshes it through on_change.

In advisory mode nothing here reaches the trading path: cli.py hands the
RiskManager and the step no overlay at all.
"""

from __future__ import annotations

import time
from collections.abc import Callable
from dataclasses import replace
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any

from engine.core.config import BacktestConfig
from engine.core.risk_overlay import SessionOverlay, neutral_for
from engine.core.risk_report import RiskReport, parse_report
from engine.core.trading_calendar import EASTERN, is_session, next_session
from research.risk_overlay.archive import ReportArchive, compose, session_overlay, week_cap
from research.risk_overlay.control import risk_report_handlers
from research.risk_overlay.inputs import build_inputs, closes_from_bars
from research.risk_overlay.mapping import MappingInputs, map_report

# Sessions of the trader's bar journal read for the realised volatility.
JOURNAL_SESSIONS = 11


def trading_session(moment: datetime) -> date:
    """The session a trader started at `moment` trades: today's, or the next."""
    day = moment.astimezone(EASTERN).date()
    return day if is_session(day) else next_session(day)


def trader_inputs(
    config: BacktestConfig,
    inbox,
    *,
    external_dir: str | Path | None = None,
) -> Callable[[RiskReport, date, datetime], tuple[MappingInputs, list[str]]]:
    """inputs_for() for the handlers: the deployment's own daily closes from
    its bar journal (`inbox`, a ControlInbox), the outside data, the
    engine's calendars."""

    def inputs_for(report: RiskReport, session: date, received_at: datetime):
        closes: list[float] = []
        if inbox is not None:
            try:
                bars = inbox.bars(JOURNAL_SESSIONS)
            except Exception:
                bars = []
            stamp = datetime.combine(session, datetime.min.time(), tzinfo=EASTERN).timestamp()
            closes = closes_from_bars(b for b in bars if float(b.get("t", 0)) < stamp)
        return build_inputs(
            config.backtest.symbol,
            session,
            received_at=received_at,
            closes=closes,
            external_dir=external_dir,
        )

    return inputs_for


class SessionRisk:
    """One deployment's overlay for the session it trades."""

    def __init__(
        self,
        config: BacktestConfig,
        control_dir: str | Path,
        *,
        inbox=None,
        external_dir: str | Path | None = None,
        clock: Callable[[], float] = time.time,
        log: Callable[[str], None] = print,
    ) -> None:
        if config.risk.overlay is None:
            raise ValueError("SessionRisk needs a config with risk.overlay")
        self.config = config
        self.settings = config.risk.overlay
        self.archive = ReportArchive.in_control_dir(control_dir)
        self.inbox = inbox
        self._inputs_for = trader_inputs(config, inbox, external_dir=external_dir)
        self._clock = clock
        self._log = log
        self.session: date | None = None
        self.overlay: SessionOverlay | None = None
        self.entry: dict | None = None
        self.notes: list[str] = []
        self.checked_at: str | None = None
        self.listeners: list[Callable[[SessionOverlay], None]] = []

    @property
    def mode(self) -> str:
        return self.settings.mode

    def now(self) -> datetime:
        return datetime.fromtimestamp(self._clock(), UTC)

    def start(self, session: date | None = None) -> SessionOverlay:
        """At the session's start: the archived report mapped again with the
        freshest inputs, the week's cap composed in, the result recorded."""
        now = self.now()
        self.session = session or trading_session(now)
        overlay, entry = session_overlay(self.archive, self.session, self.settings, as_of=now)
        self.notes = []
        if (
            entry is not None
            and entry.get("report")
            and entry.get("outcome") in ("applied", "tightened")
        ):
            rechecked = self._recheck(entry, now)
            if rechecked is not None:
                overlay = rechecked
        self._set(overlay, entry)
        if entry is not None:
            self.archive.update(
                self.session,
                start={
                    "at": now.isoformat(),
                    "overlay": overlay.to_dict(),
                    "summary": overlay.describe(),
                    "notes": list(self.notes),
                },
            )
        self._log(f"Risk report ({self.mode}): {self.describe()}")
        return overlay

    def _recheck(self, entry: dict, now: datetime) -> SessionOverlay | None:
        audit = parse_report(entry["report"])
        if not audit.ok:
            self.notes.append("its archived report no longer parses; trading as configured")
            return neutral_for(self.session, mode=self.mode, reasons=self.notes)
        report = audit.require()
        received = datetime.fromisoformat(entry["received_at"])
        inputs, notes = self._inputs_for(report, self.session, received)
        self.notes.extend(notes)
        mapped = map_report(report, inputs, self.settings)
        daily = mapped.overlay
        archived = SessionOverlay.from_dict(entry["overlay"])
        if entry.get("outcome") == "tightened" or self.opened(now):
            # A session already trading (a restart mid-session, or a report
            # that tightened it after the open) may tighten, never loosen.
            daily = archived.tightest(daily)
        cap, reasons = week_cap(self.archive.receipts(), self.session, self.settings, as_of=now)
        overlay = compose(daily, cap, reasons)
        if overlay.to_dict() != SessionOverlay.from_dict(entry["overlay"]).to_dict():
            self.notes.append("re-checked against the morning's outside data")
        return overlay

    def refresh(self, session: date) -> None:
        """A report was applied or cleared (the handlers' on_change)."""
        if self.session is not None and session != self.session:
            return  # another session's: this one is unchanged
        now = self.now()
        overlay, entry = session_overlay(self.archive, session, self.settings, as_of=now)
        if self.overlay is not None and self.opened(now):
            overlay = self.overlay.tightest(overlay)  # never loosens a session trading
        self.session = session
        self._set(overlay, entry)
        self._log(f"Risk report ({self.mode}) changed: {self.describe()}")

    def opened(self, now: datetime | None = None) -> bool:
        from research.risk_overlay.control import first_window

        if self.session is None:
            return False
        return (now or self.now()) >= first_window(self.config, self.session)

    def _set(self, overlay: SessionOverlay, entry: dict | None) -> None:
        self.overlay = replace(overlay, mode=self.mode)
        self.entry = entry
        self.checked_at = self.now().isoformat()
        for listener in list(self.listeners):
            listener(self.overlay)

    def enforced(self) -> SessionOverlay | None:
        """The overlay the trading path is handed: None in advisory mode."""
        if self.overlay is None or self.mode != "enforce":
            return None
        return self.overlay

    def describe(self) -> str:
        if self.overlay is None:
            return "not checked yet"
        if self.entry is None and not self.overlay.changes_trading:
            return "no report: trading as configured"
        return self.overlay.describe()

    def status(self) -> dict[str, Any]:
        """status.json's `risk_overlay`."""
        overlay = self.overlay
        entry = self.entry or {}
        mapped = entry.get("mapped") or {}
        if overlay is None:
            state = "unchecked"
        elif not entry and not overlay.changes_trading:
            state = "none"
        elif self.mode == "enforce":
            state = "in_force"
        else:
            state = "suggested"
        return {
            "session": self.session.isoformat() if self.session else None,
            "mode": self.mode,
            "state": state,
            "summary": self.describe(),
            "overlay": overlay.to_dict() if overlay is not None else None,
            "report": (
                {
                    "sha256": entry.get("sha256"),
                    "received_at": entry.get("received_at"),
                    "operator": entry.get("operator"),
                    "as_of": entry.get("as_of"),
                    "outcome": entry.get("outcome"),
                    "tier": mapped.get("tier"),
                    "score": mapped.get("score"),
                    "abstained": mapped.get("abstained"),
                }
                if entry
                else None
            ),
            "notes": list(self.notes),
            "checked_at": self.checked_at,
        }


def handlers(
    config: BacktestConfig,
    control_dir: str | Path,
    *,
    inbox=None,
    external_dir: str | Path | None = None,
    on_change: Callable[[date], None] | None = None,
    clock: Callable[[], float] = time.time,
) -> dict[str, Callable[[Any], str]]:
    """apply_risk_report and clear_risk_report for this deployment's trader,
    or {} when its config takes no reports."""
    if config.risk.overlay is None:
        return {}
    return risk_report_handlers(
        config,
        archive=ReportArchive.in_control_dir(control_dir),
        inputs_for=trader_inputs(config, inbox, external_dir=external_dir),
        on_change=on_change,
        clock=clock,
    )


__all__ = ["SessionRisk", "handlers", "trader_inputs", "trading_session"]
