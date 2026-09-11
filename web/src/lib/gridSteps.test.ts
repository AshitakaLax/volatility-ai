/**
 * The Fixed | Sweep grid-step builder. Each case below is one where a
 * wrong answer (an oversized array Pydantic rejects, a silently
 * collapsed range, float dust on the wire) looks fine on screen.
 */
import { describe, expect, it } from "vitest";

import { buildGridSteps, type GridStepInput } from "./gridSteps";

const base: GridStepInput = { mode: "fixed", fixedPct: "1", minPct: "0.5", maxPct: "1.5", count: "5" };

describe("buildGridSteps — fixed", () => {
  it("one value, converted to a fraction", () => {
    expect(buildGridSteps({ ...base, mode: "fixed", fixedPct: "1" })).toEqual({
      steps: [0.01],
      errors: [],
    });
  });

  it("kills the /100 float dust", () => {
    expect(buildGridSteps({ ...base, mode: "fixed", fixedPct: "0.7" }).steps).toEqual([0.007]);
  });

  it("rejects out-of-range / non-numeric", () => {
    for (const bad of ["0", "100", "-1", "", "x"]) {
      const r = buildGridSteps({ ...base, mode: "fixed", fixedPct: bad });
      expect(r.steps).toEqual([]);
      expect(r.errors.length).toBeGreaterThan(0);
    }
  });
});

describe("buildGridSteps — sweep", () => {
  it("evenly spaced, ascending, fractions", () => {
    expect(buildGridSteps({ ...base, mode: "sweep", minPct: "0.5", maxPct: "1", count: "3" })).toEqual({
      steps: [0.005, 0.0075, 0.01],
      errors: [],
    });
  });

  it("count 1 is a single value with no error", () => {
    expect(buildGridSteps({ ...base, mode: "sweep", minPct: "0.5", maxPct: "1", count: "1" })).toEqual({
      steps: [0.005],
      errors: [],
    });
  });

  it("count 12 is allowed; count 13 errors AND never builds a 13-element array", () => {
    const ok = buildGridSteps({ ...base, mode: "sweep", minPct: "0.2", maxPct: "2", count: "12" });
    expect(ok.errors).toEqual([]);
    expect(ok.steps).toHaveLength(12);
    const over = buildGridSteps({ ...base, mode: "sweep", minPct: "0.2", maxPct: "2", count: "13" });
    expect(over.steps).toEqual([]);
    expect(over.errors.some((e) => e.includes("1 to 12"))).toBe(true);
  });

  it("a fractional count errors", () => {
    expect(
      buildGridSteps({ ...base, mode: "sweep", minPct: "0.5", maxPct: "1", count: "2.5" }).errors,
    ).not.toEqual([]);
  });

  it("min >= max with count > 1 is a hard error, not a silent collapse", () => {
    const r = buildGridSteps({ ...base, mode: "sweep", minPct: "2", maxPct: "1", count: "3" });
    expect(r.steps).toEqual([]);
    expect(r.errors.some((e) => e.includes("below max"))).toBe(true);
  });

  it("min == max with count > 1 also errors", () => {
    expect(
      buildGridSteps({ ...base, mode: "sweep", minPct: "1", maxPct: "1", count: "3" }).errors,
    ).not.toEqual([]);
  });

  it("blank or non-numeric bounds error", () => {
    for (const [min, max] of [["", "1"], ["x", "1"], ["0.5", ""]]) {
      expect(
        buildGridSteps({ ...base, mode: "sweep", minPct: min!, maxPct: max!, count: "3" }).errors,
      ).not.toEqual([]);
    }
  });

  it("bounds closer than the fraction resolution dedupe to one step, no error", () => {
    const r = buildGridSteps({
      ...base,
      mode: "sweep",
      minPct: "0.5",
      maxPct: "0.500000001",
      count: "3",
    });
    expect(r.errors).toEqual([]);
    expect(r.steps).toHaveLength(1);
  });

  it("every resolved step is a valid fraction 0<s<1, 1..12 of them", () => {
    const r = buildGridSteps({ ...base, mode: "sweep", minPct: "0.1", maxPct: "50", count: "10" });
    expect(r.errors).toEqual([]);
    expect(r.steps.length).toBeGreaterThanOrEqual(1);
    expect(r.steps.length).toBeLessThanOrEqual(12);
    for (const s of r.steps) {
      expect(s).toBeGreaterThan(0);
      expect(s).toBeLessThan(1);
    }
    expect([...r.steps].sort((a, b) => a - b)).toEqual(r.steps);
  });
});
