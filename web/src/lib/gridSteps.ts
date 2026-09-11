/**
 * Turning the "Grid step" panel's Fixed | Sweep inputs into the
 * `grid_steps` list the backtest engine sweeps.
 *
 * Pure, like lib/filters.ts and lib/strategyParams.ts. The engine takes
 * `grid_steps` as a 1..12 list of fractions (`server/backtest.py`
 * RunRequest, `src/analysis/validation.validate_grid_steps`); a Fixed
 * step is just a one-element sweep. Every value that reaches the wire is
 * validated here so a bad bound is a red line under the field, never a
 * 400 on Run or an oversized array Pydantic rejects.
 *
 * The Sweep-mode point math itself (Linear / Logarithmic / Random) lives
 * in lib/sweepStrategies.ts, unit-agnostic -- this module owns only the
 * PERCENT-domain rules (0 < pct < 100, the `/100` conversion) and stays
 * the one place profit target (which shares that same domain) goes
 * through too.
 */
import { buildSweepValues, MAX_SWEEP_POINTS, type SweepStrategyKind } from "./sweepStrategies";

/** Kill the float dust a `/100` conversion leaves: 0.5 % -> 0.005, not
 * 0.004999999999999999. */
function round(value: number): number {
  return Number(value.toFixed(10));
}

export type StepMode = "fixed" | "sweep";

export interface GridStepInput {
  mode: StepMode;
  /** Raw text of the single Fixed-mode input, a PERCENT. */
  fixedPct: string;
  /** Raw text of the Sweep min / max (PERCENT) and count. */
  minPct: string;
  maxPct: string;
  count: string;
  /** Which sweep-value generator to use in "sweep" mode. Defaults to
   * "linear" -- the only strategy this ever supported before the
   * per-argument sweep-strategy dropdown existed. */
  strategy?: SweepStrategyKind;
  /** "random" strategy only: reproducibility seed, passed straight
   * through to sweepStrategies.ts. */
  seed?: string;
}

export interface GridStepResult {
  /** Fractions, ascending, de-duped. 1..12 entries when `errors` is
   * empty; may be `[]` mid-edit. */
  steps: number[];
  errors: string[];
}

function pctInRange(value: number): boolean {
  return Number.isFinite(value) && value > 0 && value < 100;
}

/** The `grid_steps` list (fractions) for the current panel state, plus
 * any client-side errors. */
export function buildGridSteps(input: GridStepInput): GridStepResult {
  if (input.mode === "fixed") {
    const pct = Number(input.fixedPct);
    if (!pctInRange(pct)) {
      return { steps: [], errors: ["grid step must be between 0 and 100%"] };
    }
    return { steps: [round(pct / 100)], errors: [] };
  }

  const errors: string[] = [];
  const min = Number(input.minPct);
  const max = Number(input.maxPct);

  if (input.minPct.trim() === "" || input.maxPct.trim() === "" || !Number.isFinite(min) || !Number.isFinite(max)) {
    errors.push("enter a numeric min and max");
  } else if (!pctInRange(min) || !pctInRange(max)) {
    errors.push("each step must be between 0 and 100%");
  }
  if (errors.length > 0) return { steps: [], errors };

  const generated = buildSweepValues(
    input.strategy ?? "linear",
    { min, max, count: Number(input.count), seed: input.seed },
    { integer: false },
  );
  if (generated.errors.length > 0) return { steps: [], errors: generated.errors };

  // Re-dedupe AFTER the /100 conversion, not just before it: two points
  // sweepStrategies.ts kept distinct at percent-scale can still collide
  // once divided down to a fraction (this is exactly how the old
  // fixed/sweep code worked, and a real case -- see gridSteps.test.ts's
  // "bounds closer than the fraction resolution" case).
  const steps = [...new Set(generated.values.map((point) => round(point / 100)))].sort(
    (a, b) => a - b,
  );
  return { steps, errors: [] };
}

export { MAX_SWEEP_POINTS };
