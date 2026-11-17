import { useEffect, useState } from "react";

import { api } from "@/lib/api";
import { appendNewer, easternSession, lastSessions, newest } from "@/lib/journal";
import type { TraderFill } from "@/types/control";

export { easternSession } from "@/lib/journal";

// A tick books at most a handful of fills a minute.
const POLL_MS = 15_000;

/**
 * The fills a deployment's trader booked in its last `sessions` sessions,
 * polled, and the subset from today's session -- not merely the newest
 * session in its journal, which on a day with no fills yet is yesterday's.
 * The window is loaded once; each poll after asks only for newer fills
 * (lib/journal.ts), so a busy session is not downloaded again every time.
 */
export function useDeploymentFills(deploymentId: string | null, sessions: number) {
  const [fills, setFills] = useState<TraderFill[] | null>(null);
  const [today, setToday] = useState<TraderFill[] | null>(null);

  useEffect(() => {
    setFills(null);
    setToday(null);
    if (!deploymentId) return;
    const window_ = Math.max(sessions, 1);
    let cancelled = false;
    let held: TraderFill[] | null = null;
    const show = (rows: TraderFill[]) => {
      const session = easternSession(Date.now() / 1000);
      const ofToday = rows.filter((fill) => easternSession(fill.t) === session);
      setFills(rows); // the same array when nothing is new: no re-render
      // Today's subset can change with no new fill (the session rolled over).
      setToday((previous) =>
        previous && previous.length === ofToday.length && newest(previous) === newest(ofToday)
          ? previous
          : ofToday,
      );
    };
    const load = () => {
      const since = held ? newest(held) : undefined;
      api
        .deploymentFills(deploymentId, window_, since)
        .then((next) => {
          if (cancelled) return;
          held = held ? lastSessions(appendNewer(held, next), window_) : next;
          show(held);
        })
        .catch(() => {
          if (!cancelled && held === null) {
            setFills([]);
            setToday([]);
          }
        });
    };
    load();
    const timer = window.setInterval(load, POLL_MS);
    return () => {
      cancelled = true;
      window.clearInterval(timer);
    };
  }, [deploymentId, sessions]);

  return { fills, today };
}
