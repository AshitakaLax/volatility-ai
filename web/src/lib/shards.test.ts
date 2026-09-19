/**
 * Shard summaries, labels, and which controls each shard allows.
 */
import { describe, expect, it } from "vitest";

import type { Shard } from "@/types/backtest";

import {
  connLabel,
  describeSeen,
  scheduleLabel,
  shardActions,
  stateLabel,
  summarizeShards,
  sweepLabel,
  versionMismatch,
} from "./shards";

function shard(over: Partial<Shard> = {}): Shard {
  return {
    name: "fast-shard",
    local: false,
    conn: "online",
    state: "idle",
    host: "10.0.0.5",
    commit: "abc1234",
    dirty: false,
    cores: 16,
    seen_s: 1,
    since: 0,
    paused: false,
    locked_out: false,
    schedule: null,
    run: null,
    ...over,
  };
}

const RUN = { id: "0123456789abcdef", name: "RSP rsi [3/16]", progress: 0.4, msg: "RSP: 40/96" };

describe("summarizeShards", () => {
  it("counts connected, working, paused and locked-out shards", () => {
    const summary = summarizeShards([
      shard({ name: "local", local: true }),
      shard({ state: "running", run: RUN }),
      shard({ state: "pausing", run: RUN }),
      shard({ state: "paused", conn: "stale" }),
      shard({ state: "locked_out" }),
      shard({ conn: "offline" }),
    ]);
    expect(summary).toEqual({ total: 6, online: 4, working: 2, paused: 2, lockedOut: 1 });
  });

  it("is all zeros for no shards", () => {
    expect(summarizeShards([])).toEqual({
      total: 0,
      online: 0,
      working: 0,
      paused: 0,
      lockedOut: 0,
    });
  });
});

describe("shardActions", () => {
  it("offers pause to a working or idle shard", () => {
    expect(shardActions(shard({ state: "running", run: RUN }))).toEqual({
      pause: true,
      resume: false,
      forget: false,
    });
  });

  it("offers resume to a paused or pausing shard", () => {
    expect(shardActions(shard({ state: "paused" })).resume).toBe(true);
    expect(shardActions(shard({ state: "pausing", run: RUN }))).toMatchObject({
      pause: false,
      resume: true,
    });
  });

  it("offers forget only for an offline remote shard", () => {
    expect(shardActions(shard({ conn: "offline" })).forget).toBe(true);
    expect(shardActions(shard({ conn: "stale" })).forget).toBe(false);
    expect(shardActions(shard({ conn: "offline", local: true })).forget).toBe(false);
  });

  it("still lets a disconnected shard be paused", () => {
    expect(shardActions(shard({ conn: "offline" })).pause).toBe(true);
  });
});

describe("versionMismatch", () => {
  it("flags a different commit", () => {
    expect(versionMismatch(shard({ commit: "abc1234" }), "def5678")).toBe(true);
  });

  it("does not flag an unknown commit on either side", () => {
    expect(versionMismatch(shard({ commit: null }), "def5678")).toBe(false);
    expect(versionMismatch(shard({ commit: "abc1234" }), null)).toBe(false);
    expect(versionMismatch(shard({ commit: "abc1234" }), "abc1234")).toBe(false);
  });
});

describe("labels", () => {
  it("describes connection states in words", () => {
    expect(connLabel("online")).toBe("connected");
    expect(connLabel("stale")).toBe("not responding");
    expect(connLabel("offline")).toBe("disconnected");
  });

  it("describes how long ago a heartbeat was", () => {
    expect(describeSeen(0)).toBe("just now");
    expect(describeSeen(42.7)).toBe("42s ago");
    expect(describeSeen(185)).toBe("3m ago");
    expect(describeSeen(7300)).toBe("2h ago");
  });

  it("names a sweep by its label, else a short id", () => {
    expect(sweepLabel(RUN)).toBe("RSP rsi [3/16]");
    expect(sweepLabel({ ...RUN, name: "  " })).toBe("0123456789");
    expect(sweepLabel({ ...RUN, name: null })).toBe("0123456789");
  });

  it("describes locked_out distinctly from a manual pause", () => {
    expect(stateLabel("locked_out")).toMatch(/locked out/);
    expect(stateLabel("paused")).not.toMatch(/locked out/);
  });
});

describe("scheduleLabel", () => {
  it("renders a 12-hour range", () => {
    expect(scheduleLabel({ enabled: true, start: "07:00", end: "19:00" })).toBe(
      "7:00 AM - 7:00 PM",
    );
    expect(scheduleLabel({ enabled: false, start: "00:00", end: "12:30" })).toBe(
      "12:00 AM - 12:30 PM",
    );
  });

  it("is null with no window configured", () => {
    expect(scheduleLabel(null)).toBeNull();
    expect(scheduleLabel({ enabled: false, start: null, end: null })).toBeNull();
  });
});
