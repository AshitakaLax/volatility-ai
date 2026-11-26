import { useState } from "react";

import { Mark, Swatch } from "@/components/live/ForecastChart";
import { useElementWidth } from "@/hooks/useElementWidth";
import { LANDING, signed } from "@/lib/forecastChart";
import {
  dollars,
  fanExtent,
  inUnit,
  niceTicks,
  type FanPoint,
  type Outcome,
  type Unit,
} from "@/lib/forecastReview";
import { cn } from "@/lib/utils";
import type { GeneratedReport, HorizonKey } from "@/types/forecast";

/**
 * Where a report says the fund goes: from the base close, each horizon's
 * 90% range, middle 50% and median -- the report shown in blue, a second
 * one to compare against in gray lines -- and, once a horizon's last
 * session has closed, where the fund actually was (the Live page's marks:
 * a dot inside a range, a triangle outside it). Horizons are evenly spaced,
 * not to scale in time: a year is 252 sessions, a day one.
 *
 * Hovering a horizon reads every value at it; clicking one shows its whole
 * distribution below (the buttons under the chart do the same from the
 * keyboard). The horizon table beside it carries every value without a
 * pointer.
 */

export interface FanSeries {
  label: string;
  report: GeneratedReport;
  points: FanPoint[];
}

interface Props {
  subject: FanSeries;
  compare?: FanSeries | null;
  unit: Unit;
  outcomes?: Record<HorizonKey, Outcome> | null;
  selected: HorizonKey;
  onSelect: (key: HorizonKey) => void;
  /** The session a horizon ends on, where known. */
  endOf?: (key: HorizonKey) => string | null;
  day: (iso: string) => string;
}

const HEIGHT = 260;
// The x labels where a horizon's slot is too narrow for "1 quarter".
const SHORT: Record<FanPoint["key"], string> = {
  base: "Close",
  tomorrow: "1d",
  next_week: "1w",
  next_month: "1m",
  next_quarter: "1q",
  next_year: "1y",
};
const PAD = { top: 14, right: 18, bottom: 30, left: 58 };
const FALLBACK_WIDTH = 640;

function format(value: number, unit: Unit, digits = 1): string {
  return unit === "price" ? dollars(value) : signed(value, digits);
}

function tickText(value: number, unit: Unit): string {
  if (unit === "price") return dollars(value);
  return value === 0 ? "0%" : signed(value, Number.isInteger(value) ? 0 : 1);
}

function path(
  points: readonly FanPoint[],
  x: (i: number) => number,
  y: (v: number) => number,
  pick: (p: FanPoint) => number,
) {
  return points
    .map((p, i) => `${i ? "L" : "M"}${x(i).toFixed(1)},${y(pick(p)).toFixed(1)}`)
    .join(" ");
}

function band(
  points: readonly FanPoint[],
  x: (i: number) => number,
  y: (v: number) => number,
  top: (p: FanPoint) => number,
  bottom: (p: FanPoint) => number,
) {
  const upper = points.map((p, i) => `${x(i).toFixed(1)},${y(top(p)).toFixed(1)}`);
  const lower = points.map((p, i) => `${x(i).toFixed(1)},${y(bottom(p)).toFixed(1)}`).reverse();
  return `M${upper.join(" L")} L${lower.join(" L")} Z`;
}

export function FanChart({
  subject,
  compare,
  unit,
  outcomes,
  selected,
  onSelect,
  endOf,
  day,
}: Props) {
  const [ref, measured] = useElementWidth();
  const [hover, setHover] = useState<number | null>(null);
  const width = measured || FALLBACK_WIDTH;
  const points = subject.points;
  const n = points.length;
  const plotWidth = Math.max(80, width - PAD.left - PAD.right);
  const plotHeight = HEIGHT - PAD.top - PAD.bottom;

  const landed = points
    .slice(1)
    .map((p) => (p.key === "base" ? null : outcomes?.[p.key]))
    .filter((o): o is Outcome => Boolean(o && o.return_pct !== null))
    .map((o) => inUnit(subject.report, o.return_pct as number, unit));
  const [lo, hi] = fanExtent(compare ? [points, compare.points] : [points], landed);
  const x = (i: number) => PAD.left + (n > 1 ? (i / (n - 1)) * plotWidth : plotWidth / 2);
  const y = (v: number) => PAD.top + ((hi - v) / (hi - lo)) * plotHeight;
  const ticks = niceTicks(lo, hi, 5);
  const zero = inUnit(subject.report, 0, unit);
  const slot = n > 1 ? plotWidth / (n - 1) : plotWidth;
  const shown = hover ?? null;

  return (
    <div className="space-y-2" data-testid="fan-chart">
      <div ref={ref} className="relative min-w-0" onMouseLeave={() => setHover(null)}>
        <svg
          width={width}
          height={HEIGHT}
          viewBox={`0 0 ${width} ${HEIGHT}`}
          className="tnum block max-w-full"
          role="img"
          aria-label={`${subject.report.symbol} forecast from the ${dollars(subject.report.base_price)} close through ${points[n - 1]?.label ?? ""}: the 90% range, the middle 50% and the median at each horizon`}
        >
          {points.map((p, i) =>
            p.key === selected ? (
              <rect
                key={`sel-${p.key}`}
                x={x(i) - Math.min(28, slot / 2)}
                y={PAD.top - 6}
                width={Math.min(56, slot)}
                height={plotHeight + 6}
                rx={4}
                className="fill-foreground/5"
              />
            ) : null,
          )}
          {ticks.map((value) => (
            <g key={value}>
              <line
                x1={PAD.left}
                x2={width - PAD.right}
                y1={y(value)}
                y2={y(value)}
                className="stroke-border"
                strokeWidth={1}
              />
              <text
                x={PAD.left - 8}
                y={y(value) + 4}
                textAnchor="end"
                className="fill-muted-foreground text-[11px]"
              >
                {tickText(value, unit)}
              </text>
            </g>
          ))}
          <line
            x1={PAD.left}
            x2={width - PAD.right}
            y1={y(zero)}
            y2={y(zero)}
            className="stroke-muted-foreground/70"
            strokeWidth={1}
          />

          <path
            d={band(
              points,
              x,
              y,
              (p) => p.p95,
              (p) => p.p05,
            )}
            className="fill-series-1/12"
          />
          <path
            d={band(
              points,
              x,
              y,
              (p) => p.p75,
              (p) => p.p25,
            )}
            className="fill-series-1/25"
          />
          {compare ? (
            <g>
              {(["p05", "p95"] as const).map((key) => (
                <path
                  key={key}
                  d={path(compare.points, x, y, (p) => p[key])}
                  className="fill-none stroke-muted-foreground"
                  strokeWidth={1}
                  strokeDasharray="4 3"
                />
              ))}
              <path
                d={path(compare.points, x, y, (p) => p.median)}
                className="fill-none stroke-muted-foreground"
                strokeWidth={2}
                strokeLinejoin="round"
                strokeLinecap="round"
              />
            </g>
          ) : null}
          <path
            d={path(points, x, y, (p) => p.median)}
            className="fill-none stroke-series-1"
            strokeWidth={2}
            strokeLinejoin="round"
            strokeLinecap="round"
          />
          {points.map((p, i) => (
            <circle
              key={`dot-${p.key}`}
              cx={x(i)}
              cy={y(p.median)}
              r={4}
              className="fill-series-1 stroke-card"
              strokeWidth={2}
            />
          ))}
          {points.map((p, i) => {
            if (p.key === "base") return null;
            const outcome = outcomes?.[p.key];
            if (!outcome || outcome.return_pct === null) return null;
            return (
              <Mark
                key={`out-${p.key}`}
                cx={x(i) + 9}
                cy={y(inUnit(subject.report, outcome.return_pct, unit))}
                where={outcome.landing}
              />
            );
          })}
          {shown !== null ? (
            <line
              x1={x(shown)}
              x2={x(shown)}
              y1={PAD.top}
              y2={PAD.top + plotHeight}
              className="stroke-foreground/40"
              strokeWidth={1}
            />
          ) : null}
          {points.map((p, i) => (
            <text
              key={`x-${p.key}`}
              x={x(i)}
              y={HEIGHT - 8}
              textAnchor={i === 0 ? "start" : i === n - 1 ? "end" : "middle"}
              className={cn(
                "text-[11px]",
                p.key === selected ? "fill-foreground font-semibold" : "fill-muted-foreground",
              )}
            >
              {slot < 72 ? SHORT[p.key] : p.label}
            </text>
          ))}
          {points.map((p, i) => (
            <rect
              key={`hit-${p.key}`}
              x={x(i) - slot / 2}
              y={0}
              width={slot}
              height={HEIGHT}
              fill="transparent"
              className={p.key === "base" ? undefined : "cursor-pointer"}
              onMouseEnter={() => setHover(i)}
              onClick={() => {
                setHover(i);
                if (p.key !== "base") onSelect(p.key);
              }}
            />
          ))}
        </svg>
        {shown !== null && points[shown] ? (
          <Readout
            left={Math.min(Math.max(x(shown) + 12, 4), width - 236)}
            point={points[shown]}
            compare={compare?.points[shown] ?? null}
            subjectLabel={subject.label}
            compareLabel={compare?.label ?? null}
            outcome={
              points[shown].key === "base"
                ? null
                : (outcomes?.[points[shown].key as HorizonKey] ?? null)
            }
            end={
              points[shown].key === "base"
                ? null
                : (endOf?.(points[shown].key as HorizonKey) ?? null)
            }
            report={subject.report}
            unit={unit}
            day={day}
          />
        ) : null}
      </div>
      <Legend compareLabel={compare?.label ?? null} outcomes={Boolean(landed.length)} />
    </div>
  );
}

function Readout({
  left,
  point,
  compare,
  subjectLabel,
  compareLabel,
  outcome,
  end,
  report,
  unit,
  day,
}: {
  left: number;
  point: FanPoint;
  compare: FanPoint | null;
  subjectLabel: string;
  compareLabel: string | null;
  outcome: Outcome | null;
  end: string | null;
  report: GeneratedReport;
  unit: Unit;
  day: (iso: string) => string;
}) {
  const heading =
    point.key === "base"
      ? `The ${dollars(report.base_price)} close it starts from`
      : `${point.label}${point.sessions > 1 ? ` · ${point.sessions} sessions` : ""}${end ? ` · to ${day(end)}` : ""}`;
  return (
    <div
      className="tnum pointer-events-none absolute top-1 z-10 w-56 space-y-1.5 rounded-md border border-border bg-card px-2.5 py-2 text-xs shadow-md"
      style={{ left }}
    >
      <p className="font-medium text-foreground">{heading}</p>
      {point.key !== "base" ? (
        <>
          <ReadoutRow
            keyClass="stroke-series-1"
            value={`median ${format(point.median, unit)}`}
            detail={`50% ${format(point.p25, unit)} to ${format(point.p75, unit)} · 90% ${format(point.p05, unit)} to ${format(point.p95, unit)}`}
            label={subjectLabel}
          />
          {compare && compareLabel ? (
            <ReadoutRow
              keyClass="stroke-muted-foreground"
              value={`median ${format(compare.median, unit)}`}
              detail={`90% ${format(compare.p05, unit)} to ${format(compare.p95, unit)}`}
              label={compareLabel}
            />
          ) : null}
          {outcome && outcome.return_pct !== null ? (
            <p className="flex items-center gap-1.5">
              <Swatch where={outcome.landing} />
              <span className="font-medium text-foreground">
                actual {format(inUnit(report, outcome.return_pct, unit), unit)}
              </span>
              <span className="text-muted-foreground">{LANDING[outcome.landing].label}</span>
            </p>
          ) : null}
        </>
      ) : null}
    </div>
  );
}

function ReadoutRow({
  keyClass,
  value,
  detail,
  label,
}: {
  keyClass: string;
  value: string;
  detail: string;
  label: string;
}) {
  return (
    <div className="flex gap-1.5">
      <svg viewBox="0 0 12 12" className="mt-1 size-3 shrink-0" aria-hidden="true">
        <line x1={0} x2={12} y1={6} y2={6} className={keyClass} strokeWidth={2} />
      </svg>
      <div className="min-w-0">
        <p className="font-medium text-foreground">{value}</p>
        <p className="text-muted-foreground">{detail}</p>
        <p className="truncate text-muted-foreground">{label}</p>
      </div>
    </div>
  );
}

function Legend({ compareLabel, outcomes }: { compareLabel: string | null; outcomes: boolean }) {
  return (
    <div className="flex flex-wrap gap-x-4 gap-y-1 text-xs text-muted-foreground">
      <span className="flex items-center gap-1.5">
        <svg viewBox="0 0 16 12" className="h-3 w-4" aria-hidden="true">
          <rect x={0} y={0} width={16} height={12} rx={2} className="fill-series-1/12" />
          <rect x={0} y={3} width={16} height={6} rx={1} className="fill-series-1/25" />
          <line x1={0} x2={16} y1={6} y2={6} className="stroke-series-1" strokeWidth={2} />
        </svg>
        This report: 90% range, middle 50%, median
      </span>
      {compareLabel ? (
        <span className="flex min-w-0 items-center gap-1.5">
          <svg viewBox="0 0 16 12" className="h-3 w-4 shrink-0" aria-hidden="true">
            <line
              x1={0}
              x2={16}
              y1={1}
              y2={1}
              className="stroke-muted-foreground"
              strokeWidth={1}
              strokeDasharray="4 3"
            />
            <line
              x1={0}
              x2={16}
              y1={6}
              y2={6}
              className="stroke-muted-foreground"
              strokeWidth={2}
            />
            <line
              x1={0}
              x2={16}
              y1={11}
              y2={11}
              className="stroke-muted-foreground"
              strokeWidth={1}
              strokeDasharray="4 3"
            />
          </svg>
          <span className="truncate">Compared: {compareLabel} (median, 90% range)</span>
        </span>
      ) : null}
      {outcomes
        ? (["in50", "in90", "below"] as const).map((where) => (
            <span key={where} className="flex items-center gap-1.5">
              <Swatch where={where} />
              {where === "below" ? "outside its 90% range" : LANDING[where].label}
            </span>
          ))
        : null}
    </div>
  );
}
