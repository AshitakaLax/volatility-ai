import { describe, expect, it } from "vitest";

import type { Run } from "@/types/backtest";

import {
  batchCounts,
  batchProgress,
  groupByBatch,
  isBatch,
  itemIsActive,
  orderActiveItems,
} from "./runBatches";
import { queuePositions } from "./runQueue";

let n = 0;

function run(over: Partial<Run> = {}, req: Partial<Run["req"]> = {}): Run {
  n += 1;
  return {
    id: `r${n}`,
    status: "queued",
    progress: 0,
    pos: null,
    shard: null,
    msg: null,
    error: null,
    req: {
      tickers: ["TQQQ"],
      grid_steps: [0.01],
      targets: [0.005],
      ...req,
    },
    report: null,
    ...over,
  };
}

describe("groupByBatch", () => {
  it("leaves unbatched runs alone", () => {
    const runs = [run(), run()];
    expect(groupByBatch(runs)).toEqual(runs);
  });

  it("groups chunks sharing a batch_id, ordered by batch_index", () => {
    const a = run({ id: "a" }, { batch_id: "b1", batch_index: 2, batch_total: 2 });
    const b = run({ id: "b" }, { batch_id: "b1", batch_index: 1, batch_total: 2 });
    const grouped = groupByBatch([a, b]);
    expect(grouped).toHaveLength(1);
    expect(isBatch(grouped[0]!)).toBe(true);
    if (isBatch(grouped[0]!)) {
      expect(grouped[0]!.batchId).toBe("b1");
      expect(grouped[0]!.runs.map((r) => r.id)).toEqual(["b", "a"]);
    }
  });

  it("keeps a lone batch_id holder as a plain run", () => {
    const runs = [run({}, { batch_id: "solo", batch_index: 1, batch_total: 1 })];
    const grouped = groupByBatch(runs);
    expect(grouped).toHaveLength(1);
    expect(isBatch(grouped[0]!)).toBe(false);
  });
});

describe("itemIsActive / orderActiveItems", () => {
  it("a batch is active while any chunk is", () => {
    const done = run({ status: "complete" }, { batch_id: "b1", batch_index: 1, batch_total: 2 });
    const running = run({ status: "running" }, { batch_id: "b1", batch_index: 2, batch_total: 2 });
    const [batch] = groupByBatch([done, running]);
    expect(itemIsActive(batch!)).toBe(true);
    expect(itemIsActive(done)).toBe(false);
  });

  it("orders running items before pending ones", () => {
    const queued = run({ status: "queued", pos: 1 });
    const active = run({ status: "running" });
    const ordered = orderActiveItems(groupByBatch([queued, active]), queuePositions([queued, active]));
    expect(ordered.map((item) => (isBatch(item) ? "batch" : item.id))).toEqual([active.id, queued.id]);
  });
});

describe("batchCounts / batchProgress", () => {
  it("counts by status and averages progress", () => {
    const batch = {
      batchId: "b1",
      runs: [
        run({ status: "running", progress: 0.5 }),
        run({ status: "queued", progress: 0 }),
        run({ status: "complete", progress: 1 }),
      ],
    };
    const counts = batchCounts(batch);
    expect(counts.running).toBe(1);
    expect(counts.queued).toBe(1);
    expect(counts.complete).toBe(1);
    expect(counts.failed).toBe(0);
    expect(batchProgress(batch)).toBeCloseTo(0.5);
  });
});
