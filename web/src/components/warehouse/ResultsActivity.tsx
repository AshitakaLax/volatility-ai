import { ExternalLink } from "lucide-react";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/primitives";
import { pct, runUrl } from "@/lib/utils";
import { ago, barHeights, whole } from "@/lib/warehouse";
import type { WarehouseStatus } from "@/types/warehouse";

/**
 * The sweeps and simulations recorded: how fast they are arriving, the
 * best each strategy has found per fund, and the latest sweeps.
 *
 * Ranked by Total Return % -- never Capital Velocity Index, which
 * saturates at 1.0 on long datasets. Return/Drawdown beside it is the
 * Calmar-style check on how the return was earned.
 */
export function ResultsActivity({ status, now }: { status: WarehouseStatus; now: Date }) {
  const { results, summary } = status;
  const heights = barHeights(results.hourly);
  const failed = results.by_status.FAILED ?? 0;
  const seconds = results.mean_ms_last_hour !== null ? results.mean_ms_last_hour / 1000 : null;

  return (
    <Card>
      <CardHeader>
        <CardTitle>Sweeps and simulations</CardTitle>
        <p className="text-xs text-muted-foreground">
          {whole(summary.simulations)} simulations in {whole(summary.sweeps)} sweeps ·{" "}
          {whole(summary.last_hour)} in the last hour, {whole(summary.last_day)} in the last day
          {seconds !== null ? ` · ${seconds.toFixed(0)} s per configuration per worker` : ""} ·{" "}
          {failed ? (
            <span className="text-loss">{whole(failed)} failed</span>
          ) : (
            "none failed"
          )}{" "}
          · trade logs kept for {whole(results.executions.simulations)} best configurations (
          {whole(results.executions.rows)} fills)
        </p>
      </CardHeader>
      <CardContent className="space-y-6">
        <div>
          <div className="mb-1 flex justify-between text-xs text-muted-foreground">
            <span>Simulations per hour, last {results.hourly.length} hours</span>
            <span>peak {whole(Math.max(0, ...results.hourly.map((hour) => hour.n)))}</span>
          </div>
          <div className="flex h-16 items-end gap-px rounded border border-border/50 p-1">
            {results.hourly.map((hour, index) => (
              <div
                key={hour.hour}
                className="flex-1 rounded-sm bg-primary/70"
                style={{ height: `${Math.max(heights[index] ?? 0, hour.n > 0 ? 2 : 0)}%` }}
                title={`${new Date(hour.hour).toLocaleString()}: ${whole(hour.n)}`}
              />
            ))}
          </div>
        </div>

        <div className="overflow-x-auto">
          <div className="mb-2 text-xs font-semibold">Best found, by fund and strategy</div>
          <table className="w-full min-w-[820px] text-sm">
            <thead>
              <tr className="border-b border-border text-left text-xs text-muted-foreground">
                <th className="pb-2 font-medium">Fund</th>
                <th className="pb-2 font-medium">Strategy</th>
                <th className="pb-2 text-right font-medium">Sweeps</th>
                <th className="pb-2 text-right font-medium">Simulations</th>
                <th className="pb-2 text-right font-medium">Best return</th>
                <th className="pb-2 text-right font-medium">Its max drawdown</th>
                <th className="pb-2 text-right font-medium">Return / drawdown</th>
                <th className="pb-2 text-right font-medium">Last result</th>
              </tr>
            </thead>
            <tbody>
              {results.strategies.map((row) => (
                <tr
                  key={`${row.fund}/${row.strategy}`}
                  className="border-b border-border/50 last:border-0"
                >
                  <td className="py-1.5 font-medium">{row.fund}</td>
                  <td className="py-1.5">{row.strategy}</td>
                  <td className="py-1.5 text-right tabular-nums">{whole(row.sweeps)}</td>
                  <td className="py-1.5 text-right tabular-nums">{whole(row.simulations)}</td>
                  <td className="py-1.5 text-right font-semibold tabular-nums">
                    {pct(row.best_return, 1, true)}
                  </td>
                  <td className="py-1.5 text-right tabular-nums">{pct(row.best_drawdown, 1)}</td>
                  <td className="py-1.5 text-right tabular-nums">
                    {row.best_calmar !== null ? row.best_calmar.toFixed(2) : "--"}
                  </td>
                  <td className="py-1.5 text-right text-xs text-muted-foreground">
                    {ago(row.last, now)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <div className="overflow-x-auto">
          <div className="mb-2 text-xs font-semibold">
            Latest {results.recent.length} sweeps
          </div>
          <table className="w-full min-w-[820px] text-sm">
            <thead>
              <tr className="border-b border-border text-left text-xs text-muted-foreground">
                <th className="pb-2 font-medium">Started</th>
                <th className="pb-2 font-medium">Run</th>
                <th className="pb-2 font-medium">Fund</th>
                <th className="pb-2 font-medium">Strategy</th>
                <th className="pb-2 text-right font-medium">Simulations</th>
                <th className="pb-2 text-right font-medium">Best return</th>
                <th className="pb-2 text-right font-medium">Last result</th>
              </tr>
            </thead>
            <tbody>
              {results.recent.map((sweep) => (
                <tr key={sweep.id} className="border-b border-border/50 last:border-0">
                  <td className="py-1.5 text-xs text-muted-foreground">
                    {sweep.created ? new Date(sweep.created).toLocaleString() : "--"}
                  </td>
                  <td className="max-w-[320px] truncate py-1.5 text-xs" title={sweep.id}>
                    {sweep.run_id ? (
                      <a
                        className="inline-flex items-center gap-1 hover:underline"
                        href={runUrl(sweep.run_id)}
                        target="_blank"
                        rel="noopener noreferrer"
                      >
                        {sweep.run_name ?? sweep.run_id}
                        <ExternalLink className="size-3" />
                      </a>
                    ) : (
                      <span className="text-muted-foreground">{sweep.id}</span>
                    )}
                  </td>
                  <td className="py-1.5 font-medium">{sweep.fund ?? "--"}</td>
                  <td className="py-1.5">{sweep.strategy ?? "--"}</td>
                  <td className="py-1.5 text-right tabular-nums">
                    {whole(sweep.simulations)}
                    {sweep.failed ? (
                      <span className="text-loss"> ({whole(sweep.failed)} failed)</span>
                    ) : null}
                  </td>
                  <td className="py-1.5 text-right tabular-nums">
                    {pct(sweep.best_return, 1, true)}
                  </td>
                  <td className="py-1.5 text-right text-xs text-muted-foreground">
                    {ago(sweep.last, now)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </CardContent>
    </Card>
  );
}
