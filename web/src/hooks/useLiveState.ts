import { useCallback, useEffect, useState } from "react";

import { api } from "@/lib/api";
import type { Frame } from "@/types/backtest";
import type { DeploymentDetail } from "@/types/control";
import type { LiveState } from "@/types/telemetry";

import { useWebSocket } from "./useWebSocket";

// The trader's status and the commands' outcomes change without the ledger
// changing (a supervisor waiting for the open, a command applied that moved
// nothing), so they are polled; the ledger itself is pushed over the socket.
const DETAIL_POLL_MS = 5000;

/**
 * One deployment, by id: its ledger kept current over a socket, and its
 * summary -- run state, desired state, commands -- polled beside it.
 *
 * Fetches once immediately as well as subscribing. The socket sends on
 * connect, but the fetch means the page has something to draw during the
 * handshake -- and outside market hours a deployment can be quiet for
 * sixteen hours, so "wait for the first push" is not a strategy.
 *
 * Nothing here changes anything: commands are sent from the control bar,
 * and `refresh` is how it asks to see their outcome sooner.
 */
export function useLiveState(deploymentId: string | null) {
  const [detail, setDetail] = useState<DeploymentDetail | null>(null);
  const [state, setState] = useState<LiveState | null>(null);
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(() => {
    if (!deploymentId) return;
    api
      .deployment(deploymentId)
      .then((next) => {
        setDetail(next);
        setState(next.state);
        setError(null);
      })
      .catch((cause: unknown) => setError(cause instanceof Error ? cause.message : String(cause)));
  }, [deploymentId]);

  useEffect(() => {
    setDetail(null);
    setState(null);
    if (!deploymentId) return;
    refresh();
    const timer = window.setInterval(refresh, DETAIL_POLL_MS);
    return () => window.clearInterval(timer);
  }, [deploymentId, refresh]);

  const health = useWebSocket<Frame<LiveState>>(
    deploymentId
      ? `ws://${window.location.host}/api/live/ws?deployment=${encodeURIComponent(deploymentId)}`
      : null,
    (frame) => {
      if (frame.t === "data") {
        setState(frame.d);
        setError(null);
      } else if (frame.t === "err") {
        setError(frame.msg);
      }
      // A heartbeat carries no data by design -- it exists so a client
      // can tell "nothing changed" from "this connection is dead".
    },
  );

  return { state, detail, error, health, refresh };
}
