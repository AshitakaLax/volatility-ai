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
  DateRange,
  ExecutionFilters,
  OrderStatusFilter,
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
