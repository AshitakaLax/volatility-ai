/**
 * The backtesting wire contract.
 *
 * These mirror what `tools/export_ui_data.py` actually emits, which is
 * in turn what `server/backtest.py` will serialise from the same
 * helpers. They were written against a real exported run rather than
 * from the spec alone, so the optionality below reflects what the
 * engine genuinely does or does not produce.
 *
 * WHY SO MANY FIELDS ARE OPTIONAL. Three different absences are
 * modelled here and they mean different things:
 *
 *   - `rsi_at_entry` is absent while the 14-period window is seeding.
 *     Not zero: a zero would filter as "extremely oversold" and drag
 *     every early trade into an RSI<30 query, which is exactly
 *     backwards.
 *   - `matched_buy_id` / `profit_realized` / `sell_reason` exist only on
 *     sells. A buy has not realised anything yet.
 *   - Metric fields are always present but may be 0 on a run that
 *     produced no closed trades, which is a real outcome rather than an
 *     error.
 */

/** Which side of the book, as the engine records it. */
export type ExecutionSide = "BUY" | "SELL";

/**
 * Why a lot was sold.
 *
 * `signal_exit` is the ONE path in this system permitted to realise a
 * loss (see `src/no_loss_guard.py`), which is why a UI should be able to
 * tell the two apart: a red marker on a signal exit is information, the
 * same marker on a profit target would be a bug.
 */
export type SellReason = "profit_target" | "signal_exit";

/** One fill. Buys and sells share the shape; sells carry more. */
export interface BacktestExecution {
  /**
   * Unique per fill. Derived as `${lot_id}-${side}-${bar_index}` because
   * the lot id alone is NOT unique across a lot's rows -- one buy and
   * possibly several partial sells share it. Use `matched_buy_id` to
   * join a sell back to its buy, never this.
   */
  order_id: string;
  ticker: string;
  type: ExecutionSide;
  price: number;
  shares: number;
  /** ISO 8601, timezone-aware. */
  timestamp: string;
  /** Absent during the indicator's warmup window -- see the note above. */
  rsi_at_entry?: number;
  /** Sells only: the lot id this fill closed. The cycle-connector join key. */
  matched_buy_id?: string;
  /**
   * Sells only. This is `economics.realized_pnl` -- the same figure the
   * no-loss guard computes -- and it CAN be negative on a signal exit.
   * It is deliberately not `(target - basis) * qty`, which would report
   * every trade as a winner.
   */
  profit_realized?: number;
  /** Sells only. */
  sell_reason?: SellReason;
}

/**
 * One fund's summary metrics.
 *
 * NOTE ON THE TWO VELOCITY MEASURES. They are different numbers and are
 * deliberately not merged:
 *
 *   capital_velocity_index   closed / TOTAL lots. The engine's default
 *                            ranking metric; every sweep result in the
 *                            project README is ordered by it.
 *   harvest_to_stuck_ratio   closed / STUCK lots. Completed cycles per
 *                            lot still waiting on the market.
 */
export interface FundPerformanceMetrics {
  ticker: string;
  net_yield_pct: number;
  cagr_pct: number;
  max_drawdown_pct: number;
  sharpe_ratio: number;
  sortino_ratio: number;
  /** Gross profit / gross loss. With no losing trade this is the gross
   * profit rather than Infinity, which does not survive JSON. */
  profit_factor: number;
  win_rate_pct: number;
  max_consecutive_losses: number;
  /** Capital tied up in open inventory at the final mark -- the real
   * cost of the no-loss invariant. */
  stuck_capital_value: number;
  capital_velocity_index: number;
  harvest_to_stuck_ratio: number;
  /** In bars, from a lot's first buy to its last sell. */
  avg_hold_duration: number;
  /**
   * Calendar-year extremes.
   *
   * The worst year is the one this project keeps returning to: a
   * strategy is judged on the year it does worst, not on a ten-year
   * average a single 2020 can carry.
   *
   * Optional because a report exported before these existed must still
   * render rather than crashing the page.
   */
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
 * Daily equity, plus the normalised form the overlay chart needs.
 *
 * `normalized` is rebased to 100 at the first point. That is what makes
 * two funds with different starting prices comparable on one axis, and
 * it is the entire purpose of the multi-fund view.
 *
 * The three arrays are parallel and equal-length.
 */
export interface EquitySeries {
  /** `YYYY-MM-DD`. */
  dates: string[];
  equity: number[];
  normalized: number[];
}

/** The span of bars a run actually saw. */
export interface BarWindow {
  start: string;
  end: string;
  count: number;
}

/**
 * One cell of the parameter sweep.
 *
 * Metrics only, deliberately. Carrying each configuration's executions
 * would multiply the payload by the size of the grid to draw a heatmap
 * that needs one number per cell.
 */
export interface SweepConfiguration {
  grid_step: number;
  profit_target: number;
  /** The resolved strategy-param combo THIS cell ran with -- distinct
   * per cell once a strategy param is swept. `{}` for a report predating
   * this field. */
  strategy_params: Record<string, ParamValue>;
  metrics: FundPerformanceMetrics;
}

export interface FundResult {
  metrics: FundPerformanceMetrics;
  /** May be empty: a low-volatility fund on a grid tuned for a 3x one
   * legitimately never trades. Render "no executions", not an error. */
  executions: BacktestExecution[];
  equity_curve: EquitySeries;
  /**
   * Every combination run, ranked by the engine's own default metric.
   * Index 0 is the same configuration `metrics` above describes.
   *
   * Optional because a static export predating this field must still
   * render -- the matrix hides rather than the page failing.
   */
  configurations?: SweepConfiguration[];
  bars: BarWindow;
}

/** The parameters a run was produced under. */
export interface BacktestParameters {
  /** The label the run was submitted with, or null if it was unnamed.
   * Descriptive only -- see `BacktestRunRequest.name`. */
  name?: string | null;
  grid_step_pct: number | null;
  profit_target_pct: number | null;
  /** A `strategy_id` from `src/strategy_registry.py`. */
  sizing_model: string;
  /**
   * The RESOLVED sizing-model arguments -- what the engine was built
   * with after defaults were filled in and `target_return` was aligned
   * to the grid. Absent on a report predating this field.
   *
   * A value is a LIST when that argument was swept (server-side
   * `expand_strategy_params`): the run-level snapshot then shows every
   * value that argument took across the whole sweep, while each
   * `SweepConfiguration.strategy_params` cell shows only the one
   * combination that produced it.
   */
  strategy_params?: Record<string, ParamValue | ParamValue[]>;
  /** "close" requires the bar's CLOSE to reach a level; "intrabar" fills
   * a level TOUCHED during the bar -- roughly 1.85x more fills. */
  fill_model: string;
  enforce_no_loss: boolean;
  /**
   * Workers the run ACTUALLY used, not what was asked for.
   *
   * 1 is normal and often correct: below roughly 500k bar-configurations
   * a process pool measured SLOWER than serial on Windows, where every
   * worker is a fresh interpreter that re-imports pandas.
   */
  n_jobs?: number;
}

export interface BacktestTimeframe {
  start: string | null;
  end: string | null;
  interval: string;
}

/** The top-level payload. One run, one or more funds. */
export interface MultiFundBacktestReport {
  run_id: string;
  parameters: BacktestParameters;
  timeframe: BacktestTimeframe;
  funds: Record<string, FundResult>;
}

/* ------------------------------------------------------------------ */
/* Client-side view state                                             */
/* ------------------------------------------------------------------ */

/** Candle-aggregation buckets. The engine runs on 1Min; the rest are
 * rollups. */
export type Timeframe = "1Min" | "5Min" | "15Min" | "1Hour" | "1Day";

/**
 * The Execution chart's zoom level. Each caps how wide a window it will
 * pull so the payload stays small and the resolution stays REAL rather
 * than a server downsample of the whole run:
 *
 *   "1d"  daily candles over the whole backtest
 *   "1h"  hourly candles, at most a 10-day window
 *   "1m"  minute candles, at most a 2-day window
 */
export type ChartResolution = "1d" | "1h" | "1m";

/**
 * "Stuck" is this project's word for an open lot: capital committed and
 * not yet returned, because the grid only sells at a profit.
 */
export type OrderStatusFilter = "all" | "stuck" | "closed";

export interface DateRange {
  start: string | null;
  end: string | null;
}

export interface ExecutionFilters {
  /** The Execution chart's zoom level. Persisted here (not local to the
   * chart) so it survives a tab switch, like the rest of the view. */
  chartResolution: ChartResolution;
  range: DateRange;
  status: OrderStatusFilter;
  /** Inclusive bounds. Executions with no `rsi_at_entry` are excluded
   * when either bound is set -- unknown is not the same as in-range. */
  rsiMin: number | null;
  rsiMax: number | null;
  /** Empty means no restriction, not "no funds". */
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

/** An inclusive numeric band. `null` on an end means "unbounded". */
export interface NumericRange {
  min: number | null;
  max: number | null;
}

/**
 * A view filter over the flattened run-history table.
 *
 * Categorical fields (`tickers`, `models`, `fillModels`) are
 * OR-within / AND-between: an empty list is no restriction, a non-empty
 * one keeps rows whose value is in it.
 *
 * Numeric fields are addressed by a NAMESPACED key so an input argument
 * and a result metric can never collide:
 *
 *   `grid_step`, `profit_target`   the swept dimensions, in PERCENT
 *   `param:<name>`                 a numeric sizing-model argument
 *   `metric:<key>`                 a `FundPerformanceMetrics` field
 *
 * Each numeric field carries both a set of exact values to keep
 * (`values`) and a band (`ranges`); a row passes when it satisfies
 * whichever of the two is set (OR), so "1% or 1.5%" and "0.5%–2%" are
 * both expressible and setting neither leaves the field open. A row that
 * does not have the field at all is excluded once the field is gated --
 * unknown is not a match, the same rule the RSI filter follows.
 */
export interface RunHistoryFilters {
  /** Case-insensitive substring over the run name. "" = no restriction;
   * a row with no name drops out once this is non-empty. */
  name: string;
  tickers: string[];
  models: string[];
  fillModels: string[];
  /** Namespaced field key -> exact values to keep. Empty list / absent
   * key = no restriction. */
  values: Record<string, number[]>;
  /** Namespaced field key -> inclusive band. Absent key = no
   * restriction. */
  ranges: Record<string, NumericRange>;
  /**
   * Optional numeric fields the reader has ADDED to the panel (a
   * sizing-model argument, a result metric) but may not have typed a
   * bound into yet. Purely presentational -- `filterHistoryRows`
   * ignores it -- so a freshly added field does not vanish before it
   * is used, and stays put while its inputs are cleared and retyped.
   * `grid_step` and `profit_target` are always shown and never listed
   * here.
   */
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

/**
 * A submitted run, for the bidirectional half of the UI.
 *
 * One engine run costs roughly 23 seconds on ten years of minute bars,
 * so a run is a JOB: the POST returns an id and progress arrives over a
 * WebSocket. A synchronous request would time out.
 */
export type RunStatus = "queued" | "running" | "complete" | "failed";

export interface BacktestRunRequest {
  /**
   * An optional human label for the run, carried through to the report
   * and the history table. Purely descriptive -- the engine never reads
   * it -- so a sweep can be found later by "what it was for" rather than
   * only by its 12-hex id.
   */
  name?: string;
  tickers: string[];
  grid_steps: number[];
  profit_targets: number[];
  sizing_model: string;
  /** A value is a list to sweep that argument -- server/backtest.py's
   * `expand_strategy_params` cross-products it against grid_steps and
   * profit_targets, exactly like those two already sweep. */
  strategy_params?: Record<string, ParamValue | ParamValue[]>;
  fill_model?: "close" | "intrabar";
  enforce_no_loss?: boolean;
  /** ISO date, inclusive. Applied BEFORE the bar cap. */
  start?: string;
  /** ISO date, inclusive of the whole day. */
  end?: string;
  /** Cap on bars fed to the engine. A full file is a million rows. */
  limit?: number;
}

/** One OHLC bar from /api/backtest/bars, already downsampled. */
export interface PriceBar {
  /** Epoch seconds. */
  time: number;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

export interface BarSeries {
  ticker: string;
  /** The bucket the server rolled up to, so the UI can say so. */
  bucket_seconds: number;
  /** How many 1-minute rows went in. */
  source_rows: number;
  bars: PriceBar[];
}

export interface BacktestRunState {
  run_id: string;
  /** The label this run was submitted with, echoed on the job snapshot
   * so an in-flight run can be shown by name before its report exists.
   * null for an unnamed run. */
  name?: string | null;
  status: RunStatus;
  /** 0-1. Coarse: the server reports per-configuration completion. */
  progress: number;
  message: string | null;
  report: MultiFundBacktestReport | null;
  error: string | null;
  /**
   * The submitted request, echoed back on the job snapshot -- present
   * for a QUEUED or RUNNING job too, not just a completed one, so a
   * client can describe what a sweep covers (tickers, grid, strategy
   * params) before it has a report to read that from. Optional only
   * for a server predating this field. A narrow shape: only what
   * ActiveRuns/requestSummary.ts actually read, not every RunRequest
   * field (start/end/limit/n_jobs/enforce_no_loss are on the wire too,
   * just not carried through this type).
   */
  request?: {
    tickers: string[];
    grid_steps: number[];
    profit_targets: number[];
    sizing_model: string;
    strategy_params?: Record<string, ParamValue | ParamValue[]>;
    fill_model?: string;
  };
}

/* ------------------------------------------------------------------ */
/* History                                                            */
/* ------------------------------------------------------------------ */

/**
 * One row of the history table: a (run, fund, grid step, target) tuple.
 *
 * Flattened server-side because "rank the runs" is the wrong shape --
 * a run holds several funds and each fund several configurations, and
 * the comparable thing is a single configuration's metrics.
 */
export interface HistoryRow {
  run_id: string;
  /** The label the run was submitted with; null for older or unnamed
   * runs. Repeated on every row of a run because the table is flattened
   * to one row per configuration. */
  name: string | null;
  /** Epoch seconds, from the stored file's mtime. */
  saved_at: number | null;
  ticker: string;
  grid_step: number | null;
  profit_target: number | null;
  sizing_model: string | null;
  /** The resolved sizing-model arguments THIS ROW's cell ran with (or,
   * for a report predating per-cell values, the run-level snapshot).
   * `{}` for a run archived before either existed. */
  strategy_params: Record<string, ParamValue>;
  fill_model: string | null;
  /** Where the ENGINE ranked this cell; 0 is its own pick. Lets a
   * reader see when their chosen metric disagrees with it. */
  engine_rank: number;
  start: string | null;
  end: string | null;
  bars: number | null;
  metrics: FundPerformanceMetrics;
}

/* ------------------------------------------------------------------ */
/* Dynamic sizing-model parameters                                    */
/*                                                                    */
/* `GET /api/backtest/funds` carries `sizing_params[id].params` -- one */
/* spec per constructor argument of every sizing model -- so the      */
/* "Run a backtest" form can render exactly that model's inputs and   */
/* swap them when the model changes. Mirrors server/backtest.py's     */
/* `describe_params()`; `sizing_details` still carries the older      */
/* `required` / `defaults` shape for its existing consumers.          */
/* ------------------------------------------------------------------ */

/** A concrete parameter value on the wire. `null` is never sent -- a
 * blank field is omitted from `strategy_params` entirely. */
export type ParamValue = number | string | boolean;

export interface ParamSpec {
  /** Constructor keyword. The exact key the form puts in `strategy_params`. */
  name: string;
  /** Drives the widget and the client-side parse. `bool` is a two-option
   * select; `int` steps by 1; `str` is free text unless `enum` is set. */
  type: "float" | "int" | "bool" | "str";
  /** May legitimately be left blank (annotation admits `None`, or the
   * constructor default is `None`). A blank non-nullable required field
   * blocks the run. */
  nullable: boolean;
  /** No constructor default -- must be supplied. */
  required: boolean;
  /** The bare constructor default, or `null` when required / when the
   * real default is `None`. */
  default: ParamValue | null;
  /** What the field is seeded to and what "reset" restores: the
   * project's committed value when there is one, else `default`. */
  suggested: ParamValue | null;
  /** `name` came from a committed project config -> shown in Primary and
   * counted in the "differs from committed defaults" readout. */
  has_suggested: boolean;
  /** Closed choice set for a `str` field (today: `vol_measure`); render
   * a `<select>`. `null` otherwise. */
  enum: string[] | null;
  group: "primary" | "advanced";
  /** `false` -> render disabled with `locked_reason`; the engine owns
   * this value (derived at run time, or set by the server). */
  editable: boolean;
  locked_reason: string | null;
  /** Non-null only for `bayesian_dual_scale.target_return`: the form
   * shows it tracking the Profit target field and NEVER sends it -- the
   * server aligns it to the grid's single profit target. */
  mirrors: "profit_target" | null;
  /** Suggested `<input type="number" step>`: `"1"` for int, `"any"` for
   * float, `null` for bool/enum/str. Advisory -- the server bounds it. */
  step: string | null;
  /** Whether the "enable sweep" checkbox may render for this argument --
   * `editable && mirrors === null && (type in ("int","float") || enum)`.
   * A locked (engine-owned) or grid-mirrored value cannot also be
   * independently swept.
   *
   * TWO SWEEPABLE SHAPES, dispatched on `enum` at render time (mirrors
   * server/backtest.py's own `describe_params`, which is why there is no
   * separate `sweep_kind` field -- `enum` already says which this is,
   * since a `_PARAM_ENUMS` field is never typed int/float):
   *   RANGE   int/float, enum === null -- SweepableParamField's
   *           min/max/count/strategy generator (lib/sweepStrategies.ts).
   *   OPTIONS str with enum set -- OptionsSweepField's checklist of
   *           which of `enum`'s own values to include
   *           (lib/strategyParams.ts's buildOptionsSweep).
   * A plain `str` (no enum) or a `bool` is never sweepable -- neither
   * has a bounded set of named options to check boxes for. */
  sweepable: boolean;
}

export interface SizingParamsEntry {
  params: ParamSpec[];
}

/* ------------------------------------------------------------------ */
/* Grid-step trigger method                                           */
/*                                                                    */
/* `/funds` carries `grid_trigger[id]` -- which methods a sizing model */
/* supports for deciding WHEN a grid buy fires. Mirrors                */
/* server/backtest.py's `describe_grid_trigger()`.                     */
/* ------------------------------------------------------------------ */

/** "last_buy": level = last_buy_price × (1 − step) (a fresh low below
 * the last fill). "local_reference": level = max(last_buy_price,
 * rolling_high) × (1 − step) (retriggers on any local pullback).
 * "regime_widened": last_buy's formula with the STEP multiplied by a
 * model-driven latch — the reference is still the last fill, but the
 * spacing widens while a regime model reads crash. Always locked; the
 * widening is what the strategy is, not an operator choice. */
export type GridTriggerMethod = "last_buy" | "local_reference" | "regime_widened";

export interface GridTrigger {
  /** Supported methods in display order; index 0 is the default. A
   * single-entry list renders as a locked (disabled) control. */
  methods: GridTriggerMethod[];
  default: GridTriggerMethod;
  /** The strategy_param whose PRESENCE selects `local_reference`. null
   * when the method is locked. */
  controlled_by: string | null;
  /** The strategy_param that IS the rolling-high window (set for
   * hf_local_reference and bayesian_dual_scale; null elsewhere -- so
   * bell_curve's Gaussian-window `lookback_days` is never mistaken for
   * a trigger window). */
  window_param: string | null;
  /** Value written to `window_param` the first time `local_reference`
   * is picked. null when it seeds itself. */
  window_default: number | null;
}

/** The fallback for a model an older server did not describe: last_buy
 * only, no window, no choice -- today's behaviour. */
export const GENERIC_GRID_TRIGGER: GridTrigger = {
  methods: ["last_buy"],
  default: "last_buy",
  controlled_by: null,
  window_param: null,
  window_default: null,
};

/** One reason a would-be run is invalid, attached to a field when the
 * server can pin it there. */
export interface ValidateError {
  field: string | null;
  message: string;
}

export interface ValidateResponse {
  ok: boolean;
  /** What the engine would build with -- defaults filled in,
   * `target_return` aligned. `null`/absent when invalid. A value is a
   * list when that argument was submitted as a sweep. */
  resolved_strategy_params?: Record<string, ParamValue | ParamValue[]> | null;
  /** The subset the server set or changed vs. what was submitted. */
  aligned?: Record<string, ParamValue>;
  errors: ValidateError[];
  /** Set by the client when the server has no `/validate` route yet
   * (older deployment mid-rollout): treated as "not blocking". */
  degraded?: boolean;
}
