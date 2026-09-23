/**
 * Grouping of bisected sweeps for the ActiveRuns list.
 *
 * A sweep too large for one submission is split server-side into
 * independent chunks sharing a batch_id (server/backtest.py
 * bisect_request); each chunk is queued as its own Run. The operator
 * submitted one sweep, so the list shows one card per batch with
 * rolled-up progress, expanding to the chunk rows on demand.
 *
 * Pure, like lib/runQueue.ts. Covered in runBatches.test.ts.
 */
import { isActive } from "@/lib/runQueue";
import type { QueuePosition } from "@/lib/runQueue";
import type { Run, RunStatus } from "@/types/backtest";

export interface RunBatch {
  batchId: string;
  runs: Run[];
}

export type BatchItem = Run | RunBatch;

/** Type guard: a batch carries runs, a run carries an id. */
export function isBatch(item: BatchItem): item is RunBatch {
  return (item as RunBatch).batchId !== undefined && Array.isArray((item as RunBatch).runs);
}

function batchIdOf(run: Run): string | null {
  return run.req.batch_id ?? null;
}

/**
 * Group runs sharing a batch_id, preserving first-seen order. A batch_id
 * held by a single run stays a plain Run -- one chunk renders as one
 * row, not as a one-child batch card. Chunk rows inside a batch follow
 * batch_index order.
 */
export function groupByBatch(runs: Run[]): BatchItem[] {
  const byId = new Map<string, Run[]>();
  for (const run of runs) {
    const id = batchIdOf(run);
    if (id === null) continue;
    if (!byId.has(id)) byId.set(id, []);
    byId.get(id)!.push(run);
  }
  const batched = new Set<string>();
  for (const [id, members] of byId) {
    if (members.length > 1) {
      members.sort((a, b) => (a.req.batch_index ?? 0) - (b.req.batch_index ?? 0));
      batched.add(id);
    }
  }
  const out: BatchItem[] = [];
  const emitted = new Set<string>();
  for (const run of runs) {
    const id = batchIdOf(run);
    if (id !== null && batched.has(id)) {
      if (emitted.has(id)) continue;
      emitted.add(id);
      out.push({ batchId: id, runs: byId.get(id)! });
    } else {
      out.push(run);
    }
  }
  return out;
}

/** Active means still in flight: any member running or holding a place. */
export function itemIsActive(item: BatchItem): boolean {
  if (isBatch(item)) return item.runs.some((run) => isActive(run.status));
  return isActive(item.status);
}

function itemRank(item: BatchItem, positions: Map<string, QueuePosition>): number {
  const runs = isBatch(item) ? item.runs : [item];
  if (runs.some((run) => run.status === "running")) return -2;
  if (runs.some((run) => run.status === "pausing" || run.status === "cancelling")) return -1;
  let best = Number.MAX_SAFE_INTEGER;
  for (const run of runs) {
    const pos = positions.get(run.id)?.position;
    if (pos !== undefined && pos < best) best = pos;
  }
  return best;
}

/**
 * Active items in run order: running first, then pending by queue
 * position. Terminal items are excluded -- the caller renders those
 * from the ungrouped pass as "recent".
 */
export function orderActiveItems(
  grouped: BatchItem[],
  positions: Map<string, QueuePosition>,
): BatchItem[] {
  return grouped
    .filter((item) => itemIsActive(item))
    .sort((a, b) => itemRank(a, positions) - itemRank(b, positions));
}

const ALL_STATUSES: RunStatus[] = [
  "queued",
  "running",
  "pausing",
  "cancelling",
  "paused",
  "cancelled",
  "complete",
  "failed",
];

/** Chunk counts by status; the card lists only the nonzero ones. */
export function batchCounts(batch: RunBatch): Record<RunStatus, number> {
  const counts = Object.fromEntries(ALL_STATUSES.map((status) => [status, 0])) as Record<
    RunStatus,
    number
  >;
  for (const run of batch.runs) counts[run.status] += 1;
  return counts;
}

/** Mean chunk progress, 0-1 -- the card's rolled-up bar. */
export function batchProgress(batch: RunBatch): number {
  if (batch.runs.length === 0) return 0;
  return batch.runs.reduce((sum, run) => sum + run.progress, 0) / batch.runs.length;
}
