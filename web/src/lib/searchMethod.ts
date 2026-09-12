/**
 * How the submitted combination space is EXPLORED, not how big it is --
 * that remains every enabled per-field "Sweep" checkbox (sweepStrategies.ts
 * generates each field's own value list; this only picks the algorithm
 * that walks the resulting grid). Mirrors server/backtest.py's
 * RunRequest.search_strategy/n_trials/rank_by/search_direction/search_seed
 * exactly -- see that file's own field comments for the server-side half
 * of this contract.
 *
 * A DIFFERENT "strategy" THAN sweepStrategies.ts's SweepStrategyKind,
 * despite the name collision risk: that one picks how ONE field's OWN
 * range is sampled into concrete values (linear/logarithmic/random).
 * This one picks how the ENGINE walks the resulting cross-product
 * (exhaustively, or via Optuna). Named SearchMethod, not "search
 * strategy", specifically so the two are never confused in code or in
 * the UI -- they answer different questions and a submission uses both
 * at once (e.g. a random-sampled range on one field, explored by TPE).
 */

export type SearchMethodKind = "grid" | "bayesian";

/**
 * Columns _simulate_single's own metrics dict actually carries
 * (src/optimization/optimization_controller.py) -- the set BayesianSearch
 * can optimize toward AND the plain grid summary can sort by. "Sharpe
 * Ratio"/"Sortino Ratio" are NOT here on purpose: they are computed
 * later, only for display, and are not valid rank_by targets -- see
 * RunRequest.rank_by's own comment.
 */
export const RANK_BY_OPTIONS: readonly string[] = [
  "Capital Velocity Index",
  "Total Return %",
  "Return/Drawdown",
  "Harvest to Stuck Ratio",
  "Max Drawdown %",
];

export const DEFAULT_RANK_BY = "Capital Velocity Index";

/** Matches RunRequest.n_trials' own Field(ge=2, le=500). */
export const MIN_TRIALS = 2;
export const MAX_TRIALS = 500;

export interface SearchMethodState {
  strategy: SearchMethodKind;
  /** Raw text, like every other numeric field in this form -- "" is the
   * distinct blank/unset state. Only meaningful while strategy is
   * "bayesian"; REQUIRED then (server/backtest.py's build_config
   * refuses a bayesian request with none, on purpose -- see its own
   * comment on why no default budget is offered). */
  nTrials: string;
  rankBy: string;
  direction: "maximize" | "minimize";
  /** Optional; "" -> a fresh exploration order each submission. */
  seed: string;
}

export const DEFAULT_SEARCH_METHOD_STATE: SearchMethodState = {
  strategy: "grid",
  nTrials: "",
  rankBy: DEFAULT_RANK_BY,
  direction: "maximize",
  seed: "",
};

/**
 * Client-side errors for the current state, or [] when it is valid
 * enough to submit. Mirrors the one thing the server actually enforces
 * (n_trials required and in range for bayesian) -- everything else
 * (rank_by, direction) has no wrong answer at this layer since the
 * dropdown only ever offers valid values.
 */
export function searchMethodErrors(state: SearchMethodState): string[] {
  if (state.strategy !== "bayesian") return [];
  const raw = state.nTrials.trim();
  if (raw === "") return ["enter a trial budget"];
  const n = Number(raw);
  if (!Number.isInteger(n) || n < MIN_TRIALS || n > MAX_TRIALS) {
    return [`trial budget must be a whole number from ${MIN_TRIALS} to ${MAX_TRIALS}`];
  }
  return [];
}
