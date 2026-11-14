/**
 * A deployment's results over time, for the Live page's Performance card:
 * realised profit session by session and running, beside the shadow
 * backtest of the same days where the `tracking` service recorded one
 * (tools/track_live.py, served by GET .../tracking).
 *
 * Two sources, joined: the tracking record, which keeps every session for
 * good but is written once a day, and the trader's own fill journal, which
 * holds only its newest sessions but is current to the minute. A session in
 * both takes the journal's trades (the day may not have been over when the
 * record was written) and keeps the record's shadow and fill figures.
 */
import type { TraderFill } from "@/types/control";

/** One row of GET /api/live/deployments/{id}/tracking. */
export interface TrackedSession {
  /** Eastern session date, YYYY-MM-DD. */
  session: string;
  status: "traded" | "partial" | "missed" | "unknown" | string;
  buys: number;
  sells: number;
  realized_pnl: number;
  loss_sales: number;
  orders_placed: number;
  /** Share of placed orders that filled; null with none placed. */
  fill_share: number | null;
  /** Slippage against the limit, and what the cost model charges, in bps. */
  live_bps?: number | null;
  model_bps?: number | null;
  /** A Fidelity bridge's minutes not ready in the regular session. */
  not_ready_minutes: number | null;
  shadow: { buys: number; sells: number; realized_pnl: number; return_pct: number } | null;
}

export interface Tracking {
  sessions: TrackedSession[];
  /** Epoch seconds the record was last written; null when it never was. */
  updated_at: number | null;
}

export interface PerformanceRow {
  session: string;
  buys: number;
  sells: number;
  realized: number;
  /** Realised profit up to and including this session. */
  running: number;
  status: string | null;
  shadowRealized: number | null;
  /** The shadow's running realised profit; null before its first session. */
  shadowRunning: number | null;
  fillShare: number | null;
  notReadyMinutes: number | null;
}

export interface Performance {
  rows: PerformanceRow[];
  realized: number;
  buys: number;
  sells: number;
  /** Sessions with a sale / sessions that realised a loss. */
  winning: number;
  losing: number;
  best: PerformanceRow | null;
  worst: PerformanceRow | null;
  /** Over the sessions the shadow covers: live against it. */
  shadow: { sessions: number; live: number; shadow: number } | null;
  /** Placed orders that filled, across tracked sessions. */
  fillShare: number | null;
  notReadyMinutes: number | null;
  missed: number;
}

function eastern(seconds: number): string {
  return new Date(seconds * 1000).toLocaleDateString("en-CA", { timeZone: "America/New_York" });
}

export function performance(tracked: TrackedSession[], fills: TraderFill[]): Performance {
  const bySession = new Map<string, Omit<PerformanceRow, "running" | "shadowRunning">>();
  for (const row of tracked) {
    bySession.set(row.session, {
      session: row.session,
      buys: row.buys,
      sells: row.sells,
      realized: row.realized_pnl,
      status: row.status,
      shadowRealized: row.shadow ? row.shadow.realized_pnl : null,
      fillShare: row.fill_share,
      notReadyMinutes: row.not_ready_minutes,
    });
  }
  const journal = new Map<string, { buys: number; sells: number; realized: number }>();
  for (const fill of fills) {
    const session = eastern(fill.t);
    const day = journal.get(session) ?? { buys: 0, sells: 0, realized: 0 };
    if (fill.side === "buy") day.buys += 1;
    else {
      day.sells += 1;
      day.realized += fill.pnl ?? 0;
    }
    journal.set(session, day);
  }
  for (const [session, day] of journal) {
    const kept = bySession.get(session);
    bySession.set(session, {
      session,
      status: kept?.status ?? null,
      shadowRealized: kept?.shadowRealized ?? null,
      fillShare: kept?.fillShare ?? null,
      notReadyMinutes: kept?.notReadyMinutes ?? null,
      ...day,
    });
  }

  const rows: PerformanceRow[] = [];
  let running = 0;
  let shadowRunning: number | null = null;
  for (const row of [...bySession.values()].sort((a, b) => a.session.localeCompare(b.session))) {
    running += row.realized;
    if (row.shadowRealized !== null) shadowRunning = (shadowRunning ?? 0) + row.shadowRealized;
    rows.push({ ...row, running, shadowRunning });
  }

  const shadowed = rows.filter((row) => row.shadowRealized !== null);
  const placed = tracked.reduce((sum, row) => sum + row.orders_placed, 0);
  const filled = tracked.reduce(
    (sum, row) => sum + (row.fill_share ?? 0) * row.orders_placed,
    0,
  );
  const minutes = tracked.filter((row) => row.not_ready_minutes !== null);
  const traded = rows.filter((row) => row.sells > 0);
  const extreme = (pick: (a: PerformanceRow, b: PerformanceRow) => boolean) =>
    traded.reduce<PerformanceRow | null>((best, row) => (!best || pick(row, best) ? row : best), null);
  return {
    rows,
    realized: running,
    buys: rows.reduce((sum, row) => sum + row.buys, 0),
    sells: rows.reduce((sum, row) => sum + row.sells, 0),
    winning: rows.filter((row) => row.realized > 0).length,
    losing: rows.filter((row) => row.realized < 0).length,
    best: extreme((a, b) => a.realized > b.realized),
    worst: extreme((a, b) => a.realized < b.realized),
    shadow: shadowed.length
      ? {
          sessions: shadowed.length,
          live: shadowed.reduce((sum, row) => sum + row.realized, 0),
          shadow: shadowed.reduce((sum, row) => sum + (row.shadowRealized ?? 0), 0),
        }
      : null,
    fillShare: placed ? filled / placed : null,
    notReadyMinutes: minutes.length
      ? minutes.reduce((sum, row) => sum + (row.not_ready_minutes ?? 0), 0)
      : null,
    missed: tracked.filter((row) => row.status === "missed").length,
  };
}
