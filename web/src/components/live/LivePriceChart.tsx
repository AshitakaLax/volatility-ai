import {
  type CandlestickData,
  ColorType,
  type IChartApi,
  type ISeriesApi,
  type Time,
  createChart,
} from "lightweight-charts";
import { BarChart2 } from "lucide-react";
import { useEffect, useMemo, useRef, useState } from "react";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/primitives";
import { usePriceBars } from "@/hooks/usePriceBars";
import { aggregate } from "@/lib/filters";
import { cn } from "@/lib/utils";
import type { Timeframe } from "@/types/backtest";

/**
 * Configurable OHLC candlestick chart for the Live page.
 *
 * RANGE vs. BAR SIZE are independent. The range controls how far back the
 * fetch goes; the bar size controls how the server's 1-minute bars are
 * rolled up client-side. Both are in the toolbar.
 *
 * LIVE UPDATES. The WebSocket pushes `last_price` on every tick. Rather
 * than re-fetching, this component updates the final (in-progress) candle
 * in-place: if the current bar's bucket already exists in the series it is
 * updated; if not a new candle is appended. No backend work required.
 *
 * MAX_POINTS. Sized so the server never downsamples coarser than the
 * chosen bar increment. A 2-day fetch at 1-minute bars needs at most
 * 2 * 24 * 60 = 2880 points; handing the API that number guarantees it
 * won't pre-aggregate the data before we receive it.
 */

interface Props {
  /** The loop's trading symbol; null = no store selected / not yet known. */
  symbol: string | null;
  /** The loop's last observed price from the WebSocket state push. */
  lastPrice: number | null;
  /** ISO timestamp of the last tick — used to distinguish a new tick from a
   *  re-render with the same price. */
  lastPriceAt: string | null;
  height?: number;
}

// -------------------------------------------------------------------------
// Configuration tables
// -------------------------------------------------------------------------

type RangeDays = 1 | 2 | 5 | 10;

const RANGE_OPTIONS: { label: string; days: RangeDays }[] = [
  { label: "1D", days: 1 },
  { label: "2D", days: 2 },
  { label: "5D", days: 5 },
  { label: "10D", days: 10 },
];

type BarKey = "1m" | "5m" | "15m" | "1H" | "1D";

interface BarSpec {
  label: string;
  /** Seconds in one bar, for bucket math. */
  bucketSeconds: number;
  /** Timeframe string for the client-side `aggregate()` helper. */
  timeframe: Timeframe;
}

const BAR_OPTIONS: { key: BarKey; spec: BarSpec }[] = [
  { key: "1m",  spec: { label: "1m",  bucketSeconds: 60,      timeframe: "1Min" } },
  { key: "5m",  spec: { label: "5m",  bucketSeconds: 300,     timeframe: "5Min" } },
  { key: "15m", spec: { label: "15m", bucketSeconds: 900,     timeframe: "15Min" } },
  { key: "1H",  spec: { label: "1H",  bucketSeconds: 3600,    timeframe: "1Hour" } },
  { key: "1D",  spec: { label: "1D",  bucketSeconds: 86_400,  timeframe: "1Day" } },
];

const BAR_SPEC: Record<BarKey, BarSpec> = Object.fromEntries(
  BAR_OPTIONS.map(({ key, spec }) => [key, spec]),
) as Record<BarKey, BarSpec>;

// -------------------------------------------------------------------------

function buildStart(days: number): string {
  const ms = Date.now() - days * 24 * 60 * 60 * 1000;
  return new Date(ms).toISOString().slice(0, 10); // YYYY-MM-DD
}

function maxPointsFor(days: RangeDays, barKey: BarKey): number {
  const rangeMinutes = days * 24 * 60;
  const spec = BAR_SPEC[barKey];
  // Always request at least enough points that the server bucket won't
  // be coarser than our chosen bar size. +20% headroom for rounding.
  return Math.ceil((rangeMinutes * 60) / spec.bucketSeconds) + 100;
}

// -------------------------------------------------------------------------

export function LivePriceChart({ symbol, lastPrice, lastPriceAt, height = 400 }: Props) {
  const [rangeDays, setRangeDays] = useState<RangeDays>(2);
  const [barKey, setBarKey] = useState<BarKey>("1m");

  const start = useMemo(() => buildStart(rangeDays), [rangeDays]);
  const maxPoints = useMemo(() => maxPointsFor(rangeDays, barKey), [rangeDays, barKey]);

  const { candles, error } = usePriceBars(symbol, start, null, maxPoints);
  const loading = candles === null && !error;

  // Roll 1-minute server bars up to the selected bar size client-side.
  const rolledCandles = useMemo(() => {
    if (!candles) return null;
    return aggregate(candles, BAR_SPEC[barKey].timeframe);
  }, [candles, barKey]);

  // -----------------------------------------------------------------------
  // Chart refs
  // -----------------------------------------------------------------------

  const container = useRef<HTMLDivElement>(null);
  const chart = useRef<IChartApi | null>(null);
  const series = useRef<ISeriesApi<"Candlestick"> | null>(null);

  // -----------------------------------------------------------------------
  // Chart lifecycle — create once, destroy on unmount
  // -----------------------------------------------------------------------

  useEffect(() => {
    if (!container.current) return;

    const created = createChart(container.current, {
      height,
      layout: {
        background: { type: ColorType.Solid, color: "transparent" },
        // Literal rgba rather than CSS token — lightweight-charts parses a
        // limited colour grammar and throws on oklch(), taking the whole
        // view down with it. Same decision as BacktestChart.
        textColor: "rgba(140, 140, 150, 0.9)",
        fontFamily: "inherit",
      },
      grid: {
        vertLines: { color: "rgba(128,128,128,0.08)" },
        horzLines: { color: "rgba(128,128,128,0.08)" },
      },
      rightPriceScale: { borderVisible: false },
      timeScale: {
        borderVisible: false,
        timeVisible: true,
        secondsVisible: false,
      },
      crosshair: { mode: 0 },
    });

    const candleSeries = created.addCandlestickSeries({
      upColor: "#26a69a",
      downColor: "#ef5350",
      borderVisible: false,
      wickUpColor: "#26a69a",
      wickDownColor: "#ef5350",
    });

    chart.current = created;
    series.current = candleSeries;

    const resize = () => {
      if (!container.current) return;
      created.applyOptions({ width: container.current.clientWidth });
    };
    resize();
    window.addEventListener("resize", resize);

    return () => {
      window.removeEventListener("resize", resize);
      created.remove();
      chart.current = null;
      series.current = null;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [height]);

  // -----------------------------------------------------------------------
  // Data effect — re-run when historical candles or bar size changes
  // -----------------------------------------------------------------------

  useEffect(() => {
    if (!series.current || rolledCandles === null) return;

    series.current.setData(
      rolledCandles.map(
        (c): CandlestickData<Time> => ({
          time: c.time as Time,
          open: c.open,
          high: c.high,
          low: c.low,
          close: c.close,
        }),
      ),
    );

    chart.current?.timeScale().fitContent();
  }, [rolledCandles]);

  // -----------------------------------------------------------------------
  // Live tick effect — update the in-progress candle from WebSocket pushes
  // -----------------------------------------------------------------------

  useEffect(() => {
    if (!series.current || lastPrice === null || lastPriceAt === null) return;

    // Derive the bar-bucket timestamp for "right now".
    const nowSec = Math.floor(Date.parse(lastPriceAt) / 1000);
    const bucketSec = BAR_SPEC[barKey].bucketSeconds;
    const barTime = Math.floor(nowSec / bucketSec) * bucketSec;

    series.current.update({
      time: barTime as Time,
      open: lastPrice,
      high: lastPrice,
      low: lastPrice,
      close: lastPrice,
    });
  }, [lastPrice, lastPriceAt, barKey]);

  // -----------------------------------------------------------------------
  // Render
  // -----------------------------------------------------------------------

  return (
    <Card>
      <CardHeader className="flex-row flex-wrap items-center justify-between gap-3">
        <CardTitle className="flex items-center gap-2">
          <BarChart2 className="size-4" />
          Price
          {symbol ? (
            <span className="text-xs font-normal text-muted-foreground">· {symbol}</span>
          ) : null}
        </CardTitle>

        <div className="flex flex-wrap items-center gap-3 text-xs">
          {/* Range picker */}
          <div className="flex items-center gap-1.5 text-muted-foreground">
            <span>Range</span>
            <div className="flex overflow-hidden rounded-md border border-border">
              {RANGE_OPTIONS.map(({ label, days }) => (
                <button
                  key={days}
                  type="button"
                  onClick={() => setRangeDays(days)}
                  className={cn(
                    "px-2.5 py-1 transition-colors",
                    rangeDays === days
                      ? "bg-primary text-primary-foreground"
                      : "hover:bg-accent text-muted-foreground",
                  )}
                >
                  {label}
                </button>
              ))}
            </div>
          </div>

          {/* Bar size picker */}
          <div className="flex items-center gap-1.5 text-muted-foreground">
            <span>Bars</span>
            <div className="flex overflow-hidden rounded-md border border-border">
              {BAR_OPTIONS.map(({ key }) => (
                <button
                  key={key}
                  type="button"
                  onClick={() => setBarKey(key)}
                  className={cn(
                    "px-2.5 py-1 transition-colors",
                    barKey === key
                      ? "bg-primary text-primary-foreground"
                      : "hover:bg-accent text-muted-foreground",
                  )}
                >
                  {BAR_SPEC[key].label}
                </button>
              ))}
            </div>
          </div>

          {/* Meta */}
          {rolledCandles !== null && rolledCandles.length > 0 ? (
            <span className="text-muted-foreground">
              {rolledCandles.length} bars · {rangeDays}D window
            </span>
          ) : null}
        </div>
      </CardHeader>

      <CardContent>
        <div className="relative" style={{ height }}>
          <div ref={container} className="absolute inset-0" />
        </div>

        {loading ? (
          <p className="mt-3 text-sm text-muted-foreground">Loading price history…</p>
        ) : error ? (
          <p className="mt-3 text-sm text-loss">Could not load bars: {error}</p>
        ) : !symbol ? (
          <p className="mt-3 text-sm text-muted-foreground">
            Select a store to see the price chart.
          </p>
        ) : rolledCandles !== null && rolledCandles.length === 0 ? (
          <p className="mt-3 text-sm text-muted-foreground">
            No bars for this window — try a wider range.
          </p>
        ) : null}
      </CardContent>
    </Card>
  );
}
