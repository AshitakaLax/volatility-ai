import { describe, expect, it } from "vitest";

import { appendNewer, easternSession, lastSessions, newest } from "@/lib/journal";
import { clampPage, pageCount, pageOf } from "@/lib/paging";

// 2026-11-16 15:00 UTC = 10:00 ET, and the next two sessions.
const MON = Date.UTC(2026, 10, 16, 15) / 1000;
const DAY = 86400;

describe("a journal polled incrementally", () => {
  it("appends only rows newer than the newest held, and keeps the array when none are", () => {
    const have = [{ t: MON }, { t: MON + 60 }];
    expect(newest(have)).toBe(MON + 60);
    expect(newest([])).toBeUndefined();
    expect(appendNewer(have, [])).toBe(have);
    expect(appendNewer(have, [{ t: MON + 60 }])).toBe(have);
    expect(appendNewer(have, [{ t: MON + 60 }, { t: MON + 120 }]).map((r) => r.t)).toEqual([
      MON,
      MON + 60,
      MON + 120,
    ]);
    expect(appendNewer([], [{ t: MON }])).toEqual([{ t: MON }]);
  });

  it("drops the oldest session once the window moves past it", () => {
    const rows = [{ t: MON }, { t: MON + DAY }, { t: MON + 2 * DAY }];
    expect(easternSession(MON)).toBe("2026-11-16");
    expect(lastSessions(rows, 2).map((r) => easternSession(r.t))).toEqual([
      "2026-11-17",
      "2026-11-18",
    ]);
    expect(lastSessions(rows, 5)).toBe(rows);
  });
});

describe("a table a page at a time", () => {
  it("pages, and clamps a page past the end to the last", () => {
    const rows = Array.from({ length: 120 }, (_, i) => i);
    expect(pageCount(120, 50)).toBe(3);
    expect(pageCount(0, 50)).toBe(1);
    expect(pageOf(rows, 0, 50)).toEqual(rows.slice(0, 50));
    expect(pageOf(rows, 2, 50)).toEqual(rows.slice(100));
    expect(pageOf(rows, 9, 50)).toEqual(rows.slice(100));
    expect(clampPage(-1, 120, 50)).toBe(0);
  });
});
