import { useCallback, useState } from "react";

import { api, ApiError } from "@/lib/api";
import type { BacktestRunRequest, BacktestRunState } from "@/types/backtest";

import { useWebSocket } from "./useWebSocket";

interface RunFrame {
  type: "run" | "heartbeat" | "error";
  run?: BacktestRunState;
  detail?: string;
}

/**
 * Submit a backtest and follow it to completion.
 *
 * A run takes seconds to minutes, so the POST only queues it: the id
 * comes back immediately and progress arrives over a socket. That
 * asymmetry is the whole reason this is a hook rather than an awaited
 * call -- the component needs to render three different things (queued,
 * running with progress, complete) from one submission.
 */
export function useBacktestRun() {
  const [run, setRun] = useState<BacktestRunState | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const watching = run && (run.status === "queued" || run.status === "running");
  const health = useWebSocket<RunFrame>(
    watching ? `ws://${window.location.host}/api/backtest/ws/${run.run_id}` : null,
    (frame) => {
      if (frame.type === "run" && frame.run) setRun(frame.run);
      else if (frame.type === "error" && frame.detail) setError(frame.detail);
    },
  );

  /**
   * Follow a run this tab did not start.
   *
   * A page refresh mid-sweep, or a second machine opening the
   * dashboard, has no submission to hang state on -- but the run is
   * there and its socket works the same. Fetching the current state
   * first matters: a run that finished a second ago would otherwise
   * wait forever for an event that has already passed.
   */
  const attach = useCallback(async (runId: string) => {
    setError(null);
    try {
      setRun(await api.run(runId));
    } catch (cause) {
      setError(cause instanceof ApiError ? cause.message : String(cause));
    }
  }, []);

  const submit = useCallback(async (request: BacktestRunRequest) => {
    setSubmitting(true);
    setError(null);
    try {
      // Replaces any previous run rather than accumulating: the server
      // keeps the history, and a form that quietly queued a second run
      // because someone double-clicked would be a way to lose a machine
      // to a queue nobody asked for.
      setRun(await api.submitRun(request));
    } catch (cause) {
      setError(cause instanceof ApiError ? cause.message : String(cause));
      setRun(null);
    } finally {
      setSubmitting(false);
    }
  }, []);

  return { run, submit, attach, submitting, error, health };
}
