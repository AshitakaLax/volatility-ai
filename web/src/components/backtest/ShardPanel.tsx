import { Clock, Loader2, Pause, Play, Server, Trash2 } from "lucide-react";
import { useCallback, useEffect, useRef, useState, type ReactNode } from "react";

import { Badge, Button, Card, CardContent } from "@/components/ui/primitives";
import { ApiError, api } from "@/lib/api";
import {
  connLabel,
  describeSeen,
  scheduleLabel,
  shardActions,
  stateLabel,
  summarizeShards,
  sweepLabel,
  versionMismatch,
} from "@/lib/shards";
import { cn, runUrl } from "@/lib/utils";
import type { Shard, ShardList } from "@/types/backtest";

import { ShardScheduleDialog } from "./ShardScheduleDialog";

/**
 * The machines working the backtest queue, and a pause for each.
 *
 * One SWEEP (a queued run) is the unit of distribution: each shard claims
 * one, runs it on its own cores, and reports every finished configuration
 * back to the engine host. "local" is the engine host itself.
 *
 * ABOVE THE FORM, AND DELIBERATELY SMALL. It sat under the form first,
 * where the answer to "is my other machine connected?" was below a tall
 * parameter form and easy to miss entirely. It belongs where it is read:
 * before submitting, because what is connected decides where the sweep
 * runs. So it is one wrapping row of chips rather than a stacked list --
 * a handful of machines has to cost a line or two, not a screen.
 *
 * Pausing a shard is not pausing a run. The shard finishes the
 * configurations already in flight and hands its sweep back to the queue,
 * where the next free shard continues it from those results -- so pausing
 * one machine frees its CPU without stalling the sweep. To hold a sweep
 * itself, pause it in the run list further down.
 *
 * Polls, like ActiveRuns, and a little faster while anything is working or
 * a shard is not responding, since connection state is the thing this
 * panel exists to show.
 */

const ACTIVE_POLL_MS = 3000;
const IDLE_POLL_MS = 10000;

export function ShardPanel() {
  const [list, setList] = useState<ShardList | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);
  // An engine host that predates shards answers 404: render nothing.
  const [unsupported, setUnsupported] = useState(false);
  // One control at a time: "<name>:<op>" or "all".
  const [busy, setBusy] = useState<string | null>(null);
  // The shard whose lockout-window dialog is open, if any.
  const [editing, setEditing] = useState<Shard | null>(null);
  const refresh = useRef<() => void>(() => {});

  useEffect(() => {
    let cancelled = false;
    let timer: number | undefined;
    let generation = 0;

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
        .shards()
        .then((body) => {
          if (cancelled || mine !== generation) return;
          setList(body);
          setError(null);
          const lively = body.shards.some((shard) => shard.run !== null || shard.conn === "stale");
          schedule(lively ? ACTIVE_POLL_MS : IDLE_POLL_MS);
        })
        .catch((cause: unknown) => {
          if (cancelled || mine !== generation) return;
          if (cause instanceof ApiError && cause.status === 404) {
            setUnsupported(true);
            return;
          }
          setError(cause instanceof Error ? cause.message : String(cause));
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
  }, []);

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

  if (unsupported) return null;

  const shards = list?.shards ?? [];
  const summary = summarizeShards(shards);
  const remote = shards.filter((shard) => !shard.local).length;
  const allPaused = list?.paused ?? false;

  const title = list
    ? [
        `Shards · ${summary.online} of ${summary.total} connected`,
        summary.working ? `${summary.working} working` : null,
        summary.paused ? `${summary.paused} paused` : null,
        summary.lockedOut ? `${summary.lockedOut} locked out` : null,
      ]
        .filter(Boolean)
        .join(" · ")
    : "Shards";

  return (
    <Card>
      <CardContent className="flex flex-wrap items-center gap-x-3 gap-y-2 p-3">
        <span className="flex items-center gap-2 text-xs font-semibold">
          {summary.working > 0 ? (
            <Loader2 className="size-3.5 animate-spin" />
          ) : (
            <Server className="size-3.5" />
          )}
          {title}
        </span>

        {shards.map((shard) => (
          <ShardChip
            key={shard.name}
            shard={shard}
            mainCommit={list?.commit ?? null}
            busy={busy}
            onAction={(op) => {
              if (
                op === "forget" &&
                !window.confirm(`Remove the disconnected shard "${shard.name}" from the list?`)
              ) {
                return;
              }
              void perform(`${shard.name}:${op}`, () => api.controlShard(shard.name, { op }));
            }}
            onOpenSchedule={() => setEditing(shard)}
          />
        ))}

        <div className="ml-auto flex items-center gap-2">
          {error ? <Badge tone="loss">engine host unreachable</Badge> : null}
          {shards.length > 0 ? (
            <Button
              variant="outline"
              className="h-7 px-2 text-xs"
              disabled={busy !== null}
              onClick={() => void perform("all", () => api.setShardsPaused(!allPaused))}
              title={
                allPaused
                  ? "Let every shard take sweeps again"
                  : "Every shard stops taking sweeps; a running sweep goes back to the queue after its in-flight configurations"
              }
            >
              {busy === "all" ? (
                <Loader2 className="size-3.5 animate-spin" />
              ) : allPaused ? (
                <Play className="size-3.5" />
              ) : (
                <Pause className="size-3.5" />
              )}
              {allPaused ? "Resume all" : "Pause all"}
            </Button>
          ) : null}
        </div>

        {actionError ? (
          <p className="w-full rounded-md bg-loss/10 px-2 py-1 text-xs text-loss" role="alert">
            {actionError}
          </p>
        ) : null}

        {list && remote === 0 ? (
          <p className="w-full text-[11px] text-muted-foreground">
            Only this machine works the queue. Add one with{" "}
            <code className="rounded bg-secondary px-1 py-0.5 font-mono">
              python cli.py shard --name &lt;name&gt; --main &lt;this host&gt;
            </code>{" "}
            (this server must be started with{" "}
            <code className="rounded bg-secondary px-1 py-0.5 font-mono">--host 0.0.0.0</code> to be
            reachable).
          </p>
        ) : null}
        {error ? <p className="w-full text-[11px] text-muted-foreground">{error}</p> : null}
      </CardContent>

      {editing ? (
        <ShardScheduleDialog
          shard={editing}
          onClose={() => setEditing(null)}
          onSaved={() => refresh.current()}
        />
      ) : null}
    </Card>
  );
}

type ShardAction = "pause" | "resume" | "forget";

/**
 * One machine, on one line: a status dot, its name, what it is doing, and
 * its controls. A running shard shows the sweep (a link to it) with a
 * percentage and a hairline progress bar underneath; everything else --
 * host, cores, commit -- is in the tooltip rather than on screen, because
 * this strip sits above the form and must not push it down.
 */
function ShardChip({
  shard,
  mainCommit,
  busy,
  onAction,
  onOpenSchedule,
}: {
  shard: Shard;
  mainCommit: string | null;
  busy: string | null;
  onAction: (op: ShardAction) => void;
  onOpenSchedule: () => void;
}) {
  const actions = shardActions(shard);
  const mismatch = versionMismatch(shard, mainCommit);
  const percent = shard.run ? Math.round(shard.run.progress * 100) : 0;
  const scheduleText = scheduleLabel(shard.schedule);

  const control = (op: ShardAction, label: string, icon: ReactNode) => (
    <Button
      variant="ghost"
      className={cn("size-6 p-0", op === "forget" && "hover:text-loss")}
      title={label}
      aria-label={`${label} (${shard.name})`}
      disabled={busy !== null}
      onClick={() => onAction(op)}
    >
      {busy === `${shard.name}:${op}` ? <Loader2 className="size-3 animate-spin" /> : icon}
    </Button>
  );

  const tooltip = [
    stateLabel(shard.state),
    shard.local ? "this server" : shard.host,
    shard.cores ? `${shard.cores} cores` : null,
    shard.commit ? `${shard.commit}${shard.dirty ? " (modified)" : ""}` : null,
    connLabel(shard.conn),
    shard.conn === "online" ? null : `last heard ${describeSeen(shard.seen_s)}`,
    scheduleText
      ? `lockout ${scheduleText}${shard.schedule?.enabled ? "" : " (disabled)"}`
      : null,
    "click the name to set a lockout window",
  ]
    .filter(Boolean)
    .join(" · ");

  return (
    <span
      className={cn(
        "inline-flex flex-col gap-0.5 rounded-md border border-border px-2 py-1",
        shard.conn === "offline" && "opacity-60",
      )}
      title={tooltip}
    >
      <span className="flex items-center gap-1.5 text-xs">
        <span
          className={cn(
            "size-2 shrink-0 rounded-full",
            shard.conn === "online" && "bg-profit",
            shard.conn === "stale" && "bg-stuck",
            shard.conn === "offline" && "bg-muted-foreground/40",
          )}
          aria-hidden
        />
        <button
          type="button"
          className="font-medium underline-offset-2 hover:underline"
          title={`Set a lockout window for ${shard.name}`}
          onClick={onOpenSchedule}
        >
          {shard.name}
        </button>
        {scheduleText ? (
          <Clock
            className={cn(
              "size-3 shrink-0",
              shard.schedule?.enabled ? "text-stuck" : "text-muted-foreground/50",
            )}
            aria-hidden
          />
        ) : null}

        <span
          className={cn(
            "max-w-[22rem] truncate text-muted-foreground",
            (shard.state === "pausing" || shard.state === "locked_out") && "text-stuck",
          )}
        >
          {shard.conn === "offline"
            ? "disconnected"
            : shard.run
              ? null
              : shard.state === "paused"
                ? "paused"
                : shard.state === "locked_out"
                  ? "locked out"
                  : "idle"}
          {shard.run ? (
            <>
              <a
                href={runUrl(shard.run.id)}
                target="_blank"
                rel="noopener noreferrer"
                className="text-foreground underline-offset-2 hover:underline"
              >
                {sweepLabel(shard.run)}
              </a>
              <span className="tnum"> · {percent}%</span>
              {shard.state === "pausing" ? " · pausing" : ""}
            </>
          ) : null}
        </span>

        {mismatch ? (
          <Badge
            tone="loss"
            className="text-[10px] font-normal"
            title={`This shard runs ${shard.commit}; the engine host runs ${mainCommit}. Its results would come from a different engine.`}
          >
            version mismatch
          </Badge>
        ) : null}

        <span className="flex shrink-0 items-center">
          {actions.pause
            ? control(
                "pause",
                shard.run
                  ? "Pause: finish the configurations in flight, then hand the sweep to another shard"
                  : "Pause: take no more sweeps",
                <Pause className="size-3" />,
              )
            : null}
          {actions.resume ? control("resume", "Resume", <Play className="size-3" />) : null}
          {actions.forget
            ? control("forget", "Remove from the list", <Trash2 className="size-3" />)
            : null}
        </span>
      </span>

      {shard.run ? (
        <span className="block h-0.5 overflow-hidden rounded-full bg-secondary">
          <span
            className={cn(
              "block h-full transition-all duration-500",
              shard.state === "pausing" ? "bg-stuck" : "bg-primary",
            )}
            style={{ width: `${Math.max(percent, 2)}%` }}
          />
        </span>
      ) : null}
    </span>
  );
}
