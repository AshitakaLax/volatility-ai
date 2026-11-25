/**
 * The Forecast tab (server/forecast_generator.py, research/forecast_generator/).
 *
 * Hand-mirrored from server/: the status and runs are forecast_generator.py's
 * responses, a result is generator.Generated.to_dict(), the report is the risk
 * report engine/core/risk_report.py parses, and the snapshot is
 * generator.build_snapshot's. Change both sides together.
 */
import type { Audit } from "@/types/riskReport";

export type ForecastEngineId = "chronos" | "bootstrap";

export interface ForecastEngine {
  id: ForecastEngineId;
  label: string;
  available: boolean;
  /** Where it runs, or why it cannot run here. */
  detail: string;
}

export const HORIZON_KEYS = [
  "tomorrow",
  "next_week",
  "next_month",
  "next_quarter",
  "next_year",
] as const;

export type HorizonKey = (typeof HORIZON_KEYS)[number];

export interface ReportBin {
  min_pct: number;
  max_pct: number;
  prob: number;
  cdf: number;
}

export interface ReportHorizon {
  label: string;
  trading_days: number;
  bin_width_pct: number;
  underflow_prob: number;
  overflow_prob: number;
  bins: ReportBin[];
  summary: {
    mean_pct: number;
    median_pct: number;
    std_pct: number;
    prob_positive: number;
    expected_shortfall_5pct: number;
    quantiles_pct: Record<"p01" | "p05" | "p25" | "p75" | "p95" | "p99", number>;
  };
}

/** The risk report, as the Live page is pasted it. */
export interface GeneratedReport {
  schema_version: string;
  symbol: string;
  as_of: string;
  target_session: string;
  base_price: number;
  return_type: "simple_pct";
  model: string;
  prompt_version: string;
  execution_signals: {
    data_quality: { confidence_score: number; source_coverage: string; missing_inputs: string[] };
    regime: string;
    volatility_state: string;
    implied_vs_realized_vol_spread_pct: number;
    expected_1d_move_pct: number;
    skew_bias: string;
    overnight_gap_risk: string;
    kelly_fraction_cap: number;
    next_day_catalysts: { time_utc?: string; event: string; impact: string }[];
    suggested_strategy_weights: Record<string, number>;
  };
  horizons: Record<HorizonKey, ReportHorizon>;
}

/** Where and when one snapshot value was read. */
export interface InputObservation {
  field: string;
  source: "yahoo_chart_1d" | "yahoo_chart_1m" | "cboe_daily_csv" | string;
  ticker: string;
  kind: "daily_close" | "intraday_bar";
  observed_at: string | null;
  session_date: string;
  reference_observed_at: string | null;
}

/** What was observable at the run. Display only: none of it is a model input. */
export interface ForecastSnapshot {
  symbol: string;
  underlying_symbol: string;
  leverage_factor: number;
  base_session_date: string;
  target_session: string;
  as_of_utc: string;
  market_session_phase: string;
  prev_close: number;
  pre_market_or_latest_price: number | null;
  pre_market_change_pct: number | null;
  premarket_window_start_et: string;
  premarket_window_end_et: string;
  premarket_open_4am: number | null;
  premarket_window_high: number | null;
  premarket_window_low: number | null;
  premarket_window_change_pct: number | null;
  premarket_window_volume: number | null;
  intraday_high: number | null;
  intraday_low: number | null;
  five_day_return_pct: number | null;
  twenty_day_return_pct: number | null;
  overnight_futures_symbol: string;
  overnight_futures_change_pct: number | null;
  futures_daily_change_pct: number | null;
  vix_level: number | null;
  vix_overnight_level: number | null;
  vxn_level: number | null;
  rvx_level: number | null;
  vix9d_level: number | null;
  vix3m_level: number | null;
  symbol_iv_pct: number | null;
  iv_rank_pct: number | null;
  realized_vol_20d_pct: number | null;
  us_10y_yield_pct: number | null;
  dxy_level: number | null;
  wti_crude_usd: number | null;
  missing_inputs: string[];
  confidence_score: number;
  source_coverage: string;
  notes: string[];
  input_observations: InputObservation[];
}

export interface ForecastResult {
  report: GeneratedReport;
  audit: Audit & { session: string | null; sha256: string | null };
  snapshot: ForecastSnapshot;
  sources: { title: string; uri: string; domain: string }[];
  diagnostics: {
    engine: ForecastEngineId;
    model_id: string;
    history_observations: number;
    covariates_used: string[];
    simulation_paths: number;
    block_length: number;
    direct_steps: number;
    native_horizon: number;
    extension_steps: number;
    base_session: string;
    target_session: string;
    calibration_status: string;
  };
}

export type ForecastRunState = "queued" | "running" | "done" | "failed" | "refused";

export interface ForecastRun {
  id: string;
  symbol: string;
  engine: ForecastEngineId;
  state: ForecastRunState;
  started_at: string;
  finished_at: string | null;
  progress: { at: string; message: string }[];
  /** Why it was refused, or what failed. */
  error: string | null;
  result: ForecastResult | null;
}

/** GET /api/forecast/status. */
export interface ForecastStatus {
  engines: ForecastEngine[];
  symbols: string[];
  can_generate: boolean;
  target_session: string | null;
  why_not: string | null;
  /** Newest first. */
  runs: ForecastRun[];
}

export interface StartedForecast {
  run: ForecastRun;
  target_session: string;
}
