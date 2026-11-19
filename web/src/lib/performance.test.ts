import { describe, expect, it } from "vitest";

import { performance, type TrackedSession } from "@/lib/performance";
import type { TraderFill } from "@/types/control";

function tracked(session: string, over: Partial<TrackedSession> = {}): TrackedSession {
  return {
    session,
    status: "traded",
    buys: 0,
    sells: 0,
    realized_pnl: 0,
    loss_sales: 0,
    orders_placed: 0,
    fill_share: null,
    not_ready_minutes: null,
    shadow: null,
    ...over,
  };
}

/** Noon Eastern on a November day (EST, UTC-5), in epoch seconds. */
function noon(day: string): number {
  return Date.parse(`${day}T17:00:00Z`) / 1000;
}

function sell(day: string, pnl: number): TraderFill {
  return { t: noon(day), side: "sell", lot: "a", qty: 1, price: 10, pnl };
}

function buy(day: string): TraderFill {
  return { t: noon(day), side: "buy", lot: "a", qty: 1, price: 10 };
}

describe("a deployment's results over time", () => {
  it("is empty with nothing recorded", () => {
    const none = performance([], []);
    expect(none.rows).toEqual([]);
    expect(none).toMatchObject({ realized: 0, shadow: null, fillShare: null, best: null });
  });

  it("runs the realised profit session by session, oldest first", () => {
    const out = performance(
      [
        tracked("2026-11-11", { sells: 2, realized_pnl: 5 }),
        tracked("2026-11-10", { sells: 1, realized_pnl: -2, status: "partial" }),
      ],
      [],
    );
    expect(out.rows.map((row) => [row.session, row.realized, row.running])).toEqual([
      ["2026-11-10", -2, -2],
      ["2026-11-11", 5, 3],
    ]);
    expect(out).toMatchObject({ realized: 3, winning: 1, losing: 1 });
    expect(out.best?.session).toBe("2026-11-11");
    expect(out.worst?.session).toBe("2026-11-10");
  });

  it("takes today's trades from the journal and keeps the record's shadow", () => {
    const out = performance(
      [
        tracked("2026-11-12", {
          sells: 1,
          realized_pnl: 1,
          shadow: { buys: 2, sells: 2, realized_pnl: 4, return_pct: 0.1 },
        }),
      ],
      [buy("2026-11-12"), sell("2026-11-12", 1), sell("2026-11-12", 2), sell("2026-11-13", 7)],
    );
    expect(out.rows).toHaveLength(2);
    // The record was written before the day's second sale.
    expect(out.rows[0]).toMatchObject({ buys: 1, sells: 2, realized: 3, shadowRealized: 4 });
    // A session only the journal has: no shadow, and the shadow's line holds.
    expect(out.rows[1]).toMatchObject({ realized: 7, running: 10, shadowRealized: null, shadowRunning: 4 });
    expect(out.shadow).toEqual({ sessions: 1, live: 3, shadow: 4 });
  });

  it("weights the share of orders that filled by the orders placed", () => {
    const out = performance(
      [
        tracked("2026-11-10", { orders_placed: 10, fill_share: 0.5, not_ready_minutes: 13 }),
        tracked("2026-11-11", { orders_placed: 30, fill_share: 1, not_ready_minutes: 0 }),
        tracked("2026-11-12", { status: "missed" }),
      ],
      [],
    );
    expect(out.fillShare).toBeCloseTo(35 / 40);
    expect(out.notReadyMinutes).toBe(13);
    expect(out.missed).toBe(1);
  });
});
