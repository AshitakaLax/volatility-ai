import { useCallback, useEffect, useRef, useState } from "react";

/**
 * A GET re-issued every `everyMs` while the component is mounted, and on
 * demand through `refresh`.
 *
 * The next poll is scheduled when the previous one ANSWERS, not on a fixed
 * interval: a slow answer (the warehouse's first bar scan takes seconds
 * while a sweep has every core) never stacks requests behind itself. An
 * answer that arrives after a newer request was issued, or after unmount,
 * is dropped. A failed poll keeps the last good data beside the error, so
 * a blip does not blank the page.
 */
export function usePolled<T>(load: () => Promise<T>, everyMs: number) {
  const [data, setData] = useState<T | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const refreshRef = useRef<() => void>(() => {});

  useEffect(() => {
    let cancelled = false;
    let timer: number | undefined;
    let generation = 0;

    function tick() {
      const mine = ++generation;
      if (timer !== undefined) window.clearTimeout(timer);
      timer = undefined;
      setLoading(true);
      load()
        .then((body) => {
          if (cancelled || mine !== generation) return;
          setData(body);
          setError(null);
        })
        .catch((cause: unknown) => {
          if (cancelled || mine !== generation) return;
          setError(cause instanceof Error ? cause.message : String(cause));
        })
        .finally(() => {
          if (cancelled || mine !== generation) return;
          setLoading(false);
          timer = window.setTimeout(tick, everyMs);
        });
    }

    refreshRef.current = tick;
    tick();
    return () => {
      cancelled = true;
      refreshRef.current = () => {};
      if (timer !== undefined) window.clearTimeout(timer);
    };
  }, [load, everyMs]);

  const refresh = useCallback(() => refreshRef.current(), []);
  return { data, error, loading, refresh };
}
