/**
 * The frontend's only real logic, tested.
 *
 * Everything else in this app renders data it was handed. These
 * functions DECIDE things -- which executions belong to which lot, which
 * survive a filter, how minute bars roll up -- and each of the cases
 * below is one where the wrong answer looks entirely plausible on screen.
 */
import { describe, expect, it } from "vitest";

import type { BacktestExecution, ExecutionFilters } from "@/types/backtest";

import { aggregate, buildCycles, filterExecutions, lotIdOf, openLotIds } from "./filters";

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
  timeframe: "1Day",
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
