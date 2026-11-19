import { describe, expect, it } from "vitest";

import { parsePlace, placeHash } from "@/lib/nav";

describe("the page's address", () => {
  it("opens on Live when it names nothing", () => {
    expect(parsePlace("")).toEqual({ tab: "live", deployment: null });
    expect(parsePlace("#nonsense")).toEqual({ tab: "live", deployment: null });
  });

  it("names a tab, and on Live a deployment", () => {
    expect(parsePlace("#backtest")).toEqual({ tab: "backtest", deployment: null });
    expect(parsePlace("#live/fidelity")).toEqual({ tab: "live", deployment: "fidelity" });
    expect(parsePlace("#/warehouse")).toEqual({ tab: "warehouse", deployment: null });
    // A deployment means nothing off the Live page, and is never markup.
    expect(parsePlace("#backtest/fidelity").deployment).toBeNull();
    expect(parsePlace("#live/<script>").deployment).toBeNull();
  });

  it("lands a run opened in its own tab on its result", () => {
    expect(parsePlace("", "?run=abc123").tab).toBe("result");
    expect(parsePlace("#backtest", "?run=abc123").tab).toBe("backtest");
  });

  it("round-trips", () => {
    for (const hash of ["#live", "#live/paper-ultimate", "#algorithms"]) {
      expect(placeHash(parsePlace(hash))).toBe(hash);
    }
  });
});
