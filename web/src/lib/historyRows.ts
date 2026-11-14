/**
 * Run History's rows, with a run of identical results folded into one.
 *
 * A search that re-tries a configuration (Bayesian, a sweep over a
 * parameter the strategy ignores) stores the same result many times, and
 * ranked by any metric they sit together: forty rows saying one thing.
 * Adjacent rows of the same run whose configuration and every figure agree
 * are shown once, with how many there were. Only adjacent ones, and only on
 * the page the server sent: the ranking and the paging stay the server's.
 */
import type { HistoryRow } from "@/types/backtest";

export interface HistoryGroup {
  row: HistoryRow;
  /** Rows folded into this one, itself included. */
  count: number;
  /** The first row's index on the page. */
  index: number;
}

function signature(row: HistoryRow): string {
  return JSON.stringify([
    row.run,
    row.ticker,
    row.name,
    row.model,
    row.fill,
    row.grid,
    row.target,
    row.start,
    row.end,
    row.m,
  ]);
}

export function foldRepeats(rows: HistoryRow[]): HistoryGroup[] {
  const groups: HistoryGroup[] = [];
  let last: string | null = null;
  rows.forEach((row, index) => {
    const key = signature(row);
    const open = groups[groups.length - 1];
    if (open && key === last) open.count += 1;
    else groups.push({ row, count: 1, index });
    last = key;
  });
  return groups;
}
