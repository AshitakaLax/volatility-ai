/**
 * The submitted-request counterpart to sweepSummary.ts: what a sweep
 * covers BEFORE it has completed metrics. Each case below is one where
 * a wrong answer (an undercounted simulation total, an axis reported as
 * swept when it never varied) looks fine on screen until the number
 * shown doesn't match what the engine actually ran.
 */
import { describe, expect, it } from "vitest";

import { describeRequestAxes, expandStrategyParams } from "./requestSummary";

describe("expandStrategyParams", () => {
  it("no strategy_params at all yields one empty combination, not zero", () => {
    expect(expandStrategyParams(undefined)).toEqual([{}]);
  });

  it("an empty object yields one empty combination", () => {
    expect(expandStrategyParams({})).toEqual([{}]);
  });

  it("all-scalar params pass through as a single combination", () => {
    expect(expandStrategyParams({ a: 1, b: "x", c: true })).toEqual([{ a: 1, b: "x", c: true }]);
  });

  it("one swept key produces one combination per value, fixed keys repeated", () => {
    const out = expandStrategyParams({ a: [1, 2], b: 3 });
    expect(out).toEqual([
      { a: 1, b: 3 },
      { a: 2, b: 3 },
    ]);
  });

  it("two swept keys cross-product", () => {
    const out = expandStrategyParams({ a: [1, 2], b: ["x", "y"] });
    expect(out).toHaveLength(4);
    expect(out).toEqual(
      expect.arrayContaining([
        { a: 1, b: "x" },
        { a: 1, b: "y" },
        { a: 2, b: "x" },
        { a: 2, b: "y" },
      ]),
    );
  });

  it("an empty swept list is skipped rather than throwing", () => {
    expect(() => expandStrategyParams({ a: [] })).not.toThrow();
  });
});

describe("describeRequestAxes", () => {
  it("a single-value, single-ticker request is exactly one simulation", () => {
    const summary = describeRequestAxes({
      grid_steps: [0.01],
      profit_targets: [0.005],
      tickers: ["TQQQ"],
    });
    expect(summary.simulationCount).toBe(1);
    expect(summary.axes).toEqual([]);
  });

  it("multiplies every axis together, including a strategy-param sweep and multiple tickers", () => {
    const summary = describeRequestAxes({
      grid_steps: [0.01, 0.02, 0.03],
      profit_targets: [0.005, 0.01],
      strategy_params: { max_trade_pct: [0.05, 0.08] },
      tickers: ["TQQQ", "SOXL"],
    });
    // 3 steps x 2 targets x 2 strategy-param combos x 2 tickers
    expect(summary.simulationCount).toBe(24);
  });

  it("reports grid_step/profit_target axes only when they actually vary", () => {
    const swept = describeRequestAxes({
      grid_steps: [0.01, 0.02],
      profit_targets: [0.005],
      tickers: ["TQQQ"],
    });
    expect(swept.axes.map((a) => a.key)).toEqual(["grid_step"]);

    const fixed = describeRequestAxes({
      grid_steps: [0.01],
      profit_targets: [0.005],
      tickers: ["TQQQ"],
    });
    expect(fixed.axes).toEqual([]);
  });

  it("reports a swept strategy param as its own axis", () => {
    const summary = describeRequestAxes({
      grid_steps: [0.01],
      profit_targets: [0.005],
      strategy_params: { lookback_days: [10, 20, 30] },
      tickers: ["TQQQ"],
    });
    const axis = summary.axes.find((a) => a.key === "lookback_days");
    expect(axis?.values).toEqual([10, 20, 30]);
  });

  it("does not report a strategy param with only one distinct value", () => {
    const summary = describeRequestAxes({
      grid_steps: [0.01],
      profit_targets: [0.005],
      strategy_params: { lookback_days: [10, 10], max_trade_pct: 0.05 },
      tickers: ["TQQQ"],
    });
    expect(summary.axes).toEqual([]);
  });

  it("reports multiple tickers as an axis", () => {
    const summary = describeRequestAxes({
      grid_steps: [0.01],
      profit_targets: [0.005],
      tickers: ["TQQQ", "SOXL"],
    });
    expect(summary.axes).toEqual([{ key: "tickers", label: "Funds", values: ["SOXL", "TQQQ"] }]);
  });
});
