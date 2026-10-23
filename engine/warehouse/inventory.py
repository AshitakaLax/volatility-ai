"""
What the warehouse holds, for the web UI's Warehouse tab
(server/warehouse_status.py): the bars per fund and how far behind each is,
the sweeps and simulations recorded, and what it all takes on disk.

--------------------------------------------------------------------
READ-ONLY, AND CHEAP ENOUGH TO POLL WHILE A SWEEP RUNS

Every query goes through bars._reading() -- WAREHOUSE_LOCK's read side, a
read-only open that waits out another process's write, closed on exit -- so
the server's own result writer waits for a status read rather than failing
it, and nothing here can write. Each function opens, queries and closes; no
result outlives its call. DuckDB gets STATUS_THREADS threads, not one per
core: the cores belong to the sweep, and these are aggregates over a few
million rows (the whole fund inventory took 0.8 s on 9.7M bars with every
core busy).

Nothing here raises. An absent warehouse, one another process holds, and a
missing duckdb all come back as a dict that says which, so a status page
can show it instead of a 500.

--------------------------------------------------------------------
WHAT "UP TO DATE" MEANS

Holding every bar through the last completed NYSE session
(engine/core/trading_calendar.py). Bars to add is an ESTIMATE: the sessions
missing times the fund's own median bars per session over its last
DENSITY_SESSIONS sessions -- 390 for a regular-hours fund, ~756 for one
kept with extended hours, ~211 for a thinly traded one with minutes that
never print. A flat 390 would be wrong for two of the eight funds here.
"""

from __future__ import annotations

import hashlib
import math
import os
import shutil
from collections.abc import Callable
from datetime import UTC, date, datetime, time, timedelta
from pathlib import Path
from typing import Any

from engine.core.trading_calendar import (
    EASTERN,
    last_completed_session,
    previous_session,
    sessions_between,
)
from engine.warehouse.bars import (
    FINGERPRINT_AGGREGATE,
    _reading,
    fingerprint_digest,
    warehouse_root,
)
from engine.warehouse.connection import (
    EXECUTIONS_DIR,
    EXTERNAL_DIR,
    MARKET_DATA_DB,
    OHLCV_DIR,
    SIM_RESULTS_DB,
)

# DuckDB threads for a status query (see the module docstring).
STATUS_THREADS = 4

# Sessions the bars-per-session median is taken over.
DENSITY_SESSIONS = 20

# A fund's last session counts as held only if it reaches this (Eastern):
# a regular-hours fund's last bar is 15:59, an extended-hours one's 19:59.
# Earlier means the session was fetched while it was still trading.
_FULL_SESSION_FROM = time(15, 30)

# The fund of a sweep: the server records it under server_run (its
# backtest.symbol was the request's default before 2026-10-20); a sweep
# from cli.py names it in backtest.symbol.
_SWEEP_FUND = (
    "COALESCE(json_extract_string(s.base_parameters, '$.server_run.ticker'), "
    "json_extract_string(s.base_parameters, '$.backtest.symbol'))"
)


def _finite(value: Any) -> float | None:
    """A float JSON can carry: Return/Drawdown is legitimately infinite, and
    a JSON response refuses inf and nan."""
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None


def _iso(value: Any) -> str | None:
    return value.isoformat() if value is not None else None


def _query(read: Callable[[Any], dict[str, Any]]) -> dict[str, Any]:
    """Run `read(con)` against a read-only connection, never raising.

    Every answer carries `available` (a warehouse exists here), `busy`
    (another process is holding it) and `error` (anything else that went
    wrong), so the caller can tell "empty" from "could not look".
    """
    errors: list[str] = []
    exists = (warehouse_root() / MARKET_DATA_DB).exists()
    try:
        with _reading(threads=STATUS_THREADS, errors=errors) as con:
            if con is None:
                reason = errors[0] if errors else None
                busy = bool(reason) and "lock" in reason.lower()
                return {
                    "available": exists,
                    "busy": busy,
                    "error": None if busy else reason,
                }
            body = read(con)
    except Exception as e:
        return {"available": exists, "busy": False, "error": f"{type(e).__name__}: {e}"}
    return {"available": True, "busy": False, "error": None, **body}


# --------------------------------------------------------------------
# Bars
# --------------------------------------------------------------------


def ohlcv_signature() -> str | None:
    """A cheap identity for the bar lake's current contents: its files'
    paths, sizes and modification times. It changes on every ingest and
    never otherwise, so the fund inventory -- the one scan of every bar --
    is redone only when it does. None when there is no lake."""
    lake = warehouse_root() / OHLCV_DIR
    if not lake.is_dir():
        return None
    listing = []
    for directory, _dirs, files in os.walk(lake):
        for name in files:
            path = Path(directory, name)
            try:
                stat = path.stat()
            except OSError:
                continue
            listing.append(f"{path.relative_to(lake)}:{stat.st_size}:{stat.st_mtime_ns}")
    return hashlib.sha256("\n".join(sorted(listing)).encode()).hexdigest()[:32]


def fund_inventory() -> dict[str, Any]:
    """Every fund with bars: its span, sessions, duplicates, recent density
    and fingerprint (the dataset_version a sweep run now would record), plus
    the assets dimension's description of it."""

    def read(con: Any) -> dict[str, Any]:
        try:
            rows = con.execute(
                f"""SELECT ticker, {FINGERPRINT_AGGREGATE},
                           COUNT(DISTINCT (timestamp AT TIME ZONE 'America/New_York')::DATE),
                           COUNT(DISTINCT timestamp)
                    FROM ohlcv GROUP BY ticker ORDER BY ticker"""
            ).fetchall()
        except Exception as e:
            if "ohlcv" in str(e):  # no lake yet: no view to read
                return {"funds": {}, "assets": _assets(con)}
            raise
        funds = {}
        for ticker, count, first, last, xor, sessions, distinct in rows:
            funds[ticker] = {
                "bars": int(count),
                "first": _iso(first),
                "last": _iso(last),
                "sessions": int(sessions),
                "duplicates": int(count - distinct),
                "fingerprint": fingerprint_digest((count, first, last, xor)),
                "bars_per_session": None,
                "last_session_bars": None,
            }
        if rows:
            # Only the last weeks are read: the lake is sorted by (ticker,
            # timestamp), so the row groups before this are skipped.
            since = min(row[3] for row in rows) - timedelta(days=60)
            density = con.execute(
                f"""WITH days AS (
                        SELECT ticker,
                               (timestamp AT TIME ZONE 'America/New_York')::DATE AS day,
                               COUNT(DISTINCT timestamp) AS n
                        FROM ohlcv WHERE timestamp >= ? GROUP BY ALL
                    ), ranked AS (
                        SELECT ticker, n,
                               row_number() OVER (PARTITION BY ticker ORDER BY day DESC) AS r
                        FROM days
                    )
                    SELECT ticker, median(n), max(n) FILTER (WHERE r = 1)
                    FROM ranked WHERE r <= {DENSITY_SESSIONS} GROUP BY ticker""",
                [since],
            ).fetchall()
            for ticker, median, last_day in density:
                if ticker in funds:
                    funds[ticker]["bars_per_session"] = _finite(median)
                    funds[ticker]["last_session_bars"] = int(last_day) if last_day else None
        return {"funds": funds, "assets": _assets(con)}

    return _query(read)


def _assets(con: Any) -> dict[str, dict[str, Any]]:
    try:
        rows = con.execute(
            "SELECT ticker, sector, active_from, leverage_ratio FROM market_data.assets"
        ).fetchall()
    except Exception:
        return {}
    return {
        ticker: {
            "sector": sector,
            "inception": _iso(active_from),
            "leverage": _finite(leverage),
        }
        for ticker, sector, active_from, leverage in rows
    }


def freshness(
    last_bar: str | datetime | None,
    bars_per_session: float | None,
    last_session_bars: int | None,
    now: datetime,
) -> dict[str, Any]:
    """How far one fund is from holding every bar through the last
    completed session, at `now` (tz-aware).

    A last session that stops before 15:30 Eastern was fetched mid-session
    and counts as missing, less the bars it already has.
    """
    through = last_completed_session(now)
    answer: dict[str, Any] = {
        "through": through.isoformat(),
        "last_session": None,
        "partial": False,
        "sessions_behind": None,
        "bars_to_add": None,
    }
    if last_bar is None:
        return answer
    if isinstance(last_bar, str):
        last_bar = datetime.fromisoformat(last_bar)
    local = last_bar.astimezone(EASTERN)
    held: date = local.date()
    partial = local.time() < _FULL_SESSION_FROM
    complete_through = previous_session(held) if partial else held
    behind = len(sessions_between(complete_through, through)) if complete_through < through else 0
    bars = None
    if bars_per_session:
        bars = behind * bars_per_session
        if partial and last_session_bars:
            bars -= min(last_session_bars, bars_per_session)
        bars = max(0, round(bars))
    answer.update(
        last_session=held.isoformat(), partial=partial, sessions_behind=behind, bars_to_add=bars
    )
    return answer


# --------------------------------------------------------------------
# Sweeps and simulations
# --------------------------------------------------------------------


def results_summary(now: datetime, hours: int = 48) -> dict[str, Any]:
    """The sweeps and simulations recorded: totals, the last `hours` hours'
    activity hour by hour, one row per sweep, and which bars (dataset
    version) each fund's simulations ran on.

    One row per SWEEP is returned -- bounded by runs x funds, not by
    configurations -- for the caller to group and trim.
    """
    hour_now = now.astimezone(UTC).replace(minute=0, second=0, microsecond=0)
    window_start = hour_now - timedelta(hours=hours - 1)

    def read(con: Any) -> dict[str, Any]:
        total, last_hour, last_day, mean_ms = con.execute(
            """SELECT COUNT(*),
                      COUNT(*) FILTER (WHERE completed_at >= ?),
                      COUNT(*) FILTER (WHERE completed_at >= ?),
                      AVG(execution_time_ms) FILTER (WHERE completed_at >= ?)
               FROM sim.simulations""",
            [now - timedelta(hours=1), now - timedelta(days=1), now - timedelta(hours=1)],
        ).fetchone()
        by_status = dict(
            con.execute(
                "SELECT status::VARCHAR, COUNT(*) FROM sim.simulations GROUP BY 1"
            ).fetchall()
        )
        counted = dict(
            con.execute(
                """SELECT date_trunc('hour', completed_at), COUNT(*) FROM sim.simulations
                   WHERE completed_at >= ? GROUP BY 1""",
                [window_start],
            ).fetchall()
        )
        hourly = []
        for step in range(hours):
            hour = window_start + timedelta(hours=step)
            hourly.append({"hour": hour.isoformat(), "n": int(counted.get(hour, 0))})

        sweeps = []
        for row in con.execute(
            f"""SELECT s.sweep_id, s.algorithm, s.created_at, {_SWEEP_FUND},
                       json_extract_string(s.base_parameters, '$.strategy.strategy_id'),
                       json_extract_string(s.base_parameters, '$.server_run.run_id'),
                       json_extract_string(s.base_parameters, '$.server_run.name'),
                       COUNT(m.simulation_id),
                       COUNT(m.simulation_id) FILTER (WHERE m.status = 'FAILED'),
                       MAX(m.completed_at),
                       MAX(m.total_return),
                       arg_max(m.max_drawdown, m.total_return),
                       arg_max(json_extract_string(m.metrics_json, '$."Return/Drawdown"'),
                               m.total_return)
                FROM sim.sweeps s LEFT JOIN sim.simulations m USING (sweep_id)
                GROUP BY ALL ORDER BY s.created_at DESC"""
        ).fetchall():
            (sweep_id, algorithm, created, fund, strategy, run_id, run_name) = row[:7]
            (simulations, failed, last, best_return, best_drawdown, calmar) = row[7:]
            sweeps.append(
                {
                    "id": sweep_id,
                    "algorithm": algorithm,
                    "created": _iso(created),
                    "fund": fund,
                    "strategy": strategy,
                    "run_id": run_id,
                    "run_name": run_name,
                    "simulations": int(simulations),
                    "failed": int(failed),
                    "last": _iso(last),
                    "best_return": _finite(best_return),
                    "best_drawdown": _finite(best_drawdown),
                    "best_calmar": _finite(calmar),
                }
            )

        versions = [
            {"fund": fund, "dataset_version": version, "simulations": int(n)}
            for fund, version, n in con.execute(
                f"""SELECT {_SWEEP_FUND}, m.dataset_version, COUNT(*)
                    FROM sim.simulations m JOIN sim.sweeps s USING (sweep_id) GROUP BY ALL"""
            ).fetchall()
        ]

        try:
            rows, simulated = con.execute(
                "SELECT COUNT(*), COUNT(DISTINCT simulation_id) FROM sim.trade_executions"
            ).fetchone()
        except Exception:  # no executions lake yet: no view
            rows, simulated = 0, 0

        return {
            "sweeps": len(sweeps),
            "simulations": int(total),
            "last_hour": int(last_hour),
            "last_day": int(last_day),
            "mean_ms_last_hour": _finite(mean_ms),
            "by_status": {str(k): int(v) for k, v in by_status.items()},
            "hourly": hourly,
            "sweep_rows": sweeps,
            "versions": versions,
            "executions": {"rows": int(rows), "simulations": int(simulated)},
        }

    return _query(read)


# --------------------------------------------------------------------
# Storage
# --------------------------------------------------------------------


def _tree(path: Path) -> tuple[int, int]:
    """(files, bytes) under `path`, 0s when absent."""
    files = size = 0
    for directory, _dirs, names in os.walk(path):
        for name in names:
            try:
                size += Path(directory, name).stat().st_size
                files += 1
            except OSError:
                continue
    return files, size


def storage_summary() -> dict[str, Any]:
    """What the warehouse takes on disk -- read from the filesystem, so it
    answers even when DuckDB cannot open the files -- plus the small
    reference tables' row counts and the DuckDB version."""
    root = warehouse_root()
    catalogs = []
    for name in (MARKET_DATA_DB, f"{MARKET_DATA_DB}.wal", SIM_RESULTS_DB, f"{SIM_RESULTS_DB}.wal"):
        path = root / name
        if path.is_file():
            stat = path.stat()
            catalogs.append(
                {
                    "name": name,
                    "bytes": stat.st_size,
                    "modified": datetime.fromtimestamp(stat.st_mtime, UTC).isoformat(),
                }
            )

    by_fund: dict[str, int] = {}
    ohlcv = root / OHLCV_DIR
    if ohlcv.is_dir():
        for child in sorted(ohlcv.iterdir()):
            if child.is_dir() and child.name.startswith("ticker="):
                by_fund[child.name.removeprefix("ticker=")] = _tree(child)[1]
    lakes = {}
    for name in (OHLCV_DIR, EXECUTIONS_DIR, EXTERNAL_DIR):
        files, size = _tree(root / name)
        lakes[name] = {"files": files, "bytes": size}
    lakes[OHLCV_DIR]["by_fund"] = by_fund

    try:
        usage = shutil.disk_usage(root)
        disk = {"total": usage.total, "free": usage.free}
    except OSError:
        disk = None

    def read(con: Any) -> dict[str, Any]:
        def scalar(sql: str) -> int | None:
            try:
                return int(con.execute(sql).fetchone()[0])
            except Exception:
                return None

        try:
            events = {
                str(kind): int(n)
                for kind, n in con.execute(
                    "SELECT event_type, COUNT(*) FROM market_data.market_events GROUP BY 1"
                ).fetchall()
            }
        except Exception:
            events = {}
        try:
            external = [
                {"provider": provider, "series": int(n), "newest": _iso(newest)}
                for provider, n, newest in con.execute(
                    """SELECT provider, COUNT(*), MAX(last_date)
                       FROM market_data.external_series GROUP BY 1 ORDER BY 1"""
                ).fetchall()
            ]
        except Exception:
            external = []
        return {
            "duckdb": con.execute("SELECT library_version FROM pragma_version()").fetchone()[0],
            "tables": {
                "assets": scalar("SELECT COUNT(*) FROM market_data.assets"),
                "broker_environments": scalar("SELECT COUNT(*) FROM sim.broker_environments"),
                "market_events": events,
                "external_series": external,
            },
        }

    return {
        **_query(read),
        "root": str(root),
        "catalogs": catalogs,
        "lakes": lakes,
        "tmp_bytes": _tree(root / "tmp")[1],
        "disk": disk,
    }


__all__ = [
    "DENSITY_SESSIONS",
    "STATUS_THREADS",
    "freshness",
    "fund_inventory",
    "ohlcv_signature",
    "results_summary",
    "storage_summary",
]
