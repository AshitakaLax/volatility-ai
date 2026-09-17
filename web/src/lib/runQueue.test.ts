/**
 * Queue position, display order, and the controls each run allows.
 *
 * Positions come from the server -- runs can be reordered, so submission
 * order is not execution order and is never used to guess one.
 */
import { describe, expect, it } from "vitest";

import type { Run } from "@/types/backtest";

import {
  availableActions,
  isActive,
  moveTarget,
  orderActiveRuns,
  queuePositions,
} from "./runQueue";

function run(over: Partial<Run> = {}): Run {
  return {
    id: "r1",
    status: "queued",
    progress: 0,
    pos: null,
    msg: null,
    error: null,
    req: { tickers: ["TQQQ"], grid_steps: [0.01], targets: [0.005] },
    report: null,
    ...over,
  };
}

describe("queuePositions -- server-provided", () => {
  it("uses pos, not submission order", () => {
    // Submitted a, b, c; then c was moved to the front.
    const positions = queuePositions([
      run({ id: "c", pos: 1 }),
      run({ id: "b", pos: 3 }),
      run({ id: "a", pos: 2 }),
    ]);
    expect(positions.get("c")).toEqual({ position: 1, of: 3 });
    expect(positions.get("a")).toEqual({ position: 2, of: 3 });
    expect(positions.get("b")).toEqual({ position: 3, of: 3 });
  });

  it("paused runs hold a place alongside queued ones", () => {
    const positions = queuePositions([
      run({ id: "q", status: "queued", pos: 2 }),
      run({ id: "p", status: "paused", pos: 1 }),
      run({ id: "r", status: "running", pos: null }),
    ]);
    expect(positions.get("p")).toEqual({ position: 1, of: 2 });
    expect(positions.get("q")).toEqual({ position: 2, of: 2 });
    expect(positions.has("r")).toBe(false);
  });
});

describe("queuePositions -- only what the server says", () => {
  it("a pending run the server gave no position gets none, rather than a guess", () => {
    expect(queuePositions([run({ id: "a", pos: null })]).has("a")).toBe(false);
  });

  it("only pending jobs get a position -- running and finished are excluded", () => {
    const positions = queuePositions([
      run({ id: "queued-2", status: "queued", pos: 2 }),
      run({ id: "failed-1", status: "failed" }),
      run({ id: "cancelled-1", status: "cancelled" }),
      run({ id: "running-1", status: "running" }),
      run({ id: "pausing-1", status: "pausing" }),
      run({ id: "queued-1", status: "queued", pos: 1 }),
      run({ id: "complete-1", status: "complete" }),
    ]);
    expect([...positions.keys()].sort()).toEqual(["queued-1", "queued-2"]);
    expect(positions.get("queued-1")).toEqual({ position: 1, of: 2 });
  });

  it("no pending jobs yields an empty map", () => {
    expect(queuePositions([run({ status: "running" }), run({ status: "complete" })]).size).toBe(0);
  });
});

describe("orderActiveRuns", () => {
  it("running first, then pending by position, finished excluded", () => {
    const ordered = orderActiveRuns([
      run({ id: "done", status: "complete", pos: null }),
      run({ id: "second", status: "paused", pos: 2 }),
      run({ id: "first", status: "queued", pos: 1 }),
      run({ id: "now", status: "running", pos: null }),
    ]);
    expect(ordered.map((r) => r.id)).toEqual(["now", "first", "second"]);
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
    const actions = availableActions(run({ status: "pausing" }), undefined);
    expect([actions.pause, actions.resume, actions.cancel]).toEqual([false, true, true]);
  });

  it("a pending cancel leaves nothing to press", () => {
    const actions = availableActions(run({ status: "cancelling" }), undefined);
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
