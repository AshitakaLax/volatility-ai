"""An in-process queue for backtest runs.

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
WHAT IS DELIBERATELY NOT HERE

No persistence. A server restart loses queued and running jobs, and that
is acceptable for a single-operator tool -- the alternative is a real
task queue, which is a dependency and an operational surface this
project does not need. It is stated rather than discovered: the ledger
records it as a known limitation.
"""

from __future__ import annotations

import queue
import threading
import traceback
import uuid
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, Literal

RunStatus = Literal["queued", "running", "complete", "failed"]


@dataclass
class Job:
    """One submitted run and everything observers need about it."""

    run_id: str
    request: dict[str, Any]
    status: RunStatus = "queued"
    progress: float = 0.0
    message: str | None = None
    result: dict[str, Any] | None = None
    error: str | None = None
    # Bumped on every mutation, so a poller can tell "nothing changed"
    # from "I missed an update" without diffing the whole payload.
    revision: int = 0

    def snapshot(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "status": self.status,
            "progress": round(self.progress, 4),
            "message": self.message,
            "report": self.result,
            "error": self.error,
            "revision": self.revision,
        }


class JobQueue:
    """Serial background execution with observable state.

    Every mutation happens under one lock and then notifies a Condition,
    so a waiter is woken by a real change rather than by a timer. That
    matters for the WebSocket: polling a status dict on a sleep loop
    would add latency to a job that already takes half a minute, and
    would burn a thread doing nothing while it waited.
    """

    def __init__(
        self,
        runner: Callable[[dict[str, Any], Callable[[float, str], None]], dict],
        on_complete: Callable[[Job], None] | None = None,
    ):
        self._runner = runner
        # Called once per completed job. Injected rather than imported
        # so the queue stays a queue: it knows nothing about where a
        # result is archived, and a test can watch completions without
        # touching a disk.
        self._on_complete = on_complete
        self._jobs: dict[str, Job] = {}
        self._pending: queue.Queue[str] = queue.Queue()
        self._condition = threading.Condition()
        self._worker: threading.Thread | None = None

    def _ensure_worker(self) -> None:
        """Start the worker lazily, on first submission.

        Not at import: importing this module must not spawn a thread,
        or every test that touches the server would leak one.
        """
        if self._worker is None or not self._worker.is_alive():
            self._worker = threading.Thread(target=self._drain, name="backtest-worker", daemon=True)
            self._worker.start()

    def submit(self, request: dict[str, Any]) -> Job:
        job = Job(run_id=uuid.uuid4().hex[:12], request=request)
        with self._condition:
            self._jobs[job.run_id] = job
            self._condition.notify_all()
        self._pending.put(job.run_id)
        self._ensure_worker()
        return job

    def get(self, run_id: str) -> Job | None:
        with self._condition:
            return self._jobs.get(run_id)

    def all(self) -> list[Job]:
        """Newest first. Insertion order is submission order."""
        with self._condition:
            return list(reversed(list(self._jobs.values())))

    def _update(self, job: Job, **fields: Any) -> None:
        with self._condition:
            for key, value in fields.items():
                setattr(job, key, value)
            job.revision += 1
            self._condition.notify_all()

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

    def _drain(self) -> None:
        while True:
            run_id = self._pending.get()
            job = self.get(run_id)
            if job is None:
                continue
            self._update(job, status="running", progress=0.0, message="starting")

            def report(fraction: float, note: str, _job: Job = job) -> None:
                self._update(_job, progress=fraction, message=note)

            try:
                result = self._runner(job.request, report)
            except Exception as exc:
                # The traceback goes to the server log; the client gets
                # the exception's own message. A stack trace in a browser
                # is neither useful nor safe to show.
                traceback.print_exc()
                self._update(
                    job,
                    status="failed",
                    error=f"{type(exc).__name__}: {exc}",
                    message="failed",
                )
            else:
                self._update(
                    job, status="complete", progress=1.0, message="complete", result=result
                )
                # ARCHIVED AFTER the job is marked complete, never
                # before: a websocket watcher is woken by that update,
                # and making it wait on a disk write would add latency
                # to the thing someone is actually watching.
                if self._on_complete is not None:
                    self._on_complete(job)


__all__ = ["Job", "JobQueue", "RunStatus"]
