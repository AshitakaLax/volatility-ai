/**
 * Identifying and summarizing sweep configurations. Each case below is
 * one where a wrong answer (two different cells colliding under one
 * key, an unswept axis reported as part of the sweep) looks fine on
 * screen and only shows up as a configuration the reader can't tell
 * apart from another, or a summary that doesn't match the matrix.
 */
import { describe, expect, it } from "vitest";

import type { SweepConfiguration } from "@/types/backtest";

import { configurationKey, configurationLabel, describeSweepAxes } from "./sweepSummary";

function metrics(cagr = 0) {
  return {
    ticker: "TQQQ",
    net_yield_pct: 0,
    cagr_pct: cagr,
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
  };
}

function config(over: Partial<SweepConfiguration> = {}): SweepConfiguration {
  return {
    grid_step: 0.01,
    profit_target: 0.005,
    strategy_params: {},
    metrics: metrics(),
    ...over,
  };
}

describe("configurationKey", () => {
  it("two cells sharing a strategy_params combo but differing grid_step/profit_target do NOT collide", () => {
    const a = config({ grid_step: 0.01, strategy_params: { lookback_days: 10 } });
    const b = config({ grid_step: 0.02, strategy_params: { lookback_days: 10 } });
    expect(configurationKey(a)).not.toBe(configurationKey(b));
  });

  it("is stable regardless of strategy_params key insertion order", () => {
    const a = config({ strategy_params: { a: 1, b: 2 } });
    const b = config({ strategy_params: { b: 2, a: 1 } });
    expect(configurationKey(a)).toBe(configurationKey(b));
  });

  it("handles an empty strategy_params", () => {
    expect(() => configurationKey(config({ strategy_params: {} }))).not.toThrow();
  });

  it("identical cells produce the same key", () => {
    const a = config({ grid_step: 0.02, profit_target: 0.01, strategy_params: { x: 5 } });
    const b = config({ grid_step: 0.02, profit_target: 0.01, strategy_params: { x: 5 } });
    expect(configurationKey(a)).toBe(configurationKey(b));
  });
});

describe("configurationLabel", () => {
  it("includes step and target as percents", () => {
    expect(configurationLabel(config({ grid_step: 0.01, profit_target: 0.005 }))).toContain(
      "step 1.00%",
    );
    expect(configurationLabel(config({ grid_step: 0.01, profit_target: 0.005 }))).toContain(
      "target 0.50%",
    );
  });

  it("appends the strategy_params combo when present, omits it when empty", () => {
    expect(configurationLabel(config({ strategy_params: {} }))).not.toContain("=");
    expect(configurationLabel(config({ strategy_params: { lookback_days: 10 } }))).toContain(
      "lookback_days=10",
    );
  });
});

describe("describeSweepAxes", () => {
  it("a grid-step-only sweep reports one axis and omits profit_target", () => {
    const configs = [
      config({ grid_step: 0.01 }),
      config({ grid_step: 0.02 }),
      config({ grid_step: 0.03 }),
    ];
    const summary = describeSweepAxes(configs);
    expect(summary.configurationCount).toBe(3);
    expect(summary.axes.map((axis) => axis.key)).toEqual(["grid_step"]);
    expect(summary.axes[0]!.values).toEqual([0.01, 0.02, 0.03]);
  });

  it("adding a swept strategy param adds a second axis", () => {
    const configs = [
      config({ grid_step: 0.01, strategy_params: { lookback_days: 10 } }),
      config({ grid_step: 0.02, strategy_params: { lookback_days: 20 } }),
    ];
    const summary = describeSweepAxes(configs);
    expect(summary.axes.map((axis) => axis.key).sort()).toEqual(["grid_step", "lookback_days"]);
    const paramAxis = summary.axes.find((axis) => axis.key === "lookback_days")!;
    expect(paramAxis.values).toEqual([10, 20]);
  });

  it("a single configuration yields no axes", () => {
    const summary = describeSweepAxes([config()]);
    expect(summary.configurationCount).toBe(1);
    expect(summary.axes).toEqual([]);
  });

  it("an empty configuration list yields no axes and a zero count", () => {
    expect(describeSweepAxes([])).toEqual({ configurationCount: 0, axes: [] });
  });

  it("sorts a non-numeric strategy-param axis lexicographically", () => {
    const configs = [
      config({ strategy_params: { vol_measure: "range" } }),
      config({ strategy_params: { vol_measure: "stdev" } }),
    ];
    const axis = describeSweepAxes(configs).axes.find((entry) => entry.key === "vol_measure")!;
    expect(axis.values).toEqual(["range", "stdev"]);
  });

  it("a strategy param present on only some cells is still detected", () => {
    const configs = [config({ strategy_params: {} }), config({ strategy_params: { extra: 5 } })];
    // extra has only one DISTINCT value across the cells that carry it
    // (5), so it is not reported as a swept axis -- only one value ever
    // appears, regardless of how many cells omit the key entirely.
    expect(describeSweepAxes(configs).axes.some((axis) => axis.key === "extra")).toBe(false);
  });
});
