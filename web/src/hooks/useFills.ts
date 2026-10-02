import { useEffect, useState } from "react";

import { api } from "@/lib/api";
import type { Fill, FillsPage, FillsQuery } from "@/types/backtest";

/** Which run's fund to read fills from. */
export interface FillsSource {
  runId: string;
  ticker: string;
}

/**
 * One page of a fund's fills (or cycles) from GET /runs/{id}/fills.
 *
 * Reports no longer carry fills inline, so the chart, the trade log and
 * the filter counts each ask for exactly what they show. `params: null`
 * (or no source) means "nothing to ask for" -- e.g. a collapsed trade log.
 *
 * Keyed by the serialised request, and a response to anything but the
 * latest is dropped: switching funds or filters faster than a page lands
 * must never paint the previous request's rows over the current one.
 */
export function useFills<Row = Fill>(
  source: FillsSource | null,
  params: Omit<FillsQuery, "ticker"> | null,
): { page: FillsPage<Row> | null; error: string | null; loading: boolean } {
  const [page, setPage] = useState<FillsPage<Row> | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const key = source && params ? JSON.stringify({ ...source, params }) : null;

  useEffect(() => {
    if (!key) {
      setPage(null);
      setLoading(false);
      return;
    }
    const request = JSON.parse(key) as FillsSource & { params: Omit<FillsQuery, "ticker"> };
    let cancelled = false;
    // Cleared, not kept: the previous rows belong to a different request
    // (another fund, window or page) and showing them while this one loads
    // is exactly the "table didn't clear" bug Run History once had.
    setPage(null);
    setLoading(true);
    setError(null);
    api
      .fills<Row>(request.runId, { ...request.params, ticker: request.ticker })
      .then((body) => {
        if (!cancelled) setPage(body);
      })
      .catch((cause: unknown) => {
        if (cancelled) return;
        setError(cause instanceof Error ? cause.message : String(cause));
        setPage(null);
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [key]);

  return { page, error, loading };
}
