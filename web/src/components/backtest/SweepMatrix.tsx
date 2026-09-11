import { FileInput, Grid3x3 } from "lucide-react";
import { useState } from "react";

import { Card, CardContent, CardHeader, CardTitle, Field, Select } from "@/components/ui/primitives";
import { cn, pct, usd } from "@/lib/utils";
import type { FundResult, SweepConfiguration } from "@/types/backtest";

/**
 * The parameter sweep as a heatmap: grid step against profit target.
 *
 * WHY THE SCALE IS PER-METRIC AND SIGNED. Colour runs from the minimum
 * to the maximum of the cells actually present, not from zero, because
 * a sweep whose results all sit between 38% and 39% would otherwise be
 * one flat block. For metrics where lower is better -- drawdown, stuck
 * capital -- the scale is inverted, so "good" is always the same colour
 * and a reader never has to remember which way a particular column runs.
 *
 * WHY THERE IS NO "BEST" BADGE. This project's own results repeatedly
 * show the highest-return cell belonging to a configuration nobody would
 * deploy, and a matrix that crowned one would be making a
 * recommendation it has no basis for. The engine's ranking already puts
 * its own choice first in the table above; this shows the shape of the
 * surface, which is the thing a single number cannot.
 */

interface Props {
  funds: Record<string, FundResult>;
  /**
   * A cell was clicked -- selects it as BacktestResult's current
   * configuration, so RiskRewardMetrics (instant, metrics are already
   * carried per cell) and, on request, the chart/trade log ("View full
   * detail", a scoped re-run) reflect exactly this configuration. Fired
   * with the whole cell, not just the two axes, since a cell's identity
   * also depends on its resolved strategy_params once one of those is
   * swept too.
   */
  onSelectConfiguration?: (config: SweepConfiguration) => void;
  /**
   * Stage a cell's grid_step/profit_target onto the Run-a-Backtest form
   * and switch to the Backtesting tab -- for launching a broader NEW
   * sweep around this point, not for viewing this one's own detail
   * (onSelectConfiguration does that, in place). A separate, explicit
   * affordance per cell so this still-useful capability isn't lost
   * merely because a bare cell click now means something else.
   */
  onLoadIntoForm?: (gridStep: number, profitTarget: number) => void;
}

type MetricKey =
  | "cagr_pct"
  | "net_yield_pct"
  | "max_drawdown_pct"
  | "sharpe_ratio"
  | "win_rate_pct"
  | "stuck_capital_value"
  | "total_trades";

const METRICS: { key: MetricKey; label: string; higherIsBetter: boolean; format: (v: number) => string }[] = [
  { key: "cagr_pct", label: "CAGR", higherIsBetter: true, format: (v) => pct(v, 1) },
  { key: "net_yield_pct", label: "Net yield", higherIsBetter: true, format: (v) => pct(v, 2) },
  { key: "max_drawdown_pct", label: "Max drawdown", higherIsBetter: false, format: (v) => pct(v, 1) },
  { key: "sharpe_ratio", label: "Sharpe", higherIsBetter: true, format: (v) => v.toFixed(2) },
  { key: "win_rate_pct", label: "Win rate", higherIsBetter: true, format: (v) => pct(v, 0) },
  {
    key: "stuck_capital_value",
    label: "Stuck capital",
    higherIsBetter: false,
    format: (v) => usd(v, 0),
  },
  { key: "total_trades", label: "Trades", higherIsBetter: true, format: (v) => String(v) },
];

function shade(value: number, min: number, max: number, higherIsBetter: boolean): string {
  // A degenerate range is one colour, not a division by zero.
  if (max === min) return "oklch(0.6 0.02 286 / 0.25)";
  const position = (value - min) / (max - min);
  const good = higherIsBetter ? position : 1 - position;
  // Red through neutral to green, alpha carrying the intensity so the
  // text on top stays readable at every level.
  const hue = 25 + good * 127;
  const alpha = 0.12 + Math.abs(good - 0.5) * 0.5;
  return `oklch(0.7 0.16 ${hue} / ${alpha.toFixed(3)})`;
}

/** A stable, human-readable label for one cell's resolved combo --
 * dictionary order isn't guaranteed on the wire, so entries are sorted
 * by key before joining. `{}` (no strategy param swept) reads as "—". */
function comboKey(params: SweepConfiguration["strategy_params"]): string {
  return JSON.stringify(Object.entries(params ?? {}).sort(([a], [b]) => a.localeCompare(b)));
}
function comboLabel(params: SweepConfiguration["strategy_params"]): string {
  const entries = Object.entries(params ?? {}).sort(([a], [b]) => a.localeCompare(b));
  return entries.length === 0 ? "—" : entries.map(([key, value]) => `${key}=${value}`).join(", ");
}

export function SweepMatrix({ funds, onSelectConfiguration, onLoadIntoForm }: Props) {
  const withGrid = Object.entries(funds).filter(
    ([, fund]) => (fund.configurations?.length ?? 0) > 1,
  );
  const [metric, setMetric] = useState<MetricKey>("cagr_pct");
  const [ticker, setTicker] = useState<string>(withGrid[0]?.[0] ?? "");
  const [combo, setCombo] = useState<string>("");

  // A single-configuration run has no surface to show. Rendering an
  // empty 1x1 grid would suggest the sweep did something it did not.
  if (withGrid.length === 0) return null;

  const fund = funds[ticker] ?? withGrid[0]?.[1];
  const allCells: SweepConfiguration[] = fund?.configurations ?? [];
  const spec = METRICS.find((entry) => entry.key === metric) ?? METRICS[0]!;

  // Once a strategy param is ALSO swept, several cells can share one
  // (grid_step, profit_target) pair -- one per combo. The 2D heatmap
  // below can only show one combo at a time, so when more than one is
  // present, a "Params" selector picks which slice to render; the
  // lookup below is built from that slice, never the whole cell set, so
  // no combo is silently dropped by the last-write-wins Map underneath.
  const combos = [...new Map(allCells.map((cell) => [comboKey(cell.strategy_params), cell.strategy_params])).entries()];
  const activeCombo = combos.some(([key]) => key === combo) ? combo : (combos[0]?.[0] ?? "");
  const cells = combos.length > 1 ? allCells.filter((cell) => comboKey(cell.strategy_params) === activeCombo) : allCells;

  const steps = [...new Set(cells.map((cell) => cell.grid_step))].sort((a, b) => a - b);
  const targets = [...new Set(cells.map((cell) => cell.profit_target))].sort((a, b) => a - b);

  const values = cells.map((cell) => cell.metrics[spec.key]);
  const min = Math.min(...values);
  const max = Math.max(...values);

  const lookup = new Map(
    cells.map((cell) => [`${cell.grid_step}|${cell.profit_target}`, cell]),
  );

  return (
    <Card>
      <CardHeader className="flex-row items-end justify-between gap-4">
        <div>
          <CardTitle className="flex items-center gap-2">
            <Grid3x3 className="size-4" />
            Parameter sweep
          </CardTitle>
          <p className="mt-1 text-xs text-muted-foreground">
            {cells.length} configuration{cells.length === 1 ? "" : "s"} · grid step down,
            profit target across. Colour is scaled to this grid's own range, and inverted
            where lower is better.
          </p>
        </div>
        <div className="flex gap-3">
          {withGrid.length > 1 ? (
            <Field label="Fund">
              <Select value={ticker} onChange={(event) => setTicker(event.currentTarget.value)}>
                {withGrid.map(([name]) => (
                  <option key={name} value={name}>
                    {name}
                  </option>
                ))}
              </Select>
            </Field>
          ) : null}
          {combos.length > 1 ? (
            <Field label="Params">
              <Select value={activeCombo} onChange={(event) => setCombo(event.currentTarget.value)}>
                {combos.map(([key, params]) => (
                  <option key={key} value={key}>
                    {comboLabel(params)}
                  </option>
                ))}
              </Select>
            </Field>
          ) : null}
          <Field label="Metric">
            <Select
              value={metric}
              onChange={(event) => setMetric(event.currentTarget.value as MetricKey)}
            >
              {METRICS.map((entry) => (
                <option key={entry.key} value={entry.key}>
                  {entry.label}
                </option>
              ))}
            </Select>
          </Field>
        </div>
      </CardHeader>

      <CardContent className="overflow-x-auto">
        <table className="text-sm">
          <thead>
            <tr>
              <th className="p-2 text-left text-xs font-medium text-muted-foreground">
                step ╲ target
              </th>
              {targets.map((target) => (
                <th
                  key={target}
                  className="tnum p-2 text-right text-xs font-medium text-muted-foreground"
                >
                  {(target * 100).toFixed(2)}%
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="tnum">
            {steps.map((step) => (
              <tr key={step}>
                <td className="p-2 text-xs font-medium text-muted-foreground">
                  {(step * 100).toFixed(2)}%
                </td>
                {targets.map((target) => {
                  const cell = lookup.get(`${step}|${target}`);
                  if (!cell) {
                    // A combination the engine skipped or that errored.
                    // Blank, not zero -- zero is a result.
                    return (
                      <td key={target} className="p-2 text-right text-muted-foreground">
                        --
                      </td>
                    );
                  }
                  const value = cell.metrics[spec.key];
                  return (
                    <td
                      key={target}
                      className={cn(
                        "relative min-w-[86px] rounded p-2 text-right font-medium",
                        "border border-border/40",
                        onSelectConfiguration && "cursor-pointer hover:ring-1 hover:ring-ring",
                      )}
                      onClick={() => onSelectConfiguration?.(cell)}
                      style={{ background: shade(value, min, max, spec.higherIsBetter) }}
                      title={
                        `step ${(step * 100).toFixed(2)}% · target ${(target * 100).toFixed(2)}%\n` +
                        `CAGR ${pct(cell.metrics.cagr_pct)} · DD ${pct(cell.metrics.max_drawdown_pct)}\n` +
                        `${cell.metrics.closed_trades} closed of ${cell.metrics.total_trades}` +
                        (onSelectConfiguration ? "\n\nclick to view this configuration below" : "")
                      }
                    >
                      {onLoadIntoForm ? (
                        <button
                          type="button"
                          title="Load into form for a new sweep"
                          onClick={(event) => {
                            event.stopPropagation();
                            onLoadIntoForm(step, target);
                          }}
                          className="absolute top-0.5 left-0.5 text-muted-foreground/60 hover:text-foreground"
                        >
                          <FileInput className="size-3" />
                        </button>
                      ) : null}
                      {spec.format(value)}
                    </td>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </CardContent>
    </Card>
  );
}
