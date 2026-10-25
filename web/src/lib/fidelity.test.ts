/**
 * The Fidelity connection as the Live page says it: one verdict, the chain
 * of links, and the bridge host's journal -- from what the bridge host
 * reports (fidelity_gateway/bridge/host.py).
 */
import { describe, expect, it } from "vitest";

import type {
  BridgeEvent,
  BridgeStatus,
  DeploymentSummary,
  ReadinessItem,
  TraderStatus,
} from "@/types/control";

import { ago, attachedWords, chain, duration, goneFor, sessionTime, timeline, verdict } from "./fidelity";

// Saturday 2026-10-24, 12:00 Eastern.
const NOW = Date.parse("2026-10-24T16:00:00Z");
const MONDAY_OPEN = "2026-10-26T13:30:00+00:00";

function iso(secondsAgo: number): string {
  return new Date(NOW - secondsAgo * 1000).toISOString();
}

function items(over: Partial<Record<ReadinessItem["id"], Partial<ReadinessItem>>> = {}) {
  const base: ReadinessItem[] = [
    { id: "bridge", label: "Bridge", state: "ok", detail: "listening on ws://0.0.0.0:8765", fix: null },
    { id: "extension", label: "Extension", state: "ok", detail: "connected", fix: null },
    { id: "version", label: "Extension version", state: "ok", detail: "0.6.0", fix: null },
    { id: "fidelity", label: "Fidelity tab", state: "ok", detail: "signed in", fix: null },
    { id: "trading", label: "Allow trading", state: "ok", detail: "on", fix: null },
    { id: "account", label: "Account check", state: "unknown", detail: "not checked", fix: null },
  ];
  return base.map((i) => ({ ...i, ...(over[i.id] ?? {}) }));
}

function bridge(over: Partial<BridgeStatus> = {}): BridgeStatus {
  const list = items();
  return {
    state: "listening",
    detail: "ready",
    listening: true,
    listen_error: null,
    mode: "live",
    deployment: "fidelity",
    symbol: "RSP",
    account_name: "Traditional IRA",
    max_order_value: 2000,
    connection: {
      connected: true,
      since: iso(3600),
      last_heard: iso(12),
      disconnected_at: null,
      client: "172.16.0.130",
      version: "0.6.0",
      versions: { minimum: "0.3.0", latest: "0.6.0" },
      advice: null,
      permissions: { preview: true, place: true },
      url: "ws://0.0.0.0:8765/fidelity-bridge",
      mode: null,
      account_name: null,
      max_order_value: null,
    },
    attached: null,
    readiness: { ready: true, blocking: null, summary: "ready", fix: null, items: list },
    last_check: null,
    session_open: false,
    next_open: MONDAY_OPEN,
    build: null,
    updated_at: iso(5),
    heartbeat_seconds: 15,
    stale: false,
    age_s: 5,
    ...over,
  };
}

function deployment(over: Partial<DeploymentSummary> = {}): DeploymentSummary {
  return {
    id: "fidelity",
    label: "Fidelity (real money)",
    service: "fidelity",
    broker: "fidelity",
    error: null,
    paper: false,
    bridge: bridge(),
    ...over,
  };
}

function trader(over: Partial<TraderStatus> = {}): TraderStatus {
  return {
    state: "waiting_for_open",
    detail: null,
    process: "supervisor",
    next_open: null,
    last_tick_at: null,
    open_lots: null,
    open_orders: null,
    algorithm: null,
    updated_at: iso(5),
    heartbeat_seconds: 15,
    account: null,
    stale: false,
    ...over,
  };
}

describe("the verdict", () => {
  it("says ready for the next open in Eastern time between sessions", () => {
    const v = verdict(deployment(), NOW);
    expect(v.label).toBe("Ready for Mon 09:30 ET");
    expect(v.tone).toBe("profit");
    expect(v.fix).toBeNull();
  });

  it("names the one thing to fix when not ready", () => {
    const blocked = bridge({
      readiness: {
        ready: false,
        blocking: "fidelity",
        summary: "Fidelity tab: Fidelity signed you out",
        fix: "sign in to Fidelity again in that browser",
        items: items({ fidelity: { state: "fail", detail: "Fidelity signed you out" } }),
      },
    });
    const v = verdict(deployment({ bridge: blocked }), NOW);
    expect(v.label).toBe("Not ready: Fidelity tab");
    expect(v.tone).toBe("loss");
    expect(v.detail).toContain("signed you out");
    expect(v.fix).toContain("sign in");
  });

  it("does not trust a bridge host that stopped reporting", () => {
    const v = verdict(deployment({ bridge: bridge({ stale: true, updated_at: iso(600) }) }), NOW);
    expect(v.label).toBe("Bridge host not reporting");
    expect(v.detail).toContain("10 min ago");
    expect(v.fix).toContain("fidelity-bridge");
  });

  it("says trading while the session's loop trades", () => {
    const v = verdict(
      deployment({ status: trader({ state: "trading", process: "loop" }) }),
      NOW,
    );
    expect(v.label).toBe("Connected · trading");
  });

  it("passes on a warning without calling it not ready", () => {
    const warned = bridge({
      readiness: {
        ready: true,
        blocking: null,
        summary: "ready",
        fix: null,
        items: items({ version: { state: "warn", detail: "0.5.0: build 0.6.0" } }),
      },
    });
    const v = verdict(deployment({ bridge: warned }), NOW);
    expect(v.tone).toBe("profit");
    expect(v.detail).toContain("0.5.0");
  });

  it("falls back to the trader's report without a bridge host", () => {
    const v = verdict(deployment({ bridge: null, status: trader({ stale: true }) }), NOW);
    expect(v.label).toBe("No report");
  });
});

describe("the chain", () => {
  it("runs from the bridge to the account, with a trader step between", () => {
    const steps = chain(bridge(), NOW);
    expect(steps.map((s) => s.id)).toEqual([
      "bridge",
      "extension",
      "fidelity",
      "trading",
      "trader",
      "account",
    ]);
    const extension = steps[1]!;
    expect(extension.detail).toBe("from 172.16.0.130 · v0.6.0 · last heard 12 s ago");
    expect(steps[4]!).toMatchObject({ state: "unknown", detail: "none until Mon 09:30 ET" });
  });

  it("counts the extension's last ping from now, not from the report", () => {
    expect(chain(bridge(), NOW + 30_000)[1]!.detail).toContain("last heard 42 s ago");
  });

  it("folds an old extension's warning into its step", () => {
    const warned = bridge({
      readiness: {
        ready: true,
        blocking: null,
        summary: "ready",
        fix: null,
        items: items({ version: { state: "warn", detail: "0.5.0: an update is waiting" } }),
      },
    });
    const extension = chain(warned, NOW)[1]!;
    expect(extension.state).toBe("warn");
    expect(extension.detail).toContain("an update is waiting");
  });

  it("names the attached trader, and warns of a session with none", () => {
    const attached = chain(
      bridge({
        session_open: true,
        attached: {
          process: "loop",
          pid: 4117,
          deployment: "fidelity",
          build: null,
          since: iso(120),
          status: null,
        },
      }),
      NOW,
    )[4]!;
    expect(attached).toMatchObject({
      state: "ok",
      detail: "the trading loop (pid 4117) since 2 min ago",
    });
    expect(chain(bridge({ session_open: true }), NOW)[4]!.state).toBe("warn");
  });
});

describe("the timeline", () => {
  it("is newest first and says how long a disconnect lasted", () => {
    const t0 = NOW / 1000;
    const events: BridgeEvent[] = [
      { t: t0 - 600, kind: "connected", detail: "The extension connected." },
      { t: t0 - 300, kind: "disconnected", detail: "The extension disconnected." },
      { t: t0 - 60, kind: "connected", detail: "The extension connected." },
      { t: t0 - 30, kind: "fidelity", detail: "Fidelity signed you out.", state: "signed_out" },
    ];
    const rows = timeline(events);
    expect(rows.map((r) => r.kind)).toEqual(["fidelity", "connected", "disconnected", "connected"]);
    expect(rows[0]!.tone).toBe("loss");
    expect(rows[1]!.span).toBe("back after 4 min");
    expect(rows[3]!.span).toBeNull();
  });

  it("colours the trading switch and checks by what they said", () => {
    const rows = timeline([
      { t: 1, kind: "trading", detail: "off", on: false },
      { t: 2, kind: "check", detail: "passed", ok: true },
    ]);
    expect(rows.map((r) => r.tone)).toEqual(["profit", "stuck"]);
  });
});

describe("words", () => {
  it("durations read like a person says them", () => {
    expect(duration(45)).toBe("45 s");
    expect(duration(600)).toBe("10 min");
    expect(duration(2 * 3600 + 5 * 60)).toBe("2 h 5 min");
    expect(duration(3 * 86400 + 4 * 3600)).toBe("3 d 4 h");
  });

  it("times are the market's own", () => {
    expect(sessionTime(MONDAY_OPEN, NOW)).toBe("Mon 09:30 ET");
    expect(sessionTime("2026-10-24T20:00:00Z", NOW)).toBe("16:00 ET");
    expect(ago(iso(90 * 60), NOW)).toBe("1 h 30 min ago");
    expect(ago(null, NOW)).toBe("never");
  });

  it("a disconnect's length is counted for the banner", () => {
    const gone = bridge({
      connection: { ...bridge().connection, connected: false, disconnected_at: iso(240) },
    });
    expect(goneFor(gone, NOW)).toBe("4 min");
    expect(goneFor(bridge(), NOW)).toBeNull();
    expect(attachedWords({ process: "check", pid: null })).toBe("a connection check");
  });
});
