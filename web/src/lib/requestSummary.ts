/**
 * What a SUBMITTED (not yet completed) sweep covers.
 *
 * lib/sweepSummary.ts's describeSweepAxes() answers the same question
 * for a COMPLETED report's `SweepConfiguration[]` -- which requires a
 * `metrics` per cell, i.e. only exists once a run finishes. A queued or
 * running job has no such data; all that exists is the raw request it
 * was submitted with. This file answers the prior question -- "how many
 * simulations did this submission ask for" -- from that raw shape
 * instead, so ActiveRuns can describe a sweep before it completes.
 *
 * Pure, like lib/sweepSummary.ts and lib/filters.ts. Covered in
 * requestSummary.test.ts.
 */
import { distinct, sortValues } from "@/lib/sweepSummary";
import type { ParamValue } from "@/types/backtest";

/**
 * A TS port of src/core/config.py's expand_strategy_params: a list
 * value is ALWAYS a sweep axis, never a literal value; scalars pass
 * through untouched. Ported rather than re-derived so a
 * frontend-computed simulation count matches the engine's own
 * combinations count exactly, not an approximation of it.
 *
 * `{}` or no strategy_params at all -> `[{}]` (one, empty, combination)
 * -- mirrors the Python's own "no params" case, not zero combinations.
 */
export function expandStrategyParams(
  params: Record<string, ParamValue | ParamValue[]> | undefined,
): Record<string, ParamValue>[] {
  if (!params || Object.keys(params).length === 0) return [{}];

  const swept = Object.entries(params).filter(
    (entry): entry is [string, ParamValue[]] => Array.isArray(entry[1]),
  );
  if (swept.length === 0) return [params as Record<string, ParamValue>];

  // An empty list is a real request-shape problem (it would silently
  // sweep nothing), but this runs on an already-accepted, already-queued
  // job -- not pre-submission validation, which is `/validate`'s job.
  // Skip it rather than throw, so one malformed axis on a job the
  // server already accepted doesn't crash the running-sweeps display.
  const fixed = Object.fromEntries(
    Object.entries(params).filter((entry) => !Array.isArray(entry[1])),
  ) as Record<string, ParamValue>;
  let combinations: Record<string, ParamValue>[] = [{}];
  for (const [key, values] of swept) {
    if (values.length === 0) continue;
    combinations = combinations.flatMap((combo) => values.map((value) => ({ ...combo, [key]: value })));
  }
  return combinations.map((combo) => ({ ...fixed, ...combo }));
}

export interface RequestAxis {
  /** "grid_step" | "profit_target" | "tickers" | a strategy-param name. */
  key: string;
  label: string;
  /** Distinct values seen, sorted. Always length > 1 -- see
   * describeRequestAxes. */
  values: ParamValue[];
}

export interface RequestSummary {
  /** grid_steps.length * profit_targets.length *
   * expandStrategyParams(strategy_params).length * tickers.length. */
  simulationCount: number;
  /** Only the axes that actually vary across this submission -- an
   * axis with one value isn't part of "the sweep." */
  axes: RequestAxis[];
}

/**
 * What a submitted request covers: how many simulations, and which
 * arguments actually vary. Mirrors describeSweepAxes()'s "only report
 * what varies" convention, from the request shape instead of a
 * completed report's configurations.
 *
 * ACCEPTED APPROXIMATION: server/backtest.py's run_backtest() filters
 * `tickers` down to those with an actual local data file before
 * computing its own total_units; this uses the submitted ticker list
 * as-is. ParameterForm only offers tickers /funds already reports as
 * available, so this shouldn't diverge through the UI -- a sweep
 * submitted some other way with an unavailable ticker would see a
 * slightly optimistic count here, consistent with this feature's
 * resolved scope (aggregate, request-derived progress, not a live
 * mirror of exactly what the engine iterates).
 */
export function describeRequestAxes(request: {
  grid_steps: number[];
  profit_targets: number[];
  strategy_params?: Record<string, ParamValue | ParamValue[]>;
  tickers: string[];
}): RequestSummary {
  const strategyParamsGrid = expandStrategyParams(request.strategy_params);
  const simulationCount =
    request.grid_steps.length *
    request.profit_targets.length *
    strategyParamsGrid.length *
    request.tickers.length;

  const axes: RequestAxis[] = [];
  if (request.grid_steps.length > 1) {
    axes.push({ key: "grid_step", label: "Grid step", values: sortValues(request.grid_steps) });
  }
  if (request.profit_targets.length > 1) {
    axes.push({
      key: "profit_target",
      label: "Profit target",
      values: sortValues(request.profit_targets),
    });
  }
  for (const [name, value] of Object.entries(request.strategy_params ?? {})) {
    if (Array.isArray(value) && distinct(value).length > 1) {
      axes.push({ key: name, label: name, values: sortValues(value) });
    }
  }
  if (request.tickers.length > 1) {
    axes.push({ key: "tickers", label: "Funds", values: [...request.tickers].sort() });
  }

  return { simulationCount, axes };
}
