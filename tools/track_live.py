#!/usr/bin/env python
"""Live against backtest, session by session: what each deployment did, how
its orders filled, and what a backtest of the same algorithm did on the same
days.

    python tools/track_live.py --all                      # every deployment, once
    python tools/track_live.py --deployment fidelity
    python tools/track_live.py --all --no-shadow          # the journals only
    python tools/track_live.py --all --daily 20:40        # now, then daily, Eastern
    python tools/track_live.py --report                   # print what is stored

docker-compose.yml's `tracking` service runs the --daily form. It reads the
deployments of config/deployments.yaml: each one's config, the journals its
trader writes in its control directory (engine/trading/control_inbox.py)
and the algorithm override beside its ledger. It writes only
output/tracking/ (--out): `<id>/sessions.jsonl`, one row a session, and
`report.md`.

--------------------------------------------------------------------
WHY IT KEEPS ITS OWN ROWS

A trader's journals hold its newest ten sessions. Every run folds those
into sessions.jsonl, where a session is kept for good, so the record grows
past the journals' window. A session still in the journals is recomputed
(its day may not have been over last time); an older one is left as stored.

--------------------------------------------------------------------
WHAT A SESSION'S ROW SAYS

  availability  The bars the trader traded on, within the regular session:
                the first and the last, and the longest gap between two.
                `missed` with none; `partial` when it started LATE_MINUTES
                late, stopped that early, or went GAP_MINUTES without a bar.
                Not a count of bars: a thin fund's feed has minutes with no
                print. For a Fidelity deployment, also how long its bridge
                was not ready inside the day it trades, and the reasons
                (the bridge host's event journal) -- and the same for the
                regular session alone, 09:30-16:00, where a day that starts
                at 07:00 and a sign-in that came at 08:30 do not count.
  activity      Orders placed, filled, cancelled and expired; buys and
                their value; sells, their proceeds and realised profit;
                sales below cost.
  execution     For each filled order, its average price against its limit
                in basis points (positive is worse for the trader), beside
                what the config's cost model charges a backtest for that
                bar (base_bps + vol_multiplier x the bar's move). And the
                share of placed orders that filled: a backtest fills every
                trigger.
  shadow        A backtest of the algorithm IN FORCE TODAY -- the config's,
                with any override laid over it -- on the warehouse's bars, from
                the first tracked session, with the config's own costs,
                fills and capital: its buys, sells, realised profit and
                return each session.

--------------------------------------------------------------------
WHAT THE SHADOW IS NOT

The shadow is today's algorithm run over every tracked session; each row
records the algorithm it was first tracked under, and the report says when
that changed. Sessions first seen on the tool's first run all carry that
day's.

The shadow starts from cash on the first tracked session. The live book
may have started earlier and carry lots the shadow never bought, and once
two books differ their later trades differ too. Its profit is "what the
algorithm does with every session traded and every trigger filled at the
modelled cost", to hold beside what was realised; it is exact only for a
trial begun on a fresh ledger. The execution figures need no such caveat:
they are measured order by order.

The warehouse's bars are the consolidated tape; a trader's own feed may be
IEX. The shadow says which bars it used.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import signal
import statistics
import sys
import time
from collections.abc import Callable, Iterable
from datetime import UTC, date, datetime, timedelta
from datetime import time as clock_time
from itertools import pairwise
from pathlib import Path
from typing import Any

_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from engine.core.trading_calendar import EASTERN, sessions_between

REGULAR_OPEN, REGULAR_CLOSE = clock_time(9, 30), clock_time(16, 0)
LATE_MINUTES = 15
GAP_MINUTES = 30
JOURNAL_WINDOW = 10  # sessions a trader's journals keep (control_inbox.JOURNAL_SESSIONS)
RETRY_SECONDS = 3600
DEFAULT_OUT = _REPO_ROOT / "output" / "tracking"
FINAL_EVENTS = ("filled", "cancelled", "canceled", "expired", "rejected")


def _eastern(seconds: float) -> datetime:
    return datetime.fromtimestamp(float(seconds), UTC).astimezone(EASTERN)


def session_of(seconds: float) -> date:
    return _eastern(seconds).date()


def _at(day: date, at: clock_time) -> float:
    return datetime.combine(day, at, tzinfo=EASTERN).timestamp()


# --------------------------------------------------------------------
# Availability
# --------------------------------------------------------------------


def regular_bars(bars: Iterable[dict], day: date) -> list[dict]:
    """`day`'s regular-session bars, one per minute stamp (the journal can
    hold a bar many times over), in time order."""
    start, end = _at(day, REGULAR_OPEN), _at(day, REGULAR_CLOSE)
    by_stamp = {int(b["t"]): b for b in bars if start <= float(b.get("t", 0)) < end}
    return [by_stamp[t] for t in sorted(by_stamp)]


def availability(bars: list[dict], day: date) -> dict[str, Any]:
    """Whether the trader was watching `day`'s regular session (module
    docstring, availability), from its bars as regular_bars returns them."""
    if not bars:
        return {"status": "missed", "bars": 0, "why": "no bars journaled in the regular session"}
    opened, closed = _at(day, REGULAR_OPEN), _at(day, REGULAR_CLOSE)
    stamps = [float(b["t"]) for b in bars]
    late = (stamps[0] - opened) / 60
    early = (closed - 60 - stamps[-1]) / 60  # the last bar is the 15:59 one
    gap = max((b - a) / 60 for a, b in pairwise(stamps)) if len(stamps) > 1 else 0
    why = []
    if late >= LATE_MINUTES:
        why.append(f"first bar {late:.0f} min after the open")
    if early >= LATE_MINUTES:
        why.append(f"last bar {early:.0f} min before the close")
    if gap >= GAP_MINUTES:
        why.append(f"{gap:.0f} min without a bar")
    return {
        "status": "partial" if why else "traded",
        "bars": len(bars),
        "first": _eastern(stamps[0]).strftime("%H:%M"),
        "last": _eastern(stamps[-1]).strftime("%H:%M"),
        "longest_gap_minutes": round(gap, 1),
        **({"why": "; ".join(why)} if why else {}),
    }


def not_ready(events: Iterable[dict], start: float, end: float) -> dict[str, Any] | None:
    """How long a bridge was not ready within [start, end), from its host's
    `ready` / `not_ready` events in time order, and why. None when the
    journal says nothing about the span (no event at or before its end)."""
    state: bool | None = None
    since = start
    seconds = 0.0
    reasons: dict[str, float] = {}
    reason = ""
    seen = False
    for event in sorted(events, key=lambda e: float(e.get("t", 0))):
        kind, at = event.get("kind"), float(event.get("t", 0))
        if kind not in ("ready", "not_ready") or at >= end:
            continue
        seen = True
        if at > start and state is False:
            span = at - max(since, start)
            seconds += span
            reasons[reason] = reasons.get(reason, 0.0) + span
        state, since = kind == "ready", at
        reason = _reason(event.get("detail"))
    if not seen:
        return None
    if state is False:
        span = end - max(since, start)
        seconds += span
        reasons[reason] = reasons.get(reason, 0.0) + span
    worst = sorted(reasons.items(), key=lambda item: -item[1])[:3]
    return {
        "minutes": round(seconds / 60, 1),
        "share": round(seconds / (end - start), 4) if end > start else 0.0,
        "reasons": [{"why": why, "minutes": round(s / 60, 1)} for why, s in worst if s > 0],
    }


def _reason(detail: Any) -> str:
    """A not-ready event's cause in a few words: what precedes the first
    colon after "Not ready", without addresses or numbers that vary."""
    text = str(detail or "").removeprefix("Not ready: ").strip()
    head, _, rest = text.partition(":")
    words = (rest.split(".")[0].split("(")[0].strip() or head).strip()
    return f"{head.strip()}: {words}"[:100] if rest else head.strip()[:100]


# --------------------------------------------------------------------
# Activity and execution
# --------------------------------------------------------------------


def activity(fills: Iterable[dict], orders: Iterable[dict]) -> dict[str, Any]:
    buys = [f for f in fills if f.get("side") == "buy"]
    sells = [f for f in fills if f.get("side") == "sell"]
    events: dict[str, int] = {}
    for row in orders:
        name = str(row.get("event"))
        events[name] = events.get(name, 0) + 1
    return {
        "orders_placed": events.get("placed", 0),
        "orders_filled": events.get("filled", 0),
        "orders_cancelled": events.get("cancelled", 0) + events.get("canceled", 0),
        "orders_expired": events.get("expired", 0),
        "buys": len(buys),
        "buy_value": round(sum(float(f.get("value") or 0) for f in buys), 2),
        "sells": len(sells),
        "proceeds": round(sum(float(f.get("proceeds") or 0) for f in sells), 2),
        "realized_pnl": round(sum(float(f.get("pnl") or 0) for f in sells), 2),
        "loss_sales": sum(1 for f in sells if float(f.get("pnl") or 0) < -1e-8),
    }


def model_bps(bars: list[dict], at: float, base_bps: float, vol_multiplier: float) -> float | None:
    """What engine/execution/cost_models.DynamicSlippageModel charges for
    the bar an order placed at `at` belongs to: base_bps plus vol_multiplier
    x that bar's move against the close before it, in basis points. None
    when the bars do not reach it."""
    stamps = [float(b["t"]) for b in bars]
    index = max((i for i, t in enumerate(stamps) if t <= at), default=None)
    if index is None or at - stamps[index] > 180:
        return None
    if index == 0 or not bars[index - 1].get("c"):
        return base_bps
    previous = float(bars[index - 1]["c"])
    move = abs(float(bars[index]["c"]) - previous) / previous
    return base_bps + vol_multiplier * move * 1e4


def execution(
    orders: Iterable[dict], bars: list[dict], base_bps: float, vol_multiplier: float
) -> list[dict]:
    """One row per order that filled (module docstring, execution). `bars`
    are the day's journaled bars, deduped and in time order."""
    by_order: dict[str, list[dict]] = {}
    for row in orders:
        by_order.setdefault(str(row.get("order")), []).append(row)
    out = []
    for rows in by_order.values():
        rows.sort(key=lambda r: float(r.get("t", 0)))
        placed = next((r for r in rows if r.get("event") == "placed"), None)
        done = next((r for r in reversed(rows) if r.get("avg_price") and r.get("filled_qty")), None)
        if placed is None or done is None or not placed.get("limit"):
            continue
        limit, price = float(placed["limit"]), float(done["avg_price"])
        sign = 1.0 if placed.get("kind") == "buy" else -1.0
        out.append(
            {
                "kind": placed.get("kind"),
                "window": placed.get("session"),
                "qty": float(done["filled_qty"]),
                "limit": limit,
                "price": price,
                "live_bps": round(sign * (price - limit) / limit * 1e4, 2),
                "model_bps": _round(model_bps(bars, float(placed["t"]), base_bps, vol_multiplier)),
                "seconds_to_fill": round(float(done["t"]) - float(placed["t"]), 1),
            }
        )
    return out


def _round(value: float | None, places: int = 2) -> float | None:
    return None if value is None else round(value, places)


def execution_summary(rows: list[dict], placed: int) -> dict[str, Any]:
    """Across filled orders: the value-weighted and median slippage against
    the limit, the model's for the same bars, and the share that filled."""
    if not rows:
        return {"filled": 0, "placed": placed, "fill_share": 0.0 if placed else None}
    weights = [r["qty"] * r["price"] for r in rows]
    total = sum(weights)
    modelled = [
        (r["model_bps"], w)
        for r, w in zip(rows, weights, strict=True)
        if r["model_bps"] is not None
    ]
    return {
        "filled": len(rows),
        "placed": placed,
        "fill_share": round(len(rows) / placed, 4) if placed else None,
        "live_bps": round(
            sum(r["live_bps"] * w for r, w in zip(rows, weights, strict=True)) / total, 2
        ),
        "live_bps_median": round(statistics.median(r["live_bps"] for r in rows), 2),
        "model_bps": (
            round(sum(b * w for b, w in modelled) / sum(w for _, w in modelled), 2)
            if modelled
            else None
        ),
        "seconds_to_fill_median": round(statistics.median(r["seconds_to_fill"] for r in rows), 1),
    }


# --------------------------------------------------------------------
# A session, and a deployment's sessions
# --------------------------------------------------------------------


def track_session(
    day: date,
    *,
    bars: list[dict],
    fills: list[dict],
    orders: list[dict],
    events: list[dict] | None = None,
    span: tuple[float, float] | None = None,
    base_bps: float = 0.0,
    vol_multiplier: float = 0.0,
    bars_kept: bool = True,
) -> dict[str, Any]:
    """`day`'s row from the journal rows of that day. `events` and `span`
    (the day the deployment trades, epoch seconds) are a Fidelity bridge's.
    `bars_kept` False says the bar journal no longer reaches `day` (it keeps
    fewer sessions than a quiet fill journal does), so nothing can be said
    of whether the trader was watching."""
    all_bars = sorted({int(b["t"]): b for b in bars}.values(), key=lambda b: b["t"])
    regular = regular_bars(all_bars, day)
    watched = (
        availability(regular, day)
        if bars_kept
        else {"status": "unknown", "bars": 0, "why": "its bars are no longer in the journal"}
    )
    done = execution(orders, all_bars, base_bps, vol_multiplier)
    acts = activity(fills, orders)
    row: dict[str, Any] = {
        "session": day.isoformat(),
        "availability": watched,
        "activity": acts,
        "execution": execution_summary(done, acts["orders_placed"]),
        "orders": done,
    }
    if events is not None and span is not None:
        row["bridge_not_ready"] = not_ready(events, *span)
        row["bridge_not_ready_regular"] = not_ready(
            events, _at(day, REGULAR_OPEN), _at(day, REGULAR_CLOSE)
        )
    return row


def by_session(rows: Iterable[dict]) -> dict[date, list[dict]]:
    out: dict[date, list[dict]] = {}
    for row in rows:
        if "t" in row:
            out.setdefault(session_of(row["t"]), []).append(row)
    return out


def cost_settings(config) -> tuple[float, float]:
    """(base_bps, vol_multiplier) of the config's cost model; a model that
    is not dynamic slippage charges its flat bps and no volatility part."""
    costs = config.costs
    if getattr(costs, "model_type", None) == "dynamic_slippage":
        return float(costs.base_bps or 0.0), float(costs.vol_multiplier or 0.0)
    return float(getattr(costs, "slippage_bps", 0.0) or 0.0), 0.0


def track_deployment(deployment, now: datetime) -> list[dict]:
    """A row for every session the deployment's journals reach, oldest
    first, through the last one that is over at `now`. Sessions inside the
    journals' span with nothing journaled are rows too: `missed`."""
    inbox = deployment.inbox()
    if inbox is None:
        return []
    config = deployment.config()
    bars = by_session(inbox.bars(JOURNAL_WINDOW))
    fills = by_session(inbox.fills(JOURNAL_WINDOW))
    orders = by_session(inbox.orders(JOURNAL_WINDOW))
    seen = sorted({*bars, *fills, *orders})
    if not seen:
        return []
    bridge = deployment.bridge_inbox() if config.live.fidelity is not None else None
    events = bridge.events(14) if bridge is not None else None
    calendar = None
    if events is not None:
        from engine.core.venue_sessions import VenueCalendar

        calendar = VenueCalendar("fidelity", config.live.traded_sessions)
    base_bps, vol_multiplier = cost_settings(config)
    local = now.astimezone(EASTERN)
    last = local.date() if local.time() >= REGULAR_CLOSE else local.date() - timedelta(days=1)
    rows = []
    for day in sessions_between(seen[0] - timedelta(days=1), min(last, max(seen[-1], last))):
        if day > last:
            break
        span = None
        if calendar is not None:
            window = calendar.day_span(day)
            span = (
                (window[0].timestamp(), min(window[1].timestamp(), now.timestamp()))
                if window
                else None
            )
        rows.append(
            track_session(
                day,
                bars=bars.get(day, []),
                fills=fills.get(day, []),
                orders=orders.get(day, []),
                events=events,
                span=span,
                base_bps=base_bps,
                vol_multiplier=vol_multiplier,
                bars_kept=bool(bars) and day >= min(bars),
            )
        )
    return rows


# --------------------------------------------------------------------
# The shadow backtest
# --------------------------------------------------------------------


def algorithm_in_force(deployment) -> tuple[dict, str]:
    """What the deployment's next session trades -- its config file's
    algorithm with the override beside its ledger laid over it, when the
    deployment lets one apply -- and where it came from ("config" or
    "override"). Read, never written."""
    from research.strategies.live_algorithm import override_path

    config = deployment.config()
    algorithm = {
        "strategy_id": config.strategy.strategy_id,
        "strategy_params": dict(config.strategy.strategy_params or {}),
        "step": config.live.step,
        "profit_target": config.live.profit_target,
    }
    bridge = config.live.fidelity.bridge if config.live.fidelity else None
    if not (deployment.caps.algorithm_changes or (bridge and bridge.allow_algorithm_changes)):
        return algorithm, "config"
    try:
        data = json.loads(override_path(deployment.state_db).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return algorithm, "config"
    if not isinstance(data, dict) or not data.get("strategy_id"):
        return algorithm, "config"
    return {key: data.get(key, algorithm[key]) for key in algorithm}, "override"


def shadow_config(config, algorithm: dict):
    """The deployment's config as a single-point backtest of `algorithm`:
    its own costs, fill model, risk limits and capital; the grid is the
    live step and target."""
    from engine.core.config import BacktestConfig
    from research.strategies.strategy_registry import may_realize_loss

    data = config.to_dict()
    data["strategy"] = {
        "strategy_id": algorithm["strategy_id"],
        "strategy_params": dict(algorithm.get("strategy_params") or {}),
    }
    data["grid"] = {"steps": [algorithm["step"]], "profit_targets": [algorithm["profit_target"]]}
    data.setdefault("execution", {})["allow_signal_exit"] = may_realize_loss(
        algorithm["strategy_id"], data["strategy"]["strategy_params"]
    )
    data.setdefault("output", {})["return_full_results"] = False
    data.pop("live", None)  # a backtest: nothing here may be taken for a deployment
    return BacktestConfig.from_dict(data)


def shadow_sessions(config, since: date, *, load: Callable[[str], Any] | None = None) -> dict:
    """{session ISO date: {"buys", "sells", "realized_pnl", "return_pct"}}
    from a backtest of `config` on the warehouse's bars from `since`, the
    strategy warmed with the history before it. `load(symbol)` gives the
    bars (default: engine.warehouse.bars.load_frame)."""
    import pandas as pd

    from research.optimization.optimization_controller import OptimizationController
    from research.strategies.natr_regime import daily_bars
    from research.strategies.strategy_registry import resolve_strategy, session_bars

    if load is None:
        from engine.warehouse.bars import load_frame as load
    cls = resolve_strategy(config.strategy.strategy_id)
    full = session_bars(cls, load(config.backtest.symbol), config.strategy.strategy_params)
    start = pd.Timestamp(datetime.combine(since, clock_time(0, 0), tzinfo=EASTERN)).tz_convert(
        "UTC"
    )
    frame = full[full.index >= start]
    if frame.empty:
        raise ValueError(f"the warehouse has no {config.backtest.symbol} bars from {since}")
    kwargs = config.to_run_sweep_kwargs(cls)
    kwargs.update(n_jobs=1, return_full_results=False)
    history = full[full.index < frame.index[0]]
    if callable(getattr(cls, "warm_up", None)) and not history.empty:
        daily = daily_bars(history)
        if "volume" in history.columns:
            daily["volume"] = history["volume"].resample("1D").sum().reindex(daily.index)
        kwargs["warm_up_daily"] = daily
    out: dict[str, dict] = {}

    class Sink:  # the one configuration, reduced to its sessions, then let go
        def open_sweep(self, **_):
            return "track_live"

        def record(self, *, row, sim_result, elapsed_ms):
            curve = sim_result.equity_curve
            days = pd.DatetimeIndex(curve.index).tz_convert(EASTERN).tz_localize(None).normalize()
            equity = pd.Series(curve.to_numpy(float), index=days).groupby(level=0).last()
            previous = float(config.backtest.initial_cash)
            for day, value in equity.items():
                out[str(day.date())] = {
                    "buys": 0,
                    "sells": 0,
                    "realized_pnl": 0.0,
                    "return_pct": round((float(value) / previous - 1) * 100, 4)
                    if previous
                    else 0.0,
                }
                previous = float(value)
            blotter = sim_result.trade_blotter
            if blotter is None or blotter.empty:
                return
            when = pd.to_datetime(blotter["timestamp"], utc=True).dt.tz_convert(EASTERN)
            for stamp, side, pnl in zip(
                when,
                blotter["side"],
                blotter.get("profit_realized", [0.0] * len(blotter)),
                strict=True,
            ):
                entry = out.get(str(stamp.date()))
                if entry is None:
                    continue
                if side == "buy":
                    entry["buys"] += 1
                else:
                    entry["sells"] += 1
                    if pnl is not None and not (isinstance(pnl, float) and math.isnan(pnl)):
                        entry["realized_pnl"] = round(entry["realized_pnl"] + float(pnl), 2)

        def close_sweep(self):
            pass

    OptimizationController(historical_data=frame).run_sweep(**kwargs, result_sink=Sink())
    return out


# --------------------------------------------------------------------
# The stored record
# --------------------------------------------------------------------


def load_rows(path: Path) -> dict[str, dict]:
    """sessions.jsonl as {session: row}; a line that does not parse is skipped."""
    rows: dict[str, dict] = {}
    if not path.exists():
        return rows
    for line in path.read_text(encoding="utf-8").splitlines():
        try:
            row = json.loads(line)
        except ValueError:
            continue
        if isinstance(row, dict) and row.get("session"):
            rows[str(row["session"])] = row
    return rows


def merge_rows(stored: dict[str, dict], fresh: list[dict]) -> dict[str, dict]:
    """`fresh` over `stored`: a session the journals still hold is replaced,
    an older one kept (module docstring, WHY IT KEEPS ITS OWN ROWS)."""
    merged = dict(stored)
    for row in fresh:
        before = merged.get(row["session"], {})
        merged[row["session"]] = {**before, **row}
        if before.get("algorithm"):  # what it traded when first tracked stays
            merged[row["session"]]["algorithm"] = before["algorithm"]
    return dict(sorted(merged.items()))


def write_atomic(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    partial = path.with_name(f".{path.name}.partial")
    partial.write_text(text, encoding="utf-8")
    os.replace(partial, path)


def store(path: Path, rows: dict[str, dict]) -> None:
    write_atomic(path, "".join(json.dumps(row, sort_keys=True) + "\n" for row in rows.values()))


# --------------------------------------------------------------------
# The report
# --------------------------------------------------------------------


def _not_ready_share(spans: list[dict]) -> float | None:
    """Minutes not ready over the minutes the spans cover; None with none."""
    if not spans:
        return None
    covered = sum(b["minutes"] / b["share"] for b in spans if b["share"])
    return round(sum(b["minutes"] for b in spans) / covered, 4) if covered else 0.0


def summarize(rows: list[dict]) -> dict[str, Any]:
    """Totals over stored rows: sessions by status, what was realised, how
    orders filled, and the shadow beside them where it ran."""
    status = [r["availability"]["status"] for r in rows]
    orders = [o for r in rows for o in r.get("orders", [])]
    placed = sum(r["activity"]["orders_placed"] for r in rows)
    shadowed = [r for r in rows if r.get("shadow")]
    bridge = [r["bridge_not_ready"] for r in rows if r.get("bridge_not_ready")]
    regular = [r["bridge_not_ready_regular"] for r in rows if r.get("bridge_not_ready_regular")]
    return {
        "sessions": len(rows),
        "traded": status.count("traded"),
        "partial": status.count("partial"),
        "missed": status.count("missed"),
        "unknown": status.count("unknown"),
        "buys": sum(r["activity"]["buys"] for r in rows),
        "sells": sum(r["activity"]["sells"] for r in rows),
        "realized_pnl": round(sum(r["activity"]["realized_pnl"] for r in rows), 2),
        "loss_sales": sum(r["activity"]["loss_sales"] for r in rows),
        "execution": execution_summary(orders, placed),
        "bridge_not_ready_share": _not_ready_share(bridge),
        "bridge_not_ready_regular_share": _not_ready_share(regular),
        "bridge_not_ready_regular_minutes": (
            round(sum(b["minutes"] for b in regular), 1) if regular else None
        ),
        "shadow": (
            {
                "sessions": len(shadowed),
                "buys": sum(r["shadow"]["buys"] for r in shadowed),
                "sells": sum(r["shadow"]["sells"] for r in shadowed),
                "realized_pnl": round(sum(r["shadow"]["realized_pnl"] for r in shadowed), 2),
                "return_pct": round(
                    (math.prod(1 + r["shadow"]["return_pct"] / 100 for r in shadowed) - 1) * 100, 3
                ),
                "live_realized_pnl": round(sum(r["activity"]["realized_pnl"] for r in shadowed), 2),
            }
            if shadowed
            else None
        ),
    }


def _bps(value: float | None) -> str:
    return "n/a" if value is None else f"{value:+.1f} bp"


def report(deployment_id: str, rows: list[dict], meta: dict) -> str:
    total = summarize(rows)
    done = total["execution"]
    algorithms = list(dict.fromkeys(r["algorithm"] for r in rows if r.get("algorithm")))
    lines = [
        f"## {deployment_id}",
        "",
        f"{meta.get('label', deployment_id)}: {meta.get('algorithm', 'algorithm unknown')} on "
        f"{meta.get('symbol', '?')}, tracked from {rows[0]['session']} to {rows[-1]['session']}.",
        "",
        f"- **Sessions:** {total['sessions']}: {total['traded']} traded, {total['partial']} partial, "
        f"{total['missed']} missed"
        + (f", {total['unknown']} older than the bar journal" if total["unknown"] else "")
        + ".",
    ]
    if total["bridge_not_ready_share"] is not None:
        inside = total.get("bridge_not_ready_regular_share")
        lines.append(
            f"- **Bridge not ready:** {total['bridge_not_ready_share'] * 100:.0f}% of the hours it trades"
            + (
                f"; {inside * 100:.1f}% of the regular session "
                f"({total['bridge_not_ready_regular_minutes']:.0f} min in all)."
                if inside is not None
                else "."
            )
        )
    lines.append(
        f"- **Live:** {total['buys']} buys, {total['sells']} sells, ${total['realized_pnl']:,.2f} "
        f"realised, {total['loss_sales']} sale(s) below cost."
    )
    if done["filled"]:
        lines.append(
            f"- **Execution:** {done['filled']} of {done['placed']} orders filled "
            f"({(done['fill_share'] or 0) * 100:.0f}%); against the limit {_bps(done['live_bps'])} "
            f"(median {_bps(done['live_bps_median'])}); the cost model charges "
            f"{_bps(done['model_bps'])} for the same bars; median {done['seconds_to_fill_median']:.0f} s to fill."
        )
    elif done["placed"]:
        lines.append(f"- **Execution:** none of {done['placed']} placed orders filled.")
    shadow = total["shadow"]
    if shadow:
        lines.append(
            f"- **Shadow backtest** ({meta.get('shadow_bars', 'warehouse bars')}, "
            f"${meta.get('capital', 0):,.0f}, over {shadow['sessions']} session(s)): {shadow['buys']} buys, "
            f"{shadow['sells']} sells, ${shadow['realized_pnl']:,.2f} realised, {shadow['return_pct']:+.2f}% "
            f"return; live realised ${shadow['live_realized_pnl']:,.2f} over the same sessions."
        )
    elif meta.get("shadow_error"):
        lines.append(f"- **Shadow backtest:** not run: {meta['shadow_error']}")
    bought = sum(r["activity"]["buy_value"] for r in rows)
    if shadow and meta.get("capital") and bought > float(meta["capital"]):
        lines.append(
            f"- **The shadow's capital is not the account's.** The live book bought ${bought:,.0f} "
            f"over these sessions, more than the ${meta['capital']:,.0f} the config gives a backtest "
            "(backtest.initial_cash). Compare counts and returns, not dollars."
        )
    if len(algorithms) > 1:
        lines.append(
            "- **The algorithm changed while tracked** (" + "; then ".join(algorithms) + "). The "
            "shadow is today's algorithm over every session, so it is comparable only from the change."
        )
    lines += [
        "",
        "| Session | Status | Bars | Bridge not ready | Placed / filled | Buys | Sells | Realised | "
        "Fill vs limit | Model | Shadow buys / sells | Shadow realised | Shadow return |",
        "|---|---|---|---|---|---|---|---|---|---|---|---|---|",
    ]
    for row in rows:
        have, act, ex = row["availability"], row["activity"], row["execution"]
        bridge = row.get("bridge_not_ready")
        inside = row.get("bridge_not_ready_regular")
        shadow = row.get("shadow")
        status = have["status"] + (f" ({have['why']})" if have.get("why") else "")
        away = "" if not bridge else f"{round(bridge['minutes'])} min"
        if bridge and inside:
            away += f" ({round(inside['minutes'])} regular)"
        lines.append(
            f"| {row['session']} | {status} | {have['bars']} | {away} | "
            f"{act['orders_placed']} / {act['orders_filled']} | {act['buys']} | {act['sells']} | "
            f"${act['realized_pnl']:,.2f} | {_bps(ex.get('live_bps')) if ex['filled'] else ''} | "
            f"{_bps(ex.get('model_bps')) if ex['filled'] else ''} | "
            + (
                f"{shadow['buys']} / {shadow['sells']} | ${shadow['realized_pnl']:,.2f} | "
                f"{shadow['return_pct']:+.2f}% |"
                if shadow
                else " | | |"
            )
        )
    reasons: dict[str, float] = {}
    for row in rows:
        for item in (row.get("bridge_not_ready") or {}).get("reasons", []):
            reasons[item["why"]] = reasons.get(item["why"], 0.0) + item["minutes"]
    if reasons:
        lines += ["", "Why the bridge was not ready, by time:", ""]
        lines += [
            f"- {why}: {minutes / 60:.1f} h"
            for why, minutes in sorted(reasons.items(), key=lambda item: -item[1])[:5]
        ]
    return "\n".join(lines) + "\n"


# --------------------------------------------------------------------
# A run, and the daily loop
# --------------------------------------------------------------------


def run_deployment(
    deployment, out: Path, now: datetime, *, shadow: bool = True, load=None
) -> str | None:
    """Track one deployment into `out`/<id>/ and return its report, or None
    when its trader has journaled nothing yet."""
    path = out / deployment.id / "sessions.jsonl"
    fresh = track_deployment(deployment, now)
    config = deployment.config()
    algorithm, source = algorithm_in_force(deployment)
    named = (
        f"{algorithm['strategy_id']} step {algorithm['step']} target {algorithm['profit_target']}"
    )
    for row in fresh:
        row["algorithm"] = named
    rows = merge_rows(load_rows(path), fresh)
    if not rows:
        return None
    meta: dict[str, Any] = {
        "label": deployment.label,
        "symbol": config.backtest.symbol,
        "algorithm": f"{algorithm['strategy_id']} (step {algorithm['step']}, target "
        f"{algorithm['profit_target']}; from the {source})",
        "capital": float(config.backtest.initial_cash),
        "shadow_bars": "warehouse bars",
    }
    if shadow:
        try:
            since = date.fromisoformat(next(iter(rows)))
            found = shadow_sessions(shadow_config(config, algorithm), since, load=load)
            for session, row in rows.items():
                row["shadow"] = found.get(session)
        except Exception as exc:  # the journals' record stands without it
            meta["shadow_error"] = f"{type(exc).__name__}: {exc}"[:300]
    store(path, rows)
    text = report(deployment.id, list(rows.values()), meta)
    write_atomic(out / deployment.id / "report.md", text)
    return text


def run_once(
    deployments: list, out: Path, now: datetime, *, shadow: bool = True, report_to=print
) -> bool:
    """Track every deployment; one that fails is a line, and the run fails."""
    ok, parts = True, []
    for deployment in deployments:
        try:
            text = run_deployment(deployment, out, now, shadow=shadow)
        except Exception as exc:
            report_to(f"[tracking] {deployment.id}: FAILED {type(exc).__name__}: {exc}"[:300])
            ok = False
            continue
        if text is None:
            report_to(f"[tracking] {deployment.id}: nothing journaled yet")
            continue
        parts.append(text)
        report_to(
            f"[tracking] {deployment.id}: {text.splitlines()[4] if len(text.splitlines()) > 4 else 'tracked'}"
        )
    if parts:
        header = f"# Live against backtest\n\nWritten {now.astimezone(EASTERN):%Y-%m-%d %H:%M %Z} by tools/track_live.py.\n\n"
        write_atomic(out / "report.md", header + "\n".join(parts))
    return ok


def next_run(now: datetime, at: clock_time) -> datetime:
    local = now.astimezone(EASTERN)
    candidate = datetime.combine(local.date(), at, tzinfo=EASTERN)
    if candidate <= local:
        candidate = datetime.combine(local.date() + timedelta(days=1), at, tzinfo=EASTERN)
    return candidate


def run_daily(
    at: clock_time,
    once: Callable[[], bool],
    *,
    now: Callable[[], datetime] = lambda: datetime.now(UTC),
    sleep: Callable[[float], None] = time.sleep,
    report_to: Callable[[str], None] = print,
    rounds: int | None = None,
) -> None:
    done = 0
    while rounds is None or done < rounds:
        ok = once()
        done += 1
        wake = next_run(now(), at)
        if not ok:
            wake = min(wake, now() + timedelta(seconds=RETRY_SECONDS))
        report_to(f"[tracking] next run {wake.astimezone(EASTERN):%Y-%m-%d %H:%M %Z}")
        sleep(max(0.0, (wake - now()).total_seconds()))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--deployment", nargs="+", help="these deployments (config/deployments.yaml)"
    )
    parser.add_argument("--all", action="store_true", help="every registered deployment")
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT, help="where the record is kept")
    parser.add_argument("--no-shadow", action="store_true", help="the journals only, no backtest")
    parser.add_argument("--daily", metavar="HH:MM", help="run now, then daily at this Eastern time")
    parser.add_argument("--report", action="store_true", help="print the stored report and exit")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.report:
        path = args.out / "report.md"
        if not path.exists():
            print(f"{path} does not exist yet: run tools/track_live.py --all", file=sys.stderr)
            return 1
        print(path.read_text(encoding="utf-8"))
        return 0
    from server import live_registry

    registered = live_registry.registry()
    wanted = list(registered) if args.all or not args.deployment else args.deployment
    unknown = sorted(set(wanted) - set(registered))
    if unknown:
        parser.error(
            f"not a registered deployment: {', '.join(unknown)} (known: {', '.join(registered)})"
        )
    at = None
    if args.daily:
        try:
            at = datetime.strptime(args.daily, "%H:%M").time()
        except ValueError:
            parser.error(f"--daily wants HH:MM, got {args.daily!r}")

    def deployments() -> list:
        # Re-read each run: a config written since the service started is picked up.
        found = live_registry.registry()
        return [
            found[name] for name in wanted if name in found and found[name].config_path.exists()
        ]

    def once() -> bool:
        return run_once(deployments(), args.out, datetime.now(UTC), shadow=not args.no_shadow)

    if at is None:
        return 0 if once() else 1

    def stop(signum, frame):  # PID 1 in a container: SIGTERM has no default action
        raise SystemExit(0)

    signal.signal(signal.SIGTERM, stop)
    run_daily(at, once)
    return 0


if __name__ == "__main__":
    sys.exit(main())
