/**
 * The dynamic-parameter helpers: schema -> seeded form state -> a
 * `strategy_params` payload. Each case below is one where a wrong answer
 * (a stray key, a float where an int is wanted, sending a field the
 * server aligns itself) looks fine on screen and fails on the run.
 */
import { describe, expect, it } from "vitest";

import type { ParamSpec } from "@/types/backtest";

import type { SweepFieldState } from "@/lib/sweepStrategies";

import {
  blankRequired,
  buildOptionsSweep,
  buildParamSweep,
  buildStrategyParams,
  diffFromDefaults,
  paramErrorsFor,
  seedOf,
  seedValues,
  type OptionsSweepFieldState,
} from "./strategyParams";

function spec(over: Partial<ParamSpec> = {}): ParamSpec {
  return {
    name: "x",
    type: "float",
    nullable: false,
    required: false,
    default: 0,
    suggested: 0,
    has_suggested: false,
    enum: null,
    group: "advanced",
    editable: true,
    locked_reason: null,
    mirrors: null,
    step: "any",
    sweepable: true,
    ...over,
  };
}

function sweep(over: Partial<SweepFieldState> = {}): SweepFieldState {
  return { enabled: true, strategy: "linear", start: "1", end: "5", count: "3", seed: "", ...over };
}

function optionsSweep(over: Partial<OptionsSweepFieldState> = {}): OptionsSweepFieldState {
  return { enabled: true, selected: [], ...over };
}

// The two swept dimensions of `fixed` and `bell_curve`, close to what
// server describe_params() actually emits.
const FIXED: ParamSpec[] = [
  // `float | None` on the ctor, but the server marks it required for the
  // form (FixedPortfolioPercentage raises without one).
  spec({ name: "allocation_pct", required: true, nullable: false, default: null, suggested: 0.05, has_suggested: true, group: "primary" }),
  spec({
    name: "percentage",
    nullable: true,
    default: null,
    suggested: null,
    editable: false,
    sweepable: false,
    locked_reason: "deprecated alias of allocation_pct -- use allocation_pct",
  }),
];

const BELL: ParamSpec[] = [
  spec({ name: "max_trade_pct", required: true, default: null, suggested: 0.08, has_suggested: true, group: "primary" }),
  spec({ name: "lookback_days", required: true, default: null, suggested: 20, has_suggested: true, group: "primary" }),
  spec({ name: "bars_per_day", type: "int", required: true, default: null, suggested: 387, has_suggested: true, group: "primary", step: "1" }),
  spec({ name: "mu", default: 0.2, suggested: 0.2 }),
  spec({ name: "sigma", default: 0.1, suggested: 0.1 }),
  spec({ name: "baseline_price", type: "float", nullable: true, default: null, suggested: null, editable: false, sweepable: false, locked_reason: "captured from the first bar" }),
];

const BAYES_HEAD: ParamSpec[] = [
  spec({ name: "max_trade_pct", required: true, default: null, suggested: 0.05, has_suggested: true, group: "primary" }),
  spec({
    name: "target_return",
    required: true,
    default: null,
    suggested: 0.0075,
    has_suggested: true,
    group: "primary",
    editable: false,
    sweepable: false,
    mirrors: "profit_target",
    locked_reason: "the server sets this to the grid's profit target",
  }),
  spec({ name: "bars_per_day", type: "int", required: true, default: null, suggested: 387, has_suggested: true, group: "primary", step: "1" }),
  spec({ name: "vol_measure", type: "str", default: "stdev", suggested: "stdev", enum: ["stdev", "range"], step: null, sweepable: true }),
  spec({ name: "allow_target_return_mismatch", type: "bool", default: false, suggested: false, step: null, sweepable: false }),
  // The grid-step trigger's local-reference window: optional, nullable,
  // seeds blank -> omitted unless the method selector sets it.
  spec({ name: "lookback_days", nullable: true, default: null, suggested: null, group: "advanced" }),
];

const ML: ParamSpec[] = [
  spec({ name: "max_trade_pct", required: true, default: null, suggested: 0.05, has_suggested: true, group: "primary" }),
  spec({ name: "ticker", type: "str", required: true, default: null, suggested: "COWZ", has_suggested: true, group: "primary", editable: false, sweepable: false, locked_reason: "trained on COWZ", step: null }),
  spec({ name: "confidence_floor", default: 0.25, suggested: 0.25, has_suggested: true, group: "primary" }),
];

describe("seedValues", () => {
  it("seeds each field to its suggested value as a string, blank for null", () => {
    const seed = seedValues(BELL);
    expect(seed.max_trade_pct).toBe("0.08");
    expect(seed.bars_per_day).toBe("387");
    expect(seed.baseline_price).toBe(""); // suggested null -> blank
  });

  it("omits mirrors fields entirely -- they are not stored", () => {
    expect("target_return" in seedValues(BAYES_HEAD)).toBe(false);
  });

  it("seedOf stringifies bool and enum suggestions", () => {
    expect(seedOf(spec({ type: "bool", suggested: false }))).toBe("false");
    expect(seedOf(spec({ type: "str", suggested: "stdev" }))).toBe("stdev");
  });
});

describe("buildStrategyParams", () => {
  it("a no-edit fixed submit sends exactly {allocation_pct: 0.05}", () => {
    expect(buildStrategyParams(FIXED, seedValues(FIXED))).toEqual({ allocation_pct: 0.05 });
  });

  it("a no-edit bell_curve submit sends exactly its committed defaults", () => {
    expect(buildStrategyParams(BELL, seedValues(BELL))).toEqual({
      max_trade_pct: 0.08,
      lookback_days: 20,
      bars_per_day: 387,
    });
  });

  it("never sends the deprecated `percentage` alias or a locked derived field", () => {
    const values = { ...seedValues(BELL), baseline_price: "71.5" };
    expect("baseline_price" in buildStrategyParams(BELL, values)).toBe(false);
    const fv = { ...seedValues(FIXED), percentage: "0.1" };
    expect("percentage" in buildStrategyParams(FIXED, fv)).toBe(false);
  });

  it("never sends a mirrors field even if a value leaks into the map", () => {
    const values = { ...seedValues(BAYES_HEAD), target_return: "0.9" };
    expect("target_return" in buildStrategyParams(BAYES_HEAD, values)).toBe(false);
  });

  it("omits the local-reference window when blank, sends it as a number when the method sets it", () => {
    // last_buy method: lookback_days seeds blank -> not on the wire.
    expect("lookback_days" in buildStrategyParams(BAYES_HEAD, seedValues(BAYES_HEAD))).toBe(false);
    // local_reference method: the selector wrote "0.03".
    const set = { ...seedValues(BAYES_HEAD), lookback_days: "0.03" };
    expect(buildStrategyParams(BAYES_HEAD, set).lookback_days).toBe(0.03);
  });

  it("omits a blank field rather than sending null or empty string", () => {
    const values = { ...seedValues(BELL), mu: "" };
    expect("mu" in buildStrategyParams(BELL, values)).toBe(false);
  });

  it("omits a pure-optional field left at its constructor default, includes it when moved", () => {
    expect("mu" in buildStrategyParams(BELL, seedValues(BELL))).toBe(false); // at default 0.2
    const moved = { ...seedValues(BELL), mu: "0.25" };
    expect(buildStrategyParams(BELL, moved).mu).toBe(0.25);
  });

  it("types int fields as integers, bool as JSON boolean, enum as string", () => {
    const values = {
      ...seedValues(BAYES_HEAD),
      bars_per_day: "390",
      vol_measure: "range",
      allow_target_return_mismatch: "true",
    };
    const out = buildStrategyParams(BAYES_HEAD, values);
    expect(out.bars_per_day).toBe(390);
    expect(Number.isInteger(out.bars_per_day)).toBe(true);
    expect(out.vol_measure).toBe("range");
    expect(out.allow_target_return_mismatch).toBe(true);
  });

  it("includes ticker for an ml model (required, server does not inject it)", () => {
    expect(buildStrategyParams(ML, seedValues(ML)).ticker).toBe("COWZ");
  });

  it("drops a half-typed number rather than sending NaN", () => {
    const values = { ...seedValues(BELL), max_trade_pct: "-" };
    expect("max_trade_pct" in buildStrategyParams(BELL, values)).toBe(false);
  });
});

describe("diffFromDefaults", () => {
  it("is empty when every editable field is at its seed", () => {
    expect(diffFromDefaults(BELL, seedValues(BELL))).toEqual([]);
  });

  it("reports only changed editable non-mirror fields", () => {
    const values = { ...seedValues(BELL), mu: "0.3", max_trade_pct: "0.12" };
    const diff = diffFromDefaults(BELL, values);
    expect(diff.map((d) => d.name).sort()).toEqual(["max_trade_pct", "mu"]);
    expect(diff.find((d) => d.name === "mu")).toEqual({ name: "mu", from: "0.2", to: "0.3" });
  });

  it("ignores the locked target_return even if the map carries a stale value", () => {
    const values = { ...seedValues(BAYES_HEAD), target_return: "0.5" };
    expect(diffFromDefaults(BAYES_HEAD, values).some((d) => d.name === "target_return")).toBe(false);
  });
});

describe("blankRequired", () => {
  it("names a required editable field left blank", () => {
    const values = { ...seedValues(BELL), max_trade_pct: "" };
    expect(blankRequired(BELL, values)).toEqual(["max_trade_pct"]);
  });

  it("is empty when required fields are filled, and ignores the locked ticker", () => {
    expect(blankRequired(BELL, seedValues(BELL))).toEqual([]);
    expect(blankRequired(ML, { ...seedValues(ML), ticker: "" })).toEqual([]); // ticker not editable
  });
});

describe("buildParamSweep", () => {
  it("resolves a linear range for a float param", () => {
    const r = buildParamSweep(spec({ name: "max_trade_pct", type: "float" }), sweep({ start: "0.05", end: "0.1", count: "3" }));
    expect(r.errors).toEqual([]);
    expect(r.values).toEqual([0.05, 0.075, 0.1]);
  });

  it("rounds to whole numbers for an int param", () => {
    const r = buildParamSweep(spec({ name: "bars_per_day", type: "int" }), sweep({ start: "1", end: "3", count: "5" }));
    expect(r.errors).toEqual([]);
    expect(r.values).toEqual([1, 2, 3]); // 1, 1.5, 2, 2.5, 3 -> rounded, deduped
  });

  it("a blank start or end errors rather than treating it as zero", () => {
    expect(buildParamSweep(spec(), sweep({ start: "" })).errors.length).toBeGreaterThan(0);
    expect(buildParamSweep(spec(), sweep({ end: "" })).errors.length).toBeGreaterThan(0);
  });
});

describe("buildOptionsSweep", () => {
  const vm = spec({ name: "vol_measure", type: "str", enum: ["stdev", "range"], sweepable: true });

  it("submits the selected subset, in the enum's own order", () => {
    const r = buildOptionsSweep(vm, optionsSweep({ selected: ["range", "stdev"] }));
    expect(r.errors).toEqual([]);
    expect(r.values).toEqual(["stdev", "range"]);
  });

  it("a single selected option is a valid sweep of one", () => {
    const r = buildOptionsSweep(vm, optionsSweep({ selected: ["range"] }));
    expect(r.values).toEqual(["range"]);
  });

  it("nothing checked errors rather than sending an empty list", () => {
    const r = buildOptionsSweep(vm, optionsSweep({ selected: [] }));
    expect(r.values).toEqual([]);
    expect(r.errors.length).toBeGreaterThan(0);
  });

  it("ignores a stale selection outside the current enum", () => {
    const r = buildOptionsSweep(vm, optionsSweep({ selected: ["range", "log"] }));
    expect(r.values).toEqual(["range"]);
  });
});

describe("buildStrategyParams -- sweep-aware", () => {
  it("a sweep-enabled sweepable param is sent as a list, ignoring its scalar text", () => {
    const sweepFields = { max_trade_pct: sweep({ start: "0.05", end: "0.1", count: "2" }) };
    const out = buildStrategyParams(BELL, { ...seedValues(BELL), max_trade_pct: "0.9" }, sweepFields);
    expect(out.max_trade_pct).toEqual([0.05, 0.1]);
  });

  it("a sweep with client errors is omitted, not sent as an empty/partial list", () => {
    const sweepFields = { max_trade_pct: sweep({ start: "", end: "0.1" }) };
    const out = buildStrategyParams(BELL, seedValues(BELL), sweepFields);
    expect("max_trade_pct" in out).toBe(false);
  });

  it("sweepFields is ignored for a non-sweepable (locked/mirrored) param", () => {
    const sweepFields = { target_return: sweep() };
    const out = buildStrategyParams(BAYES_HEAD, seedValues(BAYES_HEAD), sweepFields);
    expect("target_return" in out).toBe(false);
  });

  it("an enabled enum options sweep is sent as a list, ignoring its scalar text", () => {
    const optionSweepFields = { vol_measure: optionsSweep({ selected: ["stdev", "range"] }) };
    const out = buildStrategyParams(BAYES_HEAD, seedValues(BAYES_HEAD), {}, optionSweepFields);
    expect(out.vol_measure).toEqual(["stdev", "range"]);
  });

  it("an options sweep with nothing checked is omitted, not sent as an empty list", () => {
    const optionSweepFields = { vol_measure: optionsSweep({ selected: [] }) };
    const out = buildStrategyParams(BAYES_HEAD, seedValues(BAYES_HEAD), {}, optionSweepFields);
    expect("vol_measure" in out).toBe(false);
  });

  it("sweepFields (the numeric map) is ignored for an enum param even if it carries a stale entry", () => {
    const values = { ...seedValues(BAYES_HEAD), vol_measure: "range" };
    const sweepFields = { vol_measure: sweep({ enabled: true }) }; // a numeric range, wrongly keyed
    const out = buildStrategyParams(BAYES_HEAD, values, sweepFields);
    expect(out.vol_measure).toBe("range"); // the scalar text, not buildParamSweep's numeric output
  });
});

describe("blankRequired -- sweep-aware", () => {
  it("a required field with an enabled, valid sweep is not blank", () => {
    const values = { ...seedValues(BELL), max_trade_pct: "" };
    const sweepFields = { max_trade_pct: sweep({ start: "0.05", end: "0.1", count: "2" }) };
    expect(blankRequired(BELL, values, sweepFields)).toEqual([]);
  });

  it("a required field with an enabled but invalid sweep is still blank", () => {
    const values = { ...seedValues(BELL), max_trade_pct: "" };
    const sweepFields = { max_trade_pct: sweep({ start: "", end: "0.1" }) };
    expect(blankRequired(BELL, values, sweepFields)).toEqual(["max_trade_pct"]);
  });

  it("a required enum field with nothing checked is blank", () => {
    // vol_measure is not required in the fixture; check the mechanism
    // directly the way the numeric case does, on a required copy of it.
    const required = [spec({ name: "vol_measure", type: "str", enum: ["stdev", "range"], sweepable: true, required: true, default: "stdev", suggested: "stdev" })];
    const values = { vol_measure: "" };
    const optionSweepFields = { vol_measure: optionsSweep({ selected: [] }) };
    expect(blankRequired(required, values, {}, optionSweepFields)).toEqual(["vol_measure"]);
  });

  it("a required enum field with an enabled, non-empty options sweep is not blank", () => {
    const required = [spec({ name: "vol_measure", type: "str", enum: ["stdev", "range"], sweepable: true, required: true, default: "stdev", suggested: "stdev" })];
    const values = { vol_measure: "" };
    const optionSweepFields = { vol_measure: optionsSweep({ selected: ["stdev"] }) };
    expect(blankRequired(required, values, {}, optionSweepFields)).toEqual([]);
  });
});

describe("diffFromDefaults -- sweep-aware", () => {
  it("reports a swept field as changed, labeled 'swept'", () => {
    const sweepFields = { mu: sweep() };
    const diff = diffFromDefaults(BELL, seedValues(BELL), sweepFields);
    expect(diff.find((d) => d.name === "mu")).toEqual({ name: "mu", from: "0.2", to: "swept" });
  });

  it("reports an enum options sweep as changed, labeled 'swept'", () => {
    const optionSweepFields = { vol_measure: optionsSweep({ selected: ["stdev", "range"] }) };
    const diff = diffFromDefaults(BAYES_HEAD, seedValues(BAYES_HEAD), {}, optionSweepFields);
    expect(diff.find((d) => d.name === "vol_measure")).toEqual({
      name: "vol_measure",
      from: "stdev",
      to: "swept",
    });
  });

  it("a disabled options sweep does not mark an unchanged enum field as swept", () => {
    const optionSweepFields = { vol_measure: optionsSweep({ enabled: false, selected: ["range"] }) };
    const diff = diffFromDefaults(BAYES_HEAD, seedValues(BAYES_HEAD), {}, optionSweepFields);
    expect(diff.some((d) => d.name === "vol_measure")).toBe(false);
  });
});

describe("paramErrorsFor", () => {
  const errors = [
    { field: "max_trade_pct", message: "must be in (0, 1]" },
    { field: null, message: "cannot sweep 2 profit targets" },
  ];
  it("filters to one field, and to the unattached errors for null", () => {
    expect(paramErrorsFor("max_trade_pct", errors)).toHaveLength(1);
    expect(paramErrorsFor(null, errors)[0]!.message).toContain("cannot sweep");
    expect(paramErrorsFor("mu", errors)).toEqual([]);
    expect(paramErrorsFor("x", undefined)).toEqual([]);
  });
});
