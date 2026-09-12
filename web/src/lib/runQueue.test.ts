/**
 * Queue position is a stand-in for the server's own FIFO order, computed
 * purely from what GET /api/backtest/runs already returns. Each case
 * below is one where a wrong answer (sorting by run_id, trusting list
 * order without un-reversing it) looks fine on a small list and only
 * shows up once several jobs are actually queued.
 */
import { describe, expect, it } from "vitest";

import type { BacktestRunState } from "@/types/backtest";

import { queuePositions } from "./runQueue";

function run(over: Partial<BacktestRunState> = {}): BacktestRunState {
  return {
    run_id: "r1",
    status: "queued",
    progress: 0,
    message: null,
    report: null,
    error: null,
    ...over,
  };
}

describe("queuePositions", () => {
  it("a single queued job is next up, 1 of 1", () => {
    const positions = queuePositions([run({ run_id: "a" })]);
    expect(positions.get("a")).toEqual({ position: 1, of: 1 });
  });

  it("positions follow SUBMISSION order, not list order -- the input is newest-first", () => {
    // Submitted a, then b, then c (oldest to newest). GET /runs returns
    // newest-first: c, b, a.
    const positions = queuePositions([
      run({ run_id: "c" }),
      run({ run_id: "b" }),
      run({ run_id: "a" }),
    ]);
    expect(positions.get("a")).toEqual({ position: 1, of: 3 });
    expect(positions.get("b")).toEqual({ position: 2, of: 3 });
    expect(positions.get("c")).toEqual({ position: 3, of: 3 });
  });

  it("does not sort by run_id -- a lexicographically later id can still be next up", () => {
    // Submitted "zzz" first, then "aaa" -- newest-first input is [aaa, zzz].
    const positions = queuePositions([
      run({ run_id: "aaa" }),
      run({ run_id: "zzz" }),
    ]);
    expect(positions.get("zzz")).toEqual({ position: 1, of: 2 });
    expect(positions.get("aaa")).toEqual({ position: 2, of: 2 });
  });

  it("only queued jobs get a position -- running/complete/failed are excluded", () => {
    const positions = queuePositions([
      run({ run_id: "queued-2", status: "queued" }),
      run({ run_id: "failed-1", status: "failed" }),
      run({ run_id: "running-1", status: "running" }),
      run({ run_id: "queued-1", status: "queued" }),
      run({ run_id: "complete-1", status: "complete" }),
    ]);
    expect([...positions.keys()].sort()).toEqual(["queued-1", "queued-2"].sort());
    expect(positions.get("queued-1")).toEqual({ position: 1, of: 2 });
    expect(positions.get("queued-2")).toEqual({ position: 2, of: 2 });
  });

  it("no queued jobs yields an empty map", () => {
    const positions = queuePositions([run({ status: "running" }), run({ status: "complete" })]);
    expect(positions.size).toBe(0);
  });
});
