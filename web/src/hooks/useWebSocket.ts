import { useCallback, useEffect, useRef, useState } from "react";

import type { ConnectionHealth } from "@/types/telemetry";

/**
 * A WebSocket that reconnects, with observable health.
 *
 * WHY THE BACKOFF IS CAPPED AND JITTERED. An unbounded backoff leaves a
 * tab silently dead after a laptop wakes; an uncapped-but-fixed retry
 * from several open tabs hits the server in lockstep every time it
 * restarts. Doubling to a 15s ceiling with jitter avoids both.
 *
 * WHY `url === null` IS A FIRST-CLASS STATE. The caller often does not
 * know what to connect to yet -- no store selected, no run submitted --
 * and a hook that demanded a string would force a placeholder URL that
 * fails to connect and pollutes the retry counter.
 */
export function useWebSocket<T>(
  url: string | null,
  onMessage: (message: T) => void,
): ConnectionHealth {
  const [health, setHealth] = useState<ConnectionHealth>({
    status: "closed",
    retries: 0,
    lastMessageAt: null,
    latencyMs: null,
  });

  // The handler is held in a ref so a caller passing an inline arrow --
  // which every caller does -- does not tear down and rebuild the
  // socket on every render.
  const handler = useRef(onMessage);
  handler.current = onMessage;

  const socket = useRef<WebSocket | null>(null);
  const timer = useRef<number | null>(null);
  const attempt = useRef(0);
  const closing = useRef(false);

  const connect = useCallback((target: string) => {
    if (closing.current) return;
    setHealth((previous) => ({
      ...previous,
      status: attempt.current === 0 ? "connecting" : "reconnecting",
      retries: attempt.current,
    }));

    const ws = new WebSocket(target);
    socket.current = ws;

    ws.onopen = () => {
      attempt.current = 0;
      setHealth((previous) => ({ ...previous, status: "open", retries: 0 }));
    };

    ws.onmessage = (event: MessageEvent<string>) => {
      const receivedAt = Date.now();
      setHealth((previous) => ({
        ...previous,
        lastMessageAt: receivedAt,
        // Time since the previous frame. Not a true round trip -- the
        // server pushes rather than answering -- so it is reported as
        // the interval it actually is and named latencyMs only because
        // that is what a reader watches it for.
        latencyMs: previous.lastMessageAt === null ? null : receivedAt - previous.lastMessageAt,
      }));
      try {
        handler.current(JSON.parse(event.data) as T);
      } catch {
        // A malformed frame is not a reason to drop a live connection.
      }
    };

    ws.onerror = () => {
      setHealth((previous) => ({ ...previous, status: "error" }));
    };

    ws.onclose = () => {
      if (closing.current) {
        setHealth((previous) => ({ ...previous, status: "closed" }));
        return;
      }
      attempt.current += 1;
      const backoff = Math.min(15_000, 500 * 2 ** Math.min(attempt.current, 5));
      const jittered = backoff * (0.7 + Math.random() * 0.6);
      setHealth((previous) => ({
        ...previous,
        status: "reconnecting",
        retries: attempt.current,
      }));
      timer.current = window.setTimeout(() => connect(target), jittered);
    };
  }, []);

  useEffect(() => {
    if (!url) {
      setHealth({ status: "closed", retries: 0, lastMessageAt: null, latencyMs: null });
      return;
    }
    closing.current = false;
    attempt.current = 0;
    connect(url);

    return () => {
      // Closing deliberately must not schedule a reconnect, or a tab
      // navigating away leaves a timer resurrecting a dead socket.
      closing.current = true;
      if (timer.current !== null) window.clearTimeout(timer.current);
      socket.current?.close();
    };
  }, [url, connect]);

  return health;
}
