/**
 * Where a queued job sits, relative to the others waiting.
 *
 * Pure, like lib/sweepSummary.ts and lib/requestSummary.ts. Covered in
 * runQueue.test.ts.
 */
import type { BacktestRunState } from "@/types/backtest";

export interface QueuePosition {
  /** 1-indexed; 1 means "next up". */
  position: number;
  /** How many jobs are queued in total (including this one). */
  of: number;
}

/**
 * Every currently-QUEUED job's position, keyed by run_id.
 *
 * Safe to compute purely client-side: server/jobs.py's JobQueue is a
 * SINGLE-WORKER FIFO (one thread drains one queue.Queue, one id at a
 * time), so at most one job is ever "running" and every other
 * non-terminal job is strictly "queued" in the order it was submitted --
 * there is no scheduling this could get wrong.
 *
 * `runsNewestFirst` is exactly what GET /api/backtest/runs returns
 * (JobQueue.all(): "Newest first. Insertion order is submission
 * order.") -- reversing it back recovers true submission order. This
 * does NOT sort by run_id: run_id is a random uuid4 hex, not a
 * timestamp, so sorting by it would silently scramble the queue.
 */
export function queuePositions(
  runsNewestFirst: BacktestRunState[],
): Map<string, QueuePosition> {
  const submissionOrder = [...runsNewestFirst].reverse();
  const queued = submissionOrder.filter((run) => run.status === "queued");

  const positions = new Map<string, QueuePosition>();
  queued.forEach((run, index) => {
    positions.set(run.run_id, { position: index + 1, of: queued.length });
  });
  return positions;
}
