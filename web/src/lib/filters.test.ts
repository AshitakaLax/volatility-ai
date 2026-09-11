/**
 * The frontend's only real logic, tested.
 *
 * Everything else in this app renders data it was handed. These
 * functions DECIDE things -- which executions belong to which lot, which
 * survive a filter, how minute bars roll up -- and each of the cases
 * below is one where the wrong answer looks entirely plausible on screen.
 */
import { describe, expect, it } from "vitest";

import {
  EMPTY_RUN_HISTORY_FILTERS,
  type BacktestExecution,
  type ExecutionFilters,
  type FundPerformanceMetrics,
  type HistoryRow,
  type RunHistoryFilters,
} from "@/types/backtest";

import {
  CHART_RESOLUTIONS,
  aggregate,
  buildCycles,
  chartWindow,
  filterExecutions,
  filterHistoryRows,
  historyFieldValue,
  historyInputFields,
  lotIdOf,
  nextRunHistorySort,
  openLotIds,
  runHistoryFilterActive,
  sortHistoryRows,
} from "./filters";

function buy(lot: string, bar: number, extra: Partial<BacktestExecution> = {}): BacktestExecution {
  return {
    order_id: `${lot}-buy-${bar}`,
    ticker: "TQQQ",
    type: "BUY",
    price: 100,
    shares: 1,
    timestamp: "2026-03-01T14:30:00+00:00",
    ...extra,
  };
}

function sell(lot: string, bar: number, extra: Partial<BacktestExecution> = {}): BacktestExecution {
  return {
    order_id: `${lot}-sell-${bar}`,
    ticker: "TQQQ",
    type: "SELL",
    price: 101,
    shares: 1,
    timestamp: "2026-03-02T14:30:00+00:00",
    matched_buy_id: lot,
    profit_realized: 1,
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

describe("lotIdOf", () => {
  it("reads the lot out of a buy's qualified order id", () => {
    expect(lotIdOf(buy("SIM-000008", 235))).toBe("SIM-000008");
  });

  it("prefers matched_buy_id on a sell", () => {
    expect(lotIdOf(sell("SIM-000008", 400))).toBe("SIM-000008");
  });

  it("splits on the LAST marker, so a lot id containing one survives", () => {
    // Contrived, but the alternative (indexOf) would silently truncate
    // and merge two different lots into one cycle.
    const odd = buy("weird-buy-lot", 12);
    expect(lotIdOf(odd)).toBe("weird-buy-lot");
  });
});

describe("buildCycles", () => {
  it("pairs a buy with the sell that closed it", () => {
    const cycles = buildCycles([buy("A", 1), sell("A", 9)]);
    expect(cycles).toHaveLength(1);
    expect(cycles[0]!.open).toBe(false);
    expect(cycles[0]!.realized).toBe(1);
  });

  it("sums partial sells against one lot", () => {
    const cycles = buildCycles([
      buy("A", 1),
      sell("A", 5, { profit_realized: 0.4 }),
      sell("A", 9, { profit_realized: 0.6 }),
    ]);
    expect(cycles[0]!.sells).toHaveLength(2);
    expect(cycles[0]!.realized).toBeCloseTo(1.0);
  });

  it("reports an unsold lot as open with null realised", () => {
    // null, not 0. Zero would read as "closed for no gain", which is a
    // different and much better outcome than "never came back".
    const cycles = buildCycles([buy("A", 1)]);
    expect(cycles[0]!.open).toBe(true);
    expect(cycles[0]!.realized).toBeNull();
  });

  it("keeps the FIRST buy when a lot id somehow appears twice", () => {
    const cycles = buildCycles([buy("A", 1), buy("A", 50), sell("A", 60)]);
    expect(cycles).toHaveLength(1);
    expect(cycles[0]!.buy.order_id).toBe("A-buy-1");
  });

  it("ignores a sell whose lot has no buy rather than inventing one", () => {
    const cycles = buildCycles([sell("GHOST", 5)]);
    expect(cycles).toHaveLength(0);
  });
});

describe("openLotIds", () => {
  it("is the buys with no matching sell", () => {
    const open = openLotIds([buy("A", 1), sell("A", 2), buy("B", 3)]);
    expect([...open]).toEqual(["B"]);
  });
});

describe("filterExecutions", () => {
  it("excludes executions with NO rsi when a bound is set", () => {
    // THE ONE THAT MATTERS. An execution inside the 14-bar warmup has no
    // RSI. Including it in "RSI < 30" would claim the strategy entered
    // on a reading that did not exist.
    const warmup = buy("A", 1);
    const known = buy("B", 2, { rsi_at_entry: 25 });
    const out = filterExecutions([warmup, known], { ...BASE, rsiMax: 30 });
    expect(out.map((e) => e.order_id)).toEqual(["B-buy-2"]);
  });

  it("keeps unknown-rsi executions when no bound is set", () => {
    const out = filterExecutions([buy("A", 1)], BASE);
    expect(out).toHaveLength(1);
  });

  it("treats rsi bounds as inclusive", () => {
    const at30 = buy("A", 1, { rsi_at_entry: 30 });
    expect(filterExecutions([at30], { ...BASE, rsiMax: 30 })).toHaveLength(1);
    expect(filterExecutions([at30], { ...BASE, rsiMin: 30 })).toHaveLength(1);
  });

  it("includes the whole of the end day, not the instant it begins", () => {
    // A picker gives "2026-03-02". Someone choosing a single day means
    // that day; a naive string compare against the full ISO timestamp
    // would return nothing at all.
    const sameDay = sell("A", 9); // 2026-03-02T14:30
    const out = filterExecutions([sameDay], {
      ...BASE,
      range: { start: "2026-03-02", end: "2026-03-02" },
    });
    expect(out).toHaveLength(1);
  });

  it("splits open from closed lots by status", () => {
    const rows = [buy("A", 1), sell("A", 2), buy("B", 3)];
    expect(filterExecutions(rows, { ...BASE, status: "stuck" }).map((e) => e.order_id)).toEqual([
      "B-buy-3",
    ]);
    expect(filterExecutions(rows, { ...BASE, status: "closed" }).map((e) => e.order_id)).toEqual([
      "A-buy-1",
      "A-sell-2",
    ]);
  });

  it("treats an empty ticker list as no restriction", () => {
    expect(filterExecutions([buy("A", 1)], { ...BASE, tickers: [] })).toHaveLength(1);
    expect(filterExecutions([buy("A", 1)], { ...BASE, tickers: ["RSP"] })).toHaveLength(0);
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

function metrics(over: Partial<FundPerformanceMetrics> = {}): FundPerformanceMetrics {
  return {
    ticker: "TQQQ",
    net_yield_pct: 0,
    cagr_pct: 0,
    max_drawdown_pct: 0,
    sharpe_ratio: 0,
    sortino_ratio: 0,
    profit_factor: 0,
    win_rate_pct: 0,
    max_consecutive_losses: 0,
    stuck_capital_value: 0,
    capital_velocity_index: 0,
    harvest_to_stuck_ratio: 0,
    avg_hold_duration: 0,
    total_trades: 0,
    closed_trades: 0,
    open_trades: 0,
    signal_exits: 0,
    final_equity: 0,
    ...over,
  };
}

type HistRowOverride = Partial<Omit<HistoryRow, "metrics">> & {
  metrics?: Partial<FundPerformanceMetrics>;
};

function histRow(over: HistRowOverride = {}): HistoryRow {
  return {
    run_id: "r1",
    name: null,
    saved_at: 0,
    ticker: "TQQQ",
    grid_step: 0.01,
    profit_target: 0.005,
    sizing_model: "fixed",
    strategy_params: {},
    fill_model: "close",
    engine_rank: 0,
    start: "2026-01-01",
    end: "2026-02-01",
    bars: 1000,
    ...over,
    metrics: metrics(over.metrics),
  };
}

const NONE: RunHistoryFilters = EMPTY_RUN_HISTORY_FILTERS;

describe("historyFieldValue", () => {
  it("reads the swept dimensions as a PERCENT, not a fraction", () => {
    // The table shows grid_step * 100, so the filter inputs are percents
    // too -- comparing a typed "1" against a stored 0.01 would match
    // nothing.
    expect(historyFieldValue(histRow({ grid_step: 0.015 }), "grid_step")).toBeCloseTo(1.5);
    expect(historyFieldValue(histRow({ profit_target: 0.005 }), "profit_target")).toBeCloseTo(0.5);
  });

  it("reads a numeric sizing-model argument by its param: key", () => {
    const row = histRow({ strategy_params: { allocation_pct: 0.05, ticker: "COWZ" } });
    expect(historyFieldValue(row, "param:allocation_pct")).toBe(0.05);
    // A non-numeric argument is not a numeric field -- Fund handles it.
    expect(historyFieldValue(row, "param:ticker")).toBeNull();
  });

  it("reads a result metric by its metric: key, and null when absent", () => {
    expect(historyFieldValue(histRow({ metrics: { cagr_pct: 12.5 } }), "metric:cagr_pct")).toBe(
      12.5,
    );
    // worst_year_pct is optional; a row without it must read as unknown,
    // not zero.
    expect(historyFieldValue(histRow(), "metric:worst_year_pct")).toBeNull();
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

describe("sortHistoryRows", () => {
  it("a null sort returns the rows completely unchanged (caller applies its own default)", () => {
    const rows = [histRow({ run_id: "b" }), histRow({ run_id: "a" })];
    expect(sortHistoryRows(rows, null, "cagr_pct")).toBe(rows);
  });

  it("sorts a plain string column both directions", () => {
    const rows = [histRow({ name: "beta" }), histRow({ name: "alpha" }), histRow({ name: "gamma" })];
    expect(sortHistoryRows(rows, { column: "name", direction: "asc" }, "cagr_pct").map((r) => r.name)).toEqual([
      "alpha",
      "beta",
      "gamma",
    ]);
    expect(sortHistoryRows(rows, { column: "name", direction: "desc" }, "cagr_pct").map((r) => r.name)).toEqual([
      "gamma",
      "beta",
      "alpha",
    ]);
  });

  it("sorts a numeric column", () => {
    const rows = [histRow({ grid_step: 0.02 }), histRow({ grid_step: 0.01 }), histRow({ grid_step: 0.03 })];
    expect(
      sortHistoryRows(rows, { column: "grid_step", direction: "asc" }, "cagr_pct").map((r) => r.grid_step),
    ).toEqual([0.01, 0.02, 0.03]);
  });

  it("a null value sorts LAST regardless of direction", () => {
    const rows = [histRow({ name: "known" }), histRow({ name: null }), histRow({ name: "also known" })];
    expect(sortHistoryRows(rows, { column: "name", direction: "asc" }, "cagr_pct").at(-1)!.name).toBeNull();
    expect(sortHistoryRows(rows, { column: "name", direction: "desc" }, "cagr_pct").at(-1)!.name).toBeNull();
  });

  it("the 'metric' column reads whichever FundPerformanceMetrics key is passed", () => {
    const rows = [
      histRow({ run_id: "hi", metrics: { sharpe_ratio: 2 } }),
      histRow({ run_id: "lo", metrics: { sharpe_ratio: 1 } }),
    ];
    expect(
      sortHistoryRows(rows, { column: "metric", direction: "desc" }, "sharpe_ratio").map((r) => r.run_id),
    ).toEqual(["hi", "lo"]);
  });

  it("does not mutate the input array", () => {
    const rows = [histRow({ run_id: "b" }), histRow({ run_id: "a" })];
    const copy = [...rows];
    sortHistoryRows(rows, { column: "run_id", direction: "asc" }, "cagr_pct");
    expect(rows).toEqual(copy);
  });

  describe("saved_at", () => {
    it("sorts by recorded save time", () => {
      const rows = [
        histRow({ run_id: "old", saved_at: 100 }),
        histRow({ run_id: "new", saved_at: 300 }),
        histRow({ run_id: "mid", saved_at: 200 }),
      ];
      expect(
        sortHistoryRows(rows, { column: "saved_at", direction: "asc" }, "cagr_pct").map(
          (r) => r.run_id,
        ),
      ).toEqual(["old", "mid", "new"]);
    });

    it("a row with no saved_at is treated as NOW, not as missing -- it sorts among the most recent, not last", () => {
      const rows = [
        histRow({ run_id: "old", saved_at: 100 }),
        histRow({ run_id: "unknown", saved_at: null }),
      ];
      // Descending (newest first): the unknown row -- "now" -- outranks
      // a row genuinely saved in 1970.
      expect(
        sortHistoryRows(rows, { column: "saved_at", direction: "desc" }, "cagr_pct").map(
          (r) => r.run_id,
        ),
      ).toEqual(["unknown", "old"]);
    });
  });
});

describe("filterHistoryRows", () => {
  it("matches the name as a case-insensitive substring", () => {
    const rows = [histRow({ name: "RSI oversold sweep" }), histRow({ name: "bell curve" }), histRow()];
    const out = filterHistoryRows(rows, { ...NONE, name: "oversold" });
    expect(out.map((r) => r.name)).toEqual(["RSI oversold sweep"]);
  });

  it("drops an unnamed row once a name filter is set", () => {
    expect(filterHistoryRows([histRow({ name: null })], { ...NONE, name: "x" })).toHaveLength(0);
  });

  it("treats a categorical list as OR-within, AND-between", () => {
    const rows = [
      histRow({ ticker: "TQQQ", sizing_model: "fixed" }),
      histRow({ ticker: "RSP", sizing_model: "fixed" }),
      histRow({ ticker: "TQQQ", sizing_model: "rsi" }),
    ];
    const out = filterHistoryRows(rows, { ...NONE, tickers: ["TQQQ", "RSP"], models: ["fixed"] });
    expect(out).toHaveLength(2);
    expect(out.every((r) => r.sizing_model === "fixed")).toBe(true);
  });

  it("filters a swept dimension by a percent RANGE", () => {
    const rows = [
      histRow({ grid_step: 0.005 }),
      histRow({ grid_step: 0.01 }),
      histRow({ grid_step: 0.02 }),
    ];
    const out = filterHistoryRows(rows, {
      ...NONE,
      ranges: { grid_step: { min: 0.75, max: 1.5 } },
    });
    expect(out.map((r) => r.grid_step)).toEqual([0.01]);
  });

  it("filters a swept dimension by a set of exact values", () => {
    const rows = [
      histRow({ grid_step: 0.005 }),
      histRow({ grid_step: 0.01 }),
      histRow({ grid_step: 0.02 }),
    ];
    const out = filterHistoryRows(rows, { ...NONE, values: { grid_step: [0.5, 2] } });
    expect(out.map((r) => r.grid_step).sort()).toEqual([0.005, 0.02]);
  });

  it("passes a row that satisfies EITHER the value set or the range", () => {
    const rows = [histRow({ grid_step: 0.005 }), histRow({ grid_step: 0.03 })];
    const out = filterHistoryRows(rows, {
      ...NONE,
      values: { grid_step: [3] },
      ranges: { grid_step: { min: null, max: 0.6 } },
    });
    expect(out).toHaveLength(2);
  });

  it("filters on a result metric range", () => {
    const rows = [
      histRow({ metrics: { cagr_pct: 5 } }),
      histRow({ metrics: { cagr_pct: 20 } }),
      histRow({ metrics: { cagr_pct: 40 } }),
    ];
    const out = filterHistoryRows(rows, { ...NONE, ranges: { "metric:cagr_pct": { min: 10, max: 30 } } });
    expect(out.map((r) => r.metrics.cagr_pct)).toEqual([20]);
  });

  it("EXCLUDES a row missing the gated field rather than letting it through", () => {
    // The same rule filterExecutions follows for an execution with no
    // RSI: a run that never recorded worst_year_pct, or a model that
    // never took `period`, must not slip past a bound the reader set.
    const rows = [
      histRow({ metrics: { cagr_pct: 10, worst_year_pct: -5 } }),
      histRow({ metrics: { cagr_pct: 10 } }), // no worst_year_pct
    ];
    const out = filterHistoryRows(rows, {
      ...NONE,
      ranges: { "metric:worst_year_pct": { min: -10, max: 0 } },
    });
    expect(out).toHaveLength(1);

    const paramRows = [
      histRow({ strategy_params: { period: 14 } }),
      histRow({ strategy_params: {} }),
    ];
    expect(
      filterHistoryRows(paramRows, { ...NONE, ranges: { "param:period": { min: 10, max: 20 } } }),
    ).toHaveLength(1);
  });

  it("is conjunctive across every clause", () => {
    const rows = [
      histRow({ name: "keep", ticker: "TQQQ", grid_step: 0.01, metrics: { cagr_pct: 25 } }),
      histRow({ name: "keep", ticker: "RSP", grid_step: 0.01, metrics: { cagr_pct: 25 } }),
      histRow({ name: "drop", ticker: "TQQQ", grid_step: 0.01, metrics: { cagr_pct: 25 } }),
      histRow({ name: "keep", ticker: "TQQQ", grid_step: 0.05, metrics: { cagr_pct: 25 } }),
      histRow({ name: "keep", ticker: "TQQQ", grid_step: 0.01, metrics: { cagr_pct: 1 } }),
    ];
    const out = filterHistoryRows(rows, {
      ...NONE,
      name: "keep",
      tickers: ["TQQQ"],
      ranges: { grid_step: { min: 0.5, max: 2 }, "metric:cagr_pct": { min: 10, max: null } },
    });
    expect(out).toHaveLength(1);
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
    expect(runHistoryFilterActive({ ...NONE, tickers: ["TQQQ"] })).toBe(true);
    expect(runHistoryFilterActive({ ...NONE, ranges: { grid_step: { min: 1, max: null } } })).toBe(
      true,
    );
  });
});

describe("historyInputFields", () => {
  it("always offers the two swept dimensions, with their distinct values sorted", () => {
    const rows = [
      histRow({ grid_step: 0.02 }),
      histRow({ grid_step: 0.005 }),
      histRow({ grid_step: 0.02 }),
    ];
    const fields = historyInputFields(rows);
    const gridStep = fields.find((f) => f.key === "grid_step")!;
    expect(gridStep.values).toEqual([0.5, 2]);
    expect(fields.some((f) => f.key === "profit_target")).toBe(true);
  });

  it("offers every numeric sizing-model argument and skips non-numeric ones", () => {
    const rows = [
      histRow({ strategy_params: { allocation_pct: 0.05 } }),
      histRow({ strategy_params: { max_trade_pct: 0.08, ticker: "COWZ" } }),
    ];
    const keys = historyInputFields(rows).map((f) => f.key);
    expect(keys).toContain("param:allocation_pct");
    expect(keys).toContain("param:max_trade_pct");
    expect(keys).not.toContain("param:ticker");
  });
});
