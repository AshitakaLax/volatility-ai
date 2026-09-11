import { ListTree } from "lucide-react";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/primitives";
import { describeSweepAxes, type SweepAxis } from "@/lib/sweepSummary";
import type { SweepConfiguration } from "@/types/backtest";

/**
 * A broad overview of one fund's sweep: how many configurations, and
 * which arguments actually varied across them -- read before diving into
 * a specific one below (ConfigurationList) or the heatmap (SweepMatrix).
 *
 * Rendered only when there is a real sweep to describe (BacktestResult
 * gates this on `configurations.length > 1`, the same threshold
 * SweepMatrix's own internal guard uses), so an ordinary single-
 * configuration run's page carries no trace of this section.
 */

interface Props {
  configurations: SweepConfiguration[];
}

function formatAxisValues(axis: SweepAxis): string {
  const isPercentAxis = axis.key === "grid_step" || axis.key === "profit_target";
  const format = (value: SweepAxis["values"][number]): string =>
    isPercentAxis && typeof value === "number" ? `${(value * 100).toFixed(2)}%` : String(value);
  // A long axis reads better as a range than a wall of numbers; a short
  // one is more informative listed out in full.
  if (axis.values.length > 6) {
    return `${axis.values.length} values, ${format(axis.values[0]!)} – ${format(axis.values.at(-1)!)}`;
  }
  return `${axis.values.length} values: ${axis.values.map(format).join(", ")}`;
}

export function SweepSummary({ configurations }: Props) {
  const summary = describeSweepAxes(configurations);

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <ListTree className="size-4" />
          Sweep details
        </CardTitle>
        <p className="mt-1 text-xs text-muted-foreground">
          {summary.configurationCount} configuration{summary.configurationCount === 1 ? "" : "s"}{" "}
          in this sweep.
        </p>
      </CardHeader>
      <CardContent className="flex flex-wrap gap-x-6 gap-y-2 pt-0">
        {summary.axes.map((axis) => (
          <div key={axis.key} className="flex flex-col gap-0.5">
            <span className="text-xs font-medium text-muted-foreground">{axis.label}</span>
            <span className="text-sm">{formatAxisValues(axis)}</span>
          </div>
        ))}
      </CardContent>
    </Card>
  );
}
