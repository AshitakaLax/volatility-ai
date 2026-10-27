import type { OrderEvent, TradingWindow, WindowSummary } from "@/types/control";

/** One order, folded from its moments in the trader's orders journal. */
export interface OrderRow {
  order: string;
  kind: OrderEvent["kind"];
  session: OrderEvent["session"];
  placedAt: number | null;
  limit: number | null;
  qty: number | null;
  filledQty: number;
  avgPrice: number | null;
  /** "working" until it ends. */
  outcome: "working" | "filled" | "partially_filled" | "cancelled" | "expired" | "rejected";
  /** Why a cancel was asked: its time-to-live, or its window's end. */
  why: OrderEvent["why"] | null;
  endedAt: number | null;
}

const ENDS = new Set(["filled", "cancelled", "expired", "rejected"]);

/** The journal's events, one row per order, newest placed first. */
export function orderRows(events: OrderEvent[]): OrderRow[] {
  const rows = new Map<string, OrderRow>();
  for (const event of [...events].sort((a, b) => a.t - b.t)) {
    const row = rows.get(event.order) ?? {
      order: event.order,
      kind: event.kind,
      session: event.session,
      placedAt: null,
      limit: event.limit,
      qty: event.qty,
      filledQty: 0,
      avgPrice: null,
      outcome: "working" as const,
      why: null,
      endedAt: null,
    };
    if (event.event === "placed") row.placedAt = event.t;
    row.limit = event.limit ?? row.limit;
    row.qty = event.qty ?? row.qty;
    row.filledQty = event.filled_qty;
    row.avgPrice = event.avg_price;
    if (event.why) row.why = event.why;
    if (event.event === "partially_filled" && row.outcome === "working") {
      row.outcome = "partially_filled";
    }
    if (ENDS.has(event.event)) {
      row.outcome = event.event as OrderRow["outcome"];
      row.endedAt = event.t;
    }
    rows.set(event.order, row);
  }
  return [...rows.values()].sort((a, b) => (b.placedAt ?? 0) - (a.placedAt ?? 0));
}

const SESSION_WORDS: Record<TradingWindow["session"], string> = {
  pre_market: "pre-market",
  regular: "regular",
  after_hours: "after-hours",
};

export function sessionWords(session: OrderEvent["session"]): string {
  return session ? SESSION_WORDS[session] : "regular";
}

/** How an order ended, in words: "filled", "cancelled: rested 5 min", ... */
export function outcomeWords(row: OrderRow): string {
  const partial = row.filledQty > 0 && row.outcome !== "filled" ? ` (${row.filledQty} filled)` : "";
  switch (row.outcome) {
    case "filled":
      return "filled";
    case "working":
      return "working";
    case "partially_filled":
      return `partly filled${partial}`;
    case "cancelled":
      return (
        (row.why === "ttl"
          ? "cancelled: rested too long"
          : row.why === "session_end"
            ? "cancelled: its window closed"
            : "cancelled") + partial
      );
    case "expired":
      return `expired${partial}`;
    case "rejected":
      return "rejected by the venue";
  }
}

/** A window's audit in one line: "pre-market: 2 orders, 9 filled at $217.31; 1 cancelled". */
export function windowWords(summary: WindowSummary): string {
  const head = `${sessionWords(summary.session)}: ${summary.orders} order${summary.orders === 1 ? "" : "s"}`;
  const filled =
    summary.filled_qty > 0 && summary.avg_price !== null
      ? `, ${summary.filled_qty} filled at $${summary.avg_price.toFixed(2)}`
      : summary.orders > 0
        ? ", nothing filled"
        : "";
  const ended = Object.entries(summary.ended)
    .filter(([how]) => how !== "filled")
    .map(([how, count]) => `${count} ${how}`)
    .join(", ");
  return head + filled + (ended ? `; ${ended}` : "");
}
