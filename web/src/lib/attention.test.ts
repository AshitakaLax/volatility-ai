import { describe, expect, it } from "vitest";

import { attention, defaultDeployment, pageTitle } from "@/lib/attention";
import type { BridgeStatus, DeploymentSummary, TraderStatus } from "@/types/control";

const NOW = Date.parse("2026-11-14T16:00:00Z");

function status(state: TraderStatus["state"], stale = false): TraderStatus {
  return { state, detail: null, process: "supervisor", stale } as TraderStatus;
}

function bridge(ready: boolean): BridgeStatus {
  return {
    stale: false,
    session_open: false,
    next_open: "2026-11-16T14:30:00+00:00",
    attached: null,
    updated_at: new Date(NOW).toISOString(),
    readiness: {
      ready,
      blocking: ready ? null : "fidelity",
      summary: ready ? "ready" : "Fidelity is signed out",
      fix: ready ? null : "sign in to Fidelity in the browser with the extension",
      items: [{ id: "fidelity", label: "Fidelity tab", state: ready ? "ok" : "fail", detail: "", fix: null }],
    },
  } as unknown as BridgeStatus;
}

function deployment(over: Partial<DeploymentSummary>): DeploymentSummary {
  return {
    id: "d",
    label: "D",
    service: null,
    broker: "alpaca",
    error: null,
    paper: true,
    symbol: "TQQQ",
    controllable: true,
    ...over,
  };
}

const paper = deployment({ id: "paper", label: "Ultimate (paper)", status: status("closed") });
const idle = deployment({ id: "live", label: "Production", paper: false, status: status("not_running", true) });
const fidelity = (ready: boolean) =>
  deployment({
    id: "fidelity",
    label: "Fidelity (real money)",
    broker: "fidelity",
    paper: false,
    symbol: "RSP",
    status: status("closed"),
    bridge: bridge(ready),
  });

describe("what needs the reader", () => {
  it("is nothing when everything that runs is well", () => {
    expect(attention([paper, idle, fidelity(true)], NOW)).toEqual([]);
  });

  it("says a refused risk report, while it is recent, and never a missing one", () => {
    const refused = (finished_at: string) =>
      deployment({
        id: "paper",
        label: "Ultimate (paper)",
        status: status("closed"),
        risk_reports: {
          takes: true,
          why_not: null,
          settings: { mode: "advisory", mapping: "v1", levers: { daily: true, spacing: true, weekly: true } },
          last: {
            id: "abc",
            status: "rejected",
            detail: "the report does not pass the audit (1 problem(s)): symbol: missing",
            created_at: finished_at,
            finished_at,
            operator: "owner",
          },
        },
      });
    const [item] = attention([refused("2026-11-14T03:00:00Z")], NOW);
    expect(item?.title).toBe("Risk report refused");
    expect(item?.detail).toContain("symbol: missing");
    expect(attention([refused("2026-11-12T03:00:00Z")], NOW)).toEqual([]);
    const none = deployment({ id: "p", status: status("closed"), risk_reports: { takes: true, why_not: null, settings: null, last: null } });
    expect(attention([none], NOW)).toEqual([]);
  });

  it("names a Fidelity connection that cannot trade, with its fix", () => {
    const [item] = attention([paper, fidelity(false)], NOW);
    expect(item).toMatchObject({
      id: "fidelity",
      title: "Not ready: Fidelity tab",
      detail: "Fidelity is signed out",
      tone: "loss",
    });
    expect(item?.fix).toContain("sign in");
  });

  it("puts real money before paper, and skips what is not set up", () => {
    const halted = deployment({ id: "p2", label: "P2", status: status("trading"), ledger: { exists: true, halt: "position mismatch" } });
    const unset = deployment({ id: "new", label: "New", setup: "its config does not exist", error: "missing" });
    const found = attention([halted, unset, fidelity(false)], NOW);
    expect(found.map((item) => item.id)).toEqual(["fidelity", "p2"]);
    expect(found[1]).toMatchObject({ title: "Buys halted", detail: "position mismatch", tone: "stuck" });
  });

  it("flags a config that does not load", () => {
    const broken = deployment({ id: "x", label: "X", error: "live.step is required" });
    expect(attention([broken], NOW)[0]).toMatchObject({ title: "Config error", detail: "live.step is required" });
  });
});

describe("the deployment shown first", () => {
  it("is real money that something reports for", () => {
    expect(defaultDeployment([paper, idle, fidelity(true)])).toBe("fidelity");
  });

  it("else whatever reports, else the first listed", () => {
    expect(defaultDeployment([idle, paper])).toBe("paper");
    expect(defaultDeployment([idle])).toBe("live");
    expect(defaultDeployment([])).toBeNull();
  });
});

describe("the browser tab's title", () => {
  it("leads with what is wrong", () => {
    expect(pageTitle([paper, fidelity(false)], NOW)).toBe(
      "⚠ Not ready: Fidelity tab · Fidelity (real money) — volatility-ai",
    );
  });

  it("says how real money stands when nothing is", () => {
    expect(pageTitle([paper, fidelity(true)], NOW)).toMatch(/^Ready for .* · RSP — volatility-ai$/);
  });

  it("is the site's name with no real money reporting", () => {
    expect(pageTitle([paper, idle], NOW)).toBe("volatility-ai");
  });
});
