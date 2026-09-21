import {
  AlertCircle,
  Ban,
  CheckCircle2,
  ChevronDown,
  ChevronRight,
  ChevronUp,
  ChevronsUp,
  Layers,
  Loader2,
  Pause,
  Play,
  Timer,
  X,
} from "lucide-react";
import { useCallback, useEffect, useRef, useState, type ReactNode } from "react";

import { Badge, Button, Card, CardContent, CardHeader, CardTitle } from "@/components/ui/primitives";
import { api } from "@/lib/api";
import { describeRequestAxes } from "@/lib/requestSummary";
import {
  availableActions,
  isActive,
  moveTarget,
  isRunning,
  queuePositions,
  type QueuePosition,
} from "@/lib/runQueue";
import {
  batchCounts,
  batchProgress,
  groupByBatch,
  isBatch,
  itemIsActive,
  orderActiveItems,
  type RunBatch,
} from "@/lib/runBatches";
import { cn, runUrl } from "@/lib/utils";
import type { Run } from "@/types/backtest";

/**
 * Backtests in flight, and the controls to steer them.
 *
 * WHY THIS EXISTS. useBacktestRun tracks the run THIS tab submitted. A
 * fresh page load knew about none of them -- so refreshing during a
 * sweep, or opening the dashboard on a second machine, showed an idle
 * page while the engine was busy. The runs were there the whole time;
 * nothing asked.
 *
 * WHY IT NOW HAS CONTROLS. tools/sweep_rsp_all.py queues 84 runs that
 * take days, and a queue that long needs steering: pause one to let
 * something urgent through, move a slice of the sweep to the front,
 * cancel a strategy whose early chunks already answered the question,
 * pause everything before restarting the machine. Every control here
 * maps to one server/jobs.py transition, and lib/runQueue.ts decides
 * which are offered so the page never shows a button the server would
 * refuse.
 *
 * It polls rather than subscribing. A websocket per run would mean
 * opening and closing sockets as jobs come and go, to learn the same
 * thing one cheap request answers for all of them at once. After any
 * control it re-polls at once, so the effect shows without a two-second
 * lag.
 *
 * POLLING SLOWS WHEN NOTHING IS WORKING -- nothing running, nothing
 * queued behind an unpaused queue. An idle dashboard left open overnight
 * should not make a request every two seconds until morning.
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

type RunAction = "pause" | "resume" | "cancel" | "runNext" | "moveUp" | "moveDown";

export function ActiveRuns({ onSettled }: Props) {
  const [runs, setRuns] = useState<Run[]>([]);
  const [queuePaused, setQueuePaused] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);
  // One control at a time: "<run_id>:<action>" or "queue".
  const [busy, setBusy] = useState<string | null>(null);
  const refresh = useRef<() => void>(() => {});

  useEffect(() => {
    let cancelled = false;
    let timer: number | undefined;
    // Each poll takes a generation; a response to anything but the latest
    // is dropped. Without it, a control's immediate re-poll racing a
    // scheduled one would start two polling loops that never merge.
    let generation = 0;
    // Tracked so a run that finishes between polls still notifies once,
    // rather than the caller having to diff the list itself.
    let previouslyActive = new Set<string>();

    const schedule = (ms: number) => {
      timer = window.setTimeout(tick, ms);
    };

    function tick() {
      const mine = ++generation;
      if (timer !== undefined) {
        window.clearTimeout(timer);
        timer = undefined;
      }
      api
        .runs()
        .then((body) => {
          if (cancelled || mine !== generation) return;
          const paused = body.paused;
          setRuns(body.runs);
          setQueuePaused(paused);
          setError(null);

          const active = new Set(
            body.runs.filter((run) => isActive(run.status)).map((run) => run.id),
          );
          const justFinished = [...previouslyActive].some((id) => !active.has(id));
          previouslyActive = active;
          if (justFinished) onSettled?.();

          const working = body.runs.some(
            (run) => isRunning(run.status) || (run.status === "queued" && !paused),
          );
          schedule(working ? ACTIVE_POLL_MS : IDLE_POLL_MS);
        })
        .catch((cause: unknown) => {
          if (cancelled || mine !== generation) return;
          setError(cause instanceof Error ? cause.message : String(cause));
          // Keep trying, slowly. The engine host being down is a state
          // to recover from, not a reason to stop looking.
          schedule(IDLE_POLL_MS);
        });
    }

    refresh.current = tick;
    tick();
    return () => {
      cancelled = true;
      refresh.current = () => {};
      if (timer !== undefined) window.clearTimeout(timer);
    };
  }, [onSettled]);

  const perform = useCallback(async (key: string, call: () => Promise<unknown>) => {
    setBusy(key);
    setActionError(null);
    try {
      await call();
    } catch (cause) {
      setActionError(cause instanceof Error ? cause.message : String(cause));
    } finally {
      setBusy(null);
      refresh.current();
    }
  }, []);

  const positions = queuePositions(runs);
  // Grouped by batch_id before active/recent are split out -- a batch
  // straddling both (some chunks done, some not) would otherwise have
  // its terminal chunks compete with unrelated runs for "recent"'s 3
  // slots one chunk at a time, instead of as the one thing it is.
  const grouped = groupByBatch(runs);
  const active = orderActiveItems(grouped, positions);
  const recent = grouped.filter((item) => !itemIsActive(item)).slice(0, 3);

  const onAction = (run: Run, action: RunAction) => {
    const label = runLabel(run) ?? run.id;
    const position = positions.get(run.id);
    const calls: Record<RunAction, () => Promise<unknown>> = {
      pause: () => api.controlRun(run.id, { op: "pause" }),
      resume: () => api.controlRun(run.id, { op: "resume" }),
      cancel: () => api.controlRun(run.id, { op: "cancel" }),
      runNext: () => api.controlRun(run.id, { op: "next" }),
      moveUp: () =>
        api.controlRun(run.id, { op: "move", pos: position ? moveTarget(position, "up") : 0 }),
      moveDown: () =>
        api.controlRun(run.id, { op: "move", pos: position ? moveTarget(position, "down") : 0 }),
    };
    if (action === "cancel") {
      const losesProgress = run.status === "running" || run.status === "paused";
      const confirmed = window.confirm(
        losesProgress
          ? `Cancel "${label}"? The configurations it has finished will be discarded. This can't be undone.`
          : `Cancel "${label}"? It will be removed from the queue.`,
      );
      if (!confirmed) return;
    }
    void perform(`${run.id}:${action}`, calls[action]);
  };

  // Per CHUNK, not per card -- a 7-chunk batch with 3 running should say
  // so, even though it renders as one card in the list below.
  const running = runs.filter((run) => run.status === "running").length;
  const queued = runs.filter((run) => run.status === "queued").length;
  const paused = runs.filter((run) => run.status === "paused").length;

  // Nothing active and nothing recent is the ordinary state, and an
  // empty card saying "no runs" every time is noise. A paused queue is
  // not ordinary: it will silently start nothing, so it always shows.
  if (active.length === 0 && recent.length === 0 && !error && !queuePaused) return null;

  const counts = [
    running ? `${running} running` : null,
    queued ? `${queued} queued` : null,
    paused ? `${paused} paused` : null,
  ].filter(Boolean);

  return (
    <Card>
      <CardHeader className="flex-row flex-wrap items-center justify-between gap-2">
        <CardTitle className="flex items-center gap-2">
          {running > 0 && !queuePaused ? (
            <Loader2 className="size-4 animate-spin" />
          ) : (
            <Timer className="size-4" />
          )}
          {counts.length > 0 ? `Backtests · ${counts.join(" · ")}` : "Recent runs"}
        </CardTitle>
        <div className="flex items-center gap-2">
          {error ? <Badge tone="loss">engine host unreachable</Badge> : null}
          {queuePaused ? <Badge tone="stuck">queue paused</Badge> : null}
          {active.length > 0 || queuePaused ? (
            <Button
              variant="outline"
              className="h-7 px-2 text-xs"
              disabled={busy !== null}
              onClick={() =>
                void perform("queue", () => api.setQueuePaused(!queuePaused))
              }
              title={
                queuePaused
                  ? "Start runs again, resuming whatever pausing the queue paused"
                  : "Start no new runs; the running one pauses after its in-flight configurations"
              }
            >
              {queuePaused ? <Play className="size-3.5" /> : <Pause className="size-3.5" />}
              {queuePaused ? "Resume queue" : "Pause queue"}
            </Button>
          ) : null}
        </div>
      </CardHeader>

      <CardContent className="space-y-3">
        {actionError ? (
          <p className="rounded-md bg-loss/10 px-2 py-1 text-xs text-loss" role="alert">
            {actionError}
          </p>
        ) : null}
        {/* Scrolls inside itself: a sweep series is dozens of runs, and the
            parameter form below should not be pushed off the page by it. */}
        <div className="max-h-[36rem] space-y-3 overflow-y-auto pr-1">
          {[...active, ...recent].map((item) =>
            isBatch(item) ? (
              <BatchRow
                key={item.batchId}
                batch={item}
                positions={positions}
                queuePaused={queuePaused}
                busy={busy}
                onAction={onAction}
              />
            ) : (
              <RunRow
                key={item.id}
                run={item}
                position={positions.get(item.id)}
                queuePaused={queuePaused}
                busy={busy}
                onAction={(action) => onAction(item, action)}
              />
            ),
          )}
        </div>
        {error ? <p className="text-xs text-muted-foreground">{error}</p> : null}
      </CardContent>
    </Card>
  );
}

function runLabel(run: Run): string | null {
  return (
    run.req.name?.trim() || `${run.req.model ?? "fixed"} · ${run.req.tickers.join(", ")}`
  );
}

function statusText(
  run: Run,
  position: QueuePosition | undefined,
  queuePaused: boolean,
): string {
  const place = position
    ? position.position === 1
      ? "next up"
      : `position ${position.position} of ${position.of}`
    : null;
  switch (run.status) {
    case "queued": {
      const parts = ["queued", place, queuePaused ? "waiting for the queue to resume" : null];
      // A run interrupted by a restart or resumed after a pause picks up
      // from its checkpoint, which is worth saying -- it will not start over.
      if (run.msg && /resum/i.test(run.msg)) parts.push("resumes where it stopped");
      return parts.filter(Boolean).join(" — ");
    }
    case "paused":
      return ["paused", place].filter(Boolean).join(" — ");
    case "cancelled":
      return "cancelled";
    default:
      return run.msg ?? run.status;
  }
}

function RunRow({
  run,
  position,
  queuePaused,
  busy,
  onAction,
}: {
  run: Run;
  /** This run's place among pending jobs, or undefined when it isn't pending. */
  position: QueuePosition | undefined;
  queuePaused: boolean;
  busy: string | null;
  onAction: (action: RunAction) => void;
}) {
  const active = isActive(run.status);
  const percent = Math.round(run.progress * 100);
  const actions = availableActions(run, position);
  const label = runLabel(run);

  // One JOB already IS one sweep -- grouping means describing what THIS
  // job covers, not merging several jobs together. Only computable when
  // the snapshot carries the submitted request.
  const summary = describeRequestAxes(run.req);

  const control = (action: RunAction, title: string, icon: ReactNode) => (
    <Button
      variant="ghost"
      className={cn("size-7 p-0", action === "cancel" && "hover:text-loss")}
      title={title}
      aria-label={title}
      disabled={busy !== null}
      onClick={() => onAction(action)}
    >
      {busy === `${run.id}:${action}` ? <Loader2 className="size-3.5 animate-spin" /> : icon}
    </Button>
  );

  return (
    <div className="flex flex-col gap-1">
      <div className="flex items-center gap-2">
        {/* Where it sits, at a glance -- the thing reordering changes. */}
        <span
          className={cn(
            "tnum w-8 shrink-0 text-center text-[11px] font-medium",
            run.status === "running" ? "text-primary" : "text-muted-foreground",
          )}
        >
          {run.status === "running" ? "now" : position ? `#${position.position}` : ""}
        </span>

        {/* Full width for the name: a sweep series differs only in its
            "[3/16]" suffix, and a truncated label cannot be reordered by. */}
        <span
          className="min-w-0 flex-1 truncate text-xs"
          title={label ? `${label} · ${run.id}` : run.id}
        >
          {label ? (
            <span className="text-foreground">{label}</span>
          ) : (
            <span className="font-mono text-muted-foreground">{run.id.slice(0, 10)}</span>
          )}
        </span>

        {/* Which machine has it -- sweeps run on shards (see ShardPanel). */}
        {run.shard && isRunning(run.status) ? (
          <Badge className="shrink-0 text-[11px] font-normal" title={`Running on shard ${run.shard}`}>
            {run.shard}
          </Badge>
        ) : null}

        <div className="flex shrink-0 items-center gap-0.5">
          {actions.runNext ? control("runNext", "Run next", <ChevronsUp className="size-3.5" />) : null}
          {actions.moveUp ? control("moveUp", "Move up", <ChevronUp className="size-3.5" />) : null}
          {actions.moveDown ? control("moveDown", "Move down", <ChevronDown className="size-3.5" />) : null}
          {actions.pause
            ? control(
                "pause",
                run.status === "running" ? "Pause after the in-flight configurations" : "Pause",
                <Pause className="size-3.5" />,
              )
            : null}
          {actions.resume ? control("resume", "Resume", <Play className="size-3.5" />) : null}
          {actions.cancel ? control("cancel", "Cancel", <X className="size-3.5" />) : null}

          {run.status === "complete" ? (
            <CheckCircle2 className="mx-1 size-4 text-profit" />
          ) : run.status === "failed" ? (
            <AlertCircle className="mx-1 size-4 text-loss" />
          ) : run.status === "cancelled" ? (
            <Ban className="mx-1 size-4 text-muted-foreground" />
          ) : null}
          {/* A real anchor, not a button + callback: this opens in its
              own tab (target="_blank"), matching every other "view an
              existing run" action, so the running list here is never
              replaced by the report it opens. */}
          <a
            href={runUrl(run.id)}
            target="_blank"
            rel="noopener noreferrer"
            className={cn(
              "ml-1 inline-flex h-7 items-center justify-center gap-2 rounded-md px-2 text-xs font-medium",
              "border border-border bg-transparent transition-colors hover:bg-accent",
              "focus-visible:ring-2 focus-visible:ring-ring focus-visible:outline-none",
            )}
          >
            {active ? "Watch" : "Open"}
          </a>
        </div>
      </div>

      <div className="pl-10">
        <div className="flex items-center justify-between gap-2 text-xs">
          <span
            className={cn(
              run.status === "failed" && "text-loss",
              (run.status === "pausing" || run.status === "cancelling") && "text-stuck",
              run.status === "paused" && "text-muted-foreground",
            )}
          >
            {statusText(run, position, queuePaused)}
          </span>
          {active && percent > 0 ? <span className="tnum text-muted-foreground">{percent}%</span> : null}
        </div>
        {active ? (
          <div className="mt-1 h-1.5 overflow-hidden rounded-full bg-secondary">
            <div
              className={cn(
                "h-full transition-all duration-500",
                run.status === "paused" ? "bg-muted-foreground/40" : "bg-primary",
                // A queued run with no progress is waiting, not working, and
                // should not show a bar creeping forward. One resuming from
                // a checkpoint shows where it will pick up instead.
                run.status === "queued" && percent === 0 && !queuePaused && "animate-pulse",
              )}
              style={{
                width: `${run.status === "queued" && percent === 0 ? 100 : Math.max(percent, 2)}%`,
              }}
            />
          </div>
        ) : null}

        {summary ? (
          <div className="mt-1 flex flex-wrap items-center gap-1.5 text-[11px] text-muted-foreground">
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
    </div>
  );
}

/**
 * One batch: a sweep too large for one submission, bisected server-side
 * into independent chunks that share a batch_id (server/backtest.py
 * bisect_request). Collapsed to a single card with rolled-up progress by
 * default -- an operator steering the queue thinks of it as one sweep,
 * the same way they submitted it -- with every chunk's own RunRow, and
 * its own controls, one click away.
 */
function BatchRow({
  batch,
  positions,
  queuePaused,
  busy,
  onAction,
}: {
  batch: RunBatch;
  positions: Map<string, QueuePosition>;
  queuePaused: boolean;
  busy: string | null;
  onAction: (run: Run, action: RunAction) => void;
}) {
  const [expanded, setExpanded] = useState(false);
  const active = itemIsActive(batch);
  const percent = Math.round(batchProgress(batch) * 100);
  const label = runLabel(batch.runs[0]!);
  // Bisection only ever splits one chunk's swept values into two --
  // summing each chunk's own count recovers the original total exactly.
  const totalSimulations = batch.runs.reduce(
    (sum, run) => sum + describeRequestAxes(run.req).simulationCount,
    0,
  );
  const counts = batchCounts(batch);
  const summary = (Object.entries(counts) as [Run["status"], number][])
    .filter(([, count]) => count > 0)
    .map(([status, count]) => `${count} ${status}`)
    .join(", ");

  return (
    <div className="flex flex-col gap-1 rounded-md border border-border/60 p-2">
      <div className="flex items-center gap-2">
        <button
          type="button"
          onClick={() => setExpanded((value) => !value)}
          className="flex size-6 shrink-0 items-center justify-center text-muted-foreground hover:text-foreground"
          aria-label={expanded ? "Collapse batch" : "Expand batch"}
          aria-expanded={expanded}
        >
          {expanded ? (
            <ChevronDown className="size-3.5" />
          ) : (
            <ChevronRight className="size-3.5" />
          )}
        </button>
        <Layers className="size-3.5 shrink-0 text-muted-foreground" />
        <span
          className="min-w-0 flex-1 truncate text-xs"
          title={`${label} · batch ${batch.batchId}`}
        >
          <span className="text-foreground">{label}</span>
        </span>
        <Badge className="shrink-0 text-[11px] font-normal">{batch.runs.length} runs</Badge>
      </div>

      <div className="pl-8">
        <div className="flex items-center justify-between gap-2 text-xs">
          <span className="text-muted-foreground">{summary}</span>
          {active && percent > 0 ? (
            <span className="tnum text-muted-foreground">{percent}%</span>
          ) : null}
        </div>
        {active ? (
          <div className="mt-1 h-1.5 overflow-hidden rounded-full bg-secondary">
            <div
              className="h-full bg-primary transition-all duration-500"
              style={{ width: `${Math.max(percent, 2)}%` }}
            />
          </div>
        ) : null}
        <div className="mt-1 text-[11px] text-muted-foreground">
          {totalSimulations} simulation{totalSimulations === 1 ? "" : "s"} total across{" "}
          {batch.runs.length} runs
        </div>
      </div>

      {expanded ? (
        <div className="mt-1 flex flex-col gap-2 border-l border-border/60 py-1 pl-3">
          {batch.runs.map((run) => (
            <RunRow
              key={run.id}
              run={run}
              position={positions.get(run.id)}
              queuePaused={queuePaused}
              busy={busy}
              onAction={(action) => onAction(run, action)}
            />
          ))}
        </div>
      ) : null}
    </div>
  );
}
