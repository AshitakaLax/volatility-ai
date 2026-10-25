import { History } from "lucide-react";
import { useCallback, useState } from "react";

import { Button } from "@/components/ui/primitives";
import { usePolled } from "@/hooks/usePolled";
import { api } from "@/lib/api";
import type { Tone } from "@/lib/control";
import { timeline } from "@/lib/fidelity";
import { cn } from "@/lib/utils";

/**
 * The bridge host's journal for the last two days, newest first: the
 * extension connecting and disconnecting (and how long it was gone), being
 * turned away and why, Fidelity signing in and out, the trading switch,
 * each session's loop attaching and leaving, readiness changing, account
 * checks. A disconnect explains itself after the fact here.
 */
const POLL_MS = 15_000;
const FIRST = 12;

const DOT: Record<Tone, string> = {
  neutral: "bg-muted-foreground/50",
  profit: "bg-profit",
  loss: "bg-loss",
  stuck: "bg-stuck",
};

function when(seconds: number): string {
  return new Date(seconds * 1000).toLocaleString([], {
    weekday: "short",
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
  });
}

export function ConnectionTimeline({ deploymentId }: { deploymentId: string }) {
  const load = useCallback(() => api.bridgeEvents(deploymentId, 48), [deploymentId]);
  const events = usePolled(load, POLL_MS);
  const [all, setAll] = useState(false);
  const rows = timeline(events.data ?? []);
  const shown = all ? rows : rows.slice(0, FIRST);

  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between gap-2">
        <h3 className="flex items-center gap-1.5 text-xs font-medium text-muted-foreground">
          <History className="size-3.5" aria-hidden />
          Connection timeline, last 48 hours
        </h3>
        {events.error ? <span className="text-xs text-loss">{events.error}</span> : null}
      </div>
      {events.data && rows.length === 0 ? (
        <p className="text-xs text-muted-foreground">
          Nothing recorded yet: the bridge host writes here once it runs.
        </p>
      ) : (
        <ol className="space-y-1">
          {shown.map((row) => (
            <li key={`${row.t}-${row.kind}`} className="flex items-baseline gap-2 text-xs">
              <span className={cn("mt-1 size-2 shrink-0 rounded-full", DOT[row.tone])} aria-hidden />
              <span className="w-36 shrink-0 font-mono text-muted-foreground tabular-nums">
                {when(row.t)}
              </span>
              <span className="min-w-0">
                {row.text}
                {row.span ? <span className="text-muted-foreground"> ({row.span})</span> : null}
              </span>
            </li>
          ))}
        </ol>
      )}
      {rows.length > FIRST ? (
        <Button variant="ghost" className="h-7 px-2 text-xs" onClick={() => setAll(!all)}>
          {all ? "Show the latest only" : `Show all ${rows.length}`}
        </Button>
      ) : null}
    </div>
  );
}
