/**
 * The Forecast tab's pure parts: which run to show, how often to ask, and
 * the rows the page renders from a generated report and its snapshot.
 *
 * Signs are not colours here: a negative forecast is not something wrong
 * (web/CLAUDE.md, "Red means something is wrong"); an audit error is.
 */
import type {
  ForecastRun,
  ForecastSnapshot,
  GeneratedReport,
  HorizonKey,
  InputObservation,
} from "@/types/forecast";
import { HORIZON_KEYS } from "@/types/forecast";

/** While a run is going, the page asks every 2 s; otherwise every 30 s. */
export const POLL_RUNNING_MS = 2_000;
export const POLL_IDLE_MS = 30_000;

export function activeRun(runs: readonly ForecastRun[]): ForecastRun | null {
  return runs.find((run) => run.state === "queued" || run.state === "running") ?? null;
}

export function pollEvery(runs: readonly ForecastRun[] | undefined): number {
  return runs && activeRun(runs) ? POLL_RUNNING_MS : POLL_IDLE_MS;
}

/** The run the page shows: the one going, else the newest. */
export function shownRun(runs: readonly ForecastRun[]): ForecastRun | null {
  return activeRun(runs) ?? runs[0] ?? null;
}

export function pct(value: number | null | undefined, digits = 2, signed = true): string {
  if (value === null || value === undefined || !Number.isFinite(value)) return "—";
  const text = value.toFixed(digits);
  return `${signed && value > 0 ? "+" : ""}${text}%`;
}

export function level(value: number | null | undefined, digits = 2): string {
  if (value === null || value === undefined || !Number.isFinite(value)) return "—";
  return value.toFixed(digits);
}

export interface HorizonRow {
  key: HorizonKey;
  label: string;
  days: number;
  median: number;
  p05: number;
  p95: number;
  probPositive: number;
  es5: number;
  /** Share of the probability inside the bins; below 0.9 the audit warns. */
  binCoverage: number;
}

export function horizonRows(report: GeneratedReport): HorizonRow[] {
  return HORIZON_KEYS.filter((key) => report.horizons[key]).map((key) => {
    const horizon = report.horizons[key];
    const summary = horizon.summary;
    return {
      key,
      label: horizon.label,
      days: horizon.trading_days,
      median: summary.median_pct,
      p05: summary.quantiles_pct.p05,
      p95: summary.quantiles_pct.p95,
      probPositive: summary.prob_positive,
      es5: summary.expected_shortfall_5pct,
      binCoverage: 1 - horizon.underflow_prob - horizon.overflow_prob,
    };
  });
}

const SOURCE_LABEL: Record<string, string> = {
  yahoo_chart_1d: "Yahoo daily close",
  yahoo_chart_1m: "Yahoo 1-min bar",
  cboe_daily_csv: "Cboe daily close",
};

/** "Yahoo 1-min bar NQ=F at 04:19 ET" or "Cboe daily close VIX9D, 2026-11-23". */
export function observedText(observation: InputObservation | undefined): string {
  if (!observation) return "";
  const source = SOURCE_LABEL[observation.source] ?? observation.source;
  if (observation.kind === "intraday_bar" && observation.observed_at) {
    const at = new Date(observation.observed_at).toLocaleTimeString("en-US", {
      timeZone: "America/New_York",
      hour: "2-digit",
      minute: "2-digit",
      hour12: false,
    });
    return `${source} ${observation.ticker} at ${at} ET`;
  }
  return `${source} ${observation.ticker}, ${observation.session_date}`;
}

export interface InputRow {
  field: keyof ForecastSnapshot;
  label: string;
  value: string;
  observed: string;
  /** Asked for, and not read. */
  missing: boolean;
}

type Format = "pct" | "level";

const formatted = (value: number | null, format: Format) =>
  format === "pct" ? pct(value) : level(value);

/** The inputs the page lists, in the order a 4:20am reader wants them:
 * what has already moved overnight first, then the volatility family, then
 * the prior close's context. */
const INPUTS: [keyof ForecastSnapshot, string, Format][] = [
  ["overnight_futures_change_pct", "Index futures since the close", "pct"],
  ["pre_market_change_pct", "Pre-market vs. prior close", "pct"],
  ["premarket_window_change_pct", "Opening pre-market window", "pct"],
  ["vix_overnight_level", "VIX overnight", "level"],
  ["vix_level", "VIX (prior close)", "level"],
  ["vix9d_level", "VIX9D (prior close)", "level"],
  ["vix3m_level", "VIX3M (prior close)", "level"],
  ["vxn_level", "VXN (prior close)", "level"],
  ["rvx_level", "RVX (prior close)", "level"],
  ["iv_rank_pct", "IV rank (252 sessions)", "level"],
  ["symbol_iv_pct", "Implied vol, leverage-scaled", "level"],
  ["realized_vol_20d_pct", "Realised vol, 20 sessions", "level"],
  ["futures_daily_change_pct", "Index futures, last session", "pct"],
  ["prev_close", "Prior close", "level"],
  ["us_10y_yield_pct", "10-year yield", "level"],
  ["dxy_level", "Dollar index", "level"],
  ["wti_crude_usd", "WTI crude", "level"],
];

export function inputRows(snapshot: ForecastSnapshot): InputRow[] {
  const observed = new Map(snapshot.input_observations.map((o) => [o.field, o]));
  const missing = new Set(snapshot.missing_inputs);
  return INPUTS.flatMap(([field, label, format]) => {
    const raw = snapshot[field];
    const value = typeof raw === "number" ? raw : null;
    // RVX belongs to the Russell funds alone; an absent field nobody asked
    // for is not a missing input.
    if (value === null && !missing.has(String(field))) return [];
    return [
      {
        field,
        label:
          field === "overnight_futures_change_pct"
            ? `${snapshot.overnight_futures_symbol} since the close`
            : label,
        value: formatted(value, format),
        observed: observedText(observed.get(String(field))),
        missing: value === null,
      },
    ];
  });
}

/** "4:20 AM" style, Eastern, for the as-of line. */
export function easternTime(iso: string): string {
  return new Date(iso).toLocaleString("en-US", {
    timeZone: "America/New_York",
    month: "short",
    day: "numeric",
    hour: "numeric",
    minute: "2-digit",
  });
}

// ------------------------------------------------------------------
// The hand-off to the Live page's RiskReportPanel: the tab leaves the
// report in this browser tab's sessionStorage, the panel takes it once.
// Session storage can be missing or refuse (a private window, a blocked
// site), so every access is guarded; the hand-off is a convenience, and
// the report can always be downloaded and pasted instead.

const HANDOFF_KEY = "vai.forecast.handoff";

export function handOffReport(report: GeneratedReport, storage?: Storage): boolean {
  try {
    (storage ?? window.sessionStorage).setItem(HANDOFF_KEY, JSON.stringify(report, null, 2));
    return true;
  } catch {
    return false;
  }
}

export function takeHandedOffReport(storage?: Storage): string | null {
  try {
    const store = storage ?? window.sessionStorage;
    const text = store.getItem(HANDOFF_KEY);
    store.removeItem(HANDOFF_KEY);
    return text;
  } catch {
    return null;
  }
}

export function reportFileName(report: GeneratedReport): string {
  return `${report.symbol.toLowerCase()}_${report.target_session}_forecast.json`;
}
