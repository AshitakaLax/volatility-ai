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
 */

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
}

export interface GridStepResult {
  /** Fractions, ascending, de-duped. 1..12 entries when `errors` is
   * empty; may be `[]` mid-edit. */
  steps: number[];
  errors: string[];
}

const MAX_STEPS = 12;

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
  const rawCount = Number(input.count);

  if (input.minPct.trim() === "" || input.maxPct.trim() === "" || !Number.isFinite(min) || !Number.isFinite(max)) {
    errors.push("enter a numeric min and max");
  } else if (!pctInRange(min) || !pctInRange(max)) {
    errors.push("each step must be between 0 and 100%");
  }

  if (!Number.isInteger(rawCount) || rawCount < 1 || rawCount > MAX_STEPS) {
    errors.push(`count must be a whole number from 1 to ${MAX_STEPS}`);
  }

  // Clamp for GENERATION regardless, so a pasted 99 never transiently
  // builds a 99-element array even while the error above is showing.
  const count = Math.min(MAX_STEPS, Math.max(1, Math.trunc(rawCount) || 1));

  if (count > 1 && Number.isFinite(min) && Number.isFinite(max) && min >= max) {
    errors.push("sweep min must be below max (use Fixed, or count 1, for a single value)");
  }

  if (errors.length > 0) return { steps: [], errors };

  const points: number[] =
    count === 1 ? [min] : Array.from({ length: count }, (_, i) => min + (i * (max - min)) / (count - 1));
  const steps = [...new Set(points.map((point) => round(point / 100)))].sort((a, b) => a - b);
  return { steps, errors: [] };
}
