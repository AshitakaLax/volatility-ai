"""server/warehouse_status.py: the Warehouse tab's two reads.

The warehouse half SKIPS WITHOUT DUCKDB/POLARS, like the other warehouse
tests; the system half does not need them.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

import server.backtest as backtest
import server.warehouse_status as status
from server.app import app
from server.jobs import JobQueue, QueueStore

GRID = {
    "tickers": ["TQQQ", "RSP"],
    "grid_steps": [0.01, 0.02, 0.03],
    "targets": [0.005, 0.01],
    "model": "fixed",
    "params": {"allocation_pct": [0.05, 0.1]},
}


@pytest.fixture(autouse=True)
def fresh_caches():
    status.reset_caches()
    yield
    status.reset_caches()


# --------------------------------------------------------------------
# What is left in the queue
# --------------------------------------------------------------------


def test_a_grid_run_is_counted_as_run_backtest_runs_it():
    """3 steps x 2 targets x 2 allocations, for each of two tickers."""
    assert backtest.request_configurations(GRID) == 24


def test_a_bayesian_run_is_counted_by_its_trial_budget():
    request = {**GRID, "tickers": ["TQQQ"], "bayes": {"trials": 7}}
    assert backtest.request_configurations(request) == 7


def test_a_request_that_no_longer_validates_has_no_size():
    assert backtest.request_configurations({**GRID, "model": "no-such-strategy"}) is None


class _Paused:
    """A runner that is never reached: the queue below is paused."""

    def __call__(self, request, report, control):  # pragma: no cover
        raise AssertionError("the queue is paused")


def test_the_queue_summary_counts_what_is_left(monkeypatch, tmp_path):
    queue = JobQueue(runner=_Paused(), store=QueueStore(lambda: tmp_path / "queue"))
    queue.pause_all()
    monkeypatch.setattr(backtest, "queue", queue)
    first = queue.submit({**GRID, "name": "one"})
    queue.submit({**GRID, "name": "two"})
    held = queue.submit({**GRID, "name": "three"})
    with queue._condition:
        first.status, first.progress = "running", 0.25
        held.status = "paused"

    summary = status.queue_summary()
    assert summary["counts"] == {"running": 1, "queued": 1, "paused": 1}
    # All of the queued one and the running one's unfinished part; the
    # paused one waits for a person.
    assert summary["remaining_configurations"] == 24 + 18
    assert summary["remaining_runs"] == 2
    assert summary["running"][0]["name"] == "one"
    assert summary["running"][0]["configurations"] == 24


# --------------------------------------------------------------------
# GET /system
# --------------------------------------------------------------------


def _hwmon(root, name: str, sensors: dict[str, tuple[int, int, int]]) -> None:
    root.mkdir(parents=True)
    (root / "name").write_text(f"{name}\n")
    for i, (label, (now, high, crit)) in enumerate(sensors.items(), start=1):
        (root / f"temp{i}_label").write_text(label)
        (root / f"temp{i}_input").write_text(str(now))
        (root / f"temp{i}_max").write_text(str(high))
        (root / f"temp{i}_crit").write_text(str(crit))


def test_temperatures_are_each_packages_with_its_limits(tmp_path, monkeypatch):
    _hwmon(
        tmp_path / "hwmon0",
        "coretemp",
        {
            "Package id 0": (74000, 83000, 93000),
            "Core 0": (70000, 83000, 93000),
            "Core 1": (76000, 83000, 93000),
        },
    )
    _hwmon(tmp_path / "hwmon1", "nvme", {"Composite": (40000, 80000, 85000)})
    monkeypatch.setattr(status, "HWMON_ROOT", tmp_path)
    assert status.temperatures() == [
        {"label": "Package id 0", "c": 74.0, "high": 83.0, "crit": 93.0, "hottest": 76.0}
    ]


def test_throttling_counts_cpus_not_events(tmp_path, monkeypatch):
    for cpu, (core, package) in enumerate([(0, 0), (3, 0), (0, 0)]):
        directory = tmp_path / f"cpu{cpu}" / "thermal_throttle"
        directory.mkdir(parents=True)
        (directory / "core_throttle_count").write_text(str(core))
        (directory / "package_throttle_count").write_text(str(package))
    monkeypatch.setattr(status, "CPU_ROOT", tmp_path)
    assert status.throttling() == {"throttled_cpus": 1, "max_events": 3}

    monkeypatch.setattr(status, "CPU_ROOT", tmp_path / "absent")
    assert status.throttling() is None


def test_cores_busy_needs_two_readings(tmp_path, monkeypatch):
    stat = tmp_path / "cpu.stat"
    monkeypatch.setattr(status, "CGROUP_ROOT", tmp_path)
    monkeypatch.setattr(status, "_cpu_sample", None)
    times = iter([100.0, 110.0])
    monkeypatch.setattr(status, "_clock", lambda: next(times))

    stat.write_text("usage_usec 1000000\nuser_usec 1\n")
    assert status.cores_busy() is None
    stat.write_text("usage_usec 81000000\nuser_usec 1\n")
    assert status.cores_busy() == 8.0  # 80 s of CPU in 10 s


def test_backups_report_the_newest_archive(tmp_path, monkeypatch):
    monkeypatch.setenv("VAI_BACKUP_DIR", str(tmp_path))
    (tmp_path / "volatility-ai-db_host_2026-10-18_073000Z.tar.gz").write_bytes(b"x" * 10)
    newest = tmp_path / "volatility-ai-db_host_2026-10-19_073000Z.tar.gz"
    newest.write_bytes(b"x" * 30)
    import os

    os.utime(newest, (2_000_000_000, 2_000_000_000))
    answer = status.backups()
    assert answer["count"] == 2 and answer["bytes"] == 40
    assert answer["latest"]["name"] == newest.name and answer["latest"]["bytes"] == 30

    monkeypatch.setenv("VAI_BACKUP_DIR", str(tmp_path / "absent"))
    assert status.backups() is None


def test_the_system_route_answers_without_a_container_or_sensors(tmp_path, monkeypatch):
    monkeypatch.setattr(status, "HWMON_ROOT", tmp_path / "none")
    monkeypatch.setattr(status, "CPU_ROOT", tmp_path / "none")
    monkeypatch.setattr(
        backtest, "queue", JobQueue(runner=_Paused(), store=QueueStore(lambda: tmp_path / "q"))
    )
    body = TestClient(app).get("/api/backtest/system").json()
    assert body["host"]["cpus"] and body["host"]["temperatures"] == []
    assert body["host"]["throttling"] is None
    assert body["queue"]["remaining_configurations"] == 0
    assert {disk["label"] for disk in body["disks"]} == {"warehouse", "output", "backups"}


# --------------------------------------------------------------------
# GET /warehouse
# --------------------------------------------------------------------


@pytest.fixture
def warehouse(tmp_path, monkeypatch):
    pytest.importorskip("duckdb")
    pytest.importorskip("polars")
    from engine.tests.test_warehouse_inventory import _ingest, _record, _sessions
    from engine.warehouse import bars

    root = tmp_path / "warehouse"
    monkeypatch.setenv("VAI_WAREHOUSE_DIR", str(root))
    monkeypatch.setattr(status, "KNOWN_DATA", {"FULL": "data/FULL.csv", "NOPE": "data/NOPE.csv"})
    _ingest(root, tmp_path, "FULL", _sessions(["2026-10-05", "2026-10-06", "2026-10-07"]))
    _record(
        root,
        "server-run1-FULL",
        bars.fingerprint("FULL"),
        [3.0, 8.0],
        strategy={"strategy_id": "fixed"},
        server_run={"run_id": "run1", "ticker": "FULL", "name": "first"},
    )
    _record(root, "cli-old", "older", [1.0], backtest={"symbol": "FULL"})
    return root


def test_the_warehouse_route_reports_funds_results_and_storage(warehouse):
    body = TestClient(app).get("/api/backtest/warehouse").json()
    assert body["available"] and not body["busy"] and body["error"] is None
    assert body["summary"]["funds"] == 1 and body["summary"]["bars"] == 39
    assert body["summary"]["sweeps"] == 2 and body["summary"]["simulations"] == 3

    funds = {row["ticker"]: row for row in body["funds"]}
    assert funds["NOPE"]["ingested"] is False and funds["NOPE"]["bars"] is None
    full = funds["FULL"]
    assert full["bars"] == 39 and full["bars_per_session"] == 13
    assert full["last_session"] == "2026-10-07" and full["sessions_behind"] >= 1
    assert full["simulations"] == 3 and full["current_simulations"] == 2
    assert full["older_simulations"] == 1 and full["best_return"] == 8.0

    strategies = body["results"]["strategies"]
    assert {(row["fund"], row["strategy"]) for row in strategies} == {
        ("FULL", "fixed"),
        ("FULL", "?"),
    }
    assert body["results"]["recent"][0]["id"] in {"server-run1-FULL", "cli-old"}
    assert body["storage"]["lakes"]["ohlcv"]["by_fund"].keys() == {"FULL"}


def test_the_bar_scan_is_redone_only_when_the_lake_changes(warehouse, tmp_path, monkeypatch):
    from engine.tests.test_warehouse_inventory import _ingest, _sessions

    scans = []
    real = status.inventory.fund_inventory

    def counted():
        scans.append(1)
        return real()

    monkeypatch.setattr(status.inventory, "fund_inventory", counted)
    client = TestClient(app)
    client.get("/api/backtest/warehouse")
    client.get("/api/backtest/warehouse")
    assert len(scans) == 1
    _ingest(warehouse, tmp_path / "more", "MORE", _sessions(["2026-10-05"]))
    body = client.get("/api/backtest/warehouse").json()
    assert len(scans) == 2 and body["summary"]["funds"] == 2


def test_results_are_recomputed_after_their_time_to_live(warehouse, monkeypatch):
    calls = []
    real = status.inventory.results_summary

    def counted(now):
        calls.append(now)
        return real(now)

    monkeypatch.setattr(status.inventory, "results_summary", counted)
    clock = iter([0.0, 10.0, status.RESULTS_TTL_SECONDS + 1])
    monkeypatch.setattr(status, "_clock", lambda: next(clock))
    client = TestClient(app)
    for _ in range(3):
        client.get("/api/backtest/warehouse")
    assert len(calls) == 2


def test_a_busy_warehouse_serves_the_last_good_answer(warehouse, monkeypatch):
    client = TestClient(app)
    first = client.get("/api/backtest/warehouse").json()
    status.reset_caches()
    client.get("/api/backtest/warehouse")  # a good answer, cached

    busy = {"available": True, "busy": True, "error": None}
    monkeypatch.setattr(status.inventory, "fund_inventory", lambda: busy)
    monkeypatch.setattr(status.inventory, "ohlcv_signature", lambda: "changed")
    body = client.get("/api/backtest/warehouse").json()
    assert body["busy"] is True
    assert body["summary"]["bars"] == first["summary"]["bars"]
