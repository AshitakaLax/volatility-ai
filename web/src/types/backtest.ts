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
  grid_step_pct: number | null;
  profit_target_pct: number | null;
  /** A `strategy_id` from `src/strategy_registry.py`. */
  sizing_model: string;
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

/** Chart aggregation. The engine runs on 1Min; the rest are rollups. */
export type Timeframe = "1Min" | "5Min" | "15Min" | "1Hour" | "1Day";

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
  timeframe: Timeframe;
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
  timeframe: "1Day",
  range: { start: null, end: null },
  status: "all",
  rsiMin: null,
  rsiMax: null,
  tickers: [],
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
  tickers: string[];
  grid_steps: number[];
  profit_targets: number[];
  sizing_model: string;
  strategy_params?: Record<string, number | string | boolean>;
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
  status: RunStatus;
  /** 0-1. Coarse: the server reports per-configuration completion. */
  progress: number;
  message: string | null;
  report: MultiFundBacktestReport | null;
  error: string | null;
}
