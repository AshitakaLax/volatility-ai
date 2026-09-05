import { Filter, RotateCcw } from "lucide-react";

import { Badge, Button, Card, CardContent, Field, Input, Select } from "@/components/ui/primitives";
import { DEFAULT_FILTERS, type ExecutionFilters, type Timeframe } from "@/types/backtest";

/**
 * Drill-down controls over a run's executions.
 *
 * Every control here is a VIEW filter -- it changes what is drawn, never
 * what was computed. Re-running with different parameters is
 * ParameterForm's job, and keeping the two visually distinct matters:
 * one is free and instant, the other costs 23 seconds of engine time,
 * and a user should be able to tell which they are about to do.
 */

interface Props {
  filters: ExecutionFilters;
  onChange: (filters: ExecutionFilters) => void;
  /** Tickers present in the loaded report. */
  availableTickers: string[];
  /** How many executions survive the current filters, out of how many. */
  showing: number;
  total: number;
}

const TIMEFRAMES: Timeframe[] = ["1Min", "5Min", "15Min", "1Hour", "1Day"];

/** Presets, as day offsets from the report's end. */
const PRESETS: { label: string; days: number | null }[] = [
  { label: "All", days: null },
  { label: "1M", days: 30 },
  { label: "3M", days: 90 },
  { label: "1Y", days: 365 },
];

export function FilterPanel({ filters, onChange, availableTickers, showing, total }: Props) {
  const set = <K extends keyof ExecutionFilters>(key: K, value: ExecutionFilters[K]) =>
    onChange({ ...filters, [key]: value });

  const applyPreset = (days: number | null) => {
    if (days === null) {
      onChange({ ...filters, range: { start: null, end: null } });
      return;
    }
    const end = new Date();
    const start = new Date(end.getTime() - days * 86_400_000);
    onChange({
      ...filters,
      range: {
        start: start.toISOString().slice(0, 10),
        end: end.toISOString().slice(0, 10),
      },
    });
  };

  const filtered = showing !== total;

  return (
    <Card>
      <CardContent className="flex flex-wrap items-end gap-4 pt-5">
        <Field label="Timeframe">
          <Select
            value={filters.timeframe}
            onChange={(event) => set("timeframe", event.currentTarget.value as Timeframe)}
          >
            {TIMEFRAMES.map((timeframe) => (
              <option key={timeframe} value={timeframe}>
                {timeframe}
              </option>
            ))}
          </Select>
        </Field>

        <Field label="From">
          <Input
            type="date"
            value={filters.range.start ?? ""}
            onChange={(event) =>
              set("range", { ...filters.range, start: event.currentTarget.value || null })
            }
          />
        </Field>

        <Field label="To">
          <Input
            type="date"
            value={filters.range.end ?? ""}
            onChange={(event) =>
              set("range", { ...filters.range, end: event.currentTarget.value || null })
            }
          />
        </Field>

        <div className="flex gap-1 pb-0.5">
          {PRESETS.map((preset) => (
            <Button
              key={preset.label}
              variant="outline"
              className="h-8 px-2 text-xs"
              onClick={() => applyPreset(preset.days)}
            >
              {preset.label}
            </Button>
          ))}
        </div>

        <Field label="Lot status">
          <Select
            value={filters.status}
            onChange={(event) =>
              set("status", event.currentTarget.value as ExecutionFilters["status"])
            }
          >
            <option value="all">All lots</option>
            {/* "Stuck" is this project's own word for an open lot:
                capital committed and not yet returned. */}
            <option value="stuck">Open / stuck only</option>
            <option value="closed">Harvested only</option>
          </Select>
        </Field>

        <Field label="RSI at entry">
          <div className="flex items-center gap-1">
            <Input
              type="number"
              min={0}
              max={100}
              placeholder="min"
              className="w-20"
              value={filters.rsiMin ?? ""}
              onChange={(event) =>
                set("rsiMin", event.currentTarget.value === "" ? null : Number(event.currentTarget.value))
              }
            />
            <span className="text-muted-foreground">–</span>
            <Input
              type="number"
              min={0}
              max={100}
              placeholder="max"
              className="w-20"
              value={filters.rsiMax ?? ""}
              onChange={(event) =>
                set("rsiMax", event.currentTarget.value === "" ? null : Number(event.currentTarget.value))
              }
            />
          </div>
        </Field>

        {availableTickers.length > 1 ? (
          <Field label="Fund">
            <Select
              value={filters.tickers[0] ?? ""}
              onChange={(event) =>
                set("tickers", event.currentTarget.value === "" ? [] : [event.currentTarget.value])
              }
            >
              <option value="">All</option>
              {availableTickers.map((ticker) => (
                <option key={ticker} value={ticker}>
                  {ticker}
                </option>
              ))}
            </Select>
          </Field>
        ) : null}

        <div className="ml-auto flex items-center gap-3">
          <Badge tone={filtered ? "stuck" : "neutral"} className="gap-1">
            <Filter className="size-3" />
            {showing} / {total}
          </Badge>
          {filtered ? (
            <Button variant="ghost" onClick={() => onChange(DEFAULT_FILTERS)}>
              <RotateCcw className="size-3.5" />
              Reset
            </Button>
          ) : null}
        </div>
      </CardContent>

      {(filters.rsiMin !== null || filters.rsiMax !== null) && (
        <CardContent className="pt-0">
          {/* Said out loud, because it changes what the count above
              means: an execution inside the indicator's warmup has no
              RSI, and treating unknown as in-range would claim the
              strategy entered on a reading that did not exist. */}
          <p className="text-xs text-muted-foreground">
            Executions with no RSI (inside the 14-bar warmup) are excluded while an RSI
            bound is set.
          </p>
        </CardContent>
      )}
    </Card>
  );
}
