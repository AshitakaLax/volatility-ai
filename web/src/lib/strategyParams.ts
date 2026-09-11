/**
 * Turning a sizing model's parameter schema into form state and back
 * into a `strategy_params` payload.
 *
 * Pure functions, like lib/filters.ts: the only real logic the frontend
 * has, and the part where a wrong answer (a stray key, a float where an
 * int is wanted, sending a field the server aligns itself) looks
 * entirely plausible until a run dies. Covered in strategyParams.test.ts.
 *
 * THE SERVER DOES NOT COERCE `strategy_params`. Every value is handed to
 * the constructor exactly as JSON parsed it, so an `int` field must go
 * out as `387`, not `387.0`, and a `bool` as `true`, not `"true"`.
 */
import { buildSweepValues, type SweepFieldState, type SweepGenerationResult } from "@/lib/sweepStrategies";
import type { ParamSpec, ParamValue, ValidateError } from "@/types/backtest";

/**
 * The value a field is seeded to and that "reset" restores, held as a
 * STRING: `""` is the distinct "blank / unset" state (never the same as
 * `"0"`), and every input in the form emits strings anyway. A `null`
 * suggestion (no committed value, `None` default) seeds blank.
 */
export function seedOf(spec: ParamSpec): string {
  return spec.suggested == null ? "" : String(spec.suggested);
}

/**
 * The initial per-field text map for a model's specs. `mirrors` fields
 * are left out entirely -- they are not stored, they render from the
 * live Profit target input -- so replacing this map on a model change is
 * exactly "add the new model's fields, drop the old one's".
 */
export function seedValues(specs: ParamSpec[]): Record<string, string> {
  const out: Record<string, string> = {};
  for (const spec of specs) {
    if (spec.mirrors !== null) continue;
    out[spec.name] = seedOf(spec);
  }
  return out;
}

function parseValue(spec: ParamSpec, raw: string): ParamValue {
  if (spec.type === "bool") return raw === "true";
  if (spec.enum || spec.type === "str") return raw;
  if (spec.type === "int") return parseInt(raw, 10);
  return Number(raw);
}

/**
 * A sweepable strategy param's "enable sweep" state -> the concrete
 * value list to submit for it, via lib/sweepStrategies.ts's generators.
 * Unlike grid step / profit target (lib/gridSteps.ts), a strategy param
 * has no fixed percent domain -- bounds are whatever raw numbers the
 * param's own range is, and `opts.integer` follows `spec.type` so a
 * sweep over an `int` param never emits a fraction.
 */
export function buildParamSweep(spec: ParamSpec, sweep: SweepFieldState): SweepGenerationResult {
  if (sweep.start.trim() === "" || sweep.end.trim() === "") {
    return { values: [], errors: ["enter a numeric min and max"] };
  }
  return buildSweepValues(
    sweep.strategy,
    { min: Number(sweep.start), max: Number(sweep.end), count: Number(sweep.count), seed: sweep.seed },
    { integer: spec.type === "int" },
  );
}

/**
 * The `strategy_params` object to submit for `specs` given the current
 * field text `values`, and (per sweepable field) the "enable sweep"
 * state in `sweepFields`.
 *
 * INCLUDED: an editable field with a non-blank value that is either a
 * committed default (`has_suggested`) or has been moved off its
 * constructor default. Plus `ticker` for the ml models (required, and
 * the server does not inject it). A `spec.sweepable` field whose sweep
 * is enabled and resolves cleanly is sent as a LIST -- the server-side
 * counterpart of grid_steps/profit_targets already sweeping this way
 * (`expand_strategy_params`).
 *
 * OMITTED: blank fields (never sent as `null`/`""`); any `mirrors` field
 * (`target_return` -- the server aligns it to the grid); `editable:false`
 * fields other than `ticker` (`percentage`, `baseline_price` -- the
 * engine owns them); optional advanced fields left at their default; a
 * swept field whose range currently has client errors (the Run button
 * is disabled in that state -- this is defense in depth, not load-bearing).
 *
 * A no-edit submit therefore sends exactly the model's committed
 * defaults -- byte-identical to the old blind `sizing_details.defaults`
 * splat and to what the server's empty-`strategy_params` fallback
 * produces.
 */
export function buildStrategyParams(
  specs: ParamSpec[],
  values: Record<string, string>,
  sweepFields: Record<string, SweepFieldState> = {},
): Record<string, ParamValue | ParamValue[]> {
  const out: Record<string, ParamValue | ParamValue[]> = {};
  for (const spec of specs) {
    if (spec.mirrors !== null) continue;
    if (!spec.editable && spec.name !== "ticker") continue;
    const sweep = spec.sweepable ? sweepFields[spec.name] : undefined;
    if (sweep?.enabled) {
      const generated = buildParamSweep(spec, sweep);
      if (generated.errors.length === 0 && generated.values.length > 0) {
        out[spec.name] = generated.values;
      }
      continue;
    }
    const raw = (values[spec.name] ?? "").trim();
    if (raw === "") continue;
    const value = parseValue(spec, raw);
    if (typeof value === "number" && Number.isNaN(value)) continue;
    if (spec.has_suggested || String(value) !== String(spec.default)) {
      out[spec.name] = value;
    }
  }
  return out;
}

export interface ParamDiff {
  name: string;
  from: string;
  to: string;
}

/** Editable, non-mirrored fields whose current value differs from their
 * seed -- what the "differs from committed defaults" readout shows. A
 * swept field always counts as changed (there is no single seed value
 * to compare against once it is a range), shown as "swept". */
export function diffFromDefaults(
  specs: ParamSpec[],
  values: Record<string, string>,
  sweepFields: Record<string, SweepFieldState> = {},
): ParamDiff[] {
  const out: ParamDiff[] = [];
  for (const spec of specs) {
    if (!spec.editable || spec.mirrors !== null) continue;
    const sweep = spec.sweepable ? sweepFields[spec.name] : undefined;
    if (sweep?.enabled) {
      out.push({ name: spec.name, from: seedOf(spec) || "—", to: "swept" });
      continue;
    }
    const now = values[spec.name] ?? "";
    const seed = seedOf(spec);
    if (now !== seed) out.push({ name: spec.name, from: seed || "—", to: now || "—" });
  }
  return out;
}

/** Required editable fields left blank -- the run cannot be submitted
 * while any of these exist. A required field whose sweep is enabled and
 * resolves to at least one value is NOT blank, even though its scalar
 * text is -- the sweep supplies the value(s) instead. */
export function blankRequired(
  specs: ParamSpec[],
  values: Record<string, string>,
  sweepFields: Record<string, SweepFieldState> = {},
): string[] {
  return specs
    .filter((spec) => {
      if (!spec.editable || !spec.required) return false;
      const sweep = spec.sweepable ? sweepFields[spec.name] : undefined;
      if (sweep?.enabled) {
        const generated = buildParamSweep(spec, sweep);
        return generated.errors.length > 0 || generated.values.length === 0;
      }
      return (values[spec.name] ?? "").trim() === "";
    })
    .map((spec) => spec.name);
}

/** The validation errors pinned to one field (or the unattached ones
 * when `name` is null). */
export function paramErrorsFor(
  name: string | null,
  errors: ValidateError[] | undefined,
): ValidateError[] {
  if (!errors) return [];
  return errors.filter((error) => error.field === name);
}
