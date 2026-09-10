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
 * The `strategy_params` object to submit for `specs` given the current
 * field text `values`.
 *
 * INCLUDED: an editable field with a non-blank value that is either a
 * committed default (`has_suggested`) or has been moved off its
 * constructor default. Plus `ticker` for the ml models (required, and
 * the server does not inject it).
 *
 * OMITTED: blank fields (never sent as `null`/`""`); any `mirrors` field
 * (`target_return` -- the server aligns it to the grid); `editable:false`
 * fields other than `ticker` (`percentage`, `baseline_price` -- the
 * engine owns them); optional advanced fields left at their default.
 *
 * A no-edit submit therefore sends exactly the model's committed
 * defaults -- byte-identical to the old blind `sizing_details.defaults`
 * splat and to what the server's empty-`strategy_params` fallback
 * produces.
 */
export function buildStrategyParams(
  specs: ParamSpec[],
  values: Record<string, string>,
): Record<string, ParamValue> {
  const out: Record<string, ParamValue> = {};
  for (const spec of specs) {
    if (spec.mirrors !== null) continue;
    if (!spec.editable && spec.name !== "ticker") continue;
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
 * seed -- what the "differs from committed defaults" readout shows. */
export function diffFromDefaults(
  specs: ParamSpec[],
  values: Record<string, string>,
): ParamDiff[] {
  const out: ParamDiff[] = [];
  for (const spec of specs) {
    if (!spec.editable || spec.mirrors !== null) continue;
    const now = values[spec.name] ?? "";
    const seed = seedOf(spec);
    if (now !== seed) out.push({ name: spec.name, from: seed || "—", to: now || "—" });
  }
  return out;
}

/** Required editable fields left blank -- the run cannot be submitted
 * while any of these exist. */
export function blankRequired(
  specs: ParamSpec[],
  values: Record<string, string>,
): string[] {
  return specs
    .filter(
      (spec) => spec.editable && spec.required && (values[spec.name] ?? "").trim() === "",
    )
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
