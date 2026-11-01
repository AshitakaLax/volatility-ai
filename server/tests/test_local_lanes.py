"""server/jobs.py's local lanes: VAI_LOCAL_WORKERS runs several queued runs on
this machine at once, each lane a local shard of its own."""

from __future__ import annotations

import threading

import pytest

from server.jobs import LOCAL_SHARD, JobQueue, QueueError, QueueStore, lane_name, local_workers

TIMEOUT = 10.0


class Gate:
    """A runner that holds every run until released, counting how many are in at once."""

    def __init__(self) -> None:
        self.release = threading.Event()
        self.lock = threading.Lock()
        self.inside = 0
        self.most = 0
        self.arrived = threading.Semaphore(0)

    def __call__(self, request, report, control):
        with self.lock:
            self.inside += 1
            self.most = max(self.most, self.inside)
        self.arrived.release()
        assert self.release.wait(TIMEOUT)
        with self.lock:
            self.inside -= 1
        return {"name": request["name"]}


@pytest.fixture
def gate() -> Gate:
    return Gate()


@pytest.fixture
def queue(tmp_path, gate) -> JobQueue:
    return JobQueue(runner=gate, store=QueueStore(lambda: tmp_path / "queue"), workers=3)


def wait_until(queue: JobQueue, predicate) -> None:
    with queue._condition:
        assert queue._condition.wait_for(predicate, timeout=TIMEOUT), "condition never held"


def test_lane_names():
    assert [lane_name(i) for i in (1, 2, 3)] == [LOCAL_SHARD, "local-2", "local-3"]


def test_the_environment_sets_the_lane_count(monkeypatch):
    monkeypatch.delenv("VAI_LOCAL_WORKERS", raising=False)
    assert local_workers() == 1
    monkeypatch.setenv("VAI_LOCAL_WORKERS", "8")
    assert local_workers() == 8
    monkeypatch.setenv("VAI_LOCAL_WORKERS", "0")
    assert local_workers() == 1
    monkeypatch.setenv("VAI_LOCAL_WORKERS", "9999")
    assert local_workers() == 64
    monkeypatch.setenv("VAI_LOCAL_WORKERS", "many")
    assert local_workers() == 1


def test_queued_runs_go_to_the_lanes_at_once(queue, gate):
    jobs = [queue.submit({"name": f"r{i}"}) for i in range(5)]
    for _ in range(3):
        assert gate.arrived.acquire(timeout=TIMEOUT)
    wait_until(queue, lambda: sum(queue.get(j.run_id).status == "running" for j in jobs) == 3)
    assert gate.most == 3
    assert {queue.get(j.run_id).shard for j in jobs if queue.get(j.run_id).status == "running"} == {
        "local",
        "local-2",
        "local-3",
    }
    assert [s["name"] for s in queue.shards()] == ["local", "local-2", "local-3"]
    gate.release.set()
    wait_until(queue, lambda: all(queue.get(j.run_id).status == "complete" for j in jobs))
    assert gate.most == 3


def test_one_run_is_never_taken_by_two_lanes(queue, gate):
    gate.release.set()
    jobs = [queue.submit({"name": f"r{i}"}) for i in range(12)]
    wait_until(queue, lambda: all(queue.get(j.run_id).status == "complete" for j in jobs))


def test_pausing_local_pauses_every_lane_and_resuming_restarts_them(queue, gate):
    queue.pause_shard(LOCAL_SHARD)
    assert all(s["paused"] for s in queue.shards())
    jobs = [queue.submit({"name": f"r{i}"}) for i in range(3)]
    assert not gate.arrived.acquire(timeout=0.2)
    queue.resume_shard(LOCAL_SHARD)
    gate.release.set()
    wait_until(queue, lambda: all(queue.get(j.run_id).status == "complete" for j in jobs))


def test_a_remote_shard_cannot_take_a_lane_name(queue):
    with pytest.raises(QueueError):
        queue.register_shard("local-2", "i1")


def test_the_default_is_one_lane(tmp_path, gate, monkeypatch):
    monkeypatch.delenv("VAI_LOCAL_WORKERS", raising=False)
    q = JobQueue(runner=gate, store=QueueStore(lambda: tmp_path / "q"))
    assert [s["name"] for s in q.shards()] == [LOCAL_SHARD]
