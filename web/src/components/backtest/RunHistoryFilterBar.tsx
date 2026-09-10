import { Filter, RotateCcw, X } from "lucide-react";
import { type ReactNode, useMemo } from "react";

import { Badge, Button, Field, Input, Select } from "@/components/ui/primitives";
import {
  HISTORY_METRIC_FIELDS,
  historyInputFields,
  runHistoryFilterActive,
  sameNumber,
} from "@/lib/filters";
import { cn } from "@/lib/utils";
import {
  EMPTY_RUN_HISTORY_FILTERS,
  type HistoryRow,
  type NumericRange,
  type RunHistoryFilters,
} from "@/types/backtest";

/**
 * The filter controls above the run-history table.
 *
 * Every control here is a VIEW filter -- it narrows what is listed,
 * never what was computed. It is deliberately busier than the execution
 * FilterPanel because history is where a reader compares dozens of
 * sweeps: categorical inputs (fund, algorithm, fill model) are
 * multi-select chips, the swept dimensions and any sizing-model
 * argument take a set of exact values AND a band, and every result
 * metric can be added as a band of its own.
 *
 * The actual filtering is `filterHistoryRows` in lib/filters.ts, tested
 * there; this component only edits the RunHistoryFilters object.
 */

interface Props {
  /** The UNFILTERED rows -- the control derives its options from them. */
  rows: HistoryRow[];
  filters: RunHistoryFilters;
  onChange: (next: RunHistoryFilters) => void;
  /** Rows surviving the current filter, out of the total. */
  showing: number;
  total: number;
}

const ALWAYS_SHOWN = new Set(["grid_step", "profit_target"]);
/** Above this many distinct values a field gets a range only -- a strip
 * of 40 chips is not a control. */
const MAX_CHIPS = 12;

function Chip({
  active,
  onClick,
  children,
}: {
  active: boolean;
  onClick: () => void;
  children: ReactNode;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={cn(
        "rounded-md border px-2 py-1 text-xs transition-colors",
        active
          ? "border-primary bg-primary text-primary-foreground"
          : "border-border hover:bg-accent",
      )}
    >
      {children}
    </button>
  );
}

export function RunHistoryFilterBar({ rows, filters, onChange, showing, total }: Props) {
  const funds = useMemo(
    () => [...new Set(rows.map((row) => row.ticker))].sort(),
    [rows],
  );
  const models = useMemo(
    () =>
      [...new Set(rows.map((row) => row.sizing_model).filter((v): v is string => Boolean(v)))].sort(),
    [rows],
  );
  const fills = useMemo(
    () =>
      [...new Set(rows.map((row) => row.fill_model).filter((v): v is string => Boolean(v)))].sort(),
    [rows],
  );
  const inputFields = useMemo(() => historyInputFields(rows), [rows]);

  const labelFor = (key: string): string => {
    const input = inputFields.find((field) => field.key === key);
    if (input) return input.label;
    const metric = HISTORY_METRIC_FIELDS.find((field) => `metric:${field.key}` === key);
    return metric ? metric.label : key;
  };
  const chipsFor = (key: string): number[] => {
    const input = inputFields.find((field) => field.key === key);
    if (!input) return [];
    return input.values.length >= 2 && input.values.length <= MAX_CHIPS ? input.values : [];
  };

  // Optional fields to render as their own range row: the ones the
  // reader added, plus any that already carry a value/range from a
  // restored filter, minus the two that are always shown.
  const extraKeys = useMemo(() => {
    const keys = new Set<string>(filters.extraFields);
    for (const key of Object.keys(filters.values)) keys.add(key);
    for (const key of Object.keys(filters.ranges)) keys.add(key);
    for (const key of ALWAYS_SHOWN) keys.delete(key);
    return [...keys];
  }, [filters]);

  const addableFields = useMemo(() => {
    const taken = new Set(extraKeys);
    const inputs = inputFields.filter(
      (field) => !ALWAYS_SHOWN.has(field.key) && !taken.has(field.key),
    );
    const metrics = HISTORY_METRIC_FIELDS.map((field) => ({
      key: `metric:${field.key}`,
      label: field.label,
    })).filter((field) => !taken.has(field.key));
    return { inputs, metrics };
  }, [extraKeys, inputFields]);

  const setToggle = (
    listKey: "tickers" | "models" | "fillModels",
    value: string,
  ) => {
    const current = filters[listKey];
    onChange({
      ...filters,
      [listKey]: current.includes(value)
        ? current.filter((entry) => entry !== value)
        : [...current, value],
    });
  };

  const toggleValue = (key: string, value: number) => {
    const current = filters.values[key] ?? [];
    const has = current.some((entry) => sameNumber(entry, value));
    const next = has
      ? current.filter((entry) => !sameNumber(entry, value))
      : [...current, value];
    const values = { ...filters.values };
    if (next.length === 0) delete values[key];
    else values[key] = next;
    onChange({ ...filters, values });
  };

  const setRangeEnd = (key: string, end: keyof NumericRange, raw: string) => {
    const parsed = raw === "" ? null : Number(raw);
    const current = filters.ranges[key] ?? { min: null, max: null };
    const merged: NumericRange = {
      ...current,
      [end]: parsed === null || Number.isNaN(parsed) ? null : parsed,
    };
    const ranges = { ...filters.ranges };
    if (merged.min === null && merged.max === null) delete ranges[key];
    else ranges[key] = merged;
    onChange({ ...filters, ranges });
  };

  const addField = (key: string) => {
    if (!key || ALWAYS_SHOWN.has(key) || filters.extraFields.includes(key)) return;
    onChange({ ...filters, extraFields: [...filters.extraFields, key] });
  };

  const removeField = (key: string) => {
    const values = { ...filters.values };
    const ranges = { ...filters.ranges };
    delete values[key];
    delete ranges[key];
    onChange({
      ...filters,
      values,
      ranges,
      extraFields: filters.extraFields.filter((entry) => entry !== key),
    });
  };

  const active = runHistoryFilterActive(filters);

  // A plain function that RETURNS JSX, deliberately not a nested
  // component: a `<NumericRow/>` redefined every render would remount on
  // each keystroke and the range input would lose focus mid-type.
  const numericRow = (fieldKey: string) => {
    const chips = chipsFor(fieldKey);
    const selected = filters.values[fieldKey] ?? [];
    const range = filters.ranges[fieldKey] ?? { min: null, max: null };
    return (
      <div
        key={fieldKey}
        className="flex flex-wrap items-center gap-2 rounded-md border border-border/60 px-2 py-1.5"
      >
        <span className="text-xs font-medium text-muted-foreground">{labelFor(fieldKey)}</span>
        {chips.map((value) => (
          <Chip
            key={value}
            active={selected.some((entry) => sameNumber(entry, value))}
            onClick={() => toggleValue(fieldKey, value)}
          >
            {trimNumber(value)}
          </Chip>
        ))}
        <div className="flex items-center gap-1">
          <Input
            type="number"
            placeholder="min"
            className="w-20"
            value={range.min ?? ""}
            onChange={(event) => setRangeEnd(fieldKey, "min", event.currentTarget.value)}
          />
          <span className="text-muted-foreground">–</span>
          <Input
            type="number"
            placeholder="max"
            className="w-20"
            value={range.max ?? ""}
            onChange={(event) => setRangeEnd(fieldKey, "max", event.currentTarget.value)}
          />
        </div>
        {!ALWAYS_SHOWN.has(fieldKey) ? (
          <button
            type="button"
            onClick={() => removeField(fieldKey)}
            title="Remove this filter"
            className="text-muted-foreground hover:text-foreground"
          >
            <X className="size-3.5" />
          </button>
        ) : null}
      </div>
    );
  };

  return (
    <div className="space-y-3 rounded-lg border border-border/60 bg-background/40 p-3">
      <div className="flex flex-wrap items-end gap-4">
        <Field label="Name contains">
          <Input
            className="w-48"
            placeholder="substring of the run name"
            value={filters.name}
            onChange={(event) => onChange({ ...filters, name: event.currentTarget.value })}
          />
        </Field>

        {funds.length > 1 ? (
          <ChipGroup
            label="Fund"
            options={funds}
            selected={filters.tickers}
            onToggle={(value) => setToggle("tickers", value)}
          />
        ) : null}

        {models.length > 1 ? (
          <ChipGroup
            label="Algorithm"
            options={models}
            selected={filters.models}
            onToggle={(value) => setToggle("models", value)}
          />
        ) : null}

        {fills.length > 1 ? (
          <ChipGroup
            label="Fill model"
            options={fills}
            selected={filters.fillModels}
            onToggle={(value) => setToggle("fillModels", value)}
          />
        ) : null}

        <div className="ml-auto flex items-center gap-3">
          <Badge tone={showing !== total ? "stuck" : "neutral"} className="gap-1">
            <Filter className="size-3" />
            {showing} / {total}
          </Badge>
          {active ? (
            <Button
              variant="ghost"
              onClick={() => onChange(EMPTY_RUN_HISTORY_FILTERS)}
              title="Clear every filter"
            >
              <RotateCcw className="size-3.5" />
              Reset
            </Button>
          ) : null}
        </div>
      </div>

      <div className="flex flex-wrap items-start gap-2">
        {numericRow("grid_step")}
        {numericRow("profit_target")}
        {extraKeys.map((key) => numericRow(key))}

        <Select
          className="h-8 w-52"
          value=""
          onChange={(event) => addField(event.currentTarget.value)}
        >
          <option value="">+ Add input / result filter…</option>
          {addableFields.inputs.length > 0 ? (
            <optgroup label="Input arguments">
              {addableFields.inputs.map((field) => (
                <option key={field.key} value={field.key}>
                  {field.label}
                </option>
              ))}
            </optgroup>
          ) : null}
          <optgroup label="Results">
            {addableFields.metrics.map((field) => (
              <option key={field.key} value={field.key}>
                {field.label}
              </option>
            ))}
          </optgroup>
        </Select>
      </div>
    </div>
  );
}

function ChipGroup({
  label,
  options,
  selected,
  onToggle,
}: {
  label: string;
  options: string[];
  selected: string[];
  onToggle: (value: string) => void;
}) {
  return (
    <div className="flex flex-col gap-1.5">
      <span className="text-xs font-medium text-muted-foreground">{label}</span>
      <div className="flex flex-wrap gap-1.5">
        {options.map((option) => (
          <Chip key={option} active={selected.includes(option)} onClick={() => onToggle(option)}>
            {option}
          </Chip>
        ))}
      </div>
    </div>
  );
}

/** Drop the float dust a percent conversion leaves (0.75000000001 -> "0.75"). */
function trimNumber(value: number): string {
  return Number(value.toFixed(6)).toString();
}
