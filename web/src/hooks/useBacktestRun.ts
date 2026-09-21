import { useCallback, useState } from "react";

import { api, ApiError } from "@/lib/api";
import { isActive } from "@/lib/runQueue";
import type { Frame, Run, RunReq } from "@/types/backtest";

import { useWebSocket } from "./useWebSocket";

/** A submission too large for one Run, bisected server-side. There is no
 * single report to follow -- each chunk produces its own -- so this is
 * a name and a count, not something this hook watches. ActiveRuns'
 * own poll (which already covers every job regardless of origin) is
 * where the chunks are actually followed. */
export interface Batch {
  batchId: string;
  count: number;
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
  const [run, setRun] = useState<Run | null>(null);
  const [batch, setBatch] = useState<Batch | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const watching = run && isActive(run.status);
  const health = useWebSocket<Frame<Run>>(
    watching ? `ws://${window.location.host}/api/backtest/ws/${run.id}` : null,
    (frame) => {
      if (frame.t === "data") setRun(frame.d);
      else if (frame.t === "err") setError(frame.msg);
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

  const submit = useCallback(async (request: RunReq) => {
    setSubmitting(true);
    setError(null);
    setBatch(null);
    try {
      // Replaces any previous run rather than accumulating: the server
      // keeps the history, and a form that quietly queued a second run
      // because someone double-clicked would be a way to lose a machine
      // to a queue nobody asked for.
      const response = await api.submitRun(request);
      if ("batch_id" in response) {
        // Bisected into independent chunks -- nothing here is "the"
        // run to watch, so stop tracking one and name the batch instead.
        setRun(null);
        setBatch({ batchId: response.batch_id, count: response.runs.length });
      } else {
        setRun(response);
      }
    } catch (cause) {
      setError(cause instanceof ApiError ? cause.message : String(cause));
      setRun(null);
    } finally {
      setSubmitting(false);
    }
  }, []);

  return { run, batch, submit, attach, submitting, error, health };
}
