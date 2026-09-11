/**
 * Identifying and summarizing one sweep's configurations -- the cells a
 * grid_step x profit_target x strategy_params sweep produced.
 *
 * Pure, like lib/filters.ts and lib/sweepStrategies.ts: the only real
 * logic behind BacktestResult's sweep-summary section and configuration
 * list, covered in sweepSummary.test.ts.
 */
import type { ParamValue, SweepConfiguration } from "@/types/backtest";

function sortedParamEntries(
  params: SweepConfiguration["strategy_params"],
): [string, ParamValue][] {
  return Object.entries(params ?? {}).sort(([a], [b]) => a.localeCompare(b));
}

/**
 * A stable identity for one configuration: grid_step + profit_target +
 * its resolved strategy_params combo, together.
 *
 * grid_step/profit_target alone is not enough once a strategy param is
 * ALSO swept (several cells can share one pair); strategy_params alone
 * is not enough either -- two cells sharing one strategy_params combo but
 * differing in grid_step/profit_target would otherwise collide. That is
 * a real bug SweepMatrix.tsx's own narrower "Params" selector key
 * (strategy_params only, a different and smaller concern -- which
 * combo's HEATMAP SLICE to show) does not need to avoid, but this one
 * does: it identifies one exact cell, not a slice of many.
 */
export function configurationKey(config: SweepConfiguration): string {
  return JSON.stringify([
    config.grid_step,
    config.profit_target,
    sortedParamEntries(config.strategy_params),
  ]);
}

/** A human-readable label for one configuration. */
export function configurationLabel(config: SweepConfiguration): string {
  const base = `step ${(config.grid_step * 100).toFixed(2)}% · target ${(config.profit_target * 100).toFixed(2)}%`;
  const entries = sortedParamEntries(config.strategy_params);
  if (entries.length === 0) return base;
  return `${base} · ${entries.map(([key, value]) => `${key}=${value}`).join(", ")}`;
}

export interface SweepAxis {
  /** "grid_step" | "profit_target" | a strategy-param name. */
  key: string;
  label: string;
  /** Distinct values seen, sorted (numeric axes ascending, others
   * lexicographically). Always length > 1 -- see describeSweepAxes. */
  values: ParamValue[];
}

export interface SweepSummary {
  configurationCount: number;
  /** Only the axes that actually VARIED across `configurations` -- an
   * axis with one distinct value isn't part of "the sweep," so it's
   * omitted rather than reported as a no-op range. */
  axes: SweepAxis[];
}

function distinct<T extends ParamValue>(values: T[]): T[] {
  const seen: T[] = [];
  for (const value of values) {
    if (!seen.includes(value)) seen.push(value);
  }
  return seen;
}

function sortValues(values: ParamValue[]): ParamValue[] {
  if (values.every((value) => typeof value === "number")) {
    return [...(values as number[])].sort((a, b) => a - b);
  }
  return [...values].sort((a, b) => String(a).localeCompare(String(b)));
}

/**
 * Every axis actually varied across `configurations` -- the top of the
 * "sweep summary" section reads straight off this.
 */
export function describeSweepAxes(configurations: SweepConfiguration[]): SweepSummary {
  const axes: SweepAxis[] = [];

  const gridSteps = distinct(configurations.map((config) => config.grid_step));
  if (gridSteps.length > 1) {
    axes.push({ key: "grid_step", label: "Grid step", values: sortValues(gridSteps) });
  }

  const profitTargets = distinct(configurations.map((config) => config.profit_target));
  if (profitTargets.length > 1) {
    axes.push({ key: "profit_target", label: "Profit target", values: sortValues(profitTargets) });
  }

  const paramNames = new Set<string>();
  for (const config of configurations) {
    for (const name of Object.keys(config.strategy_params ?? {})) paramNames.add(name);
  }
  for (const name of [...paramNames].sort()) {
    const values = distinct(
      configurations
        .map((config) => config.strategy_params?.[name])
        .filter((value): value is ParamValue => value !== undefined),
    );
    if (values.length > 1) {
      axes.push({ key: name, label: name, values: sortValues(values) });
    }
  }

  return { configurationCount: configurations.length, axes };
}
