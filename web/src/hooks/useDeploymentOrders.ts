import { useEffect, useState } from "react";

import { api } from "@/lib/api";
import { appendNewer, easternSession, newest } from "@/lib/journal";
import type { OrderEvent } from "@/types/control";

// An order's life moves on a minute's tick.
const POLL_MS = 15_000;

/** Today's order events for a deployment (its trader's orders journal),
 * polled: loaded once, then only the events after the newest held. */
export function useDeploymentOrders(deploymentId: string | null) {
  const [events, setEvents] = useState<OrderEvent[] | null>(null);

  useEffect(() => {
    setEvents(null);
    if (!deploymentId) return;
    let cancelled = false;
    let held: OrderEvent[] | null = null;
    const load = () => {
      const since = held ? newest(held) : undefined;
      api
        .deploymentOrders(deploymentId, 1, since)
        .then((next) => {
          if (cancelled) return;
          const today = easternSession(Date.now() / 1000);
          const merged = held ? appendNewer(held, next) : next;
          const ofToday = merged.filter((event) => easternSession(event.t) === today);
          // The same array when nothing is new and the session has not rolled over.
          held = ofToday.length === merged.length ? merged : ofToday;
          setEvents(held);
        })
        .catch(() => {
          if (!cancelled && held === null) setEvents([]);
        });
    };
    load();
    const timer = window.setInterval(load, POLL_MS);
    return () => {
      cancelled = true;
      window.clearInterval(timer);
    };
  }, [deploymentId]);

  return events;
}
