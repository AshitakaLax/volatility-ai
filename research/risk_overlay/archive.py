"""
The risk report archive, and the overlay a session trades under.

--------------------------------------------------------------------
LAYOUT -- in the deployment's control directory, written by its TRADER only

  risk_reports/<session>.json             the report in force for a session:
                                          the raw report, its SHA-256, who
                                          sent it and from where, when it
                                          arrived, the mapping id, the overlay,
                                          the mode, the outcome -- and every
                                          report received for that session
                                          (`receipts`), the ones not applied
                                          included
  risk_reports/superseded/<session>-<sha8>.json  one replaced before its
                                          session opened, or cleared

The same one-file-a-session format holds proxy and synthetic reports for a
backtest (`source`: llm | proxy | synthetic | replay), so a backtest replays
an archive exactly as a trader would have read it.

--------------------------------------------------------------------
THE WEEK'S EXPOSURE CAP (lever G)

Set at the week's first session (Monday's, or each block of five sessions)
by the newest report received before it and at most `max_age_days` old --
normally Friday's or Sunday's. A report received later with a LOWER ceiling
tightens the cap at once (the next tick live; the next session in a
backtest). A higher one waits for the next reset. No report: no cap.

--------------------------------------------------------------------
THE SESSION'S OVERLAY

The session's own report's daily overlay (NEUTRAL without one: as
configured, governor and boosts included), with its exposure ceiling the
min() of the daily tier's and the week's cap. The RiskManager then takes the
min() with the YAML's drawdown-ramped ceiling.
"""

from __future__ import annotations

import json
import logging
import os
import uuid
from collections.abc import Iterable, Mapping
from dataclasses import replace
from datetime import UTC, date, datetime, timedelta
from functools import lru_cache
from pathlib import Path
from typing import Any

from engine.core.config import RiskOverlayConfig
from engine.core.risk_overlay import OverlaySchedule, SessionOverlay, neutral_for
from engine.core.risk_report import regular_bounds
from engine.core.trading_calendar import is_session, next_session, previous_session

logger = logging.getLogger(__name__)

ARCHIVE_DIRNAME = "risk_reports"
SOURCES = ("llm", "proxy", "synthetic", "replay")
# The first session the five-session weeks are counted from.
_BLOCK_ANCHOR = date(2001, 1, 2)


def _iso(moment: datetime) -> str:
    return moment.astimezone(UTC).isoformat()


def _when(text: Any) -> datetime | None:
    if not isinstance(text, str):
        return None
    try:
        moment = datetime.fromisoformat(text)
    except ValueError:
        return None
    return moment if moment.tzinfo else moment.replace(tzinfo=UTC)


def _write_json(path: Path, data: Mapping[str, Any]) -> None:
    """Whole file or none: written beside its destination, then renamed."""
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{uuid.uuid4().hex[:8]}.tmp")
    with open(temporary, "w", encoding="utf-8") as handle:
        json.dump(data, handle, indent=2, sort_keys=True, default=str)
        handle.write("\n")
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temporary, path)


def _read_json(path: Path) -> dict | None:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return None
    except (OSError, ValueError) as exc:
        logger.warning(f"Unreadable risk report archive file {path}: {exc}")
        return None
    return data if isinstance(data, dict) else None


class ReportArchive:
    """One deployment's risk_reports/ (or a backtest's archive directory)."""

    def __init__(self, root: str | Path) -> None:
        self.root = Path(root)

    @classmethod
    def in_control_dir(cls, control_dir: str | Path) -> ReportArchive:
        return cls(Path(control_dir) / ARCHIVE_DIRNAME)

    def path(self, session: date) -> Path:
        return self.root / f"{session.isoformat()}.json"

    def current(self, session: date) -> dict | None:
        return _read_json(self.path(session))

    def sessions(self) -> list[date]:
        if not self.root.is_dir():
            return []
        found = []
        for path in self.root.glob("*.json"):
            try:
                found.append(date.fromisoformat(path.stem))
            except ValueError:
                continue
        return sorted(found)

    def entries(self, since: date | None = None, through: date | None = None) -> list[dict]:
        """Every session's entry, oldest first."""
        rows = []
        for session in self.sessions():
            if (since and session < since) or (through and session > through):
                continue
            entry = self.current(session)
            if entry is not None:
                rows.append(entry)
        return rows

    def superseded(self) -> list[dict]:
        directory = self.root / "superseded"
        if not directory.is_dir():
            return []
        rows = [_read_json(path) for path in sorted(directory.glob("*.json"))]
        return [row for row in rows if row is not None]

    def receipts(self, since: date | None = None) -> list[dict]:
        """Every report received, applied or not, oldest first: what the
        weekly cap reads."""
        rows: list[dict] = []
        for entry in self.entries(since=since):
            rows.extend(entry.get("receipts") or [])
        for entry in self.superseded():
            session = entry.get("session")
            if since and session and session < since.isoformat():
                continue
            rows.extend(entry.get("receipts") or [])
        seen = set()
        unique = []
        for row in sorted(rows, key=lambda r: r.get("received_at") or ""):
            key = (row.get("sha256"), row.get("received_at"))
            if key in seen:
                continue
            seen.add(key)
            unique.append(row)
        return unique

    def write(self, session: date, entry: Mapping[str, Any]) -> dict:
        """Make `entry` the session's. One it replaces is kept under
        superseded/."""
        old = self.current(session)
        if old is not None and old.get("sha256") != entry.get("sha256"):
            self._retire(session, old)
        data = {**entry, "session": session.isoformat()}
        _write_json(self.path(session), data)
        return data

    def update(self, session: date, **fields: Any) -> dict | None:
        """Add `fields` to the session's entry (the trader's start record)."""
        entry = self.current(session)
        if entry is None:
            return None
        entry.update(fields)
        _write_json(self.path(session), entry)
        return entry

    def clear(self, session: date, *, by: str, reason: str, at: datetime) -> dict | None:
        """Withdraw the session's report: kept under superseded/, marked."""
        entry = self.current(session)
        if entry is None:
            return None
        entry = {
            **entry,
            "outcome": "cleared",
            "cleared": {"by": by, "reason": reason, "at": _iso(at)},
        }
        self._retire(session, entry)
        self.path(session).unlink(missing_ok=True)
        return entry

    def _retire(self, session: date, entry: Mapping[str, Any]) -> None:
        sha = str(entry.get("sha256") or "unknown")[:8]
        _write_json(self.root / "superseded" / f"{session.isoformat()}-{sha}.json", entry)


# --------------------------------------------------------------------
# The week
# --------------------------------------------------------------------


@lru_cache(maxsize=4096)
def _session_index(session: date) -> int:
    """How many sessions after _BLOCK_ANCHOR `session` is (0 for the anchor)."""
    count, day = 0, _BLOCK_ANCHOR
    while day < session:
        day = next_session(day)
        count += 1
    return count


def week_start(session: date, reset: str = "monday") -> date:
    """The first session of `session`'s week: the first session on or
    after that calendar week's Monday, or the first of its block of five."""
    if not is_session(session):
        raise ValueError(f"{session} is not a session")
    if reset == "five_sessions":
        if session < _BLOCK_ANCHOR:
            raise ValueError(f"five-session weeks are counted from {_BLOCK_ANCHOR}")
        day, back = session, _session_index(session) % 5
        for _ in range(back):
            day = previous_session(day)
        return day
    monday = session - timedelta(days=session.weekday())
    day = monday
    while not is_session(day):
        day += timedelta(days=1)
    return day


def week_cap(
    receipts: Iterable[Mapping[str, Any]],
    session: date,
    settings: RiskOverlayConfig,
    *,
    as_of: datetime | None = None,
) -> tuple[float | None, list[str]]:
    """The week's exposure cap in force for `session` at `as_of` (default:
    the session's open, as a backtest reads it), and why. `receipts` are
    rows with `received_at`, `weekly_ceiling` and `session`."""
    if not settings.weekly.enabled:
        return None, []
    first = week_start(session, settings.weekly.reset)
    first_open = regular_bounds(first)[0]
    moment = as_of or regular_bounds(session)[0]
    oldest = first_open - timedelta(days=int(settings.weekly.max_age_days))
    rows = []
    for row in receipts:
        received = _when(row.get("received_at"))
        ceiling = row.get("weekly_ceiling")
        if received is None or ceiling is None:
            continue
        rows.append((received, float(ceiling), row))
    rows.sort(key=lambda item: item[0])
    setter = None
    for received, ceiling, row in rows:
        if oldest <= received < first_open:
            setter = (received, ceiling, row)
    cap = setter[1] if setter else None
    reasons = []
    if setter:
        reasons.append(
            f"this week's cap {cap:.0%}, set by the report received "
            f"{setter[0].astimezone(UTC):%Y-%m-%d %H:%M} UTC"
        )
    for received, ceiling, _row in rows:
        if first_open <= received < moment and (cap is None or ceiling < cap):
            cap = ceiling
            reasons.append(
                f"tightened to {ceiling:.0%} by the report received "
                f"{received.astimezone(UTC):%Y-%m-%d %H:%M} UTC"
            )
    return cap, reasons


def compose(
    daily: SessionOverlay, cap: float | None, reasons: Iterable[str] = ()
) -> SessionOverlay:
    """`daily` with the week's cap: its ceiling the min() of the two."""
    if cap is None:
        return replace(daily, weekly_ceiling=None)
    ceiling = cap if daily.exposure_ceiling is None else min(cap, daily.exposure_ceiling)
    return replace(
        daily,
        exposure_ceiling=ceiling,
        weekly_ceiling=cap,
        reasons=tuple(daily.reasons) + tuple(reasons),
    )


def overlay_from(
    entry: Mapping[str, Any] | None,
    session: date,
    settings: RiskOverlayConfig,
    receipts: Iterable[Mapping[str, Any]],
    *,
    as_of: datetime | None = None,
) -> SessionOverlay:
    """The overlay `session` trades under, from its entry (None: no report)
    and the receipts the week's cap reads."""
    if entry is not None and entry.get("overlay"):
        daily = replace(SessionOverlay.from_dict(entry["overlay"]), mode=settings.mode)
    else:
        daily = neutral_for(session, mode=settings.mode)
    cap, reasons = week_cap(receipts, session, settings, as_of=as_of)
    return compose(daily, cap, reasons)


def session_overlay(
    archive: ReportArchive,
    session: date,
    settings: RiskOverlayConfig,
    *,
    as_of: datetime | None = None,
) -> tuple[SessionOverlay, dict | None]:
    """The overlay `session` trades under (module docstring), and its
    archive entry (None: no report for it)."""
    entry = archive.current(session)
    first = week_start(session, settings.weekly.reset) if settings.weekly.enabled else session
    receipts = archive.receipts(since=first - timedelta(days=int(settings.weekly.max_age_days) + 7))
    return overlay_from(entry, session, settings, receipts, as_of=as_of), entry


def schedule_from_entries(
    entries: Iterable[Mapping[str, Any]],
    sessions: Iterable[date],
    settings: RiskOverlayConfig,
) -> OverlaySchedule:
    """Every session's overlay, as a backtest reads an archive: each one as
    it stood at that session's open. `entries` are archive entries (each
    with its `receipts`); read once, composed in memory."""
    by_session: dict[str, Mapping[str, Any]] = {}
    receipts: list[Mapping[str, Any]] = []
    for entry in entries:
        if entry.get("session"):
            by_session[str(entry["session"])] = entry
        receipts.extend(entry.get("receipts") or [])
    receipts.sort(key=lambda row: row.get("received_at") or "")
    stamps = [_when(row.get("received_at")) for row in receipts]
    overlays = {}
    for session in sorted(sessions):
        entry = by_session.get(session.isoformat())
        nearby = receipts
        if settings.weekly.enabled:
            # Only the receipts that can touch this week: a long history stays linear.
            first = week_start(session, settings.weekly.reset)
            low = regular_bounds(first)[0] - timedelta(days=int(settings.weekly.max_age_days))
            high = regular_bounds(session)[0]
            nearby = [
                r
                for r, t in zip(receipts, stamps, strict=True)
                if t is not None and low <= t < high
            ]
        overlay = overlay_from(entry, session, settings, nearby)
        if overlay.changes_trading or overlay.report_sha256:
            overlays[session] = overlay
    return OverlaySchedule(overlays)


def schedule(
    archive: ReportArchive,
    sessions: Iterable[date],
    settings: RiskOverlayConfig,
) -> OverlaySchedule:
    """schedule_from_entries over `archive`'s entries."""
    return schedule_from_entries(archive.entries(), sessions, settings)


__all__ = [
    "ARCHIVE_DIRNAME",
    "SOURCES",
    "ReportArchive",
    "compose",
    "overlay_from",
    "schedule",
    "schedule_from_entries",
    "session_overlay",
    "week_cap",
    "week_start",
]
