import { useEffect, useState } from "react";

import { api } from "@/lib/api";
import type { Candle } from "@/lib/filters";
import type { BarSeries } from "@/types/backtest";

/**
 * Real OHLC for a window, from the server.
 *
 * The server downsamples: a ten-year minute file is a million rows and
 * roughly 60 MB, and no browser should be asked to parse that to draw a
 * few thousand pixels. What comes back is proper OHLC aggregation, not
 * every Nth row -- under the engine's "intrabar" fill model a level
 * TOUCHED during a bar is a fill, so dropping the extremes would leave
 * markers hanging off candles that never reached them.
 *
 * Returns null (not an empty array) before the first response, so a
 * caller can tell "loading" from "this window genuinely has no bars".
 */
export function usePriceBars(
  ticker: string | null,
  start: string | null,
  end: string | null,
  maxPoints?: number,
): { candles: Candle[] | null; meta: Omit<BarSeries, "bars"> | null; error: string | null } {
  const [candles, setCandles] = useState<Candle[] | null>(null);
  const [meta, setMeta] = useState<Omit<BarSeries, "bars"> | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!ticker) {
      setCandles(null);
      setMeta(null);
      return;
    }
    let cancelled = false;
    setCandles(null);
    setError(null);

    api
      .bars(ticker, start, end, maxPoints)
      .then((series) => {
        // A stale response from a previous ticker must not overwrite the
        // current one -- the user can change funds faster than a 60 MB
        // file is read.
        if (cancelled) return;
        setCandles(series.bars);
        setMeta({
          ticker: series.ticker,
          bucket_seconds: series.bucket_seconds,
          source_rows: series.source_rows,
        });
      })
      .catch((cause: unknown) => {
        if (cancelled) return;
        setError(cause instanceof Error ? cause.message : String(cause));
        setCandles([]);
      });

    return () => {
      cancelled = true;
    };
  }, [ticker, start, end, maxPoints]);

  return { candles, meta, error };
}
