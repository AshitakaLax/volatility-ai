/**
 * Queue position, display order, and the controls each run allows.
 *
 * Positions come from the server whenever it sends them -- runs can be
 * reordered, so submission order is no longer execution order. The
 * fallback cases below cover a server that predates queue controls, where
 * each case is one a wrong answer (sorting by run_id, trusting list order
 * without un-reversing it) looks fine on a small list and only shows up
 * once several jobs are actually queued.
 */
import { describe, expect, it } from "vitest";

import type { BacktestRunState } from "@/types/backtest";

import {
  availableActions,
  isActive,
  moveTarget,
  orderActiveRuns,
  queuePositions,
} from "./runQueue";

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

describe("queuePositions -- server-provided", () => {
  it("uses queue_position, not submission order, once the server sends it", () => {
    // Submitted a, b, c; then c was moved to the front.
    const positions = queuePositions([
      run({ run_id: "c", queue_position: 1 }),
      run({ run_id: "b", queue_position: 3 }),
      run({ run_id: "a", queue_position: 2 }),
    ]);
    expect(positions.get("c")).toEqual({ position: 1, of: 3 });
    expect(positions.get("a")).toEqual({ position: 2, of: 3 });
    expect(positions.get("b")).toEqual({ position: 3, of: 3 });
  });

  it("paused runs hold a place alongside queued ones", () => {
    const positions = queuePositions([
      run({ run_id: "q", status: "queued", queue_position: 2 }),
      run({ run_id: "p", status: "paused", queue_position: 1 }),
      run({ run_id: "r", status: "running", queue_position: null }),
    ]);
    expect(positions.get("p")).toEqual({ position: 1, of: 2 });
    expect(positions.get("q")).toEqual({ position: 2, of: 2 });
    expect(positions.has("r")).toBe(false);
  });
});

describe("queuePositions -- fallback for an older server", () => {
  it("a single queued job is next up, 1 of 1", () => {
    const positions = queuePositions([run({ run_id: "a" })]);
    expect(positions.get("a")).toEqual({ position: 1, of: 1 });
  });

  it("positions follow SUBMISSION order, not list order -- the input is newest-first", () => {
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
    const positions = queuePositions([run({ run_id: "aaa" }), run({ run_id: "zzz" })]);
    expect(positions.get("zzz")).toEqual({ position: 1, of: 2 });
    expect(positions.get("aaa")).toEqual({ position: 2, of: 2 });
  });

  it("only pending jobs get a position -- running and finished are excluded", () => {
    const positions = queuePositions([
      run({ run_id: "queued-2", status: "queued" }),
      run({ run_id: "failed-1", status: "failed" }),
      run({ run_id: "cancelled-1", status: "cancelled" }),
      run({ run_id: "running-1", status: "running" }),
      run({ run_id: "queued-1", status: "queued" }),
      run({ run_id: "complete-1", status: "complete" }),
    ]);
    expect([...positions.keys()].sort()).toEqual(["queued-1", "queued-2"]);
    expect(positions.get("queued-1")).toEqual({ position: 1, of: 2 });
  });

  it("a mix of runs with and without queue_position falls back rather than half-trusting", () => {
    const positions = queuePositions([
      run({ run_id: "b", queue_position: 1 }),
      run({ run_id: "a" }),
    ]);
    expect(positions.get("a")).toEqual({ position: 1, of: 2 });
  });

  it("no pending jobs yields an empty map", () => {
    expect(queuePositions([run({ status: "running" }), run({ status: "complete" })]).size).toBe(0);
  });
});

describe("orderActiveRuns", () => {
  it("running first, then pending by position, finished excluded", () => {
    const ordered = orderActiveRuns([
      run({ run_id: "done", status: "complete", queue_position: null }),
      run({ run_id: "second", status: "paused", queue_position: 2 }),
      run({ run_id: "first", status: "queued", queue_position: 1 }),
      run({ run_id: "now", status: "running", queue_position: null }),
    ]);
    expect(ordered.map((r) => r.run_id)).toEqual(["now", "first", "second"]);
  });
});

describe("availableActions", () => {
  const at = (position: number, of: number) => ({ position, of });

  it("a running run can be paused or cancelled but not moved", () => {
    expect(availableActions(run({ status: "running" }), undefined)).toEqual({
      pause: true,
      resume: false,
      cancel: true,
      runNext: false,
      moveUp: false,
      moveDown: false,
    });
  });

  it("a pending pause can be taken back, and is not offered twice", () => {
    const actions = availableActions(run({ status: "running", stop_requested: "pause" }), undefined);
    expect([actions.pause, actions.resume, actions.cancel]).toEqual([false, true, true]);
  });

  it("a pending cancel leaves nothing to press", () => {
    const actions = availableActions(
      run({ status: "running", stop_requested: "cancel" }),
      undefined,
    );
    expect(Object.values(actions).every((allowed) => !allowed)).toBe(true);
  });

  it("the head of the queue cannot move up or jump the queue; the tail cannot move down", () => {
    expect(availableActions(run(), at(1, 3))).toMatchObject({ runNext: false, moveUp: false, moveDown: true });
    expect(availableActions(run(), at(3, 3))).toMatchObject({ runNext: true, moveUp: true, moveDown: false });
  });

  it("paused offers resume instead of pause", () => {
    expect(availableActions(run({ status: "paused" }), at(2, 2))).toMatchObject({
      pause: false,
      resume: true,
      cancel: true,
      runNext: true,
    });
  });

  it.each(["complete", "failed", "cancelled"] as const)("a %s run allows nothing", (status) => {
    const actions = availableActions(run({ status }), undefined);
    expect(Object.values(actions).every((allowed) => !allowed)).toBe(true);
    expect(isActive(status)).toBe(false);
  });
});

describe("moveTarget", () => {
  it("translates a one-place move into the server's 0-based index without the moved run", () => {
    // Pending [A, B, C]. B is at place 2.
    expect(moveTarget({ position: 2, of: 3 }, "up")).toBe(0); // -> [B, A, C]
    expect(moveTarget({ position: 2, of: 3 }, "down")).toBe(2); // -> [A, C, B]
    expect(moveTarget({ position: 1, of: 3 }, "up")).toBe(0);
  });
});
