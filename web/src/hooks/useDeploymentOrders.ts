import { useEffect, useState } from "react";

import { api } from "@/lib/api";
import { easternSession } from "@/hooks/useDeploymentFills";
import type { OrderEvent } from "@/types/control";

// An order's life moves on a minute's tick.
const POLL_MS = 15_000;

/** Today's order events for a deployment (its trader's orders journal), polled. */
export function useDeploymentOrders(deploymentId: string | null) {
  const [events, setEvents] = useState<OrderEvent[] | null>(null);

  useEffect(() => {
    setEvents(null);
    if (!deploymentId) return;
    let cancelled = false;
    const load = () => {
      api
        .deploymentOrders(deploymentId, 1)
        .then((next) => {
          if (cancelled) return;
          const today = easternSession(Date.now() / 1000);
          setEvents(next.filter((event) => easternSession(event.t) === today));
        })
        .catch(() => {
          if (!cancelled) setEvents([]);
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
