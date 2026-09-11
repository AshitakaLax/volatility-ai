/**
 * Turning a "Starting X / Ending X / Number of Steps" (or Min/Max/Count)
 * range into a concrete list of values to sweep -- the value-generation
 * half of the "enable sweep" checkbox. Unit-agnostic on purpose: it
 * knows nothing about percent domains or `/100` conversion, so the same
 * three generators serve grid step, profit target, and any arbitrary
 * numeric strategy param without being copied per argument. Callers own
 * their own domain rules (lib/gridSteps.ts's 0-100% bound; a strategy
 * param's own type/range) and convert before/after calling in here.
 *
 * Pure, like lib/filters.ts and lib/strategyParams.ts -- covered in
 * sweepStrategies.test.ts.
 *
 * FIVE STRATEGIES ARE NAMED, ONLY THREE GENERATE VALUES TODAY.
 * Multi-Resolution (coarse-to-fine) and Adaptive/Heuristic both imply a
 * coarse pass, inspecting its results, then refining -- genuine
 * multi-round orchestration nothing reachable from the web submit path
 * does today (src/optimization/search_strategies.py's GridSearch/
 * RandomSearch/BayesianSearch all enumerate or sample an ALREADY-fixed
 * discrete space; none of them expand a range themselves, and none
 * re-visits a combination after seeing its result). Faking either as a
 * static list would claim behavior that does not exist, so both are
 * stubs: they exist only so `SweepStrategyKind`/`buildSweepValues`'s
 * dispatch is exhaustive, and the UI renders them as disabled
 * "(coming soon)" entries rather than ever calling them for real values.
 */

export type SweepStrategyKind =
  | "linear"
  | "logarithmic"
  | "random"
  | "multi_resolution"
  | "adaptive";

/** The two strategies not yet implemented -- kept in one place so the
 * dropdown can grey them out without hand-listing them twice. */
export const UNIMPLEMENTED_SWEEP_STRATEGIES: readonly SweepStrategyKind[] = [
  "multi_resolution",
  "adaptive",
];

/** Same ceiling `RunRequest.grid_steps`/`profit_targets` enforce
 * server-side (`Field(..., max_length=12)`) -- kept here, not
 * re-declared per caller, so grid step, profit target, and a swept
 * strategy param all agree on one number. */
export const MAX_SWEEP_POINTS = 12;

export interface SweepGenerationInput {
  min: number;
  max: number;
  count: number;
  /** "random" only: blank/non-numeric -> Math.random() (a fresh list
   * each time); a numeric seed -> the same list every time. */
  seed?: string | undefined;
}

export interface SweepGenerationOptions {
  /** Round every generated point to the nearest whole number before
   * dedupe -- for sweeping a `type: "int"` param (e.g. bars_per_day),
   * so a linear sweep never emits 387.33. */
  integer: boolean;
}

export interface SweepGenerationResult {
  /** Ascending, de-duped, 1..MAX_SWEEP_POINTS entries when `errors` is
   * empty; always `[]` when it is not -- an invalid input never
   * transiently produces a partial or oversized array. */
  values: number[];
  errors: string[];
}

/** Kill float dust the way lib/gridSteps.ts's own `round()` does --
 * shared here so every strategy dedupes on the same resolution. */
function round(value: number): number {
  return Number(value.toFixed(10));
}

function finalize(points: number[], opts: SweepGenerationOptions): number[] {
  const rounded = points.map((point) => (opts.integer ? Math.round(point) : round(point)));
  return [...new Set(rounded)].sort((a, b) => a - b);
}

/** Validates `rawCount`, pushing an error if it fails, and returns the
 * CLAMPED count to generate with regardless -- so a pasted 99 never
 * transiently builds a 99-element array even while the error shows. */
function resolveCount(rawCount: number, errors: string[]): number {
  if (!Number.isInteger(rawCount) || rawCount < 1 || rawCount > MAX_SWEEP_POINTS) {
    errors.push(`count must be a whole number from 1 to ${MAX_SWEEP_POINTS}`);
  }
  return Math.min(MAX_SWEEP_POINTS, Math.max(1, Math.trunc(rawCount) || 1));
}

export function buildLinearSweep(
  input: SweepGenerationInput,
  opts: SweepGenerationOptions,
): SweepGenerationResult {
  const { min, max } = input;
  const errors: string[] = [];
  if (!Number.isFinite(min) || !Number.isFinite(max)) {
    errors.push("enter a numeric min and max");
  }
  const count = resolveCount(input.count, errors);
  if (count > 1 && Number.isFinite(min) && Number.isFinite(max) && min >= max) {
    errors.push("min must be below max (use a single point, or count 1, for a fixed value)");
  }
  if (errors.length > 0) return { values: [], errors };

  const points =
    count === 1 ? [min] : Array.from({ length: count }, (_, i) => min + (i * (max - min)) / (count - 1));
  return { values: finalize(points, opts), errors: [] };
}

export function buildLogarithmicSweep(
  input: SweepGenerationInput,
  opts: SweepGenerationOptions,
): SweepGenerationResult {
  const { min, max } = input;
  const errors: string[] = [];
  if (!Number.isFinite(min) || !Number.isFinite(max)) {
    errors.push("enter a numeric min and max");
  } else if (min <= 0 || max <= 0) {
    // log is undefined at/below zero -- a step-percent or a strategy
    // param sweeping through zero has no meaningful log spacing.
    errors.push("logarithmic sweep requires values greater than 0");
  }
  const count = resolveCount(input.count, errors);
  if (
    count > 1 &&
    Number.isFinite(min) &&
    Number.isFinite(max) &&
    min > 0 &&
    max > 0 &&
    min >= max
  ) {
    errors.push("min must be below max (use a single point, or count 1, for a fixed value)");
  }
  if (errors.length > 0) return { values: [], errors };

  const points =
    count === 1
      ? [min]
      : Array.from({ length: count }, (_, i) => min * Math.pow(max / min, i / (count - 1)));
  return { values: finalize(points, opts), errors: [] };
}

/** A tiny, dependency-free deterministic PRNG (mulberry32) -- only so a
 * numeric seed reproduces the same list twice. Not cryptographic, and
 * does not need to be: this picks display values for a form, not
 * anything security-sensitive. */
function mulberry32(seed: number): () => number {
  let state = seed | 0;
  return () => {
    state = (state + 0x6d2b79f5) | 0;
    let t = Math.imul(state ^ (state >>> 15), 1 | state);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

export function buildRandomSweep(
  input: SweepGenerationInput,
  opts: SweepGenerationOptions,
): SweepGenerationResult {
  const { min, max } = input;
  const errors: string[] = [];
  if (!Number.isFinite(min) || !Number.isFinite(max)) {
    errors.push("enter a numeric min and max");
  }
  const count = resolveCount(input.count, errors);
  // Unlike linear/logarithmic, a degenerate range is a hard error even
  // at count 1 -- "sample N points in a range" has no meaning over a
  // range that isn't one. Use Fixed for a single known value.
  if (Number.isFinite(min) && Number.isFinite(max) && min >= max) {
    errors.push("min must be below max");
  }
  if (errors.length > 0) return { values: [], errors };

  const seedText = (input.seed ?? "").trim();
  const seedNumber = seedText === "" ? Number.NaN : Number(seedText);
  const random = Number.isFinite(seedNumber) ? mulberry32(seedNumber) : Math.random;
  const points = Array.from({ length: count }, () => min + random() * (max - min));
  return { values: finalize(points, opts), errors: [] };
}

export function buildMultiResolutionSweep(
  _input: SweepGenerationInput,
  _opts: SweepGenerationOptions,
): SweepGenerationResult {
  return { values: [], errors: ["multi-resolution sweep is not implemented yet"] };
}

export function buildAdaptiveSweep(
  _input: SweepGenerationInput,
  _opts: SweepGenerationOptions,
): SweepGenerationResult {
  return { values: [], errors: ["adaptive sweep is not implemented yet"] };
}

/**
 * One sweepable argument's "enable sweep" checkbox state, held by
 * ParameterForm as `Record<argument name, SweepFieldState>` -- one entry
 * for `grid_step`, one for `profit_target`, and one per sweepable
 * strategy param (`ParamSpec.sweepable`). Raw text throughout, like
 * lib/strategyParams.ts's `paramValues`: `""` is the distinct
 * blank/unset state, and every input in the form emits strings anyway.
 */
export interface SweepFieldState {
  enabled: boolean;
  /** Only meaningful while `enabled`; shown by the "Sweep strategy"
   * dropdown. */
  strategy: SweepStrategyKind;
  /** "Starting X" (Linear/Logarithmic) or "Min X" (Random). */
  start: string;
  /** "Ending X" (Linear/Logarithmic) or "Max X" (Random). */
  end: string;
  /** "Number of Steps" / sample count. */
  count: string;
  /** "random" only, optional. */
  seed: string;
}

export const DEFAULT_SWEEP_FIELD_STATE: SweepFieldState = {
  enabled: false,
  strategy: "linear",
  start: "",
  end: "",
  count: "5",
  seed: "",
};

/** Dispatches to the generator named by `strategy`. The one call site a
 * caller needs -- lib/gridSteps.ts and lib/strategyParams.ts both go
 * through this rather than switching on the strategy themselves. */
export function buildSweepValues(
  strategy: SweepStrategyKind,
  input: SweepGenerationInput,
  opts: SweepGenerationOptions,
): SweepGenerationResult {
  switch (strategy) {
    case "linear":
      return buildLinearSweep(input, opts);
    case "logarithmic":
      return buildLogarithmicSweep(input, opts);
    case "random":
      return buildRandomSweep(input, opts);
    case "multi_resolution":
      return buildMultiResolutionSweep(input, opts);
    case "adaptive":
      return buildAdaptiveSweep(input, opts);
  }
}
