import { ListChecks } from "lucide-react";

import { Badge, Card, CardContent, CardHeader, CardTitle } from "@/components/ui/primitives";
import { configurationKey } from "@/lib/sweepSummary";
import { cn, pct } from "@/lib/utils";
import type { SweepConfiguration } from "@/types/backtest";

/**
 * Every simulation the sweep ran, one row each, selectable.
 *
 * Deliberately simple: no column sorting (unlike RunHistory's), in
 * engine-ranked order (index 0 first) -- this is a picker over ONE
 * report's own configurations, not the whole-history table sorting was
 * built for. Selecting a row drives what RiskRewardMetrics/BacktestChart/
 * TradeLog show below, in BacktestResult.
 */

interface Props {
  configurations: SweepConfiguration[];
  selectedKey: string | null;
  onSelect: (config: SweepConfiguration) => void;
}

function paramsLabel(params: SweepConfiguration["strategy_params"]): string {
  const entries = Object.entries(params ?? {}).sort(([a], [b]) => a.localeCompare(b));
  return entries.length === 0 ? "—" : entries.map(([key, value]) => `${key}=${value}`).join(", ");
}

export function ConfigurationList({ configurations, selectedKey, onSelect }: Props) {
  if (configurations.length <= 1) return null;

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <ListChecks className="size-4" />
          Simulations
        </CardTitle>
        <p className="mt-1 text-xs text-muted-foreground">
          Select one to see its metrics, chart and trade log below.
        </p>
      </CardHeader>
      <CardContent className="overflow-x-auto pt-0">
        <table className="w-full min-w-[640px] text-sm">
          <thead>
            <tr className="border-b border-border text-left text-xs text-muted-foreground">
              <th className="pb-2 font-medium">#</th>
              <th className="pb-2 text-right font-medium">Step</th>
              <th className="pb-2 text-right font-medium">Target</th>
              <th className="pb-2 font-medium">Params</th>
              <th className="pb-2 text-right font-medium">CAGR</th>
              <th className="pb-2 text-right font-medium">Max DD</th>
            </tr>
          </thead>
          <tbody className="tnum">
            {configurations.map((config, index) => {
              const key = configurationKey(config);
              const selected = key === selectedKey;
              return (
                <tr
                  key={key}
                  data-testid="configuration-row"
                  onClick={() => onSelect(config)}
                  className={cn(
                    "cursor-pointer border-b border-border/50 last:border-0 hover:bg-accent",
                    selected && "bg-accent",
                  )}
                >
                  <td className="py-2 text-muted-foreground">
                    {index + 1}
                    {index === 0 ? <Badge className="ml-1.5">engine pick</Badge> : null}
                  </td>
                  <td className="py-2 text-right">{pct(config.grid_step * 100, 3)}</td>
                  <td className="py-2 text-right">{pct(config.profit_target * 100, 3)}</td>
                  <td className="max-w-[220px] truncate py-2 text-xs text-muted-foreground">
                    {paramsLabel(config.strategy_params)}
                  </td>
                  <td className="py-2 text-right">{pct(config.metrics.cagr_pct, 1)}</td>
                  <td className="py-2 text-right text-loss">
                    {pct(config.metrics.max_drawdown_pct, 1)}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </CardContent>
    </Card>
  );
}
