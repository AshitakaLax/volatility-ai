/**
 * Shapes returned by /api/ml/* -- see server/ml_insights.py.
 *
 * THIS IS A RESEARCH VIEW. Nothing typed here is a trading signal: no
 * sizing strategy reads any of it, and none of it is in a position to
 * become one by a UI change alone. See ml_plan.md, "Phase ML-0" for what
 * has actually been measured, and how weak most of it still is.
 */

export type ByTicker<T> = Record<string, T>;

/** GET /sources returns these, sorted by (category, provider, remote_id). */
export interface MlSeries {
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

export interface Dataset {
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

/** Per-fold AUC for one feature set, plus the paired comparison against
 * `bar` -- see tools/evaluate_ml_features.py for why paired, not two
 * independent means. */
export interface Eval {
  per_fold: Record<"bar" | "macro" | "both" | "shuffled", number[]>;
  paired_lift_mean: number;
  paired_lift_se: number;
  folds_positive: number;
  verdict: string;
  base_rate: number;
}

export interface Ablation {
  baseline_auc: number;
  /** How many are `consistent` is counted from here, not sent. */
  blocks: {
    category: string;
    columns: number;
    lift_mean: number;
    lift_se: number;
    folds_positive: number;
    folds_total: number;
    consistent: boolean;
  }[];
}
