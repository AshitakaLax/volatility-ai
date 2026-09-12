import { describe, expect, it } from "vitest";

import {
  DEFAULT_SEARCH_METHOD_STATE,
  MAX_TRIALS,
  MIN_TRIALS,
  searchMethodErrors,
  type SearchMethodState,
} from "./searchMethod";

function state(over: Partial<SearchMethodState> = {}): SearchMethodState {
  return { ...DEFAULT_SEARCH_METHOD_STATE, ...over };
}

describe("searchMethodErrors", () => {
  it("is empty for grid, regardless of nTrials", () => {
    expect(searchMethodErrors(state({ strategy: "grid" }))).toEqual([]);
    expect(searchMethodErrors(state({ strategy: "grid", nTrials: "" }))).toEqual([]);
  });

  it("requires nTrials for bayesian", () => {
    expect(searchMethodErrors(state({ strategy: "bayesian", nTrials: "" }))).toEqual([
      "enter a trial budget",
    ]);
  });

  it("accepts a value in range", () => {
    expect(searchMethodErrors(state({ strategy: "bayesian", nTrials: "50" }))).toEqual([]);
    expect(searchMethodErrors(state({ strategy: "bayesian", nTrials: String(MIN_TRIALS) }))).toEqual(
      [],
    );
    expect(searchMethodErrors(state({ strategy: "bayesian", nTrials: String(MAX_TRIALS) }))).toEqual(
      [],
    );
  });

  it("rejects a value outside [MIN_TRIALS, MAX_TRIALS]", () => {
    expect(searchMethodErrors(state({ strategy: "bayesian", nTrials: "1" })).length).toBeGreaterThan(
      0,
    );
    expect(
      searchMethodErrors(state({ strategy: "bayesian", nTrials: String(MAX_TRIALS + 1) })).length,
    ).toBeGreaterThan(0);
  });

  it("rejects a non-integer", () => {
    expect(searchMethodErrors(state({ strategy: "bayesian", nTrials: "10.5" })).length).toBeGreaterThan(
      0,
    );
  });

  it("rejects non-numeric text rather than coercing to 0", () => {
    expect(searchMethodErrors(state({ strategy: "bayesian", nTrials: "abc" })).length).toBeGreaterThan(
      0,
    );
  });
});
