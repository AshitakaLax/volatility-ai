/**
 * Where a pending job sits, what order to show jobs in, and which queue
 * controls each one allows.
 *
 * Pure, like lib/sweepSummary.ts and lib/requestSummary.ts. Covered in
 * runQueue.test.ts.
 */
import type { BacktestRunState, RunStatus } from "@/types/backtest";

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

/** Not finished: running, or holding a place in the queue. */
export function isActive(status: RunStatus): boolean {
  return status === "running" || isPending(status);
}

/**
 * Every PENDING job's position, keyed by run_id.
 *
 * THE SERVER'S queue_position WINS WHENEVER IT IS PRESENT. Runs can now be
 * reordered and moved to the front, so submission order stopped being
 * execution order -- deriving position client-side from it would show the
 * wrong "next up" the moment anyone used those controls.
 *
 * The fallback below is only for a server that predates queue controls.
 * There JobQueue was a strict single-worker FIFO, so reversing GET /runs's
 * newest-first list recovers true order. It does NOT sort by run_id: that
 * is a random uuid4 hex, not a timestamp.
 */
export function queuePositions(runsNewestFirst: BacktestRunState[]): Map<string, QueuePosition> {
  const pending = runsNewestFirst.filter((run) => isPending(run.status));
  const positions = new Map<string, QueuePosition>();
  const serverKnows =
    pending.length > 0 && pending.every((run) => typeof run.queue_position === "number");

  if (serverKnows) {
    for (const run of pending) {
      positions.set(run.run_id, { position: run.queue_position as number, of: pending.length });
    }
    return positions;
  }

  [...pending].reverse().forEach((run, index) => {
    positions.set(run.run_id, { position: index + 1, of: pending.length });
  });
  return positions;
}

/**
 * Active jobs in the order they will run: the running one first, then
 * pending jobs by queue position. Terminal jobs are excluded.
 */
export function orderActiveRuns(runsNewestFirst: BacktestRunState[]): BacktestRunState[] {
  const positions = queuePositions(runsNewestFirst);
  const running = runsNewestFirst.filter((run) => run.status === "running");
  const pending = runsNewestFirst
    .filter((run) => isPending(run.status))
    .sort(
      (a, b) =>
        (positions.get(a.run_id)?.position ?? Number.MAX_SAFE_INTEGER) -
        (positions.get(b.run_id)?.position ?? Number.MAX_SAFE_INTEGER),
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
 * A RUNNING job's pause/cancel is a request that lands after its in-flight
 * configurations finish; while one is pending, the same control is not
 * offered twice, and a pending pause can still be taken back with resume.
 */
export function availableActions(
  run: BacktestRunState,
  position: QueuePosition | undefined,
): RunActions {
  if (run.status === "running") {
    const stop = run.stop_requested ?? null;
    return {
      ...NONE,
      pause: stop === null,
      resume: stop === "pause",
      cancel: stop !== "cancel",
    };
  }
  if (isPending(run.status)) {
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
  return NONE;
}

/**
 * The server's `position` for a one-place move, which is 0-based among
 * pending jobs with the moved job taken out first -- so "up one" from
 * 1-indexed place p is index p-2, and "down one" is index p.
 */
export function moveTarget(position: QueuePosition, direction: "up" | "down"): number {
  return direction === "up" ? Math.max(0, position.position - 2) : position.position;
}
