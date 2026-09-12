import { ParamField } from "@/components/backtest/ParamField";
import { Checkbox } from "@/components/ui/primitives";
import type { OptionsSweepFieldState } from "@/lib/strategyParams";
import type { ParamSpec, ValidateError } from "@/types/backtest";

/**
 * A sweepable ENUM strategy param (`spec.enum` set, `spec.sweepable`):
 * an "enable sweep" checkbox above the field, exactly like
 * SweepableParamField's own. Unchecked renders the ordinary `<select>`
 * ParamField unmodified; checked replaces it with a checklist of
 * `spec.enum`'s own values -- there is no range to generate between
 * "stdev" and "range", only a subset to choose.
 *
 * Module-scope, same reasoning as ParamField/SweepableParamField: a
 * component redefined inside ParameterForm on every render would
 * remount here and drop focus mid-keystroke -- moot for checkboxes
 * specifically, but the convention is kept so every field in the form
 * follows one rule rather than two.
 */

interface Props {
  spec: ParamSpec;
  /** Scalar text, used only while the sweep is off. */
  value: string;
  onChange: (name: string, value: string) => void;
  onReset: (name: string) => void;
  sweep: OptionsSweepFieldState;
  onSweepChange: (name: string, next: OptionsSweepFieldState) => void;
  /** Already filtered to this field. */
  errors: ValidateError[];
  disabled: boolean;
}

export function OptionsSweepField({
  spec,
  value,
  onChange,
  onReset,
  sweep,
  onSweepChange,
  errors,
  disabled,
}: Props) {
  const options = spec.enum ?? [];

  function toggle(option: string, checked: boolean) {
    const selected = checked
      ? [...sweep.selected, option]
      : sweep.selected.filter((entry) => entry !== option);
    onSweepChange(spec.name, { ...sweep, selected });
  }

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
          <div className="flex flex-col gap-1">
            {options.map((option) => (
              <label key={option} className="flex items-center gap-1.5 text-xs">
                <Checkbox
                  checked={sweep.selected.includes(option)}
                  disabled={disabled}
                  onChange={(event) => toggle(option, event.currentTarget.checked)}
                />
                {option}
              </label>
            ))}
          </div>
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
