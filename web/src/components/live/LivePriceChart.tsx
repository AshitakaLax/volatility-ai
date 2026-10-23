import {
  type CandlestickData,
  ColorType,
  type IChartApi,
  type IPriceLine,
  type ISeriesApi,
  type SeriesMarker,
  type Time,
  createChart,
} from "lightweight-charts";
import { BarChart2 } from "lucide-react";
import { useEffect, useMemo, useRef, useState } from "react";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/primitives";
import { api } from "@/lib/api";
import { aggregate, type Candle } from "@/lib/filters";
import { cn } from "@/lib/utils";
import type { Timeframe } from "@/types/backtest";
import type { TraderFill } from "@/types/control";

/**
 * The deployment's price, as its TRADER saw it: the minute bars it traded
 * on, from its own bar journal (engine/trading/control_inbox.py) -- not the
 * warehouse, whose bars are another feed and lag a running deployment by
 * days. The sessions before today come from the history the trader replays
 * at each start, so the chart has context from the first minute.
 *
 * On top: every fill it booked (blue arrows for buys; green circles for
 * sales, red for one that realised a loss -- only Ultimate's regime exit
 * may) and the price its next buy triggers at.
 *
 * RANGE vs. BAR SIZE are independent: the range picks how many sessions of
 * the journal to fetch (it keeps ten), the bar size rolls its minute bars up
 * client-side. The newest candle is updated in place from the socket's
 * last price between fetches.
 */

interface Props {
  deploymentId: string | null;
  symbol: string | null;
  /** The loop's last observed price from the WebSocket state push. */
  lastPrice: number | null;
  lastPriceAt: string | null;
  /** The sessions' fills, for the markers. */
  fills: TraderFill[];
  /** A buy triggers at or below this; null when none would. */
  buyLevel: number | null;
  height?: number;
}

type Sessions = 1 | 2 | 5 | 10;

const RANGE_OPTIONS: { label: string; sessions: Sessions }[] = [
  { label: "1D", sessions: 1 },
  { label: "2D", sessions: 2 },
  { label: "5D", sessions: 5 },
  { label: "10D", sessions: 10 },
];

type BarKey = "1m" | "5m" | "15m" | "1H";

const BAR_OPTIONS: { key: BarKey; label: string; seconds: number; timeframe: Timeframe }[] = [
  { key: "1m", label: "1m", seconds: 60, timeframe: "1Min" },
  { key: "5m", label: "5m", seconds: 300, timeframe: "5Min" },
  { key: "15m", label: "15m", seconds: 900, timeframe: "15Min" },
  { key: "1H", label: "1H", seconds: 3600, timeframe: "1Hour" },
];

const BAR = Object.fromEntries(BAR_OPTIONS.map((option) => [option.key, option])) as Record<
  BarKey,
  (typeof BAR_OPTIONS)[number]
>;

// A new minute bar lands in the journal every tick; fetch them about as often.
const REFRESH_MS = 60_000;

export function LivePriceChart({
  deploymentId,
  symbol,
  lastPrice,
  lastPriceAt,
  fills,
  buyLevel,
  height = 400,
}: Props) {
  const [sessions, setSessions] = useState<Sessions>(2);
  const [barKey, setBarKey] = useState<BarKey>("1m");
  const [candles, setCandles] = useState<Candle[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setCandles(null);
    setError(null);
    if (!deploymentId) return;
    let cancelled = false;
    const load = () => {
      api
        .deploymentBars(deploymentId, sessions)
        .then((bars) => {
          if (cancelled) return;
          setCandles(bars.bars.map(([time, open, high, low, close]) => ({ time, open, high, low, close })));
          setError(null);
        })
        .catch((cause: unknown) => {
          if (!cancelled) setError(cause instanceof Error ? cause.message : String(cause));
        });
    };
    load();
    const timer = window.setInterval(load, REFRESH_MS);
    return () => {
      cancelled = true;
      window.clearInterval(timer);
    };
  }, [deploymentId, sessions]);

  const rolled = useMemo(
    () => (candles ? aggregate(candles, BAR[barKey].timeframe) : null),
    [candles, barKey],
  );

  const container = useRef<HTMLDivElement>(null);
  const chart = useRef<IChartApi | null>(null);
  const series = useRef<ISeriesApi<"Candlestick"> | null>(null);
  const buyLine = useRef<IPriceLine | null>(null);

  useEffect(() => {
    if (!container.current) return;
    const created = createChart(container.current, {
      height,
      layout: {
        background: { type: ColorType.Solid, color: "transparent" },
        // Literal rgba rather than a CSS token: lightweight-charts parses a
        // limited colour grammar and throws on oklch().
        textColor: "rgba(140, 140, 150, 0.9)",
        fontFamily: "inherit",
      },
      grid: {
        vertLines: { color: "rgba(128,128,128,0.08)" },
        horzLines: { color: "rgba(128,128,128,0.08)" },
      },
      rightPriceScale: { borderVisible: false },
      timeScale: { borderVisible: false, timeVisible: true, secondsVisible: false },
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
      if (container.current) created.applyOptions({ width: container.current.clientWidth });
    };
    resize();
    window.addEventListener("resize", resize);
    return () => {
      window.removeEventListener("resize", resize);
      created.remove();
      chart.current = null;
      series.current = null;
      buyLine.current = null;
    };
  }, [height]);

  // The bars, then the fills on them.
  useEffect(() => {
    if (!series.current || rolled === null) return;
    series.current.setData(
      rolled.map(
        (c): CandlestickData<Time> => ({
          time: c.time as Time,
          open: c.open,
          high: c.high,
          low: c.low,
          close: c.close,
        }),
      ),
    );
    const bucket = BAR[barKey].seconds;
    const first = rolled[0]?.time ?? Number.POSITIVE_INFINITY;
    const markers: SeriesMarker<Time>[] = fills
      .filter((fill) => fill.t >= first)
      .map((fill) => {
        const buy = fill.side === "buy";
        const loss = (fill.pnl ?? 0) < 0;
        return {
          time: (Math.floor(fill.t / bucket) * bucket) as Time,
          position: buy ? "belowBar" : "aboveBar",
          color: buy ? "#3b82f6" : loss ? "#ef4444" : "#22c55e",
          shape: buy ? "arrowUp" : "circle",
          text: buy ? "B" : `S ${(fill.pnl ?? 0).toFixed(2)}`,
        };
      });
    // Time-ordered, or the library drops them silently.
    markers.sort((a, b) => Number(a.time) - Number(b.time));
    series.current.setMarkers(markers);
    chart.current?.timeScale().fitContent();
  }, [rolled, fills, barKey]);

  // The next buy's price, as a line.
  useEffect(() => {
    if (!series.current) return;
    if (buyLine.current) {
      series.current.removePriceLine(buyLine.current);
      buyLine.current = null;
    }
    if (buyLevel !== null) {
      buyLine.current = series.current.createPriceLine({
        price: buyLevel,
        color: "rgba(59,130,246,0.7)",
        lineWidth: 1,
        lineStyle: 2,
        axisLabelVisible: true,
        title: "next buy",
      });
    }
  }, [buyLevel, rolled]);

  // Between fetches, move the newest candle with the socket's last price.
  useEffect(() => {
    if (!series.current || lastPrice === null || lastPriceAt === null || !rolled?.length) return;
    const bucket = BAR[barKey].seconds;
    const at = Math.floor(Math.floor(Date.parse(lastPriceAt) / 1000) / bucket) * bucket;
    const newest = rolled[rolled.length - 1];
    if (!newest || at < newest.time) return;
    series.current.update(
      at === newest.time
        ? {
            time: at as Time,
            open: newest.open,
            high: Math.max(newest.high, lastPrice),
            low: Math.min(newest.low, lastPrice),
            close: lastPrice,
          }
        : { time: at as Time, open: lastPrice, high: lastPrice, low: lastPrice, close: lastPrice },
    );
  }, [lastPrice, lastPriceAt, barKey, rolled]);

  return (
    <Card>
      <CardHeader className="flex-row flex-wrap items-center justify-between gap-3">
        <CardTitle className="flex items-center gap-2">
          <BarChart2 className="size-4" />
          Price
          {symbol ? (
            <span className="text-xs font-normal text-muted-foreground">
              · {symbol}, as the trader saw it
            </span>
          ) : null}
        </CardTitle>
        <div className="flex flex-wrap items-center gap-3 text-xs">
          <Picker
            label="Range"
            options={RANGE_OPTIONS.map((o) => ({ key: o.sessions, label: o.label }))}
            value={sessions}
            onChange={setSessions}
          />
          <Picker
            label="Bars"
            options={BAR_OPTIONS.map((o) => ({ key: o.key, label: o.label }))}
            value={barKey}
            onChange={setBarKey}
          />
          {rolled?.length ? (
            <span className="text-muted-foreground">
              {rolled.length} bars · {fills.length} fills
            </span>
          ) : null}
        </div>
      </CardHeader>
      <CardContent>
        <div className="relative" style={{ height }}>
          <div ref={container} className="absolute inset-0" />
        </div>
        {!deploymentId ? (
          <p className="mt-3 text-sm text-muted-foreground">Pick a deployment to see its price.</p>
        ) : error ? (
          <p className="mt-3 text-sm text-loss">Could not load its bars: {error}</p>
        ) : candles === null ? (
          <p className="mt-3 text-sm text-muted-foreground">Loading the trader's bars…</p>
        ) : candles.length === 0 ? (
          <p className="mt-3 text-sm text-muted-foreground">
            Its trader has recorded no bars yet: they start with its next session (or restart).
          </p>
        ) : null}
      </CardContent>
    </Card>
  );
}

function Picker<K extends string | number>({
  label,
  options,
  value,
  onChange,
}: {
  label: string;
  options: { key: K; label: string }[];
  value: K;
  onChange: (key: K) => void;
}) {
  return (
    <div className="flex items-center gap-1.5 text-muted-foreground">
      <span>{label}</span>
      <div className="flex overflow-hidden rounded-md border border-border">
        {options.map((option) => (
          <button
            key={option.key}
            type="button"
            onClick={() => onChange(option.key)}
            className={cn(
              "px-2.5 py-1 transition-colors",
              value === option.key
                ? "bg-primary text-primary-foreground"
                : "text-muted-foreground hover:bg-accent",
            )}
          >
            {option.label}
          </button>
        ))}
      </div>
    </div>
  );
}
