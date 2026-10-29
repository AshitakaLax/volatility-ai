import { describe, expect, it } from "vitest";

import { actionsFor, promotionKind, trialBlocker } from "@/lib/algorithms";
import type { Candidate } from "@/types/algorithms";

const base = {
  id: "fixed-tqqq-abc123-0",
  label: "x",
  symbols: ["TQQQ"],
  strategy_id: "fixed",
  strategy_params: {},
  step: 0.01,
  profit_target: 0.02,
  evidence: {},
  created_at: "",
  created_by: "",
  trial: null,
  promotion: null,
  stage: "candidate",
  paper_deployments: ["paper"],
} as Candidate;

describe("what a candidate can do next", () => {
  it("offers a trial only where a paper deployment trades its fund", () => {
    expect(actionsFor(base)).toContain("trial");
    const none = { ...base, paper_deployments: [] };
    expect(actionsFor(none)).not.toContain("trial");
    expect(trialBlocker(none)).toMatch(/No paper deployment trades TQQQ/);
    expect(trialBlocker(base)).toBeNull();
  });

  it("lets the owner sign off before a pass, and only a promoted one publish", () => {
    expect(actionsFor(base)).toContain("override");
    expect(actionsFor({ ...base, stage: "paper_trial" })).toEqual(["evaluate", "override"]);
    expect(actionsFor({ ...base, stage: "promoted" })).toEqual(["publish"]);
    expect(actionsFor({ ...base, stage: "published" })).toEqual([]);
  });

  it("says a manual promotion is manual", () => {
    expect(promotionKind(base)).toBeNull();
    const manual = { ...base, promotion: { passed: true, manual: true, failures: [] } };
    expect(promotionKind(manual)).toBe("owner sign-off (manual)");
    expect(promotionKind({ ...manual, promotion: { passed: true, failures: [] } })).toBe(
      "paper trial",
    );
  });
});
