/**
 * Shapes returned by /api/ml/* -- see server/ml_insights.py.
 *
 * THIS IS A RESEARCH VIEW. Nothing typed here is a trading signal: no
 * sizing strategy reads any of it, and none of it is in a position to
 * become one by a UI change alone. See ml_plan.md, "Phase ML-0" for
 * what has actually been measured, and how weak most of it still is.
 */

export interface ExternalSeries {
  key: string;
  provider: "fred" | "cboe" | "yahoo";
  remote_id: string;
  category: string;
  description: string;
  lag_days: number;
  rows: number;
  first: string;
  last: string;
}

export interface SourcesSummary {
  total_series: number;
  by_category: Record<string, number>;
  series: ExternalSeries[];
}

export interface DatasetSummary {
  rows: number;
  stride: number;
  first: string;
  last: string;
  feature_count: number;
  label_count: number;
  features_fully_present: number;
  features_below_half: string[];
  base_rate: Record<string, number>;
}

export interface DatasetsResponse {
  tickers: Record<string, DatasetSummary>;
}

/** Per-fold AUC for one feature set, plus the paired comparison against
 * `bar` -- see tools/evaluate_ml_features.py's own docstring for why
 * paired, not two independent means. */
export interface TickerEvaluation {
  per_fold: {
    bar: number[];
    macro: number[];
    both: number[];
    shuffled: number[];
  };
  paired_lift_mean: number;
  paired_lift_se: number;
  folds_positive: number;
  verdict: string;
  base_rate: number;
}

export interface EvaluationResponse {
  label: string;
  tickers: Record<string, TickerEvaluation>;
}

export interface AblationBlock {
  category: string;
  columns: number;
  lift_mean: number;
  lift_se: number;
  folds_positive: number;
  folds_total: number;
  consistent: boolean;
}

export interface TickerAblation {
  baseline_auc: number;
  blocks: AblationBlock[];
  consistent_count: number;
  total_blocks: number;
}

export interface AblationResponse {
  label: string;
  tickers: Record<string, TickerAblation>;
}
