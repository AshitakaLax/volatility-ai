"""
What a mapping reads besides the report (mapping.MappingInputs).

  implied move   the 1-day move the fund's options index implies: leverage x
                 index / sqrt(252) -- 3 x VXN / sqrt(252) for TQQQ. Read
                 point in time the way the risk governor reads its series
                 (research/strategies/risk_governor.py): the newest value
                 stamped before 04:00 UTC of the session's own date, and none
                 at all when that is more than MAX_AGE_DAYS old -- a stale
                 feed skips the cross-check rather than freezing it.
  proxy move     the proxy's expected 1-day move: the implied move blended
                 equally with the fund's realised volatility over its last
                 REALISED_SESSIONS sessions (docs/daily_risk_report_plan.md,
                 "The proxy report"). research/risk_overlay/proxy.py builds
                 whole proxy reports from the same two functions.
  the calendar   the engine's own FOMC decision days and megacap earnings
                 reaction sessions (engine/data/fomc_calendar.py,
                 earnings_calendar.py): what a report missed is added as high.

The server's preview, the trader that applies a report and the backtests
all build their inputs here, so they agree.
"""

from __future__ import annotations

import math
from collections.abc import Iterable, Sequence
from datetime import UTC, date, datetime, time, timedelta
from itertools import pairwise
from pathlib import Path

from engine.core.risk_report import Catalyst
from engine.core.trading_calendar import EASTERN
from research.risk_overlay.baselines import Baseline, baseline_for
from research.risk_overlay.mapping import MappingInputs

# Each fund's options index (research/ml/sources.py file keys) and leverage.
IMPLIED_INDEX: dict[str, tuple[str, float]] = {
    "TQQQ": ("cboe_VXN", 3.0),
    "SQQQ": ("cboe_VXN", 3.0),
    "QLD": ("cboe_VXN", 2.0),
    "QQQ": ("cboe_VXN", 1.0),
    "UPRO": ("cboe_VIX", 3.0),
    "SPXL": ("cboe_VIX", 3.0),
    "SSO": ("cboe_VIX", 2.0),
    "SPY": ("cboe_VIX", 1.0),
    "RSP": ("cboe_VIX", 1.0),
    "IWM": ("cboe_RVX", 1.0),
    "TNA": ("cboe_RVX", 3.0),
}
SESSION_CUTOFF_UTC = 4  # research/strategies/risk_governor.py's point-in-time rule
MAX_AGE_DAYS = 7
REALISED_SESSIONS = 10
FOMC_DECISION_TIME = time(14, 0)  # Eastern: the statement


def implied_move(
    symbol: str, session: date, external_dir: str | Path | None = None
) -> tuple[float | None, str]:
    """(the implied 1-day move in percent, what it came from) -- or (None,
    why not)."""
    from research.strategies.risk_governor import external_directory, read_series

    known = IMPLIED_INDEX.get(symbol.upper())
    if known is None:
        return None, f"no options index is known for {symbol}"
    key, leverage = known
    path = external_directory(external_dir) / f"{key}.csv"
    if not path.exists():
        return None, f"{key} is not in the outside data"
    try:
        series = read_series(path)
    except (OSError, ValueError) as exc:
        return None, f"{key} could not be read: {exc}"
    cutoff = datetime.combine(session, time(SESSION_CUTOFF_UTC), tzinfo=UTC)
    before = series[series.index < cutoff]
    if before.empty:
        return None, f"{key} has no reading before {session}"
    stamp = before.index[-1].to_pydatetime()
    if (cutoff - stamp) > timedelta(days=MAX_AGE_DAYS):
        return None, f"{key}'s newest reading is from {stamp.date()}: stale"
    value = float(before.iloc[-1])
    name = key.split("_", 1)[1]
    return leverage * value / math.sqrt(252.0), f"{name} {value:.2f} on {stamp.date()}"


def realised_sigma_pct(closes: Sequence[float], sessions: int = REALISED_SESSIONS) -> float | None:
    """The standard deviation of the last `sessions` close-to-close returns,
    in percent; None with fewer than five."""
    values = [float(c) for c in closes if c is not None and c > 0]
    returns = [b / a - 1.0 for a, b in pairwise(values)][-sessions:]
    if len(returns) < 5:
        return None
    mean = sum(returns) / len(returns)
    variance = sum((r - mean) ** 2 for r in returns) / (len(returns) - 1)
    return 100.0 * math.sqrt(variance)


def proxy_move(implied_pct: float | None, realised_pct: float | None) -> float | None:
    """The proxy's expected move: the two blended equally, or whichever is known."""
    known = [v for v in (implied_pct, realised_pct) if v is not None]
    if not known:
        return None
    return sum(known) / len(known)


def calendar_catalysts(session: date, *, live: bool = True) -> tuple[Catalyst, ...]:
    """The engine's own catalysts for `session`: its FOMC decision (the
    14:00 ET statement) and a megacap earnings reaction session. `live`
    adds the reaction sessions refreshed from EDGAR after the committed list
    (engine/data/earnings_calendar.py), as a live loop reads them."""
    from engine.data.earnings_calendar import is_earnings_reaction_day, later_reaction_dates
    from engine.data.fomc_calendar import is_fomc_day

    found = []
    if is_fomc_day(session):
        at = datetime.combine(session, FOMC_DECISION_TIME, tzinfo=EASTERN).astimezone(UTC)
        found.append(Catalyst("FOMC decision (engine calendar)", "high", at=at, source="engine"))
    reaction = is_earnings_reaction_day(session) or (live and session in later_reaction_dates())
    if reaction:
        found.append(
            Catalyst("Megacap earnings reaction session (engine calendar)", "high", source="engine")
        )
    return tuple(found)


def closes_from_bars(bars: Iterable[dict]) -> list[float]:
    """Each session's last regular-hours close from minute bars ({"t":
    epoch seconds, "c": close}), oldest first: a trader's bar journal as
    daily closes."""
    by_day: dict[date, tuple[float, float]] = {}
    for bar in bars:
        try:
            moment = datetime.fromtimestamp(float(bar["t"]), UTC).astimezone(EASTERN)
            close = float(bar["c"])
        except (KeyError, TypeError, ValueError):
            continue
        if not time(9, 30) <= moment.time() < time(16, 0):
            continue
        day = moment.date()
        if day not in by_day or moment.timestamp() >= by_day[day][0]:
            by_day[day] = (moment.timestamp(), close)
    return [by_day[day][1] for day in sorted(by_day)]


def build_inputs(
    symbol: str,
    session: date,
    *,
    received_at: datetime | None = None,
    closes: Sequence[float] = (),
    last_close: float | None = None,
    external_dir: str | Path | None = None,
    baseline: Baseline | None = None,
    live: bool = True,
) -> tuple[MappingInputs, list[str]]:
    """The inputs for `symbol`'s `session`, and notes on what was missing.
    `closes` are the fund's daily closes before the session (oldest first);
    `last_close` defaults to the last of them."""
    notes: list[str] = []
    implied, source = implied_move(symbol, session, external_dir)
    if implied is None:
        notes.append(f"no implied-move cross-check: {source}")
    realised = realised_sigma_pct(closes)
    if realised is None:
        notes.append("too few closes for the realised volatility")
    if last_close is None and closes:
        last_close = float(closes[-1])
    inputs = MappingInputs(
        symbol=symbol.upper(),
        session=session,
        received_at=received_at,
        last_close=last_close,
        implied_move_pct=implied,
        implied_source=source if implied is not None else None,
        proxy_move_pct=proxy_move(implied, realised),
        calendar=calendar_catalysts(session, live=live),
        baseline=baseline if baseline is not None else baseline_for(symbol),
    )
    return inputs, notes


__all__ = [
    "IMPLIED_INDEX",
    "MAX_AGE_DAYS",
    "REALISED_SESSIONS",
    "build_inputs",
    "calendar_catalysts",
    "closes_from_bars",
    "implied_move",
    "proxy_move",
    "realised_sigma_pct",
]
