/**
 * The Live page's deployments and commands, mirrored by hand from
 * server/live.py (deployment_summary, run_state) and server/live_control.py.
 *
 * A deployment is named by id (config/deployments.yaml), never by path. Its
 * STATUS is what its trader last reported through its control directory --
 * stale reports read as "not_running" rather than as what they last said --
 * and its LEDGER is read mode=ro. A command is an intent the trader applies
 * between ticks or between sessions; its own `status` says when it has.
 */
import type { Param, ParamValue } from "@/types/backtest";
import type { LiveState } from "@/types/telemetry";

/** What a deployment's trader is doing, as one chip. */
export type RunState =
  | "trading"
  | "buys_paused"
  | "winding_down"
  | "waiting_for_open"
  /** A start that could not reach the broker yet (the extension, Fidelity
   * signed out, the bridge not ready): tried again on its own. */
  | "waiting_for_broker"
  | "closed"
  | "disabled"
  | "starting"
  | "restarting"
  | "stopping"
  | "stopped"
  | "recovery_required"
  | "not_running";

/** What the Live page may ask of this deployment: its config's
 * live.control, with the real-money rules applied. */
export interface Caps {
  /** Always: it only ever reduces exposure. */
  pause_buys: true;
  resume_buys: boolean;
  enable_disable: boolean;
  algorithm_changes: boolean;
  profiles_only: boolean;
  ledger_reset: boolean;
}

export type Broker = "alpaca" | "fidelity";

/** A strategy's own diagnostics() -- flat, plain values. Ultimate's carry its
 * regime: ultimate_mode, ultimate_exit_active, regime_since, regime_natr,
 * regime_median, regime_reading, regime_earliest_change, ... */
export type Diagnostics = Record<string, string | number | boolean | null>;

/** What the loop will do next, written after every tick. */
export interface Decision {
  /** The tick's price. */
  price: number;
  /** A buy triggers at or below this; null when the strategy buys at no price now. */
  buy_level: number | null;
  /** The price its grid measures from (the last buy, or the session's start). */
  reference: number | null;
  /** What stops a buy, in the loop's words; null when nothing does. */
  blocked: string | null;
  strategy: Diagnostics | null;
  /** On its venue's windows (live.sessions): the window this tick is in
   * (null between them), the next one, the dollars resting buys hold back,
   * and why the second data source was not used, when it was not. */
  window?: TradingWindow | null;
  next_window?: TradingWindow | null;
  reserved?: number;
  secondary_feed?: string;
}

/** One of a venue's trading windows (engine/core/venue_sessions.py). */
export interface TradingWindow {
  session: "pre_market" | "regular" | "after_hours";
  /** ISO times, Eastern. */
  start: string;
  end: string;
}

/** The engine's own readiness, apart from the broker's (cli.py _EngineFirst). */
export interface EngineStatus {
  state: "starting" | "warming_up" | "ready" | "trading";
  detail: string;
  since: string;
}

/** How a trading window went (the loop's audit when it ended). */
export interface WindowSummary {
  day: string;
  session: TradingWindow["session"];
  start: string;
  end: string;
  at: string;
  orders: number;
  filled_qty: number;
  avg_price: number | null;
  /** How the orders ended: filled, cancelled, expired, rejected -> count. */
  ended: Record<string, number>;
  /** The venue's position against the ledger's, or why it was not checked. */
  position?: { venue: number; ledger: number } | string;
  /** What disagreed; buys are halted for reconciliation when present. */
  problem?: string;
}

/** One moment of an order's life (the trader's orders journal). */
export interface OrderEvent {
  /** Epoch seconds. */
  t: number;
  order: string;
  kind: "buy" | "sell";
  event:
    | "placed"
    | "partially_filled"
    | "filled"
    | "cancel_requested"
    | "cancelled"
    | "expired"
    | "rejected";
  session: TradingWindow["session"] | null;
  limit: number | null;
  qty: number | null;
  filled_qty: number;
  avg_price: number | null;
  reason: string | null;
  /** A cancel's cause: its time-to-live, or its window's end. */
  why?: "ttl" | "session_end";
}

/** While an override trades, the CONFIG FILE's algorithm fed the same bars:
 * what switching back would do now. */
export interface ShadowState {
  strategy: Diagnostics | null;
  /** Lots its own exit would sell on this bar. */
  would_sell: number;
  would_sell_cost: number;
}

/** Which code a process runs (engine/core/build_info.py). */
export interface BuildInfo {
  /** From VAI_BUILD_COMMIT, when the image was built with one. */
  commit: string | null;
  /** A fingerprint of the source: equal exactly when the code is. */
  code: string | null;
  python: string;
  pid: number;
  started_at: string;
}

/** The Fidelity Bridge extension's side of a Fidelity deployment. */
export interface FidelityConnection {
  connected: boolean;
  since: string | null;
  last_heard: string | null;
  disconnected_at: string | null;
  /** The browser's address, as the bridge saw it. */
  client: string | null;
  version: string | null;
  versions: { minimum?: string | null; latest?: string | null };
  /** What to do about an old extension, or null. */
  advice: string | null;
  /** The extension's switches; "place" is its "Allow trading". null before it says. */
  permissions: { preview: boolean; place: boolean } | null;
  url: string | null;
  /** The connected extension's Fidelity tab, by the session's rule. */
  fidelity_tab?: {
    state: "signed_in" | "signed_out" | "no_tab" | "elsewhere";
    url: string | null;
    since: string | null;
  } | null;
  /** The last connection turned away, and why (address, key, origin). */
  last_refused?: { at: string; client: string; reason: string } | null;
  /** How the last connection ended: its WebSocket close code and reason. */
  last_disconnect?: {
    at: string;
    client: string | null;
    code: number | null;
    reason: string | null;
  } | null;
  /** "live" places real orders; "preview" stops at Fidelity's preview. */
  mode: "live" | "preview" | null;
  account_name: string | null;
  max_order_value: number | null;
}

export interface TraderStatus {
  state: RunState;
  detail: string | null;
  process: "loop" | "supervisor" | null;
  next_open: string | null;
  last_tick_at: string | null;
  open_lots: number | null;
  open_orders: number | null;
  algorithm: {
    strategy_id: string;
    step: number | null;
    profit_target: number | null;
    override?: AlgorithmOverride | null;
  } | null;
  updated_at: string | null;
  heartbeat_seconds: number | null;
  /** A one-way tag of the account it trades -- never the key or number. */
  account: string | null;
  cash?: number | null;
  breaker?: { state: string; reason: string | null } | null;
  now?: Decision | null;
  shadow?: ShadowState | null;
  build?: BuildInfo | null;
  broker?: Broker | null;
  /** Why the venue cannot be reached right now; null when it can. */
  broker_unavailable?: string | null;
  fidelity?: FidelityConnection | null;
  /** A start that stopped: the lifecycle stage, and whether it is tried
   * again on its own (the broker could not be reached yet). */
  stage?: string | null;
  retryable?: boolean | null;
  /** The deployment the trader says it is, and the ledger it trades: the
   * file's name and a one-way tag of its path. */
  deployment?: string | null;
  ledger?: string | null;
  /** On its venue's windows (live.sessions): the engine's own readiness,
   * apart from the broker's, and how the last trading window went. */
  engine?: EngineStatus | null;
  last_window?: WindowSummary | null;
  /** True when no report arrived in three heartbeats: state is then "not_running". */
  stale: boolean;
}

/* ------------------------------------------------------------------ */
/* A Fidelity deployment's bridge host (fidelity_gateway/bridge/host.py) */
/* ------------------------------------------------------------------ */

/** One link of the chain from this server to the account. */
export interface ReadinessItem {
  id: "bridge" | "extension" | "version" | "fidelity" | "trading" | "account";
  label: string;
  /** "fail" stops a session starting; "unknown" never does on its own. */
  state: "ok" | "warn" | "fail" | "unknown";
  detail: string;
  fix: string | null;
}

/** fidelity_gateway/bridge/readiness.py: ready, or the one thing to fix. */
export interface Readiness {
  ready: boolean;
  blocking: ReadinessItem["id"] | null;
  summary: string;
  fix: string | null;
  items: ReadinessItem[];
}

/** The read-only account check's last result. */
export interface AccountCheck {
  at: string;
  ok: boolean;
  detail: string;
  by?: string;
}

/** The process attached to the bridge host: a session's trading loop, or a
 * connection check. */
export interface BridgeAttached {
  process: "loop" | "check" | "tool" | string | null;
  pid: number | null;
  deployment: string | null;
  build: BuildInfo | null;
  since: string | null;
  /** Its own engine status, as the extension sees it. */
  status: Record<string, unknown> | null;
}

/** The bridge host's own report, up between sessions too. */
export interface BridgeStatus {
  state: "listening" | "port_conflict" | "stopped";
  detail: string | null;
  listening: boolean;
  listen_error: string | null;
  /** "live" places real orders; "preview" stops at Fidelity's preview. */
  mode: "live" | "preview";
  deployment: string | null;
  symbol: string | null;
  account_name: string | null;
  max_order_value: number | null;
  connection: FidelityConnection;
  attached: BridgeAttached | null;
  readiness: Readiness;
  last_check: AccountCheck | null;
  session_open: boolean;
  next_open: string | null;
  build: BuildInfo | null;
  updated_at: string;
  heartbeat_seconds: number;
  /** No report in three heartbeats: what it last said no longer holds. */
  stale: boolean;
  age_s: number | null;
}

/** One line of the bridge host's journal (GET .../bridge/events). */
export interface BridgeEvent {
  /** Epoch seconds. */
  t: number;
  kind:
    | "started"
    | "stopped"
    | "listening"
    | "port_conflict"
    | "config"
    | "connected"
    | "disconnected"
    | "refused"
    | "fidelity"
    | "trading"
    | "attached"
    | "detached"
    | "attach_refused"
    | "ready"
    | "not_ready"
    | "check"
    | string;
  detail: string;
  code?: number | null;
  client?: string | null;
  version?: string | null;
  state?: string;
  on?: boolean;
  ok?: boolean;
  by?: string;
}

/** The algorithm a deployment trades, for its card: the trader's own report
 * while it reports, otherwise what its next session will trade. */
export interface AlgorithmInForce {
  strategy_id: string;
  /** What it does, in a line: the words the extension's popup shows too
   * (research/strategies/live_algorithm.algorithm_summary). */
  summary?: string;
  /** null when the trader's report names a strategy the files do not. */
  strategy_params: Record<string, ParamValue> | null;
  step: number | null;
  profit_target: number | null;
  source: "config" | "web" | "extension";
  profile: string | null;
  /** The committed profile's label when it is one. */
  label: string | null;
  changed_by: string | null;
  changed_at: string | null;
  reason: string | null;
  /** True for the trader's own report. */
  reported: boolean;
  config_file: Algorithm;
}

/** One fill the trader booked (its fill journal). */
export interface TraderFill {
  /** Epoch seconds. */
  t: number;
  side: "buy" | "sell";
  lot: string;
  qty: number;
  price: number;
  /** A buy: what it cost, and the target its lot carries. */
  value?: number;
  target?: number;
  /** A sale: why (profit_target or signal_exit), what it fetched net,
   * what its lot cost, and the difference. */
  reason?: string;
  proceeds?: number;
  cost?: number;
  pnl?: number;
}

/** Whether sessions should run. Enabled unless an operator said otherwise. */
export interface Desired {
  enabled: boolean;
  /** Buys paused; trading stops by itself once nothing is open. */
  wind_down: boolean;
  by: string | null;
  reason: string | null;
  at: string | null;
}

/** The ledger's own figures, read mode=ro. `exists: false` with `error` for
 * a deployment that has never run -- a normal state, not a failure. */
export interface LedgerSummary {
  exists: boolean;
  error?: string;
  /** Non-null exactly when halted: the reason is the flag. */
  halt?: string | null;
  open_lots?: number;
  cash?: number | null;
  last_px?: number | null;
  last_tick?: string | null;
}

/** GET /api/live/deployments, one per deployment. Everything after `error`
 * is absent when the deployment's config does not load -- or does not exist
 * yet (`setup` then says what to do). */
export interface DeploymentSummary {
  id: string;
  label: string;
  /** The compose service that runs it -- named when it is not running. */
  service: string | null;
  /** The venue: Alpaca's API, or Fidelity through the browser extension. */
  broker: Broker;
  error: string | null;
  /** Set when the deployment is registered but its config does not exist. */
  setup?: string;
  /** From the deployment's config (live.paper_trading), not a file name. */
  paper?: boolean;
  symbol?: string;
  /** The CONFIG FILE's algorithm; `algorithm` is the one in force. */
  strategy_id?: string;
  step?: number | null;
  profit_target?: number | null;
  algorithm?: AlgorithmInForce;
  /** False when the registry names no control directory for it. */
  controllable?: boolean;
  caps?: Caps;
  status?: TraderStatus;
  desired?: Desired;
  ledger?: LedgerSummary;
  /** Commands queued and not yet taken by the trader. */
  pending?: number;
  /** A Fidelity deployment's bridge host; null when none has reported. */
  bridge?: BridgeStatus | null;
}

export type CommandType =
  | "pause_buys"
  | "resume_buys"
  | "disable"
  | "enable"
  | "switch_algorithm"
  | "revert_algorithm"
  | "rewarm"
  | "reset_paper_ledger"
  /** Read-only: the bridge host checks the account through the extension. */
  | "check_connection";

export type CommandStatus =
  | "queued"
  | "applying"
  | "applied"
  | "rejected"
  | "superseded"
  | "expired"
  | "cancelled";

export type Timing = "now" | "next_session" | "when_flat";

/** One command and what came of it, newest first in a deployment's log. */
export interface CommandRow {
  id: string;
  type: CommandType;
  args: Record<string, unknown>;
  timing: Timing;
  reason: string;
  operator: string;
  client: string | null;
  created_at: string;
  expires_at: string;
  idempotency_key: string | null;
  seq: number;
  status: CommandStatus;
  /** The trader's own words on what it did, or why it refused. */
  detail: string;
  finished_at: string | null;
}

/** GET /api/live/deployments/{id}. */
export interface DeploymentDetail extends DeploymentSummary {
  /** null until the deployment's ledger exists. */
  state: LiveState | null;
  commands: CommandRow[];
}

/** POST /api/live/deployments/{id}/commands. */
export interface CommandRequest {
  type: CommandType;
  args?: Record<string, unknown>;
  timing?: Timing;
  /** 3-500 characters: shown to whoever finds the deployment in this state. */
  reason: string;
  operator: string;
  idempotency_key?: string;
  /** The deployment's id typed back, for a command with large consequences. */
  confirm?: string;
}

export interface QueuedCommand {
  command: CommandRow;
  /** False when an idempotency key matched an earlier command. */
  new: boolean;
  /** Set when the trader is not running: it applies when it next starts. */
  warning: string | null;
}

/* ------------------------------------------------------------------ */
/* The algorithm (GET .../algorithm, POST .../algorithm/check)         */
/* ------------------------------------------------------------------ */

/** What a deployment trades: research/strategies/live_algorithm.py's four
 * fields. Not the symbol, account, risk limits or broker -- those stay in
 * the deployment's file. */
export interface Algorithm {
  strategy_id: string;
  strategy_params: Record<string, ParamValue>;
  step: number | null;
  profit_target: number | null;
}

/** Who changed it from the config file's, how and when. */
export interface AlgorithmOverride {
  channel: "web" | "extension";
  changedAt: string | null;
  changedBy: string | null;
  reason: string | null;
  profile: string | null;
}

/** A committed profile (config/live_profiles/), and whether THIS deployment
 * may switch to it. */
export interface ProfileRow extends Algorithm {
  id: string;
  label: string;
  symbols: string[];
  evidence: Record<string, unknown>;
  /** Carries a passing paper promotion: what real money needs. */
  promoted: boolean;
  /** How it was promoted: a paper trial's pass, or the owner's own sign-off. */
  promotion_kind?: "paper" | "manual" | null;
  usable: boolean;
  why: string | null;
}

/** A strategy, its parameter schema, and whether it can trade live HERE
 * (its own live rules against this deployment's settings). */
export interface StrategyRow {
  id: string;
  params: Param[];
  live_capable: boolean;
  why: string | null;
}

export interface AlgorithmView {
  editable: boolean;
  /** Real money: committed profiles only. */
  profiles_only: boolean;
  paper: boolean;
  symbol: string;
  /** What is in force: the override if any, else the config file's. */
  current: Algorithm;
  config_file: Algorithm;
  source: "config" | "web" | "extension";
  override: AlgorithmOverride | null;
  /** What the running loop reports trading; null when none runs. */
  live: { strategy_id: string; step: number | null; profit_target: number | null } | null;
  /** Written but not yet traded: the loop switches at its next tick. */
  pending: boolean;
  profiles: ProfileRow[];
  strategies: StrategyRow[];
}

/** What a switch does to the open book. Lots keep the targets they were
 * bought at; what can change for them is whether a signal exit applies. */
export type LegacyLots = "keep" | "exit_at_cost" | "wait";

export interface Impact {
  open_lots: number;
  /** What the dry run assumed for the lots held now. */
  legacy_lots?: LegacyLots;
  cost: number;
  lots_at_new_target: number;
  signal_exit_before: boolean;
  signal_exit_after: boolean;
  notes: string[];
}

export interface ChangeCheck {
  ok: boolean;
  errors: string[];
  change?: Algorithm;
  current?: Algorithm;
  impact?: Impact;
  /** Why the id must be typed back to send it, or null. */
  typed?: string | null;
  legacy_lots?: LegacyLots;
}

/** A switch to check or send: a committed profile, or (paper) the change. */
export interface ChangeRequest {
  profile_id?: string;
  strategy_id?: string;
  strategy_params?: Record<string, ParamValue>;
  step?: number;
  profit_target?: number;
  /** What to do with the lots held at the switch. Default keep. */
  legacy_lots?: LegacyLots;
}
