/**
 * The live-deployment wire contract.
 *
 * Mirrors `src/dashboard_data.py`'s `DeploymentState` and `Lot`, which
 * the Python server reuses verbatim. That module opens the SQLite store
 * with `file:...?mode=ro`, so the DATABASE DRIVER refuses writes -- the
 * read-only guarantee is enforced below the application, not by
 * convention in it.
 *
 * WHAT THIS DATA IS NOT. The live loop holds its working state in
 * memory and writes through to the store once per tick, so everything
 * here is up to one poll interval behind (60s by default). The UI must
 * SAY so rather than imply currency: a dashboard that looks real-time
 * and is not will eventually be trusted at the wrong moment.
 */

/** One open position. The grid's unit of inventory. */
export interface InventoryLot {
  order_id: string;
  symbol: string;
  buy_price: number;
  shares: number;
  /** Fractional, e.g. 0.003 for 30bps. */
  profit_target: number;
  /** `buy_price * (1 + profit_target)`, fixed at registration. */
  target_sell_price: number;
  /**
   * How far price must rise, as a fraction, for this lot to sell.
   *
   * `null` when there is no current mark to compare against -- which is
   * deliberately DISTINCT from 0, meaning "already there".
   */
  distance_to_target: number | null;
  /** Fraction below the last buy at which the next rung triggers. */
  distance_to_next_step: number | null;
  /** Mark-to-market at the last observed price. */
  current_value: number | null;
}

/** Proceeds not yet settled, as `[settles_on_session, amount]`. */
export type PendingSettlement = [number, number];

/**
 * Everything one deployment's store holds.
 *
 * Every field is nullable or defaulted because a store that has never
 * run is a NORMAL state, not an error: a fresh deployment has no cash
 * meta, no lots and no halt, and the UI should say so rather than fail.
 */
export interface DeploymentState {
  /** Path to the SQLite store. Also the account-switcher key. */
  path: string;
  exists: boolean;
  cash: number | null;
  /** Sale proceeds inside their T+N settlement window. */
  unsettled: number;
  /** `cash - unsettled`, floored at zero. What can actually be spent. */
  buying_power: number | null;
  peak_equity: number | null;
  /** Circuit breaker. Blocks NEW BUYS only -- exits keep running, and
   * nothing in this system force-liquidates. */
  halted: boolean;
  halt_reason: string;
  lots: InventoryLot[];
  closed_lots: InventoryLot[];
  pending_settlement: PendingSettlement[];
  /** Monotonic store revision. The WebSocket pushes when this changes. */
  revision: number;
  /** Seconds since the store file was last written -- a file-mtime
   * proxy, which cannot distinguish "stopped" from "market closed". */
  last_write_age: number | null;
  /** The loop's OWN last observed price and tick time: a real mark and a
   * real heartbeat, where `last_write_age` is only a proxy. */
  last_price: number | null;
  last_tick_at: string | null;
}

/** A row from the loop's activity journal. */
export interface ActivityEntry {
  timestamp: string;
  kind: string;
  detail: string;
}

/* ------------------------------------------------------------------ */
/* Connection                                                          */
/* ------------------------------------------------------------------ */

export type ConnectionStatus =
  | "connecting"
  | "open"
  | "reconnecting"
  | "closed"
  | "error";

export interface ConnectionHealth {
  status: ConnectionStatus;
  /** Resets to 0 on a successful open. */
  retries: number;
  /** Epoch ms of the last frame of any kind. */
  lastMessageAt: number | null;
  /** Round-trip of the last heartbeat, ms. */
  latencyMs: number | null;
}

/* ------------------------------------------------------------------ */
/* Deployment health                                                   */
/* ------------------------------------------------------------------ */

export interface DeploymentTelemetry {
  git_commit: string | null;
  git_branch: string | null;
  git_dirty: boolean;
  deployed_at: string | null;
  /** Absent outside a container -- most deployments here run bare. */
  cpu_pct: number | null;
  memory_mb: number | null;
  memory_limit_mb: number | null;
}

/** One selectable account, backed by one store file. */
export interface AccountRef {
  path: string;
  label: string;
  paper: boolean;
}

/* ------------------------------------------------------------------ */
/* Commands                                                            */
/* ------------------------------------------------------------------ */

/**
 * What the UI may ask the system to do.
 *
 * `emergency_halt` is THE ONLY ONE IMPLEMENTED, and that is a decision
 * rather than an omission. It maps onto the existing `CircuitBreaker`,
 * which already persists, survives restart and is operator-reversible.
 *
 * The other two are typed here so the UI can render them greyed out
 * WITH THEIR REASON, which is more honest than hiding controls a reader
 * might expect:
 *
 *   liquidate_all       `src/live_trading_loop.py`: "NO FORCED
 *                       LIQUIDATION, EVER. There is no code path in
 *                       this module that sells a lot for any reason
 *                       other than its profit target being met and the
 *                       no-loss guard permitting it." There is nothing
 *                       to call, and adding it would mean a forced-sell
 *                       path that realises losses.
 *   parameter_override  Live parameters come from a committed config,
 *                       not from a browser: routing real capital should
 *                       be a reviewable decision.
 */
export type CommandKind =
  | "emergency_halt"
  | "liquidate_all"
  | "parameter_override";

export interface CommandDescriptor {
  kind: CommandKind;
  label: string;
  available: boolean;
  /** Why not, shown in the UI when `available` is false. */
  unavailableReason?: string;
  /** Whether it needs a confirmation modal before firing. */
  destructive: boolean;
}

export const COMMANDS: readonly CommandDescriptor[] = [
  {
    kind: "emergency_halt",
    label: "Emergency halt",
    available: true,
    destructive: true,
  },
  {
    kind: "liquidate_all",
    label: "Liquidate all positions",
    available: false,
    unavailableReason:
      "Not implemented, by design. The trading loop has no code path that sells a lot " +
      "for any reason other than its profit target being met and the no-loss guard " +
      "permitting it. Adding one would mean forced selling at a loss.",
    destructive: true,
  },
  {
    kind: "parameter_override",
    label: "Override live parameters",
    available: false,
    unavailableReason:
      "Live parameters come from a committed config file, not from a browser, so that " +
      "routing real capital stays a reviewable decision.",
    destructive: true,
  },
] as const;

export interface HaltRequest {
  path: string;
  reason: string;
}

export interface HaltResponse {
  halted: boolean;
  halt_reason: string;
  revision: number;
}
