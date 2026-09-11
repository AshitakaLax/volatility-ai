import { ParamField } from "@/components/backtest/ParamField";
import { SweepControls } from "@/components/backtest/SweepControls";
import { Checkbox } from "@/components/ui/primitives";
import type { SweepFieldState } from "@/lib/sweepStrategies";
import type { ParamSpec, ValidateError } from "@/types/backtest";

/**
 * A sweepable strategy param (`spec.sweepable`): an "enable sweep"
 * checkbox above the field, exactly like GridStepPanel's own. Unchecked
 * renders the ordinary scalar ParamField unmodified; checked replaces it
 * with the shared Sweep Strategy dropdown + range inputs.
 *
 * Module-scope, same reasoning as ParamField/GridStepPanel: redefined
 * inside ParameterForm on every render, it would remount and drop focus
 * mid-keystroke.
 */

interface Props {
  spec: ParamSpec;
  /** Scalar text, used only while the sweep is off. */
  value: string;
  onChange: (name: string, value: string) => void;
  onReset: (name: string) => void;
  sweep: SweepFieldState;
  onSweepChange: (name: string, next: SweepFieldState) => void;
  /** Already filtered to this field (scalar errors when off, sweep-range
   * errors when on -- both are pinned to the same field name). */
  errors: ValidateError[];
  disabled: boolean;
}

export function SweepableParamField({
  spec,
  value,
  onChange,
  onReset,
  sweep,
  onSweepChange,
  errors,
  disabled,
}: Props) {
  return (
    <div className="flex flex-col gap-1.5">
      <label className="flex w-fit items-center gap-1.5 text-[11px] text-muted-foreground">
        <Checkbox
          checked={sweep.enabled}
          disabled={disabled}
          onChange={(event) =>
            onSweepChange(spec.name, { ...sweep, enabled: event.currentTarget.checked })
          }
        />
        Sweep
      </label>

      {sweep.enabled ? (
        <div className="flex flex-col gap-1.5">
          <span className="text-xs font-medium text-muted-foreground">
            {spec.name}
            {spec.required ? <span className="text-loss"> *</span> : null}
          </span>
          <SweepControls
            label={spec.name}
            state={sweep}
            onChange={(next) => onSweepChange(spec.name, next)}
            disabled={disabled}
          />
          {errors.map((error, index) => (
            <span key={index} className="max-w-52 text-[11px] leading-tight text-loss">
              {error.message}
            </span>
          ))}
        </div>
      ) : (
        <ParamField
          spec={spec}
          value={value}
          onChange={onChange}
          onReset={onReset}
          errors={errors}
          disabled={disabled}
        />
      )}
    </div>
  );
}
