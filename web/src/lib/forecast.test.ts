import { describe, expect, it } from "vitest";

import {
  POLL_IDLE_MS,
  POLL_RUNNING_MS,
  handOffReport,
  horizonRows,
  inputRows,
  observedText,
  pct,
  pollEvery,
  reportFileName,
  shownRun,
  takeHandedOffReport,
} from "@/lib/forecast";
import type { ForecastRun, ForecastSnapshot, GeneratedReport, ReportHorizon } from "@/types/forecast";

function horizon(label: string, days: number, median: number): ReportHorizon {
  return {
    label,
    trading_days: days,
    bin_width_pct: 1.5,
    underflow_prob: 0.05,
    overflow_prob: 0.07,
    bins: [],
    summary: {
      mean_pct: median,
      median_pct: median,
      std_pct: 3,
      prob_positive: 0.52,
      expected_shortfall_5pct: -8.4,
      quantiles_pct: { p01: -9, p05: -6.6, p25: -2, p75: 2, p95: 6.4, p99: 8.5 },
    },
  };
}

const report = {
  symbol: "TQQQ",
  target_session: "2026-11-25",
  horizons: {
    tomorrow: horizon("Tomorrow (1D)", 1, 0.17),
    next_week: horizon("Next Week (5D)", 5, 0.5),
    next_month: horizon("Next Month (21D)", 21, 1),
    next_quarter: horizon("Next Quarter (63D)", 63, 2),
    next_year: horizon("Next Year (252D)", 252, 5),
  },
} as unknown as GeneratedReport;

function run(state: ForecastRun["state"], id: string): ForecastRun {
  return {
    id,
    symbol: "TQQQ",
    engine: "bootstrap",
    state,
    started_at: "2026-11-25T09:20:00+00:00",
    finished_at: null,
    progress: [],
    error: null,
    result: null,
  };
}

const snapshot = {
  overnight_futures_symbol: "NQ=F",
  overnight_futures_change_pct: -3.09,
  pre_market_change_pct: null,
  vix_level: 26.36,
  rvx_level: null,
  prev_close: 46.19,
  missing_inputs: ["pre_market_change_pct"],
  input_observations: [
    {
      field: "overnight_futures_change_pct",
      source: "yahoo_chart_1m",
      ticker: "NQ=F",
      kind: "intraday_bar",
      observed_at: "2026-11-25T09:19:00Z",
      session_date: "2026-11-25",
      reference_observed_at: "2026-11-24T20:59:00Z",
    },
    {
      field: "vix_level",
      source: "yahoo_chart_1d",
      ticker: "^VIX",
      kind: "daily_close",
      observed_at: null,
      session_date: "2026-11-24",
      reference_observed_at: null,
    },
  ],
} as unknown as ForecastSnapshot;

describe("which run the Forecast tab shows, and how often it asks", () => {
  it("shows the run going, else the newest", () => {
    expect(shownRun([run("done", "b"), run("running", "a")])?.id).toBe("a");
    expect(shownRun([run("refused", "b"), run("done", "a")])?.id).toBe("b");
    expect(shownRun([])).toBeNull();
  });

  it("asks quickly only while a run is going", () => {
    expect(pollEvery([run("queued", "a")])).toBe(POLL_RUNNING_MS);
    expect(pollEvery([run("done", "a")])).toBe(POLL_IDLE_MS);
    expect(pollEvery(undefined)).toBe(POLL_IDLE_MS);
  });
});

describe("the report's rows", () => {
  it("lists the horizons in order, with what the bins hold", () => {
    const rows = horizonRows(report);
    expect(rows.map((r) => r.days)).toEqual([1, 5, 21, 63, 252]);
    expect(rows[0]).toMatchObject({ median: 0.17, p05: -6.6, p95: 6.4, es5: -8.4 });
    expect(rows[0]?.binCoverage).toBeCloseTo(0.88);
  });

  it("formats a signed percentage, and nothing as a dash", () => {
    expect(pct(1.234)).toBe("+1.23%");
    expect(pct(-3.09)).toBe("-3.09%");
    expect(pct(null)).toBe("—");
  });
});

describe("the snapshot's inputs", () => {
  it("lead with the overnight move, named for its future, with where it was read", () => {
    const rows = inputRows(snapshot);
    expect(rows[0]).toMatchObject({
      field: "overnight_futures_change_pct",
      label: "NQ=F since the close",
      value: "-3.09%",
      missing: false,
    });
    expect(rows[0]?.observed).toMatch(/^Yahoo 1-min bar NQ=F at 04:19 ET$/);
  });

  it("marks an input asked for and not read, and hides one nobody asked for", () => {
    const rows = inputRows(snapshot);
    expect(rows.find((r) => r.field === "pre_market_change_pct")).toMatchObject({ missing: true, value: "—" });
    expect(rows.find((r) => r.field === "rvx_level")).toBeUndefined();
  });

  it("names a daily close by its session", () => {
    expect(observedText(snapshot.input_observations[1])).toBe("Yahoo daily close ^VIX, 2026-11-24");
    expect(observedText(undefined)).toBe("");
  });
});

describe("handing the report to the Live page", () => {
  function memory(): Storage {
    const items = new Map<string, string>();
    return {
      get length() {
        return items.size;
      },
      clear: () => items.clear(),
      getItem: (key) => items.get(key) ?? null,
      key: (index) => [...items.keys()][index] ?? null,
      removeItem: (key) => void items.delete(key),
      setItem: (key, value) => void items.set(key, value),
    };
  }

  it("is taken once", () => {
    const storage = memory();
    expect(handOffReport(report, storage)).toBe(true);
    expect(JSON.parse(takeHandedOffReport(storage) ?? "{}").symbol).toBe("TQQQ");
    expect(takeHandedOffReport(storage)).toBeNull();
  });

  it("fails quietly where storage refuses", () => {
    const refusing = {
      ...memory(),
      setItem: () => {
        throw new Error("denied");
      },
      getItem: () => {
        throw new Error("denied");
      },
    } as Storage;
    expect(handOffReport(report, refusing)).toBe(false);
    expect(takeHandedOffReport(refusing)).toBeNull();
  });

  it("names the download by fund and session", () => {
    expect(reportFileName(report)).toBe("tqqq_2026-11-25_forecast.json");
  });
});
