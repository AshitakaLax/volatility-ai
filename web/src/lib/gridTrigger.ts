/**
 * Picking the initial grid-step trigger method for a model.
 *
 * Pure so it is testable and so ParameterForm carries no per-model
 * `if`. "reload a saved report whose params seeded `lookback_days` ->
 * preselect local_reference" falls out of this.
 */
import type { GridTrigger, GridTriggerMethod } from "@/types/backtest";

export { GENERIC_GRID_TRIGGER } from "@/types/backtest";

/**
 * The method to select for a model given its trigger descriptor and the
 * seeded param text map. A locked (single-method) descriptor pins
 * `methods[0]`. Otherwise `local_reference` when the window param is
 * already non-blank, else the descriptor's default.
 */
export function initialTriggerMethod(
  trigger: GridTrigger,
  seeded: Record<string, string>,
): GridTriggerMethod {
  if (trigger.methods.length === 1) return trigger.methods[0]!;
  if (trigger.window_param && (seeded[trigger.window_param] ?? "").trim() !== "") {
    return "local_reference";
  }
  return trigger.default;
}
