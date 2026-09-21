/**
 * The backtesting wire contract, mirrored by hand from server/backtest.py
 * (and tools/export_ui_data.py, whose serialisers it reuses).
 *
 * CONDENSED ON PURPOSE. Run-level fields are stated once (RunMeta), a
 * fund's headline metrics are its first cell, flags that are false or
 * null are omitted, and anything the client can derive exactly is not
 * sent. Archived runs written in the old shape are translated on the
 * server (server/contract.py), so nothing here hedges for them.
 *
 * THREE ABSENCES THAT MEAN DIFFERENT THINGS:
 *   - Fill.rsi is absent while the 14-period window seeds. Not 0: a zero
 *     would filter as "extremely oversold" and drag every early trade
 *     into an RSI<30 query.
 *   - Fill.pnl / Fill.why exist only on sells. A buy has realised nothing.
 *   - Metrics are always present but may be 0 on a run with no closed
 *     trades -- a real outcome, not an error.
 */

/** A concrete parameter value. `null` is never sent -- blank is omitted. */
export type ParamValue = number | string | boolean;
export type Params = Record<string, ParamValue>;
/** A list value is a SWEPT argument (server-side expand_strategy_params). */
export type SweptParams = Record<string, ParamValue | ParamValue[]>;

/** Every WebSocket frame: `data` carries the payload, `hb` says the
 * connection is alive while nothing changed, `err` is reported in-band. */
export type Frame<T> = { t: "data"; d: T } | { t: "hb" } | { t: "err"; msg: string };

/* ------------------------------------------------------------------ */
/* Report                                                             */
/* ------------------------------------------------------------------ */

/**
 * One configuration's metrics.
 *
 * capital_velocity_index is closed / TOTAL lots (the engine's default
 * ranking); harvest_to_stuck_ratio is closed / STUCK lots. Different
 * numbers, deliberately not merged. profit_factor with no losing trade
 * is the gross profit, not Infinity (which does not survive JSON). The
 * calendar-year fields are optional for a report archived before them.
 */
export interface Metrics {
  net_yield_pct: number;
  cagr_pct: number;
  max_drawdown_pct: number;
  sharpe_ratio: number;
  sortino_ratio: number;
  profit_factor: number;
  win_rate_pct: number;
  max_consecutive_losses: number;
  /** Capital tied up in open inventory at the final mark -- the real cost
   * of the no-loss invariant. */
  stuck_capital_value: number;
  capital_velocity_index: number;
  harvest_to_stuck_ratio: number;
  /** In bars, first buy to last sell. */
  avg_hold_duration: number;
  /** A strategy is judged on its worst year, not a ten-year average. */
  worst_year_pct?: number;
  best_year_pct?: number;
  avg_annual_pct?: number;
  return_over_drawdown?: number;
  total_trades: number;
  closed_trades: number;
  open_trades: number;
  /** Sells permitted to realise a loss. 0 unless signal exits are on. */
  signal_exits: number;
  final_equity: number;
}

/**
 * Why a lot was sold. `signal_exit` is the ONE path permitted to realise a
 * loss (src/trading/no_loss_guard.py): a red marker on it is information,
 * on a profit target it would be a bug.
 */
export type SellReason = "profit_target" | "signal_exit";

/** One fill. A fund's fills live under its ticker, so they carry none. */
export interface Fill {
  /** The lot this fill opened or closed -- a sell joins its buy on it.
   * Not unique alone (one buy, possibly several partial sells); the key
   * is (lot, side, i) -- see lib/filters.ts fillKey. */
  lot: string;
  side: "BUY" | "SELL";
  /** Bar index of the fill. */
  i: number;
  px: number;
  qty: number;
  /** ISO 8601, timezone-aware. */
  ts: string;
  /** Absent during the indicator warmup -- never 0. */
  rsi?: number;
  /** Sells only: economics.realized_pnl, the no-loss guard's own figure.
   * CAN be negative on a signal exit -- deliberately not
   * (target - basis) * qty, which would report every trade a winner. */
  pnl?: number;
  why?: SellReason;
}

/** One cell of the sweep: metrics only -- carrying each cell's fills
 * would multiply the payload by the grid to draw one number per cell. */
export interface Cell {
  grid: number | null;
  target: number | null;
  /** The resolved combination THIS cell ran with. */
  params: Params;
  m: Metrics;
}

export interface Fund {
  /** Every configuration, ranked by the engine. cells[0] is the one
   * `fills` and `equity` come from, and its `m` is the fund's headline. */
  cells: Cell[];
  /** May be empty: a low-volatility fund on a grid tuned for a 3x one
   * legitimately never trades. Render "no executions", not an error. */
  fills: Fill[];
  /** Daily, parallel arrays. The overlay chart rebases to 100 itself
   * (FundComparison), so that form is not sent. */
  equity: { dates: string[]; equity: number[] };
  /** The span of bars the run actually saw. */
  bars: { start: string; end: string; count: number };
}

/** Run-level fields, stated once -- shared by a Report and History. */
export interface RunMeta {
  /** The submitted label, trimmed; null when unnamed. Descriptive only. */
  name: string | null;
  /** A `strategy_id` from src/trading/strategy_registry.py. */
  model: string | null;
  /** "close" needs the bar's CLOSE to reach a level; "intrabar" fills a
   * level TOUCHED during the bar -- roughly 1.85x more fills. */
  fill: string | null;
  no_loss: boolean;
  /** RESOLVED arguments (defaults filled, target_return aligned); a list
   * where the argument was swept, showing every value it took. */
  params: SweptParams;
  /** The headline cell's grid step / profit target. */
  grid: number | null;
  target: number | null;
  /** Workers the run ACTUALLY used. 1 is often right: below ~500k
   * bar-configurations a pool measured SLOWER than serial on Windows. */
  jobs?: number;
  start: string | null;
  end: string | null;
  interval: string;
  /** A sweep too large for one submission is split into independent
   * chunks that share a batch_id; batch_total is 1 for the common,
   * unsplit case. Absent on a run archived before batching existed. */
  batch_id?: string | null;
  batch_index?: number;
  batch_total?: number;
}

/** One run, one or more funds. */
export interface Report extends RunMeta {
  id: string;
  funds: Record<string, Fund>;
}

/* ------------------------------------------------------------------ */
/* Runs                                                               */
/* ------------------------------------------------------------------ */

/**
 * A submission. One engine run is ~23 seconds on ten years of minute
 * bars, so a run is a JOB: the POST returns its snapshot and progress
 * arrives over a WebSocket.
 */
export interface RunReq {
  /** An optional label, carried to the report and history. Never read by
   * the engine. */
  name?: string;
  tickers: string[];
  grid_steps: number[];
  targets: number[];
  model?: string;
  /** Omitted or {} -> the model's committed defaults. A list sweeps that
   * argument, cross-producted with grid_steps x targets. */
  params?: SweptParams;
  fill?: "close" | "intrabar";
  no_loss?: boolean;
  /** ISO date, inclusive. Applied BEFORE the bar cap. */
  start?: string;
  /** ISO date, inclusive of the whole day. */
  end?: string;
  /** Cap on bars fed to the engine. A full file is a million rows. */
  limit?: number;
  jobs?: number;
  /** Present: sample `trials` combinations with Optuna's TPE instead of
   * running them all -- the same engine `cli.py search` drives. A trial
   * budget is REQUIRED; the server refuses a bayesian run without one. */
  bayes?: { trials: number; seed?: number };
  /** The objective Optuna optimises AND the column cells are sorted by.
   * Restricted to columns the engine's per-combination metrics carry --
   * "Sharpe Ratio" is display-only and not valid here. */
  rank_by?: string;
  minimize?: boolean;
  /** ECHO ONLY -- stamped by the server (POST /runs), never sent by the
   * client. A sweep too large for one submission is bisected into
   * independent chunks that share a batch_id; batch_total is 1 for the
   * common, unsplit case. See SubmitResponse. */
  batch_id?: string;
  batch_index?: number;
  batch_total?: number;
}

/**
 * "pausing" / "cancelling": a stop asked of a RUNNING run that lands once
 * the configurations already in the process pool finish (up to about a
 * minute). "paused" holds a place and resumes from its checkpoint;
 * "cancelled" is terminal.
 */
export type RunStatus =
  | "queued"
  | "running"
  | "pausing"
  | "cancelling"
  | "paused"
  | "cancelled"
  | "complete"
  | "failed";

export interface Run {
  id: string;
  status: RunStatus;
  /** 0-1, per configuration. */
  progress: number;
  /** 1-indexed place among queued + paused runs, in the order they will
   * run -- not submission order once anything moved. null otherwise. */
  pos: number | null;
  /** The shard running it ("local" is the engine host itself); null
   * unless running. Absent from servers that predate shards. */
  shard?: string | null;
  msg: string | null;
  error: string | null;
  /** The submission, echoed from the moment it is queued -- the name and
   * the sweep's shape are read from here before a report exists. */
  req: RunReq;
  report: Report | null;
}

/**
 * POST /api/backtest/runs's response. A sweep that fits under the
 * combination ceiling in one submission returns a plain Run, exactly as
 * every server has always returned -- backward compatible, and still
 * what most submissions get back. One too large for that is bisected
 * server-side into independent chunks that share a batch_id, each
 * queued as its own Run; every chunk's own req.batch_id/batch_index/
 * batch_total agree with this wrapper's own fields. lib/runBatches.ts
 * groups Run[] back into batches for display.
 */
export type SubmitResponse = Run | { batch_id: string; runs: Run[] };

/** A queue control. `pos` is 0-based among pending runs with this one
 * taken out; see lib/runQueue.ts moveTarget. */
export type RunOp = { op: "pause" | "resume" | "cancel" | "next" } | { op: "move"; pos: number };

/* ------------------------------------------------------------------ */
/* Shards                                                             */
/* ------------------------------------------------------------------ */

/**
 * "stale": no heartbeat for `stale_s`; "offline": none for `timeout_s`,
 * and whatever it was running has been handed to another shard.
 */
export type ShardConn = "online" | "stale" | "offline";

/** "pausing": paused (manually, or by its own lockout window opening)
 * while a sweep is still finishing its in-flight configurations; that
 * sweep then goes back to the queue. "locked_out": idle and currently
 * inside its own configured window, but never manually paused --
 * `paused` stays false throughout, since a schedule and a manual pause
 * are independent facts (server/jobs.py's "LOCKOUT WINDOWS" doc). */
export type ShardState = "idle" | "running" | "pausing" | "paused" | "locked_out";

/** A daily lockout window, server-local wall-clock time. `start`/`end`
 * are "HH:MM" (24-hour); both set whenever either is, even if
 * `enabled` is false -- disabling keeps them for next time, distinct
 * from clearing (server returns `null` for a cleared window). */
export interface ShardSchedule {
  enabled: boolean;
  start: string | null;
  end: string | null;
}

/** One machine working the backtest queue (server/jobs.py `Shard`). */
export interface Shard {
  name: string;
  /** The engine host's own worker. Always online; cannot be forgotten. */
  local: boolean;
  conn: ShardConn;
  state: ShardState;
  host: string | null;
  commit: string | null;
  dirty: boolean | null;
  cores: number | null;
  /** Seconds since its last heartbeat. 0 for the local shard. */
  seen_s: number;
  /** Epoch seconds it registered. */
  since: number;
  /** The manual toggle only -- independent of `locked_out`. */
  paused: boolean;
  /** Whether its configured lockout window covers this instant. */
  locked_out: boolean;
  /** Its configured lockout window, or null if it has none. */
  schedule: ShardSchedule | null;
  run: { id: string; name: string | null; progress: number; msg: string | null } | null;
}

export interface ShardList {
  shards: Shard[];
  /** Every shard is paused (or pausing). */
  paused: boolean;
  /** The engine host's commit; a shard on another one is flagged. */
  commit: string | null;
  stale_s: number;
  timeout_s: number;
}

export type ShardOp = { op: "pause" | "resume" | "forget" };

/** One thing wrong with a would-be run; `field` when it can be pinned. */
export interface ValidateError {
  field?: string;
  msg: string;
}

/** A dry run of submit's own validation. Valid exactly when `errors` is
 * empty. */
export interface Validation {
  errors: ValidateError[];
  /** What the engine would build with. Absent when invalid. */
  resolved?: SweptParams;
  /** The subset the server set or changed vs. what was submitted. */
  aligned?: Params;
  /** Client-only: the server had no /validate route (404), so validation
   * falls back to submit time rather than blocking the form. */
  degraded?: boolean;
}

/* ------------------------------------------------------------------ */
/* History                                                            */
/* ------------------------------------------------------------------ */

/** GET /history: run-level fields once, then one row per cell. */
export interface History {
  runs: Record<string, RunMeta & { saved_at: number | null }>;
  rows: (Cell & { run: string; ticker: string; rank: number; bars: number | null })[];
}

/**
 * One row of the history table as the client uses it: a cell joined with
 * the run-level fields it is filtered and sorted on (lib/api.ts history).
 * `rank` is where the ENGINE ranked the cell; 0 is its own pick.
 */
export interface HistoryRow extends Cell {
  run: string;
  ticker: string;
  rank: number;
  bars: number | null;
  name: string | null;
  model: string | null;
  fill: string | null;
  start: string | null;
  end: string | null;
  /** Epoch seconds, from the stored file's mtime. */
  saved_at: number | null;
  /** Absent on a run archived before batching existed. */
  batch_id: string | null;
  batch_index: number | null;
  batch_total: number | null;
}

/* ------------------------------------------------------------------ */
/* Catalog: funds, and each sizing model's parameters                 */
/* ------------------------------------------------------------------ */

/**
 * One constructor argument, as sent. Omitted flags are false; `suggested`
 * is present only when the project has a committed value for it.
 */
export interface Param {
  /** Constructor keyword -- the exact key put in `params`. */
  name: string;
  type: "float" | "int" | "bool" | "str";
  /** The bare constructor default; null when required or when it is None. */
  default: ParamValue | null;
  /** The committed value the field is seeded to and "reset" restores. */
  suggested?: ParamValue;
  /** No constructor default -- must be supplied. Never also nullable. */
  required?: true;
  /** May be left blank. */
  nullable?: true;
  /** A closed choice set for a `str` field; render a select. */
  enum?: string[];
  /** Present when the engine owns the value (derived at run time, or set
   * by the server): the reason, shown on the disabled field. */
  locked?: string;
  /** bayesian_dual_scale.target_return tracks the Profit target field and
   * is NEVER sent -- the server aligns it to the grid. */
  mirrors?: "profit_target";
}

/**
 * A Param with the fields the form derives filled in -- what the form
 * components read. Built by lib/strategyParams.ts paramSpec.
 */
export interface ParamSpec {
  name: string;
  type: Param["type"];
  nullable: boolean;
  required: boolean;
  default: ParamValue | null;
  /** `suggested ?? default`. */
  suggested: ParamValue | null;
  /** From a committed config -> Primary, and counted in the "differs from
   * committed defaults" readout. */
  has_suggested: boolean;
  enum: string[] | null;
  /** "primary" exactly when required or committed. */
  group: "primary" | "advanced";
  editable: boolean;
  locked_reason: string | null;
  mirrors: "profit_target" | null;
  /** `<input step>`: "1" for int, "any" for float, null for bool/enum/str. */
  step: string | null;
  /**
   * Whether the "enable sweep" checkbox renders: editable, not mirrored,
   * and either int/float (a RANGE sweep, SweepableParamField) or enum (an
   * OPTIONS checklist, OptionsSweepField) -- dispatched on `enum`. A plain
   * str or a bool has no bounded set to sweep.
   */
  sweepable: boolean;
}

/**
 * When a grid buy fires.
 *   last_buy         level = last_buy_price x (1 - step)
 *   local_reference  level = max(last_buy_price, rolling_high) x (1 - step)
 *   regime_widened   last_buy's formula with the STEP widened by a model
 *                    latch while a regime model reads crash. Always locked.
 */
export type TriggerMethod = "last_buy" | "local_reference" | "regime_widened";

export interface Trigger {
  /** Display order; [0] is the default; a single entry is locked. */
  methods: TriggerMethod[];
  /** The param whose PRESENCE selects local_reference. */
  control?: string;
  /** The param that IS the rolling-high window (never bell_curve's
   * Gaussian lookback_days), and the value written the first time
   * local_reference is picked -- absent when it seeds itself. */
  window?: { param: string; seed?: number };
}

/** For a model the server did not describe: last_buy, no choice. */
export const GENERIC_TRIGGER: Trigger = { methods: ["last_buy"] };

/** GET /funds. */
export interface Catalog {
  /** Presence is reported rather than filtered, so a missing file can be
   * named (`cli.py fetch-data`). */
  funds: { ticker: string; path: string; ok: boolean }[];
  models: Record<string, { params: Param[]; trigger: Trigger }>;
}

/** One OHLCV bar: epoch seconds, open, high, low, close, volume. */
export type Bar = [t: number, o: number, h: number, l: number, c: number, v: number];

/** GET /api/backtest/bars (a server-side OHLC rollup) and /api/live/bars. */
export interface Bars {
  /** The bucket the server rolled up to, so the UI can say so. */
  bucket_s: number;
  /** How many 1-minute rows went in. */
  rows: number;
  /** Live only: the bar file, which can lag a running deployment. */
  source?: string;
  bars: Bar[];
}

/* ------------------------------------------------------------------ */
/* Client-side view state                                             */
/* ------------------------------------------------------------------ */

/** Candle-aggregation buckets. The engine runs on 1Min. */
export type Timeframe = "1Min" | "5Min" | "15Min" | "1Hour" | "1Day";

/**
 * The Execution chart's zoom. Each caps its window so the resolution is
 * REAL rather than a server downsample: "1d" whole run, "1h" at most 10
 * days, "1m" at most 2 days.
 */
export type ChartResolution = "1d" | "1h" | "1m";

/** "Stuck" is this project's word for an open lot. */
export type OrderStatusFilter = "all" | "stuck" | "closed";

export interface DateRange {
  start: string | null;
  end: string | null;
}

/** An inclusive band; `null` on an end means unbounded. */
export interface NumericRange {
  min: number | null;
  max: number | null;
}

export interface ExecutionFilters {
  /** Persisted here, not in the chart, so it survives a tab switch. */
  chartResolution: ChartResolution;
  range: DateRange;
  status: OrderStatusFilter;
  /** Inclusive. Fills with no `rsi` are excluded once either bound is
   * set -- unknown is not in range. */
  rsiMin: number | null;
  rsiMax: number | null;
  /** The fund being viewed; empty means the first. */
  tickers: string[];
}

export const DEFAULT_FILTERS: ExecutionFilters = {
  chartResolution: "1d",
  range: { start: null, end: null },
  status: "all",
  rsiMin: null,
  rsiMax: null,
  tickers: [],
};

/**
 * A filter over the history table. Categorical fields are OR-within,
 * AND-between; an empty list is no restriction.
 *
 * Numeric fields are keyed by a NAMESPACED name so an input and a result
 * can never collide: `grid_step` / `profit_target` (in PERCENT),
 * `param:<name>`, `metric:<key>`. Each keeps exact `values` and/or a
 * band in `ranges`; a row passes when either is satisfied, and a row lacking the
 * field is excluded once it is gated.
 */
export interface RunHistoryFilters {
  /** Case-insensitive substring over the run name. */
  name: string;
  tickers: string[];
  models: string[];
  fillModels: string[];
  /** Namespaced key -> exact values to keep. Empty/absent = open. */
  values: Record<string, number[]>;
  /** Namespaced key -> inclusive band. Absent = open. */
  ranges: Record<string, NumericRange>;
  /** Optional numeric fields ADDED to the panel but not yet bounded.
   * Presentational only -- filterHistoryRows ignores it. */
  extraFields: string[];
}

export const EMPTY_RUN_HISTORY_FILTERS: RunHistoryFilters = {
  name: "",
  tickers: [],
  models: [],
  fillModels: [],
  values: {},
  ranges: {},
  extraFields: [],
};
