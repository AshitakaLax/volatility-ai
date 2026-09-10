import {
  type CandlestickData,
  ColorType,
  type IChartApi,
  type ISeriesApi,
  type IPriceLine,
  createChart,
  type SeriesMarker,
  type Time,
} from "lightweight-charts";
import { useEffect, useRef } from "react";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/primitives";
import { usePriceBars } from "@/hooks/usePriceBars";
import { CHART_RESOLUTIONS, aggregate, buildCycles, chartWindow, toEpochSeconds } from "@/lib/filters";
import { cn } from "@/lib/utils";
import type { BacktestExecution, ChartResolution, DateRange } from "@/types/backtest";

/**
 * Price with executions on it.
 *
 * FOUR THINGS ARE DRAWN, AND THE THIRD IS WHY PHASE 1 EXISTED:
 *
 *   markers      a triangle at every buy, a diamond at every sell.
 *   target lines a horizontal line at each OPEN lot's exit price -- the
 *                order actually resting at the broker.
 *   connectors   a line from each buy to the sell that closed it. This
 *                needs the buy and the sell to name the same lot, which
 *                the blotter could not express until `lot_id` was added
 *                to both sides.
 *   candles      pulled at the selected zoom level and aggregated to it.
 *
 * ZOOM IS A FETCH, NOT JUST AN AGGREGATION. "1m" pulls at most a 2-day
 * window and "1H" at most 10 days, each with a high `max_points`, so the
 * server sends real minute / near-minute bars for that span rather than
 * a downsample of the whole ten-year file that no client-side rollup
 * could recover detail from. "1D" pulls the whole run.
 *
 * CONNECTORS ARE DRAWN ON A CANVAS, NOT AS SERIES. lightweight-charts
 * has no segment primitive, and one LineSeries per cycle would mean
 * thousands of series on a real run. An overlay canvas positioned with
 * timeToCoordinate/priceToCoordinate costs one canvas regardless.
 */

interface Props {
  ticker: string | null;
  executions: BacktestExecution[];
  /** The Execution-chart zoom level, and how to change it. Held in the
   * parent's filters so it survives a tab switch. */
  resolution: ChartResolution;
  onResolutionChange: (resolution: ChartResolution) => void;
  /** The filter-panel window (may be open); the chart pulls a sub-window
   * of it at the current zoom. */
  range: DateRange;
  /** The run's actual data bounds -- the anchor when `range` is open. */
  dataRange: DateRange;
  /** Lots with no matching sell, so their targets are still live. */
  openLotIds: Set<string>;
  /**
   * The run's profit target, as a fraction. Required, not defaulted: a
   * lot's exit price is buy_price * (1 + target), and an assumed value
   * would draw every open lot's resting order at a price no order is
   * actually at -- wrong in a way that looks entirely plausible.
   */
  profitTarget: number;
  height?: number;
}

// Above this, connectors become a mesh that hides the price rather than
// explaining it, and the canvas work stops being free. The cap is
// reported in the UI rather than applied silently.
const MAX_CONNECTORS = 400;

const RESOLUTION_ORDER: ChartResolution[] = ["1d", "1h", "1m"];

export function BacktestChart({
  ticker,
  executions,
  resolution,
  onResolutionChange,
  range,
  dataRange,
  openLotIds,
  profitTarget,
  height = 460,
}: Props) {
  const container = useRef<HTMLDivElement>(null);
  const overlay = useRef<HTMLCanvasElement>(null);
  const chart = useRef<IChartApi | null>(null);
  const series = useRef<ISeriesApi<"Candlestick"> | null>(null);
  const priceLines = useRef<IPriceLine[]>([]);

  const spec = CHART_RESOLUTIONS[resolution];
  const win = chartWindow(resolution, range, dataRange);
  const { candles, error } = usePriceBars(ticker, win.start, win.end, spec.maxPoints);
  const loading = candles === null;

  const cycles = buildCycles(executions);
  const closed = cycles.filter((cycle) => !cycle.open);
  const truncated = Math.max(0, closed.length - MAX_CONNECTORS);

  // --- chart lifecycle -------------------------------------------------
  useEffect(() => {
    if (!container.current) return;
    const created = createChart(container.current, {
      height,
      layout: {
        background: { type: ColorType.Solid, color: "transparent" },
        // A LITERAL, not the --muted-foreground token. That token is an
        // oklch() value, and lightweight-charts parses a limited colour
        // grammar: handed one it throws "Cannot parse color", and since
        // the throw happens during render it takes the whole view down
        // with it -- a blank page, not a mis-coloured axis. An e2e test
        // against the real deployment is what caught it.
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
      if (!container.current) return;
      created.applyOptions({ width: container.current.clientWidth });
      sizeOverlay();
    };
    resize();
    window.addEventListener("resize", resize);

    // The overlay must follow every pan and zoom, not just resizes.
    created.timeScale().subscribeVisibleLogicalRangeChange(drawConnectors);

    return () => {
      window.removeEventListener("resize", resize);
      created.remove();
      chart.current = null;
      series.current = null;
      priceLines.current = [];
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [height]);

  // --- data ----------------------------------------------------------
  useEffect(() => {
    if (!series.current) return;
    // null candles = a zoom-level refetch is in flight. Leave the last
    // frame on screen rather than blanking it to []; the "Loading…" line
    // below already signals the wait.
    if (candles === null) return;
    const rolled = aggregate(candles, spec.bucket);
    series.current.setData(
      rolled.map(
        (candle): CandlestickData<Time> => ({
          time: candle.time as Time,
          open: candle.open,
          high: candle.high,
          low: candle.low,
          close: candle.close,
        }),
      ),
    );

    const markers: SeriesMarker<Time>[] = executions.map((execution) => {
      const buy = execution.type === "BUY";
      const loss = (execution.profit_realized ?? 0) < 0;
      return {
        time: toEpochSeconds(execution.timestamp) as Time,
        position: buy ? "belowBar" : "aboveBar",
        // A signal exit that realised a loss is drawn as a loss. It is
        // the only sell in this system permitted to be one, and a chart
        // that coloured it like a harvest would hide the distinction the
        // whole no-loss design is built around.
        color: buy ? "#3b82f6" : loss ? "#ef4444" : "#22c55e",
        shape: buy ? "arrowUp" : "circle",
        text: buy
          ? `B ${execution.shares.toFixed(2)}`
          : `S ${(execution.profit_realized ?? 0).toFixed(2)}`,
      };
    });
    // Markers must be time-ordered or the library drops them silently.
    markers.sort((a, b) => Number(a.time) - Number(b.time));
    series.current.setMarkers(markers);

    // Target lines for lots still open: the orders actually resting.
    for (const line of priceLines.current) series.current.removePriceLine(line);
    priceLines.current = cycles
      .filter((cycle) => openLotIds.has(cycle.lotId))
      .slice(0, 60)
      .map((cycle) =>
        series.current!.createPriceLine({
          // buy_price * (1 + profit_target) is how the engine derives a
          // lot's target. The execution does not carry the target, so it
          // is recomputed with the run's OWN parameter rather than a
          // constant that would be wrong for every other configuration.
          price: cycle.buy.price * (1 + profitTarget),
          color: "rgba(234,179,8,0.55)",
          lineWidth: 1,
          lineStyle: 2,
          axisLabelVisible: false,
          title: "",
        }),
      );

    chart.current?.timeScale().fitContent();
    drawConnectors();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [candles, executions, resolution, openLotIds, profitTarget]);

  // --- connectors ------------------------------------------------------
  function sizeOverlay() {
    const canvas = overlay.current;
    const host = container.current;
    if (!canvas || !host) return;
    const ratio = window.devicePixelRatio || 1;
    canvas.width = host.clientWidth * ratio;
    canvas.height = host.clientHeight * ratio;
    canvas.style.width = `${host.clientWidth}px`;
    canvas.style.height = `${host.clientHeight}px`;
    canvas.getContext("2d")?.setTransform(ratio, 0, 0, ratio, 0, 0);
  }

  function drawConnectors() {
    const canvas = overlay.current;
    const context = canvas?.getContext("2d");
    if (!canvas || !context || !chart.current || !series.current) return;

    context.clearRect(0, 0, canvas.width, canvas.height);
    const timeScale = chart.current.timeScale();
    const priceScale = series.current;

    context.lineWidth = 1;
    for (const cycle of closed.slice(0, MAX_CONNECTORS)) {
      const exit = cycle.sells[cycle.sells.length - 1];
      if (!exit) continue;

      const x1 = timeScale.timeToCoordinate(toEpochSeconds(cycle.buy.timestamp) as Time);
      const x2 = timeScale.timeToCoordinate(toEpochSeconds(exit.timestamp) as Time);
      const y1 = priceScale.priceToCoordinate(cycle.buy.price);
      const y2 = priceScale.priceToCoordinate(exit.price);
      // null means the point is outside the visible range -- skipped
      // rather than clamped, which would draw a line to the edge of the
      // viewport that no trade corresponds to.
      if (x1 === null || x2 === null || y1 === null || y2 === null) continue;

      context.strokeStyle =
        (cycle.realized ?? 0) < 0 ? "rgba(239,68,68,0.45)" : "rgba(34,197,94,0.35)";
      context.beginPath();
      context.moveTo(x1, y1);
      context.lineTo(x2, y2);
      context.stroke();
    }
  }

  useEffect(() => {
    sizeOverlay();
    drawConnectors();
  });

  const spanLabel =
    spec.maxSpanSeconds === null
      ? "whole test"
      : `${Math.round(spec.maxSpanSeconds / 86_400)}-day max`;

  return (
    <Card>
      <CardHeader className="flex-row flex-wrap items-center justify-between gap-3">
        <CardTitle>Execution chart</CardTitle>
        <div className="flex flex-wrap items-center gap-4 text-xs text-muted-foreground">
          <div className="flex overflow-hidden rounded-md border border-border">
            {RESOLUTION_ORDER.map((option) => (
              <button
                key={option}
                type="button"
                onClick={() => onResolutionChange(option)}
                title={
                  option === "1d"
                    ? "daily candles, whole backtest"
                    : option === "1h"
                      ? "hourly candles, last 10 days"
                      : "minute candles, last 2 days"
                }
                className={cn(
                  "px-2.5 py-1 transition-colors",
                  resolution === option
                    ? "bg-primary text-primary-foreground"
                    : "hover:bg-accent",
                )}
              >
                {CHART_RESOLUTIONS[option].label}
              </button>
            ))}
          </div>
          <Legend color="#3b82f6" label="buy" />
          <Legend color="#22c55e" label="harvest" />
          <Legend color="#ef4444" label="loss exit" />
          <Legend color="rgba(234,179,8,0.8)" label="open target" />
          <span>
            {closed.length} cycle{closed.length === 1 ? "" : "s"}
            {truncated > 0 ? ` (${truncated} connectors not drawn)` : ""} · {spanLabel}
          </span>
        </div>
      </CardHeader>
      <CardContent>
        <div className="relative" style={{ height }}>
          <div ref={container} className="absolute inset-0" />
          <canvas ref={overlay} className="pointer-events-none absolute inset-0" />
        </div>
        {loading ? (
          <p className="mt-3 text-sm text-muted-foreground">Loading price history…</p>
        ) : error ? (
          <p className="mt-3 text-sm text-loss">
            Could not load price bars: {error}. Markers are still placed at their execution
            prices.
          </p>
        ) : executions.length === 0 ? (
          <p className="mt-3 text-sm text-muted-foreground">
            No executions in this range. A low-volatility fund on a grid tuned for a
            leveraged one legitimately never trades -- widen the date range, or lower the
            grid step.
          </p>
        ) : candles !== null && candles.length === 0 ? (
          <p className="mt-3 text-sm text-muted-foreground">
            No price bars for this window. Try a wider zoom.
          </p>
        ) : null}
      </CardContent>
    </Card>
  );
}

function Legend({ color, label }: { color: string; label: string }) {
  return (
    <span className="flex items-center gap-1.5">
      <span className="size-2 rounded-full" style={{ background: color }} />
      {label}
    </span>
  );
}
