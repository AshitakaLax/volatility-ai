import { describe, expect, it } from "vitest";

import { coverage, labelled, landing, signed, yExtent, yTicks } from "@/lib/forecastChart";
import type { ForecastSession } from "@/types/riskReport";

// Thursday's report for Fri Nov 20 (tests/fixtures/risk_reports/tqqq_2026-11-20.json).
const FRIDAY: ForecastSession = {
  session: "2026-11-20",
  symbol: "TQQQ",
  sha256: "43b37d111346",
  as_of: "2026-11-20T02:38:15+00:00",
  received_at: "2026-11-22T20:00:00+00:00",
  reports: 1,
  expected_move_pct: 8.38,
  median_pct: -0.19,
  quantiles: { p01: -22.01, p05: -13.42, p25: -5.04, p75: 4.55, p95: 11.95, p99: 18.85 },
  volatility_state: "extreme",
  actual: null,
  score: null,
};

function closed(returnPct: number, score?: ForecastSession["score"]): ForecastSession {
  return {
    ...FRIDAY,
    actual: {
      return_pct: returnPct,
      close: 40.99,
      prior_close: 48.99,
      prior_session: "2026-11-19",
      recorded_at: "2026-11-22T20:00:00+00:00",
    },
    score: score ?? null,
  };
}

describe("landing", () => {
  it("waits for a close it does not have", () => {
    expect(landing(FRIDAY)).toBe("pending");
  });

  it("places a close in its band", () => {
    expect(landing(closed(0.5))).toBe("in50");
    expect(landing(closed(-8))).toBe("in90");
    expect(landing(closed(12.5))).toBe("above");
    expect(landing(closed(-16.33))).toBe("below");
  });

  it("takes the server's score over its own reading", () => {
    const scored = closed(0.5, { in_90: true, in_50: false, pit: 0.6, pinball: 1, move_ratio: 0.1 });
    expect(landing(scored)).toBe("in90");
  });

  it("counts the band edges as inside, as the score does", () => {
    expect(landing(closed(-13.42))).toBe("in90");
    expect(landing(closed(4.55))).toBe("in50");
  });
});

describe("the axis", () => {
  it("reaches every range and close, rounded to its step", () => {
    expect(yExtent([FRIDAY])).toBe(15);
    expect(yExtent([closed(-16.33)])).toBe(20);
    expect(yExtent([])).toBe(5);
  });

  it("is symmetric about zero", () => {
    expect(yTicks(15)).toEqual([-15, -10, -5, 0, 5, 10, 15]);
    expect(yTicks(40)).toEqual([-40, -30, -20, -10, 0, 10, 20, 30, 40]);
  });
});

describe("coverage", () => {
  it("counts only the sessions that have closed", () => {
    expect(coverage([FRIDAY, closed(-16.33), closed(0.2), closed(-8)])).toEqual({
      closed: 3,
      in90: 2,
      in50: 1,
    });
  });
});

describe("labels", () => {
  it("always labels the newest and thins the rest when narrow", () => {
    const wide = labelled(4, 60);
    expect([0, 1, 2, 3].map(wide)).toEqual([true, true, true, true]);
    const narrow = labelled(5, 40);
    expect([0, 1, 2, 3, 4].map(narrow)).toEqual([true, false, true, false, true]);
  });

  it("signs a percentage with a true minus", () => {
    expect(signed(-16.333)).toBe("−16.3%");
    expect(signed(3.5)).toBe("+3.5%");
    expect(signed(-0.01)).toBe("0.0%");
  });
});
