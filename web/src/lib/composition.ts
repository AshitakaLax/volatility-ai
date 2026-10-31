/**
 * The composed model's helpers (research/composition/ on the server): a buy
 * and a sell policy chosen independently -- several of each submit the buy x
 * sell MATRIX as one run, since the server sweeps a list of components
 * (engine/core/config.expand_strategy_params).
 *
 * Pure, like lib/strategyParams.ts; covered by composition.test.ts.
 */
import { buildStrategyParams, paramSpec, seedValues } from "@/lib/strategyParams";
import type {
  Cell,
  ComponentValue,
  Composition,
  Param,
  ParamSpec,
  ParamValue,
  SellPolicy,
} from "@/types/backtest";

export const COMPOSED_MODEL = "composed";

export type Side = "buy" | "sell";

/** One chosen policy and its fields' raw text (as the rest of the form keeps it). */
export interface ChosenPolicy {
  id: string;
  values: Record<string, string>;
}

export interface CompositionState {
  buys: ChosenPolicy[];
  sells: ChosenPolicy[];
}

/** The champion buying and the grid's own fixed target selling: the server's
 * committed default for `composed`, and the champion exactly. */
export const DEFAULT_BUY = "hf_local_reference";
export const DEFAULT_SELL = "fixed_target";

export function isComponent(value: unknown): value is ComponentValue {
  return (
    typeof value === "object" &&
    value !== null &&
    !Array.isArray(value) &&
    typeof (value as { id?: unknown }).id === "string"
  );
}

/** A parameter value as text: a component reads `id(k=v, ...)`. */
export function paramText(value: ParamValue | null | undefined): string {
  if (value === null || value === undefined) return "";
  if (isComponent(value)) {
    const entries = Object.entries(value.params ?? {}).sort(([a], [b]) => a.localeCompare(b));
    return entries.length === 0
      ? value.id
      : `${value.id}(${entries.map(([k, v]) => `${k}=${String(v)}`).join(", ")})`;
  }
  return String(value);
}

/** The buy and sell policy ids of a composed cell's params, or null. */
export function composedNames(params: Cell["params"] | undefined): { buy: string; sell: string } | null {
  const buy = params?.buy;
  const sell = params?.sell;
  return isComponent(buy) && isComponent(sell) ? { buy: buy.id, sell: sell.id } : null;
}

export function specsFor(composition: Composition | undefined, side: Side, id: string): ParamSpec[] {
  const params: Param[] =
    (side === "buy" ? composition?.buys[id]?.params : composition?.sells[id]?.params) ?? [];
  return params.map(paramSpec);
}

export function choose(composition: Composition | undefined, side: Side, id: string): ChosenPolicy {
  return { id, values: seedValues(specsFor(composition, side, id)) };
}

export function initialState(composition: Composition | undefined): CompositionState {
  return {
    buys: composition?.buys[DEFAULT_BUY] ? [choose(composition, "buy", DEFAULT_BUY)] : [],
    sells: composition?.sells[DEFAULT_SELL] ? [choose(composition, "sell", DEFAULT_SELL)] : [],
  };
}

/** Add or remove a policy, keeping the others' edits. `single` (a live
 * deployment trades one pairing, not a matrix): choosing one replaces the
 * side's choice, and the last one cannot be removed. */
export function toggle(
  state: CompositionState,
  composition: Composition | undefined,
  side: Side,
  id: string,
  single = false,
): CompositionState {
  const key = side === "buy" ? "buys" : "sells";
  const chosen = state[key];
  const on = chosen.some((policy) => policy.id === id);
  if (single) {
    return on ? state : { ...state, [key]: [choose(composition, side, id)] };
  }
  const next = on ? chosen.filter((policy) => policy.id !== id) : [...chosen, choose(composition, side, id)];
  return { ...state, [key]: next };
}

/** The editor's state for a composed algorithm already in force: each side's
 * policy, its fields seeded from the catalogue and overlaid with what is
 * traded. Anything else (not composed, or an unknown policy) starts from the
 * defaults. */
export function stateFrom(
  params: Record<string, ParamValue> | undefined,
  composition: Composition | undefined,
): CompositionState {
  const pick = (side: Side, raw: ParamValue | undefined): ChosenPolicy | null => {
    if (!isComponent(raw)) return null;
    const known = side === "buy" ? composition?.buys[raw.id] : composition?.sells[raw.id];
    if (!known) return null;
    const base = choose(composition, side, raw.id);
    const overlay: Record<string, string> = {};
    for (const [name, value] of Object.entries(raw.params ?? {})) {
      if (value !== null && value !== undefined) overlay[name] = String(value);
    }
    return { id: raw.id, values: { ...base.values, ...overlay } };
  };
  const fallback = initialState(composition);
  const buy = pick("buy", params?.buy);
  const sell = pick("sell", params?.sell);
  return { buys: buy ? [buy] : fallback.buys, sells: sell ? [sell] : fallback.sells };
}

export function setValue(
  state: CompositionState,
  side: Side,
  id: string,
  name: string,
  value: string,
): CompositionState {
  const key = side === "buy" ? "buys" : "sells";
  return {
    ...state,
    [key]: state[key].map((policy) =>
      policy.id === id ? { ...policy, values: { ...policy.values, [name]: value } } : policy,
    ),
  };
}

function component(composition: Composition | undefined, side: Side, policy: ChosenPolicy): ComponentValue {
  const params = buildStrategyParams(specsFor(composition, side, policy.id), policy.values);
  // Components carry single values: a policy's own parameter sweep is a
  // matrix config's job (config/matrix/), not this form's.
  const flat: Record<string, number | string | boolean> = {};
  for (const [name, value] of Object.entries(params)) {
    if (!Array.isArray(value) && !isComponent(value)) flat[name] = value;
  }
  return { id: policy.id, params: flat };
}

/** strategy_params for the composed model: one component per side, or a
 * list of them -- the server sweeps the lists, buy x sell. */
export function composedParams(
  state: CompositionState,
  composition: Composition | undefined,
): Record<string, ComponentValue | ComponentValue[]> {
  const side = (which: Side, chosen: ChosenPolicy[]) => {
    const components = chosen.map((policy) => component(composition, which, policy));
    return components.length === 1 ? components[0]! : components;
  };
  return { buy: side("buy", state.buys), sell: side("sell", state.sells) };
}

/** How many buy x sell cells the choice is. */
export function cellCount(state: CompositionState): number {
  return state.buys.length * state.sells.length;
}

/** The chosen sell policies that may sell below cost. */
export function lossCapable(state: CompositionState, composition: Composition | undefined): string[] {
  return state.sells
    .map((policy) => policy.id)
    .filter((id) => (composition?.sells[id] as SellPolicy | undefined)?.loss);
}

export interface MatrixCell {
  buy: string;
  sell: string;
  value: number | null;
  /** How many configurations of the run land in this cell. */
  count: number;
  loss: boolean;
}

/**
 * A composed run's cells as a buy x sell grid: per (buy, sell), the BEST
 * value of `metric` across its configurations (grid steps, targets) --
 * the highest, or the lowest for a metric where lower is better.
 */
export function matrixOf(
  cells: Cell[],
  metric: (cell: Cell) => number | null | undefined,
  composition?: Composition,
  higherIsBetter = true,
): { buys: string[]; sells: string[]; grid: Map<string, MatrixCell> } {
  const grid = new Map<string, MatrixCell>();
  const buys: string[] = [];
  const sells: string[] = [];
  for (const cell of cells) {
    const names = composedNames(cell.params);
    if (!names) continue;
    if (!buys.includes(names.buy)) buys.push(names.buy);
    if (!sells.includes(names.sell)) sells.push(names.sell);
    const key = `${names.buy}|${names.sell}`;
    const value = metric(cell);
    const current = grid.get(key);
    const better =
      value !== null && value !== undefined && Number.isFinite(value)
        ? current?.value === null ||
          current?.value === undefined ||
          (higherIsBetter ? value > current.value : value < current.value)
        : false;
    grid.set(key, {
      buy: names.buy,
      sell: names.sell,
      value: better ? value! : (current?.value ?? null),
      count: (current?.count ?? 0) + 1,
      loss: Boolean(composition?.sells[names.sell]?.loss),
    });
  }
  return { buys, sells, grid };
}
