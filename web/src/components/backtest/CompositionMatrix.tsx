import { Grid2x2 } from "lucide-react";
import { useEffect, useMemo, useState } from "react";

import { Badge, Card, CardContent, CardHeader, CardTitle, Field, Select } from "@/components/ui/primitives";
import { api } from "@/lib/api";
import { matrixOf } from "@/lib/composition";
import { pct } from "@/lib/utils";
import type { Cell, Composition } from "@/types/backtest";

/**
 * A composed run as a buy x sell heatmap: each cell is one pairing's BEST
 * configuration on the chosen metric (over its grid steps and targets).
 *
 * The same per-metric, signed colour scale as SweepMatrix -- "good" is
 * always the same colour, lower-is-better metrics inverted -- and the same
 * refusal to crown a winner: a one-run heatmap shows the shape of the
 * surface, not a recommendation. The interaction question (does the best
 * sell depend on the buy?) needs many funds and years, which is
 * `cli.py matrix`'s report (research/composition/analysis.py).
 *
 * Sell algorithms that may sell below cost are marked in their column.
 */

type MetricKey = "net_yield_pct" | "cagr_pct" | "max_drawdown_pct" | "sharpe_ratio" | "return_over_drawdown";

const METRICS: { key: MetricKey; label: string; higherIsBetter: boolean; format: (v: number) => string }[] = [
  { key: "net_yield_pct", label: "Net yield", higherIsBetter: true, format: (v) => pct(v, 2) },
  { key: "cagr_pct", label: "CAGR", higherIsBetter: true, format: (v) => pct(v, 1) },
  { key: "return_over_drawdown", label: "Return / drawdown", higherIsBetter: true, format: (v) => v.toFixed(2) },
  { key: "max_drawdown_pct", label: "Max drawdown", higherIsBetter: false, format: (v) => pct(v, 1) },
  { key: "sharpe_ratio", label: "Sharpe", higherIsBetter: true, format: (v) => v.toFixed(2) },
];

function shade(value: number, min: number, max: number, higherIsBetter: boolean): string {
  if (max === min) return "oklch(0.6 0.02 286 / 0.25)";
  const good = higherIsBetter ? (value - min) / (max - min) : (max - value) / (max - min);
  const hue = 25 + good * 127;
  const alpha = 0.12 + Math.abs(good - 0.5) * 0.5;
  return `oklch(0.7 0.16 ${hue} / ${alpha.toFixed(3)})`;
}

export function CompositionMatrix({ configurations }: { configurations: Cell[] }) {
  const [metricKey, setMetricKey] = useState<MetricKey>("net_yield_pct");
  const [composition, setComposition] = useState<Composition | undefined>(undefined);
  useEffect(() => {
    api
      .funds()
      .then((body) => setComposition(body.composition))
      .catch(() => {
        /* only the loss marks need it */
      });
  }, []);
  const metric = METRICS.find((entry) => entry.key === metricKey)!;
  const { buys, sells, grid } = useMemo(
    () =>
      matrixOf(
        configurations,
        (cell) => (cell.m as unknown as Record<string, number | null | undefined>)[metric.key],
        composition,
        metric.higherIsBetter,
      ),
    [configurations, metric, composition],
  );
  if (buys.length === 0) return null;
  const values = [...grid.values()].map((cell) => cell.value).filter((v): v is number => v !== null);
  const min = Math.min(...values);
  const max = Math.max(...values);
  return (
    <Card data-testid="composition-matrix">
      <CardHeader className="flex-row items-center justify-between">
        <CardTitle className="flex items-center gap-2">
          <Grid2x2 className="size-4" />
          Buy × sell
        </CardTitle>
        <Field label="Metric">
          <Select value={metricKey} onChange={(event) => setMetricKey(event.currentTarget.value as MetricKey)}>
            {METRICS.map((entry) => (
              <option key={entry.key} value={entry.key}>
                {entry.label}
              </option>
            ))}
          </Select>
        </Field>
      </CardHeader>
      <CardContent className="overflow-x-auto">
        <table className="text-xs">
          <thead>
            <tr>
              <th className="px-2 py-1 text-left font-medium text-muted-foreground">buy ↓ / sell →</th>
              {sells.map((sell) => (
                <th key={sell} className="px-2 py-1 text-left font-medium">
                  <span className="flex flex-col gap-0.5">
                    {sell}
                    {composition?.sells[sell]?.loss ? (
                      <Badge tone="loss" className="w-fit px-1.5 py-0 text-[10px]">
                        may sell below cost
                      </Badge>
                    ) : null}
                  </span>
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {buys.map((buy) => (
              <tr key={buy}>
                <td className="px-2 py-1 font-medium">{buy}</td>
                {sells.map((sell) => {
                  const cell = grid.get(`${buy}|${sell}`);
                  const value = cell?.value ?? null;
                  return (
                    <td
                      key={sell}
                      className="px-2 py-1 text-right tabular-nums"
                      style={value !== null ? { background: shade(value, min, max, metric.higherIsBetter) } : undefined}
                      title={cell ? `${cell.count} configuration${cell.count === 1 ? "" : "s"}` : "not run"}
                    >
                      {value !== null ? metric.format(value) : "—"}
                    </td>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
        <p className="mt-2 text-[11px] text-muted-foreground">
          Each cell is its pairing's best configuration over the run's grid steps and targets. One run on
          one fund: whether the best sell depends on the buy, across funds and years, is the matrix
          report's question (cli.py matrix).
        </p>
      </CardContent>
    </Card>
  );
}
