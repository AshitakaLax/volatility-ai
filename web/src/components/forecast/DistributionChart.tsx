import { useState } from "react";

import { Swatch } from "@/components/live/ForecastChart";
import { useElementWidth } from "@/hooks/useElementWidth";
import { LANDING, signed } from "@/lib/forecastChart";
import {
  distribution,
  dollars,
  niceTicks,
  type Distribution,
  type Outcome,
} from "@/lib/forecastReview";
import { cn } from "@/lib/utils";
import type { ReportHorizon } from "@/types/forecast";

/**
 * One horizon's whole distribution: the report's bins as bars (height is
 * the chance per percentage point of return, so bins of different widths
 * compare), its 5%, median and 95% marked, a second report's outline to
 * compare against, and where the fund actually closed once it has.
 */

interface Side {
  label: string;
  horizon: ReportHorizon;
  basePrice: number;
}

interface Props {
  title: string;
  subject: Side;
  compare?: Side | null;
  outcome?: Outcome | null;
}

const HEIGHT = 210;
const PAD = { top: 22, right: 14, bottom: 26, left: 46 };
const FALLBACK_WIDTH = 640;

/** The chance `found` puts inside [lo, hi), read from its bins. */
function chanceIn(found: Distribution, lo: number, hi: number): number {
  return found.bars.reduce((sum, bar) => {
    const overlap = Math.min(bar.hi, hi) - Math.max(bar.lo, lo);
    return overlap > 0 ? sum + bar.density * overlap : sum;
  }, 0);
}

export function DistributionChart({ title, subject, compare, outcome }: Props) {
  const [ref, measured] = useElementWidth();
  const [hover, setHover] = useState<number | null>(null);
  const width = measured || FALLBACK_WIDTH;
  const mine = distribution(subject.horizon);
  const theirs = compare ? distribution(compare.horizon) : null;
  const actual = outcome?.return_pct ?? null;

  const q = subject.horizon.summary.quantiles_pct;
  const median = subject.horizon.summary.median_pct;
  // Every bar, the 5%/median/95% marks and the actual close are inside it,
  // with a little room so a mark at the edge keeps its label.
  const reach = [mine.lo, mine.hi, q.p05, q.p95, median, ...(theirs ? [theirs.lo, theirs.hi] : [])];
  if (actual !== null) reach.push(actual);
  const span = Math.max(...reach) - Math.min(...reach) || 1;
  const lo = Math.min(...reach) - span * 0.03;
  const hi = Math.max(...reach) + span * 0.03;
  const top =
    Math.max(
      ...mine.bars.map((b) => b.density),
      ...(theirs?.bars.map((b) => b.density) ?? []),
      1e-6,
    ) * 1.12;
  const plotWidth = Math.max(80, width - PAD.left - PAD.right);
  const plotHeight = HEIGHT - PAD.top - PAD.bottom;
  const x = (v: number) => PAD.left + ((v - lo) / (hi - lo || 1)) * plotWidth;
  const y = (d: number) => PAD.top + (1 - d / top) * plotHeight;

  const xTicks = niceTicks(lo, hi, Math.max(3, Math.min(8, Math.floor(plotWidth / 70))));
  const yTicks = niceTicks(0, top, 3).filter((d) => d > 0);
  const shown = hover !== null ? mine.bars[hover] : null;

  const step = theirs
    ? theirs.bars
        .map((bar, i) => {
          const left = `${x(bar.lo).toFixed(1)},${y(bar.density).toFixed(1)}`;
          const right = `${x(bar.hi).toFixed(1)},${y(bar.density).toFixed(1)}`;
          return `${i ? "L" : `M${x(bar.lo).toFixed(1)},${y(0).toFixed(1)} L`}${left} L${right}`;
        })
        .join(" ") + ` L${x(theirs.hi).toFixed(1)},${y(0).toFixed(1)}`
    : null;

  const markers = [
    { value: q.p05, label: "5%" },
    { value: median, label: "median" },
    { value: q.p95, label: "95%" },
  ];

  return (
    <div className="space-y-2" data-testid="distribution-chart">
      <p className="text-sm font-medium">{title}</p>
      <div ref={ref} className="relative min-w-0" onMouseLeave={() => setHover(null)}>
        <svg
          width={width}
          height={HEIGHT}
          viewBox={`0 0 ${width} ${HEIGHT}`}
          className="tnum block max-w-full"
          role="img"
          aria-label={`${title}: the chance of each return, 90% between ${signed(q.p05)} and ${signed(q.p95)}, median ${signed(median)}`}
        >
          {yTicks.map((d) => (
            <g key={d}>
              <line
                x1={PAD.left}
                x2={width - PAD.right}
                y1={y(d)}
                y2={y(d)}
                className="stroke-border"
                strokeWidth={1}
              />
              <text
                x={PAD.left - 8}
                y={y(d) + 4}
                textAnchor="end"
                className="fill-muted-foreground text-[11px]"
              >
                {`${Number((d * 100).toFixed(1))}%`}
              </text>
            </g>
          ))}
          <line
            x1={PAD.left}
            x2={width - PAD.right}
            y1={y(0)}
            y2={y(0)}
            className="stroke-muted-foreground/70"
            strokeWidth={1}
          />
          {mine.bars.map((bar, i) => {
            const left = x(bar.lo);
            const barWidth = x(bar.hi) - left;
            const gap = barWidth >= 4 ? 1 : 0;
            return (
              <rect
                key={`${bar.lo}`}
                x={left + gap}
                y={y(bar.density)}
                width={Math.max(0.5, barWidth - 2 * gap)}
                height={Math.max(0, y(0) - y(bar.density))}
                className={hover === i ? "fill-series-1" : "fill-series-1/55"}
              />
            );
          })}
          {step ? (
            <path
              d={step}
              className="fill-none stroke-muted-foreground"
              strokeWidth={2}
              strokeLinejoin="round"
            />
          ) : null}
          {markers.map((marker) => (
            <g key={marker.label}>
              <line
                x1={x(marker.value)}
                x2={x(marker.value)}
                y1={PAD.top - 4}
                y2={y(0)}
                className="stroke-foreground/45"
                strokeWidth={1}
              />
              <text
                x={x(marker.value)}
                y={PAD.top - 8}
                textAnchor="middle"
                className="fill-muted-foreground text-[11px]"
              >
                {marker.label}
              </text>
            </g>
          ))}
          {actual !== null && outcome ? (
            <g>
              <line
                x1={x(actual)}
                x2={x(actual)}
                y1={PAD.top}
                y2={y(0)}
                className={cn(
                  LANDING[outcome.landing].tone === "profit"
                    ? "stroke-profit"
                    : LANDING[outcome.landing].tone === "stuck"
                      ? "stroke-stuck"
                      : "stroke-loss",
                )}
                strokeWidth={2}
              />
              <circle
                cx={x(actual)}
                cy={PAD.top + 4}
                r={4.5}
                className={cn(
                  "stroke-card",
                  LANDING[outcome.landing].tone === "profit"
                    ? "fill-profit"
                    : LANDING[outcome.landing].tone === "stuck"
                      ? "fill-stuck"
                      : "fill-loss",
                )}
                strokeWidth={2}
              />
            </g>
          ) : null}
          {xTicks.map((value) => (
            <text
              key={`x-${value}`}
              x={x(value)}
              y={HEIGHT - 8}
              textAnchor="middle"
              className="fill-muted-foreground text-[11px]"
            >
              {value === 0 ? "0%" : signed(value, Number.isInteger(value) ? 0 : 1)}
            </text>
          ))}
          {mine.bars.map((bar, i) => (
            <rect
              key={`hit-${bar.lo}`}
              x={x(bar.lo)}
              y={PAD.top}
              width={Math.max(1, x(bar.hi) - x(bar.lo))}
              height={plotHeight}
              fill="transparent"
              onMouseEnter={() => setHover(i)}
            />
          ))}
        </svg>
        {shown ? (
          <div
            className="tnum pointer-events-none absolute top-1 z-10 w-52 space-y-1 rounded-md border border-border bg-card px-2.5 py-2 text-xs shadow-md"
            style={{
              left: Math.min(Math.max(x(shown.hi) + 8, 4), width - 214),
            }}
          >
            <p className="font-medium text-foreground">{(shown.prob * 100).toFixed(1)}% chance</p>
            <p className="text-muted-foreground">
              {signed(shown.lo)} to {signed(shown.hi)} ·{" "}
              {dollars(subject.basePrice * (1 + shown.lo / 100))} to{" "}
              {dollars(subject.basePrice * (1 + shown.hi / 100))}
            </p>
            {theirs && compare ? (
              <p className="text-muted-foreground">
                {compare.label}: {(chanceIn(theirs, shown.lo, shown.hi) * 100).toFixed(1)}%
              </p>
            ) : null}
          </div>
        ) : null}
      </div>
      <div className="flex flex-wrap gap-x-4 gap-y-1 text-xs text-muted-foreground">
        <span className="flex items-center gap-1.5">
          <svg viewBox="0 0 12 12" className="size-3" aria-hidden="true">
            <rect x={1} y={3} width={4} height={9} className="fill-series-1/55" />
            <rect x={7} y={0} width={4} height={12} className="fill-series-1/55" />
          </svg>
          This report: chance per 1% of return
        </span>
        {compare ? (
          <span className="flex min-w-0 items-center gap-1.5">
            <svg viewBox="0 0 16 12" className="h-3 w-4 shrink-0" aria-hidden="true">
              <path
                d="M0,11 L0,5 L8,5 L8,2 L16,2"
                className="fill-none stroke-muted-foreground"
                strokeWidth={2}
              />
            </svg>
            <span className="truncate">Compared: {compare.label}</span>
          </span>
        ) : null}
        {outcome && actual !== null ? (
          <span className="flex items-center gap-1.5">
            <Swatch where={outcome.landing} />
            actual {signed(actual)}, {LANDING[outcome.landing].label}
          </span>
        ) : null}
        <span>
          Beyond the bars: {(mine.under * 100).toFixed(1)}% below {signed(mine.lo, 0)},{" "}
          {(mine.over * 100).toFixed(1)}% above {signed(mine.hi, 0)}
        </span>
      </div>
    </div>
  );
}
