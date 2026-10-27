import { describe, expect, it } from "vitest";

import type { OrderEvent } from "@/types/control";

import { orderRows, outcomeWords, windowWords } from "./orders";

function event(over: Partial<OrderEvent>): OrderEvent {
  return {
    t: 100,
    order: "a",
    kind: "buy",
    event: "placed",
    session: "pre_market",
    limit: 217.0,
    qty: 9,
    filled_qty: 0,
    avg_price: null,
    reason: null,
    ...over,
  };
}

describe("orderRows", () => {
  it("folds an order's moments into one row and says how it ended", () => {
    const rows = orderRows([
      event({ t: 100 }),
      event({ t: 160, event: "partially_filled", filled_qty: 4, avg_price: 216.98 }),
      event({ t: 400, event: "cancel_requested", filled_qty: 4, avg_price: 216.98, why: "ttl" }),
      event({ t: 430, event: "cancelled", filled_qty: 4, avg_price: 216.98 }),
    ]);
    expect(rows).toHaveLength(1);
    const row = rows[0]!;
    expect(row.outcome).toBe("cancelled");
    expect(row.filledQty).toBe(4);
    expect(outcomeWords(row)).toBe("cancelled: rested too long (4 filled)");
  });

  it("lists the newest placed first and keeps a working order working", () => {
    const rows = orderRows([
      event({ t: 100, order: "old" }),
      event({ t: 120, order: "old", event: "filled", filled_qty: 9, avg_price: 217 }),
      event({ t: 300, order: "new", kind: "sell", session: "after_hours" }),
    ]);
    expect(rows.map((r) => r.order)).toEqual(["new", "old"]);
    expect(outcomeWords(rows[0]!)).toBe("working");
    expect(outcomeWords(rows[1]!)).toBe("filled");
  });
});

describe("windowWords", () => {
  it("says what filled and how the rest ended", () => {
    const words = windowWords({
      day: "2026-10-27",
      session: "pre_market",
      start: "",
      end: "",
      at: "",
      orders: 2,
      filled_qty: 9,
      avg_price: 217.314,
      ended: { filled: 1, cancelled: 1 },
    });
    expect(words).toBe("pre-market: 2 orders, 9 filled at $217.31; 1 cancelled");
  });
});
