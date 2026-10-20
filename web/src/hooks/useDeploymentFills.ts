import { useEffect, useState } from "react";

import { api } from "@/lib/api";
import type { TraderFill } from "@/types/control";

// A tick books at most a handful of fills a minute.
const POLL_MS = 15_000;

/** The Eastern session date ("YYYY-MM-DD") an epoch-seconds time falls on --
 * how the trader's journal files its fills. */
export function easternSession(seconds: number): string {
  return new Date(seconds * 1000).toLocaleDateString("en-CA", { timeZone: "America/New_York" });
}

/**
 * The fills a deployment's trader booked in its last `sessions` sessions,
 * polled, and the subset from today's session -- not merely the newest
 * session in its journal, which on a day with no fills yet is yesterday's.
 */
export function useDeploymentFills(deploymentId: string | null, sessions: number) {
  const [fills, setFills] = useState<TraderFill[] | null>(null);
  const [today, setToday] = useState<TraderFill[] | null>(null);

  useEffect(() => {
    setFills(null);
    setToday(null);
    if (!deploymentId) return;
    let cancelled = false;
    const load = () => {
      api
        .deploymentFills(deploymentId, Math.max(sessions, 1))
        .then((next) => {
          if (cancelled) return;
          const session = easternSession(Date.now() / 1000);
          setFills(next);
          setToday(next.filter((fill) => easternSession(fill.t) === session));
        })
        .catch(() => {
          if (!cancelled) {
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
