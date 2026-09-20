"""server/jobs.py: ordering, pause/cancel/resume, reordering, durability.

Every test synchronises on threading.Event gates and on the queue's own
Condition (which it notifies on every change) -- never on a sleep, per
tests/CLAUDE.md. A fake runner stands in for run_backtest and speaks the
same RunControl protocol: check should_stop() before each unit of work,
checkpoint each finished unit, skip units already checkpointed.
"""

from __future__ import annotations

import json
import threading

import pytest

from server.jobs import JobQueue, QueueError, QueueStore, RunStopped, UnknownRun

TIMEOUT = 10.0


class Harness:
    """A fake runner whose every step waits for the test to allow it."""

    def __init__(self) -> None:
        self.gates: dict[str, threading.Event] = {}
        self.at_gate: dict[str, threading.Event] = {}
        self.started: list[str] = []
        self.finished: list[str] = []
        self.hold_before_stopping: dict[str, threading.Event] = {}
        # Set the moment a runner has OBSERVED should_stop() as true.
        self.stopping: dict[str, threading.Event] = {}

    def gate(self, name: str) -> threading.Event:
        return self.gates.setdefault(name, threading.Event())

    def arrived(self, name: str) -> threading.Event:
        return self.at_gate.setdefault(name, threading.Event())

    def runner(self, request, report, control):
        name = request["name"]
        steps = request.get("steps", 1)
        self.started.append(name)
        done = len(control.completed_rows("T"))
        for step in range(done, steps):
            self.arrived(name).set()
            if request.get("gated"):
                assert self.gate(name).wait(TIMEOUT), f"{name} was never released"
                self.gate(name).clear()
            if control.should_stop():
                self.stopping.setdefault(name, threading.Event()).set()
                hold = self.hold_before_stopping.get(name)
                if hold is not None:
                    assert hold.wait(TIMEOUT)
                raise RunStopped(name)
            control.record_row("T", {"step": step})
            report((step + 1) / steps, f"{step + 1}/{steps}")
        self.finished.append(name)
        return {"name": name}


def wait_until(queue: JobQueue, predicate, timeout: float = TIMEOUT) -> None:
    with queue._condition:
        assert queue._condition.wait_for(predicate, timeout=timeout), "condition never held"


def status(queue: JobQueue, run_id: str) -> str:
    job = queue.get(run_id)
    assert job is not None
    return job.status


@pytest.fixture
def harness() -> Harness:
    return Harness()


@pytest.fixture
def store(tmp_path) -> QueueStore:
    return QueueStore(lambda: tmp_path / "queue")


@pytest.fixture
def queue(harness, store) -> JobQueue:
    return JobQueue(runner=harness.runner, store=store)


def block_worker(queue: JobQueue, harness: Harness, name: str = "blocker") -> str:
    """Occupy the single worker with a gated job, so later submissions wait."""
    job = queue.submit({"name": name, "gated": True})
    assert harness.arrived(name).wait(TIMEOUT)
    return job.run_id


def release(queue: JobQueue, harness: Harness, name: str, run_id: str) -> None:
    harness.gate(name).set()
    wait_until(queue, lambda: status(queue, run_id) == "complete")


class TestOrdering:
    def test_runs_start_in_submission_order(self, queue, harness):
        ids = [queue.submit({"name": n}).run_id for n in ("a", "b", "c")]
        wait_until(queue, lambda: all(status(queue, i) == "complete" for i in ids))
        assert harness.started == ["a", "b", "c"]

    def test_positions_count_pending_runs_only(self, queue, harness):
        blocker = block_worker(queue, harness)
        b = queue.submit({"name": "b"})
        c = queue.submit({"name": "c"})
        assert queue.get(blocker).queue_position is None
        assert (b.queue_position, c.queue_position) == (1, 2)
        release(queue, harness, "blocker", blocker)
        wait_until(queue, lambda: status(queue, c.run_id) == "complete")
        assert c.queue_position is None

    def test_run_next_jumps_the_queue(self, queue, harness):
        blocker = block_worker(queue, harness)
        ids = {n: queue.submit({"name": n}).run_id for n in ("b", "c", "d")}
        queue.run_next(ids["d"])
        assert [j.name for j in queue.pending()] == ["blocker", "d", "b", "c"]
        release(queue, harness, "blocker", blocker)
        wait_until(queue, lambda: all(status(queue, i) == "complete" for i in ids.values()))
        assert harness.started == ["blocker", "d", "b", "c"]

    def test_move_places_and_clamps(self, queue, harness):
        block_worker(queue, harness)
        ids = {n: queue.submit({"name": n}).run_id for n in ("b", "c", "d")}
        queue.move(ids["b"], 2)
        assert [j.name for j in queue.pending()][1:] == ["c", "d", "b"]
        queue.move(ids["d"], 99)
        assert [j.name for j in queue.pending()][1:] == ["c", "b", "d"]
        assert [queue.get(ids[n]).queue_position for n in ("c", "b", "d")] == [1, 2, 3]

    def test_a_running_or_finished_run_cannot_be_moved(self, queue, harness):
        blocker = block_worker(queue, harness)
        with pytest.raises(QueueError):
            queue.move(blocker, 0)
        release(queue, harness, "blocker", blocker)
        with pytest.raises(QueueError):
            queue.run_next(blocker)

    def test_an_unknown_run_is_reported_as_unknown(self, queue):
        with pytest.raises(UnknownRun):
            queue.pause("nope")


class TestPauseResumeCancelWhileQueued:
    def test_a_paused_run_is_skipped_until_resumed(self, queue, harness):
        blocker = block_worker(queue, harness)
        b = queue.submit({"name": "b"}).run_id
        c = queue.submit({"name": "c"}).run_id
        queue.pause(b)
        release(queue, harness, "blocker", blocker)
        wait_until(queue, lambda: status(queue, c) == "complete")
        assert status(queue, b) == "paused"
        assert queue.get(b).queue_position == 1
        queue.resume(b)
        wait_until(queue, lambda: status(queue, b) == "complete")
        assert harness.started == ["blocker", "c", "b"]

    def test_a_cancelled_run_never_starts(self, queue, harness):
        blocker = block_worker(queue, harness)
        b = queue.submit({"name": "b"}).run_id
        c = queue.submit({"name": "c"}).run_id
        queue.cancel(b)
        release(queue, harness, "blocker", blocker)
        wait_until(queue, lambda: status(queue, c) == "complete")
        assert status(queue, b) == "cancelled"
        assert "b" not in harness.started

    def test_run_next_resumes_a_paused_run(self, queue, harness):
        blocker = block_worker(queue, harness)
        b = queue.submit({"name": "b"}).run_id
        c = queue.submit({"name": "c"}).run_id
        queue.pause(c)
        queue.run_next(c)
        assert status(queue, c) == "queued"
        release(queue, harness, "blocker", blocker)
        wait_until(queue, lambda: status(queue, b) == "complete")
        assert harness.started == ["blocker", "c", "b"]

    def test_finished_runs_reject_controls(self, queue, harness):
        run_id = queue.submit({"name": "a"}).run_id
        wait_until(queue, lambda: status(queue, run_id) == "complete")
        for action in (queue.pause, queue.cancel, queue.resume):
            with pytest.raises(QueueError):
                action(run_id)


class TestStoppingARunningRun:
    def test_pause_keeps_the_checkpoint_and_resume_continues_from_it(self, queue, harness, store):
        job = queue.submit({"name": "a", "gated": True, "steps": 4})
        run_id = job.run_id
        # Let two steps finish, then ask for a pause while it waits on the third.
        for _ in range(2):
            assert harness.arrived("a").wait(TIMEOUT)
            harness.arrived("a").clear()
            harness.gate("a").set()
        assert harness.arrived("a").wait(TIMEOUT)
        queue.pause(run_id)
        assert queue.get(run_id).stop_requested == "pause"
        harness.gate("a").set()
        wait_until(queue, lambda: status(queue, run_id) == "paused")
        assert queue.get(run_id).stop_requested is None
        assert [r["step"] for r in store.load_rows(run_id)["T"]] == [0, 1]

        harness.arrived("a").clear()
        queue.resume(run_id)
        for _ in range(2):
            assert harness.arrived("a").wait(TIMEOUT)
            harness.arrived("a").clear()
            harness.gate("a").set()
        wait_until(queue, lambda: status(queue, run_id) == "complete")
        # Resumed at step 2, not from zero; the checkpoint is gone once done.
        assert harness.started == ["a", "a"]
        assert store.load_rows(run_id) == {}

    def test_cancel_discards_the_checkpoint(self, queue, harness, store):
        run_id = queue.submit({"name": "a", "gated": True, "steps": 3}).run_id
        assert harness.arrived("a").wait(TIMEOUT)
        harness.arrived("a").clear()
        harness.gate("a").set()
        assert harness.arrived("a").wait(TIMEOUT)
        assert store.load_rows(run_id)["T"] == [{"step": 0}]
        queue.cancel(run_id)
        harness.gate("a").set()
        wait_until(queue, lambda: status(queue, run_id) == "cancelled")
        assert store.load_rows(run_id) == {}
        assert run_id not in [j.run_id for j in queue.pending()]

    def test_resuming_after_the_stop_already_landed_requeues_it(self, queue, harness):
        """Paused, then resumed while the engine was already winding down:
        what was last asked is "run", so it must not end up parked."""
        hold = threading.Event()
        harness.hold_before_stopping["a"] = hold
        run_id = queue.submit({"name": "a", "gated": True, "steps": 2}).run_id
        assert harness.arrived("a").wait(TIMEOUT)
        queue.pause(run_id)
        harness.arrived("a").clear()
        harness.gate("a").set()
        # Only once the runner has actually seen the stop is it too late to
        # take back -- resuming before that would just be an ordinary resume.
        assert harness.stopping.setdefault("a", threading.Event()).wait(TIMEOUT)
        queue.resume(run_id)
        harness.hold_before_stopping.pop("a")
        hold.set()
        for _ in range(2):  # requeued, restarted, and run to the end
            assert harness.arrived("a").wait(TIMEOUT)
            harness.arrived("a").clear()
            harness.gate("a").set()
        wait_until(queue, lambda: status(queue, run_id) == "complete")
        assert harness.started == ["a", "a"]


class TestQueuePause:
    def test_pausing_the_queue_pauses_the_running_run_and_resuming_restores_it(
        self, queue, harness
    ):
        run_id = queue.submit({"name": "a", "gated": True, "steps": 2}).run_id
        b = queue.submit({"name": "b"}).run_id
        assert harness.arrived("a").wait(TIMEOUT)
        queue.pause_all()
        harness.gate("a").set()
        wait_until(queue, lambda: status(queue, run_id) == "paused")
        assert queue.paused
        assert status(queue, b) == "queued"  # waiting, not individually paused
        assert "b" not in harness.started

        harness.arrived("a").clear()
        queue.resume_all()
        for _ in range(2):
            assert harness.arrived("a").wait(TIMEOUT)
            harness.arrived("a").clear()
            harness.gate("a").set()
        wait_until(queue, lambda: status(queue, b) == "complete")
        assert harness.started == ["a", "a", "b"]

    def test_resuming_the_queue_leaves_individually_paused_runs_paused(self, queue, harness):
        blocker = block_worker(queue, harness)
        b = queue.submit({"name": "b"}).run_id
        queue.pause(b)
        queue.pause_all()
        queue.resume_all()
        release(queue, harness, "blocker", blocker)
        assert status(queue, b) == "paused"


class TestDurability:
    def test_state_is_written_on_every_structural_change(self, queue, harness, store):
        blocker = block_worker(queue, harness)
        b = queue.submit({"name": "b"}).run_id
        queue.pause(b)
        state = store.load_state()
        assert [(j["run_id"], j["status"]) for j in state["jobs"]] == [
            (blocker, "running"),
            (b, "paused"),
        ]
        release(queue, harness, "blocker", blocker)
        assert [j["run_id"] for j in store.load_state()["jobs"]] == [b]

    def test_restore_resumes_an_interrupted_run_from_its_checkpoint(self, harness, store):
        store.save_state(
            {
                "version": 1,
                "paused": False,
                "jobs": [
                    {
                        "run_id": "r1",
                        "name": "a",
                        "request": {"name": "a", "steps": 3},
                        "status": "running",
                        "submitted_at": 1.0,
                    },
                    {
                        "run_id": "r2",
                        "name": "b",
                        "request": {"name": "b"},
                        "status": "queued",
                        "submitted_at": 2.0,
                    },
                ],
            }
        )
        store.append_row("r1", "T", {"step": 0})
        store.append_row("r1", "T", {"step": 1})

        fresh = JobQueue(runner=harness.runner, store=store)
        assert fresh.restore() == 2
        wait_until(fresh, lambda: status(fresh, "r2") == "complete")
        assert harness.started == ["a", "b"]  # interrupted run first, same id
        assert fresh.get("r1").status == "complete"

    def test_restore_keeps_paused_runs_paused_and_honours_a_pending_cancel(self, harness, store):
        store.save_state(
            {
                "version": 1,
                "paused": False,
                "jobs": [
                    {"run_id": "p", "request": {"name": "p"}, "status": "paused"},
                    {
                        "run_id": "x",
                        "request": {"name": "x"},
                        "status": "running",
                        "stop_requested": "cancel",
                    },
                    {
                        "run_id": "q",
                        "request": {"name": "q"},
                        "status": "running",
                        "stop_requested": "pause",
                    },
                ],
            }
        )
        store.append_row("x", "T", {"step": 0})
        fresh = JobQueue(runner=harness.runner, store=store)
        assert fresh.restore() == 2
        assert fresh.get("x") is None
        assert store.load_rows("x") == {}
        assert (status(fresh, "p"), status(fresh, "q")) == ("paused", "paused")

    def test_restore_of_a_paused_queue_starts_nothing(self, harness, store):
        store.save_state(
            {
                "version": 1,
                "paused": True,
                "jobs": [{"run_id": "a", "request": {"name": "a"}, "status": "queued"}],
            }
        )
        fresh = JobQueue(runner=harness.runner, store=store)
        fresh.restore()
        assert fresh.paused and status(fresh, "a") == "queued"
        fresh.resume_all()
        wait_until(fresh, lambda: status(fresh, "a") == "complete")

    def test_restore_translates_a_legacy_request_and_persists_the_new_shape(
        self, harness, store, tmp_path
    ):
        """A state.json written before the contract was condensed -- a
        multi-day sweep can be sitting in one -- comes back with the new
        field names, on the job, on its snapshot, and on disk."""
        legacy = {
            "name": "sweep",
            "tickers": ["RSP"],
            "profit_targets": [0.005],
            "sizing_model": "fixed",
            "strategy_params": {"allocation_pct": 0.05},
            "fill_model": "intrabar",
            "n_jobs": 11,
            "search_strategy": "grid",
            "search_direction": "maximize",
        }
        store.save_state(
            {
                "version": 1,
                "paused": True,
                "jobs": [{"run_id": "old", "request": legacy, "status": "queued"}],
            }
        )
        fresh = JobQueue(runner=harness.runner, store=store)
        assert fresh.restore() == 1
        expected = {
            "name": "sweep",
            "tickers": ["RSP"],
            "targets": [0.005],
            "model": "fixed",
            "params": {"allocation_pct": 0.05},
            "fill": "intrabar",
            "jobs": 11,
        }
        assert fresh.get("old").request == expected
        assert fresh.get("old").snapshot()["req"] == expected
        on_disk = json.loads((tmp_path / "queue" / "state.json").read_text(encoding="utf-8"))
        assert on_disk["jobs"][0]["request"] == expected

    def test_a_running_job_with_a_pending_stop_reports_it_as_its_status(self, queue, harness):
        run_id = block_worker(queue, harness, "busy")
        queue.pause(run_id)
        assert queue.get(run_id).snapshot()["status"] == "pausing"
        queue.resume(run_id)
        queue.cancel(run_id)
        assert queue.get(run_id).snapshot()["status"] == "cancelling"
        harness.gate("busy").set()
        wait_until(queue, lambda: status(queue, run_id) == "cancelled")

    def test_a_line_cut_short_by_a_crash_is_skipped(self, store, tmp_path):
        store.append_row("r", "T", {"step": 0})
        path = tmp_path / "queue" / "r.rows.jsonl"
        with path.open("a", encoding="utf-8") as handle:
            handle.write('{"ticker": "T", "row": {"st')
        assert store.load_rows("r") == {"T": [{"step": 0}]}

    def test_a_corrupt_state_file_starts_empty_rather_than_failing(self, store, tmp_path):
        (tmp_path / "queue").mkdir(parents=True)
        (tmp_path / "queue" / "state.json").write_text("{not json", encoding="utf-8")
        assert store.load_state() is None

    def test_numpy_scalars_in_rows_survive_the_round_trip(self, store):
        np = pytest.importorskip("numpy")
        store.append_row("r", "T", {"a": np.float64(1.5), "b": np.int64(3), "c": float("nan")})
        row = store.load_rows("r")["T"][0]
        assert row["a"] == 1.5 and row["b"] == 3 and row["c"] != row["c"]

    def test_an_in_memory_queue_touches_no_disk(self, harness, tmp_path, monkeypatch):
        monkeypatch.setenv("VAI_QUEUE_DIR", str(tmp_path / "should-not-exist"))
        q = JobQueue(runner=harness.runner)
        run_id = q.submit({"name": "a"}).run_id
        wait_until(q, lambda: status(q, run_id) == "complete")
        assert q.restore() == 0
        assert not (tmp_path / "should-not-exist").exists()


def test_state_json_is_plain_json(store, tmp_path):
    """Hand-inspectable, which matters when a queue needs to be debugged at 2am."""
    store.save_state({"version": 1, "paused": False, "jobs": []})
    assert (
        json.loads((tmp_path / "queue" / "state.json").read_text(encoding="utf-8"))["version"] == 1
    )


def test_restore_keeps_submission_order_distinct_from_execution_order(harness, store):
    """A reordered queue persists in EXECUTION order; all() must still list
    by submission, and the order must still run as persisted."""
    store.save_state(
        {
            "version": 1,
            "paused": True,
            "jobs": [
                {
                    "run_id": "late",
                    "request": {"name": "late"},
                    "status": "queued",
                    "submitted_at": 20.0,
                },
                {
                    "run_id": "early",
                    "request": {"name": "early"},
                    "status": "queued",
                    "submitted_at": 10.0,
                },
            ],
        }
    )
    fresh = JobQueue(runner=harness.runner, store=store)
    fresh.restore()
    assert [j.run_id for j in fresh.all()] == ["late", "early"]  # newest submitted first
    assert [j.run_id for j in fresh.pending()] == ["late", "early"]  # runs as persisted
    assert fresh.get("late").queue_position == 1
