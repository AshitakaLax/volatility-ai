/**
 * The result page's and Run History's pure helpers.
 *
 * Filtering itself moved server-side: fills are paged per fund
 * (server/fills.py) and history is queried per fund
 * (server/history_query.py), each with the rules this file used to
 * apply in the browser -- and the tests that pinned them, ported. What
 * stays here is what the browser still decides: request shapes, chart
 * windows and aggregation, sort-header cycling, and row identity.
 */
import type {
  ChartResolution,
  DateRange,
  ExecutionFilters,
  Fill,
  FillsQuery,
  HistoryQuery,
  Metrics,
  Params,
  RunHistoryFilters,
  Timeframe,
} from "@/types/backtest";

/** A fill's unique key. The lot alone is NOT unique -- one buy and
 * possibly several partial sells share it -- so it is qualified by side
 * and bar, in exactly one place rather than at each call site. */
export function fillKey(fill: Fill): string {
  return `${fill.lot}-${fill.side.toLowerCase()}-${fill.i}`;
}

/**
 * Which fund the result page shows: the filter's pick when the loaded
 * report actually has it, else the report's first fund.
 *
 * The filter outlives any one report -- App owns it so the date range
 * survives a tab switch -- so a fund picked on one report can be absent
 * from the next. Trusting it there left the page with no fund, no
 * metrics, and, on a single-fund report, no Fund selector to get out.
 */
export function resolveSelectedFund(picked: string[], available: string[]): string | null {
  const first = picked[0];
  if (first !== undefined && available.includes(first)) return first;
  return available[0] ?? null;
}

/**
 * The page's execution filters as GET /runs/{id}/fills parameters -- the
 * same filters the browser used to apply, sent instead of applied.
 */
export function fillsParams(filters: ExecutionFilters): Omit<FillsQuery, "ticker"> {
  return {
    start: filters.range.start,
    end: filters.range.end,
    status: filters.status,
    rsi_min: filters.rsiMin,
    rsi_max: filters.rsiMax,
  };
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
/* Run-history helpers                                                */
/*                                                                    */
/* The table is one row per (run, fund, cell), filtered, sorted and   */
/* paged by the server (server/history_query.py). These are the bits  */
/* the filter bar and table still decide in the browser.              */
/* ------------------------------------------------------------------ */

/** Floats that came from the same computation but a different path
 * (a stored chip value vs. a freshly derived row value) can differ in
 * the last bit; treat them as equal within a hair. */
export function sameNumber(a: number, b: number): boolean {
  return Math.abs(a - b) <= 1e-9;
}

/**
 * A stable, order-independent identity for a cell's resolved strategy-
 * param combination. Dictionary order isn't guaranteed on the wire, so
 * entries are sorted by key before joining.
 *
 * (grid, target) alone is NOT a unique identity: once a strategy param
 * is swept too (a Bayesian search over e.g. oversold_threshold/period
 * with grid_step/profit_target held fixed), many cells legitimately
 * share one (grid, target) pair, one per combo. This is what lets
 * SweepMatrix's combo selector tell them apart.
 *
 * NOT a row identity on its own: a Bayesian search re-tries identical
 * configurations, so equal combos recur within one run. Run History keys
 * rows by (run, fund, engine rank) instead.
 */
export function comboKey(params: Params | null | undefined): string {
  return JSON.stringify(Object.entries(params ?? {}).sort(([a], [b]) => a.localeCompare(b)));
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
    filters.models.length > 0 ||
    filters.fillModels.length > 0 ||
    filters.window.start !== null ||
    filters.window.end !== null ||
    activeNumericFieldKeys(filters).length > 0
  );
}

/** The curated result metrics offered as range filters, in the order
 * the table shows them. */
export const HISTORY_METRIC_FIELDS: { key: keyof Metrics; label: string }[] = [
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

/* ------------------------------------------------------------------ */
/* Run-history column sort                                            */
/*                                                                    */
/* Clicking a column header cycles ascending -> descending -> off; the*/
/* "off" state is not a third sort of its own -- RunHistory.tsx falls */
/* back to its existing "Rank by" ranking, so this never replaces that*/
/* default, only overrides it while a column is actively picked.      */
/* ------------------------------------------------------------------ */

export type RunHistoryColumn =
  | "name"
  | "ticker"
  | "grid_step"
  | "profit_target"
  | "sizing_model"
  | "metric"
  | "cagr_pct"
  | "max_drawdown_pct"
  | "worst_year_pct"
  | "total_trades"
  | "window"
  | "run_id"
  | "saved_at";

export interface RunHistorySort {
  column: RunHistoryColumn;
  direction: "asc" | "desc";
}

/** The 3-state cycle for one header click: not-active -> asc, asc ->
 * desc, desc -> off (null). Clicking a DIFFERENT column always starts
 * IT at asc and discards whatever was active before -- only one column
 * sorts at a time, the same convention a spreadsheet or data grid uses. */
export function nextRunHistorySort(
  current: RunHistorySort | null,
  column: RunHistoryColumn,
): RunHistorySort | null {
  if (!current || current.column !== column) return { column, direction: "asc" };
  if (current.direction === "asc") return { column, direction: "desc" };
  return null;
}

/**
 * One Run History page request. The fund is required; the "Rank by"
 * default sort (no column picked) is the rank metric, best end first --
 * `higherIsBetter` says which end that is for the chosen metric.
 */
export function historyQueryBody(args: {
  ticker: string;
  filters: RunHistoryFilters;
  sort: RunHistorySort | null;
  rankBy: keyof Metrics;
  higherIsBetter: boolean;
  page: number;
  pageSize: number;
}): HistoryQuery {
  const { extraFields: _presentational, ...filters } = args.filters;
  void _presentational;
  return {
    ticker: args.ticker,
    filters,
    sort: args.sort ?? { column: "metric", direction: args.higherIsBetter ? "desc" : "asc" },
    rank_by: args.rankBy,
    offset: Math.max(0, (args.page - 1) * args.pageSize),
    limit: args.pageSize,
  };
}
