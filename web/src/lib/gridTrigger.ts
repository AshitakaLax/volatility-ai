/**
 * Picking the initial grid-step trigger method for a model.
 *
 * Pure so it is testable and so ParameterForm carries no per-model
 * `if`. "reload a saved report whose params seeded `lookback_days` ->
 * preselect local_reference" falls out of this.
 */
import type { Trigger, TriggerMethod } from "@/types/backtest";

export { GENERIC_TRIGGER } from "@/types/backtest";

/**
 * The method to select for a model given its trigger descriptor and the
 * seeded param text map. A locked (single-method) descriptor pins
 * `methods[0]`. Otherwise `local_reference` when the window param is
 * already non-blank, else the default -- `methods[0]`.
 */
/**
 * Whether a method's level is measured from a rolling high, so the form
 * shows (and requires) the descriptor's window param. regime_switched is
 * local_reference, over the same window, whenever its regime reads calm.
 */
export function usesWindow(method: TriggerMethod): boolean {
  return method === "local_reference" || method === "regime_switched";
}

export function initialTriggerMethod(
  trigger: Trigger,
  seeded: Record<string, string>,
): TriggerMethod {
  if (trigger.methods.length === 1) return trigger.methods[0]!;
  if (trigger.window && (seeded[trigger.window.param] ?? "").trim() !== "") {
    return "local_reference";
  }
  return trigger.methods[0]!;
}
