/**
 * A backtest configuration proposed as a live profile: the id the loader
 * accepts, and strings that cannot break the document.
 */
import { describe, expect, it } from "vitest";

import type { Cell, Report } from "@/types/backtest";

import { profileId, profileYaml } from "./profileYaml";

const cell = {
  grid: 0.00075,
  target: 0.003,
  params: { per_lot_pct: 0.0003, vol_measure: "stdev", dd_throttle_start: false },
  m: { net_yield_pct: 230.7, cagr_pct: 11.9, max_drawdown_pct: 37.9, return_over_drawdown: 6.08 },
} as unknown as Cell;

const report = {
  id: "edd1a30961fc",
  name: 'RSP brute force: "best"',
  model: "hf_local_reference",
  funds: { RSP: { bars: { start: "2016-01-04", end: "2026-10-08", count: 1 } } },
} as unknown as Report;

describe("a profile proposal", () => {
  it("takes an id the loader accepts", () => {
    expect(profileId("hf_local_reference", "RSP")).toBe("hf-local-reference-rsp");
    expect(profileId("ultimate", "URSP_SIM")).toBe("ultimate-ursp-sim");
  });

  it("is the four algorithm fields with the run as evidence", () => {
    const text = profileYaml(report, "RSP", cell);
    expect(text).toContain("id: hf-local-reference-rsp\n");
    expect(text).toContain('symbols: ["RSP"]\n');
    expect(text).toContain('strategy_id: "hf_local_reference"\n');
    expect(text).toContain("  per_lot_pct: 0.0003\n");
    expect(text).toContain('  vol_measure: "stdev"\n');
    expect(text).toContain("  dd_throttle_start: false\n");
    expect(text).toContain("step: 0.00075\nprofit_target: 0.003\n");
    expect(text).toContain('    run: "edd1a30961fc"\n');
    expect(text).toContain("    return_over_drawdown: 6.08\n");
  });

  it("quotes a name that would otherwise break the YAML", () => {
    expect(profileYaml(report, "RSP", cell)).toContain(
      '    name: "RSP brute force: \\"best\\""\n',
    );
  });
});
