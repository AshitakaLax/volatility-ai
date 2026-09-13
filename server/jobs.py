"""A durable, controllable queue for backtest runs.

--------------------------------------------------------------------
WHY A QUEUE AT ALL

One engine run costs roughly 23 seconds on ten years of minute bars --
measured, not estimated; an earlier guess of five minutes in plan.md was
wrong by a factor of ten and shaped a whole staging design before anyone
checked. Either way it is far too long for a synchronous request: the
POST returns an id immediately and the work happens behind it.

--------------------------------------------------------------------
WHY A THREAD AND NOT THE EVENT LOOP

run_sweep is CPU-bound pandas. Running it on the event loop would block
every other request for its whole duration, including the read-only live
WebSocket that an operator may be watching a real deployment through.
One worker thread keeps the loop responsive.

ONE worker here, but that is about ORDERING, not about cores. Runs queue
so their progress is legible and so two submissions cannot interleave
their output; parallelism happens INSIDE a run, where server/backtest.py
hands run_sweep an n_jobs of one-less-than-the-core-count.

An earlier version of this file justified the single worker by saying a
pool would starve a live trading loop sharing the machine. That premise
was wrong for this deployment -- the loop runs on separate hardware --
and the reasoning is corrected rather than quietly deleted, because the
constraint it described is real on a box that does run both.

--------------------------------------------------------------------
WHY IT IS NOW DURABLE, WHEN IT DELIBERATELY WAS NOT

This file used to say, under "what is deliberately not here", that a
restart losing queued and running jobs was acceptable: a queued run was
a few seconds of intent and resubmitting it was trivial. That was true
when a run took half a minute. It stopped being true, and the evidence
is specific:

  tools/sweep_rsp_all.py queued 84 runs -- 108,672 configurations, about
  four days -- and the machine rebooted eleven hours in. Everything
  queued was gone, and so was the run in flight: 1,536 configurations
  and 85 minutes of engine time, lost at roughly 99%.

So the premise is recorded as falsified rather than the paragraph being
deleted. What is persisted, under VAI_QUEUE_DIR (default output/queue/,
which is git-ignored):

  state.json          the pending jobs, their order, and whether the
                      queue itself is paused. Rewritten atomically on
                      every structural change (submit, pause, move,
                      finish) -- never on progress ticks, which arrive
                      once per configuration.
  <run_id>.rows.jsonl one line per FINISHED configuration of a run in
                      progress, appended as each lands. This is what
                      lets a run resume at configuration granularity
                      rather than from zero: a restart now costs the
                      in-flight batch (at most n_jobs configurations),
                      not the run.

A run that was RUNNING when the process died comes back queued, at the
front, and resumes from its rows. Paused runs come back paused. Nothing
terminal is persisted here -- completed runs already live in
server/history.py, and a failed or cancelled run has nothing to resume.

Still not a real task queue: no second worker, no retries, no
distributed anything. The narrow version of durability, for the same
reason history.py is the narrow version of persistence.

--------------------------------------------------------------------
STOPPING A RUN THAT IS ALREADY RUNNING

Pause and cancel on a RUNNING job are requests, honoured cooperatively.
The runner is handed a RunControl and checks should_stop() before it
starts each new configuration; server/backtest.py does that through the
search strategy's suggest(), which ends run_sweep's loop cleanly. In the
parallel path a batch already handed to the process pool finishes first
(on RSP's full history that is up to ~60 seconds), and its rows are
checkpointed -- so a pause loses nothing and a cancel waits at most one
batch. Killing worker processes mid-configuration instead would be
faster to stop and would throw away work that is, by then, nearly done.

A runner that honoured a stop raises RunStopped; the queue then files the
job as paused (resumable, rows kept) or cancelled (rows discarded)
according to what was asked.
"""

from __future__ import annotations

import contextlib
import json
import logging
import os
import threading
import time
import traceback
import uuid
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal

logger = logging.getLogger("Optimizer")

RunStatus = Literal["queued", "running", "paused", "cancelled", "complete", "failed"]
StopRequest = Literal["pause", "cancel"]

# Waiting for its turn (queued) or waiting to be allowed one (paused).
# Both hold a place in the order; both can be moved.
PENDING: frozenset[str] = frozenset({"queued", "paused"})
TERMINAL: frozenset[str] = frozenset({"cancelled", "complete", "failed"})

_ROOT = Path(__file__).resolve().parent.parent


class RunStopped(Exception):
    """Raised by a runner that stopped early because it was asked to."""


class QueueError(Exception):
    """A control action that does not apply to the job's current state."""


class UnknownRun(KeyError):
    """No job with that id is known to this queue."""


def directory() -> Path:
    """Where queue state lives. Read at call time, like history.directory,
    so a test can repoint it with monkeypatch.setenv."""
    configured = os.environ.get("VAI_QUEUE_DIR")
    return Path(configured) if configured else _ROOT / "output" / "queue"


def _json_default(value: Any) -> Any:
    """numpy scalars ride along in result rows; everything else is plain."""
    item = getattr(value, "item", None)
    if callable(item):
        return item()
    return str(value)


class QueueStore:
    """The on-disk half. Every method swallows OSError and logs it.

    The same rule history.save follows: a storage fault must never be
    able to fail a backtest. A full disk degrades the queue to exactly its
    old in-memory behavior for as long as the fault lasts, rather than
    stopping a run that would otherwise have finished.
    """

    def __init__(self, root: Callable[[], Path] = directory):
        self._root = root
        # Row appends come from the worker thread, state writes from
        # request threads. One lock keeps a checkpoint discard from racing
        # an append into a file that is being deleted.
        self._lock = threading.Lock()

    def save_state(self, state: dict[str, Any]) -> None:
        with self._lock:
            try:
                target = self._root()
                target.mkdir(parents=True, exist_ok=True)
                path = target / "state.json"
                # Temporary name then replace, so a crash mid-write cannot
                # leave a half-written state that loses the whole queue.
                staging = path.with_suffix(".json.tmp")
                staging.write_text(json.dumps(state, default=_json_default), encoding="utf-8")
                staging.replace(path)
            except OSError as exc:
                logger.warning(f"Could not persist queue state: {exc}")

    def load_state(self) -> dict[str, Any] | None:
        try:
            path = self._root() / "state.json"
            if not path.exists():
                return None
            return json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            logger.warning(f"Could not read queue state, starting empty: {exc}")
            return None

    def append_row(self, run_id: str, ticker: str, row: dict[str, Any]) -> None:
        line = json.dumps({"ticker": ticker, "row": row}, default=_json_default)
        with self._lock:
            try:
                target = self._root()
                target.mkdir(parents=True, exist_ok=True)
                with (target / f"{run_id}.rows.jsonl").open("a", encoding="utf-8") as handle:
                    handle.write(line + "\n")
            except OSError as exc:
                logger.warning(f"Could not checkpoint a row for {run_id}: {exc}")

    def load_rows(self, run_id: str) -> dict[str, list[dict[str, Any]]]:
        """Checkpointed rows by ticker, in the order they finished.

        A final line cut short by a crash mid-append is skipped rather than
        failing the load: every line before it is intact, and losing one
        configuration is the whole cost of the crash.
        """
        rows: dict[str, list[dict[str, Any]]] = {}
        try:
            path = self._root() / f"{run_id}.rows.jsonl"
            if not path.exists():
                return rows
            for line in path.read_text(encoding="utf-8").splitlines():
                if not line.strip():
                    continue
                try:
                    entry = json.loads(line)
                except ValueError:
                    continue
                rows.setdefault(entry["ticker"], []).append(entry["row"])
        except OSError as exc:
            logger.warning(f"Could not read checkpoint for {run_id}: {exc}")
        return rows

    def discard(self, run_id: str) -> None:
        with self._lock, contextlib.suppress(OSError):
            (self._root() / f"{run_id}.rows.jsonl").unlink(missing_ok=True)


@dataclass
class Job:
    """One submitted run and everything observers need about it."""

    run_id: str
    request: dict[str, Any]
    # A descriptive label lifted off the request at submit time, so a
    # queued or running job can be shown by name before its report
    # exists. None for an unnamed run.
    name: str | None = None
    status: RunStatus = "queued"
    progress: float = 0.0
    message: str | None = None
    result: dict[str, Any] | None = None
    error: str | None = None
    # Bumped on every mutation, so a poller can tell "nothing changed"
    # from "I missed an update" without diffing the whole payload.
    revision: int = 0
    submitted_at: float = field(default_factory=time.time)
    # 1-indexed place among PENDING jobs in execution order; None when
    # running or finished. Owned by the queue, which is the only thing
    # that knows the order -- a client deriving it from submission order
    # would be wrong the moment anything was moved.
    queue_position: int | None = None
    # A pause/cancel asked of a RUNNING job that it has not yet honoured.
    stop_requested: StopRequest | None = None
    # True when this job is paused only because the whole queue was, so
    # resuming the queue resumes it too instead of skipping past it.
    paused_by_queue: bool = False

    def snapshot(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "name": self.name,
            "status": self.status,
            "progress": round(self.progress, 4),
            "message": self.message,
            "report": self.result,
            "error": self.error,
            "revision": self.revision,
            "queue_position": self.queue_position,
            "stop_requested": self.stop_requested,
            "submitted_at": self.submitted_at,
            # The submitted request, echoed back verbatim -- exactly what
            # the browser itself just POSTed, nothing new exposed. Lets a
            # client describe a QUEUED or RUNNING job's shape (tickers,
            # grid, strategy params) before it has a report to read that
            # from.
            "request": self.request,
        }


class RunControl:
    """What a runner may ask of the queue while it works."""

    def __init__(self, queue: JobQueue, job: Job, rows: dict[str, list[dict[str, Any]]]):
        self._queue = queue
        self._job = job
        self._rows = rows

    def should_stop(self) -> bool:
        """True once a pause or cancel has been asked of this run."""
        with self._queue._condition:
            return self._job.stop_requested is not None

    def completed_rows(self, ticker: str) -> list[dict[str, Any]]:
        """Configurations of `ticker` already finished before this attempt."""
        return list(self._rows.get(ticker, []))

    def record_row(self, ticker: str, row: dict[str, Any]) -> None:
        """Checkpoint one finished configuration. Never raises."""
        if self._queue._store is not None:
            self._queue._store.append_row(self._job.run_id, ticker, row)


class JobQueue:
    """Serial background execution with observable, controllable state.

    Every mutation happens under one lock and then notifies a Condition,
    so a waiter is woken by a real change rather than by a timer. That
    matters for the WebSocket: polling a status dict on a sleep loop
    would add latency to a job that already takes half a minute, and
    would burn a thread doing nothing while it waited.
    """

    def __init__(
        self,
        runner: Callable[..., dict],
        on_complete: Callable[[Job], None] | None = None,
        store: QueueStore | None = None,
    ):
        # Called as runner(request, report, control).
        self._runner = runner
        # Called once per completed job. Injected rather than imported
        # so the queue stays a queue: it knows nothing about where a
        # result is archived, and a test can watch completions without
        # touching a disk.
        self._on_complete = on_complete
        # None keeps the queue purely in memory -- what a unit test wants.
        self._store = store
        # Insertion order is submission order.
        self._jobs: dict[str, Job] = {}
        # Execution order of every non-terminal job, the running one first.
        self._order: list[str] = []
        self._paused = False
        self._condition = threading.Condition()
        self._worker: threading.Thread | None = None

    # ---------------------------------------------------------------
    # Reading
    # ---------------------------------------------------------------

    @property
    def paused(self) -> bool:
        with self._condition:
            return self._paused

    def get(self, run_id: str) -> Job | None:
        with self._condition:
            return self._jobs.get(run_id)

    def all(self) -> list[Job]:
        """Newest first. Insertion order is submission order."""
        with self._condition:
            return list(reversed(list(self._jobs.values())))

    def pending(self) -> list[Job]:
        """Every non-terminal job in the order it will run, running first."""
        with self._condition:
            return [self._jobs[run_id] for run_id in self._order]

    def wait_for_change(self, run_id: str, since: int, timeout: float) -> Job | None:
        """Block until this job's revision passes `since`, or time out.

        A timeout returns the CURRENT job rather than None, so the caller
        can send a heartbeat and distinguish a quiet job from a dead
        connection.
        """
        with self._condition:
            job = self._jobs.get(run_id)
            if job is None:
                return None
            if job.revision > since:
                return job
            self._condition.wait_for(lambda: job.revision > since, timeout=timeout)
            return job

    # ---------------------------------------------------------------
    # Submitting and restoring
    # ---------------------------------------------------------------

    def submit(self, request: dict[str, Any]) -> Job:
        # Whitespace-only is treated as unnamed, matching what the report
        # records -- a job labelled "   " in the running list helps nobody.
        label = str(request.get("name") or "").strip() or None
        job = Job(run_id=uuid.uuid4().hex[:12], request=request, name=label)
        with self._condition:
            self._jobs[job.run_id] = job
            self._order.append(job.run_id)
            self._changed()
        self._ensure_worker()
        return job

    def restore(self) -> int:
        """Reload pending jobs from disk and resume draining. Returns how many.

        Called once at application startup, never at import: importing
        this module must not spawn a thread or read a directory, or every
        test that touches the server would do both.
        """
        if self._store is None:
            return 0
        state = self._store.load_state()
        if not state:
            return 0
        restored = 0
        with self._condition:
            self._paused = bool(state.get("paused", False))
            for entry in state.get("jobs", []):
                run_id = entry.get("run_id")
                if not run_id or run_id in self._jobs:
                    continue
                was = entry.get("status")
                stop = entry.get("stop_requested")
                job = Job(
                    run_id=run_id,
                    request=entry.get("request") or {},
                    name=entry.get("name"),
                    submitted_at=float(entry.get("submitted_at") or time.time()),
                    paused_by_queue=bool(entry.get("paused_by_queue", False)),
                )
                if stop == "cancel":
                    # Asked to cancel and never got the chance: honour it.
                    self._store.discard(run_id)
                    continue
                if was == "paused" or stop == "pause":
                    job.status = "paused"
                    job.message = "paused"
                elif was == "running":
                    job.status = "queued"
                    job.message = "interrupted by a server restart -- will resume"
                else:
                    job.status = "queued"
                self._jobs[run_id] = job
                self._order.append(run_id)
                restored += 1
            # state.json is in EXECUTION order, but _jobs promises submission
            # order (all() is "newest first"). After a reorder the two differ,
            # so re-insert by submission time rather than inheriting the order.
            self._jobs = dict(sorted(self._jobs.items(), key=lambda item: item[1].submitted_at))
            self._changed()
        self._ensure_worker()
        return restored

    # ---------------------------------------------------------------
    # Controls
    # ---------------------------------------------------------------

    def pause(self, run_id: str) -> Job:
        with self._condition:
            job = self._require(run_id)
            if job.status == "queued":
                job.status = "paused"
                job.message = "paused"
                job.paused_by_queue = False
            elif job.status == "running":
                if job.stop_requested == "cancel":
                    raise QueueError("This run is already being cancelled.")
                job.stop_requested = "pause"
                job.message = "pausing after the configurations in flight finish"
            elif job.status == "paused":
                job.paused_by_queue = False
            else:
                raise QueueError(f"A {job.status} run cannot be paused.")
            self._changed(job)
            return job

    def resume(self, run_id: str) -> Job:
        with self._condition:
            job = self._require(run_id)
            if job.status == "paused":
                job.status = "queued"
                job.message = "queued -- will resume"
                job.paused_by_queue = False
            elif job.status == "running" and job.stop_requested == "pause":
                # Changed its mind before the pause landed.
                job.stop_requested = None
                job.message = "running"
            elif job.status in ("queued", "running"):
                pass
            else:
                raise QueueError(f"A {job.status} run cannot be resumed.")
            self._changed(job)
            return job

    def cancel(self, run_id: str) -> Job:
        with self._condition:
            job = self._require(run_id)
            if job.status in PENDING:
                job.status = "cancelled"
                job.message = "cancelled"
                job.stop_requested = None
                self._order.remove(run_id)
                if self._store is not None:
                    self._store.discard(run_id)
            elif job.status == "running":
                job.stop_requested = "cancel"
                job.message = "cancelling after the configurations in flight finish"
            else:
                raise QueueError(f"A {job.status} run cannot be cancelled.")
            self._changed(job)
            return job

    def move(self, run_id: str, position: int) -> Job:
        """Place a pending job at `position` (0 = next) among pending jobs.

        The running job is not part of the pending order and cannot be
        displaced: it already holds the worker, and moving something ahead
        of it would change nothing until it finished anyway.
        """
        with self._condition:
            job = self._require(run_id)
            if job.status not in PENDING:
                raise QueueError(
                    f"Only queued or paused runs can be moved, not a {job.status} one."
                )
            running = [rid for rid in self._order if self._jobs[rid].status == "running"]
            waiting = [rid for rid in self._order if rid != run_id and rid not in running]
            position = max(0, min(int(position), len(waiting)))
            waiting.insert(position, run_id)
            self._order = running + waiting
            self._changed(job)
            return job

    def run_next(self, run_id: str) -> Job:
        """Move to the front of the pending order, resuming it if paused.

        "Run this next" means run it: leaving it paused at the front would
        make the worker skip straight past the job just promoted.
        """
        with self._condition:
            job = self._require(run_id)
            if job.status == "paused":
                job.status = "queued"
                job.message = "queued -- next up"
                job.paused_by_queue = False
            self.move(run_id, 0)
            return job

    def pause_all(self) -> None:
        """Stop dispatching. The running job pauses after its batch."""
        with self._condition:
            self._paused = True
            for run_id in self._order:
                job = self._jobs[run_id]
                if job.status == "running" and job.stop_requested is None:
                    job.stop_requested = "pause"
                    job.paused_by_queue = True
                    job.message = "pausing -- the queue was paused"
            self._changed()

    def resume_all(self) -> None:
        """Start dispatching again, and un-pause what pause_all paused."""
        with self._condition:
            self._paused = False
            for run_id in self._order:
                job = self._jobs[run_id]
                if job.status == "paused" and job.paused_by_queue:
                    job.status = "queued"
                    job.message = "queued -- will resume"
                    job.paused_by_queue = False
                elif job.status == "running" and job.paused_by_queue:
                    job.stop_requested = None
                    job.paused_by_queue = False
                    job.message = "running"
            self._changed()
        self._ensure_worker()

    # ---------------------------------------------------------------
    # Internals
    # ---------------------------------------------------------------

    def _require(self, run_id: str) -> Job:
        job = self._jobs.get(run_id)
        if job is None:
            raise UnknownRun(run_id)
        return job

    def _changed(self, *touched: Job) -> None:
        """Recompute positions, bump revisions, persist, wake waiters.

        Caller holds the lock. Every job whose position moved gets a new
        revision as well as the ones named, so a websocket watching a job
        that was pushed back a place hears about it.
        """
        bumped = {job.run_id for job in touched}
        position = 0
        for run_id in self._order:
            job = self._jobs[run_id]
            new = None
            if job.status in PENDING:
                position += 1
                new = position
            if job.queue_position != new:
                job.queue_position = new
                bumped.add(run_id)
        for run_id in bumped:
            self._jobs[run_id].revision += 1
        self._persist()
        self._condition.notify_all()

    def _persist(self) -> None:
        if self._store is None:
            return
        self._store.save_state(
            {
                "version": 1,
                "paused": self._paused,
                "jobs": [
                    {
                        "run_id": job.run_id,
                        "name": job.name,
                        "request": job.request,
                        "status": job.status,
                        "submitted_at": job.submitted_at,
                        "stop_requested": job.stop_requested,
                        "paused_by_queue": job.paused_by_queue,
                    }
                    for job in (self._jobs[run_id] for run_id in self._order)
                ],
            }
        )

    def _update(self, job: Job, **fields: Any) -> None:
        """A progress tick: observable, not persisted -- one per configuration."""
        with self._condition:
            for key, value in fields.items():
                setattr(job, key, value)
            job.revision += 1
            self._condition.notify_all()

    def _next_runnable(self) -> Job | None:
        if self._paused:
            return None
        for run_id in self._order:
            job = self._jobs[run_id]
            if job.status == "queued":
                return job
        return None

    def _ensure_worker(self) -> None:
        """Start the worker lazily, on first submission or restore.

        Not at import: importing this module must not spawn a thread,
        or every test that touches the server would leak one.
        """
        if self._worker is None or not self._worker.is_alive():
            self._worker = threading.Thread(target=self._drain, name="backtest-worker", daemon=True)
            self._worker.start()

    def _finish(self, job: Job, **fields: Any) -> None:
        """File a job as terminal: out of the order, checkpoint discarded."""
        with self._condition:
            for key, value in fields.items():
                setattr(job, key, value)
            job.stop_requested = None
            if job.run_id in self._order:
                self._order.remove(job.run_id)
            if self._store is not None:
                self._store.discard(job.run_id)
            self._changed(job)

    def _drain(self) -> None:
        while True:
            with self._condition:
                self._condition.wait_for(lambda: self._next_runnable() is not None)
                job = self._next_runnable()
                assert job is not None
                # Running jobs lead the order, so a restart files it first.
                self._order.remove(job.run_id)
                self._order.insert(0, job.run_id)
                job.status = "running"
                job.progress = 0.0
                job.message = "starting"
                job.error = None
                self._changed(job)

            rows = self._store.load_rows(job.run_id) if self._store is not None else {}
            control = RunControl(self, job, rows)

            def report(fraction: float, note: str, _job: Job = job) -> None:
                self._update(_job, progress=fraction, message=note)

            try:
                result = self._runner(job.request, report, control)
            except RunStopped:
                with self._condition:
                    asked = job.stop_requested
                    job.stop_requested = None
                    if asked == "pause":
                        job.status = "paused"
                        job.message = (
                            "paused -- the queue is paused" if job.paused_by_queue else "paused"
                        )
                        self._changed(job)
                        continue
                    if asked is None:
                        # Paused, then resumed after the engine had already
                        # stopped taking new configurations. It is still at
                        # the front, so requeueing resumes it at once from
                        # its checkpoint rather than parking it as paused
                        # against what was last asked.
                        job.status = "queued"
                        job.message = "resuming"
                        self._changed(job)
                        continue
                self._finish(job, status="cancelled", message="cancelled")
            except Exception as exc:
                # The traceback goes to the server log; the client gets
                # the exception's own message. A stack trace in a browser
                # is neither useful nor safe to show.
                traceback.print_exc()
                self._finish(
                    job,
                    status="failed",
                    error=f"{type(exc).__name__}: {exc}",
                    message="failed",
                )
            else:
                self._finish(
                    job, status="complete", progress=1.0, message="complete", result=result
                )
                # ARCHIVED AFTER the job is marked complete, never
                # before: a websocket watcher is woken by that update,
                # and making it wait on a disk write would add latency
                # to the thing someone is actually watching.
                if self._on_complete is not None:
                    self._on_complete(job)


__all__ = [
    "PENDING",
    "TERMINAL",
    "Job",
    "JobQueue",
    "QueueError",
    "QueueStore",
    "RunControl",
    "RunStatus",
    "RunStopped",
    "UnknownRun",
    "directory",
]
