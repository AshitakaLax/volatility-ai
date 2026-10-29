/**
 * The Algorithms tab's contract with server/algorithms.py (mirrored by hand,
 * like the rest of types/). A candidate is a backtest cell kept as a library
 * entry; it is promoted by a passing paper trial or the owner's sign-off, and
 * published into config/live_profiles/.
 */
import type { LegacyLots } from "@/types/control";

export type AlgorithmStage = "candidate" | "paper_trial" | "promoted" | "published";

/** The promotion gate's verdict, or the owner's sign-off (manual). */
export interface Promotion {
  passed: boolean;
  manual?: boolean;
  failures: string[];
  /** Counters nobody journals yet: each fails a paper trial. */
  unmeasured?: string[];
  criteria?: Record<string, number>;
  record?: Record<string, number | string>;
  reason?: string;
  by?: string;
  at?: string;
  evaluated_at?: string;
}

export interface Trial {
  deployment: string;
  /** Epoch seconds the trial's counting starts from. */
  started_at: number;
  started: string;
  command: string | null;
  evaluation: Promotion | null;
}

export interface Candidate {
  id: string;
  label: string;
  symbols: string[];
  strategy_id: string;
  strategy_params: Record<string, unknown>;
  step: number | null;
  profit_target: number | null;
  evidence: { backtest?: Record<string, string | number | null> };
  created_at: string;
  created_by: string;
  trial: Trial | null;
  promotion: Promotion | null;
  published?: { at: string; by: string };
  stage: AlgorithmStage;
  /** Paper deployments trading its fund. */
  paper_deployments: string[];
}

export interface AlgorithmLibrary {
  candidates: Candidate[];
}

export interface CandidateRequest {
  run: string;
  ticker: string;
  cell: number;
  operator: string;
}

export interface TrialRequest {
  deployment: string;
  operator: string;
  legacy_lots: LegacyLots;
  timing: "now" | "next_session" | "when_flat";
}
