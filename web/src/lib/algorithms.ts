/** The Algorithms tab's pure logic: where a candidate stands, and what it can do next. */
import type { AlgorithmStage, Candidate, EnginePick } from "@/types/algorithms";

export const STAGE_LABEL: Record<AlgorithmStage, string> = {
  candidate: "Candidate",
  paper_trial: "On paper trial",
  promoted: "Promoted",
  published: "Live profile",
};

/** Section order on the page: the way a candidate travels. */
export const STAGES: AlgorithmStage[] = ["candidate", "paper_trial", "promoted", "published"];

export type CandidateAction = "trial" | "evaluate" | "override" | "publish" | "delete";

/** The actions that apply at a stage. A promoted candidate may be published; any
 * candidate that is not yet may be signed off by the owner. */
export function actionsFor(candidate: Candidate): CandidateAction[] {
  switch (candidate.stage) {
    case "candidate":
      return [
        ...(candidate.paper_deployments.length > 0 ? (["trial"] as const) : []),
        "override",
        "delete",
      ];
    case "paper_trial":
      return ["evaluate", "override"];
    case "promoted":
      return ["publish"];
    case "published":
      return [];
  }
}

/** Why a candidate cannot start a paper trial, or null when it can. */
export function trialBlocker(candidate: Candidate): string | null {
  if (candidate.paper_deployments.length > 0) return null;
  const refused = candidate.paper_refused ?? [];
  if (refused.length > 0) {
    // Paper deployments on its fund exist, but their trader would refuse it:
    // say why, since only their own config files can change that.
    return `No paper deployment would take it: ${refused
      .map((entry) => `${entry.deployment} — ${entry.reason}`)
      .join("; ")}`;
  }
  return `No paper deployment trades ${candidate.symbols.join(", ")}: a trial needs one (a paper account for that fund).`;
}

/** "paper trial" or "owner sign-off (manual)" for a promoted candidate. */
export function promotionKind(candidate: Candidate): string | null {
  if (!candidate.promotion?.passed) return null;
  return candidate.promotion.manual ? "owner sign-off (manual)" : "paper trial";
}

export function percent(value: unknown): string {
  return typeof value === "number" && Number.isFinite(value) ? `${value.toFixed(1)}%` : "—";
}

/** One line of the engine-pick menu: where it ran, what it is, how it did. */
export function pickLabel(pick: EnginePick): string {
  const share = (value: number | null | undefined) =>
    value === null || value === undefined ? "--" : `${Number((value * 100).toFixed(3))}%`;
  const figure = (value: number | null | undefined) =>
    value === null || value === undefined ? "--" : `${value.toFixed(1)}%`;
  return [
    pick.ticker,
    pick.model ?? "?",
    `step ${share(pick.grid)} / target ${share(pick.target)}`,
    `CAGR ${figure(pick.m.cagr_pct)}`,
    `DD ${figure(pick.m.max_drawdown_pct)}`,
    pick.added ? "(added)" : null,
  ]
    .filter(Boolean)
    .join(" · ");
}
