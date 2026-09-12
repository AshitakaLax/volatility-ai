import { AlertCircle, CheckCircle2, Loader2, Timer } from "lucide-react";
import { useEffect, useState } from "react";

import { Badge, Card, CardContent, CardHeader, CardTitle } from "@/components/ui/primitives";
import { api } from "@/lib/api";
import { describeRequestAxes } from "@/lib/requestSummary";
import { queuePositions } from "@/lib/runQueue";
import { cn, runUrl } from "@/lib/utils";
import type { BacktestRunState } from "@/types/backtest";

/**
 * Backtests in flight, found on load rather than only when you started
 * them.
 *
 * WHY THIS EXISTS. useBacktestRun tracks the run THIS tab submitted. A
 * fresh page load knew about none of them -- so refreshing during a
 * sweep, or opening the dashboard on a second machine, showed an idle
 * page while the engine was busy. The runs were there the whole time;
 * nothing asked.
 *
 * It polls rather than subscribing. A websocket per run would mean
 * opening and closing sockets as jobs come and go, to learn the same
 * thing one cheap request answers for all of them at once. The socket
 * is the right tool for watching ONE run closely, which is what
 * useBacktestRun does after a submission.
 *
 * POLLING STOPS WHEN NOTHING IS RUNNING. An idle dashboard left open
 * overnight should not make a request every two seconds until morning.
 */

interface Props {
  /** Called when a run finishes, so history can refresh. */
  onSettled?: () => void;
}

const ACTIVE_POLL_MS = 2000;
// Slower when nothing is in flight: this only has to notice a run
// someone started elsewhere, and a few seconds of lag on that costs
// nothing.
const IDLE_POLL_MS = 15000;

export function ActiveRuns({ onSettled }: Props) {
  const [runs, setRuns] = useState<BacktestRunState[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    let timer: number | undefined;
    // Tracked so a run that finishes between polls still notifies once,
    // rather than the caller having to diff the list itself.
    let previouslyActive = new Set<string>();

    const tick = () => {
      api
        .runs()
        .then((body) => {
          if (cancelled) return;
          setRuns(body.runs);
          setError(null);

          const active = new Set(
            body.runs
              .filter((run) => run.status === "queued" || run.status === "running")
              .map((run) => run.run_id),
          );
          const justFinished = [...previouslyActive].some((id) => !active.has(id));
          previouslyActive = active;
          if (justFinished) onSettled?.();

          timer = window.setTimeout(tick, active.size > 0 ? ACTIVE_POLL_MS : IDLE_POLL_MS);
        })
        .catch((cause: unknown) => {
          if (cancelled) return;
          setError(cause instanceof Error ? cause.message : String(cause));
          // Keep trying, slowly. The engine host being down is a state
          // to recover from, not a reason to stop looking.
          timer = window.setTimeout(tick, IDLE_POLL_MS);
        });
    };

    tick();
    return () => {
      cancelled = true;
      if (timer !== undefined) window.clearTimeout(timer);
    };
  }, [onSettled]);

  const active = runs.filter((run) => run.status === "queued" || run.status === "running");
  const recent = runs.filter((run) => run.status !== "queued" && run.status !== "running").slice(0, 3);
  // `runs` is exactly GET /runs's own newest-first order -- the shape
  // queuePositions expects to recover true submission order from.
  const positions = queuePositions(runs);

  // Nothing running and nothing recent is the ordinary state, and an
  // empty card saying "no runs" every time is noise.
  if (active.length === 0 && recent.length === 0 && !error) return null;

  return (
    <Card>
      <CardHeader className="flex-row items-center justify-between">
        <CardTitle className="flex items-center gap-2">
          {active.length > 0 ? (
            <Loader2 className="size-4 animate-spin" />
          ) : (
            <Timer className="size-4" />
          )}
          {active.length > 0
            ? `${active.length} backtest${active.length === 1 ? "" : "s"} running`
            : "Recent runs"}
        </CardTitle>
        {error ? <Badge tone="loss">engine host unreachable</Badge> : null}
      </CardHeader>

      <CardContent className="space-y-3">
        {[...active, ...recent].map((run) => (
          <RunRow key={run.run_id} run={run} queuePosition={positions.get(run.run_id)} />
        ))}
        {error ? (
          <p className="text-xs text-muted-foreground">{error}</p>
        ) : null}
      </CardContent>
    </Card>
  );
}

function RunRow({
  run,
  queuePosition,
}: {
  run: BacktestRunState;
  /** This run's place among currently-queued jobs, or undefined when it
   * isn't queued (running/complete/failed) or the caller has none to
   * offer. */
  queuePosition?: { position: number; of: number } | undefined;
}) {
  const running = run.status === "running" || run.status === "queued";
  const percent = Math.round(run.progress * 100);

  // One JOB already IS one sweep -- grouping means describing what THIS
  // job covers, not merging several jobs together. Only computable when
  // the snapshot carries the submitted request (added this session;
  // absent only for a server predating it, in which case this row just
  // falls back to today's plainer rendering).
  const summary = run.request ? describeRequestAxes(run.request) : null;
  const label =
    run.name ??
    (run.request ? `${run.request.sizing_model} · ${run.request.tickers.join(", ")}` : null);

  const statusText =
    run.status === "queued"
      ? queuePosition
        ? queuePosition.position === 1
          ? "queued — next up"
          : `queued — position ${queuePosition.position} of ${queuePosition.of}`
        : "queued"
      : (run.message ?? run.status);

  return (
    <div className="flex flex-col gap-1">
      <div className="flex items-center gap-4">
        {/* The submitted label when there is one, a sizing-model/ticker
            fallback derived from the request when there isn't, the id
            as a last resort -- a list of "which of my sweeps is this"
            is exactly what the name was added for. The id stays
            reachable via the Open/Watch link either way. */}
        <span
          className="w-24 shrink-0 truncate text-xs text-muted-foreground"
          title={label ? `${label} · ${run.run_id}` : run.run_id}
        >
          {label ? (
            <span className="text-foreground">{label}</span>
          ) : (
            <span className="font-mono">{run.run_id.slice(0, 10)}</span>
          )}
        </span>

        <div className="flex-1">
          <div className="flex items-center justify-between gap-2 text-xs">
            <span className={cn(run.status === "failed" && "text-loss")}>{statusText}</span>
            {running ? <span className="tnum text-muted-foreground">{percent}%</span> : null}
          </div>
          {running ? (
            <div className="mt-1 h-1.5 overflow-hidden rounded-full bg-secondary">
              <div
                className={cn(
                  "h-full bg-primary transition-all duration-500",
                  // A queued run has made no progress and should not show
                  // a bar creeping forward -- it is waiting, not working.
                  run.status === "queued" && "animate-pulse",
                )}
                style={{ width: `${Math.max(percent, run.status === "queued" ? 100 : 2)}%` }}
              />
            </div>
          ) : null}
        </div>

        <div className="flex w-32 shrink-0 items-center justify-end gap-2">
          {run.status === "complete" ? (
            <CheckCircle2 className="size-4 text-profit" />
          ) : run.status === "failed" ? (
            <AlertCircle className="size-4 text-loss" />
          ) : null}
          {/* A real anchor, not a button + callback: this opens in its
              own tab (target="_blank"), matching every other "view an
              existing run" action, so the running list here is never
              replaced by the report it opens. Styled to match Button's
              outline variant directly rather than making that shared
              primitive polymorphic for one caller. */}
          <a
            href={runUrl(run.run_id)}
            target="_blank"
            rel="noopener noreferrer"
            className={cn(
              "inline-flex h-7 items-center justify-center gap-2 rounded-md px-2 text-xs font-medium",
              "border border-border bg-transparent transition-colors hover:bg-accent",
              "focus-visible:ring-2 focus-visible:ring-ring focus-visible:outline-none",
            )}
          >
            {running ? "Watch" : "Open"}
          </a>
        </div>
      </div>

      {summary ? (
        <div className="flex flex-wrap items-center gap-1.5 pl-[calc(6rem+1rem)] text-[11px] text-muted-foreground">
          <span>
            {summary.simulationCount} simulation{summary.simulationCount === 1 ? "" : "s"}
          </span>
          {summary.axes.map((axis) => (
            <Badge key={axis.key} className="text-[11px] font-normal">
              {axis.label}: {axis.values.length}
            </Badge>
          ))}
        </div>
      ) : null}
    </div>
  );
}
