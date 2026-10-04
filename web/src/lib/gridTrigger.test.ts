import { describe, expect, it } from "vitest";

import type { Trigger } from "@/types/backtest";

import { GENERIC_TRIGGER, initialTriggerMethod, usesWindow } from "./gridTrigger";

const HF: Trigger = { methods: ["local_reference"], window: { param: "lookback_days" } };
const BAYES: Trigger = {
  methods: ["last_buy", "local_reference"],
  control: "lookback_days",
  window: { param: "lookback_days", seed: 0.03 },
};

describe("initialTriggerMethod", () => {
  it("a locked (single-method) descriptor pins methods[0]", () => {
    expect(initialTriggerMethod(HF, {})).toBe("local_reference");
    expect(initialTriggerMethod(GENERIC_TRIGGER, {})).toBe("last_buy");
    // even if a seeded value would otherwise suggest the other method
    expect(initialTriggerMethod({ ...HF }, { lookback_days: "" })).toBe("local_reference");
  });

  it("a choice descriptor defaults to methods[0] when the window param is blank", () => {
    expect(initialTriggerMethod(BAYES, {})).toBe("last_buy");
    expect(initialTriggerMethod(BAYES, { lookback_days: "" })).toBe("last_buy");
  });

  it("a choice descriptor preselects local_reference when the window param is already set", () => {
    expect(initialTriggerMethod(BAYES, { lookback_days: "0.03" })).toBe("local_reference");
  });
});

describe("GENERIC_TRIGGER", () => {
  it("is last_buy only, no window, no choice", () => {
    expect(GENERIC_TRIGGER).toEqual({ methods: ["last_buy"] });
  });
});

describe("usesWindow", () => {
  it("is true exactly for the methods measured from a rolling high", () => {
    expect(usesWindow("local_reference")).toBe(true);
    expect(usesWindow("regime_switched")).toBe(true);
    expect(usesWindow("last_buy")).toBe(false);
    expect(usesWindow("regime_widened")).toBe(false);
    expect(usesWindow("exposure_target")).toBe(false);
  });

  it("a locked regime_switched descriptor selects itself and keeps its window", () => {
    const ultimate: Trigger = { methods: ["regime_switched"], window: { param: "lookback_days" } };
    const method = initialTriggerMethod(ultimate, { lookback_days: "0.02" });
    expect(method).toBe("regime_switched");
    expect(usesWindow(method)).toBe(true);
  });
});
