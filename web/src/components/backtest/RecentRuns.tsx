import { ArrowUpRight } from "lucide-react";
import { useEffect, useState } from "react";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/primitives";
import { api } from "@/lib/api";
import { runUrl } from "@/lib/utils";
import type { RunSummary } from "@/types/backtest";

/**
 * What to open, on a Backtest result page with nothing loaded: the runs
 * this server finished most recently. The queue's own listing, so nothing
 * more is downloaded than Active runs already reads; older runs are in Run
 * history on the Backtesting tab.
 */
const SHOWN = 8;

export function RecentRuns() {
  const [runs, setRuns] = useState<RunSummary[] | null>(null);

  useEffect(() => {
    let cancelled = false;
    api
      .runs()
      .then((body) => {
        if (!cancelled) setRuns(body.runs.filter((run) => run.status === "complete"));
      })
      .catch(() => {
        if (!cancelled) setRuns([]);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <Card>
      <CardHeader>
        <CardTitle>No run loaded</CardTitle>
        <p className="text-xs text-muted-foreground">
          Open one below, or from Run history or Active runs on the{" "}
          <a className="text-foreground underline" href="#backtest">
            Backtesting
          </a>{" "}
          tab, or submit a new backtest there.
        </p>
      </CardHeader>
      <CardContent>
        {runs === null ? (
          <div className="h-16 animate-pulse rounded-md bg-secondary/50" />
        ) : runs.length === 0 ? (
          <p className="text-sm text-muted-foreground">
            Nothing has finished since this server started.
          </p>
        ) : (
          <ul className="divide-y divide-border/60" data-testid="recent-runs">
            {runs
              .slice(-SHOWN)
              .reverse()
              .map((run) => (
                <li key={run.id}>
                  <a
                    href={runUrl(run.id)}
                    className="flex items-center justify-between gap-3 py-2 text-sm hover:text-foreground"
                  >
                    <span className="min-w-0 truncate">
                      {run.req.name || `${run.req.model ?? "run"} · ${run.req.tickers.join(", ")}`}
                    </span>
                    <span className="flex shrink-0 items-center gap-2 text-xs text-muted-foreground">
                      <span className="font-mono">{run.id.slice(0, 8)}</span>
                      <ArrowUpRight className="size-3.5" />
                    </span>
                  </a>
                </li>
              ))}
          </ul>
        )}
      </CardContent>
    </Card>
  );
}
