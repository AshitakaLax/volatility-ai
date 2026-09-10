/**
 * Filtering and cycle-matching over a run's executions.
 *
 * Pure functions on purpose: this is where the only real logic in the
 * frontend lives, and logic that renders is logic nobody tests. Every
 * function here takes data and returns data, and filters.test.ts covers
 * the cases below that are easy to get quietly wrong.
 */
import type {
  BacktestExecution,
  ChartResolution,
  DateRange,
  ExecutionFilters,
  FundPerformanceMetrics,
  HistoryRow,
  OrderStatusFilter,
  RunHistoryFilters,
  Timeframe,
} from "@/types/backtest";

/** A buy and the sells that closed it. */
export interface TradeCycle {
  lotId: string;
  buy: BacktestExecution;
  /** Empty for a lot still open -- what this project calls "stuck". */
  sells: BacktestExecution[];
  /** Summed across partial sells. null while nothing has closed. */
  realized: number | null;
  open: boolean;
}

/**
 * Group executions into cycles by lot.
 *
 * A sell names its lot through `matched_buy_id`; a buy is identified by
 * the `lot_id` embedded in its `order_id` as `${lot}-buy-${bar}`. The
 * order_id is qualified that way because a lot id alone is NOT unique
 * across a lot's rows -- one buy and possibly several partial sells
 * share it -- so parsing it back out is how a buy is matched, and it is
 * done in exactly one place rather than at each call site.
 */
export function buildCycles(executions: BacktestExecution[]): TradeCycle[] {
  const buys = new Map<string, BacktestExecution>();
  const sells = new Map<string, BacktestExecution[]>();

  for (const execution of executions) {
    if (execution.type === "BUY") {
      const lotId = lotIdOf(execution);
      // FIRST buy wins. A lot has exactly one opening fill; if two rows
      // ever claimed the same lot, silently overwriting would move the
      // cycle's start and change every hold duration drawn from it.
      if (!buys.has(lotId)) buys.set(lotId, execution);
    } else if (execution.matched_buy_id) {
      const existing = sells.get(execution.matched_buy_id);
      if (existing) existing.push(execution);
      else sells.set(execution.matched_buy_id, [execution]);
    }
  }

  const cycles: TradeCycle[] = [];
  for (const [lotId, buy] of buys) {
    const closes = sells.get(lotId) ?? [];
    const realized = closes.reduce<number | null>(
      (total, sell) =>
        sell.profit_realized === undefined ? total : (total ?? 0) + sell.profit_realized,
      null,
    );
    cycles.push({ lotId, buy, sells: closes, realized, open: closes.length === 0 });
  }
  return cycles;
}

/** The lot id an execution belongs to. */
export function lotIdOf(execution: BacktestExecution): string {
  if (execution.type === "SELL" && execution.matched_buy_id) return execution.matched_buy_id;
  // "SIM-000008-buy-235" -> "SIM-000008". Split on the LAST occurrence,
  // since a lot id could itself contain the separator.
  const marker = execution.type === "BUY" ? "-buy-" : "-sell-";
  const index = execution.order_id.lastIndexOf(marker);
  return index === -1 ? execution.order_id : execution.order_id.slice(0, index);
}

/**
 * Which lots are still open, from the executions alone.
 *
 * Derived rather than read from a field, because the engine does not
 * mark an execution as belonging to an open lot -- open is simply the
 * absence of a matching sell.
 */
export function openLotIds(executions: BacktestExecution[]): Set<string> {
  const closed = new Set<string>();
  for (const execution of executions) {
    if (execution.type === "SELL" && execution.matched_buy_id) {
      closed.add(execution.matched_buy_id);
    }
  }
  const open = new Set<string>();
  for (const execution of executions) {
    if (execution.type === "BUY") {
      const lotId = lotIdOf(execution);
      if (!closed.has(lotId)) open.add(lotId);
    }
  }
  return open;
}

function withinRange(timestamp: string, range: DateRange): boolean {
  if (range.start && timestamp < range.start) return false;
  // The end bound is INCLUSIVE of the whole day. A picker gives
  // "2026-03-27", and a user selecting a single day means that day, not
  // the instant midnight begins it -- a plain `>` would return nothing.
  if (range.end && timestamp.slice(0, 10) > range.end) return false;
  return true;
}

function matchesStatus(
  execution: BacktestExecution,
  status: OrderStatusFilter,
  open: Set<string>,
): boolean {
  if (status === "all") return true;
  const isOpen = open.has(lotIdOf(execution));
  return status === "stuck" ? isOpen : !isOpen;
}

function matchesRsi(execution: BacktestExecution, min: number | null, max: number | null): boolean {
  if (min === null && max === null) return true;
  // UNKNOWN IS NOT IN RANGE. An execution inside the indicator's warmup
  // has no RSI, and including it in an "RSI < 30" query would claim the
  // strategy entered on a reading that did not exist.
  if (execution.rsi_at_entry === undefined) return false;
  if (min !== null && execution.rsi_at_entry < min) return false;
  if (max !== null && execution.rsi_at_entry > max) return false;
  return true;
}

/** Apply every filter. Order is irrelevant; all are conjunctive. */
export function filterExecutions(
  executions: BacktestExecution[],
  filters: ExecutionFilters,
): BacktestExecution[] {
  const open = openLotIds(executions);
  return executions.filter(
    (execution) =>
      withinRange(execution.timestamp, filters.range) &&
      matchesStatus(execution, filters.status, open) &&
      matchesRsi(execution, filters.rsiMin, filters.rsiMax) &&
      (filters.tickers.length === 0 || filters.tickers.includes(execution.ticker)),
  );
}

/** Seconds per aggregation bucket, for rolling bars up. */
export const TIMEFRAME_SECONDS: Record<Timeframe, number> = {
  "1Min": 60,
  "5Min": 300,
  "15Min": 900,
  "1Hour": 3600,
  "1Day": 86_400,
};

export interface Candle {
  time: number;
  open: number;
  high: number;
  low: number;
  close: number;
}

/**
 * Roll 1-minute bars up to a coarser timeframe.
 *
 * OHLC is aggregated properly -- first open, max high, min low, last
 * close -- rather than by sampling every Nth bar, which would drop the
 * extremes and draw a chart whose highs and lows never happened. This
 * matters here more than usual: the engine's "intrabar" fill model
 * fills on a level TOUCHED during a bar, so the wicks are exactly where
 * the executions are.
 */
export function aggregate(candles: Candle[], timeframe: Timeframe): Candle[] {
  const bucketSeconds = TIMEFRAME_SECONDS[timeframe];
  if (bucketSeconds <= 60 || candles.length === 0) return candles;

  const out: Candle[] = [];
  let current: Candle | null = null;
  let bucket = -1;

  for (const candle of candles) {
    const candleBucket = Math.floor(candle.time / bucketSeconds);
    if (current === null || candleBucket !== bucket) {
      if (current) out.push(current);
      bucket = candleBucket;
      current = { ...candle, time: candleBucket * bucketSeconds };
    } else {
      current.high = Math.max(current.high, candle.high);
      current.low = Math.min(current.low, candle.low);
      current.close = candle.close;
    }
  }
  if (current) out.push(current);
  return out;
}

/** Epoch seconds, which is what lightweight-charts wants. */
export function toEpochSeconds(iso: string): number {
  return Math.floor(new Date(iso).getTime() / 1000);
}

/* ------------------------------------------------------------------ */
/* Execution-chart zoom                                               */
/* ------------------------------------------------------------------ */

const DAY = 86_400;

/**
 * What each Execution-chart zoom level pulls and draws.
 *
 *   bucket          the candle size after client-side aggregation.
 *   maxSpanSeconds  the widest window this level will fetch, anchored to
 *                   the end of the run (or the end of the filter range).
 *                   null = the whole run.
 *   maxPoints       the `/bars` downsample hint. Set high enough that the
 *                   server bucket for the CAPPED window is at or below
 *                   `bucket` -- so "1m" really shows minute bars, not a
 *                   server rollup of the whole ten-year file.
 */
export const CHART_RESOLUTIONS: Record<
  ChartResolution,
  { label: string; bucket: Timeframe; maxSpanSeconds: number | null; maxPoints: number }
> = {
  "1d": { label: "1D", bucket: "1Day", maxSpanSeconds: null, maxPoints: 4000 },
  "1h": { label: "1H", bucket: "1Hour", maxSpanSeconds: 10 * DAY, maxPoints: 6000 },
  "1m": { label: "1m", bucket: "1Min", maxSpanSeconds: 2 * DAY, maxPoints: 6000 },
};

/**
 * The date window the Execution chart should fetch for a zoom level.
 *
 * The anchor is the end of the filter range (or, when that is open, the
 * end of the run's data). A capped level starts `maxSpanSeconds` before
 * that anchor, but never earlier than the filter range / data actually
 * begins. Pure and unit-tested -- the off-by-a-window bug here is
 * invisible on screen (it just looks like the run traded less).
 */
export function chartWindow(
  resolution: ChartResolution,
  range: DateRange,
  data: DateRange,
): DateRange {
  const spec = CHART_RESOLUTIONS[resolution];
  const end = range.end ?? data.end;
  const lower = range.start ?? data.start;
  if (spec.maxSpanSeconds === null || !end) return { start: lower, end };

  const cappedStart = new Date(new Date(end).getTime() - spec.maxSpanSeconds * 1000).toISOString();
  const start =
    lower && new Date(lower).getTime() > new Date(cappedStart).getTime() ? lower : cappedStart;
  return { start, end };
}

/* ------------------------------------------------------------------ */
/* Run-history filtering                                              */
/*                                                                    */
/* The history table is flattened to one row per (run, fund, grid     */
/* cell). Filtering it is the same shape of problem as filtering       */
/* executions -- pure, conjunctive, and easy to get quietly wrong on  */
/* the "unknown value" case -- so it lives here beside the other      */
/* filter and is covered by the same test file.                       */
/* ------------------------------------------------------------------ */

/** Floats that came from the same computation but a different path
 * (a stored chip value vs. a freshly derived row value) can differ in
 * the last bit; treat them as equal within a hair. */
export function sameNumber(a: number, b: number): boolean {
  return Math.abs(a - b) <= 1e-9;
}

/**
 * The value of one namespaced numeric field on a history row, in the
 * SAME unit the table and the filter inputs use:
 *
 *   grid_step / profit_target   stored as a fraction, read as a PERCENT
 *   param:<name>                the raw argument, when it is numeric
 *   metric:<key>                the raw metric (cagr_pct etc. are
 *                               already percent-scaled by the engine)
 *
 * Returns null when the field does not apply -- an old report with no
 * such metric, a model that never took the argument, or a non-numeric
 * argument such as `ticker`.
 */
export function historyFieldValue(row: HistoryRow, key: string): number | null {
  if (key === "grid_step") return row.grid_step === null ? null : row.grid_step * 100;
  if (key === "profit_target") {
    return row.profit_target === null ? null : row.profit_target * 100;
  }
  if (key.startsWith("param:")) {
    const raw = row.strategy_params?.[key.slice("param:".length)];
    return typeof raw === "number" && Number.isFinite(raw) ? raw : null;
  }
  if (key.startsWith("metric:")) {
    const raw = row.metrics[key.slice("metric:".length) as keyof FundPerformanceMetrics];
    return typeof raw === "number" && Number.isFinite(raw) ? raw : null;
  }
  return null;
}

function numericFieldPasses(row: HistoryRow, key: string, filters: RunHistoryFilters): boolean {
  const values = filters.values[key];
  const range = filters.ranges[key];
  const hasValues = values !== undefined && values.length > 0;
  const hasRange = range !== undefined && (range.min !== null || range.max !== null);
  if (!hasValues && !hasRange) return true;

  const actual = historyFieldValue(row, key);
  // UNKNOWN IS NOT A MATCH. A row missing this field must not slip
  // through a gate the reader deliberately set -- same rule the RSI
  // filter follows for an execution inside the indicator warmup.
  if (actual === null) return false;

  const inValues = hasValues && values.some((value) => sameNumber(value, actual));
  const inRange =
    hasRange &&
    (range.min === null || actual >= range.min) &&
    (range.max === null || actual <= range.max);

  // values OR range: either one satisfied is enough, so a discrete pick
  // and a band can be combined on the same field without fighting.
  return Boolean(inValues || inRange);
}

/** The namespaced keys of every numeric field the filter actually
 * gates -- an empty `values` list or an all-null range does not count. */
export function activeNumericFieldKeys(filters: RunHistoryFilters): string[] {
  const keys = new Set<string>();
  for (const [key, values] of Object.entries(filters.values)) {
    if (values.length > 0) keys.add(key);
  }
  for (const [key, range] of Object.entries(filters.ranges)) {
    if (range.min !== null || range.max !== null) keys.add(key);
  }
  return [...keys];
}

/** True when any part of the filter would remove a row. */
export function runHistoryFilterActive(filters: RunHistoryFilters): boolean {
  return (
    filters.name.trim() !== "" ||
    filters.tickers.length > 0 ||
    filters.models.length > 0 ||
    filters.fillModels.length > 0 ||
    activeNumericFieldKeys(filters).length > 0
  );
}

/** Apply every run-history filter. All clauses are conjunctive. */
export function filterHistoryRows(
  rows: HistoryRow[],
  filters: RunHistoryFilters,
): HistoryRow[] {
  const needle = filters.name.trim().toLowerCase();
  const numericKeys = activeNumericFieldKeys(filters);

  return rows.filter((row) => {
    if (needle && !(row.name ?? "").toLowerCase().includes(needle)) return false;
    if (filters.tickers.length > 0 && !filters.tickers.includes(row.ticker)) return false;
    if (
      filters.models.length > 0 &&
      !(row.sizing_model !== null && filters.models.includes(row.sizing_model))
    ) {
      return false;
    }
    if (
      filters.fillModels.length > 0 &&
      !(row.fill_model !== null && filters.fillModels.includes(row.fill_model))
    ) {
      return false;
    }
    for (const key of numericKeys) {
      if (!numericFieldPasses(row, key, filters)) return false;
    }
    return true;
  });
}

/** One filterable field, plus the distinct values present for its
 * "pick specific values" chips (ascending; empty for a continuous
 * field like a metric). */
export interface HistoryFieldOption {
  key: string;
  label: string;
  group: "Input arguments" | "Results";
  values: number[];
}

/** The curated result metrics offered as range filters, in the order
 * the table shows them. */
export const HISTORY_METRIC_FIELDS: { key: keyof FundPerformanceMetrics; label: string }[] = [
  { key: "net_yield_pct", label: "Net yield %" },
  { key: "cagr_pct", label: "CAGR %" },
  { key: "worst_year_pct", label: "Worst year %" },
  { key: "best_year_pct", label: "Best year %" },
  { key: "max_drawdown_pct", label: "Max drawdown %" },
  { key: "return_over_drawdown", label: "Return / drawdown" },
  { key: "sharpe_ratio", label: "Sharpe" },
  { key: "sortino_ratio", label: "Sortino" },
  { key: "profit_factor", label: "Profit factor" },
  { key: "win_rate_pct", label: "Win rate %" },
  { key: "capital_velocity_index", label: "Capital velocity" },
  { key: "stuck_capital_value", label: "Stuck capital $" },
  { key: "avg_hold_duration", label: "Avg hold (bars)" },
  { key: "total_trades", label: "Total trades" },
];

function distinctValues(rows: HistoryRow[], key: string): number[] {
  const seen: number[] = [];
  for (const row of rows) {
    const value = historyFieldValue(row, key);
    if (value !== null && !seen.some((existing) => sameNumber(existing, value))) {
      seen.push(value);
    }
  }
  return seen.sort((a, b) => a - b);
}

/**
 * The numeric INPUT-argument fields present across the loaded rows.
 *
 * `grid_step` and `profit_target` are always offered -- they are the
 * swept dimensions -- even when the loaded history holds a single value
 * of each. Every numeric sizing-model argument seen in any row is
 * offered too; non-numeric arguments (`ticker`) are left to the Fund
 * control.
 */
export function historyInputFields(rows: HistoryRow[]): HistoryFieldOption[] {
  const out: HistoryFieldOption[] = [
    { key: "grid_step", label: "Grid step %", group: "Input arguments", values: distinctValues(rows, "grid_step") },
    {
      key: "profit_target",
      label: "Profit target %",
      group: "Input arguments",
      values: distinctValues(rows, "profit_target"),
    },
  ];

  const paramKeys = new Set<string>();
  for (const row of rows) {
    for (const [name, value] of Object.entries(row.strategy_params ?? {})) {
      if (typeof value === "number" && Number.isFinite(value)) paramKeys.add(name);
    }
  }
  for (const name of [...paramKeys].sort()) {
    const key = `param:${name}`;
    out.push({ key, label: name, group: "Input arguments", values: distinctValues(rows, key) });
  }
  return out;
}
