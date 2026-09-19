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

This paragraph used to end "still not a real task queue: no second
worker, no retries, no distributed anything." The next section is why
that stopped being true; durability itself is still the narrow version,
for the same reason history.py is the narrow version of persistence.

--------------------------------------------------------------------
SHARDS: ONE SWEEP PER MACHINE, MANY MACHINES

A run (one sweep) is the unit of distribution. A SHARD is a process
that claims one queued run, runs every configuration of it on its own
cores, and reports each finished configuration back here -- where it is
checkpointed exactly as the local worker's rows are. That shared
checkpoint is what makes a run portable: whichever shard claims it next
resumes at configuration granularity, so reassigning a run costs only
the configurations that were in flight.

  local         This process's own worker is a shard too, named
                "local". A machine with no remote shards behaves exactly
                as before; pausing "local" frees this machine's cores
                while remote shards keep draining the queue.
  remote        `cli.py shard --name N --main HOST` (server/shard_client.py)
                speaks to server/shards.py over HTTP: register, claim,
                sync (heartbeat + progress + finished rows), finish.

Three rules keep two machines from ever writing the same run:

  ownership     every sync/finish names the run it is about, and is
                refused (NotOwner / owned=false) unless the queue still
                has that run assigned to that shard. A shard that loses
                ownership stops its run and discards what it had not yet
                delivered.
  timeout       a remote shard silent for SHARD_TIMEOUT_SECONDS is marked
                offline and its run is released to the front of the
                queue. If it comes back, its reports are refused by the
                rule above.
  supersede     registering a name that is already registered replaces
                the old process (and releases its run at once). The old
                process is told ShardSuperseded and exits, so two shards
                started with the same name cannot fight over it.

Pausing a SHARD is not pausing a RUN: the shard stops taking
configurations and its run goes back to the queue (not to "paused") so
another shard continues it. Pausing a run or the queue works as it
always has, on whichever shard the run happens to be.

--------------------------------------------------------------------
LOCKOUT WINDOWS: A SCHEDULE IS NOT A PAUSE

Each shard may also carry a daily lockout window (`set_shard_schedule`,
`_in_lockout`) -- wall-clock hours, server-local, during which it
behaves as if paused: no new claim, and a run in flight goes back to
the queue after its in-flight configurations, same as above. It is
kept as a SEPARATE fact from `Shard.paused` rather than implemented by
having a scheduler thread call pause_shard/resume_shard at the window's
edges, for one reason: that would require deciding, at the moment a
window closes, whether the shard was ALSO manually paused independently
of the schedule -- and un-pausing it either guesses wrong sometimes or
needs a second flag to remember which reason is which. A pure
time-of-day check has no such state to reconcile: every caller that
gates on `shard.paused` also checks `_in_lockout(shard.name)`, and the
two are true or false independently, always.

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
from datetime import datetime
from pathlib import Path
from typing import Any, Literal

from server import contract

logger = logging.getLogger("Optimizer")

RunStatus = Literal["queued", "running", "paused", "cancelled", "complete", "failed"]
StopRequest = Literal["pause", "cancel"]
ShardOutcome = Literal["complete", "failed", "stopped", "released"]

LOCAL_SHARD = "local"
# Letters, digits, dot, dash, underscore; it appears in URL paths and log
# lines, so nothing that needs escaping in either.
SHARD_NAME_PATTERN = r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,63}$"
# A remote shard syncs every couple of seconds. Silent this long, it is
# shown as not responding; silent SHARD_TIMEOUT_SECONDS, its run is
# released to the next free shard.
SHARD_STALE_SECONDS = 15.0
SHARD_TIMEOUT_SECONDS = 60.0

# Waiting for its turn (queued) or waiting to be allowed one (paused).
# Both hold a place in the order; both can be moved.
PENDING: frozenset[str] = frozenset({"queued", "paused"})
TERMINAL: frozenset[str] = frozenset({"cancelled", "complete", "failed"})

_ROOT = Path(__file__).resolve().parent.parent

_HHMM = "%H:%M"


def _parse_hhmm(value: str) -> datetime:
    """A bare time-of-day as a `datetime` on an arbitrary fixed date, so
    two of them can be compared with the usual operators. Raises
    ValueError for anything not exactly 24-hour HH:MM."""
    return datetime.strptime(value, _HHMM)


def _in_window(now: datetime, start: datetime, end: datetime) -> bool:
    """Whether `now`'s time-of-day falls in [start, end).

    `start > end` is a window that WRAPS PAST MIDNIGHT (e.g. 22:00 to
    06:00 -- an overnight lockout) rather than an empty or invalid one:
    it means "from start to end of day, and from start of day to end".
    """
    if start <= end:
        return start <= now < end
    return now >= start or now < end


class RunStopped(Exception):
    """Raised by a runner that stopped early because it was asked to."""


class QueueError(Exception):
    """A control action that does not apply to the job's current state."""


class UnknownRun(KeyError):
    """No job with that id is known to this queue."""


class UnknownShard(KeyError):
    """No shard registered under that name -- e.g. this server restarted."""


class ShardSuperseded(Exception):
    """A newer process registered under this shard's name."""


class NotOwner(Exception):
    """The run is not, or is no longer, assigned to the shard reporting on it."""


@dataclass
class Shard:
    """One machine working the queue. `last_seen` is on the queue's clock."""

    name: str
    instance: str
    registered_at: float
    last_seen: float
    local: bool = False
    host: str | None = None
    commit: str | None = None
    dirty: bool | None = None
    cores: int | None = None
    paused: bool = False
    # Set by reap(); cleared by the next message from the shard.
    offline: bool = False
    run_id: str | None = None


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
        self.append_rows(run_id, [(ticker, row)])

    def append_rows(self, run_id: str, rows: list[tuple[str, dict[str, Any]]]) -> None:
        if not rows:
            return
        lines = "".join(
            json.dumps({"ticker": ticker, "row": row}, default=_json_default) + "\n"
            for ticker, row in rows
        )
        with self._lock:
            try:
                target = self._root()
                target.mkdir(parents=True, exist_ok=True)
                with (target / f"{run_id}.rows.jsonl").open("a", encoding="utf-8") as handle:
                    handle.write(lines)
            except OSError as exc:
                logger.warning(f"Could not checkpoint {len(rows)} row(s) for {run_id}: {exc}")

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
    # The shard running it; None unless running. Not persisted: a run
    # that was running when this process died comes back queued.
    shard: str | None = None

    def snapshot(self) -> dict[str, Any]:
        """The job as a wire `Run` (web/src/types/backtest.ts)."""
        return {
            "id": self.run_id,
            # A pending stop on a running job is reported AS its status
            # (pausing / cancelling) rather than as a second field.
            "status": contract.status(self.status, self.stop_requested),
            "progress": round(self.progress, 4),
            "pos": self.queue_position,
            "shard": self.shard,
            "msg": self.message,
            "error": self.error,
            "rev": self.revision,
            "submitted_at": self.submitted_at,
            # The submitted request, echoed back verbatim -- exactly what
            # was POSTed, nothing new exposed. Lets a client describe a
            # QUEUED or RUNNING job (tickers, grid, strategy params, name)
            # before it has a report to read that from.
            "req": self.request,
            "report": self.result,
        }


class RunControl:
    """What a runner may ask of the queue while it works."""

    def __init__(self, queue: JobQueue, job: Job, rows: dict[str, list[dict[str, Any]]]):
        self._queue = queue
        self._job = job
        self._rows = rows

    def should_stop(self) -> bool:
        """True once a pause or cancel has been asked of this run, or the
        shard running it has been paused."""
        return self._queue._should_stop(self._job)

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
        clock: Callable[[], float] = time.monotonic,
        wall_clock: Callable[[], datetime] = datetime.now,
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
        # An RLock underneath (Condition's default), which the shard paths
        # rely on: _release and _settle_stopped call _finish/_changed while
        # already holding it.
        self._condition = threading.Condition()
        self._worker: threading.Thread | None = None
        # Injected so shard timeouts are tested without sleeping. This is
        # a DURATION clock (monotonic by default) -- never wall-clock
        # time, and never used to decide what time of day it is.
        self._clock = clock
        # Separate from the one above: lockout windows ("7:00-19:00") are
        # a time-OF-DAY question, which a monotonic clock cannot answer.
        # Injected the same way, for the same reason -- a test sets a
        # fixed datetime rather than sleeping until a real window opens.
        self._wall_clock = wall_clock
        # Shard name -> {"enabled", "start", "end"} ("HH:MM" strings).
        # Keyed by NAME, not held on the Shard object: a window must
        # survive that shard's own process restarting (Shard instances
        # are recreated on every register_shard call) and must be
        # settable before a shard has ever registered.
        self._schedules: dict[str, dict[str, Any]] = {}
        now = clock()
        self._shards: dict[str, Shard] = {
            LOCAL_SHARD: Shard(
                name=LOCAL_SHARD,
                instance=LOCAL_SHARD,
                registered_at=time.time(),
                last_seen=now,
                local=True,
                cores=os.cpu_count(),
            )
        }
        # Pauses of remote shards that are not registered right now (this
        # process restarted), applied when they register again.
        self._paused_names: set[str] = set()

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
            paused_shards = {str(name) for name in state.get("paused_shards", [])}
            self._shards[LOCAL_SHARD].paused = LOCAL_SHARD in paused_shards
            self._paused_names = paused_shards - {LOCAL_SHARD}
            self._schedules = {
                str(name): schedule
                for name, schedule in state.get("schedules", {}).items()
                if isinstance(schedule, dict)
            }
            for entry in state.get("jobs", []):
                run_id = entry.get("run_id")
                if not run_id or run_id in self._jobs:
                    continue
                was = entry.get("status")
                stop = entry.get("stop_requested")
                job = Job(
                    run_id=run_id,
                    # A state.json written before the contract was condensed
                    # holds the old field names; translated once, here, and
                    # persisted in the new shape by the _changed() below.
                    request=contract.request(entry.get("request") or {}),
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
    # Shards: reading and operator controls
    # ---------------------------------------------------------------

    def shards(self) -> list[dict[str, Any]]:
        """Every known shard as a wire `Shard` (web/src/types/backtest.ts),
        the local one first."""
        with self._condition:
            now = self._clock()
            ordered = sorted(self._shards.values(), key=lambda s: (not s.local, s.name.lower()))
            return [self._shard_snapshot(shard, now) for shard in ordered]

    def shard(self, name: str) -> dict[str, Any]:
        with self._condition:
            return self._shard_snapshot(self._shard(name), self._clock())

    def pause_shard(self, name: str) -> dict[str, Any]:
        """Stop the shard taking work. Its run, if any, stops after the
        configurations in flight and goes back to the queue."""
        with self._condition:
            shard = self._shard(name)
            shard.paused = True
            self._changed()
            return self._shard_snapshot(shard, self._clock())

    def resume_shard(self, name: str) -> dict[str, Any]:
        with self._condition:
            shard = self._shard(name)
            shard.paused = False
            self._paused_names.discard(name)
            self._changed()
            snapshot = self._shard_snapshot(shard, self._clock())
        if shard.local:
            self._ensure_worker()
        return snapshot

    def shard_schedule(self, name: str) -> dict[str, Any] | None:
        with self._condition:
            schedule = self._schedules.get(name)
            return dict(schedule) if schedule else None

    def set_shard_schedule(
        self, name: str, enabled: bool, start: str | None, end: str | None
    ) -> dict[str, Any] | None:
        """Configure, change, or clear a shard's daily lockout window --
        wall-clock hours, server-local, outside of which it behaves
        exactly as it always has. Inside them it claims no new work and,
        if already running one, hands it back after the configurations in
        flight -- the same effect as a manual pause (see `_in_lockout`),
        arrived at automatically rather than by a person clicking Pause
        at 7 and Resume at 19 every day.

        NOT gated on the name being a currently-registered shard, unlike
        pause_shard/resume_shard/forget_shard -- deliberately, so a
        window survives that shard's own process being restarted (its
        Shard object is torn down and recreated by register_shard) and
        can be set before it has ever registered at all. The UI only
        ever calls this for a name it is already showing, so this is
        permissiveness with no real caller who could misuse it.

        `enabled=False` with no start/end CLEARS the window entirely
        rather than merely disabling it, since the UI's clear action and
        its "turn it off but remember the times" toggle are the same
        request shape otherwise indistinguishable at this layer -- a
        caller wanting the second one passes the times back with
        enabled=False.
        """
        with self._condition:
            if enabled:
                if not start or not end:
                    raise QueueError("A lockout window needs both a start and an end time.")
                for field_name, value in (("start", start), ("end", end)):
                    try:
                        _parse_hhmm(value)
                    except ValueError as exc:
                        raise QueueError(
                            f"{field_name} must be a 24-hour HH:MM time, got {value!r}."
                        ) from exc
            if not enabled and not start and not end:
                self._schedules.pop(name, None)
                schedule = None
            else:
                schedule = {"enabled": enabled, "start": start, "end": end}
                self._schedules[name] = schedule
            self._changed()
            still_locked = self._in_lockout(name)
        if name == LOCAL_SHARD and not still_locked:
            self._ensure_worker()
        return schedule

    def set_shards_paused(self, paused: bool) -> None:
        """Pause or resume every shard, including the local one."""
        with self._condition:
            for shard in self._shards.values():
                shard.paused = paused
            if not paused:
                self._paused_names.clear()
            self._changed()
        if not paused:
            self._ensure_worker()

    def forget_shard(self, name: str) -> None:
        """Drop an offline shard from the list. A connected one would just
        register again, so forgetting it is refused rather than pointless."""
        with self._condition:
            shard = self._shard(name)
            if shard.local:
                raise QueueError("The local shard is this server; it cannot be removed.")
            if self._connection(shard, self._clock()) != "offline":
                raise QueueError(f"Shard {name} is still connected; stop its process first.")
            del self._shards[name]
            self._paused_names.discard(name)
            self._changed()

    def reap(self) -> list[str]:
        """Mark silent remote shards offline and release their runs.

        Returns the released run ids. Called periodically by
        server/shards.py; cheap enough to call on every listing too.
        """
        released: list[str] = []
        with self._condition:
            now = self._clock()
            changed = False
            for shard in self._shards.values():
                if shard.local or shard.offline:
                    continue
                if now - shard.last_seen < SHARD_TIMEOUT_SECONDS:
                    continue
                shard.offline = True
                changed = True
                if shard.run_id is not None:
                    released.append(shard.run_id)
                    self._release(
                        shard.run_id, f"shard {shard.name} stopped responding -- will resume"
                    )
            if changed:
                self._changed()
        return released

    # ---------------------------------------------------------------
    # Shards: the protocol a remote shard speaks (server/shards.py)
    # ---------------------------------------------------------------

    def register_shard(
        self,
        name: str,
        instance: str,
        *,
        host: str | None = None,
        commit: str | None = None,
        dirty: bool | None = None,
        cores: int | None = None,
    ) -> dict[str, Any]:
        """Register (or re-register) a remote shard. Last registration wins.

        A pause survives re-registration: an operator who paused a
        machine does not want a restart of its process to quietly
        un-pause it.
        """
        if name == LOCAL_SHARD:
            raise QueueError(f"{LOCAL_SHARD!r} is this server's own worker; pick another name.")
        with self._condition:
            existing = self._shards.get(name)
            keep_run: str | None = None
            if existing is not None and existing.run_id is not None:
                if existing.instance == instance:
                    # The same process retrying a registration whose
                    # answer it never saw: nothing about its run changed.
                    keep_run = existing.run_id
                else:
                    self._release(existing.run_id, f"shard {name} restarted -- will resume")
            paused = existing.paused if existing is not None else name in self._paused_names
            self._paused_names.discard(name)
            shard = Shard(
                name=name,
                instance=instance,
                registered_at=time.time(),
                last_seen=self._clock(),
                host=host,
                commit=commit,
                dirty=dirty,
                cores=cores,
                paused=paused,
                run_id=keep_run,
            )
            self._shards[name] = shard
            self._changed()
            return self._shard_snapshot(shard, self._clock())

    def claim(self, name: str, instance: str, wait: float = 0.0) -> tuple[Job, dict] | None:
        """Hand the next queued run to a remote shard, waiting up to `wait`
        seconds for one. Returns (job, checkpointed rows by ticker) or None.
        """
        with self._condition:
            shard = self._remote_shard(name, instance)
            self._touch(shard)
            if shard.run_id is not None:
                # Asking for work means it is not running what we think it
                # is -- a claim whose answer was lost, most likely.
                self._release(shard.run_id, f"shard {name} dropped it -- will resume")

            def ready() -> bool:
                current = self._shards.get(name)
                if current is None or current.instance != instance:
                    return True
                return (
                    not current.paused
                    and not self._in_lockout(name)
                    and self._next_runnable() is not None
                )

            self._condition.wait_for(ready, timeout=wait)
            shard = self._remote_shard(name, instance)
            self._touch(shard)
            job = None if (shard.paused or self._in_lockout(name)) else self._next_runnable()
            if job is None:
                return None
            self._start(job, shard)
        rows = self._store.load_rows(job.run_id) if self._store is not None else {}
        return job, rows

    def shard_sync(
        self,
        name: str,
        instance: str,
        run_id: str | None,
        *,
        progress: float | None = None,
        message: str | None = None,
        rows: list[tuple[str, dict[str, Any]]] | None = None,
    ) -> dict[str, Any]:
        """Heartbeat, progress, and finished configurations, in one call.

        Rows are checkpointed only while the shard still owns the run --
        under the lock, so a release cannot slip between the ownership
        check and the append and leave a row in a checkpoint another
        shard has already read.
        """
        with self._condition:
            shard = self._remote_shard(name, instance)
            self._touch(shard)
            job = self._jobs.get(run_id) if run_id is not None else None
            owned = job is not None and self._owns(shard, job)
            stop = False
            if owned:
                assert job is not None
                if rows and self._store is not None:
                    self._store.append_rows(job.run_id, rows)
                if progress is not None:
                    self._update(
                        job,
                        progress=progress,
                        message=message if message is not None else job.message,
                    )
                stop = self._should_stop(job)
            return {
                "paused": shard.paused,
                "locked_out": self._in_lockout(shard.name),
                "owned": owned,
                "stop": stop,
            }

    def shard_finish(
        self,
        name: str,
        instance: str,
        run_id: str,
        outcome: ShardOutcome,
        *,
        result: dict[str, Any] | None = None,
        error: str | None = None,
    ) -> None:
        """A remote shard is done with a run, one way or another.

        complete   the report; archived like a local completion.
        failed     the run itself failed -- terminal, as it would be here.
        stopped    it honoured a stop (run pause/cancel, or shard pause).
        released   the shard gave it back for its own reasons (shutting
                   down, lost the main server mid-run): back to the queue.
        """
        with self._condition:
            shard = self._remote_shard(name, instance)
            self._touch(shard)
            job = self._jobs.get(run_id)
            if job is None or not self._owns(shard, job):
                raise NotOwner(f"Run {run_id} is not assigned to shard {name}.")
            if outcome == "stopped":
                note = (
                    f"released by paused shard {name} -- will resume"
                    if shard.paused
                    else "resuming"
                )
                self._settle_stopped(job, note)
                return
            if outcome == "released":
                reason = f": {error}" if error else ""
                self._release(run_id, f"shard {name} gave it back{reason} -- will resume")
                return
            if outcome == "failed":
                self._finish(job, status="failed", error=error or "failed", message="failed")
                return
            self._finish(job, status="complete", progress=1.0, message="complete", result=result)
        if self._on_complete is not None:
            self._on_complete(job)

    # ---------------------------------------------------------------
    # Internals
    # ---------------------------------------------------------------

    def _shard(self, name: str) -> Shard:
        shard = self._shards.get(name)
        if shard is None:
            raise UnknownShard(name)
        return shard

    def _remote_shard(self, name: str, instance: str) -> Shard:
        """The registered remote shard, or why this caller is not it."""
        shard = self._shards.get(name)
        if shard is None or shard.local:
            raise UnknownShard(name)
        if shard.instance != instance:
            raise ShardSuperseded(f"Another process registered as shard {name}.")
        return shard

    def _touch(self, shard: Shard) -> None:
        shard.last_seen = self._clock()
        # Back from offline: its old run was already released, and its
        # reports about that run are refused by _owns.
        shard.offline = False

    @staticmethod
    def _owns(shard: Shard, job: Job) -> bool:
        return job.status == "running" and job.shard == shard.name and shard.run_id == job.run_id

    def _in_lockout(self, name: str) -> bool:
        """Whether `name`'s configured lockout window covers this instant.

        Deliberately independent of `Shard.paused`: a schedule and a
        manual pause are two different reasons a shard takes no work, and
        keeping them as separate never-stored-together facts means
        resuming from one never has to guess whether it should also
        clear the other. Callers that need "will this shard do anything
        right now" check both.
        """
        schedule = self._schedules.get(name)
        if not schedule or not schedule.get("enabled"):
            return False
        try:
            start = _parse_hhmm(schedule["start"])
            end = _parse_hhmm(schedule["end"])
        except (KeyError, TypeError, ValueError):
            return False
        return _in_window(_parse_hhmm(self._wall_clock().strftime(_HHMM)), start, end)

    def _should_stop(self, job: Job) -> bool:
        with self._condition:
            if job.stop_requested is not None:
                return True
            shard = self._shards.get(job.shard) if job.shard is not None else None
            return shard is not None and (shard.paused or self._in_lockout(shard.name))

    def _connection(self, shard: Shard, now: float) -> str:
        if shard.local:
            return "online"
        age = now - shard.last_seen
        if shard.offline or age >= SHARD_TIMEOUT_SECONDS:
            return "offline"
        return "stale" if age >= SHARD_STALE_SECONDS else "online"

    def _shard_snapshot(self, shard: Shard, now: float) -> dict[str, Any]:
        job = self._jobs.get(shard.run_id) if shard.run_id is not None else None
        locked_out = self._in_lockout(shard.name)
        if job is not None:
            state = "pausing" if (shard.paused or locked_out) else "running"
        elif shard.paused:
            state = "paused"
        elif locked_out:
            state = "locked_out"
        else:
            state = "idle"
        return {
            "name": shard.name,
            "local": shard.local,
            "conn": self._connection(shard, now),
            "state": state,
            "host": shard.host,
            "commit": shard.commit,
            "dirty": shard.dirty,
            "cores": shard.cores,
            "seen_s": 0.0 if shard.local else round(max(0.0, now - shard.last_seen), 1),
            "since": shard.registered_at,
            "paused": shard.paused,
            "locked_out": locked_out,
            "schedule": self._schedules.get(shard.name),
            "run": (
                {
                    "id": job.run_id,
                    "name": job.name,
                    "progress": round(job.progress, 4),
                    "msg": job.message,
                }
                if job is not None
                else None
            ),
        }

    def _start(self, job: Job, shard: Shard) -> None:
        """Hand `job` to `shard`. Caller holds the lock."""
        # Running jobs lead the order, so a restart files it first.
        self._order.remove(job.run_id)
        self._order.insert(0, job.run_id)
        job.status = "running"
        job.progress = 0.0
        job.message = "starting" if shard.local else f"starting on {shard.name}"
        job.error = None
        job.shard = shard.name
        shard.run_id = job.run_id
        self._changed(job)

    def _detach(self, job: Job) -> None:
        """Unlink a job from its shard. Caller holds the lock."""
        if job.shard is not None:
            shard = self._shards.get(job.shard)
            if shard is not None and shard.run_id == job.run_id:
                shard.run_id = None
        job.shard = None

    def _release(self, run_id: str, note: str) -> None:
        """Take a running job back from its shard. Caller holds the lock.

        It stays where running jobs sit -- ahead of everything pending --
        so it is the next thing any free shard claims. A stop that was
        asked of it before its shard went away is honoured here, since
        the shard never will.
        """
        job = self._jobs.get(run_id)
        if job is None or job.status != "running":
            return
        self._settle_stopped(job, note)

    def _settle_stopped(self, job: Job, note: str) -> None:
        """File a running job that stopped early, by what was asked of it."""
        with self._condition:
            self._detach(job)
            asked = job.stop_requested
            job.stop_requested = None
            if asked == "pause":
                job.status = "paused"
                job.message = "paused -- the queue is paused" if job.paused_by_queue else "paused"
                self._changed(job)
                return
            if asked is None:
                # Not asked to stop by anyone watching the RUN: a shard
                # paused or went away, or a pause was taken back after the
                # engine had already stopped. Requeued at the front, it
                # resumes from its checkpoint on the next free shard.
                job.status = "queued"
                job.message = note
                self._changed(job)
                return
        self._finish(job, status="cancelled", message="cancelled")

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
                "paused_shards": sorted(
                    self._paused_names
                    | {name for name, shard in self._shards.items() if shard.paused}
                ),
                "schedules": self._schedules,
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
            self._detach(job)
            if job.run_id in self._order:
                self._order.remove(job.run_id)
            if self._store is not None:
                self._store.discard(job.run_id)
            self._changed(job)

    def _local_ready(self) -> bool:
        return (
            not self._shards[LOCAL_SHARD].paused
            and not self._in_lockout(LOCAL_SHARD)
            and self._next_runnable() is not None
        )

    def _drain(self) -> None:
        """The local shard: this process's own worker."""
        local = self._shards[LOCAL_SHARD]
        while True:
            with self._condition:
                self._condition.wait_for(self._local_ready)
                job = self._next_runnable()
                assert job is not None
                self._start(job, local)

            rows = self._store.load_rows(job.run_id) if self._store is not None else {}
            control = RunControl(self, job, rows)

            def report(fraction: float, note: str, _job: Job = job) -> None:
                self._update(_job, progress=fraction, message=note)

            try:
                result = self._runner(job.request, report, control)
            except RunStopped:
                # Paused-then-resumed after the engine had already stopped
                # taking configurations requeues with "resuming", at the
                # front -- so this worker picks it straight back up from
                # its checkpoint unless the local shard itself was paused,
                # in which case the next free remote shard does.
                note = (
                    "released by the paused local shard -- will resume"
                    if local.paused
                    else "resuming"
                )
                self._settle_stopped(job, note)
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
    "LOCAL_SHARD",
    "PENDING",
    "SHARD_NAME_PATTERN",
    "SHARD_STALE_SECONDS",
    "SHARD_TIMEOUT_SECONDS",
    "TERMINAL",
    "Job",
    "JobQueue",
    "NotOwner",
    "QueueError",
    "QueueStore",
    "RunControl",
    "RunStatus",
    "RunStopped",
    "Shard",
    "ShardOutcome",
    "ShardSuperseded",
    "UnknownRun",
    "UnknownShard",
    "directory",
]
