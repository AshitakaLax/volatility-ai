import { Input, Select } from "@/components/ui/primitives";
import type { GridStepResult, StepMode } from "@/lib/gridSteps";
import { cn } from "@/lib/utils";
import type { GridTrigger, GridTriggerMethod, ValidateError } from "@/types/backtest";

/**
 * The "Grid step" cluster: a Fixed | Sweep value control and, where the
 * sizing model has a choice, a trigger-method selector.
 *
 * Module-scope like ParamField so the typed inputs are not remounted on
 * every ParameterForm render (which would drop focus mid-keystroke).
 * Fully controlled -- it owns no state.
 */

const METHOD_LABEL: Record<GridTriggerMethod, string> = {
  last_buy: "Last buy price",
  local_reference: "Local reference (rolling high)",
};
const METHOD_HELP: Record<GridTriggerMethod, string> = {
  last_buy: "Buy when price falls one step below the last fill.",
  local_reference:
    "Buy on a step-sized pullback from max(last fill, N-day high) — re-fires on local dips, not only on a fresh low.",
};

interface Props {
  stepMode: StepMode;
  onStepModeChange: (mode: StepMode) => void;
  /** Fixed-mode single value (raw percent text). */
  gridStep: number;
  onGridStepChange: (value: number) => void;
  /** Sweep-mode inputs (raw text). */
  sweepMin: string;
  sweepMax: string;
  sweepCount: string;
  onSweepMinChange: (value: string) => void;
  onSweepMaxChange: (value: string) => void;
  onSweepCountChange: (value: string) => void;
  /** Resolved list + client errors for the current inputs. */
  gridSteps: GridStepResult;

  trigger: GridTrigger;
  /** The effective method (already resolved to methods[0] when locked). */
  method: GridTriggerMethod;
  onMethodChange: (method: GridTriggerMethod) => void;
  /** The rolling-high window value + its errors (only when the model
   * has a window_param and local_reference is active). */
  windowValue: string;
  onWindowChange: (value: string) => void;
  windowErrors: ValidateError[];

  disabled: boolean;
}

export function GridStepPanel({
  stepMode,
  onStepModeChange,
  gridStep,
  onGridStepChange,
  sweepMin,
  sweepMax,
  sweepCount,
  onSweepMinChange,
  onSweepMaxChange,
  onSweepCountChange,
  gridSteps,
  trigger,
  method,
  onMethodChange,
  windowValue,
  onWindowChange,
  windowErrors,
  disabled,
}: Props) {
  const locked = trigger.methods.length === 1;
  const showWindow = method === "local_reference" && trigger.window_param !== null;
  const pct = (fraction: number) => `${Number((fraction * 100).toFixed(4))}%`;

  return (
    <div className="flex flex-col gap-2">
      <div className="flex items-center gap-2">
        <span className="text-xs font-medium text-muted-foreground">Grid step</span>
        <div className="flex overflow-hidden rounded-md border border-border text-xs" data-testid="grid-step-mode">
          {(["fixed", "sweep"] as StepMode[]).map((mode) => (
            <button
              key={mode}
              type="button"
              disabled={disabled}
              onClick={() => onStepModeChange(mode)}
              className={cn(
                "px-2.5 py-1 transition-colors disabled:opacity-50",
                stepMode === mode
                  ? "bg-primary text-primary-foreground"
                  : "hover:bg-accent",
              )}
            >
              {mode === "fixed" ? "Fixed" : "Sweep"}
            </button>
          ))}
        </div>
      </div>

      {stepMode === "fixed" ? (
        <Input
          type="number"
          step="0.05"
          min="0.01"
          className="w-24"
          value={gridStep}
          disabled={disabled}
          onChange={(event) => onGridStepChange(Number(event.currentTarget.value))}
        />
      ) : (
        <div className="flex items-center gap-2">
          <Input
            type="number"
            step="0.05"
            placeholder="min %"
            className="w-20"
            value={sweepMin}
            disabled={disabled}
            onChange={(event) => onSweepMinChange(event.currentTarget.value)}
          />
          <span className="text-muted-foreground">–</span>
          <Input
            type="number"
            step="0.05"
            placeholder="max %"
            className="w-20"
            value={sweepMax}
            disabled={disabled}
            onChange={(event) => onSweepMaxChange(event.currentTarget.value)}
          />
          <Input
            type="number"
            step="1"
            min="1"
            max="12"
            placeholder="n"
            className="w-16"
            value={sweepCount}
            disabled={disabled}
            onChange={(event) => onSweepCountChange(event.currentTarget.value)}
          />
        </div>
      )}

      {stepMode === "sweep" && gridSteps.errors.length === 0 && gridSteps.steps.length > 0 ? (
        <p className="max-w-64 text-[11px] leading-tight text-muted-foreground">
          {gridSteps.steps.length} configuration{gridSteps.steps.length === 1 ? "" : "s"} —{" "}
          {gridSteps.steps.map(pct).join(", ")} · ~23s each
        </p>
      ) : null}
      {gridSteps.errors.map((error, index) => (
        <p key={index} className="text-[11px] leading-tight text-loss">
          {error}
        </p>
      ))}

      <Select
        data-testid="grid-trigger-method"
        className="w-44"
        value={method}
        disabled={disabled || locked}
        onChange={(event) => onMethodChange(event.currentTarget.value as GridTriggerMethod)}
      >
        {trigger.methods.map((option) => (
          <option key={option} value={option}>
            {METHOD_LABEL[option]}
          </option>
        ))}
      </Select>
      <p className="max-w-64 text-[11px] leading-tight text-muted-foreground">
        {METHOD_HELP[method]}
      </p>

      {showWindow ? (
        <div className="flex flex-col gap-1">
          <span className="text-[11px] font-medium text-muted-foreground">
            Reference window (days)
          </span>
          <Input
            type="number"
            step="any"
            min="0"
            className={cn("w-28", windowValue.trim() === "" && "border-loss")}
            value={windowValue}
            disabled={disabled}
            onChange={(event) => onWindowChange(event.currentTarget.value)}
          />
          {windowValue.trim() === "" ? (
            <span className="text-[11px] leading-tight text-loss">
              required for this trigger method
            </span>
          ) : null}
          {windowErrors.map((error, index) => (
            <span key={index} className="max-w-64 text-[11px] leading-tight text-loss">
              {error.message}
            </span>
          ))}
        </div>
      ) : null}
    </div>
  );
}
