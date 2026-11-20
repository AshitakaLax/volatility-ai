import { describe, expect, it } from "vitest";

import {
  checkedByDefault,
  levers,
  overlayLine,
  parsePasted,
  reportDeployments,
  sessionDay,
  tierLabel,
  tierTone,
  would,
} from "@/lib/riskReport";
import type { DeploymentSummary } from "@/types/control";
import type { RiskOverlay, RiskReportPreview } from "@/types/riskReport";

function overlay(over: Partial<RiskOverlay> = {}): RiskOverlay {
  return {
    session: "2026-11-20",
    pause: false,
    buy_multiplier: 1,
    exposure_ceiling: null,
    step_multiplier: 1,
    target_multiplier: 1,
    blackouts: [],
    supersedes: [],
    mode: "advisory",
    tier: 0,
    weekly_ceiling: null,
    reasons: [],
    mapping_id: "v1",
    report_sha256: null,
    exempt: ["reversal"],
    ...over,
  };
}

function preview(over: Partial<RiskReportPreview> = {}): RiskReportPreview {
  return {
    deployment: "paper",
    label: "Paper",
    symbol: "TQQQ",
    paper: true,
    takes_reports: true,
    why_not: null,
    settings: { mode: "advisory", mapping: "v1", levers: { daily: true, spacing: true, weekly: true } },
    typed: null,
    audit: { ok: true, errors: [], warnings: [] },
    would: "apply",
    ...over,
  };
}

describe("the pasted report", () => {
  it("is one JSON object, a code fence allowed", () => {
    expect(parsePasted('```json\n{"symbol": "TQQQ"}\n```').report).toEqual({ symbol: "TQQQ" });
    expect(parsePasted("").report).toBeNull();
    expect(parsePasted("[1, 2]").error).toMatch(/one JSON object/);
    expect(parsePasted("{nope").error).toMatch(/^Not JSON/);
  });
});

describe("the deployments it may go to", () => {
  it("are every one configured for reports, real money beside paper", () => {
    const settings = { mode: "advisory" as const, mapping: "v1", levers: { daily: true, spacing: true, weekly: true } };
    const d = (id: string, paper: boolean, configured: boolean): DeploymentSummary => ({
      id,
      label: id,
      service: null,
      broker: "alpaca",
      error: null,
      paper,
      risk_reports: { takes: configured, why_not: null, settings: configured ? settings : null },
    });
    expect(reportDeployments([d("a", true, true), d("b", false, true), d("c", true, false)]).map((x) => x.id)).toEqual([
      "a",
      "b",
    ]);
  });

  it("are ticked when the report would do something to them", () => {
    expect(checkedByDefault(preview())).toBe(true);
    expect(checkedByDefault(preview({ would: "tighten" }))).toBe(true);
    expect(checkedByDefault(preview({ would: "not_applied" }))).toBe(false);
    expect(checkedByDefault(preview({ would: "unchanged" }))).toBe(false);
    expect(checkedByDefault(preview({ takes_reports: false }))).toBe(false);
    expect(checkedByDefault(preview({ audit: { ok: false, errors: [], warnings: [] } }))).toBe(false);
  });

  it("say why one takes none", () => {
    expect(would(preview({ takes_reports: false, why_not: "its config has no risk.overlay" })).label).toContain(
      "risk.overlay",
    );
    expect(would(preview({ would: "refused" })).tone).toBe("loss");
  });
});

describe("the overlay in words", () => {
  it("names each lever that changes", () => {
    expect(levers(overlay())).toEqual([]);
    expect(levers(overlay({ pause: true, step_multiplier: 2.04, exposure_ceiling: 0.6 }))).toEqual([
      "no new grid buys",
      "lots ≤ 60% of equity",
      "step ×2.0",
    ]);
    expect(levers(overlay({ buy_multiplier: 0.75 }))).toEqual(["buys ×0.75"]);
  });

  it("tiers and their tones", () => {
    expect(tierLabel(3)).toBe("tier 3");
    expect(tierLabel(3, true)).toBe("abstains");
    expect(tierTone(3)).toBe("loss");
    expect(tierTone(1)).toBe("stuck");
    expect(tierTone(0)).toBe("neutral");
  });

  it("the session as a day", () => {
    expect(sessionDay("2026-11-20")).toBe("Fri, Nov 20");
  });

  it("the trader's line", () => {
    expect(overlayLine({ session: "2026-11-20", mode: "advisory", state: "none", summary: "", overlay: null, report: null, notes: [], checked_at: null })?.text).toContain(
      "trading as configured",
    );
    const suggested = overlayLine({
      session: "2026-11-20",
      mode: "advisory",
      state: "suggested",
      summary: "Fri Nov 20: no new grid buys",
      overlay: overlay({ pause: true, tier: 3 }),
      report: null,
      notes: [],
      checked_at: null,
    });
    expect(suggested?.text).toContain("suggested (advisory: not traded)");
    expect(suggested?.tone).toBe("stuck");
  });
});
