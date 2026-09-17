/**
 * The live-deployment wire contract, mirrored from server/live.py.
 *
 * That module reads through src/data/dashboard_data.py, which opens the
 * SQLite store `mode=ro` -- the DRIVER refuses writes, so read-only is
 * enforced below the application, not by convention in it.
 *
 * WHAT THIS DATA IS NOT. The loop writes through to the store once per
 * tick, so everything here is up to one poll interval behind (60s by
 * default). The UI must SAY so: a dashboard that looks real-time and is
 * not will eventually be trusted at the wrong moment.
 */

/** One open position -- the grid's unit of inventory. */
export interface Lot {
  id: string;
  symbol: string;
  /** Buy price. */
  px: number;
  qty: number;
  /** Fractional, e.g. 0.003 for 30bps. */
  target: number;
  /** px x (1 + target), fixed at registration. */
  target_px: number;
  /** How far price must rise, as a fraction, for this lot to sell --
   * computed server-side so there is one definition. null when there is
   * no mark, which is DISTINCT from 0 ("already there"). A lot's market
   * value is qty x LiveState.last_px. */
  to_target: number | null;
  /** How far below the last mark this lot was bought (px / mark - 1). */
  vs_mark: number | null;
}

/** What the loop is TRADING, written through every tick. Empty for a
 * store written before the loop recorded it -- render unknown, not zeros.
 * This is what would have made a 30% target meant as 0.3% visible. */
export interface LiveParams {
  symbol?: string;
  /** Fractional, e.g. 0.00075 for 7.5bps. */
  step?: number;
  profit_target?: number;
  strategy_id?: string;
  paper?: boolean;
  poll_interval_seconds?: number;
  extended_hours?: boolean;
}

/**
 * Everything one store holds. A store that has never run is a NORMAL
 * state, not an error: no cash, no lots, no halt -- say so, don't fail.
 */
export interface LiveState {
  exists: boolean;
  /** Monotonic store revision; the WebSocket pushes when it changes. */
  rev: number;
  cash: number | null;
  /** Sale proceeds inside their T+N settlement window. */
  unsettled: number;
  /** cash - unsettled, floored at zero: what can actually be spent. */
  buying_power: number | null;
  peak_equity: number | null;
  /** The circuit breaker: non-null exactly when halted, and the value is
   * the reason. Blocks NEW BUYS only -- nothing force-liquidates. */
  halt: string | null;
  lots: Lot[];
  closed: Lot[];
  /** Proceeds not yet settled, as [settles_on_session, amount]. */
  settling: [session: number, amount: number][];
  /** Seconds since the store file was written -- an mtime proxy that
   * cannot tell "stopped" from "market closed". */
  write_age_s: number | null;
  /** The loop's OWN last mark and tick time: a real heartbeat. */
  last_px: number | null;
  last_tick: string | null;
  params: LiveParams;
}

/** A live RSI reading, from the same WilderRSI the strategy trades on. */
export interface Rsi {
  /** null until the period seeds -- an unseeded average is a partial mean. */
  rsi: number | null;
  /** Bars used. */
  n: number;
  as_of: string | null;
  /** The bar FILE, which can lag a running deployment. */
  source: string;
}

/** A row from the loop's activity journal, newest first. */
export interface Activity {
  timestamp: string;
  kind: string;
  detail: string;
}

/* ------------------------------------------------------------------ */
/* Client-side                                                         */
/* ------------------------------------------------------------------ */

export type ConnectionStatus = "connecting" | "open" | "reconnecting" | "closed" | "error";

export interface ConnectionHealth {
  status: ConnectionStatus;
  /** Resets to 0 on a successful open. */
  retries: number;
  /** Epoch ms of the last frame of any kind. */
  lastMessageAt: number | null;
  /** Round-trip of the last heartbeat, ms. */
  latencyMs: number | null;
}

/** A store path's picker label and paper badge. A NAMING CONVENTION, not
 * a fact about the account -- the store does not record it -- so nothing
 * may gate a decision on `paper`. */
export function describeStore(path: string): { path: string; label: string; paper: boolean } {
  return {
    path,
    label: path.split(/[\\/]/).pop() ?? path,
    paper: path.toLowerCase().includes("paper"),
  };
}
