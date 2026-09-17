/**
 * Where a pending job sits, what order to show jobs in, and which queue
 * controls each one allows.
 *
 * Pure, like lib/sweepSummary.ts and lib/requestSummary.ts. Covered in
 * runQueue.test.ts.
 */
import type { Run, RunStatus } from "@/types/backtest";

export interface QueuePosition {
  /** 1-indexed; 1 means "next up". */
  position: number;
  /** How many jobs are pending in total (including this one). */
  of: number;
}

/** Waiting for its turn, or waiting to be allowed one. Both hold a place. */
export function isPending(status: RunStatus): boolean {
  return status === "queued" || status === "paused";
}

/** Holding the worker: running, possibly with a stop on the way. */
export function isRunning(status: RunStatus): boolean {
  return status === "running" || status === "pausing" || status === "cancelling";
}

/** Not finished: running, or holding a place in the queue. */
export function isActive(status: RunStatus): boolean {
  return isRunning(status) || isPending(status);
}

/**
 * Every PENDING job's position, keyed by id -- the server's `pos`, which
 * is execution order. Submission order stopped being that the moment runs
 * could be reordered, so it is never derived client-side.
 */
export function queuePositions(runsNewestFirst: Run[]): Map<string, QueuePosition> {
  const pending = runsNewestFirst.filter((run) => isPending(run.status));
  const positions = new Map<string, QueuePosition>();
  for (const run of pending) {
    if (run.pos !== null) positions.set(run.id, { position: run.pos, of: pending.length });
  }
  return positions;
}

/**
 * Active jobs in the order they will run: the running one first, then
 * pending jobs by queue position. Terminal jobs are excluded.
 */
export function orderActiveRuns(runsNewestFirst: Run[]): Run[] {
  const positions = queuePositions(runsNewestFirst);
  const running = runsNewestFirst.filter((run) => isRunning(run.status));
  const pending = runsNewestFirst
    .filter((run) => isPending(run.status))
    .sort(
      (a, b) =>
        (positions.get(a.id)?.position ?? Number.MAX_SAFE_INTEGER) -
        (positions.get(b.id)?.position ?? Number.MAX_SAFE_INTEGER),
    );
  return [...running, ...pending];
}

export interface RunActions {
  pause: boolean;
  resume: boolean;
  cancel: boolean;
  /** Move to the front of the queue (resuming it, if paused). */
  runNext: boolean;
  moveUp: boolean;
  moveDown: boolean;
}

const NONE: RunActions = {
  pause: false,
  resume: false,
  cancel: false,
  runNext: false,
  moveUp: false,
  moveDown: false,
};

/**
 * Which controls make sense for a job right now -- mirrored from the
 * transitions server/jobs.py accepts, so the UI never offers an action
 * the server would answer with 409.
 *
 * A running job's pause/cancel is a request that lands after its
 * in-flight configurations finish ("pausing" / "cancelling"); the same
 * control is not offered twice, and a pending pause can still be taken
 * back with resume.
 */
export function availableActions(run: Run, position: QueuePosition | undefined): RunActions {
  switch (run.status) {
    case "running":
      return { ...NONE, pause: true, cancel: true };
    case "pausing":
      return { ...NONE, resume: true, cancel: true };
    case "cancelling":
      return NONE;
    case "queued":
    case "paused": {
      const place = position?.position ?? 1;
      const of = position?.of ?? 1;
      return {
        pause: run.status === "queued",
        resume: run.status === "paused",
        cancel: true,
        runNext: place > 1,
        moveUp: place > 1,
        moveDown: place < of,
      };
    }
    default:
      return NONE;
  }
}

/**
 * The server's `pos` for a one-place move, which is 0-based among pending
 * jobs with the moved job taken out first -- so "up one" from 1-indexed
 * place p is index p-2, and "down one" is index p.
 */
export function moveTarget(position: QueuePosition, direction: "up" | "down"): number {
  return direction === "up" ? Math.max(0, position.position - 2) : position.position;
}
