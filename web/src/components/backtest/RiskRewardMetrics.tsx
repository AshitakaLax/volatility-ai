import { AlertTriangle, Gauge, TrendingUp } from "lucide-react";

import { Badge, Card, CardContent, CardHeader, CardTitle } from "@/components/ui/primitives";
import { cn, pct, usd } from "@/lib/utils";
import type { FundPerformanceMetrics } from "@/types/backtest";

/**
 * The performance panel: traditional risk/reward, then the grid-specific
 * measures that only mean anything for this strategy.
 *
 * The two groups are separated deliberately. Sharpe and max drawdown are
 * comparable to any strategy anywhere; Stuck Capital and Capital Velocity
 * describe a book that can only sell at a profit, and reading them beside
 * a Sharpe ratio without that distinction invites comparing them to
 * numbers from strategies where the concepts do not exist.
 */

interface Props {
  metrics: FundPerformanceMetrics;
  /** Buy-and-hold for the same window, when known. The bar that matters. */
  benchmarkCagr?: number | null;
}

function Metric({
  label,
  value,
  hint,
  tone,
}: {
  label: string;
  value: string;
  // `| undefined` explicitly, because exactOptionalPropertyTypes
  // distinguishes "absent" from "present and undefined" -- and every
  // caller here passes a conditional that may evaluate to undefined.
  hint?: string | undefined;
  tone?: "profit" | "loss" | "stuck" | undefined;
}) {
  return (
    <div className="flex flex-col gap-0.5">
      <span className="text-xs text-muted-foreground">{label}</span>
      <span
        className={cn(
          "tnum text-lg font-semibold",
          tone === "profit" && "text-profit",
          tone === "loss" && "text-loss",
          tone === "stuck" && "text-stuck",
        )}
      >
        {value}
      </span>
      {hint ? <span className="text-xs text-muted-foreground">{hint}</span> : null}
    </div>
  );
}

export function RiskRewardMetrics({ metrics, benchmarkCagr }: Props) {
  const beatsBenchmark =
    benchmarkCagr === null || benchmarkCagr === undefined
      ? null
      : metrics.cagr_pct > benchmarkCagr;

  // Return per unit of drawdown. This project ranks by it constantly and
  // it is not in the payload, so it is derived here rather than adding a
  // field that would then exist in two places.
  const returnOverDrawdown =
    metrics.max_drawdown_pct > 0 ? metrics.cagr_pct / metrics.max_drawdown_pct : null;

  return (
    <div className="grid gap-4 lg:grid-cols-2">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <TrendingUp className="size-4" />
            Risk and reward
          </CardTitle>
        </CardHeader>
        <CardContent className="grid grid-cols-2 gap-4 sm:grid-cols-4">
          <Metric
            label="Net yield"
            value={pct(metrics.net_yield_pct)}
            tone={metrics.net_yield_pct >= 0 ? "profit" : "loss"}
          />
          <Metric
            label="CAGR"
            value={pct(metrics.cagr_pct)}
            hint={
              benchmarkCagr === null || benchmarkCagr === undefined
                ? undefined
                : `hold ${pct(benchmarkCagr)}`
            }
            tone={beatsBenchmark === null ? undefined : beatsBenchmark ? "profit" : "loss"}
          />
          <Metric
            label="Max drawdown"
            value={pct(metrics.max_drawdown_pct)}
            hint={returnOverDrawdown === null ? undefined : `${returnOverDrawdown.toFixed(2)}x ret/dd`}
            tone="loss"
          />
          <Metric label="Sharpe" value={metrics.sharpe_ratio.toFixed(2)} />
          <Metric
            label="Sortino"
            value={metrics.sortino_ratio.toFixed(2)}
            hint="downside only"
          />
          <Metric
            label="Profit factor"
            value={metrics.profit_factor.toFixed(2)}
            hint={metrics.max_consecutive_losses === 0 ? "no losing trade" : undefined}
          />
          <Metric label="Win rate" value={pct(metrics.win_rate_pct, 1)} />
          <Metric
            label="Max consecutive losses"
            value={String(metrics.max_consecutive_losses)}
          />
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Gauge className="size-4" />
            Grid behaviour
          </CardTitle>
          <p className="text-xs text-muted-foreground">
            What a book that only sells at a profit actually did with the capital.
          </p>
        </CardHeader>
        <CardContent className="grid grid-cols-2 gap-4 sm:grid-cols-4">
          <Metric
            label="Stuck capital"
            value={usd(metrics.stuck_capital_value, 0)}
            hint={`${metrics.open_trades} open lot${metrics.open_trades === 1 ? "" : "s"}`}
            tone={metrics.stuck_capital_value > 0 ? "stuck" : undefined}
          />
          <Metric
            label="Capital velocity"
            value={metrics.capital_velocity_index.toFixed(3)}
            hint="closed / total"
          />
          <Metric
            label="Harvest : stuck"
            value={metrics.harvest_to_stuck_ratio.toFixed(2)}
            hint="closed / open"
          />
          <Metric
            label="Avg hold"
            value={`${metrics.avg_hold_duration.toFixed(0)} bars`}
          />
          <Metric label="Total trades" value={String(metrics.total_trades)} />
          <Metric label="Closed" value={String(metrics.closed_trades)} />
          <Metric label="Final equity" value={usd(metrics.final_equity, 0)} />
          <div className="flex flex-col gap-1">
            <span className="text-xs text-muted-foreground">Signal exits</span>
            <div>
              {metrics.signal_exits > 0 ? (
                <Badge tone="loss" className="gap-1">
                  <AlertTriangle className="size-3" />
                  {metrics.signal_exits}
                </Badge>
              ) : (
                <Badge>0</Badge>
              )}
            </div>
            {/* The ONE exit path permitted to realise a loss. A run with
                any is a materially different strategy from one with none,
                and that should be visible without reading a config. */}
            <span className="text-xs text-muted-foreground">
              {metrics.signal_exits > 0 ? "losses were realised" : "no loss realised"}
            </span>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
