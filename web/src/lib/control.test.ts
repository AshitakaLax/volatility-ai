/**
 * Which commands the Live page offers a deployment, and when it asks for
 * the id typed back -- the same rules server/live_control.py enforces.
 */
import { describe, expect, it } from "vitest";

import type { DeploymentSummary } from "@/types/control";

import {
  actions,
  algorithmLabel,
  algorithmName,
  algorithmOrigin,
  byBroker,
  chip,
  commandLabel,
  defaultTiming,
  diffAlgorithms,
  fidelityChip,
  gridWords,
  nowLine,
  position,
  regimeLine,
  sameCode,
  shadowLine,
  sharedAccounts,
  sourceLabel,
  statusTone,
  tradeTotals,
  typedReason,
} from "./control";

function deployment(over: Partial<DeploymentSummary> = {}): DeploymentSummary {
  return {
    id: "paper-ultimate",
    label: "Ultimate (paper)",
    service: "paper-ultimate",
    broker: "alpaca",
    error: null,
    paper: true,
    symbol: "TQQQ",
    strategy_id: "ultimate",
    step: 0.00075,
    profit_target: 0.3,
    controllable: true,
    caps: {
      pause_buys: true,
      resume_buys: true,
      enable_disable: true,
      algorithm_changes: true,
      profiles_only: false,
      ledger_reset: true,
    },
    status: {
      state: "trading",
      detail: null,
      process: "loop",
      next_open: null,
      last_tick_at: null,
      open_lots: 0,
      open_orders: 0,
      algorithm: null,
      updated_at: null,
      heartbeat_seconds: 60,
      account: "aaaaaaaaaaaa",
      stale: false,
    },
    desired: { enabled: true, wind_down: false, by: null, reason: null, at: null },
    ledger: { exists: true, halt: null, open_lots: 0, cash: 1000 },
    pending: 0,
    ...over,
  };
}

const ids = (d: DeploymentSummary) => actions(d).map((a) => a.id);

describe("the state chip", () => {
  it("is the trader's own report", () => {
    expect(chip(deployment())).toMatchObject({ label: "Trading", tone: "profit" });
  });

  it("names the service to start when nothing is running", () => {
    const d = deployment({
      status: { ...deployment().status!, state: "not_running", detail: "last report 9 min ago" },
    });
    expect(chip(d).label).toBe("Not running");
    expect(chip(d).detail).toContain("docker compose up -d paper-ultimate");
  });

  it("says when a config does not load", () => {
    expect(chip(deployment({ error: "bad yaml" }))).toMatchObject({ label: "Config error" });
  });
});

describe("what is offered", () => {
  it("pause, wind down and disable while trading", () => {
    expect(ids(deployment())).toEqual(["pause", "wind_down", "disable_now", "reset_ledger"]);
  });

  it("resume instead of pause once halted", () => {
    expect(ids(deployment({ ledger: { exists: true, halt: "paused by op" } }))[0]).toBe("resume");
  });

  it("enable once disabled, or to cancel a wind-down", () => {
    const disabled = deployment({
      desired: { enabled: false, wind_down: false, by: "op", reason: "x", at: null },
    });
    expect(ids(disabled)).toEqual(["pause", "enable", "reset_ledger"]);
    const winding = deployment({
      desired: { enabled: true, wind_down: true, by: "op", reason: "x", at: null },
    });
    expect(actions(winding).find((a) => a.id === "enable")?.label).toBe("Cancel wind-down");
  });

  it("says why a command the config does not grant is unavailable", () => {
    const d = deployment({ caps: { ...deployment().caps!, enable_disable: false } });
    const disable = actions(d).find((a) => a.id === "disable_now");
    expect(disable?.blocked).toBe("its config does not grant live.control.enable_disable");
    expect(actions(d).find((a) => a.id === "pause")?.blocked).toBeNull();
  });

  it("offers nothing without a control directory", () => {
    expect(actions(deployment({ controllable: false }))).toEqual([]);
  });
});

describe("typed confirmation", () => {
  it("is needed to disable with lots open, and says how many", () => {
    const d = deployment({ ledger: { exists: true, halt: null, open_lots: 3 } });
    expect(typedReason(d, "disable", { mode: "now" })).toBe(
      "3 open lots would get no exits while disabled",
    );
    expect(typedReason(d, "disable", { mode: "wind_down" })).toBeNull();
  });

  it("is needed for everything but a pause on real money", () => {
    const money = deployment({ paper: false });
    expect(typedReason(money, "pause_buys")).toBeNull();
    expect(typedReason(money, "resume_buys")).toBe("this deployment trades real money");
    expect(typedReason(money, "enable")).toBe("this deployment trades real money");
  });

  it("is not needed for ordinary paper commands", () => {
    expect(typedReason(deployment(), "pause_buys")).toBeNull();
    expect(typedReason(deployment(), "disable", { mode: "now" })).toBeNull();
  });
});

describe("the command log", () => {
  it("labels a command by what it did", () => {
    expect(commandLabel({ type: "disable", args: { mode: "wind_down" } })).toBe("Wind down");
    expect(commandLabel({ type: "disable", args: {} })).toBe("Disable now");
    expect(commandLabel({ type: "resume_buys", args: { reset_drawdown_baseline: true } })).toBe(
      "Resume buys (drawdown baseline reset)",
    );
  });

  it("colours outcomes", () => {
    expect(statusTone("applied")).toBe("profit");
    expect(statusTone("rejected")).toBe("loss");
    expect(statusTone("queued")).toBe("stuck");
    expect(statusTone("cancelled")).toBe("neutral");
  });
});

describe("the algorithm panel", () => {
  const ultimate = {
    strategy_id: "ultimate",
    strategy_params: { per_lot_pct: 0.0002, bear_dd: 0.5 },
    step: 0.00075,
    profit_target: 0.3,
  };
  const champion = {
    strategy_id: "hf_local_reference",
    strategy_params: { per_lot_pct: 0.0003 },
    step: 0.00075,
    profit_target: 0.003,
  };

  it("labels an algorithm in percent", () => {
    expect(algorithmLabel(ultimate)).toBe("ultimate · step 0.075% · target 30%");
  });

  it("diffs what a switch changes", () => {
    expect(diffAlgorithms(ultimate, champion)).toEqual([
      { field: "strategy", from: "ultimate", to: "hf_local_reference" },
      { field: "profit target", from: "30%", to: "0.3%" },
      { field: "bear_dd", from: "0.5", to: "--" },
      { field: "per_lot_pct", from: "0.0002", to: "0.0003" },
    ]);
    expect(diffAlgorithms(ultimate, ultimate)).toEqual([]);
  });

  it("waits for the next session when a signal exit is involved", () => {
    const impact = {
      open_lots: 3,
      cost: 100,
      lots_at_new_target: 0,
      signal_exit_before: true,
      signal_exit_after: false,
      notes: [],
    };
    expect(defaultTiming(impact)).toBe("next_session");
    expect(defaultTiming({ ...impact, signal_exit_before: false })).toBe("now");
    expect(defaultTiming(undefined)).toBe("now");
  });

  it("says where the algorithm in force came from", () => {
    expect(sourceLabel({ source: "config", override: null })).toBe("the config file");
    expect(
      sourceLabel({
        source: "web",
        override: {
          channel: "web",
          changedAt: null,
          changedBy: "levi",
          reason: "x",
          profile: "champion-hf-tqqq",
        },
      }),
    ).toBe("the Live page by levi (profile champion-hf-tqqq)");
  });
});

describe("phase 3", () => {
  it("offers a fresh paper ledger only once disabled, typed back", () => {
    const enabled = actions(deployment()).find((a) => a.id === "reset_ledger");
    expect(enabled?.blocked).toBe("disable it first");
    const disabled = actions(
      deployment({ desired: { enabled: false, wind_down: false, by: null, reason: null, at: null } }),
    ).find((a) => a.id === "reset_ledger");
    expect(disabled?.blocked).toBeNull();
    expect(disabled?.typed).toBe("the ledger it has is archived and a fresh one started");
    expect(actions(deployment({ paper: false })).some((a) => a.id === "reset_ledger")).toBe(false);
  });

  it("names deployments that trade one account together", () => {
    const a = deployment({ id: "a", label: "A" });
    const b = deployment({ id: "b", label: "B" });
    const c = deployment({
      id: "c",
      label: "C",
      status: { ...deployment().status!, account: "bbbbbbbbbbbb" },
    });
    expect(sharedAccounts([a, b, c])).toEqual({ a: ["B"], b: ["A"] });
    const stale = deployment({ id: "b", status: { ...deployment().status!, stale: true } });
    expect(sharedAccounts([a, stale])).toEqual({});
  });
});

/* ------------------------------------------------------------------ */
/* Reading a deployment                                                */
/* ------------------------------------------------------------------ */

const TURBULENT = {
  ultimate_mode: "turbulent",
  ultimate_exit_active: true,
  ultimate_reversal_tagged: 1,
  regime_since: "2026-10-19",
  regime_natr: 4.97,
  regime_median: 4.73,
  regime_reading: "turbulent",
  regime_earliest_change: "2026-10-26",
};

function trading(now: Partial<NonNullable<DeploymentSummary["status"]>> = {}) {
  return deployment({ status: { ...deployment().status!, ...now } });
}

describe("the venues", () => {
  it("groups by broker, Alpaca first, and keeps an empty Fidelity section", () => {
    const sections = byBroker([deployment(), deployment({ id: "live", broker: "alpaca" })]);
    expect(sections.map((s) => s.broker)).toEqual(["alpaca", "fidelity"]);
    expect(sections[0]?.deployments).toHaveLength(2);
    expect(sections[1]?.deployments).toEqual([]);
  });

  it("puts a Fidelity deployment in its own section", () => {
    const sections = byBroker([deployment(), deployment({ id: "fidelity", broker: "fidelity" })]);
    expect(sections[1]?.deployments.map((d) => d.id)).toEqual(["fidelity"]);
  });
});

describe("the algorithm in force", () => {
  const inForce = {
    strategy_id: "hf_local_reference",
    strategy_params: {},
    step: 0.00075,
    profit_target: 0.003,
    source: "web" as const,
    profile: "champion-hf-tqqq",
    label: "Champion grid (hf_local_reference), TQQQ",
    changed_by: "ashitakalax",
    changed_at: "2026-10-20T15:55:12+00:00",
    reason: "Ultimate is turbulent",
    reported: true,
    config_file: { strategy_id: "ultimate", strategy_params: {}, step: 0.00075, profit_target: 0.3 },
  };

  it("is named by its profile, and its grid in words", () => {
    expect(algorithmName(inForce)).toBe("Champion grid (hf_local_reference), TQQQ");
    expect(algorithmName({ ...inForce, label: null })).toBe("hf_local_reference");
    expect(gridWords(0.00075, 0.003)).toBe("buys each 0.075% dip, sells each lot at +0.3%");
  });

  it("says who switched it", () => {
    expect(algorithmOrigin(inForce)).toBe("switched on the Live page by ashitakalax");
    expect(algorithmOrigin({ ...inForce, source: "config" })).toBe("the config file's algorithm");
  });
});

describe("what it is doing now", () => {
  const now = { price: 70, buy_level: 69.93, reference: 70, blocked: null, strategy: null };

  it("names the next buy's price", () => {
    const line = nowLine(trading({ now }));
    expect(line?.text).toBe("Next buy at or below $69.93 (0.10% under $70.00).");
    expect(line?.tone).toBe("profit");
  });

  it("says what blocks a buy", () => {
    const line = nowLine(
      trading({ now: { ...now, buy_level: null, blocked: "the strategy buys at no price right now" } }),
    );
    expect(line?.text).toBe("Not buying: the strategy buys at no price right now.");
  });

  it("puts an unreachable broker first", () => {
    const line = nowLine(trading({ now, broker_unavailable: "signed out of Fidelity" }));
    expect(line?.text).toContain("signed out of Fidelity");
  });

  it("says nothing between sessions", () => {
    expect(nowLine(trading({ now, process: "supervisor" }))).toBeNull();
  });

  it("explains Ultimate's regime", () => {
    expect(regimeLine(TURBULENT)).toBe(
      "Turbulent since Mon, Oct 19 (volatility 4.97 against its median 4.73 at the last close): " +
        "no grid buys, only a reversal lot on a deep down day; it can change Mon, Oct 26 at the " +
        "earliest.",
    );
    expect(regimeLine({ entry_suppressed: false })).toBeNull();
  });
});

describe("switching back", () => {
  const algorithm = {
    strategy_id: "hf_local_reference",
    strategy_params: {},
    step: 0.00075,
    profit_target: 0.003,
    source: "web" as const,
    profile: "champion-hf-tqqq",
    label: null,
    changed_by: null,
    changed_at: null,
    reason: null,
    reported: true,
    config_file: { strategy_id: "ultimate", strategy_params: {}, step: 0.00075, profit_target: 0.3 },
  };

  it("warns that an active regime exit would sell the open lots", () => {
    const d = deployment({
      algorithm,
      status: {
        ...deployment().status!,
        open_lots: 37,
        shadow: { strategy: TURBULENT, would_sell: 0, would_sell_cost: 0 },
      },
    });
    const line = shadowLine(d);
    expect(line?.tone).toBe("loss");
    expect(line?.text).toContain("would sell 36 open lots at market");
  });

  it("says when it would sell nothing", () => {
    const d = deployment({
      algorithm,
      status: {
        ...deployment().status!,
        shadow: { strategy: { ultimate_mode: "calm" }, would_sell: 0, would_sell_cost: 0 },
      },
    });
    expect(shadowLine(d)?.text).toContain("would sell nothing");
  });

  it("says nothing while the config file's algorithm trades", () => {
    expect(shadowLine(deployment())).toBeNull();
  });
});

describe("the book and the day's trades", () => {
  it("values the open lots at the last mark", () => {
    const lot = { id: "a", symbol: "TQQQ", px: 50, qty: 2, target: 0.01, target_px: 50.5, to_target: null, vs_mark: null };
    const book = position({ lots: [lot, { ...lot, id: "b", px: 60 }], last_px: 55 } as never);
    expect(book).toMatchObject({ lots: 2, shares: 4, cost: 220, value: 220, unrealized: 0, average: 55 });
  });

  it("totals buys, sales and what the sales realised", () => {
    const totals = tradeTotals([
      { t: 1, side: "buy", lot: "a", qty: 1, price: 70, value: 70 },
      { t: 2, side: "sell", lot: "a", qty: 1, price: 70.21, pnl: 0.21 },
      { t: 3, side: "sell", lot: "b", qty: 1, price: 69, pnl: -1 },
    ]);
    expect(totals).toEqual({ buys: 1, sells: 2, bought: 70, realized: -0.79 });
  });
});

describe("the Fidelity connection", () => {
  const connected = {
    connected: true,
    since: null,
    last_heard: null,
    disconnected_at: null,
    client: "172.16.0.20",
    version: "1.4.0",
    versions: {},
    advice: null,
    permissions: { preview: true, place: true },
    url: null,
    mode: "live" as const,
    account_name: "Traditional IRA",
    max_order_value: 500,
  };

  it("reads connected and trading", () => {
    expect(fidelityChip(connected, true).label).toBe("Connected · trading allowed");
  });

  it("says when the extension is gone, or trading is off", () => {
    expect(fidelityChip({ ...connected, connected: false }, true).label).toBe(
      "Extension disconnected",
    );
    expect(
      fidelityChip({ ...connected, permissions: { preview: true, place: false } }, true).label,
    ).toBe("Trading switched off");
  });

  it("says nothing is reporting when the engine is not running", () => {
    expect(fidelityChip(connected, false).label).toBe("No report");
  });
});

describe("which code a trader runs", () => {
  it("compares fingerprints, and admits when it cannot", () => {
    const build = { commit: null, code: "abc", python: "3.12", pid: 1, started_at: "" };
    expect(sameCode(build, "abc")).toBe(true);
    expect(sameCode(build, "def")).toBe(false);
    expect(sameCode({ ...build, code: null }, "abc")).toBeNull();
  });
});
