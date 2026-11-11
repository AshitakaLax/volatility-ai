import { describe, expect, it } from "vitest";

import { actionsFor, pickLabel, promotionKind, trialBlocker } from "@/lib/algorithms";
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

  it("says why a paper deployment on its fund would refuse it", () => {
    const refused = {
      ...base,
      paper_deployments: [],
      paper_refused: [{ deployment: "paper", reason: "needs execution.allow_signal_exit" }],
    };
    expect(trialBlocker(refused)).toMatch(/paper — needs execution.allow_signal_exit/);
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

describe("pickLabel", () => {
  const pick = {
    run: "abc",
    ticker: "TQQQ",
    rank: 0,
    name: null,
    model: "ultimate",
    grid: 0.002,
    target: 0.1,
    start: null,
    end: null,
    m: { cagr_pct: 37.64, max_drawdown_pct: 22.2 },
    candidate_id: "ultimate-tqqq-abc-0",
    added: false,
  };

  it("names the fund, algorithm, grid and results", () => {
    expect(pickLabel(pick)).toBe(
      "TQQQ · ultimate · step 0.2% / target 10% · CAGR 37.6% · DD 22.2%",
    );
  });

  it("marks one already kept and tolerates figures a run did not record", () => {
    expect(pickLabel({ ...pick, added: true, m: {}, grid: null })).toBe(
      "TQQQ · ultimate · step -- / target 10% · CAGR -- · DD -- · (added)",
    );
  });
});
