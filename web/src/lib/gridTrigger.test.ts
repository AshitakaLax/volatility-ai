import { describe, expect, it } from "vitest";

import type { GridTrigger } from "@/types/backtest";

import { GENERIC_GRID_TRIGGER, initialTriggerMethod } from "./gridTrigger";

const HF: GridTrigger = {
  methods: ["local_reference"],
  default: "local_reference",
  controlled_by: null,
  window_param: "lookback_days",
  window_default: null,
};
const BAYES: GridTrigger = {
  methods: ["last_buy", "local_reference"],
  default: "last_buy",
  controlled_by: "lookback_days",
  window_param: "lookback_days",
  window_default: 0.03,
};

describe("initialTriggerMethod", () => {
  it("a locked (single-method) descriptor pins methods[0]", () => {
    expect(initialTriggerMethod(HF, {})).toBe("local_reference");
    expect(initialTriggerMethod(GENERIC_GRID_TRIGGER, {})).toBe("last_buy");
    // even if a seeded value would otherwise suggest the other method
    expect(initialTriggerMethod({ ...HF }, { lookback_days: "" })).toBe("local_reference");
  });

  it("a choice descriptor defaults to its `default` when the window param is blank", () => {
    expect(initialTriggerMethod(BAYES, {})).toBe("last_buy");
    expect(initialTriggerMethod(BAYES, { lookback_days: "" })).toBe("last_buy");
  });

  it("a choice descriptor preselects local_reference when the window param is already set", () => {
    expect(initialTriggerMethod(BAYES, { lookback_days: "0.03" })).toBe("local_reference");
  });
});

describe("GENERIC_GRID_TRIGGER", () => {
  it("is last_buy only, no window, no choice", () => {
    expect(GENERIC_GRID_TRIGGER.methods).toEqual(["last_buy"]);
    expect(GENERIC_GRID_TRIGGER.window_param).toBeNull();
    expect(GENERIC_GRID_TRIGGER.controlled_by).toBeNull();
  });
});
