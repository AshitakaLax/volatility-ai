import { useCallback, useEffect, useState } from "react";

import { api } from "@/lib/api";
import type { DeploymentState } from "@/types/telemetry";

import { useWebSocket } from "./useWebSocket";

interface LiveFrame {
  type: "state" | "heartbeat" | "error";
  state?: DeploymentState;
  detail?: string;
}

/**
 * One deployment's state, kept current over a socket.
 *
 * Fetches once immediately as well as subscribing. The socket sends on
 * connect, but the fetch means the page has something to draw during the
 * handshake -- and outside market hours a deployment can be quiet for
 * sixteen hours, so "wait for the first push" is not a strategy.
 *
 * READ-ONLY BY CONSTRUCTION. Every path here is a GET or a socket the
 * server only ever writes to; there is no mutation in this hook. The
 * halt lives in CommandCenter, on its own explicit call.
 */
export function useLiveState(path: string | null) {
  const [state, setState] = useState<DeploymentState | null>(null);
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(() => {
    if (!path) return;
    api
      .liveState(path)
      .then((next) => {
        setState(next);
        setError(null);
      })
      .catch((cause: unknown) => setError(cause instanceof Error ? cause.message : String(cause)));
  }, [path]);

  useEffect(refresh, [refresh]);

  const health = useWebSocket<LiveFrame>(
    path ? `ws://${window.location.host}/api/live/ws?path=${encodeURIComponent(path)}` : null,
    (frame) => {
      if (frame.type === "state" && frame.state) {
        setState(frame.state);
        setError(null);
      } else if (frame.type === "error" && frame.detail) {
        setError(frame.detail);
      }
      // A heartbeat carries no data by design -- it exists so a client
      // can tell "nothing changed" from "this connection is dead".
    },
  );

  return { state, error, health, refresh };
}
