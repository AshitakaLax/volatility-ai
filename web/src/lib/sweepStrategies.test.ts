/**
 * The Linear / Logarithmic / Random-Monte-Carlo range-to-list
 * generators, and the dispatcher that picks between them. Each case
 * below is one where a wrong answer (an oversized array, a silently
 * collapsed range, an irreproducible "seeded" list) looks fine on
 * screen and only shows up as a bad sweep.
 */
import { describe, expect, it } from "vitest";

import {
  buildAdaptiveSweep,
  buildLinearSweep,
  buildLogarithmicSweep,
  buildMultiResolutionSweep,
  buildRandomSweep,
  buildSweepValues,
  MAX_SWEEP_POINTS,
  type SweepGenerationInput,
} from "./sweepStrategies";

const RAW = { integer: false };
const base: SweepGenerationInput = { min: 1, max: 5, count: 5 };

describe("buildLinearSweep", () => {
  it("count 1 returns a single point, no error", () => {
    expect(buildLinearSweep({ ...base, count: 1 }, RAW)).toEqual({ values: [1], errors: [] });
  });

  it("evenly spaced, ascending", () => {
    expect(buildLinearSweep({ min: 0, max: 4, count: 5 }, RAW).values).toEqual([0, 1, 2, 3, 4]);
  });

  it(`count outside 1..${MAX_SWEEP_POINTS} errors and never generates`, () => {
    const over = buildLinearSweep({ ...base, count: MAX_SWEEP_POINTS + 1 }, RAW);
    expect(over.values).toEqual([]);
    expect(over.errors.some((e) => e.includes(`1 to ${MAX_SWEEP_POINTS}`))).toBe(true);

    const zero = buildLinearSweep({ ...base, count: 0 }, RAW);
    expect(zero.values).toEqual([]);
    expect(zero.errors.length).toBeGreaterThan(0);
  });

  it("a non-integer count errors", () => {
    expect(buildLinearSweep({ ...base, count: 2.5 }, RAW).errors.length).toBeGreaterThan(0);
  });

  it("min >= max with count > 1 errors; count 1 does not", () => {
    const bad = buildLinearSweep({ min: 5, max: 1, count: 3 }, RAW);
    expect(bad.values).toEqual([]);
    expect(bad.errors.some((e) => e.includes("below max"))).toBe(true);

    expect(buildLinearSweep({ min: 5, max: 1, count: 1 }, RAW).errors).toEqual([]);
  });

  it("non-numeric bounds error", () => {
    expect(buildLinearSweep({ min: Number.NaN, max: 5, count: 3 }, RAW).errors.length).toBeGreaterThan(0);
  });

  it("dedupes points closer than the rounding resolution", () => {
    const r = buildLinearSweep({ min: 0.5, max: 0.5 + 1e-11, count: 3 }, RAW);
    expect(r.errors).toEqual([]);
    expect(r.values).toHaveLength(1);
  });

  it("opts.integer rounds every point before dedupe", () => {
    const r = buildLinearSweep({ min: 1, max: 3, count: 5 }, { integer: true });
    expect(r.errors).toEqual([]);
    // 1, 1.5, 2, 2.5, 3 -> rounds to 1, 2, 2, 3, 3 -> dedupes to 1, 2, 3
    expect(r.values).toEqual([1, 2, 3]);
  });

  it("results are ascending and within 1..MAX_SWEEP_POINTS entries", () => {
    const r = buildLinearSweep({ min: 0.1, max: 50, count: 10 }, RAW);
    expect(r.errors).toEqual([]);
    expect(r.values.length).toBeGreaterThanOrEqual(1);
    expect(r.values.length).toBeLessThanOrEqual(MAX_SWEEP_POINTS);
    expect([...r.values].sort((a, b) => a - b)).toEqual(r.values);
  });
});

describe("buildLogarithmicSweep", () => {
  it("count 1 returns a single point", () => {
    expect(buildLogarithmicSweep({ ...base, count: 1 }, RAW)).toEqual({ values: [1], errors: [] });
  });

  it("log-spaced, ascending", () => {
    const r = buildLogarithmicSweep({ min: 1, max: 100, count: 3 }, RAW);
    expect(r.errors).toEqual([]);
    expect(r.values).toEqual([1, 10, 100]);
  });

  it("min <= 0 or max <= 0 errors", () => {
    expect(buildLogarithmicSweep({ min: 0, max: 10, count: 3 }, RAW).errors.length).toBeGreaterThan(0);
    expect(buildLogarithmicSweep({ min: -1, max: 10, count: 3 }, RAW).errors.length).toBeGreaterThan(0);
    expect(buildLogarithmicSweep({ min: 1, max: 0, count: 3 }, RAW).errors.length).toBeGreaterThan(0);
  });

  it("min >= max with count > 1 errors; count 1 does not", () => {
    expect(buildLogarithmicSweep({ min: 10, max: 1, count: 3 }, RAW).errors.some((e) => e.includes("below max"))).toBe(true);
    expect(buildLogarithmicSweep({ min: 10, max: 1, count: 1 }, RAW).errors).toEqual([]);
  });
});

describe("buildRandomSweep", () => {
  it("the same seed produces the same list twice", () => {
    const a = buildRandomSweep({ min: 0, max: 100, count: 6, seed: "42" }, RAW);
    const b = buildRandomSweep({ min: 0, max: 100, count: 6, seed: "42" }, RAW);
    expect(a.errors).toEqual([]);
    expect(a.values).toEqual(b.values);
  });

  it("a different seed produces a different list", () => {
    const a = buildRandomSweep({ min: 0, max: 100, count: 6, seed: "1" }, RAW);
    const b = buildRandomSweep({ min: 0, max: 100, count: 6, seed: "2" }, RAW);
    expect(a.values).not.toEqual(b.values);
  });

  it("a blank seed does not error, and stays within range", () => {
    const r = buildRandomSweep({ min: 2, max: 4, count: 5 }, RAW);
    expect(r.errors).toEqual([]);
    for (const v of r.values) {
      expect(v).toBeGreaterThanOrEqual(2);
      expect(v).toBeLessThanOrEqual(4);
    }
  });

  it("min >= max is a hard error even at count 1", () => {
    expect(buildRandomSweep({ min: 5, max: 5, count: 1 }, RAW).errors.length).toBeGreaterThan(0);
  });

  it("dedupe may silently reduce below count -- not an error", () => {
    // A degenerate-but-valid range with count > the number of distinct
    // integers available, rounded -- some collisions are expected.
    const r = buildRandomSweep({ min: 1, max: 2, count: 12, seed: "7" }, { integer: true });
    expect(r.errors).toEqual([]);
    expect(r.values.length).toBeLessThanOrEqual(12);
    expect(r.values.length).toBeGreaterThanOrEqual(1);
  });

  it(`count outside 1..${MAX_SWEEP_POINTS} errors`, () => {
    expect(buildRandomSweep({ min: 0, max: 1, count: MAX_SWEEP_POINTS + 1 }, RAW).errors.length).toBeGreaterThan(0);
  });
});

describe("the unimplemented strategies", () => {
  it("multi-resolution always errors, never returns values", () => {
    const r = buildMultiResolutionSweep(base, RAW);
    expect(r.values).toEqual([]);
    expect(r.errors.length).toBeGreaterThan(0);
  });

  it("adaptive always errors, never returns values", () => {
    const r = buildAdaptiveSweep(base, RAW);
    expect(r.values).toEqual([]);
    expect(r.errors.length).toBeGreaterThan(0);
  });
});

describe("buildSweepValues dispatcher", () => {
  it("routes to the matching generator for every strategy", () => {
    expect(buildSweepValues("linear", base, RAW)).toEqual(buildLinearSweep(base, RAW));
    expect(buildSweepValues("logarithmic", base, RAW)).toEqual(buildLogarithmicSweep(base, RAW));
    expect(buildSweepValues("multi_resolution", base, RAW)).toEqual(buildMultiResolutionSweep(base, RAW));
    expect(buildSweepValues("adaptive", base, RAW)).toEqual(buildAdaptiveSweep(base, RAW));
  });
});
