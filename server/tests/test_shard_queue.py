"""server/jobs.py's shard rules: claim, ownership, release, timeout, pause.

Remote shards are driven directly through the queue's protocol methods
(no HTTP), with an injected clock so timeouts are tested without
sleeping. The local shard -- the queue's own worker -- is kept paused
unless a test is about it, so remote claims are deterministic.
"""

from __future__ import annotations

import threading
from datetime import datetime

import pytest

from server.jobs import (
    LOCAL_SHARD,
    SHARD_STALE_SECONDS,
    SHARD_TIMEOUT_SECONDS,
    JobQueue,
    NotOwner,
    QueueError,
    QueueStore,
    RunStopped,
    ShardSuperseded,
    UnknownShard,
)

TIMEOUT = 10.0


class Clock:
    def __init__(self) -> None:
        self.now = 1000.0

    def __call__(self) -> float:
        return self.now

    def advance(self, seconds: float) -> None:
        self.now += seconds


class WallClock:
    """The time-of-day clock lockout windows check, independent of
    `Clock` above -- monotonic seconds cannot answer "is it 7am"."""

    def __init__(self) -> None:
        self.now = datetime(2024, 1, 1, 12, 0)  # noon; the date is arbitrary

    def __call__(self) -> datetime:
        return self.now

    def set(self, hour: int, minute: int = 0) -> None:
        self.now = self.now.replace(hour=hour, minute=minute)


class LocalRunner:
    """The local worker's runner. With "gated", it waits before step
    "gate_at" (default 0) until the test releases it."""

    def __init__(self) -> None:
        self.started: list[str] = []
        self.release = threading.Event()
        self.arrived = threading.Event()

    def __call__(self, request, report, control):
        self.started.append(request["name"])
        done = len(control.completed_rows("T"))
        for step in range(done, request.get("steps", 1)):
            if request.get("gated") and step == request.get("gate_at", 0):
                self.arrived.set()
                assert self.release.wait(TIMEOUT)
            if control.should_stop():
                raise RunStopped(request["name"])
            control.record_row("T", {"step": step})
        return {"name": request["name"], "resumed_from": done}


@pytest.fixture
def clock() -> Clock:
    return Clock()


@pytest.fixture
def wall_clock() -> WallClock:
    return WallClock()


@pytest.fixture
def runner() -> LocalRunner:
    return LocalRunner()


@pytest.fixture
def completed() -> list[str]:
    return []


@pytest.fixture
def queue(tmp_path, clock, wall_clock, runner, completed) -> JobQueue:
    q = JobQueue(
        runner=runner,
        on_complete=lambda job: completed.append(job.run_id),
        store=QueueStore(lambda: tmp_path / "queue"),
        clock=clock,
        wall_clock=wall_clock,
    )
    q.pause_shard(LOCAL_SHARD)
    return q


def wait_until(queue: JobQueue, predicate) -> None:
    with queue._condition:
        assert queue._condition.wait_for(predicate, timeout=TIMEOUT), "condition never held"


def shard_view(queue: JobQueue, name: str) -> dict:
    return next(s for s in queue.shards() if s["name"] == name)


class TestRegistration:
    def test_the_local_shard_is_always_listed_first(self, queue):
        queue.register_shard("zeta", "i1")
        queue.register_shard("alpha", "i2")
        assert [s["name"] for s in queue.shards()] == [LOCAL_SHARD, "alpha", "zeta"]
        assert shard_view(queue, LOCAL_SHARD)["local"] is True

    def test_local_is_a_reserved_name(self, queue):
        with pytest.raises(QueueError):
            queue.register_shard(LOCAL_SHARD, "i1")

    def test_a_remote_call_cannot_impersonate_the_local_shard(self, queue):
        with pytest.raises(UnknownShard):
            queue.shard_sync(LOCAL_SHARD, LOCAL_SHARD, None)

    def test_an_unregistered_shard_is_told_so(self, queue):
        with pytest.raises(UnknownShard):
            queue.claim("ghost", "i1")

    def test_a_newer_process_supersedes_the_old_one_and_takes_nothing_with_it(self, queue):
        queue.register_shard("fast", "old")
        job = queue.submit({"name": "a"})
        assert queue.claim("fast", "old")[0].run_id == job.run_id

        queue.register_shard("fast", "new")

        with pytest.raises(ShardSuperseded):
            queue.shard_sync("fast", "old", job.run_id)
        # Released at once rather than after a timeout: the new process
        # is not running it, whatever the old one is doing.
        assert queue.get(job.run_id).status == "queued"
        assert queue.claim("fast", "new")[0].run_id == job.run_id

    def test_a_retried_registration_from_the_same_process_keeps_its_run(self, queue):
        queue.register_shard("fast", "same")
        job = queue.submit({"name": "a"})
        queue.claim("fast", "same")
        queue.register_shard("fast", "same")
        assert queue.get(job.run_id).status == "running"
        assert queue.shard_sync("fast", "same", job.run_id)["owned"] is True

    def test_a_pause_survives_re_registration(self, queue):
        queue.register_shard("fast", "old")
        queue.pause_shard("fast")
        queue.register_shard("fast", "new")
        assert shard_view(queue, "fast")["state"] == "paused"


class TestClaimAndReport:
    def test_claim_hands_out_runs_in_queue_order_one_per_shard(self, queue):
        queue.register_shard("a", "ia")
        queue.register_shard("b", "ib")
        first = queue.submit({"name": "first"})
        second = queue.submit({"name": "second"})

        assert queue.claim("a", "ia")[0].run_id == first.run_id
        assert queue.claim("b", "ib")[0].run_id == second.run_id
        assert queue.get(first.run_id).shard == "a"
        assert queue.get(second.run_id).snapshot()["shard"] == "b"
        assert shard_view(queue, "a")["run"]["id"] == first.run_id

    def test_nothing_to_claim_returns_none(self, queue):
        queue.register_shard("a", "ia")
        assert queue.claim("a", "ia") is None

    def test_a_paused_shard_claims_nothing(self, queue):
        queue.register_shard("a", "ia")
        queue.submit({"name": "x"})
        queue.pause_shard("a")
        assert queue.claim("a", "ia") is None

    def test_a_queue_pause_holds_remote_shards_too(self, queue):
        queue.register_shard("a", "ia")
        queue.submit({"name": "x"})
        queue.pause_all()
        assert queue.claim("a", "ia") is None

    def test_claim_waits_for_a_submission(self, queue):
        queue.register_shard("a", "ia")
        result: list = []
        waiter = threading.Thread(
            target=lambda: result.append(queue.claim("a", "ia", wait=TIMEOUT))
        )
        waiter.start()
        job = queue.submit({"name": "late"})
        waiter.join(TIMEOUT)
        assert result and result[0][0].run_id == job.run_id

    def test_synced_rows_are_checkpointed_and_progress_is_observable(self, queue):
        queue.register_shard("a", "ia")
        job = queue.submit({"name": "x"})
        queue.claim("a", "ia")

        answer = queue.shard_sync(
            "a", "ia", job.run_id, progress=0.5, message="1/2", rows=[("T", {"step": 0})]
        )

        assert answer == {"paused": False, "locked_out": False, "owned": True, "stop": False}
        assert queue.get(job.run_id).progress == 0.5
        assert queue.get(job.run_id).message == "1/2"
        assert queue._store.load_rows(job.run_id) == {"T": [{"step": 0}]}

    def test_a_heartbeat_with_no_run_is_not_ownership_of_anything(self, queue):
        queue.register_shard("a", "ia")
        assert queue.shard_sync("a", "ia", None) == {
            "paused": False,
            "locked_out": False,
            "owned": False,
            "stop": False,
        }

    def test_complete_archives_the_report(self, queue, completed):
        queue.register_shard("a", "ia")
        job = queue.submit({"name": "x"})
        queue.claim("a", "ia")
        queue.shard_finish("a", "ia", job.run_id, "complete", result={"id": ""})

        assert queue.get(job.run_id).status == "complete"
        assert queue.get(job.run_id).result == {"id": ""}
        assert queue.get(job.run_id).shard is None
        assert completed == [job.run_id]
        assert shard_view(queue, "a")["state"] == "idle"
        # The checkpoint of a finished run is discarded, as for local runs.
        assert queue._store.load_rows(job.run_id) == {}

    def test_failed_is_terminal(self, queue):
        queue.register_shard("a", "ia")
        job = queue.submit({"name": "x"})
        queue.claim("a", "ia")
        queue.shard_finish("a", "ia", job.run_id, "failed", error="ValueError: boom")
        assert queue.get(job.run_id).status == "failed"
        assert queue.get(job.run_id).error == "ValueError: boom"

    def test_released_goes_back_to_the_front_with_its_checkpoint(self, queue):
        queue.register_shard("a", "ia")
        queue.register_shard("b", "ib")
        job = queue.submit({"name": "x"})
        later = queue.submit({"name": "later"})
        queue.claim("a", "ia")
        queue.shard_sync("a", "ia", job.run_id, rows=[("T", {"step": 0})])

        queue.shard_finish("a", "ia", job.run_id, "released", error="shutting down")

        assert queue.get(job.run_id).status == "queued"
        assert queue.get(job.run_id).queue_position == 1
        assert later.queue_position == 2
        claimed, rows = queue.claim("b", "ib")
        assert claimed.run_id == job.run_id
        assert rows == {"T": [{"step": 0}]}


class TestOwnership:
    def test_a_shard_cannot_report_on_a_run_it_does_not_hold(self, queue):
        queue.register_shard("a", "ia")
        queue.register_shard("b", "ib")
        job = queue.submit({"name": "x"})
        queue.claim("a", "ia")

        answer = queue.shard_sync("b", "ib", job.run_id, rows=[("T", {"step": 9})])

        assert answer["owned"] is False
        assert queue._store.load_rows(job.run_id) == {}
        with pytest.raises(NotOwner):
            queue.shard_finish("b", "ib", job.run_id, "complete", result={})
        assert queue.get(job.run_id).status == "running"

    def test_claiming_again_releases_what_the_shard_lost_track_of(self, queue):
        """A claim whose answer never arrived: the shard asks again, and
        the run it was given comes straight back to it."""
        queue.register_shard("a", "ia")
        job = queue.submit({"name": "x"})
        queue.claim("a", "ia")
        again = queue.claim("a", "ia")
        assert again[0].run_id == job.run_id
        assert queue.get(job.run_id).shard == "a"


class TestTimeout:
    def test_a_quiet_shard_goes_stale_then_offline_and_loses_its_run(self, queue, clock):
        queue.register_shard("a", "ia")
        job = queue.submit({"name": "x"})
        queue.claim("a", "ia")

        clock.advance(SHARD_STALE_SECONDS + 1)
        assert queue.reap() == []
        assert shard_view(queue, "a")["conn"] == "stale"

        clock.advance(SHARD_TIMEOUT_SECONDS)
        assert queue.reap() == [job.run_id]
        view = shard_view(queue, "a")
        assert view["conn"] == "offline"
        assert view["run"] is None
        assert queue.get(job.run_id).status == "queued"
        assert "stopped responding" in queue.get(job.run_id).message

    def test_a_shard_that_comes_back_is_refused_its_old_run(self, queue, clock):
        queue.register_shard("a", "ia")
        queue.register_shard("b", "ib")
        job = queue.submit({"name": "x"})
        queue.claim("a", "ia")
        clock.advance(SHARD_TIMEOUT_SECONDS + 1)
        queue.shard_sync("b", "ib", None)  # b stays fresh
        queue.reap()
        queue.claim("b", "ib")

        answer = queue.shard_sync("a", "ia", job.run_id, rows=[("T", {"step": 0})])

        assert answer["owned"] is False
        assert shard_view(queue, "a")["conn"] == "online"
        assert queue.get(job.run_id).shard == "b"

    def test_the_local_shard_never_times_out(self, queue, clock):
        clock.advance(SHARD_TIMEOUT_SECONDS * 10)
        queue.reap()
        assert shard_view(queue, LOCAL_SHARD)["conn"] == "online"

    def test_a_stop_asked_before_the_shard_vanished_is_honoured(self, queue, clock):
        queue.register_shard("a", "ia")
        paused = queue.submit({"name": "p"})
        queue.claim("a", "ia")
        queue.pause(paused.run_id)
        clock.advance(SHARD_TIMEOUT_SECONDS + 1)
        queue.reap()
        assert queue.get(paused.run_id).status == "paused"

        queue.register_shard("b", "ib")
        cancelled = queue.submit({"name": "c"})
        queue.claim("b", "ib")
        queue.cancel(cancelled.run_id)
        clock.advance(SHARD_TIMEOUT_SECONDS + 1)
        queue.reap()
        assert queue.get(cancelled.run_id).status == "cancelled"

    def test_only_an_offline_shard_can_be_forgotten(self, queue, clock):
        queue.register_shard("a", "ia")
        with pytest.raises(QueueError):
            queue.forget_shard("a")
        with pytest.raises(QueueError):
            queue.forget_shard(LOCAL_SHARD)
        clock.advance(SHARD_TIMEOUT_SECONDS + 1)
        queue.forget_shard("a")
        assert [s["name"] for s in queue.shards()] == [LOCAL_SHARD]


class TestStopping:
    def test_a_run_pause_reaches_the_shard_and_files_the_run_paused(self, queue):
        queue.register_shard("a", "ia")
        job = queue.submit({"name": "x"})
        queue.claim("a", "ia")
        queue.pause(job.run_id)

        assert queue.shard_sync("a", "ia", job.run_id)["stop"] is True
        queue.shard_finish("a", "ia", job.run_id, "stopped")

        assert queue.get(job.run_id).status == "paused"
        assert shard_view(queue, "a")["state"] == "idle"

    def test_a_run_cancel_reaches_the_shard_and_discards_the_checkpoint(self, queue):
        queue.register_shard("a", "ia")
        job = queue.submit({"name": "x"})
        queue.claim("a", "ia")
        queue.shard_sync("a", "ia", job.run_id, rows=[("T", {"step": 0})])
        queue.cancel(job.run_id)
        assert queue.shard_sync("a", "ia", job.run_id)["stop"] is True
        queue.shard_finish("a", "ia", job.run_id, "stopped")
        assert queue.get(job.run_id).status == "cancelled"
        assert queue._store.load_rows(job.run_id) == {}

    def test_pausing_a_shard_hands_its_run_to_another(self, queue):
        queue.register_shard("a", "ia")
        queue.register_shard("b", "ib")
        job = queue.submit({"name": "x"})
        queue.claim("a", "ia")
        queue.shard_sync("a", "ia", job.run_id, rows=[("T", {"step": 0})])

        view = queue.pause_shard("a")
        assert view["state"] == "pausing"
        assert queue.shard_sync("a", "ia", job.run_id) == {
            "paused": True,
            "locked_out": False,
            "owned": True,
            "stop": True,
        }
        queue.shard_finish("a", "ia", job.run_id, "stopped")

        assert queue.get(job.run_id).status == "queued"
        assert "paused shard a" in queue.get(job.run_id).message
        assert shard_view(queue, "a")["state"] == "paused"
        claimed, rows = queue.claim("b", "ib")
        assert claimed.run_id == job.run_id
        assert rows == {"T": [{"step": 0}]}

    def test_pause_all_and_resume_all_cover_every_shard(self, queue):
        queue.register_shard("a", "ia")
        queue.set_shards_paused(True)
        assert {s["state"] for s in queue.shards()} == {"paused"}
        queue.set_shards_paused(False)
        assert {s["state"] for s in queue.shards()} == {"idle"}


class TestLocalShard:
    def test_a_paused_local_shard_leaves_work_for_remote_shards(self, queue, runner):
        queue.register_shard("a", "ia")
        job = queue.submit({"name": "x"})
        assert queue.claim("a", "ia")[0].run_id == job.run_id
        assert runner.started == []

    def test_resuming_the_local_shard_starts_the_worker(self, queue, runner):
        job = queue.submit({"name": "x"})
        queue.resume_shard(LOCAL_SHARD)
        wait_until(queue, lambda: queue.get(job.run_id).status == "complete")
        assert runner.started == ["x"]

    def test_pausing_the_local_shard_mid_run_releases_it_to_a_remote_one(self, queue, runner):
        queue.resume_shard(LOCAL_SHARD)
        job = queue.submit({"name": "x", "gated": True, "gate_at": 1, "steps": 2})
        assert runner.arrived.wait(TIMEOUT)
        assert shard_view(queue, LOCAL_SHARD)["run"]["id"] == job.run_id

        queue.pause_shard(LOCAL_SHARD)
        runner.release.set()
        wait_until(queue, lambda: queue.get(job.run_id).status == "queued")
        assert "paused local shard" in queue.get(job.run_id).message

        queue.register_shard("a", "ia")
        claimed, rows = queue.claim("a", "ia")
        assert claimed.run_id == job.run_id
        # The step the local worker finished before stopping travels
        # with the run.
        assert rows == {"T": [{"step": 0}]}

    def test_a_local_shard_pause_survives_a_restart(self, tmp_path, clock, runner):
        store = QueueStore(lambda: tmp_path / "q")
        first = JobQueue(runner=runner, store=store, clock=clock)
        first.pause_shard(LOCAL_SHARD)
        first.register_shard("a", "ia")
        first.pause_shard("a")
        first.submit({"name": "x"})
        first.pause_all()  # keep the (paused) local worker from mattering

        second = JobQueue(runner=runner, store=store, clock=clock)
        second.restore()
        assert shard_view(second, LOCAL_SHARD)["state"] == "paused"
        # A remote shard's pause is remembered until it registers again.
        second.register_shard("a", "new-instance")
        assert shard_view(second, "a")["state"] == "paused"


class TestLockoutSchedule:
    """A daily lockout window: same effect as a manual pause (no new
    claim, a running job hands back), computed fresh from wall-clock
    time rather than stored as one -- see server/jobs.py's own
    "LOCKOUT WINDOWS" docstring section for why."""

    def test_an_unregistered_name_is_accepted(self, queue):
        """Deliberately permissive: a window can be set for a shard that
        has never registered, so it is already in force the first time
        that machine connects."""
        written = queue.set_shard_schedule("not-yet-connected", True, "07:00", "19:00")
        assert written == {"enabled": True, "start": "07:00", "end": "19:00"}

    def test_enabling_without_both_times_is_refused(self, queue):
        queue.register_shard("a", "ia")
        with pytest.raises(QueueError):
            queue.set_shard_schedule("a", True, "07:00", None)
        with pytest.raises(QueueError):
            queue.set_shard_schedule("a", True, None, None)

    def test_a_malformed_time_is_refused(self, queue):
        queue.register_shard("a", "ia")
        with pytest.raises(QueueError):
            queue.set_shard_schedule("a", True, "7am", "19:00")
        with pytest.raises(QueueError):
            queue.set_shard_schedule("a", True, "07:00", "25:00")

    def test_set_then_read_round_trips(self, queue):
        queue.register_shard("a", "ia")
        written = queue.set_shard_schedule("a", True, "07:00", "19:00")
        assert written == {"enabled": True, "start": "07:00", "end": "19:00"}
        assert queue.shard_schedule("a") == written
        assert shard_view(queue, "a")["schedule"] == written

    def test_disabling_with_no_times_clears_it(self, queue):
        queue.register_shard("a", "ia")
        queue.set_shard_schedule("a", True, "07:00", "19:00")
        cleared = queue.set_shard_schedule("a", False, None, None)
        assert cleared is None
        assert queue.shard_schedule("a") is None

    def test_disabling_with_times_kept_keeps_them_for_next_time(self, queue):
        queue.register_shard("a", "ia")
        queue.set_shard_schedule("a", True, "07:00", "19:00")
        off = queue.set_shard_schedule("a", False, "07:00", "19:00")
        assert off == {"enabled": False, "start": "07:00", "end": "19:00"}
        assert queue.shard_schedule("a")["enabled"] is False

    def test_a_remote_shard_claims_nothing_inside_its_window(self, queue, wall_clock):
        queue.register_shard("a", "ia")
        queue.set_shard_schedule("a", True, "07:00", "19:00")
        queue.submit({"name": "x"})

        wall_clock.set(12, 0)
        assert queue.claim("a", "ia") is None
        assert shard_view(queue, "a")["state"] == "locked_out"
        assert shard_view(queue, "a")["paused"] is False  # never a manual pause

        wall_clock.set(20, 0)
        claimed, _rows = queue.claim("a", "ia")
        assert claimed.name == "x"

    def test_an_overnight_window_wraps_past_midnight(self, queue, wall_clock):
        queue.register_shard("a", "ia")
        queue.set_shard_schedule("a", True, "22:00", "06:00")
        queue.submit({"name": "x"})

        wall_clock.set(23, 30)
        assert queue.claim("a", "ia") is None
        wall_clock.set(3, 0)
        assert queue.claim("a", "ia") is None
        wall_clock.set(12, 0)
        claimed, _rows = queue.claim("a", "ia")
        assert claimed.name == "x"

    def test_the_local_worker_does_not_dispatch_inside_its_window(self, queue, wall_clock, runner):
        queue.set_shard_schedule(LOCAL_SHARD, True, "07:00", "19:00")
        wall_clock.set(12, 0)
        queue.resume_shard(LOCAL_SHARD)
        job = queue.submit({"name": "x"})

        with queue._condition:
            assert not queue._condition.wait_for(lambda: bool(runner.started), timeout=0.3)
        assert queue.get(job.run_id).status == "queued"

        wall_clock.set(20, 0)
        # Nothing re-checks the window on its own -- the same as a manual
        # pause, becoming eligible again wakes the worker on the next
        # queue change. resume_shard is a convenient no-op nudge here;
        # what matters is that the window no longer covers "now".
        queue.resume_shard(LOCAL_SHARD)
        wait_until(queue, lambda: queue.get(job.run_id).status == "complete")
        assert runner.started == ["x"]

    def test_a_window_opening_mid_run_hands_the_job_back(self, queue, wall_clock, runner):
        wall_clock.set(6, 0)
        queue.set_shard_schedule(LOCAL_SHARD, True, "07:00", "19:00")
        queue.resume_shard(LOCAL_SHARD)
        job = queue.submit({"name": "x", "gated": True, "gate_at": 1, "steps": 2})
        assert runner.arrived.wait(TIMEOUT)

        wall_clock.set(7, 0)  # the window opens while a configuration is in flight
        runner.release.set()
        wait_until(queue, lambda: queue.get(job.run_id).status == "queued")

        queue.register_shard("a", "ia")
        claimed, rows = queue.claim("a", "ia")
        assert claimed.run_id == job.run_id
        assert rows == {"T": [{"step": 0}]}

    def test_a_schedule_survives_a_restart(self, tmp_path, clock, wall_clock, runner):
        store = QueueStore(lambda: tmp_path / "q")
        first = JobQueue(runner=runner, store=store, clock=clock, wall_clock=wall_clock)
        first.pause_shard(LOCAL_SHARD)
        first.register_shard("a", "ia")
        first.set_shard_schedule("a", True, "07:00", "19:00")

        second = JobQueue(runner=runner, store=store, clock=clock, wall_clock=wall_clock)
        second.restore()
        # Set before this shard has registered with the NEW process at
        # all -- restore() must not require a live Shard to hold it.
        assert second.shard_schedule("a") == {"enabled": True, "start": "07:00", "end": "19:00"}
