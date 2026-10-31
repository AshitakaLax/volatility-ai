import { describe, expect, it } from "vitest";

import {
  cellCount,
  composedNames,
  composedParams,
  initialState,
  lossCapable,
  matrixOf,
  paramText,
  setValue,
  toggle,
} from "@/lib/composition";
import type { Cell, Composition } from "@/types/backtest";

const composition: Composition = {
  buys: {
    hf_local_reference: {
      params: [
        { name: "per_lot_pct", type: "float", default: null, suggested: 0.0002, required: true },
        { name: "lookback_days", type: "float", default: null, suggested: 0.02, required: true },
      ],
    },
    fixed: { params: [{ name: "allocation_pct", type: "float", default: null, suggested: 0.05, required: true }] },
  },
  sells: {
    fixed_target: { label: "Fixed target", params: [] },
    scale_out: {
      label: "Scale out",
      params: [{ name: "rungs", type: "str", default: "0.5@0.01,0.5@0.03", suggested: "0.5@0.01,0.5@0.03" }],
      partial: true,
    },
    regime_exit: { label: "Regime exit", params: [], loss: true },
  },
};

describe("composition state", () => {
  it("starts as the champion with a fixed target", () => {
    const state = initialState(composition);
    expect(state.buys.map((p) => p.id)).toEqual(["hf_local_reference"]);
    expect(state.sells.map((p) => p.id)).toEqual(["fixed_target"]);
    expect(composedParams(state, composition)).toEqual({
      buy: { id: "hf_local_reference", params: { per_lot_pct: 0.0002, lookback_days: 0.02 } },
      sell: { id: "fixed_target", params: {} },
    });
  });

  it("sends a list per side once several are chosen: the matrix", () => {
    let state = initialState(composition);
    state = toggle(state, composition, "buy", "fixed");
    state = toggle(state, composition, "sell", "scale_out");
    state = toggle(state, composition, "sell", "regime_exit");
    expect(cellCount(state)).toBe(6);
    const params = composedParams(state, composition);
    expect(Array.isArray(params.buy) && params.buy.map((c) => c.id)).toEqual(["hf_local_reference", "fixed"]);
    expect(Array.isArray(params.sell) && params.sell.length).toBe(3);
  });

  it("keeps a policy's edits and parses them by type", () => {
    let state = toggle(initialState(composition), composition, "sell", "scale_out");
    state = setValue(state, "sell", "scale_out", "rungs", "0.3@0.01,0.7@0.04");
    state = setValue(state, "buy", "hf_local_reference", "per_lot_pct", "0.001");
    const params = composedParams(state, composition);
    expect(params.sell).toContainEqual({ id: "scale_out", params: { rungs: "0.3@0.01,0.7@0.04" } });
    expect(params.buy).toEqual({
      id: "hf_local_reference",
      params: { per_lot_pct: 0.001, lookback_days: 0.02 },
    });
  });

  it("names the chosen sells that may sell below cost", () => {
    const state = toggle(initialState(composition), composition, "sell", "regime_exit");
    expect(lossCapable(state, composition)).toEqual(["regime_exit"]);
  });
});

describe("reading a composed run", () => {
  const cell = (buy: string, sell: string, value: number): Cell =>
    ({
      grid: 0.01,
      target: 0.01,
      params: { buy: { id: buy, params: {} }, sell: { id: sell, params: { x: 1 } } },
      m: { net_yield_pct: value },
    }) as unknown as Cell;

  it("labels a component by its id and parameters", () => {
    expect(paramText({ id: "scale_out", params: { rungs: "a", b: 2 } })).toBe("scale_out(b=2, rungs=a)");
    expect(paramText({ id: "fixed_target" })).toBe("fixed_target");
    expect(paramText(0.5)).toBe("0.5");
  });

  it("finds the halves of a composed cell, and nothing in a plain one", () => {
    expect(composedNames(cell("a", "b", 1).params)).toEqual({ buy: "a", sell: "b" });
    expect(composedNames({ allocation_pct: 0.05 })).toBeNull();
  });

  it("lays the cells out buy x sell with each cell's best", () => {
    const cells = [cell("a", "x", 1), cell("a", "x", 3), cell("a", "y", 2), cell("b", "x", -1)];
    const { buys, sells, grid } = matrixOf(cells, (c) => c.m.net_yield_pct, composition);
    expect(buys).toEqual(["a", "b"]);
    expect(sells).toEqual(["x", "y"]);
    expect(grid.get("a|x")).toMatchObject({ value: 3, count: 2 });
    expect(grid.get("b|y")).toBeUndefined();
  });
});
