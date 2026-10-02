/**
 * The pure helpers the browser still owns, tested.
 *
 * Execution and history FILTERING moved server-side, and the cases that
 * pinned them moved with it (server/tests/test_fills.py,
 * server/tests/test_history_api.py). What remains here still decides
 * things -- request shapes, how minute bars roll up, chart windows, row
 * identity -- where the wrong answer looks entirely plausible on screen.
 */
import { describe, expect, it } from "vitest";

import {
  EMPTY_RUN_HISTORY_FILTERS,
  type ExecutionFilters,
  type Fill,
  type RunHistoryFilters,
} from "@/types/backtest";

import {
  CHART_RESOLUTIONS,
  aggregate,
  chartWindow,
  comboKey,
  fillKey,
  fillsParams,
  historyQueryBody,
  nextRunHistorySort,
  resolveSelectedFund,
  runHistoryFilterActive,
} from "./filters";

function buy(lot: string, bar: number, extra: Partial<Fill> = {}): Fill {
  return { lot, side: "BUY", i: bar, px: 100, qty: 1, ts: "2026-03-01T14:30:00+00:00", ...extra };
}

function sell(lot: string, bar: number, extra: Partial<Fill> = {}): Fill {
  return {
    lot,
    side: "SELL",
    i: bar,
    px: 101,
    qty: 1,
    ts: "2026-03-02T14:30:00+00:00",
    pnl: 1,
    ...extra,
  };
}

const BASE: ExecutionFilters = {
  chartResolution: "1d",
  range: { start: null, end: null },
  status: "all",
  rsiMin: null,
  rsiMax: null,
  tickers: [],
};

describe("fillKey", () => {
  it("qualifies the lot by side and bar, since the lot alone repeats", () => {
    expect(fillKey(buy("SIM-000008", 235))).toBe("SIM-000008-buy-235");
    expect(fillKey(sell("SIM-000008", 400))).toBe("SIM-000008-sell-400");
  });

  it("keeps a buy and its partial sells distinct", () => {
    const keys = [buy("A", 1), sell("A", 5), sell("A", 9)].map(fillKey);
    expect(new Set(keys).size).toBe(3);
  });
});

describe("resolveSelectedFund", () => {
  it("uses the filter's pick when the report has that fund", () => {
    expect(resolveSelectedFund(["QQQ"], ["TQQQ", "QQQ"])).toBe("QQQ");
  });

  it("falls back to the first fund when nothing is picked ('All')", () => {
    expect(resolveSelectedFund([], ["TQQQ", "QQQ"])).toBe("TQQQ");
  });

  it("falls back to the first fund when the pick came from a different report", () => {
    // The filter outlives the report. Trusting a stale "QQQ" on a
    // TQQQ-only report left the page with no fund and, with one fund,
    // no selector to change it.
    expect(resolveSelectedFund(["QQQ"], ["TQQQ"])).toBe("TQQQ");
  });

  it("is null when the report has no funds", () => {
    expect(resolveSelectedFund(["QQQ"], [])).toBeNull();
  });
});

describe("aggregate", () => {
  const minutes = [
    { time: 0, open: 10, high: 12, low: 9, close: 11 },
    { time: 60, open: 11, high: 15, low: 8, close: 14 },
    { time: 120, open: 14, high: 14, low: 13, close: 13 },
  ];

  it("keeps the extremes rather than sampling", () => {
    // Sampling every Nth bar would draw a chart whose highs and lows
    // never happened -- and under the "intrabar" fill model the wicks
    // are exactly where the executions are.
    const [rolled] = aggregate(minutes, "1Hour");
    expect(rolled).toEqual({ time: 0, open: 10, high: 15, low: 8, close: 13 });
  });

  it("is a no-op at the source resolution", () => {
    expect(aggregate(minutes, "1Min")).toBe(minutes);
  });

  it("starts a new bucket at each boundary", () => {
    const spanning = [
      { time: 0, open: 1, high: 1, low: 1, close: 1 },
      { time: 3600, open: 2, high: 2, low: 2, close: 2 },
    ];
    expect(aggregate(spanning, "1Hour")).toHaveLength(2);
  });

  it("handles an empty series", () => {
    expect(aggregate([], "1Day")).toEqual([]);
  });
});

describe("chartWindow", () => {
  const data = { start: "2016-01-04T14:30:00+00:00", end: "2026-09-05T20:00:00+00:00" };

  it("1d over an open range is the whole run", () => {
    expect(chartWindow("1d", { start: null, end: null }, data)).toEqual({
      start: data.start,
      end: data.end,
    });
  });

  it("1m caps to a 2-day window anchored at the data end", () => {
    const win = chartWindow("1m", { start: null, end: null }, data);
    expect(win.end).toBe(data.end);
    const spanMs = new Date(win.end!).getTime() - new Date(win.start!).getTime();
    expect(spanMs).toBe(CHART_RESOLUTIONS["1m"].maxSpanSeconds! * 1000);
  });

  it("1h caps to a 10-day window", () => {
    const win = chartWindow("1h", { start: null, end: null }, data);
    const spanMs = new Date(win.end!).getTime() - new Date(win.start!).getTime();
    expect(spanMs).toBe(10 * 86_400 * 1000);
  });

  it("anchors to the filter range end when one is set", () => {
    const win = chartWindow("1m", { start: null, end: "2020-06-15T00:00:00+00:00" }, data);
    expect(win.end).toBe("2020-06-15T00:00:00+00:00");
    expect(new Date(win.start!).getTime()).toBe(
      new Date("2020-06-13T00:00:00+00:00").getTime(),
    );
  });

  it("never starts earlier than the filter range does", () => {
    // A 1-day filter range is narrower than 1m's 2-day cap -- the cap
    // must not pull data from before the range the user chose.
    const range = { start: "2020-06-15T00:00:00+00:00", end: "2020-06-15T23:59:00+00:00" };
    const win = chartWindow("1m", range, data);
    expect(win.start).toBe(range.start);
    expect(win.end).toBe(range.end);
  });

  it("falls back to the data end as the anchor when the range is open", () => {
    expect(chartWindow("1h", { start: null, end: null }, { start: null, end: null })).toEqual({
      start: null,
      end: null,
    });
  });
});

/* ---------------- run-history filtering ---------------------------- */

const NONE: RunHistoryFilters = EMPTY_RUN_HISTORY_FILTERS;

describe("comboKey", () => {
  // SweepMatrix's combo selector tells cells apart by this once a
  // strategy param is swept too (several cells then share one
  // grid/target pair). Not a row identity: a Bayesian search re-tries
  // identical combos, which is why Run History keys rows by rank.
  it("differs for rows that share grid/target/run but differ only in params", () => {
    const a = comboKey({ oversold_threshold: 30, period: 7 });
    const b = comboKey({ oversold_threshold: 40, period: 7 });
    expect(a).not.toBe(b);
  });

  it("is order-independent -- the same combo never produces two keys", () => {
    const a = comboKey({ oversold_threshold: 30, period: 7 });
    const b = comboKey({ period: 7, oversold_threshold: 30 });
    expect(a).toBe(b);
  });

  it("treats absent and empty params as the same combo", () => {
    expect(comboKey(undefined)).toBe(comboKey({}));
    expect(comboKey(null)).toBe(comboKey({}));
  });
});

describe("nextRunHistorySort", () => {
  it("clicking an inactive column starts it ascending", () => {
    expect(nextRunHistorySort(null, "name")).toEqual({ column: "name", direction: "asc" });
  });

  it("clicking the active column cycles asc -> desc -> off", () => {
    const asc: { column: "name"; direction: "asc" } = { column: "name", direction: "asc" };
    const desc = nextRunHistorySort(asc, "name");
    expect(desc).toEqual({ column: "name", direction: "desc" });
    expect(nextRunHistorySort(desc, "name")).toBeNull();
  });

  it("clicking a DIFFERENT column always restarts it at ascending", () => {
    const active = { column: "name", direction: "desc" } as const;
    expect(nextRunHistorySort(active, "ticker")).toEqual({ column: "ticker", direction: "asc" });
  });
});

describe("runHistoryFilterActive", () => {
  it("is false for the empty filter and for empty sub-parts", () => {
    expect(runHistoryFilterActive(NONE)).toBe(false);
    expect(runHistoryFilterActive({ ...NONE, name: "   " })).toBe(false);
    expect(runHistoryFilterActive({ ...NONE, values: { grid_step: [] } })).toBe(false);
    expect(
      runHistoryFilterActive({ ...NONE, ranges: { grid_step: { min: null, max: null } } }),
    ).toBe(false);
    // extraFields is presentational -- adding a row without typing a
    // bound does not make the view "filtered".
    expect(runHistoryFilterActive({ ...NONE, extraFields: ["metric:cagr_pct"] })).toBe(false);
  });

  it("is true as soon as any clause would remove a row", () => {
    expect(runHistoryFilterActive({ ...NONE, name: "x" })).toBe(true);
    expect(runHistoryFilterActive({ ...NONE, window: { start: "2026-01-01", end: null } })).toBe(
      true,
    );
    expect(runHistoryFilterActive({ ...NONE, ranges: { grid_step: { min: 1, max: null } } })).toBe(
      true,
    );
  });
});

describe("fillsParams", () => {
  it("sends the page's execution filters to the fills endpoint unchanged", () => {
    expect(
      fillsParams({ ...BASE, range: { start: "2026-01-01", end: "2026-02-01" }, status: "stuck", rsiMin: 20, rsiMax: 30 }),
    ).toEqual({ start: "2026-01-01", end: "2026-02-01", status: "stuck", rsi_min: 20, rsi_max: 30 });
  });

  it("leaves open bounds open rather than inventing them", () => {
    expect(fillsParams(BASE)).toEqual({ start: null, end: null, status: "all", rsi_min: null, rsi_max: null });
  });
});

describe("historyQueryBody", () => {
  const args = {
    ticker: "TQQQ",
    filters: { ...NONE, name: "sweep", extraFields: ["metric:cagr_pct"] },
    sort: null,
    rankBy: "max_drawdown_pct" as const,
    higherIsBetter: false,
    page: 3,
    pageSize: 50,
  };

  it("defaults to the rank metric, best end first", () => {
    expect(historyQueryBody(args).sort).toEqual({ column: "metric", direction: "asc" });
    expect(historyQueryBody({ ...args, higherIsBetter: true }).sort).toEqual({ column: "metric", direction: "desc" });
  });

  it("an explicitly clicked column wins over the rank default", () => {
    const sort = { column: "name", direction: "desc" } as const;
    expect(historyQueryBody({ ...args, sort }).sort).toEqual(sort);
  });

  it("pages by offset and never sends the presentational extraFields", () => {
    const body = historyQueryBody(args);
    expect(body.offset).toBe(100);
    expect(body.limit).toBe(50);
    expect(body.ticker).toBe("TQQQ");
    expect(body.rank_by).toBe("max_drawdown_pct");
    expect(body.filters).not.toHaveProperty("extraFields");
    expect(body.filters.name).toBe("sweep");
  });
});
