import { describe, expect, it } from "vitest";

import {
  appliedBySha,
  appliedText,
  calibration,
  caught,
  distribution,
  dollars,
  fanExtent,
  fanPoints,
  horizonsThrough,
  keptRowFor,
  keptText,
  madeBy,
  modelLabel,
  niceTicks,
  outcomeText,
  outcomes,
} from "@/lib/forecastReview";
import { sessionDay } from "@/lib/riskReport";
import type { GeneratedReport, HorizonKey, ReportHorizon } from "@/types/forecast";
import type { KeptReport, RiskReportEntry } from "@/types/riskReport";

function horizon(spread: number, median = 0): ReportHorizon {
  return {
    label: "h",
    trading_days: 1,
    bin_width_pct: 2,
    underflow_prob: 0.01,
    overflow_prob: 0.02,
    bins: [
      { min_pct: -4, max_pct: -2, prob: 0.2, cdf: 0.21 },
      { min_pct: -2, max_pct: 0, prob: 0.3, cdf: 0.51 },
      { min_pct: 0, max_pct: 4, prob: 0.47, cdf: 0.98 },
    ],
    summary: {
      mean_pct: median,
      median_pct: median,
      std_pct: spread / 2,
      prob_positive: 0.5,
      expected_shortfall_5pct: -spread * 1.2,
      quantiles_pct: {
        p01: -spread * 1.4,
        p05: -spread,
        p25: -spread / 3,
        p75: spread / 3,
        p95: spread,
        p99: spread * 1.4,
      },
    },
  };
}

const REPORT = {
  symbol: "TQQQ",
  as_of: "2026-11-25T12:44:03Z",
  target_session: "2026-11-25",
  base_price: 50,
  model: "amazon/chronos-2 zero-shot (direct 21-session quantiles; 2,000 scenarios)",
  horizons: {
    tomorrow: horizon(10, -1),
    next_week: horizon(20, 1),
    next_month: horizon(40, 2),
    next_quarter: horizon(60, 4),
    next_year: horizon(100, 10),
  },
} as unknown as GeneratedReport;

function row(over: Partial<KeptReport> = {}): KeptReport {
  return {
    session: "2026-11-25",
    symbol: "TQQQ",
    sha256: "a".repeat(64),
    as_of: "2026-11-25T12:44:03.000000+00:00",
    received_at: "2026-11-25T12:45:00+00:00",
    reports: 1,
    expected_move_pct: 6,
    median_pct: -1,
    quantiles: { p01: -14, p05: -10, p25: -3.3, p75: 3.3, p95: 10, p99: 14 },
    volatility_state: "high",
    actual: null,
    score: null,
    model: REPORT.model,
    base_price: 50,
    mean_pct: -1,
    std_pct: 5,
    prob_positive: 0.45,
    es5_pct: -12,
    regime: null,
    gap_risk: null,
    skew_bias: null,
    confidence: 0.8,
    warnings: 0,
    newest: true,
    has_inputs: true,
    receipt_count: 1,
    receipts: [
      {
        received_at: "2026-11-25T12:45:00+00:00",
        operator: "forecast service",
        via: "check",
      },
    ],
    horizons: {
      next_week: { end_session: "2026-12-02", score: null },
      next_month: { end_session: "2026-12-24", score: null },
      next_quarter: { end_session: "2027-02-25", score: null },
      next_year: { end_session: "2027-11-26", score: null },
    },
    ...over,
  };
}

function closed(returnPct: number, over: Partial<KeptReport> = {}): KeptReport {
  return row({
    actual: {
      return_pct: returnPct,
      close: 50 * (1 + returnPct / 100),
      prior_close: 50,
      prior_session: "2026-11-24",
      recorded_at: "2026-11-26T02:00:00+00:00",
    },
    ...over,
  });
}

function weekScored(returnPct: number, inside: { in_90: boolean; in_50: boolean }) {
  return {
    end_session: "2026-12-02",
    score: {
      end_session: "2026-12-02",
      end_close: 50 * (1 + returnPct / 100),
      return_pct: returnPct,
      pit: returnPct > 0 ? 0.99 : 0.01,
      pinball: 1,
      ...inside,
    },
  };
}

describe("who made it, with what", () => {
  it("names the models briefly", () => {
    expect(modelLabel(REPORT.model)).toBe("Chronos-2");
    expect(
      modelLabel(
        "amazon/chronos-2 (public service equinai-chronos-2-api.hf.space; 10,000 scenarios)",
      ),
    ).toBe("Chronos-2 (public service)");
    expect(modelLabel("historical-bootstrap baseline, no model (5-session block)")).toBe(
      "Historical baseline",
    );
    expect(modelLabel("eod_regime_conditioned_forecast")).toBe("eod_regime_conditioned_forecast");
    expect(modelLabel(null)).toBe("unnamed model");
  });

  it("names who first added it", () => {
    expect(madeBy(row().receipts)).toBe("forecast service");
    expect(madeBy([{ received_at: "x", operator: null, via: "archive:paper-ultimate" }])).toBe(
      "paper-ultimate's archive",
    );
    expect(madeBy([{ received_at: "x", operator: null, via: "import" }])).toBe("imported");
    expect(madeBy([{ received_at: "x", operator: null, via: "check" }])).toBe("the page");
    expect(madeBy([])).toBe("unknown");
    expect(
      madeBy([
        { received_at: "t", operator: null, via: "archive:paper-ultimate" },
        { received_at: "t", operator: "owner", via: "check" },
      ]),
    ).toBe("owner");
  });

  it("says how it reached the database", () => {
    expect(keptText(row().receipts)).toBe("kept by the forecast service");
    expect(keptText([{ received_at: "x", operator: "owner", via: "check" }])).toBe("kept by owner");
    expect(keptText([{ received_at: "x", operator: null, via: "import" }])).toBe(
      "imported from a file",
    );
    expect(keptText([{ received_at: "x", operator: null, via: "archive:paper" }])).toBe(
      "copied from paper's archive",
    );
  });

  it("joins each report to the traders that archived it", () => {
    const entry = (sha256: string, outcome: RiskReportEntry["outcome"]) =>
      ({ sha256, outcome, received_at: "t", operator: "o" }) as RiskReportEntry;
    const found = appliedBySha({
      "paper-ultimate": [entry("s1", "applied")],
      paper: [entry("s1", "not_applied"), entry("s2", "applied")],
    });
    expect(found.get("s1")?.map((a) => a.deployment)).toEqual(["paper", "paper-ultimate"]);
    expect(appliedText(found.get("s1"))).toBe("applied to paper-ultimate; not applied: paper");
    expect(appliedText(found.get("s3"))).toBe("not sent to a trader");
    const copied = [{ received_at: "t", operator: null, via: "archive:paper-ultimate" }];
    expect(appliedText(undefined, copied)).toBe("sent to paper-ultimate");
    expect(appliedText(found.get("s1"), copied)).toBe(
      "applied to paper-ultimate; not applied: paper",
    );
  });

  it("finds the kept row a run's report became", () => {
    expect(keptRowFor(REPORT, [row()])?.sha256).toBe("a".repeat(64));
    expect(keptRowFor({ ...REPORT, model: "other" }, [row()])).toBeUndefined();
    expect(keptRowFor({ ...REPORT, as_of: "2026-11-25T12:45:00Z" }, [row()])).toBeUndefined();
  });
});

describe("the fan", () => {
  it("starts at the close and widens through the horizons asked for", () => {
    const points = fanPoints(REPORT, "next_month", "pct");
    expect(points.map((p) => p.key)).toEqual(["base", "tomorrow", "next_week", "next_month"]);
    expect(points[0]).toMatchObject({ p05: 0, median: 0, p95: 0 });
    expect(points[2]).toMatchObject({
      p05: -20,
      median: 1,
      p95: 20,
      sessions: 5,
    });
    expect(horizonsThrough("next_year")).toHaveLength(5);
  });

  it("in dollars from the report's own base close", () => {
    const points = fanPoints(REPORT, "next_week", "price");
    expect(points[0]?.median).toBe(50);
    expect(points[1]?.p05).toBeCloseTo(45);
    expect(points[2]?.p95).toBeCloseTo(60);
  });

  it("reaches every series and outcome drawn", () => {
    const [lo, hi] = fanExtent([fanPoints(REPORT, "next_week", "pct")], [35]);
    expect(lo).toBeLessThan(-20);
    expect(hi).toBeGreaterThan(35);
  });
});

describe("what came of each horizon", () => {
  it("waits for each close, naming the session", () => {
    const found = outcomes(row())!;
    expect(found.tomorrow.landing).toBe("pending");
    expect(found.next_week).toEqual({
      landing: "pending",
      return_pct: null,
      end_session: "2026-12-02",
    });
    expect(outcomeText(found.next_week, sessionDay)).toBe("closes Wed, Dec 2");
  });

  it("places each close in its own horizon's ranges", () => {
    const found = outcomes(
      closed(-12, {
        score: {
          in_90: false,
          in_50: false,
          pit: 0.02,
          pinball: 3,
          move_ratio: 2,
        },
        horizons: {
          ...row().horizons,
          next_week: weekScored(25, { in_90: false, in_50: false }),
        },
      }),
    )!;
    expect(found.tomorrow.landing).toBe("below");
    expect(found.next_week.landing).toBe("above");
    expect(found.next_week.return_pct).toBe(25);
    expect(found.next_month.landing).toBe("pending");
    expect(outcomeText(found.next_week, sessionDay)).toBe("above its 90%");
  });

  it("has nothing to say for a report not kept", () => {
    expect(outcomes(null)).toBeNull();
  });
});

describe("one horizon's distribution", () => {
  it("is the bins as a density, so different widths compare", () => {
    const found = distribution(REPORT.horizons.tomorrow);
    expect(found.bars.map((b) => b.density)).toEqual([0.1, 0.15, 0.1175]);
    expect(found).toMatchObject({ lo: -4, hi: 4, under: 0.01, over: 0.02 });
  });
});

describe("the track record", () => {
  it("counts each horizon's closes inside its ranges, for the report in force and by model", () => {
    const rows = [
      closed(1, { sha256: "1", newest: true }), // inside the 50%
      closed(8, { sha256: "2", newest: true }), // inside the 90%
      closed(-15, {
        sha256: "3",
        newest: false,
        model: "eod_regime_conditioned_forecast",
        horizons: {
          ...row().horizons,
          next_week: weekScored(2, { in_90: true, in_50: true }),
        },
      }),
      row({ sha256: "4", newest: true }), // waiting
    ];
    const { inForce, byModel } = calibration(rows);
    expect(inForce.reports).toBe(3);
    expect(inForce.horizons.tomorrow).toEqual({ closed: 2, in90: 2, in50: 1 });
    expect(byModel.map((m) => [m.model, m.reports])).toEqual([
      ["Chronos-2", 3],
      ["eod_regime_conditioned_forecast", 1],
    ]);
    const eod = byModel[1]!;
    expect(eod.horizons.tomorrow).toEqual({ closed: 1, in90: 0, in50: 0 });
    expect(eod.horizons.next_week).toEqual({ closed: 1, in90: 1, in50: 1 });
    expect(caught(eod.horizons.next_month as never, "in90")).toBe("none closed yet");
    expect(caught(inForce.horizons.tomorrow, "in90")).toBe("2 of 2");
  });
});

describe("axes and labels", () => {
  it("ticks at round values", () => {
    expect(niceTicks(-13, 12, 5)).toEqual([-10, -5, 0, 5, 10]);
    expect(niceTicks(38, 61, 4)).toEqual([40, 50, 60]);
    expect(niceTicks(38, 61, 6)).toEqual([40, 45, 50, 55, 60]);
    expect(niceTicks(1, 1)).toEqual([1]);
  });

  it("prints prices", () => {
    expect(dollars(41.2)).toBe("$41.20");
    expect(dollars(128.4)).toBe("$128");
  });

  it("knows every horizon key", () => {
    const keys: HorizonKey[] = ["tomorrow", "next_week", "next_month", "next_quarter", "next_year"];
    expect(horizonsThrough("next_year")).toEqual(keys);
  });
});
