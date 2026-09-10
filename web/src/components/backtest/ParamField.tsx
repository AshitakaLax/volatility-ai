import { RotateCcw } from "lucide-react";

import { Input, Select } from "@/components/ui/primitives";
import { cn } from "@/lib/utils";
import type { ParamSpec, ValidateError } from "@/types/backtest";

/**
 * One sizing-model constructor argument, rendered as the right kind of
 * input for its type.
 *
 * Module-scope on purpose: a component redefined inside ParameterForm on
 * every render would remount here and the input would lose focus on
 * every keystroke.
 */

interface Props {
  spec: ParamSpec;
  /** Raw input text. "" means blank/unset. */
  value: string;
  onChange: (name: string, value: string) => void;
  onReset: (name: string) => void;
  /** Server validation errors already filtered to this field. */
  errors: ValidateError[];
  disabled: boolean;
  /** For `mirrors` fields (target_return): the value it tracks, shown
   * read-only. */
  mirroredValue?: string | undefined;
  /** For `mirrors` fields: the value the engine reports it will use,
   * once a validation round has come back. */
  alignedNote?: string | undefined;
}

export function ParamField({
  spec,
  value,
  onChange,
  onReset,
  errors,
  disabled,
  mirroredValue,
  alignedNote,
}: Props) {
  const locked = !spec.editable;
  const seeded = spec.suggested == null ? "" : String(spec.suggested);
  const changed = !locked && spec.mirrors === null && value !== seeded;
  const blankRequired = spec.editable && spec.required && value.trim() === "";

  const shown = spec.mirrors !== null ? (mirroredValue ?? "") : value;

  return (
    <div className="flex flex-col gap-1.5">
      <span className="flex items-center gap-1.5 text-xs font-medium text-muted-foreground">
        {spec.name}
        {spec.required ? <span className="text-loss">*</span> : null}
        {changed ? (
          <button
            type="button"
            onClick={() => onReset(spec.name)}
            title={`reset to ${seeded || "blank"}`}
            className="text-muted-foreground hover:text-foreground"
          >
            <RotateCcw className="size-3" />
          </button>
        ) : null}
      </span>

      {spec.enum ? (
        <Select
          className="w-40"
          value={shown}
          disabled={disabled || locked}
          onChange={(event) => onChange(spec.name, event.currentTarget.value)}
        >
          {spec.enum.map((option) => (
            <option key={option} value={option}>
              {option}
            </option>
          ))}
        </Select>
      ) : spec.type === "bool" ? (
        <Select
          className="w-24"
          value={shown || "false"}
          disabled={disabled || locked}
          onChange={(event) => onChange(spec.name, event.currentTarget.value)}
        >
          <option value="false">false</option>
          <option value="true">true</option>
        </Select>
      ) : spec.type === "str" ? (
        <Input
          type="text"
          className="w-40"
          value={shown}
          disabled={disabled || locked}
          onChange={(event) => onChange(spec.name, event.currentTarget.value)}
        />
      ) : (
        <Input
          type="number"
          step={spec.step ?? "any"}
          placeholder={spec.nullable ? "auto" : undefined}
          className={cn("w-28", blankRequired && "border-loss")}
          value={shown}
          disabled={disabled || locked}
          onChange={(event) => onChange(spec.name, event.currentTarget.value)}
        />
      )}

      {locked && spec.locked_reason ? (
        <span className="max-w-52 text-[11px] leading-tight text-muted-foreground">
          {spec.locked_reason}
          {alignedNote ? ` — engine: ${alignedNote}` : ""}
        </span>
      ) : null}
      {errors.map((error, index) => (
        <span key={index} className="max-w-52 text-[11px] leading-tight text-loss">
          {error.message}
        </span>
      ))}
    </div>
  );
}
