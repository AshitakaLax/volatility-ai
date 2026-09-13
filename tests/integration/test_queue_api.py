"""The queue-control endpoints, through the real router and a fake runner.

server.backtest's routes read the module-global `queue` at call time, so
swapping in a fresh JobQueue gives each test a private queue driven by a
gated runner -- the HTTP contract under test without engine time, and
without touching the module queue other integration tests share.
"""

from __future__ import annotations

import threading

import pytest
from fastapi.testclient import TestClient

import server.backtest as backtest
from server.app import app
from server.jobs import JobQueue, QueueStore, RunStopped

TIMEOUT = 10.0
RUN = {
    "tickers": ["TQQQ"],
    "grid_steps": [0.01],
    "profit_targets": [0.005],
    "sizing_model": "fixed",
    "strategy_params": {"allocation_pct": 0.05},
}


class GatedRunner:
    def __init__(self) -> None:
        self.release = threading.Event()
        self.arrived = threading.Event()
        self.started: list[str] = []

    def __call__(self, request, report, control):
        self.started.append(request.get("name"))
        self.arrived.set()
        assert self.release.wait(TIMEOUT)
        if control.should_stop():
            raise RunStopped()
        return {"run_id": "", "funds": {}}


@pytest.fixture
def runner():
    return GatedRunner()


@pytest.fixture
def client(monkeypatch, tmp_path, runner):
    fresh = JobQueue(runner=runner, store=QueueStore(lambda: tmp_path / "queue"))
    monkeypatch.setattr(backtest, "queue", fresh)
    monkeypatch.setattr(backtest, "_archive", lambda job: None)
    yield TestClient(app)
    runner.release.set()


def submit(client, name: str) -> str:
    response = client.post("/api/backtest/runs", json={**RUN, "name": name})
    assert response.status_code == 202, response.text
    return response.json()["run_id"]


def wait_for(status: str, run_id: str) -> None:
    q = backtest.queue
    with q._condition:
        assert q._condition.wait_for(lambda: q.get(run_id).status == status, timeout=TIMEOUT), (
            f"{run_id} never reached {status}"
        )


def test_runs_listing_reports_positions_and_queue_state(client, runner):
    running = submit(client, "first")
    assert runner.arrived.wait(TIMEOUT)
    a, b = submit(client, "a"), submit(client, "b")

    body = client.get("/api/backtest/runs").json()
    by_id = {run["run_id"]: run for run in body["runs"]}
    assert body["queue"] == {"paused": False}
    assert by_id[running]["queue_position"] is None
    assert (by_id[a]["queue_position"], by_id[b]["queue_position"]) == (1, 2)


def test_run_next_and_move_reorder_and_answer_with_the_new_snapshot(client, runner):
    submit(client, "first")
    assert runner.arrived.wait(TIMEOUT)
    a, b, c = submit(client, "a"), submit(client, "b"), submit(client, "c")

    moved = client.post(f"/api/backtest/runs/{c}/run-next").json()
    assert moved["run_id"] == c and moved["queue_position"] == 1

    client.post(f"/api/backtest/runs/{a}/move", json={"position": 2})
    positions = {
        run["run_id"]: run["queue_position"]
        for run in client.get("/api/backtest/runs").json()["runs"]
    }
    assert (positions[c], positions[b], positions[a]) == (1, 2, 3)


def test_pausing_a_running_run_is_a_request_until_it_lands(client, runner):
    run_id = submit(client, "first")
    assert runner.arrived.wait(TIMEOUT)

    snapshot = client.post(f"/api/backtest/runs/{run_id}/pause").json()
    assert snapshot["status"] == "running" and snapshot["stop_requested"] == "pause"

    runner.release.set()
    wait_for("paused", run_id)
    assert client.get(f"/api/backtest/runs/{run_id}").json()["status"] == "paused"

    runner.arrived.clear()
    assert client.post(f"/api/backtest/runs/{run_id}/resume").json()["status"] == "queued"
    wait_for("complete", run_id)


def test_cancel_then_invalid_actions_are_409_and_unknown_ids_404(client, runner):
    submit(client, "first")
    assert runner.arrived.wait(TIMEOUT)
    queued = submit(client, "a")

    assert client.post(f"/api/backtest/runs/{queued}/cancel").json()["status"] == "cancelled"
    for action in ("pause", "resume", "cancel", "run-next"):
        assert client.post(f"/api/backtest/runs/{queued}/{action}").status_code == 409
    assert client.post(f"/api/backtest/runs/{queued}/move", json={"position": 0}).status_code == 409
    assert client.post("/api/backtest/runs/doesnotexist/pause").status_code == 404
    assert (
        client.post(f"/api/backtest/runs/{queued}/move", json={"position": -1}).status_code == 422
    )


def test_pausing_the_queue_holds_everything_and_resuming_releases_it(client, runner):
    assert client.post("/api/backtest/queue/pause").json() == {"queue": {"paused": True}}
    run_id = submit(client, "held")
    # Paused BEFORE the submit, so the worker can never have been handed it:
    # asserted from the queue's own state, not by waiting to see nothing happen.
    assert backtest.queue.get(run_id).status == "queued"
    assert runner.started == []
    assert client.get("/api/backtest/runs").json()["queue"] == {"paused": True}

    runner.release.set()
    assert client.post("/api/backtest/queue/resume").json() == {"queue": {"paused": False}}
    wait_for("complete", run_id)
