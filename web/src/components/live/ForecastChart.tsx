import { useEffect, useRef, useState } from "react";

import {
  LANDING,
  coverage,
  labelled,
  landing,
  signed,
  yExtent,
  yTicks,
  type Landing,
} from "@/lib/forecastChart";
import { sessionDay } from "@/lib/riskReport";
import { cn } from "@/lib/utils";
import type { Tone } from "@/lib/control";
import type { ForecastSession, RiskForecasts } from "@/types/riskReport";

/**
 * Forecast against the close: each session's report (its 90% range, middle
 * 50% and median for the session's close-to-close return) and, once the
 * tracking service has recorded the close, where the return landed. Green
 * inside the middle 50%, amber inside the 90%, red outside it (a triangle
 * pointing the way it missed). A session still waiting for its close is
 * drawn dashed. Read from the forecast database (server/risk_forecasts.py);
 * the panel refreshes it when Check stores a report.
 */

const HEIGHT = 230;
const PAD = { top: 12, right: 12, bottom: 26, left: 44 };
const MAX_SLOT = 76;
const FALLBACK_WIDTH = 640;

const FILL: Record<Tone, string> = {
  profit: "fill-profit",
  stuck: "fill-stuck",
  loss: "fill-loss",
  neutral: "fill-neutral",
};

interface Props {
  data: RiskForecasts | null;
  error: string | null;
  /** The report Check just stored: its column is marked and described. */
  highlight?: string | null;
  /** A click on a session's column: the Forecast tab opens that report. */
  onSelect?: ((sha256: string) => void) | undefined;
}

/** The element's width, followed as it resizes. */
function useWidth() {
  const ref = useRef<HTMLDivElement>(null);
  const [width, setWidth] = useState(0);
  useEffect(() => {
    const node = ref.current;
    if (!node || typeof ResizeObserver === "undefined") return;
    const observer = new ResizeObserver(([entry]) => setWidth(entry?.contentRect.width ?? 0));
    observer.observe(node);
    return () => observer.disconnect();
  }, []);
  return [ref, width] as const;
}

export function ForecastChart({ data, error, highlight, onSelect }: Props) {
  const [ref, width] = useWidth();
  const [hover, setHover] = useState<number | null>(null);
  const rows = data?.sessions ?? [];
  const shownIndex =
    hover ?? (highlight ? rows.findIndex((row) => row.sha256 === highlight) : -1);
  const shown = rows[shownIndex >= 0 ? shownIndex : rows.length - 1];
  const tally = coverage(rows);

  return (
    <div className="space-y-2" data-testid="forecast-chart">
      <div className="flex flex-wrap items-baseline justify-between gap-x-4 gap-y-1">
        <p className="text-sm font-medium">
          Forecast against the close{data?.symbol ? ` · ${data.symbol}` : ""}
        </p>
        {rows.length ? (
          <p className="tnum text-xs text-muted-foreground">
            {tally.closed
              ? `Inside its 90%: ${tally.in90} of ${tally.closed} (90% wanted) · inside its middle 50%: ${tally.in50} of ${tally.closed} (50% wanted)`
              : "No session has closed yet"}
          </p>
        ) : null}
      </div>
      <div ref={ref} className="min-w-0">
        {rows.length ? (
          <Plot
            rows={rows}
            width={width || FALLBACK_WIDTH}
            hover={hover}
            setHover={setHover}
            highlight={highlight ?? null}
            onSelect={onSelect}
          />
        ) : (
          <p className="rounded-md border border-dashed border-border p-3 text-xs text-muted-foreground">
            {error
              ? `The forecast database could not be read: ${error}`
              : "No report saved yet. Check one and it is kept here; its actual return is added after its session closes."}
          </p>
        )}
      </div>
      {shown ? <Detail row={shown} /> : null}
      {rows.length ? <Legend /> : null}
      {rows.length ? <Table rows={rows} /> : null}
      {error && rows.length ? <p className="text-xs text-loss">{error}</p> : null}
    </div>
  );
}

function Plot({
  rows,
  width,
  hover,
  setHover,
  highlight,
  onSelect,
}: {
  rows: ForecastSession[];
  width: number;
  hover: number | null;
  setHover: (index: number | null) => void;
  highlight: string | null;
  onSelect?: ((sha256: string) => void) | undefined;
}) {
  const n = rows.length;
  const plotWidth = Math.max(40, Math.min(width - PAD.left - PAD.right, n * MAX_SLOT));
  const svgWidth = PAD.left + plotWidth + PAD.right;
  const plotHeight = HEIGHT - PAD.top - PAD.bottom;
  const slot = plotWidth / n;
  const extent = yExtent(rows);
  const x = (index: number) => PAD.left + slot * (index + 0.5);
  const y = (value: number) => PAD.top + ((extent - value) / (2 * extent)) * plotHeight;
  const showLabel = labelled(n, slot);
  const w90 = 6;
  const w50 = Math.min(14, slot * 0.5);
  const wMedian = Math.min(20, slot - 4);

  return (
    <svg
      width={svgWidth}
      height={HEIGHT}
      viewBox={`0 0 ${svgWidth} ${HEIGHT}`}
      className="tnum block max-w-full"
      role="img"
      aria-label={`${rows[0]?.symbol ?? ""} forecast ranges and where each close landed, ${sessionDay(rows[0]?.session)} to ${sessionDay(rows[n - 1]?.session)}`}
      onMouseLeave={() => setHover(null)}
    >
      {rows.map((row, index) =>
        row.sha256 === highlight || hover === index ? (
          <rect
            key={`ground-${row.sha256}`}
            x={PAD.left + slot * index}
            y={PAD.top - 6}
            width={slot}
            height={plotHeight + 6}
            rx={4}
            className={row.sha256 === highlight ? "fill-secondary" : "fill-foreground/5"}
          />
        ) : null,
      )}
      {yTicks(extent).map((value) => (
        <g key={value}>
          <line
            x1={PAD.left}
            x2={svgWidth - PAD.right}
            y1={y(value)}
            y2={y(value)}
            className={value === 0 ? "stroke-muted-foreground/60" : "stroke-border"}
            strokeWidth={1}
          />
          <text
            x={PAD.left - 8}
            y={y(value) + 4}
            textAnchor="end"
            className="fill-muted-foreground text-[11px]"
          >
            {value === 0 ? "0%" : signed(value, 0)}
          </text>
        </g>
      ))}
      {rows.map((row, index) => {
        const q = row.quantiles;
        const cx = x(index);
        const where = landing(row);
        const pending = where === "pending";
        return (
          <g key={row.sha256}>
            <rect
              x={cx - w90 / 2}
              y={y(q.p95)}
              width={w90}
              height={y(q.p05) - y(q.p95)}
              rx={3}
              className={pending ? "fill-none stroke-neutral" : "fill-neutral/35"}
              strokeWidth={pending ? 1.5 : 0}
              strokeDasharray={pending ? "3 3" : undefined}
            />
            <rect
              x={cx - w50 / 2}
              y={y(q.p75)}
              width={w50}
              height={y(q.p25) - y(q.p75)}
              rx={3}
              className={pending ? "fill-card stroke-neutral" : "fill-neutral/70"}
              strokeWidth={pending ? 1.5 : 0}
              strokeDasharray={pending ? "3 3" : undefined}
            />
            <line
              x1={cx - wMedian / 2}
              x2={cx + wMedian / 2}
              y1={y(row.median_pct)}
              y2={y(row.median_pct)}
              className={pending ? "stroke-neutral" : "stroke-foreground/75"}
              strokeWidth={2}
              strokeLinecap="round"
            />
            {row.actual ? <Mark cx={cx} cy={y(row.actual.return_pct)} where={where} /> : null}
            {showLabel(index) ? (
              <text
                x={cx}
                y={HEIGHT - 8}
                textAnchor="middle"
                className={cn(
                  "text-[11px]",
                  row.sha256 === highlight ? "fill-foreground font-semibold" : "fill-muted-foreground",
                )}
              >
                {sessionDay(row.session).replace(/^\w+,? /, "")}
              </text>
            ) : null}
            <rect
              x={PAD.left + slot * index}
              y={0}
              width={slot}
              height={HEIGHT}
              fill="transparent"
              onMouseEnter={() => setHover(index)}
              onClick={() => {
                setHover(index);
                onSelect?.(row.sha256);
              }}
              className={onSelect ? "cursor-pointer" : undefined}
            />
          </g>
        );
      })}
    </svg>
  );
}

/** Where a close landed: a dot inside a range, a triangle pointing the way it missed. */
export function Mark({ cx, cy, where }: { cx: number; cy: number; where: Landing }) {
  const fill = FILL[LANDING[where].tone];
  if (where === "above" || where === "below") {
    const size = 6.5;
    const tip = size * 1.1;
    const points =
      where === "above"
        ? `${cx},${cy - tip} ${cx - size},${cy + tip * 0.6} ${cx + size},${cy + tip * 0.6}`
        : `${cx},${cy + tip} ${cx - size},${cy - tip * 0.6} ${cx + size},${cy - tip * 0.6}`;
    return (
      <polygon points={points} className={cn(fill, "stroke-card")} strokeWidth={2} strokeLinejoin="round" />
    );
  }
  return <circle cx={cx} cy={cy} r={5.5} className={cn(fill, "stroke-card")} strokeWidth={2} />;
}

export function Swatch({ where }: { where: Landing }) {
  return (
    <svg viewBox="0 0 12 12" className="inline size-3 shrink-0" aria-hidden="true">
      {where === "above" || where === "below" ? (
        <polygon points="6,1 1,11 11,11" className={FILL[LANDING[where].tone]} />
      ) : (
        <circle cx={6} cy={6} r={5} className={FILL[LANDING[where].tone]} />
      )}
    </svg>
  );
}

function Detail({ row }: { row: ForecastSession }) {
  const q = row.quantiles;
  const where = landing(row);
  return (
    <div className="tnum space-y-0.5 text-xs text-muted-foreground">
      <p>
        <span className="font-medium text-foreground">{sessionDay(row.session)}</span>: forecast
        90% {signed(q.p05)} to {signed(q.p95)}, middle 50% {signed(q.p25)} to {signed(q.p75)},
        median {signed(row.median_pct)}, move {row.expected_move_pct.toFixed(1)}%
        {row.reports > 1 ? ` (the newest of ${row.reports} reports)` : ""}
      </p>
      {row.actual ? (
        <p className="flex flex-wrap items-center gap-x-1.5">
          <span className="text-foreground">Actual {signed(row.actual.return_pct)}</span>
          <Swatch where={where} />
          <span>{LANDING[where].label}</span>
        </p>
      ) : (
        <p>Actual: recorded by the nightly tracking run after the session closes.</p>
      )}
    </div>
  );
}

function Legend() {
  return (
    <div className="flex flex-wrap gap-x-4 gap-y-1 text-xs text-muted-foreground">
      <span className="flex items-center gap-1.5">
        <svg viewBox="0 0 16 16" className="size-4" aria-hidden="true">
          <rect x={6.5} y={1} width={3} height={14} rx={1.5} className="fill-neutral/35" />
          <rect x={4} y={4.5} width={8} height={7} rx={2} className="fill-neutral/70" />
          <line x1={2.5} x2={13.5} y1={8} y2={8} className="stroke-foreground/75" strokeWidth={2} />
        </svg>
        Forecast: 90% range, middle 50%, median
      </span>
      {(["in50", "in90", "below"] as const).map((where) => (
        <span key={where} className="flex items-center gap-1.5">
          <Swatch where={where} />
          {where === "below" ? "outside its 90% range" : LANDING[where].label}
        </span>
      ))}
      <span className="flex items-center gap-1.5">
        <svg viewBox="0 0 16 16" className="size-4" aria-hidden="true">
          <rect
            x={4}
            y={2}
            width={8}
            height={12}
            rx={2}
            className="fill-card stroke-neutral"
            strokeWidth={1.5}
            strokeDasharray="3 3"
          />
        </svg>
        waiting for the close
      </span>
    </div>
  );
}

function Table({ rows }: { rows: ForecastSession[] }) {
  return (
    <details>
      <summary className="cursor-pointer text-xs text-muted-foreground">Show as a table</summary>
      <div className="mt-1 overflow-x-auto">
        <table className="tnum w-full text-left text-xs">
          <thead className="text-muted-foreground">
            <tr>
              <th className="py-1 pr-3 font-medium">Session</th>
              <th className="py-1 pr-3 font-medium">90% range</th>
              <th className="py-1 pr-3 font-medium">Middle 50%</th>
              <th className="py-1 pr-3 font-medium">Median</th>
              <th className="py-1 pr-3 font-medium">Move</th>
              <th className="py-1 pr-3 font-medium">Actual</th>
              <th className="py-1 pr-3 font-medium">Landed</th>
            </tr>
          </thead>
          <tbody>
            {[...rows].reverse().map((row) => {
              const q = row.quantiles;
              return (
                <tr key={row.sha256} className="border-t border-border">
                  <td className="py-1 pr-3 whitespace-nowrap">{sessionDay(row.session)}</td>
                  <td className="py-1 pr-3 whitespace-nowrap">
                    {signed(q.p05)} to {signed(q.p95)}
                  </td>
                  <td className="py-1 pr-3 whitespace-nowrap">
                    {signed(q.p25)} to {signed(q.p75)}
                  </td>
                  <td className="py-1 pr-3">{signed(row.median_pct)}</td>
                  <td className="py-1 pr-3">{row.expected_move_pct.toFixed(1)}%</td>
                  <td className="py-1 pr-3">{row.actual ? signed(row.actual.return_pct) : "--"}</td>
                  <td className="py-1 pr-3 whitespace-nowrap">{LANDING[landing(row)].label}</td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </details>
  );
}
