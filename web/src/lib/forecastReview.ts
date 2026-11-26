/**
 * The Forecast tab's review: every report the forecast database keeps
 * (server/risk_forecasts.py, GET .../reports and .../report), what each said
 * about each horizon, and what came of it. Pure functions the tab's
 * components draw from, pinned by forecastReview.test.ts.
 *
 * A report says five things about the future -- the next session, a week, a
 * month, a quarter and a year (engine/core/risk_report.HORIZONS) -- and the
 * database scores each against the close of its last session once that has
 * closed: the next session's by the nightly tracking run, the longer ones as
 * each one's last session passes (tools/score_risk_reports.score_horizon).
 *
 * Signs are not colours (web/CLAUDE.md, "Red means something is wrong"): a
 * forecast of a fall is not a fault. Where a close landed outside its range
 * is, and wears the same marks the Live page's chart uses (lib/forecastChart).
 */
import { landing, type Landing } from "@/lib/forecastChart";
import { sessionDay } from "@/lib/riskReport";
import {
  HORIZON_KEYS,
  type GeneratedReport,
  type HorizonKey,
  type ReportHorizon,
} from "@/types/forecast";
import type {
  ForecastReceipt,
  KeptReport,
  LongerHorizonKey,
  RiskReportEntry,
} from "@/types/riskReport";

export const HORIZON_LABEL: Record<HorizonKey, string> = {
  tomorrow: "1 day",
  next_week: "1 week",
  next_month: "1 month",
  next_quarter: "1 quarter",
  next_year: "1 year",
};

/** The sessions each spans (engine/core/risk_report.HORIZONS). */
export const HORIZON_SESSIONS: Record<HorizonKey, number> = {
  tomorrow: 1,
  next_week: 5,
  next_month: 21,
  next_quarter: 63,
  next_year: 252,
};

export const LONGER_HORIZONS: readonly LongerHorizonKey[] = [
  "next_week",
  "next_month",
  "next_quarter",
  "next_year",
];

// ------------------------------------------------------------------
// Who made it, with what, and who it was sent to

/** A model string as a short name: the generator's and the public
 * service's Chronos-2 told apart, anything else up to its first
 * parenthesis. The whole string is shown beside it where there is room. */
export function modelLabel(model: string | null | undefined): string {
  const text = (model ?? "").trim();
  if (!text) return "unnamed model";
  if (/^historical-bootstrap baseline/i.test(text)) return "Historical baseline";
  if (/chronos-2 zero-shot/i.test(text)) return "Chronos-2";
  if (/chronos-2/i.test(text) && /hf\.space|public service/i.test(text)) {
    return "Chronos-2 (public service)";
  }
  const head = text.split(" (")[0]?.trim() ?? text;
  return head.length > 40 ? `${head.slice(0, 39)}…` : head;
}

/** Who first added it: the operator the page or the forecast service named,
 * or a file imported by hand -- and only when neither did, a trader's archive
 * copied in overnight (its copy carries the time the trader was sent it, so
 * it can tie with the Check that sent it). */
export function madeBy(receipts: readonly ForecastReceipt[]): string {
  const first = receipts.find((r) => !r.via.startsWith("archive:")) ?? receipts[0];
  if (!first) return "unknown";
  if (first.via.startsWith("archive:")) return `${first.via.slice("archive:".length)}'s archive`;
  if (first.via === "import") return first.operator ? `imported by ${first.operator}` : "imported";
  return first.operator || "the page";
}

/** How it reached the database, as a phrase: "kept by the forecast service",
 * "imported from a file", "copied from paper-ultimate's archive". */
export function keptText(receipts: readonly ForecastReceipt[]): string {
  const first = receipts.find((r) => !r.via.startsWith("archive:")) ?? receipts[0];
  if (!first) return "not kept yet";
  if (first.via.startsWith("archive:")) {
    return `copied from ${first.via.slice("archive:".length)}'s archive`;
  }
  if (first.via === "import") return "imported from a file";
  if (first.operator === "forecast service") return "kept by the forecast service";
  return first.operator ? `kept by ${first.operator}` : "kept from the page";
}

/** One trader's archive entry for a report: sent there, and what it did. */
export interface Applied {
  deployment: string;
  outcome: RiskReportEntry["outcome"];
  at: string;
  operator: string;
}

/** Each report's archive entries across the traders, by its id. */
export function appliedBySha(
  archives: Record<string, readonly RiskReportEntry[]>,
): Map<string, Applied[]> {
  const out = new Map<string, Applied[]>();
  for (const [deployment, entries] of Object.entries(archives)) {
    for (const entry of entries) {
      const list = out.get(entry.sha256) ?? [];
      list.push({
        deployment,
        outcome: entry.outcome,
        at: entry.received_at,
        operator: entry.operator,
      });
      out.set(entry.sha256, list);
    }
  }
  for (const list of out.values()) list.sort((a, b) => a.deployment.localeCompare(b.deployment));
  return out;
}

/** "applied to paper-ultimate", "not applied: paper-ultimate", "not sent to a
 * trader". A trader whose archive the database copied it from, and whose
 * archive is not read here now, is "sent to" it. */
export function appliedText(
  applied: readonly Applied[] | undefined,
  receipts: readonly ForecastReceipt[] = [],
): string {
  const known = new Set((applied ?? []).map((a) => a.deployment));
  const taken = (applied ?? []).filter((a) => a.outcome !== "not_applied").map((a) => a.deployment);
  const refused = (applied ?? [])
    .filter((a) => a.outcome === "not_applied")
    .map((a) => a.deployment);
  const archived = [
    ...new Set(
      receipts
        .filter((r) => r.via.startsWith("archive:"))
        .map((r) => r.via.slice("archive:".length))
        .filter((deployment) => !known.has(deployment)),
    ),
  ];
  const parts = [];
  if (taken.length) parts.push(`applied to ${taken.join(", ")}`);
  if (refused.length) parts.push(`not applied: ${refused.join(", ")}`);
  if (archived.length) parts.push(`sent to ${archived.join(", ")}`);
  return parts.length ? parts.join("; ") : "not sent to a trader";
}

/** The kept row a run's report became, when it was kept: the same fund,
 * moment and model. (Its hash is the server's to compute.) */
export function keptRowFor(
  report: GeneratedReport,
  rows: readonly KeptReport[],
): KeptReport | undefined {
  const at = Date.parse(report.as_of);
  return rows.find(
    (row) =>
      row.symbol === report.symbol && Date.parse(row.as_of) === at && row.model === report.model,
  );
}

// ------------------------------------------------------------------
// What a report says about each horizon, and what came of it

export type Unit = "pct" | "price";

export interface FanPoint {
  key: HorizonKey | "base";
  label: string;
  sessions: number;
  p05: number;
  p25: number;
  median: number;
  p75: number;
  p95: number;
}

/** A value of `report` in the unit shown: its return, or the price that
 * return reaches from the report's base close. */
export function inUnit(
  report: Pick<GeneratedReport, "base_price">,
  pct: number,
  unit: Unit,
): number {
  return unit === "price" ? report.base_price * (1 + pct / 100) : pct;
}

/** The horizons shown, the first through `through`. */
export function horizonsThrough(through: HorizonKey): HorizonKey[] {
  return HORIZON_KEYS.slice(0, HORIZON_KEYS.indexOf(through) + 1);
}

/** The fan: the base close, then each horizon's 90% range (p05-p95), middle
 * 50% (p25-p75) and median, through `through`. */
export function fanPoints(report: GeneratedReport, through: HorizonKey, unit: Unit): FanPoint[] {
  const zero = inUnit(report, 0, unit);
  const base: FanPoint = {
    key: "base",
    label: "Close",
    sessions: 0,
    p05: zero,
    p25: zero,
    median: zero,
    p75: zero,
    p95: zero,
  };
  return [
    base,
    ...horizonsThrough(through).map((key) => {
      const summary = report.horizons[key].summary;
      const q = summary.quantiles_pct;
      return {
        key,
        label: HORIZON_LABEL[key],
        sessions: HORIZON_SESSIONS[key],
        p05: inUnit(report, q.p05, unit),
        p25: inUnit(report, q.p25, unit),
        median: inUnit(report, summary.median_pct, unit),
        p75: inUnit(report, q.p75, unit),
        p95: inUnit(report, q.p95, unit),
      };
    }),
  ];
}

/** What came of one horizon: where its close landed, or the session it
 * waits for. */
export interface Outcome {
  landing: Landing;
  return_pct: number | null;
  /** The session it is measured at; null for a report not kept. */
  end_session: string | null;
}

/** Where a scored close landed: its PIT (where it fell in the report's
 * distribution) says which way it missed. */
export function scoreLanding(score: { in_50: boolean; in_90: boolean; pit: number }): Landing {
  if (score.in_50) return "in50";
  if (score.in_90) return "in90";
  return score.pit >= 0.5 ? "above" : "below";
}

/** What came of one longer horizon of a kept report. */
export function horizonOutcome(row: KeptReport, key: LongerHorizonKey): Outcome {
  const found = row.horizons?.[key];
  const score = found?.score ?? null;
  if (!score)
    return {
      landing: "pending",
      return_pct: null,
      end_session: found?.end_session ?? null,
    };
  return {
    landing: scoreLanding(score),
    return_pct: score.return_pct,
    end_session: score.end_session,
  };
}

/** Where each horizon's close landed in the report's ranges, from its kept
 * row: the next session's from its close and score, each longer one from
 * its horizon score once its last session has closed. Null for a report
 * not kept. */
export function outcomes(row: KeptReport | null | undefined): Record<HorizonKey, Outcome> | null {
  if (!row) return null;
  const out = {
    tomorrow: {
      landing: landing(row),
      return_pct: row.actual?.return_pct ?? null,
      end_session: row.session,
    },
  } as Record<HorizonKey, Outcome>;
  for (const key of LONGER_HORIZONS) out[key] = horizonOutcome(row, key);
  return out;
}

/** Short, for a table cell: "in its 50%", "in its 90%", "above its 90%",
 * "below its 90%", or the session it waits for. */
export function outcomeText(outcome: Outcome | undefined, day: (iso: string) => string): string {
  if (!outcome) return "--";
  if (outcome.landing === "pending" && !outcome.end_session) return "waiting for the close";
  switch (outcome.landing) {
    case "in50":
      return "in its 50%";
    case "in90":
      return "in its 90%";
    case "above":
      return "above its 90%";
    case "below":
      return "below its 90%";
    default:
      return outcome.end_session ? `closes ${day(outcome.end_session)}` : "waiting";
  }
}

// ------------------------------------------------------------------
// One horizon's distribution

export interface DistributionBar {
  lo: number;
  hi: number;
  /** The chance the return lands in [lo, hi). */
  prob: number;
  /** prob per percentage point, so bins of different widths compare. */
  density: number;
}

export interface Distribution {
  bars: DistributionBar[];
  /** Below the first bin and above the last. */
  under: number;
  over: number;
  lo: number;
  hi: number;
}

export function distribution(horizon: ReportHorizon): Distribution {
  const bars = horizon.bins
    .filter((bin) => bin.max_pct > bin.min_pct)
    .map((bin) => ({
      lo: bin.min_pct,
      hi: bin.max_pct,
      prob: bin.prob,
      density: bin.prob / (bin.max_pct - bin.min_pct),
    }));
  return {
    bars,
    under: horizon.underflow_prob,
    over: horizon.overflow_prob,
    lo: bars.length ? Math.min(...bars.map((b) => b.lo)) : -1,
    hi: bars.length ? Math.max(...bars.map((b) => b.hi)) : 1,
  };
}

// ------------------------------------------------------------------
// The track record

export interface HorizonTally {
  closed: number;
  in90: number;
  in50: number;
}

export interface ModelRecord {
  model: string;
  reports: number;
  /** By horizon: of those whose close is in, how many landed in each range. */
  horizons: Record<HorizonKey, HorizonTally>;
}

function tally(rows: readonly KeptReport[], model: string): ModelRecord {
  const horizons = Object.fromEntries(
    HORIZON_KEYS.map((key) => [key, { closed: 0, in90: 0, in50: 0 }]),
  ) as Record<HorizonKey, HorizonTally>;
  for (const row of rows) {
    const next = landing(row);
    if (next !== "pending") {
      horizons.tomorrow.closed += 1;
      if (next === "in50" || next === "in90") horizons.tomorrow.in90 += 1;
      if (next === "in50") horizons.tomorrow.in50 += 1;
    }
    for (const key of LONGER_HORIZONS) {
      const score = row.horizons?.[key]?.score;
      if (!score) continue;
      horizons[key].closed += 1;
      if (score.in_90) horizons[key].in90 += 1;
      if (score.in_50) horizons[key].in50 += 1;
    }
  }
  return { model, reports: rows.length, horizons };
}

/** How often each horizon's close landed inside its ranges: for the report
 * in force each session (its newest, the one the traders read), and for
 * every report of each model. A calibrated forecast puts about 9 in 10
 * inside its 90% range and half inside its middle 50%. */
export function calibration(rows: readonly KeptReport[]): {
  inForce: ModelRecord;
  byModel: ModelRecord[];
} {
  const groups = new Map<string, KeptReport[]>();
  for (const row of rows) {
    const name = modelLabel(row.model);
    groups.set(name, [...(groups.get(name) ?? []), row]);
  }
  return {
    inForce: tally(
      rows.filter((row) => row.newest),
      "The report in force each session",
    ),
    byModel: [...groups.entries()]
      .map(([name, list]) => tally(list, name))
      .sort((a, b) => b.reports - a.reports || a.model.localeCompare(b.model)),
  };
}

/** "2 of 4", or "none closed yet". */
export function caught(found: HorizonTally, band: "in90" | "in50"): string {
  return found.closed ? `${found[band]} of ${found.closed}` : "none closed yet";
}

// ------------------------------------------------------------------
// Axes

/** Round ticks covering [lo, hi], about `count` of them. */
export function niceTicks(lo: number, hi: number, count = 5): number[] {
  if (!(hi > lo)) return [lo];
  const raw = (hi - lo) / Math.max(1, count);
  const power = 10 ** Math.floor(Math.log10(raw));
  const step = [1, 2, 2.5, 5, 10].map((m) => m * power).find((s) => s >= raw) ?? raw;
  const out: number[] = [];
  for (let value = Math.ceil(lo / step) * step; value <= hi + step * 1e-9; value += step) {
    out.push(Number(value.toFixed(10)));
  }
  return out;
}

/** The y range every series and outcome drawn reaches, padded a little. */
export function fanExtent(
  series: readonly FanPoint[][],
  extra: readonly number[] = [],
): [number, number] {
  const values = [...series.flatMap((points) => points.flatMap((p) => [p.p05, p.p95])), ...extra];
  if (!values.length) return [-1, 1];
  let lo = Math.min(...values);
  let hi = Math.max(...values);
  if (hi - lo < 1e-9) {
    lo -= 1;
    hi += 1;
  }
  const pad = (hi - lo) * 0.06;
  return [lo - pad, hi + pad];
}

/** "$41.20", "$128". */
export function dollars(value: number): string {
  return `$${value.toFixed(Math.abs(value) >= 100 ? 0 : 2)}`;
}

/** "Fri, Nov 20 · 9:38 PM · eod_regime_conditioned_forecast": a kept report, named. */
export function reportName(row: Pick<KeptReport, "session" | "as_of" | "model">): string {
  return `${sessionDay(row.session)} · ${easternClock(row.as_of)} · ${modelLabel(row.model)}`;
}

/** "7:44 AM" Eastern. */
export function easternClock(iso: string): string {
  return new Date(iso).toLocaleTimeString("en-US", {
    timeZone: "America/New_York",
    hour: "numeric",
    minute: "2-digit",
  });
}
