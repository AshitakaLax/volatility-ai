import { useEffect, useState } from "react";

/**
 * Date.now(), refreshed every `everyMs` while mounted: for times counted
 * from now -- "last heard 12 s ago" -- that should move between the
 * server's reports rather than jump at each.
 */
export function useNow(everyMs = 1000): number {
  const [now, setNow] = useState(() => Date.now());
  useEffect(() => {
    const timer = window.setInterval(() => setNow(Date.now()), everyMs);
    return () => window.clearInterval(timer);
  }, [everyMs]);
  return now;
}
