"""
What one session may be told by a risk report: the overlay.

docs/daily_risk_report_plan.md is the design. A report never reaches the
trading path itself. A versioned, deterministic mapping
(research/risk_overlay/mapping.py) turns it into a SessionOverlay inside
bounds the deployment's YAML sets, and only the overlay is read below.

--------------------------------------------------------------------
IT CAN ONLY TAKE RISK AWAY

Every lever is bounded so that a report removes risk from what the
reviewed file trades and never adds it (the owner's decision, Nov 20 2026):

  pause             no new buys this session (exempt buys excepted)
  buy_multiplier    each proposed buy times this, in [0, 1]
  exposure_ceiling  the share of equity open lots may hold, combined with
                    the YAML's drawdown-ramped ceiling by min()
  step_multiplier   the grid step times this, in [1, max]: never narrower
  target_multiplier the profit target of lots bought this session, 1 unless
                    the YAML opts in (spacing.target_follows)
  blackouts         UTC windows with no new buys
  supersedes        the strategy's day-level levers this session's report
                    replaces (`governor`, `event_boosts`), only those the
                    YAML names; empty on a session no report set

The two exceptions (a superseded governor pause, a following target) are
the YAML's own choices, not the report's.

--------------------------------------------------------------------
NEUTRAL IS "NO REPORT"

NEUTRAL changes nothing, `supersedes` included: a session no report set
trades exactly as configured, governor and event boosts too. An
OverlaySchedule maps sessions to overlays and answers NEUTRAL for every
session it does not name.

--------------------------------------------------------------------
ADVISORY OR ENFORCE

The overlay carries the deployment's mode. In `advisory` mode it is built,
shown, archived and shadowed exactly as `enforce` would build it, and the
trading path is never handed it: an advisory session trades the YAML.

Pure and standard library only (layer 0): the RiskManager, the grid's
step, the backtest and the live loop all read the same object.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field, replace
from datetime import UTC, date, datetime
from typing import Any

from engine.core.trading_calendar import EASTERN

MODES = ("advisory", "enforce")
SUPERSEDABLE = ("governor", "event_boosts")
EXEMPTIONS = ("reversal",)


def _eastern_date(moment: datetime) -> date:
    if moment.tzinfo is None:
        moment = moment.replace(tzinfo=UTC)
    return moment.astimezone(EASTERN).date()


@dataclass(frozen=True)
class SessionOverlay:
    """What one session is told. The defaults are NEUTRAL."""

    session: date | None = None
    pause: bool = False
    buy_multiplier: float = 1.0
    exposure_ceiling: float | None = None
    step_multiplier: float = 1.0
    target_multiplier: float = 1.0
    blackouts: tuple[tuple[datetime, datetime], ...] = ()
    supersedes: frozenset[str] = frozenset()
    mode: str = "advisory"
    # What the Live page and the journals say about it.
    tier: int | None = None
    weekly_ceiling: float | None = None
    reasons: tuple[str, ...] = ()
    mapping_id: str | None = None
    report_sha256: str | None = None
    exempt: tuple[str, ...] = field(default=EXEMPTIONS)

    def __post_init__(self) -> None:
        if not 0.0 <= self.buy_multiplier <= 1.0:
            raise ValueError(f"buy_multiplier must be in [0, 1], got {self.buy_multiplier}")
        if self.exposure_ceiling is not None and not 0.0 <= self.exposure_ceiling <= 1.0:
            raise ValueError(f"exposure_ceiling must be in [0, 1], got {self.exposure_ceiling}")
        if self.weekly_ceiling is not None and not 0.0 <= self.weekly_ceiling <= 1.0:
            raise ValueError(f"weekly_ceiling must be in [0, 1], got {self.weekly_ceiling}")
        if self.step_multiplier < 1.0:
            raise ValueError(f"step_multiplier must be at least 1, got {self.step_multiplier}")
        if self.target_multiplier < 1.0:
            raise ValueError(f"target_multiplier must be at least 1, got {self.target_multiplier}")
        if self.mode not in MODES:
            raise ValueError(f"mode must be one of {', '.join(MODES)}, got {self.mode!r}")
        unknown = set(self.supersedes) - set(SUPERSEDABLE)
        if unknown:
            raise ValueError(f"supersedes names unknown levers {sorted(unknown)}")
        unknown = set(self.exempt) - set(EXEMPTIONS)
        if unknown:
            raise ValueError(f"exempt names unknown buys {sorted(unknown)}")
        for start, end in self.blackouts:
            if start.tzinfo is None or end.tzinfo is None or end <= start:
                raise ValueError("a blackout is a UTC window whose end is after its start")

    # -- what it does ----------------------------------------------------

    @property
    def changes_trading(self) -> bool:
        """Whether it would change anything were it enforced."""
        return (
            self.pause
            or self.buy_multiplier < 1.0
            or self.exposure_ceiling is not None
            or self.step_multiplier > 1.0
            or self.target_multiplier > 1.0
            or bool(self.blackouts)
            or bool(self.supersedes)
        )

    @property
    def enforced(self) -> bool:
        return self.mode == "enforce"

    def in_blackout(self, moment: datetime) -> bool:
        if moment.tzinfo is None:
            moment = moment.replace(tzinfo=UTC)
        return any(start <= moment < end for start, end in self.blackouts)

    def ceiling(self) -> float:
        """The exposure ceiling, 1 (no ceiling of its own) when unset."""
        return 1.0 if self.exposure_ceiling is None else self.exposure_ceiling

    # -- comparison ------------------------------------------------------

    def no_looser_than(self, other: SessionOverlay) -> bool:
        """True when every lever takes at least as much risk away as
        `other`'s."""
        # A pause stops every buy the overlay governs (an exempt buy is never
        # handed the overlay at all), so the other buy levers size nothing
        # under it: it is the tightest a session can be told.
        if self.pause:
            return True
        if other.pause:
            return False
        return (
            self.buy_multiplier <= other.buy_multiplier + 1e-12
            and self.ceiling() <= other.ceiling() + 1e-12
            and self.step_multiplier >= other.step_multiplier - 1e-12
            and set(other.blackouts) <= set(self.blackouts)
        )

    def tightest(self, other: SessionOverlay) -> SessionOverlay:
        """Lever by lever, the tighter of the two: what a later report may
        make of a session already trading, which it may tighten and never
        loosen. The rest (the words, the report's hash) are `other`'s."""
        ceilings = [c for c in (self.exposure_ceiling, other.exposure_ceiling) if c is not None]
        weekly = [c for c in (self.weekly_ceiling, other.weekly_ceiling) if c is not None]
        tiers = [t for t in (self.tier, other.tier) if t is not None]
        return replace(
            other,
            pause=self.pause or other.pause,
            buy_multiplier=min(self.buy_multiplier, other.buy_multiplier),
            exposure_ceiling=min(ceilings) if ceilings else None,
            step_multiplier=max(self.step_multiplier, other.step_multiplier),
            # A target follows the step only where the YAML opts in; holding
            # a lot longer is not a tightening, so the earlier one stands.
            target_multiplier=self.target_multiplier,
            blackouts=tuple(sorted(set(self.blackouts) | set(other.blackouts))),
            supersedes=self.supersedes | other.supersedes,
            weekly_ceiling=min(weekly) if weekly else None,
            tier=max(tiers) if tiers else None,
        )

    # -- the wire ----------------------------------------------------------

    def to_dict(self) -> dict[str, Any]:
        return {
            "session": self.session.isoformat() if self.session else None,
            "pause": self.pause,
            "buy_multiplier": self.buy_multiplier,
            "exposure_ceiling": self.exposure_ceiling,
            "step_multiplier": self.step_multiplier,
            "target_multiplier": self.target_multiplier,
            "blackouts": [[s.isoformat(), e.isoformat()] for s, e in self.blackouts],
            "supersedes": sorted(self.supersedes),
            "mode": self.mode,
            "tier": self.tier,
            "weekly_ceiling": self.weekly_ceiling,
            "reasons": list(self.reasons),
            "mapping_id": self.mapping_id,
            "report_sha256": self.report_sha256,
            "exempt": list(self.exempt),
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> SessionOverlay:
        def when(text: str) -> datetime:
            moment = datetime.fromisoformat(text)
            return moment if moment.tzinfo else moment.replace(tzinfo=UTC)

        session = data.get("session")
        return cls(
            session=date.fromisoformat(session) if session else None,
            pause=bool(data.get("pause", False)),
            buy_multiplier=float(data.get("buy_multiplier", 1.0)),
            exposure_ceiling=(
                float(data["exposure_ceiling"])
                if data.get("exposure_ceiling") is not None
                else None
            ),
            step_multiplier=float(data.get("step_multiplier", 1.0)),
            target_multiplier=float(data.get("target_multiplier", 1.0)),
            blackouts=tuple((when(s), when(e)) for s, e in data.get("blackouts") or ()),
            supersedes=frozenset(data.get("supersedes") or ()),
            mode=str(data.get("mode", "advisory")),
            tier=int(data["tier"]) if data.get("tier") is not None else None,
            weekly_ceiling=(
                float(data["weekly_ceiling"]) if data.get("weekly_ceiling") is not None else None
            ),
            reasons=tuple(str(r) for r in data.get("reasons") or ()),
            mapping_id=data.get("mapping_id"),
            report_sha256=data.get("report_sha256"),
            exempt=tuple(data.get("exempt", EXEMPTIONS)),
        )

    def describe(self) -> str:
        """The overlay in words, for the Live page and the journals."""
        when = f"{self.session:%a %b} {self.session.day}: " if self.session else ""
        if not self.changes_trading:
            return when + "trading as configured"
        parts = []
        if self.pause:
            exempt = " (reversal lots allowed)" if "reversal" in self.exempt else ""
            parts.append(f"no new grid buys{exempt}")
        elif self.buy_multiplier < 1.0:
            parts.append(f"buys at {self.buy_multiplier:.0%} of their size")
        if self.exposure_ceiling is not None:
            parts.append(f"open lots held to {self.exposure_ceiling:.0%} of equity")
        if self.step_multiplier > 1.0:
            parts.append(f"grid step x{self.step_multiplier:.1f}")
        if self.target_multiplier > 1.0:
            parts.append(f"targets x{self.target_multiplier:.1f} for lots bought today")
        if self.blackouts:
            parts.append(f"{len(self.blackouts)} catalyst blackout(s)")
        if self.supersedes:
            names = {"governor": "risk governor", "event_boosts": "event-day boosts"}
            levers = " and ".join(names[s] for s in sorted(self.supersedes, reverse=True))
            parts.append(f"the report stands in for the {levers}")
        parts.append("sells unchanged")
        return when + "; ".join(parts)


NEUTRAL = SessionOverlay()


def neutral_for(
    session: date, *, mode: str = "advisory", reasons: Iterable[str] = ()
) -> SessionOverlay:
    """NEUTRAL named for a session: what a session no report set trades."""
    return SessionOverlay(session=session, mode=mode, reasons=tuple(reasons))


def session_step(step: float, overlay: SessionOverlay | None) -> float:
    """The grid step a session's buys trigger on: the YAML's, widened by an
    enforced overlay's step_multiplier, never narrowed. Every caller that
    hands a strategy its step goes through here, so backtest and live widen
    the same way."""
    if overlay is None or not overlay.enforced:
        return step
    return step * max(1.0, overlay.step_multiplier)


def session_target(profit_target: float, overlay: SessionOverlay | None) -> float:
    """The profit target a lot bought under `overlay` carries."""
    if overlay is None or not overlay.enforced:
        return profit_target
    return profit_target * max(1.0, overlay.target_multiplier)


class OverlaySchedule:
    """Sessions to overlays. A session it does not name reads NEUTRAL --
    which, unlike a named overlay, supersedes nothing."""

    def __init__(
        self, overlays: Mapping[date, SessionOverlay] | Iterable[SessionOverlay] = ()
    ) -> None:
        if isinstance(overlays, Mapping):
            items = dict(overlays)
        else:
            items = {}
            for overlay in overlays:
                if overlay.session is None:
                    raise ValueError("a scheduled overlay must name its session")
                items[overlay.session] = overlay
        for session, overlay in items.items():
            if overlay.session is not None and overlay.session != session:
                raise ValueError(f"the overlay for {session} names {overlay.session}")
        self._overlays = {s: (o if o.session else replace(o, session=s)) for s, o in items.items()}

    def __len__(self) -> int:
        return len(self._overlays)

    def __contains__(self, session: date) -> bool:
        return session in self._overlays

    def sessions(self) -> list[date]:
        return sorted(self._overlays)

    def get(self, session: date) -> SessionOverlay:
        return self._overlays.get(session, NEUTRAL)

    def at(self, moment: datetime) -> SessionOverlay:
        """The overlay of the session `moment` falls on (its Eastern date)."""
        return self.get(_eastern_date(moment))

    def items(self) -> list[tuple[date, SessionOverlay]]:
        return sorted(self._overlays.items())

    def content_hash(self) -> str:
        """Identifies the schedule: two runs that differ only in it must
        not be taken for one simulation (docs/daily_risk_report_plan.md,
        "Engine support for a schedule")."""
        rows = [
            {**overlay.to_dict(), "reasons": [], "mapping_id": overlay.mapping_id}
            for _, overlay in self.items()
        ]
        text = json.dumps(rows, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(text.encode("utf-8")).hexdigest()


__all__ = [
    "EXEMPTIONS",
    "MODES",
    "NEUTRAL",
    "SUPERSEDABLE",
    "OverlaySchedule",
    "SessionOverlay",
    "neutral_for",
    "session_step",
    "session_target",
]
