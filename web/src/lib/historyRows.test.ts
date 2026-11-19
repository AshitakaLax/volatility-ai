import { describe, expect, it } from "vitest";

import { foldRepeats } from "@/lib/historyRows";
import type { HistoryRow } from "@/types/backtest";

function row(over: Partial<HistoryRow> = {}): HistoryRow {
  return {
    run: "939e1625",
    ticker: "TQQQ",
    rank: 0,
    name: "tuned full-window",
    model: "hf_local_reference",
    fill: "intrabar",
    grid: 0.00105,
    target: 0.51245,
    start: "2016-01-04",
    end: "2026-08-21",
    m: { cagr_pct: 50.8, max_drawdown_pct: 71.7, total_trades: 438143 },
    ...over,
  } as unknown as HistoryRow;
}

describe("a page of run history", () => {
  it("folds a run of identical results into one, with how many", () => {
    const groups = foldRepeats([row({ rank: 1 }), row({ rank: 2 }), row({ rank: 3 })]);
    expect(groups).toHaveLength(1);
    expect(groups[0]).toMatchObject({ count: 3, index: 0 });
    expect(groups[0]?.row.rank).toBe(1);
  });

  it("keeps rows that differ in configuration, figures or run", () => {
    const groups = foldRepeats([
      row(),
      row({ target: 0.6 }),
      row({ m: { cagr_pct: 50.7 } as HistoryRow["m"] }),
      row({ run: "other" }),
    ]);
    expect(groups.map((group) => group.count)).toEqual([1, 1, 1, 1]);
  });

  it("folds only neighbours, so the server's order is kept", () => {
    const groups = foldRepeats([row(), row({ target: 0.6 }), row(), row()]);
    expect(groups.map((group) => [group.index, group.count])).toEqual([
      [0, 1],
      [1, 1],
      [2, 2],
    ]);
  });

  it("is nothing for nothing", () => {
    expect(foldRepeats([])).toEqual([]);
  });
});
