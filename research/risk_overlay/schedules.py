"""
A backtest's risk report schedule: an archive (or a schedule file) read the
way a trader would have read it, session by session.

risk.overlay in a backtest config names where the reports come from
(docs/daily_risk_report_plan.md, "Engine support for a schedule"):

  source: reports | proxy | synthetic   `path` is an archive directory in
                         research/risk_overlay/archive.py's format -- one
                         JSON per session with the raw report and the
                         inputs it was mapped with. Each report is mapped
                         AGAIN with this config's settings and mapping, so
                         one archive serves every variant a sweep tries.
  source: schedule       `path` is a JSON file of overlays by session,
                         {"overlays": [{"session": ..., ...}, ...]}: a
                         synthetic schedule from tools/probe_risk_overlay.py
                         (constant tiers, the oracle, a shifted null)

Only `mode: enforce` builds a schedule: advisory trades the YAML, so its
backtest is the no-overlay run. A probe may skip all this and hand
run_sweep a RiskManager whose `overlay` it built itself.
"""

from __future__ import annotations

import json
from collections.abc import Iterable, Mapping
from dataclasses import replace
from datetime import date, datetime
from functools import lru_cache
from pathlib import Path
from typing import Any

from engine.core.config import RiskOverlayConfig
from engine.core.risk_overlay import OverlaySchedule, SessionOverlay
from engine.core.risk_report import Catalyst, RiskReport, parse_report
from research.risk_overlay.archive import ReportArchive, schedule_from_entries
from research.risk_overlay.baselines import Baseline, baseline_for
from research.risk_overlay.mapping import MappingInputs, map_report


def _catalysts(rows: Iterable[Mapping[str, Any]] | None) -> tuple[Catalyst, ...]:
    out = []
    for row in rows or ():
        at = row.get("at")
        out.append(
            Catalyst(
                event=str(row.get("event", "")),
                impact=str(row.get("impact", "low")),
                at=datetime.fromisoformat(at) if at else None,
                source=str(row.get("source", "engine")),
            )
        )
    return tuple(out)


def entry_inputs(
    entry: Mapping[str, Any], report: RiskReport, symbol: str, baseline: Baseline | None
) -> MappingInputs:
    """The inputs an archived report was mapped with, as the entry kept them."""
    kept = entry.get("inputs") or {}
    received = entry.get("received_at")
    base = kept.get("baseline")
    return MappingInputs(
        symbol=symbol.upper(),
        session=report.session,
        received_at=datetime.fromisoformat(received) if received else None,
        last_close=kept.get("last_close"),
        implied_move_pct=kept.get("implied_move_pct"),
        implied_source=kept.get("implied_source"),
        proxy_move_pct=kept.get("proxy_move_pct"),
        calendar=_catalysts(kept.get("calendar")),
        baseline=Baseline.from_dict(base) if isinstance(base, Mapping) else baseline,
    )


def remapped(
    entries: Iterable[Mapping[str, Any]],
    settings: RiskOverlayConfig,
    symbol: str,
    *,
    baseline: Baseline | None = None,
) -> list[dict]:
    """Each archived report mapped with `settings`, as an entry the week's
    cap and schedule_from_entries read."""
    baseline = baseline if baseline is not None else baseline_for(symbol)
    out = []
    for entry in entries:
        audit = parse_report(entry.get("report") or {})
        if not audit.ok:
            continue
        report = audit.require()
        mapped = map_report(report, entry_inputs(entry, report, symbol, baseline), settings)
        out.append(
            {
                "session": report.session.isoformat(),
                "received_at": entry.get("received_at"),
                "overlay": mapped.overlay.to_dict(),
                "receipts": [
                    {
                        "received_at": entry.get("received_at"),
                        "weekly_ceiling": mapped.weekly_ceiling,
                        "sha256": report.sha256,
                    }
                ],
            }
        )
    return out


def read_schedule_file(path: str | Path, settings: RiskOverlayConfig) -> OverlaySchedule:
    """A schedule file's overlays, in `settings`' mode."""
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    rows = data.get("overlays", []) if isinstance(data, dict) else data
    overlays = [replace(SessionOverlay.from_dict(row), mode=settings.mode) for row in rows]
    return OverlaySchedule(overlays)


@lru_cache(maxsize=8)
def _archive_entries(path: str, stamp: float) -> tuple[dict, ...]:
    return tuple(ReportArchive(path).entries())


def schedule_for_run(
    settings: RiskOverlayConfig | None,
    symbol: str,
    sessions: Iterable[date],
) -> OverlaySchedule | None:
    """The schedule a backtest of `settings` enforces over `sessions`, or
    None (no overlay, advisory, or no reports to read)."""
    if settings is None or settings.mode != "enforce" or not settings.path:
        return None
    if settings.source == "schedule":
        return read_schedule_file(settings.path, settings)
    root = Path(settings.path)
    stamp = max((p.stat().st_mtime for p in root.glob("*.json")), default=0.0)
    entries = remapped(_archive_entries(str(root), stamp), settings, symbol)
    return schedule_from_entries(entries, list(sessions), settings)


def write_schedule_file(path: str | Path, overlays: Iterable[SessionOverlay], **meta: Any) -> None:
    """A schedule file (source: schedule) -- tools/probe_risk_overlay.py's."""
    data = {**meta, "overlays": [o.to_dict() for o in overlays]}
    Path(path).write_text(json.dumps(data, indent=1, sort_keys=True) + "\n", encoding="utf-8")


__all__ = [
    "entry_inputs",
    "read_schedule_file",
    "remapped",
    "schedule_for_run",
    "write_schedule_file",
]
