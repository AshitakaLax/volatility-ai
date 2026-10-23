/**
 * The Warehouse tab's judgement calls: stale, hot, overdue, full, and when
 * the queue will be done.
 */
import { describe, expect, it } from "vitest";

import type { FundRow, Temperature } from "@/types/warehouse";

import {
  ago,
  backupTone,
  barHeights,
  bytes,
  diskTone,
  duration,
  freshness,
  queueEta,
  temperatureTone,
  whole,
} from "./warehouse";

function fund(over: Partial<FundRow> = {}): FundRow {
  return {
    ticker: "RSP",
    ingested: true,
    known: true,
    bars: 1_055_694,
    first: "2016-01-04T14:30:00+00:00",
    last: "2026-10-08T19:59:00+00:00",
    sessions: 2707,
    duplicates: 0,
    bars_per_session: 390,
    through: "2026-10-19",
    last_session: "2026-10-08",
    partial: false,
    sessions_behind: 7,
    bars_to_add: 2730,
    sweeps: 19,
    simulations: 21851,
    current_simulations: 21851,
    older_simulations: 0,
    best_return: 230.7,
    bytes: 12_108_076,
    sector: "Equity Index (Equal Weight)",
    inception: "2003-04-24",
    leverage: 1,
    ...over,
  };
}

const NOW = new Date("2026-10-20T01:30:00Z");

describe("formatting", () => {
  it("sizes in the largest unit under 1024 of it", () => {
    expect(bytes(512)).toBe("512 B");
    expect(bytes(124_644_656)).toBe("118.9 MB");
    expect(bytes(983_348_297_728)).toBe("915.8 GB");
    expect(bytes(null)).toBe("--");
  });

  it("counts whole numbers with separators", () => {
    expect(whole(1_055_694)).toBe("1,055,694");
    expect(whole(undefined)).toBe("--");
  });

  it("spans by their two largest units", () => {
    expect(duration(0.75)).toBe("45m");
    expect(duration(5.5)).toBe("5h 30m");
    expect(duration(52.5)).toBe("2d 4h");
    expect(duration(48)).toBe("2d");
  });

  it("says how long ago", () => {
    expect(ago("2026-10-20T01:29:20Z", NOW)).toBe("40s ago");
    expect(ago("2026-10-20T01:00:00Z", NOW)).toBe("30m ago");
    expect(ago("2026-10-19T13:34:24Z", NOW)).toBe("12h ago");
    expect(ago("2026-10-08T19:59:00Z", NOW)).toBe("11d ago");
    expect(ago(null, NOW)).toBe("never");
  });
});

describe("freshness", () => {
  it("is up to date through the last completed session", () => {
    expect(freshness(fund({ sessions_behind: 0 }))).toEqual({ label: "Up to date", tone: "profit" });
  });

  it("lags for a week of sessions, then is stale", () => {
    expect(freshness(fund({ sessions_behind: 1 }))).toEqual({
      label: "1 session behind",
      tone: "stuck",
    });
    expect(freshness(fund({ sessions_behind: 5 })).tone).toBe("stuck");
    expect(freshness(fund({ sessions_behind: 7 }))).toEqual({
      label: "7 sessions behind",
      tone: "loss",
    });
  });

  it("names a last session fetched before it closed", () => {
    expect(freshness(fund({ sessions_behind: 1, partial: true })).label).toBe(
      "1 session behind (last one partial)",
    );
  });

  it("is neutral about a fund never ingested", () => {
    expect(freshness(fund({ ingested: false, sessions_behind: null }))).toEqual({
      label: "Not ingested",
      tone: "neutral",
    });
  });
});

describe("temperatures", () => {
  const reading = (c: number): Temperature => ({
    label: "Package id 0",
    c,
    high: 83,
    crit: 93,
    hottest: c,
  });

  it("is fine well under the CPU's own high limit", () => {
    expect(temperatureTone(reading(74))).toBe("profit");
  });

  it("warns within five degrees of it, and alarms past it", () => {
    expect(temperatureTone(reading(78))).toBe("stuck");
    expect(temperatureTone(reading(83))).toBe("loss");
  });

  it("falls back to the critical limit, and says nothing without either", () => {
    expect(temperatureTone({ ...reading(90), high: null })).toBe("stuck");
    expect(temperatureTone({ ...reading(90), high: null, crit: null })).toBe("neutral");
  });
});

describe("backups and disks", () => {
  const backups = (at: string) => ({
    dir: "/app/backups",
    count: 3,
    bytes: 200_000,
    latest: { name: "x.tar.gz", bytes: 70_000, at },
  });

  it("is overdue a little after a day", () => {
    expect(backupTone(backups("2026-10-19T07:30:00Z"), NOW)).toBe("profit");
    expect(backupTone(backups("2026-10-18T07:30:00Z"), NOW)).toBe("loss");
    expect(backupTone(null, NOW)).toBe("loss");
    expect(backupTone({ ...backups("x"), latest: null }, NOW)).toBe("loss");
  });

  it("warns under a fifth free and alarms under a tenth", () => {
    expect(diskTone(50, 100)).toBe("neutral");
    expect(diskTone(15, 100)).toBe("stuck");
    expect(diskTone(5, 100)).toBe("loss");
    expect(diskTone(null, 100)).toBe("neutral");
  });
});

describe("the queue", () => {
  it("finishes at the last hour's rate", () => {
    const eta = queueEta(5000, 2500, 50_000, NOW);
    expect(eta?.hours).toBe(2);
    expect(eta?.at.toISOString()).toBe("2026-10-20T03:30:00.000Z");
  });

  it("falls back to the day's average when the last hour ran nothing", () => {
    expect(queueEta(2400, 0, 2400, NOW)?.hours).toBe(24);
  });

  it("has no answer with nothing left or nothing running", () => {
    expect(queueEta(0, 2500, 50_000, NOW)).toBeNull();
    expect(queueEta(100, 0, 0, NOW)).toBeNull();
  });

  it("scales the activity strip to its busiest hour", () => {
    expect(barHeights([{ n: 0 }, { n: 50 }, { n: 100 }])).toEqual([0, 50, 100]);
    expect(barHeights([{ n: 0 }, { n: 0 }])).toEqual([0, 0]);
  });
});
