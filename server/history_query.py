"""Run History queries: filter, sort and page one fund's cells server-side.

WHY SERVER-SIDE. Run History used to download every cell of every
stored run and filter in the browser. With retention uncapped that is
unbounded -- one brute-force sweep alone is 170k cells -- so a query now
names a FUND (required) plus the same filters the browser applied, and
gets back one page.

THE RULES ARE A PORT of web/src/lib/filters.ts (filterHistoryRows,
historyFieldValue, sortHistoryRows, historyInputFields) as it stood,
so the table behaves exactly as before -- including the cases those
functions' tests pin:

  - a numeric field reads in the UNIT THE TABLE SHOWS: grid_step and
    profit_target as percents, param:<name> raw, metric:<key> raw,
    window_days as inclusive calendar days, window_bars as bars;
  - a field's filter is a set of exact values OR a band -- either one
    satisfied passes the row;
  - UNKNOWN IS NOT A MATCH: a row missing a gated field is excluded;
  - a simulation window matches by OVERLAP, inclusive of both ends;
  - sorting puts a missing value LAST in either direction, and a row
    with no recorded save time sorts as if saved now.
"""

from __future__ import annotations

import math
import threading
import time
from datetime import UTC, datetime
from typing import Any

from server.history import index_entries, index_generation

# A row's run-level fields, joined back from the run it came from.
RUN_FIELDS = (
    "name",
    "model",
    "fill",
    "start",
    "end",
    "saved_at",
    "batch_id",
    "batch_index",
    "batch_total",
)
SORT_COLUMNS = {
    "name",
    "ticker",
    "grid_step",
    "profit_target",
    "sizing_model",
    "metric",
    "cagr_pct",
    "max_drawdown_pct",
    "worst_year_pct",
    "total_trades",
    "window",
    "run_id",
    "saved_at",
}
MAX_PAGE = 500


def _number(value: Any) -> float | None:
    # bool is an int in Python but not a number in the browser's typeof.
    if isinstance(value, bool) or not isinstance(value, int | float):
        return None
    return float(value) if math.isfinite(value) else None


def _parse(ts: str | None) -> datetime | None:
    if not ts:
        return None
    try:
        parsed = datetime.fromisoformat(ts)
    except ValueError:
        return None
    # A bare date is UTC midnight, as `new Date("2026-01-01")` reads it.
    return parsed if parsed.tzinfo is not None else parsed.replace(tzinfo=UTC)


def field_value(row: dict[str, Any], key: str) -> float | None:
    """historyFieldValue: the value a numeric filter compares against."""
    if key == "grid_step":
        return None if row.get("grid") is None else row["grid"] * 100
    if key == "profit_target":
        return None if row.get("target") is None else row["target"] * 100
    if key == "window_bars":
        return _number(row.get("bars"))
    if key == "window_days":
        start, end = _parse(row.get("start")), _parse(row.get("end"))
        if start is None or end is None:
            return None
        return float(max(0, math.floor((end - start).total_seconds() / 86_400) + 1))
    if key.startswith("param:"):
        return _number((row.get("params") or {}).get(key[len("param:") :]))
    if key.startswith("metric:"):
        return _number((row.get("m") or {}).get(key[len("metric:") :]))
    return None


def _same(a: float, b: float) -> bool:
    return abs(a - b) <= 1e-9


def _active_numeric(filters: dict[str, Any]) -> list[str]:
    keys = {key for key, values in (filters.get("values") or {}).items() if values}
    for key, band in (filters.get("ranges") or {}).items():
        if band and (band.get("min") is not None or band.get("max") is not None):
            keys.add(key)
    return sorted(keys)


def _numeric_passes(row: dict[str, Any], key: str, filters: dict[str, Any]) -> bool:
    values = (filters.get("values") or {}).get(key) or []
    band = (filters.get("ranges") or {}).get(key) or {}
    low, high = band.get("min"), band.get("max")
    has_values, has_band = bool(values), low is not None or high is not None
    if not has_values and not has_band:
        return True
    actual = field_value(row, key)
    if actual is None:
        return False
    in_values = has_values and any(_same(float(v), actual) for v in values)
    in_band = has_band and (low is None or actual >= low) and (high is None or actual <= high)
    return bool(in_values or in_band)


def _window_matches(row: dict[str, Any], window: dict[str, Any]) -> bool:
    lo, hi = window.get("start"), window.get("end")
    if lo is None and hi is None:
        return True
    if not row.get("start") or not row.get("end"):
        return False
    start, end = row["start"][:10], row["end"][:10]
    if lo and end < lo:
        return False
    return not (hi and start > hi)


def matches(row: dict[str, Any], filters: dict[str, Any]) -> bool:
    """filterHistoryRows for one row. Every clause is conjunctive."""
    needle = (filters.get("name") or "").strip().lower()
    if needle and needle not in (row.get("name") or "").lower():
        return False
    models = filters.get("models") or []
    if models and not (row.get("model") is not None and row["model"] in models):
        return False
    fills = filters.get("fillModels") or []
    if fills and not (row.get("fill") is not None and row["fill"] in fills):
        return False
    if not _window_matches(row, filters.get("window") or {}):
        return False
    return all(_numeric_passes(row, key, filters) for key in _active_numeric(filters))


def _column_value(row: dict[str, Any], column: str, metric: str, now: float) -> Any:
    def metric_value(key: str) -> float | None:
        return _number((row.get("m") or {}).get(key))

    if column == "name":
        return row.get("name")
    if column == "ticker":
        return row.get("ticker")
    if column == "grid_step":
        return row.get("grid")
    if column == "profit_target":
        return row.get("target")
    if column == "sizing_model":
        return row.get("model")
    if column == "metric":
        return metric_value(metric)
    if column in ("cagr_pct", "max_drawdown_pct", "worst_year_pct", "total_trades"):
        return metric_value(column)
    if column == "window":
        if not row.get("start"):
            return None
        return f"{row['start'][:10]}→{(row.get('end') or '')[:10]}"
    if column == "run_id":
        return row.get("run")
    if column == "saved_at":
        return row["saved_at"] if row.get("saved_at") is not None else now
    return None


def sort_rows(
    rows: list[dict[str, Any]], column: str, direction: str, metric: str
) -> list[dict[str, Any]]:
    """sortHistoryRows: one column, missing values last either way. Stable,
    so equal values keep the order the rows were indexed in."""
    now = time.time()
    keyed = [(_column_value(row, column, metric, now), row) for row in rows]
    present = [item for item in keyed if item[0] is not None]
    missing = [row for value, row in keyed if value is None]

    def order(item: tuple[Any, dict[str, Any]]) -> Any:
        value = item[0]
        # A string column sorts the way localeCompare does closely enough:
        # case-insensitive first, then exact.
        return (value.casefold(), value) if isinstance(value, str) else value

    present.sort(key=order, reverse=direction == "desc")
    return [row for _, row in present] + missing


# ---------------------------------------------------------------------
# The fund's rows, joined and cached per index state
# ---------------------------------------------------------------------


_rows_lock = threading.Lock()
_rows_cache: dict[str, tuple[int, list[dict[str, Any]]]] = {}


def fund_rows(ticker: str) -> list[dict[str, Any]]:
    """Every cell of `ticker` across stored runs, newest run first, with
    the run-level fields joined on (the browser used to do this join).
    Rebuilt only when the stored runs change, not on every query."""
    entries = index_entries()
    generation = index_generation()
    with _rows_lock:
        cached = _rows_cache.get(ticker)
        if cached is not None and cached[0] == generation:
            return cached[1]
    out: list[dict[str, Any]] = []
    for entry in entries:
        run = entry.get("run") or {}
        joined = {field: run.get(field) for field in RUN_FIELDS}
        for row in entry.get("rows") or []:
            if row.get("ticker") == ticker:
                out.append({**row, **joined, "run": entry["id"]})
    with _rows_lock:
        _rows_cache[ticker] = (generation, out)
    return out


def funds() -> list[dict[str, Any]]:
    """Which funds have history, with how much and how recently."""
    stats: dict[str, dict[str, Any]] = {}
    for entry in index_entries():
        saved = (entry.get("run") or {}).get("saved_at")
        tickers = {row.get("ticker") for row in entry.get("rows") or []}
        for row in entry.get("rows") or []:
            stat = stats.setdefault(
                row["ticker"], {"ticker": row["ticker"], "rows": 0, "runs": 0, "last_saved": None}
            )
            stat["rows"] += 1
        for ticker in tickers:
            stat = stats[ticker]
            stat["runs"] += 1
            if saved is not None and (stat["last_saved"] is None or saved > stat["last_saved"]):
                stat["last_saved"] = saved
    return sorted(stats.values(), key=lambda s: s["ticker"])


def runs() -> dict[str, dict[str, Any]]:
    """Run-level fields of every stored run, keyed by id -- names for
    dedupe (cli.py submit, tools/sweep_rsp_all.py) without any cells."""
    return {entry["id"]: entry["run"] for entry in index_entries() if entry.get("run")}


def _distinct(rows: list[dict[str, Any]], key: str) -> list[float]:
    seen: list[float] = []
    for row in rows:
        value = field_value(row, key)
        if value is not None and not any(_same(existing, value) for existing in seen):
            seen.append(value)
    return sorted(seen)


def facets(ticker: str) -> dict[str, Any]:
    """historyInputFields plus the categorical options, for one fund."""
    rows = fund_rows(ticker)
    fields = [
        {
            "key": "grid_step",
            "label": "Grid step %",
            "group": "Input arguments",
            "values": _distinct(rows, "grid_step"),
        },
        {
            "key": "profit_target",
            "label": "Profit target %",
            "group": "Input arguments",
            "values": _distinct(rows, "profit_target"),
        },
        {
            "key": "window_days",
            "label": "Window (days)",
            "group": "Input arguments",
            "values": _distinct(rows, "window_days"),
        },
        {
            "key": "window_bars",
            "label": "Window (bars)",
            "group": "Input arguments",
            "values": _distinct(rows, "window_bars"),
        },
    ]
    params: set[str] = set()
    for row in rows:
        for name, value in (row.get("params") or {}).items():
            if _number(value) is not None:
                params.add(name)
    for name in sorted(params):
        key = f"param:{name}"
        fields.append(
            {"key": key, "label": name, "group": "Input arguments", "values": _distinct(rows, key)}
        )
    return {
        "ticker": ticker,
        "rows": len(rows),
        "runs": len({row["run"] for row in rows}),
        "models": sorted({row["model"] for row in rows if row.get("model")}),
        "fills": sorted({row["fill"] for row in rows if row.get("fill")}),
        "fields": fields,
    }


def query(body: dict[str, Any]) -> dict[str, Any]:
    """One page of one fund's cells, filtered and sorted."""
    ticker = body["ticker"]
    filters = body.get("filters") or {}
    sort = body.get("sort") or {}
    column = sort.get("column") if sort.get("column") in SORT_COLUMNS else "metric"
    direction = "asc" if sort.get("direction") == "asc" else "desc"
    metric = body.get("rank_by") or "cagr_pct"
    offset = max(0, int(body.get("offset") or 0))
    limit = max(1, min(int(body.get("limit") or 50), MAX_PAGE))

    rows = fund_rows(ticker)
    matched = [row for row in rows if matches(row, filters)]
    ordered = sort_rows(matched, column, direction, metric)
    return {
        "ticker": ticker,
        "total": len(matched),
        "total_unfiltered": len(rows),
        "runs_matched": len({row["run"] for row in matched}),
        "offset": offset,
        "rows": ordered[offset : offset + limit],
    }


__all__ = ["facets", "field_value", "fund_rows", "funds", "matches", "query", "runs", "sort_rows"]
