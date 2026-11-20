"""
What a report would do to one deployment: the Live page's "Check".

server/live_control.py's preview route calls preview() for each deployment
the panel lists. It READS -- the deployment's config, its archive, its bar
journal, the outside data -- and writes nothing: the trader parses and maps
the report again when it applies it, by the same functions, so the preview
says what the trader will do as long as nothing changes in between.
"""

from __future__ import annotations

from collections.abc import Mapping
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from engine.core.config import BacktestConfig, LiveControlConfig
from engine.core.risk_overlay import NEUTRAL, SessionOverlay
from engine.core.risk_report import parse_report, regular_bounds
from research.risk_overlay.archive import ReportArchive, compose, week_cap
from research.risk_overlay.control import first_window
from research.risk_overlay.inputs import build_inputs, closes_from_bars
from research.risk_overlay.live import JOURNAL_SESSIONS
from research.risk_overlay.mapping import map_report


def takes_reports(config: BacktestConfig, caps: LiveControlConfig) -> tuple[bool, str | None]:
    """Whether the Live page may send this deployment a report, and why not."""
    if config.risk.overlay is None:
        return False, "its config has no risk.overlay"
    if not caps.risk_reports:
        return False, "its config does not grant live.control.risk_reports"
    return True, None


def overlay_settings(config: BacktestConfig) -> dict[str, Any] | None:
    overlay = config.risk.overlay
    if overlay is None:
        return None
    return {
        "mode": overlay.mode,
        "mapping": overlay.mapping,
        "levers": {
            "daily": overlay.daily,
            "spacing": overlay.spacing.enabled,
            "weekly": overlay.weekly.enabled,
        },
    }


def preview(
    config: BacktestConfig,
    caps: LiveControlConfig,
    *,
    control_dir: str | Path | None,
    report: Mapping[str, Any] | str,
    now: datetime | None = None,
    external_dir: str | Path | None = None,
    inbox=None,
) -> dict[str, Any]:
    """What `report` would do to the deployment (module docstring)."""
    now = now or datetime.now(UTC)
    takes, why = takes_reports(config, caps)
    paper = bool(config.live.paper_trading)
    out: dict[str, Any] = {
        "symbol": config.backtest.symbol,
        "paper": paper,
        "takes_reports": takes,
        "why_not": why,
        "settings": overlay_settings(config),
        "typed": None if paper else "this deployment trades real money",
    }
    audit = parse_report(report)
    out["audit"] = audit.to_dict()
    if not audit.ok:
        out["would"] = "refused"
        out["detail"] = "the report does not pass the audit"
        return out
    parsed = audit.require()
    session = parsed.session
    out["session"] = session.isoformat()
    out["sha256"] = parsed.sha256
    settings = config.risk.overlay
    if settings is None:
        out["would"] = "refused"
        out["detail"] = why
        return out
    closes: list[float] = []
    if inbox is not None:
        try:
            bars = inbox.bars(JOURNAL_SESSIONS)
        except Exception:
            bars = []
        open_at = regular_bounds(session)[0].timestamp()
        closes = closes_from_bars(b for b in bars if float(b.get("t", 0)) < open_at)
    inputs, notes = build_inputs(
        config.backtest.symbol,
        session,
        received_at=now,
        closes=closes,
        external_dir=external_dir,
    )
    mapped = map_report(parsed, inputs, settings)
    out["mapped"] = mapped.to_dict()
    out["notes"] = notes
    archive = ReportArchive.in_control_dir(control_dir) if control_dir is not None else None
    existing = archive.current(session) if archive is not None else None
    receipts = archive.receipts() if archive is not None else []
    this = {"received_at": now.isoformat(), "weekly_ceiling": mapped.weekly_ceiling}
    overlay = mapped.overlay
    if now >= regular_bounds(session)[1]:
        out["would"], out["detail"] = "refused", f"the {session} session has already ended"
    elif existing is not None and existing.get("sha256") == parsed.sha256:
        out["would"], out["detail"] = "unchanged", "this report is already the one in force"
    elif not paper and existing is not None:
        out["would"], out["detail"] = (
            "refused",
            f"real money takes one report a session, and {session} has one",
        )
    elif now >= first_window(config, session):
        base = (
            SessionOverlay.from_dict(existing["overlay"])
            if existing is not None and existing.get("overlay")
            else NEUTRAL
        )
        tightened = base.tightest(overlay)
        if tightened.no_looser_than(base) and base.no_looser_than(tightened):
            out["would"], out["detail"] = (
                "not_applied",
                f"{session} is already trading and this report would not tighten it",
            )
        else:
            overlay = tightened
            out["would"], out["detail"] = (
                "tighten",
                f"{session} is trading: it tightens at the next tick",
            )
    elif existing is not None:
        out["would"], out["detail"] = "replace", f"it replaces the report {session} has"
    else:
        out["would"], out["detail"] = "apply", f"it becomes {session}'s report"
    cap, reasons = week_cap([*receipts, this], session, settings)
    composed = compose(overlay, cap, reasons)
    out["overlay"] = composed.to_dict()
    out["summary"] = composed.describe()
    out["mode"] = settings.mode
    out["existing"] = (
        {
            "sha256": existing.get("sha256"),
            "received_at": existing.get("received_at"),
            "operator": existing.get("operator"),
            "summary": existing.get("summary"),
        }
        if existing
        else None
    )
    return out


__all__ = ["overlay_settings", "preview", "takes_reports"]
