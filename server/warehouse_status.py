"""The Warehouse tab's two reads: what the warehouse holds, and the state of
the machine and the queue that fill it.

    GET /api/backtest/warehouse   funds and their freshness, sweeps and
                                  simulations, what it all takes on disk
    GET /api/backtest/system      host load and temperatures, memory, disks,
                                  the queue's remaining work, shards, backups

--------------------------------------------------------------------
READ-ONLY

Two GET routes and nothing else. The warehouse is read through
engine/warehouse/inventory.py -- bars.py's read-only open, under
WAREHOUSE_LOCK's read side -- and this module imports nothing that could
open it read-write. Everything else is a file listing or a /sys and
/proc read. server/tests/test_server_capability.py holds it to that.

--------------------------------------------------------------------
CACHED, BECAUSE A SWEEP IS USING EVERY CORE

The fund inventory reads every bar in the lake (3.3 s for 9.7M bars with
every core busy), and its answer can only change when an ingest rewrites
the lake -- so it is recomputed when the lake's file listing changes and
never otherwise. Results and storage are recomputed at most every
RESULTS_TTL_SECONDS. One computation at a time: two open tabs share it.
A warehouse another process is holding answers with the last good
snapshot, flagged `busy`, rather than with nothing.

Freshness is computed per request from the cached last bars, so "N
sessions behind" moves at 16:00 Eastern without anything being re-read.

--------------------------------------------------------------------
UNDER /api/backtest, LIKE shards.py

The warehouse belongs to whichever host runs the backtests. Under this
prefix, a host that forwards backtests (upstream.py) forwards these too.
"""

from __future__ import annotations

import os
import shutil
import threading
import time
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from fastapi import APIRouter

from engine.warehouse import inventory
from engine.warehouse.bars import warehouse_root
from server import backtest, deployment, history, jobs
from tools.backup_databases import default_backup_dir
from tools.export_ui_data import KNOWN_DATA

router = APIRouter(prefix="/api/backtest", tags=["warehouse"])

RESULTS_TTL_SECONDS = 30.0
RECENT_SWEEPS = 25

# What the system read looks at. Module-level so tests can point them at
# a fixture tree.
HWMON_ROOT = Path("/sys/class/hwmon")
CPU_ROOT = Path("/sys/devices/system/cpu")
CGROUP_ROOT = Path("/sys/fs/cgroup")

# hwmon drivers that report CPU temperatures: Intel, AMD, a Raspberry Pi.
_CPU_SENSORS = {"coretemp", "k10temp", "zenpower", "cpu_thermal"}

# Injected by tests; never sleep.
_clock: Callable[[], float] = time.monotonic


def _now() -> datetime:
    return datetime.now(UTC)


# --------------------------------------------------------------------
# Caching
# --------------------------------------------------------------------


class _Cache:
    """One value, the key it was computed for, and a lock that makes
    concurrent requests wait for one computation instead of each running
    their own."""

    def __init__(self) -> None:
        self.lock = threading.Lock()
        self.key: object = None
        self.value: dict[str, Any] | None = None


_funds = _Cache()
_results = _Cache()
_storage = _Cache()


def _cached(cache: _Cache, key: object, compute: Callable[[], dict[str, Any]]) -> dict[str, Any]:
    """cache's value for `key`, computed if the key changed.

    An answer that could not read the warehouse (busy, or an error) is never
    kept -- the next request tries again -- and is served as the previous
    good answer, flagged, when there is one.
    """
    with cache.lock:
        if cache.value is not None and cache.key == key:
            return cache.value
        value = compute()
        if value.get("busy") or value.get("error"):
            if cache.value is None:
                return value
            return {**cache.value, "busy": value.get("busy"), "error": value.get("error")}
        cache.key, cache.value = key, value
        return value


def reset_caches() -> None:
    """Forget every cached answer (tests; a manual refresh does not need it)."""
    for cache in (_funds, _results, _storage):
        with cache.lock:
            cache.key, cache.value = None, None


# --------------------------------------------------------------------
# GET /warehouse
# --------------------------------------------------------------------


def _fund_rows(
    funds: dict[str, Any], results: dict[str, Any], storage: dict[str, Any], now: datetime
) -> list[dict[str, Any]]:
    """One row per fund with bars, and per fund in the registry without."""
    held = funds.get("funds", {})
    assets = funds.get("assets", {})
    by_fund_bytes = storage.get("lakes", {}).get("ohlcv", {}).get("by_fund", {})

    sweeps: dict[str, list[dict[str, Any]]] = {}
    for sweep in results.get("sweep_rows", []):
        sweeps.setdefault(sweep["fund"], []).append(sweep)
    versions: dict[str, list[dict[str, Any]]] = {}
    for row in results.get("versions", []):
        versions.setdefault(row["fund"], []).append(row)

    rows = []
    for ticker in sorted(set(held) | set(KNOWN_DATA)):
        fund = held.get(ticker) or {}
        mine = sweeps.get(ticker, [])
        returns = [s["best_return"] for s in mine if s["best_return"] is not None]
        simulations = sum(s["simulations"] for s in mine)
        current = sum(
            v["simulations"]
            for v in versions.get(ticker, [])
            if fund and v["dataset_version"] == fund["fingerprint"]
        )
        rows.append(
            {
                "ticker": ticker,
                "ingested": bool(fund),
                "known": ticker in KNOWN_DATA,
                **{
                    key: fund.get(key)
                    for key in (
                        "bars",
                        "first",
                        "last",
                        "sessions",
                        "duplicates",
                        "bars_per_session",
                    )
                },
                **inventory.freshness(
                    fund.get("last"),
                    fund.get("bars_per_session"),
                    fund.get("last_session_bars"),
                    now,
                ),
                "sweeps": len(mine),
                "simulations": simulations,
                "current_simulations": current,
                "older_simulations": simulations - current,
                "best_return": max(returns) if returns else None,
                "bytes": by_fund_bytes.get(ticker),
                **assets.get(ticker, {"sector": None, "inception": None, "leverage": None}),
            }
        )
    return rows


def _strategy_rows(sweeps: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Sweeps grouped by (fund, strategy): the best Total Return % found and
    its drawdown and Return/Drawdown -- never Capital Velocity Index, which
    saturates on long datasets."""
    groups: dict[tuple[str, str], dict[str, Any]] = {}
    for sweep in sweeps:
        key = (sweep["fund"] or "?", sweep["strategy"] or "?")
        group = groups.setdefault(
            key,
            {
                "fund": key[0],
                "strategy": key[1],
                "sweeps": 0,
                "simulations": 0,
                "failed": 0,
                "best_return": None,
                "best_drawdown": None,
                "best_calmar": None,
                "best_sweep": None,
                "last": None,
            },
        )
        group["sweeps"] += 1
        group["simulations"] += sweep["simulations"]
        group["failed"] += sweep["failed"]
        if sweep["last"] and (group["last"] is None or sweep["last"] > group["last"]):
            group["last"] = sweep["last"]
        best = sweep["best_return"]
        if best is not None and (group["best_return"] is None or best > group["best_return"]):
            group.update(
                best_return=best,
                best_drawdown=sweep["best_drawdown"],
                best_calmar=sweep["best_calmar"],
                best_sweep=sweep["id"],
            )
    return sorted(
        groups.values(),
        key=lambda g: (g["fund"], -(g["best_return"] if g["best_return"] is not None else -1e18)),
    )


def _lake_bytes(storage: dict[str, Any]) -> int:
    return sum(c["bytes"] for c in storage.get("catalogs", [])) + sum(
        lake["bytes"] for lake in storage.get("lakes", {}).values()
    )


@router.get("/warehouse")
def warehouse() -> dict[str, Any]:
    """Everything the warehouse holds, summarised (bounded by funds and
    strategies, never by simulations)."""
    now = _now()
    funds = _cached(_funds, inventory.ohlcv_signature(), inventory.fund_inventory)
    bucket = int(_clock() // RESULTS_TTL_SECONDS)
    results = _cached(_results, bucket, lambda: inventory.results_summary(now))
    storage = _cached(_storage, bucket, inventory.storage_summary)

    rows = _fund_rows(funds, results, storage, now)
    sweeps = results.get("sweep_rows", [])
    parts = (funds, results, storage)
    errors = [part["error"] for part in parts if part.get("error")]
    return {
        "at": now.isoformat(),
        "available": any(part.get("available") for part in parts),
        "busy": any(part.get("busy") for part in parts),
        "error": errors[0] if errors else None,
        "through": inventory.freshness(None, None, None, now)["through"],
        "summary": {
            "funds": sum(1 for row in rows if row["ingested"]),
            "bars": sum(row.get("bars") or 0 for row in rows),
            "sweeps": results.get("sweeps", 0),
            "simulations": results.get("simulations", 0),
            "executions": results.get("executions", {}).get("rows", 0),
            "last_hour": results.get("last_hour", 0),
            "last_day": results.get("last_day", 0),
            "bytes": _lake_bytes(storage) + storage.get("tmp_bytes", 0),
            "free": (storage.get("disk") or {}).get("free"),
        },
        "funds": rows,
        "results": {
            "by_status": results.get("by_status", {}),
            "hourly": results.get("hourly", []),
            "mean_ms_last_hour": results.get("mean_ms_last_hour"),
            "executions": results.get("executions", {"rows": 0, "simulations": 0}),
            "strategies": _strategy_rows(sweeps),
            "recent": sweeps[:RECENT_SWEEPS],
        },
        "storage": {
            key: storage.get(key)
            for key in ("root", "catalogs", "lakes", "tmp_bytes", "disk", "duckdb", "tables")
        },
    }


# --------------------------------------------------------------------
# GET /system
# --------------------------------------------------------------------


def _text(path: Path) -> str | None:
    try:
        return path.read_text(encoding="utf-8").strip()
    except OSError:
        return None


def _integer(path: Path) -> int | None:
    text = _text(path)
    return int(text) if text and text.lstrip("-").isdigit() else None


def _celsius(path: Path) -> float | None:
    millis = _integer(path)
    return round(millis / 1000, 1) if millis is not None else None


def temperatures() -> list[dict[str, Any]]:
    """Each CPU package's temperature, with the limits the CPU itself
    reports: `high` (cooling should be at full) and `crit` (it starts
    slowing itself down). A sensor with no package reading reports its
    hottest one. Empty where /sys has none (a VM, a Mac)."""
    readings = []
    for device in sorted(HWMON_ROOT.glob("hwmon*")):
        name = _text(device / "name")
        if name not in _CPU_SENSORS:
            continue
        sensors = []
        for path in sorted(device.glob("temp*_input")):
            base = path.name.removesuffix("_input")
            celsius = _celsius(path)
            if celsius is None:
                continue
            sensors.append(
                {
                    "label": _text(device / f"{base}_label") or name,
                    "c": celsius,
                    "high": _celsius(device / f"{base}_max"),
                    "crit": _celsius(device / f"{base}_crit"),
                }
            )
        if not sensors:
            continue
        hottest = max(sensor["c"] for sensor in sensors)
        packages = [s for s in sensors if s["label"].startswith(("Package", "Tctl", "Tdie"))]
        for sensor in packages or [max(sensors, key=lambda s: s["c"])]:
            readings.append({**sensor, "hottest": hottest})
    return readings


def throttling() -> dict[str, int] | None:
    """Logical CPUs that have hit their thermal limit since boot, and the
    most events any one has logged. None where they cannot be read -- which
    includes every Docker container: Docker mounts an empty tmpfs over each
    cpu*/thermal_throttle (a side-channel mitigation), while hwmon's
    temperatures stay visible."""
    seen = False
    throttled = worst = 0
    for directory in CPU_ROOT.glob("cpu[0-9]*/thermal_throttle"):
        counts = [
            count
            for count in (
                _integer(directory / "core_throttle_count"),
                _integer(directory / "package_throttle_count"),
            )
            if count is not None
        ]
        if not counts:
            continue
        seen = True
        if any(counts):
            throttled += 1
            worst = max(worst, *counts)
    return {"throttled_cpus": throttled, "max_events": worst} if seen else None


_cpu_sample: tuple[float, int] | None = None
_cpu_lock = threading.Lock()


def cores_busy() -> float | None:
    """This container's CPU use, in cores, averaged since the previous call.

    cgroup v2 counts microseconds of CPU used; a rate needs two readings,
    so the first call answers None rather than invent one.
    """
    global _cpu_sample
    usage = None
    for line in (_text(CGROUP_ROOT / "cpu.stat") or "").splitlines():
        key, _, value = line.partition(" ")
        if key == "usage_usec" and value.isdigit():
            usage = int(value)
    if usage is None:
        return None
    with _cpu_lock:
        now = _clock()
        previous, _cpu_sample = _cpu_sample, (now, usage)
    if previous is None or now - previous[0] < 1.0:
        return None
    return round((usage - previous[1]) / 1e6 / (now - previous[0]), 1)


def _disk(label: str, path: Path) -> dict[str, Any]:
    try:
        usage = shutil.disk_usage(path)
    except OSError:
        return {"label": label, "path": str(path), "total": None, "free": None}
    return {"label": label, "path": str(path), "total": usage.total, "free": usage.free}


def backups() -> dict[str, Any] | None:
    """The archive directory the backup service writes: how many, how big,
    and the newest. None when it is not visible from here."""
    directory = default_backup_dir()
    if not directory.is_dir():
        return None
    archives = []
    for path in directory.glob("*.tar.gz"):
        try:
            stat = path.stat()
        except OSError:
            continue
        archives.append((stat.st_mtime, path.name, stat.st_size))
    newest = max(archives) if archives else None
    return {
        "dir": str(directory),
        "count": len(archives),
        "bytes": sum(size for _, _, size in archives),
        "latest": (
            {
                "name": newest[1],
                "bytes": newest[2],
                "at": datetime.fromtimestamp(newest[0], UTC).isoformat(),
            }
            if newest
            else None
        ),
    }


# A run's request never changes once submitted, so neither does its size.
_sizes: dict[str, int | None] = {}


def _size(job: jobs.Job) -> int | None:
    if job.run_id not in _sizes:
        _sizes[job.run_id] = backtest.request_configurations(job.request)
    return _sizes[job.run_id]


def queue_summary() -> dict[str, Any]:
    """The queue's runs by status, what is running, and the configurations
    left: every queued run, plus the unfinished part of each running one.
    Paused runs are counted, not included -- they wait for a person."""
    counts: dict[str, int] = {}
    running = []
    remaining = 0
    unknown = False
    for job in backtest.queue.all():
        counts[job.status] = counts.get(job.status, 0) + 1
        if job.status not in ("queued", "running"):
            continue
        size = _size(job)
        if size is None:
            unknown = True
        elif job.status == "queued":
            remaining += size
        else:
            remaining += round(size * (1.0 - job.progress))
        if job.status == "running":
            running.append(
                {
                    "id": job.run_id,
                    "name": job.name,
                    "progress": round(job.progress, 4),
                    "msg": job.message,
                    "shard": job.shard,
                    "configurations": size,
                }
            )
    return {
        "paused": backtest.queue.paused,
        "counts": counts,
        "running": running,
        "remaining_runs": counts.get("queued", 0) + len(running),
        "remaining_configurations": remaining,
        "some_unsized": unknown,
    }


def shard_summary() -> dict[str, int]:
    shards = backtest.queue.shards()
    return {
        "total": len(shards),
        "online": sum(1 for shard in shards if shard["conn"] == "online"),
        "working": sum(1 for shard in shards if shard["run"] is not None),
    }


@router.get("/system")
def system() -> dict[str, Any]:
    """The machine and the queue, read fresh every call (all cheap)."""
    try:
        load = list(os.getloadavg())
    except OSError:
        load = None
    container = deployment.container_stats()
    if container is not None:
        container = {**container, "cpu_pct": None, "cores_busy": cores_busy()}
    return {
        "at": _now().isoformat(),
        "build": deployment.describe()["build"],
        "host": {
            "cpus": os.cpu_count(),
            "load": load,
            "temperatures": temperatures(),
            "throttling": throttling(),
        },
        "container": container,
        "disks": [
            _disk("warehouse", warehouse_root()),
            _disk("output", history.directory()),
            _disk("backups", default_backup_dir()),
        ],
        "queue": queue_summary(),
        "shards": shard_summary(),
        "backups": backups(),
    }


__all__ = ["router", "system", "warehouse"]
